"""app/utils/theme.py — 디자인 시스템 단일 출처 정합 테스트 (U2).

★ 핵심 keeper: `.streamlit/config.toml` 은 정적 파일이라 파이썬 상수와
물리적 단일화 불가 → 본 테스트가 toml ↔ PALETTE hex 정합을 CI 로 강제.
hex 가 갈라지면 (한쪽만 수정) CI 레드.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from app.utils import theme

_CONFIG_PATH = Path(__file__).resolve().parent.parent / ".streamlit" / "config.toml"


def _theme_section() -> dict:
    with _CONFIG_PATH.open("rb") as f:
        return tomllib.load(f)["theme"]


# ---- config.toml ↔ PALETTE 정합 (단일 출처 계약) ------------------------


def test_config_toml_exists() -> None:
    assert _CONFIG_PATH.exists(), ".streamlit/config.toml 부재 — U2 테마 미적용"


def test_config_matches_palette() -> None:
    """toml [theme] 색 == PALETTE (갈라지면 CI 레드)."""
    cfg = _theme_section()
    assert cfg["backgroundColor"] == theme.PALETTE["bg"]
    assert cfg["secondaryBackgroundColor"] == theme.PALETTE["surface"]
    assert cfg["textColor"] == theme.PALETTE["text"]
    assert cfg["primaryColor"] == theme.PALETTE["accent"]
    assert cfg["borderColor"] == theme.PALETTE["border"]
    assert cfg["linkColor"] == theme.PALETTE["accent"]  # 포인트 1색 원칙


def test_config_sidebar_matches_surface() -> None:
    """[theme.sidebar] = 표면색 (카드·사이드바 동일 표면, 헌법 4)."""
    cfg = _theme_section()
    assert cfg["sidebar"]["backgroundColor"] == theme.PALETTE["surface"]
    assert cfg["sidebar"]["borderColor"] == theme.PALETTE["border"]


def test_config_dark_base() -> None:
    cfg = _theme_section()
    assert cfg["base"] == "dark"


# ---- 헌법 차원 박제 ------------------------------------------------------


def test_palette_no_pure_black_or_white() -> None:
    """헌법 1: 순흑·순백 금지."""
    assert "#000000" not in theme.PALETTE.values()
    assert "#FFFFFF" not in {v.upper() for v in theme.PALETTE.values()}


def test_state_band_opacity_range() -> None:
    """헌법 3: 상태 띠 opacity 0.25~0.35."""
    assert 0.25 <= theme.STATE_BAND_OPACITY <= 0.35


def test_plotly_layout_uses_palette() -> None:
    """plotly 공통 기반이 팔레트 상수 공유 (U4 적용 전 기반 박제)."""
    layout = theme.PLOTLY_LAYOUT
    assert layout["paper_bgcolor"] == theme.PALETTE["bg"]
    assert layout["plot_bgcolor"] == theme.PALETTE["surface"]
    assert layout["xaxis"]["gridcolor"] == theme.PALETTE["border"]


def test_state_risk_colors_3_keys() -> None:
    """상태·위험 각 3 키 + 위험회피/높음 = 동일 red, 위험선호/낮음 = 동일 teal."""
    assert set(theme.STATE_COLORS) == {"위험회피", "중립", "위험선호"}
    assert set(theme.RISK_COLORS) == {"높음", "중간", "낮음"}
    assert theme.STATE_COLORS["위험회피"] == theme.RISK_COLORS["높음"]
    assert theme.STATE_COLORS["위험선호"] == theme.RISK_COLORS["낮음"]


def test_formatters_reexport_same_objects() -> None:
    """formatters 의 색 상수 = theme 동일 객체 (단일 출처, 사본 금지)."""
    from app.utils import formatters

    assert formatters.STATE_COLORS is theme.STATE_COLORS
    assert formatters.RISK_COLORS is theme.RISK_COLORS
    assert formatters.FALLBACK_COLOR == theme.FALLBACK_COLOR
