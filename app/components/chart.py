"""차트 컴포넌트 — PriceChartWithStateOverlay, RatioGrid.

docs/ui_design.md §2.5·§2.6. plotly + cp949 컬럼 자동 식별.

★ 검증 5.1 (Phase 4 TypeError 차단): vline·vrect 의 x 인자에 모두
`.to_pydatetime()` 적용 (pandas Timestamp 산술 회피).

Phase 4 자산 변환:
- (B) 정정: render_price_chart_with_regime → PriceChartWithStateOverlay,
  render_ratio_grid → RatioGrid (검증 1)
- (C) 재사용: find_close_column·compute_state_blocks·state_color·
  find_date_column_or_index (단위 a)
- (D) 의존성 처리: 빈 상태 → EmptyState 위임 (단위 f warning.py 작성 완료,
  Q2 (A) 로 inline st.info 5 곳 교체)
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp
import streamlit as st

from app.components.warning import EmptyState
from app.utils.formatters import state_color
from app.utils.state_mapper import (
    compute_state_blocks,
    find_close_column,
    find_date_column_or_index,
)

# 빈 상태 범례 이모지 (Q4: 단위 d metric_card 일관, 색맹 대응 NFR-7)
_STATE_LEGEND = "🔴 위험회피 · ⚪ 중립 · 🟢 위험선호"


def PriceChartWithStateOverlay(
    ticker: str,
    name: str,
    ohlcv: pd.DataFrame | None,
    state_series: pd.DataFrame | None,
    as_of: pd.Timestamp,
) -> None:
    """주가 line + 시장 상태 배경 overlay + 분석 시점 vline.

    docs/ui_design.md §2.5 spec.

    ★ 검증 5.1: add_vline·add_vrect 의 x 인자에 `.to_pydatetime()` 적용
    (Phase 4 TypeError 차단).

    Args:
        ticker: 종목 코드.
        name: 종목명.
        ohlcv: KRX OHLCV DataFrame (None/empty → 빈 상태 안내).
        state_series: 시장 상태 시계열 (None → overlay 없이 주가만).
        as_of: 분석 시점.
    """
    # 빈 상태 (Q2 (A): EmptyState 위임 — 단위 f warning.py)
    if ohlcv is None or ohlcv.empty:
        EmptyState(
            message=f"{ticker} 의 일간 시세 데이터가 없습니다.",
            suggestion="다른 종목 또는 다른 시점을 선택해 보세요.",
        )
        return

    close_col = find_close_column(ohlcv)
    if close_col is None:
        EmptyState(message="종가 컬럼을 찾지 못했습니다.")
        return

    date_key = find_date_column_or_index(ohlcv)
    if date_key is None:
        EmptyState(message="날짜 정보를 찾지 못했습니다.")
        return

    # Q2 (A): 단위 a find_date_column_or_index 시그너처 (str | "__index__")
    # → chart 내부에서 date series 추출
    if date_key == "__index__":
        date_values = pd.to_datetime(ohlcv.index)
    else:
        date_values = pd.to_datetime(ohlcv[date_key])

    fig = go.Figure()

    # 시장 상태 배경 shading (vrect blocks) — ★ to_pydatetime (검증 5.1)
    if state_series is not None and not state_series.empty:
        blocks = compute_state_blocks(state_series)
        for _, block in blocks.iterrows():
            fig.add_vrect(
                x0=pd.Timestamp(block["start"]).to_pydatetime(),
                x1=pd.Timestamp(block["end"]).to_pydatetime(),
                fillcolor=state_color(block["label"]),
                opacity=0.12,
                line_width=0,
            )

    # 주가 line
    fig.add_trace(
        go.Scatter(
            x=date_values,
            y=ohlcv[close_col],
            mode="lines",
            name="종가",
            line={"color": "#1f77b4", "width": 1.5},
            hovertemplate="%{x|%Y-%m-%d}<br>종가: %{y:,.0f} 원<extra></extra>",
        )
    )

    # 분석 시점 vline + annotation — ★ to_pydatetime (검증 5.1)
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
        title=f"{ticker} {name} 주가 + 시장 상황",
        xaxis_title="날짜",
        yaxis_title="종가 (원)",
        hovermode="x unified",
        height=420,
        margin={"t": 50, "b": 40, "l": 40, "r": 20},
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"배경 색상: {_STATE_LEGEND}. 점선: 선택한 분석 시점.")


def RatioGrid(
    ticker: str,
    ticker_features: pd.DataFrame | None,
    as_of: pd.Timestamp,
) -> None:
    """재무 비율 4 (부채비율·유동비율·영업이익률·ROA) 2×2 추이 차트.

    docs/ui_design.md §2.6 spec. ★ 검증 5.1: vline x 인자 `.to_pydatetime()`.

    Args:
        ticker: 종목 코드.
        ticker_features: 종목별 features 시계열 (None/empty → 빈 상태 안내).
        as_of: 분석 시점.
    """
    if ticker_features is None or ticker_features.empty:
        EmptyState(
            message=f"{ticker} 의 재무 비율 시계열 데이터가 없습니다.",
            suggestion="다른 종목 또는 다른 시점을 선택해 보세요.",
        )
        return
    if "as_of" not in ticker_features.columns:
        EmptyState(message="분석 시점 정보를 찾지 못했습니다.")
        return

    df = ticker_features.sort_values("as_of").copy()
    df["as_of"] = pd.to_datetime(df["as_of"])

    # 일반인 친화 한국어 제목 (검증 4)
    ratio_layout = [
        ("debt_ratio", "부채비율 (부채/자본)", 1, 1),
        ("current_ratio", "유동비율 (유동자산/유동부채)", 1, 2),
        ("op_margin", "영업이익률 (영업이익/매출)", 2, 1),
        ("roa", "총자산이익률 (순이익/자산)", 2, 2),
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
                hovertemplate="%{x|%Y-%m-%d}<br>%{y:.2f}<extra></extra>",
            ),
            row=row_idx,
            col=col_idx,
        )
        # ★ to_pydatetime (검증 5.1)
        fig.add_vline(
            x=as_of_py,
            line_dash="dash",
            line_color="#444",
            row=row_idx,
            col=col_idx,
        )

    fig.update_layout(
        height=520,
        title=f"{ticker} 재무 비율 추이",
        margin={"t": 80, "b": 40, "l": 40, "r": 20},
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("점선: 선택한 분석 시점. 값이 없는 구간은 빈칸으로 표시됩니다.")


def StateStripeChart(state_series: pd.DataFrame | None) -> None:
    """시장 상태 시계열 가로 색 띠 (주가 없음 — docs/ui_design.md §1.3).

    compute_state_blocks 로 연속 상태 구간을 묶어 plotly px.timeline 색 띠로
    렌더. PriceChartWithStateOverlay (주가 + overlay) 와 달리 *순수
    state-over-time* 시각화. None/empty → EmptyState 위임 (단위 e/f 정합).

    Args:
        state_series: 시장 상태 시계열 (columns date·state_label).
    """
    if state_series is None or state_series.empty:
        EmptyState(
            message="시장 상태 시계열 데이터가 없습니다.",
            suggestion="데이터 파이프라인 생성 후 다시 시도해 주세요.",
        )
        return

    blocks = compute_state_blocks(state_series)
    if blocks.empty:
        EmptyState(message="시장 상태 구간을 계산할 수 없습니다.")
        return

    blocks = blocks.copy()
    blocks["축"] = "시장 상태"  # 단일 행 stripe
    color_map = {label: state_color(label) for label in blocks["label"].unique()}
    fig = px.timeline(
        blocks,
        x_start="start",
        x_end="end",
        y="축",
        color="label",
        color_discrete_map=color_map,
    )
    fig.update_yaxes(title="")
    fig.update_layout(
        title="시장 상태 시계열 (색상 = 상태)",
        xaxis_title="기간",
        height=240,
        legend_title="시장 상태",
        margin={"t": 50, "b": 40, "l": 40, "r": 20},
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"색상: {_STATE_LEGEND}.")
