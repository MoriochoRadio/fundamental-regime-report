"""페이지 헤더 + 종목 헤더 컴포넌트 (docs/ui_design.md §2.1·§2.2).

pure 렌더링 함수 (st.* 직접 호출, 반환 None).

Phase 4 자산 변환:
- (B) 정정: render_page_header → PageHeader, render_ticker_header →
  TickerHeader (3 단계 §2 spec 정합, 검증 1 매핑)
- (D) 폐기: TickerHeader 의 fs_div 파라미터 (ML 차원 메타, 검증 2 매핑) +
  4 metric grid → 단순 헤더 (h2 + caption, 3 단계 §2.2 spec)
- (C) 재사용 + (E) 신규: format_ticker_option (단위 a; format_won 은 절대
  금액 미노출 결정으로 제거 — 상대 순위 표기)
"""

from __future__ import annotations

import math

import streamlit as st

from app.utils.formatters import format_ticker_option


def PageHeader(title: str, subtitle: str | None = None) -> None:
    """페이지 진입 헤더 — 제목 (h1) + 부제 (caption).

    docs/ui_design.md §2.1 spec.

    Args:
        title: 페이지 제목 (h1, text.h1 토큰).
        subtitle: 부제 (caption, text.caption 토큰). None 이면 미표시.
    """
    if not title:
        return
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def _missing_rank(rank: float | None) -> bool:
    """순위 결측 판정 (None·NaN·비수치 → True)."""
    if rank is None:
        return True
    try:
        return math.isnan(float(rank))
    except (TypeError, ValueError):
        return True


def TickerHeader(
    ticker_code: str,
    ticker_name: str,
    marcap_rank: float | None = None,
) -> None:
    """종목 헤더 — "코드 종목명" (h2) + 시가총액 *상대 순위* (caption).

    docs/ui_design.md §2.2 spec. Phase 4 의 fs_div 4 metric grid 폐기
    (검증 2 매핑) → 단순 헤더.

    ★ 시가총액 *절대 금액* 은 출처(FDR 현 시점 스냅샷) 검증 한계로
    화면 미노출 — 동일 스냅샷 내 *상대 순위* 만 표기 (정직성 원칙).

    Args:
        ticker_code: 종목 코드 (6 자리).
        ticker_name: 종목명.
        marcap_rank: 분석 대상 내 시가총액 순위 (1 = 최대).
            None/NaN 이면 "—" caption (상장폐지 종목 등).
    """
    if not ticker_code:
        return
    st.header(format_ticker_option(ticker_code, ticker_name))
    if _missing_rank(marcap_rank):
        st.caption("시가총액: — (현 시점 정보 없음 — 상장폐지 종목 등)")
    else:
        st.caption(
            f"시가총액: 현 시점 기준 분석 대상 내 {int(float(marcap_rank))}위 "  # type: ignore[arg-type]
            "(과거 시점 추적은 본 시스템 범위 밖)"
        )
