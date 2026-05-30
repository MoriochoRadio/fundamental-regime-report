# UI Components — 페이지 와이어프레임 · 컴포넌트 명세 · 한국어 UX 카피

**버전**: v1 (2026-05-21, Phase 3 산출물)
**상태**: 사용자 검토 대기 → Phase 4 구현 입력
**관련**: `docs/ux_design.md` (Phase 2 산출물)

본 문서는 UX 설계 (페르소나·시나리오·디자인 시스템) 의 *실재 구현 명세*. Phase 4
구현 시 각 컴포넌트가 본 문서의 *props·상태·이벤트* 정확히 따르도록 강제.

---

## 0. 디렉토리 구조 (Phase 4 입력)

```
app/
├── main.py                       # slim entry, 라우팅·page_config 만
├── data_loader.py                # 기존 (확장 유지)
├── components/                   # 신규 — 재사용 컴포넌트
│   ├── __init__.py
│   ├── header.py                 # PageHeader, TickerHeader
│   ├── metric_card.py            # RiskScoreCard, RegimeCard, ...
│   ├── chart.py                  # PriceChartWithRegime, RatioGrid, ...
│   ├── interpretation.py         # RegimeConditionalBox
│   ├── warning.py                # ModelLimitWarning, EmptyState
│   └── navigation.py             # SidebarNav (page selector)
├── pages/                        # 신규 — 페이지 분리
│   ├── __init__.py
│   ├── overview.py               # render_overview
│   ├── ticker_analysis.py        # render_ticker_analysis
│   ├── regime_timeline.py        # render_regime_timeline
│   ├── d2_results.py             # render_d2_results
│   └── limitations.py            # render_limitations
└── utils/                        # 신규 — 포매팅·매핑
    ├── __init__.py
    ├── formatters.py             # format_won, format_percent, ...
    └── regime_mapper.py          # lookup_regime_at (영업일 매핑)
```

**원칙**:
- `main.py` = 라우팅 + page_config 만 (50줄 미만)
- `components/` = stateless presentational (Streamlit primitive wrapper)
- `pages/` = data loading + components 조합 (페이지별 1 함수)
- `utils/` = pure function (테스트 용이)

---

## 1. 컴포넌트 명세

### 1.1 `PageHeader` (components/header.py)

**역할**: 페이지 진입 헤더 — 제목 + 부제 + 핵심 가치 1 줄

**Props**:
| name | type | default | 의미 |
|---|---|---|---|
| `title` | str | required | h1 제목 |
| `subtitle` | str | None | h3 부제 (선택) |
| `value_message` | str | None | 핵심 가치 1 줄 (info banner) |

**Streamlit 구현**:
```python
def render_page_header(title: str, subtitle: str | None = None,
                      value_message: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.markdown(f"### {subtitle}")
    if value_message:
        st.info(value_message)
```

### 1.2 `TickerHeader` (components/header.py)

**역할**: 종목 분석 페이지 상단 — 종목코드·이름·시총·fs_div 4 요소

**Props**:
| name | type | required | 의미 |
|---|---|---|---|
| `ticker` | str | ✓ | 6자리 종목코드 |
| `name` | str | ✓ | 종목명 |
| `marcap` | float \| None | ✗ | 시가총액 (현시점) |
| `fs_div` | str \| None | ✗ | CFS/OFS/absent |

**Streamlit 구현**:
```python
def render_ticker_header(ticker, name, marcap=None, fs_div=None):
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("종목코드", ticker)
    col2.metric("종목명", name)
    col3.metric("시가총액 (현시점)", format_won(marcap))
    col4.metric("재무 출처", fs_div or "—")
    st.caption(
        "ℹ️ 시가총액은 현재 시점 스냅샷 (FDR). 과거 시점 시총 추적은 본 "
        "프로젝트 범위 밖입니다."
    )
```

### 1.3 `RiskScoreCard` (components/metric_card.py)

**역할**: D2 위험 확률 색상 코딩 표시

**Props**:
- `proba: float | None` — 0~1 또는 None (skipped fold)
- `class_weight: str` — "balanced" or "unweighted"

**색상 매핑** (디자인 시스템 §7.1):
- proba ≥ 0.5 → `risk.high` (red), 라벨 "높음"
- 0.1 ≤ proba < 0.5 → `risk.medium` (orange), 라벨 "중간"
- proba < 0.1 → `risk.low` (green), 라벨 "낮음"
- None → 회색, "평가 제외 시점"

**Streamlit 구현**:
```python
def render_risk_score_card(proba: float | None, class_weight: str):
    if proba is None:
        st.metric("D2 위험 확률", "—")
        st.caption("⚠️ 평가 제외 시점 (양성 0 인 fold)")
        return

    level, color = classify_risk(proba)  # (label, hex)
    st.metric(
        "D2 위험 확률",
        f"{proba:.4f}",
        delta=f"{level} ({class_weight})",
        delta_color="off",  # color는 markdown 으로
    )
    st.markdown(
        f"<div style='color:{color}; font-weight:bold;'>● {level}</div>",
        unsafe_allow_html=True,
    )
```

### 1.4 `RegimeCard` (components/metric_card.py)

**Props**: `regime: str | None`

**Streamlit 구현**:
```python
def render_regime_card(regime: str | None):
    if regime is None:
        st.metric("시장 국면", "—")
        st.caption("ℹ️ Warmup 기간 (2015 초반) 또는 시점 외")
        return
    color = REGIME_COLORS.get(regime, "#888")
    st.metric("시장 국면", regime)
    st.markdown(
        f"<div style='color:{color}; font-weight:bold;'>● {regime}</div>",
        unsafe_allow_html=True,
    )
```

### 1.5 `PriceChartWithRegime` (components/chart.py)

**역할**: 주가 line + regime 배경 색상 overlay + 분석 시점 vline

**Props**:
- `ticker: str`
- `name: str`
- `ohlcv: pd.DataFrame` — index=날짜, "종가" 컬럼
- `state_series: pd.DataFrame | None` — date·state_label
- `as_of: pd.Timestamp` — 분석 시점 (vline 위치)

**구현 핵심**:
- close 컬럼 자동 식별 (cp949 "종가" 또는 "Close")
- `ohlcv.reset_index()` 후 date column 식별
- `add_vrect` 로 regime block (contiguous group)
- `add_vline` 분석 시점 — `as_of.to_pydatetime()` 변환 (§5.9 학습)
- `add_annotation` 별도 호출 (annotation_text 인자 미사용)

**상태**:
- ohlcv None → empty state
- close 컬럼 식별 실패 → empty state + 에러 안내
- state_series None → 배경 색상 생략, line 만 표시

### 1.6 `RatioGrid` (components/chart.py)

**역할**: 재무 비율 4 (debt_ratio·current_ratio·op_margin·roa) 2×2 subplot

**Props**:
- `ticker_features: pd.DataFrame` — as_of 정렬, 4 ratio 컬럼
- `as_of: pd.Timestamp` — vline 위치
- `name: str`

**구현 핵심**:
- `plotly.subplots.make_subplots(2, 2)`
- 각 ratio 별 line + markers + vline (`as_of.to_pydatetime()`)
- y축 자동 스케일 (각 ratio 별 다름)
- 빈 비율 (NaN) 은 자동 gap

**상태**:
- features 빈 DataFrame → empty state
- 일부 ratio NaN → 차트는 표시, gap 자동

### 1.7 `RegimeConditionalBox` (components/interpretation.py)

**역할**: 국면 × ratio × ticker 통합 해석 (C-4 v1 — static template)

**Props**:
- `regime: str | None`
- `ticker_features: pd.Series | None` — 4 ratio 값
- `ticker_name: str`

**규칙** (Phase 3 v1, static):

| 국면 | 핵심 메시지 |
|---|---|
| 위험회피 | 시장 위기 — 부채비율 상승·영업이익 둔화의 *부실 신호 해석이 강화*. 단 본 모델 random 미만 → 가이드만. |
| 위험선호 | 시장 상승 — 동일 약화 신호가 *전반 회복세에 가려질 수 있음*. 신호 누락 주의. |
| 중립 | 전이 교차로 — 위험회피 전환 확률 0.925. 재무 변화를 *전이 신호*로 함께. |
| None | 매핑 불가 (warmup) — 시점 외 또는 데이터 없음. |

**Streamlit 구현**:
```python
def render_regime_conditional_box(regime, ticker_features, ticker_name):
    text = _build_interpretation(regime, ticker_features, ticker_name)
    st.info(text)
```

### 1.8 `ModelLimitWarning` (components/warning.py)

**역할**: 모든 페이지 적용 가능한 모델 한계 경고 (red banner)

**Props**:
- `context: Literal["ticker", "regime", "d2", "limitations"] = "ticker"`
  — context 별 문구 조정

**Streamlit 구현**:
```python
def render_model_limit_warning(context="ticker"):
    msg = LIMIT_MESSAGES.get(context, LIMIT_MESSAGES["ticker"])
    st.error(msg)
```

**LIMIT_MESSAGES**:
```python
LIMIT_MESSAGES = {
    "ticker": (
        "⚠️ **본 모델은 random 미만 성능** (PR-AUC 0.0136 < base rate 0.0205). "
        "위 위험 확률은 *해석 가이드일 뿐* — 실제 투자 판단·신용 평가 사용 금지."
    ),
    "regime": (
        "⚠️ 시장 국면은 *과거 데이터 사후 분석* 결과. *주가 예측 아님* "
        "(CLAUDE.md §3.2). 트레이딩 신호 사용 금지."
    ),
    ...
}
```

### 1.9 `EmptyState` (components/warning.py)

**역할**: 데이터 없음·skipped 시점·산출물 부재 상태

**Props**:
- `icon: str = "📭"`
- `title: str` — 큰 글씨 메시지
- `description: str | None` — 부연 설명
- `action: str | None` — 복구 방법 (예: 다른 시점 선택, 스크립트 실행)

**Streamlit 구현**:
```python
def render_empty_state(title, description=None, action=None, icon="📭"):
    st.markdown(f"### {icon} {title}")
    if description:
        st.caption(description)
    if action:
        st.info(f"💡 {action}")
```

### 1.10 `SidebarNav` (components/navigation.py)

**역할**: 사이드바 페이지 selector

**Props**: 없음 (현재 페이지는 session_state)

**Streamlit 구현**:
```python
PAGES = [
    ("개요", "overview"),
    ("★ 종목 분석", "ticker"),
    ("시장 국면", "regime"),
    ("D2 baseline 결과", "d2"),
    ("⚠️ Limitations", "limitations"),
]

def render_sidebar_nav() -> str:
    labels = [p[0] for p in PAGES]
    selected = st.sidebar.radio("페이지 선택", labels)
    return dict(PAGES)[selected]  # 'overview' 등
```

---

## 2. 페이지별 와이어프레임

### 2.1 개요 (Overview) — `pages/overview.py`

```
┌─────────────────────────────────────────────────────────────┐
│  기업 펀더멘털 + 시장 국면 인지형 통합 분석 리포트          │
│                                                             │
│  한국 KOSPI200 (point-in-time) 배치 분석                   │
│                                                             │
│  > 본 프로젝트는 negative finding (모델 random 미만) 을    │
│  > 정직 박제하며, 그 자체가 D2 정직성 사슬 5 차원 + §7.6   │
│  > 검토 사이클의 핵심 가치 입증입니다.                     │
└─────────────────────────────────────────────────────────────┘

┌─── ★ 정직성 사슬 5 차원 (시각화 카드 5개) ─────────────────┐
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│  │ 1.   │ │ 2.   │ │ 3.   │ │ 4.   │ │ 5.   │              │
│  │ 변수 │ │ 양성 │ │ 격리 │ │ 시간 │ │ LLM  │              │
│  │      │ │ 충분 │ │      │ │      │ │ 격리 │              │
│  │ §5.5.│ │ §5.5.│ │ test │ │ walk │ │ test │              │
│  │ 9    │ │ 10   │ │_iso  │ │_fwd  │ │_app  │              │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘              │
└─────────────────────────────────────────────────────────────┘

┌─── 단계별 진행 상태 (st.dataframe) ────────────────────────┐
│  단계         상태     박제 위치                            │
│  1. 데이터    ✅       data/raw, data/external             │
│  2. 펀더멘털  ✅       reports/d2_baseline_model_card.md   │
│  3. 시장 국면 ✅       reports/regime_model_card.md        │
│  4. 대시보드  🔄       app/ 본 대시보드                    │
│  5. 마무리    ✅       README.md, PROGRESS §5.8            │
└─────────────────────────────────────────────────────────────┘

┌─── CTA ─────────────────────────────────────────────────────┐
│  [★ 종목 분석 시작 →] (st.page_link or st.button)           │
│  종목을 선택해서 위험 점수·국면·재무 비율 통합 확인         │
└─────────────────────────────────────────────────────────────┘

┌─── 핵심 메시지 (3 cards) ───────────────────────────────────┐
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │ Negative     │ │ K=4 ablation │ │ 검토 사이클  │         │
│  │ finding 정직 │ │ 정량 정답    │ │ §7.6 박제    │         │
│  │ 박제         │ │ 발견         │ │              │         │
│  └──────────────┘ └──────────────┘ └──────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

**컴포넌트 사용**:
- `PageHeader(title, subtitle, value_message)`
- 사슬 5 차원 카드 — `st.columns(5)` + custom markdown
- 단계 표 — `st.dataframe`
- CTA — `st.button` (`on_click` → session_state page="ticker")

### 2.2 ★ 종목 분석 (Ticker Analysis) — `pages/ticker_analysis.py`

```
┌─────────────────────────────────────────────────────────────┐
│  [사이드바]                                                 │
│    페이지 선택 (radio)                                      │
│    ─────                                                    │
│    종목 분석 옵션:                                          │
│    🔍 종목 선택 (selectbox, 검색가능)                       │
│      └─ "005930 삼성전자" 형식                              │
│    📅 분석 시점 (selectbox)                                 │
│      └─ 최신부터, skipped 는 ⚠️ 마크                       │
│    ⚖️ class_weight ablation (radio)                         │
│      └─ balanced (기본) / unweighted                        │
└─────────────────────────────────────────────────────────────┘

┌─── 종목 헤더 (TickerHeader) ────────────────────────────────┐
│  [코드 005930]  [이름 삼성전자]  [시총 1,625 조원]  [CFS]   │
│  ℹ️ 시가총액은 현재 시점 스냅샷. 과거 시총 추적 범위 밖.   │
└─────────────────────────────────────────────────────────────┘

┌─── 핵심 지표 (4 columns) ──────────────────────────────────┐
│  [RiskScoreCard]      [RegimeCard]                          │
│   D2 위험 확률 0.034   시장 국면 위험회피                   │
│   ● 낮음 (balanced)   ● 위험회피                           │
│                                                             │
│  [LabelCard]          [FsDivCard]                           │
│   1년 forward 양성    재무 출처 CFS                         │
│   0                                                         │
└─────────────────────────────────────────────────────────────┘

┌─── 국면 조건부 해석 (RegimeConditionalBox) ────────────────┐
│  ℹ️ 현재 시장이 **위험회피 (위기)** 국면입니다.            │
│                                                             │
│  위험회피 국면에서는 *같은 부채비율 상승·영업이익 둔화* 가  │
│  *일반 시 대비 더 강한 부실 신호*로 해석될 수 있습니다.    │
│                                                             │
│  단 본 모델은 random 미만이라 *방향성 가이드만* 으로 사용. │
│                                                             │
│  해당 시점 종목 ratio: 부채비율 1.34 · 유동비율 2.10 ·      │
│  영업이익률 0.11 · ROA 0.08                                 │
└─────────────────────────────────────────────────────────────┘

┌─── 주가 + 시장 국면 overlay (PriceChartWithRegime) ────────┐
│  [plotly 차트, height 420]                                  │
│  - x: 날짜, y: 종가                                         │
│  - 배경: regime 색상 (위험회피=red·중립=gray·위험선호=green│
│         alpha 0.15)                                         │
│  - 점선: 분석 시점                                          │
│  - hover: 일자·종가·국면                                    │
│  배경 색상 범례: ● 위험회피 ● 중립 ● 위험선호               │
└─────────────────────────────────────────────────────────────┘

┌─── 재무 비율 추이 (RatioGrid 2×2) ─────────────────────────┐
│  ┌──────────────┐ ┌──────────────┐                          │
│  │ debt_ratio   │ │ current_ratio│                          │
│  │ [plotly line]│ │ [plotly line]│                          │
│  └──────────────┘ └──────────────┘                          │
│  ┌──────────────┐ ┌──────────────┐                          │
│  │ op_margin    │ │ roa          │                          │
│  │ [plotly line]│ │ [plotly line]│                          │
│  └──────────────┘ └──────────────┘                          │
│  점선: 분석 시점                                            │
└─────────────────────────────────────────────────────────────┘

┌─── 모델 한계 경고 (ModelLimitWarning) ─────────────────────┐
│  ⚠️ **본 모델은 random 미만 성능** (PR-AUC 0.0136 < base   │
│  rate 0.0205). 위 위험 확률은 *해석 가이드일 뿐* —          │
│  실제 투자 판단·신용 평가 사용 금지.                       │
│                                                             │
│  자세한 한계: [⚠️ Limitations 페이지]                       │
└─────────────────────────────────────────────────────────────┘
```

**컴포넌트 사용**:
- `TickerHeader` (1)
- `RiskScoreCard` + `RegimeCard` + 2 metric card (4)
- `RegimeConditionalBox` (1)
- `PriceChartWithRegime` (1)
- `RatioGrid` (1)
- `ModelLimitWarning(context="ticker")` (1)

**상태**:
- skipped fold 시점 → `RiskScoreCard(proba=None)` + `EmptyState` 부분 적용
- universe 비멤버 → `EmptyState(title="이 종목은 분석 시점 universe 멤버가 아님")`
- ohlcv 없음 → 차트 자리에 `EmptyState`

### 2.3 시장 국면 시계열 — `pages/regime_timeline.py`

```
┌─── PageHeader ──────────────────────────────────────────────┐
│  시장 국면 시계열 (HMM K=3)                                 │
│  ℹ️ KOSPI200 일간 지수 → 3 피처 (수익률·변동성·비율) →     │
│     HMM 학습 → 3 국면 분류.                                 │
└─────────────────────────────────────────────────────────────┘

┌─── 분포 + 색상 범례 ────────────────────────────────────────┐
│  위험선호 57.8%   중립 26.7%   위험회피 15.5%               │
│  ● red          ● gray       ● green                       │
└─────────────────────────────────────────────────────────────┘

┌─── 국면 시계열 (plotly scatter) ───────────────────────────┐
│  [전체 2,273 obs, 일간]                                     │
│  hover: 일자·국면 라벨                                      │
└─────────────────────────────────────────────────────────────┘

┌─── 전이 행렬 (st.dataframe + heatmap) ─────────────────────┐
│           위험회피    중립      위험선호                    │
│  위험회피  0.003     0.997     0.000                        │
│  중립      0.925     0.017     0.058                        │
│  위험선호  0.000     0.024     0.976                        │
│                                                             │
│  자기 지속성 강함. 중립이 위험회피로 전환 자주.            │
└─────────────────────────────────────────────────────────────┘

┌─── ★ K=4 Ablation 비교 (신규 추가 Phase 4) ────────────────┐
│  K=3 본 라인의 *명명 부합 약함* (위험회피 코로나 27.9%) →   │
│  K=4 ablation 정량 정답 발견 (위험회피 82%)                 │
│                                                             │
│  ┌────────────────────┬────────────┬────────────┐           │
│  │ 항목               │ K=3 (본)   │ K=4 (ablation)│        │
│  ├────────────────────┼────────────┼────────────┤           │
│  │ log-likelihood     │ -9442.92   │ -7640.05   │           │
│  │ BIC                │ 19,156.36  │ 15,674.28  │           │
│  │ 2020 코로나 위기   │ 27.9%      │ 82.0%      │           │
│  └────────────────────┴────────────┴────────────┘           │
│                                                             │
│  → 본 라인 K=3 유지 (학술 관행), K=4 는 *대안 시나리오*.   │
└─────────────────────────────────────────────────────────────┘

┌─── 도메인 spot-check (2020 코로나) ────────────────────────┐
│  2020-02-15 ~ 2020-05-15 (61 obs)                          │
│  중립 42.6% · 위험선호 29.5% · 위험회피 27.9%               │
│  (학술 명명 부합 약함 정직 박제 — §5.6.1)                   │
└─────────────────────────────────────────────────────────────┘

┌─── ModelLimitWarning(context="regime") ────────────────────┐
│  ⚠️ 시장 국면은 *과거 데이터 사후 분석* 결과.              │
│     *주가 예측 아님*. 트레이딩 신호 사용 금지.             │
└─────────────────────────────────────────────────────────────┘
```

### 2.4 D2 baseline 결과 — `pages/d2_results.py`

```
┌─── PageHeader ──────────────────────────────────────────────┐
│  D2 부실 라벨 baseline 결과                                 │
│  ⚠️ **Negative Finding 정직 박제** — 모델 random 미만       │
│     (PR-AUC 0.0136 < base rate 0.0205).                    │
│     §5.5.7 KOSPI200 부실 사건 희소성의 경험적 정량 증거.   │
└─────────────────────────────────────────────────────────────┘

┌─── 데이터 통계 (4 metric) ─────────────────────────────────┐
│  features 8,008  양성 45  평가 fold 9  skip fold 19         │
└─────────────────────────────────────────────────────────────┘

┌─── Full pooled — balanced ────────────────────────────────┐
│  [st.dataframe metric × value × 95% CI]                    │
│  caption: base rate ≈ 2.05% (37/1801)                       │
└─────────────────────────────────────────────────────────────┘

┌─── balanced vs unweighted ablation ───────────────────────┐
│  [st.dataframe class_weight × pr_auc·roc_auc·brier]         │
│  caption: 차이 < 0.001 → class weight 효과 양성 부족 무력. │
└─────────────────────────────────────────────────────────────┘

┌─── 지주 군 분리 평가 ──────────────────────────────────────┐
│  [2 columns]                                                │
│  지주 군 (3 종목):           │  일반 군 (지주 제외):       │
│   n_positive 12              │   n_positive 25            │
│   pr_auc 0.3281              │   pr_auc 0.0094            │
│   roc_auc 0.0778             │   roc_auc 0.2862           │
│                                                             │
│  caption: 지주 군 N=12 — Top-K CI [0,1] 완전 변동           │
└─────────────────────────────────────────────────────────────┘

┌─── (A) 데이터 보강 결과 ──────────────────────────────────┐
│  3,583 호출 · status 전환 0 · errors 0 · 16분               │
│  caption: notfound 가 실제 데이터 부재 (DART 직접 응답)     │
└─────────────────────────────────────────────────────────────┘

┌─── ModelLimitWarning(context="d2") ────────────────────────┐
│  ⚠️ 본 모델은 random 미만. 위 모든 수치는 *데이터 한계의   │
│     정량 증거*. 실거래·신용 평가 사용 금지.                │
└─────────────────────────────────────────────────────────────┘
```

### 2.5 ⚠️ Limitations — `pages/limitations.py`

```
┌─── PageHeader ──────────────────────────────────────────────┐
│  ⚠️ Limitations (방법론적 특징)                            │
│  본 페이지는 본 프로젝트의 **방법론적 특징 핵심**.          │
│  모든 한계가 *정직 박제* — 사용성 가치는 *negative finding │
│  의 정직성 + 정직성 사슬 5 차원 + 모집단 한계 정량 증명*.  │
└─────────────────────────────────────────────────────────────┘

┌─── 6 한계 항목 (각 expander) ──────────────────────────────┐
│  ▼ 1. 단계 2 — D2 baseline Negative Finding                 │
│       PR-AUC 0.0136 < base rate 0.0205                      │
│       ROC-AUC 0.2651 < 0.5                                  │
│       class weight ablation 효과 0                          │
│       ★ 박제: §5.5.17 + d2_baseline_model_card.md           │
│                                                             │
│  ▼ 2. (A) 데이터 보강 — Strong Negative Evidence            │
│       notfound 3,583 OFS 재페치 → status 전환 0             │
│       DART 직접 응답 = 실제 데이터 부재                     │
│       ★ 박제: §5.5.17 (A) 단락                              │
│                                                             │
│  ▼ 3. 단계 3 — Regime 명명 부합 약함                        │
│       state 0 (위험회피) = 정체 패턴 (학술 정의 부합 약함) │
│       2020 코로나 위험회피 27.9% 만 (K=4 ablation 82% 비교)│
│       ★ 박제: §5.6.1                                        │
│                                                             │
│  ▼ 4. HMM 시드 불안정성                                     │
│       log-lik 변동 13.6%, BIC 13.4%                         │
│       GMM 0.06%·K-Means 0.007% 대비 매우 불안정            │
│       ★ 박제: §5.6.2 + regime_model_card.md                 │
│                                                             │
│  ▼ 5. 자동 K=4 vs 도메인 K=3 Tension                        │
│       BIC·AIC 자동 선택 K=4 (15,674 vs K=3 19,156)          │
│       본 라인 K=3 유지 (학술 관행), K=4 는 ablation 대안   │
│       ★ 박제: §5.6.2                                        │
│                                                             │
│  ▼ 6. KOSPI200 모집단 부실 사건 희소성                      │
│       양성 종목 20 (universe 321의 6.2%)                    │
│       28 fold 중 19 fold 양성 0 → 평가 가능 fold 9          │
│       §5.5.6 B3 기각 유지 (point-in-time 정합성 X)         │
│       ★ 박제: §5.5.6·§5.5.7                                 │
└─────────────────────────────────────────────────────────────┘

┌─── 프로젝트 핵심 메시지 (5 cards) ─────────────────────────┐
│  1. 정직성 사슬 5 차원                                      │
│  2. §7.6 검토 사이클                                        │
│  3. 5 후보 검증 후 D2 채택                                  │
│  4. negative finding 정직성                                 │
│  5. 자기 점검 사이클                                        │
└─────────────────────────────────────────────────────────────┘

┌─── 추가 자료 link ──────────────────────────────────────────┐
│  📄 PROGRESS.md §5.5 ~ §5.9 박제 [link]                     │
│  📄 reports/d2_baseline_model_card.md [link]                │
│  📄 reports/regime_model_card.md [link]                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 한국어 UX 마이크로카피 전체 목록

### 3.1 사이드바·네비게이션

| 위치 | 문구 |
|---|---|
| 사이드바 헤더 | `페이지 선택` |
| 종목 분석 옵션 | `종목 선택` / `분석 시점` / `class_weight (ablation)` |
| 종목 selectbox placeholder | `종목 검색...` |

### 3.2 메트릭 카드

| 카드 | label |
|---|---|
| RiskScoreCard | `D2 위험 확률` |
| RegimeCard | `시장 국면` |
| LabelCard | `1년 forward 양성 라벨` |
| FsDivCard | `재무 출처` |
| TickerHeader 카드 4 | `종목코드` / `종목명` / `시가총액 (현시점)` / `재무 출처` |

### 3.3 상태 메시지

| 상황 | 문구 |
|---|---|
| Skipped fold | `⚠️ 평가 제외 시점 (양성 0 인 fold)` |
| Warmup | `ℹ️ Warmup 기간 (2015 초반) 또는 시점 외` |
| 종목 비멤버 | `이 종목은 분석 시점 universe 멤버가 아닙니다` |
| OHLCV 없음 | `이 종목의 일간 시세 캐시가 없습니다` |
| 산출물 부재 | `⚠️ 산출물이 없습니다. {script} 를 먼저 실행하세요` |
| 데이터 로드 실패 | `데이터 로드 실패. 자세한 내용은 PROGRESS 참조` |

### 3.4 한계·경고

| 위치 | 문구 |
|---|---|
| ModelLimitWarning ticker | `⚠️ 본 모델은 random 미만 성능 (PR-AUC 0.0136 < base rate 0.0205). 위 위험 확률은 해석 가이드일 뿐 — 실거래·신용 평가 사용 금지.` |
| ModelLimitWarning regime | `⚠️ 시장 국면은 과거 데이터 사후 분석. 주가 예측 아님. 트레이딩 신호 사용 금지.` |
| ModelLimitWarning d2 | `⚠️ 본 모델은 random 미만. 모든 수치는 데이터 한계의 정량 증거.` |

### 3.5 해석 박스 (RegimeConditionalBox)

| 국면 | 본문 (§1.7 참조) |

### 3.6 시가총액 caption

`ℹ️ 시가총액은 현재 시점 스냅샷 (FDR StockListing). 과거 시점 시총 추적은 본 프로젝트 범위 밖입니다.`

---

## 4. utils 명세

### 4.1 `format_won(value: float | None) -> str`

```python
def format_won(value):
    if value is None or pd.isna(value): return "—"
    val = float(value)
    if val >= 1e12: return f"{val / 1e12:,.2f} 조원"
    if val >= 1e8:  return f"{val / 1e8:,.1f} 억원"
    return f"{val:,.0f} 원"
```

### 4.2 `format_percent(value, decimal=2)`, `format_proba(value)`

### 4.3 `classify_risk(proba: float | None) -> tuple[str, str]`

(label, hex_color) 반환 — RiskScoreCard 색상 코딩.

### 4.4 `lookup_regime_at(date_val) -> str | None`

state_series 에서 *가장 가까운 영업일 ≤ date* 의 regime label.

### 4.5 `find_close_column(ohlcv: pd.DataFrame) -> str | None`

cp949 "종가" 또는 영문 "Close" 자동 식별.

### 4.6 `compute_regime_blocks(state_series) -> pd.DataFrame`

contiguous regime block → (start, end, label) DataFrame (vrect 입력).

---

## 5. 상태별 UI 명세

| 상태 | 영향받는 컴포넌트 | UI |
|---|---|---|
| 로딩 | 모든 페이지 | `st.spinner("데이터 로드 중...")` (>500ms) |
| 빈 (Empty) | RiskScoreCard·차트들 | `EmptyState` 사용 |
| Skipped fold | RiskScoreCard | `proba=None`, caption "평가 제외 시점" |
| Warmup | RegimeCard | `regime=None`, caption "warmup 기간" |
| 종목 비멤버 | 페이지 전체 | `EmptyState(title=..., action="다른 종목 선택")` |
| 산출물 부재 | 페이지 전체 | `EmptyState(title=..., action="scripts/X 실행")` |
| 차트 렌더 실패 | 차트 컴포넌트 | `EmptyState(title="차트 표시 실패", description=err_short)` + 다른 섹션은 정상 |

---

## 6. Phase 4 구현 순서

1. `app/utils/` — formatters, regime_mapper (테스트 우선)
2. `app/components/` — header, metric_card, warning, empty_state
3. `app/components/chart.py` — PriceChartWithRegime, RatioGrid (vline 의 to_pydatetime 적용)
4. `app/components/interpretation.py` — RegimeConditionalBox (static template)
5. `app/pages/` — 5 페이지 분리
6. `app/main.py` slim refactor — 라우팅만
7. Phase 5 QA — Streamlit AppTest + 시각 회귀

각 단계마다:
- ruff format + check
- streamlit-like sys.path import 검증
- 단위 테스트 (가능한 경우)
- 사이클 단위 git commit

---

## 7. Phase 5 QA 입력

Phase 5 산출물 `docs/qa_checklist.md` 의 입력 항목:

- 각 Use Case (UC-1 ~ UC-7) 별 e2e step-by-step 검증
- 각 컴포넌트 단위 테스트 (utils 우선)
- Streamlit AppTest 페이지 렌더 검증
- headless browser 시각 회귀 (Playwright)
- 한국어 폰트·인코딩·문구 검증
- 접근성 (색 대비·키보드·screen reader)
- 반응형 (모바일·태블릿·데스크탑)
