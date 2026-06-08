"""features 빌더 룩어헤드 차단 — (β) 런타임 mock contract (PROGRESS §5.5.14).

(α) AST 블랙리스트 (tests/test_isolation.py iii) 가 *OpenDartReader 직접 호출*
차단이라면, 본 (β) 는 *빌더에 mock reporter 주입 → mock 이 받은 모든 시점
인자가 as_of 이하* 검증.

vacuous 위험 양 단계 상호 보완:
- (α) 단독은 getattr·간접 호출에 vacuous → (β) 가 실제 호출 패턴 검증
- (β) 단독은 *코드 작성 시점에 mock 호출 안 한 경우* 회귀 검출 못함 →
  (α) 가 *지속 회귀 게이트*

(β) 검증 대상:
- build_features 가 호출하는 reporter 메서드 (latest_available 등) 의
  *t 인자* 가 as_of 이하
- universe_loader 의 as_of(t) 인자가 build_features 의 as_of 이하

설계 (PROGRESS §5.5.14 (b-2)): mock 정확한 시점 검증 로직은 *YAGNI* —
현 시점 baseline.py 가 reporter.latest_available 하나만 호출. 호출 패턴
확장 시 본 테스트도 추가.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from frr.features.baseline import build_features


class _MockReporter:
    """build_features 가 받은 시점 인자 추적 + 빈 결과 반환."""

    def __init__(self) -> None:
        self.received_times: list[date] = []
        self.received_years: list[list[int]] = []

    def latest_available(self, ticker: str, t: date, years: list[int]) -> Any:
        self.received_times.append(t)
        self.received_years.append(list(years))
        return None  # 빈 결과 — build_features 는 empty row 반환


class _MockUniverseLoader:
    """build_features 가 받은 universe 호출 시점 추적."""

    def __init__(self, tickers_at_quarter: dict[str, list[str]]) -> None:
        self._tickers = tickers_at_quarter
        self.received_as_of_times: list[date] = []

    def as_of(self, t: date) -> str:
        self.received_as_of_times.append(t)
        return "2020Q1"

    def tickers(self, quarter: str) -> list[str]:
        return self._tickers.get(quarter, [])


def test_build_features_reporter_receives_t_le_as_of(tmp_path: Path) -> None:
    """build_features 가 reporter.latest_available 에 넘긴 시점 ≤ as_of."""
    mock_reporter = _MockReporter()
    mock_universe = _MockUniverseLoader({"2020Q1": ["005930"]})
    as_of = date(2020, 6, 30)

    build_features(
        ticker="005930",
        as_of=as_of,
        reporter=mock_reporter,  # type: ignore[arg-type]
        universe_loader=mock_universe,  # type: ignore[arg-type]
        krx_ohlcv_cache_dir=tmp_path,
    )

    assert all(t <= as_of for t in mock_reporter.received_times), (
        f"reporter 가 as_of({as_of}) 초과 시점 인자를 받음: {mock_reporter.received_times}"
    )


def test_build_features_universe_receives_t_le_as_of(tmp_path: Path) -> None:
    """build_features 가 universe_loader.as_of 에 넘긴 시점 ≤ as_of."""
    mock_reporter = _MockReporter()
    mock_universe = _MockUniverseLoader({"2020Q1": ["005930"]})
    as_of = date(2020, 6, 30)

    build_features(
        ticker="005930",
        as_of=as_of,
        reporter=mock_reporter,  # type: ignore[arg-type]
        universe_loader=mock_universe,  # type: ignore[arg-type]
        krx_ohlcv_cache_dir=tmp_path,
    )

    assert all(t <= as_of for t in mock_universe.received_as_of_times), (
        f"universe 가 as_of({as_of}) 초과 시점 인자를 받음: {mock_universe.received_as_of_times}"
    )


def test_build_features_reporter_years_le_as_of_year(tmp_path: Path) -> None:
    """build_features 가 reporter 에 넘긴 years 범위가 as_of.year 이하 + 1년 마진.

    baseline.py 의 years = [as_of.year - 1, as_of.year]. as_of 이후 데이터를
    *시도* 자체 안 함 (reporter.latest_available 의 룩어헤드 차단 책임이 별도
    내부에서 작동).
    """
    mock_reporter = _MockReporter()
    mock_universe = _MockUniverseLoader({"2020Q1": ["005930"]})
    as_of = date(2020, 6, 30)

    build_features(
        ticker="005930",
        as_of=as_of,
        reporter=mock_reporter,  # type: ignore[arg-type]
        universe_loader=mock_universe,  # type: ignore[arg-type]
        krx_ohlcv_cache_dir=tmp_path,
    )

    # years 의 모든 값 ≤ as_of.year
    for years_call in mock_reporter.received_years:
        for y in years_call:
            assert y <= as_of.year, f"reporter 가 as_of.year({as_of.year}) 초과 연도를 받음: {y}"


def test_build_features_returns_empty_row_when_reporter_returns_none(tmp_path: Path) -> None:
    """reporter.latest_available 가 None 반환 시 빈 row DataFrame 반환."""
    mock_reporter = _MockReporter()
    mock_universe = _MockUniverseLoader({"2020Q1": ["005930"]})
    as_of = date(2020, 6, 30)

    result = build_features(
        ticker="005930",
        as_of=as_of,
        reporter=mock_reporter,  # type: ignore[arg-type]
        universe_loader=mock_universe,  # type: ignore[arg-type]
        krx_ohlcv_cache_dir=tmp_path,
    )

    assert len(result) == 1
    assert result.iloc[0]["ticker"] == "005930"
    assert result.iloc[0]["as_of"] == as_of
    assert pd.isna(result.iloc[0]["debt_ratio"])
    assert pd.isna(result.iloc[0]["op_margin"])
