"""국면 입력 피처 — KOSPI200 지수 일간 시계열 → 3 피처 (PROGRESS §5.6 D4).

피처 정의:
1. rolling 20일 수익률 (월간 추세) — close.pct_change(20) 누적
2. rolling 60일 실현 변동성 (분기 변동) — log return 의 rolling std × sqrt(252)
3. 20일/60일 변동성 비율 (변동성 가속) — 단기/장기 비율

표준화: rolling z-score (각 시점 in-sample 통계, 룩어헤드 차단).

룩어헤드 차단 (§5 방법론적 원칙):
- 모든 rolling 연산은 *t 시점에서 t 이전 데이터만* 사용
- z-score 도 expanding 윈도우 또는 *충분히 긴 rolling* 으로 in-sample 통계
- 본 모듈은 *batch 산출* 이나 각 row 는 *self-contained* (t 이전 데이터만)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# 피처 컬럼 박제 (회귀 게이트)
FEATURE_COLUMNS: list[str] = ["ret_20d", "vol_60d", "vol_ratio_20_60"]


def compute_features(
    close: pd.Series,
    *,
    return_window: int = 20,
    short_vol_window: int = 20,
    long_vol_window: int = 60,
    z_score_window: int = 252,
    annualization: float = 252.0,
) -> pd.DataFrame:
    """KOSPI200 일간 close → 3 피처 + rolling z-score 표준화.

    Args:
        close: KOSPI200 일간 close. DatetimeIndex 권장.
        return_window: 누적 수익률 윈도우 (기본 20일).
        short_vol_window: 단기 변동성 윈도우 (기본 20일).
        long_vol_window: 장기 변동성 윈도우 (기본 60일).
        z_score_window: 표준화 rolling 윈도우 (기본 252일 = 1년).
        annualization: 변동성 연환산 (기본 sqrt(252)).

    Returns:
        DataFrame[index=close.index, columns=FEATURE_COLUMNS]. 초기 row 는
        rolling 윈도우 미달로 NaN — *batch 산출 시 모델 학습 전 drop*.

    Raises:
        ValueError: close 가 비었거나 단일 값.
    """
    if len(close) < long_vol_window + z_score_window:
        raise ValueError(
            f"close 길이 ({len(close)}) 부족 — 최소 "
            f"{long_vol_window + z_score_window} 일 필요 "
            f"(long_vol={long_vol_window} + z_score={z_score_window})"
        )

    # 1. log return (변동성 산출용)
    log_ret = np.log(close).diff()

    # 2. 누적 수익률 (단순 pct_change 누적, 20일)
    ret_20d = close.pct_change(return_window)

    # 3. 단기·장기 실현 변동성 (연환산)
    sqrt_ann = np.sqrt(annualization)
    vol_short = log_ret.rolling(short_vol_window).std() * sqrt_ann
    vol_long = log_ret.rolling(long_vol_window).std() * sqrt_ann

    # 4. 변동성 비율
    vol_ratio = vol_short / vol_long

    # 5. rolling z-score 표준화 (각 시점 in-sample 통계, 룩어헤드 차단)
    def _rolling_zscore(series: pd.Series, window: int) -> pd.Series:
        m = series.rolling(window, min_periods=window // 2).mean()
        s = series.rolling(window, min_periods=window // 2).std()
        return (series - m) / s

    df = pd.DataFrame(
        {
            "ret_20d": _rolling_zscore(ret_20d, z_score_window),
            "vol_60d": _rolling_zscore(vol_long, z_score_window),
            "vol_ratio_20_60": _rolling_zscore(vol_ratio, z_score_window),
        }
    )

    return df


def drop_warmup_rows(df: pd.DataFrame) -> pd.DataFrame:
    """초기 rolling 윈도우 미달 NaN row 제거."""
    return df.dropna(subset=FEATURE_COLUMNS)
