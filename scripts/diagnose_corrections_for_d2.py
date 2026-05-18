"""B1 (정정공시 신호) D2 라벨 후보 검증 — v2 (캐시 + 정밀 필터).

배경:
- KRX 옵션 B (시점별 관리종목 스냅샷)는 [12006] 페이지에 일자 입력 요소
  부재로 *구조적 불가* 확정 → D2 재정의 트랙.
- v1 진단: 광범위 severe 필터 (사업보고서·반기·분기·감사·재무제표 키워드)
  결과 *310/321 종목 양성 = 96.6%* → **라벨 오염 실패 사례**.
- 사용자 지시: 시간 임계 (예: 원본 + 90일 이후) 같은 자의적 규칙 *금지*.
  정정의 *시간 지연*이 아니라 *대상 성격*으로 판별.

v2 변경:
1. corrections 데이터를 `data/raw/dart_corrections/all_corrections.parquet`
   로 캐시 → 재진단 시 DART 호출 0.
2. 정밀 severe 필터 — 정기 재무보고서 정정만:
   - 포함: `[기재정정]사업/반기/분기/감사보고서`, `[첨부정정]…`, `감사보고서제출`
   - 제외: `잠정`, `전망`, `공정공시` (실적·전망 공정공시는 재무 정정 X)

한계:
- report_nm 만으로 *어떤 항목이 정정됐는지* (재무 수치 vs 임원/지분 등)
  까지는 판별 불가. 완전 판별은 정정 본문 파싱 필요.

보고:
(a) 정밀 severe 양성 종목 수 + 유니버스 비율
(b) walk-forward 연도별 양성 분포 — 0 연도 유무
(c) spot-check 상위 10 — 우량주 채움 여부 (정의 헐거움 신호)
(d) 정밀 B1 합집합 상폐 부실 8 최종 양성 비율
"""

from __future__ import annotations

import contextlib
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

with contextlib.suppress(AttributeError, OSError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORRECTIONS_CACHE = PROJECT_ROOT / "data" / "raw" / "dart_corrections" / "all_corrections.parquet"

from frr.data.universe_loader import KOSPI200QuarterlyLoader  # noqa: E402


def section(t: str) -> None:
    print()
    print("=" * 72)
    print(t)
    print("=" * 72)


# ---- 유니버스 -----------------------------------------------------------

loader = KOSPI200QuarterlyLoader.from_default(project_root=PROJECT_ROOT)
universe: set[str] = set()
for q in loader.available_quarters():
    universe.update(loader.tickers(q))
print(f"유니버스 union: {len(universe)} 종목")


# ---- 1. corrections 데이터: 캐시 우선 -----------------------------------

section("1. corrections 데이터 (캐시 또는 DART fetch)")

if CORRECTIONS_CACHE.exists():
    print(f"  캐시 hit: {CORRECTIONS_CACHE}")
    df_corr = pd.read_parquet(CORRECTIONS_CACHE)
    print(f"  로딩: {len(df_corr)} 건")
else:
    print(f"  캐시 miss → DART 호출 ({len(universe)} 종목, ~14분 예상)")
    import opendartreader

    odr = opendartreader.OpenDartReader(os.environ["DART_API_KEY"])
    corrections: list[dict] = []
    fail_count = 0
    start_ts = time.time()
    universe_sorted = sorted(universe)

    for i, ticker in enumerate(universe_sorted, 1):
        try:
            df = odr.list(ticker, "20150101", "20241231")
            if df is None or len(df) == 0:
                continue
            mask = df["report_nm"].astype(str).str.contains("정정", na=False)
            for _, row in df[mask].iterrows():
                corrections.append(
                    {
                        "ticker": ticker,
                        "rcept_dt": str(row["rcept_dt"]),
                        "report_nm": str(row["report_nm"]),
                        "rcept_no": str(row["rcept_no"]),
                    }
                )
        except Exception as e:
            fail_count += 1
            if fail_count <= 3:
                print(f"  FAIL {ticker}: {type(e).__name__}: {str(e)[:60]}")
        if i % 50 == 0:
            elapsed = time.time() - start_ts
            print(f"  [{i}/{len(universe_sorted)}] 누적 {len(corrections)} 건 ({elapsed:.1f}s)")

    df_corr = pd.DataFrame(corrections)
    CORRECTIONS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    df_corr.to_parquet(CORRECTIONS_CACHE)
    print(f"  캐시 저장: {CORRECTIONS_CACHE} ({len(df_corr)} 건, {fail_count} 실패)")


# ---- 2. 정밀 severe 필터 ------------------------------------------------

section("2. 정밀 severe 필터 적용")

INCLUDE_PATTERNS = [
    r"\[기재정정\]사업보고서",
    r"\[첨부정정\]사업보고서",
    r"\[기재정정\]반기보고서",
    r"\[첨부정정\]반기보고서",
    r"\[기재정정\]분기보고서",
    r"\[첨부정정\]분기보고서",
    r"\[기재정정\]감사보고서",
    r"\[첨부정정\]감사보고서",
    r"감사보고서제출",  # "[첨부정정]감사보고서제출" 같은 형태
]
EXCLUDE_KEYWORDS = ["잠정", "전망", "공정공시"]

_include_re = re.compile("|".join(INCLUDE_PATTERNS))


def is_strict_severe(report_nm: str) -> bool:
    rn = str(report_nm)
    if any(kw in rn for kw in EXCLUDE_KEYWORDS):
        return False
    return bool(_include_re.search(rn))


df_corr["is_strict_severe"] = df_corr["report_nm"].apply(is_strict_severe)
strict_severe = df_corr[df_corr["is_strict_severe"]].copy()
strict_severe["rcept_date"] = pd.to_datetime(
    strict_severe["rcept_dt"], format="%Y%m%d", errors="coerce"
)
strict_severe = strict_severe.dropna(subset=["rcept_date"])

print(f"  정밀 severe 매칭: {len(strict_severe)} 건 (전체 {len(df_corr)} 의 "
      f"{100 * len(strict_severe) / len(df_corr):.1f}%)")

# 분석 기간 한정 + 중복 제거
mask_window = (strict_severe["rcept_date"] >= pd.Timestamp("2015-01-01")) & (
    strict_severe["rcept_date"] <= pd.Timestamp("2024-12-31")
)
strict_window = strict_severe[mask_window].drop_duplicates(subset=["ticker", "rcept_no"])
print(f"  2015-2024 + 중복 제거 (rcept_no): {len(strict_window)} 건")

# report_nm 패턴 분포 (정밀 필터 결과 내)
print("\n  정밀 severe — report_nm top 10:")
for nm, n in strict_window["report_nm"].value_counts().head(10).items():
    print(f"    {n:4d}  {nm}")


# ---- 3. (a) 정밀 severe 양성 종목 수 + 비율 -----------------------------

section("3. (a) 정밀 severe 양성 종목 수")

severe_tickers = set(strict_window["ticker"])
print(f"  양성 종목 수: {len(severe_tickers)}")
print(f"  유니버스 대비 비율: {100 * len(severe_tickers) / len(universe):.1f}%")


# ---- 4. (b) walk-forward 연도별 양성 분포 -------------------------------

section("4. (b) walk-forward 연도별 양성 분포")

years = strict_window["rcept_date"].dt.year
year_ticker_sets: dict[int, set[str]] = defaultdict(set)
for _, r in strict_window.iterrows():
    year_ticker_sets[r["rcept_date"].year].add(r["ticker"])

zero_years = []
for year in range(2015, 2025):
    n_events = (years == year).sum()
    n_tickers = len(year_ticker_sets[year])
    flag = " <- ZERO" if n_tickers == 0 else ""
    print(f"  {year}: 이벤트 {n_events:3d} / 고유 종목 {n_tickers:3d}{flag}")
    if n_tickers == 0:
        zero_years.append(year)

print(f"\n  → 양성 0 연도: {zero_years if zero_years else '없음'}")


# ---- 5. (c) spot-check 상위 10 (우량주 채움 여부) -----------------------

section("5. (c) spot-check — 정밀 severe 다발 종목 상위 10")

top_tickers = strict_window["ticker"].value_counts().head(10)
KNOWN_BLUE_CHIPS = {  # 한국 대표 우량주
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "005380": "현대차",
    "066570": "LG전자",
    "035420": "NAVER",
    "035720": "카카오",
    "051910": "LG화학",
    "005490": "POSCO홀딩스",
    "207940": "삼성바이오로직스",
    "006400": "삼성SDI",
    "068270": "셀트리온",
    "105560": "KB금융",
    "055550": "신한지주",
    "086790": "하나금융지주",
    "017670": "SK텔레콤",
    "030200": "KT",
}
blue_count = 0
for ticker, n in top_tickers.items():
    name = KNOWN_BLUE_CHIPS.get(ticker, "")
    blue_flag = " ★ blue-chip" if ticker in KNOWN_BLUE_CHIPS else ""
    if ticker in KNOWN_BLUE_CHIPS:
        blue_count += 1
    print(f"    {ticker} {name:12s}: {n} 건{blue_flag}")
print(f"\n  → top 10 중 우량주(blue-chip): {blue_count} 종목")


# ---- 6. (d) 정밀 B1 합집합 상폐 부실 8 — 최종 양성 -------------------------

section("6. (d) 정밀 B1 합집합 상폐 부실 8 — 최종 양성 비율")

from frr.data.fdr import FDRDataSource  # noqa: E402

delisting = FDRDataSource(project_root=PROJECT_ROOT).delisting()
mask_dl = (
    (delisting["DelistingDate"] >= pd.Timestamp("2015-01-01"))
    & (delisting["DelistingDate"] <= pd.Timestamp("2024-12-31"))
    & (delisting["Market"] == "KOSPI")
    & (delisting["Symbol"].str.len() == 6)
    & (delisting["Symbol"].isin(universe))
)
delisted_universe = delisting[mask_dl]
distress_kw = ["잠식", "해산", "감사", "부도", "회생", "관리"]
mask_distress = delisted_universe["Reason"].astype(str).apply(
    lambda r: any(kw in r for kw in distress_kw)
)
distress_delisted = delisted_universe[mask_distress]
delisted_tickers = set(distress_delisted["Symbol"])
print(f"  상폐 부실 종목: {len(delisted_tickers)}")

overlap = severe_tickers & delisted_tickers
union_set = severe_tickers | delisted_tickers
print(f"  정밀 severe ∩ 상폐 부실: {len(overlap)} 종목")
print(f"  합집합 (D2 최종 양성 후보): {len(union_set)} 종목")
print(f"  유니버스 대비 비율: {100 * len(union_set) / len(universe):.1f}%")

# 합산 연도별 분포
events_by_year: dict[int, set[str]] = defaultdict(set)
for _, r in distress_delisted.iterrows():
    events_by_year[r["DelistingDate"].year].add(r["Symbol"])
for _, r in strict_window.iterrows():
    events_by_year[r["rcept_date"].year].add(r["ticker"])

print("\n  합산 연도별 양성 종목 분포:")
combined_zero = []
for year in range(2015, 2025):
    n = len(events_by_year[year])
    flag = " <- ZERO" if n == 0 else ""
    print(f"    {year}: {n:3d}{flag}")
    if n == 0:
        combined_zero.append(year)
print(f"\n  → 합산 0 연도: {combined_zero if combined_zero else '없음'}")


# ---- 결과 요약 + 판정 기준 적용 -----------------------------------------

section("결과 요약 + 판정 기준 적용")

pct = 100 * len(union_set) / len(universe)
print(f"  - 정밀 severe 양성 종목: {len(severe_tickers)} (유니버스 비율 "
      f"{100 * len(severe_tickers) / len(universe):.1f}%)")
print(f"  - 양성 0 연도: {zero_years if zero_years else '없음'}")
print(f"  - spot-check top 10 우량주 비중: {blue_count}/10")
print(f"  - 정밀 B1 합집합 상폐 부실 합집합: {len(union_set)} ({pct:.1f}%)")

print("\n  판정 기준 적용:")
verdict = []
if pct >= 80:
    verdict.append(f"양성 비율 {pct:.1f}% — 라벨 오염 위험 (90%대)")
elif pct < 10:
    verdict.append(f"양성 비율 {pct:.1f}% — 너무 적음 (학습 부족)")
else:
    verdict.append(f"양성 비율 {pct:.1f}% — 합리적 범위 (한 자릿수~십몇 %)")

if len(union_set) < 30:
    verdict.append(f"양성 종목 {len(union_set)} < 30 — 학습 부족")
if combined_zero:
    verdict.append(f"양성 0 연도 존재: {combined_zero}")
if blue_count >= 5:
    verdict.append(f"spot-check top 10 중 우량주 {blue_count}개 — 정의 헐거움 신호")

print("\n  진단 결과:")
for v in verdict:
    print(f"    • {v}")

if pct >= 80 or len(union_set) < 30 or blue_count >= 5:
    print("\n  → B1 폐기 → B3 (KOSDAQ 스코프 변경) 정식 논의로 전환 권고")
else:
    print("\n  → B1로 D2 확정 검토 가능")
