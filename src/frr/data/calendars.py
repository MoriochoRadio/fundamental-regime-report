"""KRX 영업일 캘린더.

설계 결정:
- **영업일 출처**: FinanceDataReader 의 `KS200` (KOSPI200 지수) 일별
  OHLCV index. 지수 데이터는 임의 종목과 달리 *모든 거래일에 값이
  존재* 하므로 거래정지·상장폐지의 영향을 받지 않는다.
- **캐시**: `data/raw/calendars/kospi_business_days_<start>_<end>.parquet`.
  첫 호출 시 자동 생성, 이후 호출은 캐시에서 로딩 (네트워크 0회).
- **단위 테스트**: 합성 캘린더로 외부 의존성 없이 로직 검증.
- **통합 테스트**: 실제 FDR fetch (네트워크 필요).

룩어헤드 차단 관점:
- 본 모듈 자체는 시점별 데이터를 다루지 않으므로 룩어헤드와 직접 관련
  없다. 다만 호출자(예: `universe_loader.as_of`, DART rcept_dt+1 lag)
  가 본 모듈을 사용할 때 *과거→미래* 방향만 쓰면 룩어헤드 차단이
  보장된다. `previous_business_day` 와 `floor` 는 항상 *입력 이하* 의
  영업일만 반환한다는 점이 핵심 보증.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class KRXBusinessCalendar:
    """KRX 영업일 집합과 그 위의 조회 연산.

    `business_days` 는 *집합* 의 의미로 사용된다 (중복 무시·정렬 무관).
    """

    business_days: list[date]
    _bd_set: frozenset[date] = field(init=False, repr=False)
    _sorted: list[date] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        normalized = [_to_date(d) for d in self.business_days]
        if not normalized:
            raise ValueError("KRXBusinessCalendar 는 빈 영업일 리스트로 만들 수 없음")
        self._bd_set = frozenset(normalized)
        self._sorted = sorted(self._bd_set)

    # ---- 범위 ------------------------------------------------------------

    @property
    def first(self) -> date:
        return self._sorted[0]

    @property
    def last(self) -> date:
        return self._sorted[-1]

    # ---- 기본 조회 -------------------------------------------------------

    def is_business_day(self, d: date) -> bool:
        """*영업일 집합에 속하는가*. 범위 밖은 정의상 영업일이 아니므로 False.

        엄격한 범위 검사가 필요하면 `first`/`last` 와 직접 비교하라.
        """
        return d in self._bd_set

    def previous_business_day(self, d: date) -> date:
        """*엄격히 d 이전* 의 가장 가까운 영업일."""
        cur = d - timedelta(days=1)
        while cur >= self.first:
            if cur in self._bd_set:
                return cur
            cur -= timedelta(days=1)
        raise LookupError(f"{d} 이전 영업일이 캘린더 범위 밖")

    def next_business_day(self, d: date) -> date:
        """*엄격히 d 이후* 의 가장 가까운 영업일."""
        cur = d + timedelta(days=1)
        while cur <= self.last:
            if cur in self._bd_set:
                return cur
            cur += timedelta(days=1)
        raise LookupError(f"{d} 이후 영업일이 캘린더 범위 밖")

    def floor(self, d: date) -> date:
        """d 가 영업일이면 그대로, 아니면 가장 가까운 *직전* 영업일."""
        if self.first <= d <= self.last and d in self._bd_set:
            return d
        if d > self.last:
            return self._sorted[-1]
        return self.previous_business_day(d)

    def ceil(self, d: date) -> date:
        """d 가 영업일이면 그대로, 아니면 가장 가까운 *직후* 영업일."""
        if self.first <= d <= self.last and d in self._bd_set:
            return d
        if d < self.first:
            return self._sorted[0]
        return self.next_business_day(d)

    def add_business_days(self, d: date, n: int) -> date:
        """*영업일 기준* n 만큼 이동.

        n > 0: 미래 방향으로 n 영업일.
        n < 0: 과거 방향으로 |n| 영업일.
        n == 0: d 가 영업일이면 그대로, 아니면 직전 영업일로 floor.

        D7 (DART 공시 접수일 + 1영업일) 은 `add_business_days(rcept_dt, 1)`
        또는 `next_business_day(rcept_dt)` 로 표현된다.
        """
        if n == 0:
            return self.floor(d)
        if n > 0:
            cur = d if d in self._bd_set else self.previous_business_day(d)
            for _ in range(n):
                cur = self.next_business_day(cur)
            return cur
        # n < 0
        cur = d if d in self._bd_set else self.next_business_day(d)
        for _ in range(-n):
            cur = self.previous_business_day(cur)
        return cur

    # ---- 범위 추출 -------------------------------------------------------

    def business_days_between(self, start: date, end: date) -> list[date]:
        """[start, end] 폐구간 안의 영업일 모두 (오름차순)."""
        if start > end:
            raise ValueError(f"start={start} > end={end}")
        return [d for d in self._sorted if start <= d <= end]

    # ---- 캐시 + fetch ----------------------------------------------------

    CACHE_REL_DIR = Path("data/raw/calendars")
    _CACHE_NAME = "kospi_business_days_{start}_{end}.parquet"

    @classmethod
    def from_cache_or_fetch(
        cls,
        start: date,
        end: date,
        project_root: Path | None = None,
    ) -> KRXBusinessCalendar:
        """캐시가 있으면 로딩, 없으면 FDR로 fetch 후 캐시."""
        root = Path(project_root) if project_root else Path.cwd()
        cache_dir = root / cls.CACHE_REL_DIR
        cache_path = cache_dir / cls._CACHE_NAME.format(
            start=start.isoformat(), end=end.isoformat()
        )
        if cache_path.exists():
            logger.info("calendars cache hit: %s", cache_path)
            df = pd.read_parquet(cache_path)
            days = [_to_date(d) for d in df["business_day"]]
            return cls(business_days=days)

        logger.info("calendars cache miss, fetching from FDR")
        cal = cls.fetch_from_fdr(start, end)
        cache_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"business_day": [pd.Timestamp(d) for d in cal._sorted]}).to_parquet(
            cache_path
        )
        logger.info("calendars cache written: %s", cache_path)
        return cal

    @classmethod
    def fetch_from_fdr(cls, start: date, end: date) -> KRXBusinessCalendar:
        """FDR의 KS200 지수 일별 OHLCV index에서 영업일 추출."""
        import FinanceDataReader as fdr  # 지연 import: 단위 테스트는 fdr 없이 가능

        df = fdr.DataReader("KS200", start.isoformat(), end.isoformat())
        if df is None or len(df) == 0:
            raise RuntimeError(f"FDR KS200 시계열이 비어 있음 (start={start}, end={end})")
        days = [_to_date(d) for d in df.index]
        return cls(business_days=days)


# ---- 유틸 -----------------------------------------------------------------


def _to_date(v: object) -> date:
    """`date` 또는 `Timestamp`/`datetime`/문자열을 `date` 로 정규화."""
    if isinstance(v, date) and not isinstance(v, pd.Timestamp):
        # pd.Timestamp는 date의 서브클래스이므로 별도 처리
        return v
    if isinstance(v, pd.Timestamp):
        return v.date()
    if hasattr(v, "date") and callable(v.date):
        return v.date()  # type: ignore[no-any-return]
    if isinstance(v, str):
        return date.fromisoformat(v)
    raise TypeError(f"date로 정규화 불가: {v!r} (type={type(v).__name__})")
