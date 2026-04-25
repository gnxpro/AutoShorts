from dataclasses import dataclass

@dataclass
class SummaryCardSpec:
    title: str
    value: str
    subtitle: str = ""
    tone: str = "neutral"
    icon: str = ""

def build_summary_card(title, value, subtitle="", tone="neutral", icon=""):
    return SummaryCardSpec(
        title=title,
        value=value,
        subtitle=subtitle,
        tone=tone,
        icon=icon,
    )
