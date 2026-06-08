"""app/components/interpretation.py 단위 테스트.

단계 5 단위 (g) 산출물. docs/ui_design.md §2.7·§3.5 매핑.

★ 핵심 회귀: StateInterpretBox 출력에 ML 차원 문구 (random 미만·전이확률·
PR-AUC 등) 비노출 (docs §2.7·§5(1) 박제). 한계 고백은 ModelLimitBadge 책임.

컴포넌트 = pure 렌더링 함수. st mock 으로 호출 검증.
"""

from __future__ import annotations

from unittest.mock import patch

from app.components.interpretation import StateInterpretBox


def _info_text(mock_st) -> str:
    """mock_st.info 호출에 전달된 텍스트 인자 결합."""
    texts: list[str] = []
    for c in mock_st.info.call_args_list:
        texts.extend(str(a) for a in c.args)
    return "\n".join(texts)


# ---- 9 조합 template sampling -----------------------------------------------


def test_template_risk_off_high() -> None:
    """위험회피 × 높음 → 신중한 검토 문구."""
    with patch("app.components.interpretation.st") as mock_st:
        StateInterpretBox("위험회피", "높음")
        mock_st.info.assert_called_once()
        assert "위험회피 시장 상태에서 높은 위험 수준은 신중한 검토" in _info_text(mock_st)


def test_template_neutral_medium() -> None:
    """중립 × 중간 → 일반적 범주 문구."""
    with patch("app.components.interpretation.st") as mock_st:
        StateInterpretBox("중립", "중간")
        assert "중립 시장 상태에서 중간 위험 수준은 일반적 범주" in _info_text(mock_st)


def test_template_risk_on_low() -> None:
    """위험선호 × 낮음 → 매우 안정적 문구."""
    with patch("app.components.interpretation.st") as mock_st:
        StateInterpretBox("위험선호", "낮음")
        assert "위험선호 시장 상태에서 양호 재무는 매우 안정적" in _info_text(mock_st)


# ---- llm_text 합성 ----------------------------------------------------------


def test_llm_text_appended() -> None:
    """llm_text 전달 → template + 서술 본문 포함."""
    with patch("app.components.interpretation.st") as mock_st:
        StateInterpretBox("중립", "낮음", llm_text="빌드타임 생성 서술 단락입니다.")
        text = _info_text(mock_st)
        assert "중립 시장 상태에서 양호 재무는 안정적" in text
        assert "빌드타임 생성 서술 단락입니다." in text


def test_llm_text_none_template_only() -> None:
    """llm_text None → template 만 (추가 단락 없음)."""
    with patch("app.components.interpretation.st") as mock_st:
        StateInterpretBox("중립", "낮음", llm_text=None)
        text = _info_text(mock_st)
        assert "중립 시장 상태에서 양호 재무는 안정적" in text
        # template 한 문장만 — 줄바꿈 단락 구분자 부재
        assert "\n\n" not in text


# ---- ★ ML 수치/문구 비노출 회귀 --------------------------------------------


def test_no_ml_phrases() -> None:
    """★ docs §2.7·§5(1): ML 차원 문구 비노출 (전 9 조합)."""
    forbidden = ["random 미만", "0.925", "PR-AUC", "base rate", "drawdown", "전이확률"]
    states = ["위험회피", "중립", "위험선호"]
    risks = ["낮음", "중간", "높음"]
    for state in states:
        for risk in risks:
            with patch("app.components.interpretation.st") as mock_st:
                StateInterpretBox(state, risk)
                text = _info_text(mock_st)
                for token in forbidden:
                    assert token not in text, f"({state},{risk}): '{token}' 노출됨"


# ---- 방어적 입력 ------------------------------------------------------------


def test_unknown_state_fallback() -> None:
    """미지 state → 예외 없이 fallback (st.info 1회)."""
    with patch("app.components.interpretation.st") as mock_st:
        StateInterpretBox("알수없음", "낮음")
        mock_st.info.assert_called_once()
        assert "충분하지 않아" in _info_text(mock_st)


def test_none_inputs_fallback() -> None:
    """state/risk None → fallback, 예외 없이 완료."""
    with patch("app.components.interpretation.st") as mock_st:
        StateInterpretBox(None, None)
        mock_st.info.assert_called_once()
        assert "충분하지 않아" in _info_text(mock_st)


# ---- 검증 1: 함수명 정정 ----------------------------------------------------


def test_component_name_state_not_regime() -> None:
    """검증 1: StateInterpretBox 존재 + render_regime_conditional_box 부재."""
    from app import components
    from app.components import interpretation

    assert hasattr(components, "StateInterpretBox")
    assert not hasattr(interpretation, "render_regime_conditional_box")
    assert not hasattr(interpretation, "RegimeConditionalBox")
