"""tests/test_labels.py — D2 라벨 모듈 단위 + 통합 테스트.

단위 7건 (합성 데이터, CI 실행):
  (1) drawdown 49.9% — 임계 미만 → 양성 아님
  (2) drawdown 50.0% — 임계 정확 + 영업이익 양→음 전환 → 양성 B
  (3) drawdown 60% + 영업이익 양→양 유지 → 양성 아님 (전환 미충족)
  (4) drawdown 60% + 영업이익 음→음 (이미 적자) → 양성 아님 (전환 없음)
  (5) A·B 동시 발생 ticker — events 2개 반환 + ticker 1개 dedup 검증
  (6) build_labels forward window 경계 — event_date = as_of + 365 → label=1
  (7) build_labels 룩어헤드 차단 — t 이전 event → label=0

통합 1건 (@pytest.mark.integration, 캐시 의존, CI 제외):
  D2 양성 20 종목 정답지 (EXPECTED_POSITIVES) 정확 일치 + 0년 + 우량주
  spot-check.

게이트 (PROGRESS §5.5.7/§5.5.9/§5.5.10):
- A=1 (포스코플랜텍 051310) + B=19 = alpha 20, 중복 0.
- 0년 = {2015, 2021, 2023} (A·B 합쳐서 양성 0 연도)
- 실패 시 §5.5.10 명시 진단: "구현 버그 vs D2 근거 흔들림" 자동 구분.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest
import yaml

from frr.labels import (
    LabelEvent,
    build_labels,
    find_distress_events,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ============================================================================
# 합성 데이터 helper — DART finstate parquet + meta.yaml 생성
# ============================================================================


def _write_finstate(
    ticker_dir: Path, year: int, op_income: float | None, status: str = "ok"
) -> None:
    """합성 DART finstate 캐시 생성 (tmp_path 격리)."""
    ticker_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = ticker_dir / f"{year}_FY.parquet"
    meta_path = ticker_dir / f"{year}_FY.meta.yaml"
    if op_income is None:
        # status != ok → 빈 DataFrame
        df = pd.DataFrame({"account_nm": [], "thstrm_amount": []})
    else:
        df = pd.DataFrame(
            {
                "account_nm": ["영업이익", "당기순이익"],
                "thstrm_amount": [str(int(op_income)), "0"],
            }
        )
    df.to_parquet(parquet_path)
    meta_path.write_text(yaml.safe_dump({"status": status}), encoding="utf-8")


def _make_ohlcv(
    dates: list[pd.Timestamp], closes: list[float], min_periods_pad: int = 252
) -> pd.DataFrame:
    """합성 OHLCV — 최소 252영업일 보장을 위해 padding."""
    # padding (drawdown rolling window 만족용) — 직전 평탄 padding
    pad_n = max(0, min_periods_pad - len(dates))
    if pad_n > 0:
        first_dt = dates[0]
        pad_dates = pd.date_range(end=first_dt - pd.Timedelta(days=1), periods=pad_n, freq="B")
        pad_closes = [closes[0]] * pad_n
        all_dates = list(pad_dates) + dates
        all_closes = pad_closes + closes
    else:
        all_dates = dates
        all_closes = closes
    return pd.DataFrame({"종가": all_closes}, index=pd.DatetimeIndex(all_dates))


def _write_ohlcv(cache_dir: Path, ticker: str, df: pd.DataFrame) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_dir / f"{ticker}.parquet")


def _empty_fdr_delisting() -> pd.DataFrame:
    """A 신호용 빈 delisting (B 단위 테스트 시)."""
    return pd.DataFrame(
        {
            "Symbol": pd.Series([], dtype=str),
            "Market": pd.Series([], dtype=str),
            "DelistingDate": pd.Series([], dtype="datetime64[ns]"),
            "Reason": pd.Series([], dtype=str),
        }
    )


# ============================================================================
# Mock universe_loader (build_labels 단위용)
# ============================================================================


class _MockLoader:
    """KOSPI200QuarterlyLoader 호환 minimal mock — build_labels 단위 테스트용."""

    def __init__(self, quarters_tickers: dict[str, set[str]], as_of_map: dict[date, str]):
        self._quarters_tickers = quarters_tickers
        self._as_of_map = as_of_map

    def available_quarters(self) -> list[str]:
        return list(self._quarters_tickers.keys())

    def tickers(self, q: str) -> set[str]:
        return self._quarters_tickers.get(q, set())

    def as_of(self, t: date) -> str | None:
        return self._as_of_map.get(t)


# ============================================================================
# (1) drawdown 49.9% — 임계 미만, 양성 아님
# ============================================================================


def test_drawdown_under_threshold_no_event(tmp_path: Path) -> None:
    krx_dir = tmp_path / "krx"
    dart_dir = tmp_path / "dart"
    ticker = "999991"
    # peak 100 → trough 50.1 (49.9% drop) — 임계 미충족
    dates = list(pd.date_range("2020-01-01", periods=60, freq="B"))
    closes = [100.0] * 30 + [50.1] * 30
    _write_ohlcv(krx_dir, ticker, _make_ohlcv(dates, closes))
    _write_finstate(dart_dir / ticker, 2019, 100.0)
    _write_finstate(dart_dir / ticker, 2020, -100.0)  # 전환 가능, 단 dd 임계 미달

    events = find_distress_events(
        universe={ticker},
        fdr_delisting=_empty_fdr_delisting(),
        krx_ohlcv_cache_dir=krx_dir,
        dart_finstate_cache_dir=dart_dir,
    )
    assert len(events) == 0, "dd 49.9% (임계 미달) — 양성 안 됨"


# ============================================================================
# (2) drawdown 50.0% + 영업이익 양→음 → 양성 B
# ============================================================================


def test_drawdown_at_threshold_with_op_transition_positive(tmp_path: Path) -> None:
    krx_dir = tmp_path / "krx"
    dart_dir = tmp_path / "dart"
    ticker = "999992"
    # peak 100 → trough 50.0 (50% drop) — 임계 정확 도달
    dates = list(pd.date_range("2020-01-01", periods=60, freq="B"))
    closes = [100.0] * 30 + [50.0] * 30
    _write_ohlcv(krx_dir, ticker, _make_ohlcv(dates, closes))
    _write_finstate(dart_dir / ticker, 2019, 100.0)  # 양수
    _write_finstate(dart_dir / ticker, 2020, -100.0)  # 음수 전환

    events = find_distress_events(
        universe={ticker},
        fdr_delisting=_empty_fdr_delisting(),
        krx_ohlcv_cache_dir=krx_dir,
        dart_finstate_cache_dir=dart_dir,
    )
    assert len(events) == 1
    e = events[0]
    assert e.ticker == ticker
    assert e.source == "B"
    assert e.op_prev == 100.0
    assert e.op_curr == -100.0
    assert e.drawdown_pct is not None and e.drawdown_pct <= -0.50


# ============================================================================
# (3) drawdown 60% + 영업이익 양→양 유지 → 양성 아님 (전환 미충족)
# ============================================================================


def test_drawdown_passes_but_op_stays_positive(tmp_path: Path) -> None:
    krx_dir = tmp_path / "krx"
    dart_dir = tmp_path / "dart"
    ticker = "999993"
    dates = list(pd.date_range("2020-01-01", periods=60, freq="B"))
    closes = [100.0] * 30 + [40.0] * 30  # 60% drop
    _write_ohlcv(krx_dir, ticker, _make_ohlcv(dates, closes))
    _write_finstate(dart_dir / ticker, 2019, 100.0)
    _write_finstate(dart_dir / ticker, 2020, 50.0)  # 양수 유지

    events = find_distress_events(
        universe={ticker},
        fdr_delisting=_empty_fdr_delisting(),
        krx_ohlcv_cache_dir=krx_dir,
        dart_finstate_cache_dir=dart_dir,
    )
    assert len(events) == 0, "dd 60% 충족하나 op 전환 없음 — 양성 안 됨"


# ============================================================================
# (4) drawdown 60% + 영업이익 음→음 (이미 적자) → 양성 아님
# ============================================================================


def test_drawdown_passes_but_op_already_negative(tmp_path: Path) -> None:
    krx_dir = tmp_path / "krx"
    dart_dir = tmp_path / "dart"
    ticker = "999994"
    dates = list(pd.date_range("2020-01-01", periods=60, freq="B"))
    closes = [100.0] * 30 + [40.0] * 30
    _write_ohlcv(krx_dir, ticker, _make_ohlcv(dates, closes))
    _write_finstate(dart_dir / ticker, 2019, -50.0)  # 이미 음수
    _write_finstate(dart_dir / ticker, 2020, -100.0)  # 여전히 음수

    events = find_distress_events(
        universe={ticker},
        fdr_delisting=_empty_fdr_delisting(),
        krx_ohlcv_cache_dir=krx_dir,
        dart_finstate_cache_dir=dart_dir,
    )
    assert len(events) == 0, "op_prev <= 0 — 양→음 전환 조건 미충족, 양성 안 됨"


# ============================================================================
# (5) A·B 동시 ticker — events 2개 + ticker dedup
# ============================================================================


def test_a_and_b_concurrent_returns_two_events(tmp_path: Path) -> None:
    krx_dir = tmp_path / "krx"
    dart_dir = tmp_path / "dart"
    ticker = "999995"
    dates = list(pd.date_range("2020-01-01", periods=60, freq="B"))
    closes = [100.0] * 30 + [40.0] * 30  # 60% drop
    _write_ohlcv(krx_dir, ticker, _make_ohlcv(dates, closes))
    _write_finstate(dart_dir / ticker, 2019, 100.0)
    _write_finstate(dart_dir / ticker, 2020, -100.0)

    # A 신호 — 동일 ticker delisting (자본전액잠식)
    fdr = pd.DataFrame(
        {
            "Symbol": [ticker],
            "Market": ["KOSPI"],
            "DelistingDate": [pd.Timestamp("2020-06-15")],
            "Reason": ["자본전액잠식"],
        }
    )

    events = find_distress_events(
        universe={ticker},
        fdr_delisting=fdr,
        krx_ohlcv_cache_dir=krx_dir,
        dart_finstate_cache_dir=dart_dir,
    )
    sources = sorted(e.source for e in events)
    assert sources == ["A", "B"], "A·B 동시 → events 2 개 반환"

    # ticker 단위 집계 (호출자 책임) — set 으로 dedup 시 1
    ticker_set = {e.ticker for e in events}
    assert len(ticker_set) == 1
    assert ticker in ticker_set


# ============================================================================
# (6) build_labels forward window 365일 경계
# ============================================================================


def test_build_labels_forward_window_boundary() -> None:
    ticker = "999996"
    as_of = date(2020, 1, 1)
    # event_date = as_of + 365일 → label=1 (경계 포함)
    event_at_365 = LabelEvent(
        ticker=ticker,
        event_date=date(2020, 12, 31),  # 2020-01-01 + 365 = 2020-12-31
        source="B",
        detail="boundary",
    )
    # event_date = as_of + 366일 → label=0 (경계 밖)
    event_at_366 = LabelEvent(
        ticker=ticker,
        event_date=date(2021, 1, 1),
        source="B",
        detail="just outside",
    )

    loader = _MockLoader(
        quarters_tickers={"2020Q1": {ticker}},
        as_of_map={as_of: "2020Q1"},
    )

    # event_at_365 — label=1
    df_1 = build_labels([event_at_365], universe_loader=loader, as_of_grid=[as_of])
    assert len(df_1) == 1
    assert df_1.iloc[0]["label"] == 1, "event_date = as_of + 365일 → label=1 (경계 포함)"

    # event_at_366 — label=0
    df_0 = build_labels([event_at_366], universe_loader=loader, as_of_grid=[as_of])
    assert len(df_0) == 1
    assert df_0.iloc[0]["label"] == 0, "event_date = as_of + 366일 → label=0 (경계 밖)"


# ============================================================================
# (7) build_labels 룩어헤드 차단 — t 이전 event 무시
# ============================================================================


def test_build_labels_lookahead_blocked() -> None:
    ticker = "999997"
    as_of = date(2020, 6, 1)
    # event_date < as_of → label=0 (룩어헤드 차단 — 미래만 본다)
    past_event = LabelEvent(
        ticker=ticker,
        event_date=date(2020, 5, 1),
        source="B",
        detail="past — must be excluded",
    )
    # event_date = as_of (정확히 같음) → label=0 (strictly > as_of)
    same_day_event = LabelEvent(
        ticker=ticker,
        event_date=as_of,
        source="B",
        detail="same day — must be excluded (strictly > as_of)",
    )

    loader = _MockLoader(
        quarters_tickers={"2020Q2": {ticker}},
        as_of_map={as_of: "2020Q2"},
    )

    df = build_labels([past_event, same_day_event], universe_loader=loader, as_of_grid=[as_of])
    assert len(df) == 1
    assert df.iloc[0]["label"] == 0, "t 이전·t 동일 event → label=0 (룩어헤드 차단)"


# ============================================================================
# 통합 테스트 (실 캐시 의존, CI 제외) — D2 정답지 20 종목 게이트
# ============================================================================


EXPECTED_POSITIVES_A: frozenset[str] = frozenset(
    {
        "051310",  # 포스코플랜텍 — 자본전액잠식 (2016-04-15)
    }
)
EXPECTED_POSITIVES_B: frozenset[str] = frozenset(
    {
        "003920",  # 남양유업
        "005070",  # 코스모신소재
        "007810",  # 코리아써키트
        "008060",  # 대덕
        "010690",  # 화신
        "010950",  # S-Oil
        "019680",  # 대교
        "029530",  # 신도리코
        "033240",  # 자화전자
        "034730",  # SK (신, 합병 후 신설)
        "035250",  # 강원랜드
        "047810",  # 한국항공우주
        "066970",  # 엘앤에프
        "073240",  # 금호타이어
        "096770",  # SK이노베이션
        "267250",  # HD현대
        "267260",  # HD현대일렉트릭
        "361610",  # SK아이이테크놀로지
        "450080",  # 에코프로머티
    }
)
# A 교집합 B = ∅ (실데이터 검증, 포스코플랜텍 ∉ B), 합집합 20
EXPECTED_POSITIVES: frozenset[str] = EXPECTED_POSITIVES_A | EXPECTED_POSITIVES_B
# §5.5.9/§5.5.10 확정 0년 — A·B 합쳐서 양성 0 인 연도
EXPECTED_ZERO_YEARS: frozenset[int] = frozenset({2015, 2021, 2023})


@pytest.mark.integration
def test_find_distress_events_reproduces_20_positives() -> None:
    """D2 정답지 20 종목 정확 일치 게이트 — §5.5.7/§5.5.9/§5.5.10.

    실패 시 §5.5.10 명시 진단:
    - 구현 버그 (코드 변경 직후 일부만 어긋남) → labels.py 수정
    - D2 근거 흔들림 (전체 카운트 어긋남) → 즉시 멈추고 보고

    캐시 의존 (KRX OHLCV + DART finstate + FDR delisting), CI 제외 marker.
    """
    from frr.data.fdr import FDRDataSource
    from frr.data.universe_loader import KOSPI200QuarterlyLoader

    loader = KOSPI200QuarterlyLoader.from_default(project_root=PROJECT_ROOT)
    universe: set[str] = set()
    for q in loader.available_quarters():
        universe.update(loader.tickers(q))

    fdr_source = FDRDataSource(project_root=PROJECT_ROOT)
    events = find_distress_events(
        universe=universe,
        fdr_delisting=fdr_source.delisting(),
        krx_ohlcv_cache_dir=PROJECT_ROOT / "data" / "raw" / "krx" / "ohlcv",
        dart_finstate_cache_dir=PROJECT_ROOT / "data" / "raw" / "dart",
    )

    a_tickers = {e.ticker for e in events if e.source == "A"}
    b_tickers = {e.ticker for e in events if e.source == "B"}

    # === 핵심 게이트 — frozenset 정확 일치 ===

    # A: 포스코플랜텍 단일 (P1 정정, §5.5.9)
    assert a_tickers == EXPECTED_POSITIVES_A, (
        f"A 1 재현 실패: 실제 {sorted(a_tickers)} vs 기대 {sorted(EXPECTED_POSITIVES_A)}"
    )

    # B 19 frozenset 정확 일치 검증.
    # §5.5.9 P1 정정에서 distress filter 변경(A에만 영향, B 무관)이
    # step 2 진단 재실행에서 frozenset 동치(B_PRE_FIX_check=True)로 입증됨.
    # 미래에 진단 로직 변경이 의도치 않게 B에 영향 주면 이 assertion이 즉시 잡음.
    assert b_tickers == EXPECTED_POSITIVES_B, (
        f"B 19 재현 실패: pre-only={sorted(EXPECTED_POSITIVES_B - b_tickers)}, "
        f"current-only={sorted(b_tickers - EXPECTED_POSITIVES_B)}"
    )

    # Union 무결성 + 중복 0
    assert a_tickers | b_tickers == EXPECTED_POSITIVES, "Union 무결성 실패"
    assert a_tickers & b_tickers == set(), "A ∩ B = 공집합 실패"
    assert len(EXPECTED_POSITIVES) == 20, "EXPECTED_POSITIVES 20 항상성"

    # === 0년 검증 (§5.5.9/§5.5.10 확정) ===
    event_years = {e.event_date.year for e in events}
    for zero_year in EXPECTED_ZERO_YEARS:
        assert zero_year not in event_years, (
            f"{zero_year}년 양성 0 재현 실패 (§5.5.9/§5.5.10 확정 0년)"
        )

    # === 우량주 spot-check (혼입 차단) ===
    BLUE_CHIPS: frozenset[str] = frozenset(
        {
            "005930",
            "000660",
            "005380",
            "066570",
            "035420",
            "035720",
            "051910",
            "005490",
            "207940",
            "006400",
        }
    )
    assert (a_tickers | b_tickers) & BLUE_CHIPS == set(), "우량주 양성 혼입"
