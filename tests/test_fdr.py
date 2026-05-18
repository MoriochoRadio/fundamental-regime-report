"""FDR 어댑터 단위 + 통합 테스트.

단위 테스트는 외부 의존성 없이 `_normalize_dtypes` + 캐시 hit 경로를
검증한다. 통합 테스트는 실제 FDR fetch 후 캐시 생성을 1개 검증한다.

격리 원칙은 *단계 2 진입 시* 별도 격리 테스트(`tests/test_*_isolation.py`)
에서 검증할 예정. 본 파일은 *어댑터 자체의 동작* 만 검증한다.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from frr.data.fdr import FDRDataSource, _normalize_dtypes

# ---- _normalize_dtypes 단위 테스트 ---------------------------------------


def test_normalize_keeps_code_leading_zeros() -> None:
    raw = pd.DataFrame({"Code": [5930, 660, 35720], "Name": ["a", "b", "c"]})
    out = _normalize_dtypes(raw)
    assert out["Code"].tolist() == ["005930", "000660", "035720"]


def test_normalize_keeps_symbol_leading_zeros() -> None:
    """상장폐지 테이블은 'Symbol' 컬럼명을 쓴다."""
    raw = pd.DataFrame({"Symbol": ["6380", "28740"], "Name": ["카프로", "경성전기"]})
    out = _normalize_dtypes(raw)
    assert out["Symbol"].tolist() == ["006380", "028740"]


def test_normalize_strips_float_dot_zero() -> None:
    """일부 출처가 종목코드를 float로 주는 경우 (예: 5930.0)."""
    raw = pd.DataFrame({"Code": ["5930.0", "6380.0"], "Name": ["a", "b"]})
    out = _normalize_dtypes(raw)
    assert out["Code"].tolist() == ["005930", "006380"]


def test_normalize_dates_to_datetime() -> None:
    raw = pd.DataFrame(
        {
            "Symbol": ["006380"],
            "ListingDate": ["1976-08-02"],
            "DelistingDate": ["2017-12-29"],
            "ArrantEnforceDate": [None],
            "ArrantEndDate": [None],
        }
    )
    out = _normalize_dtypes(raw)
    assert pd.api.types.is_datetime64_any_dtype(out["ListingDate"])
    assert pd.api.types.is_datetime64_any_dtype(out["DelistingDate"])
    assert out.loc[0, "DelistingDate"].year == 2017


def test_normalize_handles_missing_optional_columns() -> None:
    """모든 종목코드·날짜 컬럼이 있을 필요 없음."""
    raw = pd.DataFrame({"Name": ["x"], "Marcap": [100]})
    out = _normalize_dtypes(raw)
    assert "Code" not in out.columns
    assert "Name" in out.columns


# ---- 캐시 hit 경로 (네트워크 없이) ---------------------------------------


def test_listing_uses_cache_when_present(tmp_path: Path) -> None:
    src = FDRDataSource(project_root=tmp_path)
    # 합성 캐시 미리 두기
    cache = src.cache_dir / "stocklisting_kospi.parquet"
    cache.parent.mkdir(parents=True, exist_ok=True)
    synthetic = pd.DataFrame({"Code": ["005930"], "Name": ["삼성전자"], "Marcap": [1]})
    synthetic.to_parquet(cache)

    out = src.listing()  # 캐시 hit → 네트워크 호출 없음
    assert out["Code"].tolist() == ["005930"]
    assert out["Name"].tolist() == ["삼성전자"]


def test_delisting_uses_cache_when_present(tmp_path: Path) -> None:
    src = FDRDataSource(project_root=tmp_path)
    cache = src.cache_dir / "stocklisting_delisting.parquet"
    cache.parent.mkdir(parents=True, exist_ok=True)
    synthetic = pd.DataFrame(
        {"Symbol": ["006380"], "Name": ["카프로"], "DelistingDate": pd.to_datetime(["2017-12-29"])}
    )
    synthetic.to_parquet(cache)

    out = src.delisting()
    assert out["Symbol"].tolist() == ["006380"]
    assert out.loc[0, "DelistingDate"].year == 2017


# ---- 통합 테스트 (실제 FDR fetch, 네트워크 필요) -------------------------


def test_listing_fetch_real(tmp_path: Path) -> None:
    """실제 FDR로 KOSPI 전종목을 받아 dtype 정규화 결과를 확인."""
    src = FDRDataSource(project_root=tmp_path)
    df = src.listing()
    assert len(df) >= 800, f"KOSPI 종목 수 too small: {len(df)}"
    assert "Code" in df.columns
    # 종목코드는 6자리 문자열
    sample = df["Code"].iloc[0]
    assert isinstance(sample, str) and len(sample) == 6


def test_delisting_fetch_real_has_kospi_ordinary_2015_2024(tmp_path: Path) -> None:
    """실제 FDR 상폐 데이터에 *KOSPI 일반 종목(6자리)* 2015-2024 폐지가 다수 존재.

    참고 — 2026-05-18 진단으로 발견된 한계:
    - FDR KRX-DELISTING(4128건)은 상당수가 신주인수권·우선주 등
      *부산물 종목* (8자리 코드, "...2R" 류 이름).
    - 일부 *진짜* 부실 상장폐지(예: 카프로 006380)는 *FDR 데이터에 누락*.
    → 단계 2 D2 라벨 정의 시 출처 보강 필요 (별도 결정).

    본 테스트는 어댑터 *동작 검증* 목적이므로 *최소한 KOSPI 일반 종목
    상폐가 충분히 존재*함만 확인 (D2 라벨 정의의 *원천 후보* 가 있음).
    """
    src = FDRDataSource(project_root=tmp_path)
    df = src.delisting()
    is_kospi_ordinary = (
        (df["Market"] == "KOSPI")
        & (df["Symbol"].astype(str).str.len() == 6)
    )
    years = df["DelistingDate"].dt.year
    is_in_range = (years >= 2015) & (years <= 2024)
    candidates = df[is_kospi_ordinary & is_in_range]
    assert len(candidates) >= 30, (
        f"KOSPI 일반 종목 2015-2024 상폐 후보가 너무 적음: {len(candidates)}"
    )


def test_listing_writes_cache(tmp_path: Path) -> None:
    """첫 fetch 후 캐시 파일이 생성되어야."""
    src = FDRDataSource(project_root=tmp_path)
    assert not (src.cache_dir / "stocklisting_kospi.parquet").exists()
    src.listing()
    assert (src.cache_dir / "stocklisting_kospi.parquet").exists()


@pytest.mark.skip(reason="명시적 refresh 검증 — 시간 절약 위해 기본 skip")
def test_refresh_rewrites_cache(tmp_path: Path) -> None:
    src = FDRDataSource(project_root=tmp_path)
    src.listing()
    cache = src.cache_dir / "stocklisting_kospi.parquet"
    mtime_before = cache.stat().st_mtime
    src.listing(refresh=True)
    mtime_after = cache.stat().st_mtime
    assert mtime_after > mtime_before
