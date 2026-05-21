"""KOSPI200 분기 구성 로더 (point-in-time 유니버스).

데이터 출처: KRX 정보데이터시스템에서 사용자가 수동 다운로드한 분기말
CSV 파일들. 매니페스트(`data/external/kospi200_quarterly/MANIFEST.yaml`)
가 단일 source of truth이며, 본 로더는 *완전히 검증된* 분기만 외부에
노출한다.

설계 원칙:
- **룩어헤드 차단**: `as_of(t)` 는 *t 시점 이후* 의 분기말 데이터를
  절대 사용하지 않는다. 단계 2 룩어헤드 테스트 묶음의 첫 검증 대상.
- **무결성 검증**: 매니페스트의 `sha256` 과 실제 파일의 sha256이 일치
  해야만 그 분기를 "검증됨"으로 간주한다. 변조·손상 즉시 탐지.
- **dtype 보존**: 종목코드는 6자리 문자열이며, 정수로 캐스팅되면 앞 0이
  사라져 DART·pykrx 조회가 통째로 깨진다. read_csv 단계에서 강제.
- **점진 다운로드 친화**: 사용자가 40분기를 한 번에 받지 않을 가능성이
  높다. 매니페스트에 *부분적으로 채워진* 엔트리가 있어도 본 로더는
  완전 엔트리만 노출하며, 미완성 엔트리는 조용히 skip(또는 디버그
  로그)한다.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


class ManifestError(Exception):
    """매니페스트 자체에 문제가 있을 때 (필드 누락·형식 오류 등)."""


class IntegrityError(Exception):
    """파일이 매니페스트의 sha256과 불일치할 때 (변조·손상 의심)."""


@dataclass(frozen=True)
class QuarterEntry:
    """매니페스트의 한 분기 엔트리 (검증 전·후 모두 표현)."""

    quarter: str
    requested_date: date
    actual_reference_date: date | None
    filename: str | None
    downloaded_at: date | None
    sha256: str | None
    encoding: str | None
    notes: str | None

    def is_complete(self) -> bool:
        """파일을 실제로 열어보지 않고 메타만으로 완성 여부 판정."""
        return all(
            x is not None
            for x in (
                self.actual_reference_date,
                self.filename,
                self.downloaded_at,
                self.sha256,
                self.encoding,
            )
        )


class KOSPI200QuarterlyLoader:
    """분기 KOSPI200 구성 CSV 묶음을 매니페스트로부터 안전하게 로드."""

    DEFAULT_REL_DIR = Path("data/external/kospi200_quarterly")
    MANIFEST_FILENAME = "MANIFEST.yaml"

    def __init__(self, data_dir: Path, manifest: dict[str, Any]) -> None:
        self.data_dir = Path(data_dir)
        self._manifest = manifest
        self._entries: dict[str, QuarterEntry] = self._parse_entries(manifest)

    # ---- 생성자 ----------------------------------------------------------

    @classmethod
    def from_default(cls, project_root: Path | None = None) -> KOSPI200QuarterlyLoader:
        """프로젝트 루트 기준 기본 경로에서 로딩."""
        root = Path(project_root) if project_root else Path.cwd()
        data_dir = root / cls.DEFAULT_REL_DIR
        manifest_path = data_dir / cls.MANIFEST_FILENAME
        if not manifest_path.exists():
            raise ManifestError(f"매니페스트가 없음: {manifest_path}")
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
        return cls(data_dir=data_dir, manifest=manifest)

    # ---- 공개 API --------------------------------------------------------

    def available_quarters(self) -> list[str]:
        """완전 검증을 통과한 분기 ID들 (정렬됨)."""
        verified = []
        for q, entry in sorted(self._entries.items()):
            try:
                if self._is_verified(entry):
                    verified.append(q)
            except IntegrityError:
                raise  # 변조는 즉시 표면화
        return verified

    def composition(self, quarter: str) -> pd.DataFrame:
        """주어진 분기의 200개 구성 종목 + 부가 정보 (csv_schema 그대로)."""
        entry = self._require_verified(quarter)
        path = self.data_dir / entry.filename  # type: ignore[arg-type]
        df = pd.read_csv(
            path,
            encoding=entry.encoding,
            dtype={"종목코드": "string"},  # 앞 0 보존 — 가장 중요한 dtype 결정
        )
        return df

    def tickers(self, quarter: str) -> list[str]:
        """주어진 분기의 종목코드 리스트 (6자리 문자열, 앞 0 보존)."""
        return self.composition(quarter)["종목코드"].tolist()

    def as_of(self, t: date) -> str:
        """시점 *t* 에 적용 가능한 *가장 최근* 분기 ID.

        룩어헤드 차단의 핵심: `actual_reference_date > t` 인 분기는
        절대로 반환하지 않는다. 분기말이 비영업일이라 매니페스트의
        `actual_reference_date` 가 비어 있는 경우는 (미래 도입) `calendars`
        모듈로 직전 영업일을 계산해 채울 예정. v1에서는 비어 있는
        엔트리는 검증을 통과하지 못해 `available_quarters()` 에서 자동
        제외된다.
        """
        for q in reversed(self.available_quarters()):
            entry = self._entries[q]
            ref = entry.actual_reference_date
            assert ref is not None  # 완전 검증을 통과했으므로 보장
            if ref <= t:
                return q
        raise LookupError(
            f"{t} 시점 이전의 검증된 KOSPI200 분기 데이터가 없음 "
            "(매니페스트에서 더 이른 분기를 다운로드·검증해야 함)"
        )

    def reference_date(self, quarter: str) -> date:
        """주어진 분기의 권위 있는 기준일자 (holiday fallback 포함).

        매니페스트의 `actual_reference_date` 를 반환. 분기말 자연 종료일이
        비영업일인 경우 사용자가 직전 영업일로 보정한 일자가 박혀 있음
        (13/40 분기, PROGRESS §2). walk-forward grid 의 권위 있는 분기말
        영업일 매핑 제공 — 분기 라벨 → date 변환에서 *추론* 으로 대체하면
        holiday fallback 권위가 깨지므로 본 메서드 사용.
        """
        entry = self._require_verified(quarter)
        assert entry.actual_reference_date is not None  # 완전 검증 통과
        return entry.actual_reference_date

    # ---- 내부 ------------------------------------------------------------

    def _parse_entries(self, manifest: dict[str, Any]) -> dict[str, QuarterEntry]:
        raw_quarters = manifest.get("quarters")
        if not isinstance(raw_quarters, list):
            raise ManifestError("`quarters` 키가 리스트가 아님")
        entries: dict[str, QuarterEntry] = {}
        for i, item in enumerate(raw_quarters):
            if not isinstance(item, dict):
                raise ManifestError(f"quarters[{i}] 가 dict가 아님")
            try:
                entry = QuarterEntry(
                    quarter=str(item["quarter"]),
                    requested_date=_as_date(item["requested_date"]),
                    actual_reference_date=_as_optional_date(item.get("actual_reference_date")),
                    filename=item.get("filename"),
                    downloaded_at=_as_optional_date(item.get("downloaded_at")),
                    sha256=item.get("sha256"),
                    encoding=item.get("encoding"),
                    notes=item.get("notes"),
                )
            except KeyError as e:
                raise ManifestError(f"quarters[{i}] 필수 키 누락: {e}") from e
            if entry.quarter in entries:
                raise ManifestError(f"분기 ID 중복: {entry.quarter}")
            entries[entry.quarter] = entry
        return entries

    def _is_verified(self, entry: QuarterEntry) -> bool:
        """파일 존재·sha256·메타 완전성을 모두 검사. 변조는 IntegrityError."""
        if not entry.is_complete():
            logger.debug("%s: 미완성 엔트리 (필드 누락), skip", entry.quarter)
            return False
        path = self.data_dir / entry.filename  # type: ignore[arg-type]
        if not path.exists():
            logger.warning("%s: 매니페스트는 채워졌으나 파일 없음 (%s). skip", entry.quarter, path)
            return False
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != entry.sha256:
            raise IntegrityError(
                f"{entry.quarter} sha256 불일치 — 파일={actual}, 매니페스트={entry.sha256}"
            )
        return True

    def _require_verified(self, quarter: str) -> QuarterEntry:
        entry = self._entries.get(quarter)
        if entry is None:
            raise KeyError(f"매니페스트에 없는 분기: {quarter}")
        if not self._is_verified(entry):
            raise ManifestError(f"{quarter} 미검증 — 매니페스트 필드가 비었거나 파일이 없음")
        return entry


# ---- 유틸 -----------------------------------------------------------------


def _as_date(v: Any) -> date:
    """YAML이 date를 그대로 주면 통과, 문자열이면 파싱."""
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        return date.fromisoformat(v)
    raise ManifestError(f"날짜로 해석 불가: {v!r}")


def _as_optional_date(v: Any) -> date | None:
    if v is None:
        return None
    return _as_date(v)
