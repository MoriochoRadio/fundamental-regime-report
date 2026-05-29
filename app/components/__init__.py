"""app/components — Streamlit UI 컴포넌트 (pure 렌더링 함수).

단계 5 단위 (c)~ 산출물. docs/ui_design.md §2 컴포넌트 spec 매핑.

각 컴포넌트는 *pure 렌더링 함수* (st.* 직접 호출, 반환 None).
data layer (app/data_loader.py) 와 utility (app/utils/) 와 분리 (검증 6).
"""

from app.components.chart import PriceChartWithStateOverlay, RatioGrid
from app.components.header import PageHeader, TickerHeader
from app.components.interpretation import StateInterpretBox
from app.components.metric_card import RiskScoreCard, StateCard
from app.components.warning import EmptyState, ModelLimitBadge

__all__ = [
    "EmptyState",
    "ModelLimitBadge",
    "PageHeader",
    "PriceChartWithStateOverlay",
    "RatioGrid",
    "RiskScoreCard",
    "StateCard",
    "StateInterpretBox",
    "TickerHeader",
]
