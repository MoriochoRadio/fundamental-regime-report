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
