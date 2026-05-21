"""차트 컴포넌트 — PriceChartWithRegime, RatioGrid.

docs/ui_components.md §1.5·§1.6. plotly + cp949 컬럼 자동 식별.
§5.9 학습: vline 의 x 인자에 .to_pydatetime() 적용 (Timestamp 산술 회피).
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
import streamlit as st
from utils.formatters import regime_color
from utils.regime_mapper import (
    compute_regime_blocks,
    find_close_column,
    find_date_column_or_index,
)

from .warning import render_empty_state


def render_price_chart_with_regime(
    ticker: str,
    name: str,
    ohlcv: pd.DataFrame | None,
    state_series: pd.DataFrame | None,
    as_of: pd.Timestamp,
) -> None:
    """주가 line + regime 배경 색상 overlay + 분석 시점 vline."""
    if ohlcv is None or ohlcv.empty:
        render_empty_state(
            title="일간 시세 데이터 없음",
            description=f"{ticker} 의 KRX OHLCV 캐시가 없습니다.",
            action="`scripts/collect_data.py --tickers {ticker}` 실행",
        )
        return

    close_col = find_close_column(ohlcv)
    if close_col is None:
        render_empty_state(
            title="종가 컬럼 식별 실패",
            description=f"OHLCV 컬럼: {', '.join(map(str, ohlcv.columns))}",
        )
        return

    date_series, df_reset = find_date_column_or_index(ohlcv)
    if date_series is None or df_reset is None:
        render_empty_state(title="날짜 컬럼 식별 실패")
        return

    fig = go.Figure()

    # state background shading (vrect blocks)
    if state_series is not None and not state_series.empty:
        blocks = compute_regime_blocks(state_series)
        for _, block in blocks.iterrows():
            fig.add_vrect(
                x0=pd.Timestamp(block["start"]).to_pydatetime(),
                x1=pd.Timestamp(block["end"]).to_pydatetime(),
                fillcolor=regime_color(block["label"]),
                opacity=0.12,
                line_width=0,
            )

    # 주가 line
    fig.add_trace(
        go.Scatter(
            x=date_series,
            y=df_reset[close_col],
            mode="lines",
            name="종가",
            line={"color": "#1f77b4", "width": 1.5},
            hovertemplate="%{x|%Y-%m-%d}<br>종가: %{y:,.0f} 원<extra></extra>",
        )
    )

    # 분석 시점 vline + annotation (§5.9 학습: to_pydatetime 필수)
    as_of_py = pd.Timestamp(as_of).to_pydatetime()
    fig.add_vline(x=as_of_py, line_dash="dash", line_color="#444")
    fig.add_annotation(
        x=as_of_py,
        y=1,
        yref="paper",
        text=f"분석 시점 {pd.Timestamp(as_of).strftime('%Y-%m-%d')}",
        showarrow=False,
        yanchor="bottom",
        font={"size": 11, "color": "#444"},
    )

    fig.update_layout(
        title=f"{ticker} {name} 종가 + 시장 국면 overlay",
        xaxis_title="날짜",
        yaxis_title="종가 (원)",
        hovermode="x unified",
        height=420,
        margin={"t": 50, "b": 40, "l": 40, "r": 20},
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "배경: 🔴 위험회피 · ⚪ 중립 · 🟢 위험선호 (alpha 0.12). 점선: 사용자 선택 분석 시점."
    )


def render_ratio_grid(
    ticker: str,
    ticker_features: pd.DataFrame | None,
    as_of: pd.Timestamp,
) -> None:
    """재무 비율 4 (debt_ratio·current_ratio·op_margin·roa) 2x2 subplot."""
    if ticker_features is None or ticker_features.empty:
        render_empty_state(
            title="재무 비율 시계열 데이터 없음",
            description=f"{ticker} 의 features 시계열을 찾을 수 없습니다.",
            action="`scripts/train_d2_baseline.py` 실행",
        )
        return

    df = ticker_features.sort_values("as_of").copy()
    if "as_of" not in df.columns:
        render_empty_state(title="as_of 컬럼 없음")
        return
    df["as_of"] = pd.to_datetime(df["as_of"])

    ratio_layout = [
        ("debt_ratio", "부채비율 (부채총계/자본총계)", 1, 1),
        ("current_ratio", "유동비율 (유동자산/유동부채)", 1, 2),
        ("op_margin", "영업이익률 (영업이익/매출액)", 2, 1),
        ("roa", "ROA (당기순이익/자산총계)", 2, 2),
    ]

    titles = [layout[1] for layout in ratio_layout]
    fig = sp.make_subplots(rows=2, cols=2, subplot_titles=titles)

    as_of_py = pd.Timestamp(as_of).to_pydatetime()

    for col, _title, row_idx, col_idx in ratio_layout:
        if col not in df.columns:
            continue
        fig.add_trace(
            go.Scatter(
                x=df["as_of"],
                y=df[col],
                mode="lines+markers",
                name=col,
                showlegend=False,
                marker={"size": 5},
                line={"width": 1.5},
                hovertemplate="%{x|%Y-%m-%d}<br>" + col + ": %{y:.4f}<extra></extra>",
            ),
            row=row_idx,
            col=col_idx,
        )
        fig.add_vline(
            x=as_of_py,
            line_dash="dash",
            line_color="#444",
            row=row_idx,
            col=col_idx,
        )

    fig.update_layout(
        height=520,
        title=f"{ticker} 재무 비율 4 추이 (28 분기말)",
        margin={"t": 80, "b": 40, "l": 40, "r": 20},
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("점선: 사용자 선택 분석 시점. 분모 0 또는 결측 시 NaN (차트 gap).")
