"""universe_loader 단위 테스트.

2015Q1 한 분기만 다운로드된 단계에서도 의미 있는 검증이 가능하도록
설계됐다. 향후 분기가 늘어나면 일부 테스트는 자연스럽게 커버리지가
넓어지지만, 본 테스트들은 *최소 1개 분기*만 있어도 동작한다.

핵심 검증 항목:
- 매니페스트가 비어 있지 않은 엔트리만 노출하는가
- sha256 무결성이 작동하는가
- 종목코드의 앞 0이 보존되는가 (가장 중요한 dtype 결정)
- 카프로(006380, 2017-12 상폐)가 2015Q1에 포함되는가
  → point-in-time 유니버스 정의가 실제로 *상폐 종목까지 포함*하는지
- `as_of(t)` 가 룩어헤드를 차단하는가
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from frr.data.universe_loader import (
    IntegrityError,
    KOSPI200QuarterlyLoader,
    ManifestError,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def loader() -> KOSPI200QuarterlyLoader:
    return KOSPI200QuarterlyLoader.from_default(project_root=PROJECT_ROOT)


# ---- 매니페스트 파싱 / 노출 ------------------------------------------------


def test_2015q1_is_available(loader: KOSPI200QuarterlyLoader) -> None:
    assert "2015Q1" in loader.available_quarters()


def test_unfilled_quarters_are_hidden(loader: KOSPI200QuarterlyLoader) -> None:
    """매니페스트에 40분기가 있지만 채워진 건 1개뿐 — 그 1개만 노출되어야."""
    available = loader.available_quarters()
    # 최소 2015Q1은 있어야 하고, 사용자가 더 다운로드하지 않은 분기는 제외됨
    assert "2015Q1" in available
    # 채워지지 않은 임의의 분기는 노출되면 안 됨
    assert "2024Q4" not in available  # 아직 다운로드 X


# ---- CSV 파싱 / dtype 보존 ------------------------------------------------


def test_composition_2015q1_has_200_rows(loader: KOSPI200QuarterlyLoader) -> None:
    df = loader.composition("2015Q1")
    assert len(df) == 200, f"KOSPI200은 200종목, 실제 {len(df)}"


def test_ticker_keeps_leading_zeros(loader: KOSPI200QuarterlyLoader) -> None:
    """가장 중요한 dtype 결정: 종목코드 앞 0 보존."""
    tickers = loader.tickers("2015Q1")
    # 삼성전자 005930 — 앞 0이 사라지면 "5930"이 됨
    assert "005930" in tickers
    # 모든 종목코드가 6자리 문자열
    assert all(isinstance(t, str) and len(t) == 6 for t in tickers)


def test_columns_match_expected_schema(loader: KOSPI200QuarterlyLoader) -> None:
    df = loader.composition("2015Q1")
    expected = ["종목코드", "종목명", "종가", "대비", "등락률", "상장시가총액"]
    assert list(df.columns) == expected


# ---- point-in-time 정확성 ------------------------------------------------


def test_caprol_present_in_2015q1(loader: KOSPI200QuarterlyLoader) -> None:
    """카프로(006380)는 2017-12 상장폐지됐으나 2015Q1에는 KOSPI200이었음.

    point-in-time 유니버스가 *현재 시점 시총 상위* 만 사용하는 단순 모델과
    다르게, 분석 기간 내 상폐된 종목까지 정확히 포함함을 확인하는 테스트.
    부실 라벨(D2)의 양성 클래스가 손실되지 않음의 근거.
    """
    tickers = loader.tickers("2015Q1")
    assert "006380" in tickers, "카프로 미포함 — point-in-time 유니버스가 깨짐"


# ---- 룩어헤드 차단 -------------------------------------------------------


def test_as_of_returns_q1_after_q1_end(loader: KOSPI200QuarterlyLoader) -> None:
    """2015-04-15 시점 → 2015Q1 (2015-03-31) 이 적용."""
    assert loader.as_of(date(2015, 4, 15)) == "2015Q1"


def test_as_of_returns_q1_on_exact_q1_end(loader: KOSPI200QuarterlyLoader) -> None:
    """2015-03-31 *당일* 도 적용 가능 (분기말 종가 기준이므로)."""
    assert loader.as_of(date(2015, 3, 31)) == "2015Q1"


def test_as_of_blocks_lookahead(loader: KOSPI200QuarterlyLoader) -> None:
    """2015-03-30 → 사용 가능한 검증 분기 중 t 이전이 없음 → LookupError.

    이게 *룩어헤드 차단의 핵심 증명* 이다. 미래 분기를 절대 반환하지 않는다.
    """
    with pytest.raises(LookupError):
        loader.as_of(date(2015, 3, 30))


# ---- 무결성 검증 (변조 시뮬레이션, tmp_path 격리) -----------------------


def test_sha256_mismatch_raises(tmp_path: Path) -> None:
    """파일이 매니페스트와 다르면 IntegrityError 가 즉시 발생."""
    # 실제 파일을 복사해 격리 환경 구성
    src = PROJECT_ROOT / "data" / "external" / "kospi200_quarterly"
    dst = tmp_path / "data" / "external" / "kospi200_quarterly"
    dst.mkdir(parents=True)
    (dst / "kospi200_2015Q1_20150331.csv").write_bytes(
        (src / "kospi200_2015Q1_20150331.csv").read_bytes() + b"corrupted"
    )
    # 매니페스트 그대로 복사 (sha256은 원본 기준이라 이제 미스매치)
    (dst / "MANIFEST.yaml").write_bytes((src / "MANIFEST.yaml").read_bytes())

    loader = KOSPI200QuarterlyLoader.from_default(project_root=tmp_path)
    with pytest.raises(IntegrityError):
        loader.available_quarters()


# ---- 누락 분기 요청 ------------------------------------------------------


def test_unknown_quarter_raises_keyerror(loader: KOSPI200QuarterlyLoader) -> None:
    with pytest.raises(KeyError):
        loader.composition("1999Q1")


def test_unverified_quarter_raises_manifest_error(loader: KOSPI200QuarterlyLoader) -> None:
    """매니페스트에는 있으나 다운로드되지 않은 분기 직접 호출 시 명확한 에러."""
    with pytest.raises(ManifestError):
        loader.composition("2024Q4")
