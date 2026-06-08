"""baseline features 빌더 단위 테스트 — 4 ratio 산출 + strict default + 경계.

연관: PROGRESS §5.5.14 (b-1) / §5.5.15 (fs_div 컬럼 동행 정당화).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from frr.features.baseline import (
    FEATURE_COLUMNS,
    RATIO_SPEC,
    _amount_from_account,
    _ratio,
    build_features,
)


def _fake_finstate_df(values: dict[str, float]) -> pd.DataFrame:
    """`{account_nm: amount}` → DART finstate 응답 모양."""
    return pd.DataFrame(
        {
            "account_nm": list(values.keys()),
            "thstrm_amount": [f"{int(v):,}" for v in values.values()],
            "rcept_no": ["20210309000744"] * len(values),
        }
    )


class _FakeReportRef:
    def __init__(self, fs_div: str | None) -> None:
        self.fs_div = fs_div


class _FakeReportResult:
    def __init__(self, df: pd.DataFrame, fs_div: str | None) -> None:
        self.df = df
        self.ref = _FakeReportRef(fs_div)


class _StubReporter:
    def __init__(self, result: Any = None) -> None:
        self._result = result

    def latest_available(self, ticker: str, t: date, years: list[int]) -> Any:
        return self._result


class _StubUniverseLoader:
    def __init__(self, members: list[str]) -> None:
        self._members = members

    def as_of(self, t: date) -> str:
        return "2020Q1"

    def tickers(self, quarter: str) -> list[str]:
        return self._members


# ---- strict default — 누락 인자 ValueError ------------------------------


def test_build_features_missing_reporter_raises(tmp_path: Path) -> None:
    """reporter=None → ValueError (strict default 정책)."""
    with pytest.raises(ValueError, match="의존성 명시 주입"):
        build_features(
            ticker="005930",
            as_of=date(2020, 6, 30),
            reporter=None,
            universe_loader=_StubUniverseLoader(["005930"]),  # type: ignore[arg-type]
            krx_ohlcv_cache_dir=tmp_path,
        )


def test_build_features_missing_universe_raises(tmp_path: Path) -> None:
    """universe_loader=None → ValueError."""
    with pytest.raises(ValueError, match="의존성 명시 주입"):
        build_features(
            ticker="005930",
            as_of=date(2020, 6, 30),
            reporter=_StubReporter(),  # type: ignore[arg-type]
            universe_loader=None,
            krx_ohlcv_cache_dir=tmp_path,
        )


# ---- universe 멤버 검증 ---------------------------------------------------


def test_build_features_non_member_raises(tmp_path: Path) -> None:
    """as_of 시점에 universe 비멤버 → ValueError."""
    with pytest.raises(ValueError, match=r"universe.*멤버 아님"):
        build_features(
            ticker="999999",
            as_of=date(2020, 6, 30),
            reporter=_StubReporter(),  # type: ignore[arg-type]
            universe_loader=_StubUniverseLoader(["005930"]),  # type: ignore[arg-type]
            krx_ohlcv_cache_dir=tmp_path,
        )


# ---- 정상 ratio 산출 ------------------------------------------------------


def test_build_features_computes_4_ratios(tmp_path: Path) -> None:
    """4 ratio 산출 + fs_div 컬럼 동행."""
    finstate = _fake_finstate_df(
        {
            "부채총계": 60_000_000_000,  # 부채 60억
            "자본총계": 40_000_000_000,  # 자본 40억 → debt_ratio = 1.5
            "유동자산": 30_000_000_000,
            "유동부채": 20_000_000_000,  # current_ratio = 1.5
            "영업이익": 10_000_000_000,
            "매출액": 100_000_000_000,  # op_margin = 0.10
            "당기순이익": 5_000_000_000,
            "자산총계": 100_000_000_000,  # roa = 0.05
        }
    )
    reporter = _StubReporter(_FakeReportResult(finstate, fs_div="CFS"))

    result = build_features(
        ticker="005930",
        as_of=date(2020, 6, 30),
        reporter=reporter,  # type: ignore[arg-type]
        universe_loader=_StubUniverseLoader(["005930"]),  # type: ignore[arg-type]
        krx_ohlcv_cache_dir=tmp_path,
    )

    assert list(result.columns) == FEATURE_COLUMNS
    assert len(result) == 1
    row = result.iloc[0]
    assert row["ticker"] == "005930"
    assert row["as_of"] == date(2020, 6, 30)
    assert row["fs_div"] == "CFS"
    assert row["debt_ratio"] == pytest.approx(1.5)
    assert row["current_ratio"] == pytest.approx(1.5)
    assert row["op_margin"] == pytest.approx(0.10)
    assert row["roa"] == pytest.approx(0.05)


# ---- 경계: 분모 0 / 분자 누락 ---------------------------------------------


def test_ratio_returns_none_on_zero_denominator() -> None:
    """분모 0 → None (DivisionByZero 회피)."""
    df = _fake_finstate_df({"부채총계": 100, "자본총계": 0})
    assert _ratio(df, "부채총계", "자본총계") is None


def test_ratio_returns_none_on_missing_numerator() -> None:
    """분자 계정 누락 → None."""
    df = _fake_finstate_df({"자본총계": 100})  # 부채총계 없음
    assert _ratio(df, "부채총계", "자본총계") is None


def test_amount_from_account_returns_none_for_missing_columns() -> None:
    """account_nm / thstrm_amount 컬럼 둘 다 없으면 None."""
    df = pd.DataFrame({"other_col": [1, 2]})
    assert _amount_from_account(df, "부채총계") is None


# ---- RATIO_SPEC 박제 검증 -------------------------------------------------


def test_ratio_spec_keys_match_feature_columns() -> None:
    """RATIO_SPEC 의 키가 FEATURE_COLUMNS 의 ratio 부분과 정확히 일치 (회귀 게이트)."""
    ratio_keys = set(RATIO_SPEC.keys())
    expected_columns = {"debt_ratio", "current_ratio", "op_margin", "roa"}
    assert ratio_keys == expected_columns
    # FEATURE_COLUMNS 도 일관
    assert set(FEATURE_COLUMNS) - {"ticker", "as_of", "fs_div"} == expected_columns
