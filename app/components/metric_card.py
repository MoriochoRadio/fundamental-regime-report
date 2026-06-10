"""위험 점수 + 시장 상태 카드 (docs/ui_design.md §2.3·§2.4, U3 카드화).

3 층 구조 (단계 + 수치 + 접는 설명) — 사용자 결정 (Q1).
pure 렌더링 함수 (st.* 직접 호출, 반환 None).

U3 개편 (2026-06):
- 카드를 카드답게 — st.container(border=True) 로 묶음 (헌법 4)
- 색 원 이모지(🟢🟡🔴⚪) → st.badge 교체. badge 색은 config.toml
  redColor/greenColor/orangeColor/grayColor 가 탈채도 팔레트로 정렬
  (app/utils/theme.py BADGE_COLOR_MAP·test_theme 정합).
  텍스트 라벨 항상 병기 — 색맹 대응 (NFR-7) 유지.
- 숫자 위계: config.toml metricValueFontSize = 2.5rem (헌법 2)
"""

from __future__ import annotations

import streamlit as st

from app.utils.formatters import classify_risk, format_percent, state_color
from app.utils.theme import BADGE_COLOR_MAP

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
    """위험 점수 카드 — 테두리 컨테이너 + 3 층 구조 (단계 badge + 수치 + 설명).

    docs/ui_design.md §2.3 spec + U3 카드화.

    Args:
        proba: 0~1 위험 확률 또는 None (분석 평가 제외 시점).
    """
    with st.container(border=True):
        if proba is None:
            # 1 층: 단계 (—) — 결측은 badge 생략 (caption 이 설명)
            st.metric("위험 점수", "—")
            st.caption("분석 평가 제외 시점 (평가 자료 부족)")
        else:
            level, _ = classify_risk(proba)
            # 1 층: 단계 + 색 badge (이모지 대체, 라벨 병기 — 색맹 대응)
            st.metric("위험 점수", level)
            st.badge(level, color=BADGE_COLOR_MAP.get(level, "gray"))
            # 2 층: 수치 (퍼센트 — 날것 확률 노출 금지, format_percent 출력)
            st.caption(f"추정 위험 확률: {format_percent(proba, decimal=1)}")
        # 3 층: 접는 설명 (None 에서도 일반 교육 텍스트 표시)
        with st.expander("이 수치는 무엇인가요?"):
            st.write(RISK_SCORE_EXPLANATION)


def StateCard(state: str | None) -> None:
    """시장 상태 카드 — 테두리 컨테이너 + 3 층 구조 (라벨 badge + 설명).

    docs/ui_design.md §2.4 spec (← Phase 4 RegimeCard 정정) + U3 카드화.

    Args:
        state: 시장 상태 한국어 라벨 ("위험회피"/"중립"/"위험선호") 또는
            None (분석 시작 9 개월간 정확도 낮음).
    """
    with st.container(border=True):
        if state is None:
            st.metric("시장 상태", "—")
            st.caption("분석 시작 9 개월간은 시장 상태 분류 정확도가 낮음")
        else:
            # 1 층 + 2 층: 라벨 + 색 badge (state 는 분류 라벨이라 별도 수치 없음)
            st.metric("시장 상태", state)
            st.badge(state, color=BADGE_COLOR_MAP.get(state, "gray"))
            # state_color 는 향후 차트 차원 사용 (검증 1: regime_color → state_color)
            _ = state_color(state)
        # 3 층: 접는 설명
        with st.expander("이 상태는 무엇인가요?"):
            st.write(STATE_EXPLANATION)
