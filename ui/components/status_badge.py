from dataclasses import dataclass

STATUS_TONES = {
    "neutral": {"bg": "#2B3240", "fg": "#F5F7FA"},
    "success": {"bg": "#163E2A", "fg": "#86EFAC"},
    "warning": {"bg": "#4A3411", "fg": "#FCD34D"},
    "danger": {"bg": "#4C1D1D", "fg": "#FCA5A5"},
    "info": {"bg": "#0C3B52", "fg": "#7DD3FC"},
}

@dataclass
class StatusBadgeSpec:
    label: str
    tone: str = "neutral"

    @property
    def colors(self):
        return STATUS_TONES.get(self.tone, STATUS_TONES["neutral"])

def build_status_badge(label, tone="neutral"):
    return StatusBadgeSpec(label=label, tone=tone)
