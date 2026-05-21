"""D2 baseline 결과 페이지 — docs/ui_components.md §2.4."""

from __future__ import annotations

import pandas as pd
import streamlit as st
from components.header import render_page_header
from components.warning import render_empty_state, render_model_limit_warning
from data_loader import load_d2_results, load_refetch_summary


def _format_metric_row(metrics: dict, name: str) -> dict:
    """metric dict → table row (value + CI)."""
    val = metrics.get(name)
    ci = metrics.get(f"{name}_ci95")
    ci_str = f"[{ci[0]:.4f}, {ci[1]:.4f}]" if ci and len(ci) == 2 else "—"
    return {"metric": name, "value": f"{val:.4f}" if val is not None else "—", "95% CI": ci_str}


def render_d2_results() -> None:
    """D2 baseline 결과 페이지."""
    render_page_header(
        title="D2 부실 라벨 baseline 결과",
        value_message=(
            "⚠️ **Negative Finding 정직 박제** — 모델 random 미만 "
            "(PR-AUC 0.0136 < base rate 0.0205). "
            "본 결과는 KOSPI200 부실 사건 희소성의 *경험적 정량 증거*."
        ),
    )

    d2 = load_d2_results()
    refetch = load_refetch_summary()

    if d2 is None:
        render_empty_state(
            title="D2 산출물 부재",
            action="`uv run python scripts/train_d2_baseline.py` 실행",
            icon="⚠️",
        )
        return

    # === 데이터 통계 ===
    st.markdown("### 데이터 통계")
    data_summary = d2.get("data_summary", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("features cells", f"{data_summary.get('merged_rows', 0):,}")
    c2.metric("양성 cells", data_summary.get("merged_positives", "—"))
    c3.metric("fold 평가", data_summary.get("fold_evaluated", "—"))
    c4.metric("fold skip", len(data_summary.get("fold_skipped_ids", [])))

    st.markdown("---")

    results = d2.get("results", {})

    # === Full pooled — balanced ===
    if "balanced" in results:
        st.markdown("### Full pooled — balanced (class weight 보정)")
        full = results["balanced"].get("full", {})
        rows = [
            _format_metric_row(full, m)
            for m in ("pr_auc", "roc_auc", "brier", "ece", "top_k_precision")
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        n_pos = full.get("n_positive", 0)
        n_total = full.get("n_total", 1)
        base_rate = (n_pos / max(n_total, 1)) * 100
        st.caption(
            f"base rate = {n_pos} / {n_total} ≈ {base_rate:.2f}%. "
            "PR-AUC < base rate + ROC-AUC < 0.5 → 모델 random 미만."
        )

    # === Ablation ===
    if "unweighted" in results:
        st.markdown("### Class weight ablation — balanced vs unweighted")
        ablation_rows = []
        for cw in ("balanced", "unweighted"):
            full = results[cw].get("full", {})
            ablation_rows.append(
                {
                    "class_weight": cw,
                    "pr_auc": f"{full.get('pr_auc', 0):.4f}",
                    "roc_auc": f"{full.get('roc_auc', 0):.4f}",
                    "brier": f"{full.get('brier', 0):.4f}",
                }
            )
        st.dataframe(pd.DataFrame(ablation_rows), use_container_width=True, hide_index=True)
        st.caption("차이 < 0.001 → class weight 효과 0. *양성 절대 수 부족 앞에서 보완 무력*.")

    # === 지주 군 vs 일반 군 ===
    if "balanced" in results:
        st.markdown("### 지주 군 분리 평가 (§5.5.16)")
        st.caption("fs_div as feature 학습 + 지주 군 평가 분리. 학습 임계 미달이라 *군별 학습 X*.")
        holding = results["balanced"].get("holding", {})
        non_holding = results["balanced"].get("non_holding", {})
        c_h, c_n = st.columns(2)
        with c_h:
            st.markdown("**🏢 지주 군 (034730·267250·096770)**")
            st.metric("n_positive (cells)", holding.get("n_positive", "—"))
            st.metric("PR-AUC", f"{holding.get('pr_auc', 0):.4f}")
            st.metric("ROC-AUC", f"{holding.get('roc_auc', 0):.4f}")
        with c_n:
            st.markdown("**📊 일반 군 (지주 제외)**")
            st.metric("n_positive (cells)", non_holding.get("n_positive", "—"))
            st.metric("PR-AUC", f"{non_holding.get('pr_auc', 0):.4f}")
            st.metric("ROC-AUC", f"{non_holding.get('roc_auc', 0):.4f}")
        st.caption(
            "지주 군 N=12 — Top-K precision CI [0.0000, 1.0000] 완전 변동 "
            "(§5.5.16 짚을 점 1 의 경험적 확인)."
        )

    # === (A) 데이터 보강 결과 ===
    if refetch:
        st.markdown("---")
        st.markdown("### (A) 데이터 보강 시도 결과 — Strong Negative Evidence")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("총 호출", f"{refetch.get('total_targets', 0):,}")
        c2.metric("status 전환", refetch.get("status_changed_to_ok", "—"))
        c3.metric("errors", refetch.get("errors", "—"))
        c4.metric("소요 (초)", refetch.get("elapsed_seconds", "—"))
        st.caption(
            "notfound 3,583 OFS 재페치 → status 전환 0건. "
            "DART 응답 모두 *조회 데이터 없음* → notfound 는 *실제 데이터 부재* "
            "(D10 fetcher 미적용 아님). 모집단 한계 강한 증명."
        )

    st.markdown("---")
    render_model_limit_warning(context="d2")
