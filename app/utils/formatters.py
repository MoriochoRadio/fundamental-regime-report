"""숫자·문자 포매팅 (한국어 UX) — pure functions.

docs/ui_design.md §2 컴포넌트 spec + §3 UI Copy 매핑.

7 함수 + helper + 상수. 모든 출력 일반인 5 초 이해 (§5 (1) 부속 박제 부합).

Phase 4 자산 변환:
- (C) 그대로 재사용: format_won·format_percent·format_proba·classify_risk·
  _is_missing·RISK_HIGH_THRESHOLD·RISK_MEDIUM_THRESHOLD·RISK_COLORS
- (B) 정정: REGIME_COLORS → STATE_COLORS, regime_color → state_color
  (검증 1 매핑)
- (신규): format_ratio·format_ticker_option·format_date
"""

from __future__ import annotations

import math

import pandas as pd

# === risk classification (RiskScoreCard 색상, 3 단계 docs/ui_design.md §2.3) ===
RISK_HIGH_THRESHOLD = 0.5
RISK_MEDIUM_THRESHOLD = 0.1

RISK_COLORS: dict[str, str] = {
    "높음": "#d62728",
    "중간": "#ff9800",
    "낮음": "#2ca02c",
}

# === state 색상 (2 단계 docs/ux_design.md §4.1, regime → state 정정) ===
STATE_COLORS: dict[str, str] = {
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

    >>> format_won(1_625_000_000_000_000)
    '1,625.00 조원'
    >>> format_won(145_790_000_000_000)
    '145.79 조원'
    >>> format_won(50_000_000_000)
    '500.0 억원'
    >>> format_won(12_345_678)
    '12,345,678 원'
    >>> format_won(None)
    '—'
    >>> format_won(float('nan'))
    '—'
    >>> format_won(float('inf'))
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
    """비율 (0.0 ~ 1.0) → 한국어 percent 표기.

    >>> format_percent(0.1234)
    '12.34%'
    >>> format_percent(0.1234, decimal=1)
    '12.3%'
    >>> format_percent(None)
    '—'
    """
    if _is_missing(value):
        return "—"
    val = float(value)  # type: ignore[arg-type]
    if math.isinf(val) or math.isnan(val):
        return "—"
    return f"{val * 100:.{decimal}f}%"


def format_proba(value: float | None) -> str:
    """확률 (0.0 ~ 1.0) → 4 자리 소수점 표기.

    (참고: UI 차원에서는 일반적으로 format_percent + classify_risk 사용 권장.
    본 함수는 모델 카드·내부 디버깅 차원 4 자리 정밀 표기.)

    >>> format_proba(0.013564)
    '0.0136'
    >>> format_proba(0.5)
    '0.5000'
    >>> format_proba(None)
    '—'
    """
    if _is_missing(value):
        return "—"
    val = float(value)  # type: ignore[arg-type]
    if math.isinf(val) or math.isnan(val):
        return "—"
    return f"{val:.4f}"


def format_ratio(value: float | None, decimal: int = 2) -> str:
    """재무 비율 (배수) → 소수점 표기.

    >>> format_ratio(1.234)
    '1.23'
    >>> format_ratio(1.234, decimal=3)
    '1.234'
    >>> format_ratio(None)
    '—'
    """
    if _is_missing(value):
        return "—"
    val = float(value)  # type: ignore[arg-type]
    if math.isinf(val) or math.isnan(val):
        return "—"
    return f"{val:.{decimal}f}"


def classify_risk(proba: float | None) -> tuple[str, str]:
    """위험 확률 → (label, color hex) 3 단계 분류.

    임계: < 0.1 낮음 / 0.1 ~ 0.5 중간 / >= 0.5 높음.

    >>> classify_risk(0.05)
    ('낮음', '#2ca02c')
    >>> classify_risk(0.3)
    ('중간', '#ff9800')
    >>> classify_risk(0.7)
    ('높음', '#d62728')
    >>> classify_risk(None)
    ('—', '#757575')
    """
    if _is_missing(proba):
        return ("—", "#757575")
    val = float(proba)  # type: ignore[arg-type]
    if math.isinf(val) or math.isnan(val):
        return ("—", "#757575")
    if val >= RISK_HIGH_THRESHOLD:
        return ("높음", RISK_COLORS["높음"])
    if val >= RISK_MEDIUM_THRESHOLD:
        return ("중간", RISK_COLORS["중간"])
    return ("낮음", RISK_COLORS["낮음"])


def state_color(state_label: str | None) -> str:
    """state label → 색상 hex (위험회피·중립·위험선호).

    Phase 4 regime_color 의 정정 (검증 1 매핑).

    >>> state_color("위험회피")
    '#d62728'
    >>> state_color("중립")
    '#7f7f7f'
    >>> state_color("위험선호")
    '#2ca02c'
    >>> state_color(None)
    '#757575'
    >>> state_color("미지정")
    '#757575'
    """
    if state_label is None or state_label not in STATE_COLORS:
        return "#757575"
    return STATE_COLORS[state_label]


def format_ticker_option(code: str, name: str) -> str:
    """종목 옵션 표기 — "코드 종목명".

    docs/ui_design.md §2.2 TickerHeader 매핑.

    >>> format_ticker_option("005930", "삼성전자")
    '005930 삼성전자'
    >>> format_ticker_option("000660", "SK하이닉스")
    '000660 SK하이닉스'
    """
    return f"{code} {name}"


def format_date(date_val: pd.Timestamp | str | None) -> str:
    """날짜 → ISO 8601 ("YYYY-MM-DD") 표기.

    >>> format_date(pd.Timestamp("2024-12-31"))
    '2024-12-31'
    >>> format_date("2024-12-31")
    '2024-12-31'
    >>> format_date(None)
    '—'
    """
    if date_val is None:
        return "—"
    try:
        ts = pd.Timestamp(date_val)
    except (ValueError, TypeError):
        return "—"
    if pd.isna(ts):
        return "—"
    return ts.strftime("%Y-%m-%d")
