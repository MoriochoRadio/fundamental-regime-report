"""평가 함수 단위 테스트 (PROGRESS §5.5.16 D8 박제 + 짚을 점 1).

PR-AUC + AUC + Brier + Calibration (ECE) + Top-K precision + bootstrap CI.
"""

from __future__ import annotations

import numpy as np
import pytest

from frr.models.evaluation import (
    evaluate_predictions,
    expected_calibration_error,
    top_k_precision,
)

# ---- ECE 단위 ------------------------------------------------------------


def test_ece_perfect_calibration_zero() -> None:
    """완벽 캘리브레이션 — ECE = 0.

    각 bin 의 예측 평균 = 실제 양성 비율.
    """
    # 합성: 0.1 확률 100 sample 중 10 양성, 0.5 확률 100 sample 중 50 양성
    np.random.seed(42)
    y_pred = np.concatenate([np.full(100, 0.1), np.full(100, 0.5)])
    y_true = np.concatenate([np.array([1] * 10 + [0] * 90), np.array([1] * 50 + [0] * 50)])
    ece = expected_calibration_error(y_true, y_pred, n_bins=10)
    assert ece < 0.05  # 완벽 가까움


def test_ece_extreme_miscalibration_high() -> None:
    """과신 — 0.9 예측인데 실제 양성 0% → ECE 큼."""
    y_pred = np.full(100, 0.9)
    y_true = np.zeros(100)
    ece = expected_calibration_error(y_true, y_pred)
    assert ece > 0.8  # 0.9 - 0.0 = 0.9 가까움


# ---- Top-K precision 단위 -----------------------------------------------


def test_top_k_precision_int_k() -> None:
    """k=정수 — 상위 k 인덱스 양성 비율."""
    y_pred = np.array([0.9, 0.8, 0.7, 0.6, 0.5])
    y_true = np.array([1, 1, 0, 1, 0])  # 상위 2 = [1,1] → precision=1.0
    assert top_k_precision(y_true, y_pred, k=2) == pytest.approx(1.0)


def test_top_k_precision_float_ratio() -> None:
    """k=비율 (0.4) — n=10 의 40% = 4 sample."""
    y_pred = np.linspace(0.9, 0.0, 10)
    y_true = np.array([1, 1, 0, 1, 0, 0, 0, 0, 0, 0])  # 상위 4 → [1,1,0,1] = 0.75
    assert top_k_precision(y_true, y_pred, k=0.4) == pytest.approx(0.75)


def test_top_k_precision_invalid_float_raises() -> None:
    """k=float 가 (0, 1] 밖 → ValueError."""
    y_pred = np.array([0.5, 0.5])
    y_true = np.array([0, 1])
    with pytest.raises(ValueError, match=r"\(0, 1\]"):
        top_k_precision(y_true, y_pred, k=1.5)


# ---- evaluate_predictions 통합 ------------------------------------------


def test_evaluate_predictions_all_metrics_present() -> None:
    """기본 (bootstrap=0) → 5 metric + n_positive + n_total."""
    rng = np.random.default_rng(42)
    n = 200
    y_true = (rng.random(n) < 0.1).astype(int)
    y_pred = rng.random(n)

    result = evaluate_predictions(y_true, y_pred, top_k_ratio=0.1)
    assert set(result.keys()) >= {
        "pr_auc",
        "roc_auc",
        "brier",
        "ece",
        "top_k_precision",
        "n_positive",
        "n_total",
    }
    assert result["n_total"] == n
    assert result["n_positive"] == int(y_true.sum())


def test_evaluate_predictions_single_class_returns_nan() -> None:
    """양성·음성 단일 클래스 → PR-AUC·AUC NaN (정의 안 됨)."""
    y_true = np.zeros(100, dtype=int)
    y_pred = np.linspace(0, 1, 100)

    result = evaluate_predictions(y_true, y_pred)
    assert np.isnan(result["pr_auc"])  # type: ignore[arg-type]
    assert np.isnan(result["roc_auc"])  # type: ignore[arg-type]
    assert result["n_positive"] == 0


def test_evaluate_predictions_bootstrap_ci() -> None:
    """bootstrap_n > 0 → 각 metric 에 _ci95 (lo, hi) 추가."""
    rng = np.random.default_rng(42)
    n = 300
    y_true = (rng.random(n) < 0.1).astype(int)
    y_pred = rng.random(n)

    result = evaluate_predictions(y_true, y_pred, bootstrap_n=100, random_state=42)
    for metric in ["pr_auc", "roc_auc", "brier", "ece", "top_k_precision"]:
        assert f"{metric}_ci95" in result
        ci = result[f"{metric}_ci95"]
        assert isinstance(ci, tuple) and len(ci) == 2
        lo, hi = ci
        assert lo <= hi


def test_evaluate_predictions_n_positive_reported() -> None:
    """양성 N 항상 보고됨 — §5.5.16 짚을 점 1 (통계적 변동성 명시 의무)."""
    y_true = np.array([0, 0, 0, 0, 0, 0, 0, 1, 1, 1])  # N positive = 3
    y_pred = np.linspace(0, 1, 10)

    result = evaluate_predictions(y_true, y_pred)
    assert result["n_positive"] == 3
