"""사이드바 네비게이션 컴포넌트 — SidebarNav.

docs/ui_design.md §2.10·§3.1. pure 렌더링 함수 (st.* 직접 호출).

Q1 (A): st.sidebar.radio selector + 선택 key 반환 (st.navigation 미사용 —
app/pages/ 미생성, 페이지 조립 단계에서 main.py if/elif dispatch 와 연결).
Q2 (A): stateless — 내부 session_state 없음, current_page 입력만.
Q3 (A): radio 네이티브 강조 + "● 현재 페이지" caption (라벨 "●" prefix 금지).

Phase 4 자산 변환:
- (B) 정정: render_sidebar_nav → SidebarNav, "시장 국면" → "시장 상태"
  (검증 1, regime → state), 메뉴 5 → 4
- (D) 폐기: "D2 baseline 결과" 페이지 (메뉴 5→4) + "★"·"⚠️ (방법론적
  특징)" 장식 라벨 + 내부 st.session_state 동기화
- (E) 신규: docs §3.1 4-라벨 + current_page 강조 + "● 현재 페이지"
"""

from __future__ import annotations

import streamlit as st

# 4-페이지 메뉴 (라벨, key) — docs §3.1·§2.10 (5→4, D2 baseline 페이지 폐기)
_PAGES = [
    ("개요", "overview"),
    ("종목 분석", "ticker"),
    ("시장 상태", "state"),
    ("한계", "limitations"),
]


def SidebarNav(current_page: str = "overview") -> str:
    """사이드바 4-페이지 selector. 선택된 페이지 key (str) 반환.

    docs/ui_design.md §2.10 spec + §3.1 라벨.

    Args:
        current_page: 현재 페이지 key (기본 선택 강조). 미지 key 는
            첫 페이지("overview") 로 fallback.

    Returns:
        선택된 페이지 key ("overview"/"ticker"/"state"/"limitations").
    """
    labels = [label for label, _ in _PAGES]
    label_to_key = {label: key for label, key in _PAGES}
    key_to_label = {key: label for label, key in _PAGES}

    # 미지 current_page → 첫 페이지 fallback (방어 입력)
    default_label = key_to_label.get(current_page, labels[0])

    selected_label = st.sidebar.radio(
        "페이지 선택",
        labels,
        index=labels.index(default_label),
    )
    st.sidebar.caption("● 현재 페이지")
    return label_to_key[selected_label]
