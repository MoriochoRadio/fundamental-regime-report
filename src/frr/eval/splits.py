"""Walk-forward expanding-window splits with embargo gap.

본 모듈은 D2 정직성 사슬의 *시간 차원* (PROGRESS §5.5.12). features 격리가
import-level 변수 누수 차단이듯 (tests/test_isolation.py), embargo 는 fold train
내부 label 정의가 미래 event 를 본 결과 (시간 누수) 차단.

**Embargo 본질** (PROGRESS §5.5.12):
    fold 의 train 내부 각 as_of=s 의 label 은 (s, s + forward_window] event 로
    결정. 만약 s + forward_window > train_end 이면 *label 정의 자체가 train_end
    이후 event 를 본 결과* → train 에 미래 정보 누수. 따라서 train 의 모든
    as_of s 가 s ≤ train_end - forward_window 보장 필요.

    → `embargo_days = forward_window_days = 365` (기본). forward_window 는
    labels.py 소관, embargo_days 는 본 모듈 소관 — *호출자가 일관성 책임*.
    forward window 변경 시 embargo 도 동일 변경.

**D2 정직성 4 차원 종합** (§5.5.12):
- 변수 차원: §5.5.9 distress 화이트리스트 (`{"자본전액잠식"}`)
- 양성 충분성: §5.5.10 forward window 1→2년 ablation 기각
- 격리 차원: tests/test_isolation.py (features 변수 누수 차단)
- **시간 차원: 본 모듈** (시간 누수 차단)

격리 차원이 *features 변수 누수* 를, embargo 가 *시간 누수* 를 차단 — 두
안전장치가 동시 작동해야 모델 평가의 정직성 보존.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from frr.data.universe_loader import KOSPI200QuarterlyLoader


@dataclass(frozen=True)
class WalkForwardFold:
    """Expanding window fold + embargo 무결성 검증.

    walk_forward_expanding 우회하고 직접 생성해도 dataclass-level 검증 작동
    (features 격리가 import-level 차단이듯). 정밀화 #3 (PROGRESS §5.5.12).

    Fields:
        train_start: 분석 기간 시작 (모든 fold 고정 — expanding window 특성).
        train_end: 본 fold 의 train 종료 (embargo 충족하는 마지막 grid 분기).
        test_as_of: test 시점 (분기말 영업일, label = forward 1년 event 결정).
        embargo_days: train·test 사이 시간 간격 (forward_window 와 일관 책임).
        fold_id: 0-indexed.
    """

    train_start: date
    train_end: date
    test_as_of: date
    embargo_days: int
    fold_id: int

    def __post_init__(self) -> None:
        # 시간 순 검증
        if not (self.train_start < self.train_end < self.test_as_of):
            raise ValueError(
                f"fold {self.fold_id}: train_start < train_end < test_as_of 위반 "
                f"(train_start={self.train_start}, train_end={self.train_end}, "
                f"test_as_of={self.test_as_of})"
            )
        # embargo 본질 검증 (정밀화 #3, §5.5.12)
        embargo_threshold = self.test_as_of - timedelta(days=self.embargo_days)
        if self.train_end > embargo_threshold:
            raise ValueError(
                f"fold {self.fold_id}: embargo 위반 — train_end={self.train_end} > "
                f"test_as_of - embargo_days({self.embargo_days}) = {embargo_threshold}. "
                "train label 정의가 train_end 이후 event 를 본 결과 (시간 누수)."
            )


def walk_forward_expanding(
    *,
    as_of_grid: list[date],
    min_train_quarters: int = 8,
    embargo_days: int = 365,
    analysis_start: date = date(2015, 1, 1),
    zero_year_handling: Literal["skip", "merged", "synthetic", "raise"] = "raise",
    zero_years: frozenset[int] | None = None,
) -> list[WalkForwardFold]:
    """Expanding window walk-forward + embargo gap.

    알고리즘:
        for each test_as_of in sorted(as_of_grid):
            train_end_threshold = test_as_of - timedelta(days=embargo_days)
            valid_train_grid = [q for q in grid if q <= train_end_threshold]
            if len(valid_train_grid) < min_train_quarters: continue
            train_end = max(valid_train_grid)
            yield WalkForwardFold(train_start=analysis_start, train_end, test_as_of, ...)

    Args:
        as_of_grid: 분기말 영업일 date 리스트 (자동 정렬). `_quarter_end_grid(loader)`
            로 추출 가능.
        min_train_quarters: train 분기 최소 수 (기본 8 = 2년 = 학습 임계).
        embargo_days: train·test 시간 누수 차단 간격. **forward_window_days 와
            일관성 호출자 책임** (둘 다 365 기본).
        analysis_start: expanding window 의 train 시작 (모든 fold 고정).
        zero_year_handling: 0년 fold 처리 (D8 결정 시점에 구현, 현재 "raise" 만 지원).
        zero_years: 양성 0 인 연도 frozenset (`zero_year_handling != "raise"` 시 사용).

    Returns:
        WalkForwardFold list (fold_id 순 = test_as_of 시간 순).

    Raises:
        ValueError: `min_train_quarters > len(as_of_grid)` — silent 빈 fold 차단 (정밀화 #2).
        NotImplementedError: `zero_year_handling != "raise"` — D8 결정 시점에 구현.
    """
    # 정밀화 #2 (silent 차단, §5.5.12)
    if min_train_quarters > len(as_of_grid):
        raise ValueError(
            f"min_train_quarters({min_train_quarters}) > len(as_of_grid)"
            f"({len(as_of_grid)}) — fold 0 으로 silent 실패 차단. "
            "grid 가 부족하거나 min_train 이 과도하게 큼."
        )

    # 0년 fold 처리 placeholder (D8 결정 시점에 구현, 격리 (iii) 와 같은 패턴)
    if zero_year_handling != "raise":
        raise NotImplementedError(
            f"zero_year_handling={zero_year_handling!r} 는 D8 결정 시점에 구현. "
            "현재는 'raise' (기본) 만 지원. PROGRESS §5.5.10 참조 — "
            "라벨 측 보강 안 함, 모델 측 보완 (class weight·forward window ablation·"
            "bootstrap·시점별 가중치) 우선 결정."
        )

    grid = sorted(as_of_grid)
    folds: list[WalkForwardFold] = []
    fold_id = 0

    for test_as_of in grid:
        train_end_threshold = test_as_of - timedelta(days=embargo_days)
        valid_train_grid = [q for q in grid if q <= train_end_threshold]
        if len(valid_train_grid) < min_train_quarters:
            continue
        train_end = max(valid_train_grid)
        folds.append(
            WalkForwardFold(
                train_start=analysis_start,
                train_end=train_end,
                test_as_of=test_as_of,
                embargo_days=embargo_days,
                fold_id=fold_id,
            )
        )
        fold_id += 1

    return folds


def _quarter_end_grid(loader: KOSPI200QuarterlyLoader) -> list[date]:
    """universe_loader 의 available_quarters → reference_date 리스트.

    `loader.reference_date(quarter)` 가 매니페스트의 `actual_reference_date`
    를 권위 정보로 반환 — holiday fallback (13/40 분기, PROGRESS §2) 보존.
    분기 라벨 → date 변환에서 *추론* 으로 대체하면 holiday fallback 권위가
    깨지므로 본 헬퍼 사용.

    universe_loader 책임 분리 유지 (§5.5.12 합의) — loader 는 universe 자체,
    walk-forward 모듈이 grid 추출 헬퍼 보유.
    """
    return [loader.reference_date(q) for q in loader.available_quarters()]
