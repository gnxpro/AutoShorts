from dataclasses import dataclass

@dataclass
class LoadingBlockSpec:
    label: str = "Loading..."
    detail: str = ""
    active: bool = True

def build_loading_block(label="Loading...", detail="", active=True):
    return LoadingBlockSpec(
        label=label,
        detail=detail,
        active=active,
    )
