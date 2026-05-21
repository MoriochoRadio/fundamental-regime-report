"""regime state_series 시점 매핑 + contiguous block 추출.

docs/ui_components.md §4 — lookup_regime_at, compute_regime_blocks,
find_close_column.
"""

from __future__ import annotations

import pandas as pd


def lookup_regime_at(
    date_val: pd.Timestamp | None,
    state_series: pd.DataFrame | None,
) -> str | None:
    """state_series 에서 *가장 가까운 영업일 ≤ date* 의 regime label.

    state_series: columns date·state_label, 일간 freq, 2015-10-01 ~ 2024-12-30.

    Args:
        date_val: 조회 시점. None → None.
        state_series: regime 시계열. None or empty → None.

    Returns:
        regime label str 또는 None (warmup 또는 데이터 외).
    """
    if date_val is None or state_series is None or state_series.empty:
        return None
    if "date" not in state_series.columns or "state_label" not in state_series.columns:
        return None
    target = pd.Timestamp(date_val)
    df = state_series.copy()
    df["date"] = pd.to_datetime(df["date"])
    mask = df["date"] <= target
    if not mask.any():
        return None
    last = df[mask].sort_values("date").iloc[-1]
    return str(last["state_label"])


def compute_regime_blocks(state_series: pd.DataFrame | None) -> pd.DataFrame:
    """contiguous regime block → (start, end, label) DataFrame.

    plotly add_vrect 입력. state_series 가 *동일 label 연속* 인 영역을
    하나의 block 으로 묶음.

    Args:
        state_series: columns date·state_label.

    Returns:
        DataFrame[start, end, label] (날짜 datetime). 빈 입력 → 빈 DataFrame.
    """
    if state_series is None or state_series.empty:
        return pd.DataFrame(columns=["start", "end", "label"])
    df = state_series.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    # block id: label 변경 시점마다 +1
    df["_block"] = (df["state_label"] != df["state_label"].shift()).cumsum()
    blocks = df.groupby("_block").agg(
        start=("date", "min"),
        end=("date", "max"),
        label=("state_label", "first"),
    )
    return blocks.reset_index(drop=True)


def find_close_column(ohlcv: pd.DataFrame | None) -> str | None:
    """cp949 "종가" 또는 영문 "Close" 컬럼 자동 식별.

    pykrx 캐시는 한국어 컬럼 ("시가", "고가", "저가", "종가", "거래량",
    "등락률"). 다른 출처는 영문.

    Args:
        ohlcv: OHLCV DataFrame.

    Returns:
        close 컬럼 이름 또는 None.
    """
    if ohlcv is None or ohlcv.empty:
        return None
    for candidate in ("종가", "Close", "close"):
        if candidate in ohlcv.columns:
            return candidate
    # contains 검사 (예: "종가KRW" 등 변형)
    for col in ohlcv.columns:
        if "종가" in col or col.lower() == "close":
            return col
    return None


def find_date_column_or_index(
    ohlcv: pd.DataFrame | None,
) -> tuple[pd.Series | None, pd.DataFrame | None]:
    """OHLCV 의 *date* 가 index 인지 column 인지 식별.

    Returns (date_series, df_reset). df_reset 은 index 가 column 으로 정리된 DataFrame.
    """
    if ohlcv is None or ohlcv.empty:
        return (None, None)
    # index 가 datetime 이면 reset
    if isinstance(ohlcv.index, pd.DatetimeIndex):
        df_reset = ohlcv.reset_index()
        date_col = df_reset.columns[0]
        return (pd.to_datetime(df_reset[date_col]), df_reset)
    # column 에 date 후보
    for candidate in ("날짜", "Date", "date"):
        if candidate in ohlcv.columns:
            df_reset = ohlcv.copy()
            return (pd.to_datetime(df_reset[candidate]), df_reset)
    # 마지막 시도: 첫 컬럼이 datetime convertible
    try:
        s = pd.to_datetime(ohlcv.iloc[:, 0])
        return (s, ohlcv.copy())
    except (ValueError, TypeError):
        return (None, None)
