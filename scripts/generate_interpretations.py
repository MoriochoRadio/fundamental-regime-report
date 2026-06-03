"""LLM 해석 빌드타임 배치 — (ticker, as_of) → 한국어 서술 YAML 생성.

CLAUDE.md §3.4: LLM 호출은 *빌드타임 배치 1회* → YAML 고정 → 서비스 런타임
(대시보드) 호출 0회. 대시보드는 본 산출물(YAML)만 읽는다.

- resume/idempotent: 기존 YAML 은 skip (재실행 시 이어감, 재호출 0).
- throttle: 호출 간 간격 (free 티어 RPM 대응). 503/429 재시도는 GeminiProvider 내장.
- 에러: 항목별 실패는 로그 + 계속 (배치 중단 안 함) + 요약 출력.

실행:
    uv run python scripts/generate_interpretations.py --scope latest --limit 10
    (GEMINI_API_KEY 필요 — .env 또는 환경변수)
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from app import data_loader as dl  # noqa: E402
from app.utils.formatters import classify_risk, format_percent  # noqa: E402
from app.utils.state_mapper import lookup_state_at  # noqa: E402
from frr.llm.gemini import _DEFAULT_MODEL, GeminiProvider  # noqa: E402
from frr.llm.interpretation import generate_interpretation  # noqa: E402

OUT_DIR = _ROOT / "data" / "interim" / "llm_interpretations"


def _targets(scope: str) -> list[tuple[str, pd.Timestamp]]:
    """평가 가능 (ticker, test_as_of) 목록. scope=latest → 종목별 최신 시점만."""
    preds = dl.load_d2_predictions()
    if preds is None or preds.empty:
        return []
    pb = preds[preds["class_weight"] == "balanced"].dropna(subset=["proba"]).copy()
    pb["test_as_of"] = pd.to_datetime(pb["test_as_of"])
    combos = pb[["ticker", "test_as_of"]].drop_duplicates()
    if scope == "latest":
        idx = combos.groupby("ticker")["test_as_of"].idxmax()
        combos = combos.loc[idx]
    pairs = [
        (str(t), pd.Timestamp(a))
        for t, a in zip(combos["ticker"], combos["test_as_of"], strict=True)
    ]
    return sorted(pairs)


def main() -> None:
    ap = argparse.ArgumentParser(description="LLM 해석 빌드타임 배치 생성")
    ap.add_argument("--scope", choices=["latest", "all"], default="latest")
    ap.add_argument("--limit", type=int, default=0, help="0=무제한 (앞에서 N개만)")
    ap.add_argument("--throttle", type=float, default=6.0, help="호출 간 간격(초)")
    ap.add_argument("--model", default=_DEFAULT_MODEL)
    args = ap.parse_args()

    load_dotenv()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    uni = dl.load_universe()
    name_map = dict(zip(uni["ticker"], uni["name"], strict=False))
    preds = dl.load_d2_predictions()
    pb = preds[preds["class_weight"] == "balanced"]
    feats = dl.load_d2_features()
    state_series = dl.load_state_series()

    targets = _targets(args.scope)
    if args.limit:
        targets = targets[: args.limit]

    provider: GeminiProvider | None = None  # lazy — 전부 skip 시 키 불필요
    n_ok = n_skip = n_fail = 0
    for tk, ao in targets:
        ao_str = ao.strftime("%Y-%m-%d")
        path = OUT_DIR / f"{tk}_{ao_str}.yaml"
        if path.exists():
            n_skip += 1
            continue
        try:
            row = pb[(pb["ticker"] == tk) & (pb["test_as_of"] == ao)]
            proba = float(row.iloc[0]["proba"])
            level, _color = classify_risk(proba)
            state = lookup_state_at(ao, state_series)
            fr = feats[(feats["ticker"] == tk) & (feats["as_of"] == ao)]
            ratios: dict[str, float | None] = {}
            if not fr.empty:
                r0 = fr.iloc[0]
                ratios = {
                    k: (round(float(r0[k]), 4) if pd.notna(r0[k]) else None)
                    for k in ("debt_ratio", "current_ratio", "op_margin", "roa")
                }
            if provider is None:
                provider = GeminiProvider(model=args.model)
            result = generate_interpretation(
                provider,
                ticker=tk,
                name=name_map.get(tk, tk),
                as_of=ao_str,
                proba_pct=format_percent(proba, decimal=1),
                risk_level=level,
                state=state or "(없음)",
                ratios=ratios,
                model=args.model,
            )
            path.write_text(
                yaml.safe_dump(result, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            n_ok += 1
            print(f"[OK] {tk} {ao_str}")
            time.sleep(args.throttle)
        except Exception as exc:  # 항목 실패는 로그 + 계속 (배치 중단 금지)
            n_fail += 1
            print(f"[FAIL] {tk} {ao_str}: {type(exc).__name__}: {exc}")
            continue

    print(
        f"\n요약: 생성 {n_ok} · skip {n_skip} · 실패 {n_fail} · "
        f"대상 {len(targets)} (scope={args.scope})"
    )


if __name__ == "__main__":
    main()
