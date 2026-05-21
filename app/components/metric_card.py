"""Metric cards — RiskScoreCard, RegimeCard, LabelCard, FsDivCard.

docs/ui_components.md §1.3·§1.4.
"""

from __future__ import annotations

import streamlit as st
from utils.formatters import classify_risk, format_proba, regime_color


def render_risk_score_card(proba: float | None, class_weight: str) -> None:
    """D2 위험 확률 색상 코딩 표시 (높음/중간/낮음).

    Args:
        proba: 0~1 확률 또는 None (skipped fold).
        class_weight: "balanced" or "unweighted" — caption 표시.
    """
    if proba is None:
        st.metric("D2 위험 확률", "—")
        st.caption("⚠️ 평가 제외 시점 (양성 0 인 fold)")
        return

    level, color = classify_risk(proba)
    st.metric("D2 위험 확률", format_proba(proba))
    st.markdown(
        f"<div style='color:{color}; font-weight:bold; font-size:14px;'>"
        f"● {level} <span style='color:#666; font-weight:normal;'>({class_weight})</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def render_regime_card(regime: str | None) -> None:
    """시장 국면 색상 코딩 표시."""
    if regime is None:
        st.metric("시장 국면", "—")
        st.caption("ℹ️ Warmup 기간 (2015 초반) 또는 시점 외")
        return
    color = regime_color(regime)
    st.metric("시장 국면", regime)
    st.markdown(
        f"<div style='color:{color}; font-weight:bold; font-size:14px;'>● {regime}</div>",
        unsafe_allow_html=True,
    )


def render_label_card(label: int | None) -> None:
    """1년 forward 양성 라벨 (0/1) 표시."""
    if label is None:
        st.metric("1년 forward 양성", "—")
        st.caption("이 시점의 라벨 데이터 없음")
        return
    color = "#d62728" if label == 1 else "#7f7f7f"
    label_text = "양성 (사건 발생)" if label == 1 else "음성"
    st.metric("1년 forward 양성", str(int(label)))
    st.markdown(
        f"<div style='color:{color}; font-weight:bold; font-size:14px;'>● {label_text}</div>",
        unsafe_allow_html=True,
    )


def render_fs_div_card(fs_div: str | None) -> None:
    """재무 출처 (CFS/OFS/absent) badge."""
    if fs_div is None or fs_div == "—":
        st.metric("재무 출처", "—")
        return
    desc = {
        "CFS": "연결재무제표",
        "OFS": "별도재무제표",
        "absent": "보고서 없음",
    }
    st.metric("재무 출처", fs_div)
    if fs_div in desc:
        st.caption(desc[fs_div])
