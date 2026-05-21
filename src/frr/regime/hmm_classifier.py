"""HMM 본 라인 분류기 (PROGRESS §5.6 D3).

설계:
- Gaussian HMM (`hmmlearn.hmm.GaussianHMM`)
- K=3 (위험회피·중립·위험선호) — 학술 관행
- covariance_type="full" (각 상태가 다른 covariance)
- forward filtering — *t 시점 가능 상태 분포 (alpha)* 만 사용. Viterbi 의
  backward smoothing 은 *retrospective 분석* 용도로 별도 산출.

룩어헤드 차단:
- 학습은 *전체 시계열 batch* — 단계 3 batch 분석 (CLAUDE.md §3.2).
- inference 시 *t 시점에 t 이전 obs 만 누적 alpha* 사용 권장.
- 본 모듈은 *학습 함수 + forward filtering helper* 제공.

State labeling 사후 명명:
- HMM 상태 0/1/2 는 *번호만*. 학습 후 *각 상태의 평균 ret_20d·vol_60d*
  로 사후 명명 (`label_states_by_return_vol`).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM


def train_hmm(
    X: pd.DataFrame,
    *,
    n_components: int = 3,
    covariance_type: str = "full",
    n_iter: int = 200,
    random_state: int = 42,
    tol: float = 1e-3,
) -> GaussianHMM:
    """Gaussian HMM 학습.

    Args:
        X: features DataFrame (warmup NaN drop 후).
        n_components: 상태 수 (기본 3).
        covariance_type: "full"·"diag"·"tied"·"spherical" (기본 "full").
        n_iter: EM 반복 (기본 200).
        random_state: 시드 (재현성).
        tol: 수렴 임계 (기본 1e-3).

    Returns:
        학습된 GaussianHMM. `.score(X)` 로 log-likelihood, `.predict(X)`로
        Viterbi 경로 (retrospective), `.predict_proba(X)` 로 forward-backward
        posterior 산출 가능.

    Raises:
        ValueError: X 가 NaN 포함 또는 비었음.
    """
    if X.isna().any().any():
        raise ValueError("train_hmm: X 에 NaN 포함 — drop_warmup_rows 적용 필요")
    if len(X) == 0:
        raise ValueError("train_hmm: X 가 빈 DataFrame")

    model = GaussianHMM(
        n_components=n_components,
        covariance_type=covariance_type,
        n_iter=n_iter,
        random_state=random_state,
        tol=tol,
    )
    model.fit(X.to_numpy())
    return model


def forward_filter(
    model: GaussianHMM,
    X: pd.DataFrame,
) -> np.ndarray:
    """Forward-only filtering — *t 시점 alpha* 행렬 (n_samples × n_components).

    표준 forward-backward 의 alpha 만 사용. backward beta 사용하지 않음 (룩어헤드
    차단). 정규화된 alpha — 각 row 합 = 1.

    `hmmlearn` API: `_compute_log_likelihood` + `_do_forward_log_pass` 가 *공개
    아님*. 대안: `score_samples` 의 posteriors 는 *forward-backward* (룩어헤드).
    본 함수는 *수동 forward* 산출.

    Args:
        model: 학습된 GaussianHMM.
        X: features DataFrame.

    Returns:
        forward alpha (n_samples × n_components, 정규화).
    """
    obs = X.to_numpy()
    n_samples = len(obs)
    n_states = model.n_components

    # log emission probability (n_samples × n_states)
    # _compute_log_likelihood 는 hmmlearn 내부 API — 공개 아님이라
    # 대안: 각 상태의 multivariate Gaussian PDF 직접 계산
    from scipy.stats import multivariate_normal

    log_emiss = np.zeros((n_samples, n_states))
    for k in range(n_states):
        mean = model.means_[k]
        cov = model.covars_[k]
        log_emiss[:, k] = multivariate_normal.logpdf(obs, mean=mean, cov=cov)

    # forward in log space
    log_alpha = np.full((n_samples, n_states), -np.inf)
    log_alpha[0] = np.log(model.startprob_ + 1e-300) + log_emiss[0]

    log_transmat = np.log(model.transmat_ + 1e-300)
    for t in range(1, n_samples):
        # log_alpha[t, k] = log_emiss[t, k] + logsumexp_j(log_alpha[t-1, j] + log_transmat[j, k])
        for k in range(n_states):
            log_alpha[t, k] = log_emiss[t, k] + _logsumexp(log_alpha[t - 1] + log_transmat[:, k])

    # 정규화 (각 row 합 = 1, log space → linear)
    log_norm = np.array([_logsumexp(log_alpha[t]) for t in range(n_samples)])
    alpha = np.exp(log_alpha - log_norm[:, np.newaxis])
    return alpha


def _logsumexp(a: np.ndarray) -> float:
    """수치 안정 logsumexp."""
    m = float(np.max(a))
    if m == -np.inf:
        return -np.inf
    return m + float(np.log(np.sum(np.exp(a - m))))


def label_states_by_return_vol(
    model: GaussianHMM,
    feature_names: list[str],
    *,
    return_col: str = "ret_20d",
    vol_col: str = "vol_60d",
) -> dict[int, str]:
    """학습된 HMM 의 각 상태를 *위기 점수 (vol_z − ret_z) 순* 사후 명명.

    학술 정의:
    - 위험회피 (Risk-off): 수익률 ↓ + 변동성 ↑ → 위기 점수 *높음*
    - 위험선호 (Risk-on): 수익률 ↑ + 변동성 ↓ → 위기 점수 *낮음*
    - 중립: 그 사이

    명명 규칙 (정정 2026-05-21, 초기 vol 순 단순 매칭 부적합 발견 후):
    - 각 상태의 *위기 점수* = mean(vol_z) − mean(ret_z) 계산
    - 위기 점수 가장 높음 → 위험회피
    - 위기 점수 가장 낮음 → 위험선호
    - 중간 → 중립

    K≠3 인 경우 generic `state_{k}` 명명.

    Args:
        model: 학습된 GaussianHMM.
        feature_names: 컬럼 순서.
        return_col: 수익률 컬럼 이름.
        vol_col: 변동성 컬럼 이름.

    Returns:
        {state_idx: label} — "위험회피"·"중립"·"위험선호".
    """
    means = model.means_  # shape (n_components, n_features)
    ret_idx = feature_names.index(return_col)
    vol_idx = feature_names.index(vol_col)

    if len(means) != 3:
        return {k: f"state_{k}" for k in range(len(means))}

    # 위기 점수 = vol_z - ret_z (높을수록 위기)
    risk_scores = [(means[k, vol_idx] - means[k, ret_idx], k) for k in range(3)]
    risk_scores.sort()  # 오름차순 (낮은 위기 → 높은 위기)

    # 가장 낮은 위기 점수 → 위험선호, 중간 → 중립, 가장 높음 → 위험회피
    result: dict[int, str] = {}
    result[risk_scores[0][1]] = "위험선호"
    result[risk_scores[1][1]] = "중립"
    result[risk_scores[2][1]] = "위험회피"
    return result
