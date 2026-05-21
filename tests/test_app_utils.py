"""app/utils 단위 테스트 — pure functions.

Phase 4.1 산출물. docs/ui_components.md §4·§5 명세 검증.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

APP_DIR = Path(__file__).resolve().parent.parent / "app"
sys.path.insert(0, str(APP_DIR))

from utils.formatters import (  # noqa: E402
    classify_risk,
    format_date,
    format_percent,
    format_proba,
    format_ratio,
    format_ticker_option,
    format_won,
    regime_color,
)
from utils.regime_mapper import (  # noqa: E402
    compute_regime_blocks,
    find_close_column,
    find_date_column_or_index,
    lookup_regime_at,
)

# ---- format_won --------------------------------------------------------


def test_format_won_jo() -> None:
    assert format_won(1_625_000_000_000_000) == "1,625.00 조원"


def test_format_won_eok() -> None:
    assert format_won(50_000_000_000) == "500.0 억원"


def test_format_won_won() -> None:
    assert format_won(12_345_678) == "12,345,678 원"


def test_format_won_none() -> None:
    assert format_won(None) == "—"


def test_format_won_nan() -> None:
    assert format_won(float("nan")) == "—"


def test_format_won_inf() -> None:
    assert format_won(float("inf")) == "—"


# ---- format_percent ----------------------------------------------------


def test_format_percent_basic() -> None:
    assert format_percent(0.1234) == "12.34%"


def test_format_percent_decimal_1() -> None:
    assert format_percent(0.1234, decimal=1) == "12.3%"


def test_format_percent_none() -> None:
    assert format_percent(None) == "—"


# ---- format_proba / format_ratio --------------------------------------


def test_format_proba_4_decimals() -> None:
    assert format_proba(0.013564) == "0.0136"


def test_format_proba_none() -> None:
    assert format_proba(None) == "—"


def test_format_ratio() -> None:
    assert format_ratio(1.342, decimal=3) == "1.342"


# ---- classify_risk ----------------------------------------------------


def test_classify_risk_high() -> None:
    label, color = classify_risk(0.7)
    assert label == "높음"
    assert color == "#d62728"


def test_classify_risk_medium() -> None:
    label, _color = classify_risk(0.2)
    assert label == "중간"


def test_classify_risk_low() -> None:
    label, color = classify_risk(0.05)
    assert label == "낮음"
    assert color == "#2ca02c"


def test_classify_risk_none() -> None:
    label, _color = classify_risk(None)
    assert label == "—"


def test_classify_risk_boundary_high() -> None:
    """경계값 0.5 → 높음."""
    label, _ = classify_risk(0.5)
    assert label == "높음"


def test_classify_risk_boundary_medium() -> None:
    """경계값 0.1 → 중간."""
    label, _ = classify_risk(0.1)
    assert label == "중간"


# ---- regime_color -----------------------------------------------------


def test_regime_color_known() -> None:
    assert regime_color("위험회피") == "#d62728"
    assert regime_color("중립") == "#7f7f7f"
    assert regime_color("위험선호") == "#2ca02c"


def test_regime_color_unknown() -> None:
    assert regime_color("xxx") == "#888888"


def test_regime_color_none() -> None:
    assert regime_color(None) == "#888888"


# ---- format_ticker_option ---------------------------------------------


def test_format_ticker_option_with_name() -> None:
    assert format_ticker_option("005930", "삼성전자") == "005930 삼성전자"


def test_format_ticker_option_no_name() -> None:
    assert format_ticker_option("005930", None) == "005930"


# ---- format_date ------------------------------------------------------


def test_format_date_iso() -> None:
    assert format_date(pd.Timestamp("2024-12-30")) == "2024-12-30"


def test_format_date_kr() -> None:
    assert format_date(pd.Timestamp("2024-12-30"), fmt="kr") == "2024년 12월 30일"


def test_format_date_none() -> None:
    assert format_date(None) == "—"


# ---- lookup_regime_at -------------------------------------------------


def _synthetic_state_series() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range("2020-01-01", periods=10, freq="D"),
            "state_idx": [0, 0, 0, 1, 1, 2, 2, 2, 2, 0],
            "state_label": [
                "위험선호",
                "위험선호",
                "위험선호",
                "중립",
                "중립",
                "위험회피",
                "위험회피",
                "위험회피",
                "위험회피",
                "위험선호",
            ],
        }
    )


def test_lookup_regime_exact() -> None:
    s = _synthetic_state_series()
    assert lookup_regime_at(pd.Timestamp("2020-01-06"), s) == "위험회피"


def test_lookup_regime_between() -> None:
    """*가장 가까운 영업일 ≤ date* — 1/3 (위험선호) 이전 1/4 도 위험선호."""
    s = _synthetic_state_series()
    # 2020-01-04 는 중립 시작일 — 1/4 = 중립
    assert lookup_regime_at(pd.Timestamp("2020-01-04"), s) == "중립"


def test_lookup_regime_before_data() -> None:
    """데이터 시작 전 → None."""
    s = _synthetic_state_series()
    assert lookup_regime_at(pd.Timestamp("2019-12-01"), s) is None


def test_lookup_regime_after_data() -> None:
    """데이터 끝 후 → 마지막 label."""
    s = _synthetic_state_series()
    assert lookup_regime_at(pd.Timestamp("2025-01-01"), s) == "위험선호"


def test_lookup_regime_none_inputs() -> None:
    assert lookup_regime_at(None, _synthetic_state_series()) is None
    assert lookup_regime_at(pd.Timestamp("2020-01-01"), None) is None


# ---- compute_regime_blocks --------------------------------------------


def test_compute_regime_blocks_basic() -> None:
    s = _synthetic_state_series()
    blocks = compute_regime_blocks(s)
    # 위험선호 (1-3) → 중립 (4-5) → 위험회피 (6-9) → 위험선호 (10) = 4 blocks
    assert len(blocks) == 4
    assert list(blocks["label"]) == ["위험선호", "중립", "위험회피", "위험선호"]
    assert blocks.iloc[0]["start"] == pd.Timestamp("2020-01-01")
    assert blocks.iloc[0]["end"] == pd.Timestamp("2020-01-03")


def test_compute_regime_blocks_empty() -> None:
    assert compute_regime_blocks(pd.DataFrame()).empty
    assert compute_regime_blocks(None).empty


# ---- find_close_column ------------------------------------------------


def test_find_close_column_korean() -> None:
    df = pd.DataFrame({"시가": [1], "종가": [2], "거래량": [3]})
    assert find_close_column(df) == "종가"


def test_find_close_column_english() -> None:
    df = pd.DataFrame({"Open": [1], "Close": [2]})
    assert find_close_column(df) == "Close"


def test_find_close_column_none() -> None:
    df = pd.DataFrame({"other": [1]})
    assert find_close_column(df) is None
    assert find_close_column(None) is None
    assert find_close_column(pd.DataFrame()) is None


# ---- find_date_column_or_index ----------------------------------------


def test_find_date_index() -> None:
    df = pd.DataFrame(
        {"종가": [1, 2, 3]},
        index=pd.date_range("2024-01-01", periods=3, freq="D"),
    )
    date_s, df_reset = find_date_column_or_index(df)
    assert date_s is not None
    assert df_reset is not None
    assert len(date_s) == 3
    assert date_s.iloc[0] == pd.Timestamp("2024-01-01")


def test_find_date_column() -> None:
    df = pd.DataFrame({"날짜": pd.date_range("2024-01-01", periods=3), "종가": [1, 2, 3]})
    date_s, _ = find_date_column_or_index(df)
    assert date_s is not None
    assert len(date_s) == 3


def test_find_date_none() -> None:
    s, df = find_date_column_or_index(None)
    assert s is None and df is None


def test_find_date_empty() -> None:
    s, df = find_date_column_or_index(pd.DataFrame())
    assert s is None and df is None
