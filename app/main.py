"""Streamlit 대시보드 entry point (단계 4, PROGRESS §5.7).

CLAUDE.md §8.6 박제:
- 정적 읽기 전용
- LLM SDK import 0 (CI 검사 의무)
- reports/ + data/interim/ 정적 산출물만 사용

실행:
    uv run streamlit run app/main.py
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data_loader import (
    load_as_of_grid,
    load_d2_features,
    load_d2_predictions,
    load_ohlcv,
    load_state_series,
    load_universe,
)


def render_overview() -> None:
    """페이지 1: 프로젝트 개요 + 단계별 상태."""
    st.title("기업 펀더멘털 + 시장 국면 인지형 통합 분석 리포트")
    st.markdown(
        """
        **개인 ML 연구 프로젝트** — 한국 KOSPI200 (point-in-time) 배치 분석.
        D2 부실 라벨 스코어링 + HMM 시장 국면 분류 + 통합 시각화.

        본 대시보드는 *정적 산출물 전용 시각화* (CLAUDE.md §8.6).
        런타임 LLM 호출 0회 (§3.4).
        """
    )

    st.markdown("### 단계별 진행 상태")
    st.markdown(
        """
        | 단계 | 상태 | 박제 |
        |---|---|---|
        | 1. 데이터 셋업 | ✅ | universe 321, grid 40, DART/KRX/FDR 캐시 |
        | 2. 펀더멘털 모듈 | ✅ | LightGBM + walk-forward (§5.5.17 negative finding) |
        | 3. 시장 국면 모듈 | ✅ | HMM K=3 (§5.6.1, §5.6.2 명명 부합 약함 정직 박제) |
        | 4. 통합 대시보드 | 🔄 | 본 대시보드 |
        | 5. 마무리 | 대기 | README + docs |
        """
    )


def render_regime_timeline() -> None:
    """페이지 2: 시장 상태 시계열.

    단위 (b): 정정된 load_state_series 호출 + 전이 행렬 블록 제거 (FR-9
    Won't 매핑, 검증 3 직접 매핑). 페이지 *완전 재구성* 은 단위 (i)~(l)
    의 시장 상태 페이지 신규 작성에서.
    """
    st.title("시장 상태 시계열")

    state_series = load_state_series()

    if state_series is None or state_series.empty:
        st.warning("⚠️ 시장 상태 산출물 없음. `scripts/train_regime.py` 먼저 실행.")
        return

    state_series["date"] = pd.to_datetime(state_series["date"])
    st.markdown(
        f"**기간**: {state_series['date'].min().date()} ~ {state_series['date'].max().date()} "
        f"({len(state_series):,} obs)"
    )

    # state 색상 매핑
    color_map = {
        "위험회피": "#d62728",  # red
        "중립": "#7f7f7f",  # gray
        "위험선호": "#2ca02c",  # green
    }

    # state 시계열 (segments)
    fig = px.scatter(
        state_series,
        x="date",
        y="state_label",
        color="state_label",
        color_discrete_map=color_map,
        title="시장 상태 시계열",
    )
    fig.update_traces(marker={"size": 4})
    st.plotly_chart(fig, use_container_width=True)

    # State 분포
    st.markdown("### 상태 분포")
    dist = state_series["state_label"].value_counts()
    fig_pie = go.Figure(
        data=[
            go.Pie(
                labels=dist.index.tolist(),
                values=dist.values.tolist(),
                marker={"colors": [color_map.get(s, "#888") for s in dist.index]},
            )
        ]
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # 단위 (b) 폐기: 전이 행렬 블록 (검증 3 직접 매핑, FR-9 Won't).
    # 페이지 *완전 재구성* 은 단위 (i)~(l) 의 시장 상태 페이지 신규 작성.


def render_d2_results() -> None:
    """페이지 3: D2 baseline 결과 — 단위 (b) stub.

    검증 2 직접 매핑 (D2 baseline 별도 페이지 폐기 + 모델 카드 link 만).
    페이지 *완전 폐기* (메뉴 항목 제거 포함) 는 단위 (i)~(l) 의 한계 페이지
    재구성에서.
    """
    st.title("D2 baseline 결과")
    st.warning(
        "⚠️ 본 페이지는 단위 (i)~(l) 에서 폐기 예정 (검증 2 직접 매핑, "
        "FR-9 Won't). 기술 차원 별도 자료는 모델 카드 참조: "
        "`reports/d2_baseline_model_card.md`."
    )


def render_limitations() -> None:
    """페이지 4: Limitations — 방법론적 특징 핵심."""
    st.title("⚠️ Limitations — 정직 박제 (방법론적 특징)")

    st.markdown(
        """
        본 페이지는 본 프로젝트의 **방법론적 특징 핵심**.
        모든 한계가 *정직 박제* 되어 있어 *negative finding 의 정직성* +
        *D2 정직성 사슬 4 차원* + *모집단 한계 정량 증명* 가치 제공.
        """
    )

    st.markdown("---")

    # 1. 단계 2 negative finding
    st.markdown("### 1. 단계 2 — D2 baseline Negative Finding")
    st.markdown(
        """
        - **PR-AUC 0.0136** < base rate 0.0205 → 모델 random 보다 나쁨
        - **ROC-AUC 0.2651** < 0.5 (정반대 예측에 가까움)
        - **class weight ablation 효과 0** — balanced vs unweighted 차이 < 0.001
          → *양성 절대 수 부족 앞에서 보완 무력*

        ★ 박제 권위: PROGRESS §5.5.17 + `reports/d2_baseline_model_card.md`
        """
    )

    # 2. (A) 데이터 보강
    st.markdown("### 2. (A) 데이터 보강 결과 — Strong Negative Evidence")
    st.markdown(
        """
        - notfound 3,583 OFS 재페치 → **status 전환 0건**
        - DART API 응답 모두 `{status: '013', '조회된 데이타가 없습니다'}`
        - → notfound 가 *D10 fetcher 미적용*이 아니라 *실제 데이터 부재*
        - **§5.5.7 KOSPI200 부실 사건 희소성** 이 *데이터 출처 변경으로
          극복 불가능* 함을 정량 증명

        ★ 박제 권위: PROGRESS §5.5.17 (A) 단락
        """
    )

    # 3. 단계 3 명명 부합 약함 (정적 본문, 단위 (b) stub: load_regime_results
    # 폐기로 동적 데이터 호출 제거)
    st.markdown("### 3. 단계 3 — Regime 학술 명명 부합 약함")
    st.markdown(
        """
        HMM K=3 상태별 means (rolling z-score):

        | state | 명명 | ret_20d | vol_60d | 위기 점수 |
        |---|---|---|---|---|
        | 2 | 위험선호 | +0.549 | +0.309 | -0.240 (낮음) |
        | 1 | 중립 | -0.752 | -0.008 | +0.744 |
        | 0 | 위험회피 | -0.809 | -0.015 | +0.794 (높음) |

        - **state 0 (위험회피)** = *낮은 ret + 낮은 vol = 정체 패턴*
          (학술 정의 부합 약함)
        - **2020 코로나 spot-check**: 위험회피 27.9% 만 (중립 42.6% 더 많음)
        - 모델은 *3 분리* 했으나 *학술 표준 위험회피·위험선호 와 정확히
          매칭 안 됨*

        ★ 박제 권위: PROGRESS §5.6.1
        """
    )

    # 4. HMM 시드 불안정성 (정적 본문, 단위 (b) stub: load_regime_comparison
    # 폐기로 동적 데이터 호출 제거)
    st.markdown("### 4. HMM 시드 불안정성")
    st.markdown(
        """
        5 시드 (42, 123, 7, 2024, 999) log-likelihood 변동:

        | 모델 | 변동 폭 |
        |---|---|
        | **HMM** | **-9442 ~ -8312 (13.6%)** ⚠️ |
        | GMM | -10101 ~ -10107 (0.06%) |
        | K-Means inertia | 5436.5 ~ 5436.9 (0.007%) |

        → **HMM EM 알고리즘 local optima 의존성**. 단일 시드 (random_state=42)
        결과 권위 — 다른 시드는 *다른 결과* 가능.

        ★ 박제 권위: PROGRESS §5.6.2 + `reports/regime_model_card.md`
        """
    )

    # 5. 자동 K=4 vs 도메인 K=3 tension
    st.markdown("### 5. 자동 K=4 vs 도메인 K=3 Tension")
    st.markdown(
        """
        BIC·AIC 자동 선택은 **K=4** 가 최소:

        | model | K=2 BIC | K=3 BIC | K=4 BIC |
        |---|---|---|---|
        | HMM | 18,743.58 | 19,156.36 | **15,674.28** ⬅ 최소 |
        | GMM | 20,603.42 | 20,429.49 | **20,384.76** ⬅ 최소 |

        - 본 라인 K=3 채택 (학술 관행 + 도메인 해석)
        - K=4 결과는 *대안 시나리오* — 단계 5 ablation 분석 후보

        ★ 박제 권위: PROGRESS §5.6.2
        """
    )

    # 6. KOSPI200 모집단 희소성
    st.markdown("### 6. KOSPI200 모집단 부실 사건 희소성")
    st.markdown(
        """
        - 양성 종목 20 (universe 321 중 6.2%)
        - 양성 cells 45 (전체 8,008 의 0.56%)
        - 28 walk-forward fold 중 19 fold (68%) 가 train_pos=0 또는 test_pos=0
          → 평가 가능 fold 9
        - *§5.5.6 (B3 KOSDAQ 확장) 기각* 유지 — point-in-time 정합성 X

        → **D1 정직성과 §5 격리 원칙** 유지하면서 *모델 학습 불가능 수준*
        의 데이터 한계 확인.

        ★ 박제 권위: PROGRESS §5.5.6·§5.5.7
        """
    )

    st.markdown("---")
    st.markdown(
        """
        ### 프로젝트 핵심 메시지

        본 프로젝트는 *negative finding* 이지만 다음 가치 박제:

        1. **D2 정직성 사슬 4 차원**: 변수·양성충분성·격리·시간 (§5.5.12)
        2. **§7.6 작업 진입 검토 사이클**: 4 단계 매 작업 의무 (CLAUDE.md)
        3. **5 후보 전수 검증·기각 후 D2 채택**: 입증된 최선 (§5.5.7)
        4. **negative finding 의 정직성** + **모집단 한계 정량 증명**
        5. **17+ commit 자기 점검 사이클**: 모든 결정이 PROGRESS 박제·실측·자문 검토 통과
        """
    )


# ============================================================================
# 사이클 2 — 종목 분석 페이지 (CLAUDE.md §2 핵심 사용자 시나리오 구현)
# ============================================================================


# 시장 국면 색상 (regime 페이지와 일관)
_REGIME_COLOR_MAP = {
    "위험회피": "#d62728",  # red
    "중립": "#7f7f7f",  # gray
    "위험선호": "#2ca02c",  # green
}


def _lookup_state_at(date_val: pd.Timestamp) -> str | None:
    """state_series 에서 *가장 가까운 영업일 ≤ date* 의 state label.

    단위 (b) 정정: load_regime_state_series → load_state_series.
    단위 (i)~(l) 에서 app/utils/state_mapper.py 의 lookup_state_at 으로
    완전 교체 예정.
    """
    state = load_state_series()
    if state is None or state.empty:
        return None
    state = state.copy()
    state["date"] = pd.to_datetime(state["date"])
    mask = state["date"] <= date_val
    if not mask.any():
        return None
    return str(state[mask].iloc[-1]["state_label"])


def _format_won(value: float | None) -> str:
    """원 단위 금액 → 조/억 단위 사람 친화 표시."""
    if value is None or pd.isna(value):
        return "—"
    val = float(value)
    if val >= 1e12:
        return f"{val / 1e12:.2f} 조원"
    if val >= 1e8:
        return f"{val / 1e8:.1f} 억원"
    return f"{val:,.0f} 원"


def _state_conditional_text(
    regime: str | None,
    ticker_features: pd.Series | None,
) -> str:
    """C-4 국면 조건부 해석 텍스트 (static template, v1).

    본 v1 은 *방향성 가이드 정적 문구*. *동적 규칙 박제* 는 향후 사이클.
    모델이 random 미만이므로 *해석 가이드만* 명시.
    """
    if regime is None:
        return "ℹ️ 시장 국면 데이터 없음 (warmup 9 개월 또는 분석 시점 외)."

    template = {
        "위험회피": (
            "현재 시장이 **위험회피 (위기)** 국면입니다. 위험회피 국면에서는 "
            "*같은 부채비율 상승·영업이익 둔화* 가 *일반 시 대비 더 강한 "
            "부실 신호*로 해석될 수 있습니다. 단 본 모델은 random 미만이라 "
            "*방향성 가이드만* 으로 사용하세요."
        ),
        "위험선호": (
            "현재 시장이 **위험선호 (상승)** 국면입니다. 위험선호 국면에서는 "
            "*동일 재무 지표 약화* 가 *시장 전반 회복세에 가려질 수 있어* "
            "해석 시 주의 필요. 본 모델은 random 미만이라 *방향성 가이드만*."
        ),
        "중립": (
            "현재 시장이 **중립** 국면입니다. 중립 국면은 *전이로 자주 이동* "
            "하는 교차로 역할 — 위험회피로 전환 확률 0.925 (§5.6.1). 재무 "
            "지표 변화를 *전이 신호*로 함께 해석. 본 모델은 random 미만이라 "
            "*방향성 가이드만*."
        ),
    }
    base = template.get(regime, f"현재 시장 국면: **{regime}**.")

    # ticker features 가 있으면 z-score 부착 (정적, v1)
    if ticker_features is not None and not ticker_features.empty:
        ratios = []
        for col, label in [
            ("debt_ratio", "부채비율"),
            ("current_ratio", "유동비율"),
            ("op_margin", "영업이익률"),
            ("roa", "ROA"),
        ]:
            v = ticker_features.get(col)
            if v is not None and not pd.isna(v):
                ratios.append(f"{label} {v:.4f}")
        if ratios:
            base += f"\n\n해당 시점 종목 ratio: {' · '.join(ratios)}."
    return base


def render_ticker_analysis() -> None:
    """페이지: 종목 분석 — CLAUDE.md §2 통합 리포트 구현 (사이클 2).

    7 섹션:
    1. 종목 선택 사이드바
    2. 헤더 (코드·이름·시총)
    3. 위험 점수 + 시장 국면
    4. 국면 조건부 해석 텍스트
    5. 주가 차트 + state overlay
    6. 재무 비율 추이
    7. 모델 한계 경고
    """
    st.title("종목 분석 — 통합 리포트")

    # === 1. 사이드바: 종목 선택 / 시점 / ablation ===
    universe = load_universe()
    feats_all = load_d2_features()
    preds_all = load_d2_predictions()
    grid = load_as_of_grid()

    if universe.empty or feats_all is None:
        st.warning(
            "⚠️ 산출물 없음. `scripts/train_d2_baseline.py` 실행 (predictions.parquet + "
            "features.parquet 생성) 후 사용."
        )
        return

    name_map: dict[str, str] = dict(zip(universe["ticker"], universe["name"], strict=True))
    marcap_map: dict[str, float] = dict(zip(universe["ticker"], universe["marcap"], strict=True))

    tickers = sorted(name_map.keys())
    ticker = st.sidebar.selectbox(
        "종목 선택",
        tickers,
        format_func=lambda t: f"{t} {name_map.get(t, '')}",
    )

    as_of_options = grid if grid else []
    as_of = st.sidebar.selectbox(
        "분석 시점",
        as_of_options[::-1],  # 최신부터
        format_func=lambda d: d.strftime("%Y-%m-%d"),
    )
    cw = st.sidebar.radio("class_weight ablation", ["balanced", "unweighted"])

    # === 2. 헤더 ===
    col1, col2, col3 = st.columns(3)
    col1.metric("종목코드", ticker)
    col2.metric("종목명", name_map.get(ticker, "—"))
    col3.metric("시가총액 (현시점)", _format_won(marcap_map.get(ticker)))
    st.caption(
        "ℹ️ 시가총액은 FDR 현 시점 스냅샷 (CLAUDE.md §8.1) — 과거 시점 시가총액 추적 X. 참고용."
    )

    # === 3. 위험 점수 + 시장 국면 ===
    st.markdown("### 위험 점수 + 시장 국면")

    # ticker × as_of 의 prediction 조회
    pred_row = None
    if preds_all is not None:
        sel = preds_all[
            (preds_all["ticker"] == ticker)
            & (preds_all["test_as_of"] == as_of)
            & (preds_all["class_weight"] == cw)
        ]
        if not sel.empty:
            pred_row = sel.iloc[0]

    # ticker × as_of 의 features 조회
    feat_row = None
    sel_f = feats_all[(feats_all["ticker"] == ticker) & (feats_all["as_of"] == as_of)]
    if not sel_f.empty:
        feat_row = sel_f.iloc[0]

    # 해당 시점 시장 상태
    regime_label = _lookup_state_at(as_of)

    col_a, col_b, col_c, col_d = st.columns(4)
    if pred_row is not None:
        proba = float(pred_row["proba"])
        col_a.metric("D2 위험 확률", f"{proba:.4f}")
    else:
        col_a.metric("D2 위험 확률", "—")
        col_a.caption("skipped fold (양성 0) — prediction 없음")
    col_b.metric("시장 국면", regime_label if regime_label else "—")
    if feat_row is not None:
        col_c.metric("양성 라벨 (1년 forward)", int(feat_row["label"]))
        col_d.metric("fs_div", str(feat_row.get("fs_div", "—")))
    else:
        col_c.metric("양성 라벨", "—")
        col_d.metric("fs_div", "—")

    # === 4. 국면 조건부 해석 ===
    st.markdown("### 국면 조건부 해석")
    st.info(_state_conditional_text(regime_label, feat_row))

    # === 5. 주가 차트 + state overlay ===
    st.markdown("### 주가 + 시장 국면 overlay")
    ohlcv = load_ohlcv(ticker)
    state_series = load_state_series()

    if ohlcv is None or ohlcv.empty:
        st.warning(f"⚠️ {ticker} OHLCV 캐시 없음.")
    else:
        # cp949 한국어 컬럼 — 종가 컬럼 추출
        close_col = next((c for c in ohlcv.columns if "종가" in c or c == "Close"), None)
        if close_col is None:
            st.warning("종가 컬럼 식별 실패. 컬럼: " + ", ".join(ohlcv.columns))
        else:
            ohlcv_plot = ohlcv.reset_index()
            date_col = ohlcv_plot.columns[0]  # index → first column (보통 "날짜")
            ohlcv_plot[date_col] = pd.to_datetime(ohlcv_plot[date_col])

            fig = go.Figure()
            # state background shading
            if state_series is not None and not state_series.empty:
                state = state_series.copy()
                state["date"] = pd.to_datetime(state["date"])
                # 단순화: 각 state 구간을 contiguous block 으로 묶어 shaded rect 추가
                state["block"] = (state["state_label"] != state["state_label"].shift()).cumsum()
                blocks = state.groupby("block").agg(
                    start=("date", "min"), end=("date", "max"), label=("state_label", "first")
                )
                for _, b in blocks.iterrows():
                    fig.add_vrect(
                        x0=b["start"],
                        x1=b["end"],
                        fillcolor=_REGIME_COLOR_MAP.get(b["label"], "#cccccc"),
                        opacity=0.15,
                        line_width=0,
                    )

            fig.add_trace(
                go.Scatter(
                    x=ohlcv_plot[date_col],
                    y=ohlcv_plot[close_col],
                    mode="lines",
                    name="종가",
                    line={"color": "#1f77b4"},
                )
            )
            fig.add_vline(
                x=as_of.to_pydatetime(),
                line_dash="dash",
                line_color="#444",
            )
            fig.add_annotation(
                x=as_of.to_pydatetime(),
                y=1,
                yref="paper",
                text=f"분석 시점 {as_of.strftime('%Y-%m-%d')}",
                showarrow=False,
                yanchor="bottom",
            )
            fig.update_layout(
                title=f"{ticker} {name_map.get(ticker, '')} 종가 + 시장 국면 overlay",
                xaxis_title="날짜",
                yaxis_title="종가 (원)",
                hovermode="x unified",
                height=420,
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "배경 색상: 시장 국면 (빨강=위험회피·회색=중립·초록=위험선호). "
                "점선: 사용자 선택 분석 시점."
            )

    # === 6. 재무 비율 추이 ===
    st.markdown("### 재무 비율 추이 (28 분기말 grid, rolling z-score 아님)")
    ticker_feats = feats_all[feats_all["ticker"] == ticker].sort_values("as_of")
    if ticker_feats.empty:
        st.warning(f"{ticker} 의 features 시계열 없음.")
    else:
        import plotly.subplots as sp

        fig2 = sp.make_subplots(
            rows=2,
            cols=2,
            subplot_titles=("debt_ratio", "current_ratio", "op_margin", "roa"),
        )
        for col, row_, col_ in [
            ("debt_ratio", 1, 1),
            ("current_ratio", 1, 2),
            ("op_margin", 2, 1),
            ("roa", 2, 2),
        ]:
            fig2.add_trace(
                go.Scatter(
                    x=ticker_feats["as_of"],
                    y=ticker_feats[col],
                    mode="lines+markers",
                    name=col,
                    showlegend=False,
                ),
                row=row_,
                col=col_,
            )
            fig2.add_vline(
                x=as_of.to_pydatetime(), line_dash="dash", line_color="#444", row=row_, col=col_
            )
        fig2.update_layout(height=500, title=f"{ticker} 재무 비율 4개 추이")
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("점선: 사용자 선택 분석 시점. 분모 0 또는 결측 시 NaN.")

    # === 7. 모델 한계 경고 ===
    st.error(
        "⚠️ **본 모델은 random 미만 성능** (PR-AUC 0.0136 < base rate 0.0205). "
        "위 위험 확률은 *해석 가이드일 뿐* — 실제 투자 판단·신용 평가 사용 금지. "
        "Limitations 페이지 참조 (CLAUDE.md §4.2 OUT 박제)."
    )


def main() -> None:
    st.set_page_config(
        page_title="기업 펀더멘털 + 시장 국면 통합 리포트",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    page = st.sidebar.radio(
        "페이지 선택",
        [
            "개요",
            "★ 종목 분석",
            "시장 국면 시계열",
            "D2 baseline 결과",
            "⚠️ Limitations (방법론적 특징)",
        ],
    )

    if page == "개요":
        render_overview()
    elif page == "★ 종목 분석":
        render_ticker_analysis()
    elif page == "시장 국면 시계열":
        render_regime_timeline()
    elif page == "D2 baseline 결과":
        render_d2_results()
    elif page == "⚠️ Limitations (방법론적 특징)":
        render_limitations()


if __name__ == "__main__":
    main()
