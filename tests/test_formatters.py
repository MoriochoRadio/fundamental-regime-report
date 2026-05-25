"""app/utils/formatters.py 단위 테스트.

단계 5 단위 (a) 산출물. 검증 7 (에러 7 단위 테스트) + 검증 4 (§5 (1) 부속
박제 UI 차원 적용) 매핑.

Phase 4 tests/test_app_utils.py 자산 변환:
- (C) 그대로 재사용 (format_won·format_percent·format_proba 등)
- (B) 정정 (regime_color → state_color)
"""

from __future__ import annotations

import math

import pytest

from app.utils.formatters import (
    RISK_COLORS,
    RISK_HIGH_THRESHOLD,
    RISK_MEDIUM_THRESHOLD,
    STATE_COLORS,
    classify_risk,
    format_date,
    format_percent,
    format_proba,
    format_ratio,
    format_ticker_option,
    format_won,
    state_color,
)

# ---- format_won --------------------------------------------------------


def test_format_won_jo() -> None:
    assert format_won(1_625_000_000_000_000) == "1,625.00 조원"


def test_format_won_jo_decimal() -> None:
    assert format_won(145_790_000_000_000) == "145.79 조원"


def test_format_won_eok() -> None:
    assert format_won(50_000_000_000) == "500.0 억원"


def test_format_won_won() -> None:
    assert format_won(12_345_678) == "12,345,678 원"


def test_format_won_negative_jo() -> None:
    assert format_won(-1_625_000_000_000_000) == "-1,625.00 조원"


def test_format_won_zero() -> None:
    assert format_won(0) == "0 원"


def test_format_won_none() -> None:
    assert format_won(None) == "—"


def test_format_won_nan() -> None:
    assert format_won(float("nan")) == "—"


def test_format_won_inf() -> None:
    assert format_won(float("inf")) == "—"


def test_format_won_neg_inf() -> None:
    assert format_won(float("-inf")) == "—"


# ---- format_percent ----------------------------------------------------


def test_format_percent_basic() -> None:
    assert format_percent(0.1234) == "12.34%"


def test_format_percent_decimal_1() -> None:
    assert format_percent(0.1234, decimal=1) == "12.3%"


def test_format_percent_decimal_0() -> None:
    assert format_percent(0.1234, decimal=0) == "12%"


def test_format_percent_none() -> None:
    assert format_percent(None) == "—"


def test_format_percent_nan() -> None:
    assert format_percent(float("nan")) == "—"


def test_format_percent_zero() -> None:
    assert format_percent(0.0) == "0.00%"


def test_format_percent_one() -> None:
    assert format_percent(1.0) == "100.00%"


# ---- format_proba ------------------------------------------------------


def test_format_proba_4_decimals() -> None:
    assert format_proba(0.013564) == "0.0136"


def test_format_proba_half() -> None:
    assert format_proba(0.5) == "0.5000"


def test_format_proba_zero() -> None:
    assert format_proba(0.0) == "0.0000"


def test_format_proba_one() -> None:
    assert format_proba(1.0) == "1.0000"


def test_format_proba_none() -> None:
    assert format_proba(None) == "—"


def test_format_proba_nan() -> None:
    assert format_proba(float("nan")) == "—"


# ---- format_ratio ------------------------------------------------------


def test_format_ratio_basic() -> None:
    assert format_ratio(1.234) == "1.23"


def test_format_ratio_decimal_3() -> None:
    assert format_ratio(1.2345, decimal=3) == "1.234"


def test_format_ratio_zero() -> None:
    assert format_ratio(0.0) == "0.00"


def test_format_ratio_negative() -> None:
    assert format_ratio(-1.5) == "-1.50"


def test_format_ratio_none() -> None:
    assert format_ratio(None) == "—"


def test_format_ratio_nan() -> None:
    assert format_ratio(float("nan")) == "—"


# ---- classify_risk -----------------------------------------------------


def test_classify_risk_low() -> None:
    label, color = classify_risk(0.05)
    assert label == "낮음"
    assert color == RISK_COLORS["낮음"]


def test_classify_risk_medium_lower_boundary() -> None:
    label, color = classify_risk(RISK_MEDIUM_THRESHOLD)
    assert label == "중간"
    assert color == RISK_COLORS["중간"]


def test_classify_risk_medium() -> None:
    label, color = classify_risk(0.3)
    assert label == "중간"
    assert color == RISK_COLORS["중간"]


def test_classify_risk_high_boundary() -> None:
    label, color = classify_risk(RISK_HIGH_THRESHOLD)
    assert label == "높음"
    assert color == RISK_COLORS["높음"]


def test_classify_risk_high() -> None:
    label, color = classify_risk(0.7)
    assert label == "높음"
    assert color == RISK_COLORS["높음"]


def test_classify_risk_none() -> None:
    label, color = classify_risk(None)
    assert label == "—"
    assert color == "#757575"


def test_classify_risk_nan() -> None:
    label, color = classify_risk(float("nan"))
    assert label == "—"
    assert color == "#757575"


# ---- state_color (Phase 4 regime_color 정정) --------------------------


def test_state_color_risk_off() -> None:
    assert state_color("위험회피") == "#d62728"


def test_state_color_neutral() -> None:
    assert state_color("중립") == "#7f7f7f"


def test_state_color_risk_on() -> None:
    assert state_color("위험선호") == "#2ca02c"


def test_state_color_none() -> None:
    assert state_color(None) == "#757575"


def test_state_color_unknown_label() -> None:
    assert state_color("미지정") == "#757575"


def test_state_colors_constant_3_keys() -> None:
    """STATE_COLORS = 위험회피·중립·위험선호 3 키."""
    assert set(STATE_COLORS.keys()) == {"위험회피", "중립", "위험선호"}


# ---- format_ticker_option ---------------------------------------------


def test_format_ticker_option_samsung() -> None:
    assert format_ticker_option("005930", "삼성전자") == "005930 삼성전자"


def test_format_ticker_option_sk_hynix() -> None:
    assert format_ticker_option("000660", "SK하이닉스") == "000660 SK하이닉스"


# ---- format_date -------------------------------------------------------


def test_format_date_timestamp() -> None:
    import pandas as pd

    assert format_date(pd.Timestamp("2024-12-31")) == "2024-12-31"


def test_format_date_string() -> None:
    assert format_date("2024-12-31") == "2024-12-31"


def test_format_date_none() -> None:
    assert format_date(None) == "—"


def test_format_date_invalid() -> None:
    assert format_date("not-a-date") == "—"


def test_format_date_nat() -> None:
    import pandas as pd

    assert format_date(pd.NaT) == "—"


# ---- 본질 박제 점검 (§5 (1) 부속 박제) --------------------------------


def test_no_ml_terms_in_classify_risk_output() -> None:
    """classify_risk 출력 label 이 ML 용어 노출 0 (§5 (1) 부속 박제)."""
    labels = {classify_risk(p)[0] for p in [0.05, 0.3, 0.7, None]}
    # 일반인 친화 라벨만
    assert labels == {"낮음", "중간", "높음", "—"}


def test_no_ml_terms_in_state_colors() -> None:
    """STATE_COLORS 키가 ML 용어 노출 0 (§5 (1) 부속 박제)."""
    forbidden = {"regime", "risk_off", "risk_on", "neutral"}
    keys_lower = {k.lower() for k in STATE_COLORS}
    assert keys_lower.isdisjoint(forbidden)


# ---- 상수 정합성 -------------------------------------------------------


def test_risk_thresholds_ordered() -> None:
    """위험 임계가 단조 증가."""
    assert math.isclose(RISK_MEDIUM_THRESHOLD, 0.1)
    assert math.isclose(RISK_HIGH_THRESHOLD, 0.5)
    assert RISK_MEDIUM_THRESHOLD < RISK_HIGH_THRESHOLD


def test_risk_colors_keys() -> None:
    """RISK_COLORS = 낮음·중간·높음 3 키."""
    assert set(RISK_COLORS.keys()) == {"낮음", "중간", "높음"}


# ---- pytest doctest collection (Phase 4 자산 — doctest 보존) ----------


def test_doctest_format_won() -> None:
    """format_won doctest 통과 검증."""
    import doctest

    from app.utils import formatters

    results = doctest.testmod(formatters, verbose=False)
    assert results.failed == 0, f"{results.failed} doctest failures"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0.0, "낮음"),
        (0.05, "낮음"),
        (0.0999, "낮음"),
        (0.1, "중간"),
        (0.3, "중간"),
        (0.4999, "중간"),
        (0.5, "높음"),
        (0.99, "높음"),
        (1.0, "높음"),
    ],
)
def test_classify_risk_boundaries(value: float, expected: str) -> None:
    """classify_risk 경계 매트릭스."""
    label, _ = classify_risk(value)
    assert label == expected
