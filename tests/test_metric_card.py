"""app/components/metric_card.py 단위 테스트.

단계 5 단위 (d) 산출물. 검증 7 (방어적 입력) + 검증 1·2·4 매핑.

컴포넌트 = pure 렌더링 함수 (st.* 직접 호출, 반환 None).
3 층 구조 (단계 + 퍼센트 + 접는 설명) — 사용자 결정.
mock-based 테스트 — st.* 호출 인자 검증.
"""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

from app.components.metric_card import RiskScoreCard, StateCard


def _make_mock_st() -> MagicMock:
    """st mock — expander 가 context manager 지원."""
    mock_st = MagicMock()
    mock_st.expander.return_value.__enter__ = MagicMock(return_value=None)
    mock_st.expander.return_value.__exit__ = MagicMock(return_value=False)
    return mock_st


# ---- RiskScoreCard ---------------------------------------------------------


def test_risk_score_card_low() -> None:
    """proba 낮음 (0.05) → 🟢 낮음 + 퍼센트 caption + 설명 expander."""
    mock_st = _make_mock_st()
    with patch("app.components.metric_card.st", mock_st):
        RiskScoreCard(0.05)
        metric_args = mock_st.metric.call_args[0]
        assert metric_args[0] == "위험 점수"
        assert "🟢" in metric_args[1]
        assert "낮음" in metric_args[1]
        mock_st.expander.assert_called_once_with("이 수치는 무엇인가요?")


def test_risk_score_card_medium() -> None:
    """proba 중간 (0.3) → 🟡 중간."""
    mock_st = _make_mock_st()
    with patch("app.components.metric_card.st", mock_st):
        RiskScoreCard(0.3)
        metric_args = mock_st.metric.call_args[0]
        assert "🟡" in metric_args[1]
        assert "중간" in metric_args[1]


def test_risk_score_card_high() -> None:
    """proba 높음 (0.7) → 🔴 높음."""
    mock_st = _make_mock_st()
    with patch("app.components.metric_card.st", mock_st):
        RiskScoreCard(0.7)
        metric_args = mock_st.metric.call_args[0]
        assert "🔴" in metric_args[1]
        assert "높음" in metric_args[1]


def test_risk_score_card_none() -> None:
    """proba None → ⚪ — + 분석 평가 제외 caption + 설명 expander 여전히 표시."""
    mock_st = _make_mock_st()
    with patch("app.components.metric_card.st", mock_st):
        RiskScoreCard(None)
        metric_args = mock_st.metric.call_args[0]
        assert "—" in metric_args[1]
        # 설명 expander 는 None 에서도 표시 (일반 교육 텍스트)
        mock_st.expander.assert_called_once_with("이 수치는 무엇인가요?")


def test_risk_score_card_nan() -> None:
    """proba NaN → ⚪ — (classify_risk NaN 처리)."""
    mock_st = _make_mock_st()
    with patch("app.components.metric_card.st", mock_st):
        RiskScoreCard(float("nan"))
        metric_args = mock_st.metric.call_args[0]
        assert "—" in metric_args[1]


# ---- StateCard -------------------------------------------------------------


def test_state_card_risk_off() -> None:
    """위험회피 → 🔴 위험회피 + 설명 expander."""
    mock_st = _make_mock_st()
    with patch("app.components.metric_card.st", mock_st):
        StateCard("위험회피")
        metric_args = mock_st.metric.call_args[0]
        assert metric_args[0] == "시장 상태"
        assert "🔴" in metric_args[1]
        assert "위험회피" in metric_args[1]
        mock_st.expander.assert_called_once_with("이 상태는 무엇인가요?")


def test_state_card_neutral() -> None:
    """중립 → ⚪ 중립."""
    mock_st = _make_mock_st()
    with patch("app.components.metric_card.st", mock_st):
        StateCard("중립")
        metric_args = mock_st.metric.call_args[0]
        assert "중립" in metric_args[1]


def test_state_card_risk_on() -> None:
    """위험선호 → 🟢 위험선호."""
    mock_st = _make_mock_st()
    with patch("app.components.metric_card.st", mock_st):
        StateCard("위험선호")
        metric_args = mock_st.metric.call_args[0]
        assert "🟢" in metric_args[1]
        assert "위험선호" in metric_args[1]


def test_state_card_none_warmup() -> None:
    """state None → ⚪ — + 분석 시작 9 개월 caption."""
    mock_st = _make_mock_st()
    with patch("app.components.metric_card.st", mock_st):
        StateCard(None)
        metric_args = mock_st.metric.call_args[0]
        assert "—" in metric_args[1]
        caption_arg = mock_st.caption.call_args[0][0]
        assert "9 개월" in caption_arg


def test_state_card_unknown_label() -> None:
    """미지정 라벨 → ⚪ (방어적, _STATE_EMOJI fallback)."""
    mock_st = _make_mock_st()
    with patch("app.components.metric_card.st", mock_st):
        StateCard("미지정")
        metric_args = mock_st.metric.call_args[0]
        assert "⚪" in metric_args[1]
        assert "미지정" in metric_args[1]


# ---- 검증 2 매핑: class_weight 폐기 + label/fs_div 카드 부재 ---------------


def test_risk_score_card_no_class_weight_param() -> None:
    """검증 2: RiskScoreCard 가 class_weight 파라미터 없음 (ablation ML 폐기)."""
    sig = inspect.signature(RiskScoreCard)
    assert "class_weight" not in sig.parameters
    assert set(sig.parameters.keys()) == {"proba"}


def test_deprecated_cards_absent() -> None:
    """검증 2: label/fs_div 카드 폐기 (3 단계 §2 spec 부재)."""
    from app.components import metric_card

    assert not hasattr(metric_card, "render_label_card")
    assert not hasattr(metric_card, "render_fs_div_card")
    assert not hasattr(metric_card, "LabelCard")
    assert not hasattr(metric_card, "FsDivCard")
    # 함수명 정정 (검증 1)
    assert not hasattr(metric_card, "render_risk_score_card")
    assert not hasattr(metric_card, "render_regime_card")
    assert not hasattr(metric_card, "RegimeCard")


# ---- 검증 4 매핑: 날것 확률 (0.0136) 노출 0 --------------------------------


def test_risk_score_card_no_raw_proba_4_decimals() -> None:
    """검증 4: 날것 확률 4 자리 (0.0136) 노출 0 — format_percent 만."""
    mock_st = _make_mock_st()
    with patch("app.components.metric_card.st", mock_st):
        RiskScoreCard(0.013564)
        # metric + caption 모든 출력에서 "0.0136" 같은 4 자리 소수 노출 0
        all_text = ""
        for call in mock_st.metric.call_args_list + mock_st.caption.call_args_list:
            if call[0]:
                all_text += str(call[0][0]) + " " + (str(call[0][1]) if len(call[0]) > 1 else "")
        assert "0.0136" not in all_text
        assert "0.013564" not in all_text
        # 퍼센트 형태 (format_percent) 노출 — "1.4%" 예상
        assert "%" in all_text


# ---- 신규: 퍼센트 표시 + 설명 expander ------------------------------------


def test_risk_score_card_percent_displayed() -> None:
    """퍼센트 형태 (format_percent) caption 표시."""
    mock_st = _make_mock_st()
    with patch("app.components.metric_card.st", mock_st):
        RiskScoreCard(0.136)
        caption_arg = mock_st.caption.call_args[0][0]
        assert "%" in caption_arg
        assert "13.6%" in caption_arg


def test_both_cards_have_explanation_expander() -> None:
    """두 카드 모두 설명 expander 존재 (3 층 구조)."""
    mock_st = _make_mock_st()
    with patch("app.components.metric_card.st", mock_st):
        RiskScoreCard(0.3)
        assert mock_st.expander.call_count == 1
    mock_st2 = _make_mock_st()
    with patch("app.components.metric_card.st", mock_st2):
        StateCard("중립")
        assert mock_st2.expander.call_count == 1


# ---- 검증 1: 컴포넌트 이름 정정 (export) -----------------------------------


def test_component_export() -> None:
    """검증 1: RiskScoreCard·StateCard export (RegimeCard 부재)."""
    from app import components

    assert hasattr(components, "RiskScoreCard")
    assert hasattr(components, "StateCard")
    assert not hasattr(components, "RegimeCard")
