"""FinanceDataReader (FDR) 어댑터.

역할:
- 현 시점 **KOSPI 전종목 메타데이터** (`Code`, `Name`, `Marcap`,
  `ListingShares`, …) — 현재 시점 스냅샷이므로 *유니버스 시점별 구성은
  여기에서 가져오지 않는다*. 시점별 KOSPI200 구성은
  `universe_loader.KOSPI200QuarterlyLoader` (KRX 수동 CSV) 담당.
- **KRX 상장폐지 데이터** (`Symbol`, `Name`, `ListingDate`,
  `DelistingDate`, `Reason`, …) — 단계 2의 D2 부실 라벨 정의에 사용.

데이터 소스 결정 근거:
- pykrx 의 *시점별 전종목/인덱스* API 는 KRX 변경으로 모두 망가졌음
  (단계 1 가용성 검증 참고). FDR 의 `StockListing` 패키지가 *현 시점*
  KOSPI 전종목 + 상장폐지 데이터의 유일한 자동 출처.

★ 격리 원칙 (CLAUDE.md §5 박제):
- `delisting()` 의 컬럼 — 특히 `DelistingDate`·`Reason`·
  `ArrantEnforceDate` — 는 *결과 변수*이므로 펀더멘털 모델의
  **피처로 사용 금지**. 라벨(D2) 정의에만 흘러간다.
- 단계 2 진입 시 *상장폐지 메타데이터 격리 검증 테스트*를 추가해
  이 원칙이 코드 상에서 깨지지 않음을 자동 점검한다.

캐시 정책:
- `data/raw/fdr/*.parquet` (gitignored).
- 시점 데이터가 아닌 *현재 시점 스냅샷*이라 자주 변하지만 분석 기간에
  비하면 안정적이다. `refresh=True`로 강제 재수집 가능.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class FDRDataSource:
    """FDR StockListing 호출 + parquet 캐시."""

    DEFAULT_CACHE_REL_DIR = Path("data/raw/fdr")

    def __init__(
        self,
        project_root: Path | None = None,
        cache_rel_dir: Path | None = None,
    ) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.cache_rel_dir = Path(cache_rel_dir) if cache_rel_dir else self.DEFAULT_CACHE_REL_DIR

    @property
    def cache_dir(self) -> Path:
        return self.project_root / self.cache_rel_dir

    # ---- 공개 API --------------------------------------------------------

    def listing(self, *, refresh: bool = False) -> pd.DataFrame:
        """현 시점 KOSPI 전종목 리스트.

        반환 컬럼 (FDR 0.9.x 기준): Code, ISU_CD, Name, Market, Dept,
        Close, ChangeCode, Changes, ChagesRatio, Open, High, Low, Volume,
        Amount, Marcap, Stocks, MarketId. `Code` 는 6자리 문자열로 보장.
        """
        return self._read_or_fetch(
            cache_name="stocklisting_kospi.parquet",
            fdr_key="KOSPI",
            refresh=refresh,
        )

    def delisting(self, *, refresh: bool = False) -> pd.DataFrame:
        """KRX 상장폐지 종목 (전체 시장·전 기간).

        반환 컬럼: Symbol, Name, Market, SecuGroup, Kind, ListingDate,
        DelistingDate, Reason, ArrantEnforceDate, ArrantEndDate, Industry,
        ParValue, ListingShares, ToSymbol, ToName. 종목코드(`Symbol`) 와
        날짜 컬럼은 dtype 정규화됨.
        """
        return self._read_or_fetch(
            cache_name="stocklisting_delisting.parquet",
            fdr_key="KRX-DELISTING",
            refresh=refresh,
        )

    # ---- 내부 ------------------------------------------------------------

    def _read_or_fetch(
        self,
        *,
        cache_name: str,
        fdr_key: str,
        refresh: bool,
    ) -> pd.DataFrame:
        cache = self.cache_dir / cache_name
        if cache.exists() and not refresh:
            logger.info("fdr cache hit: %s", cache)
            return pd.read_parquet(cache)
        logger.info("fdr cache miss, fetching '%s'", fdr_key)
        df = _fetch_stock_listing(fdr_key)
        df = _normalize_dtypes(df)
        cache.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache)
        logger.info("fdr cache written: %s (%d rows)", cache, len(df))
        return df


# ---- 모듈 함수 ------------------------------------------------------------


def _fetch_stock_listing(key: str) -> pd.DataFrame:
    """FDR StockListing 호출 (지연 import — 단위 테스트에서 mock 가능)."""
    import FinanceDataReader as _fdr  # alias로 모듈명 충돌 회피

    df = _fdr.StockListing(key)
    if df is None or len(df) == 0:
        raise RuntimeError(f"FDR StockListing('{key}') 결과가 비어 있음")
    return df.reset_index(drop=True)


def _normalize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """종목코드를 6자리 str로, 날짜 컬럼을 datetime64로 정규화."""
    df = df.copy()

    # 종목코드 컬럼: KOSPI listing 은 'Code', delisting 은 'Symbol'.
    # 앞 0 보존이 가장 중요한 dtype 결정 (CLAUDE.md / docs/data_sources.md §3.4).
    for col in ("Code", "Symbol"):
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"\.0$", "", regex=True)  # float→str 캐스팅 잔재 제거
                .str.zfill(6)
            )

    # 날짜 컬럼: pandas datetime64 로
    for col in ("ListingDate", "DelistingDate", "ArrantEnforceDate", "ArrantEndDate"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df
