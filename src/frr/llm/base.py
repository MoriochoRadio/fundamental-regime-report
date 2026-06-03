"""LLMProvider 인터페이스 (CLAUDE.md §3.4·§8.6).

공급자(Gemini 등)를 추상화 — 다른 모듈은 본 인터페이스만 보고, 구현 교체
가능. 외부 LLM SDK import 는 본 패키지(src/frr/llm/) 안에서만.

★ §3.4 역할 분리: LLM 은 *검증된 수치·라벨의 한국어 서술화* 보조 도구.
수치·라벨을 결정·생성·변조하지 않는다. 빌드타임 배치 1회 호출 전용
(서비스 런타임 호출 0회).
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """LLM 공급자 추상 인터페이스.

    구현체는 `generate` 만 제공하면 된다 (빌드타임 배치 스크립트가 호출).
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        """프롬프트 → 생성 텍스트 (한국어 서술).

        Args:
            prompt: 사용자 프롬프트 (검증된 입력 수치·맥락 포함).
            system: system instruction (역할·제약 고정). None 이면 미지정.
            temperature: 생성 온도 (재현성 위해 낮게 — 기본 0.2).

        Returns:
            생성된 텍스트 (빈 문자열일 수 있으나 구현체는 strip 권장).
        """
        ...
