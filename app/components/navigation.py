"""네비게이션 페이지 레지스트리 — build_nav_pages / ticker_page (U1 개편).

docs/ui_design.md §2.10·§3.1. SidebarNav 라디오 폐기 → st.navigation(v2)
단일 한글 메뉴. 본 모듈이 4 페이지 정의(라벨·아이콘·url_path)의 *단일 출처*.

U1 개편 근거 (실측, 2026-06):
- app/pages/ 폴더 존재로 streamlit v1 자동 등록(영문 메뉴)이 SidebarNav 와
  이중화 → `st.navigation()` 호출이 v1 자동 등록을 명시적으로 끈다
  (streamlit commands/navigation.py: `uses_pages_directory = False`)
  — 폴더명 변경 불필요.
- 페이지 정체성 = url_path 해시 (streamlit navigation/page.py:
  `_script_hash = calc_hash(url_path)`) → CTA 의 st.switch_page 는
  동일 정의 Page 재구성(ticker_page)으로 동작, 순환 import 0.

★ app.pages import 는 함수 내부 lazy — main → navigation → pages →
(overview → navigation) 순환을 import 시점에서 차단.
"""

from __future__ import annotations

import streamlit as st


def ticker_page() -> st.Page:
    """종목 분석 Page 단건 — 레지스트리와 동일 정의 (CTA st.switch_page 용).

    url_path="ticker" 가 페이지 정체성 (해시 기준) — build_nav_pages 의
    등록본과 동일해야 이동이 성립한다 (tests/test_navigation.py 박제).
    """
    from app.pages import ticker_analysis

    return st.Page(
        ticker_analysis.render,
        title="종목 분석",
        icon=":material/query_stats:",
        url_path="ticker",
    )


def build_nav_pages() -> list[st.Page]:
    """4 페이지 st.Page 목록 — 한글 라벨 + material 아이콘, 개요 = default.

    main.py 의 `st.navigation(build_nav_pages())` 입력. 브라우저 탭 제목은
    각 Page 의 title (set_page_config page_title 미지정, v2 동작).
    """
    from app.pages import limitations, market_state, overview

    return [
        st.Page(
            overview.render,
            title="개요",
            icon=":material/home:",
            default=True,
        ),
        ticker_page(),
        st.Page(
            market_state.render,
            title="시장 상태",
            icon=":material/waves:",
            url_path="state",
        ),
        st.Page(
            limitations.render,
            title="한계",
            icon=":material/warning:",
            url_path="limitations",
        ),
    ]
