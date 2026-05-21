"""HMM vs GMM vs K-Means 비교 + K=2·3·4 BIC·AIC 진단 (PROGRESS §5.6.2).

CLAUDE.md §8.4 박제 — hmmlearn 본 라인 + sklearn GMM·K-Means 비교.

기준:
- 모델: HMM (`hmmlearn.GaussianHMM`) / GMM (`sklearn.mixture.GaussianMixture`) /
  K-Means (`sklearn.cluster.KMeans`)
- K: 2·3·4 비교
- 평가: BIC·AIC (GMM·HMM 만), inertia (K-Means)
- State labeling 동일 — 위기 점수 (vol_z - ret_z) 순 (K=3 만 지원)
- 안정성: 다른 random_state 시드로 결과 변동 측정 (별도 함수)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture


def fit_hmm(X: pd.DataFrame, *, n_components: int = 3, random_state: int = 42) -> GaussianHMM:
    """HMM 적합 (compare 용 wrapper, train_hmm 와 동일)."""
    model = GaussianHMM(
        n_components=n_components,
        covariance_type="full",
        n_iter=200,
        random_state=random_state,
        tol=1e-3,
    )
    model.fit(X.to_numpy())
    return model


def fit_gmm(X: pd.DataFrame, *, n_components: int = 3, random_state: int = 42) -> GaussianMixture:
    """GMM 적합 (시점 독립 가정, HMM 의 전이 행렬 없음)."""
    model = GaussianMixture(
        n_components=n_components,
        covariance_type="full",
        random_state=random_state,
        max_iter=200,
        tol=1e-3,
    )
    model.fit(X.to_numpy())
    return model


def fit_kmeans(X: pd.DataFrame, *, n_clusters: int = 3, random_state: int = 42) -> KMeans:
    """K-Means 적합."""
    model = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init=10,
        max_iter=300,
    )
    model.fit(X.to_numpy())
    return model


def hmm_bic_aic(model: GaussianHMM, X: pd.DataFrame) -> tuple[float, float]:
    """HMM BIC·AIC — log-likelihood + 파라미터 수 기반.

    파라미터 수:
    - means: K × D
    - covars (full): K × D × (D+1) / 2
    - transmat: K × (K-1) 자유도
    - startprob: K-1 자유도
    """
    n_samples = len(X)
    K = model.n_components
    D = X.shape[1]
    n_params = K * D + K * D * (D + 1) // 2 + K * (K - 1) + (K - 1)
    log_lik = float(model.score(X.to_numpy()))
    bic = -2.0 * log_lik + n_params * np.log(n_samples)
    aic = -2.0 * log_lik + 2 * n_params
    return float(bic), float(aic)


def compare_k_range(
    X: pd.DataFrame,
    *,
    k_values: tuple[int, ...] = (2, 3, 4),
    random_state: int = 42,
) -> pd.DataFrame:
    """K=2·3·4 비교 — HMM/GMM/K-Means × K → BIC·AIC·log_lik·inertia.

    Returns:
        DataFrame[model, K, log_lik, bic, aic, inertia] (long format).
    """
    rows = []
    for k in k_values:
        # HMM
        hmm = fit_hmm(X, n_components=k, random_state=random_state)
        hmm_ll = float(hmm.score(X.to_numpy()))
        hmm_bic, hmm_aic = hmm_bic_aic(hmm, X)
        rows.append(
            {
                "model": "HMM",
                "K": k,
                "log_lik": hmm_ll,
                "bic": hmm_bic,
                "aic": hmm_aic,
                "inertia": None,
                "converged": bool(hmm.monitor_.converged),
            }
        )

        # GMM
        gmm = fit_gmm(X, n_components=k, random_state=random_state)
        gmm_ll = float(gmm.score(X.to_numpy()) * len(X))  # score() 가 mean log-lik
        rows.append(
            {
                "model": "GMM",
                "K": k,
                "log_lik": gmm_ll,
                "bic": float(gmm.bic(X.to_numpy())),
                "aic": float(gmm.aic(X.to_numpy())),
                "inertia": None,
                "converged": bool(gmm.converged_),
            }
        )

        # K-Means
        km = fit_kmeans(X, n_clusters=k, random_state=random_state)
        rows.append(
            {
                "model": "K-Means",
                "K": k,
                "log_lik": None,
                "bic": None,
                "aic": None,
                "inertia": float(km.inertia_),
                "converged": True,
            }
        )
    return pd.DataFrame(rows)


def stability_check(
    X: pd.DataFrame,
    *,
    n_components: int = 3,
    seeds: tuple[int, ...] = (42, 123, 7, 2024, 999),
) -> pd.DataFrame:
    """시드 변동 안정성 검사 — HMM/GMM/K-Means × seed → log-lik·BIC·AIC·inertia.

    학습된 모델의 *시드 의존성* 측정. 안정성 높을수록 결과 신뢰도 ↑.
    """
    rows = []
    for seed in seeds:
        hmm = fit_hmm(X, n_components=n_components, random_state=seed)
        hmm_bic, hmm_aic = hmm_bic_aic(hmm, X)
        rows.append(
            {
                "model": "HMM",
                "seed": seed,
                "log_lik": float(hmm.score(X.to_numpy())),
                "bic": hmm_bic,
                "aic": hmm_aic,
            }
        )
        gmm = fit_gmm(X, n_components=n_components, random_state=seed)
        rows.append(
            {
                "model": "GMM",
                "seed": seed,
                "log_lik": float(gmm.score(X.to_numpy()) * len(X)),
                "bic": float(gmm.bic(X.to_numpy())),
                "aic": float(gmm.aic(X.to_numpy())),
            }
        )
        km = fit_kmeans(X, n_clusters=n_components, random_state=seed)
        rows.append(
            {
                "model": "K-Means",
                "seed": seed,
                "log_lik": None,
                "bic": None,
                "aic": None,
                "inertia": float(km.inertia_),
            }
        )
    return pd.DataFrame(rows)
