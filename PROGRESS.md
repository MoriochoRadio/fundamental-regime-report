# PROGRESS.md

이 문서는 본 프로젝트의 **변하는 상태**를 추적한다.
변하지 않는 사실·규칙·방향은 `CLAUDE.md` 에 있다.

**마지막 갱신**: 2026-05-18 (configs/data.yaml + config 로더 + 68 테스트 통과)

---

## 1. 현재 상태 (Current Status)

- **단계**: **1 — 데이터 셋업** (유니버스 인프라 완성, 시세·재무 어댑터 단계)
- **요약**: 환경·가용성·데이터 소스 결정·40/40 CSV 다운로드·universe_loader·
  calendars 모두 완료. 32 테스트 전부 통과. 다음은 DART/FDR/pykrx 어댑터
  + configs/data.yaml + 룩어헤드 통합 테스트 + CI.
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
- [x] **`src/frr/data/dart.py` v1 작성** — `DARTReporter`: `fetch_report(ticker, year, period)` / `available_at(t)` / `latest_available(t)`. **`rcept_no` 첫 8자 → `rcept_dt`** 추출, **`available_from = rcept_dt + 1영업일`** (D7 룩어헤드 차단의 코드 구현). 캐시 = parquet + yaml sidecar, `notfound` 상태 메타 기록으로 DART 한도 절약. CFS 기본 (D10 결정 대기).
- [x] **`tests/test_dart.py` 11 테스트 통과** — 단위 10 + **통합 1 (실 DART API + 실 캘린더 FDR fetch로 005930 2020 사업보고서 페치 + rcept_dt 2021-03-09 + available_from 2021-03-10 검증)**. 전체 61 + 1 skip (4.49s).
- [x] **`configs/data.yaml` + `src/frr/config.py` 작성** — 분석 기간·유니버스 매니페스트·DART lag·periods·fs_div 의 단일 source of truth. frozen dataclass 4개 + `load_data_config(path)`. pydantic 미도입 (단순성 우선). `fs_div: CFS` 주석에 *D10 결정 대기* 표기.
- [x] **`tests/test_config.py` 7 테스트 통과** — 실 yaml 검증 1 + 경계(tmp_path 격리) 6. 전체 68 + 1 skip (4.85s).

---

## 3. 다음 할 일 (Next)

> 모두 사용자 확인을 받은 뒤 진행한다.

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
   12. **`scripts/collect_data.py`** ← **다음** — 배치 수집 진입점
   13. `tests/test_time_align.py` — D7 lag 적용 + 룩어헤드 차단 통합 테스트 (격리 두 항목은 단계 2)
   14. GitHub Actions CI (`.github/workflows/ci.yml`) — lint + pytest

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

---

## 4-pre. 미해결 이슈 — 코드 (Open Issues)

> 결정이 아니라 *코드 차원에서 점검 예정* 항목.

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
| D2 | 부실(라벨) 정의 | 관리종목 지정, 상장폐지, 신용등급 다운그레이드, Altman Z 임계 등 | 미정 |
| D3 | 국면 모델 | HMM(상태 수 K=?), GMM, K-Means, 변경점 탐지 | 미정 |
| D4 | 국면 입력 피처 | 지수 수익률, 변동성, 거래량, 금리/환율 등 매크로 | 미정 |
| D5 | 대시보드 프레임워크 | ~~Streamlit / Dash / Next.js + FastAPI~~ | ✅ **Streamlit + plotly** |
| D6 | LLM 공급자·정책 | ~~Anthropic / OpenAI / 로컬~~ | ✅ **Gemini Free Tier + LLMProvider 추상화 / 빌드타임 배치 1회 / 런타임 0호출** |
| D7 | 재무 데이터 시점 처리 | ~~lag 값 미정~~ | ✅ **DART 접수일 `rcept_dt` + 1영업일** |
| - | 분석 기간 | ~~2010-2024 (가용성 미충족)~~ | ✅ **2015-01-01 ~ 2024-12-31** (가용성 사유) |
| D8 | 평가 지표 | 부실 분류: AUC/PR-AUC/Brier? 국면: 안정성/지속성/사후해석성? | 미정 |
| D9 | 모델 카드/리포트 양식 | 출력 스키마(JSON) → LLM 서술화 파이프라인 | 미정 |
| D10 | 연결(CFS) vs 별도(OFS) 재무제표 선택 | dart.py v1은 `OpenDartReader.finstate` 기본 호출(CFS 우선). 단계 2 D2(부실 라벨)·피처 설계에 영향: 지주회사·금융지주는 별도 기반이 더 정확할 수도. 일부 종목 CFS 미작성 → OFS fallback 정책 필요. | 미정 (단계 2 진입 시 재검토) |

---

## 5. 학습된 규칙·결정 로그 (Decision Log)

> 확정되면 시간 역순으로 누적. 동시에 CLAUDE.md에도 반영한다.

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
