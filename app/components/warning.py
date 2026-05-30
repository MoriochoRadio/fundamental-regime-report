"""한계 배지 + 빈 상태 컴포넌트 — ModelLimitBadge, EmptyState.

docs/ui_design.md §2.8·§2.9·§3.4·§1.4. pure 렌더링 함수 (st.* 직접 호출,
반환 None). 토큰 추상 미구현 → 단위 d/e 동형 직접 st.* 사용.

★ docs §2.8 박제: 원본 ML 수치 (PR-AUC·base rate 등) 노출 *금지*.
일반인 친화 정직 문구만 사용 (test_warning.py 비노출 회귀로 박제).

Phase 4 자산 변환:
- (B) 정정: render_model_limit_warning(context) → ModelLimitBadge(variant),
  render_empty_state(title, description, action, icon) →
  EmptyState(message, suggestion) (검증 1, PascalCase 통일)
- (D) 폐기: LIMIT_MESSAGES dict 의 PR-AUC 수치 문구 전부 (§2.8 금지) +
  context 4 키 (ticker/regime/d2/limitations) → variant 3 종 재설계 +
  render_empty_state 의 (title, description, action, icon) 4-인자 시그너처
- (E) 신규: variant 분기 본문 (docs §3.4·§1.4 verbatim) +
  EmptyState 기본 메시지 (docs §2.9)
"""

from __future__ import annotations

import streamlit as st

# 모든 페이지 상단 배지 + 첫 진입 모달 본문 (docs §3.4, ML 수치 노출 금지)
_BADGE_TEXT = "⚠️ 본 시스템은 시연용 데모입니다. 실제 투자에 사용 금지."

# 한계 페이지 전체 본문 — 3 한계 항목 (docs §1.4 verbatim, 일반인 친화)
_PAGE_INTRO = (
    "본 시스템은 *방법론과 데이터의 정직성 시연*용입니다. 다음 3 가지 한계를 명확히 안내합니다."
)
_PAGE_LIMITS = [
    (
        "1. 모델 위험 예측 정확도",
        "본 시스템의 위험 예측은 실제 사건을 거의 맞히지 못합니다. "
        "본 시스템은 *방법론과 데이터의 정직성 시연*용입니다.",
    ),
    (
        "2. 시장 상태 분류 초기 9 개월",
        "분석 시작 9 개월간 (2015-01 ~ 2015-09) 은 시장 상태 분류 "
        "정확도가 낮습니다. 이 기간은 *부분 표시* 또는 *경고* 로 안내합니다.",
    ),
    (
        "3. 분석 범위",
        "한국 KOSPI200 (한국 대표 200 대 기업) 만 분석합니다. "
        "그 외 종목은 *데이터 없음* 으로 표시됩니다.",
    ),
]

# 빈 상태 기본 메시지 (docs §2.9, Phase 4 "skipped fold — 양성 0" 정정)
_EMPTY_DEFAULT = "이 시점은 평가 자료 부족으로 분석 제외"


def ModelLimitBadge(variant: str = "badge") -> None:
    """모델 한계 안내 — variant 별 (배지 / 모달 / 한계 페이지 전체).

    docs/ui_design.md §2.8 spec + §3.4 문구.

    ★ 원본 ML 수치 (PR-AUC·base rate 등) 노출 금지 (docs §2.8) — 일반인
    친화 정직 문구만 (test_warning.py 비노출 회귀로 박제).

    Args:
        variant: "badge" (모든 페이지 상단) / "modal" (첫 진입) /
            "page_full" (한계 페이지 전체 본문). 미지정·미지원 값은
            기본 badge 로 fallback.
    """
    if variant == "page_full":
        st.markdown("# 본 시스템의 한계")
        st.write(_PAGE_INTRO)
        for heading, body in _PAGE_LIMITS:
            st.markdown(f"## {heading}")
            st.write(body)
        st.markdown("## 데모 명시")
        st.warning(_BADGE_TEXT)
        return

    # "badge" / "modal" / fallback — 동일 배지 본문 (docs §3.4)
    st.warning(_BADGE_TEXT)


def EmptyState(message: str = _EMPTY_DEFAULT, suggestion: str | None = None) -> None:
    """빈 상태 안내 박스 — 📭 아이콘 + 안내 + 다음 행동.

    docs/ui_design.md §2.9 spec. 데이터 없음·시점 평가 제외·산출물 부재 시.

    Args:
        message: 빈 상태 안내 문구 (기본: 평가 자료 부족 안내).
        suggestion: 다음 행동 제안 (예: "다른 시점 선택"). None 이면 미표시.
    """
    st.markdown(f"### 📭 {message}")
    if suggestion:
        st.info(f"💡 {suggestion}")
