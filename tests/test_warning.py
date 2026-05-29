"""app/components/warning.py 단위 테스트.

단계 5 단위 (f) 산출물. docs/ui_design.md §2.8·§2.9·§3.4 매핑.

★ 핵심 회귀: ModelLimitBadge 출력에 원본 ML 수치 (PR-AUC·base rate 등)
비노출 (docs §2.8 박제).

컴포넌트 = pure 렌더링 함수. st mock 으로 호출 검증.
"""

from __future__ import annotations

from unittest.mock import call, patch

from app.components.warning import EmptyState, ModelLimitBadge


def _collect_text(mock_st) -> str:
    """mock_st 의 모든 st.* 호출에 전달된 텍스트 인자를 결합."""
    texts: list[str] = []
    for method in ("markdown", "write", "warning", "error", "info", "caption"):
        for c in getattr(mock_st, method).call_args_list:
            texts.extend(str(a) for a in c.args)
            texts.extend(str(v) for v in c.kwargs.values())
    return "\n".join(texts)


# ---- ModelLimitBadge -------------------------------------------------------


def test_badge_variant() -> None:
    """variant=badge → 데모 배지 문구 1 회 (st.warning)."""
    with patch("app.components.warning.st") as mock_st:
        ModelLimitBadge("badge")
        mock_st.warning.assert_called_once()
        assert "시연용 데모" in _collect_text(mock_st)


def test_modal_variant() -> None:
    """variant=modal → 배지 본문 동일 (docs §3.4)."""
    with patch("app.components.warning.st") as mock_st:
        ModelLimitBadge("modal")
        mock_st.warning.assert_called_once()
        assert "실제 투자에 사용 금지" in _collect_text(mock_st)


def test_page_full_variant() -> None:
    """variant=page_full → 한계 페이지 전체 (3 한계 항목 + 데모 명시)."""
    with patch("app.components.warning.st") as mock_st:
        ModelLimitBadge("page_full")
        text = _collect_text(mock_st)
        assert "본 시스템의 한계" in text
        assert "모델 위험 예측 정확도" in text
        assert "시장 상태 분류 초기 9 개월" in text
        assert "분석 범위" in text
        mock_st.warning.assert_called_once()  # 데모 명시 line


def test_invalid_variant_fallback() -> None:
    """미지원 variant → 기본 badge fallback."""
    with patch("app.components.warning.st") as mock_st:
        ModelLimitBadge("nonsense")
        mock_st.warning.assert_called_once()
        assert "시연용 데모" in _collect_text(mock_st)


def test_badge_no_ml_numbers() -> None:
    """★ docs §2.8 박제: 원본 ML 수치 비노출 (전 variant)."""
    forbidden = ["PR-AUC", "0.0136", "base rate", "0.0205", "random 미만"]
    for variant in ("badge", "modal", "page_full"):
        with patch("app.components.warning.st") as mock_st:
            ModelLimitBadge(variant)
            text = _collect_text(mock_st)
            for token in forbidden:
                assert token not in text, f"{variant}: '{token}' 노출됨"


# ---- EmptyState ------------------------------------------------------------


def test_empty_state_default() -> None:
    """message 기본값 → 📭 안내 1 회, suggestion 미표시 (st.info 미호출)."""
    with patch("app.components.warning.st") as mock_st:
        EmptyState()
        mock_st.markdown.assert_called_once()
        assert "📭" in _collect_text(mock_st)
        mock_st.info.assert_not_called()


def test_empty_state_with_suggestion() -> None:
    """suggestion 전달 → 다음 행동 박스 (st.info) 표시."""
    with patch("app.components.warning.st") as mock_st:
        EmptyState(message="데이터 없음", suggestion="다른 시점 선택")
        assert "데이터 없음" in _collect_text(mock_st)
        mock_st.info.assert_called_once()
        assert "다른 시점 선택" in _collect_text(mock_st)


def test_empty_state_default_message_corrected() -> None:
    """기본 메시지 정정 회귀: Phase 4 'skipped fold' 부재 + docs §2.9 기본."""
    with patch("app.components.warning.st") as mock_st:
        EmptyState()
        text = _collect_text(mock_st)
        assert "skipped fold" not in text
        assert "양성 0" not in text
        assert "평가 자료 부족" in text


def test_mock_sanity() -> None:
    """call 헬퍼·mock 패턴 자체 정합."""
    with patch("app.components.warning.st") as mock_st:
        EmptyState(suggestion="x")
        assert call("💡 x") in mock_st.info.call_args_list
