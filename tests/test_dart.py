"""DARTReporter 단위 + 통합 테스트.

단위 테스트:
- `_rcept_no_to_date` 유틸
- 캐시 hit (메타 yaml + parquet 모두 사용)
- 캐시 miss → 페치 + 메타 기록 (stub fetcher)
- `notfound` 상태 (빈 응답) 메타 기록 + 재호출 시 hit
- `available_at(t)` 룩어헤드 차단
- `latest_available(t)` 가장 최근 보고서 선택

통합 테스트 (실 DART API + 실 캘린더):
- 삼성전자 005930 2020년 사업보고서(FY) 페치
- rcept_no 첫 8자 → rcept_dt 변환 확인
- available_from = rcept_dt + 1영업일
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from frr.data.calendars import KRXBusinessCalendar
from frr.data.dart import (
    DARTReporter,
    _rcept_no_to_date,
    backfill_fs_div_label,
)

# ---- 합성 캘린더 fixture ------------------------------------------------


@pytest.fixture
def calendar_2020_2022() -> KRXBusinessCalendar:
    """2020-01-02 ~ 2022-12-30 의 *평일* 합성 캘린더 (휴장일 무시 — 단위 테스트엔 충분)."""
    days = list(pd.bdate_range("2020-01-02", "2022-12-30").date)
    return KRXBusinessCalendar(business_days=days)


def _fake_finstate(rcept_no: str = "20210309000744", n_rows: int = 28) -> pd.DataFrame:
    """OpenDartReader.finstate 응답 모양의 합성 DataFrame."""
    return pd.DataFrame(
        {
            "rcept_no": [rcept_no] * n_rows,
            "reprt_code": ["11011"] * n_rows,
            "bsns_year": ["2020"] * n_rows,
            "corp_code": ["00126380"] * n_rows,
            "stock_code": ["005930"] * n_rows,
            "fs_div": ["CFS"] * n_rows,
            "account_nm": [f"항목{i}" for i in range(n_rows)],
            "thstrm_amount": ["100,000,000"] * n_rows,
            "ord": list(range(n_rows)),
            "currency": ["KRW"] * n_rows,
        }
    )


# ---- _rcept_no_to_date 단위 -------------------------------------------


def test_rcept_no_to_date_basic() -> None:
    assert _rcept_no_to_date("20210309000744") == date(2021, 3, 9)


def test_rcept_no_to_date_just_eight() -> None:
    assert _rcept_no_to_date("20200401") == date(2020, 4, 1)


def test_rcept_no_to_date_too_short() -> None:
    with pytest.raises(ValueError):
        _rcept_no_to_date("2021")


def test_rcept_no_to_date_invalid_calendar() -> None:
    with pytest.raises(ValueError):
        _rcept_no_to_date("20211301000000")  # 13월 없음


# ---- 캐시 miss → 페치 + 메타 기록 -------------------------------------


def test_fetch_writes_parquet_and_meta(
    tmp_path: Path, calendar_2020_2022: KRXBusinessCalendar
) -> None:
    calls: list[tuple[str, int, str]] = []

    def stub(ticker: str, year: int, reprt_code: str) -> pd.DataFrame:
        calls.append((ticker, year, reprt_code))
        return _fake_finstate()

    rep = DARTReporter(
        calendar=calendar_2020_2022,
        project_root=tmp_path,
        fetcher=stub,
    )
    result = rep.fetch_report("005930", 2020, "FY")

    # ref 검증
    assert result.ref.status == "ok"
    assert result.ref.rcept_dt == date(2021, 3, 9)
    # 2021-03-09 (화) 의 다음 영업일 = 2021-03-10 (수)
    assert result.ref.available_from == date(2021, 3, 10)
    # df 검증
    assert len(result.df) == 28

    # 캐시·메타 둘 다 생성
    assert (tmp_path / "data/raw/dart/005930/2020_FY.parquet").exists()
    assert (tmp_path / "data/raw/dart/005930/2020_FY.meta.yaml").exists()
    # 페치는 정확히 1회
    assert calls == [("005930", 2020, "11011")]


# ---- 캐시 hit (재호출 시 네트워크 0) -----------------------------------


def test_second_call_uses_cache(tmp_path: Path, calendar_2020_2022: KRXBusinessCalendar) -> None:
    calls: list[tuple[str, int, str]] = []

    def stub(ticker: str, year: int, reprt_code: str) -> pd.DataFrame:
        calls.append((ticker, year, reprt_code))
        return _fake_finstate()

    rep = DARTReporter(
        calendar=calendar_2020_2022,
        project_root=tmp_path,
        fetcher=stub,
    )
    rep.fetch_report("005930", 2020, "FY")
    rep.fetch_report("005930", 2020, "FY")  # 캐시 hit

    assert len(calls) == 1  # 두 번째는 페치 안 함


# ---- notfound 상태 -----------------------------------------------------


def test_empty_response_records_notfound(
    tmp_path: Path, calendar_2020_2022: KRXBusinessCalendar
) -> None:
    calls: list[tuple[str, int, str]] = []

    def stub_empty(ticker: str, year: int, reprt_code: str) -> pd.DataFrame:
        calls.append((ticker, year, reprt_code))
        return pd.DataFrame()  # DART 응답 없음 시뮬

    rep = DARTReporter(
        calendar=calendar_2020_2022,
        project_root=tmp_path,
        fetcher=stub_empty,
    )
    result = rep.fetch_report("999999", 2020, "Q1")

    assert result.ref.status == "notfound"
    assert result.ref.rcept_dt is None
    assert result.ref.available_from is None
    assert result.df.empty
    # 메타는 생성됨 (재페치 회피용)
    assert (tmp_path / "data/raw/dart/999999/2020_Q1.meta.yaml").exists()
    # 두 번째 호출은 캐시(메타) 히트 → 페치 안 함
    rep.fetch_report("999999", 2020, "Q1")
    assert len(calls) == 1


# ---- 룩어헤드 차단 -----------------------------------------------------


def test_available_at_blocks_future_reports(
    tmp_path: Path, calendar_2020_2022: KRXBusinessCalendar
) -> None:
    """시점 t 이후 available_from 인 보고서는 노출되지 않음."""

    def stub(ticker: str, year: int, reprt_code: str) -> pd.DataFrame:
        # 보고서별 다른 rcept_no:
        # FY 2020 → 2021-03-09 접수 → available_from 2021-03-10
        # Q1 2021 → 2021-05-17 접수 → available_from 2021-05-18
        mapping = {
            "11011": "20210309000744",  # FY 2020
            "11013": "20210517000123",  # Q1 2021
        }
        rno = mapping.get(reprt_code, "20990101000000")
        return _fake_finstate(rcept_no=rno)

    rep = DARTReporter(
        calendar=calendar_2020_2022,
        project_root=tmp_path,
        fetcher=stub,
    )

    # t = 2021-04-01: FY 2020(2021-03-10부터 사용 가능)만 보여야
    refs = rep.available_at("005930", date(2021, 4, 1), years=[2020, 2021])
    available = {(r.year, r.period) for r in refs}
    assert (2020, "FY") in available
    assert (2021, "Q1") not in available  # 아직 available_from(2021-05-18) 이전

    # t = 2021-06-01: 둘 다 사용 가능
    refs = rep.available_at("005930", date(2021, 6, 1), years=[2020, 2021])
    available = {(r.year, r.period) for r in refs}
    assert (2020, "FY") in available
    assert (2021, "Q1") in available


def test_latest_available_picks_most_recent(
    tmp_path: Path, calendar_2020_2022: KRXBusinessCalendar
) -> None:
    def stub(ticker: str, year: int, reprt_code: str) -> pd.DataFrame:
        mapping = {
            "11011": "20210309000744",  # FY 2020
            "11013": "20210517000123",  # Q1 2021
        }
        rno = mapping.get(reprt_code, "20990101000000")
        return _fake_finstate(rcept_no=rno)

    rep = DARTReporter(
        calendar=calendar_2020_2022,
        project_root=tmp_path,
        fetcher=stub,
    )
    result = rep.latest_available("005930", date(2021, 6, 1), years=[2020, 2021])

    assert result is not None
    assert (result.ref.year, result.ref.period) == (2021, "Q1")


def test_latest_available_returns_none_when_no_data(
    tmp_path: Path, calendar_2020_2022: KRXBusinessCalendar
) -> None:
    def stub_future(ticker: str, year: int, reprt_code: str) -> pd.DataFrame:
        # available_from 이 항상 미래
        return _fake_finstate(rcept_no="20990101000000")

    rep = DARTReporter(
        calendar=KRXBusinessCalendar(
            business_days=list(pd.bdate_range("2099-01-01", "2099-12-31").date)
        ),
        project_root=tmp_path,
        fetcher=stub_future,
    )
    result = rep.latest_available("005930", date(2020, 1, 1), years=[2020])
    assert result is None


# ---- 통합 (실 DART API 사용 — DART_API_KEY 환경변수 필요) ---------------


def test_fs_div_cfs_recorded_in_meta(
    tmp_path: Path, calendar_2020_2022: KRXBusinessCalendar
) -> None:
    """D10: fetcher 가 `_fs_div_used='CFS'` 주입 → ref.fs_div='CFS' + yaml 기록."""

    def stub_cfs(ticker: str, year: int, reprt_code: str) -> pd.DataFrame:
        df = _fake_finstate()
        df = df.copy()
        df["_fs_div_used"] = "CFS"
        return df

    rep = DARTReporter(calendar=calendar_2020_2022, project_root=tmp_path, fetcher=stub_cfs)
    result = rep.fetch_report("005930", 2020, "FY")

    assert result.ref.status == "ok"
    assert result.ref.fs_div == "CFS"
    # 본문 parquet 에는 _fs_div_used 컬럼이 *없어야* (drop 됨)
    assert "_fs_div_used" not in result.df.columns
    # 메타 yaml 에 fs_div 기록
    import yaml as _yaml

    meta = _yaml.safe_load((tmp_path / "data/raw/dart/005930/2020_FY.meta.yaml").read_text("utf-8"))
    assert meta.get("fs_div") == "CFS"


def test_fs_div_ofs_fallback_recorded(
    tmp_path: Path, calendar_2020_2022: KRXBusinessCalendar
) -> None:
    """D10: fetcher 가 OFS 만 반환 (CFS 빈 모방)."""

    def stub_ofs(ticker: str, year: int, reprt_code: str) -> pd.DataFrame:
        df = _fake_finstate()
        df = df.copy()
        df["_fs_div_used"] = "OFS"
        return df

    rep = DARTReporter(calendar=calendar_2020_2022, project_root=tmp_path, fetcher=stub_ofs)
    result = rep.fetch_report("999999", 2020, "FY")

    assert result.ref.status == "ok"
    assert result.ref.fs_div == "OFS"


def test_fs_div_notfound_has_none(tmp_path: Path, calendar_2020_2022: KRXBusinessCalendar) -> None:
    """D10: 빈 응답 (CFS·OFS 둘 다 빈) → fs_div=None."""

    def stub_empty(ticker: str, year: int, reprt_code: str) -> pd.DataFrame:
        return pd.DataFrame()

    rep = DARTReporter(calendar=calendar_2020_2022, project_root=tmp_path, fetcher=stub_empty)
    result = rep.fetch_report("999999", 2020, "FY")

    assert result.ref.status == "notfound"
    assert result.ref.fs_div is None


def test_legacy_meta_without_fs_div_loads_as_none(
    tmp_path: Path, calendar_2020_2022: KRXBusinessCalendar
) -> None:
    """D10: 기존 캐시 (fs_div 키 부재) 로드 시 None 으로 처리 (호환성)."""
    # 합성 레거시 캐시 — 파일 직접 작성
    cache_dir = tmp_path / "data" / "raw" / "dart" / "005930"
    cache_dir.mkdir(parents=True)
    legacy_meta = {
        "ticker": "005930",
        "year": 2020,
        "period": "FY",
        "status": "ok",
        "rcept_dt": "2021-03-09",
        "available_from": "2021-03-10",
        "fetched_at": "2025-01-01",
        # fs_div 키 부재 — 레거시
    }
    import yaml as _yaml

    (cache_dir / "2020_FY.meta.yaml").write_text(_yaml.safe_dump(legacy_meta), "utf-8")
    _fake_finstate().to_parquet(cache_dir / "2020_FY.parquet")

    rep = DARTReporter(
        calendar=calendar_2020_2022, project_root=tmp_path, fetcher=lambda *a: pd.DataFrame()
    )
    result = rep.fetch_report("005930", 2020, "FY")

    assert result.ref.status == "ok"
    assert result.ref.fs_div is None  # 레거시 호환


@pytest.mark.integration
def test_fetch_samsung_2020_fy_real(tmp_path: Path) -> None:
    """실 DART API로 005930 2020 사업보고서 페치."""
    import os

    from dotenv import load_dotenv

    load_dotenv()
    if not os.environ.get("DART_API_KEY"):
        pytest.skip("DART_API_KEY 미설정 — 통합 테스트 skip")

    # 실 캘린더 (2020-2022 범위, 캐시 또는 FDR fetch)
    cal = KRXBusinessCalendar.from_cache_or_fetch(
        date(2020, 1, 1), date(2022, 12, 31), project_root=tmp_path
    )

    rep = DARTReporter(calendar=cal, project_root=tmp_path)
    result = rep.fetch_report("005930", 2020, "FY")

    assert result.ref.status == "ok"
    assert isinstance(result.ref.rcept_dt, date)
    assert result.ref.available_from is not None
    assert result.ref.available_from > result.ref.rcept_dt
    assert len(result.df) >= 10  # 주요 계정 정도는 들어있음
    assert "rcept_no" in result.df.columns
    assert "account_nm" in result.df.columns
    # 캐시·메타 생성
    assert (tmp_path / "data/raw/dart/005930/2020_FY.parquet").exists()
    assert (tmp_path / "data/raw/dart/005930/2020_FY.meta.yaml").exists()


# ---- backfill_fs_div_label 단위 테스트 -----------------------------------


def _write_meta(path: Path, data: dict) -> None:
    """헬퍼: 합성 meta.yaml 작성."""
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")


def test_backfill_fs_div_label_adds_cfs_and_absent(tmp_path: Path) -> None:
    """ok → CFS, notfound → absent, 이미 키 있으면 skip.

    합성 4 meta: ok 2 (CFS 추가) + notfound 1 (absent 추가) + fs_div='OFS' 1 (skip).
    페치 0 — 네트워크 의존성 없음 (단위 테스트 충분).
    """
    cache = tmp_path / "dart"
    # ok 2 (fs_div 키 부재)
    _write_meta(
        cache / "005930" / "2020_FY.meta.yaml",
        {
            "ticker": "005930",
            "year": 2020,
            "period": "FY",
            "status": "ok",
            "rcept_dt": "2021-03-09",
            "available_from": "2021-03-10",
            "fetched_at": "2026-05-18",
        },
    )
    _write_meta(
        cache / "005930" / "2020_Q1.meta.yaml",
        {
            "ticker": "005930",
            "year": 2020,
            "period": "Q1",
            "status": "ok",
            "rcept_dt": "2020-05-15",
            "available_from": "2020-05-18",
            "fetched_at": "2026-05-18",
        },
    )
    # notfound 1 (fs_div 키 부재)
    _write_meta(
        cache / "000030" / "2019_FY.meta.yaml",
        {
            "ticker": "000030",
            "year": 2019,
            "period": "FY",
            "status": "notfound",
            "rcept_dt": None,
            "available_from": None,
            "fetched_at": "2026-05-18",
        },
    )
    # 이미 fs_div='OFS' (skip 검증용)
    _write_meta(
        cache / "267250" / "2022_FY.meta.yaml",
        {
            "ticker": "267250",
            "year": 2022,
            "period": "FY",
            "status": "ok",
            "rcept_dt": "2023-03-15",
            "available_from": "2023-03-16",
            "fs_div": "OFS",
            "fetched_at": "2026-05-19",
        },
    )

    result = backfill_fs_div_label(cache)

    assert result == {
        "updated": 3,
        "updated_ok": 2,
        "updated_notfound": 1,
        "skipped": 1,
        "errors": 0,
    }

    # 라벨 검증
    import yaml

    fy_data = yaml.safe_load((cache / "005930" / "2020_FY.meta.yaml").read_text(encoding="utf-8"))
    assert fy_data["fs_div"] == "CFS"
    nf_data = yaml.safe_load((cache / "000030" / "2019_FY.meta.yaml").read_text(encoding="utf-8"))
    assert nf_data["fs_div"] == "absent"
    ofs_data = yaml.safe_load((cache / "267250" / "2022_FY.meta.yaml").read_text(encoding="utf-8"))
    assert ofs_data["fs_div"] == "OFS"  # skip 으로 변경 없음


def test_backfill_fs_div_label_idempotent(tmp_path: Path) -> None:
    """2회 실행 시 두 번째는 updated=0, skipped=N (idempotent)."""
    cache = tmp_path / "dart"
    _write_meta(
        cache / "005930" / "2020_FY.meta.yaml",
        {
            "ticker": "005930",
            "year": 2020,
            "period": "FY",
            "status": "ok",
            "rcept_dt": "2021-03-09",
            "available_from": "2021-03-10",
            "fetched_at": "2026-05-18",
        },
    )
    _write_meta(
        cache / "000030" / "2019_FY.meta.yaml",
        {
            "ticker": "000030",
            "year": 2019,
            "period": "FY",
            "status": "notfound",
            "rcept_dt": None,
            "available_from": None,
            "fetched_at": "2026-05-18",
        },
    )

    first = backfill_fs_div_label(cache)
    assert first["updated"] == 2 and first["skipped"] == 0

    second = backfill_fs_div_label(cache)
    assert second["updated"] == 0 and second["skipped"] == 2 and second["errors"] == 0
