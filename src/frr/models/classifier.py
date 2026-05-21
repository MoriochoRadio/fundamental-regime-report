"""LightGBM 분류기 + Platt sigmoid 캘리브레이션 (PROGRESS §5.5.16 B-2).

학습 흐름:
    1. LightGBMClassifier (`is_unbalance` 또는 `class_weight` 별 분기)
    2. CalibratedClassifierCV (sigmoid = Platt scaling)
    3. fit → predict_proba 활용

설계 결정 (§5.5.16 B-2):
- class weight: balanced (sample weight 자동) + unweighted ablation
- 캘리브레이션: sigmoid (Platt) — 양성 20 적어 isotonic 과적합 회피
- random_state 시드 고정 (재현성)

학습 임계 미달 (양성 20, §5.5.7) 대응:
- LightGBM 의 `num_leaves` 작게 (15 기본) — 과적합 회피
- `min_data_in_leaf` 5 — 양성 희소성에 맞춤
- 본 하이퍼파라미터는 baseline. B-4 결과에 따라 추가 튜닝.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.calibration import CalibratedClassifierCV

ClassWeight = Literal["balanced", "unweighted"]
Calibration = Literal["sigmoid", "isotonic", "none"]


def make_base_classifier(
    *,
    class_weight: ClassWeight = "balanced",
    random_state: int = 42,
    num_leaves: int = 15,
    min_data_in_leaf: int = 5,
    n_estimators: int = 100,
    learning_rate: float = 0.05,
) -> LGBMClassifier:
    """LightGBM 베이스 분류기 (캘리브레이션 미적용).

    class_weight 옵션:
    - "balanced": LightGBM 의 `is_unbalance=True` (sample weight 자동 보정)
    - "unweighted": 보정 없음 (ablation 비교 대상)

    하이퍼파라미터:
    - num_leaves=15 (과적합 회피, 양성 희소성)
    - min_data_in_leaf=5 (leaf 분할 임계, 양성 20 에 맞춤)
    - n_estimators=100 (baseline, B-4 튜닝 가능)
    """
    is_unbalance = class_weight == "balanced"
    return LGBMClassifier(
        objective="binary",
        is_unbalance=is_unbalance,
        num_leaves=num_leaves,
        min_data_in_leaf=min_data_in_leaf,
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        random_state=random_state,
        verbose=-1,
    )


def train_classifier(
    X_train: pd.DataFrame,
    y_train: pd.Series | np.ndarray,
    *,
    class_weight: ClassWeight = "balanced",
    calibration: Calibration = "sigmoid",
    random_state: int = 42,
    cv: int = 3,
) -> CalibratedClassifierCV | LGBMClassifier:
    """LightGBM + 캘리브레이션 학습.

    Args:
        X_train: features DataFrame (numeric + 명시 categorical fs_div).
        y_train: 0/1 라벨.
        class_weight: balanced / unweighted (ablation).
        calibration: sigmoid (Platt) / isotonic / none.
        random_state: 시드 고정 (재현성).
        cv: CalibratedClassifierCV 의 cross-validation fold 수.

    Returns:
        학습된 분류기. predict_proba(X)[:, 1] 로 양성 확률 사용.

    Raises:
        ValueError: y 가 모두 동일 클래스 (학습 불가능).
    """
    y_array = np.asarray(y_train)
    if len(np.unique(y_array)) < 2:
        raise ValueError(
            f"train_classifier: y 가 단일 클래스 ({np.unique(y_array).tolist()}). "
            "양성·음성 모두 필요."
        )

    base = make_base_classifier(class_weight=class_weight, random_state=random_state)

    if calibration == "none":
        base.fit(X_train, y_array)
        return base

    # CalibratedClassifierCV — 양성 적을 때 cv 조정 필요
    n_positive = int(y_array.sum())
    effective_cv = min(cv, n_positive) if n_positive > 0 else 2
    effective_cv = max(2, effective_cv)

    cal = CalibratedClassifierCV(
        estimator=base,
        method=calibration,
        cv=effective_cv,
    )
    cal.fit(X_train, y_array)
    return cal


def predict_proba(
    classifier: CalibratedClassifierCV | LGBMClassifier,
    X: pd.DataFrame,
) -> np.ndarray:
    """양성 확률 1D array 반환.

    `classifier.predict_proba(X)` 가 (n, 2) shape 이면 [:, 1] 선택.
    """
    proba = classifier.predict_proba(X)
    if proba.ndim != 2 or proba.shape[1] != 2:
        raise ValueError(f"predict_proba: 예상 shape (n, 2), 실제 {proba.shape}")
    return proba[:, 1]
