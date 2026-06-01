"""실 데이터 렌더 통합 smoke (QA-2 — QA-1 throwaway 의 영구 박제).

4 페이지 전부 *실 산출물*(mock 아닌 실 로더)로 '실 내용 분기' 도달 검증.
mock 단위 테스트(382)가 못 보던 실 데이터 경로를 커버한다.

★ @pytest.mark.integration — 실 parquet/CSV 의존 → CI `not integration` deselect.
★ 산출물 부재 시 graceful skip (error 아님).
★ ticker/as_of 는 로더에서 *동적·결정적* 선택 (특정 종목 하드코딩 회피, 재현성).
"""

from __future__ import annotations

import importlib
from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app import data_loader as dl

pytestmark = pytest.mark.integration

# st 를 쓰는 page + component 모듈 (단일 공유 mock 으로 patch)
_ST_MODULES = (
    "app.pages.overview",
    "app.pages.ticker_analysis",
    "app.pages.market_state",
    "app.pages.limitations",
    "app.components.header",
    "app.components.metric_card",
    "app.components.chart",
    "app.components.warning",
    "app.components.interpretation",
)


def _fresh_st() -> MagicMock:
    """recording st mock — columns/expander 는 context manager."""
    st = MagicMock(name="st")
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=cm)
    cm.__exit__ = MagicMock(return_value=False)
    st.columns.side_effect = lambda n, *a, **k: [
        cm for _ in range(n if isinstance(n, int) else len(n))
    ]
    st.expander.return_value = cm
    st.sidebar = MagicMock()
    return st


def _texts(st: MagicMock) -> str:
    out: list[str] = []
    for meth in ("markdown", "write", "caption", "info", "warning", "metric", "title", "header"):
        for c in getattr(st, meth).call_args_list:
            out.extend(str(a) for a in c.args)
    return "\n".join(out)


def _run_page(page_mod: str, selectbox_returns: list | None = None) -> MagicMock:
    st = _fresh_st()
    if selectbox_returns is not None:
        st.sidebar.selectbox.side_effect = selectbox_returns
    with ExitStack() as es:
        for mod in _ST_MODULES:
            es.enter_context(patch(f"{mod}.st", st))
        importlib.import_module(page_mod).render()
    return st


@pytest.fixture(scope="module")
def real_data() -> dict:
    """실 산출물 준비 확인 + 데이터 있는 종목/시점 동적·결정적 선택.

    부재 시 skip. 선택 기준: balanced proba notna ∧ ohlcv 존재 ∧ features 존재,
    (ticker, test_as_of) 정렬 후 첫 후보 (결정적).
    """
    universe = dl.load_universe()
    feats = dl.load_d2_features()
    preds = dl.load_d2_predictions()
    state = dl.load_state_series()
    if (
        universe.empty
        or feats is None
        or feats.empty
        or preds is None
        or preds.empty
        or state is None
        or state.empty
    ):
        pytest.skip("실 산출물 부재 — 통합 smoke skip (데이터 파이프라인 미실행)")

    pb = preds[preds["class_weight"] == "balanced"] if "class_weight" in preds.columns else preds
    pb = pb.dropna(subset=["proba"]).sort_values(["ticker", "test_as_of"]).reset_index(drop=True)
    feat_tickers = set(feats["ticker"].unique())
    for _, r in pb.iterrows():
        tk = r["ticker"]
        if tk in feat_tickers and dl.load_ohlcv(tk) is not None:
            return {"ticker": tk, "as_of": pd.Timestamp(r["test_as_of"])}
    pytest.skip("실 proba + ohlcv + features 동시 보유 종목 없음")
    return {}  # unreachable (skip)


def test_overview_real(real_data: dict) -> None:
    """개요: 예시 종목 카드 실 렌더 (TickerHeader→st.header) + CTA."""
    st = _run_page("app.pages.overview")
    assert st.header.call_count >= 1
    assert st.button.called


def test_ticker_analysis_real_content(real_data: dict) -> None:
    """종목 분석: 실 proba 분기 도달 (Chart+RatioGrid 2 + Risk+State 2 카드)."""
    st = _run_page(
        "app.pages.ticker_analysis",
        selectbox_returns=[real_data["ticker"], real_data["as_of"]],
    )
    t = _texts(st)
    assert st.plotly_chart.call_count == 2  # PriceChartWithStateOverlay + RatioGrid
    assert st.metric.call_count >= 2  # RiskScoreCard + StateCard
    assert "추정 위험 확률" in t  # 실 proba 렌더 (미평가 아님)
    assert "분석 평가 제외" not in t


def test_market_state_real(real_data: dict) -> None:
    """시장 상태: StateStripeChart→plotly_chart 1 + 위기 info 1 + 9개월 warning 1."""
    st = _run_page("app.pages.market_state")
    assert st.plotly_chart.call_count == 1
    assert st.info.call_count == 1
    assert st.warning.call_count == 1


def test_limitations_real_card_isolation(real_data: dict) -> None:
    """★ 한계: 실 model card(PR-AUC 포함) 내용이 렌더 출력에 미노출 (§7.7 실 입증)."""
    card = dl.load_model_card("d2_baseline")
    assert card is not None and "PR-AUC" in card  # 실 카드엔 ML 수치 존재
    st = _run_page("app.pages.limitations")
    t = _texts(st)
    assert "reports/d2_baseline_model_card.md" in t  # 링크는 표시
    assert "PR-AUC" not in t  # 카드 내용은 렌더 미노출
    assert "0.0136" not in t
