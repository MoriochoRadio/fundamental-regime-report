"""FDR 관리종목 데이터 가용성 + D2 양성 표본 통합 진단.

배경 (2026-05-18 사용자 발견):
- KRX 정보데이터시스템 메뉴 [12006] 은 *이벤트 이력 형태가 아님* (시점별
  스냅샷). D2 옵션 E (상폐 합집합 관리종목 지정, 1년 forward) 을 *자동* 으로
  성립시키려면 FDR이 관리종목 *지정·해제 이력* 을 제공해야 한다.

검증 영역:
1. FDR 카테고리 탐색 — `StockListing` 의 가능한 키
2. delisting 테이블의 `ArrantEnforceDate`/`ArrantEndDate` 결측·유효
3. **결정적 의문**: delisting 테이블은 *상폐된 종목만* — *현재 상장 중인데
   과거 관리종목 지정 후 정상화* 종목이 *완전히 누락* 되는가?
4. 우리 유니버스 매칭 + 2015-2024 범위 분포
5. D2 양성 표본 합산: 상폐만 / 관리종목만 / 중복 / walk-forward 분포
"""

from __future__ import annotations

import contextlib
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

with contextlib.suppress(AttributeError, OSError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parent.parent

from frr.data.fdr import FDRDataSource  # noqa: E402
from frr.data.universe_loader import KOSPI200QuarterlyLoader  # noqa: E402


def section(t: str) -> None:
    print()
    print("=" * 72)
    print(t)
    print("=" * 72)


# ---- 1. FDR StockListing 카테고리 탐색 ----------------------------------

section("1. FDR StockListing 가능한 카테고리 탐색")

import FinanceDataReader as fdr  # noqa: E402

# 알려진 카테고리들
known_keys = [
    "KRX",
    "KOSPI",
    "KOSDAQ",
    "KRX-DELISTING",
    "KRX-ADMIN",
    "KRX-ADMINISTRATIVE",
    "KRX-INVESTMENT-CAUTION",
    "KRX-INVESTMENT-WARNING",
    "KRX-INVESTMENT-ALERT",
    "KRX-MARKETCAP",
]
for key in known_keys:
    try:
        df = fdr.StockListing(key)
        if df is not None and len(df) > 0:
            print(f"  OK  '{key}': shape={df.shape}, cols={list(df.columns)[:8]}...")
        else:
            print(f"  EMPTY '{key}'")
    except NotImplementedError:
        print(f"  N/A  '{key}': NotImplementedError")
    except Exception as e:
        print(f"  FAIL '{key}': {type(e).__name__}: {str(e)[:60]}")


# ---- 2. delisting 테이블의 Arrant 컬럼 분석 ------------------------------

section("2. delisting 테이블의 ArrantEnforceDate / ArrantEndDate 분석")

src = FDRDataSource(project_root=PROJECT_ROOT)
delisting = src.delisting()

print(f"  전체 delisting rows: {len(delisting)}")
print(f"  ArrantEnforceDate dtype: {delisting['ArrantEnforceDate'].dtype}")
print(f"  ArrantEndDate    dtype: {delisting['ArrantEndDate'].dtype}")

enforce_valid = delisting["ArrantEnforceDate"].notna().sum()
end_valid = delisting["ArrantEndDate"].notna().sum()
print(
    f"\n  ArrantEnforceDate 유효: {enforce_valid} / {len(delisting)} "
    f"({100 * enforce_valid / len(delisting):.1f}%)"
)
print(
    f"  ArrantEndDate    유효: {end_valid} / {len(delisting)} "
    f"({100 * end_valid / len(delisting):.1f}%)"
)

# 둘 다 유효 (지정·해제 둘 다 있음)
both_valid = (delisting["ArrantEnforceDate"].notna() & delisting["ArrantEndDate"].notna()).sum()
print(f"  지정·해제 둘 다 유효: {both_valid} 건")


# ---- 3. 2015-2024 범위 분포 ---------------------------------------------

section("3. ArrantEnforceDate 2015-2024 범위 분포 (delisting 테이블 한정)")

mask_arrant_window = (delisting["ArrantEnforceDate"] >= pd.Timestamp("2015-01-01")) & (
    delisting["ArrantEnforceDate"] <= pd.Timestamp("2024-12-31")
)
arrant_in_window = delisting[mask_arrant_window]
print(f"  2015-2024 ArrantEnforceDate: {len(arrant_in_window)} 건")

# 연도별
print("\n  연도별:")
years = pd.to_datetime(arrant_in_window["ArrantEnforceDate"]).dt.year
for year, n in years.value_counts().sort_index().items():
    print(f"    {year}: {n:3d}")

# 시장별
print("\n  시장별:")
for mkt, n in arrant_in_window["Market"].value_counts().items():
    print(f"    {mkt}: {n}")

# 6자리 일반 종목만
mask_6digit = arrant_in_window["Symbol"].str.len() == 6
print(f"\n  6자리 종목코드만: {mask_6digit.sum()}")


# ---- 4. 우리 유니버스 매칭 ----------------------------------------------

section("4. 우리 유니버스(KOSPI200 union 321 종목) 매칭")

loader = KOSPI200QuarterlyLoader.from_default(project_root=PROJECT_ROOT)
universe_union: set[str] = set()
for q in loader.available_quarters():
    universe_union.update(loader.tickers(q))
print(f"  유니버스 union: {len(universe_union)} 종목")

# 유니버스에 있고 ArrantEnforceDate 가 2015-2024 범위인 행
mask_in_universe = arrant_in_window["Symbol"].isin(universe_union)
arrant_in_uni = arrant_in_window[mask_in_universe]
print(
    f"  유니버스 + 2015-2024 ArrantEnforceDate: {len(arrant_in_uni)} 건 "
    f"(고유 종목 {arrant_in_uni['Symbol'].nunique()})"
)

# 종목별 사례
print("\n  유니버스 내 관리종목 지정 사례 (Symbol/Name/EnforceDate/EndDate/Reason):")
for _, row in arrant_in_uni.head(20).iterrows():
    enf = row["ArrantEnforceDate"]
    end = row["ArrantEndDate"]
    enf_s = enf.strftime("%Y-%m-%d") if pd.notna(enf) else "NaN"
    end_s = end.strftime("%Y-%m-%d") if pd.notna(end) else "NaN"
    print(f"    {row['Symbol']} {row['Name']:12s} {enf_s} → {end_s}  {row.get('Reason', '')[:40]}")


# ---- 5. ★ 결정적 검증: 정상화 종목 누락 여부 ----------------------------

section("5. ★ 결정적 의문 — 정상화 종목 누락 확인")

# *현재 상장 중*인 종목 (FDR 'KOSPI' listing) 과 delisting 테이블의 차집합 검증
try:
    current_kospi = fdr.StockListing("KOSPI")
    current_codes = set(current_kospi["Code"].astype(str).str.zfill(6))
    print(f"  현재 KOSPI 상장 종목: {len(current_codes)}")

    # delisting 테이블의 종목들 = 모두 *상폐된* 종목
    delisted_codes = set(delisting["Symbol"].astype(str).str.zfill(6))
    print(f"  delisting 테이블 종목: {len(delisted_codes)}")

    # 두 집합 교집합 = 매우 적어야 정상 (재상장 케이스)
    intersection = current_kospi & delisting if False else current_codes & delisted_codes
    print(f"  교집합 (현 상장 + delisting): {len(intersection)} 종목")

    # 결정적 사실: delisting 테이블 = 폐지된 종목 only
    # → ArrantEnforceDate 가 delisting 에만 있으면 *현재 상장 중인데 과거 관리종목*은 *완전 누락*
except Exception as e:
    print(f"  FAIL: {e}")

print("\n  → 의미:")
print("    delisting 테이블의 ArrantEnforceDate 는 *상폐된 종목들의 과거 관리종목 이력*만")
print("    포함한다. **현재 상장 중이지만 과거 관리종목 지정 후 정상화된 종목은 누락**.")
print("    이 누락이 D2 양성 표본의 상당 부분에 해당할 수 있다.")


# ---- 6. D2 양성 표본 합산 분석 (상폐만/관리만/중복/walk-forward) -----

section("6. D2 양성 표본 합산 — 현재 데이터(FDR delisting only) 기준")

# 분석 기간 2015-2024
mask_delist_window = (
    (delisting["DelistingDate"] >= pd.Timestamp("2015-01-01"))
    & (delisting["DelistingDate"] <= pd.Timestamp("2024-12-31"))
    & (delisting["Market"] == "KOSPI")
    & (delisting["Symbol"].str.len() == 6)
)
delisted_window = delisting[mask_delist_window]

# 유니버스 ∩ 상폐 (분석 기간)
delisted_universe = delisted_window[delisted_window["Symbol"].isin(universe_union)]
print(f"  (a) 유니버스 ∩ 상폐(2015-2024): {len(delisted_universe)} 건")

# 부실 사유 필터
distress_keywords = ["잠식", "해산", "감사", "부도", "회생", "관리"]
mask_distress = (
    delisted_universe["Reason"]
    .astype(str)
    .apply(lambda r: any(kw in r for kw in distress_keywords))
)
delisted_distress = delisted_universe[mask_distress]
print(f"      그 중 *부실 사유* 만: {len(delisted_distress)} 건")
print(f"      *비부실* (지주회사 자회사화 등): {(~mask_distress).sum()} 건")

# 유니버스 ∩ 관리종목(2015-2024)
mask_arrant_uni_window = (
    arrant_in_uni["Symbol"].notna()  # 이미 필터됨
)
arrant_distress = arrant_in_uni[mask_arrant_uni_window]
print(
    f"\n  (b) 유니버스 ∩ 관리종목(2015-2024, delisting 테이블에 한정): "
    f"{len(arrant_distress)} 건 (고유 {arrant_distress['Symbol'].nunique()})"
)

# (a) ∩ (b) — 상폐 + 관리종목 중복
overlap = set(delisted_distress["Symbol"]) & set(arrant_distress["Symbol"])
print(f"\n  (c) (a 부실 상폐) ∩ (b 관리종목) 중복 종목 수: {len(overlap)}")

# (a 합집합 b) — 합집합
union_set = set(delisted_distress["Symbol"]) | set(arrant_distress["Symbol"])
print(f"  (d) 합집합 (D2 양성 후보, 고유 종목): {len(union_set)}")

# walk-forward 분포: 연도별 양성 표본 (상폐 OR 관리종목 지정)
print("\n  연도별 양성 분포 (상폐 OR 관리종목 지정):")
events_by_year: dict[int, set[str]] = defaultdict(set)
for _, r in delisted_distress.iterrows():
    events_by_year[r["DelistingDate"].year].add(r["Symbol"])
for _, r in arrant_distress.iterrows():
    if pd.notna(r["ArrantEnforceDate"]):
        events_by_year[r["ArrantEnforceDate"].year].add(r["Symbol"])

for year in sorted(events_by_year.keys()):
    print(f"    {year}: {len(events_by_year[year])} 종목")

# 종합 평가
section("결과 요약")
enforce_pct = 100 * enforce_valid / len(delisting)
n_arrant_uni = arrant_in_uni["Symbol"].nunique()
n_arrant_distress = arrant_distress["Symbol"].nunique()
print(f"  - FDR delisting 테이블 ArrantEnforceDate 가용: {enforce_valid} 행 ({enforce_pct:.1f}%)")
print(f"  - 우리 유니버스 매칭: {n_arrant_uni} 고유 종목")
print("  - 한계: 현재 상장 중 + 과거 관리종목 정상화 종목은 delisting 테이블에 없음 → 누락")
print(
    f"  - D2 양성 합산(현 데이터): 고유 {len(union_set)} 종목 "
    f"(상폐 부실 {len(delisted_distress)} + 관리종목 {n_arrant_distress} - 중복 {len(overlap)})"
)
