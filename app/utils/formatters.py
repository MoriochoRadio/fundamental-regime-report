"""숫자·문자 포매팅 (한국어 UX) — docs/ui_components.md §4.

pure functions, 테스트 용이.
"""

from __future__ import annotations

import math
from typing import Literal

import pandas as pd

# === risk classification (RiskScoreCard 색상) — docs §1.3 ===
RISK_HIGH_THRESHOLD = 0.5
RISK_MEDIUM_THRESHOLD = 0.1

RISK_COLORS = {
    "높음": "#d62728",
    "중간": "#ff9800",
    "낮음": "#2ca02c",
}

# regime 색상 (디자인 시스템 §7.1)
REGIME_COLORS = {
    "위험회피": "#d62728",
    "중립": "#7f7f7f",
    "위험선호": "#2ca02c",
}


def _is_missing(value: object) -> bool:
    """None·NaN·pd.NA 통합 체크."""
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def format_won(value: float | None) -> str:
    """원 단위 → 조/억 한국어 표기.

    >>> format_won(1_625_265_453_024_000)
    '1,625.27 조원'
    >>> format_won(145_790_847_585_100)
    '145.79 조원'
    >>> format_won(50_000_000_000)
    '500.0 억원'
    >>> format_won(None)
    '—'
    """
    if _is_missing(value):
        return "—"
    val = float(value)  # type: ignore[arg-type]
    if math.isinf(val) or math.isnan(val):
        return "—"
    if abs(val) >= 1e12:
        return f"{val / 1e12:,.2f} 조원"
    if abs(val) >= 1e8:
        return f"{val / 1e8:,.1f} 억원"
    return f"{val:,.0f} 원"


def format_percent(value: float | None, decimal: int = 2) -> str:
    """0~1 ratio → "12.50%". None/NaN → "—"."""
    if _is_missing(value):
        return "—"
    val = float(value)  # type: ignore[arg-type]
    if math.isinf(val) or math.isnan(val):
        return "—"
    return f"{val * 100:.{decimal}f}%"


def format_proba(value: float | None, decimal: int = 4) -> str:
    """확률 0~1 → "0.0136" 또는 "—"."""
    if _is_missing(value):
        return "—"
    val = float(value)  # type: ignore[arg-type]
    if math.isinf(val) or math.isnan(val):
        return "—"
    return f"{val:.{decimal}f}"


def format_ratio(value: float | None, decimal: int = 4) -> str:
    """재무 비율 4 자리 소수. None/NaN → "—"."""
    return format_proba(value, decimal)


def classify_risk(proba: float | None) -> tuple[str, str]:
    """위험 확률 → (label, hex color). docs §1.3 매핑.

    >>> classify_risk(0.7)
    ('높음', '#d62728')
    >>> classify_risk(0.2)
    ('중간', '#ff9800')
    >>> classify_risk(0.05)
    ('낮음', '#2ca02c')
    >>> classify_risk(None)
    ('—', '#888888')
    """
    if _is_missing(proba):
        return ("—", "#888888")
    val = float(proba)  # type: ignore[arg-type]
    if math.isnan(val) or math.isinf(val):
        return ("—", "#888888")
    if val >= RISK_HIGH_THRESHOLD:
        return ("높음", RISK_COLORS["높음"])
    if val >= RISK_MEDIUM_THRESHOLD:
        return ("중간", RISK_COLORS["중간"])
    return ("낮음", RISK_COLORS["낮음"])


def regime_color(regime: str | None) -> str:
    """regime label → hex. 미식별 → 회색."""
    if regime is None:
        return "#888888"
    return REGIME_COLORS.get(regime, "#888888")


def format_ticker_option(ticker: str, name: str | None) -> str:
    """selectbox 표시용. "005930 삼성전자" 형식."""
    if name:
        return f"{ticker} {name}"
    return ticker


def format_date(value: pd.Timestamp | None, fmt: Literal["iso", "kr"] = "iso") -> str:
    """날짜 → ISO 8601 또는 한국어 표기.

    >>> import pandas as pd
    >>> format_date(pd.Timestamp("2024-12-30"))
    '2024-12-30'
    >>> format_date(pd.Timestamp("2024-12-30"), "kr")
    '2024년 12월 30일'
    """
    if value is None or pd.isna(value):
        return "—"
    ts = pd.Timestamp(value)
    if fmt == "kr":
        return f"{ts.year}년 {ts.month}월 {ts.day}일"
    return ts.strftime("%Y-%m-%d")
