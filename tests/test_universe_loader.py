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


def test_unfilled_quarters_are_hidden(tmp_path: Path) -> None:
    """매니페스트에 빈 엔트리가 있으면 그 분기는 available에서 자동 제외.

    실제 매니페스트의 채움 상태에 의존하지 않도록 tmp_path 격리.
    합성 매니페스트: 채워진 1분기 + 비어 있는 1분기.
    """
    # 실제 2015Q1 파일과 매니페스트 엔트리를 복사해 격리 환경 구성
    src_dir = PROJECT_ROOT / "data" / "external" / "kospi200_quarterly"
    dst_dir = tmp_path / "data" / "external" / "kospi200_quarterly"
    dst_dir.mkdir(parents=True)
    csv_name = "kospi200_2015Q1_20150331.csv"
    (dst_dir / csv_name).write_bytes((src_dir / csv_name).read_bytes())

    # 실제 매니페스트에서 2015Q1 엔트리만 추출해 합성 매니페스트 구성
    import yaml

    real = yaml.safe_load((src_dir / "MANIFEST.yaml").read_text(encoding="utf-8"))
    q1_entry = next(q for q in real["quarters"] if q["quarter"] == "2015Q1")
    empty_entry = {
        "quarter": "2015Q2",
        "requested_date": "2015-06-30",
        "actual_reference_date": None,
        "filename": None,
        "downloaded_at": None,
        "sha256": None,
        "encoding": None,
        "notes": None,
    }
    synthetic = {
        "source_system": real.get("source_system"),
        "index_code": real.get("index_code"),
        "quarters": [q1_entry, empty_entry],
    }
    (dst_dir / "MANIFEST.yaml").write_text(yaml.safe_dump(synthetic), encoding="utf-8")

    loader = KOSPI200QuarterlyLoader.from_default(project_root=tmp_path)
    available = loader.available_quarters()
    assert "2015Q1" in available
    assert "2015Q2" not in available  # 비어 있어 hidden


# ---- CSV 파싱 / dtype 보존 ------------------------------------------------


def test_composition_2015q1_row_count_within_bounds(loader: KOSPI200QuarterlyLoader) -> None:
    """KOSPI200은 *목표 200종목*이지만 리밸런싱 직후 일시 201/202종목 가능.

    사용자 보고(2026-05-18): 실제 다운로드 결과 데이터 행 수가 200~202의
    범위를 가지며, 인덱스 리밸런싱 시점 직후 일시적으로 증가하는 양상.
    따라서 정확히 200이 아니라 [200, 202] 범위로 검증.
    """
    df = loader.composition("2015Q1")
    assert 200 <= len(df) <= 202, f"KOSPI200 행 수 범위 [200,202] 밖: {len(df)}"


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


# ---- 분기 라벨 → 기준일자 매핑 (walk-forward grid 추출 권위) ------------


def test_reference_date_returns_actual_with_holiday_fallback(
    loader: KOSPI200QuarterlyLoader,
) -> None:
    """reference_date(quarter) 가 매니페스트의 actual_reference_date 반환.

    2015Q1 자연 종료일 2015-03-31 (영업일) → 그대로 반환. 비영업일 분기말은
    사용자가 직전 영업일로 보정한 일자가 박혀 있음 — walk-forward grid 권위.
    """
    assert loader.reference_date("2015Q1") == date(2015, 3, 31)


def test_reference_date_unknown_quarter_raises(loader: KOSPI200QuarterlyLoader) -> None:
    """매니페스트에 없는 분기는 KeyError."""
    with pytest.raises(KeyError):
        loader.reference_date("1999Q1")


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


def test_unverified_quarter_raises_manifest_error(tmp_path: Path) -> None:
    """매니페스트에는 있으나 채워지지 않은 분기를 직접 호출하면 명확한 에러.

    실제 매니페스트가 모두 채워진 상태에서도 동작하도록 tmp_path 격리.
    """
    dst_dir = tmp_path / "data" / "external" / "kospi200_quarterly"
    dst_dir.mkdir(parents=True)
    # 빈 엔트리 하나만 있는 합성 매니페스트
    import yaml

    synthetic = {
        "source_system": "synthetic",
        "index_code": "1028",
        "quarters": [
            {
                "quarter": "2099Q4",
                "requested_date": "2099-12-31",
                "actual_reference_date": None,
                "filename": None,
                "downloaded_at": None,
                "sha256": None,
                "encoding": None,
                "notes": None,
            },
        ],
    }
    (dst_dir / "MANIFEST.yaml").write_text(yaml.safe_dump(synthetic), encoding="utf-8")

    loader = KOSPI200QuarterlyLoader.from_default(project_root=tmp_path)
    with pytest.raises(ManifestError):
        loader.composition("2099Q4")
