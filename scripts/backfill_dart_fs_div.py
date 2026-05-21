"""DART 캐시 meta.yaml 의 fs_div 라벨 백필 CLI (일회성).

D10 OFS fallback 코드 (commit `6962cb7`, 2026-05-19) *이전* 페치된 캐시는
meta.yaml 에 `fs_div` 키가 없다. 본 스크립트는 status 별로 라벨 추가:

- status='ok' → fs_div='CFS' (D10 이전 fetcher 는 CFS only)
- status='notfound' → fs_div='absent' (페치 실패)

이미 fs_div 키 있는 meta 는 skip (idempotent — 반복 실행 안전).
페치 0, 네트워크 0. PROGRESS §5.5.11 후속 fs_div 라벨 백필 작업.

사용 예:
    # 기본 경로 (data/raw/dart/) 백필
    uv run python scripts/backfill_dart_fs_div.py

    # 다른 캐시 디렉토리
    uv run python scripts/backfill_dart_fs_div.py --cache-dir custom/path

코어 로직은 `src/frr/data/dart.py` 의 `backfill_fs_div_label()`.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from frr.data.dart import backfill_fs_div_label


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="DART 캐시 meta.yaml 에 fs_div 라벨 백필 (페치 0).",
    )
    p.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("data/raw/dart"),
        help="DART 캐시 루트 (기본: data/raw/dart)",
    )
    p.add_argument("-v", "--verbose", action="count", default=0, help="-v / -vv 로그 레벨")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    level = (logging.WARNING, logging.INFO, logging.DEBUG)[min(args.verbose, 2)]
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")

    if not args.cache_dir.exists():
        print(f"ERROR: 캐시 디렉토리 없음: {args.cache_dir}", file=sys.stderr)
        return 2

    result = backfill_fs_div_label(args.cache_dir)
    print("DART fs_div 백필 결과:")
    print(f"  updated:           {result['updated']}")
    print(f"    - ok → CFS:      {result['updated_ok']}")
    print(f"    - notfound → absent: {result['updated_notfound']}")
    print(f"  skipped (이미 키): {result['skipped']}")
    print(f"  errors:            {result['errors']}")
    return 1 if result["errors"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
