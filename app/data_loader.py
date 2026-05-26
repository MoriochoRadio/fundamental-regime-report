"""app/ 정적 데이터 로드 layer.

CLAUDE.md §8.6: app/ 는 *정적 읽기 전용*. 모든 데이터는 *이미 산출된*
yaml/parquet/md 만 읽음. 학습·계산·페치 0회.

단계 5 단위 (b) 산출물. 4 단계 docs/tech_architecture.md §3 데이터 흐름
spec 직접 매핑.

활성 8 함수 + helper 1:
- load_universe — ticker·name·marcap 통합 (Q2 통합)
- load_state_series — 시장 상태 시계열 (← load_regime_state_series 정정)
- load_d2_predictions — D2 위험 예측 (← load_predictions 정정)
- load_d2_features — D2 features (← load_features_timeseries 정정)
- load_ohlcv(ticker) — 종목별 OHLCV lazy load (← load_ticker_ohlcv 정정)
- load_llm_interpretation(ticker, as_of) — LLM 서술 stub (신규, future-ready)
- load_model_card(name) — 모델 카드 markdown
- load_as_of_grid — 분석 시점 grid
- _load_yaml(path) — yaml helper

@st.cache_data 의무 (4 단계 §6.1, 모든 활성 함수).

폐기 4 함수 (FR-9 Won't 매핑):
- load_d2_results / load_regime_results / load_regime_comparison /
  load_refetch_summary — ML 학습 결과 yaml 외부 UI 노출 폐기

검증 1 매핑 (regime → state 코드 활성 일관 정정): 함수명 + path 상수.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"

# Path 상수 (검증 1: regime → state 정정. 파일 경로 자체는 미변경 — data
# layer 보존)
STATE_SERIES_PATH = PROJECT_ROOT / "data" / "interim" / "regime" / "state_series.parquet"
D2_PREDICTIONS_PATH = (
    PROJECT_ROOT / "data" / "interim" / "train_d2_baseline" / "predictions.parquet"
)
D2_FEATURES_PATH = PROJECT_ROOT / "data" / "interim" / "train_d2_baseline" / "features.parquet"
KOSPI200_DIR = PROJECT_ROOT / "data" / "external" / "kospi200_quarterly"
KRX_OHLCV_DIR = PROJECT_ROOT / "data" / "raw" / "krx" / "ohlcv"
FDR_LISTING_PATH = PROJECT_ROOT / "data" / "raw" / "fdr" / "stocklisting_kospi.parquet"
# 신규 (future-ready): LLM 빌드타임 배치 서술 정적 산출물
LLM_INTERPRETATION_DIR = PROJECT_ROOT / "data" / "interim" / "llm_interpretations"


def _load_yaml(path: Path) -> dict[str, Any] | None:
    """yaml 정적 로드. 파일 부재 시 None."""
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@st.cache_data
def load_universe() -> pd.DataFrame:
    """KOSPI200 universe 메타: ticker · name · marcap (321 종목 통합).

    - name: kospi200_quarterly CSV 들의 *가장 최근 분기* 종목명
    - marcap: FDR listing *현 시점* 시가총액 (과거 시점 추적 X)

    Returns:
        DataFrame[ticker, name, marcap] (321 rows 예상). 빈 입력 시 빈 DataFrame.
    """
    name_map: dict[str, str] = {}
    if KOSPI200_DIR.exists():
        csv_files = sorted(KOSPI200_DIR.glob("kospi200_*.csv"))
        for csv in csv_files:
            try:
                df = pd.read_csv(csv, encoding="cp949", dtype={"종목코드": "string"})
            except Exception:
                continue
            for _, row in df.iterrows():
                ticker = row.get("종목코드")
                name = row.get("종목명")
                if isinstance(ticker, str) and isinstance(name, str):
                    name_map[ticker] = name

    marcap_map: dict[str, float] = {}
    if FDR_LISTING_PATH.exists():
        marcap_df = pd.read_parquet(FDR_LISTING_PATH)
        if "Code" in marcap_df.columns and "Marcap" in marcap_df.columns:
            marcap_map = dict(zip(marcap_df["Code"].astype(str), marcap_df["Marcap"], strict=True))

    if not name_map:
        return pd.DataFrame(columns=["ticker", "name", "marcap"])

    rows = [{"ticker": t, "name": n, "marcap": marcap_map.get(t)} for t, n in name_map.items()]
    return pd.DataFrame(rows).sort_values("ticker").reset_index(drop=True)


@st.cache_data
def load_state_series() -> pd.DataFrame | None:
    """시장 상태 시계열 (date, state_idx, state_label, 2,273 rows).

    Phase 4 정정: load_regime_state_series → load_state_series (검증 1 매핑).
    """
    if not STATE_SERIES_PATH.exists():
        return None
    df = pd.read_parquet(STATE_SERIES_PATH)
    if df.empty:
        return df
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data
def load_d2_predictions() -> pd.DataFrame | None:
    """D2 위험 예측 (ticker × as_of × proba × label × class_weight).

    Phase 4 정정: load_predictions → load_d2_predictions (4 단계 §3 spec
    정렬).
    """
    if not D2_PREDICTIONS_PATH.exists():
        return None
    df = pd.read_parquet(D2_PREDICTIONS_PATH)
    if df.empty:
        return df
    df = df.copy()
    if "test_as_of" in df.columns:
        df["test_as_of"] = pd.to_datetime(df["test_as_of"])
    return df


@st.cache_data
def load_d2_features() -> pd.DataFrame | None:
    """D2 features (ticker × as_of × 4 ratio + fs_div + label, 8,008 cells).

    Phase 4 정정: load_features_timeseries → load_d2_features.
    """
    if not D2_FEATURES_PATH.exists():
        return None
    df = pd.read_parquet(D2_FEATURES_PATH)
    if df.empty:
        return df
    df = df.copy()
    if "as_of" in df.columns:
        df["as_of"] = pd.to_datetime(df["as_of"])
    return df


@st.cache_data
def load_ohlcv(ticker: str) -> pd.DataFrame | None:
    """단일 ticker 의 KRX OHLCV parquet (4 단계 §6.2 lazy load 직접 매핑).

    cp949 한국어 컬럼명 (`시가`·`고가`·`저가`·`종가`·`거래량`·`등락률`).
    index = 날짜 (datetime).

    Phase 4 정정: load_ticker_ohlcv → load_ohlcv (4 단계 §3 spec 정렬).
    """
    if not ticker:
        return None
    path = KRX_OHLCV_DIR / f"{ticker}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    return df


@st.cache_data
def load_llm_interpretation(ticker: str, as_of: str) -> dict[str, Any] | None:
    """LLM 빌드타임 배치 서술 정적 로드 (4 단계 §3 spec, future-ready stub).

    CLAUDE.md §3.4 *런타임 LLM 호출 0회* 원칙 직접 매핑.

    현 단계: LLM_INTERPRETATION_DIR 미존재 → 항상 None. 단계 6/7 진입 시
    본격 구현 (LLM 빌드타임 배치 산출).

    Args:
        ticker: 종목 코드 (6 자리)
        as_of: 분석 시점 ISO 8601 ("YYYY-MM-DD")

    Returns:
        dict (서술 JSON) 또는 None (stub / 미존재).
    """
    if not LLM_INTERPRETATION_DIR.exists():
        return None
    if not ticker or not as_of:
        return None
    path = LLM_INTERPRETATION_DIR / f"{ticker}_{as_of}.yaml"
    return _load_yaml(path)


@st.cache_data
def load_model_card(name: str) -> str | None:
    """모델 카드 markdown 로드 (d2_baseline / regime).

    3 단계 §1.4 한계 페이지 link 매핑. (C) 그대로 재사용 자산.
    """
    if not name:
        return None
    path = REPORTS_DIR / f"{name}_model_card.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


@st.cache_data
def load_as_of_grid() -> list[pd.Timestamp]:
    """평가 9 fold + skipped 19 fold 의 test_as_of 통합 grid (28 분기말).

    종목 분석 페이지의 *분석 시점* 선택 옵션. (C) 그대로 재사용 (단, 내부
    호출 함수명 정정).
    """
    feats = load_d2_features()
    if feats is None or feats.empty or "as_of" not in feats.columns:
        return []
    return sorted(feats["as_of"].unique().tolist())
