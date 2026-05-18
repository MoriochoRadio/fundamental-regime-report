"""pykrx 단일 종목 OHLCV 어댑터.

역할:
- 단일 종목 일별 OHLCV (날짜 인덱스 + 한국어 컬럼). **시점별 전종목·
  인덱스 호출은 KRX 변경으로 망가졌으므로 본 어댑터는 *단일 종목*에만
  쓴다** (단계 1 가용성 검증·CLAUDE.md §8.1).

캐시 정책 (정확히 한 방식만 — 단순하고 오류 가능성 최소):
- 캐시 위치: `data/raw/krx/ohlcv/<ticker>.parquet`.
- **요청 ⊆ 캐시** → 캐시에서 슬라이스 반환 (네트워크 0회).
- 그 외 (왼쪽 확장·오른쪽 확장·겹침 없음 모두) → **합집합 범위**
  `[min(c.start, q.start), max(c.end, q.end)]` 전체를 한 번 페치해
  캐시를 덮어쓴 뒤 요청 범위를 슬라이스해 반환.
- 부분 추가 페치는 *하지 않는다*. 본 프로젝트의 호출 패턴(분석 기간
  전체를 종목별로 한 번 페치 + 이후 다양한 sub-range 슬라이스)에서
  단순 정책이 90% 케이스를 0-네트워크로 처리하고, 나머지는 *캐시
  확장*으로 자연스럽게 수렴한다.
- `refresh=True` 는 캐시를 무시하고 요청 범위만 다시 받아 덮어쓴다.

dtype:
- 종목코드는 *입력 인자*. 6자리 str (앞 0 보존)을 *호출자가 보장*해야
  한다. 본 어댑터는 종목코드를 가공하지 않는다 (universe_loader/fdr
  단에서 이미 정규화됨).
- pykrx 응답 컬럼 (한국어): 시가, 고가, 저가, 종가, 거래량, 등락률.
  본 어댑터는 그대로 반환한다.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import date
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


Fetcher = Callable[[str, date, date], pd.DataFrame]
"""(ticker, start, end) -> 일별 OHLCV DataFrame.

기본 구현은 pykrx 의 `stock.get_market_ohlcv` 래퍼. 테스트에서는
의존성 주입으로 stub 으로 대체된다.
"""


class KRXSingleTicker:
    """단일 종목 OHLCV 페치·캐시."""

    DEFAULT_CACHE_REL_DIR = Path("data/raw/krx/ohlcv")

    def __init__(
        self,
        project_root: Path | None = None,
        cache_rel_dir: Path | None = None,
        fetcher: Fetcher | None = None,
    ) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.cache_rel_dir = Path(cache_rel_dir) if cache_rel_dir else self.DEFAULT_CACHE_REL_DIR
        self._fetcher: Fetcher = fetcher if fetcher is not None else _fetch_pykrx_ohlcv

    @property
    def cache_dir(self) -> Path:
        return self.project_root / self.cache_rel_dir

    # ---- 공개 API --------------------------------------------------------

    def fetch_ohlcv(
        self,
        ticker: str,
        start: date,
        end: date,
        *,
        refresh: bool = False,
    ) -> pd.DataFrame:
        """단일 종목의 [start, end] 폐구간 일별 OHLCV.

        반환: pykrx 컬럼(`시가, 고가, 저가, 종가, 거래량, 등락률`) +
        날짜 인덱스. 슬라이스 결과가 비어 있으면 빈 DataFrame.
        """
        if start > end:
            raise ValueError(f"start={start} > end={end}")

        cache = self.cache_dir / f"{ticker}.parquet"

        if refresh:
            return self._fetch_and_overwrite(ticker, start, end, cache)

        if not cache.exists():
            return self._fetch_and_overwrite(ticker, start, end, cache)

        cached = pd.read_parquet(cache)
        if cached.empty:
            return self._fetch_and_overwrite(ticker, start, end, cache)

        c_start = cached.index.min().date()
        c_end = cached.index.max().date()

        if c_start <= start and end <= c_end:
            logger.info("krx cache hit %s [%s, %s] ⊆ [%s, %s]", ticker, start, end, c_start, c_end)
            return _slice(cached, start, end)

        # 합집합 범위 페치
        union_start = min(c_start, start)
        union_end = max(c_end, end)
        logger.info(
            "krx cache extend %s: cache=[%s,%s] req=[%s,%s] -> fetch=[%s,%s]",
            ticker,
            c_start,
            c_end,
            start,
            end,
            union_start,
            union_end,
        )
        fresh = self._fetch_and_overwrite(ticker, union_start, union_end, cache)
        return _slice(fresh, start, end)

    # ---- 내부 ------------------------------------------------------------

    def _fetch_and_overwrite(
        self, ticker: str, start: date, end: date, cache: Path
    ) -> pd.DataFrame:
        df = self._fetcher(ticker, start, end)
        df = _ensure_datetime_index(df)
        cache.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache)
        logger.info("krx cache written %s (%d rows, [%s, %s])", cache, len(df), start, end)
        return df


# ---- 모듈 함수 ------------------------------------------------------------


def _fetch_pykrx_ohlcv(ticker: str, start: date, end: date) -> pd.DataFrame:
    """pykrx 기본 fetcher (지연 import). 단위 테스트는 본 함수를 우회한다."""
    from pykrx import stock

    df = stock.get_market_ohlcv(start.strftime("%Y%m%d"), end.strftime("%Y%m%d"), ticker)
    if df is None:
        return pd.DataFrame()
    return df


def _ensure_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """parquet 왕복 시 인덱스가 사라지지 않도록 보장."""
    if isinstance(df.index, pd.DatetimeIndex):
        return df
    if df.index.name in ("날짜", "Date"):
        df.index = pd.to_datetime(df.index)
        return df
    return df


def _slice(df: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
    """날짜 인덱스 폐구간 슬라이스. 빈 결과도 안전하게 처리."""
    if df.empty:
        return df
    mask = (df.index.date >= start) & (df.index.date <= end)
    return df.loc[mask]
