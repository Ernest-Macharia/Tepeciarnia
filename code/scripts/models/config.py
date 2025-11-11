import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from utils.path_utils import CONFIG_PATH
from utils.system_utils import current_system_locale

# Get logger for this module
logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        logger.debug("Initializing Config class")
        self.data: Dict[str, Any] = {}
        self.load()
        logger.info("Config initialization completed")

    def load(self):
        """Load configuration from file"""
        logger.debug(f"Loading configuration from: {CONFIG_PATH}")
        try:
            if CONFIG_PATH.exists():
                logger.debug("Config file exists, reading contents")
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logger.info(f"Configuration loaded successfully - {len(self.data)} keys loaded")
                logger.debug(f"Config keys: {list(self.data.keys())}")
            else:
                logger.warning("Config file does not exist, creating empty configuration")
                self.data = {}
                self.save()
                logger.info("Empty configuration created and saved")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse config file (invalid JSON): {e}")
            logger.warning("Creating empty configuration due to parse error")
            self.data = {}
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}", exc_info=True)
            logger.warning("Creating empty configuration due to load error")
            self.data = {}

    def save(self):
        """Save configuration to file"""
        logger.debug(f"Saving configuration to: {CONFIG_PATH}")
        try:
            # Ensure directory exists
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Config directory ensured: {CONFIG_PATH.parent}")
            
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2)
            logger.info(f"Configuration saved successfully - {len(self.data)} keys saved")
            logger.debug(f"Saved config keys: {list(self.data.keys())}")
        except PermissionError as e:
            logger.error(f"Permission denied saving config file: {e}")
            logger.warning("Configuration changes not persisted due to permission error")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}", exc_info=True)
            logger.warning("Configuration changes not persisted due to save error")

    def get(self, key: str, default=None):
        """Get configuration value with logging"""
        value = self.data.get(key, default)
        logger.debug(f"Config get - key: '{key}', value: {value}, default: {default}")
        return value

    def set(self, key: str, value):
        """Set configuration value with logging"""
        old_value = self.data.get(key)
        logger.debug(f"Config set - key: '{key}', old_value: {old_value}, new_value: {value}")
        
        self.data[key] = value
        logger.debug(f"Config value updated in memory, saving to file")
        
        try:
            self.save()
            logger.info(f"Config key '{key}' updated successfully")
        except Exception as e:
            logger.error(f"Config key '{key}' updated in memory but failed to save: {e}")

    def get_last_video(self) -> Optional[str]:
        """Get last video path with logging"""
        last_video = self.get("last_video")
        logger.debug(f"Retrieved last video path: {last_video}")
        return last_video

    def set_last_video(self, path: str):
        """Set last video path with logging"""
        logger.info(f"Setting last video path: {path}")
        self.set("last_video", path)
        logger.debug(f"Last video path saved: {path}")

    def get_scheduler_settings(self) -> tuple:
        """Get scheduler settings with logging"""
        source = self.get("scheduler_source")
        interval = self.get("scheduler_interval", 30)
        enabled = self.get("scheduler_enabled", False)
        
        logger.debug(f"Retrieved scheduler settings - source: {source}, interval: {interval}, enabled: {enabled}")
        return source, interval, enabled

    def set_scheduler_settings(self, source: str, interval: int, enabled: bool):
        """Set scheduler settings with logging"""
        logger.info(f"Setting scheduler settings - source: {source}, interval: {interval}, enabled: {enabled}")
        self.set("scheduler_source", source)
        self.set("scheduler_interval", interval)
        self.set("scheduler_enabled", enabled)
        logger.debug("Scheduler settings saved successfully")

    def get_range_preference(self) -> str:
        """Get range preference with logging"""
        range_pref = self.get("range_preference", "all")
        logger.debug(f"Retrieved range preference: {range_pref}")
        return range_pref

    def set_range_preference(self, range_type: str):
        """Set range preference with logging"""
        logger.info(f"Setting range preference: {range_type}")
        self.set("range_preference", range_type)
        logger.debug(f"Range preference saved: {range_type}")

    def get_language(self) -> str:
        """Get language preference with logging"""
        config_language = self.get("language")
        system_language = current_system_locale()
        final_language = config_language or system_language
        
        logger.debug(f"Language preference - config: {config_language}, system: {system_language}, final: {final_language}")
        return final_language

    def set_language(self, language: str):
        """Set language preference with logging"""
        logger.info(f"Setting language preference: {language}")
        self.set("language", language)
        logger.debug(f"Language preference saved: {language}")

    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings for debugging purposes"""
        logger.debug("Retrieving all configuration settings")
        return self.data.copy()

    def clear(self):
        """Clear all configuration data with logging"""
        logger.warning("Clearing all configuration data")
        old_key_count = len(self.data)
        self.data = {}
        try:
            self.save()
            logger.info(f"Configuration cleared - {old_key_count} keys removed")
        except Exception as e:
            logger.error(f"Configuration cleared in memory but failed to save: {e}")

    def __str__(self) -> str:
        """String representation for debugging"""
        key_count = len(self.data)
        return f"Config(keys={key_count}, path={CONFIG_PATH})"