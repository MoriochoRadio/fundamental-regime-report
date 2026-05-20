"""D2 label module — 재무 충격 위험 라벨 생성.

D2 = alpha = 상폐 부실 (A) 합집합 drawdown 50% + 영업이익 음수 전환 (B), 1년 forward.

진단 스크립트 (`scripts/diagnose_a2_b1prime.py`) 의 양성 산출 로직과 byte-for-
byte 동일. D2 근거: PROGRESS §5.5.7 (D2 최종 확정) / §5.5.8 (A1 신용등급 자동
확보 불가) / §5.5.9 (distress 필터 결함 P1 정정) / §5.5.10 (forward window
1→2년 ablation 기각).

격리 원칙 (CLAUDE.md §5):
- 본 모듈은 *라벨 정의용 변수* (상폐 메타, 영업이익) 자유 접근.
- features 모듈은 *동일 변수에 접근 금지* — 단계 2 격리 테스트로 강제.

v1 NOTE:
- Forward window 1년 고정 (§5.5.10 결정).
- CFS-only DART cache. OFS fallback (D10) 은 단계 2 step #3 별도.
- Distress whitelist = {"자본전액잠식"} (P1, §5.5.9). 미래 확장은 §3 단계 2
  DoD "D2 라벨 출처 보강 결정" 항목에서 별도 검증.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Literal

import pandas as pd
import yaml

# §5.5.9 P1 정정: distress filter 화이트리스트 (현 universe + 분석기간 매칭 1건)
DISTRESS_REASONS_WHITELIST: frozenset[str] = frozenset({"자본전액잠식"})


@dataclass(frozen=True)
class LabelEvent:
    """한 ticker 의 D2 양성 사건.

    source A: 상폐 부실 (FDR delisting Reason ∈ DISTRESS_REASONS_WHITELIST)
    source B: drawdown 50% + 영업이익 음수 전환

    동일 ticker 가 A·B 둘 다 양성이면 LabelEvent 2 개 반환. ticker 단위 집계는
    호출자(build_labels 등) 책임.
    """

    ticker: str
    event_date: date
    source: Literal["A", "B"]
    detail: str
    drawdown_pct: float | None = None
    op_prev: float | None = None
    op_curr: float | None = None


def _compute_drawdown_252(close: pd.Series, window: int = 252, min_periods: int = 60) -> pd.Series:
    """rolling N영업일 peak-to-trough drawdown (음수)."""
    rolling_peak = close.rolling(window=window, min_periods=min_periods).max()
    return (close - rolling_peak) / rolling_peak


def _get_op_income(ticker_dir: Path, year: int) -> float | None:
    """DART finstate FY{year} 영업이익 반환. 부재/오류 시 None.

    진단 스크립트 (`scripts/diagnose_a2_b1prime.py`) 의 get_op_income 과
    byte-for-byte 동일 로직.
    """
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
    val_str = str(df[mask].iloc[0].get("thstrm_amount", "")).replace(",", "").replace(" ", "")
    if val_str in ("", "nan", "None", "-"):
        return None
    try:
        return float(val_str)
    except ValueError:
        return None


def find_distress_events(
    universe: set[str],
    *,
    fdr_delisting: pd.DataFrame,
    krx_ohlcv_cache_dir: Path,
    dart_finstate_cache_dir: Path,
    analysis_start: date = date(2015, 1, 1),
    analysis_end: date = date(2024, 12, 31),
    drawdown_threshold: float = -0.50,
    drawdown_window_days: int = 252,
    drawdown_min_periods: int = 60,
    distress_reasons_whitelist: frozenset[str] = DISTRESS_REASONS_WHITELIST,
) -> list[LabelEvent]:
    """D2 양성 사건 산출 — 진단 스크립트와 byte-for-byte 동일 로직.

    Signal A (상폐 부실): FDR delisting where
        Symbol ∈ universe, Market == 'KOSPI', len(Symbol) == 6,
        DelistingDate ∈ [analysis_start, analysis_end],
        Reason ∈ distress_reasons_whitelist  (P1 정정, §5.5.9)
        → LabelEvent(source="A", event_date=DelistingDate)

    Signal B (drawdown + 영업이익 음수 전환): for each ticker with KRX OHLCV cache,
        first idx where rolling 252-day drawdown <= -0.50,
        FY(dd_year-1) 영업이익 > 0 AND FY(dd_year) 영업이익 < 0
        → LabelEvent(source="B", event_date=first_dd_idx)

    Forward window 1년 고정 (§5.5.10). 현 universe + 분석기간에서 양성 20 종목
    (A=1 포스코플랜텍 051310 + B=19), 중복 0.
    """
    events: list[LabelEvent] = []

    # === Signal A — 상폐 부실 (whitelist) ===
    mask_dl = (
        (fdr_delisting["DelistingDate"] >= pd.Timestamp(analysis_start))
        & (fdr_delisting["DelistingDate"] <= pd.Timestamp(analysis_end))
        & (fdr_delisting["Market"] == "KOSPI")
        & (fdr_delisting["Symbol"].str.len() == 6)
        & (fdr_delisting["Symbol"].isin(universe))
    )
    delisted_universe = fdr_delisting[mask_dl]
    mask_distress = delisted_universe["Reason"].isin(distress_reasons_whitelist)
    for _, row in delisted_universe[mask_distress].iterrows():
        dl_date = row["DelistingDate"]
        if pd.isna(dl_date):
            continue
        events.append(
            LabelEvent(
                ticker=str(row["Symbol"]),
                event_date=dl_date.date(),
                source="A",
                detail=f"delisting: {row['Reason']}",
            )
        )

    # === Signal B — drawdown 50% + 영업이익 음수 전환 ===
    for ticker in sorted(universe):
        ohlcv_path = krx_ohlcv_cache_dir / f"{ticker}.parquet"
        if not ohlcv_path.exists():
            continue
        ticker_dir = dart_finstate_cache_dir / ticker
        if not ticker_dir.exists():
            continue
        try:
            ohlcv = pd.read_parquet(ohlcv_path)
        except Exception:
            continue
        if len(ohlcv) < drawdown_window_days:
            continue
        close = ohlcv["종가"]
        dd = _compute_drawdown_252(close, drawdown_window_days, drawdown_min_periods)
        mask_dd = dd <= drawdown_threshold
        if not mask_dd.any():
            continue
        first_dd_idx = mask_dd.idxmax()
        dd_year = first_dd_idx.year
        op_prev = _get_op_income(ticker_dir, dd_year - 1)
        op_curr = _get_op_income(ticker_dir, dd_year)
        if op_prev is None or op_curr is None:
            continue
        if op_prev > 0 and op_curr < 0:
            dd_val = float(dd.loc[first_dd_idx])
            events.append(
                LabelEvent(
                    ticker=ticker,
                    event_date=first_dd_idx.date(),
                    source="B",
                    detail=(
                        f"dd={dd_val:.2%} on {first_dd_idx.date()}, op {op_prev:.0f}->{op_curr:.0f}"
                    ),
                    drawdown_pct=dd_val,
                    op_prev=op_prev,
                    op_curr=op_curr,
                )
            )

    return events


def build_labels(
    events: list[LabelEvent],
    *,
    universe_loader: Any,  # KOSPI200QuarterlyLoader (protocol — circular import 회피)
    as_of_grid: Sequence[date],
    forward_window_days: int = 365,
) -> pd.DataFrame:
    """per-(ticker, as_of) 라벨 materialization.

    각 as_of in grid 에 대해 universe.tickers(as_of) 의 각 ticker:
      label = 1 if any event with event_date ∈ (as_of, as_of + forward_window_days]
              else 0

    같은 (ticker, as_of) 에 A·B 모두 매칭이면 source = "A+B".

    Returns DataFrame[ticker, as_of, label, source, event_date].

    Forward window 1년 고정 (§5.5.10).
    """
    rows = []
    for as_of in as_of_grid:
        as_of_ts = pd.Timestamp(as_of)
        forward_end = as_of_ts + pd.Timedelta(days=forward_window_days)
        q = universe_loader.as_of(as_of)
        if q is None:
            continue
        tickers_at_t = set(universe_loader.tickers(q))
        for ticker in sorted(tickers_at_t):
            matching = [
                e
                for e in events
                if e.ticker == ticker
                and e.event_date is not None
                and as_of_ts < pd.Timestamp(e.event_date) <= forward_end
            ]
            label = 1 if matching else 0
            sources = sorted({e.source for e in matching})
            source_str = "+".join(sources) if sources else ""
            event_date_val = matching[0].event_date if matching else None
            rows.append(
                {
                    "ticker": ticker,
                    "as_of": as_of,
                    "label": label,
                    "source": source_str,
                    "event_date": event_date_val,
                }
            )

    return pd.DataFrame(rows, columns=["ticker", "as_of", "label", "source", "event_date"])
