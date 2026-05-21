"""app/ — Streamlit 대시보드 (단계 4, PROGRESS §5.7).

CLAUDE.md §8.6 박제:
- 정적 읽기 전용. 학습·계산·LLM 호출 *금지*.
- 외부 LLM SDK import 0 (CI 검사 의무, §3.4).
- reports/ 의 정적 JSON·MD 와 models/ 학습 모델만 읽음.

단계 4 본 라인:
- D2 baseline 결과 + regime state 시계열 동시 시각화
- 모든 limitations 정직 표시 (§5.5.17 + §5.6.1 + §5.6.2)
- 면접 방어 자료 — *negative finding 의 정직성 + D2 정직성 사슬 4 차원
  + 모집단 한계 정량 증명*
"""
