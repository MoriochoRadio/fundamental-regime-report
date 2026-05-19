"""A1 1차 진단 — 신용등급 데이터 자동 확보 가능성 검증.

사용자 지시 (2026-05-18):
- B1.2 (정정 본문 파싱) 을 1인 범위 초과로 기각한 것과 동일 잣대.
- A 의 "데이터 부분 자동" 이 같은 함정인지 정직 평가.

1차 진단 (추가 DART 호출 0):
- 기존 corrections.parquet (17,723건) 에서 신용평가 키워드 매칭
- 그 결과로 정정공시에 신용평가 변동이 *얼마나 자주* 들어가는지 확인
- 거의 없으면 → 비정정 공시까지 별도 fetch 필요 (사용자 동의 받음)

키워드: 신용평가, 신용등급, NICE, KIS, 한기평, 한신평, 회사채
"""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path

import pandas as pd

with contextlib.suppress(AttributeError, OSError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CORRECTIONS_CACHE = PROJECT_ROOT / "data" / "raw" / "dart_corrections" / "all_corrections.parquet"


def section(t: str) -> None:
    print()
    print("=" * 72)
    print(t)
    print("=" * 72)


section("1차 진단 — corrections.parquet 에서 신용평가 키워드 매칭")

if not CORRECTIONS_CACHE.exists():
    print(f"  FAIL: 캐시 없음 — {CORRECTIONS_CACHE}")
    sys.exit(1)

df_corr = pd.read_parquet(CORRECTIONS_CACHE)
print(f"  corrections 캐시: {len(df_corr)} 건")

# 신용평가 관련 키워드
keywords = ["신용평가", "신용등급", "NICE", "KIS", "한기평", "한신평", "회사채"]
print(f"\n  검색 키워드: {keywords}")

mask = df_corr["report_nm"].astype(str).apply(lambda s: any(kw in s for kw in keywords))
credit_in_corrections = df_corr[mask]
print(
    f"\n  매칭: {len(credit_in_corrections)} 건 / {len(df_corr)} 전체 "
    f"({100 * len(credit_in_corrections) / len(df_corr):.2f}%)"
)

if len(credit_in_corrections) > 0:
    print("\n  매칭된 report_nm top 20:")
    for nm, n in credit_in_corrections["report_nm"].value_counts().head(20).items():
        print(f"    {n:4d}  {nm}")
    print(f"\n  매칭된 고유 종목: {credit_in_corrections['ticker'].nunique()} / 유니버스 321")

section("결과 해석")

if len(credit_in_corrections) < 50:
    print(f"  → corrections 만으로는 신용평가 변동 데이터 부족 ({len(credit_in_corrections)} 건).")
    print("  → 비정정 공시까지 별도 fetch 필요 (DART 호출 +321 ~15분).")
    print("  → 또는 다른 데이터 출처 (평가사 사이트 직접) 검토.")
else:
    print(f"  → corrections 안에 신용 관련 {len(credit_in_corrections)} 건 — 추가 진단 가치 있음.")
    print("  → 다음: 부정적 변동(하향)만 분리 가능한지 report_nm 패턴 분석.")
