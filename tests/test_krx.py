"""KRXSingleTicker 단위 + 통합 테스트.

캐시 정책 (krx.py 모듈 docstring 참조)의 모든 경로를 검증한다:

1. 캐시 없음 → 페치 후 캐시 생성
2. 요청 ⊆ 캐시 → 캐시 슬라이스 (네트워크 0)
3. 요청이 캐시를 *왼쪽* 으로 확장 → 합집합 페치
4. 요청이 캐시를 *오른쪽* 으로 확장 → 합집합 페치
5. 요청·캐시 *겹침 없음* (gap) → 합집합 페치
6. `refresh=True` → 캐시 무시 강제 재페치

단위 테스트는 의존성 주입한 stub fetcher 로 네트워크 없이 통과한다.
통합 테스트(1개)는 실 pykrx 호출 후 삼성전자 한 달치 정상 응답을 확인.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from frr.data.krx import KRXSingleTicker

# ---- stub fetcher --------------------------------------------------------


class StubFetcher:
    """전체 OHLCV DataFrame 을 들고 있다가 요청 범위만큼 슬라이스 반환."""

    def __init__(self, full: pd.DataFrame) -> None:
        self.full = full
        self.calls: list[tuple[str, date, date]] = []

    def __call__(self, ticker: str, start: date, end: date) -> pd.DataFrame:
        self.calls.append((ticker, start, end))
        mask = (self.full.index.date >= start) & (self.full.index.date <= end)
        return self.full.loc[mask].copy()


@pytest.fixture
def fake_ohlcv_2020() -> pd.DataFrame:
    """2020-01-02 ~ 2020-12-30 의 5거래일/주 가짜 OHLCV (간단화: 평일만)."""
    idx = pd.bdate_range("2020-01-02", "2020-12-30")
    return pd.DataFrame(
        {
            "시가": range(len(idx)),
            "고가": range(len(idx)),
            "저가": range(len(idx)),
            "종가": range(len(idx)),
            "거래량": [1000] * len(idx),
            "등락률": [0.0] * len(idx),
        },
        index=idx,
    )


# ---- 1. 캐시 없음 → 페치 ----------------------------------------------------


def test_no_cache_fetches_and_writes(tmp_path: Path, fake_ohlcv_2020: pd.DataFrame) -> None:
    stub = StubFetcher(fake_ohlcv_2020)
    src = KRXSingleTicker(project_root=tmp_path, fetcher=stub)
    cache_path = src.cache_dir / "005930.parquet"
    assert not cache_path.exists()

    df = src.fetch_ohlcv("005930", date(2020, 3, 1), date(2020, 3, 31))

    assert cache_path.exists()
    assert len(stub.calls) == 1
    assert stub.calls[0] == ("005930", date(2020, 3, 1), date(2020, 3, 31))
    assert df.index.min().date() >= date(2020, 3, 1)
    assert df.index.max().date() <= date(2020, 3, 31)


# ---- 2. 요청 ⊆ 캐시 → 슬라이스 hit ----------------------------------------


def test_request_subset_of_cache_no_fetch(tmp_path: Path, fake_ohlcv_2020: pd.DataFrame) -> None:
    stub = StubFetcher(fake_ohlcv_2020)
    src = KRXSingleTicker(project_root=tmp_path, fetcher=stub)
    # 캐시 미리 큰 범위로
    src.fetch_ohlcv("005930", date(2020, 1, 2), date(2020, 12, 30))
    assert len(stub.calls) == 1  # 첫 1회

    # 부분 범위 요청 — 캐시에 완전히 포함
    df = src.fetch_ohlcv("005930", date(2020, 6, 1), date(2020, 6, 30))

    assert len(stub.calls) == 1  # 추가 호출 없음 (네트워크 0)
    assert df.index.min().date() >= date(2020, 6, 1)
    assert df.index.max().date() <= date(2020, 6, 30)
    assert len(df) > 0


# ---- 3. 캐시 왼쪽으로 확장 -----------------------------------------------


def test_request_extends_cache_left(tmp_path: Path, fake_ohlcv_2020: pd.DataFrame) -> None:
    stub = StubFetcher(fake_ohlcv_2020)
    src = KRXSingleTicker(project_root=tmp_path, fetcher=stub)
    # 캐시: [2020-07-01, 2020-12-30]
    src.fetch_ohlcv("005930", date(2020, 7, 1), date(2020, 12, 30))
    assert len(stub.calls) == 1

    # 요청: [2020-01-02, 2020-06-30] — 캐시 *왼쪽* 으로 확장
    df = src.fetch_ohlcv("005930", date(2020, 1, 2), date(2020, 6, 30))

    assert len(stub.calls) == 2  # 두 번째 페치 발생
    # 두 번째 호출은 합집합 [2020-01-02, 2020-12-30]
    second_call = stub.calls[1]
    assert second_call[1] == date(2020, 1, 2)
    assert second_call[2] == date(2020, 12, 30)
    # 반환은 요청 슬라이스
    assert df.index.min().date() >= date(2020, 1, 2)
    assert df.index.max().date() <= date(2020, 6, 30)


# ---- 4. 캐시 오른쪽으로 확장 ---------------------------------------------


def test_request_extends_cache_right(tmp_path: Path, fake_ohlcv_2020: pd.DataFrame) -> None:
    stub = StubFetcher(fake_ohlcv_2020)
    src = KRXSingleTicker(project_root=tmp_path, fetcher=stub)
    # 캐시: [2020-01-02, 2020-06-30]
    src.fetch_ohlcv("005930", date(2020, 1, 2), date(2020, 6, 30))
    assert len(stub.calls) == 1

    # 요청: [2020-07-01, 2020-12-30] — 캐시 *오른쪽* 으로 확장
    df = src.fetch_ohlcv("005930", date(2020, 7, 1), date(2020, 12, 30))

    assert len(stub.calls) == 2
    second_call = stub.calls[1]
    assert second_call[1] == date(2020, 1, 2)
    assert second_call[2] == date(2020, 12, 30)
    assert df.index.min().date() >= date(2020, 7, 1)
    assert df.index.max().date() <= date(2020, 12, 30)


# ---- 5. 캐시와 요청이 겹치지 않음 (gap) ---------------------------------


def test_request_disjoint_from_cache(tmp_path: Path, fake_ohlcv_2020: pd.DataFrame) -> None:
    stub = StubFetcher(fake_ohlcv_2020)
    src = KRXSingleTicker(project_root=tmp_path, fetcher=stub)
    # 캐시: [2020-01-02, 2020-03-31]
    src.fetch_ohlcv("005930", date(2020, 1, 2), date(2020, 3, 31))
    assert len(stub.calls) == 1

    # 요청: [2020-09-01, 2020-12-30] — 캐시와 *겹침 없음* (gap)
    df = src.fetch_ohlcv("005930", date(2020, 9, 1), date(2020, 12, 30))

    assert len(stub.calls) == 2
    # 합집합 [2020-01-02, 2020-12-30] (gap 영역까지 함께 페치)
    second_call = stub.calls[1]
    assert second_call[1] == date(2020, 1, 2)
    assert second_call[2] == date(2020, 12, 30)
    assert df.index.min().date() >= date(2020, 9, 1)
    assert df.index.max().date() <= date(2020, 12, 30)


# ---- 6. refresh=True 강제 재페치 -----------------------------------------


def test_refresh_forces_refetch(tmp_path: Path, fake_ohlcv_2020: pd.DataFrame) -> None:
    stub = StubFetcher(fake_ohlcv_2020)
    src = KRXSingleTicker(project_root=tmp_path, fetcher=stub)
    src.fetch_ohlcv("005930", date(2020, 1, 2), date(2020, 12, 30))
    assert len(stub.calls) == 1

    # 같은 범위 + refresh → 캐시 hit 조건 만족하더라도 재페치
    src.fetch_ohlcv("005930", date(2020, 6, 1), date(2020, 6, 30), refresh=True)

    assert len(stub.calls) == 2
    # refresh 는 *요청 범위*만 받아서 덮어쓴다 (합집합 X)
    second_call = stub.calls[1]
    assert second_call[1] == date(2020, 6, 1)
    assert second_call[2] == date(2020, 6, 30)


# ---- 7. start > end 안전성 ----------------------------------------------


def test_invalid_range_raises(tmp_path: Path) -> None:
    src = KRXSingleTicker(project_root=tmp_path)
    with pytest.raises(ValueError):
        src.fetch_ohlcv("005930", date(2020, 12, 30), date(2020, 1, 2))


# ---- 통합: 실제 pykrx --------------------------------------------------


@pytest.mark.integration
def test_fetch_samsung_one_month_real(tmp_path: Path) -> None:
    """실 pykrx로 005930(삼성전자) 2020-01 한 달치 OHLCV."""
    src = KRXSingleTicker(project_root=tmp_path)
    df = src.fetch_ohlcv("005930", date(2020, 1, 2), date(2020, 1, 31))

    assert len(df) >= 15, f"1월 거래일 너무 적음: {len(df)}"
    expected_cols = {"시가", "고가", "저가", "종가", "거래량", "등락률"}
    assert expected_cols.issubset(set(df.columns))
    # 인덱스가 폐구간 안
    assert df.index.min().date() >= date(2020, 1, 2)
    assert df.index.max().date() <= date(2020, 1, 31)
    # 캐시 파일 생성됨
    assert (src.cache_dir / "005930.parquet").exists()
