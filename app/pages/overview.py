"""개요 페이지 (docs/ui_design.md §1.1).

render() — main.py shell 이 dispatch. 소개 + 예시 종목 카드 + 메뉴 둘러보기
+ CTA. ModelLimitBadge 는 main.py shell 에서 전역 호출 (개요 중복 호출 안 함).

Q4 (A): CTA 는 표시만 — 클릭 → 종목 분석 라우팅은 단위 (j) 종목 분석 페이지와
함께 구현.
"""

from __future__ import annotations

import streamlit as st

from app.components import PageHeader, TickerHeader
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
    marcap_map: dict[str, float] = {}
    if not universe.empty:
        name_map = dict(zip(universe["ticker"], universe["name"], strict=False))
        marcap_map = dict(zip(universe["ticker"], universe["marcap"], strict=False))

    cols = st.columns(len(_EXAMPLE_TICKERS))
    for col, ticker in zip(cols, _EXAMPLE_TICKERS, strict=True):
        with col:
            TickerHeader(ticker, name_map.get(ticker, ticker), marcap_map.get(ticker))

    st.markdown("## 메뉴 둘러보기")
    st.markdown(
        "- **종목 분석** — 관심 기업의 재무 건강 + 시장 상황\n"
        "- **시장 상태** — 시점별 시장 흐름\n"
        "- **한계** — 본 시스템의 정직한 한계 안내"
    )

    # CTA (Q4 A: 표시만 — 클릭 라우팅은 단위 j)
    if st.button("★ 종목 분석 시작"):
        st.info("왼쪽 사이드바에서 **종목 분석** 메뉴를 선택해 주세요.")
