"""app/ 격리 검증 — LLM SDK import 0 (PROGRESS §5.7, CLAUDE.md §3.4·§8.6).

CLAUDE.md §3.4 박제: 서비스 런타임 (대시보드) LLM 호출 0회 — 정적 산출물
(JSON) 만 읽음.
§8.6 박제: app/ 안에 LLM SDK import 가 없는지 *CI 검사 가능*.

검사 대상 LLM SDK (광범위):
- google.generativeai (Gemini)
- openai
- anthropic
- cohere
- transformers (Hugging Face)
- llm (local LLM 등)

검사 방식 — AST import / ImportFrom 노드 walk.
"""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_DIR = PROJECT_ROOT / "app"

LLM_FORBIDDEN_IMPORTS: frozenset[str] = frozenset(
    {
        "google.generativeai",
        "openai",
        "anthropic",
        "cohere",
        "transformers",
        "litellm",
        "llama_cpp",
    }
)

# llm 모듈 import 패턴 — frr.llm 단일 출구 (CLAUDE.md §8.6)
LLM_FORBIDDEN_PREFIXES: tuple[str, ...] = (
    "google.generativeai",
    "openai",
    "anthropic",
    "cohere",
    "transformers",
    "litellm",
    "llama_cpp",
    "frr.llm",  # app/ 은 frr.llm 직접 import 도 금지
)


def _iter_app_modules() -> list[Path]:
    """app/ 하위 모든 .py (__init__.py 포함)."""
    if not APP_DIR.exists():
        return []
    return list(APP_DIR.rglob("*.py"))


def test_app_dir_exists() -> None:
    """app/ 디렉토리 존재 — 단계 4 진입 시점부터 active."""
    assert APP_DIR.exists(), "app/ 디렉토리 없음 — 단계 4 미진입"


def test_app_no_llm_sdk_import() -> None:
    """app/ 안의 어떤 .py 도 LLM SDK 직접 import 안 함.

    CLAUDE.md §3.4 박제: 런타임 LLM 호출 0회. app/ = 정적 읽기 전용.
    """
    violations: list[str] = []
    for py_file in _iter_app_modules():
        text = py_file.read_text(encoding="utf-8")
        rel = py_file.relative_to(PROJECT_ROOT)
        try:
            tree = ast.parse(text)
        except SyntaxError as e:
            violations.append(f"{rel}: SyntaxError {e}")
            continue

        for node in ast.walk(tree):
            # from X import Y
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for prefix in LLM_FORBIDDEN_PREFIXES:
                    if module == prefix or module.startswith(f"{prefix}."):
                        violations.append(
                            f"{rel}:{node.lineno} from {module} import ... 금지 "
                            "(app/ LLM SDK import 차단, CLAUDE.md §3.4)"
                        )
            # import X (또는 import X.Y)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    for prefix in LLM_FORBIDDEN_PREFIXES:
                        if name == prefix or name.startswith(f"{prefix}."):
                            violations.append(
                                f"{rel}:{node.lineno} import {name} 금지 "
                                "(app/ LLM SDK import 차단, CLAUDE.md §3.4)"
                            )

    assert not violations, "app/ LLM SDK import 격리 위반:\n" + "\n".join(violations)


def test_app_no_training_code() -> None:
    """app/ 안에 *학습* 패턴 (sklearn fit·LightGBM train 등) 금지.

    CLAUDE.md §8.6: app/ 정적 읽기 전용. 학습·계산 *금지*.

    검증: app/ 모듈이 sklearn/lightgbm/hmmlearn 의 *학습 클래스* import 0.
    """
    forbidden_training = frozenset(
        {
            "lightgbm",
            "hmmlearn",
        }
    )
    forbidden_training_prefixes = ("sklearn.ensemble", "sklearn.linear_model", "sklearn.tree")

    violations: list[str] = []
    for py_file in _iter_app_modules():
        text = py_file.read_text(encoding="utf-8")
        rel = py_file.relative_to(PROJECT_ROOT)
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module in forbidden_training:
                    violations.append(f"{rel}:{node.lineno} from {module} import ... 금지 (학습)")
                for prefix in forbidden_training_prefixes:
                    if module.startswith(prefix):
                        violations.append(
                            f"{rel}:{node.lineno} from {module} import ... 금지 (학습)"
                        )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in forbidden_training:
                        violations.append(f"{rel}:{node.lineno} import {alias.name} 금지 (학습)")

    assert not violations, "app/ 학습 코드 import 격리 위반:\n" + "\n".join(violations)
