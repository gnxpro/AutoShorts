from dataclasses import dataclass
from typing import Optional

@dataclass
class EmptyStateSpec:
    title: str
    message: str
    action_label: str = ""
    action_key: str = ""
    icon: str = "info"

def build_empty_state(title, message, action_label="", action_key="", icon="info"):
    return EmptyStateSpec(
        title=title,
        message=message,
        action_label=action_label,
        action_key=action_key,
        icon=icon,
    )
