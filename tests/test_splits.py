"""Walk-forward expanding split 단위 테스트 9건 (PROGRESS §5.5.12).

합성 40 분기 grid 로 algorithm 자체 검증. 실제 universe_loader 기반 grid 의
fold 수 실측은 별도 (PROGRESS §5.5.12 task #4).

검증 항목:
- 1~5: 기본 동작 (fold 수·첫/마지막 fold·expanding 단조·train_start 고정)
- 6: 정밀화 #2 (min_train > len(grid) → ValueError, silent 실패 차단)
- 7: 0년 fold placeholder (NotImplementedError + 메시지 검증)
- 8: zero_year_handling="raise" 기본 정상 동작
- 9: 정밀화 #3 (WalkForwardFold 직접 생성 시 dataclass __post_init__ 검증)
"""

from __future__ import annotations

from datetime import date

import pytest

from frr.eval.splits import WalkForwardFold, walk_forward_expanding


def _synthetic_40_quarters() -> list[date]:
    """2015Q1~2024Q4 40 분기말 자연 종료일 (휴일 무시 — algorithm 자체 검증용)."""
    grid: list[date] = []
    for year in range(2015, 2025):
        grid.extend(
            [
                date(year, 3, 31),
                date(year, 6, 30),
                date(year, 9, 30),
                date(year, 12, 31),
            ]
        )
    return grid


# ============================================================================
# 1~5: 기본 동작
# ============================================================================


def test_synthetic_40_quarters_yields_29_folds() -> None:
    """40 분기 grid + min_train=8 + embargo=365 → 29 folds.

    PROGRESS §5.5.12 박제 예상 28 과 1 차이는 *윤년·threshold 동등 효과*:
    test=2017-12-31 의 threshold=2016-12-31 이 grid[7] 와 정확히 일치 →
    grid[0..7] 8 개로 첫 fold 가 i=11 부터 (박제 예상 i=12 와 1 빠름).
    박제가 "정확한 수는 코드 작성 후 실측 보고" 라고 한 항목 — 본 실측이 권위.
    """
    grid = _synthetic_40_quarters()
    folds = walk_forward_expanding(
        as_of_grid=grid,
        min_train_quarters=8,
        embargo_days=365,
        analysis_start=date(2015, 1, 1),
    )
    assert len(folds) == 29, f"예상 29 folds, 실제 {len(folds)}"


def test_first_fold_position() -> None:
    """첫 fold: test=grid[11]=2017-12-31, train_end=grid[7]=2016-12-31.

    grid[11]=2017-12-31 의 threshold = 2017-12-31 - 365 = 2016-12-31 = grid[7].
    valid_train_grid = grid[0..7] = 8 개 (min_train=8 정확히 충족).
    그 직전 grid[10]=2017-09-30 의 threshold=2016-09-30 → valid=7 개 (skip).
    """
    grid = _synthetic_40_quarters()
    folds = walk_forward_expanding(
        as_of_grid=grid,
        min_train_quarters=8,
        embargo_days=365,
        analysis_start=date(2015, 1, 1),
    )
    first = folds[0]
    assert first.fold_id == 0
    assert first.test_as_of == date(2017, 12, 31)
    assert first.train_end == date(2016, 12, 31)
    assert first.train_start == date(2015, 1, 1)


def test_last_fold_covers_2024q4() -> None:
    """마지막 fold: test=grid[39]=2024-12-31 (분석 기간 종료)."""
    grid = _synthetic_40_quarters()
    folds = walk_forward_expanding(
        as_of_grid=grid,
        min_train_quarters=8,
        embargo_days=365,
        analysis_start=date(2015, 1, 1),
    )
    last = folds[-1]
    assert last.test_as_of == date(2024, 12, 31)
    # train_end = 2024-12-31 - 365 = 2023-12-31 = grid[35] (2023Q4)
    assert last.train_end == date(2023, 12, 31)


def test_expanding_train_end_monotone_nondecreasing() -> None:
    """Expanding window: folds[i].train_end ≤ folds[i+1].train_end (시간 순)."""
    grid = _synthetic_40_quarters()
    folds = walk_forward_expanding(
        as_of_grid=grid,
        min_train_quarters=8,
        embargo_days=365,
        analysis_start=date(2015, 1, 1),
    )
    for i in range(len(folds) - 1):
        assert folds[i].train_end <= folds[i + 1].train_end, (
            f"fold {i} train_end={folds[i].train_end} > "
            f"fold {i + 1} train_end={folds[i + 1].train_end} — expanding 위반"
        )


def test_train_start_fixed_to_analysis_start() -> None:
    """Expanding window 특성: 모든 fold 의 train_start = analysis_start."""
    grid = _synthetic_40_quarters()
    analysis_start = date(2015, 1, 1)
    folds = walk_forward_expanding(
        as_of_grid=grid,
        min_train_quarters=8,
        embargo_days=365,
        analysis_start=analysis_start,
    )
    assert all(f.train_start == analysis_start for f in folds)


# ============================================================================
# 6: 정밀화 #2 — min_train > len(grid) ValueError
# ============================================================================


def test_min_train_exceeds_grid_raises_value_error() -> None:
    """min_train_quarters > len(as_of_grid) → ValueError (silent 차단, 정밀화 #2).

    빈 fold 리스트 반환 시 호출자가 *실행 안 됨* 을 인지 못 함. silent 실패 차단.
    """
    grid = _synthetic_40_quarters()
    with pytest.raises(ValueError, match="silent 실패 차단"):
        walk_forward_expanding(
            as_of_grid=grid,
            min_train_quarters=50,  # 40 < 50
            embargo_days=365,
            analysis_start=date(2015, 1, 1),
        )


# ============================================================================
# 7: 0년 fold placeholder — NotImplementedError + 메시지 검증
# ============================================================================


@pytest.mark.parametrize("handling", ["skip", "merged", "synthetic"])
def test_zero_year_handling_not_implemented(handling: str) -> None:
    """zero_year_handling != "raise" → NotImplementedError + 메시지 검증.

    메시지에 "D8 결정 시점" + "§5.5.10 참조" 둘 다 포함 — 미래 작업 시점에
    *어디서 결정* 되는지와 *왜 보강 미적용* 인지가 PROGRESS 로 연결.
    """
    grid = _synthetic_40_quarters()
    with pytest.raises(NotImplementedError) as exc_info:
        walk_forward_expanding(
            as_of_grid=grid,
            min_train_quarters=8,
            embargo_days=365,
            analysis_start=date(2015, 1, 1),
            zero_year_handling=handling,  # type: ignore[arg-type]
        )
    msg = str(exc_info.value)
    assert "D8 결정 시점" in msg, f"메시지에 'D8 결정 시점' 누락: {msg}"
    assert "§5.5.10" in msg, f"메시지에 '§5.5.10' 누락: {msg}"


# ============================================================================
# 8: zero_year_handling="raise" 기본 정상 동작
# ============================================================================


def test_zero_year_handling_raise_default_returns_folds() -> None:
    """기본 zero_year_handling="raise" → 정상 fold 생성, 0년 fold 도 그대로 반환.

    0년 fold (test 시점 forward 1년 내 양성 0) 의 *식별* 은 본 모듈 범위 외 —
    label 데이터를 참조해야 알 수 있음. 본 모듈은 grid 와 embargo 만 본다.
    "raise" 는 *호출자가 명시적으로 0년 처리 안 함을 선언* 한 모드 → 정상 동작.
    """
    grid = _synthetic_40_quarters()
    folds = walk_forward_expanding(
        as_of_grid=grid,
        min_train_quarters=8,
        embargo_days=365,
        analysis_start=date(2015, 1, 1),
        zero_year_handling="raise",  # 기본값 명시
    )
    assert len(folds) == 29
    # 2021·2023 분기 fold 도 그대로 포함 (양성 0 여부 본 모듈 범위 외)
    test_years = {f.test_as_of.year for f in folds}
    assert 2021 in test_years
    assert 2023 in test_years


# ============================================================================
# 9: 정밀화 #3 — WalkForwardFold 직접 생성 시 embargo 검증
# ============================================================================


def test_walk_forward_fold_direct_embargo_violation_raises() -> None:
    """WalkForwardFold 직접 생성 시 embargo 위반 → __post_init__ ValueError.

    features 격리가 import-level 차단이듯, fold 무결성은 dataclass-level 차단.
    walk_forward_expanding 우회해 직접 생성해도 검증 작동.
    """
    # embargo_days=365 인데 train_end 가 test - 365 보다 늦음 → 위반
    with pytest.raises(ValueError, match="embargo 위반"):
        WalkForwardFold(
            train_start=date(2015, 1, 1),
            train_end=date(2017, 6, 30),  # test - 365 = 2016-12-31 보다 늦음
            test_as_of=date(2017, 12, 31),
            embargo_days=365,
            fold_id=0,
        )


def test_walk_forward_fold_direct_time_order_violation_raises() -> None:
    """WalkForwardFold 직접 생성 시 시간 순 위반 → __post_init__ ValueError.

    train_start < train_end < test_as_of 위반 (예: train_end >= test_as_of).
    9번 테스트와 별도 검증 — 정밀화 #3 의 두 검증 단계 (시간 순 + embargo)
    중 첫 번째 단계 박제. 본 항목으로 9번 테스트 #9 가 *두 검증 모두 도달*
    가능 함을 확인.
    """
    with pytest.raises(ValueError, match="train_start < train_end < test_as_of"):
        WalkForwardFold(
            train_start=date(2015, 1, 1),
            train_end=date(2018, 1, 1),
            test_as_of=date(2018, 1, 1),  # train_end == test_as_of 위반
            embargo_days=365,
            fold_id=0,
        )
