"""DART OpenDart 정기보고서 어댑터.

역할:
- DART 정기보고서(사업/반기/분기)의 *주요 재무 계정* 페치.
- 각 보고서의 **`rcept_dt`(접수일) + 1 영업일** 로 *사용 가능 시점*
  (`available_from`)을 계산해 캐시 메타에 저장 (D7 룩어헤드 차단).
- 시점 t 에 대해 `available_at(t)` / `latest_available(t)` 로
  *t 이전에 사용 가능한 보고서만* 반환.

API (OpenDartReader 0.3.2 기준):
- `OpenDartReader(api_key).finstate(corp, bsns_year, reprt_code)`
- `reprt_code`: 11011=FY, 11012=H1, 11013=Q1, 11014=Q3
- 반환 컬럼: `rcept_no`, `reprt_code`, `bsns_year`, `corp_code`,
  `stock_code`, `fs_div`, `fs_nm`, `sj_div`, `sj_nm`, `account_nm`,
  `thstrm_*`, `frmtrm_*`, `bfefrmtrm_*`, `ord`, `currency` (총 21).
- **`rcept_no` 첫 8자 = `rcept_dt` YYYYMMDD** — 별도 list() 호출 불필요.

캐시:
- 본문 parquet: `data/raw/dart/{ticker}/{year}_{period}.parquet`
- 메타 yaml:  `data/raw/dart/{ticker}/{year}_{period}.meta.yaml`
- *notfound* (보고서 미존재) 도 메타에 status 로 기록 → 재호출 시
  중복 페치 회피.

★ 격리 원칙:
- 본 어댑터가 반환하는 컬럼·계정은 단계 2 피처 모듈의 *입력*. 모델 피처는
  *별도 모듈*에서 가공·시간 정렬되어야 하며 본 어댑터의 raw 보고서를
  *그대로* 피처로 쓰는 것을 금지 (단계 2 격리 검증 테스트).
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal

import pandas as pd
import yaml

from frr.data.calendars import KRXBusinessCalendar

logger = logging.getLogger(__name__)


PeriodCode = Literal["Q1", "H1", "Q3", "FY"]


REPORT_CODES: dict[str, str] = {
    "Q1": "11013",
    "H1": "11012",
    "Q3": "11014",
    "FY": "11011",
}


@dataclass(frozen=True)
class ReportRef:
    """보고서 메타 (페치 본문 없이 룩어헤드 결정용)."""

    ticker: str
    year: int
    period: str  # PeriodCode
    rcept_dt: date | None
    available_from: date | None
    status: str  # "ok" or "notfound"


@dataclass(frozen=True)
class ReportResult:
    """페치된 보고서 1건 (ref + 본문 DataFrame)."""

    ref: ReportRef
    df: pd.DataFrame


Fetcher = Callable[[str, int, str], pd.DataFrame]
"""(ticker, bsns_year, reprt_code) → finstate DataFrame. 빈/None 가능."""


class DARTReporter:
    """OpenDartReader.finstate 페치·캐시·시점 정렬."""

    DEFAULT_CACHE_REL_DIR = Path("data/raw/dart")

    def __init__(
        self,
        calendar: KRXBusinessCalendar,
        project_root: Path | None = None,
        cache_rel_dir: Path | None = None,
        api_key: str | None = None,
        fetcher: Fetcher | None = None,
    ) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.cache_rel_dir = Path(cache_rel_dir) if cache_rel_dir else self.DEFAULT_CACHE_REL_DIR
        self._calendar = calendar
        self._api_key = api_key  # 지연 — 실 fetcher 호출 직전에 환경변수 fallback
        self._fetcher: Fetcher | None = fetcher  # None 이면 default _odr_fetcher

    @property
    def cache_dir(self) -> Path:
        return self.project_root / self.cache_rel_dir

    # ---- 공개 API --------------------------------------------------------

    def fetch_report(
        self,
        ticker: str,
        year: int,
        period: PeriodCode,
        *,
        refresh: bool = False,
    ) -> ReportResult:
        """단일 보고서. 캐시 hit 우선, miss 시 페치 + 메타 기록."""
        if period not in REPORT_CODES:
            raise ValueError(f"period 는 Q1/H1/Q3/FY 중 하나여야 함: {period}")

        cache = self._cache_path(ticker, year, period)
        meta = self._meta_path(ticker, year, period)

        if cache.exists() and meta.exists() and not refresh:
            ref = self._load_meta(meta)
            df = pd.read_parquet(cache) if ref.status == "ok" else pd.DataFrame()
            logger.info("dart cache hit %s/%d/%s", ticker, year, period)
            return ReportResult(ref=ref, df=df)

        # 메타만 있고 본문 없으면 notfound 재사용
        if meta.exists() and not refresh:
            ref = self._load_meta(meta)
            if ref.status == "notfound":
                logger.info("dart cache hit (notfound) %s/%d/%s", ticker, year, period)
                return ReportResult(ref=ref, df=pd.DataFrame())

        return self._fetch_and_write(ticker, year, period, cache, meta)

    def available_at(
        self,
        ticker: str,
        t: date,
        years: list[int],
    ) -> list[ReportRef]:
        """시점 *t* 에 사용 가능한 보고서 메타 (룩어헤드 차단).

        주어진 *years* 와 모든 period 의 조합을 순회하며 *available_from
        이 t 이하* 인 것만 모은다. 캐시가 채워지면 두 번째 호출부터 네트워크 0.
        """
        refs: list[ReportRef] = []
        for year in years:
            for period in REPORT_CODES:
                try:
                    r = self.fetch_report(ticker, year, period)  # type: ignore[arg-type]
                except Exception as e:
                    logger.warning("fetch failed %s/%d/%s: %s", ticker, year, period, e)
                    continue
                ref = r.ref
                if ref.status != "ok":
                    continue
                if ref.available_from is None or ref.available_from > t:
                    continue
                refs.append(ref)
        return sorted(refs, key=lambda r: (r.available_from, r.year, r.period))

    def latest_available(
        self,
        ticker: str,
        t: date,
        years: list[int],
    ) -> ReportResult | None:
        """시점 *t* 에 가장 최근 사용 가능한 보고서 1건."""
        refs = self.available_at(ticker, t, years)
        if not refs:
            return None
        latest = refs[-1]
        return self.fetch_report(ticker, latest.year, latest.period)  # type: ignore[arg-type]

    # ---- 내부 ------------------------------------------------------------

    def _cache_path(self, ticker: str, year: int, period: str) -> Path:
        return self.cache_dir / ticker / f"{year}_{period}.parquet"

    def _meta_path(self, ticker: str, year: int, period: str) -> Path:
        return self.cache_dir / ticker / f"{year}_{period}.meta.yaml"

    def _fetch_and_write(
        self,
        ticker: str,
        year: int,
        period: PeriodCode,
        cache: Path,
        meta_path: Path,
    ) -> ReportResult:
        reprt_code = REPORT_CODES[period]
        fetcher = self._fetcher or _make_default_fetcher(self._api_key)
        df = fetcher(ticker, year, reprt_code)

        cache.parent.mkdir(parents=True, exist_ok=True)

        if df is None or len(df) == 0:
            ref = ReportRef(
                ticker=ticker,
                year=year,
                period=period,
                rcept_dt=None,
                available_from=None,
                status="notfound",
            )
            self._write_meta(meta_path, ref)
            logger.info("dart notfound %s/%d/%s", ticker, year, period)
            return ReportResult(ref=ref, df=pd.DataFrame())

        rcept_no = str(df["rcept_no"].iloc[0])
        rcept_dt = _rcept_no_to_date(rcept_no)
        available_from = self._calendar.add_business_days(rcept_dt, 1)

        df.to_parquet(cache)
        ref = ReportRef(
            ticker=ticker,
            year=year,
            period=period,
            rcept_dt=rcept_dt,
            available_from=available_from,
            status="ok",
        )
        self._write_meta(meta_path, ref)
        logger.info(
            "dart fetched %s/%d/%s rcept=%s available_from=%s",
            ticker,
            year,
            period,
            rcept_dt,
            available_from,
        )
        return ReportResult(ref=ref, df=df)

    def _write_meta(self, path: Path, ref: ReportRef) -> None:
        data: dict[str, Any] = {
            "ticker": ref.ticker,
            "year": ref.year,
            "period": ref.period,
            "status": ref.status,
            "rcept_dt": ref.rcept_dt.isoformat() if ref.rcept_dt else None,
            "available_from": (ref.available_from.isoformat() if ref.available_from else None),
            "fetched_at": date.today().isoformat(),
        }
        path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")

    def _load_meta(self, path: Path) -> ReportRef:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return ReportRef(
            ticker=str(data["ticker"]),
            year=int(data["year"]),
            period=str(data["period"]),
            rcept_dt=date.fromisoformat(data["rcept_dt"]) if data.get("rcept_dt") else None,
            available_from=(
                date.fromisoformat(data["available_from"]) if data.get("available_from") else None
            ),
            status=str(data.get("status", "ok")),
        )


# ---- 모듈 함수 ------------------------------------------------------------


def _rcept_no_to_date(rcept_no: str) -> date:
    """`rcept_no='20210309000744'` → `date(2021, 3, 9)`."""
    if len(rcept_no) < 8:
        raise ValueError(f"잘못된 rcept_no (8자 미만): {rcept_no!r}")
    try:
        return date(int(rcept_no[:4]), int(rcept_no[4:6]), int(rcept_no[6:8]))
    except (ValueError, TypeError) as e:
        raise ValueError(f"rcept_no 의 앞 8자를 날짜로 해석 불가: {rcept_no!r}") from e


def _make_default_fetcher(api_key: str | None) -> Fetcher:
    """OpenDartReader 기반 기본 fetcher. 키 미지정 시 환경변수에서."""
    key = api_key or os.environ.get("DART_API_KEY")
    if not key:
        raise RuntimeError(
            "DART_API_KEY 가 없음. .env 또는 환경변수에 설정하거나 "
            "DARTReporter(api_key=...) 로 직접 주입하라."
        )

    import opendartreader  # 지연 import

    odr = opendartreader.OpenDartReader(key)

    def _fetch(ticker: str, year: int, reprt_code: str) -> pd.DataFrame:
        try:
            df = odr.finstate(ticker, year, reprt_code=reprt_code)
        except Exception as e:
            logger.warning("OpenDartReader finstate 예외 %s/%d/%s: %s", ticker, year, reprt_code, e)
            return pd.DataFrame()
        if df is None:
            return pd.DataFrame()
        return df

    return _fetch
