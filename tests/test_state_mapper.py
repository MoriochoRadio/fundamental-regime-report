"""app/utils/state_mapper.py 단위 테스트.

단계 5 단위 (a) 산출물. 검증 7 (에러 7 단위 테스트) + 검증 1 (regime →
state 정정) 매핑.

Phase 4 tests/test_app_utils.py 자산 변환:
- (B) 정정 (lookup_regime_at → lookup_state_at, compute_regime_blocks →
  compute_state_blocks)
- (C) 그대로 재사용 (find_close_column)
- (신규) find_date_column_or_index (3 단계 §2 명세)
"""

from __future__ import annotations

import pandas as pd

from app.utils.state_mapper import (
    compute_state_blocks,
    find_close_column,
    find_date_column_or_index,
    lookup_state_at,
)


def _make_state_series() -> pd.DataFrame:
    """합성 state_series (4 일, 2 label)."""
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"]),
            "state_label": ["위험회피", "위험회피", "중립", "중립"],
        }
    )


# ---- lookup_state_at --------------------------------------------------


def test_lookup_state_at_exact_match() -> None:
    series = _make_state_series()
    assert lookup_state_at(pd.Timestamp("2020-01-02"), series) == "위험회피"


def test_lookup_state_at_forward_to_prior_business_day() -> None:
    """date 사이 시점은 *직전 영업일* label 반환."""
    series = _make_state_series()
    # 2020-01-02 와 2020-01-03 사이 → 직전 (2020-01-02) 의 위험회피
    assert lookup_state_at(pd.Timestamp("2020-01-02 23:59:59"), series) == "위험회피"


def test_lookup_state_at_after_last() -> None:
    """date 가 series 마지막 이후 → 마지막 label."""
    series = _make_state_series()
    assert lookup_state_at(pd.Timestamp("2020-12-31"), series) == "중립"


def test_lookup_state_at_before_warmup() -> None:
    """date 가 series 시작 이전 → None (분석 시작 9 개월 안내)."""
    series = _make_state_series()
    assert lookup_state_at(pd.Timestamp("2019-12-31"), series) is None


def test_lookup_state_at_date_none() -> None:
    assert lookup_state_at(None, _make_state_series()) is None


def test_lookup_state_at_series_none() -> None:
    assert lookup_state_at(pd.Timestamp("2020-01-02"), None) is None


def test_lookup_state_at_series_empty() -> None:
    empty = pd.DataFrame(columns=["date", "state_label"])
    assert lookup_state_at(pd.Timestamp("2020-01-02"), empty) is None


def test_lookup_state_at_missing_columns() -> None:
    """date 또는 state_label 컬럼 부재 → None (방어적)."""
    bad = pd.DataFrame({"other_col": [1, 2]})
    assert lookup_state_at(pd.Timestamp("2020-01-02"), bad) is None


# ---- compute_state_blocks ---------------------------------------------


def test_compute_state_blocks_two_blocks() -> None:
    series = _make_state_series()
    blocks = compute_state_blocks(series)
    assert len(blocks) == 2
    assert list(blocks["label"]) == ["위험회피", "중립"]
    assert blocks.iloc[0]["start"] == pd.Timestamp("2020-01-01")
    assert blocks.iloc[0]["end"] == pd.Timestamp("2020-01-02")
    assert blocks.iloc[1]["start"] == pd.Timestamp("2020-01-03")
    assert blocks.iloc[1]["end"] == pd.Timestamp("2020-01-04")


def test_compute_state_blocks_single_label() -> None:
    """모든 행이 동일 label → 1 block."""
    series = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2020-01-02"]),
            "state_label": ["중립", "중립"],
        }
    )
    blocks = compute_state_blocks(series)
    assert len(blocks) == 1
    assert blocks.iloc[0]["label"] == "중립"


def test_compute_state_blocks_alternating() -> None:
    """label 매번 변경 → 행 수만큼 block."""
    series = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
            "state_label": ["위험회피", "중립", "위험선호"],
        }
    )
    blocks = compute_state_blocks(series)
    assert len(blocks) == 3
    assert list(blocks["label"]) == ["위험회피", "중립", "위험선호"]


def test_compute_state_blocks_empty() -> None:
    empty = pd.DataFrame(columns=["date", "state_label"])
    blocks = compute_state_blocks(empty)
    assert blocks.empty
    assert list(blocks.columns) == ["start", "end", "label"]


def test_compute_state_blocks_none() -> None:
    blocks = compute_state_blocks(None)
    assert blocks.empty
    assert list(blocks.columns) == ["start", "end", "label"]


def test_compute_state_blocks_missing_columns() -> None:
    """date 또는 state_label 컬럼 부재 → 빈 DataFrame (방어적)."""
    bad = pd.DataFrame({"other": [1, 2]})
    blocks = compute_state_blocks(bad)
    assert blocks.empty


# ---- find_close_column ------------------------------------------------


def test_find_close_column_capital() -> None:
    df = pd.DataFrame({"Close": [100, 101]})
    assert find_close_column(df) == "Close"


def test_find_close_column_lower() -> None:
    df = pd.DataFrame({"close": [100, 101]})
    assert find_close_column(df) == "close"


def test_find_close_column_korean() -> None:
    df = pd.DataFrame({"종가": [100, 101]})
    assert find_close_column(df) == "종가"


def test_find_close_column_adj_close_space() -> None:
    df = pd.DataFrame({"Adj Close": [100, 101]})
    assert find_close_column(df) == "Adj Close"


def test_find_close_column_priority() -> None:
    """Close 가 종가보다 우선."""
    df = pd.DataFrame({"Close": [100], "종가": [100]})
    assert find_close_column(df) == "Close"


def test_find_close_column_absent() -> None:
    df = pd.DataFrame({"Open": [100]})
    assert find_close_column(df) is None


def test_find_close_column_none() -> None:
    assert find_close_column(None) is None


def test_find_close_column_empty() -> None:
    assert find_close_column(pd.DataFrame()) is None


# ---- find_date_column_or_index ---------------------------------------


def test_find_date_column_lower() -> None:
    df = pd.DataFrame({"date": pd.to_datetime(["2024-01-01"])})
    assert find_date_column_or_index(df) == "date"


def test_find_date_column_capital() -> None:
    df = pd.DataFrame({"Date": pd.to_datetime(["2024-01-01"])})
    assert find_date_column_or_index(df) == "Date"


def test_find_date_column_korean() -> None:
    df = pd.DataFrame({"일자": pd.to_datetime(["2024-01-01"])})
    assert find_date_column_or_index(df) == "일자"


def test_find_date_column_index() -> None:
    df = pd.DataFrame({"value": [1]}, index=pd.to_datetime(["2024-01-01"]))
    assert find_date_column_or_index(df) == "__index__"


def test_find_date_column_priority_column_over_index() -> None:
    """date 컬럼이 DatetimeIndex 보다 우선."""
    df = pd.DataFrame(
        {"date": pd.to_datetime(["2024-01-01"]), "value": [1]},
        index=pd.to_datetime(["2024-01-01"]),
    )
    assert find_date_column_or_index(df) == "date"


def test_find_date_column_absent() -> None:
    df = pd.DataFrame({"value": [1]})
    assert find_date_column_or_index(df) is None


def test_find_date_column_none() -> None:
    assert find_date_column_or_index(None) is None


def test_find_date_column_empty() -> None:
    assert find_date_column_or_index(pd.DataFrame()) is None


# ---- pytest doctest collection (state_mapper 도 doctest 보존) ---------


def test_doctest_state_mapper() -> None:
    """state_mapper doctest 통과 검증."""
    import doctest

    from app.utils import state_mapper

    results = doctest.testmod(state_mapper, verbose=False)
    assert results.failed == 0, f"{results.failed} doctest failures"
