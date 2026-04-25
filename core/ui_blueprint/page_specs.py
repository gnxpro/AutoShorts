from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
​
@dataclass
class SettingItemSpec:
key: str
label: str
value: str = ""
hint: str = ""
kind: str = "text"
editable: bool = False
@dataclass
class SettingsSectionSpec:
title: str
description: str = ""
items: List[SettingItemSpec] = field(default_factory=list)
@dataclass
class PageSpec:
title: str
subtitle: str = ""
sections: List[SettingsSectionSpec] = field(default_factory=list)
notices: List[str] = field(default_factory=list)
def to_dict(self) -> Dict[str, Any]:
return {
"title": self.title,
"subtitle": self.subtitle,
"sections": [
{
"title": section.title,
"description": section.description,
"items": [asdict(item) for item in section.items],
}
for section in self.sections
],
"notices": list(self.notices),
}
def build_settings_page_spec() -> PageSpec:
notices: List[str] = []
try:
from config.app_paths import CONFIG_DIR, DATA_DIR, GNX_CONFIG_FILE, GNX_MEMBER_FILE, ACCOUNTS_FILE, QUEUE_FILE
config_dir = str(CONFIG_DIR)
data_dir = str(DATA_DIR)
gnx_config = str(GNX_CONFIG_FILE)
gnx_member = str(GNX_MEMBER_FILE)
accounts_file = str(ACCOUNTS_FILE)
queue_file = str(QUEUE_FILE)
except Exception as exc:
notices.append(f"config.app_paths belum siap sepenuhnya: {exc}")
config_dir = "config/"
data_dir = "data/"
gnx_config = "config/gnx_config.json"
gnx_member = "config/gnx_member.json"
accounts_file = "data/accounts/social_accounts.json"
queue_file = "data/queue/production_queue.json"
sections = [
SettingsSectionSpec(
title="Configuration Paths",
description="Lokasi file konfigurasi utama aplikasi.",
items=[
SettingItemSpec(key="config_dir", label="Config Directory", value=config_dir),
SettingItemSpec(key="gnx_config", label="GNX Config File", value=gnx_config),
SettingItemSpec(key="gnx_member", label="GNX Member File", value=gnx_member),
],
),
SettingsSectionSpec(
title="Data Paths",
description="Lokasi penyimpanan data operasional aplikasi.",
items=[
SettingItemSpec(key="data_dir", label="Data Directory", value=data_dir),
SettingItemSpec(key="accounts_file", label="Accounts File", value=accounts_file),
SettingItemSpec(key="queue_file", label="Queue File", value=queue_file),
],
),
]
return PageSpec(
title="Settings",
subtitle="Ringkasan konfigurasi, path penting, dan status migrasi struktur.",
sections=sections,
notices=notices,
)
