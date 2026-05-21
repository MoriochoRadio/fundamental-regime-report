"""평가 함수 — PR-AUC + AUC + Brier + Calibration (ECE) + Top-K precision.

D8 박제 (§4 결정 로그, 2026-05-18 승인) + §5.5.16 평가 함수 설계 결정 게이트
메모 2 항목 본격 결정:

1. **양성 N=3 통계적 변동성**: `bootstrap_n > 0` 옵션 으로 95% CI 산출.
   기본 비활성 (B-3 단위 테스트 속도). B-4 결과 보고 시점에 활성.
2. **fold 단위 vs 종목 단위 평가**: 본 함수는 *주 평가 단위는 종목
   (ticker × as_of) pooled across folds*. fold 단위는 별도 helper.

기본 (양성 20 KOSPI200 모집단 한계 명시):
- N positive 가 평가 결과 dict 에 항상 포함 → 결과 해석 시 변동성 보고 의무
- bootstrap CI 옵션은 양성 적을 때 *수치적 변동성* 표시 (B-4 활성)
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    roc_auc_score,
)


def expected_calibration_error(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    n_bins: int = 10,
) -> float:
    """Expected Calibration Error (ECE).

    예측 확률을 n_bins 구간으로 분할 → 각 bin 의 평균 예측 확률 vs 실제 양성
    비율의 가중 평균 절대 차이. 0 = 완벽 캘리브레이션.
    """
    y_true_arr = np.asarray(y_true, dtype=float)
    y_pred_arr = np.asarray(y_pred_proba, dtype=float)
    if len(y_true_arr) == 0:
        return float("nan")

    bin_edges = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total = len(y_true_arr)
    for i in range(n_bins):
        lo, hi = bin_edges[i], bin_edges[i + 1]
        # 마지막 bin 은 closed-closed
        if i == n_bins - 1:
            mask = (y_pred_arr >= lo) & (y_pred_arr <= hi)
        else:
            mask = (y_pred_arr >= lo) & (y_pred_arr < hi)
        if not mask.any():
            continue
        bin_pred_mean = y_pred_arr[mask].mean()
        bin_true_mean = y_true_arr[mask].mean()
        ece += (mask.sum() / total) * abs(bin_pred_mean - bin_true_mean)
    return float(ece)


def top_k_precision(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    k: int | float,
) -> float:
    """Top-K precision — 상위 K (정수) 또는 K 비율 (0~1 float) 의 양성 비율.

    Args:
        y_true: 0/1 라벨.
        y_pred_proba: 양성 확률.
        k: 정수면 절대 개수, float 면 비율 (0 < k < 1).

    Returns:
        Top-K 의 양성 비율 (precision@K).
    """
    y_true_arr = np.asarray(y_true)
    y_pred_arr = np.asarray(y_pred_proba)
    n = len(y_true_arr)
    if n == 0:
        return float("nan")

    if isinstance(k, float):
        if not (0.0 < k <= 1.0):
            raise ValueError(f"top_k_precision: k 가 float 면 (0, 1] 범위, 실제 {k}")
        k_int = max(1, round(n * k))
    else:
        k_int = max(1, min(int(k), n))

    # 상위 k 인덱스
    top_idx = np.argsort(-y_pred_arr)[:k_int]
    return float(y_true_arr[top_idx].mean())


def evaluate_predictions(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    *,
    top_k_ratio: float = 0.1,
    bootstrap_n: int = 0,
    random_state: int = 42,
    ece_n_bins: int = 10,
) -> dict[str, float | tuple[float, float] | int]:
    """D8 박제 평가 지표 5 + 변동성 지원 (§5.5.16).

    Args:
        y_true: 0/1 라벨.
        y_pred_proba: 양성 확률.
        top_k_ratio: Top-K precision 의 K 비율 (기본 10%).
        bootstrap_n: bootstrap 반복 수. 0 = 비활성 (기본, B-3 단위 테스트).
            > 0 활성 시 각 metric 에 95% CI (lo, hi) 튜플 추가.
        random_state: bootstrap 시드.
        ece_n_bins: ECE 구간 수.

    Returns:
        dict — pr_auc, roc_auc, brier, ece, top_k_precision, n_positive,
        n_total. bootstrap_n > 0 시 각 metric 의 95% CI 추가.

    양성 N=3 통계적 변동성 (§5.5.16 짚을 점 1):
    - n_positive 항상 포함 — 결과 보고 시 "양성 N=N 으로 변동성 큼" 명시 의무
    - bootstrap_n > 0 → 95% CI 산출 (B-4 활성 권장)
    """
    y_true_arr = np.asarray(y_true)
    y_pred_arr = np.asarray(y_pred_proba)
    n_total = len(y_true_arr)
    n_positive = int(y_true_arr.sum())

    if n_total == 0 or n_positive == 0 or n_positive == n_total:
        # 단일 클래스 — PR-AUC·AUC 정의 안 됨
        return {
            "pr_auc": float("nan"),
            "roc_auc": float("nan"),
            "brier": float("nan"),
            "ece": float("nan"),
            "top_k_precision": float("nan"),
            "n_positive": n_positive,
            "n_total": n_total,
        }

    def _compute(yt: np.ndarray, yp: np.ndarray) -> dict[str, float]:
        return {
            "pr_auc": float(average_precision_score(yt, yp)),
            "roc_auc": float(roc_auc_score(yt, yp)),
            "brier": float(brier_score_loss(yt, yp)),
            "ece": expected_calibration_error(yt, yp, n_bins=ece_n_bins),
            "top_k_precision": top_k_precision(yt, yp, top_k_ratio),
        }

    base_metrics = _compute(y_true_arr, y_pred_arr)
    result: dict[str, float | tuple[float, float] | int] = {**base_metrics}

    if bootstrap_n > 0:
        rng = np.random.default_rng(random_state)
        bs_samples: dict[str, list[float]] = {k: [] for k in base_metrics}
        for _ in range(bootstrap_n):
            idx = rng.integers(0, n_total, size=n_total)
            yt_bs = y_true_arr[idx]
            yp_bs = y_pred_arr[idx]
            if yt_bs.sum() == 0 or yt_bs.sum() == len(yt_bs):
                continue  # 단일 클래스 sample skip
            m = _compute(yt_bs, yp_bs)
            for k, v in m.items():
                bs_samples[k].append(v)
        for k, samples in bs_samples.items():
            if samples:
                arr = np.asarray(samples)
                lo, hi = float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))
                result[f"{k}_ci95"] = (lo, hi)

    result["n_positive"] = n_positive
    result["n_total"] = n_total
    return result
