"""regime features 단위 테스트 (PROGRESS §5.6 D4).

3 피처 산출 + rolling z-score + 룩어헤드 차단.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from frr.regime.features import FEATURE_COLUMNS, compute_features, drop_warmup_rows


def _synthetic_close(n: int = 500, seed: int = 42) -> pd.Series:
    """합성 KOSPI200 close 시계열 (random walk)."""
    rng = np.random.default_rng(seed)
    log_ret = rng.standard_normal(n) * 0.01
    log_price = np.cumsum(log_ret) + np.log(100)
    return pd.Series(np.exp(log_price), index=pd.date_range("2020-01-01", periods=n, freq="D"))


def test_compute_features_returns_3_columns() -> None:
    """3 피처 컬럼 + DatetimeIndex 보존."""
    close = _synthetic_close(n=500)
    df = compute_features(close)
    assert list(df.columns) == FEATURE_COLUMNS
    assert df.index.equals(close.index)


def test_compute_features_initial_rows_nan() -> None:
    """초기 long_vol_window + z_score_window 미달 row 는 NaN."""
    close = _synthetic_close(n=500)
    df = compute_features(close, long_vol_window=60, z_score_window=252)
    # 초기 60 row 는 vol_60d NaN (rolling 미달)
    assert df["vol_60d"].iloc[:30].isna().all()


def test_compute_features_too_short_raises() -> None:
    """close 길이 부족 → ValueError."""
    close = _synthetic_close(n=100)
    with pytest.raises(ValueError, match="부족"):
        compute_features(close)


def test_drop_warmup_rows_removes_nan() -> None:
    """drop_warmup_rows 가 NaN 포함 row 제거."""
    close = _synthetic_close(n=500)
    df = compute_features(close)
    clean = drop_warmup_rows(df)
    assert not clean[FEATURE_COLUMNS].isna().any().any()
    # 일부 row 는 남아야
    assert len(clean) > 0


def test_compute_features_zscore_centered_near_zero() -> None:
    """rolling z-score 표준화 — clean 데이터 평균이 0 근처."""
    close = _synthetic_close(n=600)
    df = drop_warmup_rows(compute_features(close))
    # z-score 의 누적 평균은 0 근처 (rolling 안에서)
    for col in FEATURE_COLUMNS:
        m = df[col].mean()
        assert abs(m) < 1.0, f"{col} 평균 {m:.4f} — z-score 범위 밖"


def test_compute_features_no_lookahead() -> None:
    """t 시점 피처 가 t 이후 데이터에 의존하지 않음 — 룩어헤드 차단.

    검증 방법: 전체 시계열의 피처 vs *t 까지만* 자른 시계열의 피처 — t 시점
    값이 동일해야.
    """
    close = _synthetic_close(n=500)
    df_full = compute_features(close)
    # t = 400 시점 까지만 사용
    df_partial = compute_features(close.iloc[:400])
    # t=399 시점 값이 동일 (rolling 윈도우 안)
    t = 399
    for col in FEATURE_COLUMNS:
        v_full = df_full[col].iloc[t]
        v_partial = df_partial[col].iloc[t]
        if pd.isna(v_full) or pd.isna(v_partial):
            continue
        assert v_full == pytest.approx(v_partial, abs=1e-10), (
            f"{col} t={t} 시점 룩어헤드: full={v_full} partial={v_partial}"
        )
