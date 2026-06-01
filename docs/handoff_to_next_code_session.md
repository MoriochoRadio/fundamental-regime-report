# Handoff to Next Code Session — Phase 4 리셋 컨텍스트

**작성일**: 2026-05-21 (세션 한도 도달 직전 박제)
**작성자**: 자문 측 (직전 세션 종료 시점)
**대상**: 다음 Code 세션이 *0 단계 (Phase 4 폐기) + 1 단계 (요구사항 명세)* 진입할 때 컨텍스트 전달

---

## 0. 즉시 알아야 할 정보

| 항목 | 값 |
|---|---|
| **현재 작업 브랜치** | `claude/competent-jackson-a02ec0` |
| **워크트리 경로** | `C:\Users\neo62\FinanceProj\.claude\worktrees\competent-jackson-a02ec0` |
| **마지막 commit (HEAD)** | `220d1ac feat(app): Phase 4 — component·page·utils 분리 + slim main entry` |
| **상태** | **Phase 4 폐기 결정** (사용자 검토 후) — 다음 세션 0 단계에서 revert |
| **워킹 트리** | clean (미커밋 변경분 0) |
| **origin/main 대비** | 41 commits ahead |
| **GitHub PR 상태** | PR #1·#2 merged (main 까지 반영). Phase 4 commit `220d1ac` 은 PR 없이 push 됨 |

---

## 1. Phase 4 폐기 결정 배경

### 사용자 보고 (3 가지 본질 문제)

1. **TypeError 잔존** — `fig.add_vline(x=pd.Timestamp)` 가 plotly shape annotation 내부의 Timestamp 산술에서 실패. commit `33a897f` 의 핫픽스 + commit `220d1ac` 의 Phase 4 구현 *둘 다* `.to_pydatetime()` 적용했음에도 *실행 검증 부재* 로 잔존 확률.
2. **UI 사용자 친화성 0** — 일반인이 이해 가능한 시각 표현 부재. 데이터 dump 수준.
3. **렉 (성능)** — 페이지 로딩 느림. 성능 정책 부재 (caching·lazy load·page split 등).

### 사용자 진단 종합

"Phase 4 Auto mode 압축이 다음 4 가지 누락의 복합 실패":

1. **vline TypeError 잔존** — `commit 220d1ac` 의 "§5.9 학습 자기적용" 박제가 실행과 불일치. 박제 권위 vacuous (§5 원칙 5 위반).
2. **UI 사용자 친화성 0**.
3. **렉**.
4. **사용자 시나리오 부합 약함** — 단계 4 후 두 번째 같은 누락.

---

## 2. 자문 측 자기 점검 4 항목 (정직 인정)

### (a) Auto mode 압축 위험 경고 부족

Phase 4 진입 시 사용자가 "Auto mode 압축 — 5 cycle 을 1-2 메시지로 완료 (권장)" 선택했음. 자문 측이 *"권장"* 으로 표시했으나 *Auto mode 압축의 위험* (실행 검증 부재·사용자 직접 검토 누락·시각 회귀 부재) 을 사전에 강하게 경고 안 함.

### (b) §5.9 학습 자기적용의 vacuous 통과

§5.9 박제 = "streamlit-like sys.path 환경에서 import 검증 의무". Phase 4 commit `220d1ac` 의 메시지에 "§5.9 학습 자기적용 (5번째 누락 방지): streamlit-like sys.path 환경 import 검증 통과" 명시. 그러나:

- *import 통과* 만 검증, *실제 페이지 렌더링·인터랙션·시각 결과 검증 0회*
- "박제 권위가 실행 검증을 대체할 수 없음" 의 직접 사례
- §5 원칙 5 (vacuous prototype) 위반

### (c) UI/UX 측면 자문 측 약점

자문 측은 *코드 검토·테스트·박제 정직성* 에는 강함. 그러나 *시각적 완성도·인터랙션 UX·사용자 친화성* 은 *실제 사용자가 직접 사용해 봐야 검증 가능* — 자문 측 코드 검토만으로는 *원리적으로 검증 불가*.

`docs/ux_design.md` + `docs/ui_components.md` 박제는 *명세는 좋으나 구현 결과의 UX 품질을 자체 검증 못 함*. 사용자 직접 검증 의무.

### (d) 작업 분량 추정 오류

Phase 4 를 "Auto mode 압축 1-2 메시지" 로 추정. 실제로는 *설계·검증·UX 품질·성능 정책* 모두 필요 — 자문 측이 *구현 시간*만 추정하고 *검증·UX·성능 시간 제외*. 진정한 시스템적 프로토타입은 *구현 + 검증 + UX + 성능* 모두 포함해야.

---

## 3. PROGRESS §5.9 5번째 사례 박제 예정 본문

다음 세션 0 단계에서 PROGRESS.md `§5.9` 절 끝에 추가할 박제:

```markdown
### §5.9 5번째 사례 — Phase 4 Auto mode 압축 vacuous 통과 (2026-05-21)

자문 측 학습 패턴 5번째 누락 사례 — *학습 박제와 실행 결과 불일치*.

**경위**:
- 사용자 단계 4 진입 후 *기술 정직성 박제* 만 짚고 *CLAUDE.md §2 사용자
  시나리오 본질* 놓침 (§5.9 4번째 사례).
- 자문 측이 5 Phase SE 접근 권장 (Phase 2 UX·3 UI·4 구현·5 QA).
- Phase 2·3 문서 작성 후 Phase 4 진입 시 사용자가 "Auto mode 압축" 선택.
  자문 측 *Auto mode 압축 위험 경고 부족* 으로 그대로 진행.
- Phase 4 commit `220d1ac` 의 메시지에 "§5.9 학습 자기적용" 명시
  ("streamlit-like sys.path 환경 import 검증 통과") — *그러나 실제 페이지
  렌더링·인터랙션·시각 결과 검증 0회*.
- 사용자 로컬 실행 결과: TypeError 잔존 + UI 사용자 친화성 0 + 렉.

**3 문제 진단**:
1. TypeError 잔존 — 박제 권위가 실행 검증을 대체 못 함
2. UI 사용자 친화성 0 — 일반인 이해 가능한 시각 표현 부재
3. 렉 — 성능 정책 부재 (caching·lazy load·page split)

**자문 측 자기 점검 4 항목 (정직 인정)**:
1. *Auto mode 압축 위험 경고 부족*. 사용자 "권장" 선택 시 자문 측이
   실행 검증·사용자 직접 검토·시각 회귀 부재의 위험을 강하게 경고 안 함.
2. *§5.9 학습 자기적용의 vacuous 통과*. import 검증만으로 통과한 것을
   "박제 완성형" 으로 표시. §5 원칙 5 (vacuous) 직접 사례.
3. *UI/UX 측면 자문 측 약점*. 코드 검토만으로는 시각적 완성도·인터랙션
   UX·사용자 친화성 검증 *원리적으로 불가*. 사용자 직접 검증 의무.
4. *작업 분량 추정 오류*. 구현 시간만 추정하고 검증·UX·성능 시간 제외.
   진정한 시스템적 프로토타입은 *구현 + 검증 + UX + 성능* 모두 포함 필요.

**남기는 이유** (§5.5.7·§5.5.9·§5.5.10·§5.5.11·§5.5.12·§5.5.13·§5.7·§5.8·§5.9
와 동일 원칙):
- §5.9 학습 사슬의 5번째 사례 — *학습 박제 vs 실행 검증* 의 *불일치 자체*
  가 학습.
- *기술 정직성 박제만으로는 UI/UX 품질 검증 불가능* 의 직접 사례.
- 미래 자문 시스템 운용 시 *박제 권위와 실행 검증을 분리* + *Auto mode
  압축은 *destructive 가능성·UI/UX·성능* 영역에서 자문 측이 강하게 경고*.

**리셋 결정** (사용자 본질 감각 동의):
- 폐기 범위: app/utils/·app/components/·app/pages/·slim main.py·신규 utils 40 테스트
- 유지 범위: D2/regime 모델 산출물·정직성 사슬·§5.x PROGRESS·모델·데이터 layer 테스트·C-1 데이터 자산 점검
- 보존: Phase 4 commit `220d1ac` 별도 브랜치 `phase4-discarded-ref` (공부 자산)
- 진행: 새 7 단계 (요구사항→UX→UI→아키텍처→구현→QA→배포) + 매 단계 사용자 직접 검증 + Auto mode 압축 금지
```

---

## 4. 리셋 범위 명세

### 폐기 (다음 세션 0 단계에서 revert)

| 경로 | 비고 |
|---|---|
| `app/utils/` | Phase 4 산출물 (formatters·regime_mapper) |
| `app/components/` | Phase 4 산출물 (header·metric_card·warning·chart·interpretation·navigation) |
| `app/pages/` | Phase 4 산출물 (overview·ticker_analysis·regime_timeline·d2_results·limitations) |
| `app/main.py` | Phase 4 slim entry — Phase 4 *이전* 상태 (commit `33a897f`) 로 복원 |
| `tests/test_app_utils.py` | Phase 4 신규 40 테스트 |

### 유지 (revert 영향 0)

| 경로 | 이유 |
|---|---|
| `src/frr/` 전체 | 모델·데이터 layer (D2·regime·labels·eval·features·models) |
| `data/raw/`, `data/external/`, `data/interim/` | 캐시·산출물 (모델 prediction·features·regime state series·KRX OHLCV) |
| `reports/d2_baseline_model_card.md` | D2 모델 카드 |
| `reports/regime_model_card.md` | regime 모델 카드 |
| `scripts/` | 학습·진단·백필 스크립트 |
| `tests/` (app 외) | 모델·데이터 layer 테스트 |
| `docs/data_sources.md` | 데이터 출처 박제 |
| `docs/ux_design.md` (Phase 2) | UX 설계 — *재사용 가능* (재검토 후) |
| `docs/ui_components.md` (Phase 3) | UI 명세 — *재사용 가능* (재검토 후) |
| `PROGRESS.md` 모든 박제 (§5.5.X·§5.6.X·§5.7·§5.8·§5.9) | 정직성 사슬 |
| `CLAUDE.md` | 변하지 않는 사실·규칙 |
| `README.md` | 프로젝트 종합 |

### 보존 브랜치

`phase4-discarded-ref` — `220d1ac` 시점 보존 (공부 자산). 학습 후 삭제 가능.

---

## 5. 새 진행 7 단계 (다음 세션부터)

| 단계 | 산출물 | 검증 게이트 |
|---|---|---|
| **0** | revert + §5.9 5번째 박제 | 자문 보고 → 사용자 확인 |
| **1** | `docs/requirements.md` | 자문 검토 + **사용자 직접 검토** |
| **2** | `docs/ux_design.md` (재작성) | 자문 검토 + **사용자 직접 검토** |
| **3** | `docs/ui_design.md` + 텍스트 와이어프레임 | 자문 검토 + **사용자 직접 검토** |
| **4** | `docs/tech_architecture.md` (에러·성능 정책 명시) | 자문 검토 + **사용자 직접 검토** |
| **5** | 구현 (컴포넌트 단위) | **매 단위 streamlit 실행 검증 의무** |
| **6** | `docs/qa_checklist.md` (사용자 직접 검증 서명) | **사용자 직접 검증** |
| **7** | 새 PR + 머지 | 사용자 결정 게이트 |

### 매 단계 의무 원칙

- **자문 검토** — 정직성 사슬 + §7.6 4 단계
- **사용자 직접 검증** — 코드만으로 검증 불가 영역 (UX·UI·성능·인터랙션)
- **단계 산출물 commit + push** — 박제
- **Auto mode 압축 금지** — 단계 단위·컴포넌트 단위 진행

---

## 6. 다음 세션 첫 작업 (0 단계 + 1 단계)

### 0 단계 — 리셋 (자문 측 작업)

1. `git branch phase4-discarded-ref 220d1ac` — Phase 4 commit 보존
2. `git push origin phase4-discarded-ref` — 원격 보존
3. `git checkout 33a897f -- app/` — app/ Phase 4 이전 상태 복원
4. `git rm tests/test_app_utils.py` — Phase 4 신규 테스트 삭제
5. `PROGRESS.md §5.9` 절 끝에 **5번째 사례 박제** (위 §3 본문 그대로)
6. `uv run pytest -m "not integration"` — 회귀 (161 통과 예상)
7. `git commit -m "revert: discard Phase 4 vacuous prototype + record §5.9 5th lesson"`
8. `git push`
9. **자문 보고**: revert 결과 + §5.9 5번째 박제 본문 + 회귀 결과

### 1 단계 — `docs/requirements.md` 초안 작성

**구성 (사용자 명시 요구)**:

- **사용자 페르소나** 2-3명 (구체적 배경·관심·기술 수준)
- **사용자 시나리오 (UC-1 ~ UC-N)** — step-by-step 행동 + *사용자 감정·기대*
- **기능 요구사항 (FR-X)** — 각 기능 명세 + 우선순위 (P0·P1·P2)
- **비기능 요구사항 (NFR-X)** — 성능·사용성·정확성·접근성
- **수용 기준 (Acceptance Criteria)** — 각 시나리오 통과 조건
- **CLAUDE.md §2 본질 명시 반영** — "사용자가 기업 선택 → 통합 리포트"
- **모델 한계 안내 정책** — D2 random 미만 / regime warmup 9개월 / negative finding 의 학술 가치 → 사용자가 *어떻게 인지하도록 할지* UX 명세

**자문 보고**: `docs/requirements.md` 초안 전문 + 자문 검토 의견 → 사용자 직접 검토

---

## 7. 컨텍스트 — 작업 환경

### 워크트리

- main 워크트리: `C:\Users\neo62\FinanceProj` (Phase 4 *없음*, main 만)
- 작업 워크트리: `C:\Users\neo62\FinanceProj\.claude\worktrees\competent-jackson-a02ec0` (Phase 4 *있음*, HEAD = `220d1ac`)

### Python 환경

- Python 3.13 + uv lock
- 의존성: pandas·numpy·plotly·streamlit·lightgbm·hmmlearn·scikit-learn 등
- 실행: `uv run streamlit run app/main.py` (현재 Phase 4 코드 — 다음 세션 0 단계 후에는 Phase 4 *이전* 상태)

### 데이터 산출물 (유지 — 다음 세션도 사용)

- `data/interim/train_d2_baseline/predictions.parquet` (3,602 rows: ticker × as_of × proba × class_weight)
- `data/interim/train_d2_baseline/features.parquet` (8,008 rows: ticker × as_of × 4 ratio + fs_div)
- `data/interim/regime/state_series.parquet` (2,273 rows: date × state_label)
- `data/raw/krx/ohlcv/{ticker}.parquet` (universe 321 종목)
- 종목 메타 (kospi200_quarterly CSV + FDR listing)

### 최신 §5.9 학습 사슬 (5 사례)

1. Co-Authored-By 가정 오류 — git log 실측 정정
2. D10 가정 오류 — 작업 직전 dart.py 재읽기 정정
3. Streamlit entry sys.path 가정 오류 — 사용자 실행 시 발견 → subprocess test
4. CLAUDE.md §2 사용자 시나리오 *구조* 누락 (단계 4) → 종목 분석 페이지 신설
5. **Phase 4 Auto mode 압축 vacuous 통과** (본 박제) → 7 단계 SE 접근 재시작

---

## 8. 핵심 메시지 (다음 세션 자문 측 정신)

> **박제 권위 ≠ 실행 검증**.
>
> "§5.9 학습 자기적용 통과" 라고 commit 메시지에 박제해도 *실제 페이지 렌더링·인터랙션·시각 결과 검증* 없으면 vacuous.
>
> Auto mode 압축은 *코드 검증 영역* (lint·단위 테스트·import) 에서는 합리적이지만, *UI/UX·성능·사용자 인터랙션* 영역에서는 *자문 측이 강하게 경고*하고 *사용자 직접 검증을 매 단위 의무화*.
>
> 7 단계 SE 접근의 진정한 의미는 *매 단계마다 사용자 직접 검증* — Auto mode 압축의 정반대 패턴.

---

## 9. 부록 — 다음 세션 시작 시 인지 점검 게이트

다음 세션 첫 메시지에서 자문 측 자체 점검 의무:

1. ✅ 본 인수인계 메모 (`docs/handoff_to_next_code_session.md`) 읽음
2. ✅ Phase 4 commit `220d1ac` 가 현재 HEAD 임을 확인
3. ✅ §5.9 5번째 사례 박제 본문 (§3) 인지
4. ✅ 자문 측 자기 점검 4 항목 (§2) 인지
5. ✅ 리셋 범위 (폐기 vs 유지, §4) 인지
6. ✅ 7 단계 새 진행 (§5) + 매 단계 사용자 직접 검증 의무 인지
7. ✅ Auto mode 압축 금지 (§5·§8) 인지

위 7 항목 모두 인지 후 0 단계 진입.
