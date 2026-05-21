"""KOSPI200 지수 일간 시계열 → 국면 분류 학습 (PROGRESS §5.6).

알고리즘:
1. KOSPI200 지수 (FDR `KS200`) 일간 close 로드 — 2015-01-01 ~ 2024-12-31
2. 3 피처 산출 + rolling z-score (warmup drop)
3. HMM K=3 학습 (Gaussian, full covariance)
4. State labeling 사후 명명 (vol 순)
5. forward-only filtering — 각 시점 alpha
6. 결과 박제 (state 분포·전이 행렬·평균 수익률·변동성·domain 해석)

산출물:
- data/interim/regime/results.yaml — state means·transmat·distribution
- 콘솔 출력 (PROGRESS §5.6.1 박제 입력)
"""

from __future__ import annotations

import contextlib
import logging
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from frr.regime.features import FEATURE_COLUMNS, compute_features, drop_warmup_rows  # noqa: E402
from frr.regime.hmm_classifier import (  # noqa: E402
    forward_filter,
    label_states_by_return_vol,
    train_hmm,
)

with contextlib.suppress(AttributeError, OSError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

logger = logging.getLogger(__name__)
OUTPUT_DIR = PROJECT_ROOT / "data" / "interim" / "regime"
KS200_CACHE = PROJECT_ROOT / "data" / "raw" / "fdr" / "ks200_index.parquet"


def _load_ks200_close(start: date, end: date) -> pd.Series:
    """KOSPI200 지수 일간 close — FDR fetch 또는 캐시 hit."""
    if KS200_CACHE.exists():
        df = pd.read_parquet(KS200_CACHE)
        return df["Close"]

    import FinanceDataReader as fdr

    df = fdr.DataReader("KS200", start.isoformat(), end.isoformat())
    KS200_CACHE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(KS200_CACHE)
    return df["Close"]


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="단계 3 시장 국면 모듈 학습")
    parser.add_argument("--k", type=int, default=3, help="상태 수 (기본 3)")
    args = parser.parse_args(argv)
    k = args.k

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    out_dir = OUTPUT_DIR if k == 3 else OUTPUT_DIR / f"k{k}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== 단계 3 시장 국면 모듈 학습 (HMM K={k}) ===\n")

    # 1. KS200 close 로드
    print("1. KOSPI200 지수 일간 close 로드...")
    close = _load_ks200_close(date(2015, 1, 1), date(2024, 12, 31))
    print(f"   close: {len(close)} obs, {close.index[0]} ~ {close.index[-1]}")

    # 2. 3 피처 산출
    print("\n2. 3 피처 산출 (ret_20d + vol_60d + vol_ratio_20_60)...")
    df = compute_features(close)
    clean = drop_warmup_rows(df)
    print(f"   warmup drop 후 {len(clean)} obs")

    # 3. HMM K 학습
    print(f"\n3. HMM K={k} 학습 (Gaussian, full cov, random_state=42)...")
    model = train_hmm(clean, n_components=k, random_state=42, n_iter=500)
    log_lik = model.score(clean.to_numpy())
    print(f"   converged: {model.monitor_.converged}, log-likelihood: {log_lik:.2f}")

    # 4. State labeling (K=3 만 학술 명명 — 다른 K 는 state_idx 사용)
    print("\n4. State labeling...")
    labels = label_states_by_return_vol(model, FEATURE_COLUMNS)
    for state_k, label in labels.items():
        mean_ret = model.means_[state_k][FEATURE_COLUMNS.index("ret_20d")]
        mean_vol = model.means_[state_k][FEATURE_COLUMNS.index("vol_60d")]
        print(f"   state {state_k} → {label}: mean ret_20d={mean_ret:.3f}, vol_60d={mean_vol:.3f}")

    # 5. Forward-only filtering
    print("\n5. Forward-only filtering (각 시점 alpha)...")
    alpha = forward_filter(model, clean)
    states = alpha.argmax(axis=1)
    named_states = [labels[int(s)] for s in states]

    # 6. State 분포 + 전이 행렬
    from collections import Counter

    state_dist = Counter(named_states)
    print("\n6. State 분포 (forward filter argmax):")
    for label, count in sorted(state_dist.items(), key=lambda x: -x[1]):
        pct = count / len(named_states) * 100
        print(f"   {label}: {count} ({pct:.1f}%)")

    print("\n   전이 행렬 (transmat_):")
    print(f"   {' ':12s}", end="")
    for i in range(k):
        print(f"{labels[i]:>12s}", end="")
    print()
    for i in range(k):
        print(f"   from {labels[i]:7s}", end="")
        for j in range(k):
            print(f"{model.transmat_[i, j]:12.3f}", end="")
        print()

    # 7. Domain 해석 — 2020 코로나 시점 spot-check
    corona_dates = pd.date_range("2020-02-15", "2020-05-15", freq="D")
    corona_mask = clean.index.isin(corona_dates)
    corona_states = [named_states[i] for i in range(len(named_states)) if corona_mask[i]]
    if corona_states:
        corona_dist = Counter(corona_states)
        print("\n7. 2020 코로나 충격 (2020-02-15 ~ 2020-05-15) 국면 분포 spot-check:")
        for label, count in sorted(corona_dist.items(), key=lambda x: -x[1]):
            pct = count / len(corona_states) * 100
            print(f"   {label}: {count} ({pct:.1f}%)")

    # 8. yaml 저장
    summary = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "config": {
            "model": "GaussianHMM",
            "n_components": k,
            "covariance_type": "full",
            "n_iter": 500,
            "random_state": 42,
            "features": FEATURE_COLUMNS,
        },
        "data_summary": {
            "obs_total": len(close),
            "obs_clean": len(clean),
            "period_start": str(close.index[0].date()),
            "period_end": str(close.index[-1].date()),
        },
        "model_summary": {
            "converged": bool(model.monitor_.converged),
            "log_likelihood": float(log_lik),
            "state_labels": {int(state_k): v for state_k, v in labels.items()},
            "means": {int(state_k): model.means_[state_k].tolist() for state_k in range(k)},
            "transmat": model.transmat_.tolist(),
            "startprob": model.startprob_.tolist(),
        },
        "state_distribution": dict(state_dist),
    }
    out_yaml = out_dir / "results.yaml"
    out_yaml.write_text(
        yaml.safe_dump(summary, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    print(f"\n결과 yaml: {out_yaml}")

    # 9. state 시계열 저장 (시각화용)
    state_series = pd.DataFrame(
        {
            "date": clean.index,
            "state_idx": states,
            "state_label": named_states,
        }
    )
    state_series.to_parquet(out_dir / "state_series.parquet")
    print(f"state 시계열: {out_dir / 'state_series.parquet'} ({len(state_series)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
