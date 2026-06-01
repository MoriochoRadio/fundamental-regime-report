"""시장 상태 페이지 (docs/ui_design.md §1.3).

render() — main.py shell 이 dispatch (page key "state"). PageHeader +
StateStripeChart (색상 stripe) + 위기 시점 안내 + 9개월 정확도 경고.

★ Q2 (A): 위기 시점은 일반 st.info (StateInterpretBox 미사용 — 시장 전용
페이지엔 종목 risk 부재로 state×risk 9 template 이 부적합, docs-구현 조정).
★ Q3 (A): 분석 시작 9개월 정확도 한계 = st.warning (정직 안내, docs §1.3).
ModelLimitBadge 는 main.py shell 전역 호출 (중복 안 함).
"""

from __future__ import annotations

import streamlit as st

from app.components import EmptyState, PageHeader, StateStripeChart
from app.data_loader import load_state_series


def render() -> None:
    """시장 상태 페이지 렌더 — stripe 차트 + 위기 안내 + 9개월 경고."""
    PageHeader(
        "시장 상태 시계열",
        "본 시스템은 한국 KOSPI200 시장의 흐름을 위험회피·중립·위험선호 "
        "3 상태로 분류합니다. 위기 시점이 색상으로 강조됩니다.",
    )

    state_series = load_state_series()
    if state_series is None or state_series.empty:
        EmptyState(
            message="시장 상태 시계열 데이터가 아직 준비되지 않았습니다.",
            suggestion="데이터 파이프라인 생성 후 다시 시도해 주세요.",
        )
        return

    # 색상 stripe 차트 (단위 k StateStripeChart 컴포넌트)
    StateStripeChart(state_series)

    # 위기 시점 안내 (docs §1.3 verbatim, Q2 (A): 일반 info — StateInterpretBox 미사용)
    st.info(
        "위험회피 시장 상태는 안전 자산 선호가 늘어나는 시점입니다. "
        "예: 2020-02~04 코로나 충격 시점, 2022-09~10 금리 충격 시점."
    )

    # 분석 시작 9개월 정확도 한계 (docs §1.3 verbatim, Q3 (A): 정직 경고)
    st.warning(
        "분석 시작 9개월간 (2015-01 ~ 2015-09) 은 시장 상태 분류 정확도가 "
        "낮습니다. 이 기간의 해석은 참고로만 봐 주세요."
    )
