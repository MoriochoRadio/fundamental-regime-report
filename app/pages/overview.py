"""개요 페이지 (docs/ui_design.md §1.1).

render() — st.navigation(v2) 의 default Page. 소개 + 예시 종목 카드(테두리
컨테이너 + 위험/상태 badge 미리보기, U3) + 메뉴 둘러보기 + CTA.
ModelLimitBadge 는 main.py shell 에서 전역 호출 (중복 없음).

U1 개편: CTA 클릭 → st.switch_page(ticker_page()) 진짜 이동 (페이지 정체성
= url_path 해시, 레지스트리 동일 정의 — app/components/navigation.py).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.components import PageHeader
from app.components.navigation import ticker_page
from app.data_loader import load_d2_predictions, load_state_series, load_universe
from app.utils.formatters import classify_risk
from app.utils.state_mapper import lookup_state_at
from app.utils.theme import BADGE_COLOR_MAP

# 예시 종목 (docs §1.1): 삼성전자 · SK하이닉스 · SK
_EXAMPLE_TICKERS = ["005930", "000660", "034730"]


def _latest_eval(preds: pd.DataFrame | None, ticker: str) -> tuple[pd.Timestamp, float] | None:
    """종목의 최신 위험 평가 (as_of, proba) — 카드 미리보기 용.

    기존 정적 산출물(load_d2_predictions) 재사용 — 계산·페치 0 (§8.6).
    """
    if preds is None or preds.empty:
        return None
    sel = preds[preds["ticker"] == ticker]
    if "class_weight" in sel.columns:
        sel = sel[sel["class_weight"] == "balanced"]
    sel = sel.dropna(subset=["proba"])
    if sel.empty:
        return None
    row = sel.loc[pd.to_datetime(sel["test_as_of"]).idxmax()]
    return pd.Timestamp(row["test_as_of"]), float(row["proba"])


def render() -> None:
    """개요 페이지 렌더 — 소개 + 예시 종목 3 카드 + 메뉴 안내 + CTA."""
    PageHeader(
        "한국 KOSPI200 기업 분석 데모",
        "한국 KOSPI200 에 속했던 기업들(10년간 321곳, 상장폐지 포함)의 "
        "재무 건강과 시장 상황을 한눈에 보여주는 웹 시스템입니다.",
    )

    st.markdown("## 예시 종목")
    universe = load_universe()
    name_map: dict[str, str] = {}
    rank_map: dict[str, float] = {}
    if not universe.empty:
        name_map = dict(zip(universe["ticker"], universe["name"], strict=False))
        rank_map = dict(zip(universe["ticker"], universe["marcap_rank"], strict=False))

    # U3 카드화: 테두리 컨테이너 + 위험/상태 badge 미리보기 (기존 로더 재사용)
    preds = load_d2_predictions()
    state_series = load_state_series()

    cols = st.columns(len(_EXAMPLE_TICKERS))
    for col, ticker in zip(cols, _EXAMPLE_TICKERS, strict=True):
        with col, st.container(border=True):
            st.markdown(f"**{ticker} {name_map.get(ticker, ticker)}**")
            rank = rank_map.get(ticker)
            if rank is not None and pd.notna(rank):
                st.caption(f"시가총액: 현 시점 기준 분석 대상 내 {int(rank)}위")
            else:
                st.caption("시가총액: —")
            latest = _latest_eval(preds, ticker)
            if latest is not None:
                as_of, proba = latest
                level, _color = classify_risk(proba)
                state = lookup_state_at(as_of, state_series)
                risk_part = f":{BADGE_COLOR_MAP.get(level, 'gray')}-badge[위험 {level}]"
                state_part = (
                    f" :{BADGE_COLOR_MAP.get(state, 'gray')}-badge[{state}]" if state else ""
                )
                st.markdown(risk_part + state_part)
                st.caption(f"{as_of:%Y-%m-%d} 평가 기준")
            else:
                st.caption("위험 평가 시점 없음")
            if st.button("분석 보기", key=f"go_{ticker}"):
                # U4 QA 후속: 종목 분석 selectbox(key="ticker_select") 에
                # 선택 종목 전달 — 위젯 렌더 전 session_state 설정 패턴
                st.session_state["ticker_select"] = ticker
                st.switch_page(ticker_page())

    st.markdown("## 메뉴 둘러보기")
    st.markdown(
        "- **종목 분석** — 관심 기업의 재무 건강 + 시장 상황\n"
        "- **시장 상태** — 시점별 시장 흐름\n"
        "- **한계** — 본 시스템의 정직한 한계 안내"
    )

    # CTA — 종목 분석 페이지로 진짜 이동 (U1)
    if st.button("★ 종목 분석 시작"):
        st.switch_page(ticker_page())
