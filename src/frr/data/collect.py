"""배치 수집 코어 로직 (단위 테스트 가능).

`scripts/collect_data.py` 가 CLI 래퍼, 본 모듈이 *코어*다. 분리 사유:
스크립트에 모든 로직을 넣으면 import 불가 → 단위 테스트 불가능.

흐름:
1. config 로드 (이미 분리됨: `frr.config.load_data_config`)
2. calendar 로드 (FDR KS200 기반 영업일)
3. (선택) FDR listing + delisting 1회 페치
4. universe_loader 로 *모든 검증 분기* 종목 union
5. 각 종목 종목별:
   a. KRXSingleTicker.fetch_ohlcv (analysis window 전체)
   b. DARTReporter.fetch_report 각 (year, period)
6. 종목 단위 실패는 *다음 종목 계속* — 실패 목록 누적
7. CollectionSummary 반환

에러 정책:
- *수집* 은 *부분 성공* 패턴: 한 종목·한 보고서 실패가 *다음 종목/보고서*
  를 막지 않는다. 모든 실패는 `summary.failures` 에 누적되어 호출자가
  로깅·재시도 결정.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import yaml

from frr.config import DataConfig, load_data_config
from frr.data.calendars import KRXBusinessCalendar
from frr.data.dart import DARTReporter
from frr.data.fdr import FDRDataSource
from frr.data.krx import KRXSingleTicker
from frr.data.universe_loader import KOSPI200QuarterlyLoader

logger = logging.getLogger(__name__)

DEFAULT_SUMMARY_REL = Path("data/raw/collect_summary.yaml")


@dataclass
class CollectionFailure:
    """종목·보고서 단위 실패 기록."""

    ticker: str
    stage: str  # "krx" | "dart" | "fdr_listing" | "fdr_delisting"
    detail: str  # 보고서 ID 또는 메시지


@dataclass
class CollectionSummary:
    """전체 수집 결과."""

    n_tickers: int = 0
    n_krx_ok: int = 0
    n_dart_ok: int = 0
    n_dart_notfound: int = 0
    fdr_listing_ok: bool = False
    fdr_delisting_ok: bool = False
    failures: list[CollectionFailure] = field(default_factory=list)

    def add_failure(self, ticker: str, stage: str, detail: str) -> None:
        self.failures.append(CollectionFailure(ticker, stage, detail))


# ---- summary 직렬화 ----------------------------------------------------


def write_summary(
    summary: CollectionSummary,
    *,
    config_path: Path,
    analysis_start: date,
    analysis_end: date,
    summary_path: Path,
    backup_with_timestamp: bool = True,
) -> tuple[Path, Path | None]:
    """`CollectionSummary` 를 YAML 로 직렬화해 두 곳에 저장.

    - `summary_path` (덮어쓰기 — 최신 결과)
    - 같은 디렉터리에 `{stem}_{YYYYMMDD_HHMMSS}.yaml` (이력 백업, 옵션)

    반환: `(latest_path, backup_path_or_None)`.
    """
    by_stage: dict[str, int] = {}
    for f in summary.failures:
        by_stage[f.stage] = by_stage.get(f.stage, 0) + 1

    payload: dict[str, object] = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "config_path": str(config_path),
        "analysis_window": {
            "start": analysis_start.isoformat(),
            "end": analysis_end.isoformat(),
        },
        "counts": {
            "n_tickers": summary.n_tickers,
            "n_krx_ok": summary.n_krx_ok,
            "n_dart_ok": summary.n_dart_ok,
            "n_dart_notfound": summary.n_dart_notfound,
            "fdr_listing_ok": summary.fdr_listing_ok,
            "fdr_delisting_ok": summary.fdr_delisting_ok,
        },
        "failures": {
            "count": len(summary.failures),
            "by_stage": dict(sorted(by_stage.items())),
            "items": [
                {"ticker": f.ticker, "stage": f.stage, "detail": f.detail} for f in summary.failures
            ],
        },
    }

    text = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(text, encoding="utf-8")
    logger.info("collect summary written: %s", summary_path)

    backup: Path | None = None
    if backup_with_timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = summary_path.with_name(f"{summary_path.stem}_{ts}.yaml")
        backup.write_text(text, encoding="utf-8")
        logger.info("collect summary backup: %s", backup)

    return summary_path, backup


# ---- 유니버스 union ------------------------------------------------------


def build_universe_union(loader: KOSPI200QuarterlyLoader) -> list[str]:
    """모든 검증 분기의 종목 union (정렬). 단계 1 유니버스 = KOSPI200 + 상폐."""
    tickers: set[str] = set()
    for q in loader.available_quarters():
        tickers.update(loader.tickers(q))
    return sorted(tickers)


# ---- 단일 종목 수집 ------------------------------------------------------


def collect_one_ticker(
    ticker: str,
    config: DataConfig,
    krx: KRXSingleTicker,
    dart: DARTReporter,
    summary: CollectionSummary,
    *,
    skip_krx: bool = False,
    skip_dart: bool = False,
) -> None:
    """단일 종목의 KRX OHLCV + DART 정기보고서 수집. 실패는 summary 에 기록."""
    # KRX OHLCV
    if not skip_krx:
        try:
            krx.fetch_ohlcv(ticker, config.analysis.start, config.analysis.end)
            summary.n_krx_ok += 1
            logger.info("krx ok %s", ticker)
        except Exception as e:
            logger.warning("krx fail %s: %s", ticker, e)
            summary.add_failure(ticker, "krx", str(e))

    # DART: analysis window 가 걸치는 사업연도들 + 모든 period 의 곱
    if not skip_dart:
        years = list(range(config.analysis.start.year, config.analysis.end.year + 1))
        for year in years:
            for period in config.dart.periods:
                try:
                    res = dart.fetch_report(ticker, year, period)  # type: ignore[arg-type]
                except Exception as e:
                    logger.warning("dart fail %s/%d/%s: %s", ticker, year, period, e)
                    summary.add_failure(ticker, "dart", f"{year}/{period}: {e}")
                    continue
                if res.ref.status == "ok":
                    summary.n_dart_ok += 1
                else:
                    summary.n_dart_notfound += 1


# ---- 전체 수집 진입점 ----------------------------------------------------


def collect_universe(
    config_path: Path,
    *,
    project_root: Path | None = None,
    limit: int | None = None,
    ticker_filter: Iterable[str] | None = None,
    skip_krx: bool = False,
    skip_dart: bool = False,
    skip_fdr: bool = False,
    summary_path: Path | None = None,
    write_summary_file: bool = True,
    # 의존성 주입 (단위 테스트용 — 모두 None 이면 default 생성)
    calendar: KRXBusinessCalendar | None = None,
    loader: KOSPI200QuarterlyLoader | None = None,
    fdr: FDRDataSource | None = None,
    krx: KRXSingleTicker | None = None,
    dart: DARTReporter | None = None,
) -> CollectionSummary:
    """전체 유니버스 배치 수집. CLI 및 단위 테스트의 공통 진입점."""
    root = Path(project_root) if project_root else Path.cwd()
    config = load_data_config(config_path)

    # 캘린더
    if calendar is None:
        calendar = KRXBusinessCalendar.from_cache_or_fetch(
            config.analysis.start, config.analysis.end, project_root=root
        )

    # FDR listing/delisting (한 번만)
    summary = CollectionSummary()
    if not skip_fdr:
        if fdr is None:
            fdr = FDRDataSource(project_root=root)
        try:
            fdr.listing()
            summary.fdr_listing_ok = True
        except Exception as e:
            logger.warning("fdr listing fail: %s", e)
            summary.add_failure("-", "fdr_listing", str(e))
        try:
            fdr.delisting()
            summary.fdr_delisting_ok = True
        except Exception as e:
            logger.warning("fdr delisting fail: %s", e)
            summary.add_failure("-", "fdr_delisting", str(e))

    # 유니버스
    if loader is None:
        loader = KOSPI200QuarterlyLoader.from_default(project_root=root)
    tickers = build_universe_union(loader)

    # 필터·제한
    if ticker_filter is not None:
        wanted = set(ticker_filter)
        tickers = [t for t in tickers if t in wanted]
    if limit is not None:
        tickers = tickers[:limit]
    summary.n_tickers = len(tickers)

    if not tickers:
        logger.warning("수집 대상 종목 없음 (필터·제한 결과)")
        return summary

    # 단일 어댑터 인스턴스 재사용
    if krx is None:
        krx = KRXSingleTicker(project_root=root)
    if dart is None:
        dart = DARTReporter(calendar=calendar, project_root=root)

    for i, ticker in enumerate(tickers, 1):
        logger.info("[%d/%d] %s", i, len(tickers), ticker)
        collect_one_ticker(
            ticker,
            config,
            krx,
            dart,
            summary,
            skip_krx=skip_krx,
            skip_dart=skip_dart,
        )

    logger.info(
        "done: %d tickers, krx_ok=%d, dart_ok=%d, dart_notfound=%d, failures=%d",
        summary.n_tickers,
        summary.n_krx_ok,
        summary.n_dart_ok,
        summary.n_dart_notfound,
        len(summary.failures),
    )

    if write_summary_file:
        path = summary_path if summary_path is not None else root / DEFAULT_SUMMARY_REL
        write_summary(
            summary,
            config_path=config_path,
            analysis_start=config.analysis.start,
            analysis_end=config.analysis.end,
            summary_path=path,
        )

    return summary
