"""Page header + Ticker header (docs/ui_components.md §1.1·§1.2)."""

from __future__ import annotations

import streamlit as st
from utils.formatters import format_won


def render_page_header(
    title: str,
    subtitle: str | None = None,
    value_message: str | None = None,
) -> None:
    """페이지 진입 헤더 — 제목·부제·핵심 가치 1 줄.

    Args:
        title: h1 제목.
        subtitle: h3 부제 (선택).
        value_message: info banner 핵심 가치 (선택).
    """
    st.title(title)
    if subtitle:
        st.markdown(f"### {subtitle}")
    if value_message:
        st.info(value_message)


def render_ticker_header(
    ticker: str,
    name: str,
    marcap: float | None = None,
    fs_div: str | None = None,
) -> None:
    """종목 분석 페이지 상단 — 코드·이름·시총·재무 출처 4 metric."""
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("종목코드", ticker)
    col2.metric("종목명", name)
    col3.metric("시가총액 (현시점)", format_won(marcap))
    col4.metric("재무 출처", fs_div or "—")
    st.caption(
        "ℹ️ 시가총액은 현재 시점 스냅샷 (FDR StockListing). "
        "과거 시점 시총 추적은 본 프로젝트 범위 밖입니다."
    )
