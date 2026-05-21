"""tests/test_isolation.py — features 모듈 격리 검증 프레임워크.

CLAUDE.md §5 의 격리 원칙 코드 박제:
- **유니버스 변수** (KOSPI200 편입/편출·시총 순위·인덱스 비중 등) 가 피처
  모듈에 흘러들어가면 *살아남음의 함수*가 피처가 됨 → 데이터 누수
- **상폐/관리 메타** (DelistingDate·Reason·ArrantEnforceDate 등) 는 *결과
  변수*이지 *원인 변수*가 아님 → features 진입 시 라벨 누수

본 테스트는 `src/frr/features/` 가 *작성되기 전* 부터 격리 프레임워크를 박제 —
features 작성 시점에 *맨 처음부터* 격리 규칙 적용. PROGRESS §3 단계 2 DoD 의
사전 메모를 코드로 실재화.

검증 방식:
- AST 기반 import / 심볼 / 메서드 호출 검사
- 텍스트 기반 금지 컬럼 이름 참조 검사 (literal string + 속성 접근 패턴)

**한계 — 의도적 우회 검출 X**:
본 테스트는 *실수로 인한 누수* 차단이 목적. 의도적 우회 (getattr·동적
attribute·메서드 reference 저장 후 호출·문자열 키 조작 등) 는 검출하지 않음.
의도적 우회는 *코드 리뷰* 가 보완. 너무 견고한 우회 검출은 vacuous 위험
(실제 위협이 의도적 우회보다 실수 누수에 있음).

**변환 게이트** (skip → 실행 → placeholder 만 fail):
- features 디렉토리 없음 → `pytest.skip` ("미생성", 정상)
- features 디렉토리 + `.py` (단, `__init__.py` 제외) 1개 이상 → **본격 검증
  실행** (skip 자동 비활성, 격리 규칙 강제)
- features 디렉토리 + `__init__.py` 외 `.py` 0개 (placeholder 만) → `fail`
  ("skip 회피 의도 의심" — 격리 검증 우회 패턴 차단)

(iii) lookahead 차단 테스트는 *placeholder* — features 작업 시점에 본격 구현.
구체 검증 방식 (AST vs 런타임 mock vs features contract) 결정은 features
모듈 설계 결정과 함께.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FEATURES_DIR = PROJECT_ROOT / "src" / "frr" / "features"


# ============================================================================
# 변환 게이트 helper
# ============================================================================


def _check_features_dir_state() -> str:
    """features 디렉토리 상태 반환.

    Returns:
        "missing" — 디렉토리 없음 (skip, 정상)
        "empty" — 디렉토리 있고 `__init__.py` 외 `.py` 0개 (fail)
        "active" — `.py` 1개 이상 (본격 검증 실행)
    """
    if not FEATURES_DIR.exists():
        return "missing"
    py_files = [p for p in FEATURES_DIR.rglob("*.py") if p.name != "__init__.py"]
    if not py_files:
        return "empty"
    return "active"


def _iter_features_modules() -> list[Path]:
    """features/ 하위 모든 `.py` (단, `__init__.py` 제외)."""
    if not FEATURES_DIR.exists():
        return []
    return [p for p in FEATURES_DIR.rglob("*.py") if p.name != "__init__.py"]


def _gate_or_run() -> None:
    """변환 게이트 적용. missing → skip, empty → fail, active → return."""
    state = _check_features_dir_state()
    if state == "missing":
        pytest.skip("features 모듈 미생성 — 작성 시점에 자동 활성")
    if state == "empty":
        pytest.fail(
            "features 디렉토리에 코드 .py 파일 없음 (placeholder 만). "
            "skip 회피 의도 의심 — 격리 검증 우회 패턴 차단."
        )


# ============================================================================
# 격리 변수 정의 (CLAUDE.md §5)
# ============================================================================

# (i) 유니버스 변수 — *살아남음의 함수* 라 피처 진입 시 누수
UNIVERSE_FORBIDDEN_IMPORTS: frozenset[str] = frozenset(
    {
        "frr.data.universe_loader",
    }
)
UNIVERSE_FORBIDDEN_SYMBOLS: frozenset[str] = frozenset(
    {
        "KOSPI200QuarterlyLoader",
    }
)
# 명백히 유니버스 변수인 컬럼명만 — "quarter" 같은 일반어는 timestamp 분기
# 추출 등 합법 용도 충돌로 제외 (false positive 회피).
UNIVERSE_FORBIDDEN_COLUMNS: frozenset[str] = frozenset(
    {
        "kospi200_member",
        "index_weight",
        "market_cap_rank",
        "inclusion_event",
    }
)

# (ii) 상폐/관리 메타 — *결과 변수* 라 피처 진입 시 라벨 누수
# fdr 모듈 자체 import 는 허용 (fdr.listing() 등 합법 사용).
# `delisting()` 메서드 호출 + 컬럼 이름 참조만 금지.
DELISTING_FORBIDDEN_METHODS: frozenset[str] = frozenset(
    {
        "delisting",  # FDRDataSource.delisting() 호출
    }
)
DELISTING_FORBIDDEN_COLUMNS: frozenset[str] = frozenset(
    {
        "DelistingDate",
        "Reason",
        "ArrantEnforceDate",
        "ArrantEndDate",
        "Kind",
        "ToSymbol",
        "ToName",
    }
)

# (iii) Lookahead 우회 — OpenDartReader 직접 호출 메서드 (활성화 2026-05-21)
# DARTReporter 가 룩어헤드 차단의 공식 입구. features 모듈은 OpenDartReader
# 직접 호출 시 *시점 정렬 우회 가능* → 차단.
LOOKAHEAD_FORBIDDEN_METHODS: frozenset[str] = frozenset(
    {
        "finstate",
        "finstate_all",
    }
)


def _column_referenced(text: str, col: str) -> bool:
    """텍스트에서 컬럼 참조 패턴 검출 (literal string + 속성 접근).

    `df["col"]`, `df['col']`, `df.col` 패턴 매칭. 일반 단어가 docstring 등에
    우연 등장하는 false positive 회피.
    """
    return f'"{col}"' in text or f"'{col}'" in text or f".{col}" in text


def _is_type_checking_block(node: ast.AST) -> bool:
    """노드가 `if TYPE_CHECKING:` 블록인지 판정.

    TYPE_CHECKING 블록은 *런타임 실행 0* (mypy/IDE 만 본다) — import 가
    그 안에 있으면 런타임 누수 위험 본질적으로 없음. AST 검사에서 false
    positive 회피용.
    """
    if not isinstance(node, ast.If):
        return False
    test = node.test
    # `if TYPE_CHECKING:` 또는 `if typing.TYPE_CHECKING:` 패턴
    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
        return True
    return (
        isinstance(test, ast.Attribute)
        and test.attr == "TYPE_CHECKING"
        and isinstance(test.value, ast.Name)
        and test.value.id == "typing"
    )


def _collect_type_checking_imports(tree: ast.AST) -> set[int]:
    """TYPE_CHECKING 블록 내부의 import 노드의 lineno 집합.

    AST walk 가 TYPE_CHECKING 안의 import 도 평탄하게 순회하므로, 본 helper 가
    *TYPE_CHECKING 안에 속한 lineno* 를 미리 수집해 격리 검사에서 제외.
    """
    type_checking_linenos: set[int] = set()
    for node in ast.walk(tree):
        if _is_type_checking_block(node):
            for child in ast.walk(node):
                if isinstance(child, (ast.Import, ast.ImportFrom)):
                    type_checking_linenos.add(child.lineno)
                # ast.Name 노드 (심볼 참조) 도 TYPE_CHECKING 블록 내부면 제외 —
                # 하지만 TYPE_CHECKING 블록 본체는 import 만 있는 게 관례이므로
                # 본 helper 는 import lineno 만 추적. 타입 *어노테이션* 의 Name
                # 참조 (예: `reporter: DARTReporter`) 는 별도 처리 필요 — 다음
                # helper 가 ast.AnnAssign·arg.annotation 등을 식별.
    return type_checking_linenos


def _collect_annotation_name_linenos(tree: ast.AST) -> set[int]:
    """타입 어노테이션 안의 Name 노드 lineno 집합.

    `def f(x: KOSPI200QuarterlyLoader)` 의 KOSPI200QuarterlyLoader 같은
    어노테이션 Name 은 *런타임 평가 0* (from __future__ import annotations
    적용 시) — false positive 회피.
    """
    annotation_linenos: set[int] = set()

    def _walk_annotation(annot: ast.AST | None) -> None:
        if annot is None:
            return
        for sub in ast.walk(annot):
            if isinstance(sub, ast.Name):
                annotation_linenos.add(sub.lineno)

    for node in ast.walk(tree):
        # def f(x: T) → arg.annotation
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            for arg in node.args.args + node.args.kwonlyargs + node.args.posonlyargs:
                _walk_annotation(arg.annotation)
            _walk_annotation(node.returns)
        # x: T = ... 또는 x: T (AnnAssign)
        if isinstance(node, ast.AnnAssign):
            _walk_annotation(node.annotation)
    return annotation_linenos


# ============================================================================
# (i) Universe 변수 격리
# ============================================================================


def test_features_module_does_not_import_universe_vars() -> None:
    """features 모듈이 universe_loader / KOSPI200QuarterlyLoader 접근 금지.

    실수로 유니버스 변수 (KOSPI200 편입/편출·시총 순위·인덱스 비중) 가
    피처에 진입하면 *살아남음 신호* (유동성 큰 종목 = 부실 적음 류) 가
    모델에 노출 → 데이터 누수.

    검증:
    - `from frr.data.universe_loader import ...` 또는 `import frr.data.universe_loader` 금지
    - `KOSPI200QuarterlyLoader` 심볼 참조 금지
    - 컬럼 이름 (kospi200_member·index_weight·market_cap_rank·inclusion_event)
      문자열 / 속성 접근 패턴 금지
    """
    _gate_or_run()

    violations: list[str] = []
    for py_file in _iter_features_modules():
        text = py_file.read_text(encoding="utf-8")
        rel = py_file.relative_to(PROJECT_ROOT)
        try:
            tree = ast.parse(text)
        except SyntaxError as e:
            violations.append(f"{rel}: SyntaxError {e}")
            continue

        # TYPE_CHECKING 블록 내부 import / 타입 어노테이션 Name 은 *런타임 0* —
        # 격리 누수 본질 없음. 제외 lineno 수집 (α-fix, 2026-05-21).
        type_checking_linenos = _collect_type_checking_imports(tree)
        annotation_linenos = _collect_annotation_name_linenos(tree)

        for node in ast.walk(tree):
            # ImportFrom (TYPE_CHECKING 안은 제외)
            if (
                isinstance(node, ast.ImportFrom)
                and node.module in UNIVERSE_FORBIDDEN_IMPORTS
                and node.lineno not in type_checking_linenos
            ):
                violations.append(f"{rel}:{node.lineno} from {node.module} import ... 금지")
            # Import (TYPE_CHECKING 안은 제외)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if (
                        alias.name in UNIVERSE_FORBIDDEN_IMPORTS
                        and node.lineno not in type_checking_linenos
                    ):
                        violations.append(f"{rel}:{node.lineno} import {alias.name} 금지")
            # 심볼 참조 Name (타입 어노테이션 안은 제외)
            if (
                isinstance(node, ast.Name)
                and node.id in UNIVERSE_FORBIDDEN_SYMBOLS
                and node.lineno not in annotation_linenos
            ):
                violations.append(f"{rel}:{node.lineno} 심볼 {node.id} 참조 금지")

        # 금지 컬럼 이름 텍스트 참조
        for col in UNIVERSE_FORBIDDEN_COLUMNS:
            if _column_referenced(text, col):
                violations.append(f"{rel}: 컬럼 '{col}' 참조 금지 (유니버스 변수)")

    assert not violations, "유니버스 변수 격리 위반:\n" + "\n".join(violations)


# ============================================================================
# (ii) 상폐/관리 메타 격리
# ============================================================================


def test_features_module_does_not_access_delisting_meta() -> None:
    """features 모듈이 상폐/관리 메타 변수 접근 금지.

    DelistingDate·Reason·ArrantEnforceDate 등은 *라벨 정의* 에만 사용. 피처
    진입 시 라벨 누수 (모델이 *폐지된 종목 = 부실* 직접 학습).

    fdr 모듈 자체 import 는 *허용* — `fdr.listing()` (상장 메타) 등 합법
    용도 존재. `delisting()` 메서드 호출 + 컬럼 이름 참조만 금지.

    검증:
    - `obj.delisting()` 패턴 메서드 호출 금지 (AST Call.attr)
    - 컬럼 이름 (DelistingDate·Reason·ArrantEnforceDate·ArrantEndDate·Kind·
      ToSymbol·ToName) 문자열 / 속성 접근 패턴 금지

    한계: 의도적 우회 (getattr(fdr, "delisting") 등) 는 본 테스트가 검출하지
    않음. 코드 리뷰 책임.
    """
    _gate_or_run()

    violations: list[str] = []
    for py_file in _iter_features_modules():
        text = py_file.read_text(encoding="utf-8")
        rel = py_file.relative_to(PROJECT_ROOT)
        try:
            tree = ast.parse(text)
        except SyntaxError as e:
            violations.append(f"{rel}: SyntaxError {e}")
            continue

        # delisting() 메서드 호출 검출 (AST Call)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in DELISTING_FORBIDDEN_METHODS
            ):
                violations.append(f"{rel}:{node.lineno} {node.func.attr}() 메서드 호출 금지")

        # 금지 컬럼 이름 텍스트 참조
        for col in DELISTING_FORBIDDEN_COLUMNS:
            if _column_referenced(text, col):
                violations.append(f"{rel}: 컬럼 '{col}' 참조 금지 (상폐/관리 메타, 라벨 변수)")

    assert not violations, "상폐/관리 메타 격리 위반:\n" + "\n".join(violations)


# ============================================================================
# (iii) 룩어헤드 차단 — placeholder (features 작업 시점에 구체화)
# ============================================================================


def test_features_lookahead_blocked() -> None:
    """룩어헤드 차단 격리 — (α) AST 화이트리스트/블랙리스트 (2026-05-21 활성화).

    features 모듈은 *OpenDartReader 직접 호출 금지* — DARTReporter 의 시점
    정렬 메서드 (available_at / latest_available / fetch_report) 만 사용.
    OpenDartReader 의 finstate / finstate_all 직접 호출은 *룩어헤드 차단의
    공식 입구 우회* 라 금지.

    YAGNI: 본 (α) 는 *최소 블랙리스트* — OpenDartReader 직접 호출만 차단.
    *시점 인자 정확성* 은 (β) 런타임 mock contract (tests/test_features_
    lookahead.py) 가 보완.

    의도적 우회 (getattr·동적 attribute·메서드 reference 저장) 검출 X —
    코드 리뷰가 보완.
    """
    _gate_or_run()

    violations: list[str] = []
    for py_file in _iter_features_modules():
        text = py_file.read_text(encoding="utf-8")
        rel = py_file.relative_to(PROJECT_ROOT)
        try:
            tree = ast.parse(text)
        except SyntaxError as e:
            violations.append(f"{rel}: SyntaxError {e}")
            continue

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in LOOKAHEAD_FORBIDDEN_METHODS
            ):
                violations.append(
                    f"{rel}:{node.lineno} OpenDartReader 직접 호출 {node.func.attr}() "
                    "금지 — DARTReporter.{available_at, latest_available, fetch_report} 사용"
                )

    assert not violations, "룩어헤드 우회 위반:\n" + "\n".join(violations)
