"""시장 국면 모듈 — HMM 본 라인 + GMM·K-Means 비교 (단계 3, PROGRESS §5.6).

CLAUDE.md §3.2 박제:
- 데이터: KOSPI200 지수 수익률·변동성
- 방법: HMM (hmmlearn) 본 라인 + GMM·K-Means 비교
- **주가 예측 아님** (CLAUDE.md §4.2 OUT) — 국면 분류·맥락 제공만

D3·D4 결정 (PROGRESS §5.6):
- K=3 (위험회피·중립·위험선호)
- 3 피처: rolling 20일 수익률 + 60일 실현 변동성 + 20/60 변동성 비율
- 시점 정렬: forward-only filtering (Viterbi backward smoothing 회피)
- State labeling: 사후 명명 (평균 수익률·변동성 기준)
"""
