"""시장 국면 시계열 페이지 — docs/ui_components.md §2.3."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from components.header import render_page_header
from components.warning import render_empty_state, render_model_limit_warning
from data_loader import load_regime_comparison, load_regime_results, load_regime_state_series
from utils.formatters import REGIME_COLORS


def render_regime_timeline() -> None:
    """시장 국면 시계열 — HMM K=3 + K=4 ablation 비교."""
    render_page_header(
        title="시장 국면 시계열 (HMM K=3)",
        value_message=(
            "KOSPI200 일간 지수 → 3 피처 (수익률·변동성·비율) → HMM 학습 → 3 국면. "
            "*주가 예측 아님* — 국면 분류·맥락만 (CLAUDE.md §3.2)."
        ),
    )

    state_series = load_regime_state_series()
    regime_results = load_regime_results()
    comparison = load_regime_comparison()

    if state_series is None or regime_results is None:
        render_empty_state(
            title="regime 산출물 부재",
            action="`uv run python scripts/train_regime.py` 실행",
            icon="⚠️",
        )
        return

    state_series = state_series.copy()
    state_series["date"] = pd.to_datetime(state_series["date"])

    # === 분포 + 색상 범례 ===
    st.markdown("### 분포")
    dist = state_series["state_label"].value_counts()
    total = int(dist.sum())
    cols = st.columns(len(dist))
    for col, (label, count) in zip(cols, dist.items(), strict=False):
        with col:
            pct = count / total * 100
            color = REGIME_COLORS.get(label, "#888")
            st.metric(label, f"{count:,}", f"{pct:.1f}%")
            st.markdown(
                f"<div style='color:{color}; font-weight:bold; font-size:14px;'>● {label}</div>",
                unsafe_allow_html=True,
            )

    # === 국면 시계열 ===
    st.markdown("### 국면 시계열")
    st.caption(
        f"기간: {state_series['date'].min().date()} ~ {state_series['date'].max().date()} "
        f"({len(state_series):,} obs)"
    )
    fig = px.scatter(
        state_series,
        x="date",
        y="state_label",
        color="state_label",
        color_discrete_map=REGIME_COLORS,
        category_orders={"state_label": ["위험회피", "중립", "위험선호"]},
    )
    fig.update_traces(marker={"size": 4})
    fig.update_layout(
        height=360,
        hovermode="x unified",
        showlegend=False,
        margin={"t": 30, "b": 40, "l": 40, "r": 20},
    )
    st.plotly_chart(fig, use_container_width=True)

    # === 전이 행렬 ===
    st.markdown("### 전이 행렬")
    model_summary = regime_results.get("model_summary", {})
    transmat = model_summary.get("transmat", [])
    state_labels_dict = model_summary.get("state_labels", {})
    if transmat and state_labels_dict:
        labels = [
            state_labels_dict.get(str(k), state_labels_dict.get(k, f"state_{k}")) for k in range(3)
        ]
        transmat_df = pd.DataFrame(transmat, index=labels, columns=labels)
        st.dataframe(transmat_df.style.format("{:.3f}"), use_container_width=True)
        st.caption(
            "자기 지속성 강함 (위험선호 0.976·위험회피 0.997). 중립이 위험회피로 전환 자주 (0.925)."
        )

    st.markdown("---")

    # === K=4 Ablation 비교 (★ 본 프로젝트 핵심 발견) ===
    st.markdown("## ★ K=4 Ablation 정량 정답 발견")
    st.info(
        "단계 3 본 라인 K=3 의 *명명 부합 약함* (위험회피 코로나 27.9%) → "
        "K=4 ablation 으로 위험회피 **82.0%** (3 배 개선) 정량 발견. "
        "*진단 → 가설 → ablation → 정답* 완성형 과학 사이클 박제."
    )
    if comparison:
        k_range = comparison.get("k_range_comparison", [])
        if k_range:
            cmp_df = pd.DataFrame(k_range)
            hmm_only = cmp_df[cmp_df["model"] == "HMM"][["K", "log_lik", "bic", "aic"]]
            st.markdown("##### HMM K=2·3·4 BIC·AIC 비교 (자동 선택 K=4)")
            st.dataframe(
                hmm_only.style.format({"log_lik": "{:.2f}", "bic": "{:.2f}", "aic": "{:.2f}"}),
                use_container_width=True,
                hide_index=True,
            )

    # === 코로나 spot-check 비교 ===
    st.markdown("##### 2020 코로나 (2020-02-15 ~ 2020-05-15) 위기 국면 비중")
    spot = pd.DataFrame(
        [
            ("K=3 (본 라인)", 27.9, "학술 부합 약함"),
            ("K=4 (ablation)", 82.0, "학술 부합 강함"),
        ],
        columns=["설정", "위기 국면 %", "도메인 해석"],
    )
    bar = go.Figure(
        go.Bar(
            x=spot["설정"],
            y=spot["위기 국면 %"],
            text=spot["위기 국면 %"].map(lambda v: f"{v:.1f}%"),
            textposition="outside",
            marker_color=["#7f7f7f", "#d62728"],
        )
    )
    bar.update_layout(
        yaxis_title="위기 국면 (state_2) 비중 (%)",
        yaxis_range=[0, 100],
        height=340,
        margin={"t": 30, "b": 60, "l": 60, "r": 20},
    )
    st.plotly_chart(bar, use_container_width=True)
    st.caption("→ K=4 가 학술 명명·도메인 정의 *압도적 부합*. 본 라인 K=3 유지 (학술 관행).")

    st.markdown("---")
    render_model_limit_warning(context="regime")
