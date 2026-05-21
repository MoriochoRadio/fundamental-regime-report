"""LightGBM 분류기 + Platt sigmoid 단위 테스트 (PROGRESS §5.5.16 B-3).

합성 데이터로 학습 reproducibility · class weight 효과 · 캘리브레이션 동작 검증.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from frr.models.classifier import (
    make_base_classifier,
    predict_proba,
    train_classifier,
)


def _synthetic_data(
    n_samples: int = 200,
    n_features: int = 4,
    positive_rate: float = 0.1,
    random_state: int = 42,
) -> tuple[pd.DataFrame, np.ndarray]:
    """합성 features + 라벨 (양성 비율 조정 가능)."""
    rng = np.random.default_rng(random_state)
    X = rng.standard_normal((n_samples, n_features))
    # 첫 feature 와 양성 약한 상관
    logits = X[:, 0] * 1.5 - 2.0  # 양성 비율 ~12%
    proba = 1.0 / (1.0 + np.exp(-logits))
    y = (rng.random(n_samples) < proba * (positive_rate / proba.mean())).astype(int)
    X_df = pd.DataFrame(X, columns=[f"f{i}" for i in range(n_features)])
    return X_df, y


# ---- 기본 학습 + predict_proba ------------------------------------------


def test_train_classifier_basic_balanced() -> None:
    """balanced + sigmoid 학습 + predict_proba 1D 양성 확률 반환."""
    X, y = _synthetic_data(n_samples=200, positive_rate=0.1)
    clf = train_classifier(X, y, class_weight="balanced", calibration="sigmoid")
    proba = predict_proba(clf, X)
    assert proba.shape == (200,)
    assert proba.min() >= 0.0 and proba.max() <= 1.0


def test_train_classifier_unweighted_ablation() -> None:
    """unweighted ablation — class_weight="unweighted" 학습 가능."""
    X, y = _synthetic_data(n_samples=200, positive_rate=0.1)
    clf = train_classifier(X, y, class_weight="unweighted", calibration="sigmoid")
    proba = predict_proba(clf, X)
    assert proba.shape == (200,)


def test_train_classifier_no_calibration() -> None:
    """calibration='none' → LGBMClassifier 직접 반환."""
    from lightgbm import LGBMClassifier

    X, y = _synthetic_data(n_samples=200, positive_rate=0.15)
    clf = train_classifier(X, y, calibration="none")
    assert isinstance(clf, LGBMClassifier)


# ---- 시드 고정 재현성 ---------------------------------------------------


def test_train_classifier_reproducibility() -> None:
    """동일 시드 → 동일 predict_proba (재현성 — §5 방법론적 원칙)."""
    X, y = _synthetic_data(n_samples=200, positive_rate=0.1)
    clf1 = train_classifier(X, y, random_state=42, calibration="sigmoid")
    clf2 = train_classifier(X, y, random_state=42, calibration="sigmoid")
    proba1 = predict_proba(clf1, X)
    proba2 = predict_proba(clf2, X)
    np.testing.assert_allclose(proba1, proba2, atol=1e-10)


# ---- 경계: 단일 클래스 ValueError ---------------------------------------


def test_train_classifier_single_class_raises() -> None:
    """y 가 모두 동일 클래스 → ValueError (학습 불가능)."""
    X, _ = _synthetic_data(n_samples=100)
    y_all_zero = np.zeros(100, dtype=int)
    with pytest.raises(ValueError, match="단일 클래스"):
        train_classifier(X, y_all_zero)


# ---- balanced vs unweighted 효과 검증 ------------------------------------


def test_balanced_yields_different_proba_than_unweighted() -> None:
    """balanced 와 unweighted 의 predict_proba 차이 존재 (ablation 의미).

    동일 시드 + 동일 데이터에서 class_weight 만 달라지면 결과도 달라야 *ablation
    의미* 가짐.
    """
    X, y = _synthetic_data(n_samples=300, positive_rate=0.08, random_state=42)
    clf_b = train_classifier(X, y, class_weight="balanced", random_state=42)
    clf_u = train_classifier(X, y, class_weight="unweighted", random_state=42)
    proba_b = predict_proba(clf_b, X)
    proba_u = predict_proba(clf_u, X)
    # 두 결과가 *완전히 동일하면* class_weight 효과 0 (불가능, ablation 무의미)
    diff = np.abs(proba_b - proba_u).max()
    assert diff > 1e-3, f"balanced vs unweighted diff={diff:.6f} — class_weight 효과 없음"


# ---- make_base_classifier 단위 ------------------------------------------


def test_make_base_classifier_returns_lgbm() -> None:
    """make_base_classifier 가 LGBMClassifier 반환 + 하이퍼파라미터 박제."""
    from lightgbm import LGBMClassifier

    clf = make_base_classifier(class_weight="balanced", random_state=42)
    assert isinstance(clf, LGBMClassifier)
    assert clf.num_leaves == 15
    assert clf.min_data_in_leaf == 5
    assert clf.n_estimators == 100
    assert clf.is_unbalance is True


def test_make_base_classifier_unweighted() -> None:
    """unweighted → is_unbalance=False."""
    clf = make_base_classifier(class_weight="unweighted")
    assert clf.is_unbalance is False
