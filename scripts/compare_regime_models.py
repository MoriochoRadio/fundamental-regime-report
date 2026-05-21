"""HMM vs GMM vs K-Means 비교 + K=2·3·4 BIC·AIC 진단 (PROGRESS §5.6.2).

CLAUDE.md §8.4 박제 — hmmlearn 본 라인 + sklearn GMM·K-Means 비교.

산출물:
- data/interim/regime/comparison_summary.yaml
- 콘솔 출력 (PROGRESS §5.6.2 박제 입력)
"""

from __future__ import annotations

import contextlib
import logging
import sys
from pathlib import Path

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from frr.regime.comparison import compare_k_range, stability_check  # noqa: E402
from frr.regime.features import compute_features, drop_warmup_rows  # noqa: E402

with contextlib.suppress(AttributeError, OSError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

logger = logging.getLogger(__name__)
OUTPUT_DIR = PROJECT_ROOT / "data" / "interim" / "regime"
KS200_CACHE = PROJECT_ROOT / "data" / "raw" / "fdr" / "ks200_index.parquet"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== 단계 3 — HMM vs GMM vs K-Means 비교 + K=2·3·4 진단 ===\n")

    # 1. KS200 로드
    print("1. KOSPI200 지수 일간 close 로드...")
    if not KS200_CACHE.exists():
        import FinanceDataReader as fdr

        df_raw = fdr.DataReader("KS200", "2015-01-01", "2024-12-31")
        KS200_CACHE.parent.mkdir(parents=True, exist_ok=True)
        df_raw.to_parquet(KS200_CACHE)
    close = pd.read_parquet(KS200_CACHE)["Close"]
    print(f"   close: {len(close)} obs, {close.index[0]} ~ {close.index[-1]}")

    # 2. 피처 산출
    print("\n2. 3 피처 산출...")
    df = compute_features(close)
    clean = drop_warmup_rows(df)
    print(f"   clean: {len(clean)} obs")

    # 3. K=2·3·4 비교
    print("\n3. K=2·3·4 × HMM/GMM/K-Means 비교...\n")
    cmp_df = compare_k_range(clean, k_values=(2, 3, 4), random_state=42)
    print(cmp_df.to_string(index=False))

    # 4. K=3 안정성 (시드 변동)
    print("\n\n4. K=3 시드 안정성 검사 (5 seeds)...\n")
    stab_df = stability_check(clean, n_components=3, seeds=(42, 123, 7, 2024, 999))
    print(stab_df.to_string(index=False))

    # 5. BIC·AIC 자동 선택 (HMM·GMM 별)
    print("\n\n5. BIC·AIC 자동 선택 (HMM·GMM):\n")
    for model_name in ("HMM", "GMM"):
        sub = cmp_df[cmp_df["model"] == model_name].copy()
        k_bic = sub.loc[sub["bic"].idxmin(), "K"]
        k_aic = sub.loc[sub["aic"].idxmin(), "K"]
        print(f"   {model_name}: BIC 최소 K={k_bic} / AIC 최소 K={k_aic}")

    # 6. K-Means elbow (inertia)
    print("\n6. K-Means inertia (K 증가에 따라 감소, elbow 찾기):\n")
    km_sub = cmp_df[cmp_df["model"] == "K-Means"].copy()
    print(km_sub[["K", "inertia"]].to_string(index=False))

    # 7. yaml 저장
    summary = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "data_summary": {
            "obs_total": len(close),
            "obs_clean": len(clean),
            "period_start": str(close.index[0].date()),
            "period_end": str(close.index[-1].date()),
        },
        "k_range_comparison": cmp_df.to_dict("records"),
        "stability_k3": stab_df.to_dict("records"),
    }
    out_yaml = OUTPUT_DIR / "comparison_summary.yaml"
    out_yaml.write_text(
        yaml.safe_dump(summary, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    print(f"\n결과 yaml: {out_yaml}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
