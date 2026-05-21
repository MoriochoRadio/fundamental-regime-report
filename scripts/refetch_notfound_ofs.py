"""(A) notfound 2,719 OFS 재페치 — 데이터 보강 시도 (§5.5.17 후속).

PROGRESS §5.5.17 향후 방향 (C) — D10 OFS fallback 효과 측정. notfound 2,719
캐시 (D10 적용 *이전* CFS only fetcher 응답) 를 *D10 fetcher* (CFS 우선 +
OFS fallback) 로 재페치.

기대치:
- notfound 중 일부 (10-20% 추정) 가 *OFS 로는 존재* → status 'ok' 전환
- 양성 cells 증가 → 모델 학습 재시도 가치

설계 결정:
- 기존 캐시 *덮어쓰기* (refresh=True). 단 *status='notfound' meta 만* 명시
  대상 — status='ok' 캐시는 영향 0.
- DART 한도: ≤2,719 호출 (한도 ~27%). 1 세션 내 가능.
- 시간 추정: ~1-2 시간 (재페치 호출 자체 시간).

결과:
- status 변화 카운트 (ok 전환 수)
- fs_div 분포 (OFS / CFS / absent)
- yaml 저장
- 이후 backfill_fs_div_label 재실행 + labels 재산출 + 재학습 별도 결정.
"""

from __future__ import annotations

import contextlib
import logging
import sys
import time
from datetime import date
from pathlib import Path

import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from frr.data.calendars import KRXBusinessCalendar  # noqa: E402
from frr.data.dart import DARTReporter  # noqa: E402

with contextlib.suppress(AttributeError, OSError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

logger = logging.getLogger(__name__)
CACHE_DIR = PROJECT_ROOT / "data" / "raw" / "dart"
OUTPUT_DIR = PROJECT_ROOT / "data" / "interim" / "refetch_notfound_ofs"


def _find_notfound_targets() -> list[tuple[str, int, str]]:
    """캐시 walk — status='notfound' meta 의 (ticker, year, period) 리스트."""
    targets = []
    for meta_path in CACHE_DIR.glob("*/*.meta.yaml"):
        try:
            m = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(m, dict) or m.get("status") != "notfound":
            continue
        ticker = meta_path.parent.name
        stem = meta_path.name.replace(".meta.yaml", "")
        # stem 형식: "{year}_{period}" 예: "2020_FY", "2020_Q1"
        if "_" not in stem:
            continue
        year_str, period = stem.split("_", 1)
        try:
            year = int(year_str)
        except ValueError:
            continue
        targets.append((ticker, year, period))
    return targets


def main() -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    load_dotenv()

    import os

    if not os.environ.get("DART_API_KEY"):
        print("ERROR: DART_API_KEY 미설정", file=sys.stderr)
        return 2

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== (A) notfound OFS 재페치 (PROGRESS §5.5.17 (C) 데이터 보강) ===\n")

    # 1. notfound 대상 식별
    print("1. notfound 대상 식별...")
    targets = _find_notfound_targets()
    print(f"   notfound meta: {len(targets)}")

    if not targets:
        print("notfound 0건 — 작업 종료.")
        return 0

    # 2. 인프라
    print("\n2. 인프라 로드...")
    calendar = KRXBusinessCalendar.from_cache_or_fetch(
        date(2015, 1, 1), date(2025, 12, 31), project_root=PROJECT_ROOT
    )
    reporter = DARTReporter(calendar=calendar, project_root=PROJECT_ROOT)

    # 3. 재페치 (refresh=True, D10 fetcher 가 CFS+OFS 자동 시도)
    eta_min = len(targets) * 0.5 / 60
    eta_max = len(targets) * 2 / 60
    print(f"\n3. 재페치 진행 (시간 추정 {eta_min:.0f}~{eta_max:.0f}분)...")
    status_changed = 0
    errors = 0
    fs_div_new: dict[str, int] = {"CFS": 0, "OFS": 0, "None": 0}
    progress_interval = max(1, len(targets) // 20)
    t0 = time.time()

    for i, (ticker, year, period) in enumerate(targets, start=1):
        if i % progress_interval == 0 or i == len(targets):
            elapsed = time.time() - t0
            print(
                f"   [{i}/{len(targets)}] elapsed {elapsed:.0f}s "
                f"changed={status_changed} errors={errors}",
                flush=True,
            )
        try:
            result = reporter.fetch_report(ticker, year, period, refresh=True)  # type: ignore[arg-type]
            if result.ref.status == "ok":
                status_changed += 1
                fs_div = result.ref.fs_div or "None"
                fs_div_new[fs_div] = fs_div_new.get(fs_div, 0) + 1
        except Exception as e:
            errors += 1
            logger.warning("fetch 실패 %s/%d/%s: %s", ticker, year, period, e)

    elapsed = time.time() - t0
    print(f"\n4. 완료 — 총 {len(targets)} 호출 / {elapsed:.0f}s")
    print(f"   status notfound → ok 전환: {status_changed}")
    print(f"   여전히 notfound: {len(targets) - status_changed - errors}")
    print(f"   errors: {errors}")
    print(f"   fs_div 분포 (전환된 것): {fs_div_new}")

    # 5. yaml 저장
    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_targets": len(targets),
        "status_changed_to_ok": status_changed,
        "still_notfound": len(targets) - status_changed - errors,
        "errors": errors,
        "fs_div_distribution_of_changed": fs_div_new,
        "elapsed_seconds": int(elapsed),
        "dart_call_count": len(targets),
    }
    out_yaml = OUTPUT_DIR / "summary.yaml"
    out_yaml.write_text(yaml.safe_dump(summary, allow_unicode=True), encoding="utf-8")
    print(f"\nsummary yaml: {out_yaml}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
