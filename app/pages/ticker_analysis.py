"""종목 분석 페이지 (docs/ui_design.md §1.2) — 프로젝트 정체성 핵심.

render() — main.py shell 이 dispatch. 7 컴포넌트 조립:
사이드바 selector → TickerHeader → RiskScoreCard + StateCard →
StateInterpretBox → PriceChartWithStateOverlay → RatioGrid → EmptyState.

★ Q1 (A): class_weight ablation selector 제거 (ML jargon) — balanced 내부 고정.
★ Q2 (A): 개요 카드 클릭 라우팅 미구현 — 사이드바 selector 가 네비 수단.
★ Q3 (A): state-at-as_of = app/utils/state_mapper.lookup_state_at 재사용.
★ CLAUDE.md §3.4: llm_text 는 빌드타임 배치 산출물 입력만 (런타임 LLM 0회,
현 stub → None → StateInterpretBox template-only).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components import (
    EmptyState,
    PriceChartWithStateOverlay,
    RatioGrid,
    RiskScoreCard,
    StateCard,
    StateInterpretBox,
    TickerHeader,
)
from app.data_loader import (
    load_as_of_grid,
    load_d2_features,
    load_d2_predictions,
    load_llm_interpretation,
    load_ohlcv,
    load_state_series,
    load_universe,
)
from app.utils.formatters import classify_risk, format_ticker_option
from app.utils.state_mapper import lookup_state_at

# Q1 (A): 예측 조회 class_weight 내부 고정 (ablation selector 미노출)
_CLASS_WEIGHT = "balanced"


def _lookup_proba(
    preds: pd.DataFrame | None,
    ticker: str,
    as_of: pd.Timestamp | None,
) -> float | None:
    """predictions 에서 (ticker, as_of, balanced) 의 proba 조회 (없으면 None)."""
    if preds is None or preds.empty or as_of is None:
        return None
    sel = preds[(preds["ticker"] == ticker) & (preds["test_as_of"] == as_of)]
    if "class_weight" in sel.columns:
        sel = sel[sel["class_weight"] == _CLASS_WEIGHT]
    if sel.empty:
        return None
    return float(sel.iloc[0]["proba"])


def render() -> None:
    """종목 분석 페이지 렌더 — 7 컴포넌트 조립 (docs §1.2)."""
    universe = load_universe()
    feats_all = load_d2_features()

    # 데이터 없음 → 상단 EmptyState (단위 f 컴포넌트)
    if universe.empty or feats_all is None or feats_all.empty:
        EmptyState(
            message="종목 분석에 필요한 산출물이 아직 준비되지 않았습니다.",
            suggestion="데이터 파이프라인 생성 후 다시 시도해 주세요.",
        )
        return

    name_map: dict[str, str] = dict(zip(universe["ticker"], universe["name"], strict=False))
    marcap_map: dict[str, float] = dict(zip(universe["ticker"], universe["marcap"], strict=False))

    # === 1. 사이드바 selector (종목 / 분석 시점) ===
    tickers = sorted(name_map.keys())
    ticker = st.sidebar.selectbox(
        "종목 선택",
        tickers,
        format_func=lambda t: format_ticker_option(t, name_map.get(t, "")),
    )
    grid = load_as_of_grid()
    as_of: pd.Timestamp | None = None
    if grid:
        as_of = st.sidebar.selectbox(
            "분석 시점",
            grid[::-1],  # 최신부터
            format_func=lambda d: pd.Timestamp(d).strftime("%Y-%m-%d"),
        )

    # === 2. 헤더 ===
    TickerHeader(ticker, name_map.get(ticker, ticker), marcap_map.get(ticker))

    # === 3. 위험 점수 + 시장 상태 카드 ===
    preds_all = load_d2_predictions()
    state_series = load_state_series()
    proba = _lookup_proba(preds_all, ticker, as_of)
    state = lookup_state_at(as_of, state_series)

    col1, col2 = st.columns(2)
    with col1:
        RiskScoreCard(proba)
    with col2:
        StateCard(state)

    # === 4. 시장 상태 조건부 해석 (프로젝트 정체성) ===
    risk_level, _ = classify_risk(proba)
    llm_text: str | None = None
    if as_of is not None:
        interp = load_llm_interpretation(ticker, pd.Timestamp(as_of).strftime("%Y-%m-%d"))
        if isinstance(interp, dict):
            llm_text = interp.get("text")
    StateInterpretBox(state, risk_level, llm_text)

    # === 5. 주가 + 시장 상태 overlay ===
    ohlcv = load_ohlcv(ticker)
    PriceChartWithStateOverlay(ticker, name_map.get(ticker, ""), ohlcv, state_series, as_of)

    # === 6. 재무 비율 추이 ===
    ticker_feats = feats_all[feats_all["ticker"] == ticker]
    RatioGrid(ticker, ticker_feats, as_of)
