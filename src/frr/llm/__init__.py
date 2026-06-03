"""LLM 보조 도구 패키지 (빌드타임 배치 전용 — CLAUDE.md §3.4·§8.6).

★ 단일 출구: 외부 LLM SDK (google-genai 등) 는 *오직 본 패키지 안* 에서만
import 한다. 타 모듈은 `LLMProvider` 인터페이스만 본다 (교체 가능).

★ §3.4: LLM 은 *직접 만든 AI 가 아니다*. 이미 검증된 수치·라벨을 한국어로
서술하는 보조 도구다 — 수치·라벨을 결정·생성·변조하지 않는다. 호출은
*빌드타임 배치 1회* 만, 서비스 런타임(대시보드) 호출 0회.

GeminiProvider 는 `frr.llm.gemini` 에서 직접 import (패키지 import 시 SDK
로딩을 피하기 위해 여기서 re-export 하지 않음).
"""

from frr.llm.base import LLMProvider

__all__ = ["LLMProvider"]
