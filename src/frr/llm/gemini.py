"""Gemini 공급자 — LLMProvider 구현 (google-genai).

★ google-genai SDK import 는 *본 모듈(src/frr/llm/) 안에서만* (§8.6 단일 출구).
GEMINI_API_KEY 는 호출 측(빌드타임 배치 스크립트)이 환경에 로드한다
(`load_dotenv()` 등). 본 클래스는 env 또는 명시 인자에서 키를 읽는다.

빌드타임 배치 전용 — 서비스 런타임 호출 0회 (CLAUDE.md §3.4).
"""

from __future__ import annotations

import os
import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from frr.llm.base import LLMProvider

# 현행 무료 Flash 모델 (2.0 폐기 → 2.5-flash). 필요 시 생성자 model 인자로 교체.
_DEFAULT_MODEL = "gemini-2.5-flash"
# 일시적 오류 (503 과부하·429 rate limit) — 재시도 (free 티어 503 빈발).
_TRANSIENT_CODES = (429, 503)
_MAX_ATTEMPTS = 4


class GeminiProvider(LLMProvider):
    """Google Gemini 공급자 (google-genai Client)."""

    def __init__(self, *, model: str = _DEFAULT_MODEL, api_key: str | None = None) -> None:
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError(
                "GEMINI_API_KEY 미설정 — .env 또는 환경변수에 키를 로드한 뒤 사용하세요."
            )
        self._client = genai.Client(api_key=key)
        self._model = model

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        """프롬프트 → Gemini 생성 텍스트 (빌드타임 1회 호출).

        일시적 오류(503 과부하·429 rate limit)는 지수 백오프로 재시도.
        그 외 오류(400 등)는 즉시 전파.
        """
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system,
        )
        for attempt in range(_MAX_ATTEMPTS):
            try:
                resp = self._client.models.generate_content(
                    model=self._model,
                    contents=prompt,
                    config=config,
                )
                return (resp.text or "").strip()
            except genai_errors.APIError as exc:
                transient = getattr(exc, "code", None) in _TRANSIENT_CODES
                if transient and attempt < _MAX_ATTEMPTS - 1:
                    time.sleep(2**attempt)  # 1·2·4초 백오프
                    continue
                raise
        # 도달 불가 (마지막 시도는 위에서 return 또는 raise)
        raise RuntimeError("generate: 재시도 소진")
