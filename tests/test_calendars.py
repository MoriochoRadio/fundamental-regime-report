"""KRXBusinessCalendar 단위 테스트.

외부 의존성 없이(합성 캘린더로) 로직을 검증한다. 실제 FDR fetch는
별도 통합 테스트(`test_calendars_integration` 표시)에서 다룬다.
"""

from __future__ import annotations

from datetime import date

import pytest

from frr.data.calendars import KRXBusinessCalendar


@pytest.fixture
def cal() -> KRXBusinessCalendar:
    """2017년 12월 마지막 주간 + 2018년 1월 첫 주간의 합성 캘린더.

    구성:
    - 2017-12-25 (월) 크리스마스 휴장
    - 2017-12-26 (화) 영업
    - 2017-12-27 (수) 영업
    - 2017-12-28 (목) 영업
    - 2017-12-29 (금) 영업  ← 2017 연말 마지막 거래일
    - 2017-12-30 (토) 주말
    - 2017-12-31 (일) 주말
    - 2018-01-01 (월) 신정 휴장
    - 2018-01-02 (화) 영업  ← 2018 첫 거래일
    - 2018-01-03 (수) 영업
    - 2018-01-04 (목) 영업
    - 2018-01-05 (금) 영업
    """
    return KRXBusinessCalendar(
        business_days=[
            date(2017, 12, 26),
            date(2017, 12, 27),
            date(2017, 12, 28),
            date(2017, 12, 29),
            date(2018, 1, 2),
            date(2018, 1, 3),
            date(2018, 1, 4),
            date(2018, 1, 5),
        ]
    )


# ---- 기본 ----------------------------------------------------------------


def test_is_business_day_known_business(cal: KRXBusinessCalendar) -> None:
    assert cal.is_business_day(date(2017, 12, 29))
    assert cal.is_business_day(date(2018, 1, 2))


def test_is_business_day_weekend(cal: KRXBusinessCalendar) -> None:
    assert not cal.is_business_day(date(2017, 12, 30))  # 토
    assert not cal.is_business_day(date(2017, 12, 31))  # 일


def test_is_business_day_holiday(cal: KRXBusinessCalendar) -> None:
    assert not cal.is_business_day(date(2018, 1, 1))  # 신정 휴장


def test_is_business_day_out_of_range(cal: KRXBusinessCalendar) -> None:
    """캘린더 범위 밖 입력은 정의상 영업일 아님 (False)."""
    assert not cal.is_business_day(date(2017, 1, 1))
    assert not cal.is_business_day(date(2099, 1, 1))


# ---- previous/next -------------------------------------------------------


def test_previous_business_day_from_holiday(cal: KRXBusinessCalendar) -> None:
    """2018-01-01 (신정) → 직전 영업일 2017-12-29 (금)."""
    assert cal.previous_business_day(date(2018, 1, 1)) == date(2017, 12, 29)


def test_previous_business_day_from_weekend(cal: KRXBusinessCalendar) -> None:
    """2017-12-31 (일) → 2017-12-29 (금)."""
    assert cal.previous_business_day(date(2017, 12, 31)) == date(2017, 12, 29)


def test_previous_business_day_strict(cal: KRXBusinessCalendar) -> None:
    """입력 자체가 영업일이어도 *엄격히 이전*. d 자체는 포함 안 함."""
    assert cal.previous_business_day(date(2017, 12, 29)) == date(2017, 12, 28)


def test_next_business_day_from_weekend(cal: KRXBusinessCalendar) -> None:
    """2017-12-30 (토) → 2018-01-02 (신정 다음 영업일)."""
    assert cal.next_business_day(date(2017, 12, 30)) == date(2018, 1, 2)


def test_next_business_day_strict(cal: KRXBusinessCalendar) -> None:
    """입력 영업일 자체는 포함 안 함."""
    assert cal.next_business_day(date(2018, 1, 2)) == date(2018, 1, 3)


# ---- floor/ceil ----------------------------------------------------------


def test_floor_business_day_returns_same(cal: KRXBusinessCalendar) -> None:
    assert cal.floor(date(2017, 12, 29)) == date(2017, 12, 29)


def test_floor_holiday_goes_back(cal: KRXBusinessCalendar) -> None:
    """비영업일 분기말 처리의 핵심: 2018-01-01 → 2017-12-29."""
    assert cal.floor(date(2018, 1, 1)) == date(2017, 12, 29)


def test_ceil_business_day_returns_same(cal: KRXBusinessCalendar) -> None:
    assert cal.ceil(date(2018, 1, 2)) == date(2018, 1, 2)


def test_ceil_holiday_goes_forward(cal: KRXBusinessCalendar) -> None:
    assert cal.ceil(date(2018, 1, 1)) == date(2018, 1, 2)


# ---- add_business_days ---------------------------------------------------


def test_add_business_days_plus_one_from_business(cal: KRXBusinessCalendar) -> None:
    """rcept_dt + 1영업일 (D7). 2017-12-28 → 2017-12-29."""
    assert cal.add_business_days(date(2017, 12, 28), 1) == date(2017, 12, 29)


def test_add_business_days_plus_one_crosses_weekend(cal: KRXBusinessCalendar) -> None:
    """2017-12-29 (금) + 1영업일 → 2018-01-02 (신정 다음 영업일)."""
    assert cal.add_business_days(date(2017, 12, 29), 1) == date(2018, 1, 2)


def test_add_business_days_zero_on_business(cal: KRXBusinessCalendar) -> None:
    assert cal.add_business_days(date(2017, 12, 29), 0) == date(2017, 12, 29)


def test_add_business_days_zero_on_holiday(cal: KRXBusinessCalendar) -> None:
    """비영업일 + 0 → 직전 영업일로 floor (룩어헤드 차단 정신)."""
    assert cal.add_business_days(date(2018, 1, 1), 0) == date(2017, 12, 29)


def test_add_business_days_negative(cal: KRXBusinessCalendar) -> None:
    assert cal.add_business_days(date(2018, 1, 3), -1) == date(2018, 1, 2)
    assert cal.add_business_days(date(2018, 1, 2), -1) == date(2017, 12, 29)


# ---- 범위 --------------------------------------------------------------


def test_business_days_between(cal: KRXBusinessCalendar) -> None:
    days = cal.business_days_between(date(2017, 12, 28), date(2018, 1, 3))
    assert days == [
        date(2017, 12, 28),
        date(2017, 12, 29),
        date(2018, 1, 2),
        date(2018, 1, 3),
    ]


# ---- 통합 (실제 FDR fetch) ----------------------------------------------
#
# 네트워크가 필요하므로 환경에 따라 실패할 수 있다. 첫 호출 시 캐시가
# 생성되며 이후 호출은 캐시에서 로딩.


@pytest.mark.integration
def test_fetch_from_fdr_january_2018() -> None:
    """실제 KRX 2018년 1월 영업일을 받아 알려진 휴장일·영업일을 확인."""
    cal = KRXBusinessCalendar.fetch_from_fdr(date(2018, 1, 1), date(2018, 1, 31))
    # 2018-01-01 (신정) 휴장
    assert not cal.is_business_day(date(2018, 1, 1))
    # 2018-01-02 (화) 영업 - 2018 첫 거래일
    assert cal.is_business_day(date(2018, 1, 2))
    # 2018-01-06 (토) 주말
    assert not cal.is_business_day(date(2018, 1, 6))
