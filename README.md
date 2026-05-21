# fundamental-regime-report

**기업 펀더멘털 + 시장 국면 인지형 통합 분석 리포트 시스템**

한국 KOSPI200 (point-in-time) 배치 분석 — D2 부실 라벨 스코어링 + HMM 시장
국면 분류 + 통합 시각화.

> **포지셔닝**: 1인 개발자의 포트폴리오 프로젝트. *방법론적 엄밀성*과
> *명확한 스코프*가 모든 기술적 욕심보다 우선합니다. 본 프로젝트는
> **negative finding** (모델 random 미만) 을 *정직 박제*하며 그 자체가
> **D2 정직성 사슬 5 차원 + §7.6 검토 사이클** 의 핵심 가치 입증입니다.

---

## 상태

✅ **단계 1~4 완료** (2026-05-21). 단계 5 (마무리) 진행 중.

- [CLAUDE.md](CLAUDE.md) — 변하지 않는 프로젝트 사실·규칙·방향
- [PROGRESS.md](PROGRESS.md) — 모든 결정·진단·실측 박제 (§5.5/§5.6/§5.7)
- [reports/d2_baseline_model_card.md](reports/d2_baseline_model_card.md) — D2 모델 카드
- [reports/regime_model_card.md](reports/regime_model_card.md) — Regime 모델 카드

---

## ★ 면접 방어 메시지 6 항목 (포트폴리오 핵심 자산)

본 프로젝트의 가치는 *모델 성능* 이 아닌 **정직성 사슬 + 검토 사이클**입니다.
모든 한계는 *정직 박제* 되어 있어 포트폴리오·면접 자산입니다.

### (1) 정직성 사슬 5 차원

| # | 차원 | 박제 위치 | 의미 |
|---|---|---|---|
| 1 | **변수** | PROGRESS §5.5.9 | D2 distress filter 화이트리스트 (`{"자본전액잠식"}`) — 합병 노이즈 7건 제거 |
| 2 | **양성 충분성** | PROGRESS §5.5.10 | forward window 1→2년 ablation 12건 전수 검증 후 *기각* (라벨 의미 균질성 우선) |
| 3 | **격리** | `tests/test_isolation.py` (i)(ii)(iii) | features 모듈의 universe 변수·상폐 메타·OpenDartReader 직접 호출 차단 |
| 4 | **시간** | `src/frr/eval/splits.py` + PROGRESS §5.5.12 | Walk-forward expanding window + embargo = forward_window = 365일 (label 누수 차단) |
| 5 | **LLM 격리** | `tests/test_app_no_llm_import.py` + PROGRESS §5.7 | `app/` LLM SDK import 0 CI gate (CLAUDE.md §3.4 *런타임 LLM 호출 0회* 강제) |

### (2) §7.6 작업 진입 검토 사이클

**모든 작업 단위 진입 *전* 4 단계 통과 의무** (CLAUDE.md §7.6 박제):

1. PROGRESS §5.5.* + §결정 로그 점검
2. `git log -- <대상 파일>` + 최근 커밋 이력 확인
3. 관련 코드 *현 상태* 실측 재읽기
4. 작업 계획·설계 사용자 검토 게이트 통과

자문·실행 양측 모두 적용·예외 없음. §5.5.11 학습 (D10 가정 오류 +
Co-Authored-By 가정 학습) 의 공식 워크플로 박제. *워크플로 자체가 면접
방어 자산*.

### (3) 두 단계 Negative Finding 자산화

| 단계 | Negative finding | 의미 |
|---|---|---|
| **단계 2 (D2 baseline)** | PR-AUC **0.0136** < base rate 0.0205 + ROC-AUC **0.2651** < 0.5 | KOSPI200 부실 사건 *희소성* (§5.5.7) 의 경험적 정량 증명 |
| **단계 3 (HMM regime)** | 명명 학술 부합 약함 + HMM 시드 변동 **13.6%** | 모델 *3 분리* 했으나 학술 표준 위험회피·위험선호 정확 매칭 안 됨. EM local optima 의존 |

두 negative 가 *정직성 사슬 위에서* 증명된 **모집단·도메인 한계**.
*모델 성능 부족이 아닌 *데이터·도메인 본질의 정량 증거*.

### (4) (A) 데이터 보강 시도 — 4 단 layered 정직성 진술

```
baseline negative (PR-AUC 0.0136)
  → class weight ablation 효과 없음 (balanced vs unweighted < 0.001)
  → (A) OFS 재페치 3,583 호출 status 전환 0건
  → DART 직접 응답으로 진짜 데이터 부재 증명
  → KOSPI200 모집단 희소성의 모델·데이터 양측 보완 불가능 증명
```

각 단계가 *직전 시도의 결과를 받아 다음 시도로* 확장. 각 단계마다 *정직
박제* + *데이터 출처 직접 응답으로 종결*.

### (5) 실행 가이드

**환경**:
```bash
# Python 3.13 + uv (재현성)
uv sync --frozen

# DART API 키 (.env)
cp .env.example .env
# DART_API_KEY=... 채우기
```

**데이터**:
```bash
# 1. KOSPI200 분기 CSV 수동 다운로드 (40 분기, ~10분)
# docs/data_sources.md §3 참조 — KRX 정보데이터시스템에서 직접

# 2. 데이터 수집 (DART + KRX + FDR)
uv run python scripts/collect_data.py

# 3. fs_div 라벨 백필 (D10 적용 이전 캐시 호환)
uv run python scripts/backfill_dart_fs_div.py
```

**학습·시각화**:
```bash
# 단계 2 — D2 baseline 학습
uv run python scripts/train_d2_baseline.py

# 단계 3 — HMM 시장 국면 학습 + GMM/K-Means 비교
uv run python scripts/train_regime.py
uv run python scripts/compare_regime_models.py

# 단계 4 — Streamlit 대시보드
uv run streamlit run app/main.py
```

**테스트**:
```bash
# 단위 + 격리 테스트 (CI 기본)
uv run pytest -m "not integration"
# 160 통과 + 1 skip + 7 integration deselected
```

### (6) Future Work

| # | 항목 | 이유 |
|---|---|---|
| 1 | ~~**K=4 ablation (단계 3)**~~ ✅ **완료 (§5.6.4)** | K=4 가 학술 명명 부합 정량 정답 — 코로나 spot-check 위기 state 비중 K=3 27.9% → **K=4 82%** (3배 개선). log-lik -9442.92 → -7640.05. *본 라인 변경은 향후 main 머지 후 검토* (광범위 박제 갱신 필요) |
| 2 | **multiple-start EM** | HMM 시드 불안정성 13.6% 완화 — log-lik 최고 모델 선택 |
| 3 | **Features 확장 (단계 2)** | 성장률·이자보상비율·CFO 마진·운전자본 — 단 모집단 한계로 random 미만 극복 불확실 |
| 4 | **KOSDAQ 확장** | §4.1 B3 기각 사유 (point-in-time 정합성 X) 유지. 미래 대안 — KRX [12006] 일자 입력 활성화 시 |
| 5 | **LLM 빌드타임 배치** | CLAUDE.md §3.4: 서비스 런타임 0회, 빌드타임 1회. 단계 5 잔여 후보 |
| 6 | **단계 3 코로나 spot-check 보강** | 위험회피 27.9% 만 — 피처 확장 또는 K=4 채택으로 재시도 |

---

## 기술 스택

- **언어·런타임**: Python 3.13, uv (lock 고정)
- **데이터**: DART OpenDart + pykrx + FinanceDataReader + KRX 수동 CSV
- **ML**: scikit-learn 1.8 + LightGBM 4.6 + hmmlearn 0.3
- **시각화**: Streamlit + plotly + matplotlib
- **품질**: pytest + ruff + GitHub Actions CI

자세히는 [CLAUDE.md §8](CLAUDE.md) 참조.

---

## 스코프 — 절대 하지 않음

- ❌ 실시간 / 정밀 주가 예측 (CLAUDE.md §4.2)
- ❌ 실시간 트레이딩·매매 신호·신용 평가 대체
- ❌ 다국가 확장·옵션·파생·고빈도 데이터
- ❌ 모집단 확장으로 negative finding 회피 (§5.5.6 B3 기각 유지)

---

## 핵심 박제

| 박제 위치 | 내용 |
|---|---|
| `CLAUDE.md` | 변하지 않는 사실·규칙·방향 (§1~§9) |
| `PROGRESS.md` §5.5/§5.6/§5.7 | 모든 진단·결정·실측·negative finding 박제 |
| `reports/d2_baseline_model_card.md` | D2 모델 카드 8 섹션 |
| `reports/regime_model_card.md` | Regime 모델 카드 8 섹션 |
| `app/main.py` Limitations 페이지 | 6 항목 정직 박제 (시각화) |
| `tests/test_isolation.py` + `test_app_no_llm_import.py` | 정직성 사슬 5 차원 CI 강제 |

---

## 라이선스

[MIT](LICENSE)

---

🤖 Generated with [Claude Code](https://claude.com/claude-code) — 17+ commit 자기 점검 사이클로 모든 결정이 PROGRESS 박제·실측·자문 검토 통과.
