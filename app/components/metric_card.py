"""위험 점수 + 시장 상태 카드 (docs/ui_design.md §2.3·§2.4).

3 층 구조 (단계 + 수치 + 접는 설명) — 사용자 결정 (Q1).
pure 렌더링 함수 (st.* 직접 호출, 반환 None).

Phase 4 자산 변환:
- (B) 정정: render_risk_score_card → RiskScoreCard, render_regime_card →
  StateCard (검증 1), regime_color → state_color (단위 a)
- (D) 폐기: render_label_card + render_fs_div_card (ML 라벨·재무 출처,
  검증 2·4, 3 단계 §2 spec 부재) + class_weight 파라미터 (ablation ML 차원)
- (C) 재사용 + (E): classify_risk·format_percent·state_color (단위 a)
- 색 = 이모지 (Q3, unsafe_allow_html 폐기, 색맹 대응 NFR-7)
"""

from __future__ import annotations

import streamlit as st

from app.utils.formatters import classify_risk, format_percent, state_color

# 위험 단계 → 색 이모지 (Q3: unsafe_allow_html 폐기, 색맹 대응)
_RISK_EMOJI = {"낮음": "🟢", "중간": "🟡", "높음": "🔴", "—": "⚪"}
# 시장 상태 → 색 이모지
_STATE_EMOJI = {"위험회피": "🔴", "중립": "⚪", "위험선호": "🟢"}

RISK_SCORE_EXPLANATION = (
    "이 점수는 해당 기업이 앞으로 1년 안에 '재무 충격'을 겪을 가능성을 "
    "모델이 추정한 값입니다. '재무 충격'은 (1) 부실로 인한 상장폐지, 또는 "
    "(2) 주가가 절반 이하로 떨어지면서 영업이익이 흑자에서 적자로 돌아서는 "
    "경우를 뜻합니다. 숫자가 높을수록 위험 신호가 강하며, '낮음·중간·높음'은 "
    "이 숫자를 한눈에 보기 쉽게 단계로 나눈 것입니다. 단, 과거 데이터로 "
    "학습한 추정치이므로 미래를 확정하지는 않습니다."
)

STATE_EXPLANATION = (
    "시장 상태는 그 시점의 전체 주식시장 분위기를 모델이 분류한 것입니다. "
    "'위험회피'는 투자자들이 위험을 피하려는 신중한 국면, '위험선호'는 "
    "위험을 감수하려는 활발한 국면, '중립'은 그 사이를 뜻합니다. 이는 "
    "주가를 예측하는 것이 아니라, 같은 재무 상태라도 시장 분위기에 따라 "
    "다르게 읽기 위한 '배경 정보'입니다."
)


def RiskScoreCard(proba: float | None) -> None:
    """위험 점수 카드 — 3 층 구조 (단계 + 퍼센트 + 접는 설명).

    docs/ui_design.md §2.3 spec + 사용자 결정 (3 층 구조).

    Args:
        proba: 0~1 위험 확률 또는 None (분석 평가 제외 시점).
    """
    if proba is None:
        # 1 층: 단계 (—)
        st.metric("위험 점수", f"{_RISK_EMOJI['—']} —")
        st.caption("분석 평가 제외 시점 (평가 자료 부족)")
    else:
        level, _ = classify_risk(proba)
        emoji = _RISK_EMOJI.get(level, "⚪")
        # 1 층: 단계 (낮음/중간/높음 + 이모지)
        st.metric("위험 점수", f"{emoji} {level}")
        # 2 층: 수치 (퍼센트 — 날것 확률 노출 금지, format_percent 출력)
        st.caption(f"추정 위험 확률: {format_percent(proba, decimal=1)}")
    # 3 층: 접는 설명 (None 에서도 일반 교육 텍스트 표시)
    with st.expander("이 수치는 무엇인가요?"):
        st.write(RISK_SCORE_EXPLANATION)


def StateCard(state: str | None) -> None:
    """시장 상태 카드 — 3 층 구조 (단계 + 라벨 + 접는 설명).

    docs/ui_design.md §2.4 spec (← Phase 4 RegimeCard 정정).

    Args:
        state: 시장 상태 한국어 라벨 ("위험회피"/"중립"/"위험선호") 또는
            None (분석 시작 9 개월간 정확도 낮음).
    """
    if state is None:
        st.metric("시장 상태", "⚪ —")
        st.caption("분석 시작 9 개월간은 시장 상태 분류 정확도가 낮음")
    else:
        emoji = _STATE_EMOJI.get(state, "⚪")
        # 1 층 + 2 층: 단계 (= 라벨, state 는 분류 라벨이라 별도 수치 없음)
        st.metric("시장 상태", f"{emoji} {state}")
        # state_color 는 향후 차트 차원 사용 (검증 1: regime_color → state_color)
        _ = state_color(state)
    # 3 층: 접는 설명
    with st.expander("이 상태는 무엇인가요?"):
        st.write(STATE_EXPLANATION)
