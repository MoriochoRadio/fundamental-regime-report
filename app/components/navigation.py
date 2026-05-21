"""사이드바 네비게이션 (docs/ui_components.md §1.10)."""

from __future__ import annotations

import streamlit as st

PAGES = [
    ("개요", "overview"),
    ("★ 종목 분석", "ticker"),
    ("시장 국면", "regime"),
    ("D2 baseline 결과", "d2"),
    ("⚠️ Limitations (방법론적 특징)", "limitations"),
]


def render_sidebar_nav(default: str = "overview") -> str:
    """사이드바 페이지 selector. 선택된 page key (str) 반환."""
    label_to_key = dict(PAGES)
    labels = list(label_to_key.keys())
    # session_state 동기화 — CTA 버튼이 페이지 변경 시 default 갱신
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = default
    current_key = st.session_state["current_page"]
    # current_key → label
    key_to_label = {v: k for k, v in label_to_key.items()}
    default_label = key_to_label.get(current_key, labels[0])
    selected_label = st.sidebar.radio(
        "페이지 선택",
        labels,
        index=labels.index(default_label),
    )
    selected_key = label_to_key[selected_label]
    st.session_state["current_page"] = selected_key
    return selected_key
