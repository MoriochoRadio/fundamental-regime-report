"""Warning + EmptyState (docs/ui_components.md §1.8·§1.9)."""

from __future__ import annotations

import streamlit as st

LIMIT_MESSAGES = {
    "ticker": (
        "⚠️ **본 모델은 random 미만 성능** (PR-AUC 0.0136 < base rate 0.0205). "
        "위 위험 확률은 *해석 가이드일 뿐* — 실거래·신용 평가 사용 금지. "
        "자세한 한계는 사이드바 **⚠️ Limitations** 페이지 참조."
    ),
    "regime": (
        "⚠️ 시장 국면은 *과거 데이터 사후 분석* 결과. "
        "*주가 예측 아님* (CLAUDE.md §3.2). 트레이딩 신호 사용 금지."
    ),
    "d2": (
        "⚠️ 본 모델은 **random 미만** 성능. 위 모든 수치는 *모델 자랑*이 아닌 "
        "*KOSPI200 모집단의 부실 사건 희소성* 의 정량 증거입니다. "
        "실거래·신용 평가 사용 금지."
    ),
    "limitations": (
        "ℹ️ 본 페이지는 본 프로젝트의 **방법론적 특징 핵심**. 모든 한계가 *정직 박제* 되어 있습니다."
    ),
}


def render_model_limit_warning(context: str = "ticker") -> None:
    """모델 한계 경고 banner (context 별 문구)."""
    msg = LIMIT_MESSAGES.get(context, LIMIT_MESSAGES["ticker"])
    st.error(msg)


def render_empty_state(
    title: str,
    description: str | None = None,
    action: str | None = None,
    icon: str = "📭",
) -> None:
    """데이터 없음·skipped·산출물 부재 상태 UI."""
    st.markdown(f"### {icon} {title}")
    if description:
        st.caption(description)
    if action:
        st.info(f"💡 {action}")
