"""개요 페이지 (docs/ui_design.md §1.1).

render() — st.navigation(v2) 의 default Page. 소개 + 예시 종목 카드 + 메뉴
둘러보기 + CTA. ModelLimitBadge 는 main.py shell 에서 전역 호출 (중복 없음).

U1 개편: CTA 클릭 → st.switch_page(ticker_page()) 진짜 이동 (페이지 정체성
= url_path 해시, 레지스트리 동일 정의 — app/components/navigation.py).
"""

from __future__ import annotations

import streamlit as st

from app.components import PageHeader, TickerHeader
from app.components.navigation import ticker_page
from app.data_loader import load_universe

# 예시 종목 (docs §1.1): 삼성전자 · SK하이닉스 · SK
_EXAMPLE_TICKERS = ["005930", "000660", "034730"]


def render() -> None:
    """개요 페이지 렌더 — 소개 + 예시 종목 3 카드 + 메뉴 안내 + CTA."""
    PageHeader(
        "한국 KOSPI200 기업 분석 데모",
        "한국 KOSPI200 200대 기업의 재무 건강과 시장 상황을 한눈에 보여주는 웹 시스템입니다.",
    )

    st.markdown("## 예시 종목")
    universe = load_universe()
    name_map: dict[str, str] = {}
    rank_map: dict[str, float] = {}
    if not universe.empty:
        name_map = dict(zip(universe["ticker"], universe["name"], strict=False))
        rank_map = dict(zip(universe["ticker"], universe["marcap_rank"], strict=False))

    cols = st.columns(len(_EXAMPLE_TICKERS))
    for col, ticker in zip(cols, _EXAMPLE_TICKERS, strict=True):
        with col:
            TickerHeader(ticker, name_map.get(ticker, ticker), rank_map.get(ticker))

    st.markdown("## 메뉴 둘러보기")
    st.markdown(
        "- **종목 분석** — 관심 기업의 재무 건강 + 시장 상황\n"
        "- **시장 상태** — 시점별 시장 흐름\n"
        "- **한계** — 본 시스템의 정직한 한계 안내"
    )

    # CTA — 종목 분석 페이지로 진짜 이동 (U1)
    if st.button("★ 종목 분석 시작"):
        st.switch_page(ticker_page())
