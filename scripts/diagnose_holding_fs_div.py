"""지주회사·금융지주 CFS vs OFS 영업이익 spot-check 진단 (PROGRESS §5.5.14 β1).

D2 양성 20 종목 중 지주회사·금융지주 후보를 키워드로 식별 → 각 종목의
FY 2015~2024 CFS·OFS 영업이익을 비교 → 희석/증폭 분포 요약.

설계 결정 (§5.5.14 + 사용자 (d-1) 채택):
- 기존 CFS 캐시 (data/raw/dart/{ticker}/{year}_FY.parquet) **변경 0**
- OFS 페치는 **별도 경로** data/interim/holding_fs_div/{ticker}_{year}_FY_OFS.{parquet,meta.yaml}
- DARTReporter 우회 (OpenDartReader 직접 사용 — 일회성 진단)
- 재실행 시 별도 캐시 hit 으로 페치 0

연관 자료:
- PROGRESS §5.5.7 (양성 20 = A=1 + B=19)
- PROGRESS §5.5.9 (신 SK 034730 FY2019→FY2020 4.1조 감소, 증폭 사례)
- PROGRESS §5.5.14 (β1 spot-check 시점 합의)
"""

from __future__ import annotations

import contextlib
import logging
import os
import sys
from collections.abc import Iterable
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from frr.data.fdr import FDRDataSource  # noqa: E402

# Windows cp949 콘솔에서도 한국어 출력 가능하게
with contextlib.suppress(AttributeError, OSError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]


# === 양성 20 종목 (capture_d2_positives.py 와 일관) ==========================
A_TICKERS = frozenset({"051310"})  # 포스코플랜텍 (자본전액잠식, 2016-04-15)
B_TICKERS = frozenset(
    {
        "003920", "005070", "007810", "008060", "010690", "010950", "019680",
        "029530", "033240", "034730", "035250", "047810", "066970", "073240",
        "096770", "267250", "267260", "361610", "450080",
    }
)  # fmt: skip
POSITIVE_20 = A_TICKERS | B_TICKERS

# === 지주·금융지주 식별 키워드 ===============================================
HOLDING_KEYWORDS = ("지주", "홀딩스", "홀딩", "금융지주", "은행지주")

# === 분석 범위 ===============================================================
FY_YEARS = list(range(2015, 2025))  # 2015~2024
CFS_CACHE = PROJECT_ROOT / "data" / "raw" / "dart"
OFS_CACHE = PROJECT_ROOT / "data" / "interim" / "holding_fs_div"


logger = logging.getLogger(__name__)


def _name_lookup(positives: Iterable[str]) -> dict[str, str]:
    """FDR listing + delisting 에서 ticker → Name 매핑."""
    fdr = FDRDataSource(project_root=PROJECT_ROOT)
    listing = fdr.listing()
    delisting = fdr.delisting()
    name_map: dict[str, str] = {}
    # listing 은 Code, delisting 은 Symbol 컬럼명 — fdr_ticker_key 작성 전 임시
    listing_idx = listing.set_index("Code")["Name"].to_dict() if "Code" in listing.columns else {}
    delist_idx = (
        delisting.set_index("Symbol")["Name"].to_dict() if "Symbol" in delisting.columns else {}
    )
    for ticker in positives:
        name = listing_idx.get(ticker) or delist_idx.get(ticker) or "<NOT FOUND>"
        name_map[ticker] = name
    return name_map


def _identify_holdings(positives: Iterable[str], name_map: dict[str, str]) -> list[str]:
    """이름에 키워드 매칭으로 지주·금융지주 후보 추출."""
    holdings = []
    for ticker in sorted(positives):
        name = name_map.get(ticker, "")
        if any(kw in name for kw in HOLDING_KEYWORDS):
            holdings.append(ticker)
    return holdings


def _get_op_income_from_parquet(parquet_path: Path) -> float | None:
    """labels.py `_get_op_income` 와 byte-for-byte 동일 로직."""
    if not parquet_path.exists():
        return None
    try:
        df = pd.read_parquet(parquet_path)
    except Exception:
        return None
    mask = df["account_nm"].astype(str).str.contains("영업이익", na=False)
    if not mask.any():
        return None
    val_str = str(df[mask].iloc[0].get("thstrm_amount", "")).replace(",", "").replace(" ", "")
    if val_str in ("", "nan", "None", "-"):
        return None
    try:
        return float(val_str)
    except ValueError:
        return None


def _cfs_op_income(ticker: str, year: int) -> float | None:
    """기존 CFS 캐시에서 영업이익 추출."""
    parquet = CFS_CACHE / ticker / f"{year}_FY.parquet"
    return _get_op_income_from_parquet(parquet)


def _ofs_op_income(ticker: str, year: int, odr) -> float | None:  # type: ignore[no-untyped-def]
    """OFS 페치 + 별도 캐시 (재실행 시 hit)."""
    parquet = OFS_CACHE / f"{ticker}_{year}_FY_OFS.parquet"
    meta = OFS_CACHE / f"{ticker}_{year}_FY_OFS.meta.yaml"

    # 캐시 hit
    if parquet.exists() and meta.exists():
        m = yaml.safe_load(meta.read_text(encoding="utf-8"))
        if m.get("status") == "ok":
            return _get_op_income_from_parquet(parquet)
        return None  # notfound 캐시

    OFS_CACHE.mkdir(parents=True, exist_ok=True)
    try:
        df = odr.finstate_all(ticker, year, reprt_code="11011", fs_div="OFS")
    except Exception as e:
        logger.warning("OFS fetch 실패 %s/%d: %s", ticker, year, e)
        meta.write_text(
            yaml.safe_dump({"ticker": ticker, "year": year, "status": "error", "error": str(e)}),
            encoding="utf-8",
        )
        return None

    if df is None or len(df) == 0:
        meta.write_text(
            yaml.safe_dump({"ticker": ticker, "year": year, "status": "notfound", "fs_div": "OFS"}),
            encoding="utf-8",
        )
        return None

    df.to_parquet(parquet)
    meta.write_text(
        yaml.safe_dump(
            {"ticker": ticker, "year": year, "status": "ok", "fs_div": "OFS", "rows": len(df)}
        ),
        encoding="utf-8",
    )
    return _get_op_income_from_parquet(parquet)


def _classify(op_cfs: float | None, op_ofs: float | None) -> tuple[str, float | None]:
    """희석/증폭 분류 — (큰 카테고리, ratio 수치).

    카테고리: 둘 다 없음 / CFS 없음 / OFS 없음 / 증폭 / 희석 / 유사 /
              부호 차이 (CFS+OFS-) / 부호 차이 (CFS-OFS+) / 둘 다 음수
    ratio = op_cfs / op_ofs (둘 다 양수일 때만 의미, 아니면 None).
    """
    if op_cfs is None and op_ofs is None:
        return ("둘 다 없음", None)
    if op_cfs is None:
        return ("CFS 없음", None)
    if op_ofs is None:
        return ("OFS 없음", None)
    if op_cfs > 0 and op_ofs > 0:
        ratio = op_cfs / op_ofs
        if ratio > 1.5:
            return ("증폭", ratio)
        if ratio < 0.67:
            return ("희석", ratio)
        return ("유사", ratio)
    if op_cfs > 0 > op_ofs:
        return ("부호 차이 (CFS+/OFS-)", None)
    if op_cfs < 0 < op_ofs:
        return ("부호 차이 (CFS-/OFS+)", None)
    if op_cfs < 0 and op_ofs < 0:
        # 둘 다 음수도 ratio 의미 — abs 기준
        ratio = abs(op_cfs) / abs(op_ofs)
        return ("둘 다 음수", ratio)
    return ("기타", None)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    load_dotenv()

    if not os.environ.get("DART_API_KEY"):
        print("ERROR: DART_API_KEY 미설정 (.env 또는 환경변수 필요)", file=sys.stderr)
        return 2

    print("양성 20 종목 식별:")
    print(f"  A=1: {sorted(A_TICKERS)}")
    print(f"  B=19: {len(B_TICKERS)} 종목")

    name_map = _name_lookup(POSITIVE_20)
    print(f"\nFDR Name 매핑 ({len(name_map)} 종목):")
    for t in sorted(POSITIVE_20):
        print(f"  {t}: {name_map[t]}")

    keyword_holdings = _identify_holdings(POSITIVE_20, name_map)
    print(
        f"\n키워드 매칭 지주·금융지주 후보 ({len(keyword_holdings)} 종목, "
        f"키워드={HOLDING_KEYWORDS}):"
    )
    for t in keyword_holdings:
        print(f"  {t}: {name_map[t]}")
    if not keyword_holdings:
        print(
            "  (키워드 0 매칭 — 사명 변경·영문 약어로 인한 false negative. "
            "PROGRESS §3 DoD + §5.5.9 박제: 034730 SK·267250 HD현대 등 실제 지주성 종목 존재.)"
        )

    # 사용자 옵션 (B): 양성 20 전체 spot-check (키워드 매칭 우회)
    holdings = sorted(POSITIVE_20)
    print(f"\n사용자 선택 (B) — 양성 20 전체 OFS 페치 + 분포 spot-check ({len(holdings)} 종목)")

    # OpenDartReader 지연 import (env 검증 후)
    import opendartreader

    odr = opendartreader.OpenDartReader(os.environ["DART_API_KEY"])

    print(f"\n=== CFS vs OFS 영업이익 spot-check (FY {FY_YEARS[0]}~{FY_YEARS[-1]}) ===\n")
    print(
        f"{'ticker':<8} {'name':<20} {'year':<6} {'op_CFS':>18} {'op_OFS':>18}  {'cat':<24} ratio"
    )
    print("-" * 110)

    rows: list[dict] = []
    fetch_count = 0
    for ticker in holdings:
        for year in FY_YEARS:
            cfs = _cfs_op_income(ticker, year)
            # OFS: 캐시 hit 아니면 fetch (fetch_count 추적)
            ofs_parquet = OFS_CACHE / f"{ticker}_{year}_FY_OFS.parquet"
            ofs_meta = OFS_CACHE / f"{ticker}_{year}_FY_OFS.meta.yaml"
            cache_existed = ofs_parquet.exists() or ofs_meta.exists()
            ofs = _ofs_op_income(ticker, year, odr)
            if not cache_existed:
                fetch_count += 1
            category, ratio = _classify(cfs, ofs)
            cfs_s = f"{cfs:>18,.0f}" if cfs is not None else f"{'None':>18}"
            ofs_s = f"{ofs:>18,.0f}" if ofs is not None else f"{'None':>18}"
            ratio_s = f"{ratio:.2f}" if ratio is not None else "-"
            print(
                f"{ticker:<8} {name_map[ticker]:<20} {year:<6} {cfs_s} {ofs_s}  "
                f"{category:<24} {ratio_s}"
            )
            rows.append(
                {
                    "ticker": ticker,
                    "name": name_map[ticker],
                    "year": year,
                    "op_cfs": cfs,
                    "op_ofs": ofs,
                    "category": category,
                    "ratio": ratio,
                }
            )

    total_cells = len(holdings) * len(FY_YEARS)
    print(f"\nOFS 페치 발생: {fetch_count} (총 {total_cells} 셀 중 — 나머지 캐시 hit)")

    # 요약 표
    from collections import Counter

    category_ctr: Counter = Counter(r["category"] for r in rows)
    print("\n=== category 분포 ===")
    for k, v in sorted(category_ctr.items(), key=lambda x: -x[1]):
        print(f"  {v:>4}  {k}")

    # 증폭/희석 ratio 통계
    amp_ratios = [r["ratio"] for r in rows if r["category"] == "증폭" and r["ratio"] is not None]
    dil_ratios = [r["ratio"] for r in rows if r["category"] == "희석" and r["ratio"] is not None]
    if amp_ratios:
        print(
            f"\n증폭 ratio (CFS/OFS, n={len(amp_ratios)}): "
            f"median {sorted(amp_ratios)[len(amp_ratios) // 2]:.2f}, "
            f"max {max(amp_ratios):.2f}, min {min(amp_ratios):.2f}"
        )
    if dil_ratios:
        print(
            f"희석 ratio (CFS/OFS, n={len(dil_ratios)}): "
            f"median {sorted(dil_ratios)[len(dil_ratios) // 2]:.2f}, "
            f"max {max(dil_ratios):.2f}, min {min(dil_ratios):.2f}"
        )

    # 종목별 category 분포
    print("\n=== 종목별 category 분포 ===")
    by_ticker: dict[str, Counter] = {}
    for r in rows:
        by_ticker.setdefault(r["ticker"], Counter())[r["category"]] += 1
    for ticker in sorted(by_ticker.keys()):
        cats = by_ticker[ticker]
        cat_str = ", ".join(f"{c}={n}" for c, n in cats.most_common())
        print(f"  {ticker} {name_map[ticker]:<20} {cat_str}")

    # 박제용 결과 dump
    summary_path = OFS_CACHE / "diagnose_summary.yaml"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        yaml.safe_dump(
            {
                "generated_at": pd.Timestamp.now().isoformat(),
                "keyword_match_count": len(keyword_holdings),
                "keyword_match_tickers": [
                    {"ticker": t, "name": name_map[t]} for t in keyword_holdings
                ],
                "spot_check_mode": "option_B_full_20",
                "spot_check_tickers": [{"ticker": t, "name": name_map[t]} for t in holdings],
                "category_distribution": dict(category_ctr),
                "rows": rows,
                "fetch_count": fetch_count,
                "total_cells": len(holdings) * len(FY_YEARS),
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    print(f"\n요약 dump: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
