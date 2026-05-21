"""B-4 walk-forward 통합 학습 실행 (PROGRESS §5.5.16).

알고리즘:
1. 양성 사건 산출 (find_distress_events) → 양성 20 종목
2. walk-forward folds 생성 (walk_forward_expanding, 28 folds)
3. 각 fold 별:
   - test_as_of 시점의 universe 멤버 features 산출 (build_features)
   - test 라벨 산출 (build_labels)
   - 단, train 데이터는 fold 의 train_start ~ train_end 의 *모든 분기말* (ticker × as_of)
     features + 라벨을 모은 것
4. 0년 fold (양성 0) skip + 카운터
5. 각 fold 별 balanced + unweighted 학습 → test 예측
6. 모든 fold 예측 pooled → 종목 단위 (ticker × as_of) 평가
7. 지주 군별 분리 평가
8. 결과 yaml 저장 + 콘솔 출력 (B-4 보고)

설계 결정 (§5.5.16 B-2 + 게이트 메모):
- 종목 단위 (ticker × as_of) pooled 평가 (fold 단위 보조)
- balanced + unweighted ablation
- bootstrap_n=1000 활성 (B-4, §5.5.16 짚을 점 1)
- 0년 fold skip + "fold 수 28 → N" 명시
- 지주 군 (034730·267250·096770) 평가 분리 (학습은 통합)

산출물:
- data/interim/train_d2_baseline/results.yaml (gitignore)
- 콘솔 출력 (PROGRESS §5.5.17 박제 입력)
"""

from __future__ import annotations

import contextlib
import logging
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from frr.data.calendars import KRXBusinessCalendar  # noqa: E402
from frr.data.dart import DARTReporter  # noqa: E402
from frr.data.fdr import FDRDataSource  # noqa: E402
from frr.data.universe_loader import KOSPI200QuarterlyLoader  # noqa: E402
from frr.eval.splits import _quarter_end_grid, walk_forward_expanding  # noqa: E402
from frr.features.baseline import build_features  # noqa: E402
from frr.labels import build_labels, find_distress_events  # noqa: E402
from frr.models.classifier import predict_proba, train_classifier  # noqa: E402
from frr.models.evaluation import evaluate_predictions  # noqa: E402

with contextlib.suppress(AttributeError, OSError):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]

logger = logging.getLogger(__name__)

# B-1 명시 지주 (PROGRESS §5.5.15)
HOLDING_TICKERS = frozenset({"034730", "267250", "096770"})

OUTPUT_DIR = PROJECT_ROOT / "data" / "interim" / "train_d2_baseline"
KRX_OHLCV_DIR = PROJECT_ROOT / "data" / "raw" / "krx" / "ohlcv"
DART_FINSTATE_DIR = PROJECT_ROOT / "data" / "raw" / "dart"
FDR_DELIST_PATH = PROJECT_ROOT / "data" / "raw" / "fdr" / "stocklisting_delisting.parquet"


def _build_features_for_grid(
    grid: list[date],
    universe_loader: KOSPI200QuarterlyLoader,
    reporter: DARTReporter,
) -> pd.DataFrame:
    """모든 (ticker × as_of) 의 features 산출. NaN row 도 포함."""
    rows = []
    for as_of in grid:
        try:
            quarter = universe_loader.as_of(as_of)
        except LookupError:
            continue
        tickers = universe_loader.tickers(quarter)
        for ticker in tickers:
            try:
                feat = build_features(
                    ticker=ticker,
                    as_of=as_of,
                    reporter=reporter,
                    universe_loader=universe_loader,
                    krx_ohlcv_cache_dir=KRX_OHLCV_DIR,
                )
                rows.append(feat.iloc[0].to_dict())
            except Exception as e:
                logger.warning("features 실패 %s/%s: %s", ticker, as_of, e)
    return pd.DataFrame(rows)


def _prepare_xy(
    df: pd.DataFrame,
    feature_cols: list[str],
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """X (numeric features), y (label), info (ticker)."""
    X = df[feature_cols].fillna(0.0)
    y = df["label"].astype(int)
    info = df["ticker"]
    return X, y, info


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    load_dotenv()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== B-4 walk-forward 통합 학습 실행 ===\n")

    # 1. 인프라
    print("1. 인프라 로드...")
    calendar = KRXBusinessCalendar.from_cache_or_fetch(
        date(2015, 1, 1), date(2025, 12, 31), project_root=PROJECT_ROOT
    )
    universe = KOSPI200QuarterlyLoader.from_default(project_root=PROJECT_ROOT)
    reporter = DARTReporter(calendar=calendar, project_root=PROJECT_ROOT)
    grid = _quarter_end_grid(universe)
    print(f"   universe: {len(universe.available_quarters())} 분기, grid: {len(grid)} cells")

    # 2. 양성 사건 산출
    print("\n2. 양성 사건 산출 (find_distress_events)...")
    fdr = FDRDataSource(project_root=PROJECT_ROOT)
    fdr_delisting = fdr.delisting()
    # universe union
    union: set[str] = set()
    for q in universe.available_quarters():
        union.update(universe.tickers(q))
    events = find_distress_events(
        universe=union,
        fdr_delisting=fdr_delisting,
        krx_ohlcv_cache_dir=KRX_OHLCV_DIR,
        dart_finstate_cache_dir=DART_FINSTATE_DIR,
        analysis_start=date(2015, 1, 1),
        analysis_end=date(2024, 12, 31),
    )
    pos_tickers = sorted({e.ticker for e in events})
    print(f"   양성 사건: {len(events)} (종목 {len(pos_tickers)})")

    # 3. labels 산출
    print("\n3. labels 산출 (build_labels)...")
    labels = build_labels(events=events, universe_loader=universe, as_of_grid=grid)
    print(f"   labels rows: {len(labels)} (양성 {int(labels['label'].sum())})")

    # 4. features 산출 (전체 grid)
    print("\n4. features 산출 (전체 grid × universe 멤버)...")
    features = _build_features_for_grid(grid, universe, reporter)
    print(f"   features rows: {len(features)}")

    # 5. merge
    print("\n5. features × labels merge...")
    features["as_of"] = pd.to_datetime(features["as_of"]).dt.date
    labels["as_of"] = pd.to_datetime(labels["as_of"]).dt.date
    merged = features.merge(labels[["ticker", "as_of", "label"]], on=["ticker", "as_of"])
    # fs_div 를 categorical → numeric (CFS=1, OFS=0, absent=−1, None=NaN)
    fs_div_map = {"CFS": 1, "OFS": 0, "absent": -1}
    merged["fs_div_code"] = merged["fs_div"].map(fs_div_map).fillna(0).astype(int)
    print(f"   merged rows: {len(merged)} (양성 {int(merged['label'].sum())})")

    # 6. walk-forward folds
    print("\n6. walk-forward folds (min_train=8, embargo=365)...")
    folds = walk_forward_expanding(
        as_of_grid=grid,
        min_train_quarters=8,
        embargo_days=365,
        analysis_start=date(2015, 1, 1),
    )
    print(f"   folds: {len(folds)}")

    feature_cols = ["debt_ratio", "current_ratio", "op_margin", "roa", "fs_div_code"]

    # 7. 각 fold 학습 + 예측 (balanced + unweighted)
    print("\n7. fold 별 학습 + 예측 (balanced + unweighted ablation)...")
    pooled: dict[str, list[dict]] = {"balanced": [], "unweighted": []}
    skipped_folds: list[int] = []
    fold_summaries: list[dict] = []

    for fold in folds:
        train_mask = (merged["as_of"] >= fold.train_start) & (merged["as_of"] <= fold.train_end)
        test_mask = merged["as_of"] == fold.test_as_of
        train_df = merged[train_mask]
        test_df = merged[test_mask]
        train_pos = int(train_df["label"].sum())
        test_pos = int(test_df["label"].sum())

        if test_pos == 0:
            skipped_folds.append(fold.fold_id)
            fold_summaries.append(
                {
                    "fold_id": fold.fold_id,
                    "test_as_of": fold.test_as_of,
                    "train_pos": train_pos,
                    "test_pos": test_pos,
                    "skipped": True,
                }
            )
            continue
        if train_pos == 0:
            # train 양성 0 → 학습 불가능. skip.
            skipped_folds.append(fold.fold_id)
            fold_summaries.append(
                {
                    "fold_id": fold.fold_id,
                    "test_as_of": fold.test_as_of,
                    "train_pos": train_pos,
                    "test_pos": test_pos,
                    "skipped": True,
                    "reason": "train_pos=0",
                }
            )
            continue

        X_train, y_train, _ = _prepare_xy(train_df, feature_cols)
        X_test, y_test, info_test = _prepare_xy(test_df, feature_cols)

        for cw in ("balanced", "unweighted"):
            clf = train_classifier(
                X_train,
                y_train,
                class_weight=cw,  # type: ignore[arg-type]
                calibration="sigmoid",
                random_state=42,
            )
            proba = predict_proba(clf, X_test)
            for ticker, y_t, p in zip(
                info_test.tolist(), y_test.tolist(), proba.tolist(), strict=True
            ):
                pooled[cw].append(
                    {
                        "fold_id": fold.fold_id,
                        "test_as_of": fold.test_as_of,
                        "ticker": ticker,
                        "label": y_t,
                        "proba": p,
                    }
                )

        fold_summaries.append(
            {
                "fold_id": fold.fold_id,
                "test_as_of": fold.test_as_of,
                "train_pos": train_pos,
                "test_pos": test_pos,
                "skipped": False,
            }
        )

    evaluated_folds = len(folds) - len(skipped_folds)
    print(f"   fold 수 {len(folds)} → 평가 {evaluated_folds} (skip {len(skipped_folds)})")
    print(f"   skipped fold_ids: {skipped_folds}")

    # 8. 종목 단위 pooled 평가 (balanced·unweighted) + bootstrap CI
    print("\n8. 종목 단위 pooled 평가 (bootstrap_n=1000)...")
    results: dict[str, dict] = {}
    for cw in ("balanced", "unweighted"):
        df_pred = pd.DataFrame(pooled[cw])
        if len(df_pred) == 0:
            continue
        # 전체 pooled
        full_metrics = evaluate_predictions(
            df_pred["label"].to_numpy(),
            df_pred["proba"].to_numpy(),
            top_k_ratio=0.1,
            bootstrap_n=1000,
            random_state=42,
        )
        # 지주 군 평가 분리
        holding_mask = df_pred["ticker"].isin(HOLDING_TICKERS)
        holding_df = df_pred[holding_mask]
        non_holding_df = df_pred[~holding_mask]
        holding_metrics = evaluate_predictions(
            holding_df["label"].to_numpy(),
            holding_df["proba"].to_numpy(),
            top_k_ratio=0.1,
            bootstrap_n=1000,
            random_state=42,
        )
        non_holding_metrics = evaluate_predictions(
            non_holding_df["label"].to_numpy(),
            non_holding_df["proba"].to_numpy(),
            top_k_ratio=0.1,
            bootstrap_n=1000,
            random_state=42,
        )
        results[cw] = {
            "full": full_metrics,
            "holding": holding_metrics,
            "non_holding": non_holding_metrics,
        }

    # 9. 콘솔 출력
    print("\n=== 9. 결과 보고 ===")
    for cw in ("balanced", "unweighted"):
        if cw not in results:
            continue
        r = results[cw]
        print(f"\n[{cw}] full pooled:")
        for k in ("pr_auc", "roc_auc", "brier", "ece", "top_k_precision"):
            v = r["full"][k]
            ci = r["full"].get(f"{k}_ci95")
            ci_str = f" [{ci[0]:.4f}, {ci[1]:.4f}]" if ci else ""
            print(f"  {k:20s} {v:.4f}{ci_str}")
        print(f"  n_positive {r['full']['n_positive']} / n_total {r['full']['n_total']}")

        print(f"\n[{cw}] 지주 군 (034730·267250·096770):")
        for k in ("pr_auc", "roc_auc", "brier", "top_k_precision"):
            v = r["holding"][k]
            ci = r["holding"].get(f"{k}_ci95")
            ci_str = f" [{ci[0]:.4f}, {ci[1]:.4f}]" if ci else ""
            print(f"  {k:20s} {v:.4f}{ci_str}")
        print(
            f"  n_positive {r['holding']['n_positive']} / n_total {r['holding']['n_total']} "
            "(통계적 변동성 큼)"
        )

        print(f"\n[{cw}] 일반 군 (지주 제외):")
        for k in ("pr_auc", "roc_auc", "brier", "top_k_precision"):
            v = r["non_holding"][k]
            ci = r["non_holding"].get(f"{k}_ci95")
            ci_str = f" [{ci[0]:.4f}, {ci[1]:.4f}]" if ci else ""
            print(f"  {k:20s} {v:.4f}{ci_str}")
        print(
            f"  n_positive {r['non_holding']['n_positive']} / n_total {r['non_holding']['n_total']}"
        )

    # 10. yaml 저장
    summary = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "config": {
            "min_train_quarters": 8,
            "embargo_days": 365,
            "feature_cols": feature_cols,
            "holding_tickers": sorted(HOLDING_TICKERS),
            "calibration": "sigmoid",
            "bootstrap_n": 1000,
        },
        "data_summary": {
            "merged_rows": len(merged),
            "merged_positives": int(merged["label"].sum()),
            "fold_total": len(folds),
            "fold_evaluated": evaluated_folds,
            "fold_skipped_ids": skipped_folds,
        },
        "results": {
            cw: {
                "full": {k: (list(v) if isinstance(v, tuple) else v) for k, v in r["full"].items()},
                "holding": {
                    k: (list(v) if isinstance(v, tuple) else v) for k, v in r["holding"].items()
                },
                "non_holding": {
                    k: (list(v) if isinstance(v, tuple) else v) for k, v in r["non_holding"].items()
                },
            }
            for cw, r in results.items()
        },
        "fold_summaries": [
            {
                **{k: (v.isoformat() if isinstance(v, date) else v) for k, v in fs.items()},
            }
            for fs in fold_summaries
        ],
    }
    out_yaml = OUTPUT_DIR / "results.yaml"
    out_yaml.write_text(
        yaml.safe_dump(summary, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"\n결과 yaml: {out_yaml}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
