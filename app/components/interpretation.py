"""시장 상태 조건부 해석 컴포넌트 — StateInterpretBox.

docs/ui_design.md §2.7·§3.5·§3.1. 프로젝트 정체성 핵심 (CLAUDE.md §3.3
통합 레이어 — 국면-조건부 해석). pure 렌더링 함수 (st.* 직접 호출, 반환 None).

★ CLAUDE.md §3.4 박제: llm_text 는 *빌드타임 배치 산출물* 을 입력으로만
받는다. 컴포넌트 런타임 LLM 호출 0회 (정적 텍스트 렌더만).

★ docs §2.7·§5(1) 박제: ML 차원 의미가 사라진 *일반 차원 표현* 만 사용.
"random 미만"·raw ratio 수치·전이확률 등 ML 문구 노출 금지 (회귀 테스트).
한계 고백은 단위 f ModelLimitBadge 책임 (역할 분리).

Phase 4 자산 변환:
- (B) 정정: render_regime_conditional_box → StateInterpretBox,
  regime → state, "국면" → "시장 상태" (검증 1)
- (D) 폐기: _CAVEAT ("random 미만" 성능) + raw ratio 수치 부착 (:.4f) +
  전이확률 "0.925" + ticker_features·ticker_name 파라미터 +
  regime-only 3-template
- (E) 신규: state × risk 9 조합 template (docs §3.5 verbatim) +
  risk_level 파라미터 + llm_text 합성
"""

from __future__ import annotations

import streamlit as st

# 시장 상태 × 위험 수준 9 조합 조건부 해석 (docs §3.5 verbatim)
# 키: (state 한국어, risk_level 한국어) — Q2 (A): classify_risk 출력 정합
_TEMPLATES = {
    ("위험회피", "낮음"): "위험회피 시장 상태에서 양호 재무는 비교적 안정적입니다.",
    ("위험회피", "중간"): "위험회피 시장 상태에서 중간 위험 수준은 추가 관찰이 필요합니다.",
    ("위험회피", "높음"): "위험회피 시장 상태에서 높은 위험 수준은 신중한 검토가 필요합니다.",
    ("중립", "낮음"): "중립 시장 상태에서 양호 재무는 안정적입니다.",
    ("중립", "중간"): "중립 시장 상태에서 중간 위험 수준은 일반적 범주에 속합니다.",
    ("중립", "높음"): "중립 시장 상태에서 높은 위험 수준은 주의가 필요합니다.",
    ("위험선호", "낮음"): "위험선호 시장 상태에서 양호 재무는 매우 안정적입니다.",
    (
        "위험선호",
        "중간",
    ): "위험선호 시장 상태에서 중간 위험 수준은 시장 흐름에 영향을 받을 수 있습니다.",
    (
        "위험선호",
        "높음",
    ): "위험선호 시장 상태에서 높은 위험 수준은 시장 회복 시에도 주의가 필요합니다.",
}

# 미지 state/risk·None 방어 fallback (예외 없이 일반 안내)
_FALLBACK = "시장 상태 또는 위험 수준 정보가 충분하지 않아 조건부 해석을 제공할 수 없습니다."


def StateInterpretBox(
    state: str | None,
    risk_level: str | None,
    llm_text: str | None = None,
) -> None:
    """시장 상태 × 위험 수준 조건부 한국어 해석 박스.

    docs/ui_design.md §2.7 spec + §3.5 9 조합 template.

    ★ llm_text 는 빌드타임 배치 산출물 입력 (런타임 LLM 호출 0회,
    CLAUDE.md §3.4). 있으면 서술 1 단락 추가, 없으면 template 만.

    Args:
        state: 시장 상태 한국어 라벨 ("위험회피"/"중립"/"위험선호") 또는 None.
        risk_level: 위험 수준 한국어 라벨 ("낮음"/"중간"/"높음") 또는
            None/"—" (방어 입력). Q2 (A): classify_risk 출력 정합.
        llm_text: 빌드타임 생성 서술 (정적 입력). None 이면 template 만.
    """
    body = _TEMPLATES.get((state, risk_level), _FALLBACK)
    if llm_text:
        body = f"{body}\n\n{llm_text}"
    st.info(body)
