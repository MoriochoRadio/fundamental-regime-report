"""D2 양성 27 종목 코드 캡처 — 진단 스크립트 로직 byte-for-byte 재사용.

본 스크립트는 D2 라벨 확정의 근거 증거 자료인 `diagnose_a2_b1prime.py` 의
양성 산출 로직을 *byte-for-byte 동일하게* 사용해 27 종목 코드를 캡처한다.
양성 판정 코드를 한 줄도 재구현하지 않고, 진단 스크립트를 *모듈로 import*
한 뒤 그 결과 변수(`diag.union_a` 등)를 그대로 추출한다.

설계 원칙:
- 진단 스크립트 원형 보존 (한 줄도 변경 없음 — D2 근거 증거의 무결성).
- 로직 재구현 0 — 진단의 module-level 결과 변수만 추출.
- 5 assertion 으로 silently wrong 차단 (A 8 / B 19 / Union 27 / 중복 0 /
  연도 분포 일치).
- 실패 시 *D2 흔들림 vs capture 집계 버그* 자동 구분 출력.

안전 가드 (W1/W2):
- 진단 스크립트는 캐시 부재 시 두 곳에서 디스크에 쓸 수 있다:
    W1: diagnose_a2_b1prime.py L98-99 (DISCLOSURES_CACHE write)
    W2: src/frr/data/fdr.py L101-102 (FDR delisting cache write)
- 본 스크립트는 import *전에* 필수 캐시 파일/디렉토리 존재를 검증하고,
  하나라도 부재 시 즉시 abort 한다 → import 자체가 시작 안 되므로
  write path 가 물리적으로 도달 불가능.

연관 자료: PROGRESS §5.5.7 (D2 최종 확정) + §5.5.8 (A1 진단).
"""

from __future__ import annotations

import contextlib
import io
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

from frr.data.fdr import FDRDataSource

# Windows cp949 콘솔에서도 한국어/유니코드 출력 가능하게 (진단 스크립트와 동일 패턴)
with contextlib.suppress(AttributeError, OSError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# === W1/W2 사전 가드 — 필수 캐시 부재 시 abort, import 안 함 =================
REQUIRED_FILES = [
    # W1 guard: 진단 스크립트 L98-99 의 DISCLOSURES_CACHE write 차단
    PROJECT_ROOT / "data" / "raw" / "dart_corrections" / "all_disclosures.parquet",
    # W2 guard: fdr.py L101-102 의 stocklisting_delisting cache write 차단
    PROJECT_ROOT / "data" / "raw" / "fdr" / "stocklisting_delisting.parquet",
]
REQUIRED_DIRS = [
    # B1' 의 OHLCV 읽기 (캐시 부재 시 진단이 skip 만 하지만, 일관성 위해 가드)
    PROJECT_ROOT / "data" / "raw" / "krx" / "ohlcv",
    # B1' 의 영업이익 lookup (DART finstate per-ticker)
    PROJECT_ROOT / "data" / "raw" / "dart",
]
missing = [p for p in REQUIRED_FILES if not p.is_file()] + [
    p for p in REQUIRED_DIRS if not p.is_dir()
]
if missing:
    print(
        "ERROR — 진단 캐시 부재. import 시 W1/W2 write path 활성 위험으로 abort.",
        file=sys.stderr,
    )
    for p in missing:
        print(f"  MISSING: {p}", file=sys.stderr)
    print(
        "\n해결: data/raw/ 캐시 복원 (메인 워크트리 복사 또는 단계 1 재수집).",
        file=sys.stderr,
    )
    sys.exit(2)

# === 진단 스크립트 import — 로직 재사용 (재구현 0) ============================
# scripts/ 디렉토리를 import path 에 추가 (보조 스크립트 직접 실행 시 필요).
sys.path.insert(0, str(Path(__file__).parent))

# import 시 module-level 코드 실행됨 (캐시 hit → DART API 0, 디스크 read 만).
# print 출력은 redirect 로 억제 (~30-60초, side-effect 출력 노이즈 제거).
with contextlib.redirect_stdout(io.StringIO()):
    import diagnose_a2_b1prime as diag

# === 양성 변수 추출 (재구현 0 — 진단 결과 그대로) =============================
a_tickers: list[str] = sorted(diag.delisted_tickers)  # 상폐 부실 (Signal A)
b_tickers: list[str] = sorted(diag.b_local_tickers)  # drawdown+op (Signal B)
union_tickers: list[str] = sorted(diag.union_a)  # A 합집합 B (D2 양성)
overlap: list[str] = sorted(diag.overlap_a)  # A 교집합 B

# === assertion — silently wrong 차단 =========================================
# 2026-05-19 정정 (PROGRESS §5.5.9): A 8 → 1 (합병 7 노이즈 제거).
# Union 27 → 20. B 19 변동 없음 (distress filter 변경이 A 에만 영향).
assertion_errors: list[str] = []
if len(a_tickers) != 1:
    assertion_errors.append(
        f"A 1 검증 실패: 실제 {len(a_tickers)} (기대: 포스코플랜텍 051310 단일)"
    )
if len(b_tickers) != 19:
    assertion_errors.append(f"B 19 검증 실패: 실제 {len(b_tickers)}")
if len(union_tickers) != 20:
    assertion_errors.append(f"Union 20 검증 실패: 실제 {len(union_tickers)}")
if len(overlap) != 0:
    assertion_errors.append(f"중복 0 검증 실패: 실제 {overlap}")
if set(union_tickers) != set(a_tickers) | set(b_tickers):
    assertion_errors.append("Union 무결성 실패: union != a 합집합 b")
# 포스코플랜텍 (051310) ∉ B 19 명시 재확인 — 사용자 step 3 추가 조건
if "051310" in set(b_tickers):
    assertion_errors.append("포스코플랜텍 051310 ∈ B 19 — 중복 0 가정 깨짐!")
# B 19 정정 전과 1:1 동일 검증 (정정 전 리스트 hardcode)
B_PRE_FIX = frozenset(
    {
        "003920",
        "005070",
        "007810",
        "008060",
        "010690",
        "010950",
        "019680",
        "029530",
        "033240",
        "034730",
        "035250",
        "047810",
        "066970",
        "073240",
        "096770",
        "267250",
        "267260",
        "361610",
        "450080",
    }
)
if frozenset(b_tickers) != B_PRE_FIX:
    in_pre = B_PRE_FIX - frozenset(b_tickers)
    in_curr = frozenset(b_tickers) - B_PRE_FIX
    assertion_errors.append(
        f"B 19 정정 전과 차이 발견: pre-only={sorted(in_pre)}, current-only={sorted(in_curr)}"
    )

# === 연도 분포 집계 — 진단 스크립트 L411-417 와 동일 패턴 =====================
year_union: dict[int, set[str]] = defaultdict(set)
for _, row in diag.distress_delisted.iterrows():
    year_union[row["DelistingDate"].year].add(row["Symbol"])
if diag.events_b:
    df_b_local = pd.DataFrame(diag.events_b)
    for _, row in df_b_local.iterrows():
        year_union[pd.to_datetime(row["dd_date"]).year].add(row["ticker"])

# 2026-05-19 정정 (PROGRESS §5.5.9 — P1 적용 후 확정 분포):
# A 합병 7건 제거로 2015 양성 3→0 (삼성물산·SK·현대하이스코 합병), 2017 5→3,
# 2018 4→3, 2022 2→1. 0년: {2021,2023} → {2015,2021,2023} (3개).
EXPECTED_YEAR_DIST: dict[int, int] = {
    2015: 0,
    2016: 1,
    2017: 3,
    2018: 3,
    2019: 2,
    2020: 9,
    2021: 0,
    2022: 1,
    2023: 0,
    2024: 1,
}
year_mismatches: list[tuple[int, int, int]] = []
for year, expected in EXPECTED_YEAR_DIST.items():
    actual = len(year_union[year])
    if actual != expected:
        year_mismatches.append((year, expected, actual))

# === 실패 시 D2 흔들림 vs capture 집계 버그 자동 구분 진단 =====================
if assertion_errors or year_mismatches:
    print("=" * 64, file=sys.stderr)
    print("ERROR — capture 검증 실패. 원인 자동 진단:", file=sys.stderr)
    print("=" * 64, file=sys.stderr)
    for e in assertion_errors:
        print(f"  ASSERT: {e}", file=sys.stderr)
    if year_mismatches:
        print(f"  YEAR_DIST mismatches: {year_mismatches}", file=sys.stderr)

    print("\n진단 결과 원본 변수 카운트 (D2 흔들림 판정용):", file=sys.stderr)
    print(f"  diag.union_a:           {len(diag.union_a)} (기대 20, P1 정정)", file=sys.stderr)
    print(
        f"  diag.delisted_tickers:  {len(diag.delisted_tickers)} (기대 1, P1 정정)", file=sys.stderr
    )
    print(f"  diag.b_local_tickers:   {len(diag.b_local_tickers)} (기대 19)", file=sys.stderr)
    print(f"  diag.overlap_a:         {len(diag.overlap_a)} (기대 0)", file=sys.stderr)

    diag_intact = (
        len(diag.union_a) == 20
        and len(diag.delisted_tickers) == 1
        and len(diag.b_local_tickers) == 19
        and len(diag.overlap_a) == 0
    )
    print(file=sys.stderr)
    if diag_intact:
        print(
            "  → 진단 결과는 정상. 실패 원인 = **capture 의 집계 방식 버그** "
            "(D2 흔들림 아님). capture 스크립트 수정 후 재실행.",
            file=sys.stderr,
        )
    else:
        print(
            "  → 진단 결과 자체 흔들림 = **D2 위협**. 즉시 멈추고 캐시·"
            "진단 스크립트 무결성 점검 필요.",
            file=sys.stderr,
        )
    sys.exit(3)

# === ticker -> 회사명 lookup (FDR listing + delisting) ========================
# A 의 회사명은 diag.distress_delisted DataFrame 에서, B 의 회사명은 FDR listing 에서.
ticker_name: dict[str, str] = {}
# A 측: distress_delisted DataFrame 그대로
for _, _row in diag.distress_delisted.iterrows():
    sym = str(_row.get("Symbol", "")).strip()
    nm = str(_row.get("Name", "")).strip()
    if sym and nm:
        ticker_name[sym] = nm
# B 측 + 합집합: FDR listing 에서 lookup. FDR listing 의 컬럼은 'Code'
# (delisting 은 'Symbol'). 2026-05-19 발견: 두 데이터 구조가 다름.
_fdr = FDRDataSource(project_root=PROJECT_ROOT)
_listing = _fdr.listing()
for _, _row in _listing.iterrows():
    sym = str(_row.get("Code", "")).strip()
    nm = str(_row.get("Name", "")).strip()
    if sym and sym not in ticker_name:
        ticker_name[sym] = nm
# delisting 도 lookup (B 의 일부 종목이 상폐됐을 경우)
_delisting = _fdr.delisting()
for _, _row in _delisting.iterrows():
    sym = str(_row.get("Symbol", "")).strip()
    nm = str(_row.get("Name", "")).strip()
    if sym and sym not in ticker_name:
        ticker_name[sym] = nm


def _name(t: str) -> str:
    return ticker_name.get(t, "?")


# === 정상 출력 =================================================================
print("=" * 72)
print("D2 양성 20 종목 캡처 — diagnose_a2_b1prime.py 로직 byte-for-byte 재사용")
print("(2026-05-19 P1 정정 후: A 8→1 합병 노이즈 제거, B 19 변동 없음, alpha 27→20)")
print("=" * 72)

print(f"\nA (상폐 부실, {len(a_tickers)} 종목) — source: 'A':")
for t in a_tickers:
    print(f"  {t}  {_name(t)}")

print(f"\nB (drawdown+op, {len(b_tickers)} 종목) — source: 'B':")
for t in b_tickers:
    print(f"  {t}  {_name(t)}")

print(f"\nA 합집합 B (D2 양성 전체, {len(union_tickers)} 종목):")
for t in union_tickers:
    src = "A" if t in set(a_tickers) else "B"
    print(f"  {t}  {_name(t):<24} [{src}]")

print(f"\nA 교집합 B (중복): {overlap}")
print(f"포스코플랜텍 (051310) ∈ B 19 ? {'051310' in set(b_tickers)} (기대: False)")

# B 19 vs 정정 전 1:1 대조
B_PRE_FIX_check = frozenset(
    {
        "003920",
        "005070",
        "007810",
        "008060",
        "010690",
        "010950",
        "019680",
        "029530",
        "033240",
        "034730",
        "035250",
        "047810",
        "066970",
        "073240",
        "096770",
        "267250",
        "267260",
        "361610",
        "450080",
    }
)
b_current = frozenset(b_tickers)
print(f"\nB 19 정정 전과 1:1 대조: {b_current == B_PRE_FIX_check}")
if b_current == B_PRE_FIX_check:
    print("  ✓ B 19 = 정정 전과 정확히 동일 (한 종목도 차이 없음)")
else:
    print(f"  ✗ pre-only: {sorted(B_PRE_FIX_check - b_current)}")
    print(f"  ✗ current-only: {sorted(b_current - B_PRE_FIX_check)}")

print("\n연도별 분포 (이벤트 발생 연도 — A: DelistingDate.year, B: dd_date.year):")
total = 0
for year in range(2015, 2025):
    n = len(year_union[year])
    flag = " <- ZERO" if n == 0 else ""
    print(f"  {year}: {n}{flag}")
    total += n
print(f"  총합: {total}")

print("\n✓ assertion 통과: A=1 / B=19 / Union=20 / 중복=0 / Union 무결성 / 포스코 ∉ B / B 1:1 동일")
print("✓ 연도 분포 §5.5.9 확정값과 일치 (0년 = {2015, 2021, 2023})")

# === EXPECTED_POSITIVES frozenset 텍스트 (test_labels.py 박제용) =============
print()
print("=" * 64)
print("=== test_labels.py 박제용 (EXPECTED_POSITIVES) ===")
print("=" * 64)
print("EXPECTED_POSITIVES_A: frozenset[str] = frozenset({")
for t in a_tickers:
    print(f'    "{t}",  # 상폐 부실')
print("})")
print("EXPECTED_POSITIVES_B: frozenset[str] = frozenset({")
for t in b_tickers:
    print(f'    "{t}",  # drawdown+op')
print("})")
print("# A 교집합 B = 공집합 (실데이터 검증), 합집합 27")
print("EXPECTED_POSITIVES: frozenset[str] = EXPECTED_POSITIVES_A | EXPECTED_POSITIVES_B")
