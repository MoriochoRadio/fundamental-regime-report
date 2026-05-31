"""app/ 외부 노출 가드 — §7.7 금지단어 + ML 원본 수치 리터럴 0 검사.

CLAUDE.md §7.7: 공개 소스 외부 표면에 취업 차원 단어·원본 ML 평가 수치
직접 노출 금지. 본 검사는 app/ 의 모든 .py 소스(docstring·주석·코드 포함)를
스캔해 재발을 차단한다 (③-cleanup 정리 박제).

★ reports/*.md (기술 문서) 는 §7.7 면제 — 스캔 제외. app/ .py 만 대상.
"""

from __future__ import annotations

from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent.parent / "app"

# §7.7(2) 금지단어 (취업 차원) + 영문 동의어
_FORBIDDEN_WORDS = (
    "면접",
    "취업",
    "포트폴리오",
    "채용",
    "구직",
    "이력서",
    "졸업",
    "portfolio",
    "Portfolio",
    "career",
    "Career",
    "resume",
    "Resume",
)

# 원본 ML 평가 수치 리터럴 (docs §2.8 — 일반인 표면 노출 금지)
_FORBIDDEN_ML = (
    "PR-AUC",
    "ROC-AUC",
    "0.0136",
    "0.0205",
    "0.2651",
)


def _app_py_files() -> list[Path]:
    return [p for p in _APP_DIR.rglob("*.py") if "__pycache__" not in p.parts]


def test_app_no_forbidden_words() -> None:
    """app/ .py 소스에 §7.7 취업 차원 금지단어 0."""
    violations: list[str] = []
    for py in _app_py_files():
        text = py.read_text(encoding="utf-8")
        rel = py.relative_to(_APP_DIR.parent)
        for word in _FORBIDDEN_WORDS:
            if word in text:
                violations.append(f"{rel}: '{word}'")
    assert not violations, "§7.7 금지단어 노출:\n" + "\n".join(violations)


def test_app_no_ml_number_literals() -> None:
    """app/ .py 소스에 원본 ML 평가 수치 리터럴 0 (docs §2.8)."""
    violations: list[str] = []
    for py in _app_py_files():
        text = py.read_text(encoding="utf-8")
        rel = py.relative_to(_APP_DIR.parent)
        for token in _FORBIDDEN_ML:
            if token in text:
                violations.append(f"{rel}: '{token}'")
    assert not violations, "원본 ML 수치 리터럴 노출:\n" + "\n".join(violations)
