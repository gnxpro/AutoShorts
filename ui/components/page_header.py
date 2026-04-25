from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

@dataclass
class HeaderAction:
    key: str
    label: str
    callback: Optional[Callable[..., Any]] = None
    variant: str = "secondary"

@dataclass
class PageHeaderSpec:
    title: str
    subtitle: str = ""
    eyebrow: str = ""
    actions: List[HeaderAction] = field(default_factory=list)

def build_page_header(title, subtitle="", eyebrow="", actions=None):
    return PageHeaderSpec(
        title=title,
        subtitle=subtitle,
        eyebrow=eyebrow,
        actions=actions or [],
    )
