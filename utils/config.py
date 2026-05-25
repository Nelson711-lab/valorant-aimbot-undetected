"""
Configuration manager for Valorant Aimbot.
Handles loading, saving, and validating config.json.
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger("ValorantAimbot.Config")

DEFAULT_CONFIG = {
    "aimbot": {
        "enabled": True,
        "fov": 5.0,
        "smoothness": 3.5,
        "target_bone": "head",
        "max_distance": 300,
        "humanization": True,
        "recoil_compensation": False,
    },
    "triggerbot": {
        "enabled": False,
        "delay_min_ms": 120,
        "delay_max_ms": 280,
        "auto_pistol": False,
        "burst_fire": False,
    },
    "display": {
        "resolution": "1920x1080",
        "fps_target": 60,
        "show_fps": False,
        "show_bounding_box": True,
    },
    "overlay": {
        "enabled": True,
        "show_targets": True,
        "show_fov_circle": True,
        "crosshair_color": [0, 255, 0],
    },
    "profiles": {
        "active": "default",
        "auto_switch_on_agent": False,
    },
    "security": {
        "panic_key": "end",
        "auto_disable_on_death": True,
        "screenshot_blocker": False,
    },
}


class ConfigManager:
    """Manages configuration for the aimbot."""
    
    def __init__(self, config_path="config.json"):
        self.config_path = Path(config_path)
        self.data = self._load()
        self._validate()
    
    def _load(self):
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                logger.info(f"Config loaded from {self.config_path}")
                return self._merge_with_defaults(data)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load config: {e}")
        
        logger.info("Using default configuration.")
        return DEFAULT_CONFIG.copy()
    
    def _merge_with_defaults(self, data):
        """Merge loaded config with defaults for any missing keys."""
        merged = DEFAULT_CONFIG.copy()
        
        for section in merged:
            if section in data:
                if isinstance(merged[section], dict):
                    merged[section].update(data[section])
                else:
                    merged[section] = data[section]
        
        return merged
    
    def _validate(self):
        """Validate configuration values."""
        validations = [
            ("aimbot.fov", 0.1, 20.0),
            ("aimbot.smoothness", 0.1, 10.0),
            ("triggerbot.delay_min_ms", 50, 500),
            ("triggerbot.delay_max_ms", 50, 500),
        ]
        
        for path, min_val, max_val in validations:
            section, key = path.split('.')
            value = self.data.get(section, {}).get(key, 0)
            
            if value < min_val or value > max_val:
                logger.warning(
                    f"Config {path}={value} out of range ({min_val}-{max_val}). Using default."
                )
                self.data[section][key] = DEFAULT_CONFIG[section][key]
    
    def save(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.data, f, indent=4)
            logger.debug("Configuration saved.")
        except IOError as e:
            logger.error(f"Could not save config: {e}")
    
    def get(self, section, key=None):
        """Get configuration value."""
        if section not in self.data:
            return None
        if key is None:
            return self.data[section]
        return self.data[section].get(key)
    
    def set(self, section, key, value):
        """Set configuration value and save."""
        if section not in self.data:
            self.data[section] = {}
        self.data[section][key] = value
        self.save()
    
    def reset_to_default(self):
        """Reset all configuration to defaults."""
        self.data = DEFAULT_CONFIG.copy()
        self.save()
        logger.info("Configuration reset to defaults.")
    
    def export(self, filepath):
        """Export configuration to a file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.data, f, indent=4)
            logger.info(f"Config exported to {filepath}")
        except IOError as e:
            logger.error(f"Export failed: {e}")
    
    def import_config(self, filepath):
        """Import configuration from a file."""
        try:
            with open(filepath, 'r') as f:
                imported = json.load(f)
            self.data = self._merge_with_defaults(imported)
            self._validate()
            self.save()
            logger.info(f"Config imported from {filepath}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Import failed: {e}")
