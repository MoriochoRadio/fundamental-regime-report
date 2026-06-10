"""app/main.py shell 단위 테스트 (U1 — st.navigation 단일 메뉴).

main() = set_page_config(page_title 미지정·material 탭 아이콘) +
ModelLimitBadge(badge) 전역 + st.navigation(build_nav_pages()).run().
st·컴포넌트 mock 으로 shell 흐름 검증 (라우팅 자체는 streamlit v2 책임).

★ ML 수치 비노출 통합 회귀: shell + 개요 페이지 소스에 ML 원본 수치 부재
(docs §2.8·§7.7 외부 노출 표면 박제).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import app.main as main_mod

_APP_DIR = Path(__file__).resolve().parent.parent / "app"


def test_main_navigation_flow() -> None:
    """main(): set_page_config → badge 1회 → st.navigation(레지스트리).run()."""
    with (
        patch("app.main.st") as mock_st,
        patch("app.main.ModelLimitBadge") as mock_badge,
        patch("app.main.build_nav_pages") as mock_build,
    ):
        main_mod.main()
        mock_st.set_page_config.assert_called_once()
        mock_badge.assert_called_once_with("badge")
        mock_st.navigation.assert_called_once_with(mock_build.return_value)
        mock_st.navigation.return_value.run.assert_called_once_with()


def test_page_config_tab_title_per_page() -> None:
    """set_page_config: page_title 미지정 (탭 제목 = 현재 Page title, v2)
    + material 탭 아이콘 (U1 결정 ②)."""
    with (
        patch("app.main.st") as mock_st,
        patch("app.main.ModelLimitBadge"),
        patch("app.main.build_nav_pages"),
    ):
        main_mod.main()
        kwargs = mock_st.set_page_config.call_args.kwargs
        assert "page_title" not in kwargs
        assert kwargs.get("page_icon") == ":material/monitoring:"
        assert kwargs.get("layout") == "wide"


def test_badge_before_navigation_run() -> None:
    """전역 배지가 페이지 실행(run) *이전* 호출 — 모든 페이지 상단 보장."""
    order: list[str] = []
    with (
        patch("app.main.st") as mock_st,
        patch("app.main.ModelLimitBadge", side_effect=lambda *a: order.append("badge")),
        patch("app.main.build_nav_pages"),
    ):
        mock_st.navigation.return_value.run.side_effect = lambda: order.append("run")
        main_mod.main()
    assert order == ["badge", "run"]


def test_no_dispatch_dict_remains() -> None:
    """U1: SidebarNav dispatch dict(_PAGE_RENDERERS) 완전 제거 회귀."""
    assert not hasattr(main_mod, "_PAGE_RENDERERS")


def test_no_ml_numbers_in_shell_and_overview() -> None:
    """★ docs §2.8·§7.7: shell + 개요 소스에 ML 원본 수치 비노출."""
    forbidden = ["PR-AUC", "0.0136", "base rate", "0.0205", "random 미만"]
    for rel in ["main.py", "pages/overview.py"]:
        text = (_APP_DIR / rel).read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{rel}: '{token}' 노출됨"
