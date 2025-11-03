import json
from pathlib import Path
from typing import Dict, Any, Optional

from utils.path_utils import CONFIG_PATH
from utils.system_utils import current_system_locale

class Config:
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self):
        """Load configuration from file"""
        try:
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            else:
                self.data = {}
                self.save()
        except Exception:
            self.data = {}

    def save(self):
        """Save configuration to file"""
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
        except Exception:
            pass

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value):
        self.data[key] = value
        self.save()

    def get_last_video(self) -> Optional[str]:
        return self.get("last_video")

    def set_last_video(self, path: str):
        self.set("last_video", path)

    def get_scheduler_settings(self) -> tuple:
        source = self.get("scheduler_source")
        interval = self.get("scheduler_interval", 30)
        enabled = self.get("scheduler_enabled", False)
        return source, interval, enabled

    def set_scheduler_settings(self, source: str, interval: int, enabled: bool):
        self.set("scheduler_source", source)
        self.set("scheduler_interval", interval)
        self.set("scheduler_enabled", enabled)

    def get_range_preference(self) -> str:
        return self.get("range_preference", "all")

    def set_range_preference(self, range_type: str):
        self.set("range_preference", range_type)

    def get_language(self) -> str:
        return self.get("language") or current_system_locale()

    def set_language(self, language: str):
        self.set("language", language)