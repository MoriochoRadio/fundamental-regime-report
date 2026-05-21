"""Features 모듈 — 재무비율 빌더 (단계 2 step 3).

본 패키지는 PROGRESS §5.5.14 박제 설계에 따라 빌더 빌더 API + lookahead
검증 2 단계 (α AST + β 런타임 mock) + fs_div 컬럼 동행 적용.

격리 원칙 (CLAUDE.md §5):
- 유니버스 변수 (KOSPI200QuarterlyLoader 심볼·`kospi200_member`·`index_weight`
  등) **import 금지** — tests/test_isolation.py (i) 자동 활성.
- 상폐/관리 메타 (`delisting()` 메서드·`DelistingDate`·`Reason` 등 컬럼)
  **참조 금지** — tests/test_isolation.py (ii) 자동 활성.
- 빌더가 받는 시점 인자 `as_of` 이후 데이터 **사용 금지** — (α) AST 화이트
  리스트 + (β) 런타임 mock contract 검증.
"""
