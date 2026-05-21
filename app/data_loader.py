"""app/ 정적 데이터 로드 layer (단계 4, PROGRESS §5.7).

CLAUDE.md §8.6: app/ 는 *정적 읽기 전용*. 모든 데이터는 *이미 산출된*
yaml/parquet/md 만 읽음. 학습·계산·페치 0회.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
D2_RESULTS = PROJECT_ROOT / "data" / "interim" / "train_d2_baseline" / "results.yaml"
REGIME_RESULTS = PROJECT_ROOT / "data" / "interim" / "regime" / "results.yaml"
REGIME_COMPARISON = PROJECT_ROOT / "data" / "interim" / "regime" / "comparison_summary.yaml"
REGIME_STATE_SERIES = PROJECT_ROOT / "data" / "interim" / "regime" / "state_series.parquet"
REFETCH_SUMMARY = PROJECT_ROOT / "data" / "interim" / "refetch_notfound_ofs" / "summary.yaml"
D2_PREDICTIONS = PROJECT_ROOT / "data" / "interim" / "train_d2_baseline" / "predictions.parquet"
D2_FEATURES = PROJECT_ROOT / "data" / "interim" / "train_d2_baseline" / "features.parquet"
KOSPI200_DIR = PROJECT_ROOT / "data" / "external" / "kospi200_quarterly"
KRX_OHLCV_DIR = PROJECT_ROOT / "data" / "raw" / "krx" / "ohlcv"
FDR_LISTING = PROJECT_ROOT / "data" / "raw" / "fdr" / "stocklisting_kospi.parquet"


def _load_yaml(path: Path) -> dict[str, Any] | None:
    """yaml 정적 로드. 파일 부재 시 None."""
    if not path.exists():
        return None
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_d2_results() -> dict[str, Any] | None:
    """D2 baseline 학습 결과 (B-4, §5.5.17)."""
    return _load_yaml(D2_RESULTS)


def load_regime_results() -> dict[str, Any] | None:
    """HMM K=3 baseline 결과 (§5.6.1)."""
    return _load_yaml(REGIME_RESULTS)


def load_regime_comparison() -> dict[str, Any] | None:
    """HMM vs GMM vs K-Means 비교 (§5.6.2)."""
    return _load_yaml(REGIME_COMPARISON)


def load_regime_state_series() -> pd.DataFrame | None:
    """국면 state 시계열 (2,273 rows: date, state_idx, state_label)."""
    if not REGIME_STATE_SERIES.exists():
        return None
    return pd.read_parquet(REGIME_STATE_SERIES)


def load_refetch_summary() -> dict[str, Any] | None:
    """(A) OFS 재페치 결과 (§5.5.17)."""
    return _load_yaml(REFETCH_SUMMARY)


def load_model_card(name: str) -> str | None:
    """모델 카드 markdown 로드 (d2_baseline / regime)."""
    path = REPORTS_DIR / f"{name}_model_card.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


# ============================================================================
# 사이클 2 — 종목 분석 페이지용 신규 로드 함수
# ============================================================================


def load_predictions() -> pd.DataFrame | None:
    """D2 predictions — ticker × as_of × proba × label × class_weight.

    train_d2_baseline.py B-4 의 산출물. 평가 9 fold 의 test cells × 2 ablation.
    """
    if not D2_PREDICTIONS.exists():
        return None
    df = pd.read_parquet(D2_PREDICTIONS)
    df["test_as_of"] = pd.to_datetime(df["test_as_of"])
    return df


def load_features_timeseries() -> pd.DataFrame | None:
    """features baseline 시계열 — ticker × as_of × 4 ratio + fs_div + label.

    전체 grid (40 분기) × universe = 8,008 cells.
    """
    if not D2_FEATURES.exists():
        return None
    df = pd.read_parquet(D2_FEATURES)
    df["as_of"] = pd.to_datetime(df["as_of"])
    return df


def load_ticker_name_map() -> dict[str, str]:
    """universe ticker → 종목명 매핑 (kospi200_quarterly CSV 의 종목명 컬럼).

    cp949 인코딩 → Python utf-8 string 변환. 분기 CSV 들의 *최신 종목명*
    사용 (분기마다 종목명이 바뀌는 경우 드물지만 가능 — 가장 최근 분기 우선).
    """
    if not KOSPI200_DIR.exists():
        return {}
    name_map: dict[str, str] = {}
    # 정렬된 분기 CSV — 오래된 → 최신 순. dict 가 *나중에 덮어쓰기* 하므로
    # 최종 매핑은 *가장 최근 분기의 종목명*.
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
    return name_map


def load_ticker_marcap_map() -> dict[str, float]:
    """ticker → 시가총액 매핑 (FDR listing 현 시점 스냅샷).

    한계: FDR listing 은 *현 시점* 만. 과거 시점 시가총액 추적 X.
    Streamlit 헤더 표시용 *근사 시총* 으로만 사용. 한계는 페이지에 명시.
    """
    if not FDR_LISTING.exists():
        return {}
    df = pd.read_parquet(FDR_LISTING)
    if "Code" not in df.columns or "Marcap" not in df.columns:
        return {}
    return dict(zip(df["Code"].astype(str), df["Marcap"], strict=True))


def load_ticker_ohlcv(ticker: str) -> pd.DataFrame | None:
    """단일 ticker 의 KRX OHLCV parquet.

    cp949 한국어 컬럼명 (`시가`·`고가`·`저가`·`종가`·`거래량`·`등락률`).
    index = 날짜 (datetime).
    """
    path = KRX_OHLCV_DIR / f"{ticker}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    return df


def load_as_of_grid() -> list[pd.Timestamp]:
    """평가 9 fold + skipped 19 fold 의 test_as_of 통합 grid (28 분기말).

    종목 분석 페이지의 *분석 시점* 선택 옵션.
    """
    feats = load_features_timeseries()
    if feats is None:
        return []
    return sorted(feats["as_of"].unique().tolist())
