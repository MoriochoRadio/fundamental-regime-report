"""단계 1 전체 수집 결과 진단.

세 가지:
1. 실패 7건의 실제 rcept_dt — 정정공시 가설 검증
2. notfound 2,719건 종목별 분포 — point-in-time 기대 패턴 검증
3. 상폐 양성 표본 추정 — D2 자료의 기초

본 스크립트는 *진단 1회성*이라 git 추적은 하지만 *재현 절차*로 보관.
"""

from __future__ import annotations

import contextlib
import os
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv

with contextlib.suppress(AttributeError, OSError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def section(t: str) -> None:
    print()
    print("=" * 72)
    print(t)
    print("=" * 72)


# ---- 1. 실패 7건의 실제 rcept_dt 확인 -----------------------------------

section("1. 실패 7건의 실제 rcept_dt 진단")

import opendartreader  # noqa: E402

odr = opendartreader.OpenDartReader(os.environ["DART_API_KEY"])

REPORT_CODES = {"Q1": "11013", "H1": "11012", "Q3": "11014", "FY": "11011"}

failures = [
    ("013890", 2021, "FY"),
    ("013890", 2022, "FY"),
    ("013890", 2023, "FY"),
    ("013890", 2024, "FY"),
    ("018880", 2024, "FY"),
    ("105560", 2024, "H1"),
    ("105560", 2024, "FY"),
]

for ticker, year, period in failures:
    try:
        df = odr.finstate(ticker, year, reprt_code=REPORT_CODES[period])
        if df is None or len(df) == 0:
            print(f"  {ticker} {year}/{period}: 빈 결과")
            continue
        rcept_no = str(df["rcept_no"].iloc[0])
        rcept_dt = f"{rcept_no[:4]}-{rcept_no[4:6]}-{rcept_no[6:8]}"
        print(f"  {ticker} {year}/{period}: rcept_dt={rcept_dt} (rcept_no={rcept_no})")
    except Exception as e:
        print(f"  {ticker} {year}/{period}: FAIL {type(e).__name__}: {e}")


# ---- 2. notfound 종목별 분포 -------------------------------------------

section("2. notfound 2,719건 종목별 분포")

cache_dir = PROJECT_ROOT / "data" / "raw" / "dart"
status_by_ticker: dict[str, dict[str, int]] = defaultdict(lambda: {"ok": 0, "notfound": 0})

for ticker_dir in sorted(cache_dir.iterdir()):
    if not ticker_dir.is_dir():
        continue
    ticker = ticker_dir.name
    for meta_path in ticker_dir.glob("*.meta.yaml"):
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        status = meta.get("status", "unknown")
        if status in status_by_ticker[ticker]:
            status_by_ticker[ticker][status] += 1

# 비율별 분포
buckets = {
    "0% (전체 ok)": 0,
    "0-25%": 0,
    "25-50%": 0,
    "50-75%": 0,
    "75-99%": 0,
    "100% (전체 notfound)": 0,
}
for _ticker, c in status_by_ticker.items():
    total = c["ok"] + c["notfound"]
    if total == 0:
        continue
    pct = c["notfound"] / total
    if pct == 0:
        buckets["0% (전체 ok)"] += 1
    elif pct < 0.25:
        buckets["0-25%"] += 1
    elif pct < 0.5:
        buckets["25-50%"] += 1
    elif pct < 0.75:
        buckets["50-75%"] += 1
    elif pct < 1.0:
        buckets["75-99%"] += 1
    else:
        buckets["100% (전체 notfound)"] += 1

print("  종목별 notfound 비율 분포:")
for k, v in buckets.items():
    print(f"    {k:30s}: {v:3d} 종목")

print(f"\n  총 {len(status_by_ticker)} 종목 메타 파일 확인")

# notfound 많은 종목 top 15
sorted_t = sorted(status_by_ticker.items(), key=lambda x: -x[1]["notfound"])
print("\n  notfound 많은 종목 top 15:")
for ticker, counts in sorted_t[:15]:
    print(f"    {ticker}: ok={counts['ok']:2d} notfound={counts['notfound']:2d}")


# ---- 3. 상폐 양성 표본 추정 (D2 자료의 일부) ---------------------------

section("3. 분석 기간 내 KOSPI200 폐지·편출 종목 (D2 양성 추정)")

from frr.data.fdr import FDRDataSource  # noqa: E402
from frr.data.universe_loader import KOSPI200QuarterlyLoader  # noqa: E402

loader = KOSPI200QuarterlyLoader.from_default(project_root=PROJECT_ROOT)
all_quarters = loader.available_quarters()
print(f"  분기 수: {len(all_quarters)} ({all_quarters[0]} ~ {all_quarters[-1]})")

# 모든 분기 union
universe_union: set[str] = set()
for q in all_quarters:
    universe_union.update(loader.tickers(q))
print(f"  유니버스 union 크기: {len(universe_union)}")

# 마지막 분기에 *없는* 종목 = 편출 또는 폐지
last_quarter_set = set(loader.tickers(all_quarters[-1]))
dropped = universe_union - last_quarter_set
print(f"  분석 기간 중 유니버스 이탈 종목: {len(dropped)}")

# FDR delisting 매칭
fdr = FDRDataSource(project_root=PROJECT_ROOT)
delisting = fdr.delisting()
mask_recent = (
    (delisting["DelistingDate"] >= pd.Timestamp("2015-01-01"))
    & (delisting["DelistingDate"] <= pd.Timestamp("2025-12-31"))
    & (delisting["Market"] == "KOSPI")
    & (delisting["Symbol"].str.len() == 6)  # 일반 6자리만, 부산물 종목 제외
)
delisted_kospi = delisting[mask_recent]
print(f"  FDR KOSPI 일반 상폐 (2015-2025): {len(delisted_kospi)} 건")

# 우리 유니버스 ∩ FDR 상폐 = 실제 양성 후보
both = set(dropped) & set(delisted_kospi["Symbol"])
print(f"\n  → 우리 유니버스에서 *실제로 FDR 상폐 기록*된 종목: {len(both)}")
print(f"    예시: {sorted(both)[:15]}")

print(f"\n  주의: D2 옵션 E 의 *상폐* 양성은 위 {len(both)} 종목 기반.")
print("        관리종목 지정 데이터(별도 다운로드)가 추가되면 양성 표본 늘어남.")

# 사유 분포
delisted_in_universe = delisted_kospi[delisted_kospi["Symbol"].isin(dropped)]
print("\n  폐지 사유 (Reason) 분포:")
reason_counts = delisted_in_universe["Reason"].value_counts()
for reason, n in reason_counts.head(15).items():
    print(f"    {n:3d}건  {reason}")

# 연도별 분포 (walk-forward 시점별 양성 추정)
print("\n  연도별 폐지 분포 (walk-forward 양성 표본):")
years = pd.to_datetime(delisted_in_universe["DelistingDate"]).dt.year
year_counts = years.value_counts().sort_index()
for year, n in year_counts.items():
    print(f"    {year}: {n:2d} 건")
