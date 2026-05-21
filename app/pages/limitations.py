"""⚠️ Limitations 페이지 — docs/ui_components.md §2.5."""

from __future__ import annotations

import streamlit as st
from components.header import render_page_header


def render_limitations() -> None:
    """방법론적 특징 + 6 한계 항목 + 학술 가치 메시지."""
    render_page_header(
        title="⚠️ Limitations (방법론적 특징)",
        value_message=(
            "본 페이지는 본 프로젝트의 **방법론적 특징 핵심**. "
            "모든 한계가 *정직 박제* — 사용성 가치는 *negative finding 의 정직성* + "
            "*정직성 사슬 5 차원* + *모집단 한계 정량 증명* 가치 제공."
        ),
    )

    # === 6 한계 항목 (각 expander) ===
    st.markdown("## 6 한계 항목 — 정직 박제")

    with st.expander("1. 단계 2 — D2 baseline Negative Finding", expanded=True):
        st.markdown(
            """
- **PR-AUC 0.0136** < base rate 0.0205 → 모델 random 보다 나쁨
- **ROC-AUC 0.2651** < 0.5 → 정반대 예측에 가까움
- **class weight ablation 효과 0** — balanced vs unweighted 차이 < 0.001
- 양성 절대 수 부족 (20 종목 / 45 cells) 앞에서 보완 무력

★ 박제: `PROGRESS.md §5.5.17` + `reports/d2_baseline_model_card.md`
            """
        )

    with st.expander("2. (A) 데이터 보강 — Strong Negative Evidence"):
        st.markdown(
            """
- notfound 3,583 OFS 재페치 → **status 전환 0건**
- DART API 응답 모두 `{status: '013', '조회된 데이타가 없습니다'}`
- → notfound 는 *D10 fetcher 미적용*이 아니라 *실제 데이터 부재*
- **§5.5.7 KOSPI200 부실 사건 희소성** 의 *데이터 출처 변경으로 극복 불가능* 정량 증명

★ 박제: `PROGRESS.md §5.5.17 (A)`
            """
        )

    with st.expander("3. 단계 3 — Regime 학술 명명 부합 약함"):
        st.markdown(
            """
HMM K=3 의 사후 명명 부합 약함:

| state | 명명 | ret_20d | vol_60d | 도메인 해석 |
|---|---|---|---|---|
| 2 | 위험선호 | +0.549 | +0.309 | 상승+변동 (학술 정의 부분 부합) |
| 1 | 중립 | -0.752 | -0.008 | 약세 (학술 부합 약함) |
| 0 | 위험회피 | -0.809 | -0.015 | **정체 (학술 정의 부적합)** |

- 2020 코로나 spot-check: 위험회피 **27.9% 만** (학술 정의 부합 약함)
- → **K=4 ablation 으로 82.0% 정량 정답 발견** (사이드바 "시장 국면 시계열" 페이지 참조)

★ 박제: `PROGRESS.md §5.6.1` + `reports/regime_model_card.md`
            """
        )

    with st.expander("4. HMM 시드 불안정성"):
        st.markdown(
            """
5 시드 변동 (42·123·7·2024·999):

| 모델 | log-lik 변동 | 비율 |
|---|---|---|
| **HMM** | -9442 ~ -8312 | **13.6%** ⚠️ |
| GMM | -10101 ~ -10107 | 0.06% |
| K-Means inertia | 5436.5 ~ 5436.9 | 0.007% |

- HMM EM 알고리즘 *local optima 의존성*
- 본 라인 결과는 *random_state=42* 단일 시드 — 다른 시드는 다른 결과

★ 박제: `PROGRESS.md §5.6.2`
            """
        )

    with st.expander("5. 자동 K=4 vs 도메인 K=3 Tension"):
        st.markdown(
            """
BIC·AIC 자동 선택 결과:

| K | HMM BIC | HMM AIC |
|---|---|---|
| 2 | 18,743.58 | 18,623.27 |
| 3 (본 라인) | 19,156.36 | 18,955.85 |
| **4** | **15,674.28 ⬅ 최소** | **15,382.11 ⬅ 최소** |

- 본 라인 K=3 유지 (학술 관행 + 도메인 해석 가능성)
- K=4 결과는 *대안 시나리오* — 단계 3 명명 부합 약함의 *데이터가 아닌 적정 K 부족* 증명

★ 박제: `PROGRESS.md §5.6.2` + `§5.6.4`
            """
        )

    with st.expander("6. KOSPI200 모집단 부실 사건 희소성"):
        st.markdown(
            """
- 양성 종목 **20** (universe 321 중 6.2%)
- 양성 cells **45** (features 8,008 의 0.56%)
- 28 walk-forward fold 중 **19 fold (68%)** 가 train_pos=0 또는 test_pos=0 → 평가 가능 fold 9
- *§5.5.6 (B3 KOSDAQ 확장) 기각* 유지 — point-in-time 정합성 X

→ **D1 정직성 + §5 격리 원칙** 유지하면서 *모델 학습 불가능 수준* 데이터 한계 확인

★ 박제: `PROGRESS.md §5.5.6·§5.5.7`
            """
        )

    st.markdown("---")

    # === 프로젝트 핵심 메시지 5 ===
    st.markdown("## 프로젝트 핵심 메시지")
    st.markdown(
        """
본 프로젝트는 *negative finding* 이나 다음 가치 박제:

1. **D2 정직성 사슬 5 차원** — 변수·양성충분성·격리·시간·LLM 격리 (CI 강제, `PROGRESS §5.5.12`)
2. **§7.6 작업 진입 검토 사이클** — 매 작업 4 단계 의무 (`CLAUDE.md §7.6`)
3. **5 후보 전수 검증·기각 후 D2 채택** — 입증된 최선 (`PROGRESS §5.5.7`)
4. **Negative finding 의 정직성** + **모집단 한계 정량 증명**
5. **40+ commit 자기 점검 사이클** — 모든 결정이 PROGRESS·실측·자문 검토 통과
        """
    )

    st.markdown("---")

    # === 추가 자료 link ===
    st.markdown("## 추가 자료")
    st.markdown(
        """
- 📄 `PROGRESS.md` — `§5.5 ~ §5.9` 박제 본문 (정직성 학습 사슬)
- 📄 `reports/d2_baseline_model_card.md` — D2 모델 카드 8 섹션
- 📄 `reports/regime_model_card.md` — Regime 모델 카드 8 섹션
- 📄 `docs/ux_design.md` — UX 설계 (Phase 2)
- 📄 `docs/ui_components.md` — UI 컴포넌트 명세 (Phase 3)
        """
    )
