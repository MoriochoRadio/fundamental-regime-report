"""Models 모듈 — 부실 스코어링 (단계 2 B-3, PROGRESS §5.5.16).

설계 결정 박제:
- 모델: LightGBM (CLAUDE.md §8.4)
- 캘리브레이션: Platt sigmoid (양성 20 적어 safer, isotonic 과적합 회피)
- class weight: balanced + unweighted 2 가지 ablation
- 평가 지표: PR-AUC + AUC + Brier + Calibration (ECE) + Top-K precision (D8)
- 평가 단위: 종목 (ticker × as_of) 단위 pooled across folds — fold 단위는 보조
- 양성 N=3 통계적 변동성 — bootstrap CI 옵션 지원 (B-4 활성)
"""
