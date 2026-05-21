"""개요 페이지 — docs/ui_components.md §2.1."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from components.header import render_page_header


def render_overview() -> None:
    """페이지 1: 프로젝트 개요 + 정직성 사슬 5 차원 + 단계 상태 + CTA."""
    render_page_header(
        title="기업 펀더멘털 + 시장 국면 인지형 통합 분석 리포트",
        subtitle="한국 KOSPI200 (point-in-time) 배치 분석",
        value_message=(
            "본 프로젝트는 **negative finding** (모델 random 미만) 을 *정직 박제*하며, "
            "그 자체가 **D2 정직성 사슬 5 차원 + §7.6 검토 사이클** 의 핵심 가치 입증입니다."
        ),
    )

    # === 정직성 사슬 5 차원 ===
    st.markdown("## ★ 정직성 사슬 5 차원")
    chain = [
        ("1. 변수 격리", "§5.5.9 distress 화이트리스트"),
        ("2. 양성 충분성", "§5.5.10 ablation 기각"),
        ("3. 격리 (i)(ii)(iii)", "tests/test_isolation.py"),
        ("4. 시간 누수 차단", "walk-forward + embargo 365"),
        ("5. LLM 격리", "test_app_no_llm_import (CI)"),
    ]
    cols = st.columns(5)
    for col, (title, source) in zip(cols, chain, strict=True):
        with col:
            st.markdown(f"**{title}**")
            st.caption(source)

    st.markdown("---")

    # === 단계별 진행 상태 ===
    st.markdown("## 단계별 진행 상태")
    stage_df = pd.DataFrame(
        [
            ("1. 데이터 셋업", "✅", "universe 321, grid 40, DART/KRX/FDR 캐시"),
            ("2. 펀더멘털 모듈", "✅", "LightGBM + walk-forward (§5.5.17 negative finding)"),
            ("3. 시장 국면 모듈", "✅", "HMM K=3 + GMM/K-Means 비교 + K=4 ablation"),
            ("4. 통합 대시보드", "🔄", "본 대시보드 (Phase 4 구조 개편)"),
            ("5. 마무리", "✅", "README + 정직성 사슬 5 박제"),
        ],
        columns=["단계", "상태", "박제 위치"],
    )
    st.dataframe(stage_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # === CTA — 종목 분석 진입 ===
    st.markdown("### 시작하기")
    cta_col, _spacer = st.columns([1, 2])
    with cta_col:
        if st.button("★ 종목 분석 시작 →", type="primary", use_container_width=True):
            st.session_state["current_page"] = "ticker"
            st.rerun()
    st.caption("종목을 선택해서 위험 점수·국면·재무 비율 통합 확인")

    st.markdown("---")

    # === 핵심 메시지 3 카드 ===
    st.markdown("## 프로젝트 핵심 메시지")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("##### Negative Finding 정직 박제")
        st.caption(
            "PR-AUC 0.0136 < base rate 0.0205. KOSPI200 부실 사건 희소성의 경험적 정량 증거."
        )
    with c2:
        st.markdown("##### K=4 Ablation 정량 정답")
        st.caption(
            "K=3 명명 부합 약함 → K=4 ablation 으로 코로나 위기 27.9% → 82.0% "
            "(3 배 개선) 정량 발견."
        )
    with c3:
        st.markdown("##### §7.6 검토 사이클")
        st.caption(
            "매 작업 4 단계 의무 (PROGRESS·git log·코드 실측·사용자 게이트). "
            "워크플로 자체가 방법론적 특징."
        )
