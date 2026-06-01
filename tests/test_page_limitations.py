"""app/pages/limitations.py 단위 테스트 (페이지 통합 단위 l).

한계 페이지 = ModelLimitBadge("page_full") + 기술 자료 모델 카드 링크.
st·ModelLimitBadge·load_model_card mock 으로 검증.

★★ 핵심 회귀: 모델 카드 *내용*(ML 수치 포함)을 inline 렌더하지 않음 (§7.7
격리). load_model_card 반환 str 이 어떤 st 렌더 인자에도 미포함.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import DEFAULT, patch

from app.pages import limitations as lim

_SRC = Path(__file__).resolve().parent.parent / "app" / "pages" / "limitations.py"

_TARGETS = dict(
    st=DEFAULT,
    ModelLimitBadge=DEFAULT,
    load_model_card=DEFAULT,
)


def _rendered_text(mock_st) -> str:
    """st.markdown/write/caption/info/warning 에 전달된 모든 텍스트 결합."""
    texts: list[str] = []
    for method in ("markdown", "write", "caption", "info", "warning", "title", "header"):
        for c in getattr(mock_st, method).call_args_list:
            texts.extend(str(a) for a in c.args)
    return "\n".join(texts)


def test_page_full_called() -> None:
    """ModelLimitBadge('page_full') 1회 호출."""
    with patch.multiple("app.pages.limitations", **_TARGETS) as m:
        m["load_model_card"].return_value = "카드 내용"
        lim.render()
        m["ModelLimitBadge"].assert_called_once_with("page_full")


def test_model_card_link_shown() -> None:
    """load_model_card not None → 경로 링크 mention 표시."""
    with patch.multiple("app.pages.limitations", **_TARGETS) as m:
        m["load_model_card"].return_value = "카드 내용 (존재)"
        lim.render()
        text = _rendered_text(m["st"])
        assert "reports/d2_baseline_model_card.md" in text
        assert "기술 상세 자료" in text


def test_model_card_absent_section_skipped() -> None:
    """load_model_card None → 기술 자료 섹션 생략."""
    with patch.multiple("app.pages.limitations", **_TARGETS) as m:
        m["load_model_card"].return_value = None
        lim.render()
        text = _rendered_text(m["st"])
        assert "기술 상세 자료" not in text
        # page_full 본문은 여전히 렌더 (위임)
        m["ModelLimitBadge"].assert_called_once_with("page_full")


def test_card_content_not_rendered_inline() -> None:
    """★★ §7.7 핵심: 모델 카드 내용(ML 수치 포함)이 inline 렌더 안 됨."""
    fake_card = "## D2 모델 카드\nPR-AUC 0.0136 < base rate 0.0205 (random 미만)"
    with patch.multiple("app.pages.limitations", **_TARGETS) as m:
        m["load_model_card"].return_value = fake_card
        lim.render()
        text = _rendered_text(m["st"])
        assert "PR-AUC" not in text
        assert "0.0136" not in text
        assert fake_card not in text


def test_no_ml_numbers_in_source() -> None:
    """docs §2.8·§5(1): limitations.py 소스에 ML 원본 수치 리터럴 비노출."""
    src = _SRC.read_text(encoding="utf-8")
    for token in ["PR-AUC", "0.0136", "base rate", "0.0205", "ROC-AUC", "random 미만"]:
        assert token not in src, f"'{token}' 노출됨"


def test_pageheader_not_used() -> None:
    """★ Q3 (A): PageHeader 미사용 (page_full 이 h1 self-contained, namespace 미import)."""
    assert not hasattr(lim, "PageHeader")
