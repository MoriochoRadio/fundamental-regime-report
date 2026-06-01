"""app/utils — pure functions (formatters + state_mapper).

단계 5 단위 (a) 산출물.
- docs/ui_design.md §2 컴포넌트 spec 의 utility 함수 명세
- docs/tech_architecture.md §2 폴더 구조 매핑

pure functions: 의존성 0 (pandas 외). 단위 테스트 용이.
"""

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
from app.utils.state_mapper import (
    compute_state_blocks,
    find_close_column,
    find_date_column_or_index,
    lookup_state_at,
)

__all__ = [
    "RISK_COLORS",
    "RISK_HIGH_THRESHOLD",
    "RISK_MEDIUM_THRESHOLD",
    "STATE_COLORS",
    "classify_risk",
    "compute_state_blocks",
    "find_close_column",
    "find_date_column_or_index",
    "format_date",
    "format_percent",
    "format_proba",
    "format_ratio",
    "format_ticker_option",
    "format_won",
    "lookup_state_at",
    "state_color",
]
