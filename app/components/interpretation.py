"""국면 조건부 해석 박스 (docs/ui_components.md §1.7 — C-4 v1 static template)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

_TEMPLATES = {
    "위험회피": (
        "현재 시장이 **위험회피 (위기)** 국면입니다. "
        "위험회피 국면에서는 *같은 부채비율 상승·영업이익 둔화* 가 "
        "*일반 시 대비 더 강한 부실 신호*로 해석될 수 있습니다."
    ),
    "위험선호": (
        "현재 시장이 **위험선호 (상승)** 국면입니다. "
        "위험선호 국면에서는 *동일 재무 지표 약화* 가 "
        "*시장 전반 회복세에 가려질 수 있어* 신호 누락 주의가 필요합니다."
    ),
    "중립": (
        "현재 시장이 **중립** 국면입니다. "
        "중립 국면은 *전이로 자주 이동* 하는 교차로 역할입니다 — "
        "위험회피 전환 확률 0.925 (§5.6.1). "
        "재무 지표 변화를 *전이 신호*로 함께 해석하세요."
    ),
}

_CAVEAT = "\n\n단 본 모델은 **random 미만** 성능이므로 *방향성 가이드만* 으로 사용해 주세요."


def render_regime_conditional_box(
    regime: str | None,
    ticker_features: pd.Series | None,
    ticker_name: str,
) -> None:
    """국면 × ratio × ticker 통합 해석 (static template v1)."""
    if regime is None:
        st.info(
            "ℹ️ 시장 국면 데이터를 매핑할 수 없습니다 "
            "(Warmup 9 개월 또는 분석 시점이 데이터 범위 외)."
        )
        return

    base = _TEMPLATES.get(regime, f"현재 시장 국면: **{regime}**.")
    body = base + _CAVEAT

    # ticker 별 ratio 부착
    if ticker_features is not None and len(ticker_features) > 0:
        ratio_lines = []
        for col, label in [
            ("debt_ratio", "부채비율"),
            ("current_ratio", "유동비율"),
            ("op_margin", "영업이익률"),
            ("roa", "ROA"),
        ]:
            v = ticker_features.get(col) if hasattr(ticker_features, "get") else None
            if v is not None and not pd.isna(v):
                ratio_lines.append(f"- **{label}**: `{float(v):.4f}`")
        if ratio_lines:
            body += f"\n\n##### {ticker_name} 해당 시점 재무 지표\n" + "\n".join(ratio_lines)
        else:
            body += f"\n\n##### {ticker_name} 해당 시점 재무 지표 없음 (skipped 또는 결측)."

    st.info(body)
