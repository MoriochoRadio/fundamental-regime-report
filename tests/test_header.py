"""app/components/header.py 단위 테스트.

단계 5 단위 (c) 산출물. 검증 7 (방어적 입력) + 검증 1·2·4 매핑.

컴포넌트 = pure 렌더링 함수 (st.* 직접 호출, 반환 None).
mock-based 테스트 — st.* 호출 인자 검증 (Streamlit runtime 불필요).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.components.header import PageHeader, TickerHeader

# ---- PageHeader ------------------------------------------------------------


def test_page_header_title_and_subtitle() -> None:
    """title + subtitle → st.title + st.caption 호출."""
    with patch("app.components.header.st") as mock_st:
        PageHeader("제목", "부제")
        mock_st.title.assert_called_once_with("제목")
        mock_st.caption.assert_called_once_with("부제")


def test_page_header_title_only() -> None:
    """subtitle None → st.title 만 호출, st.caption 미호출."""
    with patch("app.components.header.st") as mock_st:
        PageHeader("제목")
        mock_st.title.assert_called_once_with("제목")
        mock_st.caption.assert_not_called()


def test_page_header_subtitle_none_explicit() -> None:
    """subtitle 명시 None → st.caption 미호출."""
    with patch("app.components.header.st") as mock_st:
        PageHeader("제목", None)
        mock_st.caption.assert_not_called()


def test_page_header_empty_title_defensive() -> None:
    """빈 title → 아무것도 렌더 안 함 (방어적)."""
    with patch("app.components.header.st") as mock_st:
        PageHeader("")
        mock_st.title.assert_not_called()
        mock_st.caption.assert_not_called()


# ---- TickerHeader ----------------------------------------------------------


def test_ticker_header_full() -> None:
    """3 인자 정상 → st.header (코드 종목명) + st.caption (시가총액)."""
    with patch("app.components.header.st") as mock_st:
        TickerHeader("005930", "삼성전자", 412_000_000_000_000)
        mock_st.header.assert_called_once_with("005930 삼성전자")
        # caption 호출 + 시가총액 조원 표기 포함
        assert mock_st.caption.call_count == 1
        caption_arg = mock_st.caption.call_args[0][0]
        assert "412.00 조원" in caption_arg


def test_ticker_header_marcap_none() -> None:
    """market_cap None → caption 에 "—" 표기."""
    with patch("app.components.header.st") as mock_st:
        TickerHeader("005930", "삼성전자", None)
        mock_st.header.assert_called_once_with("005930 삼성전자")
        caption_arg = mock_st.caption.call_args[0][0]
        assert "—" in caption_arg


def test_ticker_header_marcap_nan() -> None:
    """market_cap NaN → caption 에 "—" 표기 (format_won 처리)."""
    with patch("app.components.header.st") as mock_st:
        TickerHeader("005930", "삼성전자", float("nan"))
        caption_arg = mock_st.caption.call_args[0][0]
        assert "—" in caption_arg


def test_ticker_header_empty_code_defensive() -> None:
    """빈 ticker_code → 아무것도 렌더 안 함 (방어적)."""
    with patch("app.components.header.st") as mock_st:
        TickerHeader("", "삼성전자", 1000)
        mock_st.header.assert_not_called()
        mock_st.caption.assert_not_called()


# ---- 검증 2 매핑: fs_div 파라미터 폐기 확인 -------------------------------


def test_ticker_header_no_fs_div_param() -> None:
    """검증 2: TickerHeader 가 fs_div 파라미터를 받지 않음 (ML 메타 폐기)."""
    import inspect

    sig = inspect.signature(TickerHeader)
    assert "fs_div" not in sig.parameters
    # 3 단계 §2.2 spec: ticker_code, ticker_name, market_cap 만
    assert set(sig.parameters.keys()) == {"ticker_code", "ticker_name", "market_cap"}


# ---- 검증 4 매핑: 출력 일반인 친화 (ML 용어 0) ----------------------------


def test_ticker_header_caption_no_ml_terms() -> None:
    """검증 4: TickerHeader caption 에 ML 용어 원본 노출 0."""
    with patch("app.components.header.st") as mock_st:
        TickerHeader("005930", "삼성전자", 412_000_000_000_000)
        caption_arg = mock_st.caption.call_args[0][0]
        forbidden = ["fs_div", "CFS", "OFS", "PR-AUC", "regime", "HMM"]
        for term in forbidden:
            assert term not in caption_arg, f"ML 용어 '{term}' caption 노출"


# ---- import 검증 (검증 1: 함수명 정정) ------------------------------------


def test_component_names_pascal_case() -> None:
    """검증 1: 함수명 정정 (render_* → PageHeader/TickerHeader)."""
    from app import components

    assert hasattr(components, "PageHeader")
    assert hasattr(components, "TickerHeader")
    # 옛 이름 부재
    from app.components import header

    assert not hasattr(header, "render_page_header")
    assert not hasattr(header, "render_ticker_header")


def test_mock_st_usage() -> None:
    """MagicMock 패턴 검증 (테스트 자체 정합)."""
    mock = MagicMock()
    mock.title("x")
    mock.title.assert_called_once_with("x")
