"""
GNX Studio design tokens.
Used by new UI components and pages.
"""

# Spacing
SPACE_2 = 2
SPACE_4 = 4
SPACE_6 = 6
SPACE_8 = 8
SPACE_10 = 10
SPACE_12 = 12
SPACE_14 = 14
SPACE_16 = 16
SPACE_20 = 20
SPACE_24 = 24
SPACE_28 = 28
SPACE_32 = 32
SPACE_40 = 40
SPACE_48 = 48

# Radius
RADIUS_SM = 6
RADIUS_MD = 10
RADIUS_LG = 14
RADIUS_XL = 18
RADIUS_PILL = 999

# Border / stroke
BORDER_WIDTH_SM = 1
BORDER_WIDTH_MD = 2

# Common sizing
BUTTON_HEIGHT_SM = 32
BUTTON_HEIGHT_MD = 38
BUTTON_HEIGHT_LG = 44

INPUT_HEIGHT_MD = 38
INPUT_HEIGHT_LG = 44

SIDEBAR_WIDTH = 260
HEADER_HEIGHT = 56
CARD_MIN_HEIGHT = 96

# Layout padding
PAGE_PADDING_X = 20
PAGE_PADDING_Y = 16
SECTION_GAP = 16
CARD_GAP = 12

# Shadow names for future use
SHADOW_SM = "shadow_sm"
SHADOW_MD = "shadow_md"
SHADOW_LG = "shadow_lg"

THEME_TOKENS = {
    "spacing": {
        "2": SPACE_2,
        "4": SPACE_4,
        "6": SPACE_6,
        "8": SPACE_8,
        "10": SPACE_10,
        "12": SPACE_12,
        "14": SPACE_14,
        "16": SPACE_16,
        "20": SPACE_20,
        "24": SPACE_24,
        "28": SPACE_28,
        "32": SPACE_32,
        "40": SPACE_40,
        "48": SPACE_48,
    },
    "radius": {
        "sm": RADIUS_SM,
        "md": RADIUS_MD,
        "lg": RADIUS_LG,
        "xl": RADIUS_XL,
        "pill": RADIUS_PILL,
    },
}

def get_theme_tokens():
    return dict(THEME_TOKENS)
