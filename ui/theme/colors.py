"""
GNX Studio theme colors.
Safe migration layer:
- keeps compatibility with legacy core.theme_constants when present
- provides stable named colors for new ui.theme imports
"""

try:
    from core.theme_constants import *  # legacy fallback
except Exception:
    pass

def _pick(name, default):
    return globals().get(name, default)

# Core palette
COLOR_BG            = _pick("COLOR_BG", "#0F1115")
COLOR_SURFACE       = _pick("COLOR_SURFACE", "#171A21")
COLOR_SURFACE_ALT   = _pick("COLOR_SURFACE_ALT", "#1E232D")
COLOR_BORDER        = _pick("COLOR_BORDER", "#2B3240")

COLOR_TEXT          = _pick("COLOR_TEXT", "#F5F7FA")
COLOR_TEXT_MUTED    = _pick("COLOR_TEXT_MUTED", "#9AA4B2")
COLOR_TEXT_SOFT     = _pick("COLOR_TEXT_SOFT", "#C7CFD9")

COLOR_PRIMARY       = _pick("COLOR_PRIMARY", "#6D5DF6")
COLOR_PRIMARY_HOVER = _pick("COLOR_PRIMARY_HOVER", "#7C6BFF")
COLOR_SECONDARY     = _pick("COLOR_SECONDARY", "#00C2A8")

COLOR_SUCCESS       = _pick("COLOR_SUCCESS", "#22C55E")
COLOR_WARNING       = _pick("COLOR_WARNING", "#F59E0B")
COLOR_DANGER        = _pick("COLOR_DANGER", "#EF4444")
COLOR_INFO          = _pick("COLOR_INFO", "#38BDF8")

# Alias names for new code
BG = COLOR_BG
SURFACE = COLOR_SURFACE
SURFACE_ALT = COLOR_SURFACE_ALT
BORDER = COLOR_BORDER

TEXT_PRIMARY = COLOR_TEXT
TEXT_MUTED = COLOR_TEXT_MUTED
TEXT_SOFT = COLOR_TEXT_SOFT

PRIMARY = COLOR_PRIMARY
PRIMARY_HOVER = COLOR_PRIMARY_HOVER
SECONDARY = COLOR_SECONDARY

SUCCESS = COLOR_SUCCESS
WARNING = COLOR_WARNING
DANGER = COLOR_DANGER
INFO = COLOR_INFO

THEME_COLORS = {
    "bg": BG,
    "surface": SURFACE,
    "surface_alt": SURFACE_ALT,
    "border": BORDER,
    "text_primary": TEXT_PRIMARY,
    "text_muted": TEXT_MUTED,
    "text_soft": TEXT_SOFT,
    "primary": PRIMARY,
    "primary_hover": PRIMARY_HOVER,
    "secondary": SECONDARY,
    "success": SUCCESS,
    "warning": WARNING,
    "danger": DANGER,
    "info": INFO,
}

def get_theme_colors():
    return dict(THEME_COLORS)
