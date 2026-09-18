"""
Module: streamlit_app.styles.tokens
Design-system tokens: WCAG accessible White-Blue-Red clinical palette,
typography scale, spacing, and semantic risk tier badges.
"""

from typing import Dict, Tuple

# White-Blue-Red Clinical Palette
COLOR_PRIMARY = "#1E3A8A"        # Deep Clinical Navy Blue
COLOR_PRIMARY_HOVER = "#172554"  # Darker Navy
COLOR_PRIMARY_LIGHT = "#EFF6FF"  # Ice Blue Tint
COLOR_SECONDARY = "#2563EB"      # Vivid Clinical Blue
COLOR_ACCENT_BLUE = "#2563EB"    # Vivid Clinical Blue

COLOR_ALERT_RED = "#DC2626"      # Clinical Alert Red
COLOR_ALERT_RED_DARK = "#991B1B" # Deep Crimson
COLOR_ALERT_RED_BG = "#FEF2F2"   # Soft Red Alert Background
COLOR_ALERT_RED_BORDER = "#FCA5A5"

COLOR_BG_PAGE = "#F8FAFC"        # Pure Soft Light Slate Page Background
COLOR_SURFACE_CARD = "#FFFFFF"   # Pure Crisp White Card Surface
COLOR_BORDER = "#E2E8F0"         # Clean 1px Border
COLOR_BORDER_STRONG = "#CBD5E1"  # Structural Border

# Text Hierarchy
COLOR_TEXT_PRIMARY = "#0F172A"   # Crisp Slate-Black (WCAG AAA)
COLOR_TEXT_SECONDARY = "#334155" # Slate 700
COLOR_TEXT_MUTED = "#64748B"     # Slate 500

# Semantic Risk Tier System (WCAG AA Compliant on Light Backgrounds)
RISK_COLORS: Dict[str, Dict[str, str]] = {
    "High": {
        "bg": "#FEF2F2",
        "text": "#991B1B",
        "border": "#F87171",
        "accent": "#DC2626",
        "label": "High Risk"
    },
    "Elevated": {
        "bg": "#FFFBEB",
        "text": "#92400E",
        "border": "#FCD34D",
        "accent": "#D97706",
        "label": "Elevated Risk"
    },
    "Moderate": {
        "bg": "#F0F9FF",
        "text": "#0369A1",
        "border": "#BAE6FD",
        "accent": "#0284C7",
        "label": "Moderate Risk"
    },
    "Low": {
        "bg": "#F8FAFC",
        "text": "#475569",
        "border": "#CBD5E1",
        "accent": "#64748B",
        "label": "Low Risk"
    }
}

# Typography scale
FONT_FAMILY = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
FONT_SIZE_PAGE_TITLE = "1.6rem"
FONT_SIZE_SECTION_TITLE = "1.25rem"
FONT_SIZE_SUBHEADER = "1.05rem"
FONT_SIZE_BODY = "0.925rem"
FONT_SIZE_CAPTION = "0.80rem"


def get_risk_tier(prob: float, threshold: float = 0.5) -> Tuple[str, Dict[str, str]]:
    """
    Categorizes predicted probability into accessible semantic risk tier.
    Pairs color styling with unambiguous text label.
    """
    if prob >= 0.60:
        tier = "High"
    elif prob >= max(0.30, threshold * 0.75):
        tier = "Elevated"
    elif prob >= 0.15:
        tier = "Moderate"
    else:
        tier = "Low"
    return tier, RISK_COLORS[tier]


def render_risk_badge_html(prob: float, threshold: float = 0.5, multiplier: float = None) -> str:
    """Renders accessible HTML risk tier badge with text label and optional baseline multiplier."""
    tier, style = get_risk_tier(prob, threshold)
    mult_text = f" &bull; {multiplier:.1f}x baseline" if multiplier and multiplier > 1.0 else ""
    return (
        f'<span style="background-color: {style["bg"]}; color: {style["text"]}; '
        f'border: 1.5px solid {style["border"]}; padding: 4px 12px; border-radius: 6px; '
        f'font-weight: 700; font-size: 0.82rem; display: inline-flex; align-items: center; gap: 6px; letter-spacing: 0.02em;">'
        f'<span style="display:inline-block; width:8px; height:8px; border-radius:50%; background-color:{style["accent"]};"></span>'
        f'{style["label"]}{mult_text}</span>'
    )
