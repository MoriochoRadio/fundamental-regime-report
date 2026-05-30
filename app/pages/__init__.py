"""app/pages — Streamlit 페이지 모듈 (페이지 통합 단계).

각 페이지는 `render()` 함수를 export 한다 (pure 렌더링, 반환 None).
main.py shell 이 SidebarNav 반환 key 로 dispatch.

docs/ui_design.md §1.1~1.4 페이지 spec 매핑:
- overview (§1.1) — 단위 (i)
- ticker_analysis (§1.2) — 단위 (j)
- state_timeline (§1.3) — 단위 (k)
- limitations (§1.4) — 단위 (l)
"""
