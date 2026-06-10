"""app/pages/overview.py 단위 테스트 (페이지 통합 단위 i).

개요 페이지 = PageHeader + 예시 종목 3 카드(TickerHeader) + 메뉴 안내 + CTA.
st·컴포넌트·load_universe mock 으로 검증.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from app.pages.overview import render


def _universe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ticker": ["005930", "000660", "034730"],
            "name": ["삼성전자", "SK하이닉스", "SK"],
            "marcap": [4.0e14, 1.0e14, 2.0e13],
            "marcap_rank": [1.0, 2.0, 3.0],
        }
    )


def test_overview_header_and_3_cards() -> None:
    """PageHeader 1회 + TickerHeader 3회 (예시 종목 3)."""
    with (
        patch("app.pages.overview.st") as mock_st,
        patch("app.pages.overview.load_universe", return_value=_universe()),
        patch("app.pages.overview.PageHeader") as mock_ph,
        patch("app.pages.overview.TickerHeader") as mock_th,
    ):
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        render()
        mock_ph.assert_called_once()
        assert mock_th.call_count == 3


def test_overview_example_ticker_codes() -> None:
    """예시 카드 = 005930 · 000660 · 034730 (docs §1.1)."""
    with (
        patch("app.pages.overview.st") as mock_st,
        patch("app.pages.overview.load_universe", return_value=_universe()),
        patch("app.pages.overview.PageHeader"),
        patch("app.pages.overview.TickerHeader") as mock_th,
    ):
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        render()
        codes = [c.args[0] for c in mock_th.call_args_list]
        assert codes == ["005930", "000660", "034730"]


def test_overview_empty_universe_no_crash() -> None:
    """universe 빈 DataFrame → 예외 없이 렌더 (ticker 코드 자체를 name fallback)."""
    empty = pd.DataFrame(columns=["ticker", "name", "marcap", "marcap_rank"])
    with (
        patch("app.pages.overview.st") as mock_st,
        patch("app.pages.overview.load_universe", return_value=empty),
        patch("app.pages.overview.PageHeader") as mock_ph,
        patch("app.pages.overview.TickerHeader") as mock_th,
    ):
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        render()
        mock_ph.assert_called_once()
        assert mock_th.call_count == 3


def test_cta_switch_page(  # U1: CTA 진짜 이동
) -> None:
    """CTA 클릭(True) → st.switch_page(ticker_page()) 호출."""
    sentinel = MagicMock(name="ticker_page_obj")
    with (
        patch("app.pages.overview.st") as mock_st,
        patch("app.pages.overview.load_universe", return_value=_universe()),
        patch("app.pages.overview.PageHeader"),
        patch("app.pages.overview.TickerHeader"),
        patch("app.pages.overview.ticker_page", return_value=sentinel),
    ):
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_st.button.return_value = True
        render()
        mock_st.switch_page.assert_called_once_with(sentinel)


def test_cta_no_click_no_switch() -> None:
    """CTA 미클릭(False) → switch_page 미호출."""
    with (
        patch("app.pages.overview.st") as mock_st,
        patch("app.pages.overview.load_universe", return_value=_universe()),
        patch("app.pages.overview.PageHeader"),
        patch("app.pages.overview.TickerHeader"),
    ):
        mock_st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_st.button.return_value = False
        render()
        mock_st.switch_page.assert_not_called()
