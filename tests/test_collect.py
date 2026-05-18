"""`frr.data.collect` 단위 테스트.

실 어댑터를 *stub* 으로 주입해 네트워크 없이 collect_universe 의 흐름을
검증한다. 실 수집은 *수동 실행* (시간·DART 한도 부담으로 자동 테스트 X).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from frr.data.collect import (
    CollectionFailure,
    CollectionSummary,
    build_universe_union,
    collect_one_ticker,
    collect_universe,
    write_summary,
)
from frr.data.dart import ReportRef, ReportResult

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---- stub 들 ------------------------------------------------------------


class StubKRX:
    def __init__(self, fail_on: set[str] | None = None) -> None:
        self.calls: list[tuple[str, date, date]] = []
        self.fail_on = fail_on or set()

    def fetch_ohlcv(
        self, ticker: str, start: date, end: date, *, refresh: bool = False
    ) -> pd.DataFrame:
        self.calls.append((ticker, start, end))
        if ticker in self.fail_on:
            raise RuntimeError(f"intentional fail {ticker}")
        return pd.DataFrame({"종가": [100]}, index=pd.to_datetime(["2020-01-02"]))


@dataclass
class StubDART:
    """DARTReporter 인터페이스 흉내. notfound 비율 일부."""

    notfound_periods: set[str] = None  # type: ignore[assignment]
    calls: list[tuple[str, int, str]] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.notfound_periods = self.notfound_periods or set()
        self.calls = []

    def fetch_report(self, ticker: str, year: int, period: str) -> ReportResult:
        self.calls.append((ticker, year, period))
        if period in self.notfound_periods:
            ref = ReportRef(
                ticker=ticker,
                year=year,
                period=period,
                rcept_dt=None,
                available_from=None,
                status="notfound",
            )
            return ReportResult(ref=ref, df=pd.DataFrame())
        ref = ReportRef(
            ticker=ticker,
            year=year,
            period=period,
            rcept_dt=date(year + 1, 3, 31),
            available_from=date(year + 1, 4, 1),
            status="ok",
        )
        return ReportResult(ref=ref, df=pd.DataFrame({"x": [1]}))


# ---- build_universe_union ------------------------------------------------


def test_build_universe_union_real() -> None:
    """실 universe_loader 로 union 추출 — 분기에 따라 약 200~300종목."""
    from frr.data.universe_loader import KOSPI200QuarterlyLoader

    loader = KOSPI200QuarterlyLoader.from_default(project_root=PROJECT_ROOT)
    union = build_universe_union(loader)
    assert 200 <= len(union) <= 500, f"union 크기 이상: {len(union)}"
    # 정렬 + 6자리 str
    assert union == sorted(union)
    assert all(len(t) == 6 for t in union)


# ---- collect_one_ticker --------------------------------------------------


def test_collect_one_ticker_calls_both_adapters() -> None:
    from frr.config import AnalysisWindow, DARTConfig, DataConfig, UniverseConfig

    cfg = DataConfig(
        analysis=AnalysisWindow(start=date(2020, 1, 1), end=date(2021, 12, 31)),
        universe=UniverseConfig(manifest_path=Path("x")),
        dart=DARTConfig(filing_lag_business_days=1, periods=("Q1", "FY"), fs_div="CFS"),
    )
    krx = StubKRX()
    dart = StubDART()
    summary = CollectionSummary()

    collect_one_ticker("005930", cfg, krx, dart, summary)  # type: ignore[arg-type]

    assert len(krx.calls) == 1
    # DART: 2년 x 2 period = 4 호출
    assert len(dart.calls) == 4
    assert summary.n_krx_ok == 1
    assert summary.n_dart_ok == 4
    assert summary.failures == []


def test_collect_one_ticker_records_krx_failure() -> None:
    from frr.config import AnalysisWindow, DARTConfig, DataConfig, UniverseConfig

    cfg = DataConfig(
        analysis=AnalysisWindow(start=date(2020, 1, 1), end=date(2020, 12, 31)),
        universe=UniverseConfig(manifest_path=Path("x")),
        dart=DARTConfig(filing_lag_business_days=1, periods=("FY",), fs_div="CFS"),
    )
    krx = StubKRX(fail_on={"999999"})
    dart = StubDART()
    summary = CollectionSummary()

    collect_one_ticker("999999", cfg, krx, dart, summary)  # type: ignore[arg-type]

    assert summary.n_krx_ok == 0
    assert summary.n_dart_ok == 1  # DART 는 정상 계속
    assert len(summary.failures) == 1
    assert summary.failures[0].stage == "krx"


def test_collect_one_ticker_counts_notfound() -> None:
    from frr.config import AnalysisWindow, DARTConfig, DataConfig, UniverseConfig

    cfg = DataConfig(
        analysis=AnalysisWindow(start=date(2020, 1, 1), end=date(2020, 12, 31)),
        universe=UniverseConfig(manifest_path=Path("x")),
        dart=DARTConfig(filing_lag_business_days=1, periods=("Q1", "FY"), fs_div="CFS"),
    )
    krx = StubKRX()
    dart = StubDART(notfound_periods={"Q1"})
    summary = CollectionSummary()

    collect_one_ticker("005930", cfg, krx, dart, summary)  # type: ignore[arg-type]

    assert summary.n_dart_ok == 1  # FY
    assert summary.n_dart_notfound == 1  # Q1


def test_collect_one_ticker_skip_flags() -> None:
    from frr.config import AnalysisWindow, DARTConfig, DataConfig, UniverseConfig

    cfg = DataConfig(
        analysis=AnalysisWindow(start=date(2020, 1, 1), end=date(2020, 12, 31)),
        universe=UniverseConfig(manifest_path=Path("x")),
        dart=DARTConfig(filing_lag_business_days=1, periods=("FY",), fs_div="CFS"),
    )
    krx = StubKRX()
    dart = StubDART()
    summary = CollectionSummary()

    collect_one_ticker(
        "005930",
        cfg,
        krx,
        dart,
        summary,  # type: ignore[arg-type]
        skip_krx=True,
        skip_dart=True,
    )

    assert krx.calls == []
    assert dart.calls == []
    assert summary.n_krx_ok == 0
    assert summary.n_dart_ok == 0


# ---- collect_universe (전체 흐름) ----------------------------------------


class StubLoader:
    """KOSPI200QuarterlyLoader.tickers 흉내."""

    def __init__(self, quarters: dict[str, list[str]]) -> None:
        self._q = quarters

    def available_quarters(self) -> list[str]:
        return sorted(self._q.keys())

    def tickers(self, q: str) -> list[str]:
        return list(self._q[q])


class StubFDR:
    def __init__(self, listing_fail: bool = False, delisting_fail: bool = False) -> None:
        self.listing_calls = 0
        self.delisting_calls = 0
        self.listing_fail = listing_fail
        self.delisting_fail = delisting_fail

    def listing(self, *, refresh: bool = False) -> pd.DataFrame:
        self.listing_calls += 1
        if self.listing_fail:
            raise RuntimeError("fdr listing fail")
        return pd.DataFrame({"Code": ["005930"], "Name": ["삼성전자"]})

    def delisting(self, *, refresh: bool = False) -> pd.DataFrame:
        self.delisting_calls += 1
        if self.delisting_fail:
            raise RuntimeError("fdr delisting fail")
        return pd.DataFrame({"Symbol": ["006380"], "Name": ["카프로"]})


def _make_config_yaml(tmp_path: Path) -> Path:
    """tmp_path 에 합성 data.yaml. universe.manifest_path 는 dummy."""
    cfg_yaml = tmp_path / "data.yaml"
    cfg_yaml.write_text(
        """
analysis:
  start: 2020-01-01
  end: 2020-12-31
universe:
  manifest_path: dummy.yaml
dart:
  filing_lag_business_days: 1
  periods: [FY]
  fs_div: CFS
""",
        encoding="utf-8",
    )
    return cfg_yaml


def test_collect_universe_with_stubs(tmp_path: Path) -> None:
    cfg_yaml = _make_config_yaml(tmp_path)
    loader = StubLoader({"2020Q1": ["005930", "000660"], "2020Q2": ["005930", "035720"]})
    fdr = StubFDR()
    krx = StubKRX()
    dart = StubDART()

    summary = collect_universe(
        config_path=cfg_yaml,
        project_root=tmp_path,
        loader=loader,  # type: ignore[arg-type]
        fdr=fdr,  # type: ignore[arg-type]
        krx=krx,  # type: ignore[arg-type]
        dart=dart,  # type: ignore[arg-type]
        calendar=object(),  # type: ignore[arg-type]
    )

    # union = {005930, 000660, 035720}
    assert summary.n_tickers == 3
    assert summary.n_krx_ok == 3
    assert summary.n_dart_ok == 3  # 1년 x 1 period x 3 종목
    assert summary.fdr_listing_ok and summary.fdr_delisting_ok
    assert fdr.listing_calls == 1
    assert fdr.delisting_calls == 1
    assert summary.failures == []


def test_collect_universe_limit_and_filter(tmp_path: Path) -> None:
    cfg_yaml = _make_config_yaml(tmp_path)
    loader = StubLoader({"2020Q1": ["005930", "000660", "035720"]})

    summary = collect_universe(
        config_path=cfg_yaml,
        project_root=tmp_path,
        loader=loader,  # type: ignore[arg-type]
        fdr=StubFDR(),  # type: ignore[arg-type]
        krx=StubKRX(),  # type: ignore[arg-type]
        dart=StubDART(),  # type: ignore[arg-type]
        calendar=object(),  # type: ignore[arg-type]
        ticker_filter=["005930", "035720"],
        limit=1,
    )

    # 필터 + 첫 1개만
    assert summary.n_tickers == 1


def test_collect_universe_skip_fdr(tmp_path: Path) -> None:
    cfg_yaml = _make_config_yaml(tmp_path)
    loader = StubLoader({"2020Q1": ["005930"]})
    fdr = StubFDR()

    summary = collect_universe(
        config_path=cfg_yaml,
        project_root=tmp_path,
        loader=loader,  # type: ignore[arg-type]
        fdr=fdr,  # type: ignore[arg-type]
        krx=StubKRX(),  # type: ignore[arg-type]
        dart=StubDART(),  # type: ignore[arg-type]
        calendar=object(),  # type: ignore[arg-type]
        skip_fdr=True,
    )

    assert fdr.listing_calls == 0
    assert fdr.delisting_calls == 0
    assert not summary.fdr_listing_ok


def test_collect_universe_fdr_failure_recorded(tmp_path: Path) -> None:
    cfg_yaml = _make_config_yaml(tmp_path)
    loader = StubLoader({"2020Q1": ["005930"]})

    summary = collect_universe(
        config_path=cfg_yaml,
        project_root=tmp_path,
        loader=loader,  # type: ignore[arg-type]
        fdr=StubFDR(listing_fail=True),  # type: ignore[arg-type]
        krx=StubKRX(),  # type: ignore[arg-type]
        dart=StubDART(),  # type: ignore[arg-type]
        calendar=object(),  # type: ignore[arg-type]
    )

    assert not summary.fdr_listing_ok
    assert any(f.stage == "fdr_listing" for f in summary.failures)
    # FDR 실패에도 종목 수집은 계속
    assert summary.n_krx_ok == 1


# ---- write_summary 단위 + collect_universe 통합 ------------------------


def test_write_summary_creates_yaml(tmp_path: Path) -> None:
    """합성 summary 를 yaml 로 직렬화한 결과 파일 + 내용 검증."""
    summary = CollectionSummary(
        n_tickers=2,
        n_krx_ok=2,
        n_dart_ok=1,
        n_dart_notfound=1,
        fdr_listing_ok=True,
        fdr_delisting_ok=True,
        failures=[
            CollectionFailure(ticker="999999", stage="krx", detail="some error"),
        ],
    )
    out = tmp_path / "out" / "summary.yaml"
    latest, backup = write_summary(
        summary,
        config_path=Path("configs/data.yaml"),
        analysis_start=date(2020, 1, 1),
        analysis_end=date(2020, 12, 31),
        summary_path=out,
    )

    assert latest == out
    assert latest.exists()
    assert backup is not None and backup.exists()

    payload = yaml.safe_load(latest.read_text(encoding="utf-8"))
    assert payload["counts"]["n_tickers"] == 2
    assert payload["counts"]["n_krx_ok"] == 2
    assert payload["analysis_window"]["start"] == "2020-01-01"
    assert payload["failures"]["count"] == 1
    assert payload["failures"]["by_stage"] == {"krx": 1}
    assert payload["failures"]["items"][0]["ticker"] == "999999"


def test_write_summary_can_skip_backup(tmp_path: Path) -> None:
    summary = CollectionSummary(n_tickers=0)
    out = tmp_path / "s.yaml"
    latest, backup = write_summary(
        summary,
        config_path=Path("c.yaml"),
        analysis_start=date(2020, 1, 1),
        analysis_end=date(2020, 12, 31),
        summary_path=out,
        backup_with_timestamp=False,
    )
    assert latest.exists()
    assert backup is None


def test_collect_universe_writes_summary_by_default(tmp_path: Path) -> None:
    cfg_yaml = _make_config_yaml(tmp_path)
    loader = StubLoader({"2020Q1": ["005930"]})

    collect_universe(
        config_path=cfg_yaml,
        project_root=tmp_path,
        loader=loader,  # type: ignore[arg-type]
        fdr=StubFDR(),  # type: ignore[arg-type]
        krx=StubKRX(),  # type: ignore[arg-type]
        dart=StubDART(),  # type: ignore[arg-type]
        calendar=object(),  # type: ignore[arg-type]
    )

    default_path = tmp_path / "data" / "raw" / "collect_summary.yaml"
    assert default_path.exists()
    payload = yaml.safe_load(default_path.read_text(encoding="utf-8"))
    assert payload["counts"]["n_tickers"] == 1


def test_collect_universe_no_summary_when_disabled(tmp_path: Path) -> None:
    cfg_yaml = _make_config_yaml(tmp_path)
    loader = StubLoader({"2020Q1": ["005930"]})

    collect_universe(
        config_path=cfg_yaml,
        project_root=tmp_path,
        loader=loader,  # type: ignore[arg-type]
        fdr=StubFDR(),  # type: ignore[arg-type]
        krx=StubKRX(),  # type: ignore[arg-type]
        dart=StubDART(),  # type: ignore[arg-type]
        calendar=object(),  # type: ignore[arg-type]
        write_summary_file=False,
    )

    default_path = tmp_path / "data" / "raw" / "collect_summary.yaml"
    assert not default_path.exists()


def test_collect_universe_custom_summary_path(tmp_path: Path) -> None:
    cfg_yaml = _make_config_yaml(tmp_path)
    loader = StubLoader({"2020Q1": ["005930"]})
    custom = tmp_path / "logs" / "custom.yaml"

    collect_universe(
        config_path=cfg_yaml,
        project_root=tmp_path,
        loader=loader,  # type: ignore[arg-type]
        fdr=StubFDR(),  # type: ignore[arg-type]
        krx=StubKRX(),  # type: ignore[arg-type]
        dart=StubDART(),  # type: ignore[arg-type]
        calendar=object(),  # type: ignore[arg-type]
        summary_path=custom,
    )

    assert custom.exists()
    # default 경로는 사용되지 않음
    assert not (tmp_path / "data" / "raw" / "collect_summary.yaml").exists()
