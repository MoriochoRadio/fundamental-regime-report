"""app/components/navigation.py 단위 테스트 (U1 — st.navigation 레지스트리).

SidebarNav 라디오 폐기 → build_nav_pages / ticker_page 레지스트리.

★ st.Page 는 ScriptRunContext 없으면 속성 미설정(조기 return, streamlit
navigation/page.py 실측) — 본 테스트는 st mock 으로 *우리 정의*
(라벨·아이콘·url_path·default) 를 호출 인자 차원에서 검증한다.
"""

from __future__ import annotations

from unittest.mock import patch

from app.components import navigation as nav_mod

# (title, icon, url_path 또는 None=default) — U1 확정 정의
_EXPECTED = [
    ("개요", ":material/home:", None),
    ("종목 분석", ":material/query_stats:", "ticker"),
    ("시장 상태", ":material/waves:", "state"),
    ("한계", ":material/warning:", "limitations"),
]


def _page_calls() -> list:
    """build_nav_pages 실행 시 st.Page 호출 인자 목록 (등록 순서)."""
    with patch("app.components.navigation.st") as mock_st:
        nav_mod.build_nav_pages()
        return mock_st.Page.call_args_list


def test_build_nav_pages_4_pages() -> None:
    """레지스트리 = 정확히 4 페이지 (한글 메뉴 1벌)."""
    assert len(_page_calls()) == 4


def test_korean_titles_in_order() -> None:
    """한글 라벨 4종 — 개요/종목 분석/시장 상태/한계 (등록 순서)."""
    titles = [c.kwargs["title"] for c in _page_calls()]
    assert titles == [t for t, _, _ in _EXPECTED]


def test_material_icons() -> None:
    """material 아이콘 4종 (U1 결정 ②)."""
    icons = [c.kwargs["icon"] for c in _page_calls()]
    assert icons == [i for _, i, _ in _EXPECTED]


def test_overview_default_and_url_paths() -> None:
    """개요 = default (url_path 미지정) + 나머지 url_path 정합 (U1 결정 ③)."""
    calls = _page_calls()
    assert calls[0].kwargs.get("default") is True
    assert "url_path" not in calls[0].kwargs  # default 는 url_path="" (v2)
    paths = [c.kwargs.get("url_path") for c in calls[1:]]
    assert paths == ["ticker", "state", "limitations"]


def test_ticker_page_same_identity_as_registry() -> None:
    """★ CTA 용 ticker_page() = 레지스트리 등록본과 동일 정의.

    페이지 정체성 = url_path 해시 — kwargs 전체 일치로 st.switch_page
    이동 성립을 박제 (정의가 갈라지면 CTA 가 미등록 페이지를 가리킴).
    """
    registry_ticker = _page_calls()[1]
    with patch("app.components.navigation.st") as mock_st:
        nav_mod.ticker_page()
        single = mock_st.Page.call_args
    assert single.kwargs == registry_ticker.kwargs


def test_no_regime_no_d2_labels() -> None:
    """라벨에 "국면"(→상태 정정)·"D2"(폐기 페이지) 부재 회귀."""
    titles = " ".join(c.kwargs["title"] for c in _page_calls())
    assert "국면" not in titles
    assert "D2" not in titles


def test_sidebar_nav_removed() -> None:
    """U1: SidebarNav 라디오 완전 폐기 (이중 네비 해소)."""
    assert not hasattr(nav_mod, "SidebarNav")
