"""Baseline 재무비율 빌더 (단계 2 step 3, PROGRESS §5.5.14).

D2 라벨 (재무 충격 위험) 의 *원인 (BS 건전성)* + *결과 직전 신호 (IS 수익성)*
를 동시 포착하는 4 baseline 비율:

| ratio | 분자 | 분모 | 분류 |
|---|---|---|---|
| debt_ratio | 부채총계 | 자본총계 | BS — 재무 건전성 전통 지표 |
| current_ratio | 유동자산 | 유동부채 | BS — 단기 유동성 |
| op_margin | 영업이익 | 매출액 | IS — *비율* (영업이익 자체는 라벨 변수, 비율은 허용) |
| roa | 당기순이익 | 자산총계 | IS×BS 결합 — 원인 × 결과 |

★ 격리 원칙 (CLAUDE.md §5):
- 영업이익 *그 자체* 는 D2 B 신호 정의 변수 → 피처로 *제외*.
- 영업이익률 (영업이익/매출액) 은 *비율* 이라 정보 함량 다름 → 허용.
- 유니버스 변수 (KOSPI200QuarterlyLoader 심볼 등) import 금지 (`TYPE_CHECKING`
  으로만 참조 — 런타임 import 0).
- 상폐 메타 (DelistingDate·Reason 등) 접근 금지.

★ Lookahead 차단 (PROGRESS §5.5.14 (b-2)):
- 모든 외부 데이터 호출은 `as_of` 인자를 통해서만 시점 결정.
- DARTReporter 호출은 `latest_available(t)` / `available_at(t)` 만 사용
  (AST 화이트리스트, tests/test_isolation.py iii 활성화).
- 런타임 mock contract (tests/test_features_lookahead.py): mock 이 받은
  모든 시점 인자 ≤ as_of.

★ 의존성 주입 (PROGRESS §5.5.14 (b-1) strict default):
- reporter / universe_loader / krx_ohlcv_cache_dir 모두 Optional 이나
  None 시 ValueError. *정직성 — 호출자가 명시적 주입*.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from frr.data.dart import DARTReporter
    from frr.data.universe_loader import KOSPI200QuarterlyLoader


# === ratio 정의 (분자·분모 account_nm) ======================================
RATIO_SPEC: dict[str, tuple[str, str]] = {
    "debt_ratio": ("부채총계", "자본총계"),
    "current_ratio": ("유동자산", "유동부채"),
    "op_margin": ("영업이익", "매출액"),
    "roa": ("당기순이익", "자산총계"),
}

FEATURE_COLUMNS: list[str] = [
    "ticker",
    "as_of",
    "fs_div",
    "debt_ratio",
    "current_ratio",
    "op_margin",
    "roa",
]


def _amount_from_account(df: pd.DataFrame, account_nm: str) -> float | None:
    """DART finstate parquet 에서 `account_nm` 일치하는 첫 row 의 thstrm_amount.

    labels.py `_get_op_income` 패턴 재사용. 누락·파싱 실패 시 None.
    """
    if "account_nm" not in df.columns or "thstrm_amount" not in df.columns:
        return None
    mask = df["account_nm"].astype(str).str.contains(account_nm, na=False)
    if not mask.any():
        return None
    val_str = str(df[mask].iloc[0].get("thstrm_amount", "")).replace(",", "").replace(" ", "")
    if val_str in ("", "nan", "None", "-"):
        return None
    try:
        return float(val_str)
    except ValueError:
        return None


def _ratio(df: pd.DataFrame, numerator_account: str, denominator_account: str) -> float | None:
    """분자/분모 계정에서 값 추출 후 비율 계산. 분모 0 또는 누락 시 None."""
    num = _amount_from_account(df, numerator_account)
    den = _amount_from_account(df, denominator_account)
    if num is None or den is None:
        return None
    if den == 0:
        return None
    return num / den


def build_features(
    ticker: str,
    as_of: date,
    *,
    reporter: DARTReporter | None = None,
    universe_loader: KOSPI200QuarterlyLoader | None = None,
    krx_ohlcv_cache_dir: Path | None = None,
) -> pd.DataFrame:
    """Baseline 재무비율 4건 산출 (PROGRESS §5.5.14 (b-1) 시그니처).

    Args:
        ticker: 6자리 종목코드.
        as_of: 빌더의 *공식 시간 인자* — 룩어헤드 contract 의 공식 입구.
            모든 외부 데이터 호출은 본 시점 이하만 사용.
        reporter: DARTReporter 인스턴스 (strict default — None 시 ValueError).
        universe_loader: KOSPI200QuarterlyLoader 인스턴스 (strict).
        krx_ohlcv_cache_dir: KRX OHLCV 캐시 경로 (현 baseline 비율은 미사용,
            향후 가격 기반 비율 확장 시 활성).

    Returns:
        1 row DataFrame: ticker / as_of / fs_div / debt_ratio / current_ratio /
        op_margin / roa.

    Raises:
        ValueError: 의존성 인자 None / universe 비멤버.

    설계 결정 (PROGRESS §5.5.14):
    - strict default — 진입점 한 곳에서 한 번 생성.
    - fs_div 컬럼 동행 (i) — 각 row 가 어느 회계 기준에서 추출됐는지 추적.
    """
    if reporter is None or universe_loader is None or krx_ohlcv_cache_dir is None:
        raise ValueError(
            "build_features: 의존성 명시 주입 필요 — reporter / universe_loader / "
            "krx_ohlcv_cache_dir 모두 None 아니어야 함 (strict default 정책)."
        )

    # universe 멤버십 검증 (피처에 *유니버스 변수* 는 안 들어가지만, 멤버 검증은 가능)
    quarter = universe_loader.as_of(as_of)
    if ticker not in universe_loader.tickers(quarter):
        raise ValueError(f"{ticker} 는 {as_of} 시점 universe ({quarter}) 멤버 아님")

    # 최신 available FY 보고서 — 룩어헤드 차단 (reporter.latest_available 책임)
    years = list(range(as_of.year - 1, as_of.year + 1))
    result = reporter.latest_available(ticker, as_of, years=years)

    empty_row: dict[str, object] = {
        "ticker": ticker,
        "as_of": as_of,
        "fs_div": None,
        "debt_ratio": None,
        "current_ratio": None,
        "op_margin": None,
        "roa": None,
    }
    if result is None:
        return pd.DataFrame([empty_row], columns=FEATURE_COLUMNS)

    df = result.df
    row: dict[str, object] = {
        "ticker": ticker,
        "as_of": as_of,
        "fs_div": result.ref.fs_div,
    }
    for ratio_name, (numerator, denominator) in RATIO_SPEC.items():
        row[ratio_name] = _ratio(df, numerator, denominator)

    return pd.DataFrame([row], columns=FEATURE_COLUMNS)
