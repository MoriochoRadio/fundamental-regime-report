"""src/frr/llm/ 테스트 — LLMProvider 계약 (단위) + Gemini 1-call smoke (통합).

단위: 네트워크 0 (stub provider 로 ABC 계약 검증).
통합: 실 Gemini 호출 (@pytest.mark.integration, GEMINI_API_KEY 필요 → CI deselect,
키 없으면 graceful skip).
"""

from __future__ import annotations

import os

import pytest

from frr.llm import LLMProvider


class _StubProvider(LLMProvider):
    """네트워크 0 stub — ABC 계약 검증용."""

    def generate(self, prompt: str, *, system: str | None = None, temperature: float = 0.2) -> str:
        return f"[stub:{temperature}] {prompt[:20]}"


def test_llmprovider_is_abstract() -> None:
    """LLMProvider 는 추상 — 직접 인스턴스화 불가."""
    with pytest.raises(TypeError):
        LLMProvider()  # type: ignore[abstract]


def test_stub_provider_contract() -> None:
    """구현체는 generate(prompt, *, system, temperature) → str 계약 충족."""
    p = _StubProvider()
    out = p.generate("재무 충격 위험 서술", system="역할 고정", temperature=0.1)
    assert isinstance(out, str)
    assert out  # 비어있지 않음


def test_llm_package_single_export() -> None:
    """frr.llm 은 LLMProvider 만 노출 (SDK 단일 출구 — 패키지 import 시 SDK 미로딩)."""
    import frr.llm as llm_pkg

    assert llm_pkg.__all__ == ["LLMProvider"]
    assert not hasattr(llm_pkg, "GeminiProvider")  # gemini 모듈에서 직접 import


@pytest.mark.integration
def test_gemini_one_call_smoke() -> None:
    """실 Gemini 1-call — 비어있지 않은 텍스트 반환 (키 없으면 skip)."""
    if not os.environ.get("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY 미설정 — Gemini smoke skip")
    from frr.llm.gemini import GeminiProvider

    provider = GeminiProvider()
    out = provider.generate("한국어로 한 문장 인사를 작성하세요.", temperature=0.0)
    assert isinstance(out, str)
    assert out.strip(), "Gemini 가 빈 텍스트 반환"
