"""app/pages/overview.py 단위 테스트 (U3 카드화).

개요 페이지 = PageHeader + 예시 종목 3 카드(테두리 컨테이너 + 위험/상태
badge 미리보기) + 메뉴 안내 + CTA. st·컴포넌트·로더 mock 으로 검증.
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


def _preds() -> pd.DataFrame:
    """005930 만 평가 보유 — 미리보기 badge 분기 검증용."""
    return pd.DataFrame(
        {
            "ticker": ["005930"],
            "class_weight": ["balanced"],
            "test_as_of": [pd.Timestamp("2024-03-29")],
            "proba": [0.008],
        }
    )


def _patches(mock_st, preds=None):
    return (
        patch("app.pages.overview.st", mock_st),
        patch("app.pages.overview.load_universe", return_value=_universe()),
        patch("app.pages.overview.load_d2_predictions", return_value=preds),
        patch("app.pages.overview.load_state_series", return_value=None),
        patch("app.pages.overview.PageHeader"),
    )


def _mock_st(button: bool = False) -> MagicMock:
    st = MagicMock()
    st.columns.return_value = [MagicMock(), MagicMock(), MagicMock()]
    st.button.return_value = button
    return st


def _md_text(mock_st) -> str:
    return " ".join(str(a) for c in mock_st.markdown.call_args_list for a in c.args)


def test_overview_3_bordered_cards() -> None:
    """예시 종목 3 카드 — 테두리 컨테이너 3회 + 종목명 bold 마크다운."""
    st = _mock_st()
    p1, p2, p3, p4, p5 = _patches(st, preds=_preds())
    with p1, p2, p3, p4, p5:
        render()
    assert st.container.call_count == 3
    for c in st.container.call_args_list:
        assert c.kwargs.get("border") is True
    md = _md_text(st)
    for code, name in [("005930", "삼성전자"), ("000660", "SK하이닉스"), ("034730", "SK")]:
        assert f"**{code} {name}**" in md


def test_preview_badges_for_evaluated_ticker() -> None:
    """평가 보유 종목(005930) → 위험 badge 마크다운 + 평가 기준 caption."""
    st = _mock_st()
    p1, p2, p3, p4, p5 = _patches(st, preds=_preds())
    with p1, p2, p3, p4, p5:
        render()
    md = _md_text(st)
    assert ":green-badge[위험 낮음]" in md  # proba 0.008 → 낮음 → green
    caps = " ".join(str(a) for c in st.caption.call_args_list for a in c.args)
    assert "2024-03-29 평가 기준" in caps
    # 미평가 2 종목 → "위험 평가 시점 없음" caption
    assert caps.count("위험 평가 시점 없음") == 2


def test_preview_no_preds_graceful() -> None:
    """predictions 부재(None) → 전 카드 '위험 평가 시점 없음' (크래시 0)."""
    st = _mock_st()
    p1, p2, p3, p4, p5 = _patches(st, preds=None)
    with p1, p2, p3, p4, p5:
        render()
    caps = " ".join(str(a) for c in st.caption.call_args_list for a in c.args)
    assert caps.count("위험 평가 시점 없음") == 3


def test_overview_empty_universe_no_crash() -> None:
    """universe 빈 DataFrame → 예외 없이 렌더 (ticker 코드 자체 fallback)."""
    st = _mock_st()
    empty = pd.DataFrame(columns=["ticker", "name", "marcap", "marcap_rank"])
    with (
        patch("app.pages.overview.st", st),
        patch("app.pages.overview.load_universe", return_value=empty),
        patch("app.pages.overview.load_d2_predictions", return_value=None),
        patch("app.pages.overview.load_state_series", return_value=None),
        patch("app.pages.overview.PageHeader") as mock_ph,
    ):
        render()
        mock_ph.assert_called_once()
    assert st.container.call_count == 3  # 카드는 코드 fallback 으로 여전히 3개


def test_cta_switch_page() -> None:
    """CTA 클릭(마지막 버튼 True) → st.switch_page(ticker_page())."""
    sentinel = MagicMock(name="ticker_page_obj")
    st = _mock_st()
    st.button.side_effect = [False, False, False, True]  # 카드 3 + CTA
    p1, p2, p3, p4, p5 = _patches(st, preds=None)
    with p1, p2, p3, p4, p5, patch("app.pages.overview.ticker_page", return_value=sentinel):
        render()
    st.switch_page.assert_called_once_with(sentinel)


def test_card_button_switch_page() -> None:
    """카드 '분석 보기' 클릭(첫 버튼 True) → st.switch_page 이동."""
    sentinel = MagicMock(name="ticker_page_obj")
    st = _mock_st()
    st.button.side_effect = [True, False, False, False]
    p1, p2, p3, p4, p5 = _patches(st, preds=None)
    with p1, p2, p3, p4, p5, patch("app.pages.overview.ticker_page", return_value=sentinel):
        render()
    st.switch_page.assert_called_once_with(sentinel)


def test_cta_no_click_no_switch() -> None:
    """버튼 전부 미클릭 → switch_page 미호출."""
    st = _mock_st(button=False)
    p1, p2, p3, p4, p5 = _patches(st, preds=None)
    with p1, p2, p3, p4, p5:
        render()
    st.switch_page.assert_not_called()
