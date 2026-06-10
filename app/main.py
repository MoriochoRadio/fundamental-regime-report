"""Streamlit 대시보드 entry point — thin shell (U1 네비 개편).

CLAUDE.md §8.6 박제:
- 정적 읽기 전용 (런타임 LLM 호출 0회·학습·계산·페치 0회)
- reports/ + data/interim/ 정적 산출물만 읽음

실행:
    uv run streamlit run app/main.py

★ 절대 import (from app.X) — Streamlit 은 스크립트 디렉토리(app/)만 sys.path
에 추가하므로 repo-root 를 명시 주입한다. tests/test_app_no_llm_import.py 의
cwd=app/ import 검증(절대 import + 명시 sys.path 처리)도 이 주입으로 통과.

페이지 라우팅 (U1 개편):
- `st.navigation(build_nav_pages())` 단일 한글 메뉴 — v2 멀티페이지.
  st.navigation 호출이 app/pages/ 폴더의 v1 자동 등록(영문 메뉴)을 끈다
  (이중 네비 해소 근거: app/components/navigation.py docstring 실측 기록).
- v2 에서도 main 스크립트가 매 페이지 공통 실행 → 전역 배지 유지.
- set_page_config 에 page_title 미지정 → 브라우저 탭 제목 = 현재 Page title.
"""

from __future__ import annotations

import sys
from pathlib import Path

# repo-root 주입 — `streamlit run app/main.py` + cwd=app/ 양쪽에서 절대 import 보장
_REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import streamlit as st  # noqa: E402

from app.components import ModelLimitBadge  # noqa: E402
from app.components.navigation import build_nav_pages  # noqa: E402


def main() -> None:
    """대시보드 entry — 전역 한계 배지 + st.navigation 단일 메뉴."""
    st.set_page_config(
        page_icon=":material/monitoring:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 전역 한계 배지 (모든 페이지 상단, docs §2.8·§3.4)
    ModelLimitBadge("badge")

    pg = st.navigation(build_nav_pages())
    pg.run()


if __name__ == "__main__":
    main()
