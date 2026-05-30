# UI 설계 + 텍스트 와이어프레임 (UI Design + Wireframes)

> 본 문서는 3 단계 산출물. 2 단계 `docs/ux_design.md` 의 사이트맵 (4
> 페이지) + 디자인 시스템 (색상·타이포·간격·컴포넌트·반응형·접근성) +
> UX 원칙 5 + (1) 부속 박제 직접 반영. 단계 4 (`docs/tech_architecture.md`
> 에러·성능 정책) + 단계 5 (구현, 컴포넌트 단위) + 단계 6 (`docs/qa_checklist.md`)
> 의 직접 입력.
>
> 본 문서는 Phase 3 commit `ec90c86` (`docs/ui_components.md`) 의 *재작성*
> 산출:
> - 폐기 ~35%: `§0` 디렉토리 (Phase 4 입력) / `§1.4` RegimeCard ML 용어 /
>   `§1.7` RegimeConditionalBox / `§1.8` ModelLimitWarning 본문 ML 수치 /
>   `§2.3` 시장 국면의 전이 행렬·HMM 시드 분산 부분 / `§2.4` D2 baseline
>   페이지 전체 / `§6` Phase 4 구현 순서
> - 부분 변환 ~45%: 10 컴포넌트 중 9 (이름 정정 4 + 본문 정정 5) + 페이지
>   §2.1·§2.2·§2.5 + 마이크로카피 §3 + 상태별 UI §5 + QA 입력 §7
> - 그대로 재사용 ~20%: `§4` utils 명세 (format_won·format_percent·
>   classify_risk·find_close_column 등)

---

## 1. 페이지별 텍스트 와이어프레임 (4 페이지)

### 1.1 개요 (Overview) — `app/pages/overview.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚠️ 본 시스템은 시연용 데모입니다. 실제 투자에 사용 금지.            │  ← ModelLimitBadge (NFR-4)
├─────────────────────────────────────────────────────────────────────┤
│ [Sidebar]                                                            │
│  - 개요 ●                                                            │
│  - 종목 분석                                                         │
│  - 시장 상태                                                         │
│  - 한계                                                              │
├─────────────────────────────────────────────────────────────────────┤
│  # 한국 KOSPI200 기업 분석 데모                            (h1)      │
│                                                                      │
│  한국 KOSPI200 200대 기업의 재무 건강과 시장 상황을 한눈에 보여      │
│  주는 웹 시스템입니다.                                    (body)     │
│                                                                      │
│  ─────────────────────────────────────────────────────────           │
│                                                                      │
│  ## 예시 종목                                              (h2)      │
│  (3 종목 카드 — 클릭 시 종목 분석 페이지 진입, FR-5)                │
│                                                                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                  │
│  │ 005930      │ │ 000660      │ │ 034730      │                  │
│  │ 삼성전자    │ │ SK하이닉스  │ │ SK          │                  │
│  │             │ │             │ │             │                  │
│  │ 시가총액    │ │ 시가총액    │ │ 시가총액    │                  │
│  │ ~조원       │ │ ~조원       │ │ ~조원       │                  │
│  └─────────────┘ └─────────────┘ └─────────────┘                  │
│                                                                      │
│  ─────────────────────────────────────────────────────────           │
│                                                                      │
│  ## 메뉴 둘러보기                                          (h2)      │
│  - **종목 분석** — 관심 기업의 재무 건강 + 시장 상황                │
│  - **시장 상태** — 시점별 시장 흐름                                  │
│  - **한계** — 본 시스템의 정직한 한계 안내                          │
│                                                                      │
│  [ ★ 종목 분석 시작 ]                                     (CTA 버튼) │
└─────────────────────────────────────────────────────────────────────┘
```

**컴포넌트 사용**: `ModelLimitBadge`, `SidebarNav`, `PageHeader`, 예시 종목
카드 (`TickerHeader` 간소 버전), CTA 버튼.

**매핑**: FR-5 (둘러보기 가이드) + UC-1 (첫 진입 5 초) + UC-6 (메뉴 둘러보기).

### 1.2 종목 분석 (Ticker Analysis) — `app/pages/ticker_analysis.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚠️ 본 시스템은 시연용 데모입니다. 실제 투자에 사용 금지.            │  ← ModelLimitBadge
├─────────────────────────────────────────────────────────────────────┤
│ [Sidebar]                          │ [Main]                          │
│                                    │                                  │
│  종목 검색                          │  ## TickerHeader                │
│  ┌────────────────────┐            │  005930 삼성전자                │
│  │ 종목명 또는 코드   │            │  시가총액: 412 조원              │
│  └────────────────────┘            │                                  │
│  (자동완성 5 개 이내)               │  ─────────────────────────       │
│                                    │                                  │
│  분석 시점                          │  ## 4 핵심 카드                 │
│  ┌────────────────────┐            │  ┌────────┐ ┌────────┐         │
│  │ 2024-12-31 (최신)  ▼│            │  │ 재무   │ │ 시장   │         │
│  └────────────────────┘            │  │ 건강   │ │ 상태   │         │
│  ⚠️ 2019-12-30 (분석 평가 제외)    │  │        │ │        │         │
│                                    │  │ 양호   │ │ 위험   │         │
│                                    │  │ (green)│ │ 회피   │         │
│                                    │  │        │ │ (red)  │         │
│                                    │  └────────┘ └────────┘         │
│                                    │  ┌────────┐ ┌────────┐         │
│                                    │  │ 통합   │ │ 위험   │         │
│                                    │  │ 리스크 │ │ 점수   │         │
│                                    │  │        │ │        │         │
│                                    │  │ 중간   │ │ 13.6%  │         │
│                                    │  │ (oran) │ │ (oran) │         │
│                                    │  └────────┘ └────────┘         │
│                                    │                                  │
│                                    │  ## 해석 박스 (info banner)     │
│                                    │  ℹ️ 위험회피 시장 상태에서 양호  │
│                                    │     재무는 비교적 안정적입니다. │
│                                    │     단, 시장 전반의 위기 인식이 │
│                                    │     기업 평가에도 영향을 줄 수  │
│                                    │     있습니다. (LLM 서술)         │
│                                    │                                  │
│                                    │  ## 주가 + 시장 상태 차트       │
│                                    │  (PriceChartWithStateOverlay)   │
│                                    │  [시점별 색상 overlay]           │
│                                    │                                  │
│                                    │  ## 재무 비율 4 추이             │
│                                    │  (RatioGrid 2×2)                │
│                                    │  [부채비율·유동비율·ROE·매출]   │
│                                    │                                  │
│                                    │  ─────────────────────────       │
│                                    │  다음 단계:                      │
│                                    │  [한계 보기] [다른 종목 보기]    │
└─────────────────────────────────────────────────────────────────────┘
```

**컴포넌트 사용**: `ModelLimitBadge`, `SidebarNav`, `TickerHeader`,
`RiskScoreCard`, `StateCard`, `StateInterpretBox`,
`PriceChartWithStateOverlay`, `RatioGrid`, `EmptyState` (시점 평가 제외 시).

**매핑**: FR-1·FR-4·FR-7 + NFR-1·2·3·4·5·6 + UC-2·UC-4.

### 1.3 시장 상태 (Market State) — `app/pages/market_state.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚠️ 본 시스템은 시연용 데모입니다. 실제 투자에 사용 금지.            │  ← ModelLimitBadge
├─────────────────────────────────────────────────────────────────────┤
│ [Sidebar]                                                            │
│  - 개요                                                              │
│  - 종목 분석                                                         │
│  - 시장 상태 ●                                                       │
│  - 한계                                                              │
├─────────────────────────────────────────────────────────────────────┤
│  # 시장 상태 시계열                                        (h1)      │
│                                                                      │
│  본 시스템은 한국 KOSPI200 시장의 흐름을 *위험회피·중립·위험선호*    │
│  3 상태로 분류합니다. 위기 시점이 색상으로 강조됩니다.    (body)     │
│                                                                      │
│  ─────────────────────────────────────────────────────────           │
│                                                                      │
│  ## 시점별 색상 시각화                                     (h2)      │
│  ┌─────────────────────────────────────────────────────┐            │
│  │  [시장 상태 색상 stripe 차트]                       │            │
│  │  2015 ─── 2017 ─── 2019 ─── 2021 ─── 2023 ─── 2024  │            │
│  │  (위험회피=red, 중립=gray, 위험선호=green)           │            │
│  └─────────────────────────────────────────────────────┘            │
│                                                                      │
│  → 위기 시점 (예: 2020 코로나) hover → 한국어 설명                  │
│                                                                      │
│  ## 위기 시점 (info box)                                  (h2)      │
│  ℹ️ 위험회피 시장 상태는 *안전 자산 선호가 늘어나는* 시점.          │
│     예: 2020-02~04 코로나 충격 시점, 2022-09~10 금리 충격 시점.     │
│     (일반인 해석)                                                    │
│                                                                      │
│  ⚠️ 분석 시작 9 개월간 (2015-01 ~ 2015-09) 은 시장 상태 분류         │
│     정확도가 낮습니다. 이 기간은 *부분 표시* 또는 *경고* 로 안내    │
│     됩니다.                                                          │
└─────────────────────────────────────────────────────────────────────┘
```

**컴포넌트 사용**: `ModelLimitBadge`, `SidebarNav`, `PageHeader`, 색상
stripe 차트 (state 토큰 사용), `StateInterpretBox`.

**폐기**: 전이 행렬, HMM 시드 분산 (FR-9 Won't 직접 매핑, 2 단계 §2.2 결정).

**매핑**: FR-2·FR-3 + NFR-1·2·3·4·6 + UC-3.

### 1.4 한계 (Limitations) — `app/pages/limitations.py`

```
┌─────────────────────────────────────────────────────────────────────┐
│ ⚠️ 본 시스템은 시연용 데모입니다. 실제 투자에 사용 금지.            │  ← ModelLimitBadge
├─────────────────────────────────────────────────────────────────────┤
│ [Sidebar]                                                            │
│  - 한계 ●                                                            │
├─────────────────────────────────────────────────────────────────────┤
│  # 본 시스템의 한계                                        (h1)      │
│                                                                      │
│  본 시스템은 *방법론과 데이터의 정직성 시연*용입니다. 다음 3 가지   │
│  한계를 명확히 안내합니다.                                (body)     │
│                                                                      │
│  ─────────────────────────────────────────────────────────           │
│                                                                      │
│  ## 1. 모델 위험 예측 정확도                              (h2)      │
│  본 시스템의 위험 예측은 실제 사건을 거의 맞히지 못합니다. 본       │
│  시스템은 *방법론과 데이터의 정직성 시연*용입니다.                  │
│                                                                      │
│  ## 2. 시장 상태 분류 초기 9 개월                         (h2)      │
│  분석 시작 9 개월간 (2015-01 ~ 2015-09) 은 시장 상태 분류 정확      │
│  도가 낮습니다. 이 기간은 *부분 표시* 또는 *경고* 로 안내합니다.    │
│                                                                      │
│  ## 3. 분석 범위                                          (h2)      │
│  한국 KOSPI200 (한국 대표 200 대 기업) 만 분석합니다. 그 외 종목    │
│  은 *데이터 없음* 으로 표시됩니다.                                  │
│                                                                      │
│  ─────────────────────────────────────────────────────────           │
│                                                                      │
│  ## 데모 명시                                              (h2)      │
│  ⚠️ **본 시스템은 시연용 데모입니다. 실제 투자에 사용 금지.**       │
│                                                                      │
│  ─────────────────────────────────────────────────────────           │
│                                                                      │
│  ## 기술 자료 (별도 노출)                                  (h2)      │
│  - [reports/d2_baseline_model_card.md] — 위험 예측 모델 상세        │
│  - [reports/regime_model_card.md] — 시장 상태 분류 모델 상세        │
│  (기술 차원 문서, 일반인 직접 노출 본문 아님)                       │
└─────────────────────────────────────────────────────────────────────┘
```

**컴포넌트 사용**: `ModelLimitBadge`, `SidebarNav`, `PageHeader`.

**매핑**: FR-3 + NFR-2·4 + UC-5.

---

## 2. 컴포넌트 상세 spec (10 컴포넌트)

> 이름 정정 4 (RegimeCard → StateCard / RegimeConditionalBox →
> StateInterpretBox / ModelLimitWarning → ModelLimitBadge /
> PriceChartWithRegime → PriceChartWithStateOverlay) + 기존 6.
> 2 단계 §4 디자인 시스템 토큰 직접 사용.

### 2.1 `PageHeader` (`app/components/header.py`)

| 항목 | 값 |
|---|---|
| 입력 | `title: str`, `subtitle: str | None = None` |
| 출력 | 상단 페이지 헤더 (h1 + caption) |
| 동작 | st.markdown + 타이포 토큰 적용 |
| 토큰 | `text.h1`, `text.caption`, `text.primary`, `text.secondary` |

### 2.2 `TickerHeader` (`app/components/header.py`)

| 항목 | 값 |
|---|---|
| 입력 | `ticker_code: str`, `ticker_name: str`, `market_cap: float | None` |
| 출력 | 종목 코드 + 이름 + 시가총액 헤더 |
| 동작 | format: "005930 삼성전자" + 시가총액 (포맷팅: `format_won`) |
| 토큰 | `text.h2`, `text.caption` |

### 2.3 `RiskScoreCard` (`app/components/metric_card.py`)

| 항목 | 값 |
|---|---|
| 입력 | `proba: float | None`, `label: str = "위험 점수"` |
| 출력 | Metric Card — 위험 확률 + 3 단계 분류 (낮음/중간/높음) |
| 동작 | `classify_risk(proba)` 호출 → 색상 + 라벨 결정. 0.0136 같은 원본 4 자리 소수점 노출 *금지* — "13.6%" 또는 "낮음/중간/높음" 표시 |
| 토큰 | `risk.high`·`risk.medium`·`risk.low`, `text.metric_value`, `text.metric_label` |
| 매핑 | 1 단계 §7.1 (a) 한계 + 2 단계 §4.6 숫자 표기 |

### 2.4 `StateCard` (← RegimeCard) (`app/components/metric_card.py`)

| 항목 | 값 |
|---|---|
| 입력 | `state: str` ("risk_off" / "neutral" / "risk_on") |
| 출력 | Metric Card — 시장 상태 + 한국어 라벨 ("위험회피" / "중립" / "위험선호") |
| 동작 | state → token + 한국어 라벨 매핑 |
| 토큰 | `state.risk_off`·`state.neutral`·`state.risk_on`, `text.metric_value` |
| 정정 | 이름 RegimeCard → StateCard (2 단계 §4.1 토큰명 정정 일관) |

### 2.5 `PriceChartWithStateOverlay` (← PriceChartWithRegime) (`app/components/chart.py`)

| 항목 | 값 |
|---|---|
| 입력 | `ohlcv: pd.DataFrame`, `state_series: pd.DataFrame`, `as_of: pd.Timestamp | None` |
| 출력 | Plotly 차트 — 주가 (line) + 시장 상태 (color stripe overlay) |
| 동작 | `find_close_column(ohlcv)` 으로 종가 컬럼 식별. `compute_state_blocks(state_series)` 으로 색상 stripe 구간 계산. `as_of` 시점 vline (`to_pydatetime()` 적용, §5.9 학습) |
| 토큰 | `state.*`, `text.body` |
| 정정 | 이름 PriceChartWithRegime → PriceChartWithStateOverlay + 함수 `compute_regime_blocks` → `compute_state_blocks` |

### 2.6 `RatioGrid` (`app/components/chart.py`) — 그대로 재사용

| 항목 | 값 |
|---|---|
| 입력 | `ratios: pd.DataFrame` (date × {debt_ratio·current_ratio·roe·revenue}) |
| 출력 | 2×2 Plotly subplot — 4 재무 비율 추이 |
| 동작 | 각 subplot 별 line chart + as_of vline (`to_pydatetime()` 적용) |
| 토큰 | `text.body`, `text.caption` |

### 2.7 `StateInterpretBox` (← RegimeConditionalBox) (`app/components/interpretation.py`)

| 항목 | 값 |
|---|---|
| 입력 | `state: str`, `risk_level: str` ("low"/"medium"/"high"), `llm_text: str | None` |
| 출력 | Info Box — 시장 상태 + 위험 수준 조건부 한국어 해석 |
| 동작 | state × risk_level 9 조합 template + LLM 서술 합성. 모든 template *§5 (1) 부속 박제 부합* (ML 차원 의미 사라진 일반 차원 표현) |
| 토큰 | `info.banner`, `info.text` |
| 정정 | 이름 RegimeConditionalBox → StateInterpretBox + 본문 전면 재작성 |

### 2.8 `ModelLimitBadge` (← ModelLimitWarning) (`app/components/warning.py`)

| 항목 | 값 |
|---|---|
| 입력 | `variant: str` ("badge" / "modal" / "page_full") |
| 출력 | 한계 배지 (모든 페이지 상단) / 첫 진입 모달 / Limitations 페이지 전체 본문 |
| 동작 | **본문** = 1 단계 §7.1 (a) + §7.2 (iii) 결합: "본 시스템의 위험 예측은 실제 사건을 거의 맞히지 못합니다. 본 시스템은 시연용 데모입니다. 실제 투자에 사용 금지." 원본 ML 수치 (예: 이전 "PR-AUC 0.0136 < base rate 0.0205") 노출 *금지* |
| 토큰 | `warning.banner`, `warning.text` |
| 정정 | 이름 ModelLimitWarning → ModelLimitBadge + 본문 전면 재작성 (§5 (1) 부속 박제 직접 적용) |

### 2.9 `EmptyState` (`app/components/warning.py`)

| 항목 | 값 |
|---|---|
| 입력 | `message: str = "이 시점은 평가 자료 부족으로 분석 제외"`, `suggestion: str | None = None` |
| 출력 | Empty State 박스 (📭 아이콘 + 안내 + 다음 행동) |
| 동작 | 빈 상태 메시지 + suggestion (예: "다른 시점 선택") |
| 토큰 | `bg.surface`, `text.secondary` |
| 정정 | 기본 메시지 "skipped fold — 양성 0" → "이 시점은 평가 자료 부족으로 분석 제외" |

### 2.10 `SidebarNav` (`app/components/navigation.py`)

| 항목 | 값 |
|---|---|
| 입력 | `current_page: str` |
| 출력 | 사이드바 메뉴 4 페이지 (개요·종목 분석·시장 상태·한계) |
| 동작 | current_page 강조 + 페이지 이동 link |
| 토큰 | `text.body`, `bg.surface` |
| 정정 | 메뉴 5 → 4 (D2 baseline 별도 페이지 폐기, 모델 카드 link 만 한계 페이지에) |

---

## 3. UI 본문 텍스트 (Copy) — §5 (1) 부속 박제 부합 검증

> 각 페이지·컴포넌트의 한국어 본문 텍스트. 모든 본문 *ML 차원 의미 자체가
> 사라진 일반 차원 표현* (`§5` (1) 부속 박제 부합).

### 3.1 사이드바·네비게이션

| 위치 | 본문 |
|---|---|
| 메뉴 항목 | "개요" / "종목 분석" / "시장 상태" / "한계" |
| 현재 페이지 표시 | "● 현재 페이지" |

### 3.2 메트릭 카드 라벨

| 카드 | 라벨 | 값 표시 |
|---|---|---|
| 재무 건강 | "재무 건강" | "양호" / "주의" / "위험" 3 단계 |
| 시장 상태 | "시장 상태" | "위험회피" / "중립" / "위험선호" |
| 통합 리스크 | "통합 리스크" | "낮음" / "중간" / "높음" 3 단계 |
| 위험 점수 | "위험 점수" | "13.6%" 또는 "낮음/중간/높음" 3 단계 |

### 3.3 상태 메시지

| 상태 | 본문 |
|---|---|
| 분석 평가 제외 시점 | "이 시점은 평가 자료 부족으로 분석 제외" |
| universe 범위 밖 종목 | "이 종목은 분석 시점 범위 밖" |
| 데이터 산출물 부재 (일반인 모드) | "준비 중" |
| LLM 해석 준비 중 | "해석 준비 중" |
| 분석 시작 9 개월간 | "분석 시작 9 개월간은 시장 상태 분류 정확도가 낮음" |

### 3.4 한계·경고 (`ModelLimitBadge`)

| 위치 | 본문 |
|---|---|
| 배지 (모든 페이지 상단) | "⚠️ 본 시스템은 시연용 데모입니다. 실제 투자에 사용 금지." |
| 첫 진입 모달 | (배지 본문 동일) |
| 한계 페이지 전체 | "본 시스템의 위험 예측은 실제 사건을 거의 맞히지 못합니다. 본 시스템은 *방법론과 데이터의 정직성 시연*용입니다." + 3 한계 항목 + 데모 명시 |

### 3.5 해석 박스 (`StateInterpretBox`) template 9 조합

> 시장 상태 (3) × 위험 수준 (3) = 9 조합. 모두 *§5* (1) 부속 박제 부합.

| 시장 상태 | 위험 낮음 | 위험 중간 | 위험 높음 |
|---|---|---|---|
| 위험회피 | "위험회피 시장 상태에서 양호 재무는 비교적 안정적입니다." | "위험회피 시장 상태에서 중간 위험 수준은 추가 관찰이 필요합니다." | "위험회피 시장 상태에서 높은 위험 수준은 신중한 검토가 필요합니다." |
| 중립 | "중립 시장 상태에서 양호 재무는 안정적입니다." | "중립 시장 상태에서 중간 위험 수준은 일반적 범주에 속합니다." | "중립 시장 상태에서 높은 위험 수준은 주의가 필요합니다." |
| 위험선호 | "위험선호 시장 상태에서 양호 재무는 매우 안정적입니다." | "위험선호 시장 상태에서 중간 위험 수준은 시장 흐름에 영향을 받을 수 있습니다." | "위험선호 시장 상태에서 높은 위험 수준은 시장 회복 시에도 주의가 필요합니다." |

(LLM 빌드타임 배치 서술 1 단락 추가 — FR-7 매핑)

### 3.6 시가총액 caption

- format: "시가총액: 412 조원" (3 자리 콤마 + 한국어 단위)

---

## 4. 시각 디자인 토큰 적용 (2 단계 `§4` → 페이지 적용)

> 2 단계 `docs/ux_design.md §4` 디자인 시스템 토큰의 페이지·컴포넌트 적용.

| 토큰 | 적용 위치 |
|---|---|
| `state.risk_off`·`state.neutral`·`state.risk_on` | `StateCard`, `PriceChartWithStateOverlay`, 시장 상태 페이지 색상 stripe |
| `risk.high`·`risk.medium`·`risk.low` | `RiskScoreCard` 색상 코딩 |
| `warning.banner`·`warning.text` | `ModelLimitBadge` (모든 페이지 상단 + 첫 진입 모달 + 한계 페이지) |
| `info.banner`·`info.text` | `StateInterpretBox` 9 template + 시장 상태 페이지 위기 시점 해석 |
| `text.h1`·`text.h2`·`text.h3` | 페이지 제목 + 섹션 제목 |
| `text.body`·`text.caption` | 본문 + 메타·각주 |
| `text.metric_value`·`text.metric_label` | `RiskScoreCard`·`StateCard` |
| `text.korean` (line-height 1.6) | 모든 한국어 본문 |
| 간격 (8px multiple) | 모든 컴포넌트 |
| 한국어 폰트 우선순위 (Pretendard → Apple SD Gothic Neo → system-ui) | 전역 |

---

## 5. ★ 단계 5 (구현) 진입 시 검증 의무 박제 (자문 추가 짚을 점 4 항목)

> 본 §5 박제가 단계 5 구현 시 *자동 적용 체크리스트*. 단계 5 진입 직전
> §7.6 게이트의 *§7.6.3* 코드 재읽기 단계에서 본 §5 4 항목 자기 적용 의무.

### (검증 1) 토큰명 `regime.*` → `state.*` 코드 일관 정정

토큰명 + **컴포넌트 이름** + **함수 이름** + **변수 이름** + **파일명**
모두 일관 적용. 단계 5 진입 시 `grep regime` 전체 코드 베이스 검증 (UI
코드 + 데이터 처리 코드 + 테스트 코드 + 설정 파일) 의무.

본 검증의 깊은 적용: 2 단계에서 *토큰명* 만 정정으로 보았으나 `Code` 자기
발견 (3 단계 outline) — 컴포넌트 이름 (RegimeCard, RegimeConditionalBox,
PriceChartWithRegime, compute_regime_blocks 함수, regime_label 변수 등)
까지 *일관 정정 의무*. 본 §5 (검증 1) 가 단계 5 자동 적용 체크리스트.

### (검증 2) D2 baseline 별도 페이지 폐기 + 모델 카드 link 만 유지

- `app/pages/d2_results.py` 신설 *금지*
- 모델 카드 link (`reports/d2_baseline_model_card.md`) 는 *Limitations
  페이지* 에 link 만 유지
- 단계 5 진입 시 `app/pages/` 디렉토리에 `d2_results.py` 존재 검증 (있으면
  본 검증 (2) 위반)

### (검증 3) 시장 상태 페이지의 전이 행렬·HMM 시드 분산 부분 폐기

- `app/pages/market_state.py` (← `regime_timeline.py` 이름 정정) 의 해당
  섹션 신설 *금지*
- 단계 5 진입 시 `app/pages/market_state.py` 본문에 `transition`,
  `HMM`, `seed`, `시드` 등 키워드 grep 검증 (있으면 본 검증 (3) 위반)

### (검증 4) `§5` (1) 부속 박제의 UI 코드 차원 적용 (ML 용어 + 번역어 원본 노출 0)

자동 grep 검사 — UI 코드 (`app/**/*.py`) + 렌더링 결과에 다음 키워드 잔존 0:

- 원본 영문 ML 용어: `PR-AUC`, `ROC-AUC`, `Brier`, `walk-forward`,
  `embargo`, `HMM`, `K-Means`, `K-Modes`, `log-likelihood`, `ablation`,
  `class weight`, `fold`, `skipped`, `regime`, `bootstrap`, `SMOTE`,
  `forward window`, `lookback`, `seed`
- 번역어 (`§5` (1) 부속 박제 위반): `시간 분할 학습`, `평가 곡선 면적`,
  `재현율 곡선 면적`, `시드`, `편차 부트스트랩` 등 (`§5` (1) 부속 박제 의
  *번역어가 ML 차원 의미 보존* 경우)

단계 5 진입 시 본 grep 자동 검사 + 발견 시 즉시 정정 의무.

---

## 6. 매핑 표 7 차원 (신설, 정합성 검사)

> 자문 권장 `§6` 신설. 페이지 ↔ 컴포넌트 ↔ UI Copy ↔ 토큰 ↔ FR ↔ NFR ↔
> UC 7 차원 매핑 누락 0 검증.

| 페이지 (§1) | 컴포넌트 (§2) | UI Copy (§3) | 토큰 (§4) | 1단계 FR | 1단계 NFR | 1단계 UC |
|---|---|---|---|---|---|---|
| 1.1 개요 | `ModelLimitBadge`·`SidebarNav`·`PageHeader`·예시 종목 카드·CTA | §3.1 메뉴·§3.4 배지·5 초 카피·예시 종목 caption | `state`·`risk`·`text`·`bg`·`warning` | FR-3·FR-5 | NFR-1·2·3·4·6 | UC-1·UC-6 |
| 1.2 종목 분석 | `ModelLimitBadge`·`SidebarNav`·`TickerHeader`·`RiskScoreCard`·`StateCard`·`StateInterpretBox`·`PriceChartWithStateOverlay`·`RatioGrid`·`EmptyState` | §3.2 카드 라벨·§3.3 상태 메시지·§3.4 배지·§3.5 해석 9 template·§3.6 시가총액 | `state`·`risk`·`warning`·`info`·`text`·`bg` | FR-1·FR-3·FR-4·FR-5·FR-7 | NFR-1·2·3·4·5·6 | UC-2·UC-4 |
| 1.3 시장 상태 | `ModelLimitBadge`·`SidebarNav`·`PageHeader`·색상 stripe 차트·`StateInterpretBox` | §3.3 분석 시작 9 개월·§3.4 배지·위기 시점 해석 | `state`·`warning`·`info`·`text` | FR-2·FR-3 | NFR-1·2·3·4·6 | UC-3 |
| 1.4 한계 | `ModelLimitBadge`·`SidebarNav`·`PageHeader` | §3.4 한계 페이지 전체 본문 (3 한계 + 데모 명시 + 모델 카드 link) | `warning`·`info`·`text` | FR-3 | NFR-2·4 | UC-5 |

**매핑 누락 = 0** ✅ (모든 페이지 = ≥ 1 컴포넌트 + ≥ 1 copy + ≥ 1 토큰 +
≥ 1 FR + ≥ 1 NFR + ≥ 1 UC).

**메타 (자문 보강)**: 본 매핑 표는 단계 5 구현 진입 시 *페이지·컴포넌트
단위 구현 체크리스트* 로 변환 가능. 1 단계 `§9` 정합성 검사 + 2 단계 `§6`
매핑 표 + 본 3 단계 `§6` 매핑 표 (7 차원) 의 *단계별 본질 차원 분리 정신*
직접 적용.

---

## 7. 다음 단계 (단계 4 입력)

본 3 단계 산출물은 다음 단계의 직접 입력:

| 단계 | 산출물 | 본 문서에서 직접 입력 |
|---|---|---|
| 4 | `docs/tech_architecture.md` (에러·성능 정책) | `§5` 단계 5 검증 의무 4 항목 + `§2` 컴포넌트 spec + `§1` 페이지 와이어프레임 의 *에러·성능 정책* 차원 |
| 5 | 구현 (컴포넌트 단위) | 본 문서 전체 — `§1` 와이어프레임 + `§2` 컴포넌트 spec + `§3` UI Copy + `§4` 토큰 적용 + `§5` 검증 의무 자동 체크리스트 + `§6` 매핑 표 |
| 6 | `docs/qa_checklist.md` | `§5` 검증 의무 4 항목 + `§6` 매핑 표 (페이지·컴포넌트 단위 QA 체크리스트) + 2 단계 `§5` (1) 일반인 ≥ 3 명 5 초 이해 검증 |
