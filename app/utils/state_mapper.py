"""시장 상태 (state_series) 시점 매핑 + contiguous block 추출.

docs/ui_design.md §2.5 PriceChartWithStateOverlay·§2.7 StateInterpretBox
매핑 + docs/tech_architecture.md §2 폴더 구조 매핑.

Phase 4 자산 변환 (검증 1 매핑):
- 파일명: regime_mapper.py → state_mapper.py
- 함수명: lookup_regime_at → lookup_state_at
- 함수명: compute_regime_blocks → compute_state_blocks
- docstring·주석 "regime" → "시장 상태" / "state" 일관 정정
- (C) 그대로 재사용: find_close_column
- (신규): find_date_column_or_index (3 단계 §2 명세)
"""

from __future__ import annotations

import pandas as pd


def lookup_state_at(
    date_val: pd.Timestamp | None,
    state_series: pd.DataFrame | None,
) -> str | None:
    """state_series 에서 *가장 가까운 영업일 ≤ date* 의 시장 상태 라벨.

    state_series: columns date·state_label, 일간 freq, 2015-10-01 ~ 2024-12-30.

    Args:
        date_val: 조회 시점. None → None.
        state_series: 시장 상태 시계열. None or empty → None.

    Returns:
        시장 상태 라벨 str (예: "위험회피"·"중립"·"위험선호") 또는
        None (분석 시작 9 개월간 또는 데이터 외).
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


def compute_state_blocks(state_series: pd.DataFrame | None) -> pd.DataFrame:
    """contiguous 시장 상태 block → (start, end, label) DataFrame.

    plotly add_vrect 입력. state_series 가 *동일 label 연속* 인 영역을
    하나의 block 으로 묶음.

    Args:
        state_series: columns date·state_label.

    Returns:
        DataFrame[start, end, label] (날짜 datetime). 빈 입력 → 빈 DataFrame.
    """
    if state_series is None or state_series.empty:
        return pd.DataFrame(columns=["start", "end", "label"])
    if "date" not in state_series.columns or "state_label" not in state_series.columns:
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
    """OHLCV DataFrame 에서 종가 컬럼 자동 식별.

    우선순위: "Close" → "close" → "종가" → "Adj Close" → "adj_close".

    >>> import pandas as pd
    >>> df = pd.DataFrame({"Close": [100, 101]})
    >>> find_close_column(df)
    'Close'
    >>> df2 = pd.DataFrame({"종가": [100, 101]})
    >>> find_close_column(df2)
    '종가'
    >>> find_close_column(None) is None
    True
    >>> find_close_column(pd.DataFrame({"Open": [100]})) is None
    True
    """
    if ohlcv is None or ohlcv.empty:
        return None
    candidates = ("Close", "close", "종가", "Adj Close", "adj_close")
    for col in candidates:
        if col in ohlcv.columns:
            return col
    return None


def find_date_column_or_index(df: pd.DataFrame | None) -> str | None:
    """DataFrame 의 date 컬럼 자동 식별 또는 index 사용 안내.

    우선순위: "date" → "Date" → "일자" → datetime index ("__index__")
    → None.

    Returns:
        - 컬럼명 str (예: "date")
        - "__index__" (DatetimeIndex 사용 안내)
        - None (date 컬럼·index 모두 부재)

    >>> import pandas as pd
    >>> df = pd.DataFrame({"date": pd.to_datetime(["2024-01-01"])})
    >>> find_date_column_or_index(df)
    'date'
    >>> df2 = pd.DataFrame(
    ...     {"value": [1]}, index=pd.to_datetime(["2024-01-01"])
    ... )
    >>> find_date_column_or_index(df2)
    '__index__'
    >>> find_date_column_or_index(pd.DataFrame({"value": [1]})) is None
    True
    >>> find_date_column_or_index(None) is None
    True
    """
    if df is None or df.empty:
        return None
    candidates = ("date", "Date", "일자")
    for col in candidates:
        if col in df.columns:
            return col
    if isinstance(df.index, pd.DatetimeIndex):
        return "__index__"
    return None
