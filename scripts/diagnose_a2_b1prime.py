"""A2 (신용등급) + B1' (drawdown 동반 재무 악화) 동시 검증.

사용자 지시: 두 후보를 동일 진단 틀로 산출해 비교표 작성.
판정 기준: (i) 양성 비율 한 자릿수~십몇 % (ii) walk-forward 0년 없음
(iii) spot-check 우량주 미편중.

A2 — 신용등급 하향:
- DART 전 유니버스 전체 공시 fetch (~14분, +321 호출)
- all_disclosures.parquet 캐시
- 신용평가/회사채/등급 키워드 매칭
- 부정적 변동(하향)만 분리 가능 여부 평가 — 불가하면 한계 명시

B1' — 재무 동반 drawdown:
- 객관 정의: peak-to-trough 1년 drawdown ≥ 50% AND 같은 시점에서
  *직전 사업연도 영업이익 양수 → 다음 사업연도 영업이익 음수* 전환
- 50% 임계: Sharpe·Sortino 류 학술 표준값 인용 가능. 단 완벽 정당화 X.
- 데이터: KRX OHLCV 캐시 (321 종목 ohlcv.parquet) + DART finstate 캐시
"""

from __future__ import annotations

import contextlib
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv

with contextlib.suppress(AttributeError, OSError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DISCLOSURES_CACHE = (
    PROJECT_ROOT / "data" / "raw" / "dart_corrections" / "all_disclosures.parquet"
)

from frr.data.universe_loader import KOSPI200QuarterlyLoader  # noqa: E402


def section(t: str) -> None:
    print()
    print("=" * 72)
    print(t)
    print("=" * 72)


loader = KOSPI200QuarterlyLoader.from_default(project_root=PROJECT_ROOT)
universe: set[str] = set()
for q in loader.available_quarters():
    universe.update(loader.tickers(q))
universe_sorted = sorted(universe)
print(f"유니버스: {len(universe)} 종목")


# ============================================================
# A2 — 신용등급 데이터 자동 확보 + 양성 진단
# ============================================================

section("A2 — DART 전체 공시 fetch (캐시 또는 신규)")

if DISCLOSURES_CACHE.exists():
    print(f"  캐시 hit: {DISCLOSURES_CACHE}")
    df_all = pd.read_parquet(DISCLOSURES_CACHE)
    print(f"  로딩: {len(df_all)} 건")
else:
    print(f"  캐시 miss → DART 호출 ({len(universe)} 종목, ~14분)")
    import opendartreader

    odr = opendartreader.OpenDartReader(os.environ["DART_API_KEY"])
    rows: list[dict] = []
    fail_count = 0
    start_ts = time.time()
    for i, ticker in enumerate(universe_sorted, 1):
        try:
            df = odr.list(ticker, "20150101", "20241231")
            if df is None or len(df) == 0:
                continue
            for _, row in df.iterrows():
                rows.append(
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
            print(f"  [{i}/{len(universe_sorted)}] 누적 {len(rows)} ({elapsed:.1f}s)")
    df_all = pd.DataFrame(rows)
    DISCLOSURES_CACHE.parent.mkdir(parents=True, exist_ok=True)
    df_all.to_parquet(DISCLOSURES_CACHE)
    print(f"  캐시 저장: {DISCLOSURES_CACHE} ({len(df_all)} 건, 실패 {fail_count})")


section("A2 — 신용평가 키워드 매칭")

credit_kw = ["신용평가", "신용등급", "회사채", "NICE신용", "한기평", "한신평", "KIS신용"]
mask_credit = df_all["report_nm"].astype(str).apply(
    lambda s: any(kw in s for kw in credit_kw)
)
credit_events = df_all[mask_credit].copy()
print(f"  신용평가 키워드 매칭: {len(credit_events)} 건")
print(f"  고유 종목: {credit_events['ticker'].nunique()} / 유니버스 {len(universe)}")

if len(credit_events) > 0:
    print("\n  report_nm 패턴 top 15:")
    for nm, n in credit_events["report_nm"].value_counts().head(15).items():
        print(f"    {n:4d}  {nm}")
    # 부정적 변동 키워드 분리 시도
    neg_kw = [
        "하향", "강등", "하락", "Downgrade", "Negative",
        "조정(하향)", "(하향)", "BBB", "BB", "B+", "CCC",
    ]
    mask_neg = credit_events["report_nm"].astype(str).apply(
        lambda s: any(kw in s for kw in neg_kw)
    )
    n_neg = int(mask_neg.sum())
    print(f"\n  *부정적 변동* 키워드 매칭: {n_neg} 건")
    if n_neg > 0:
        print("  부정적 매칭 spot-check (상위 10):")
        for nm in credit_events[mask_neg]["report_nm"].value_counts().head(10).index:
            print(f"    {nm}")
else:
    print("\n  → 신용평가 매칭 0건. 카테고리 분포로 DART list() 응답 종류 진단.")
    import re

    def _cat(s: str) -> str:
        m = re.match(r"\[([^\]]+)\]", str(s))
        return m.group(1) if m else "(no bracket)"

    cats = df_all["report_nm"].apply(_cat)
    print("\n  DART list() 응답 [카테고리] 분포 top 20:")
    for c, n in cats.value_counts().head(20).items():
        print(f"    {n:6d}  [{c}]")
    print("\n  → DART list() 응답에 *신용평가 공시* 카테고리가 *없는지* 확인.")

section("A2 — 양성 분포 (전체 신용평가 이벤트 기준, 하향 분리 불가시 한계 명시)")

credit_events["rcept_date"] = pd.to_datetime(
    credit_events["rcept_dt"], format="%Y%m%d", errors="coerce"
)
credit_events = credit_events.dropna(subset=["rcept_date"])
mask_window = (credit_events["rcept_date"] >= pd.Timestamp("2015-01-01")) & (
    credit_events["rcept_date"] <= pd.Timestamp("2024-12-31")
)
credit_window = credit_events[mask_window]

credit_tickers = set(credit_window["ticker"])
a_pct = 100 * len(credit_tickers) / len(universe)
print(f"  유니버스 양성 종목 (2015-2024): {len(credit_tickers)} ({a_pct:.1f}%)")

print("\n  연도별 분포:")
years = credit_window["rcept_date"].dt.year
year_sets: dict[int, set[str]] = defaultdict(set)
for _, r in credit_window.iterrows():
    year_sets[r["rcept_date"].year].add(r["ticker"])
zero_a = []
for year in range(2015, 2025):
    n = len(year_sets[year])
    flag = " <- ZERO" if n == 0 else ""
    print(f"    {year}: {n:3d}{flag}")
    if n == 0:
        zero_a.append(year)

# spot-check
top_a = credit_window["ticker"].value_counts().head(10)
KNOWN_BLUE_CHIPS = {
    "005930", "000660", "005380", "066570", "035420", "035720", "051910",
    "005490", "207940", "006400", "068270", "105560", "055550", "086790",
    "017670", "030200",
}
blue_a = 0
print("\n  spot-check top 10:")
for ticker, n in top_a.items():
    blue = " ★" if ticker in KNOWN_BLUE_CHIPS else ""
    if ticker in KNOWN_BLUE_CHIPS:
        blue_a += 1
    print(f"    {ticker}: {n} 건{blue}")
print(f"  → top 10 중 우량주: {blue_a}")


# ============================================================
# B1' — peak-to-trough drawdown + 영업이익 음수 전환
# ============================================================

section("B1' — drawdown 50% + 영업이익 음수 전환 진단")

# KRX OHLCV 캐시
krx_cache_dir = PROJECT_ROOT / "data" / "raw" / "krx" / "ohlcv"
dart_cache_dir = PROJECT_ROOT / "data" / "raw" / "dart"


def compute_max_drawdown_252d(close: pd.Series) -> pd.Series:
    """롤링 252영업일(1년) peak-to-trough drawdown 비율 (음수)."""
    rolling_peak = close.rolling(window=252, min_periods=60).max()
    dd = (close - rolling_peak) / rolling_peak
    return dd


def get_op_income(ticker_dir: Path, year: int) -> float | None:
    """해당 종목·연도 사업보고서의 영업이익 (없으면 None)."""
    parquet = ticker_dir / f"{year}_FY.parquet"
    meta = ticker_dir / f"{year}_FY.meta.yaml"
    if not parquet.exists() or not meta.exists():
        return None
    try:
        m = yaml.safe_load(meta.read_text(encoding="utf-8"))
        if m.get("status") != "ok":
            return None
        df = pd.read_parquet(parquet)
    except Exception:
        return None
    mask = df["account_nm"].astype(str).str.contains("영업이익", na=False)
    if not mask.any():
        return None
    val_str = str(df[mask].iloc[0].get("thstrm_amount", ""))
    val_str = val_str.replace(",", "").replace(" ", "")
    if val_str in ("", "nan", "None", "-"):
        return None
    try:
        return float(val_str)
    except ValueError:
        return None


events_b: list[dict] = []  # ticker, year, dd_date, dd_value, op_prev, op_curr
checked = 0

for ticker in universe_sorted:
    ohlcv_path = krx_cache_dir / f"{ticker}.parquet"
    if not ohlcv_path.exists():
        continue
    ticker_dir = dart_cache_dir / ticker
    if not ticker_dir.exists():
        continue
    try:
        ohlcv = pd.read_parquet(ohlcv_path)
    except Exception:
        continue
    if len(ohlcv) < 252:
        continue
    close = ohlcv["종가"]
    dd = compute_max_drawdown_252d(close)
    # 50% 이상 drawdown 사건의 *최초 시점*만 (한 종목 다회 사건은 첫 1회)
    mask_dd = dd <= -0.50
    if not mask_dd.any():
        continue
    first_dd_idx = mask_dd.idxmax()  # first True
    dd_year = first_dd_idx.year
    # 영업이익 전환: 직전 사업연도 양수 → 현재 사업연도 음수
    op_prev = get_op_income(ticker_dir, dd_year - 1)
    op_curr = get_op_income(ticker_dir, dd_year)
    if op_prev is None or op_curr is None:
        continue
    if op_prev > 0 and op_curr < 0:
        events_b.append(
            {
                "ticker": ticker,
                "dd_date": first_dd_idx.date(),
                "dd_value": float(dd.loc[first_dd_idx]),
                "op_prev": op_prev,
                "op_curr": op_curr,
            }
        )
    checked += 1

print(f"  검사한 종목: {checked} / 유니버스 {len(universe)}")
print(f"  B1' 양성 (50%+ drawdown + 영업이익 음수 전환): {len(events_b)} 건")

if events_b:
    df_b = pd.DataFrame(events_b)
    df_b["year"] = pd.to_datetime(df_b["dd_date"]).dt.year
    b_tickers = set(df_b["ticker"])
    print(f"  고유 종목: {len(b_tickers)} ({100 * len(b_tickers) / len(universe):.1f}%)")

    print("\n  연도별 분포:")
    year_b_sets: dict[int, set[str]] = defaultdict(set)
    for _, r in df_b.iterrows():
        year_b_sets[r["year"]].add(r["ticker"])
    zero_b = []
    for year in range(2015, 2025):
        n = len(year_b_sets[year])
        flag = " <- ZERO" if n == 0 else ""
        print(f"    {year}: {n:3d}{flag}")
        if n == 0:
            zero_b.append(year)

    print("\n  spot-check 상위 10 (drawdown 큰 종목):")
    blue_b = 0
    for _, r in df_b.nsmallest(10, "dd_value").iterrows():
        blue = " ★" if r["ticker"] in KNOWN_BLUE_CHIPS else ""
        if r["ticker"] in KNOWN_BLUE_CHIPS:
            blue_b += 1
        line = (
            f"    {r['ticker']}: dd={r['dd_value']:.2%}, {r['dd_date']}, "
            f"op {r['op_prev']:.0f}->{r['op_curr']:.0f}{blue}"
        )
        print(line)
    print(f"  → top 10 중 우량주: {blue_b}")
else:
    zero_b = list(range(2015, 2025))
    blue_b = 0


# ============================================================
# 비교표 + 판정
# ============================================================

section("최종 비교표")

b_pct = (100 * len(b_tickers) / len(universe)) if events_b else 0
n_a = len(credit_tickers)
n_b = len(b_tickers) if events_b else 0
za = str(zero_a if zero_a else "없음")[:21]
zb = str(zero_b if zero_b else "없음")[:21]

print()
print(f"  {'항목':<28} {'A2 (신용평가)':<22} {'B1 prime (dd+op)':<22}")
print(f"  {'-' * 28} {'-' * 22} {'-' * 22}")
print(f"  {'양성 종목 수':<28} {n_a:<22} {n_b:<22}")
print(f"  {'유니버스 대비 비율':<28} {f'{a_pct:.1f}%':<22} {f'{b_pct:.1f}%':<22}")
print(f"  {'walk-forward 0년':<28} {za:<22} {zb:<22}")
print(f"  {'spot-check 우량주 top10':<28} {blue_a:<22} {blue_b:<22}")
print()

print("  판정 기준 적용:")
for label, pct, n, zeros, blue in [
    ("A2", a_pct, len(credit_tickers), zero_a, blue_a),
    ("B1'", b_pct, len(b_tickers) if events_b else 0, zero_b, blue_b),
]:
    flags = []
    if pct >= 80:
        flags.append(f"비율 {pct:.1f}% (오염 위험)")
    elif pct < 5:
        flags.append(f"비율 {pct:.1f}% (너무 적음)")
    if n < 30:
        flags.append(f"종목 {n}<30 (학습 부족)")
    if zeros:
        flags.append(f"0년 {zeros}")
    if blue >= 5:
        flags.append(f"우량주 {blue}/10")
    status = "OK" if not flags else " | ".join(flags)
    print(f"    {label}: {status}")


# ============================================================
# alpha — 상폐 부실(8) 합집합 B1'(19) 합집합 walk-forward
# ============================================================

section("alpha — 상폐 부실 합집합 B1' (drawdown+영업악화) 합집합 진단")

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

if events_b:
    df_b_local = pd.DataFrame(events_b)
    b_local_tickers = set(df_b_local["ticker"])
else:
    df_b_local = pd.DataFrame()
    b_local_tickers = set()
print(f"  B1' 양성 종목: {len(b_local_tickers)}")

overlap_a = delisted_tickers & b_local_tickers
union_a = delisted_tickers | b_local_tickers
print(f"  중복 (상폐 ∩ B1'): {len(overlap_a)}")
print(f"  합집합 (D2 = 상폐 부실 합집합 B1'): {len(union_a)}")
print(f"  유니버스 비율: {100 * len(union_a) / len(universe):.1f}%")

# walk-forward (이벤트 발생 *연도* — 상폐는 DelistingDate, B1'은 dd_date)
year_union: dict[int, set[str]] = defaultdict(set)
for _, r in distress_delisted.iterrows():
    year_union[r["DelistingDate"].year].add(r["Symbol"])
if events_b:
    for _, r in df_b_local.iterrows():
        y = pd.to_datetime(r["dd_date"]).year
        year_union[y].add(r["ticker"])

zero_union = []
print("\n  연도별 양성 종목 분포 (합집합):")
for year in range(2015, 2025):
    n = len(year_union[year])
    flag = " <- ZERO" if n == 0 else ""
    print(f"    {year}: {n:3d}{flag}")
    if n == 0:
        zero_union.append(year)

# spot-check — 합집합 종목 중 *상폐와 B1' 모두 해당* (이중 신호) 우선
print("\n  spot-check — 이중 신호 종목 (상폐 AND B1'):")
for ticker in sorted(overlap_a):
    blue = " ★" if ticker in KNOWN_BLUE_CHIPS else ""
    print(f"    {ticker}{blue}")

union_blue = sum(1 for t in union_a if t in KNOWN_BLUE_CHIPS)
print(f"\n  합집합 전체 중 우량주: {union_blue}")

# 판정
section("alpha 판정")
pct_u = 100 * len(union_a) / len(universe)
flags_u = []
if pct_u >= 80:
    flags_u.append(f"비율 {pct_u:.1f}% (오염 위험)")
elif pct_u < 5:
    flags_u.append(f"비율 {pct_u:.1f}% (너무 적음)")
if len(union_a) < 30:
    flags_u.append(f"종목 {len(union_a)}<30 (학습 부족)")
if zero_union:
    flags_u.append(f"0년 {zero_union}")
if union_blue >= 5:
    flags_u.append(f"우량주 {union_blue}")
status_u = "PASS (모든 기준 통과)" if not flags_u else " | ".join(flags_u)
print(f"  alpha (상폐 부실 합집합 B1'): {status_u}")
