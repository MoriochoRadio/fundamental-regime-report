"""단계 1 룩어헤드 차단 통합 테스트.

각 어댑터 단위 테스트(`test_universe_loader.py`, `test_dart.py`,
`test_calendars.py`)는 이미 *자체* 룩어헤드 검증을 포함한다. 본 파일은
그 어댑터들이 *함께* 사용될 때도 룩어헤드 차단이 깨지지 않음을 보장하는
통합 시나리오를 모은다.

검증 영역:
1. `universe_loader.as_of(t)` + `dart.available_at(t)` 동시 호출 시
   *t 이후* 정보가 *어느 한 쪽*에서도 새지 않음.
2. DART 의 `available_from = rcept_dt + 1영업일` 이 캘린더와 정확히
   일치 — 즉 시점 매핑이 *어댑터 사이에서 동등*.
3. 분기 경계·연 경계의 *경계 케이스* — 시점 t 가 분기말 직전/당일/직후
   일 때 보고서 가용성이 정확히 분리.

단계 2 진입 시 추가 예정 (현재 placeholder):
- **유니버스 변수 격리 테스트**: KOSPI200 편입/편출 변수가 펀더멘털
  모델 피처 어디에도 포함되지 않음 (CLAUDE.md §5).
- **상장폐지 메타데이터 격리 테스트**: `DelistingDate`/`Reason`/
  `ArrantEnforceDate` 등이 펀더멘털 모델 피처에 포함되지 않음.

두 격리 테스트는 *피처 모듈*(`src/frr/features/`)이 존재해야 의미가
있으므로 단계 2 진입 시 본 파일에 추가한다.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from frr.data.calendars import KRXBusinessCalendar
from frr.data.dart import DARTReporter
from frr.data.universe_loader import KOSPI200QuarterlyLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---- 합성 fixture --------------------------------------------------------


@pytest.fixture(scope="module")
def real_universe_loader() -> KOSPI200QuarterlyLoader:
    """실제 매니페스트 — 40 분기 모두 검증됨."""
    return KOSPI200QuarterlyLoader.from_default(project_root=PROJECT_ROOT)


@pytest.fixture
def calendar_2017_2022() -> KRXBusinessCalendar:
    """단계 2 통합용 — 분기 경계·연 경계 검증에 충분한 평일 캘린더."""
    days = list(pd.bdate_range("2017-01-02", "2022-12-30").date)
    return KRXBusinessCalendar(business_days=days)


def _stub_dart_fetcher(rcept_no_by_period: dict[str, str]) -> object:
    """DART finstate 응답 stub. period→rcept_no 매핑."""
    from frr.data.dart import REPORT_CODES

    period_by_code = {code: p for p, code in REPORT_CODES.items()}

    def _fetch(ticker: str, year: int, reprt_code: str) -> pd.DataFrame:
        p = period_by_code.get(reprt_code, "?")
        rno = rcept_no_by_period.get(p, "20990101000000")
        return pd.DataFrame({"rcept_no": [rno] * 3, "account_nm": ["a", "b", "c"]})

    return _fetch


# ---- 1. 유니버스 + DART 룩어헤드 동시 검증 -------------------------------


def test_universe_and_dart_block_future_simultaneously(
    tmp_path: Path,
    real_universe_loader: KOSPI200QuarterlyLoader,
    calendar_2017_2022: KRXBusinessCalendar,
) -> None:
    """시점 t 에서 universe.as_of(t) 와 dart.available_at(t) 모두 *t 이후* 정보 무반환.

    universe: as_of 가 t 이전 분기 ID 반환.
    dart:    available_at 결과의 모든 available_from <= t.
    """
    fetcher = _stub_dart_fetcher(
        {
            "FY": "20180315000001",  # 2017 FY → 2018-03-15 접수
            "Q1": "20180515000001",  # 2018 Q1 → 2018-05-15
            "H1": "20180814000001",  # 2018 H1 → 2018-08-14
            "Q3": "20181114000001",  # 2018 Q3 → 2018-11-14
        }
    )
    dart = DARTReporter(calendar=calendar_2017_2022, project_root=tmp_path, fetcher=fetcher)

    # 시점 t = 2018-06-01 — Q1 (2018-05-16 사용가능) 까지만 사용 가능.
    t = date(2018, 6, 1)

    # universe: as_of 결과의 actual_reference_date 가 t 이하
    q_id = real_universe_loader.as_of(t)
    q_entry = real_universe_loader._entries[q_id]
    assert q_entry.actual_reference_date is not None
    assert q_entry.actual_reference_date <= t, (
        f"universe 룩어헤드 위반: {q_entry.actual_reference_date} > {t}"
    )

    # dart: 모든 available_from <= t
    refs = dart.available_at("005930", t, years=[2017, 2018])
    assert all(r.available_from is not None and r.available_from <= t for r in refs)
    # 구체적으로: FY 2017 (2018-03-16부터) + Q1 2018 (2018-05-16부터) 사용 가능,
    #          H1 2018 (2018-08-15부터) + Q3 2018 (2018-11-15부터) 미사용
    available = {(r.year, r.period) for r in refs}
    assert (2017, "FY") in available
    assert (2018, "Q1") in available
    assert (2018, "H1") not in available
    assert (2018, "Q3") not in available


# ---- 2. DART available_from 이 캘린더와 정확히 일치 ---------------------


def test_dart_available_from_matches_calendar(
    tmp_path: Path, calendar_2017_2022: KRXBusinessCalendar
) -> None:
    """`available_from = calendars.add_business_days(rcept_dt, 1)` 일관성.

    DART 어댑터가 캘린더를 직접 호출하므로 *동등*이 보장되어야 한다.
    여기서는 *세 가지 다른 rcept_dt 패턴* (평일·금요일·휴장 직전)을 동시
    검증해 모듈 사이의 시점 매핑이 *어댑터 사이에서 동일*함을 확인.
    """
    cases = [
        ("20180315000000", date(2018, 3, 15)),  # 목 → 다음 영업일 금 2018-03-16
        ("20180316000000", date(2018, 3, 16)),  # 금 → 월 2018-03-19
        ("20171229000000", date(2017, 12, 29)),  # 금 → 화 2018-01-02 (연말휴장)
    ]
    for rcept_no, rcept_dt in cases:
        fetcher = _stub_dart_fetcher({"FY": rcept_no})
        dart = DARTReporter(
            calendar=calendar_2017_2022, project_root=tmp_path / rcept_no, fetcher=fetcher
        )
        result = dart.fetch_report("005930", 2017, "FY")
        # available_from 이 캘린더의 next_business_day(rcept_dt) 와 동일
        expected = calendar_2017_2022.next_business_day(rcept_dt)
        assert result.ref.available_from == expected, (
            f"rcept_dt={rcept_dt}: dart={result.ref.available_from}, cal={expected}"
        )


# ---- 3. 시점 경계 — 분기말 직전·당일·직후 -------------------------------


def test_quarter_boundary_available_at(
    tmp_path: Path,
    real_universe_loader: KOSPI200QuarterlyLoader,
    calendar_2017_2022: KRXBusinessCalendar,
) -> None:
    """2018-03-31 (Q1말 = 영업일) 시점에서 *Q1 보고서 미가용* (접수가 5월).

    분기말 *당일* 에는 아직 보고서가 접수되지 않았으므로 사용 불가가 정상.
    """
    fetcher = _stub_dart_fetcher({"Q1": "20180515000001"})  # 2018-05-15 접수
    dart = DARTReporter(calendar=calendar_2017_2022, project_root=tmp_path, fetcher=fetcher)

    # 분기말 당일
    t = date(2018, 3, 30)  # 2018-03-31은 토요일, 영업일은 30 금
    refs = dart.available_at("005930", t, years=[2018])
    # 2018 Q1 보고서 (2018-05-16 사용가능) — t 이전이므로 미가용
    assert (2018, "Q1") not in {(r.year, r.period) for r in refs}

    # 접수일 + 1영업일 시점에서는 사용 가능
    t2 = date(2018, 5, 16)
    refs2 = dart.available_at("005930", t2, years=[2018])
    assert (2018, "Q1") in {(r.year, r.period) for r in refs2}


def test_year_boundary_universe_lookahead(
    real_universe_loader: KOSPI200QuarterlyLoader,
) -> None:
    """연 경계: 2018-12-31 (영업일은 28일) → 2018Q4 매핑. 2019Q1 미참조.

    실 매니페스트로 검증 — universe_loader 룩어헤드의 *결정적* 경계.
    """
    # 2018-12-28 (금) — 2018Q4 시점 (2018-12-31 요청에 fallback 적용된 영업일)
    q_id = real_universe_loader.as_of(date(2018, 12, 31))
    assert q_id == "2018Q4"

    # 분기 직후 (2019-01-02) → 여전히 2018Q4 (2019Q1 의 actual_reference_date 는 2019-03-29)
    q_id2 = real_universe_loader.as_of(date(2019, 1, 2))
    assert q_id2 == "2018Q4"

    # 2019Q1 actual_reference_date (2019-03-29) 직전 → 여전히 2018Q4
    q_id3 = real_universe_loader.as_of(date(2019, 3, 28))
    assert q_id3 == "2018Q4"

    # 2019-03-29 당일 → 2019Q1
    q_id4 = real_universe_loader.as_of(date(2019, 3, 29))
    assert q_id4 == "2019Q1"
