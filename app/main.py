"""Streamlit 대시보드 entry point — thin shell (페이지 통합 단위 i).

CLAUDE.md §8.6 박제:
- 정적 읽기 전용 (런타임 LLM 호출 0회·학습·계산·페치 0회)
- reports/ + data/interim/ 정적 산출물만 읽음

실행:
    uv run streamlit run app/main.py

★ 절대 import (from app.X) — Streamlit 은 스크립트 디렉토리(app/)만 sys.path
에 추가하므로 repo-root 를 명시 주입한다. tests/test_app_no_llm_import.py 의
cwd=app/ import 검증(절대 import + 명시 sys.path 처리)도 이 주입으로 통과.

페이지 라우팅 (페이지 통합 단계):
- 단위 (i): main.py shell + SidebarNav dispatch + 개요 페이지
- 단위 (j)/(k)/(l): 종목 분석 / 시장 상태 / 한계 페이지 등록
"""

from __future__ import annotations

import sys
from pathlib import Path

# repo-root 주입 — `streamlit run app/main.py` + cwd=app/ 양쪽에서 절대 import 보장
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import streamlit as st  # noqa: E402

from app.components import ModelLimitBadge, SidebarNav  # noqa: E402
from app.pages import overview, ticker_analysis  # noqa: E402

# 페이지 key → 렌더러. 단위 (k)/(l) 에서 state/limitations 등록.
_PAGE_RENDERERS = {
    "overview": overview.render,
    "ticker": ticker_analysis.render,
}


def main() -> None:
    """대시보드 entry — 전역 한계 배지 + 사이드바 dispatch."""
    st.set_page_config(
        page_title="한국 KOSPI200 기업 분석 데모",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 전역 한계 배지 (모든 페이지 상단, docs §2.8·§3.4)
    ModelLimitBadge("badge")

    page = SidebarNav("overview")
    renderer = _PAGE_RENDERERS.get(page)
    if renderer is not None:
        renderer()
    else:
        # 단위 (j)/(k)/(l) 에서 구현 예정 페이지 — 임시 안내
        st.info("이 페이지는 준비 중입니다. 왼쪽에서 **개요** 메뉴를 먼저 둘러보세요.")


if __name__ == "__main__":
    main()
