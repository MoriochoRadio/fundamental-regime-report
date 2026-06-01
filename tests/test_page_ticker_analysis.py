"""app/pages/ticker_analysis.py 단위 테스트 (페이지 통합 단위 j).

종목 분석 페이지 = 7 컴포넌트 조립. st·컴포넌트·data_loader mock 으로 검증.
classify_risk·lookup_state_at·format_ticker_option 은 pure → 실함수 사용.

★ Q1 (A) 회귀: ablation *selector* 제거 = st.sidebar.radio 미호출 (행동 검증).
  ML *수치 리터럴* 비노출 = 소스 텍스트 검사. (내부 컬럼명 class_weight·
  docstring 의 'ablation' 설명어는 dev 차원 — §7.7(3) 정신, 검사 제외.)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import DEFAULT, MagicMock, patch

import pandas as pd

from app.pages import ticker_analysis as ta

_UNSET = object()
_SRC = Path(__file__).resolve().parent.parent / "app" / "pages" / "ticker_analysis.py"

# patch.multiple 대상 — st·data_loader·컴포넌트 (classify_risk 등 pure 는 실함수)
_TARGETS = dict(
    st=DEFAULT,
    load_universe=DEFAULT,
    load_d2_features=DEFAULT,
    load_d2_predictions=DEFAULT,
    load_state_series=DEFAULT,
    load_ohlcv=DEFAULT,
    load_llm_interpretation=DEFAULT,
    load_as_of_grid=DEFAULT,
    TickerHeader=DEFAULT,
    RiskScoreCard=DEFAULT,
    StateCard=DEFAULT,
    StateInterpretBox=DEFAULT,
    PriceChartWithStateOverlay=DEFAULT,
    RatioGrid=DEFAULT,
    EmptyState=DEFAULT,
)


def _universe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ticker": ["005930", "000660"],
            "name": ["삼성전자", "SK하이닉스"],
            "marcap": [4.0e14, 1.0e14],
        }
    )


def _features() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ticker": ["005930", "005930"],
            "as_of": pd.to_datetime(["2024-09-30", "2024-12-31"]),
            "debt_ratio": [1.1, 1.2],
            "current_ratio": [2.0, 2.1],
            "op_margin": [0.05, 0.06],
            "roa": [0.03, 0.04],
            "fs_div": ["CFS", "CFS"],
            "label": [0, 0],
        }
    )


def _preds() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ticker": ["005930"],
            "test_as_of": pd.to_datetime(["2024-12-31"]),
            "proba": [0.3],
            "label": [0],
            "class_weight": ["balanced"],
        }
    )


def _setup(
    m: dict,
    *,
    universe=_UNSET,
    feats=_UNSET,
    preds=_UNSET,
    grid=_UNSET,
    ohlcv=None,
    state=None,
    llm=None,
    ticker: str = "005930",
    as_of=_UNSET,
) -> None:
    """mock dict 기본 셋업 (sentinel 로 명시 None 구분)."""
    m["load_universe"].return_value = _universe() if universe is _UNSET else universe
    m["load_d2_features"].return_value = _features() if feats is _UNSET else feats
    m["load_d2_predictions"].return_value = _preds() if preds is _UNSET else preds
    m["load_as_of_grid"].return_value = [pd.Timestamp("2024-12-31")] if grid is _UNSET else grid
    m["load_ohlcv"].return_value = ohlcv
    m["load_state_series"].return_value = state
    m["load_llm_interpretation"].return_value = llm
    sel_as_of = pd.Timestamp("2024-12-31") if as_of is _UNSET else as_of
    m["st"].sidebar.selectbox.side_effect = [ticker, sel_as_of]
    m["st"].columns.return_value = [MagicMock(), MagicMock()]


def test_full_assembly_all_components() -> None:
    """정상 → 6 컴포넌트 각 1회 호출, EmptyState 미호출."""
    with patch.multiple("app.pages.ticker_analysis", **_TARGETS) as m:
        _setup(m)
        ta.render()
        m["TickerHeader"].assert_called_once()
        m["RiskScoreCard"].assert_called_once()
        m["StateCard"].assert_called_once()
        m["StateInterpretBox"].assert_called_once()
        m["PriceChartWithStateOverlay"].assert_called_once()
        m["RatioGrid"].assert_called_once()
        m["EmptyState"].assert_not_called()


def test_no_ablation_radio() -> None:
    """★ Q1 (A): class_weight ablation selector 제거 → st.sidebar.radio 미호출."""
    with patch.multiple("app.pages.ticker_analysis", **_TARGETS) as m:
        _setup(m)
        ta.render()
        m["st"].sidebar.radio.assert_not_called()


def test_two_selectboxes() -> None:
    """사이드바 selectbox 2회 (종목 + 분석 시점)."""
    with patch.multiple("app.pages.ticker_analysis", **_TARGETS) as m:
        _setup(m)
        ta.render()
        assert m["st"].sidebar.selectbox.call_count == 2


def test_stateinterpret_wiring() -> None:
    """StateInterpretBox(state, risk_level=classify_risk(proba), llm_text)."""
    with patch.multiple("app.pages.ticker_analysis", **_TARGETS) as m:
        _setup(m, llm={"text": "빌드타임 생성 서술"})
        ta.render()
        args, _ = m["StateInterpretBox"].call_args
        # 위치 인자: (state, risk_level, llm_text)
        assert args[1] == "중간"  # classify_risk(0.3) → 중간
        assert args[2] == "빌드타임 생성 서술"


def test_features_none_emptystate() -> None:
    """features None → 상단 EmptyState, 조립 컴포넌트 미호출."""
    with patch.multiple("app.pages.ticker_analysis", **_TARGETS) as m:
        _setup(m, feats=None)
        ta.render()
        m["EmptyState"].assert_called_once()
        m["TickerHeader"].assert_not_called()
        m["RiskScoreCard"].assert_not_called()


def test_empty_universe_emptystate() -> None:
    """universe 빈 DataFrame → EmptyState."""
    empty = pd.DataFrame(columns=["ticker", "name", "marcap"])
    with patch.multiple("app.pages.ticker_analysis", **_TARGETS) as m:
        _setup(m, universe=empty)
        ta.render()
        m["EmptyState"].assert_called_once()


def test_proba_none_riskcard_none() -> None:
    """매칭 prediction 없음 → RiskScoreCard(None)."""
    empty_preds = _preds().iloc[0:0]
    with patch.multiple("app.pages.ticker_analysis", **_TARGETS) as m:
        _setup(m, preds=empty_preds)
        ta.render()
        m["RiskScoreCard"].assert_called_once_with(None)


def test_no_ml_numbers_in_source() -> None:
    """★ docs §2.8·§5(1): 페이지 소스에 ML 원본 수치 리터럴 비노출."""
    src = _SRC.read_text(encoding="utf-8")
    for token in ["PR-AUC", "0.0136", "base rate", "0.0205", "ROC-AUC", "random 미만"]:
        assert token not in src, f"'{token}' 노출됨"
