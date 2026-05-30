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
    empty = pd.DataFrame(columns=["ticker", "name", "marcap"])
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
