"""src/frr/llm/interpretation.py 테스트 — 프롬프트 v2 빌더 (네트워크 0·SDK 비의존).

build_prompt·_fmt_pct 는 순수 함수. generate_interpretation 은 stub provider 로
orchestration 계약 검증 (실 LLM 호출 없음).
"""

from __future__ import annotations

from frr.llm.base import LLMProvider
from frr.llm.interpretation import (
    PROMPT_VERSION,
    SYSTEM_INSTRUCTION,
    _fmt_pct,
    build_prompt,
    generate_interpretation,
)


class _StubProvider(LLMProvider):
    def __init__(self) -> None:
        self.last_prompt: str | None = None
        self.last_system: str | None = None

    def generate(self, prompt: str, *, system: str | None = None, temperature: float = 0.2) -> str:
        self.last_prompt = prompt
        self.last_system = system
        return "stub 서술"


def test_fmt_pct() -> None:
    """×100·2소수, None/비수치 → '—'."""
    assert _fmt_pct(6.6475) == "664.75%"
    assert _fmt_pct(-0.0101) == "-1.01%"
    assert _fmt_pct(0.0) == "0.00%"
    assert _fmt_pct(None) == "—"
    assert _fmt_pct("x") == "—"


def test_build_prompt_pct_preformatted() -> None:
    """v2: 비율이 % 로 사전포맷되어 프롬프트에 들어감 (raw 소수 미노출)."""
    p = build_prompt(
        ticker="097230",
        name="한진중공업",
        as_of="2019-03-29",
        proba_pct="36.4%",
        risk_level="중간",
        state="위험선호",
        ratios={"debt_ratio": 6.6475, "current_ratio": 0.5898, "op_margin": 0.0231, "roa": -0.0101},
    )
    assert "664.75%" in p  # debt_ratio % 변환
    assert "58.98%" in p
    assert "2.31%" in p
    assert "-1.01%" in p
    assert "6.6475" not in p  # raw 소수는 프롬프트에 없음
    # 환각 가드 + 국면-조건부 + 입력 라벨
    assert "제공된 수치 외의 숫자·사실은 절대 언급하지 마세요" in p
    assert "위험선호" in p
    assert "36.4%" in p and "중간" in p


def test_build_prompt_handles_missing_ratio() -> None:
    """결측 비율 → '—' (예외 없이)."""
    p = build_prompt(
        ticker="000000",
        name="X",
        as_of="2024-12-31",
        proba_pct="—",
        risk_level="—",
        state="중립",
        ratios={"debt_ratio": None, "current_ratio": None, "op_margin": None, "roa": None},
    )
    assert "—" in p


def test_system_instruction_constraints() -> None:
    """system 제약: 서술만·새 숫자 금지·국면-조건부·투자조언 금지 골격."""
    s = SYSTEM_INSTRUCTION
    assert "서술" in s
    assert "국면-조건부" in s
    assert "투자 조언" in s


def test_generate_interpretation_schema() -> None:
    """generate_interpretation → text+inputs(raw ratios)+meta(prompt_version) 스키마."""
    stub = _StubProvider()
    out = generate_interpretation(
        stub,
        ticker="097230",
        name="한진중공업",
        as_of="2019-03-29",
        proba_pct="36.4%",
        risk_level="중간",
        state="위험선호",
        ratios={"debt_ratio": 6.6475, "current_ratio": 0.5898, "op_margin": 0.0231, "roa": -0.0101},
        model="gemini-2.5-flash",
    )
    assert out["text"] == "stub 서술"
    assert out["ticker"] == "097230"
    assert out["inputs"]["ratios"]["debt_ratio"] == 6.6475  # raw 보존 (감사)
    assert out["inputs"]["state"] == "위험선호"
    assert out["meta"]["prompt_version"] == PROMPT_VERSION
    assert out["meta"]["model"] == "gemini-2.5-flash"
    # stub 에 전달된 프롬프트는 % 포맷, system 은 제약문
    assert "664.75%" in stub.last_prompt
    assert stub.last_system == SYSTEM_INSTRUCTION
