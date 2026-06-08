"""HMM 분류기 단위 테스트 (PROGRESS §5.6 D3).

학습 reproducibility · forward filter 정규화 · state labeling.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from frr.regime.features import FEATURE_COLUMNS, compute_features, drop_warmup_rows
from frr.regime.hmm_classifier import (
    forward_filter,
    label_states_by_return_vol,
    train_hmm,
)


def _synthetic_features(n: int = 800, seed: int = 42) -> pd.DataFrame:
    """3 피처 산출 — 합성 close 기반."""
    rng = np.random.default_rng(seed)
    log_ret = rng.standard_normal(n) * 0.01
    log_price = np.cumsum(log_ret) + np.log(100)
    close = pd.Series(np.exp(log_price), index=pd.date_range("2018-01-01", periods=n, freq="D"))
    return drop_warmup_rows(compute_features(close))


def test_train_hmm_basic() -> None:
    """학습 + means_/covars_ shape."""
    X = _synthetic_features(n=800)
    model = train_hmm(X, n_components=3, random_state=42)
    assert model.means_.shape == (3, 3)
    assert model.covars_.shape == (3, 3, 3)  # full covariance


def test_train_hmm_reproducibility() -> None:
    """동일 시드 → 동일 means_ (재현성)."""
    X = _synthetic_features(n=800)
    m1 = train_hmm(X, random_state=42)
    m2 = train_hmm(X, random_state=42)
    np.testing.assert_allclose(m1.means_, m2.means_, atol=1e-10)


def test_train_hmm_rejects_nan() -> None:
    """X 에 NaN 포함 → ValueError."""
    X = _synthetic_features(n=800)
    X.iloc[10, 0] = np.nan
    with pytest.raises(ValueError, match="NaN"):
        train_hmm(X)


def test_forward_filter_normalized() -> None:
    """forward alpha — 각 row 합 = 1 (정규화)."""
    X = _synthetic_features(n=500)
    model = train_hmm(X, random_state=42)
    alpha = forward_filter(model, X)
    assert alpha.shape == (len(X), 3)
    row_sums = alpha.sum(axis=1)
    np.testing.assert_allclose(row_sums, 1.0, atol=1e-8)


def test_forward_filter_no_backward_smoothing() -> None:
    """forward filter 는 *t 시점에 t 이후 obs 사용 안 함*.

    검증: 전체 시계열의 alpha[t] vs 처음 t+1 obs 만 사용한 alpha[t] 동일.
    """
    X = _synthetic_features(n=500)
    model = train_hmm(X, random_state=42)
    alpha_full = forward_filter(model, X)
    # t=300 까지만 잘라 alpha 산출
    t = 300
    alpha_partial = forward_filter(model, X.iloc[: t + 1])
    np.testing.assert_allclose(alpha_full[t], alpha_partial[t], atol=1e-8)


def test_label_states_k3() -> None:
    """K=3 — 3 상태가 위험회피·중립·위험선호 매핑."""
    X = _synthetic_features(n=800)
    model = train_hmm(X, n_components=3, random_state=42)
    labels = label_states_by_return_vol(model, FEATURE_COLUMNS)
    assert set(labels.values()) == {"위험선호", "중립", "위험회피"}
    assert set(labels.keys()) == {0, 1, 2}


def test_label_states_k_non_3() -> None:
    """K≠3 — generic state_{k} 라벨."""
    X = _synthetic_features(n=800)
    model = train_hmm(X, n_components=2, random_state=42)
    labels = label_states_by_return_vol(model, FEATURE_COLUMNS)
    assert all(v.startswith("state_") for v in labels.values())
