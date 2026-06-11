"""한계 페이지 (docs/ui_design.md §1.4) — 페이지 통합 4/4.

render() — main.py shell 이 dispatch (page key "limitations").
ModelLimitBadge("page_full") 위임(일반어 정직 한계, ML 수치 0) + 기술 자료
모델 카드 *경로 링크 mention*.

★ §7.7 핵심: 정직함은 일반어로 화면에, 원본 ML 평가 수치는 기술 문서
(reports/*.md) 에 격리 — 본 페이지는 카드 *내용을 inline 렌더하지 않는다*.
- Q1 (A): 모델 카드 경로 링크 mention only.
- Q2 (A): load_model_card 는 *존재 확인 gate* 용도만 — 반환 str 은 st 에 미렌더.
- Q3 (A): PageHeader 생략 (page_full 이 h1 self-contained).
ModelLimitBadge 는 본 페이지에서 page_full 로 직접 호출 (shell 의 badge 와 별개).
"""

from __future__ import annotations

import streamlit as st

from app.components import ModelLimitBadge
from app.data_loader import load_model_card

# 모델 카드 (name, 일반인용 라벨, 저장소 경로) — docs §1.4 "기술 자료 (별도 노출)"
# U5: 경로 텍스트 → GitHub 클릭 링크
_REPO_URL = "https://github.com/MoriochoRadio/fundamental-regime-report"
_MODEL_CARDS = [
    ("d2_baseline", "위험 예측 모델 상세", "reports/d2_baseline_model_card.md"),
    ("regime", "시장 상태 분류 모델 상세", "reports/regime_model_card.md"),
]


def render() -> None:
    """한계 페이지 렌더 — page_full 본문 + 기술 자료 링크."""
    # 한계 페이지 전체 본문 (h1 + intro + 3 한계 + 데모 명시, 일반어·ML 수치 0)
    ModelLimitBadge("page_full")

    # 기술 자료 — 모델 카드 경로 링크 (내용 inline 렌더 안 함, §7.7 격리)
    available = [(label, path) for name, label, path in _MODEL_CARDS if load_model_card(name)]
    if available:
        st.markdown("## 기술 상세 자료")
        for label, path in available:
            st.markdown(f"- [{label}]({_REPO_URL}/blob/main/{path})")
        st.markdown(f"- [방법론 통합 문서]({_REPO_URL}/blob/main/docs/methodology.md)")
        st.caption(
            "기술 차원 문서입니다 — 클릭하면 저장소에서 열립니다 (일반인 직접 노출 본문 아님)."
        )
