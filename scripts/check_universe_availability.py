"""KOSPI200 시점별 구성 + 상장폐지 데이터 가용성 사전 확인.

배경(2026-05-17 사용자 조건):
    "pykrx로 15년치 분기별 KOSPI200 구성 + 상폐 종목 데이터가 실제로
     깨끗하게 확보 가능한지 먼저 확인하고, 제약이 있으면 알려달라."

본 스크립트는 *어떤 결정도 내리지 않는다*. pykrx가 실제로 무엇을
돌려주는지만 확인하고 결과를 출력한다.

실행:
    uv run python scripts/check_universe_availability.py
"""

from __future__ import annotations

import sys
from collections.abc import Iterable

from pykrx import stock

# Windows PowerShell cp949에서도 한글이 깨지지 않도록 utf-8 강제.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

KOSPI200_INDEX = "1028"  # 한국거래소 인덱스 코드 (KOSPI 200)


def section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def probe_kospi200(d: str) -> tuple[bool, int, str]:
    """주어진 영업일(YYYYMMDD)에 KOSPI200 구성 종목 조회 시도."""
    try:
        members = stock.get_index_portfolio_deposit_file(d, KOSPI200_INDEX)
        if members is None:
            return False, 0, "None 반환"
        members_list = list(members)
        if len(members_list) == 0:
            return False, 0, "빈 결과"
        sample = members_list[:3]
        return True, len(members_list), f"예: {sample}"
    except Exception as e:
        return False, 0, f"{type(e).__name__}: {e}"


def probe_ticker_list(d: str, market: str) -> tuple[bool, int, str]:
    """주어진 시점에 시장(KOSPI/KOSDAQ) 상장 종목 조회 시도."""
    try:
        tickers = stock.get_market_ticker_list(d, market=market)
        if tickers is None:
            return False, 0, "None"
        tickers_list = list(tickers)
        return True, len(tickers_list), f"예: {tickers_list[:3]}"
    except Exception as e:
        return False, 0, f"{type(e).__name__}: {e}"


def print_probe(label: str, ok: bool, n: int, detail: str) -> None:
    flag = "OK  " if ok else "FAIL"
    print(f"  [{flag}] {label:14s}  종목수={n:4d}  {detail}")


def discover_api(module, keywords: Iterable[str]) -> list[str]:
    """모듈에서 키워드 포함 attribute를 찾아 정렬해 반환."""
    keys = tuple(k.lower() for k in keywords)
    found = []
    for a in dir(module):
        la = a.lower()
        if any(k in la for k in keys):
            found.append(a)
    return sorted(found)


def main() -> int:
    section("1. 분석 기간(2010-2024)의 주요 시점에서 KOSPI200 구성 조회")
    probe_dates = [
        ("2010-01-04", "20100104"),  # 분석 시작
        ("2012-01-02", "20120102"),
        ("2015-01-02", "20150102"),
        ("2018-01-02", "20180102"),
        ("2021-01-04", "20210104"),
        ("2024-12-30", "20241230"),  # 분석 끝 근처
    ]
    for label, d in probe_dates:
        print_probe(label, *probe_kospi200(d))

    section("2. 분기말 그라뉼래리티 (2015년 4개 분기말)")
    quarters = ["20150331", "20150630", "20150930", "20151230"]
    for d in quarters:
        print_probe(d, *probe_kospi200(d))

    section("3. KOSPI200 데이터의 가능한 가장 이른 시점 탐색")
    early_candidates = ["20000103", "20050103", "20080102", "20100104"]
    for d in early_candidates:
        print_probe(d, *probe_kospi200(d))

    section("4. 상장폐지·종목 리스트 관련 pykrx.stock API 탐색")
    related = discover_api(stock, ["delist", "ticker", "deposit", "change"])
    print("  pykrx.stock 모듈의 관련 attribute:")
    for a in related:
        obj = getattr(stock, a)
        if callable(obj):
            doc = (obj.__doc__ or "").strip().splitlines()
            first = doc[0] if doc else "(no docstring)"
            print(f"    - {a:42s}  {first[:80]}")
        else:
            print(f"    - {a}  (non-callable: {type(obj).__name__})")

    section("5. 시점별 상장 종목 조회 (KOSPI 전 종목 수)")
    # 1차 실패가 KRX 시점 제한 때문인지 호출 형태 때문인지 분리해서 재시도
    for label, d in [
        ("2010-01-04", "20100104"),
        ("2014-05-02", "20140502"),  # KRX 데이터 제공 시작 직후
        ("2020-06-30", "20200630"),  # 분명 데이터 있을 시점
        ("2024-12-30", "20241230"),
    ]:
        print_probe(f"{label} KOSPI", *probe_ticker_list(d, market="KOSPI"))

    section("6. KRX 데이터 제공 시작(2014-05-01) 이후 KOSPI200 구성 재확인")
    for d in ["20140502", "20140630", "20141230", "20200630"]:
        print_probe(d, *probe_kospi200(d))

    section("7. KOSPI200 지수 자체 OHLCV 시계열은 2010년부터 가능한가?")
    try:
        df = stock.get_index_ohlcv_by_ticker("20100104", "20241230", KOSPI200_INDEX)
        if df is not None and len(df) > 0:
            print(f"  OK  KOSPI200 지수 시계열: {len(df):5d}행, "
                  f"기간 {df.index.min().date()} ~ {df.index.max().date()}")
            print(f"  컬럼: {list(df.columns)}")
        else:
            print("  FAIL 빈 결과")
    except Exception as e:
        print(f"  FAIL {type(e).__name__}: {e}")

    section("8. get_index_ticker_list — KOSPI 인덱스들 목록 (KOSPI200 코드 검증용)")
    try:
        idx_tickers = stock.get_index_ticker_list("20241230", market="KOSPI")
        print(f"  KOSPI 인덱스 수: {len(idx_tickers)}")
        for t in list(idx_tickers)[:15]:
            name = stock.get_index_ticker_name(t)
            mark = " <-- KOSPI200" if t == KOSPI200_INDEX else ""
            print(f"    {t}  {name}{mark}")
    except Exception as e:
        print(f"  FAIL {type(e).__name__}: {e}")

    section("9. get_stock_major_changes — 상장 주요 변경사항(상폐 추적 후보)")
    try:
        # 시그니처가 불명확하므로 docstring 확인 후 짧은 호출 시도
        fn = stock.get_stock_major_changes
        print(f"  docstring: {(fn.__doc__ or '').strip().splitlines()[0]}")
        # 시도: 단일 시점 또는 시점 범위
        for args in [("20240101", "20241231"), ("20240101",)]:
            try:
                result = fn(*args)
                print(f"  call args={args} -> type={type(result).__name__}, "
                      f"len={len(result) if hasattr(result, '__len__') else '?'}")
                if hasattr(result, "head"):
                    print(result.head(3).to_string())
                break
            except TypeError as e:
                print(f"  call args={args} TypeError: {e}")
            except Exception as e:
                print(f"  call args={args} {type(e).__name__}: {e}")
    except Exception as e:
        print(f"  FAIL {type(e).__name__}: {e}")

    section("결과 요약")
    print("  위 출력을 보고 다음을 결정한다:")
    print("    a) KOSPI200 시점별 구성을 *어느 시점부터* 가져올 수 있는가")
    print("    b) 분기말 모두 조회 가능한가 (그라뉼래리티)")
    print("    c) 상장폐지 종목을 어떤 API로 추적할 것인가")
    print("    d) 시점별 시장 전체 종목 조회는 어떤 형태인가")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
