"""app/components/chart.py 단위 테스트.

단계 5 단위 (e) 산출물. 검증 7 (방어적 입력) + 검증 1·4·5.1 매핑.

★ 검증 5.1 핵심: as_of=pd.Timestamp → add_vline/add_vrect 예외 없이 완료
(Phase 4 TypeError 차단).

컴포넌트 = pure 렌더링 함수. st mock 으로 plotly_chart 호출 검증.

★ 단위 (f) Q2 (A): 빈 상태는 EmptyState 위임 (inline st.info 폐기).
chart 가 EmptyState 를 호출하므로 회귀는 EmptyState mock 으로 검증.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from app.components.chart import PriceChartWithStateOverlay, RatioGrid, StateStripeChart


def _make_ohlcv() -> pd.DataFrame:
    """합성 OHLCV (날짜 index + 종가)."""
    dates = pd.date_range("2020-01-01", periods=10, freq="D")
    return pd.DataFrame({"종가": range(100, 110)}, index=dates)


def _make_state_series() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2020-01-03", "2020-01-05", "2020-01-07"]),
            "state_label": ["위험회피", "위험회피", "중립", "위험선호"],
        }
    )


def _make_features() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "as_of": pd.to_datetime(["2020-03-31", "2020-06-30", "2020-09-30"]),
            "debt_ratio": [1.2, 1.3, 1.1],
            "current_ratio": [2.0, 1.9, 2.1],
            "op_margin": [0.05, 0.04, 0.06],
            "roa": [0.03, 0.02, 0.04],
        }
    )


# ---- PriceChartWithStateOverlay --------------------------------------------


def test_price_chart_normal() -> None:
    """정상 (ohlcv + state) → st.plotly_chart 호출, EmptyState 미호출."""
    with (
        patch("app.components.chart.st") as mock_st,
        patch("app.components.chart.EmptyState") as mock_empty,
    ):
        PriceChartWithStateOverlay(
            "005930",
            "삼성전자",
            _make_ohlcv(),
            _make_state_series(),
            pd.Timestamp("2020-01-05"),
        )
        mock_st.plotly_chart.assert_called_once()
        mock_empty.assert_not_called()


def test_price_chart_ohlcv_none() -> None:
    """ohlcv None → EmptyState 위임, plotly_chart 미호출."""
    with (
        patch("app.components.chart.st") as mock_st,
        patch("app.components.chart.EmptyState") as mock_empty,
    ):
        PriceChartWithStateOverlay(
            "005930", "삼성전자", None, _make_state_series(), pd.Timestamp("2020-01-05")
        )
        mock_empty.assert_called_once()
        mock_st.plotly_chart.assert_not_called()


def test_price_chart_ohlcv_empty() -> None:
    """ohlcv empty → EmptyState 위임."""
    with (
        patch("app.components.chart.st") as mock_st,
        patch("app.components.chart.EmptyState") as mock_empty,
    ):
        PriceChartWithStateOverlay(
            "005930", "삼성전자", pd.DataFrame(), _make_state_series(), pd.Timestamp("2020-01-05")
        )
        mock_empty.assert_called_once()
        mock_st.plotly_chart.assert_not_called()


def test_price_chart_close_col_absent() -> None:
    """종가 컬럼 미식별 → EmptyState 위임."""
    dates = pd.date_range("2020-01-01", periods=3, freq="D")
    bad = pd.DataFrame({"Open": [1, 2, 3]}, index=dates)
    with (
        patch("app.components.chart.st") as mock_st,
        patch("app.components.chart.EmptyState") as mock_empty,
    ):
        PriceChartWithStateOverlay("005930", "삼성전자", bad, None, pd.Timestamp("2020-01-02"))
        mock_empty.assert_called_once()
        mock_st.plotly_chart.assert_not_called()


def test_price_chart_state_none_overlay_skipped() -> None:
    """state_series None → overlay 없이 주가 line 만 (plotly_chart 정상)."""
    with patch("app.components.chart.st") as mock_st:
        PriceChartWithStateOverlay(
            "005930", "삼성전자", _make_ohlcv(), None, pd.Timestamp("2020-01-05")
        )
        mock_st.plotly_chart.assert_called_once()


# ---- ★ 검증 5.1 Timestamp+plotly 회귀 -------------------------------------


def test_price_chart_timestamp_no_typeerror() -> None:
    """★ 검증 5.1: as_of=pd.Timestamp → 예외 없이 완료 (Phase 4 TypeError 차단)."""
    with patch("app.components.chart.st"):
        # pd.Timestamp 입력 — Phase 4 에서 add_vline(x=Timestamp) TypeError 발생
        # 했던 케이스. .to_pydatetime() 적용으로 예외 없이 완료해야 함.
        PriceChartWithStateOverlay(
            "005930",
            "삼성전자",
            _make_ohlcv(),
            _make_state_series(),
            pd.Timestamp("2020-01-05"),
        )
    # 예외 없이 도달 = 통과


def test_ratio_grid_timestamp_no_typeerror() -> None:
    """★ 검증 5.1: RatioGrid as_of=pd.Timestamp → 예외 없이 완료."""
    with patch("app.components.chart.st"):
        RatioGrid("005930", _make_features(), pd.Timestamp("2020-06-30"))
    # 예외 없이 도달 = 통과


# ---- RatioGrid -------------------------------------------------------------


def test_ratio_grid_normal() -> None:
    """정상 (4 비율) → st.plotly_chart 호출, EmptyState 미호출."""
    with (
        patch("app.components.chart.st") as mock_st,
        patch("app.components.chart.EmptyState") as mock_empty,
    ):
        RatioGrid("005930", _make_features(), pd.Timestamp("2020-06-30"))
        mock_st.plotly_chart.assert_called_once()
        mock_empty.assert_not_called()


def test_ratio_grid_features_none() -> None:
    """features None → EmptyState 위임."""
    with (
        patch("app.components.chart.st") as mock_st,
        patch("app.components.chart.EmptyState") as mock_empty,
    ):
        RatioGrid("005930", None, pd.Timestamp("2020-06-30"))
        mock_empty.assert_called_once()
        mock_st.plotly_chart.assert_not_called()


def test_ratio_grid_features_empty() -> None:
    """features empty → EmptyState 위임."""
    with (
        patch("app.components.chart.st") as mock_st,
        patch("app.components.chart.EmptyState") as mock_empty,
    ):
        RatioGrid("005930", pd.DataFrame(), pd.Timestamp("2020-06-30"))
        mock_empty.assert_called_once()
        mock_st.plotly_chart.assert_not_called()


def test_ratio_grid_nan_gap() -> None:
    """NaN 비율 (gap) → 정상 렌더 (NaN 은 plotly gap)."""
    feats = _make_features()
    feats.loc[1, "debt_ratio"] = float("nan")
    with patch("app.components.chart.st") as mock_st:
        RatioGrid("005930", feats, pd.Timestamp("2020-06-30"))
        mock_st.plotly_chart.assert_called_once()


# ---- Q2 (A): EmptyState 위임 회귀 -----------------------------------------


def test_empty_state_delegation_message() -> None:
    """Q2 (A): 빈 상태가 EmptyState 에 종목·안내 메시지로 위임됨."""
    with (
        patch("app.components.chart.st"),
        patch("app.components.chart.EmptyState") as mock_empty,
    ):
        PriceChartWithStateOverlay("005930", "삼성전자", None, None, pd.Timestamp("2020-01-05"))
        mock_empty.assert_called_once()
        kwargs = mock_empty.call_args.kwargs
        assert "005930" in kwargs["message"]
        assert kwargs.get("suggestion")  # 다음 행동 제안 전달


# ---- StateStripeChart (단위 k) ---------------------------------------------


def test_state_stripe_normal() -> None:
    """정상 state_series → st.plotly_chart 호출, EmptyState 미호출."""
    with (
        patch("app.components.chart.st") as mock_st,
        patch("app.components.chart.EmptyState") as mock_empty,
    ):
        StateStripeChart(_make_state_series())
        mock_st.plotly_chart.assert_called_once()
        mock_empty.assert_not_called()


def test_state_stripe_none_emptystate() -> None:
    """None/empty state_series → EmptyState 위임, 차트 미호출."""
    with (
        patch("app.components.chart.st") as mock_st,
        patch("app.components.chart.EmptyState") as mock_empty,
    ):
        StateStripeChart(None)
        mock_empty.assert_called_once()
        mock_st.plotly_chart.assert_not_called()


# ---- 검증 1: 함수명 정정 ---------------------------------------------------


def test_component_names_state_not_regime() -> None:
    """검증 1: PriceChartWithStateOverlay·RatioGrid (regime 부재)."""
    from app import components
    from app.components import chart

    assert hasattr(components, "PriceChartWithStateOverlay")
    assert hasattr(components, "RatioGrid")
    assert not hasattr(chart, "render_price_chart_with_regime")
    assert not hasattr(chart, "render_ratio_grid")
    assert not hasattr(chart, "PriceChartWithRegime")


def test_mock_sanity() -> None:
    """MagicMock 패턴 검증 (테스트 자체 정합)."""
    m = MagicMock()
    m.plotly_chart("x")
    m.plotly_chart.assert_called_once()
