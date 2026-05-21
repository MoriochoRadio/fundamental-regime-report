"""★ 종목 분석 페이지 — docs/ui_components.md §2.2 (메인 가치)."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from components.chart import render_price_chart_with_regime, render_ratio_grid
from components.header import render_page_header, render_ticker_header
from components.interpretation import render_regime_conditional_box
from components.metric_card import (
    render_fs_div_card,
    render_label_card,
    render_regime_card,
    render_risk_score_card,
)
from components.warning import render_empty_state, render_model_limit_warning
from data_loader import (
    load_as_of_grid,
    load_features_timeseries,
    load_predictions,
    load_regime_state_series,
    load_ticker_marcap_map,
    load_ticker_name_map,
    load_ticker_ohlcv,
)
from utils.formatters import format_ticker_option
from utils.regime_mapper import lookup_regime_at


def _format_as_of_label(d: pd.Timestamp, skipped_set: set[pd.Timestamp]) -> str:
    """selectbox 표시용 — skipped fold 는 ⚠️ 마크."""
    ts = pd.Timestamp(d)
    label = ts.strftime("%Y-%m-%d")
    if ts in skipped_set:
        return f"{label} ⚠️ 평가 제외"
    return label


def render_ticker_analysis() -> None:
    """★ 종목 분석 페이지 — CLAUDE.md §2 통합 리포트."""
    render_page_header(
        title="★ 종목 분석",
        value_message=(
            "종목을 선택해서 *위험 점수 + 시장 국면 + 재무 비율* 통합 리포트를 확인하세요. "
            "본 모델은 *random 미만 성능* 이라 *해석 가이드만* 으로 사용하세요."
        ),
    )

    # === 데이터 로드 ===
    name_map = load_ticker_name_map()
    feats_all = load_features_timeseries()
    preds_all = load_predictions()
    grid = load_as_of_grid()

    if not name_map or feats_all is None or feats_all.empty:
        render_empty_state(
            title="산출물이 없습니다",
            description="`predictions.parquet` 또는 `features.parquet` 부재.",
            action="`uv run python scripts/train_d2_baseline.py` 실행 후 페이지 새로고침",
            icon="⚠️",
        )
        return

    # === 사이드바: 종목·시점·ablation ===
    st.sidebar.markdown("### 종목 분석 옵션")

    tickers = sorted(name_map.keys())
    ticker = st.sidebar.selectbox(
        "🔍 종목 선택",
        tickers,
        format_func=lambda t: format_ticker_option(t, name_map.get(t)),
        help="검색 가능 — 종목코드 또는 종목명 입력",
    )

    # skipped fold 시점 set (predictions 에 없는 grid 시점)
    if preds_all is not None and not preds_all.empty:
        evaluated_set = set(pd.to_datetime(preds_all["test_as_of"].unique()))
    else:
        evaluated_set = set()
    skipped_set = set(grid) - evaluated_set

    as_of = st.sidebar.selectbox(
        "📅 분석 시점",
        grid[::-1] if grid else [pd.Timestamp.now()],
        format_func=lambda d: _format_as_of_label(d, skipped_set),
        help="⚠️ 마크는 양성 0 으로 평가 제외된 fold",
    )

    cw = st.sidebar.radio(
        "⚖️ class_weight",
        ["balanced", "unweighted"],
        help="balanced=양성 가중치 보정. unweighted=보정 없음 (ablation).",
    )

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "💡 추천 종목: \n"
        "- `005930` 삼성전자 (음성)\n"
        "- `034730` SK (양성·지주)\n"
        "- `035250` 강원랜드 (양성·코로나)\n"
        "- `051310` 포스코플랜텍 (상폐 부실)"
    )

    # === 종목 헤더 ===
    marcap_map = load_ticker_marcap_map()
    name = name_map.get(ticker, "—")

    # ticker × as_of features lookup
    feat_row = None
    sel_f = feats_all[(feats_all["ticker"] == ticker) & (feats_all["as_of"] == as_of)]
    if not sel_f.empty:
        feat_row = sel_f.iloc[0]
    fs_div = str(feat_row["fs_div"]) if feat_row is not None and "fs_div" in feat_row else None

    render_ticker_header(
        ticker=ticker,
        name=name,
        marcap=marcap_map.get(ticker),
        fs_div=fs_div,
    )

    st.markdown("---")

    # === 핵심 지표 4 ===
    st.markdown("### 핵심 지표")

    pred_row = None
    if preds_all is not None:
        sel_p = preds_all[
            (preds_all["ticker"] == ticker)
            & (preds_all["test_as_of"] == as_of)
            & (preds_all["class_weight"] == cw)
        ]
        if not sel_p.empty:
            pred_row = sel_p.iloc[0]

    regime_label = lookup_regime_at(as_of, load_regime_state_series())
    label_value = int(feat_row["label"]) if feat_row is not None and "label" in feat_row else None

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_risk_score_card(
            proba=float(pred_row["proba"]) if pred_row is not None else None,
            class_weight=cw,
        )
    with c2:
        render_regime_card(regime_label)
    with c3:
        render_label_card(label_value)
    with c4:
        render_fs_div_card(fs_div)

    st.markdown("---")

    # === 국면 조건부 해석 ===
    st.markdown("### 국면 조건부 해석")
    render_regime_conditional_box(
        regime=regime_label,
        ticker_features=feat_row,
        ticker_name=name,
    )

    st.markdown("---")

    # === 주가 + state overlay ===
    st.markdown("### 주가 + 시장 국면 overlay")
    ohlcv = load_ticker_ohlcv(ticker)
    render_price_chart_with_regime(
        ticker=ticker,
        name=name,
        ohlcv=ohlcv,
        state_series=load_regime_state_series(),
        as_of=as_of,
    )

    st.markdown("---")

    # === 재무 비율 추이 ===
    st.markdown("### 재무 비율 추이")
    ticker_feats = feats_all[feats_all["ticker"] == ticker]
    render_ratio_grid(ticker=ticker, ticker_features=ticker_feats, as_of=as_of)

    st.markdown("---")

    # === 한계 경고 ===
    render_model_limit_warning(context="ticker")
