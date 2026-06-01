"""app/components/navigation.py 단위 테스트.

단계 5 단위 (h) 산출물. docs/ui_design.md §2.10·§3.1 매핑.

컴포넌트 = pure 렌더링 함수 (선택 key 반환). st mock 으로 검증.
mock_st.sidebar.radio.return_value 로 사용자 선택을 제어.
"""

from __future__ import annotations

from unittest.mock import patch

from app.components.navigation import SidebarNav


def test_menu_labels_4_pages() -> None:
    """radio 인자에 4-페이지 라벨 (개요·종목 분석·시장 상태·한계) 포함."""
    with patch("app.components.navigation.st") as mock_st:
        mock_st.sidebar.radio.return_value = "개요"
        SidebarNav("overview")
        # radio 두 번째 위치 인자 = labels 리스트
        labels = mock_st.sidebar.radio.call_args.args[1]
        assert labels == ["개요", "종목 분석", "시장 상태", "한계"]


def test_return_key_ticker() -> None:
    """'종목 분석' 선택 → 'ticker' key 반환."""
    with patch("app.components.navigation.st") as mock_st:
        mock_st.sidebar.radio.return_value = "종목 분석"
        assert SidebarNav("overview") == "ticker"


def test_return_key_limitations() -> None:
    """'한계' 선택 → 'limitations' key 반환."""
    with patch("app.components.navigation.st") as mock_st:
        mock_st.sidebar.radio.return_value = "한계"
        assert SidebarNav("overview") == "limitations"


def test_current_page_highlight_index() -> None:
    """current_page='state' → radio index = '시장 상태' 위치 (2)."""
    with patch("app.components.navigation.st") as mock_st:
        mock_st.sidebar.radio.return_value = "시장 상태"
        SidebarNav("state")
        assert mock_st.sidebar.radio.call_args.kwargs["index"] == 2


def test_regime_to_state_and_no_d2() -> None:
    """★ 정정 회귀: '시장 국면' 부재 + '시장 상태' 존재 + 'D2 baseline' 부재 (5→4)."""
    with patch("app.components.navigation.st") as mock_st:
        mock_st.sidebar.radio.return_value = "개요"
        SidebarNav("overview")
        labels = mock_st.sidebar.radio.call_args.args[1]
        assert "시장 상태" in labels
        assert "시장 국면" not in labels
        assert not any("D2" in label for label in labels)
        assert len(labels) == 4


def test_unknown_current_page_fallback() -> None:
    """미지 current_page → 첫 페이지(개요, index 0) fallback."""
    with patch("app.components.navigation.st") as mock_st:
        mock_st.sidebar.radio.return_value = "개요"
        SidebarNav("nonexistent")
        assert mock_st.sidebar.radio.call_args.kwargs["index"] == 0


def test_component_name_state_not_regime() -> None:
    """검증 1: SidebarNav 존재 + render_sidebar_nav 부재."""
    from app import components
    from app.components import navigation

    assert hasattr(components, "SidebarNav")
    assert not hasattr(navigation, "render_sidebar_nav")
