"""pykrx 기본 호출의 동작 여부와 대안 라이브러리(FinanceDataReader) 후보 진단.

배경:
    `check_universe_availability.py` 결과 pykrx의 인덱스/티커 API들이
    빈 결과 또는 내부 KeyError를 냄. pykrx 자체가 KRX 웹 변경에
    따라가지 못하는지, 아니면 특정 API만 망가졌는지 확인이 필요.

실행: uv run python scripts/check_pykrx_health.py
"""
from __future__ import annotations

import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


def section(t: str) -> None:
    print()
    print("=" * 72)
    print(t)
    print("=" * 72)


# --- A. pykrx의 단일 종목 OHLCV (가장 기본 호출) -----------------
section("A. pykrx: 삼성전자(005930) 최근 OHLCV 조회")
from pykrx import stock

try:
    df = stock.get_market_ohlcv("20250101", "20250110", "005930")
    print(f"  타입: {type(df).__name__}, shape: {getattr(df, 'shape', '?')}")
    if hasattr(df, "head"):
        print(df.head().to_string())
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

# --- B. pykrx의 시점별 시가총액 by ticker -------------------------
section("B. pykrx: 2024-12-30 시가총액 by ticker")
try:
    df = stock.get_market_cap_by_ticker("20241230")
    print(f"  타입: {type(df).__name__}, shape: {getattr(df, 'shape', '?')}")
    if hasattr(df, "head"):
        print(df.head().to_string())
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

# --- C. pykrx 종목 이름 조회 (가장 단순) -------------------------
section("C. pykrx: 005930 종목 이름")
try:
    name = stock.get_market_ticker_name("005930")
    print(f"  005930 -> {name}")
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

# --- D. FinanceDataReader 후보 (미설치 가능) ---------------------
section("D. FinanceDataReader (FDR) 후보 — 설치 여부 + 단순 호출")
try:
    import FinanceDataReader as fdr  # type: ignore

    print(f"  FDR 설치됨, 버전: {getattr(fdr, '__version__', '?')}")
    df = fdr.DataReader("005930", "2024-12-01", "2024-12-31")
    print(f"  삼성전자 12월 OHLCV shape: {df.shape}")
    if hasattr(df, "tail"):
        print(df.tail(3).to_string())
    # KOSPI 종목 리스트
    krx = fdr.StockListing("KRX")
    print(f"\n  fdr.StockListing('KRX') shape: {krx.shape}")
    print(f"  컬럼: {list(krx.columns)}")
    print(krx.head(3).to_string())
except ImportError:
    print("  FDR 미설치 — pyproject.toml에 finance-datareader 추가 후 uv sync 필요")
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

section("진단 끝")
print("  - pykrx의 기본 호출이 동작하는지 (A/B/C로 판정)")
print("  - FDR가 대안이 될 수 있는지 (D로 판정)")
