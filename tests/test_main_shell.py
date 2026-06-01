"""app/main.py shell 단위 테스트 (페이지 통합 단위 i).

main() = set_page_config + ModelLimitBadge(badge) 전역 + SidebarNav dispatch.
st·컴포넌트·렌더러 mock 으로 dispatch 흐름 검증.

★ ML 수치 비노출 통합 회귀: shell + 개요 페이지 소스에 ML 원본 수치 부재
(docs §2.8·§7.7 외부 노출 표면 박제).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import app.main as main_mod

_APP_DIR = Path(__file__).resolve().parent.parent / "app"


def test_badge_and_overview_dispatch() -> None:
    """main(): ModelLimitBadge(badge) 1회 + page=overview → overview.render 호출."""
    mock_render = MagicMock()
    with (
        patch("app.main.st"),
        patch("app.main.ModelLimitBadge") as mock_badge,
        patch("app.main.SidebarNav", return_value="overview"),
        patch.dict("app.main._PAGE_RENDERERS", {"overview": mock_render}, clear=True),
    ):
        main_mod.main()
        mock_badge.assert_called_once_with("badge")
        mock_render.assert_called_once()


def test_dispatch_selected_page() -> None:
    """SidebarNav 반환 key 로 해당 렌더러만 호출."""
    r_over, r_tick = MagicMock(), MagicMock()
    with (
        patch("app.main.st"),
        patch("app.main.ModelLimitBadge"),
        patch("app.main.SidebarNav", return_value="ticker"),
        patch.dict("app.main._PAGE_RENDERERS", {"overview": r_over, "ticker": r_tick}, clear=True),
    ):
        main_mod.main()
        r_tick.assert_called_once()
        r_over.assert_not_called()


def test_unknown_page_placeholder() -> None:
    """미등록 page key (단위 i 미구현) → 임시 안내 st.info."""
    with (
        patch("app.main.st") as mock_st,
        patch("app.main.ModelLimitBadge"),
        patch("app.main.SidebarNav", return_value="ticker"),
        patch.dict("app.main._PAGE_RENDERERS", {"overview": MagicMock()}, clear=True),
    ):
        main_mod.main()
        mock_st.info.assert_called_once()


def test_no_ml_numbers_in_shell_and_overview() -> None:
    """★ docs §2.8·§7.7: shell + 개요 소스에 ML 원본 수치 비노출."""
    forbidden = ["PR-AUC", "0.0136", "base rate", "0.0205", "random 미만"]
    for rel in ["main.py", "pages/overview.py"]:
        text = (_APP_DIR / rel).read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{rel}: '{token}' 노출됨"
