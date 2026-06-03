"""LLM 해석 프롬프트 빌더 + 생성 orchestration (빌드타임 배치 전용).

★ CLAUDE.md §3.4: LLM 은 *검증된 수치·라벨을 한국어로 서술만* 한다. 수치·
라벨을 결정·생성·변조하지 않는다. 프롬프트 빌더는 SDK 비의존(순수 문자열)
→ 단위 테스트 가능. 실제 생성은 LLMProvider(교체 가능) 를 통해.

산출 dict 스키마 (load_llm_interpretation 이 `text` 키를 읽음):
- text: 한국어 서술 (StateInterpretBox 표시)
- inputs: LLM 이 받은 검증 수치 (추적·환각 가드 — 사후 대조용)
- meta: provider·model·prompt_version·generated_at (재현·감사)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from frr.llm.base import LLMProvider

PROMPT_VERSION = "v2"  # v2: 비율을 프롬프트에서 % 사전포맷 (표기 통일·LLM 변환 위험 제거)

# system instruction — §3.4 역할·제약 고정.
SYSTEM_INSTRUCTION = (
    "당신은 한국 KOSPI200 기업 분석 데모의 *서술 보조 도구* 입니다. "
    "이미 검증·산출된 수치와 라벨을 일반인이 이해할 한국어 문장으로 '서술' 하는 것이 "
    "유일한 역할입니다.\n"
    "규칙:\n"
    "1) 제공된 수치·라벨만 사용합니다. 새로운 숫자·사실·미래 전망을 만들지 않습니다.\n"
    "2) 위험 점수·위험 수준·시장 상태는 이미 결정된 입력입니다. 바꾸거나 새로 계산하지 않습니다.\n"
    "3) 국면-조건부 해석: 같은 재무 상태라도 시장 상태(위험회피·중립·위험선호)에 따라 "
    "어떻게 다르게 읽어야 하는지 한 문장을 포함합니다.\n"
    "4) 투자 조언·매수/매도 권유를 하지 않습니다. 본 시스템은 시연용 데모입니다.\n"
    "5) 일반인 언어로 씁니다. 전문 통계 용어·모델 평가 지표는 쓰지 않습니다.\n"
    "6) 불릿 없이 2~4문장 산문으로 작성합니다."
)


def _fmt_pct(value: Any) -> str:
    """비율(소수) → 퍼센트 문자열 (×100, 2소수). None/결측 → '—'."""
    if value is None:
        return "—"
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return "—"


def build_prompt(
    *,
    ticker: str,
    name: str,
    as_of: str,
    proba_pct: str,
    risk_level: str,
    state: str,
    ratios: dict[str, Any],
) -> str:
    """검증 입력 → 구조화 프롬프트 (순수 문자열, SDK 비의존).

    v2: 비율을 % 로 사전포맷(×100, 2소수)해 전달 → LLM 이 변환할 필요 없이
    표기 통일. 원본 raw 값은 inputs(meta)에 별도 보존(감사·환각 가드).
    """
    ratio_line = (
        f"부채비율 {_fmt_pct(ratios.get('debt_ratio'))}, "
        f"유동비율 {_fmt_pct(ratios.get('current_ratio'))}, "
        f"영업이익률 {_fmt_pct(ratios.get('op_margin'))}, "
        f"총자산이익률 {_fmt_pct(ratios.get('roa'))}"
    )
    return (
        "다음은 한 기업의 특정 시점 분석 결과입니다. 아래 수치만으로 2~4문장 "
        "한국어 서술을 작성하세요.\n\n"
        f"- 종목: {name} ({ticker})\n"
        f"- 분석 시점: {as_of}\n"
        f"- 위험 점수 (1년 내 재무 충격 가능성 추정, 이미 산출됨): {proba_pct} "
        f"→ 위험 수준 '{risk_level}'\n"
        f"- 시장 상태: {state}\n"
        f"- 재무 비율: {ratio_line}\n\n"
        f"요구: 위 수치를 일반인에게 설명하되, 시장 상태가 '{state}' 임을 고려해 "
        "같은 재무라도 어떻게 읽어야 하는지 한 문장을 포함하세요. "
        "제공된 수치 외의 숫자·사실은 절대 언급하지 마세요."
    )


def generate_interpretation(
    provider: LLMProvider,
    *,
    ticker: str,
    name: str,
    as_of: str,
    proba_pct: str,
    risk_level: str,
    state: str,
    ratios: dict[str, Any],
    model: str,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """provider 로 서술 생성 → 산출 dict (text + inputs + meta)."""
    prompt = build_prompt(
        ticker=ticker,
        name=name,
        as_of=as_of,
        proba_pct=proba_pct,
        risk_level=risk_level,
        state=state,
        ratios=ratios,
    )
    text = provider.generate(prompt, system=SYSTEM_INSTRUCTION, temperature=temperature)
    return {
        "ticker": ticker,
        "as_of": as_of,
        "text": text,
        "inputs": {
            "name": name,
            "proba_pct": proba_pct,
            "risk_level": risk_level,
            "state": state,
            "ratios": ratios,
        },
        "meta": {
            "provider": "gemini",
            "model": model,
            "prompt_version": PROMPT_VERSION,
            "generated_at": datetime.now(UTC).isoformat(),
        },
    }
