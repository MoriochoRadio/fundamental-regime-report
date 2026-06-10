"""다크 금융 리포트 디자인 시스템 — 색·스타일 단일 출처 (U2).

팔레트 A "차콜 + 시안" (U2 결정 ①, 2026-06). 디자인 헌법:
1. 색 절제 — 어두운 배경(순흑 X) + 표면 반 단계 밝게 + 포인트 1색(시안).
   상태 3종은 탈채도 red/gray/teal.
2. 위계 — 숫자 크게·설명 작게 (config.toml 타이포 옵션, U3 적용).
3. 차트 주인공 — plotly 다크 통일·그리드 희미·상태 띠 opacity 0.30 (U4 적용).
4. 일관성 — 여백·곡률·테두리 전 화면 동일 (config.toml).

★ 단일 출처 계약: `.streamlit/config.toml` 은 정적 파일이라 물리적 단일화
불가 → `tests/test_theme.py` 가 toml ↔ PALETTE hex 정합을 CI 로 강제한다.
색 hex 를 바꿀 때는 *본 모듈과 config.toml 을 함께* 수정해야 한다.

CSS 주입 0 (U2 결정 ② — 순수 Streamlit 유지, 한계 발견 시 재논의).
"""

from __future__ import annotations

# === 팔레트 A — 차콜 + 시안 (TradingView 감각) ==============================
PALETTE: dict[str, str] = {
    "bg": "#131722",  # 배경 (순흑 X)
    "surface": "#1E222D",  # 카드·사이드바 표면 (반 단계 밝게)
    "border": "#2A2E39",  # 테두리·그리드 기저
    "text": "#D1D4DC",  # 텍스트 주
    "text_muted": "#787B86",  # 텍스트 보조·캡션
    "accent": "#29B6D1",  # 포인트 단 1색 (시안)
}

# 결측·미지 라벨 공통 fallback (텍스트 보조색과 동일 — 시각 소음 최소)
FALLBACK_COLOR = "#787B86"

# === 상태 3종 — 탈채도 red / gray / teal (헌법 1) ===========================
STATE_COLORS: dict[str, str] = {
    "위험회피": "#E06C75",
    "중립": "#6B7280",
    "위험선호": "#4DB6AC",
}

# === 위험 3 단계 — 낮음 teal / 중간 탈채도 amber / 높음 red (U2 결정 ③) ====
RISK_COLORS: dict[str, str] = {
    "높음": "#E06C75",
    "중간": "#D4A04C",
    "낮음": "#4DB6AC",
}

# === st.badge 색 매핑 (U3 — 이모지 대체) ====================================
# badge 의 color 이름은 config.toml 의 redColor/greenColor/orangeColor/
# grayColor 가 위 탈채도 hex 로 정렬한다 (test_theme 정합 강제).
# 텍스트 라벨 항상 병기 — 색맹 대응 (NFR-7) 유지.
BADGE_COLOR_MAP: dict[str, str] = {
    # 위험 단계
    "낮음": "green",
    "중간": "orange",
    "높음": "red",
    # 시장 상태
    "위험선호": "green",
    "중립": "gray",
    "위험회피": "red",
    # 결측 공통
    "—": "gray",
}

# config.toml 의 색 이름 → 본 팔레트 hex (test_theme 가 toml 과 정합 검증)
THEME_NAMED_COLORS: dict[str, str] = {
    "redColor": "#E06C75",
    "greenColor": "#4DB6AC",
    "orangeColor": "#D4A04C",
    "grayColor": "#6B7280",
}

# === plotly 공통 기반 (U2 는 상수만 — 차트별 적용은 U4) =====================
# 상태 배경 띠 opacity (헌법 3: 0.25~0.35)
STATE_BAND_OPACITY = 0.30

# fig.update_layout(**PLOTLY_LAYOUT) 용 공통 다크 레이아웃
PLOTLY_LAYOUT: dict = {
    "paper_bgcolor": PALETTE["bg"],
    "plot_bgcolor": PALETTE["surface"],
    "font": {"color": PALETTE["text_muted"]},
    "xaxis": {"gridcolor": PALETTE["border"], "zerolinecolor": PALETTE["border"]},
    "yaxis": {"gridcolor": PALETTE["border"], "zerolinecolor": PALETTE["border"]},
    "hoverlabel": {"bgcolor": PALETTE["surface"], "font": {"color": PALETTE["text"]}},
}
