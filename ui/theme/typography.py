"""
GNX Studio typography tokens.
"""

FONT_FAMILY_BASE = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"

FONT_SIZE_XS = 11
FONT_SIZE_SM = 12
FONT_SIZE_MD = 14
FONT_SIZE_LG = 16
FONT_SIZE_XL = 18
FONT_SIZE_2XL = 22
FONT_SIZE_3XL = 28

FONT_WEIGHT_REGULAR = 400
FONT_WEIGHT_MEDIUM = 500
FONT_WEIGHT_SEMIBOLD = 600
FONT_WEIGHT_BOLD = 700

LINE_HEIGHT_SM = 1.2
LINE_HEIGHT_MD = 1.35
LINE_HEIGHT_LG = 1.5

TEXT_STYLE_CAPTION = {
    "font_family": FONT_FAMILY_BASE,
    "font_size": FONT_SIZE_XS,
    "font_weight": FONT_WEIGHT_REGULAR,
    "line_height": LINE_HEIGHT_SM,
}

TEXT_STYLE_BODY = {
    "font_family": FONT_FAMILY_BASE,
    "font_size": FONT_SIZE_MD,
    "font_weight": FONT_WEIGHT_REGULAR,
    "line_height": LINE_HEIGHT_LG,
}

TEXT_STYLE_BODY_STRONG = {
    "font_family": FONT_FAMILY_BASE,
    "font_size": FONT_SIZE_MD,
    "font_weight": FONT_WEIGHT_SEMIBOLD,
    "line_height": LINE_HEIGHT_LG,
}

TEXT_STYLE_TITLE = {
    "font_family": FONT_FAMILY_BASE,
    "font_size": FONT_SIZE_XL,
    "font_weight": FONT_WEIGHT_SEMIBOLD,
    "line_height": LINE_HEIGHT_MD,
}

TEXT_STYLE_HERO = {
    "font_family": FONT_FAMILY_BASE,
    "font_size": FONT_SIZE_3XL,
    "font_weight": FONT_WEIGHT_BOLD,
    "line_height": LINE_HEIGHT_MD,
}

TYPOGRAPHY = {
    "caption": TEXT_STYLE_CAPTION,
    "body": TEXT_STYLE_BODY,
    "body_strong": TEXT_STYLE_BODY_STRONG,
    "title": TEXT_STYLE_TITLE,
    "hero": TEXT_STYLE_HERO,
}

def get_typography():
    return dict(TYPOGRAPHY)
