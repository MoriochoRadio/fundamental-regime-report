# Regime Classification Model Card — 시장 국면 분류

> ⚠️ 본 문서는 기술 차원 별도 자료입니다. 일반인 안내는
> [README](../README.md) 또는 웹 페이지의 한계 페이지를 참조하세요.

**버전**: v0.1 baseline (2026-05-21)
**상태**: ✅ HMM K=3 학습 완료 / ⚠️ **학술 명명 부합 약함 + HMM 시드 불안정성** (정직 박제)
**박제 권위**: PROGRESS §5.6 (D3·D4 결정) + §5.6.1 (HMM 결과) + §5.6.2 (비교)

---

## 1. 모델 명세 (Model Specification)

### 1.1 본 라인 + 비교 대상 (CLAUDE.md §8.4)
- **본 라인**: HMM (Gaussian, `hmmlearn.GaussianHMM`, K=3, full covariance)
- **비교 대상**: GMM (`sklearn.mixture.GaussianMixture`) + K-Means (`sklearn.cluster.KMeans`)
- **하이퍼파라미터**: `n_iter=500`, `tol=1e-3`, `random_state=42` 고정
- **상태 수 K**: 3 (위험회피·중립·위험선호) — 학술 관행 (§5.6 D3 결정)
- **출처**: `src/frr/regime/hmm_classifier.py`, `comparison.py`

### 1.2 Features (D4)
| # | 컬럼 | 정의 |
|---|---|---|
| 1 | ret_20d | KOSPI200 rolling 20일 누적 수익률 (월간 추세) |
| 2 | vol_60d | log return rolling 60일 std × sqrt(252) (분기 변동) |
| 3 | vol_ratio_20_60 | rolling 20일 vol / 60일 vol (변동성 가속) |

**표준화**: rolling 252일 z-score (각 시점 in-sample 통계, **룩어헤드 차단**).

### 1.3 State labeling (사후 명명, §5 정신)
- **위기 점수 = mean(vol_z) − mean(ret_z)** 순 매칭
- 가장 낮음 → 위험선호, 가장 높음 → 위험회피
- 초기 *vol 순 단순 매칭* 부적합 발견 후 정정 (§5.6.1)

---

## 2. 학습 데이터 (Training Data)

- KOSPI200 지수 일간 close (FDR `KS200`)
- 기간: **2015-01-02 ~ 2024-12-30** (10년)
- 원본 obs: 2,458 / warmup drop 후 **2,273 obs**
- 룩어헤드 차단: rolling window 252일 + 60일 — 초기 ~185일 미달 row drop

---

## 3. 평가 결과 (§5.6.1, §5.6.2)

### 3.1 HMM K=3 baseline (random_state=42)
- 수렴 ✓, log-likelihood = -9442.92
- State means (rolling z-score):

| state | 명명 | ret_20d | vol_60d | 위기 점수 |
|---|---|---|---|---|
| 2 | 위험선호 | +0.549 | +0.309 | -0.240 (낮음) |
| 1 | 중립 | -0.752 | -0.008 | +0.744 |
| 0 | 위험회피 | -0.809 | -0.015 | +0.794 (높음) |

- State 분포 (forward filter argmax):
  - 위험선호 1,313 (57.8%) / 중립 607 (26.7%) / 위험회피 353 (15.5%)

### 3.2 전이 행렬 (자기 지속성 강함)
- from 위험회피: → 중립 0.997 (위험회피→중립 거의 항상)
- from 중립: → 위험회피 0.925 (중립 → 위험회피 자주)
- from 위험선호: → 위험선호 0.976 (자기 지속성 매우 강함)

### 3.3 K=2·3·4 BIC·AIC 자동 선택
- **HMM·GMM 모두 K=4 가 최소 BIC·AIC** (도메인 결정 K=3 과 tension)
- K-Means inertia: K 증가에 따라 자연 감소

### 3.4 시드 안정성
| 모델 | log_lik 변동 | 안정성 |
|---|---|---|
| HMM | -9442 ~ -8312 (13.6%) | ⚠️ 불안정 |
| GMM | -10101 ~ -10107 (0.06%) | 안정 |
| K-Means | inertia 0.007% | 매우 안정 |

→ **HMM EM 알고리즘 local optima 의존성** 인지.

### 3.5 도메인 spot-check (2020 코로나 2020-02-15 ~ 05-15, 61 obs)
- 중립 42.6% / 위험선호 29.5% / 위험회피 27.9%
- **학술 정의 부합 약함** — 위기 시점 위험회피 27.9% 만

---

## 4. Limitations (정직 박제)

### 4.1 학술 명명 부합 약함
- state 0 (위험회피, ret -0.809 vol -0.015) = *정체 패턴* (위험회피 학술 정의는 vol ↑)
- state 2 (위험선호, ret +0.549 vol +0.309) = *상승+변동* (위험선호 학술 정의는 vol ↓)
- 모델은 *3 분리* 했으나 학술 표준과 *정확히 매칭 안 됨*

### 4.2 HMM 시드 불안정성
- 5 시드 변동 log-lik 13.6%, BIC 13.4%
- EM 알고리즘 *시작점 sensitivity*
- 단계 4 시각화에 *random_state=42 결과만 사용* 명시

### 4.3 자동 K=4 vs 도메인 K=3 tension
- BIC·AIC 자동 선택은 K=4 가 최소
- 본 카드는 K=3 유지 (학술 관행 + 도메인 해석 가능성)
- K=4 결과는 *대안 시나리오*

### 4.4 코로나 spot-check 부합 약함
- 2020 코로나 위기 시점 위험회비 27.9% 만 (중립 42.6% 더 많음)
- 모델이 *위기 식별 약함* — 단계 4 시각화 시 한계 명시

---

## 5. Intended Use

### 5.1 의도된 사용
- 단계 4 (통합 대시보드) 의 *시장 국면 시각화* — 시계열 + state 표시
- D2 baseline 결과의 *국면-조건부 맥락* 제공
- 방법론 자료 — *3 모델 비교 + 시드 안정성 + 자동 K vs 도메인 K* 진단 박제

### 5.2 의도되지 *않은* 사용
- ❌ 트레이딩 신호·매매 결정 (CLAUDE.md §4.2 OUT)
- ❌ 주가 예측 (CLAUDE.md §3.2 — *주가 예측 아님*)
- ❌ 단일 시드 결과 권위 (반드시 *random_state=42* 명시)
- ❌ 학술 명명 자체 (정의 부합 약함, *사후 해석* 만)

---

## 6. 향후 방향

(A) **피처 확장** — 거래량 변동·매크로 (금리·환율) 추가로 학술 명명 분리
보강 가능성. 단 YAGNI — 단계 4 시각화 후 결정.

(B) **K=4 본 라인 재검토** — BIC·AIC 자동 선택 결과 채택 + *4 상태 도메인
해석 재시도*. 단 K=3 학술 관행 vs K=4 BIC 의 tension 결정 필요.

(C) **HMM 시드 안정화 — multiple-start EM** — 여러 시드로 학습 + log-lik 최고
모델 선택. 시드 sensitivity 완화.

(D) **regime ↔ D2 baseline 통합 평가** — 단계 4 대시보드에서 *각 regime 의
D2 baseline 결과 분포* 시각화. *D2 negative finding 의 regime-conditioned
re-evaluation* 가능.

---

## 7. 재현성

- 시드: `random_state=42` (HMM·GMM·K-Means 모두)
- 환경: Python 3.13, hmmlearn 0.3.3, scikit-learn 1.8.0
- 실행:
  ```bash
  uv run python scripts/train_regime.py
  uv run python scripts/compare_regime_models.py
  ```
- 산출물:
  - `data/interim/regime/results.yaml` (HMM K=3 baseline)
  - `data/interim/regime/state_series.parquet` (2,273 rows date·state)
  - `data/interim/regime/comparison_summary.yaml` (K=2·3·4 + 시드 안정성)
- 외부 데이터: KOSPI200 지수 일간 close (`data/raw/fdr/ks200_index.parquet`)

---

## 8. 단계 3 종료 + 단계 4 진입

본 모델 카드로 **단계 3 (시장 국면 모듈) 종료**. 다음:

- **단계 4 (통합 대시보드)** — Streamlit + plotly (CLAUDE.md §8.5). D2 baseline
  + regime state 시계열 동시 시각화. **모든 limitations 명시** (D2 random 미만 +
  regime 명명 약함). LLM 호출 0회 (런타임).
- **단계 5 (마무리)** — README + docs/methodology.md + 본 두 모델 카드 종합.

단계 3 종료 commit + 단계 4 진입 게이트.
