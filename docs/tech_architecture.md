# 기술 아키텍처 (Technical Architecture)

> 본 문서는 4 단계 산출물. 3 단계 `docs/ui_design.md` 의 페이지 와이어
> 프레임 + 10 컴포넌트 spec + UI Copy + 디자인 토큰 + 단계 5 검증 의무 4
> 항목 + 7 차원 매핑 표 직접 반영. 2 단계 `docs/ux_design.md §3` 인터랙션
> 흐름 + `§4.7` 반응형 + 1 단계 NFR-1 성능 (페이지 < 3 초·차트 < 1 초·
> 종목 전환 < 1 초) 직접 매핑.
>
> 본 문서의 핵심 본질 — Phase 4 의 TypeError + 렉 같은 문제의 *사전 차단
> 메커니즘*. 단계 5 진입 시 §7 누적 검증 의무 8 항목이 *자동 체크리스트*
> 로 작동.
>
> 단계 5 (구현, 컴포넌트 단위) + 단계 6 (`docs/qa_checklist.md`) 의 직접
> 입력.

---

## 1. 아키텍처 개요

> CLAUDE.md `§3.4` (AI/ML 역할 분리) + `§8.6` (레이아웃 원칙) 직접 매핑.

### 1.1 데이터 흐름 단방향 (CLAUDE.md §8.6)

```
[데이터 출처]                    [데이터 처리]                  [산출물 + 표시]
DART API ─┐                     ┌─ src/frr/data/ ──┐         ┌─ reports/*.md  (모델 카드)
pykrx ────┼─► data/raw/ ──────►│  (수집·정제·캐싱) │────────►│
FDR ──────┘                     ├─ src/frr/labels/  │         ├─ data/interim/ (features·predictions)
KRX CSV ────► data/external/ ──►│  (D2 부실 라벨)   │         │
                                ├─ src/frr/features/│         ├─ data/processed/
                                ├─ src/frr/models/  │         │
                                ├─ src/frr/regime/  │         │
                                ├─ src/frr/eval/    │         │
                                ├─ src/frr/llm/  ◄──┘ (LLM 단일 출구)
                                │                              ▼
                                │                   ┌─────────────────────┐
                                │                   │ app/ (Streamlit)    │
                                │                   │ - 정적 읽기 전용     │
                                │                   │ - LLM SDK import 0  │
                                │                   │ - reports/ + models/│
                                │                   └─────────────────────┘
```

**원칙**:
- **단방향**: `raw → interim → processed → reports` (역방향 금지)
- **LLM 단일 출구**: 외부 LLM SDK 는 *오직* `src/frr/llm/` 에서만 import
- **app/ 정적 읽기 전용**: 학습·계산·LLM 호출 *금지*. `reports/` 의 정적
  JSON + `models/` 의 학습된 모델만 읽음. CI 에서 `app/` 안에 LLM SDK
  import 없음 자동 검사 (`tests/test_app_no_llm_import.py`)
- **LLM 호출 정책** (CLAUDE.md `§3.4`): 빌드타임 배치 1 회 → JSON 고정 →
  런타임 호출 0 회

### 1.2 src layout (CLAUDE.md §8.6)

- 메인 패키지: `src/frr/` (이름 `frr`)
- 설치 후 `from frr.data import dart` 형태로 import
- `pyproject.toml` 의 `[tool.uv.sources]` 로 lock

### 1.3 점진 생성 (CLAUDE.md §8.6)

- 디렉토리·파일은 *단계 진입 시점*에 필요한 만큼만 생성
- 빈 패키지·placeholder 파일 사전 생성 금지

---

## 2. 컴포넌트 구조 (코드 폴더 매핑)

> 3 단계 `docs/ui_design.md §2` 10 컴포넌트 spec + 2 단계 `docs/ux_design.md §4`
> 디자인 시스템 → 코드 폴더 매핑.

```
app/
├── main.py                    # entry: st.set_page_config + 페이지 routing
├── data_loader.py             # 정적 로드 (parquet → DataFrame), @st.cache_data
├── components/
│   ├── __init__.py
│   ├── header.py              # PageHeader, TickerHeader
│   ├── metric_card.py         # RiskScoreCard, StateCard
│   ├── chart.py               # PriceChartWithStateOverlay, RatioGrid
│   ├── interpretation.py      # StateInterpretBox (9 template)
│   ├── warning.py             # ModelLimitBadge (badge/modal/page_full), EmptyState
│   └── navigation.py          # SidebarNav (4 메뉴)
├── pages/
│   ├── __init__.py
│   ├── overview.py            # 개요 페이지
│   ├── ticker_analysis.py     # 종목 분석 페이지 (메인 가치)
│   ├── market_state.py        # 시장 상태 페이지
│   └── limitations.py         # 한계 페이지
└── utils/
    ├── __init__.py
    ├── formatters.py          # format_won, format_percent, format_proba,
    │                          #   format_ratio, classify_risk,
    │                          #   format_ticker_option, format_date
    └── state_mapper.py        # lookup_state_at, compute_state_blocks,
                               #   find_close_column, find_date_column_or_index
```

**이름 정정 (Phase 3 → 4 단계, 단계 5 검증 1 직접 적용)**:
- `regime_mapper.py` → **`state_mapper.py`**
- `lookup_regime_at` → **`lookup_state_at`**
- `compute_regime_blocks` → **`compute_state_blocks`**
- 컴포넌트: `RegimeCard` → `StateCard`, `RegimeConditionalBox` →
  `StateInterpretBox`, `ModelLimitWarning` → `ModelLimitBadge`,
  `PriceChartWithRegime` → `PriceChartWithStateOverlay`

(3 단계 `docs/ui_design.md §5` (검증 1) 본문 확장: 토큰명 + 컴포넌트 이름 +
함수 이름 + 변수 이름 + 파일명 *모두 일관 정정* 의무.)

---

## 3. 데이터 흐름 (app/ 차원)

| 단계 | 내용 |
|---|---|
| 정적 로드 | `data_loader.py` 에서 모든 parquet 단일 시점 로드 (`@st.cache_data` 의무, §6.1) |
| 캐시 키 | 파일 경로 + 파일 mtime (변경 시 자동 invalidate) |
| 페이지 입력 | 로드된 DataFrame 을 페이지 함수에 *인자로 전달* (전역 상태 사용 금지) |
| 단방향 | `data_loader.py` → `pages/*.py` → `components/*.py` (역방향 금지) |
| 메모리 절약 | 종목별 OHLCV 는 *선택 시 lazy load* (§6.2) |

### 3.1 `data_loader.py` 함수 명세

```python
@st.cache_data
def load_universe() -> pd.DataFrame:
    """KOSPI200 분기 union 321 종목 메타 (1 회 로드)"""

@st.cache_data
def load_state_series() -> pd.DataFrame:
    """시장 상태 시계열 (date × state_label, 2,273 obs)"""

@st.cache_data
def load_d2_predictions() -> pd.DataFrame:
    """D2 위험 예측 (ticker × as_of × proba × class_weight, 3,602 rows)"""

@st.cache_data
def load_d2_features() -> pd.DataFrame:
    """D2 features (ticker × as_of × 4 ratio + fs_div, 8,008 rows)"""

@st.cache_data
def load_ohlcv(ticker: str) -> pd.DataFrame:
    """종목별 OHLCV (선택 시 lazy load)"""

@st.cache_data
def load_llm_interpretation(ticker: str, as_of: str) -> dict | None:
    """LLM 빌드타임 배치 서술 (정적 JSON, 런타임 호출 0)"""
```

---

## 4. 상태 관리

| 정책 | 내용 |
|---|---|
| `st.session_state` 사용 항목 | **3 항목만** — `current_page` (str), `selected_ticker` (str), `selected_as_of` (str ISO) |
| 사용 금지 | 큰 DataFrame 저장 (메모리 누수 차단). DataFrame 은 *함수 인자로 전달* |
| 페이지 이동 | URL 매개변수 (`?page=...&ticker=...`) + session_state 동기화 |
| 초기값 | `current_page="overview"`, `selected_ticker=None`, `selected_as_of=None` |

---

## 5. ★ 에러 처리 정책 7 항목

> 각 항목 = 단위 테스트 의무 (§7 검증 7 매핑) + 사용자 안내 본문.

### 5.1 pandas Timestamp + plotly 호환성 (Phase 4 TypeError 직접 차단)

**의무**: 모든 `fig.add_vline(x=...)` 인자에 `.to_pydatetime()` 의무.
annotation 은 별도 `fig.add_annotation` 호출.

**본 의무는 *단위 테스트 (검증 7 매핑)* + *streamlit 실행 후 실측 검증*
두 차원으로 검증**. Phase 4 의 실제 누락 본질은 *박제 vs 실측 불일치*
(`220d1ac` 박제 + 실측 잔존) — `PROGRESS §5.9` 5 번째 사례 적용 = *박제만
으로 부족, 실측 검증 의무 결합*.

**구현 예시**:

```python
# ✗ 위반 (Phase 4 TypeError 재발 위험)
fig.add_vline(x=as_of, annotation_text="분석 시점")

# ✓ 통과
fig.add_vline(x=as_of.to_pydatetime())
fig.add_annotation(x=as_of.to_pydatetime(), y=...,
                   text="분석 시점", showarrow=False)
```

**컴포넌트 매핑**: `PriceChartWithStateOverlay`, `RatioGrid`.

### 5.2 데이터 부재 (EmptyState 안내)

**의무**: 분석 평가 제외 시점·universe 비멤버·산출물 부재 시 `EmptyState`
컴포넌트 (3 단계 `§2.9`) 노출 + 다음 행동 제안.

**본문 예시**: "이 시점은 평가 자료 부족으로 분석 제외" / "다른 시점 선택" 제안.

### 5.3 universe 비멤버 종목 선택

**의무**: "이 종목은 분석 시점 범위 밖" 안내 + 사이드바 검색창 강조 (FR-4
매핑).

### 5.4 parquet 로드 실패

**의무**: `st.error` + "데이터 준비 중. 잠시 후 다시 시도해 주세요." 안내.

**개발 모드 외 traceback 노출 금지** (2 단계 `§3.7` 매핑). 개발 모드는
환경 변수 `FRR_DEV=1` 로 토글.

### 5.5 DART API 응답 부재 (단계 1 백엔드 차원)

**의무**: data layer 에서 `notfound` 메타 기록 + UI 는 "데이터 없음" 일관
표시. 단계 1 PROGRESS `§5.5.5` 결정 매핑.

### 5.6 빈 DataFrame 처리

**의무**: 모든 컴포넌트에서 `df.empty` 사전 검사 + `EmptyState` fallback.

**구현 예시**:

```python
def render_chart(df: pd.DataFrame) -> None:
    if df.empty:
        render_empty_state("데이터 없음", "다른 시점 선택")
        return
    # ... chart 렌더링
```

### 5.7 numpy NaN 처리

**의무**: `format_*` 함수에 `None` · `NaN` 입력 시 "—" 표시 (3 단계 `§2`
spec 직접).

**구현 예시**:

```python
def format_won(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    if value >= 1e12:
        return f"{value / 1e12:.1f} 조원"
    # ...
```

---

## 6. ★ 성능 정책 5 항목

> Phase 4 의 렉 문제 (페이지 로딩 느림·캐싱 부재·lazy load 부재·페이지
> 분할 부재) 직접 차단. 1 단계 NFR-1 수치 임계 매핑.

### 6.1 `@st.cache_data` 의무 (모든 정적 로드)

**의무**: `data_loader.py` 의 모든 `load_*` 함수 → `@st.cache_data` 데코
레이터 의무.

**수치 임계**: cache hit 시 < 50 ms (첫 로드는 < 500 ms).

### 6.2 큰 데이터 lazy load

**의무**:
- 321 종목 메타 → 1 회 로드 (`load_universe`)
- 종목별 OHLCV → *선택 시 lazy load* (`load_ohlcv(ticker)`)
- LLM 서술 → *선택 시 lazy load* (`load_llm_interpretation(ticker, as_of)`)

**메모리 절약**: 한 번에 321 종목 OHLCV 전체 로드 *금지*.

### 6.3 plotly 차트 데이터 크기 제한

**의무**:
- 10 년 일간 (~ 2,500 점) → 차트 차원에서는 *그대로 OK* (plotly 권장 범위
  내)
- 만약 5 년 이상 hourly 등 큰 데이터 시 *다운샘플* (월간 또는 주간 OHLC
  변환)

**컴포넌트 매핑**: `PriceChartWithStateOverlay`, `RatioGrid`.

### 6.4 페이지 분할

**의무**:
- `st.tabs` *회피* (모든 tab 사전 렌더 → 렌더 비용 누적)
- `st.sidebar` *우선* (페이지 ↔ 페이지 이동, `SidebarNav` 컴포넌트)
- 큰 섹션은 `st.expander` 로 *지연 렌더*

### 6.5 NFR-1 수치 임계 (1 단계 NFR-1 매핑)

| 항목 | 임계 | 측정 도구 |
|---|---|---|
| 페이지 초기 로딩 | < 3 초 | Chrome DevTools Performance |
| 차트 렌더 | < 1 초 | DevTools (단일 차트) |
| 종목 전환 | < 1 초 (캐시 hit 이후) | DevTools |

단계 6 QA 시 시나리오 측정 의무 (§7 검증 8 매핑).

---

## 7. ★ 단계 5 진입 시 누적 검증 의무 8 항목

> 3 단계 `docs/ui_design.md §5` 4 항목 + 4 단계 신설 4 항목 = 8 항목.
> 단계 5 진입 시 *자동 체크리스트* 로 작동. 컴포넌트 단위 + 매 단위
> streamlit 실행 검증 의무 + 매 단위 사용자 결정 게이트 (현행 유지 정책).

### (검증 1) 토큰 + 컴포넌트 + 함수 + 변수 + 파일명 일관 정정 (3 단계 박제)

`regime.*` → `state.*` 코드 일관 정정. 단계 5 진입 시 `grep regime` 전체
코드 베이스 검증 (UI 코드 + 데이터 처리 코드 + 테스트 코드 + 설정 파일)
의무.

### (검증 2) D2 baseline 별도 페이지 폐기 + 모델 카드 link 만 (3 단계 박제)

- `app/pages/d2_results.py` 신설 *금지*
- 모델 카드 link 는 *Limitations 페이지* 에 link 만 유지
- 단계 5 진입 시 `app/pages/` 디렉토리에 `d2_results.py` 존재 검증 (있으면
  본 검증 (2) 위반)

### (검증 3) 시장 상태 페이지 전이 행렬·HMM 시드 분산 폐기 (3 단계 박제)

- `app/pages/market_state.py` 의 해당 섹션 신설 *금지*
- 단계 5 진입 시 `app/pages/market_state.py` 본문에 `transition`, `HMM`,
  `seed`, `시드` 등 키워드 grep 검증

### (검증 4) `§5` (1) 부속 박제 UI 코드 차원 적용 (3 단계 박제)

자동 grep 검사 — UI 코드 (`app/**/*.py`) + 렌더링 결과에 다음 키워드 잔존 0:
- 원본 영문 ML 용어: `PR-AUC`, `ROC-AUC`, `Brier`, `walk-forward`,
  `embargo`, `HMM`, `K-Means`, `K-Modes`, `log-likelihood`, `ablation`,
  `class weight`, `fold`, `skipped`, `regime`, `bootstrap`, `SMOTE`,
  `forward window`, `lookback`, `seed`
- 번역어 (§5 (1) 부속 박제 위반): `시간 분할 학습`, `평가 곡선 면적` 등
  (번역어가 ML 차원 의미 보존 경우)

### (검증 5) 변환 22 항목 단계 5 적용 누락 0 (4 단계 신설, 자문 보강)

2 단계 7 (Empty State / 마이크로카피 / 숫자 / 분석 시점 / 호버 / 빈 상태 /
부분 데이터) + 3 단계 15 (10 컴포넌트 + UI Copy + 페이지 §2.1·§2.2·§2.5
+ 마이크로카피 + 상태별 UI + QA 입력) = **22 항목** 변환 자산이 단계 5
구현에 모두 반영.

단계 5 진입 시 22 항목 자기 점검 체크리스트 적용 의무.

### (검증 6) 단계별 본질 차원 분리 정신 적용 (4 단계 신설, 자문 보강)

외부 표면 (페이지·UI Copy·5 초 이해 차원) vs 내부 명세 (컴포넌트 spec·
토큰 적용·검증 의무·매핑 표) *자연 분리*. `PROGRESS §5.10` 사례 3호
(self-defining 메타) + 자문 보강 2 (`§6` 매핑 표 메타) 깊은 적용.

단계 5 진입 시 각 컴포넌트 작성 시 *외부 표면 차원 결과* vs *내부 명세
차원 결과* 자기 분리 의무.

### (검증 7) 에러 처리 7 항목 자동 검증 (4 단계 신설)

본 `§5` 7 항목 각각 단위 테스트 의무:
- 5.1 Timestamp+plotly → `tests/test_chart_vline_compat.py` (Timestamp 입력
  + `.to_pydatetime()` 적용 검증)
- 5.2 데이터 부재 → `tests/test_empty_state.py`
- 5.3 universe 비멤버 → `tests/test_universe_filter.py`
- 5.4 parquet 로드 실패 → `tests/test_data_loader_error.py`
- 5.5 DART notfound → 단계 1 기존 테스트 재사용 + UI 측 통합 테스트
- 5.6 빈 DataFrame → `tests/test_empty_df_handling.py` (모든 컴포넌트 대상)
- 5.7 NaN → `tests/test_formatters_nan.py`

### (검증 8) 성능 정책 5 항목 자동 측정 (4 단계 신설)

본 `§6` 5 항목 자동 측정 시나리오:
- 6.1 cache → cache hit/miss 단위 테스트 (`@st.cache_data` mock)
- 6.2 lazy load → 메모리 측정 (`psutil`) + lazy 패턴 단위 테스트
- 6.3 차트 데이터 크기 → 차트 데이터 점 개수 단위 테스트
- 6.4 페이지 분할 → `st.tabs` 사용 0 grep 자동 검사
- 6.5 NFR-1 수치 → Chrome DevTools 시나리오 (단계 6 QA)

---

## 8. 매핑 표 (정합성 검사)

> 자문 권장 §8 신설. 에러 + 성능 → FR/NFR/컴포넌트/페이지 매핑 누락 0 검증.

### 8.1 에러 처리 7 항목 매핑

| 에러 항목 (§5) | 1 단계 FR/NFR | 컴포넌트 (3 단계 §2) | 페이지 (3 단계 §1) |
|---|---|---|---|
| 5.1 Timestamp+plotly | NFR-1 (0 위반 시 렉) | `PriceChartWithStateOverlay`·`RatioGrid` | 종목 분석 |
| 5.2 데이터 부재 | FR-3 (한계 안내) | `EmptyState` | 종목 분석·시장 상태 |
| 5.3 universe 비멤버 | FR-3·FR-4 | `EmptyState`·`SidebarNav` | 종목 분석 |
| 5.4 parquet 실패 | NFR-1·NFR-5 (정확성) | 전체 컴포넌트 | 모든 페이지 |
| 5.5 DART notfound | FR-3 | `TickerHeader`·`RatioGrid` | 종목 분석 |
| 5.6 빈 DataFrame | NFR-5 | 전체 컴포넌트 | 모든 페이지 |
| 5.7 NaN | NFR-5 + 2 단계 §4.6 | `format_*` utils | 모든 페이지 |

**매핑 누락 = 0** (모든 에러 항목 = ≥ 1 FR/NFR + ≥ 1 컴포넌트 + ≥ 1 페이지).

### 8.2 성능 정책 5 항목 매핑

| 성능 (§6) | 1 단계 NFR | 컴포넌트·페이지 |
|---|---|---|
| 6.1 cache | NFR-1 | `data_loader.py` (모든 `load_*` 함수) |
| 6.2 lazy load | NFR-1 | 종목별 OHLCV·LLM 서술 |
| 6.3 차트 데이터 제한 | NFR-1 | `PriceChartWithStateOverlay`·`RatioGrid` |
| 6.4 페이지 분할 | NFR-1 | `SidebarNav` (st.tabs 회피) |
| 6.5 NFR-1 수치 임계 | NFR-1 | 단계 6 QA 측정 (모든 페이지) |

**매핑 누락 = 0** (모든 성능 항목 = ≥ 1 NFR + ≥ 1 컴포넌트/페이지).

### 8.3 누적 검증 의무 8 항목 매핑

| 검증 (§7) | 검증 방법 | 단계 5 진입 시점 자동 적용 |
|---|---|---|
| (검증 1) 일관 정정 | `grep regime` 전체 코드 베이스 | ✅ |
| (검증 2) D2 페이지 폐기 | `ls app/pages/d2_*` = 없음 | ✅ |
| (검증 3) 시장 상태 폐기 | `grep "transition\|HMM\|seed" app/pages/market_state.py` = 0 | ✅ |
| (검증 4) §5 (1) UI 적용 | `grep` ML 용어 + 번역어 = 0 (UI 코드 + 렌더링 결과) | ✅ |
| (검증 5) 변환 22 항목 | 22 항목 체크리스트 적용 | ✅ |
| (검증 6) 차원 분리 | 각 컴포넌트 외부/내부 차원 자기 분리 | ✅ |
| (검증 7) 에러 7 단위 테스트 | `tests/test_*_error.py` 7 개 통과 | ✅ |
| (검증 8) 성능 5 측정 | Chrome DevTools 시나리오 + grep | ✅ |

---

## 9. 다음 단계 (단계 5 입력)

본 4 단계 산출물은 다음 단계의 직접 입력:

| 단계 | 산출물 | 본 문서에서 직접 입력 |
|---|---|---|
| 5 | 구현 (컴포넌트 단위) | `§2` 폴더 구조 + `§3` 데이터 흐름 + `§4` 상태 관리 + `§5` 에러 처리 7 + `§6` 성능 5 + **`§7` 누적 검증 의무 8 항목 자동 체크리스트** |
| 6 | `docs/qa_checklist.md` | `§5` 에러 7 + `§6` 성능 5 + `§7` 검증 7 (단위 테스트) + `§7` 검증 8 (성능 측정) + `§8` 매핑 표 |
