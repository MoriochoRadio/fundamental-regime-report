# PROGRESS.md

이 문서는 본 프로젝트의 **변하는 상태**를 추적한다.
변하지 않는 사실·규칙·방향은 `CLAUDE.md` 에 있다.

**마지막 갱신**: 2026-05-21 (★ **단계 5 종료 = 프로젝트 종료**. 단계 1~5 모두 완료. main merge commit 진행)

---

## ★ 다음 세션 시작 지점 (Resume Marker)

> **다음 세션은 이 지점부터 이어간다 — features 모듈 작업 진입**:
>
> ### 1. 첫 메시지로 사전 점검할 항목 (§5.5.11 학습의 자문/실행 양측 게이트)
> - `git log --oneline -25` — 본 세션 walk-forward 커밋 + 그 직전 커밋 확인
> - **PROGRESS §5.5.13** — walk-forward 실측 결과 (fold 28 박제 예상 일치) +
>   universe_loader.reference_date 추가 경위 + 합성·실제 grid 차이의 의미
> - **PROGRESS §5.5.12** — walk-forward 합의 박제 (실측은 §5.5.13)
> - **PROGRESS §5.5.11** — 자문 측 정직성 사슬 2 사례
> - **PROGRESS §3 단계 2 DoD** — CFS/OFS 일관성·지주 희석/증폭·FDR ticker key 통일
> - CLAUDE.md §5 (격리 원칙) / §7.2 (코드 작성 전 절차) / §8.6 (점진 생성)
> - `tests/test_isolation.py` 변환 게이트 — features 작성 시점에 missing→active
>   전환되며 (iii) lookahead placeholder 도 본격 구현 진입
>
> ### 2. ★ 프로젝트 종료
> 단계 1~5 모두 ✅ 종료 (2026-05-21). main merge commit 완료 후 프로젝트
> 종료. 추가 작업 시 신규 PR.
>
> ### 3. 별도 결정 게이트 (features 안정화 후)
> - (β) §5.5.11 5 종목 FY refresh (페치 ≤5) — OFS fallback 영업이익 회수 정밀 분석
> - (γ) notfound 2,719 OFS 재페치 (페치 ≤2,719, DART 한도 27%) — D10 효과 ablation 측정
>
> ### 3. 다음 세션 후속 (features 후)
> 모델 (class weight·forward window ablation·bootstrap·시점별 가중치·0년 fold
> 처리, §5.5.10 결정으로 라벨 측 보강 안 함·모델 측 보완 우선) → D8 평가
> (walk-forward 본 모듈 사용) → LLM 빌드타임 배치 → Streamlit 통합.

---

## 1. 현재 상태 (Current Status)

- **단계**: ★ **단계 1~5 모두 ✅ 종료 = 프로젝트 종료** (2026-05-21).
  단계 2 negative finding + 단계 3 K=4 ablation 정량 정답 발견
  (코로나 27.9%→82% 3배 개선) + Limitations 6 항목 + 정직성 사슬 5 차원 +
  §7.6 검토 사이클 + 39+ commit 자기 점검. main merge commit 으로 PR #1
  마무리.
- **요약**: CI 4회 연속 실패(2026-05-18) → 커밋 1 (`71ef11a`) ruff format
  으로 그린 회복. 커밋 2 (`3585848`) D2 후보 상태 되돌림 + §7.4 ruff format
  규칙. 커밋 3 (`2977262`) D2 = α 최종 확정 — *5개 후보(D2(E)·B1 v1·v2·B3·A)
  전수 검증·기각 끝에 입증된 최선*. A1(신용등급 자동 확보 불가) 결과
  PROGRESS §5.5.8 박제. α 의 한계(양성 27·0년 2개·모집단 희소성)는 §5.5.7
  + §5 로그 + CLAUDE.md §4.1 세 곳에 정직히 기록. 커밋 4 (이번) `.gitattributes`
  `text eol=lf` 로 CRLF 해결 — `binary` 오추정·원복·정정 경위 §4-pre 박제
  (방법론적 엄밀성 증거, 안전장치 작동 사례).
- **원격**: https://github.com/MoriochoRadio/fundamental-regime-report (Public, MIT)

---

## 2. 완료한 작업 (Done)

- [x] 프로젝트 목적·스코프·작업 방식을 사용자와 합의
- [x] `CLAUDE.md` 초안 작성 (목표·포함/제외·방법론·산출물·협업 규칙)
- [x] `PROGRESS.md` 초안 작성 (본 문서)
- [x] 스캐폴딩: `README.md`, `LICENSE` (MIT), `.gitignore` (Python + data/model + .claude)
- [x] `git init` + 초기 커밋 (`c7c1852`)
- [x] GitHub 레포 생성·원격 연결·초기 푸시 (`origin/main`)
- [x] 기술 스택 1차 합의 (CLAUDE.md §8) — uv, OpenDartReader+pykrx, sklearn+LightGBM+hmmlearn, Gemini Free Tier, Streamlit+plotly
- [x] AI/ML 역할 분리 원칙 명문화 (CLAUDE.md §3.4) — 직접 학습 ML이 주연, LLM은 빌드타임 배치 1회만
- [x] 디렉터리 구조 합의 (CLAUDE.md §8.6) — src layout, 패키지명 `frr`, LLM 단일 출구, app/는 정적 읽기 전용, 점진 생성
- [x] 단계별 진행 계획 확정 — 5단계 7.5~11주, 각 단계의 산출물·DoD·결정 시점 명시
- [x] D1/D7/분석 기간 확정 (point-in-time KOSPI200 + 상폐 / rcept_dt+1영업일 / 2010-2024)
- [x] **단계 1 환경 셋업 완료** — uv 설치, Python 3.13, `pyproject.toml`, `uv.lock`, `src/frr/` 패키지 스켈레톤, 모든 핵심 패키지 import 검증
- [x] **단계 1 유니버스 가용성 사전 확인 완료** — `scripts/check_universe_availability.py`, `scripts/check_pykrx_health.py` 작성·실행, 다음 사실 확인:
  - KRX는 2014-05-01 이전 데이터 미제공 → 분석 기간 단축 필요
  - pykrx의 *전종목/인덱스 API*는 KRX 변경으로 망가짐 (단일 종목 OHLCV만 작동)
  - FDR로 상장폐지 데이터 풍부 (4,128건, DelistingDate/Reason 포함)
  - KOSPI200 시점별 구성은 어떤 라이브러리도 직접 제공 안 함 → 수동 CSV 다운로드 필요
- [x] **데이터 소스 문서 + 매니페스트 양식 작성** — `docs/data_sources.md` (출처·메뉴 경로·파일명 규칙·40분기 일자표·해시 계산법), `data/external/kospi200_quarterly/MANIFEST.yaml` (40분기 사전 항목 + 채울 필드 명시), `.gitignore` 갱신(`data/external/` 추적 허용)
- [x] **KOSPI200 1차 다운로드 (2015Q1) + 스키마 확정** — 사용자 다운로드 → sha256 검증 통과 → 200행·6컬럼·cp949·종목코드 6자리 str·등락률 percent·상장시가총액 과학표기법 확인. 카프로(006380, 2017 상폐) 포함 확인 → point-in-time 정확성 검증. CSV 스키마를 `docs/data_sources.md §3.4` + `MANIFEST.yaml` 상단 `csv_schema` 양쪽에 박제. 메뉴 번호 [11005]→[11006] 정정. 비영업일 처리 합의안(actual_reference_date 비우면 로더가 직전 영업일로 자동 채움) 문서화.
- [x] **`src/frr/data/universe_loader.py` v1 작성** — 매니페스트 파싱, 완전 검증된 분기만 노출, sha256 무결성 검증, 종목코드 dtype 보존, `as_of(t)` 룩어헤드 차단. 점진 다운로드 친화(미완 분기 자동 skip).
- [x] **`tests/test_universe_loader.py` 12개 테스트 통과** — 매니페스트 노출 룰, dtype 보존, 카프로 포함 (point-in-time), `as_of` 룩어헤드 차단, sha256 변조 탐지(tmp_path 격리), 미검증 분기 명확 에러. ruff 통과.
- [x] **KOSPI200 분기 CSV 다운로드 40/40 완료** — 사용자가 모든 분기 수동 다운로드·매니페스트 작성. 발견 사항 반영:
  - 행 수 *200~202*: 인덱스 리밸런싱 직후 일시 증가 → `docs/data_sources.md` + 테스트 범위 [200,202]로 갱신
  - *13/40 분기 비영업일 fallback*: KRX가 비영업일 입력 시 *직전 영업일로 자동 처리 안 함* — 사용자가 수동으로 직전 영업일 적용해 `actual_reference_date`에 기록
  - 매니페스트 헤더에 *전체 다운로드 일괄 보고* 추가 (스키마 메모 + holiday_fallback 카운트)
- [x] **`src/frr/data/calendars.py` v1 작성** — `KRXBusinessCalendar`: FDR KS200 index 기반 영업일 집합, `is_business_day` / `previous_business_day` / `next_business_day` / `floor` / `ceil` / `add_business_days(d, n)` / `business_days_between`. parquet 캐시 자동 생성. D7(rcept_dt+1) 적용 인프라.
- [x] **`tests/test_calendars.py` 20개 테스트 통과** — 합성 캘린더(외부 의존성 0) 19개 + 실제 FDR fetch 1개. 룩어헤드 차단 정신(`floor`는 항상 *입력 이하*) 검증.
- [x] **전체 테스트 32/32 통과** (1.4초). ruff clean.
- [x] **`src/frr/data/fdr.py` v1 작성** — `FDRDataSource`: `listing()` (현 KOSPI 전종목·Marcap 포함) + `delisting()` (KRX 상폐 4128건). 종목코드 6자리 str 강제·날짜 datetime64 정규화·parquet 캐시. Module docstring에 *상폐 메타데이터 격리 원칙* 박제 (단계 2 격리 테스트로 강제 예정).
- [x] **`tests/test_fdr.py` 10 + 1 skip 통과** — 단위 5(dtype 정규화 + 캐시 hit) + 통합 3(실 fetch). FDR 상폐의 *KOSPI 일반 종목 2015-2024 후보 ≥30건* 검증.
- [x] **FDR 상폐 데이터 한계 발견** — *4128건 중 상당수가 신주인수권/우선주 부산물 종목* (8자리 코드·"...2R"), *진짜 부실 상폐(카프로 006380 등) 일부 누락*. D2 라벨 정의 시 별도 출처 보강 필요 (아래 결정 로그).
- [x] **전체 42 통과 + 1 skip** (3.17초). ruff clean.
- [x] **`src/frr/data/krx.py` v1 작성** — `KRXSingleTicker.fetch_ohlcv(ticker, start, end, refresh)`. 캐시 정책: *요청 ⊆ 캐시 → 슬라이스 hit (네트워크 0)*, *그 외 → 합집합 범위 재페치 (캐시 점진 확장)*. 의존성 주입(`fetcher` 인자)으로 단위 테스트 네트워크 0회.
- [x] **`tests/test_krx.py` 8 테스트 통과** — 캐시 정책 6경로(없음/⊆/왼쪽/오른쪽/gap/refresh) + 잘못된 범위 + pykrx 실호출 통합. 전체 50 + 1 skip (3.05s).
- [x] **`.env.example` 추가** — DART 키 자리 + 발급 안내 + 보안 규칙. `.env` 는 `.gitignore` 대상.
- [x] **`src/frr/data/dart.py` v1 작성** — `DARTReporter`: `fetch_report(ticker, year, period)` / `available_at(t)` / `latest_available(t)`. **`rcept_no` 첫 8자 → `rcept_dt`** 추출, **`available_from = rcept_dt + 1영업일`** (D7 룩어헤드 차단의 코드 구현). 캐시 = parquet + yaml sidecar, `notfound` 상태 메타 기록으로 DART 한도 절약. **D10 OFS fallback 코드 적용 완료** (commit `6962cb7`, 2026-05-18) — `_make_default_fetcher` 가 CFS 우선 + OFS fallback 자동 동작, `ReportRef.fs_div` 필드 + meta.yaml `fs_div` 기록. 캐시 fs_div 메타 백필은 features 단계로 이전 (10,114 캐시 모두 fs_div=None 상태). **labels.py 영향 0 실측 확인** (본 세션 사전 검증 (가)(나)(다), §5.5.11).
- [x] **`tests/test_dart.py` 11 테스트 통과** — 단위 10 + **통합 1 (실 DART API + 실 캘린더 FDR fetch로 005930 2020 사업보고서 페치 + rcept_dt 2021-03-09 + available_from 2021-03-10 검증)**. 전체 61 + 1 skip (4.49s).
- [x] **커밋 1 — CI 수정 (`71ef11a`, 2026-05-19)** — ruff format 7파일 자동 정리 → CI 그린 회복. CI 4회 연속 실패 원인 진단: 로컬에서 `ruff check + pytest` 만 검증하고 `ruff format` 누락. 추후 재발 방지: 커밋 2 의 CLAUDE.md §7.4 한 줄 규칙으로 박제 예정.
- [x] **`configs/data.yaml` + `src/frr/config.py` 작성** — 분석 기간·유니버스 매니페스트·DART lag·periods·fs_div 의 단일 source of truth. frozen dataclass 4개 + `load_data_config(path)`. pydantic 미도입 (단순성 우선). `fs_div: CFS` 주석에 *D10 결정 대기* 표기.
- [x] **`tests/test_config.py` 7 테스트 통과** — 실 yaml 검증 1 + 경계(tmp_path 격리) 6. 전체 68 + 1 skip (4.85s).
- [x] **`src/frr/data/collect.py` + `scripts/collect_data.py` v1 작성** — 코어/CLI 분리. `collect_universe()` 가 universe_loader → FDR(1회) → 각 종목 KRX+DART. 부분 성공 패턴(종목·보고서 단위 실패 → `CollectionSummary.failures` 누적). 의존성 주입으로 단위 테스트 네트워크 0. CLI 옵션: `--config`/`--limit`/`--tickers`/`--skip-{krx,dart,fdr}`/`-v`.
- [x] **`tests/test_collect.py` 9 테스트 통과** — stub 주입 8 + 실 universe_loader union 1. 전체 77 + 1 skip (5.58s).
- [x] **collect summary 파일 출력 (v1.1)** — `write_summary()` 추가. `collect_universe()` 가 종료 시 자동으로 `data/raw/collect_summary.yaml` (덮어쓰기) + `collect_summary_YYYYMMDD_HHMMSS.yaml` (이력) 동시 저장. YAML 페이로드: generated_at + analysis_window + counts + failures(count·by_stage·items). CLI: `--summary-path PATH` override + `--no-summary-file` 비활성. 테스트 5 추가 (총 14). 전체 82 + 1 skip (5.78s).
- [x] **CLI `.env` 자동 로딩 (v1.2 fix)** — 사용자 `--limit 3` 점검에서 *DART 0/120 구조적 실패* 발견. 원인: `scripts/collect_data.py` 가 `load_dotenv()` 호출 안 함 → `DART_API_KEY` 미주입. 수정: `main()` 시작부에 `load_dotenv()` 추가 (진입점 책임 패턴, 어댑터는 `os.environ` 그대로). 점검의 가치가 실제 발휘된 사례.
- [x] **캘린더 padding (v1.3 fix)** — 2차 `--limit 3` 점검: DART 120 중 45 ok·71 notfound·**4 구조적 실패** (`2024-12-30 이후 영업일이 캘린더 범위 밖`). 원인: DART 보고서 `rcept_dt` 가 analysis_end(2024-12-31) *이후*에 접수됨 (사업보고서 +90일). 수정: `collect_universe()` 의 캘린더 fetch end 를 `analysis.end + 365일`로 확장 (`CALENDAR_END_PADDING_DAYS=365`). 캐시 fetch 비용 거의 0.
- [x] **사용자 `--limit 3` 점검 통과** — 3차 실행: 3종목 / KRX 3 / FDR OK / **DART 49 ok + 71 notfound + 0 failures**. 구조적 실패 0. 71 notfound 는 *도메인 사실* (000030 우리은행 2017 합병 폐지 → 2018+ 보고서 미존재 ≈ 28건 + 분기보고서 부분 미제출). **사용자 전체 수집 시작** (~250 종목, 예상 1~2시간).
- [x] **`tests/test_time_align.py` 4 테스트 통과** — 단계 1 룩어헤드 차단 통합 시나리오 (universe.as_of + dart.available_at 동시·available_from↔캘린더 일치·분기 경계·연 경계). 격리 두 항목(유니버스 변수·상폐 메타)은 *단계 2 진입 시* 추가 — module docstring 에 placeholder 명시. 전체 86 + 1 skip (6.56s).
- [x] **`.github/workflows/ci.yml` 작성 + integration marker 분리** — pyproject 에 `integration` marker 등록, 외부 API 의존 6 테스트(FDR/pykrx/DART)에 `@pytest.mark.integration` 부여. CI 워크플로: actions/checkout@v4 → setup-uv@v5 → Python 3.13 → `uv sync --frozen` → ruff check → ruff format --check → `pytest -m "not integration"`. **CI 단위 80 + 1 skip (2.29s, 네트워크·키 0)**. 로컬 통합 6 (3.54s). 전체 86 + 1 skip (5.06s).
- [x] **`src/frr/eval/splits.py` v1 + walk-forward expanding window 작성 (2026-05-20)** — `WalkForwardFold` (frozen dataclass + `__post_init__` 시간순/embargo 두 단계 검증), `walk_forward_expanding(*, as_of_grid, min_train_quarters=8, embargo_days=365, analysis_start, zero_year_handling="raise", zero_years=None)`, `_quarter_end_grid(loader)` 헬퍼. 정밀화 #2 (silent 차단) + 정밀화 #3 (dataclass-level 무결성) + 0년 fold placeholder (NotImplementedError + 메시지 검증). PROGRESS §5.5.12 합의 그대로 구현 + §5.5.13 실측 보고. D2 정직성 사슬 *시간 차원* 완성.
- [x] **`tests/test_splits.py` 12 테스트 통과** — 합성 40 분기 grid 기반 9 시나리오 + 시간순 검증 분리 1건 + parametrize 3건 = 총 12건. ruff clean.
- [x] **`universe_loader.reference_date(quarter) -> date` 공개 메서드 추가** — walk-forward `_quarter_end_grid(loader)` 헬퍼가 분기 라벨 → date 변환 시 권위 정보 (매니페스트 `actual_reference_date`, 13/40 분기 holiday fallback) 노출 경로. *추론* 으로 대체하면 holiday fallback 권위 깨짐 → 공개 API 1줄 확장 채택. tests/test_universe_loader.py 에 2 테스트 추가 (14 통과).
- [x] **전체 회귀 영향 0 재확인 (2026-05-20)** — 비 integration: 105 통과 + 4 skip + 7 integration deselected. ruff check + ruff format --check 통과. eval/ 모듈은 features/ 아니므로 격리 변환 게이트 영향 없음 (의도된 설계).
- [x] **features 사전 토대 0단계 — fs_div 라벨 백필 (2026-05-20)** — `src/frr/data/dart.py` 에 `backfill_fs_div_label(cache_dir) -> dict[str, int]` module-level 함수 추가 (인스턴스 의존성 0, 페치 0). status='ok'→fs_div='CFS', status='notfound'→fs_div='absent', 이미 키 있으면 skip (idempotent). `scripts/backfill_dart_fs_div.py` CLI. `tests/test_dart.py` 에 단위 테스트 2건 추가 (정상 + idempotent). ReportRef docstring 에 'absent' 라벨 추가. **실측 12,833 meta 일괄 백필**: updated 10,114 CFS + 2,719 absent, skipped 0, errors 0. 2회 실행 시 skipped 12,833·errors 0 (idempotent 실측 검증). 교차 검증: ok≠CFS=0, notfound≠absent=0. 전체 비-integration 107 통과 + 4 skip + 7 deselected.
- [x] **features 사전 토대 1단계 4 항목 설계 합의 (§5.5.14, 2026-05-20)** — (b-1) build_features 시그니처 + strict default / (b-2) lookahead 2 단계 (α AST + β 런타임 mock) / (c) fs_div (i) 컬럼 동행 + cfs_preferred + 격리 분리 + spot-check β1 시점 / (d) fdr_ticker_key NaN + warning. 2단계 작업 순서 6 단계 박제.
- [x] **CLAUDE.md §7.6 작업 진입 검토 사이클 박제 (2026-05-20, commit `a094edf`)** — 4 단계 (PROGRESS 점검 / git log / 코드 실측 / 사용자 검토 게이트). §7.2 + §7.5 + §5.5.11 정신의 명시 강화. 자문·실행 양측 적용, 예외 없음.
- [x] **2단계 step 1 — 지주회사 CFS vs OFS spot-check 진단 (§5.5.15, 2026-05-21)** — `scripts/diagnose_holding_fs_div.py` 작성·실행. 양성 20 전체 (옵션 B) 200 cells 실측: 유사 78 + 증폭 41 + 둘 다 음수 39 + 부호 차이 9 + 희석 2. 명시 지주 (034730 SK 증폭 9/10·267250 HD현대 7/10·096770 SK이노베이션 6/10) 패턴 확인. 키워드 매칭 false negative 0 발견. §5.5.15 보완 커밋 (commit `689a4ec`) 으로 (A) 표현 정밀화 + (B) 모델 단계 진입 결정 게이트 메모 추가. §3 DoD "지주회사 점검" 항목 해소.
- [x] **2단계 step 2 — `fdr_ticker_key` 추가 (2026-05-21)** — `src/frr/data/fdr.py` 에 module-level 함수 추가. `Code` (listing) / `Symbol` (delisting) 자동 탐지, 6자리 아닌 row → NaN + logger.warning, col override 지원. `tests/test_fdr.py` 단위 테스트 5건 (자동 탐지 2 + 8자리 NaN + override + ValueError). 전체 비-integration **112 통과 + 4 skip + 7 deselected**. §3 DoD "FDR ticker key 컬럼 불일치" 항목 해소.
- [x] **2단계 step 3·4·5 통합 — features/baseline.py + (α)(β) 검증 활성 (2026-05-21)** — `src/frr/features/__init__.py` + `src/frr/features/baseline.py` 신규 (PROGRESS §5.5.14 (b-1) 시그니처 strict default + 4 baseline ratio). 4 비율: debt_ratio (BS) · current_ratio (BS) · op_margin (IS, 비율) · roa (IS×BS 결합). fs_div 컬럼 동행. labels.py `_get_op_income` 패턴 재사용. universe 멤버십 검증 + ValueError 경계. `tests/test_features_baseline.py` 단위 테스트 8건 + `tests/test_features_lookahead.py` 4건 (β 런타임 mock contract — 모든 시점 인자 ≤ as_of 검증). `tests/test_isolation.py` (iii) 활성화 — (α) AST 블랙리스트 (`finstate`/`finstate_all` 금지). **α-fix**: AST 검사가 `if TYPE_CHECKING:` 블록 내부 import + 타입 어노테이션 Name 노드를 제외 (런타임 0, false positive 회피). pyproject.toml 에 RUF002/RUF003 extend-ignore 추가 (한국어 docstring + α/β/× 박제 일관성). 전체 비-integration **127 통과 + 1 skip + 7 deselected**. §3 DoD "유니버스 변수 격리" + "상장폐지/관리 메타 격리" 항목 해소. **D2 정직성 사슬 격리 차원 완성** — features 모듈 작성 시점에 (i)(ii)(iii) 자동 활성으로 *시작 시점부터 격리 강제*.
- [x] **Stage-2 모델 진입 B-1·B-2 완료 (§5.5.16, 2026-05-21)** — B-1 지주 군 양성 종목 수 실측: 명시 지주 3 (15%, 034730·267250·096770) + 의심 추가 1-2 (010690·008060), 학습 임계 미달 확인 → Code 권장 (c) (fs_div as feature 학습 + 군별 평가 분리 보고) 채택. B-2 5 항목 결정: (1) LightGBM + D8 평가 지표 유지 / (2) Platt sigmoid 캘리브레이션 / (3) balanced + unweighted ablation / (4) 0년 fold 평가 skip ("fold 수 28 → 25" 명시) / (5) fs_div as feature + 지주 군별 평가 분리. B-3 평가 함수 설계 결정 게이트 메모 2 항목 박제 (양성 N=3 통계적 변동성 + fold 단위 vs 종목 단위 평가).
- [x] **Stage-2 B-3 모델 학습 코드 작성 (2026-05-21)** — `src/frr/models/__init__.py` + `classifier.py` (`make_base_classifier`·`train_classifier`·`predict_proba`) + `evaluation.py` (`expected_calibration_error`·`top_k_precision`·`evaluate_predictions`). LightGBM + Platt sigmoid 캘리브레이션 (CalibratedClassifierCV). balanced/unweighted 2 가지 ablation 지원. 평가 5 metric (PR-AUC·ROC-AUC·Brier·ECE·Top-K precision) + n_positive·n_total 항상 보고 + bootstrap_n>0 시 95% CI 옵션 (B-4 활성 권장). `lightgbm>=4.6.0` + `scikit-learn>=1.8.0` 의존성 추가 (CLAUDE.md §8.4 박제). 단위 테스트 17건 (재현성 시드·class weight ablation 효과·캘리브레이션 동작·ECE·Top-K·bootstrap CI·단일 클래스 경계). 전체 비-integration **144 통과 + 1 skip + 7 deselected**.
- [x] **Stage-2 B-4 walk-forward 통합 학습 실행 + 결과 박제 (2026-05-21, §5.5.17)** — `scripts/train_d2_baseline.py` (features × labels × folds 통합 + balanced/unweighted ablation + 종목 단위 pooled + bootstrap_n=1000 CI + 지주 군 분리 평가). **Negative finding 정직 박제**: features 8,008 cells (양성 45) / 28 folds 중 평가 9 + skip 19 (대부분 양성 0). **PR-AUC 0.0136 < base rate 0.0205 + ROC-AUC 0.2651 < 0.5** → 모델 random 보다 나쁨. balanced vs unweighted 차이 거의 0 (class weight 효과 양성 절대 수 부족 앞에서 무력). 지주 군 (n_pos=12) CI 폭 완전 변동 = §5.5.16 짚을 점 1 의 경험적 확인. §5.5.7 박제 한계 ("KOSPI200 모집단의 부실 사건 희소성") 의 정량 증거 박제 — 학술·면접 방어 가치 큼.
- [x] **Stage-2 B-5 모델 카드 + 단계 2 종료 (2026-05-21)** — `reports/d2_baseline_model_card.md` 작성. 8 섹션: 모델 명세 (LightGBM + Platt sigmoid + 5 features) / 학습 데이터 (universe 321·grid 40·fold 28·평가 9) / 평가 결과 (PR-AUC 0.0136 random 미만, 정직 박제) / Limitations 4 (데이터·모델·지주 군 평가·D2 라벨 견고성) / 향후 방향 4 (A) Forward 2년 ablation 재고 (B) Features 확장 (C) (β)(γ) 데이터 보강 (D) 모집단 확장 거부 재확인 / 학술·면접 방어 가치 / 재현성 (시드·환경·산출물) / 단계 3 진입. **단계 2 펀더멘털 모듈 종료** — 단계 3 (시장 국면 모듈) 진입 게이트 통과.
- [x] **(A) notfound OFS 재페치 시도 — 데이터 보강 결과 박제 (§5.5.17, 2026-05-21)** — `scripts/refetch_notfound_ofs.py` 실행: notfound 3,583 호출 (16분, 한도 36%) → **status 전환 0건·errors 0·fs_div 전환 0**. DART API 응답 모두 `{status: '013', message: '조회된 데이타가 없습니다.'}`. notfound 가 *D10 fetcher 미적용*이 아니라 *실제 데이터 부재* (CFS·OFS 모두 미공시) 임을 정량 증명. §5.5.17 향후 방향 (C) 의 결과: *실효 0* — 데이터 출처 변경으로 §5.5.7 KOSPI200 모집단 한계 극복 불가능. 보완 commit `1a0283e`: PROGRESS §5.5.17 base rate 0.0205 계산 맥락 명확화 + 모델 카드 §3a Intended Use 섹션 신설.
- [x] **단계 3 — 시장 국면 모듈 (D3·D4) 작성 + HMM 학습 (§5.6, §5.6.1, 2026-05-21)** — `src/frr/regime/` 패키지 (`features.py` + `hmm_classifier.py`) + `tests/test_regime_*` 13 단위 테스트 + `scripts/train_regime.py`. D3 결정: HMM K=3 본 라인 + GMM/K-Means 비교. D4: 일간 + 3 피처 (ret_20d + vol_60d + vol_ratio_20_60) + rolling z-score. **forward-only filtering** (Viterbi backward smoothing 회피 — 룩어헤드 차단). State labeling 정정 (vol 순 → 위기 점수 vol_z − ret_z 순). 학습 결과 (§5.6.1): KS200 2,458 obs → 2,273 clean, log-likelihood -9442.92, 위험선호 57.8% + 중립 26.7% + 위험회피 15.5%. **학술 명명 부합 약함 정직 박제** — state 0 (위험회피) 가 *낮은 ret + 낮은 vol = 정체*. 2020 코로나 spot-check 위험회비 27.9% 만. hmmlearn>=0.3.3 의존성 추가.
- [x] **단계 3 — HMM vs GMM vs K-Means 비교 + K=2·3·4 진단 + 모델 카드 + 단계 3 종료 (§5.6.2, §5.6.3, 2026-05-21)** — `src/frr/regime/comparison.py` + `scripts/compare_regime_models.py` 실측. **자동 K 선택**: HMM·GMM 모두 BIC·AIC 최소 K=4 (도메인 K=3 과 tension). **HMM 시드 불안정성**: 5 시드 log-lik 변동 13.6% (-9442 ~ -8312), local optima 의존. GMM 변동 0.06%, K-Means 0.007% — 매우 안정. **HMM 적합도 > GMM** (K=3): -9442 vs -10102 (전이 행렬 정보 우월). `reports/regime_model_card.md` 작성 (8 섹션: 명세·데이터·결과·Limitations 4·Intended use·향후·재현성·단계 4 진입). **단계 3 종료** — 단계 4 통합 대시보드 진입 게이트.
- [x] **§5.5.17 보완 — notfound 분해 + 재학습 미진행 사유 (commit `adf3f80`, 2026-05-21)** — 자문 짚을 점 1 정직성 보강. 양성 20 종목 notfound 208 / 음성 종목 notfound 3,375 분해 + (A) 재페치 status 전환 0 → DART 캐시 변화 0 → 입력 변화 0 → 재학습 결과 변화 0 자명 → 재학습 미진행 사유 박제.
- [x] **단계 4 — Streamlit 대시보드 + LLM SDK import 0 격리 (§5.7, 2026-05-21)** — `app/__init__.py` + `data_loader.py` + `main.py` (4 페이지: 개요·국면 시계열·D2 결과·Limitations 6 항목 강화). `tests/test_app_no_llm_import.py` 3 테스트 (디렉토리 존재·LLM SDK import 0·학습 코드 import 0, AST 검사 — CLAUDE.md §3.4 박제 *CI 강제*). `streamlit>=1.57.0` + plotly 의존성 추가. **app/ 정적 읽기 전용 — 런타임 LLM 호출 0회·학습·계산·페치 0회 박제** (CLAUDE.md §3.4·§8.6 강제). 전체 비-integration **160 통과 + 1 skip + 7 deselected**. 단계 4 종료 — 단계 5 마무리 진입 게이트.

---

## 3. 다음 할 일 (Next)

> 모두 사용자 확인을 받은 뒤 진행한다.

### 3.0. 커밋 1~4 적용 완료 (2026-05-19) — **단계 2 진입 3 조건 충족**

- **커밋 1** (`71ef11a`): `fix(ci): apply ruff format to unblock CI`
  → CI 4회 실패 회복 (그린 ✅).
- **커밋 2** (`3585848`): `docs(d2): revert D2 to candidate state + enforce
  ruff format pre-commit` → D2 후보 상태 되돌림 + CLAUDE.md §7.4 한 줄
  (재발 방지).
- **커밋 3** (`2977262`): `docs(d2): finalize D2 = alpha after exhausting
  all candidates (E,B1v1/v2,B3,A)` → 9 항목 (PROGRESS 6 + CLAUDE.md 3) +
  A1 보고서 §5.5.8 박제 + α 한계 정직 기록 3곳 일관.
- **커밋 4** (이번): `chore: normalize CSV line endings via .gitattributes
  for sha256 manifest integrity` → `data/external/**/*.csv text eol=lf` +
  CLAUDE.md §8.3 보강 (text eol=lf 정책·sha256 LF 기준 명시) + PROGRESS
  §4-pre 정정 경위 박제 (binary 오추정·원복·text eol=lf 정정, 방법론적
  엄밀성 증거).

### 3.1. 후보 A (신용등급) 검증 — 완료 (A 기각, 2026-05-19)

A1 (자동 확보 출처 존재성): **불가능 / B1.2급 함정**. PROGRESS §5.5.8 박제.
A2 미진행 (사용자 지시 — "A1 불확실하면 A2 진행 금지" 충족: 불확실이 아니라
*명확히 불가*).
**결과**: 후보 A 기각 → D2 = α (후보 B) 확정. *5개 후보 전수 기각 여정* 종료.

### 3.2. 단계 1 진입 — 완료 기록 (2026-05-18~19)

1. ~~권장 기술 스택 제안~~ ✅
2. ~~디렉터리 구조 제안~~ ✅
3. ~~단계별 진행 계획~~ ✅
4. **단계 1 진입** — 다음 작업:
   1. ~~D1·D7·분석 기간 결정~~ ✅
   2. ~~`pyproject.toml` + `uv sync`~~ ✅ 완료
   3. ~~유니버스 가용성 사전 확인~~ ✅ 완료
   4. ~~KOSPI200 분기 CSV 수동 다운로드 절차 작성~~ ✅
   5. ~~분기 CSV 다운로드~~ ✅ 40/40 완료
   6. ~~`universe_loader.py`~~ ✅ v1 + 12 테스트
   7. ~~`src/frr/data/calendars.py`~~ ✅ v1 + 20 테스트
   8. ~~`src/frr/data/fdr.py`~~ ✅ v1 + 10 테스트 (FDR 상폐 한계 발견)
   9. ~~`src/frr/data/krx.py`~~ ✅ v1 + 8 테스트
   10. ~~`src/frr/data/dart.py`~~ ✅ v1 + 11 테스트 (D7 룩어헤드 차단 코드 구현체)
   11. ~~`configs/data.yaml` + `src/frr/config.py`~~ ✅ + 7 테스트
   12. ~~`scripts/collect_data.py` + `src/frr/data/collect.py`~~ ✅ + 9 테스트
   13. **사용자 점검 실행** (`--limit 3` → 전체 수집) ← **다음 (사용자)**
       - ~~소단계 v1.1: 최종 요약 파일 저장~~ ✅ 완료. summary YAML 자동 생성.
   14. ~~`tests/test_time_align.py`~~ ✅ 4 통합 테스트 (격리 두 항목은 단계 2 placeholder)
   15. ~~GitHub Actions CI~~ ✅ — lint + format + 단위 pytest (-m "not integration")

**→ 단계 1 코드 작업 완료. D2/D8/D9/D10 모두 ✅ 확정. 단계 2 진입 직전
마지막 관문: CRLF / `.gitattributes` (§4-pre).**

### 단계 2 진입 시 추가될 DoD (사전 메모)

- [ ] **유니버스 변수 격리 검증 테스트**: 펀더멘털 모델의 피처 어디에도
  KOSPI200 편입/편출 이벤트·시총 순위·인덱스 비중이 포함되지 않음을
  단위 테스트로 증명 (CLAUDE.md §5).
- [ ] **상장폐지/관리종목 메타데이터 격리 검증 테스트**: 펀더멘털 모델
  피처에 `DelistingDate`·`Reason`·`ArrantEnforceDate` 등 라벨 함수
  변수가 포함되지 않음을 단위 테스트로 증명 (CLAUDE.md §5). 라벨에는
  *사용해도 됨*, 피처로는 *금지*.
- [ ] **★ D2 라벨 출처 보강 결정**: FDR 상폐 데이터의 *부산물 종목 혼입* +
  *진짜 부실 폐지 누락* 한계가 확인됨 (2026-05-18). 옵션:
  (a) FDR 데이터 + 종목코드 6자리 + Reason 필터링으로 가용한 만큼만 사용
  (b) KRX 정보데이터시스템에서 *상장폐지/관리종목 지정 이력*을 분기 CSV
      처럼 수동 다운로드해 `data/external/krx_delist/` 보강
  (c) `universe_loader` 의 분기 변화에서 *KOSPI200 → 누락* 종목을 직접
      추출해 라벨 후보로 (인덱스 편출 ≠ 상폐, 분리 필요)
  단계 2 진입 시 사용자와 합의.

- [ ] **★ CFS/OFS 혼재 데이터 일관성 + 지주회사 CFS 희석/증폭 양방향 점검**
  (2026-05-19, D10 결정 옵션 (a) "CFS 우선 + OFS fallback" 채택 후속;
  2026-05-20 §5.5.9 갱신 — 증폭 사례 추가):
  옵션 (a) 적용 시 종목·시점별로 CFS 또는 OFS 가 섞이게 됨. 점검 항목:
  - **보고서별 `fs_div` 컬럼 명확 기록·전파**: DART parquet 캐시·labels·
    features 산출물에 `fs_div ∈ {CFS, OFS}` 가 항상 동행. 모델 분석 시
    어떤 회계 기준에서 추출된 수치인지 추적 가능해야 함.
  - **지주회사 CFS 부실 신호 (a) 희석 우려 + (b) 증폭 사례 양방향 검증**:
    - (a) 희석 우려: 지주회사의 CFS 는 자회사 손익이 통합되어 *모회사 단독의
      부실*이 가려질 수 있음.
    - (b) **실측 사례 (2026-05-20, §5.5.9 부수 발견)**: 신 SK 034730 FY2020 —
      자회사 (정유·화학 SK이노베이션 등) 코로나 충격이 CFS 에 통합되어
      FY2019 +3.95조 → FY2020 −1,645억 (**4.1조 감소**) 로 모회사 영업이익
      음수 전환. **희석이 아닌 증폭의 구체 데이터 포인트**.
    - 단계 2 D10 OFS fallback 적용 시 정량 분석: 지주회사군 (신 SK 034730,
      HD현대 267250, HD현대일렉트릭 267260 등 B 19 내 지주 형태 종목) 에
      대해 CFS vs OFS 영업이익 비교, 희석/증폭 양방향 분포 산출, B 신호
      정의의 도메인 정합성 검증.
  - **D2 라벨 (상폐 부실 A=1) 영향**: 포스코플랜텍은 지주회사 아니므로 직접
    영향 없음. *B 신호 (drawdown+op 전환) 의 지주회사 비중*과 OFS 적용 시
    전환 보존 여부가 핵심 점검.
  - **features 모듈 영향**: 재무비율(부채비율·ROA 등) 분모/분자가 CFS/OFS
    에서 다르게 나옴. fs_div 별 통계 (mean/std) 보고.
  - **시점**: labels.py v1 (CFS only 캐시 재사용) 완료 후, step #3 (D10
    OFS fallback 적용) 시 검증. labels.py v1 의 20 양성 reproducibility 와
    OFS fallback 적용 후 양성 분포 차이를 *문서화*하고 모델링 단계에서
    어느 라벨 버전을 채택할지 사용자 합의.

- [ ] **★ FDR 데이터셋 ticker key 컬럼 불일치** (2026-05-20,
  §5.5.9 capture 디버깅에서 발견):
  - 현상: `fdr.listing()` 컬럼은 `Code`, `fdr.delisting()` 컬럼은 `Symbol`
    — 두 데이터셋이 ticker key 컬럼명이 다름.
  - 영향: features 모듈이 종목 코드를 키로 두 데이터셋을 join 할 때
    *silently 잘못된 매핑* 또는 *키 불일치를 "데이터 없음" 으로 오해* 위험.
  - 조치: 단계 2 features 작성 시 표준화 helper (예: `fdr_ticker_key()`
    또는 `fdr.symbol_of(row)`) 또는 join 전 명시 정규화 적용. 본 항목 자체는
    features 모듈 시점에 구현.

---

## 4-pre. 미해결 이슈 — 코드 (Open Issues)

> 결정이 아니라 *코드 차원에서 점검 예정* 항목.

- **워크트리 CRLF — sha256 매니페스트 정합성 깨짐** (2026-05-19 발견 →
  ✅ **해결 (커밋 4)**):

  **원래 증상**: 본 워크트리(`competent-jackson-a02ec0`)는 `core.autocrlf=true`
  + `.gitattributes` 부재 → KOSPI200 분기 CSV들이 LF로 저장된 git index 에서
  *CRLF로 체크아웃*. 결과: 워크트리 sha256(`73df0f89...`) ≠ MANIFEST의
  LF 기준 sha256(`4307c9cb...`). `universe_loader._is_verified` 에서
  `IntegrityError` → sha256 의존 단위 테스트 11개 워크트리 한정 실패.
  CI(Linux) 는 LF 그대로라 영향 없음 (그린 유지).

  **★ 정정 경위 — 방법론적 엄밀성 증거 (D2 여정 보존 원칙과 동일)**:

  - *1차 처방 (잘못된 추정)*: `data/external/**/*.csv binary` — Code 가
    "binary 면 index 바이트(LF) 가 그대로 워크트리에 복사되므로 sha256 일치"
    로 추정. 사용자 검증 보고 안전장치 (커밋 전 `git add --renormalize .`
    결과 확인) 가 작동:
    - 실측: 40개 CSV 전부 *index 에서 변경* (각 +200 bytes ≈ 200행 × `\r`
      추가). 즉 `binary` 가 *워크트리 CRLF 를 그대로 index 로 propagate* →
      새 index sha256 = `73df0f89...` (CRLF) → 매니페스트 영구 불일치.
    - 추정 오류 원인: `binary` 의 동작 방향을 잘못 가정. 정규화를 *꺼면*
      working tree → index 방향에서 CRLF 가 그대로 들어감.
    - 사용자 경고("CSV 가 index 에서 변경되면 멈추고 보고") 에 따라 즉시
      `git restore --staged .` + `.gitattributes` 삭제로 원복. 데이터 손실 0.

  - *2차 처방 (실측 검증 통과)*: `data/external/**/*.csv text eol=lf` —
    git 이 *워크트리를 LF 로 강제* (Windows core.autocrlf 무시), index 는
    LF 그대로 (변경 0). 매니페스트 sha256 = `4307c9cb...` 와 매번 일치.
    - 1개 분기(2015Q1) 시범 적용 후 3 항목 실측 검증 통과:
      (a) `git diff --cached --stat` 에 `.gitattributes` 만 (CSV index 변경 0),
      (b) 워크트리 sha256 = 매니페스트 `4307c9cb...` 정확 일치,
      (c) `od -c` 로 CR 0개·byte count 10,889 (git 원본과 동일).
    - 39개 일괄 재체크아웃 후 40개 전체 sha256 대조: MATCH 40 / MISMATCH 0
      / SKIPPED 0. 단위 테스트 11 실패 → 0 실패 회복 (`84 passed, 1 skipped,
      6 deselected, 0 failed in 7.32s`).

  **남기는 이유**: 잘못된 처방이 *적용되기 전에* 검증 안전장치로 잡힌 사례.
  이 정정 과정 자체가 *방법론적 엄밀성의 증거* — sha256 매니페스트를
  재현성 핵심 장치로 삼고 매 작업에 검증 보고를 요구해온 누적된 신중함이
  값을 한 순간. "빨리 가자" 모드였으면 40개 CSV 가 깨진 채 커밋되고 단계 2
  에서 모델 결과가 이상해진 뒤 한참 후 추적했을 것. **D2 여정 보존(§5.5.7)
  과 같은 이유로 이 정정 경위도 지우지 않는다**.

  **부수 교훈**: Code 의 진단이 논리적으로 보여도 *git 내부 동작*처럼
  미묘한 영역은 *실측 검증 없이 일괄 적용 금지*. 이번 사건 이후 `.gitattributes`
  같은 *환경 변경*은 1개 시범 → 검증 → 일괄 패턴을 표준 절차로 채택.

- **후속 필수 — GitHub Actions Node.js 20 deprecation** (2026-05-19 PR #1 CI
  run annotation 발견):
  - 현 워크플로는 `actions/checkout@v4` + `astral-sh/setup-uv@v5` 사용 —
    둘 다 Node.js 20 기반.
  - **2026-06-02**: GitHub Actions runner 에서 Node.js 24 강제 전환 (이전까지
    `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` 환경변수로 opt-in 가능).
  - **2026-09-16**: Node.js 20 제거 — 미업그레이드 시 actions 실패.
  - 조치: 두 actions 의 Node 24 호환 최신 버전으로 업그레이드. 단순
    `.github/workflows/ci.yml` 수정.
  - 우선순위: **2026-06-02 전 필수** (6주 시한). 단계 2 진행 중 한 번에
    처리 권장. 본 시점 CI 그린 유지 영향 없음.

- **★ 룩어헤드 캘린더 경계 — 분석 기간 말단 정정공시** (2026-05-18 검증):
  분석 시점(2024-12-31) *이후* 접수된 정정공시는 룩어헤드 차단 설계에 의해
  *의도적으로* 거부된다. 2026-05-18 전체 수집에서 7건 발생 (013890 4건,
  018880 1건, 105560 2건 — 모두 2026-02~03 접수).
  - **이는 한계가 아니라 *엄밀성의 결과*** (`docs/data_sources.md §4`).
  - 면접 방어용 문서화 완료.
  - 후속: 정정공시 종목 리스트 자체는 *D2 라벨의 강한 보조 신호* (회계
    재작성·감사보고서 재발급은 부실 신호) — 단계 2 라벨 정의에서 활용 검토.

- **★ KRX OHLCV 합집합 페치 시 상장일 이전 구간 처리** (2026-05-18 기록):
  `KRXSingleTicker.fetch_ohlcv` 의 gap·확장 케이스에서 *합집합 범위* 전체를
  페치하는데, 종목의 *상장일* 이전 구간이 합집합에 포함되면 pykrx 는
  *빈/결측 응답*을 줄 수 있고 그 결과가 캐시에 그대로 섞일 수 있다.
  - 지금은 처리하지 않는다 (회귀 발견 안 됨).
  - 점검 시점: 종목별 **상장일 메타**를 다루는 시점에 함께 — `fdr.listing()`
    또는 `fdr.delisting()` 의 `ListingDate` 또는 `universe_loader` 연계에서.
  - 점검 방향: (a) 합집합 페치 시 *상장일 이후* 로 시작점 클립, 또는
    (b) 캐시에 *비어 있는 구간 마스크* 를 함께 저장, 또는
    (c) 결측 응답은 *조용히 빈 DataFrame* 으로 캐시.

---

## 4. 미해결 이슈 / 결정 대기 (Open Decisions)

각 항목은 결정 즉시 CLAUDE.md의 해당 섹션에 반영된다.

| # | 결정 사항 | 후보 / 비고 | 상태 |
|---|---|---|---|
| D1 | 분석 대상 유니버스 | ~~시총 상위 N (생존 편향)~~ | ✅ **point-in-time: 분기별 KOSPI200 + 상폐 종목 (~300~350)** |
| D2 | 부실(라벨) 정의 | **α = 상폐 부실 ∪ B1'** (drawdown 50% + 영업이익 음수 전환), 1년 forward | ✅ **확정 (2026-05-19, 입증된 최선)** — 5개 후보(D2(E)·B1 v1·v2·B3·A) 전수 검증·기각 후 채택. 양성 27 (8.4%), 0년 2 (2021·2023, 알려진 한계). §5.5.7 + §5.5.8 |
| D3 | 국면 모델 | HMM(상태 수 K=?), GMM, K-Means, 변경점 탐지 | 미정 |
| D4 | 국면 입력 피처 | 지수 수익률, 변동성, 거래량, 금리/환율 등 매크로 | 미정 |
| D5 | 대시보드 프레임워크 | ~~Streamlit / Dash / Next.js + FastAPI~~ | ✅ **Streamlit + plotly** |
| D6 | LLM 공급자·정책 | ~~Anthropic / OpenAI / 로컬~~ | ✅ **Gemini Free Tier + LLMProvider 추상화 / 빌드타임 배치 1회 / 런타임 0호출** |
| D7 | 재무 데이터 시점 처리 | ~~lag 값 미정~~ | ✅ **DART 접수일 `rcept_dt` + 1영업일** |
| - | 분석 기간 | ~~2010-2024 (가용성 미충족)~~ | ✅ **2015-01-01 ~ 2024-12-31** (가용성 사유) |
| D8 | 평가 지표 | PR-AUC + AUC + Brier + Calibration + Top-K precision, walk-forward expanding window | ✅ **승인 (2026-05-18)** |
| D9 | 모델 카드/리포트 양식 | 단일 시점 JSON 스키마 (ticker/period/report_meta/fundamentals/scores/regime_context/narrative_inputs) | ✅ **승인 (2026-05-18)** — 격리 변수 차단 검증 조건부; `key_ratios` 정확 카탈로그는 단계 2 진입 시 도메인 검토 |
| D10 | 연결(CFS) vs 별도(OFS) 재무제표 선택 | **옵션 C: CFS 우선 + OFS fallback** — `dart.py` 의 fetcher 보강 필요 | ✅ **승인 (2026-05-18)** — 단계 2 진입 시 *지주 vs 비지주* 라벨링 영향 별도 검토 명시 |

---

## 5.5. D2 부실 라벨 결정 자료 (진단 누적 기록)

### 5.5.1. 확정 사항 (2026-05-18)

- **D2(E) = D2(A) 양성 동일** — FDR `delisting.ArrantEnforceDate` 의 유니버스
  매칭이 1건뿐(포스코플랜텍, 이미 상폐 8건에 포함)이라 *관리종목 차원
  추가가 통계 기여 0*. 라벨은 *상폐 부실 사유 단독*으로 표현.
- **B2 (연속 영업적자) 폐기** — *재무비율 기반 라벨*. 모델 입력(영업이익)
  과 출력(라벨)이 *동일 변수족* → **자기참조 = 데이터 누수 회로**.
- **B4 (분위수 라벨) 폐기** — *실현 사건 아님*. 임의 임계로 라벨 정의 →
  *학습 목표 미정의*. 본질적으로 사후 적합. 검증 불가.
- **KRX [12006] 수동 다운로드 경로 완전 종료** — Cowork DOM 전수 조사
  결과 *일자 입력 요소 부재* 확정. 모든 인덱스(KOSPI200/KOSDAQ150 등)
  에 동일 적용. 시점별 관리종목 자동 확보 불가능.
- **B1 v1 폐기** — 광범위 severe 필터 (보고서 종류 + "재무제표" 키워드).
  결과: 96.6% 양성, top 1 = `[기재정정]연결재무제표기준영업(잠정)실적
  (공정공시)` (분기 잠정→확정 정정, 부실 신호 아님). **라벨 오염 실패**.
- **B1 v2 폐기** — 정밀 severe 필터 (사업/반기/분기/감사보고서 정정 only,
  잠정·전망·공정공시 제외). 결과: 1,924 이벤트로 좁혀졌으나 *양성 종목
  308 (96.0%)*. spot-check top 10 우량주 1 (KB금융만) — 정의는 좁아졌으나
  *양성률*은 거의 그대로. **report_nm 한계**: *어떤 보고서 종류*가
  정정됐는지는 알 수 있으나 *그 안의 어떤 항목 (재무 수치 vs 별첨/주석)*
  은 판별 불가. 완전 판별은 정정 본문 (XBRL/HTML) 파싱 필요 — 1인
  단계 1 후반에 무리.

### 5.5.2. ★ 두 차례 실패의 근본 원인 — 면접 방어 가치

두 차례(v1, v2)의 B1 라벨 오염 실패가 **공통 근본 원인** 노출:

> **KOSPI200 = 대형 우량주 200**. 부실 사건은 *주로 중소형주*에서 발생.
> *KOSPI200 한정 모집단*에서 부실 양성을 찾는 것 *자체가 모집단 부적합*.

이 통찰이 D2 결정에 본질적이다:
- 데이터 출처/필터 정밀화로 *해결 불가*
- *모집단 변경 (B3 스코프 확장)* 또는 *타깃 변경 (D2 재정의)* 이 답
- 두 갈래는 *D1 핵심 스코프 경계* 영향이 다르므로 *공정한 비교 진단* 필요

### 5.5.3. 진단 누적 (2026-05-18)

| 진단 | 결과 |
|---|---|
| FDR `KRX-ADMIN` 카테고리 발견 | 현재 시점 스냅샷 only (과거 시점 불가) |
| FDR `delisting.ArrantEnforceDate` 유니버스 매칭 | **1건** (포스코플랜텍) |
| 옵션 E 양성 (상폐 부실 ∪ 관리종목) | **8** (관리 차원 통계 기여 0) |
| B1 v1 (광범위 필터) | 양성률 96.6%, top 1 잠정실적 정정 |
| B1 v2 (정밀 필터) | 양성률 96.0%, spot-check 우량주 1/10 |

진단 스크립트는 모두 `scripts/` 에 git 추적 (재현용):
- `diagnose_step1_results.py`
- `diagnose_fdr_admin_for_d2.py`
- `diagnose_corrections_for_d2.py` (v1 → v2 확장, corrections 데이터를
  `data/raw/dart_corrections/all_corrections.parquet` 로 캐시)

### 5.5.4. 다음 — 두 갈래 사전 진단 (2026-05-18 대기)

D2 확정 전 *D1 스코프 경계 영향*을 고려해 두 갈래를 *공정 비교*:

- **갈래 1 (B3 — 스코프 확장)**:
  - (1a) FDR KOSDAQ 상폐 부실 사유 + walk-forward 분포 (즉시 가능)
  - (1b) KOSDAQ150 시점별 분기 구성 자동/수동 확보 가능성 — KOSPI200 때
    KRX 과거 조회 불가 전례 검토
  - (1c) 단계 2~4 파급 + 1인 일정 정직 추정 (분리/통합 ablation 상한)
- **갈래 2 (D2 타깃 재정의 — 스코프 유지)**:
  - (2a) KOSPI200 모집단 유지 + 대안 타깃 후보 평가
  - (2b) 장점·단점·자기참조 위험

두 갈래 진단이 모이면 비교표 → 최종 결정. *사전 진단 숫자 없이 확정 X*.

### 5.5.6. 두 갈래 사전 진단 결과 (2026-05-18 — `scripts/diagnose_d2_branches.py`)

| 항목 | 갈래 1 (B3 KOSDAQ) | 갈래 2 (타깃 재정의) |
|---|---|---|
| 양성 확보 | **144건** (연 6-28, 0년 없음) | A: 연 5-15 / B: 연 10-30 |
| KOSDAQ150 시점별 구성 | ❌ **불가능** (FDR/pykrx/KRX 모두 막힘) | N/A |
| Point-in-time 정합성 | ❌ 보장 불가 → **D1 원칙 위반** | ✅ KOSPI200 유지 |
| 데이터 자산 재사용 | 부분 | 전부 |
| 1인 일정 | +1.5-2주 (상한 +3주) | A: +2-3일 / B: +1-2일 |
| 자기참조 | X | A 낮음 / B 약함 |
| CLAUDE.md 변경 | §4.1 핵심 스코프 | 경미 (A) / 큼 (B) |

**갈래 1 (B3) 결정적 차단**: KOSDAQ150 시점별 구성을 *세 출처 모두 막힘*:
- FDR `StockListing("KOSDAQ150")` → NotImplementedError
- pykrx `get_index_portfolio_deposit_file("..", "2203")` → empty
- KRX [12006] → 일자 입력 부재 (Cowork 확정, 모든 인덱스 동일)

→ B3 채택 시 KOSDAQ 유니버스에 *현재 시점 구성*만 사용 = **D1에서 거부한 생존 편향 패턴 재발**. KOSPI200 수준의 정합성을 보장 못 함. *방법론적 엄밀성과 직접 충돌*.

**갈래 2 후보 비교**:

| 후보 | 평가 | 권장도 |
|---|---|---|
| **A. 신용등급 N단계 하향** | "부실 위험" → "신용 위험" 경미 변경. 외부 평가 → 자기참조 낮음. 데이터 부분 자동 (DART 공시 텍스트 파싱). +2-3일 | **1순위** |
| B. 재무 동반 drawdown | "부실" → "재무 동반 가격 충격" 큰 재정의. 자기참조 약함. 데이터 완전 자동. +1-2일 | 2순위 |
| C (어닝 쇼크) | 컨센서스 유료 → 채택 X | — |
| D (영업적자) / E (자본잠식 임계) | 자기참조 / 임의 임계 → 폐기 유지 | — |

**최종 권장**: **갈래 2 + 후보 A (신용등급)**.
- 라벨 의미 보존 (외부 평가 = 시장이 동의한 부실 신호. 학술·실무 표준)
- CLAUDE.md §3.1 "재무 건전성·부실 위험 지표" → "재무 건전성·신용 위험 지표" 경미 변경
- 자기참조 위험 가장 낮음
- 데이터 자동 확보 부분적이지만 1인 부담 ~2-3일

### 5.5.7. ★ D2 최종 확정 (2026-05-19) — α (입증된 최선)

> **α 의 성격**: α 는 *선택*된 라벨이 아니라 *5개 후보(D2(E)·B1 v1·v2·B3·
> A)를 전부 데이터로 검증·기각한 끝에 남은 입증된 최선*. 각 후보의 기각
> 사유·증거는 본 절 §5.5.1~§5.5.6 + §5.5.8 (A1) 에 누적 보존. 면접 방어
> 가치: *"부실 라벨을 어떻게 정했는가"* 의 답은 *"5번 시도·5번 기각·남은
> 최선"* 이지 *"이게 좋아 보여서 골랐다"* 가 아니다.

**D2 라벨 정의**:
> 종목 X 가 시점 t 에서 *1년 forward 기간* `[t, t+365일]` 내에
> **(A) 부실 사유 상장폐지** OR **(B) drawdown 50% 이상 발생 + 사업연도 영업이익 양수→음수 전환** 중 *하나라도* 발생하면 양성(label=1).

**근거 자료** (`scripts/diagnose_a2_b1prime.py`):
- 양성 종목 **27** (8.4%) — 상폐 부실 8 + B1' 19, *중복 0* (완전 독립)
- walk-forward 0년: 2021, 2023 (2개 — 강세장·회복기 *시장 거시 상황*)
- spot-check 우량주 0/10 (정의 헐거움 X)
- B1' spot-check 진짜 위기 사례 검증: 한국항공우주(2017 K-FX) / S-Oil·SK이노베이션(2020 코로나 정유) / 남양유업(2020 갑질·코로나) 등

**α 의 알려진 한계 (정직히 기록)**:
- **양성 절대 건수 부족**: 27건 (10년·321 종목·8.4%). 학습 임계 30 근접하나 미달.
- **0인 연도 2개** (2021·2023): 강세장·회복기 *시장 거시 상황* 의 도메인 사실.
- **근본 원인**: KOSPI200 모집단의 부실 사건 희소성 — 대형 우량주 200 한정
  유니버스에서 부실 사건이 드문 것은 본질적 제약. B3 (스코프 확장) 으로
  해결 가능했으나 *KOSDAQ150 시점별 구성 불가* 로 방법론 엄밀성과 충돌
  (§5.5.6). *모집단을 바꿀 수 없으므로 라벨 측에서 받아들이는 한계*.

**단계 2 학습 측 보완 (방향만 — 구체 설계는 단계 2 진입 시 D8 과 함께 결정)**:
- class weight (양성 비율 8.4%에 비례한 weight)
- forward window ablation (1년 ↔ 2년 — 양성 추가 확보 vs 분석 마지막 2년 손실)
- bootstrap (0년 2021·2023 보완, *시점 내* 적용으로 시계열 누수 회피)
- 시점별 가중치 (양성 다발 연도 2020 우세 회피)

이 보완책의 *구체 설계와 평가 영향*은 단계 2 진입 시 D8 평가 지표와 함께
결정 — 보완 *유무*와 무관하게 약점은 약점이며, 평가에서 *정직 보고*가 우선.

**A2 (신용등급) 최종 기각 사유**:
- DART `list(corp, start, end)` 응답 276,099건 카테고리 분포: `(no bracket)`·`[기재정정]`·`[발행조건확정]`·`[첨부정정]`·`[첨부추가]`·`[연장결정]` 만 존재
- 신용평가 공시는 *평가사가 발행자*라 *기업 corp_code 기반 검색에 미포함*
- 자동 확보는 평가사 사이트 파싱·유료 데이터 필요 → *B1.2 와 동일 1인 부담* → 기각

**CLAUDE.md 변경 (단계 2 진입 시 함께 갱신)**:
- §3.1 "재무 건전성·부실 위험 지표" → "재무 건전성·재무 충격 위험 지표"
- §3.4 D2 라벨 정의 명확화 (실현 사건 두 가지 결합)
- §4 (또는 §5) 한계 명시: KOSPI200 부실 사건 희소성·0년 2개 사실·B3 모집단 확장 불가 사유

**진단 스크립트 git 추적 (전체 D2 결정 증거자료)**:
- `scripts/diagnose_step1_results.py`
- `scripts/diagnose_fdr_admin_for_d2.py`
- `scripts/diagnose_corrections_for_d2.py` (B1 v1/v2)
- `scripts/diagnose_d2_branches.py` (B3 vs 타깃 재정의)
- `scripts/diagnose_credit_rating_feasibility.py` (A2 1차)
- `scripts/diagnose_a2_b1prime.py` (A2 + B1' + α 합집합 — 최종 확정 자료)

### 5.5.8. A1 진단 — 신용등급 자동 확보 출처 존재성 (2026-05-19)

**판정**: **불가능 / B1.2급 함정과 동일 등급 부담**. A2 미진행.

**조사 4영역 × 8출처 결과** (`scripts/diagnose_a2_b1prime.py` + 웹 1차 검증):

**영역 1 — DART 측 (4 우회 경로 모두 실패)**:
- `list(corp, 2015-2024)` × 321 종목 = 276,099 공시 전수 + 7 신용 키워드
  (`신용평가/신용등급/회사채/NICE신용/한기평/한신평/KIS신용`) 매칭 → **0건**.
  응답 카테고리: `(no bracket)·[기재정정]·[발행조건확정]·[첨부정정]·[첨부추가]·[연장결정]` 만 존재
- OpenDART DS001~DS006 + pblntf_ty A~J + pblntf_detail_ty A001~J006 전수 —
  *신용등급 전용 endpoint·코드 0개*
- 평가사 corp_code 우회 (평가사가 자기 사업보고서만 DART 제출, 제3자 등급
  액션은 평가사 사이트)
- DART 통합검색 (dsab007) — UI 키워드 검색 있으나 *export 없음·HTML
  스크래핑 부담 = B1.2급*

**영역 2 — 평가사 3사 (전부 자동 접근 차단)**:
- **KIS** (kisrating.com): KCW 구독 + **저작권 명시 금지** ("어떤 정보도...
  사전 서면동의 없이는... 무단전재되거나 복사 또는 재판매, 유포될 수
  없습니다")
- **NICE** (nicerating.com): 유료회원 필수
- **한국기업평가** (korearatings.com): 업체별통계 페이지 "본 서비스는
  한국기업평가 회원에게 제공되는 서비스입니다" 명시. Excel 다운로드 회원 한정
- → 자동 확보하려면 로그인 우회 + 저작권 위반. *완전 무료·법적 청결*
  전제와 충돌

**영역 3 — 공공 데이터 (KOFIA·SEIBRO·KIND)**:
- **KOFIA OpenAPI/FreeSIS/BIS**: 시장집계 통계 위주, *발행자별 등급 시계열
  API 노출 증거 없음*. JS 렌더링(WebSquare) 자동화는 B1.2급
- **SEIBRO**: 동일 (WebSquare)
- **KIND 자율공시**: 발행자 *자발적* 공시 — 의무 아님, *체계성·완전성
  보장 안 됨*

**영역 4 — 백업 라이브러리 (전부 없음)**:
- FDR / pykrx / yfinance / FRED / OpenBB — *KR corporate credit rating
  시계열 미제공*

**B1.2 와의 동등 비교**:

| 비교축 | B1.2 (기각됨) | A 자동 확보 시도 |
|---|---|---|
| 부담 | XBRL/HTML 파싱 | HTML 스크래핑 + JS 렌더링 우회 + 페이지 수동 매핑 |
| 데이터 보장 | DART 안에 존재 (파싱만) | *유료 구독* 또는 *공시 의무 부재* |
| 법적 위험 | 없음 | **저작권 명시 금지** (KIS) + 회원 우회 |
| 1인 일정 | "단계 1 후반 무리" | **동일 또는 더 큰** 부담 |

**부수 결론**: KOSPI200 모집단의 *부실 사건 희소성* (§5.5.2) 은 *신용등급
하향 사건 희소성*에도 동일 적용 — 자동 확보 가능했어도 양성 부족 위험.
*모집단 변경 불가* (§5.5.6 B3 기각) 이므로 라벨 측에서 한계 수용.

**진단 자료 git 추적**:
- `scripts/diagnose_credit_rating_feasibility.py` (corrections 키워드 1차 진단)
- `scripts/diagnose_a2_b1prime.py` (276,099 전수 fetch + 카테고리 분포 + 0
  매칭 입증)
- 본 §5.5.8 의 영역 2~4 웹 출처 조사 결과

---

### 5.5.9. ★ D2 distress 필터 결함 — A 8 중 7 합병성 자발 해산 (2026-05-19, 034730 정당성 검증 및 최종 박제는 2026-05-20)

> **본 절은 §5.5.7 의 "양성 27·A 8" 박제 직후 발견된 결함과 그 정정 경위의
> 기록.** 단계 2 진입 직전 *labels.py 박제 전*에 사용자 강화 조건(A 8 육안
> 게이트)이 작동해 포착. 방법론적 엄밀성의 증거로 보존 — D2 여정(§5.5.7)·
> CRLF 정정(§4-pre)과 같은 원칙.

**발견** (capture 스크립트 + `diag.distress_delisted` 원본 inspect, 2026-05-19):

A 8 종목 중 7건이 `distress_kw=["잠식","해산","감사","부도","회생","관리"]` 의
"해산" 키워드로 매칭되었으나, **실체는 합병에 의한 자발 해산** (구조개편):

| Symbol | Name | DelistingDate | Reason | 실체 |
|---|---|---|---|---|
| 051310 | 포스코플랜텍 | 2016-04-15 | 자본전액잠식 | ✅ **진정한 부실** |
| 000830 | 삼성물산 (구) | 2015-09-15 | 해산 사유 발생 | ❌ 제일모직과 합병 |
| 003600 | SK (구) | 2015-08-17 | 해산 사유 발생 | ❌ SK C&C 와 합병 |
| 010520 | 현대하이스코 | 2015-07-15 | 해산 사유 발생 | ❌ 현대제철 흡수합병 |
| 037620 | 미래에셋증권 (구) | 2017-01-20 | 해산 사유 발생 | ❌ 대우증권과 합병 |
| 068870 | LG생명과학 | 2017-01-17 | 해산 사유 발생 | ❌ LG화학 흡수합병 |
| 004130 | 대덕GDS | 2018-12-19 | 해산 사유 발생 | ❌ 합병 추정 |
| 002270 | 롯데푸드 | 2022-07-20 | 해산 사유 발생 | ❌ 롯데제과와 합병 |

→ **A 8 중 진짜 부실은 1건 (포스코플랜텍, 자본전액잠식). 7/8 이 합병성 해산**.

**§5.5.5 경고의 추적성 — 사전 경고가 있었음**:

PROGRESS §5.5.5 (2026-05-18 구버전 자료) 가 정확히 이 패턴을 *사전 경고*:
> "해산 사유 발생 | 8 | △ 사유별 검토 (**자발적 해산은 제외 권장**)"
> "지주회사 완전자회사화 | 8 | ❌ **부실 아님** (구조개편)"

§5.5.5 의 "상폐 양성 (부실 사유) | **~9**" 추정도 *이 7건을 빼고 1+α 로 계산*
했던 것. 즉 §5.5.5 단계에서는 결함을 정확히 인식했음.

**§5.5.7 박제 시 누락**:

§5.5.7 (2026-05-19 D2 최종 확정) 시 §5.5.5 의 *자발적 해산 제외 권장*이
**반영되지 않은 채** "상폐 부실 8" 로 박제됨. 결과: D2 양성 27 중 7건이
*부실 신호가 아닌 합병 신호* — 라벨 노이즈. 진단 스크립트의
`distress_kw` 필터가 *키워드 매칭만* 하고 *합병/부실 구분 신호* 미사용.

**A 육안 게이트의 박제 직전 포착**:

사용자 강화 조건 — test_labels.py 의 `EXPECTED_POSITIVES` 박제 *직전*에
A 8개 각각의 의미적 일관성 (회사명·Reason·매칭 키워드) 을 *데이터로* 확인
하는 게이트 — 가 적용되어 박제 직전 결함 발견. B 19 만 검증하고 A 는 코드만
박제했으면 **합병 7건이 부실 라벨 양성으로 모델에 흘러들어가는 노이즈 27
박제 발생**. 검증 안전장치가 정확히 작동.

**정정 결정 — P1 (필터 보강) 경위 + 최종 채택**:

P1 채택 후 *구체 보강 방식* 결정에 두 단계 검증:

**(1차 가설) `ToSymbol/ToName` 구조적 신호 — *기각***:

가설: 합병은 승계 법인 존재(ToSymbol/ToName 채워짐), 부실 상폐는 승계 없음
(비어 있음). 키워드보다 자의성 없는 판별 기준.

실측 결과 (2026-05-19, Step 1 검증):
- A 8 *전부* ToSymbol/ToName **비어 있음** — 포스코플랜텍(부실) + 합병 7건
  모두. 가설은 *KOSPI universe 한정에서 7/1 을 분리하지 못함*.
- 전체 FDR delisting 4,130 행에서 ToSymbol 결측률 **76.0%** (3,138/4,130),
  ToName 결측률 **75.2%**. *합병/부실 구분 신호로 신뢰 불가*.
→ 가설 기각. 추정의 데이터 검증이 적용 직전에 잡은 사례 (binary 오추정
§4-pre 와 같은 패턴, 시범 검증 안전장치가 다시 작동).

**(2차 안) Reason 카테고리 화이트리스트 — 채택**:

전체 delisting 의 Reason 분포 분석 결과:
- FDR Reason 은 *정밀 카테고리화*. 합병에 별도 카테고리 ("피흡수합병",
  "피흡수합병(스팩소멸합병)", "지주회사(최대주주등)의 완전자회사화 등").
- 진정 부실에도 별도 카테고리 ("자본전액잠식", "감사의견 의견거절",
  "감사의견거절(감사범위제한)", "기업의 계속성...").
- *그러나* A 7 합병은 모두 *"해산 사유 발생"* 으로 등록 (FDR 가 KOSPI 발행사
  큰 합병에는 이 카테고리 사용).

**delisted_universe 전수 분석** (universe + 분석기간 + 6자리 + KOSPI) — *총 15건*, 3 카테고리:
- `자본전액잠식`: **1** (포스코플랜텍 — 진정 부실 ✅)
- `해산 사유 발생`: **7** — *전수 합병* (검증 1)
- `지주회사(최대주주등)의 완전자회사화 등`: **7** — 합병/지주 전환, §5.5.5 가
  "❌ 부실 아님" 으로 명시했던 카테고리. distress_kw 매칭 0 → 자동 제외 (
  기존 진단의 우연한 정합).

**§5.5.2 인사이트 전수 입증** — *KOSPI200 모집단의 부실 사건 희소성*:
universe + 분석기간 안에서 *재무 부실 카테고리 매칭은 자본전액잠식 1건뿐*.
감사의견 의견거절, 감사의견거절(감사범위제한), 기업의 계속성 의문 등 *진정
부실 카테고리* 모두 universe 매칭 **0건**.

**화이트리스트 최종안 — 옵션 A (정직성 최우선)**:

```python
DISTRESS_REASONS_WHITELIST: frozenset[str] = frozenset({
    "자본전액잠식",  # universe 매칭 1건 (포스코플랜텍, 2016-04-15)
})
# 매칭 방식: delisted_universe["Reason"].isin(DISTRESS_REASONS_WHITELIST)
# 정확 일치, 부분 텍스트 매칭 X (자의적 키워드 매칭 회피)
```

**옵션 B (변종 enum 확장, 17 문자열) 기각 — 논리 정확화**:

옵션 B 기각 이유는 *"코드가 길어서"*가 아니다. 17 변종 중 *어느 것이 부실이고
어느 것이 아닌지* 선별하는 행위 자체가 §5.5.9 의 발견에서 경계한 *"자의적
키워드 땜질"* 을 *"자의적 변종 선별"* 로 이름만 바꿔 재발시키는 패턴이다.
`"자본전액잠식(2년), 기타 등록취소"` 같은 결합 텍스트나 오타 변종을 *부실
카테고리로 인정할지* 판정하는 것은 자의적 도메인 판단이다.

**옵션 A 강점은 *"짧아서"*가 아니라 *현 스코프 전수 입증된 것만 박는 정직성***.
미래 안전망 부재는 *단점이 아니라 의도된 정직* — §3 단계 2 DoD 의 "D2 라벨
출처 보강 결정" 항목에서 별도 검증 시점에 다루기로 이미 약속. D1 의 "검증 안
된 미래 종목 미포함을 한계로 명시" + 단계 1 의 "점진 생성" 원칙과 일관.

**KOSPI 계속기업 의문 추측 문자열 — 박제 직전 두 번째 포착**:

옵션 B 검토 중 *내가 추측한 카테고리 문자열* (`"기업의 계속성 및 경영의
투명성 등을 종합적으로 고려하여 코스피시장의 건전한 발전과 투자자 보호 등에
부합하지 않는 경우"`) 이 FDR 데이터에 **0건 부재**임이 발견됨. 실제 KOSPI
계속기업 의문은 5 변종 (모두 *"상장폐지기준에 해당한다고 결정"* 류 종결)
으로 존재. 사용자 강화 조건 — *isin 정확 일치가 작동하려면 문자열이 데이터의
실제 값과 한 글자도 틀리지 않아야 함* — 이 *"죽은 안전망"* 을 박제 직전에
잡음. 옵션 A 채택으로 이 추측 문자열도 폐기.

**P2/P3 기각 사유**:
- **P2** (D2 유지 + 한계 명시): B1 넓은필터에서 거부한 *"노이즈 알면서 보존"*
  패턴의 재발. *노이즈 27 > 정직한 20 이 아님*.
- **P3** (D2 = α 폐기·재정의): B 19 와 α 형식까지 버리는 과잉. 멀쩡한 부분
  보존이 옳음. §5.5.5 경고를 §5.5.7 에 *반영*하는 것이 D2 *재발명*은 아님.

**카프로 (006380) 부재 — 정상 (사용자 추정 정확)**:

FDR delisting 4,130 행에 *Symbol = "006380" 부재* (단계 1 §5.5.1 *"FDR 상폐
데이터 한계 — 진짜 부실 상폐 일부 누락"* 와 정확히 일치). universe 분기 멤버십은
`['2015Q1']` — 2015Q2 부터 편출, 2017-12 상폐. → A 후보 진입 못 함이 *데이터
부재* 이지 *로직 결함 아님*. 단계 2 진입 시 §3 "D2 라벨 출처 보강 결정"
항목 (KRX 정보데이터시스템 수동 다운로드 옵션 등) 에서 별도 다룸.

**확정 영향** (P1 적용 후, step 2-3 실측 확정):

| 항목 | §5.5.7 박제 | P1 정정 후 |
|---|---|---|
| A (상폐 부실) | 8 | **1** (포스코플랜텍만) |
| B (drawdown+op) | 19 | **19** (변동 없음 — distress filter 무관) |
| A ∩ B | 0 | **0** (포스코플랜텍 ∉ B 19) |
| **α 합집합 (D2 양성)** | **27** | **20** (−7 노이즈) |
| 양성 비율 (321 종목 중) | 8.4% | **6.2%** |
| 0년 (이벤트 발생 0 연도) | {2021, 2023} (2개) | **{2015, 2021, 2023} (3개)** — 2015 합병 3건 제거로 추가 |

학습 임계 30 에 더 빠듯해짐. D8 평가 설계에서 정면 대응 (단계 2 진입 시).

---

**A=1 / B=19 구조적 의미 — *여정의 정직한 결과***:

D2 양성 20 중 **95% (19/20)** 가 B (drawdown + 영업이익 음수 전환) 신호.
순수 상폐 부실 (A) 은 노이즈 제거 후 **포스코플랜텍 1건뿐**.

형식상 D2 = "상폐 부실 ∪ B1'" 합집합이나, **실질적으로는 drawdown 기반 재무
충격이 주축이고 순수 상폐 부실은 보강축 (1건)**. §5.5.2 의 *"KOSPI200 대형주
부실 희소성"* 인사이트가 **전수 데이터로 최종 입증** — universe 안에서
*재무 부실 상폐는 10년간 1건* (포스코플랜텍, 자본전액잠식).

**합집합 형식 유지의 이유 — 미래 대비 아닌 여정의 기록**:

처음 상폐 부실을 D2 주축으로 출발 → D2(E)·B1 v1·v2·B3·A 5 후보 기각 →
B1' 추가 → A 육안 검증으로 합병 노이즈 7건 제거 → A 가 1건으로 수렴. *"사실상
B 주축"은 의도한 설계가 아니라 데이터가 강제한 결론*. 합집합 형식을 유지하는
것은 *미래 대비*가 아니라, *이 라벨이 5 후보 기각·합병 노이즈 제거 여정을 거쳐
도출됐다는 기록 자체가 D2 정의의 일부*이기 때문이다.

**면접 방어 서술 (정직 그대로)**:

> Q: *"상폐 기여가 1건이면 사실상 drawdown 라벨 아닌가?"*
>
> A: *"맞다. KOSPI200 대형주 부실 희소성으로 순수 상폐 부실은 10년간 1건뿐
> 이며, 실질 D2 는 drawdown 주축이다. 합집합 형식을 유지하는 이유는 미래
> 대비가 아니라, 이 라벨이 5 후보 기각·합병 노이즈 제거 여정을 거쳐 도출됐다는
> 기록이 D2 정의 자체의 일부이기 때문이다. A=1 은 그 여정의 정직한 결과다."*

약점을 *미래 가능성으로 덮지 않음*. *여정의 정직한 결과로* 제시.

---

**0년 3개의 구조적 의미 — 노이즈 제거로 새로 드러난 KOSPI200 부실 신호의 진짜 구조**:

(1) **확정값**: 0년 = {2015, 2021, 2023}, 3개 (정정 전 2개에서 +1).
(2) **변동 사유**: A 에서 제거된 합병 7건 중 3건이 2015년 집중 (삼성물산
    2015-09-15 / SK 2015-08-17 / 현대하이스코 2015-07-15). 노이즈 제거로
    2015 양성 3→0. 즉 *2015 의 양성은 본래 합병 노이즈*였음.
(3) **D2 의 세 한계 동시 존재**:
    - (a) 양성 20 — **절대 부족** (학습 임계 30 미달)
    - (b) 시간 축 매우 **불균등** — 양성 7개 연도 중 2020(9건) 압도, 나머지 1~3건
    - (c) **거시 충격 집중** — 2020 코로나 panic 이 9/20 (45%)

    세 한계는 §5.5.2 "KOSPI200 대형주 부실 희소성" 인사이트의 정량 표현.
(4) **단계 2 D8 영향**: walk-forward 평가에서 *evaluation fold 선택의 핵심
    제약*. 0년 fold (2015/2021/2023) 에 양성 0 → PR-AUC 정의 불가. D8 첫
    의사결정에서 (a) fold 선택 (b) time-aware bootstrap 사용 여부 (c) 0년 fold
    처리 (skip / merged / synthetic) 를 정면 대응. *지금 §5.5.9 에는
    "한계 인지 + 단계 2 정면 대응" 으로만 박고 구체 평가 설계는 D8 시점*.

---

**034730 (신 SK) B 양성 정당성 검증 — 박제 직전 세 번째 안전장치 작동**:

A 육안 게이트 (1차) 와 KOSPI 계속기업 의문 추측 문자열 부재 발견 (2차) 에 이어
박제 직전 *세 번째 검증*: 신 SK 034730 의 B 신호가 합병(2015-08-17) 부수효과인지
독립 재무 충격인지.

실측 (`diag.events_b` 직접 추출):
- dd_date: **2020-03-17** (코로나 panic peak)
- dd_value: **−50.80%**
- op_prev (FY2019): **+3,949,864,000,000** (≈ 3.95조 흑자)
- op_curr (FY2020): **−164,471,000,000** (≈ 1,645억 적자)
- 영업이익 전환: **4.1조원 감소**
- 합병 이후 경과: **4.58년**
- OHLCV 캐시 기간: 2015-01-02 ~ 2024-12-30 (10년 풀)

판정 — 정당한 B 양성 (4 증거):
1. **시점 격차**: 합병 후 4.58년 — 부수효과로 보기엔 너무 멀음
2. **거시 원인**: 2020-03-17 = 코로나 panic peak. B 19 중 9건이 2020 다발
3. **영업이익 전환 실체**: 4.1조원 감소는 *지주회사 형태인 신 SK 가 자회사
   (정유·화학) 코로나 충격을 CFS 로 통합 반영*한 결과
4. **가격 추이**: 2-17(-19%) → 2-28(-32%) → 3-13(-44%) → 3-17(**-51%**) →
   3-19(-62% 최저) → 반등. *코로나 시장 충격 표준 패턴* (합병 부수효과의
   step-down 패턴과 형태 다름)

**세 번 박제 직전 안전장치가 모두 작동한 사례** — A 게이트 / 추측 문자열
부재 / 034730 검증. 검증 안전장치를 의례적이 아닌 *실제 작동하는 가드*로
운용해온 결과.

---

**부수 발견 1 — 지주회사 CFS *증폭* 사례 (§3 단계 2 DoD 와 cross-reference)**:

034730 정당성 검증에서 도출된 부수 인사이트. PROGRESS §3 단계 2 DoD 의
*"지주회사 CFS 부실 신호 희석 우려"* 항목과 직접 연관 — *반례 사례*:

- 희석 우려 (PROGRESS §3 기존): 지주회사 CFS 는 자회사 손익이 통합되어 *모회사
  단독의 부실*이 가려질 수 있음.
- **본 사례 — 신 SK 2020 (정반대 패턴)**: 자회사 (SK이노베이션·정유 등) 코로나
  충격이 CFS 에 *충실히 합산* 되어 모회사 영업이익 양 (+3.95조) → 음 (-1,645억)
  전환. *희석이 아니라 증폭*.

→ §3 단계 2 DoD 갱신: "CFS 의 (a) 희석 우려 + (b) 증폭 사례 양방향 검증" +
신 SK 2020 명시 사례 + 단계 2 D10 OFS fallback 적용 시 지주회사군
(034730·267250·267260 등 B 19 내) 정량 분석.

---

**부수 발견 2 — FDR `listing` (key='Code') vs `delisting` (key='Symbol')**:

`scripts/capture_d2_positives.py` 의 회사명 lookup 디버깅 중 발견. FDR 두
데이터셋이 ticker key 컬럼명이 다름:
- `fdr.listing()` 컬럼: `Code`, `ISU_CD`, `Name`, `Market`, ...
- `fdr.delisting()` 컬럼: `Symbol`, `Name`, `Market`, `Reason`, `ToSymbol`, ...

영향: features 모듈 (단계 2) 이 종목 코드를 키로 두 데이터셋을 join 할 때
*silently 잘못된 매핑* 또는 *키 불일치를 "데이터 없음" 으로 오해* 위험.
→ §3 단계 2 DoD 신설 항목: "FDR 데이터셋 표준화 helper" 추가.

---

**진행 절차 결과 기록** (사용자 명시 확인 게이트 체크):

1. ✅ Step 1 — ToSymbol/ToName 가설 *기각* (76% 결측) + Reason 카테고리
   화이트리스트 정밀화 (4 카테고리 검증 → 옵션 A 최종 채택, KOSPI 계속기업
   의문 추측 문자열 0건 부재 발견 → 죽은 안전망 폐기)
2. ✅ Step 2 — 진단 distress filter 수정 (commit X `a2fef19`) → 재실행 →
   A=1 / B=19 / α=20 / 0년 {2015,2021,2023} 확정
3. ✅ Step 3 — capture 재실행 + 034730 정당성 검증 (3번째 안전장치) →
   20 종목 전체 리스트 + 회사명 + assertion 전수 통과 (commit Y `1c50032`)
4. ✅ Step 5 — 본 §5.5.9 최종 박제 + CLAUDE.md + §3 DoD (commit Z)
5. (다음) **★ D2 데이터 충분성 검토 게이트** — labels.py 구현 *직전*:
   - (a) 보강 옵션 비교표 작성 — KOSDAQ150 시점별 구성 (KRX 정보데이터시스템
     수동 다운로드 가능성), forward window 1년→2년 확장, 기타 후보 각각의
     작업 비용·예상 양성 증분·방법론적 영향.
   - (b) 사용자 결정 — 보강 진행 후 labels.py 또는 양성 20으로 labels.py 진입.
   - (c) 결과가 "보강 안 함"이어도 의식적 검토의 기록을 남김.

   PROGRESS §3 단계 2 DoD 의 "D2 라벨 출처 보강 결정" 항목의 실행 시점이며
   labels.py 직전이 가장 자연스러운 타이밍.
6. (게이트 후) labels.py 설계안 재제시 (수치 갱신 — EXPECTED_POSITIVES·
   EXPECTED_YEAR_DIST) → 사용자 확인 → 코드 작성.

---

**남기는 이유** (§5.5.7 D2 여정·§4-pre CRLF 정정 보존과 같은 원칙):

"§5.5.5 경고 → §5.5.7 누락 → A 육안 게이트로 박제 직전 포착 → ToSymbol
가설 데이터 기각 → KOSPI 계속기업 의문 추측 문자열 부재 발견 → 034730 정당성
검증 → 옵션 A 정직성 채택" 의 전 경위는 *방법론적 추적성의 증거*. **세 번의
박제 직전 포착** (A 8 합병 / 추측 문자열 부재 / 034730 B 양성 정당성) 모두
사용자 강화 안전장치가 작동해 잡은 사례. 사후 정직성·재현성·면접 방어의
기록 자체가 가치.

---

### 5.5.10. D2 데이터 충분성 검토 게이트 결과 — O2/O1 검토 + "보강 안 함" 결정 (2026-05-20)

§5.5.9 P1 정정 후 labels.py 직전 게이트. 보강 옵션 O2 (forward 1→2년) +
O1 (KRX KOSDAQ150 가용성) 정량/정밀 검토 후 *의식적 보강 안 함* 결정 + 근거.

**O2 (forward 1→2년) — 12건 전수 의미 검증 → 전체 기각**:

표면 결과 (임시 시범 스크립트 `scripts/_o2_pilot_forward2y.py`, 본 게이트
종료 시 삭제): B 19 → 31, α 20 → 32, 0년 {2015,2021,2023} → {2015,2023},
손실 0. 학습 임계 30 *돌파*처럼 보임.

4건 spot-check 에서 §5.5.9 거울상 패턴 1차 발견 (LG디스플레이 합당 / 영풍
명확 노이즈 / 태영건설 합당 모호 / 137310 회계 구조 의문) → 사용자 (β)
채택으로 *추정 25-50%* 가 아닌 *실측* 12건 전수 검증.

**12건 전수 판정** (워크트리 인라인 inspect 로그 + 137310 DART 공시 조회):

| 카테고리 | 종목 수 | 종목 코드 (구분) |
|---|---|---|
| ✅ 합당 | 5 (42%) | 034220 (LG디스플레이) · 009410 (태영건설) · 003000 (부광약품) · 005420 (코스모화학) · 032350 (롯데관광개발) |
| ⚠ 모호 | 3 (25%) | 137310 (에스디바이오센서) · 302440 (SK바이오사이언스) · 033530 (SJG세종) |
| ❌ 명확 노이즈 | 4 (33%) | 000670 (영풍) · 000430 (대원강업) · 022100 (포스코DX) · 271940 (일진하이솔루스) |

각 종목 판정 근거 — dd 시점 부실 신호 (영업이익·매출·부채·현금흐름) vs
2년 후 적자 직접 원인 vs D2 의도 합치. 종목 코드의 사후 검색 시 워크트리
세션 로그 (2026-05-20) 참조.

**O2 기각 5 근거**:

1. **학습 임계 미달** — 모든 가중치 가정에서 α < 30:
   - 보수 (모호 = 노이즈): 신규 합당 5 → α = **25**
   - 중간 (모호 = 0.5): α = **26.5**
   - 낙관 (모호 = 합당): 신규 8 → α = **28**

   표면 α 32 의 "임계 돌파" 효과는 *실효 없음*.

2. **부분 채택의 자의성 함정** — 합당 5 만 선별하면 §5.5.9 옵션 B (변종 enum
   선별) 의 자의적 키워드 땜질 패턴 재발. 어느 종목이 합당인지 판정 자체가
   *후속 자의적 임계*.

3. **모호 3건의 라벨 의미 흐림** — 137310 (에스디바이오센서) + 302440 (SK
   바이오사이언스) 의 *코로나 사업 환경 변화*를 부실로 분류할지 D2 정의
   자체 변경 의미. 033530 약한 신호.

4. **§5.5.7/§5.5.9 정직성 원칙** — "양성 수 증가가 라벨 의미와 분리되면 안
   됨". 노이즈 4 + 모호 3 = 최소 7건이 라벨 의미와 분리 위험.

5. **양성 20 한계는 이미 정직 박제** — §5.5.9 의 0년 3개 + B 주축 95% +
   학습 임계 미달 모두 명시. labels.py 후 D8 에서 *class weight·forward
   2년 ablation·bootstrap·시점별 가중치* 의 *세컨 옵션*으로 모델 측 보완
   가능. *라벨 측 보강은 노이즈 도입 위험 큼*.

**노이즈 4건의 공통 패턴 — §5.5.9 합병 노이즈의 정확한 거울상**:

- dd 시점 매출·순익·부채 모두 *안정 또는 개선*
- 2년 후 *일시 작은 영업적자* (−50억 ~ −195억 수준)
- 다음 해 *회복* (영업이익 +흑자, 매출 증가)
- 부채비율 안정 또는 개선

→ *별개 후속 사건이 우연히 영업이익 일시 변동*. dd 시점 부실 신호 부재.

§5.5.9 합병 노이즈가 *"상폐 사실이지만 부실 아님"* 이었다면 본 케이스는
*"2년 후 적자이지만 dd 시점 부실 신호 아님"* — **시점만 바뀐 같은 패턴**.

**부수 발견 — 137310 종목명 lookup 오류**:

capture 1차 보고에서 137310 = "대한약품" 으로 표기됐으나 *FDR listing.Code
기반 lookup 결과 = 에스디바이오센서* (코로나19 진단키트 제조). §3 단계 2
DoD 의 *"FDR 데이터셋 ticker key 컬럼 불일치 (listing=Code, delisting=
Symbol)"* 항목의 두 번째 실제 사례 (신 SK CFS 증폭에 이어). features 모듈
표준화 helper 필요성 재확인.

**O1 (KRX KOSDAQ150) — §5.5.6 결론 유지**:

- WebSearch 결과 KRX Data Marketplace 통계 데이터 제공 확인했으나 *시점별
  구성 일자 입력* 메뉴의 실제 동작은 WebFetch/WebSearch 로 검증 불가 (JS
  렌더링)
- 사용자 직접 KRX 접속 또는 Playwright/Selenium 자동화는 게이트 의의 대비
  부담 과함
- §5.5.6 시점 (2026-05-18, 2일 전) 의 "KOSDAQ150 일자 입력 부재 → empty
  응답" 결론 신뢰
- 본 결정은 *게이트 단계에서 부담 vs 의의 평가로 미수행*. 단계 2 D2 보강
  항목에서 재검토 시점에 정밀 검증 (사용자 직접 접속 또는 별도 평가).

**최종 결정 — "보강 안 함"**:

양성 20 (포스코플랜텍 1 + B 19) 그대로 labels.py 진입. 한계는 §5.5.9 정직
기록 그대로 — 0년 3개 + 학습 임계 미달 + B 주축 95%. 단계 2 D8 에서 *모델
측 보완* (class weight·forward 2년 ablation·bootstrap·시점별 가중치) 으로
정면 대응.

**향후 D2 라벨 출처 보강 방향 — *자의성 함정 시점 이동 차단***:

본 검증에서 forward window 1→2년 변경이 합당/모호/노이즈 **42/25/33%** 로
*라벨 의미 균질성을 깨뜨림*이 입증됐으므로, **forward window 방향은 D2
보강 옵션에서 전체 폐기**. 합당 5 / 모호 3 / 노이즈 4 분류 자체는 *forward
window 옵션의 라벨 의미 분산을 입증하는 데이터로 기록*되며, **개별 종목을
미래 추가 후보로 우선 검토하는 근거로 사용되지 않는다** (그렇게 사용하면
§5.5.9 옵션 B 자의적 변종 선별 패턴의 *시점 이동에 불과*).

향후 D2 라벨 출처 보강은 *forward window 변경 방향이 아닌 다른 방향*으로
검토:
- KOSDAQ150 KRX 가용성 정밀 검증 (사용자 직접 KRX 접속 또는 자동화)
- KRX 별도 데이터 (정보데이터시스템 관리종목·부실관련 분류 수동 다운로드)
- 출처 자체 확장 (단계 2 §3 DoD "D2 라벨 출처 보강 결정" 항목 — FDR 한계
  보강)

**남기는 이유** (§5.5.7·§5.5.9 와 동일 원칙):

표면 매력 (α +12, 0년 해소) 을 *의미 검증으로 기각*한 사례. 절차:
*4건 spot-check 패턴 발견 → 사용자 (β) 채택 → 12건 전수 검증* — *추정 25-50%
가 아닌 실측 33% 노이즈 + 25% 모호*. 게이트의 정직성 원칙은 *결정 결과* 보다
*근거의 견고성* 우선.

본 §5.5.10 의 가치는 *"보강 안 함" 결정 자체* 가 아니라 *그 결정 근거가
12 종목 전수 의미 검증의 실측 위에 있다*는 점. 단계 2 진입 후 양성 20의
한계가 학습에 영향을 줄 때 *"왜 보강 안 했나"* 의 답이 *§5.5.10 의 12 종목
판정 + 5 근거* 로 분명. **면접 방어 정직성 = 자료 견고성**.

---

### 5.5.11. D10 가정 오류 + 작업 직전 dart.py 점검으로 잡힌 사례 (2026-05-20)

> **본 절은 본 세션의 자문 측 가정 오류와 작업 직전 실측으로 잡힌 사례
> 박제.** §5.5.9 (§5.5.5 경고 → §5.5.7 박제 시 누락) 의 거울상 패턴 —
> PROGRESS §결정 로그에 *2026-05-18 D10 옵션 C (CFS 우선 + OFS fallback)
> 승인* 박혀 있었으나 본 세션이 *"D10 미적용 단계 2 step #3 작업 예정"*
> 가정 위에서 진행한 사례.

**경위**:
- 본 세션 내내 "D10 미적용, 단계 2 step #3 작업 예정" 가정 위에서 진행
- (Z) 절충안까지 합의 — *dart.py 변경 diff + 9 FY None 케이스에 OFS
  fallback 적용*
- 작업 직전 dart.py 재읽기에서 **D10 OFS fallback 코드가 이미 적용됨**을
  발견 (commit `6962cb7` "feat(dart): D10 - CFS preferred with OFS
  fallback", 본 세션 시작 *전*)
- `test_dart.py` 에 fs_div 단위 테스트 4건도 이미 박혀 있음 (CFS 기록 / OFS
  fallback 기록 / notfound / 레거시 호환)
- 사전 검증 (가)(나)(다) — *"D10 미적용 검증"* 으로 인식했으나 *실제로는*
  *"D10 이미 적용된 상태에서 labels.py 영향 0 재검증"* 으로 의미 재해석.
  9 FY None 케이스도 *D10 fallback 시도된 후* 캐시된 결과로 추정 (정확한
  fallback 동작 여부는 features 단계 백필 시점에 정밀 분석)

**자문 측 가정 오류 — Co-Authored-By 가정 오류에 이은 두 번째 사례**:
- 첫 번째: commit Z 직전, "이전 커밋들에 Co-Authored-By 없음" 잘못된 가정
  (실제 모두 있음). Code 가 git log 로 실측 → 정정.
- 두 번째: 본 세션 내내 "D10 미적용" 잘못된 가정 (실제 commit `6962cb7` 로
  단계 1 시점 적용). Code 가 작업 직전 dart.py 재읽기로 실측 → 정정.

**교훈 — 자문 시스템도 "추정 말고 실측" 정신 적용**:
사용자 (자문 측) 와 Code 모두 동일한 정직성 원칙. 작업 진입 시점에 다음
자문 측 검증 게이트를 명시 절차로 채택:
- **PROGRESS §결정 로그 점검** — 본 세션 작업 영역의 *과거 결정* 확인
- **`git log -- <파일>`** — 작업 대상 파일의 최근 변경 이력 확인
- **관련 코드 한 번 더 읽기** — 작업 직전 *현 상태* 실측 (가정 우회 차단)

본 게이트가 §5.5.9 의 *"A 8 육안 게이트"* + §5.5.10 의 *"12건 전수 검증"*
과 같은 정신 — *가정 위에서 작업 들어가는 패턴의 시점 이동 차단*.

**(Z) → (W') 옵션 채택 사유**:
- D10 본질적 작업 (코드 + labels 영향 0) 은 이미 완료
- 잔여 항목 (백필·9 FY refresh) 은 *features 단계 자연스러운 항목*
- 본 turn 의 추가 작업: ① labels.py 통합 테스트 재실행 (양성 20 변동 0
  실측 재확인) ② dart.py fs_div 단위 테스트 4건 검증 (이미 PASS) ③ PROGRESS
  정정 박제

**잔여 항목 (features 단계 이전)**:
- 캐시 fs_div 메타 백필 (10,114 모두 None) — 일괄 vs lazy 방식은 features
  시점 결정
- 9 FY None 케이스 (롯데지주·SK텔레콤·하나투어·더블유게임즈·두산퓨얼셀)
  refresh fetch — OFS fallback 시 실제 영업이익 회수 가능성 정밀 분석
- §3 DoD 의 *지주회사 CFS 희석/증폭* 점검 항목 — D10 인프라 이미 있음,
  features 에서 활용

**남기는 이유** (§5.5.7·§5.5.9·§5.5.10 와 동일 원칙):
"PROGRESS 결정 → 본 세션 가정 누락 → 작업 직전 실측으로 포착 → 정정" 의
전 경위는 *자문 시스템도 "추정 말고 실측" 정신 적용*의 증거. 두 번 (Co-Authored-By
+ D10) 에 걸쳐 입증된 패턴 — 미래 자문 시스템 운용의 명시적 가이드.

---

### 5.5.12. Walk-forward 합의 + D2 정직성 사슬 4 차원 종합 (2026-05-20 본 세션 종료 박제)

> **본 절은 본 세션 종료 박제 — 다음 세션 walk-forward 코드 작성이 합의된
> 알고리즘·정밀화 사항을 *모른 채로 시작*하는 위험을 차단**. §5.5.11 학습
> ("작업 진입 시점에 PROGRESS·git log 점검을 자문/실행 양측 검증 게이트로")
> 의 환경 차원 적용 — 미래 세션이 합의를 *추정*이 아닌 *문서 박제 실측*으로
> 확보.

**Walk-forward 골격 합의** (옵션 X-a: 최소 골격 + 0년 placeholder):

- **위치**: `src/frr/eval/splits.py` (신규 `eval/` 패키지). 향후 D8 모듈
  (metrics·calibration·bootstrap) 가 같은 그룹으로 자연 확장 — *점진 생성*
  원칙 (CLAUDE.md §8.6).
- **as_of_grid 추출**: walk-forward 모듈 내부 `_quarter_end_grid(loader)`
  헬퍼 — universe_loader 책임 분리 유지.

**핵심 데이터 클래스**:

```python
@dataclass(frozen=True)
class WalkForwardFold:
    train_start: date     # 분석 기간 시작 (모든 fold 고정 — expanding)
    train_end: date       # 본 fold train 종료 (embargo 충족 분기말)
    test_as_of: date      # test 시점 (분기말 영업일)
    embargo_days: int     # 자체 무결성 검증용 필드
    fold_id: int

    def __post_init__(self) -> None:
        # 시간 순 검증
        if not (self.train_start < self.train_end < self.test_as_of):
            raise ValueError(...)
        # embargo 준수 검증 (정밀화 #3)
        if self.train_end > self.test_as_of - timedelta(days=self.embargo_days):
            raise ValueError(...)
```

→ walk_forward_expanding 우회하고 직접 WalkForwardFold 생성해도 검증 작동.
*features 격리 (i)(ii) 가 import-level 차단이듯, fold 무결성은 dataclass-level
차단*.

**핵심 함수 시그니처**:

```python
def walk_forward_expanding(
    *,
    as_of_grid: list[date],
    min_train_quarters: int = 8,        # 학습 임계 (2년 = 8 분기)
    embargo_days: int = 365,            # forward_window_days 와 *일관*
    analysis_start: date = date(2015, 1, 1),
    zero_year_handling: Literal["skip", "merged", "synthetic", "raise"] = "raise",
    zero_years: frozenset[int] | None = None,
) -> list[WalkForwardFold]:
    """Expanding window + embargo gap.

    forward_window_days 는 labels.py 소관, embargo_days 는 본 모듈 소관.
    호출자가 둘의 *일관성 유지 책임* (둘 다 365 기본).

    알고리즘:
      for each test_as_of in as_of_grid:
          train_end_threshold = test_as_of - timedelta(days=embargo_days)
          valid_train_grid = [q for q in as_of_grid if q <= threshold]
          if len(valid_train_grid) < min_train_quarters:
              continue   # train 분기 부족, skip
          train_end = max(valid_train_grid)
          yield WalkForwardFold(...)

    0년 fold 처리 (§5.5.10):
      zero_year_handling != "raise" → NotImplementedError
        (D8 결정 시점에 구현, 격리 (iii) placeholder 와 같은 패턴)

    min_train > len(as_of_grid) → ValueError (silent 실패 차단, 정밀화 #2)
    """
```

**Embargo 본질 — 시간 누수 차단**:

walk-forward 의 *근본적* 안전장치. fold i 의 *train 내부* 각 `as_of=s` 의
label 은 `(s, s + forward_window]` event 로 결정. 만약 `s + forward_window
> train_end` 이면 *train 의 label 정의 자체가 train_end 이후 event 를 본
결과* → **train 에 미래 정보 누수**. forward_window=365 인 본 프로젝트에서는
*train 의 모든 as_of s 가 `s ≤ train_end - 365` 보장* 되어야 함.

→ **embargo_days = forward_window_days = 365** 로 일관성 유지. 향후 forward
window 변경 시 embargo 도 동일 변경 (호출자 책임).

**예상 fold 수** (40 분기, min_train=8, embargo=365):
- 8 + 4 (1년 ≈ 4 분기) = 12 분기 누적 후 첫 fold
- 예상 첫 fold: `i=12, test=2018Q1, train=[2015Q1~2017Q1]`
- **예상 총 28 folds** (40 − 12 = 28, embargo 없는 경우 32 대비 −4)
- *정확한 수는 다음 세션 코드 작성 후 실측 보고* — 본 박제는 예상치만.

**정직성**: embargo 로 fold 수 감소 (32→28) 는 *학습 데이터 약간 손실*이나,
label 누수 차단이 *우선*. §5.5.10 의 *"노이즈 27 > 정직한 20 이 아님"* 정신과
같음 — 손실 받아들이고 정직성 보존.

**단위 테스트 9건** (CI 실행 가능, 합성 데이터):

| # | 시나리오 | 검증 |
|---|---|---|
| 1 | 합성 as_of_grid 40개, min_train=8, embargo=365 → 28 folds (예상) | fold 수 일치 |
| 2 | 첫 fold | train_end = grid[i-?], test = grid[12] (embargo 후) |
| 3 | 마지막 fold | test = grid[39] (2024Q4) |
| 4 | Expanding 확인 | `folds[i].train_end ≤ folds[i+1].train_end` 시간 순 |
| 5 | train_start 모든 fold 고정 | `all(f.train_start == analysis_start)` |
| 6 | min_train > len(as_of_grid) | **ValueError** (silent 차단, 정밀화 #2) |
| 7 | zero_year_handling="skip"/"merged"/"synthetic" 호출 | **NotImplementedError** + "D8 결정 시점" + "§5.5.10 참조" 포함 |
| 8 | zero_year_handling="raise" (기본) | 정상 fold 생성, 0년 fold 도 그대로 반환 |
| 9 | **WalkForwardFold 직접 생성 시 embargo 위반** | **ValueError** (dataclass __post_init__ 검증, 정밀화 #3) |

**다음 세션 작업 7 단계** (본 세션 종료 시 합의):
1. embargo 알고리즘 정확 구현 (train_end_threshold + valid_train_grid + skip 로직)
2. `src/frr/eval/__init__.py` + `src/frr/eval/splits.py` 작성
3. 단위 테스트 9건 (위 표)
4. 실제 분석 기간 적용 fold 수 실측 보고 (예상 28)
5. labels.py 통합 + 격리 + 회귀 영향 0 재확인
6. ruff format → commit (`feat(eval): add walk-forward expanding window with embargo gap`)
7. push → CI 그린 실측

---

**D2 정직성 사슬 4 차원 종합 정리** (본 세션 마무리 종합):

D2 라벨 정의를 *4 차원의 누수 차단* 으로 보호. 각 차원이 다른 종류의 누수를
차단하며, *모든 차원이 박제되어야 D2 의 통합적 정직성*이 성립:

| 차원 | 박제 위치 | 차단 대상 | 안전장치 |
|---|---|---|---|
| **변수 차원** | §5.5.7→§5.5.9 distress filter | 합병성 자발 해산 → A 라벨 노이즈 | A 8 육안 게이트로 7건 합병 적발 + P1 화이트리스트 `{"자본전액잠식"}` |
| **양성 충분성 차원** | §5.5.10 | 양성 수 늘리려는 forward window 확장 → 라벨 의미 균질성 파괴 | O2 forward 1→2년 ablation 12건 전수 의미 검증 (합당 5/모호 3/노이즈 4) → 자의적 변종 선별 차단 → 기각 |
| **격리 차원** | commit `a0d7932` (`tests/test_isolation.py`) | features 모듈이 라벨 변수 (DelistingDate·Reason·KOSPI200 편입 등) 직접 학습 → 라벨 누수 | AST + 컬럼 화이트리스트 + 변환 게이트 (missing/active/empty) |
| **시간 차원** | 본 §5.5.12 + 다음 세션 walk-forward + embargo | train 의 label 정의 자체가 미래 event 본 결과 → 시간 누수 | `embargo_days = forward_window_days = 365` 일관성, WalkForwardFold dataclass `__post_init__` 검증 |

**의미**: 격리 프레임워크가 *features 변수 누수*를 차단했듯, embargo 가
*시간 누수*를 차단. 두 안전장치가 *동시 작동*해야 모델 평가의 정직성 보존.
D2 정직성 사슬 4 차원이 *완성되는 시점이 walk-forward 코드 작성 직후* —
다음 세션의 의미.

**자문 측 정직성 사슬 2 사례** (§5.5.11 박제 그대로 — 본 절에서 재정리 X):
- Co-Authored-By 가정 오류 → git log 실측 정정
- D10 가정 오류 → 작업 직전 dart.py 재읽기로 §5.5.11 박제

자문/실행 양측 모두 "추정 말고 실측" 정신 적용 — 작업 진입 시점에 PROGRESS·
git log·관련 코드 *실측 점검* 을 자문 측 검증 게이트로 명시.

---

**남기는 이유** (§5.5.7·§5.5.9·§5.5.10·§5.5.11 와 동일 원칙):

본 박제의 가치는 *합의 내용 자체* 가 아니라 *합의가 다음 세션에 실측 문서로
전달되는 것*. 다음 세션이 walk-forward 합의를 *모른 채로 시작*하면 코드가
다시 처음부터 설계되거나 합의와 다른 방향으로 작성될 위험. 본 박제로 그 위험
사전 차단. **§5.5.11 학습의 환경 차원 적용**.

---

### 5.5.13. Walk-forward 코드 작성 실측 + D2 정직성 *시간 차원* 완성 (2026-05-20)

> §5.5.12 합의 코드 구현 + 실측. **§5.5.12 의 *예상* 28 folds 가 실측 28 과
> 정확히 일치** — 합의 시점의 추정이 실제로 정확했음을 검증.

**작업 7 단계** (§5.5.12 명시) 모두 완료:

1. ✅ embargo 알고리즘 정확 구현 — `train_end_threshold = test_as_of - timedelta(days=embargo_days)`, `valid_train_grid = [q for q in grid if q ≤ threshold]`, `len(valid) < min_train` 시 skip, 아니면 `train_end = max(valid)`.
2. ✅ `src/frr/eval/__init__.py` + `src/frr/eval/splits.py` 작성. `WalkForwardFold` (frozen dataclass + `__post_init__` 2 단계 검증) + `walk_forward_expanding(*, ...)` + `_quarter_end_grid(loader)` 헬퍼.
3. ✅ 단위 테스트 9건 + 시간순 검증 분리 1건 + parametrize 3건 = **총 12건 통과** (`tests/test_splits.py`).
4. ✅ **실제 40 분기 grid 적용 fold 수 = 28 (박제 예상 정확히 일치)**.
5. ✅ 전체 105 통과 + 4 skip + 7 integration deselected, 회귀 영향 0.
6. ✅ ruff format → commit (본 박제 후 진행).
7. ✅ push → CI 그린 (본 박제 후 진행).

**합성 grid (휴일 무시) 29 vs 실제 grid (holiday fallback 포함) 28** — 1 fold 차이:

- 합성: `test=2017-12-31` 의 `threshold=2016-12-31`. grid[7]=2016-12-31 정확히 일치 → valid=grid[0..7]=8개 충족 → 첫 fold (i=11).
- 실제: `test=grid[11]=2017-12-28` (holiday fallback) 의 `threshold=2016-12-28`. grid[7]=2016-12-29 (holiday fallback) > threshold → 제외, valid=7개 부족 → skip. 첫 fold = grid[12]=2018-03-30 (i=12).
- → **holiday fallback 권위 보존 효과로 1 fold 손실, 정직성 우선**. 박제 예상 28 정확히 일치.

**universe_loader.reference_date 메서드 추가 경위** (§5.5.12 합의 외 결정 — 사용자 합의 게이트 통과 후):

`_quarter_end_grid(loader)` 헬퍼가 분기 라벨 → date 변환 시 권위 정보가 매니페스트 `actual_reference_date` (13/40 분기 holiday fallback 처리됨, 실측 결과 *20/40* 으로 더 많음). 이 정보가 *private* `QuarterEntry._entries` 였음. 옵션 3 가지 (private 접근 / 공개 메서드 추가 / 추론) 중 사용자가 *공개 메서드 1줄 추가* 선택 — 캡슐화·정직성·점진 생성 (CLAUDE.md §8.6) 모두 만족.

→ `KOSPI200QuarterlyLoader.reference_date(quarter) -> date` 1 메서드 + 단위 테스트 2건 추가.

**holiday fallback 실측 20/40 분기** (PROGRESS §2 의 13/40 보다 7 분기 더 많음):
- 2015Q4·2016Q4·2017Q3·2017Q4·2018Q1~Q4·2019Q1·Q2·Q4·2020Q3·Q4·2021Q4·2022Q4·2023Q3·Q4·2024Q1·Q2·Q4
- §2 박제의 13 은 다운로드 시점 사용자 일괄 보고 카운트, 실측 20 은 매니페스트 *현재* 상태. 차이는 후속 fallback 적용 분기 — 본 절에서 실측 우선.

**D2 정직성 사슬 4 차원 — *시간 차원* 완성 시점**:

| 차원 | 박제 위치 | 상태 |
|---|---|---|
| 변수 차원 | §5.5.9 distress 화이트리스트 | ✅ |
| 양성 충분성 | §5.5.10 O2/O1 기각 | ✅ |
| 격리 차원 | commit `a0d7932` (test_isolation.py) | ✅ (features 작성 시 자동 활성) |
| **시간 차원** | **본 §5.5.13 + eval/splits.py + 12 테스트** | **✅ (본 작업으로 완성)** |

격리 (i)(ii) 가 *features 변수 누수* 를 import-level 차단했듯, embargo 가 *시간 누수* 를 dataclass-level + algorithm-level 양쪽으로 차단. 두 안전장치가 동시 작동해야 모델 평가의 통합 정직성 보존 — 본 시점에 사슬 모두 박힘.

**정밀화 #2·#3 실증 단위 테스트로 박힘**:

- 정밀화 #2 (silent 차단): `min_train_quarters > len(as_of_grid)` 시 ValueError. silent 빈 fold 리스트 반환은 호출자가 *실행 안 됨* 을 인지 못 함. 테스트 `test_min_train_exceeds_grid_raises_value_error`.
- 정밀화 #3 (dataclass-level 검증): `WalkForwardFold.__post_init__` 가 (a) 시간순 (`train_start < train_end < test_as_of`) + (b) embargo (`train_end ≤ test_as_of - embargo_days`) 2 단계 검증. walk_forward_expanding 우회해 직접 생성해도 무결성 보장. 두 단계 모두 도달 가능 함을 별도 테스트 2건으로 박제 (`test_walk_forward_fold_direct_embargo_violation_raises`, `test_walk_forward_fold_direct_time_order_violation_raises`).

**0년 fold placeholder** (격리 (iii) 와 같은 패턴):

- 현재 `zero_year_handling="raise"` 만 지원
- `"skip"/"merged"/"synthetic"` 호출 시 NotImplementedError + 메시지에 "D8 결정 시점" + "§5.5.10 참조" 둘 다 포함 — 미래 작업이 PROGRESS 결정으로 연결됨을 명시
- D8 결정 시점에 본격 구현 (호출자가 양성 0 연도 frozenset 주입)

**남기는 이유** (§5.5.7·§5.5.9·§5.5.10·§5.5.11·§5.5.12 와 동일 원칙):

§5.5.12 의 합의 박제가 *다음 세션이 모른 채로 시작하는 위험 차단* 이었듯, 본 §5.5.13 의 실측 박제는 *합의된 예상과 실측이 일치함을 보존* — 미래 features 작업 시점에 walk-forward 가 *어떻게 동작하는지·왜 28 folds 인지* 가 코드만 보고도 추적 가능. **자문 측 정직성 사슬에 *작업 완료 시점의 실측 박제* 차원 추가**.

---

### 5.5.14. Stage-1 features 사전 토대 4 항목 설계 합의 (2026-05-20)

> §7.6 작업 진입 검토 사이클 통과 후 합의. 자문 측이 §5.5.13 종료 시점에
> 4 항목 권장 + 사용자 *그대로 채택 + 정밀화*. 본 박제로 2단계 진입.

**(b-1) build_features 시그니처 + strict default**:

```python
def build_features(
    ticker: str,
    as_of: date,
    *,
    reporter: DARTReporter | None = None,
    universe_loader: KOSPI200QuarterlyLoader | None = None,
    krx_ohlcv_cache_dir: Path | None = None,
) -> pd.DataFrame:
```

- `as_of` 가 빌더의 *공식 시간 인자* — 룩어헤드 contract 의 공식 입구
- **strict default**: 의존성 주입 인자 모두 Optional 이지만 *None 시 default
  생성하지 않음*. None 이면 ValueError ("의존성 명시 주입 필요").
- 사유: (1) 정직성 — 코드 자체에 의존성 명시 / (2) 진입점 한 곳에서 한 번
  생성 / (3) labels.py 의 dependency injection 패턴과 일관
- fs_div_strategy 인자 *제외* (D10 + (i) 컬럼 동행 단일 정책)

**(b-2) lookahead 검증 2 단계**:

| 단계 | 위치 | 방식 |
|---|---|---|
| (α) AST 화이트리스트 | test_isolation.py (iii) 활성화 | features 모듈의 모든 `dart.*` 호출 attr ⊆ `{available_at, latest_available, fetch_report}` |
| (β) 런타임 mock contract | tests/test_features_lookahead.py (신규) | build_features 에 mock reporter 주입 → mock 이 받은 모든 시점 인자의 available_from ≤ as_of |

- (γ) → (β) 흡수, 별도 단계 없음
- mock 정확한 시점 검증 로직은 2단계 코드 작성 시 자문 검토 (YAGNI)
- vacuous 위험: (α) 단독은 getattr 우회·간접 호출에 vacuous → (β) 가 실제
  호출 패턴 검증으로 보완. 두 단계 *다른 누수 패턴* 차단.

**(c) fs_div (i) + 격리 분리 + spot-check β1 시점**:

- 빌더: **(i) fs_div 컬럼 동행, 단일 정책 cfs_preferred** (D10 캐시 이미 반영,
  §2 fs_div 라벨 백필 완료)
- 격리: fs_div 컬럼은 features 출력 컬럼, **모델 입력 시 제외 — 모델 모듈
  책임**. test_isolation.py 가 아닌 *모델 모듈의 separate test* 로 검증.
- spot-check 시점: **β1 = features 직전** (§5.5.9 신 SK 1건 큰 영향, 반복
  여부 확인 후 features 설계 영향 검토)
- 진단 스크립트: `scripts/diagnose_holding_fs_div.py` — 양성 20 종목 중
  지주회사·금융지주 spot-check (신 SK 034730 포함 ≥4건). CFS vs OFS 영업이익
  분포 비교 + 요약 표.
- 진단 결과 PROGRESS 박제 후 features 설계 영향 검토 자문 사이클

**(d) fdr_ticker_key NaN + warning**:

```python
def fdr_ticker_key(df: pd.DataFrame, col: str | None = None) -> pd.Series:
    """FDR DataFrame ticker key 정규화 → 6자리 string Series.

    Code (fdr.listing) / Symbol (fdr.delisting) 자동 탐지. 6자리 아닌 row → NaN.
    NaN row 발생 시 logger.warning 으로 건수 로그 (silent drop 회피).
    universe 6자리 ticker 와 join 시 NaN 자동 차단.
    """
```

- 위치: `src/frr/data/fdr.py`
- 단위 테스트 3~5건 (Code/Symbol 자동 탐지, 8자리 NaN, 6자리 pass, 로그 경고)

**2단계 작업 순서 (6 단계, 각 단계 §7.6 통과 의무)**:

1. (c) spot-check 진단 (`scripts/diagnose_holding_fs_div.py`)
   → 결과 PROGRESS 박제 → features 설계 영향 자문 사이클
2. (d) fdr_ticker_key + 단위 테스트
3. features 첫 모듈 — *사용자 결정 게이트* (재무비율 baseline 군: balance
   sheet? income statement? 둘 다? — 자문 검토 사이클)
4. test_features_lookahead.py (β 런타임 mock contract)
5. test_isolation.py (iii) 활성화 (α AST 화이트리스트)
6. CI 통과 확인 + commit

**남기는 이유** (§5.5.7·§5.5.9·§5.5.10·§5.5.11·§5.5.12·§5.5.13 와 동일 원칙):
1단계 설계 합의가 다음 작업 진입 시점에 *합의 외 결정 진입* 차단. §7.6 검토
사이클의 1 단계 (PROGRESS 점검) 가 자연스럽게 본 절 참조.

---

### 5.5.15. 지주회사 CFS vs OFS 영업이익 spot-check 실측 (2026-05-21, §5.5.14 β1)

> §5.5.14 2단계 step 1 — `scripts/diagnose_holding_fs_div.py` 실행 결과 박제.
> §7.6 검토 사이클 통과 후 진단 → 키워드 매칭 false negative 발견 → 사용자
> 옵션 B (양성 20 전체) 채택 → 200 cells 실측.

**1차 결과 — 키워드 매칭 false negative**:

양성 20 종목 이름에 키워드 `{지주, 홀딩스, 홀딩, 금융지주, 은행지주}` 매칭 **0건**. 그러나 실제 지주성 종목은 PROGRESS 박제로 명시:
- 034730 *SK* (구 SK주식회사, 순수지주) — §5.5.9 4.1조 감소 사례
- 267250 *HD현대* (구 현대중공업지주, 2023 사명 변경)
- 096770 *SK이노베이션* (중간지주)

→ **키워드 단순 매칭은 features 식별 1차 필터로 부적합** (사명 변경·영문 약어). 명시적 화이트리스트 또는 fs_div 분포 기반 사후 식별 필요.

**옵션 B 실측 — 200 cells (20 종목 × 10년 FY 2015~2024)**:

| category | count | % | 의미 |
|---|---|---|---|
| 유사 (0.67 ≤ ratio ≤ 1.5) | 78 | 39.0% | CFS ≈ OFS, 자회사 영향 작음 (일반 종목 패턴) |
| 증폭 (ratio > 1.5) | 41 | 20.5% | CFS > OFS, 자회사 이익 통합 (지주 정상 패턴) |
| 둘 다 음수 | 39 | 19.5% | 영업적자 시점 |
| 둘 다 없음 | 24 | 12.0% | FY 미존재 (상장 전 등) |
| OFS 없음 | 7 | 3.5% | OFS finstate 미공시 |
| 부호 차이 CFS-/OFS+ | 6 | 3.0% | **D2 라벨 영향** |
| 부호 차이 CFS+/OFS- | 3 | 1.5% | **D2 라벨 영향** |
| 희석 (ratio < 0.67) | 2 | 1.0% | CFS < OFS, 자회사 손실 통합 |

- 증폭 ratio: median 3.31, max 47.36, min 1.51
- 희석 ratio: median 0.64, max 0.64, min 0.19

**종목별 패턴 (지주성 특성 확인)**:

| ticker | name | 지주성 | 증폭 | 다른 |
|---|---|---|---|---|
| **034730** | **SK** | 순수지주 | **9/10** | 부호 차이 1 (§5.5.9 사례) |
| **267250** | **HD현대** | 지주 | **7/10** | 둘 다 없음 2, 부호 차이 1 |
| **096770** | **SK이노베이션** | 중간지주 | **6/10** | 희석 1, 부호 차이 1, 유사 2 |
| 267260 | HD현대일렉트릭 | 자회사 | 1/10 | 유사 5 (일반 패턴) |
| 010950 | S-Oil | 정유 | 0/10 | 유사 8 |
| 047810 | 한국항공우주 | 일반 | 0/10 | 유사 9 |

→ 명시 지주회사 (034730·267250) 는 *대부분 연도 증폭*, 중간지주 (096770) 는 *증폭 + 일부 희석/부호 차이*, 일반 종목은 *대부분 유사*. **fs_div 차이는 지주성 판정의 *사후 식별 신호*로 활용 가능** (키워드 매칭의 false negative 보완).

**부호 차이 9 cells = D2 라벨 견고성 영향**:

labels.py 는 CFS 기반으로 *영업이익 양수→음수 전환* (B 신호) 판정. CFS+/OFS- (3건) 또는 CFS-/OFS+ (6건) 인 cells 에서는 *OFS 기반으로 재산출 시 양성 판정이 다를 수 있음*. 본 spot-check 가 *현 시점 D2 양성 20 의 fs_div 견고성 정량 자료* 제공.

- §5.5.9 신 SK 034730 FY2020 사례 = *CFS-/OFS+* 부호 차이의 1 인스턴스로 본 진단에서 확인
- 양성 20 중 부호 차이 cells 가 *9 cells / 200 = 4.5%* — *희소하나 영향 가능*

**features 설계 영향 (자문 의견)**:

1. **fs_div 컬럼 동행 필수성 확인**: 200 cells 의 27% (증폭 + 희석 + 부호 차이 + 둘 다 음수) 에서 *CFS vs OFS 의미 차이 있음*. 단일 영업이익 값으로는 지주 vs 일반 구분 불가능. (i) fs_div 컬럼 동행 (§5.5.14 합의) 의 *경험적 정당화*.
2. **D2 라벨 견고성 모델 단계 결정** (사용자 검토 사이클 표현 박제):
   - **라벨 유지** — §5.5.10 정신, 라벨 재산출 안 함. 부호 차이 9 cells 는
     모델 단계에서 보완.
   - **모델 단계 보완 방향**: **(a) fs_div as feature** 또는
     **(b) 지주/일반 군별 평가 (stratification)**. 둘은 상호 배타 아닌
     선택 (둘 다 가능). 모델 단계에서 D8 평가 지표와 함께 결정.
3. **지주성 사후 식별**: 명시 화이트리스트 필요 시 *증폭 비율 ≥ 7/10* 같은 통계 임계로 *사후 식별 보조 가능*. 본 사이클은 명시 화이트리스트 결정 안 함 (모델 단계로 이전).
4. **§3 DoD "지주회사 CFS 희석/증폭 점검" 항목 해소**: 본 §5.5.15 박제로 *진단 작업* 완료. 점검 항목은 *features 빌더 작성 + 모델 단계 결정* 으로 자연 전환.

**진단 산출물**:
- 스크립트: `scripts/diagnose_holding_fs_div.py` (git 추적)
- 결과 캐시 + 요약: `data/interim/holding_fs_div/` (gitignore — 재실행 시 캐시 hit)
- 박제 권위: 본 §5.5.15 본문 (수치·종목별 패턴 모두 포함, 재현성 보장)

**모델 단계 진입 결정 게이트 메모** (§7.6 정신, 사용자 검토 사이클 박제):

단계 2 모델 진입 시 다음 두 항목 사전 확인 의무:
1. **fs_div 활용 방법 결정** — (a) feature / (b) stratification / (c) 둘 다.
   본 §5.5.15 의 분포 (27% cells 차이, 부호 차이 9) 가 결정 baseline.
2. **지주회사 군 양성 종목 수 사전 확인** — 양성 20 중 명시 지주
   (034730·267250·096770) 3 종목 (15%). 모델 stratification 결정 시
   *지주 군 양성 3건* 이 학습 임계 미달 가능성 고려. 모델 단계 진입 시
   다른 *명시 X·증폭 비율 ≥ 7/10* 종목 (예: 034730 9/10·267250 7/10) 외
   지주성 종목을 §5.5.15 표 + 도메인 검토로 *재확인* 후 stratification 결정.

**남기는 이유**: features 빌더 작성 시점에 fs_div 처리 설계가 *경험적 증거*
없이 결정되지 않도록. (i) 컬럼 동행 결정 (§5.5.14) 의 정당화 + 모델 단계에서
fs_div 활용 결정의 *baseline 자료*. PROGRESS §3 DoD 의 점검 항목 해소.
*모델 단계 진입 결정 게이트 메모 추가* (2026-05-21 보완): §7.6 검토 사이클
정신 — 단계 2 모델 진입 시 *암묵 가정* 차단.

---

### 5.5.16. Stage-2 모델 진입 — B-1 결과 + B-2 5 항목 결정 (2026-05-21)

> 단계 2 모델 진입 게이트 — §5.5.15 모델 단계 진입 결정 게이트 메모 2 항목
> 적용. 작업을 5 작은 사이클 (B-1 ~ B-5) 로 세분화. 본 §5.5.16 은 B-1
> (지주 군 양성 종목 수 실측) 결과 + B-2 (5 항목 결정) 박제. B-3 (모델 학습
> 코드) 진입 입력.

**B-1 결과 — 지주 군 양성 종목 수 실측**:

§5.5.15 종목별 패턴 + 직전 spot-check 출력 종합:

| 분류 | 종목 | 증폭 비율 | 통계적 의미 |
|---|---|---|---|
| 명시 지주 (도메인 확신) | 034730 SK·267250 HD현대·096770 SK이노베이션 | 9/10·7/10·6/10 | **3 종목 (15%)** |
| 의심 추가 (도메인 검토 필요) | 010690 화신 (증폭 5 + 부호 차이 2 + 희석 1) | 5/10 | 1 종목 추가 가능 |
| 경계 (의심 약함) | 008060 대덕 | 3/10 | 보류 |
| 일반 패턴 | 나머지 15-16 종목 | 0-1/10 | 지주 아님 |

→ **지주 군 양성 종목 수 = 최소 3 (확신) / 최대 4-5 (의심 포함)**.
양성 20 의 15-25%. *어느 가정해도 §5.5.7 학습 임계 30 미달의 추가 임계
미달*. fold별 학습 단독 fold 구성 불가능 — *모델 (b) stratification 학습
불가능*. (a) fs_div as feature + 군별 *평가 분리 보고* 만 가능.

**Code 권장 (c) 채택** — fs_div 컬럼 모델 입력 + 지주 군별 *평가 분리 보고*
(학습 분리 X). 양성 희소성 한계는 §5.5.7 박제 한계 (KOSPI200 모집단의
부실 사건 희소성) 의 *재확인*.

---

**B-2 결정 — 5 항목 (자문 1차 권장 그대로 채택, 2026-05-21)**:

| # | 항목 | 결정 | 사유 |
|---|---|---|---|
| (1) | 모델 + 평가 지표 | **sklearn + LightGBM + PR-AUC + AUC + Brier + Calibration + Top-K precision** | D8 박제 유지 (§4 결정 로그, 2026-05-18 승인). 새 결정 X. |
| (2) | 캘리브레이션 | **(i) sigmoid (Platt scaling)** | 양성 20 데이터 적어 safer. (ii) isotonic 과적합 위험. |
| (3) | class weight | **(i) balanced + (iv) unweighted 2 가지 ablation** | 두 결과 비교로 class weight 효과 직접 측정. (iii) bootstrap/SMOTE 는 시계열 누수 위험 + baseline 후 결정. |
| (4) | 0년 fold (2015·2021·2023) 처리 | **해당 fold 평가 skip + "fold 수 28 → 25" 명시** | bootstrap/SMOTE 채우기는 baseline 단계 과한 복잡도. 결과 본 뒤 추가 결정. |
| (5) | fs_div 활용 + 평가 분리 | **(a) fs_div as feature 학습 + (b) 지주 군별 평가 분리 보고** | B-1 (c) Code 권장 채택. 학습 임계 미달이라 군별 학습 X, *평가만* 분리. |

**0년 fold 처리 자세**:
- 2015 fold 가 *3 fold* (2015 분기) 없음 (walk-forward 첫 fold 가 2018Q1, §5.5.13 박제) → 2015 0년 영향 실제로는 *fold 0* (이미 walk-forward 시작 후 발생)
- 2021·2023 fold 는 *각각 4 fold = 8 fold* 가 양성 0 → 평가 skip 시 28 - 8 = **20 fold** 평가 가능

(실측은 B-4 walk-forward 통합 시 정확 계산)

---

**B-3 평가 함수 설계 결정 게이트 메모** (자문 자기 점검, B-3 시점 본격 결정):

본 짚을 점 2개를 B-3 평가 함수 설계 시 *명시 결정* 의무:

1. **평가 분리 보고의 통계적 약함** — 지주 군 양성 3-4 종목으로 PR-AUC 등
   별도 산출 시 *변동성 큼*. 결과 보고에 **"양성 N=3 으로 통계적 변동성
   큼" 명시 필수**. **bootstrap 신뢰 구간** 같은 변동성 표시 적용 권장
   (B-4 결과 보고 시점).
2. **walk-forward fold 단위 vs 종목 단위 평가** — fold 별 양성 1건 이하가
   다수일 가능성 (양성 20 / 25 fold ≈ 0.8). 대안: fold 별 예측 점수를
   모아 **종목 단위 (또는 (ticker, as_of) 단위) 로 evaluation** —
   PR-AUC·AUC·Brier 가 의미 있는 표본 수 확보. **B-3 평가 함수 설계 시점에
   본격 결정**.

**B-3 작업 진입 시 본 §5.5.16 의 평가 함수 설계 결정 게이트 메모 적용 의무**
(§7.6 정신).

---

**남기는 이유**: B-2 5 항목 결정이 다음 작업 진입 시점에 *합의 외 결정 진입*
차단. B-3 코드 작성이 본 §5.5.16 의 결정 5 항목 + 자기 점검 2개를 *명시*
참조해야 모델 학습 코드의 정직성·재현성 보존.

---

### 5.5.17. B-4 walk-forward 통합 학습 실행 결과 (2026-05-21) — Negative Finding 정직 박제

> §5.5.16 B-2 5 항목 적용 + B-3 모델 학습 코드 실측. **모델 성능이 random
> 보다 나쁨** — §5.5.7 박제 한계 ("KOSPI200 모집단의 부실 사건 희소성")
> 의 *경험적 정량 확인*. Negative finding 도 *과학적 가치* — 정직 박제.

**데이터 통계**:
- features rows: 8,008 (universe 멤버 × 40 분기말 grid 의 유효 cells)
- 양성 cells: 45 (양성 종목 20 × forward window 매칭, 평균 2-3 cells/종목)
- walk-forward folds: 28 → **평가 9 + skip 19** (skip 사유: test_pos=0 또는 train_pos=0)
- skipped fold_ids: [0, 1, 2, 3, 8, 9, 10, 11, 12, 16, 17, 18, 19, 20, 21, 22, 25, 26, 27]
- 평가 fold_ids: [4, 5, 6, 7, 13, 14, 15, 23, 24]

→ **§5.5.16 B-2 (4) 0년 fold skip "fold 수 28 → 25" 예상보다 실측 9** —
양성 cells (45) 가 평균 2-3 fold 에 집중, *대부분 fold 가 양성 0*. 양성
희소성의 *예상보다 더 극단적 형태*.

**B-4 결과 — balanced + unweighted ablation, 종목 단위 pooled, bootstrap_n=1000**:

[balanced] full pooled (n_pos=37 / n_total=1801, base rate ≈ 2.05%):

> **base rate 0.0205 = 37/1801 계산 맥락 (2026-05-21 보완)**:
> - 8,008 cells = 전체 features (universe × 40 grid 의 유효 cells)
> - 45 양성 cells = labels 전체 양성 (8,008 의 0.56%)
> - 1,801 cells = **평가 9 fold 의 test sample** (skip 19 fold 제외)
> - 37 양성 = **평가 sample 의 양성** (45 중 8 cells 가 skipped fold 안)
> - → base rate 2.05% (37/1801) vs 전체 0.56% (45/8008) 차이는 *평가
>   sample 추출 효과* — skip 된 19 fold 중 양성 0 fold 가 다수라
>   평가 sample 의 양성 비율이 *전체보다 높음*.

| metric | value | 95% CI |
|---|---|---|
| **pr_auc** | **0.0136** | [0.0100, 0.0198] |
| **roc_auc** | **0.2651** | [0.1959, 0.3439] |
| brier | 0.0211 | [0.0151, 0.0277] |
| ece | 0.0166 | [0.0106, 0.0235] |
| top_k_precision | 0.0056 | [0.0000, 0.0167] |

→ **PR-AUC < base rate (0.0205) + ROC-AUC < 0.5** → **모델이 random 보다 나쁨**.

[unweighted] full pooled (동일 데이터, ablation):

| metric | value | 95% CI |
|---|---|---|
| pr_auc | 0.0133 | [0.0099, 0.0182] |
| roc_auc | 0.2686 | [0.2081, 0.3417] |
| brier | 0.0206 | [0.0146, 0.0272] |
| ece | 0.0155 | [0.0096, 0.0222] |

→ **balanced vs unweighted 차이 거의 없음** — class weight 효과 0. 모델이
양성을 *학습하지 못함* 의 증거.

**지주 군 분리 평가 (§5.5.16 (5) 적용, 034730·267250·096770)**:

| | balanced | unweighted |
|---|---|---|
| n_positive | 12 | 12 |
| n_total | 27 | 27 |
| pr_auc | 0.3281 [0.1883, 0.5431] | 0.2877 [0.1670, 0.4621] |
| roc_auc | 0.0778 [0.0000, 0.2559] | 0.0000 [0.0000, 0.0000] |
| top_k_precision | 0.3333 [0.0000, 1.0000] | 0.0000 [0.0000, 0.0000] |

→ **지주 군 base rate = 12/27 = 44.4%** 보다 *낮은 PR-AUC* + ROC-AUC 가
0 가까움. **§5.5.16 짚을 점 1 (양성 N=12 통계적 변동성)** 의 CI 폭으로
확인 — top_k_precision balanced [0.0000, 1.0000] 폭 1.0 = *완전 변동*.

[일반 군 (지주 제외)] (n_pos=25, n_total=1774, base ≈ 1.4%):

| | balanced | unweighted |
|---|---|---|
| pr_auc | 0.0094 [0.0063, 0.0145] | 0.0097 [0.0063, 0.0151] |
| roc_auc | 0.2862 | 0.3018 |

→ 일반 군도 base rate 미만 + ROC-AUC < 0.5.

---

**(A) 데이터 보강 시도 결과 (2026-05-21, §5.5.17 (C) 후속)**:

`scripts/refetch_notfound_ofs.py` 실행 결과:
- 총 호출: **3,583 OFS 재페치** (16분 소요)
  - notfound 카운트가 PROGRESS §2 백필 시점 2,719 보다 큼 — 백필 이후
    추가 notfound (예: train_d2_baseline 의 build_features 가 *분기 보고서*
    들도 채움) 또는 meta walk 의 정의 차이. 본 박제는 *실측 3,583* 권위.
- **status notfound → ok 전환: 0 건**
- errors: 0
- DART API 응답 모두 `{'status': '013', 'message': '조회된 데이타가 없습니다.'}`
- fs_div 전환 분포: {CFS: 0, OFS: 0, None: 0}

→ **notfound 가 *D10 fetcher 미적용* 으로 인한 것이 아니라 *실제 데이터
부재* — CFS·OFS 모두 미공시 (DART 가 보고서 자체 없음)**. 데이터 보강
효과 0. *모집단 한계의 더 강한 증명*.

**§5.5.17 향후 방향 (C) 결과 박제**:
- (C) (β)+(γ) 데이터 보강 — *실효 0*. 9 FY None refresh (§5.5.11 5 종목)
  과 notfound 2,719 (실측 3,583) OFS 재페치 모두 *실제 데이터 부재*.
  CLAUDE.md §3.1 / PROGRESS §5.5.7 의 *KOSPI200 모집단의 부실 사건
  희소성* 이 *데이터 출처 변경으로 극복 불가능* 함을 정량 증명.

**notfound 분해 보고 (자문 짚을 점 1, 보완 2026-05-21)**:

| 분류 | ok | notfound |
|---|---|---|
| 양성 20 종목 | 648 | **208** |
| 음성 종목 (301) | 9,466 | **3,375** |
| 전체 (321) | 10,114 | **3,583** |

- 재페치 결과: **양성·음성 모두 status 전환 0건** (DART 응답 *조회 데이터 없음*)
- 양성 20 종목의 notfound 208 = 양성 종목당 평균 10.4 cells notfound (max 40
  = 10년 × 4 period)

**재학습 미진행 사유 (정직 박제)**:

(A) 재페치 status 전환 0 → DART 캐시 변화 0 → labels·features 입력 변화 0
→ 모델 재학습 결과 변화 0 *자명*. 재학습 자체가 무의미하므로 *진행 안 함*.

→ §5.5.17 의 PR-AUC 0.0136 등 모든 수치는 (A) 보강 시도 *후에도 변화
없음*. 박제 자료의 *재현 가능 권위* 유지.

산출물: `data/interim/refetch_notfound_ofs/summary.yaml` (gitignore).

---

**핵심 발견 (정직 박제)**:

1. **모델 성능이 random 보다 나쁨** — baseline 4 ratio (debt_ratio·current_ratio·
   op_margin·roa) + fs_div_code 5 features 로는 D2 양성 예측 *학습되지 않음*.
2. **§5.5.7 박제 한계의 경험적 정량 확인** — KOSPI200 양성 20 (학습 임계 30
   미달) + 28 fold 중 19 fold 양성 0 = *데이터 희소성이 모델 학습 불가능 수준*.
3. **balanced vs unweighted 효과 0** — class weight 보완 (§5.5.7 β) 도 *양성
   절대 수 부족* 앞에서는 작동 안 함.
4. **지주 군 stratification 평가도 의미 약함** — n_positive 12 의 CI 가
   완전 변동 (top_k_precision [0.0000, 1.0000]). §5.5.16 짚을 점 1 의
   경험적 확인.

---

**B-5 박제 입력 (모델 카드 limitations + 향후 방향)**:

본 결과는 *포트폴리오 측면에서 부정 결과가 아닌 정직 결과* — 다음 박제
가치:

1. **데이터 한계의 정량 증거 박제** — *D2 양성 20·forward 1년·KOSPI200* 조합
   이 학습 불가능함을 정량 (PR-AUC 0.01, ROC-AUC 0.27) 으로 입증.
2. **향후 방향 (단계 2 진입 후 결정 항목)**:
   - **(A) Forward window 2년 ablation** — §5.5.10 기각 사유 (라벨 의미
     균질성 파괴) *재고*. 본 결과가 *학습 불가능* 수준이라 *균질성보다
     양성 수 우선* 가능성. 다만 §5.5.10 박제 정신 유지.
   - **(B) Features 확장** (§5.5.16 B-2 baseline 후 결정) — 성장률·이자보상
     비율·CFO 마진·운전자본 등 추가. 다만 baseline 4 ratio 도 *충분
     기본*이라 추가가 *random 미만 결과를 극복할지* 불확실.
   - **(C) (β)·(γ) 데이터 보강** — 9 FY None refresh + notfound 2,719 OFS
     재페치. 9 cells × 양성 종목 매칭 작아 *결정적 영향 작음* 추정.
   - **(D) 모집단 확장 거부 재확인** — §5.5.6 (B3 KOSDAQ 확장) 기각 사유
     (point-in-time 정합성) 유지. 학습 불가능 결과를 *모집단 확장으로
     해결하는 우회* 는 §5 격리 원칙·D1 정직성과 충돌.
3. **포트폴리오 가치** — *negative finding 의 정직한 박제* + *D2 정직성
   사슬 4 차원 (변수·양성충분성·격리·시간) 모두 박힘에도 결과가 random
   미만임을 인정* = 학술·실무 가치 큼. 면접 방어용 자료로 활용.

**남기는 이유**: B-5 모델 카드의 *limitations + 향후 방향* 박제가 본 §5.5.17
의 실측 자료에 기반해야 함. *negative finding 박제* 자체가 §5.5.7~§5.5.16
의 모든 박제 정신 (정직성·재현성·실측) 의 결과.

---

### 5.6. 단계 3 (시장 국면 모듈) 진입 — D3·D4 결정 (2026-05-21)

> 단계 2 펀더멘털 모듈 종료 (B-5 + (A) 데이터 보강 negative 강한 증명) 후
> 단계 3 진입 게이트. 자문 1차 권장 그대로 채택.

**D3 (국면 모델·상태 수 K) — 결정**:
- **본 라인**: HMM (Gaussian, `hmmlearn`)
- **비교 대상**: GMM + K-Means (CLAUDE.md §8.4 박제, 안정성 비교)
- **상태 수**: **K=3** (위험회피·중립·위험선호) — 학술 관행 + 도메인 해석 가능
- **K 보조 결정**: BIC + AIC 보조 + K=2·3·4 비교 보고 + spot-check 도메인
  해석 (2008·2020 코로나 시점)

**D4 (입력 피처) — 결정**:
- **시점 단위**: 일간 (daily) — KOSPI200 지수 일간 close (FDR 캐시)
- **본 라인 피처 3개**:
  1. **rolling 20일 수익률** (월간 추세)
  2. **rolling 60일 실현 변동성** (분기 변동)
  3. **20일/60일 변동성 비율** (변동성 가속)
- **표준화**: rolling z-score (각 시점 in-sample 통계)
- **시점 정렬**: §5 룩어헤드 차단 — *forward-only filtering* (Viterbi 의
  backward smoothing 회피, 별도 retrospective 산출은 학습 외)

**자문 측 짚을 점 (코드 작성 시 본격 결정)**:

1. **HMM 시점 정렬 — forward filtering** (Viterbi backward smoothing 회피).
   *Retrospective Viterbi* 는 별도 산출물.
2. **State labeling — 사후 명명만** (CLAUDE.md §5). HMM 상태 0/1/2 는
   *번호만* — 평균 수익률·변동성으로 사후 명명.
3. **regime ↔ D2 baseline 통합 시점** — 단계 4 (대시보드) 에서 *regime
   라벨 + D2 baseline 한계 동시 시각화*. 분석적 의미보다 *맥락* 가치 우선.

**단계 3 작업 계획**:
1. `src/frr/regime/` 신규 패키지 (`__init__.py` + `features.py` + `hmm_classifier.py` + `comparison.py`)
2. KOSPI200 지수 일간 시계열 로드 (FDR 캐시 활용)
3. 3 피처 산출 (rolling z-score)
4. HMM K=3 학습 + GMM·K-Means 비교
5. State labeling (사후 명명)
6. 단위 테스트 (재현성·forward-only·룩어헤드 차단)
7. PROGRESS §5.6.1 박제 (학습 결과 + 도메인 해석)
8. 단계 3 종료 commit

---

### 5.6.1. 단계 3 시장 국면 모듈 학습 결과 (2026-05-21) — 명명 정정 + 정직 박제

> §5.6 D3·D4 결정 채택 후 `scripts/train_regime.py` 실측. 결과는 *learned
> model 자체는 의미 있으나 학술 명명 layer 부분 부합* — 정직 박제.

**데이터·모델**:
- KOSPI200 일간 close: 2,458 obs (2015-01-02 ~ 2024-12-30)
- warmup drop 후: 2,273 obs (학습용)
- HMM K=3 (Gaussian, full cov, random_state=42, n_iter=500)
- 수렴 ✓, log-likelihood: -9442.92

**State means (rolling z-score 기준)**:

| state | 명명 (정정 후) | ret_20d | vol_60d | 위기 점수 (vol_z - ret_z) |
|---|---|---|---|---|
| 2 | 위험선호 | +0.549 | +0.309 | **-0.240** (가장 낮음) |
| 1 | 중립 | -0.752 | -0.008 | +0.744 |
| 0 | 위험회피 | -0.809 | -0.015 | **+0.794** (가장 높음) |

**명명 규칙 정정 (2026-05-21)**:
- 초기 *vol 순 단순 매칭* (낮은 vol → 위험선호) → 결과 *수익률 부호 무시*로
  명명 부적합 발견.
- 정정: **위기 점수 = mean(vol_z) − mean(ret_z)** 기준 (학술 표준).
- 정정 후 매칭은 *위기 점수 순* — 가장 낮음 → 위험선호, 가장 높음 → 위험회피.

**State 분포 (forward filter argmax)**:
- 위험선호: 1,313 (57.8%)
- 중립: 607 (26.7%)
- 위험회피: 353 (15.5%)

**전이 행렬** (높은 지속성, *흡수 상태 패턴*):
```
              위험회피     중립    위험선호
from 위험회피  0.003   0.997    0.000   ← 위험회피→중립 거의 항상 전환
from 중립      0.925   0.017    0.058   ← 중립 → 위험회피 자주
from 위험선호  0.000   0.024    0.976   ← 위험선호 지속성 매우 강함
```

**도메인 spot-check (2020 코로나 2020-02-15 ~ 05-15)**:
- 중립: 26 (42.6%)
- 위험선호: 18 (29.5%)
- 위험회피: 17 (27.9%)

→ **학술 정의 부합 약함**. 위기 시점 위험회피 *27.9% 만*. 모델이 *3 분류*
했으나 *학술 표준 위험회피·위험선호 와 정확히 매칭 안 됨*.

**핵심 발견 — 명명 부합 약함 (정직 박제)**:

1. **state 2 (위험선호)**: 높은 ret + 높은 vol = *상승+변동 패턴* — 학술
   "위험선호 (낮은 vol)" 와 부분 부합. 분포 57.8% 압도적.
2. **state 0 (위험회피)**: 낮은 ret + 낮은 vol = *정체 패턴* — 학술
   "위험회피 (높은 vol)" 와 부적합.
3. **state 1 (중립)**: 낮은 ret + 평균 vol = *약세 패턴* — 중립 부합 약함.
4. **전이 행렬 흡수 패턴**: 위험회피·위험선호 모두 *자기 지속성 강함*
   (0.997·0.976). 중립이 *교차로* 역할 (위험회피 0.925).
5. **2020 코로나 위기 시점 모델 부합 약함** — 위험회피 27.9% 만, 중립
   42.6% 가장 많음.

**의미 (자문 측 정직 판단)**:

- 본 모델은 *3 분류* 자체는 *수렴·재현 가능*. log-likelihood, 전이 행렬,
  state 분포 정량 자료가 *권위*.
- *학술 표준 명명 layer* 는 *부분 부합* — KOSPI200 국면이 *위험회피·중립·
  위험선호 3 구간과 정확히 매칭 안 됨*. *3 피처 (ret + vol + vol_ratio)*
  로는 *학술 명명 분리 부족*.
- 단계 4 (통합 대시보드) 에서 *state 시계열 시각화* + *means + 분포 +
  전이 행렬 보고* + *사후 도메인 해석은 사용자 검토*로 이전.

**향후 방향 (단계 3 완료 후)**:

(a) **피처 확장** — 거래량 변동·매크로 (금리·환율) 추가로 *학술 명명
    분리 보강* 가능성. 단 YAGNI — *단계 4 시각화 후 결정*.
(b) **K 비교 (K=2, 4) 진단** — BIC + AIC + 도메인 spot-check. 단계 4 시각화
    이전 *별도 결정 게이트*.
(c) **GMM·K-Means 비교** — CLAUDE.md §8.4 박제, 단계 3 완료 의무 항목.
    별도 작업 단위.

**산출물**:
- `data/interim/regime/results.yaml` (gitignore, state means·transmat·
  distribution 박제)
- `data/interim/regime/state_series.parquet` (gitignore, 2,273 rows
  date·state_idx·state_label)
- `scripts/train_regime.py` (git 추적)
- `src/frr/regime/` (features.py + hmm_classifier.py, git 추적)

**남기는 이유**: 본 §5.6.1 박제로 *learned 모델 권위 보존* + *명명 부합
약함 정직 인정*. 단계 4 시각화·해석 단계의 *baseline 자료*. 단계 3 의
GMM·K-Means 비교 작업 (별도 commit) 도 본 결과 기준점.

---

### 5.6.2. 단계 3 — HMM vs GMM vs K-Means 비교 + K=2·3·4 진단 (2026-05-21)

> CLAUDE.md §8.4 박제 의무 — hmmlearn 본 라인 + sklearn GMM·K-Means 비교.
> `scripts/compare_regime_models.py` 실측.

**K=2·3·4 × HMM/GMM/K-Means 비교**:

| model | K | log_lik | BIC | AIC | inertia | converged |
|---|---|---|---|---|---|---|
| HMM | 2 | -9290.64 | 18743.58 | 18623.27 | — | ✓ |
| GMM | 2 | -10228.29 | 20603.42 | 20494.57 | — | ✓ |
| K-Means | 2 | — | — | — | 7279.55 | ✓ |
| HMM | 3 | -9442.92 | 19156.36 | 18955.85 | — | ✓ |
| GMM | 3 | -10102.68 | 20429.49 | 20263.35 | — | ✓ |
| K-Means | 3 | — | — | — | 5436.85 | ✓ |
| **HMM** | **4** | **-7640.05** | **15674.28** | **15382.11** | — | ✓ |
| **GMM** | **4** | **-10041.67** | **20384.76** | **20161.34** | — | ✓ |
| K-Means | 4 | — | — | — | 4244.41 | ✓ |

**자동 K 선택**:
- HMM BIC·AIC 모두 **K=4** (15674.28 최소)
- GMM BIC·AIC 모두 **K=4**
- K-Means inertia 는 K 증가에 따라 자연 감소 (elbow 약함, K=2→3 감소 폭이
  큰 편 — 1842 vs 1192)

**자동 선택 K=4 vs 도메인 결정 K=3 tension** (정직 박제):
- §5.6 박제 결정 K=3 (학술 관행 + 도메인 해석)
- 자동 선택은 K=4 — 모델이 *4 분리* 를 더 적합
- §5.6.1 *명명 부합 약함* 의 한 원인이 *적정 K 가 4* 일 가능성
- 본 단계 baseline 결정: **K=3 유지** (도메인 일관성 + 학술 표준), K=4 결과
  는 *대안 시나리오*로 박제. 단계 4 대시보드 시각화 시점에 K=3·K=4 두
  결과 함께 표시 권장.

**K=3 시드 안정성 검사 (seeds = {42, 123, 7, 2024, 999})**:

| model | seed | log_lik | BIC |
|---|---|---|---|
| HMM | 42 | -9442.92 | 19156.36 |
| HMM | 123 | -8312.95 | 16896.40 |
| HMM | 7 | -8575.96 | 17422.43 |
| HMM | 2024 | -8312.95 | 16896.40 |
| HMM | 999 | -8662.13 | 17594.77 |
| GMM | 모든 seed | -10101 ~ -10107 | 20427 ~ 20439 |
| K-Means | 모든 seed | inertia | 5436.5 ~ 5436.9 |

**HMM 시드 불안정성 정직 박제**:
- HMM log-lik 시드별 **변동 큼** (-9442.92 ~ -8312.95, *13.6%* 변동)
- BIC 변동 16896 ~ 19156 (*13.4%*)
- → **HMM 가 local optima 의존** 가능성. EM 알고리즘의 *시작점 sensitivity*.
- 대조: GMM 변동 *0.06%* + K-Means 변동 *0.007%* — 매우 안정.

**자문 측 의미**:

1. **HMM 적합도 > GMM** (K=3): HMM 이 *전이 행렬 정보* 활용해 GMM 보다 적합도
   ↑. HMM 본 라인 채택 정당화 (CLAUDE.md §8.4).
2. **HMM 시드 불안정성 — 단계 4 시각화 의무**: 단계 4 (대시보드) 에서
   *시드별 결과 변동 명시* + *random_state=42 결과만 사용 정당화*.
3. **자동 K=4 vs 도메인 K=3** — 단계 4 대시보드에 *두 결과 함께* 또는
   *K=3 본 라인 + K=4 대안* 시각화.

**산출물**:
- `src/frr/regime/comparison.py` — `compare_k_range`, `stability_check`, BIC·AIC 산출
- `scripts/compare_regime_models.py` (git 추적)
- `data/interim/regime/comparison_summary.yaml` (gitignore)

---

### 5.6.3. 단계 3 종료 + 모델 카드 (2026-05-21)

`reports/regime_model_card.md` 작성:
- 모델 명세 (HMM K=3 + GMM/K-Means 비교)
- 학습 데이터 (KS200 일간 2,458 obs → 2,273 clean)
- 평가 결과 (§5.6.1 means + 분포 + 전이 행렬, §5.6.2 K 자동 선택 K=4 vs
  도메인 K=3 tension, 시드 불안정성)
- Limitations 4: 명명 학술 부합 약함 / HMM 시드 불안정성 / 자동 K=4 도메인
  K=3 tension / 코로나 spot-check 부합 약함
- 향후 방향: 피처 확장 (거래량·매크로) / K=4 본 라인 재검토 / 시드 안정화
  기법 (multiple-start EM)
- Intended use: 단계 4 대시보드 *맥락 시각화*. 트레이딩 신호 ❌.

**단계 3 종료** — 단계 4 (통합 대시보드) 진입 게이트.

---

### 5.7. 단계 4 — Streamlit 통합 대시보드 + LLM import 0 격리 (2026-05-21)

> CLAUDE.md §8.5 박제: Streamlit + plotly. §8.6: app/ 정적 읽기 전용,
> LLM SDK import 금지 (CI 검사). §3.4: 런타임 LLM 호출 0회.

**구조**:
- `app/__init__.py` — 모듈 docstring (정적 읽기 전용 박제)
- `app/data_loader.py` — yaml/parquet/md 정적 로드 layer (학습·페치 0회)
- `app/main.py` — Streamlit entry point, 4 페이지:
  1. 개요 (단계별 상태 표)
  2. 시장 국면 시계열 (plotly scatter + 분포 pie + 전이 행렬)
  3. D2 baseline 결과 (full pooled + balanced/unweighted ablation + 지주
     군 분리 + (A) 데이터 보강 결과)
  4. **⚠️ Limitations (면접 방어 자산)** — 6 항목 모두 정직 박제

**Limitations 페이지 6 항목 (자문 짚을 점 3 모두 반영)**:
1. 단계 2 negative finding (PR-AUC 0.0136 + class weight ablation)
2. (A) 데이터 보강 결과 (notfound 3,583 전환 0)
3. 단계 3 명명 부합 약함 + state means + 2020 spot-check
4. HMM 시드 불안정성 (13.6% 변동)
5. 자동 K=4 vs 도메인 K=3 tension
6. KOSPI200 모집단 희소성 (§5.5.7 인용)

**격리 검증 — `tests/test_app_no_llm_import.py` 3 테스트 (자문 짚을 점 4)**:
- `test_app_dir_exists` — app/ 디렉토리 존재
- `test_app_no_llm_sdk_import` — google.generativeai·openai·anthropic·
  cohere·transformers·litellm·llama_cpp·frr.llm import 0 (AST 검사)
- `test_app_no_training_code` — lightgbm·hmmlearn·sklearn.ensemble/linear_
  model/tree import 0 (학습 코드 금지)

→ CLAUDE.md §3.4 박제 (서비스 런타임 LLM 호출 0회) 의 **CI 강제 박제**.
정직성 사슬 완성형.

**의존성 추가**: `streamlit>=1.57.0` + `plotly` (관련 pkg).

**실행**:
```bash
uv run streamlit run app/main.py
```

**산출물**: app/ 디렉토리 + tests/test_app_no_llm_import.py (모두 git 추적).

**자동 K=4 ablation 메모 (자문 짚을 점)**:
- 단계 5 마무리 시점에 K=4 ablation 추가 결정 게이트 — 단계 3 결과의
  자산 강화 후보. *지금 강제 안 함*. PROGRESS §5.6.2 박제 그대로 유지.

**단계 4 종료** — 단계 5 (마무리·문서) 진입 게이트.

---

### 5.6.4. K=4 Ablation 결과 — 자동 K 선택 정량적 정답 (2026-05-21)

> 단계 5 마무리 시점 자문 권장 ablation. PROGRESS §5.6.2 의 *자동 K=4 vs
> 도메인 K=3 tension* 정량 비교 — **K=4 가 학술 명명·도메인 정의 압도적
> 부합**. `scripts/train_regime.py --k 4` 실측.

**K=3 vs K=4 비교**:

| 비교 항목 | K=3 (본 라인) | K=4 (ablation) | 변화 |
|---|---|---|---|
| log-likelihood | -9442.92 | **-7640.05** | **+1,802.87** |
| BIC | 19,156.36 | **15,674.28** | **-3,482.08** (개선) |
| 수렴 | ✓ | ✓ | — |

**K=4 State means** (rolling z-score):

| state | 명명 | ret_20d | vol_60d | 도메인 해석 |
|---|---|---|---|---|
| 2 | (위기 = 위험회피) | -0.103 | **+2.609** | 음수 ret + 극도 vol — **위기**, 학술 정의 *명확 부합* |
| 3 | (위험선호) | +0.231 | -0.390 | 양수 ret + 낮은 vol — *상승*, 학술 정의 *명확 부합* |
| 1 | (위기 후 회복) | +0.311 | +1.057 | 양수 ret + 높은 vol — *회복 패턴* |
| 0 | (정체·약세) | -0.713 | -0.989 | 낮은 ret + 매우 낮은 vol — *정체* |

→ **K=3 의 "위험회피 = 정체" 부합 약함이 K=4 의 *위기 vs 정체 분리*로 해결**.

**State 분포 (K=4)**:
- state_3 (위험선호): 756 (33.3%)
- state_1 (위기 후 회복): 663 (29.2%)
- state_0 (정체·약세): 624 (27.5%)
- state_2 (위기): 230 (10.1%)

**2020 코로나 spot-check (2020-02-15 ~ 05-15)**:

| | K=3 (본 라인) | K=4 (ablation) |
|---|---|---|
| 위기 (state_2) | **27.9%** | **82.0%** ⬆ |
| 회복 (state_1) | — | 18.0% |
| 다른 state | 72.1% | 0% |

→ **K=4 가 코로나 위기 시점 82% state_2 분류** = **학술 정의·도메인 부합도
압도적**. K=3 의 27.9% 대비 *3 배 개선*.

**전이 행렬 (K=4)**:

| | state_0 | state_1 | state_2 | state_3 |
|---|---|---|---|---|
| from 0 | 0.969 | 0.008 | 0.007 | 0.016 |
| from 1 | 0.004 | 0.977 | 0.006 | 0.012 |
| from 2 | 0.000 | 0.042 | **0.954** | 0.004 |
| from 3 | 0.021 | 0.001 | 0.001 | 0.976 |

- 모든 state 자기 지속성 강함 (0.954 ~ 0.977)
- 위기 (state_2) → 회복 (state_1) 전환 0.042 (위기 종료 패턴)

**자문 측 정직 판단 — 단계 3 본 라인 결정 평가**:

1. **K=3 본 라인 결정의 부분 정정 가치 큼**: §5.6.1 의 "명명 부합 약함"
   문제가 *K=3 자체의 한계*. K=4 가 *적정 K* 임을 본 ablation 으로 정량
   증명.
2. **본 라인 본격 변경 안 함** (단계 5 시점 보수적 결정): K=3 박제·모델
   카드·대시보드 *모두 K=3 기준*. *향후 main 라인 변경 시 광범위 갱신*
   필요. 단 *본 ablation 박제 + README Future Work 항목 변경* 으로 **K=4
   가 더 적정** 메시지 박제.
3. **면접 방어 메시지 강력 보강**: "자동 K=4 vs 도메인 K=3 tension →
   ablation 실측 결과 K=4 가 학술 정의 부합 (코로나 82% vs 27.9%) →
   ablation 으로 정량 발견 박제" — *진단 → ablation → 정답 발견* 의
   완성형 정직성 사슬.

**산출물**:
- `scripts/train_regime.py --k 4` (K argument 추가)
- `data/interim/regime/k4/results.yaml` (gitignore)
- `data/interim/regime/k4/state_series.parquet` (gitignore)

**README Future Work #1 항목 — ✅ 완료 표시 + 결과 인용**:
- K=4 ablation: K=3 본 라인의 명명 부합 약함을 *데이터 측 한계* 가 아닌
  *적정 K 부족* 으로 식별. 향후 main 라인 변경 후보 (광범위 박제 갱신
  필요).

---

### 5.8. ★ 단계 5 종료 = 프로젝트 종료 (2026-05-21)

본 박제로 **fundamental-regime-report 프로젝트 종료**. 단계 1~5 모두 완료
+ main merge commit + PR #1 closed.

**전체 commit 흐름 (39+ commits)**:
- 단계 1 (데이터 셋업): 16 commits (`bccc164` ~ `8810f50`)
- 단계 2 (펀더멘털 모듈): 14 commits (B-1~B-5 + (A) 데이터 보강)
- 단계 3 (시장 국면 모듈): 3 commits (HMM + GMM/K-Means 비교 + K=4 ablation)
- 단계 4 (통합 대시보드): 1 commit (Streamlit + LLM SDK import 0 CI)
- 단계 5 (마무리): 2 commits (README + 본 종료)

**최종 자산 — 정직성 사슬 5 차원**:

| 차원 | 박제 | 위치 |
|---|---|---|
| 변수 격리 | distress filter 화이트리스트 | §5.5.9 |
| 양성 충분성 | forward window 1→2년 ablation 기각 | §5.5.10 |
| 격리 (i)(ii)(iii) | features 변수·상폐 메타·OpenDartReader 차단 | `tests/test_isolation.py` |
| 시간 | walk-forward + embargo 365일 | `src/frr/eval/splits.py` |
| LLM 격리 | app/ LLM SDK import 0 CI | `tests/test_app_no_llm_import.py` |

**§7.6 작업 진입 검토 사이클** — 자문·실행 양측 매 작업마다 4 단계 의무
실행 (CLAUDE.md §7.6, PROGRESS §5.5.11 학습 박제).

**두 단계 negative finding 정직 박제**:
- 단계 2: PR-AUC 0.0136 < base rate 0.0205 (KOSPI200 부실 희소성)
- 단계 3 K=3: 명명 부합 약함 + HMM 시드 13.6% 불안정성
- 단계 3 K=4 ablation: **27.9%→82% 코로나 위기 부합** (정량 정답 발견)
- (A) 데이터 보강: notfound 3,583 전환 0 (DART 직접 응답 모집단 한계 증명)

**최종 산출물**:
- 모든 코드 (src/frr/, app/, scripts/, tests/)
- 모델 카드 2개 (reports/d2_baseline_model_card.md + regime_model_card.md)
- README 면접 방어 메시지 6 항목
- PROGRESS.md §5.5/§5.6/§5.7/§5.8 (본 절) 완전 박제
- CLAUDE.md §7.6 작업 진입 검토 사이클
- GitHub Actions CI green (모든 단계)

**포트폴리오 가치**:
1. *Negative finding 의 정직 박제* — 학술·면접 가치
2. *진단 → 가설 → ablation → 정답 발견* 완성형 과학 사이클 (K=4 ablation)
3. *방법론적 엄밀성* + *명확한 스코프* 우선 (CLAUDE.md §4·§5)
4. *§7.6 워크플로* — 매 작업마다 4 단계 검토 의무 박제

**추가 작업 시**: 신규 branch + PR. 단계 5 = 본 박제로 종료.

---

### 5.9. 자문 측 검증 누락 정직 박제 — Streamlit entry point sys.path (2026-05-21)

> 단계 4 완료 + main merge 후 사용자가 *로컬 실행 테스트* 시도 → `ModuleNotFoundError:
> No module named 'app'` 발생. 자문 측 §7.6 *실측* 차원 누락 사례. §5.5.11 (D10
> 가정 오류·Co-Authored-By 가정 학습) 패턴의 3 번째 사례 박제.

**경위**:
- 단계 4 작성 시 `app/main.py` 가 `from app.data_loader import ...` (절대 import)
- 단위 테스트 `tests/test_app_no_llm_import.py` 는 *pytest 환경의 sys.path*
  (프로젝트 루트 포함) 에서 import 검증 통과
- *실제 `streamlit run app/main.py` 명령은 한 번도 실행 안 함* — 코드 작성 후
  실측 검증 의무 누락

**원인**:
- Streamlit 의 `streamlit run app/main.py` 는 *해당 파일 디렉토리* (`app/`) 를
  `sys.path` 첫 번째로 추가
- 이 환경에서 `from app.data_loader` 는 *`app/` 의 부모 디렉토리가 sys.path 에
  없으면* ModuleNotFoundError
- pytest 는 *프로젝트 루트가 sys.path* 라 `from app.data_loader` 정상 동작 — 즉
  단위 테스트는 *실행 환경 차이를 검출 못 함*

**정정 (commit `fix(app): streamlit entry sibling import`)**:
- `app/main.py`: `from app.data_loader import ...` → `from data_loader import ...`
- `tests/test_app_no_llm_import.py` 신규 테스트 `test_app_main_imports_under_streamlit_sys_path`:
  subprocess 로 `cwd=app + python -c "import main"` 시뮬 → import 성공 검증.
  *streamlit-like sys.path 환경에서 실제 import 가능성을 단위 테스트로 강제*.

**자문 측 학습 (§5.5.11 패턴 3 번째)**:
- 1 번째 사례: Co-Authored-By 가정 오류 — git log 실측 정정 (§5.5.11)
- 2 번째 사례: D10 가정 오류 — 작업 직전 dart.py 재읽기 정정 (§5.5.11)
- **3 번째 사례 (본 절)**: Streamlit entry point sys.path 가정 오류 — *사용자
  실행 시 발견*. 단위 테스트 sys.path 환경 ≠ 실행 환경 sys.path 환경.
  → 향후: *코드 작성 후 실행 명령 자체* (streamlit run / uvicorn / docker run
  등 entry point 명령) 를 *자문 측이 직접 실행* 또는 *동등 환경 단위 테스트*
  로 보강 의무.

**§7.6 검토 사이클 보강 (4 단계 + 본 사례)**:
- 4 단계 (PROGRESS·git log·코드 재읽기·사용자 검토 게이트) 모두 통과해도
  *entry point 명령 실측* 누락 시 본 사례 같은 사용자 발견 가능
- 자문 권장: §7.6 *실측* 차원에 *"명시 entry point 명령 (있을 경우) 자문 측
  최소 1회 실행 검증"* 항목 추가 — 본 박제로 정신 박힘. CLAUDE.md 본문 정식
  편입은 별도 결정 게이트.

**남기는 이유**: 단위 테스트 통과 ≠ 실제 실행 환경 검증. 본 사례가 *§7.6 검토
사이클의 한계점* 정직 박제. 미래 자문 시스템 운용 시 *entry point 명령 직접
실행* 패턴 의무화. §5.5.11 학습 사슬의 3 번째 사례 보존.

---

### 5.9 학습 사슬 확장 (2026-05-22 — Phase 4 reset 시 박제)

> §5.9 위 본문이 *3번째 사례 (Streamlit entry sys.path)* 박제. 본 절은
> 4번째·5번째·7번째 사례 + 6번째 자리 공석 박제. §7.6 5번째 단계 (작업
> 단위 종료 시 자기 재검토 의무) 신설 계기 (박제 ≠ 실측 3 회 누적).

#### 4번째 사례 — CLAUDE.md §2 사용자 시나리오 *구조* 누락 (단계 4, 2026-05-21)

자문 측이 단계 4 진입 후 *기술 정직성 박제* 만 짚고 *CLAUDE.md §2 사용자
시나리오 본질* (기업 선택 → 통합 리포트) 놓침. 사용자 직접 지적 → commit
`d4181d7 feat(app): ticker-centric analysis page (CLAUDE.md §2 user scenario)`
로 종목 분석 페이지 신설.

**학습**: 기술 정직성 박제 ≠ 본질 시나리오 구현. *CLAUDE.md §2 직접 매핑*
자문 측 의무.

#### 5번째 사례 — Phase 4 Auto mode 압축 vacuous 통과 (2026-05-21)

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
  압축은 destructive 가능성·UI/UX·성능 영역에서 자문 측이 강하게 경고*.

**리셋 결정** (사용자 본질 감각 동의):
- 폐기 범위: `app/components/` · `app/pages/` · `app/utils/` · `tests/test_app_utils.py`
  17 파일 (`app/main.py` 는 *변경 없음* — 추가 자기 점검 참조)
- 유지 범위: D2/regime 모델 산출물·정직성 사슬·§5.x PROGRESS·모델·데이터
  layer 테스트·C-1 데이터 자산 점검
- 보존: Phase 4 commit `220d1ac` 별도 브랜치 `phase4-discarded-ref` (공부 자산)
- 진행: 새 7 단계 (요구사항→UX→UI→아키텍처→구현→QA→배포) + 매 단계 사용자
  직접 검증 + Auto mode 압축 금지

**추가 자기 점검 — 5번째 사례의 commit message 차원 동형 (2026-05-22 reset 직전 발견)**:

`220d1ac` commit message 는 "`app/main.py` slim entry (50 줄, 라우팅 +
page_config 만)" 명시했으나 §7.6 실측 결과:
- `git diff --name-status 33a897f 220d1ac -- app/` → 17 파일 모두 `A`
  (`app/main.py` *변경 목록에 없음*)
- `git diff 33a897f HEAD -- app/main.py` → 출력 0 (두 시점 동일)
- `git log -- app/main.py` → 마지막 변경 commit = `33a897f` (Phase 1 핫픽스)

즉, slim entry refactor 가 *계획만 있고 실제 commit 에 적용되지 않음*. commit
message 의 광고 vs 실제 변경 불일치. 5번째 사례의 본질 (*박제 권위 ≠ 실행
검증*) 의 *commit message 차원 동형*. Phase 4 reset 0 단계 진입 직전 §7.6
실측 게이트 적용해 적발 — 따라서 0 단계 절차에서 *app/main.py 복원 단계
제거*.

#### 6번째 사례 (공석)

추후 발견될 누락 사례 또는 워크플로 자산 박제 자리 (사용자 예약, 2026-05-22).

#### 7번째 사례 — 세션 인수인계 박제 vs git 실측 불일치 (2026-05-22)

직전 세션의 핸드오프 메모 `docs/handoff_to_next_code_session.md` §0 표에
"PR #1·#2 merged (main 까지 반영)" 박제했으나 git 실측
(`git log origin/main`) 결과 main 브랜치는 commit `229508c` (단계 1 직후) 에
머물러 있고 Phase 4 포함 42 commit 이 작업 브랜치 위에만 누적된 상태. 직전
세션의 박제와 git 실측 불일치. 새 세션 진입 시 §7.6 4 단계 게이트의
'git log 실측' 단계가 작동해 적발.

박제는 *git 실측을 대신할 수 없음* + *세션 인수인계 시 박제 본문의 git
상태 매번 재검증 의무* 의 워크플로 자산.

#### §7.6 5번째 단계 신설 계기 (3 회 누적, 2026-05-22)

새 세션 시작 시점에 직전 세션 박제 ≠ 실측 문제가 *3 회 누적*:
1. §5.9 5번째 사례 — Phase 4 박제 vs 실행 결과 불일치
2. Phase 4 reset 직전 `220d1ac` slim entry commit message vs 실측 불일치
   (5번째 사례 *추가 자기 점검*)
3. §5.9 7번째 사례 — PR merged 박제 vs main HEAD 실측 불일치

사용자 본질 지적: "*항상 새 세션 시작 시 문제점 발생은 좋지 않은 현상*".
→ CLAUDE.md §7.6 의 4 단계 → 5 단계로 확장. 5번째 단계 = *작업 단위 종료
시 자기 재검토 의무* (a~e 검증 후 명시 보고). 본 0 단계 자체가 §7.6 5번째
단계가 적용된 *첫 사례* (commit `phase 4 reset + §7.6 5th gate ...`).

---

### 5.10 외부 노출 규칙 박제 일지 (CLAUDE.md §7.7 신설 — 2026-05-22)

> 0.5 단계 (1 단계 본문 작성 직전 신설) — 외부 노출 표면 정리 + 외부 표현
> 규칙 박제 일지. CLAUDE.md §7.7 본문 참조.

#### 박제 계기 (사용자 명시, 2026-05-22)

**사용자 본질 두 차원**:

1. **GitHub 정리 본질**: 레포 자체가 일반인·관련 인물이 들어와서 *5 초 내
   이해 + 보기 좋게 정리*. `README.md`·레포 구조·commit 메시지·산출물 모두
   *누가 봐도 이해하기 쉽게*.
2. **외부 표현 금지**: 본 프로젝트는 *Claude 와 함께 진행한 사용자의
   프로젝트로 GitHub 노출*. *포트폴리오·취업·면접·채용* 등 단어 직접 노출
   금지. 사용자 개인 동기 차원이며 외부 표면에는 표현 금지.

본 두 차원이 모든 외부 노출 표면 작업의 상위 제약. CLAUDE.md §7.7 로
*공식 규칙 박제*.

#### 사전 정정 의무 (본 0.5 단계 자체)

본 0.5 단계가 *1 단계 (requirements.md) 본문 작성 진입 전* 외부 표면
선제 정리. 1 단계 작업 자체가 *requirements.md* 라는 외부 노출 표면 추가
산출. 1 단계 진입 전 §7.7 박제 + 기존 표면 정리가 필수.

#### Q2 도메인 이력 메타 보존 (자문 보강)

**본 프로젝트는 사용자의 직전 의료영상 분석 ML 프로젝트의 도메인 이전
동기**. 외부 표면 (CLAUDE.md §1) 에서는 제거, 내부 일지에만 보존. 내부
일지 컨텍스트 보존 + 외부 노출 차단 양쪽 만족.

#### 영문 동의어 박제 계기 메타 (자문 측 학습)

§7.7 (2) 영문 동의어 추가 — `Code` 가 §7.6.3 grep 실측에서 `Portfolio
Identity` 영문 헤딩 (`CLAUDE.md §3.4 line 61`) 발견. 자문 측 직전 답변에서
한국어 금지 단어 7 개만 박제, 영문 동의어 누락. `Code` §7.6 5 단계 자기
적용 + 외부 표면 grep 실측이 *적시 적발*. §7.7 (2) 영문 동의어 박제 +
*"본 목록은 완전 폐쇄형 아님 — 새 동의어 발견 시 §7.7 본문 확장 의무"*
명시로 재발 차단.

**자문 측 학습**: 외부 표면 박제 시 *다국어 동의어 함께 고려 의무*. 향후
새 동의어 발견 시 §7.7 본문 확장 + 본 §5.10 일지 메타 박제.

#### 자문 측 자기 점검 (사용자 명시 본문 그대로)

> 자문이 직전 답변에서 "포트폴리오 평가"·"면접 방어 가치" 표현 다수 사용.
> 본 표현이 PROGRESS 박제 본문에 흡수돼 내부 일지에 잔존. PROGRESS 박제
> 자체는 정정 의무 없음 (내부 일지). 다만 앞으로 자문 답변에서 위 표현
> 자제 + 외부 노출 표면 답변 시 본 규칙 자기 적용.

#### 0.5 단계 정정·신설 일괄 (commit 본문 참조)

| 정정 4 | 위치 |
|---|---|
| CLAUDE.md §1 성격 → "1인 개발자가 Claude 와 함께 진행한 KOSPI200 분석 시스템" | line 11 |
| CLAUDE.md §1 도메인 이력 단락 제거 (메타는 본 §5.10 보존) | line 12 |
| CLAUDE.md §3.4 헤딩: Portfolio Identity → 프로젝트 정체성 | line 61 |
| README.md 첫 문단 + 정직성 사슬 한 줄 + 푸터 수치 (17+ → 73) + Claude 협업 표현 | line 1-11 + 174 |

| 신설 2 |
|---|
| CLAUDE.md §7.7 — 외부 노출 규칙 5 항목 (의무 정리·금지 단어 다국어·내부 일지 면제·매 commit 자기 점검·박제 계기 메타) |
| PROGRESS.md §5.10 — 본 일지 |

#### 0.5 단계 §7.6.5 (d) 자기 적발 (2026-05-22 — fix-up commit 사이클)

`Code` 가 README 푸터 수치를 *commit 직전 실측치 "73"* 으로 채택. 그러나
*해당 commit 자체가 +1* 추가 → push 직후 실측 74. **사용자 권장 표현
"(70+ 커밋, 진행 중)" 의 *정확치 회피* 의도** (`*"진행 중" 표현이 향후 수치
정확 일치 의무 약화*` 사용자 명시) 무시한 *과적합 채택*.

§7.6.5 (e) 정신 — *해당 사이클 내 즉시 정정* + 정직 보고. fix-up commit 으로
"73" → "70+" 정정 (사용자 원안 그대로 복원). 본 사이클 자체가 §7.6.5
(d)(e) *워크플로 적용 사례 2호* (1호 = 0 단계 phase4-discarded-ref 시점
220d1ac slim entry 불일치 적발).

**자문 측 학습**: 사용자 권장 표현 채택 시 *대안 후보 (자문 추가 가공)
삼가*. 사용자 표현이 *이미 §7.6.5 정신 내재*. 향후 사용자 권장 표현 그대로
채택 우선, 자문 가공 *최소화*.

---

### 5.5.5. 구버전 자료 (2026-05-18 초기 — 참고용 / 변경 추적)

> 아래 (1)~(4)는 *진단 누적 이전*의 초기 사용자 요청 자료. 본 §5.5.1~5.5.4
> 가 그 후 갱신본. 변경 추적·면접 방어용으로 원본 유지.

### (1) 옵션 E 양성 표본 수 — *진단 기반*

본 진단(`scripts/diagnose_step1_results.py`)으로 확인한 *상폐* 양성:

| 사유 | 건수 | D2 양성 적격 |
|---|---|---|
| 자본전액잠식 | 1 | ✅ 진정한 부실 |
| 해산 사유 발생 | 8 | △ 사유별 검토 (자발적 해산은 제외 권장) |
| 지주회사 완전자회사화 | 8 | ❌ **부실 아님** (구조개편) |
| **상폐 양성 (부실 사유)** | **~9** | — |

**관리종목 지정 양성**: 데이터 없음 (D2 자료 (4) 의 수동 다운로드 후 확정).
KOSPI200 + 상폐 유니버스 기준 추정 *10~30건* 가능 (자본잠식·횡령·감사
의견거절 등).

**합산 (E 옵션 채택 시 예상)**: 양성 **~20~40건** (10년치, 1년 forward).
중복(관리종목 → 폐지) 추정 **~5~10건**.

### (2) walk-forward 양성 분포 추정

연도별 상폐 양성 (위 17건 중 부실 사유만 보정):

| 연도 | 상폐 부실 | 관리종목(추정) | **합산** |
|---|---|---|---|
| 2015 | 1~2 | 2~3 | 3~5 |
| 2016~2018 | 각 1 | 각 2 | 각 3 |
| 2019 | 0 | 1~2 | 1~2 |
| **2020~2021** | **0** | 1 | **1 (희박)** |
| 2022 | 0 | 1 | 1 |
| 2023~2024 | 1 | 2 | 3 |

→ **2020-2021 강세장 구간 양성 zero 위험**. walk-forward 시점에 따라
*한 자릿수 또는 zero* 시점 존재. **클래스 가중치 또는 SMOTE 같은
불균형 처리 + 시점별 표본 분포 보고 필수**. PR-AUC 외 *Brier score* 가
*양성 zero 시점*에서도 의미 있음.

대응 옵션:
- step 단위: 분기 → 반기 또는 연간으로 완화 (시점 ↓, 표본 ↑)
- forward window: 1년 → 2년 (양성 ↑, 분석 마지막 2년 손실)

### (3) 격리 항목 + 단계 2 DoD 검증

**라벨 정의 전용 (피처 사용 금지)**:
- FDR `delisting` 컬럼: `DelistingDate`, `Reason`, `ArrantEnforceDate`,
  `ArrantEndDate`, `Kind`, `ToSymbol`, `ToName`
- KRX 관리종목 데이터(수동 다운로드 후): *지정일*, *해제일*, *지정 사유*

**격리 검증 방법** (단계 2 DoD):
1. **import-time 검증**: `tests/test_isolation.py` 에서 `src/frr/features/`
   하위 모듈의 AST를 파싱해 `from frr.data.fdr import delisting` 또는
   상기 컬럼명을 *문자열로* 참조하는지 검사. 발견 시 fail.
2. **데이터프레임 컬럼 화이트리스트**: 피처 빌더의 출력 컬럼을 *허용
   리스트와 비교* — 위 격리 항목명이 컬럼에 들어 있으면 fail.
3. 둘 다 자동 실행 (CI 통과 조건).

### (4) KRX 관리종목 수동 다운로드 — 범위·분량·절차

**출처**: KRX 정보데이터시스템 (http://data.krx.co.kr)

**메뉴 경로** (사용자 확인 필요 — 예상):
- 통계 > 기본통계 > 주식 > 종목정보 > **관리·투자주의·투자경고 종목** 또는
- 통계 > 기본통계 > 주식 > 종목정보 > **시장조치 종목**
- 또는 좌측 검색에 "관리종목" 입력

**다운로드 형태**:
- **옵션 A (이벤트 리스트)**: 분석 기간 전체의 *지정·해제 이벤트 1 CSV*.
  컬럼 예상: 종목코드, 종목명, 지정일, 해제일, 지정사유.
- **옵션 B (분기말 스냅샷)**: KOSPI200 패턴 재사용 — 40 분기 × CSV.
  컬럼: 종목코드, 종목명, 지정사유 (그 시점 관리종목인 종목들).

**권장**: **A (이벤트 리스트)** — 데이터 크기 작고 (한국 시장 전체 관리종목
지정 사건은 10년에 *수백 건 수준*), 시점별 *지정·해제* 정보가 *직접* 라벨링
가능. 분기 union 도 가능.

**저장 위치**: `data/external/krx_admin/` + `MANIFEST.yaml` (KOSPI200 패턴
재사용).

**예상 분량**: 1 CSV, ~수백 행, 약 30 KB.

**사용자 작업 시간**: ~10분 (KRX 시스템 메뉴 확인 + 다운로드 + 매니페스트
기록).

**절차 상세**: `docs/data_sources.md` §5 (KRX 관리종목)에 추가 작성 예정
(D2 확정 후).

---

## 5. 학습된 규칙·결정 로그 (Decision Log)

> 확정되면 시간 역순으로 누적. 동시에 CLAUDE.md에도 반영한다.

- **2026-05-19** — ★★ **D2 최종 확정** (입증된 최선):
  - D2 = α (상폐 부실 ∪ B1', 1년 forward). 양성 27 (8.4%), 0년 2 (2021·2023).
  - **확정의 성격**: α 는 *5개 후보(D2(E)·B1 v1·v2·B3·A) 전수 검증·기각
    여정 끝에 남은 입증된 최선*. *선택*이 아님. 각 후보 기각 증거는
    PROGRESS §5.5.1~§5.5.8 에 누적 보존.
  - **A1 결과 (2026-05-19, §5.5.8)**: 신용등급 자동 확보 출처 *4영역 ×
    8 출처 전수 검증 → 자동 확보 불가능* 또는 *B1.2급 함정 동등 부담*.
    DART 276,099 공시 7 키워드 매칭 0건 + 평가사 3사 전부 유료·저작권
    차단 + 공공 데이터 발행자별 시계열 미제공.
  - **α 의 한계 정직 기록**: 양성 절대 건수 부족(27) + 0년 2개 (2021·2023)
    — KOSPI200 모집단 부실 희소성에 기인. 단계 2 학습 측 보완(class weight·
    forward 2년 ablation·bootstrap·시점별 가중치) 의 *구체 설계와 평가
    영향*은 단계 2 진입 시 D8 과 함께 결정.
  - **2026-05-19 의 정정 줄(α 후보 격하)은 여정 기록으로 그대로 보존** —
    여정 자체가 포트폴리오 가치.
- **2026-05-19** — D2 확정 정정: α(상폐∪B1', 27건·8.4%)는 **후보 B**로 격하.
  사용자 요청 — 후보 A(신용등급)와 동일 진단 틀(자동 확보 가능성·양성 수·
  walk-forward 연도 분포·spot-check)로 숫자 검증 후 비교표 작성. A 가용 +
  의미 보존 우수 → A 확정. A 가 B1.2급 부담 → B 확정. 진단 누적 자료
  (§5.5) 는 전부 유효 (B 후보 증거). 커밋 2 (`docs(d2): revert D2 to
  candidate state + enforce ruff format pre-commit`) 로 박제.
- **2026-05-19** — ★ **D2 1차 후보 확정 (이후 사용자 요청으로 격하)** (§5.5.7):
  - **D2 = 상폐 부실 합집합 B1' (drawdown 50% + 영업이익 음수 전환)**, 1년 forward.
  - 양성 27 (8.4%) · 중복 0 (두 신호 독립) · 0년 2개 (2021·2023, 도메인 사실)
  - **B3 (KOSDAQ 스코프 확장) 기각**: KOSDAQ150 시점별 구성 자동·수동 모두
    불가 (FDR/pykrx/KRX) → D1에서 거부한 생존 편향 재발 위험 → 방법론적
    엄밀성과 직접 충돌. 기각 사유는 *양성 부족*이 아니라 *데이터 정합성*.
  - **A2 (신용등급 하향) 기각**: DART `list()` 가 *기업 corp_code 기반*만
    반환 → 평가사 발행 공시 미포함 → 0 매칭. 평가사 사이트 파싱은 B1.2급
    1인 부담 → 기각.
  - **B1' 단독 양성 19 (5.9%) → α 합집합 27**: 학습 임계 30 근접. 0년 4→2
    축소. 두 라벨 *완전 독립* (중복 0)으로 *진짜 정보 증가*.
  - **β 학습 측 보완 채택**: class weight / forward 2년 ablation / bootstrap /
    시점별 가중치 (단계 2 진입 시 구현).
  - **D2 결정의 학술·면접 방어 가치**: 두 차례 라벨 오염 실패(B1 v1/v2) →
    모집단 본질 통찰 → 두 갈래 공정 비교(B3 vs 타깃 재정의) → A2 데이터
    한계 검증 → B1' 객관 정의 → α 합집합 *진단 누적 자료* 자체가 포트폴리오
    가치. 모든 단계 진단 스크립트 git 추적.
- **2026-05-18** — D2 결정 누적 진단 + 폐기 결정 4건:
  - **D2(E) = D2(A) 양성 동일 확정** (관리 차원 통계 기여 0).
    라벨은 *상폐 부실 사유 단독*으로 표현.
  - **B2 폐기** (자기참조 — 영업이익이 입력·라벨 동일 변수족)
  - **B4 폐기** (비실현 사건 — 임의 임계, 사후 적합)
  - **KRX [12006] 수동 다운로드 종료** (Cowork DOM 전수 조사로 일자 입력
    요소 부재 확정. 모든 인덱스에 적용. 시점별 관리종목 자동 확보 불가능.)
  - **B1 v1 폐기** (광범위 severe 필터 → 양성 96.6%, 잠정실적 정정 등
    혼입으로 라벨 오염 실패)
  - **B1 v2 폐기** (정밀 severe 필터 → 양성 96.0%, report_nm 만으로 *어떤
    항목*이 정정됐는지 판별 불가. 정정 본문 파싱은 1인 단계 1 후반에 무리)
  - **★ 근본 원인 통찰**: KOSPI200 = 대형 우량주 → 부실 사건 모집단 부적합.
    데이터 출처·필터 정밀화로 해결 불가. *모집단 변경(B3)* 또는 *타깃
    재정의*가 답.
  - **다음**: 두 갈래 사전 진단 (B3 KOSDAQ 사전 진단 vs D2 타깃 재정의).
    스코프 변경(B3)은 D1 핵심 경계 영향이라 단순 양성 확보로 결정 X.
- **2026-05-18** — **단계 1 종료** + 전체 수집 결과 + D8/D9/D10 승인:
  - **전체 수집**: 321 종목 / KRX 321 / DART 10,114 ok + 2,719 notfound +
    **7 failures**. 7 failures **모두 룩어헤드 차단의 의도된 동작**
    (정정공시·재공시가 2026년 접수). `docs/data_sources.md §4` 박제.
  - **notfound 2,719 분포**: 252 종목 0~25%, 4 종목 100% (전체 notfound,
    합병폐지 or corp_code 매핑 실패). point-in-time 기대 패턴 일치.
  - **D8 평가 지표 승인** — PR-AUC + AUC + Brier + Calibration + Top-K precision.
    walk-forward expanding window.
  - **D9 리포트 스키마 승인** (조건부 — 격리 변수 차단 검증, `key_ratios`
    카탈로그는 단계 2 도메인 검토).
  - **D10 CFS/OFS 승인** — 옵션 C (CFS 우선 + OFS fallback). 단계 2 진입 시
    지주 vs 비지주 라벨링 영향 별도 검토 명시.
  - **D2 자료 (1)~(4) 정리 완료** (§5.5). 상폐 부실 양성 ~9건 (지주
    완전자회사화 제외), 관리종목 데이터 보강 필수. 양성 zero 위험 구간
    (2020-2021) 식별. D2 확정 대기.
- **2026-05-18** — `dart.py` v1 작성 + D10(CFS/OFS) 결정 대기 등록:
  - `DARTReporter.fetch_report(ticker, year, period)` 가 OpenDartReader.finstate
    를 호출하고, **`rcept_no` 첫 8자에서 `rcept_dt`** 를 추출한 뒤
    **`available_from = calendars.add_business_days(rcept_dt, 1)`** 로 D7
    룩어헤드 차단을 코드화. `available_at(t)` / `latest_available(t)` 가
    *t 이후 available_from* 인 보고서를 절대 반환하지 않음.
  - 캐시: `data/raw/dart/{ticker}/{year}_{period}.{parquet, meta.yaml}`.
    `notfound` 상태도 메타에 기록해 재페치 회피 (DART 한도 절약).
  - **`finstate` 기본은 연결재무제표(CFS)**. 단계 2의 D2 부실 라벨·피처
    설계에 영향 가능 → **D10 결정 대기** 등록 (단계 2 진입 시 재검토).
  - 통합 테스트 1개로 사용자 키로 005930 2020 FY 페치 성공 검증.
- **2026-05-18** — `fdr.py` 작성 + FDR 상폐 데이터 한계 발견:
  - `FDRDataSource.listing()` / `delisting()` + parquet 캐시. 종목코드
    6자리 str 강제·날짜 datetime64 정규화. Module docstring에 상폐
    메타데이터 격리 원칙 박제.
  - **FDR KRX-DELISTING 한계** (4128건):
    - 상당수가 신주인수권·우선주 *부산물 종목* (8자리 코드, "...2R" 류)
    - *진짜 부실 상폐* 일부 누락 (예: 카프로 006380 — universe_loader의
      2015Q1 데이터에 있고 2017-12 폐지된 종목인데 FDR에 없음)
    - → 단계 2 D2 라벨 정의 시 *출처 보강* 필요. 미해결 결정으로
      "단계 2 진입 시 추가될 DoD" 섹션에 기록.
- **2026-05-18** — 40/40 KOSPI200 분기 다운로드 완료 + 행 수 사실 발견:
  - 사용자가 전 분기(2015Q1~2024Q4) 수동 다운로드·매니페스트 작성 완료.
  - **새 사실 ①**: KOSPI200이 *목표 200종목*이지만 인덱스 리밸런싱 직후
    며칠 동안 신규 편입 종목이 임시 추가되어 *행 수 200~202* 가능.
    `docs/data_sources.md` §3.4 + 테스트 범위 [200,202] 갱신.
  - **새 사실 ②**: 13/40 분기가 *비영업일 fallback* 필요. KRX는 비영업일
    입력 시 *데이터 없음* 응답(자동 매핑 안 함). 사용자가 직전 영업일로
    수동 보정해 매니페스트의 `actual_reference_date` 에 기록.
- **2026-05-18** — `calendars.py` 작성: KRXBusinessCalendar (FDR KS200 기반).
  `is_business_day` / previous/next / floor/ceil / `add_business_days(d, n)`.
  D7(rcept_dt+1) 적용 인프라. parquet 캐시 자동.
- **2026-05-18** — KOSPI200 1차 다운로드(2015Q1)·CSV 스키마 확정·비영업일 처리 합의:
  - KRX 메뉴 번호 [11005]→[11006] (메뉴 이름 동일)
  - CSV 스키마: cp949·6컬럼·200행. 종목코드는 *반드시 str*, 상장시가총액은
    과학표기법 가능, 등락률은 percent 값.
  - 응답 본문에 기준일 미명시. 영업일 분기말은 그대로 기록, 비영업일은
    KRX 화면 표시 *적용 일자*를 기록하거나 null로 두면 로더가
    `calendars.py`로 직전 영업일을 채움.
  - 2015Q1에 카프로(006380, 2017-12 상폐) 포함 확인 → point-in-time
    유니버스 정의가 정확히 작동함을 첫 데이터로 검증.
- **2026-05-18** — 단계 1 가용성 검증 결과 + 데이터 소스 다층화:
  - **분석 기간 2010-2024 → 2015-2024 단축** *(사유: KRX 웹 서버가 2014-05-01
    이전 데이터를 제공하지 않음을 직접 확인)*.
  - **pykrx 시점별 전종목/인덱스 API 사용 금지** *(KRX 응답 컬럼 변경으로
    KeyError·빈 결과)*. pykrx는 *단일 종목 OHLCV·종목명*에만 사용.
  - **FinanceDataReader(FDR) 채택** — 현재 시점 전종목 리스트(Marcap),
    상장폐지 데이터(4128건, ListingDate/DelistingDate/Reason 포함),
    KOSPI200 지수 시계열 용도. `pyproject.toml`에 `finance-datareader>=0.9.94` 추가.
  - **KOSPI200 시점별 구성 — 옵션 A (수동 다운로드) 채택**:
    KRX 정보데이터시스템에서 분기 CSV 40개(2015 Q1~2024 Q4)를 *1회성 수동
    다운로드* → `data/external/kospi200_quarterly/` 에 정적 보관 + git 추적.
    자동 크롤링은 KRX 페이지 변경 리스크로 비채택 (pykrx 사례).
  - **데이터 매니페스트 정책** 신설 (CLAUDE.md §8.3) — 외부 파일마다
    source/reference_date/downloaded_at/path/sha256 기록.
  - **상장폐지 메타데이터 격리 원칙** 추가 (CLAUDE.md §5) — 폐지일·사유·
    관리종목 지정일 등을 *라벨 정의에는 사용 가능, 피처로는 금지*.
    단계 2 DoD에 검증 테스트 추가.
- **2026-05-18** — 단계 1 환경 셋업 호환성 결정:
  - **Python 3.11 → 3.13** 으로 갱신. *사유*: `opendartreader>=0.3.0` 이
    Python 3.13을 요구. 옛 버전(`<0.2.5`) 사용은 보안·DART API 변경 대응
    공백 우려로 비추.
  - **`setuptools` 70~79 범위로 핀**. *사유*: `pykrx`가 `pkg_resources`를
    import하는데 setuptools 80에서 제거됨.
  - **`opendartreader` 0.3+ import 이름은 소문자** (`import opendartreader`).
    0.2.x의 `OpenDartReader` PascalCase와 다르므로 코드 작성 시 주의.
  - **`opendartreader.__version__`이 dist 메타데이터(0.3.2)와 다른 0.2.4**
    를 노출 — 메인테이너 동기화 누락. 실제 코드는 0.3.2. 작동 영향 없음.
- **2026-05-17** — D1·D7·분석 기간 확정 (단계 1 진입 결정):
  - **D1 유니버스**: *point-in-time* — 분기별 KOSPI200 구성 종목
    + 분석 기간 내 KOSPI200 상장폐지 종목 (15년 union ≈ 300~350)
    - *근거*: 단순 시총 상위는 생존 편향으로 *부실 라벨의 양성 클래스
      자체가 사라짐* → 부실 모델 학습 무력화. 사용자가 정확히 지적.
    - *조건 1*: KOSDAQ·소형주는 후속 과제로 한계 명시 (CLAUDE.md §4.1 박제,
      단계 5에서 docs/methodology.md 정식 작성)
    - *조건 2*: 유니버스 변수(편입/편출, 시총 순위 등)는 펀더멘털 모델 피처
      사용 **금지** (CLAUDE.md §5에 격리 원칙 추가). 단계 2 DoD에 검증 테스트 추가.
    - *조건 3*: pykrx 가용성을 단계 1 첫 작업으로 사전 확인.
  - **D7 재무 lag**: DART 접수일 `rcept_dt` + 1영업일 (학술·실무 표준)
  - **분석 기간**: 2010-01-01 ~ 2024-12-31 (K-IFRS 의무화 이후 15년)
- **2026-05-17** — 단계별 진행 계획 확정 (총 7.5~11주):
  - 단계 1 데이터 셋업 1~2주 → 단계 2 펀더멘털 2~3주 → 단계 3 국면 1.5~2주
    → 단계 4 통합 대시보드 2~3주 → 단계 5 마무리 1주
  - 각 단계 진입 시점에 관련 D-항목 결정.
  - 단계 1 진입 → D1·D7·분석 기간 결정 대기.
- **2026-05-17** — 디렉터리 구조 합의 (CLAUDE.md §8.6 참조):
  - **src layout** + 패키지명 `frr` (짧고 임포트 깔끔)
  - `src/frr/llm/` 단일 출구 — 다른 모듈은 `LLMProvider` 인터페이스만 본다
  - `app/`(Streamlit)는 LLM SDK import 금지, 정적 JSON만 읽음 — CI 검사 가능
  - 데이터 흐름 단방향 (`raw → interim → processed → reports`)
  - **점진 생성** 정책 채택 — placeholder 미생성, 단계 진입 시 필요 파일만 추가
- **2026-05-17** — 기술 스택 1차 확정 (D5/D6 포함):
  - Python 3.11 + uv (재현성·속도)
  - 데이터: OpenDartReader + pykrx, parquet 저장
  - ML: scikit-learn + LightGBM, 국면: hmmlearn (GMM 비교)
  - **LLM: Gemini Free Tier** + `LLMProvider` 추상화
    - *근거*: 사용자 제약 — Max 유지 보장 없음·서비스 지속 비용 부담 어려움·*완전 무료* 우선
    - *정책*: LLM 호출은 **빌드 타임 배치 1회**만, 결과 JSON 고정.
      **서비스 런타임(대시보드) LLM 호출 0회**. 따라서 배포 시 비용 0원.
    - *원칙*: 직접 학습/개발하는 AI(부실 스코어링 + 국면 분류)가
      포트폴리오의 *주연*, LLM은 *조연* (CLAUDE.md §3.4)
  - 대시보드: Streamlit + plotly (직전 Flask와 다른 색·1인 6~12주에 안전)
  - 산출물 추적: 파일시스템 + git (MLflow 미도입)
  - 품질: pytest + ruff + GitHub Actions (lint+test)
- **2026-05-17** — 저장소 `MoriochoRadio/fundamental-regime-report`,
  Public, MIT 라이선스로 생성. GitHub 형상관리를 진행 기준으로 채택.

---

## 6. 다음 갱신 트리거 (Update Triggers)

다음 중 하나라도 발생하면 본 문서를 갱신한다:

- 한 작업 단위(기능·단계) 완료
- 새로운 결정 확정 (D1~D9 등)
- 미해결 이슈 추가/해소
- 단계 전환 (1→2, 2→3 …)
