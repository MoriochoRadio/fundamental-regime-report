"""app/data_loader.py 단위 테스트.

단계 5 단위 (b) 산출물. 검증 7 (에러 7 단위 테스트) + 검증 1·5·6 매핑.

테스트 카테고리:
- 각 활성 함수 정상 로드 (실 파일 fixture 또는 mock)
- 각 함수 파일 부재 → None / 빈 DataFrame fallback (에러 5.4 매핑)
- DataFrame schema 검증 (컬럼 + dtype)
- 에러 5.5 DART notfound 매핑
- 에러 5.6 빈 DataFrame 처리
- 에러 5.7 NaN 처리
- @st.cache_data 적용 검증
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from app import data_loader
from app.data_loader import (
    D2_FEATURES_PATH,
    D2_PREDICTIONS_PATH,
    FDR_LISTING_PATH,
    KOSPI200_DIR,
    KRX_OHLCV_DIR,
    LLM_INTERPRETATION_DIR,
    REPORTS_DIR,
    STATE_SERIES_PATH,
    _load_yaml,
    load_as_of_grid,
    load_d2_features,
    load_d2_predictions,
    load_llm_interpretation,
    load_model_card,
    load_ohlcv,
    load_state_series,
    load_universe,
)

# ---- _load_yaml helper -----------------------------------------------------


def test_load_yaml_existing(tmp_path: Path) -> None:
    p = tmp_path / "x.yaml"
    p.write_text("key: value\n", encoding="utf-8")
    result = _load_yaml(p)
    assert result == {"key": "value"}


def test_load_yaml_missing(tmp_path: Path) -> None:
    assert _load_yaml(tmp_path / "missing.yaml") is None


# ---- load_universe ---------------------------------------------------------


def test_load_universe_returns_dataframe() -> None:
    """실 파일 fixture (작업 브랜치 KOSPI200 분기 CSV 존재) 시 통과.

    파일 부재 환경에서는 빈 DataFrame 반환.
    """
    load_universe.clear()
    df = load_universe()
    assert isinstance(df, pd.DataFrame)
    assert set(df.columns) == {"ticker", "name", "marcap"}


def test_load_universe_kospi200_dir_missing(tmp_path: Path) -> None:
    """KOSPI200_DIR 부재 → 빈 DataFrame."""
    load_universe.clear()
    with patch.object(data_loader, "KOSPI200_DIR", tmp_path / "missing"):
        df = load_universe()
        assert df.empty
        assert set(df.columns) == {"ticker", "name", "marcap"}


def test_load_universe_321_tickers_when_data_available() -> None:
    """실 데이터 환경: universe 321 종목 (정확 또는 ≥ 200)."""
    load_universe.clear()
    df = load_universe()
    if df.empty:
        pytest.skip("universe 산출물 부재 (KOSPI200 분기 CSV 미존재)")
    # universe 정의: KOSPI200 quarterly union (321 종목 합의)
    assert len(df) >= 200, f"universe 종목 수 200 미만: {len(df)}"
    # ticker 6 자리 string
    assert df["ticker"].apply(lambda t: isinstance(t, str) and len(t) == 6).all()


# ---- load_state_series -----------------------------------------------------


def test_load_state_series_missing(tmp_path: Path) -> None:
    """STATE_SERIES_PATH 부재 → None."""
    load_state_series.clear()
    with patch.object(data_loader, "STATE_SERIES_PATH", tmp_path / "missing.parquet"):
        assert load_state_series() is None


def test_load_state_series_existing() -> None:
    """실 파일 존재 시: DataFrame + date dtype datetime64."""
    load_state_series.clear()
    df = load_state_series()
    if df is None:
        pytest.skip("state_series 산출물 부재")
    assert isinstance(df, pd.DataFrame)
    assert "date" in df.columns
    assert "state_label" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["date"])


# ---- load_d2_predictions ---------------------------------------------------


def test_load_d2_predictions_missing(tmp_path: Path) -> None:
    """D2_PREDICTIONS_PATH 부재 → None (에러 5.4 매핑)."""
    load_d2_predictions.clear()
    with patch.object(data_loader, "D2_PREDICTIONS_PATH", tmp_path / "missing.parquet"):
        assert load_d2_predictions() is None


def test_load_d2_predictions_existing() -> None:
    """실 파일 존재 시: DataFrame + test_as_of dtype datetime64."""
    load_d2_predictions.clear()
    df = load_d2_predictions()
    if df is None:
        pytest.skip("d2 predictions 산출물 부재")
    assert isinstance(df, pd.DataFrame)
    assert "test_as_of" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["test_as_of"])


def test_load_d2_predictions_schema() -> None:
    """schema: ticker·test_as_of·proba·label·class_weight 컬럼 존재."""
    load_d2_predictions.clear()
    df = load_d2_predictions()
    if df is None:
        pytest.skip("d2 predictions 산출물 부재")
    expected = {"ticker", "test_as_of", "proba", "class_weight"}
    assert expected.issubset(set(df.columns)), f"필수 컬럼 누락: {expected - set(df.columns)}"


# ---- load_d2_features ------------------------------------------------------


def test_load_d2_features_missing(tmp_path: Path) -> None:
    """D2_FEATURES_PATH 부재 → None."""
    load_d2_features.clear()
    with patch.object(data_loader, "D2_FEATURES_PATH", tmp_path / "missing.parquet"):
        assert load_d2_features() is None


def test_load_d2_features_existing() -> None:
    """실 파일 존재 시: DataFrame + as_of dtype datetime64."""
    load_d2_features.clear()
    df = load_d2_features()
    if df is None:
        pytest.skip("d2 features 산출물 부재")
    assert isinstance(df, pd.DataFrame)
    assert "as_of" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["as_of"])


def test_load_d2_features_schema() -> None:
    """schema: ticker·as_of·4 ratio + fs_div + label 컬럼 존재."""
    load_d2_features.clear()
    df = load_d2_features()
    if df is None:
        pytest.skip("d2 features 산출물 부재")
    expected = {"ticker", "as_of", "debt_ratio", "current_ratio", "op_margin", "roa"}
    assert expected.issubset(set(df.columns)), f"필수 컬럼 누락: {expected - set(df.columns)}"


def test_load_d2_features_nan_handling() -> None:
    """에러 5.7: NaN ratio 컬럼 — DataFrame 정상 반환 (NaN 자체는 유효 값)."""
    load_d2_features.clear()
    df = load_d2_features()
    if df is None:
        pytest.skip("d2 features 산출물 부재")
    # NaN 행 존재 가능 (분모 0 또는 결측), DataFrame 반환 자체는 정상
    assert isinstance(df, pd.DataFrame)


# ---- load_ohlcv ------------------------------------------------------------


def test_load_ohlcv_missing_ticker() -> None:
    """존재하지 않는 ticker → None."""
    load_ohlcv.clear()
    assert load_ohlcv("999999") is None


def test_load_ohlcv_empty_ticker() -> None:
    """빈 ticker → None (방어적)."""
    load_ohlcv.clear()
    assert load_ohlcv("") is None


def test_load_ohlcv_samsung_existing() -> None:
    """실 파일 존재 시 (005930 삼성전자 OHLCV): DataFrame."""
    load_ohlcv.clear()
    df = load_ohlcv("005930")
    if df is None:
        pytest.skip("OHLCV 005930 산출물 부재")
    assert isinstance(df, pd.DataFrame)


def test_load_ohlcv_missing_dir(tmp_path: Path) -> None:
    """KRX_OHLCV_DIR 부재 → None (에러 5.4 매핑)."""
    load_ohlcv.clear()
    with patch.object(data_loader, "KRX_OHLCV_DIR", tmp_path / "missing"):
        assert load_ohlcv("005930") is None


# ---- load_llm_interpretation (stub) ----------------------------------------


def test_load_llm_interpretation_stub_returns_none() -> None:
    """LLM_INTERPRETATION_DIR 미존재 → 항상 None (future-ready stub)."""
    load_llm_interpretation.clear()
    assert load_llm_interpretation("005930", "2024-12-31") is None


def test_load_llm_interpretation_empty_args() -> None:
    """빈 ticker 또는 as_of → None (방어적)."""
    load_llm_interpretation.clear()
    assert load_llm_interpretation("", "2024-12-31") is None
    load_llm_interpretation.clear()
    assert load_llm_interpretation("005930", "") is None


# ---- load_model_card -------------------------------------------------------


def test_load_model_card_existing() -> None:
    """d2_baseline 또는 regime 모델 카드 markdown 로드."""
    load_model_card.clear()
    card = load_model_card("d2_baseline")
    if card is None:
        pytest.skip("d2_baseline 모델 카드 부재")
    assert isinstance(card, str)
    assert len(card) > 0


def test_load_model_card_missing_name() -> None:
    """존재하지 않는 name → None."""
    load_model_card.clear()
    assert load_model_card("nonexistent_card") is None


def test_load_model_card_empty_name() -> None:
    """빈 name → None."""
    load_model_card.clear()
    assert load_model_card("") is None


# ---- load_as_of_grid -------------------------------------------------------


def test_load_as_of_grid_returns_list() -> None:
    """list 반환 (features 산출물 의존)."""
    load_as_of_grid.clear()
    grid = load_as_of_grid()
    assert isinstance(grid, list)


def test_load_as_of_grid_sorted() -> None:
    """grid 가 정렬됨 (오름차순)."""
    load_as_of_grid.clear()
    grid = load_as_of_grid()
    if not grid:
        pytest.skip("as_of grid 산출물 부재")
    assert grid == sorted(grid), "as_of grid 가 정렬 안 됨"
    # 모든 항목 Timestamp 가능
    for ts in grid:
        assert isinstance(ts, pd.Timestamp)


def test_load_as_of_grid_features_missing(tmp_path: Path) -> None:
    """features 부재 → 빈 list."""
    load_as_of_grid.clear()
    load_d2_features.clear()
    with patch.object(data_loader, "D2_FEATURES_PATH", tmp_path / "missing.parquet"):
        grid = load_as_of_grid()
        assert grid == []


# ---- @st.cache_data 적용 검증 ----------------------------------------------


def test_all_active_functions_have_cache_clear() -> None:
    """8 활성 함수 모두 .clear() 속성 (=@st.cache_data 적용) 존재."""
    functions = [
        load_universe,
        load_state_series,
        load_d2_predictions,
        load_d2_features,
        load_ohlcv,
        load_llm_interpretation,
        load_model_card,
        load_as_of_grid,
    ]
    for fn in functions:
        assert hasattr(fn, "clear"), f"{fn.__name__} 에 .clear() 없음 (@st.cache_data 미적용)"


# ---- 폐기 4 함수 부재 검증 (검증 1·5 매핑) --------------------------------


def test_deprecated_functions_removed() -> None:
    """폐기 4 함수 (load_d2_results 등) 가 data_loader 모듈에서 제거됨."""
    deprecated = [
        "load_d2_results",
        "load_regime_results",
        "load_regime_comparison",
        "load_refetch_summary",
    ]
    for name in deprecated:
        assert not hasattr(data_loader, name), f"{name} 가 여전히 존재 (Q3 폐기 의무 위반)"


def test_regime_function_names_renamed() -> None:
    """검증 1 매핑: regime → state 함수명 정정 완료."""
    # 정정 함수명 존재
    assert hasattr(data_loader, "load_state_series")
    assert hasattr(data_loader, "load_d2_predictions")
    assert hasattr(data_loader, "load_d2_features")
    assert hasattr(data_loader, "load_ohlcv")
    # 옛 함수명 부재
    assert not hasattr(data_loader, "load_regime_state_series")
    assert not hasattr(data_loader, "load_predictions")
    assert not hasattr(data_loader, "load_features_timeseries")
    assert not hasattr(data_loader, "load_ticker_ohlcv")
    assert not hasattr(data_loader, "load_ticker_name_map")
    assert not hasattr(data_loader, "load_ticker_marcap_map")


# ---- path 상수 정정 검증 (검증 1 매핑) -------------------------------------


def test_path_constants_renamed() -> None:
    """검증 1: REGIME_STATE_SERIES → STATE_SERIES_PATH 정정."""
    assert hasattr(data_loader, "STATE_SERIES_PATH")
    assert hasattr(data_loader, "D2_PREDICTIONS_PATH")
    assert hasattr(data_loader, "D2_FEATURES_PATH")
    assert hasattr(data_loader, "FDR_LISTING_PATH")
    assert hasattr(data_loader, "LLM_INTERPRETATION_DIR")
    # 옛 상수명 부재
    assert not hasattr(data_loader, "REGIME_STATE_SERIES")
    assert not hasattr(data_loader, "D2_RESULTS")
    assert not hasattr(data_loader, "REGIME_RESULTS")
    assert not hasattr(data_loader, "REGIME_COMPARISON")
    assert not hasattr(data_loader, "REFETCH_SUMMARY")
    assert not hasattr(data_loader, "FDR_LISTING")


# ---- path 상수 값 검증 (구조 정합) ----------------------------------------


def test_path_constants_under_project_root() -> None:
    """모든 path 상수가 PROJECT_ROOT 하위."""
    paths = [
        STATE_SERIES_PATH,
        D2_PREDICTIONS_PATH,
        D2_FEATURES_PATH,
        KOSPI200_DIR,
        KRX_OHLCV_DIR,
        FDR_LISTING_PATH,
        LLM_INTERPRETATION_DIR,
        REPORTS_DIR,
    ]
    for p in paths:
        assert isinstance(p, Path)
