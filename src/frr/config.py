"""데이터 파이프라인 설정 로더.

`configs/data.yaml` 을 읽어 동결 dataclass 트리로 반환한다. pydantic
같은 무거운 의존성은 도입하지 않는다 — 본 프로젝트의 설정은 *작고
변경 빈도가 낮음*. 필요해지면 dataclass 를 pydantic 으로 교체하기
쉬운 형태로만 유지한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AnalysisWindow:
    """분석 기간 (CLAUDE.md §4.1 의 확정값)."""

    start: date
    end: date


@dataclass(frozen=True)
class UniverseConfig:
    """point-in-time 유니버스 매니페스트 위치."""

    manifest_path: Path


@dataclass(frozen=True)
class DARTConfig:
    """DART 정기보고서 lag·period·fs_div."""

    filing_lag_business_days: int
    periods: tuple[str, ...]
    fs_div: str


@dataclass(frozen=True)
class DataConfig:
    """`configs/data.yaml` 의 전체 구조."""

    analysis: AnalysisWindow
    universe: UniverseConfig
    dart: DARTConfig


# ---- 로더 ----------------------------------------------------------------


def load_data_config(path: Path) -> DataConfig:
    """yaml 경로를 받아 `DataConfig` 로 반환. 필수 키 누락은 명확한 에러."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: 최상위가 매핑이 아님")

    try:
        analysis = AnalysisWindow(
            start=_as_date(raw["analysis"]["start"]),
            end=_as_date(raw["analysis"]["end"]),
        )
        if analysis.start > analysis.end:
            raise ValueError(f"analysis.start={analysis.start} > end={analysis.end}")

        universe = UniverseConfig(
            manifest_path=Path(str(raw["universe"]["manifest_path"])),
        )

        dart_raw = raw["dart"]
        dart = DARTConfig(
            filing_lag_business_days=int(dart_raw["filing_lag_business_days"]),
            periods=tuple(str(p) for p in dart_raw["periods"]),
            fs_div=str(dart_raw["fs_div"]),
        )
    except KeyError as e:
        raise KeyError(f"{path}: 필수 키 누락 {e}") from e

    return DataConfig(analysis=analysis, universe=universe, dart=dart)


def _as_date(v: Any) -> date:
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        return date.fromisoformat(v)
    raise TypeError(f"date 로 변환 불가: {v!r} (type={type(v).__name__})")
