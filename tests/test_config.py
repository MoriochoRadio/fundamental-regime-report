"""config 로더 단위 테스트.

실제 `configs/data.yaml` 로드 검증 + tmp_path 격리 합성 yaml 로
경계 케이스 검증.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import date
from pathlib import Path

import pytest

from frr.config import (
    AnalysisWindow,
    DARTConfig,
    DataConfig,
    UniverseConfig,
    load_data_config,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REAL_CONFIG = PROJECT_ROOT / "configs" / "data.yaml"


# ---- 실 yaml 로드 -------------------------------------------------------


def test_load_real_data_config_matches_locked_values() -> None:
    """실제 `configs/data.yaml` 이 CLAUDE.md 의 확정값과 일치."""
    cfg = load_data_config(REAL_CONFIG)

    assert cfg.analysis.start == date(2015, 1, 1)
    assert cfg.analysis.end == date(2024, 12, 31)
    assert cfg.universe.manifest_path == Path("data/external/kospi200_quarterly/MANIFEST.yaml")
    assert cfg.dart.filing_lag_business_days == 1
    assert cfg.dart.periods == ("Q1", "H1", "Q3", "FY")
    assert cfg.dart.fs_div == "CFS"  # D10 결정 대기 — 단계 2 재검토 대상


def test_loaded_config_is_immutable() -> None:
    """frozen dataclass 인지 — 실수 변경 차단."""
    cfg = load_data_config(REAL_CONFIG)
    with pytest.raises(FrozenInstanceError):
        cfg.analysis.start = date(2020, 1, 1)  # type: ignore[misc]


# ---- 경계 케이스 (tmp_path 격리) ------------------------------------------


def _write_yaml(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_missing_top_level_key_raises(tmp_path: Path) -> None:
    cfg_path = _write_yaml(
        tmp_path / "c.yaml",
        """
analysis:
  start: 2015-01-01
  end: 2024-12-31
# universe·dart 누락
""",
    )
    with pytest.raises(KeyError):
        load_data_config(cfg_path)


def test_start_after_end_raises(tmp_path: Path) -> None:
    cfg_path = _write_yaml(
        tmp_path / "c.yaml",
        """
analysis:
  start: 2024-12-31
  end: 2015-01-01
universe:
  manifest_path: x.yaml
dart:
  filing_lag_business_days: 1
  periods: [FY]
  fs_div: CFS
""",
    )
    with pytest.raises(ValueError, match="start"):
        load_data_config(cfg_path)


def test_date_can_be_str_or_yaml_date(tmp_path: Path) -> None:
    """YAML 1.2 의 자동 date 파싱과 문자열 둘 다 허용."""
    cfg_path = _write_yaml(
        tmp_path / "c.yaml",
        """
analysis:
  start: "2015-01-01"
  end: 2024-12-31
universe:
  manifest_path: m.yaml
dart:
  filing_lag_business_days: 1
  periods: [FY]
  fs_div: CFS
""",
    )
    cfg = load_data_config(cfg_path)
    assert cfg.analysis.start == date(2015, 1, 1)
    assert cfg.analysis.end == date(2024, 12, 31)


def test_periods_become_tuple(tmp_path: Path) -> None:
    """list 입력이 frozen tuple 로 정규화 (해시 가능)."""
    cfg_path = _write_yaml(
        tmp_path / "c.yaml",
        """
analysis:
  start: 2015-01-01
  end: 2024-12-31
universe:
  manifest_path: m.yaml
dart:
  filing_lag_business_days: 1
  periods:
    - Q1
    - H1
  fs_div: CFS
""",
    )
    cfg = load_data_config(cfg_path)
    assert isinstance(cfg.dart.periods, tuple)
    assert cfg.dart.periods == ("Q1", "H1")


def test_explicit_dataclass_types(tmp_path: Path) -> None:
    """클래스 트리가 정상 구성."""
    cfg = load_data_config(REAL_CONFIG)
    assert isinstance(cfg, DataConfig)
    assert isinstance(cfg.analysis, AnalysisWindow)
    assert isinstance(cfg.universe, UniverseConfig)
    assert isinstance(cfg.dart, DARTConfig)
