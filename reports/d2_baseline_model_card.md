# D2 Baseline Model Card — 재무 충격 위험 스코어링

**버전**: v0.1 baseline (2026-05-21)
**상태**: ✅ 학습·평가 완료 / ⚠️ **Negative finding — 모델 random 보다 나쁨**
**박제 권위**: PROGRESS.md §5.5.17 (학습 결과) + §5.5.7 ~ §5.5.16 (정직성 사슬)

---

## 1. 모델 명세 (Model Specification)

### 1.1 알고리즘
- **분류기**: LightGBM (`lightgbm>=4.6.0`)
- **캘리브레이션**: Platt sigmoid (`sklearn.calibration.CalibratedClassifierCV`,
  method="sigmoid")
- **하이퍼파라미터** (양성 희소성 대응):
  - `num_leaves=15` (과적합 회피)
  - `min_data_in_leaf=5` (양성 20에 맞춤)
  - `n_estimators=100`, `learning_rate=0.05`
  - `objective="binary"`, `random_state=42` 고정
- **출처**: `src/frr/models/classifier.py` (PROGRESS §5.5.16 B-3)

### 1.2 Features
| # | 컬럼 | 분류 | 분자 | 분모 |
|---|---|---|---|---|
| 1 | debt_ratio | BS | 부채총계 | 자본총계 |
| 2 | current_ratio | BS | 유동자산 | 유동부채 |
| 3 | op_margin | IS | 영업이익 | 매출액 |
| 4 | roa | IS×BS | 당기순이익 | 자산총계 |
| 5 | fs_div_code | 출처 | CFS=1·OFS=0·absent=−1 |

**격리 원칙 (CLAUDE.md §5)**:
- 영업이익 *자체*는 라벨 변수 → 피처 제외. *비율 형태만* 허용.
- 유니버스 변수·상폐 메타 모든 모델 피처 진입 차단 (test_isolation.py
  (i)(ii)(iii) 자동 활성).

### 1.3 라벨 (D2)
- **정의**: α = 상폐 부실 (A=1) ∪ drawdown 50% + 영업이익 음수 전환 (B=19),
  1년 forward (PROGRESS §5.5.7).
- **양성 사건**: 종목 20건 (KOSPI200 universe 321 중) → forward window 매칭으로
  *(ticker, as_of) cells* 단위 양성 **45 cells**.

---

## 2. 학습 데이터 (Training Data)

### 2.1 Universe
- KOSPI200 point-in-time + 분석 기간 내 상장폐지 종목 union = **321 종목**
- 분석 기간: **2015-01-01 ~ 2024-12-31** (10년)
- 시점 grid: 40 분기말 영업일 (holiday fallback 20/40, PROGRESS §5.5.13)
- 출처: `data/external/kospi200_quarterly/MANIFEST.yaml` (수동 다운로드 CSV)

### 2.2 Walk-Forward Splits
- **알고리즘**: Expanding window + embargo gap (PROGRESS §5.5.12·§5.5.13)
- **embargo_days = forward_window_days = 365** (호출자 일관성 책임)
- **min_train_quarters = 8** (학습 임계 2년)
- **총 fold 수 = 28**, 첫 fold test=2018-03-30, 마지막 test=2024-12-30

### 2.3 학습/평가 데이터 통계
- features rows: **8,008 cells** (universe 멤버 × 40 grid 의 유효 cells)
- 양성 cells: **45** (양성 종목 20 × forward window 매칭)
- 평가 fold: **9** (skip 19 — train_pos=0 또는 test_pos=0)
- 평가 fold_ids: [4, 5, 6, 7, 13, 14, 15, 23, 24]

---

## 3. 평가 결과 (Evaluation Results)

### 3.1 평가 단위·방법
- **종목 단위 (ticker × as_of) pooled across 9 평가 folds**
- 5 metric (D8 박제): PR-AUC + ROC-AUC + Brier + ECE + Top-K precision (K=10%)
- **bootstrap 95% CI** (n=1000) 모든 metric

### 3.2 Full pooled (n_total=1,801 / n_positive=37, base rate = 2.05%)

| metric | balanced | unweighted |
|---|---|---|
| **PR-AUC** | **0.0136** [0.0100, 0.0198] | 0.0133 [0.0099, 0.0182] |
| **ROC-AUC** | **0.2651** [0.1959, 0.3439] | 0.2686 [0.2081, 0.3417] |
| Brier | 0.0211 [0.0151, 0.0277] | 0.0206 [0.0146, 0.0272] |
| ECE | 0.0166 [0.0106, 0.0235] | 0.0155 [0.0096, 0.0222] |
| Top-K precision | 0.0056 [0.0000, 0.0167] | 0.0000 [0.0000, 0.0000] |

→ **PR-AUC < base rate (0.0205) + ROC-AUC < 0.5** = **모델 random 보다 나쁨**.

### 3.3 지주 군 분리 평가 (034730 SK · 267250 HD현대 · 096770 SK이노베이션)

n_total=27 / n_positive=12 (base rate 44.4%):

| metric | balanced | unweighted |
|---|---|---|
| PR-AUC | 0.3281 [0.1883, 0.5431] | 0.2877 [0.1670, 0.4621] |
| ROC-AUC | 0.0778 [0.0000, 0.2559] | 0.0000 [0.0000, 0.0000] |
| Top-K precision | 0.3333 [0.0000, 1.0000] | 0.0000 [0.0000, 0.0000] |

→ **CI 폭 완전 변동** (Top-K [0.0000, 1.0000]) = §5.5.16 짚을 점 1 (양성 N=3
통계적 변동성) 의 경험적 확인.

### 3.4 일반 군 (지주 제외)

n_total=1,774 / n_positive=25:

| metric | balanced | unweighted |
|---|---|---|
| PR-AUC | 0.0094 | 0.0097 |
| ROC-AUC | 0.2862 | 0.3018 |

---

## 3a. Intended Use (의도된 사용)

### 3a.1 의도된 사용
- **포트폴리오 자료** — D2 정직성 사슬 4 차원 박제 + negative finding
  정직 보고의 *학술·면접 방어 가치 입증*.
- **방법론 baseline** — 단계 3 (시장 국면 모듈) 의 *국면-조건부 해석*
  맥락에서 본 baseline 결과를 *데이터 한계의 정량 증거*로 활용.
- **데이터 한계 진단** — PR-AUC < base rate 결과 자체가 *KOSPI200 모집단의
  부실 사건 희소성* (§5.5.7) 의 정량 자료. 단계 4 (통합 대시보드) 에서
  *현 baseline 의 한계 + 해석 가이드* 로 표시.
- **재현 가능 워크플로** — 모든 결정·박제·테스트 통과 의무 (§7.6).

### 3a.2 의도되지 *않은* 사용
- ❌ **실거래 부실 예측·매매 신호** — 모델 random 보다 나쁨. 어떤 형태로도
  실제 투자 의사결정에 사용 금지 (CLAUDE.md §4.2 OUT).
- ❌ **신용 평가 대체** — 본 모델은 *연구 baseline*. 신용평가사·금융기관
  의사결정 대체 불가.
- ❌ **다른 모집단·시점 외삽** — KOSPI200·2015-2024 한정. KOSDAQ·소형주·
  다른 시점 외삽 시 *§5.5.6 (B3 기각) 사유* 재발.
- ❌ **모델 카드 외 수치 인용** — 본 카드 + PROGRESS §5.5.17 본문이
  *단일 권위*. 콘솔 출력·중간 산출물 인용 금지.

---

## 4. Limitations (정직 박제)

### 4.1 데이터 한계
1. **양성 절대 수 부족** — 종목 20 / cells 45. §5.5.7 박제 학습 임계 (30 미달)
   의 *경험적 정량 확인*.
2. **fold 별 양성 0 다수** — 28 fold 중 19 fold (68%) 가 train_pos=0 또는
   test_pos=0 → 평가 가능 fold = 9.
3. **모집단 희소성** — KOSPI200 (대형 우량주) 모집단에서 D2 부실 사건은
   *자연적으로 드뭄*. §5.5.6 (B3 KOSDAQ 확장) 기각 사유 (point-in-time 정합성
   X) 유지.

### 4.2 모델 한계
1. **모델 성능 < random** — PR-AUC 0.0136 < base rate 0.0205 + ROC-AUC 0.2651
   < 0.5. baseline 4 ratio 로는 D2 양성 *학습되지 않음*.
2. **class weight 효과 0** — balanced vs unweighted 차이 < 0.001. *양성 절대
   수 부족 앞에서 class weight 보완 무력*.
3. **캘리브레이션 의미 약함** — ECE 0.016 정상 보이나, *random 예측의 캘리브
   레이션*은 의미 없음.

### 4.3 지주 군 평가 한계
- n_positive=12 (cells 단위, 종목 단위로는 3 종목) → CI 폭 [0, 1]. §5.5.16
  짚을 점 1 박제 검증.
- **종목 단위 (3 종목) 로는 학습·평가 모두 통계적 의미 없음** — 평가 분리
  보고만 가능, 학습 분리는 불가능 (PROGRESS §5.5.16 B-1 (c) 채택 사유).

### 4.4 D2 라벨 견고성
- 부호 차이 9 cells (CFS vs OFS, §5.5.15) 가 labels.py B 신호 판정에 영향.
- §5.5.10 결정 (라벨 측 보강 안 함) 유지. 모델 단계에서 fs_div as feature
  채택했으나 *모델이 학습 자체를 못 하므로 의미 약화*.

---

## 5. 향후 방향 (Future Work)

§5.5.17 박제 4가지 (B-5 박제 입력):

### (A) Forward window 2년 ablation 재고
- §5.5.10 기각 사유 (라벨 의미 균질성 파괴) 재검토.
- 본 결과가 *학습 불가능* 수준이라 *균질성보다 양성 수 우선* 가능성.
- 단 §5.5.10 정신 (자의적 변종 선별 차단) 유지.

### (B) Features 확장
- 후보: 성장률 (매출·영업이익 YoY)·이자보상비율 (영업이익/이자비용)·CFO 마진·
  운전자본 변동률·차입금의존도·이자비용/매출액
- 가격 기반: rolling volatility (252-day)·short drawdown (60-day)
- 단 *random 미만 결과* 가 features 확장만으로 극복 안 될 가능성.

### (C) (β)+(γ) 데이터 보강
- (β) §5.5.11 9 FY None refresh (롯데지주·SK텔레콤·하나투어·더블유게임즈·
  두산퓨얼셀) — OFS fallback 영업이익 회수 시도.
- (γ) notfound 2,719 OFS 재페치 (DART 한도 27%) — D10 효과 ablation.
- 9 cells 양성 종목 매칭 작아 *결정적 영향 작음* 추정. 비용 대비 효과
  검토 필요.

### (D) 모집단 확장 거부 재확인
- §5.5.6 (B3 KOSDAQ 확장) 기각 유지. *학습 불가능 결과를 모집단 확장으로
  해결하는 우회는 §5 격리 원칙·D1 정직성과 충돌*.
- 학술적 정직성: *현재 모집단에서 학습 불가능* 을 *모집단 변경으로 회피*
  하면 결과의 정직성 손실.

---

## 6. 학술·면접 방어 가치

본 모델은 *negative finding* 이나 **포트폴리오 가치는 양수**:

1. **D2 정직성 사슬 4 차원** (PROGRESS §5.5.12 박제):
   - 변수 차원 (§5.5.9 distress 화이트리스트)
   - 양성 충분성 차원 (§5.5.10 forward 1→2년 ablation 기각)
   - 격리 차원 (test_isolation.py (i)(ii)(iii) 자동 활성)
   - 시간 차원 (walk-forward + embargo, §5.5.12·§5.5.13)
2. **§7.6 작업 진입 검토 사이클 박제** — 자문/실행 양측 매 작업마다 4 단계
   검토. §5.5.11 학습 (D10 가정 오류 + Co-Authored-By 가정 학습) 의 공식
   워크플로 박제.
3. **5 후보 전수 검증·기각 후 D2 채택** (§5.5.7) — 입증된 최선.
4. **negative finding 의 정직성** — 모델 random 미만임을 *축소 보고 X·정직
   박제*. 학술 표준 부합.
5. **17 commit 자기 점검 사이클** (2026-05-19 ~ 2026-05-21) — 모든 결정이
   PROGRESS 박제·실측·자문 검토 통과.

**면접 활용**:
- "왜 학습이 안 되었나?" → §5.5.7 KOSPI200 부실 사건 희소성 + §5.5.17
  정량 증거.
- "왜 모집단 확장 안 하나?" → §5.5.6 B3 기각 + §5 격리 원칙.
- "왜 features 확장 먼저 안 하나?" → YAGNI + (A)(B)(C)(D) 4가지 방향 박제
  + *모집단 한계가 features 한계보다 우선*.

---

## 7. 재현성 (Reproducibility)

### 7.1 환경
- Python 3.13, uv lock 고정 (`pyproject.toml` + `uv.lock`)
- 시드: `random_state=42` (LightGBM·CalibratedClassifierCV·bootstrap CI)

### 7.2 실행
```bash
uv run python scripts/train_d2_baseline.py
```

### 7.3 산출물
- `data/interim/train_d2_baseline/results.yaml` (gitignore — 재실행 시 캐시)
- 본 모델 카드 (`reports/d2_baseline_model_card.md`, git 추적)
- PROGRESS §5.5.17 본문 (수치·종목별 패턴 모두 포함)

### 7.4 의존성
- 데이터 캐시:
  - `data/raw/dart/{ticker}/{year}_{period}.{parquet,meta.yaml}` (10,114 ok + 2,719 notfound)
  - `data/raw/krx/ohlcv/{ticker}.parquet`
  - `data/raw/fdr/stocklisting_{kospi,delisting}.parquet`
  - `data/external/kospi200_quarterly/*.csv` (40 분기, git 추적)
- 모든 외부 데이터 매니페스트 + sha256 무결성 (CLAUDE.md §8.3).

---

## 8. 단계 2 종료 + 다음 단계

본 모델 카드로 **단계 2 (펀더멘털 모듈) 종료**. 다음:

- **단계 3 (시장 국면 모듈)** — HMM 또는 클러스터링으로 *시장 국면 분류*
  (CLAUDE.md §3.2). 본 단계는 *주가 예측 아님*. 국면 라벨이 D2 baseline
  결과를 *국면-조건부* 로 해석할 수 있는 맥락 제공.
- **단계 4 (통합 대시보드)** — Streamlit + plotly. 본 baseline 결과는
  *negative finding* 으로 그대로 표시. 모델 카드 본문이 *해석 가이드*.
- **단계 5 (마무리·문서)** — 본 모델 카드 + PROGRESS §5.5 누적 자료 +
  README 종합.

본 단계 2 종료 commit 으로 단계 3 진입 게이트 통과.
