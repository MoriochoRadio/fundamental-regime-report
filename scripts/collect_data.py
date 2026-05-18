"""배치 데이터 수집 CLI 진입점.

분석 유니버스 전체 종목에 대해 KRX OHLCV + DART 정기보고서 + FDR 메타
를 수집해 어댑터 캐시에 저장한다.

사용 예:
    # 전체 수집 (수십 분 ~ 1시간 + 소요. DART 한도·KRX 스크래핑 속도 의존)
    uv run python scripts/collect_data.py

    # 개발용 — 첫 5개 종목만
    uv run python scripts/collect_data.py --limit 5

    # 특정 종목만
    uv run python scripts/collect_data.py --tickers 005930,000660

    # DART 만 건너뛰기 (KRX·FDR 만)
    uv run python scripts/collect_data.py --skip-dart

코어 로직은 `src/frr/data/collect.py` 의 `collect_universe()` 이며,
본 스크립트는 argparse + 로깅 + 종료 코드만 담당한다.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from frr.data.collect import collect_universe

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="FRR 데이터 배치 수집 (KRX/DART/FDR → 어댑터 캐시)")
    p.add_argument(
        "--config",
        type=Path,
        default=Path("configs/data.yaml"),
        help="config 파일 경로 (기본: configs/data.yaml)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        help="처음 N개 종목만 수집 (개발용)",
    )
    p.add_argument(
        "--tickers",
        type=str,
        default=None,
        help="쉼표 구분 종목코드 (예: '005930,000660'). 미지정 시 전체 유니버스.",
    )
    p.add_argument("--skip-krx", action="store_true", help="pykrx OHLCV 건너뛰기")
    p.add_argument("--skip-dart", action="store_true", help="DART 정기보고서 건너뛰기")
    p.add_argument("--skip-fdr", action="store_true", help="FDR listing/delisting 건너뛰기")
    p.add_argument(
        "--summary-path",
        type=Path,
        default=None,
        help="요약 yaml 저장 경로 (기본: data/raw/collect_summary.yaml + 타임스탬프 백업)",
    )
    p.add_argument(
        "--no-summary-file",
        action="store_true",
        help="요약 파일 저장 비활성 (콘솔 출력만)",
    )
    p.add_argument("--verbose", "-v", action="store_true", help="로그 레벨 INFO → DEBUG")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    ticker_filter = None
    if args.tickers:
        ticker_filter = [t.strip() for t in args.tickers.split(",") if t.strip()]

    summary = collect_universe(
        config_path=args.config,
        limit=args.limit,
        ticker_filter=ticker_filter,
        skip_krx=args.skip_krx,
        skip_dart=args.skip_dart,
        skip_fdr=args.skip_fdr,
        summary_path=args.summary_path,
        write_summary_file=not args.no_summary_file,
    )

    print()
    print("=" * 60)
    print("Collection Summary")
    print("=" * 60)
    print(f"  tickers: {summary.n_tickers}")
    print(f"  krx ok: {summary.n_krx_ok}")
    print(f"  dart ok: {summary.n_dart_ok}")
    print(f"  dart notfound: {summary.n_dart_notfound}")
    print(f"  fdr listing: {'OK' if summary.fdr_listing_ok else 'SKIP/FAIL'}")
    print(f"  fdr delisting: {'OK' if summary.fdr_delisting_ok else 'SKIP/FAIL'}")
    print(f"  failures: {len(summary.failures)}")
    for f in summary.failures[:20]:
        print(f"    - {f.ticker} [{f.stage}] {f.detail[:80]}")
    if len(summary.failures) > 20:
        print(f"    ... ({len(summary.failures) - 20} more)")

    return 0 if not summary.failures else 1


if __name__ == "__main__":
    sys.exit(main())
