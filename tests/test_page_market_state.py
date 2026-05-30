"""app/pages/market_state.py 단위 테스트 (페이지 통합 단위 k).

시장 상태 페이지 = PageHeader + StateStripeChart + 위기 info + 9개월 warning.
st·컴포넌트·load_state_series mock 으로 검증.

★ Q2 (A) 회귀: StateInterpretBox 미사용 (모듈 namespace 미import — 시장
전용 페이지엔 종목 risk 부재). docstring 은 'StateInterpretBox 미사용' 설명을
포함하므로 소스 텍스트 검사 대신 namespace 검사 사용.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import DEFAULT, patch

import pandas as pd

from app.pages import market_state as ms

_SRC = Path(__file__).resolve().parent.parent / "app" / "pages" / "market_state.py"

_TARGETS = dict(
    st=DEFAULT,
    load_state_series=DEFAULT,
    PageHeader=DEFAULT,
    StateStripeChart=DEFAULT,
    EmptyState=DEFAULT,
)


def _state() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2020-02-01", "2020-03-01"]),
            "state_label": ["위험회피", "중립", "위험선호"],
        }
    )


def test_normal_render() -> None:
    """정상 → PageHeader + StateStripeChart + info + warning, EmptyState 미호출."""
    with patch.multiple("app.pages.market_state", **_TARGETS) as m:
        m["load_state_series"].return_value = _state()
        ms.render()
        m["PageHeader"].assert_called_once()
        m["StateStripeChart"].assert_called_once()
        m["st"].info.assert_called_once()
        m["st"].warning.assert_called_once()
        m["EmptyState"].assert_not_called()


def test_none_emptystate() -> None:
    """state_series None → EmptyState, StateStripeChart 미호출."""
    with patch.multiple("app.pages.market_state", **_TARGETS) as m:
        m["load_state_series"].return_value = None
        ms.render()
        m["EmptyState"].assert_called_once()
        m["StateStripeChart"].assert_not_called()


def test_empty_emptystate() -> None:
    """state_series 빈 DataFrame → EmptyState."""
    with patch.multiple("app.pages.market_state", **_TARGETS) as m:
        m["load_state_series"].return_value = pd.DataFrame(columns=["date", "state_label"])
        ms.render()
        m["EmptyState"].assert_called_once()


def test_stateinterpretbox_not_used() -> None:
    """★ Q2 (A): StateInterpretBox 미사용 — 모듈 namespace 미import."""
    assert not hasattr(ms, "StateInterpretBox")


def test_info_warning_verbatim() -> None:
    """위기 info(안전 자산 선호) + 9개월 warning 문구 정합 (docs §1.3)."""
    with patch.multiple("app.pages.market_state", **_TARGETS) as m:
        m["load_state_series"].return_value = _state()
        ms.render()
        info_text = " ".join(str(a) for c in m["st"].info.call_args_list for a in c.args)
        warn_text = " ".join(str(a) for c in m["st"].warning.call_args_list for a in c.args)
        assert "안전 자산 선호" in info_text
        assert "9개월" in warn_text


def test_no_ml_numbers_in_source() -> None:
    """docs §2.8·§5(1): 소스에 ML 원본 수치 리터럴 비노출."""
    src = _SRC.read_text(encoding="utf-8")
    for token in ["PR-AUC", "0.0136", "base rate", "0.0205", "random 미만"]:
        assert token not in src, f"'{token}' 노출됨"
