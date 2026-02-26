"""Configuration management for Image Processor."""

import json
import os
from pathlib import Path
from copy import deepcopy

DEFAULT_CONFIG = {
    "beautify": {
        "enabled": True,
        "level": "medium",
        "skin_smoothing": True,
        "brightness_auto": True,
        "hair_smoothing": True,
        "eye_enhancement": False,
        "teeth_whitening": False
    },
    "background": {
        "enabled": True,
        "mode": "solid_color",
        "color": "#FFFFFF",
        "edge_refinement": True
    },
    "ai_enhance": {
        "enabled": True,
        "level": "medium",
        "enhance_sharpness": True,
        "enhance_colors": True,
        "denoise": True,
        "super_resolution": False,
        "scale": 2
    },
    "resize": {
        "enabled": True,
        "preset": "3x4",
        "width_px": 354,
        "height_px": 472,
        "dpi": 300,
        "maintain_aspect": True,
        "auto_subject_fit": True,
        "distance_level": "medium"
    },
    "output": {
        "format": "jpg",
        "quality": 95,
        "naming": "{name}",
        "overwrite": False
    },
    "processing": {
        "parallel_workers": 4,
        "skip_on_error": True,
        "log_errors": True
    },
    "settings": {
        "language": "VI"
    }
}

SIZE_PRESETS = {
    "2x3": {"width_px": 236, "height_px": 354, "label": "2x3cm - Thẻ nhỏ"},
    "3x4": {"width_px": 354, "height_px": 472, "label": "3x4cm - CMND/CCCD"},
    "4x6": {"width_px": 472, "height_px": 709, "label": "4x6cm - Visa/Hộ chiếu"},
    "passport": {"width_px": 413, "height_px": 531, "label": "3.5x4.5cm - Passport ICAO"},
    "custom": {"width_px": 354, "height_px": 472, "label": "Custom"}
}

BG_COLOR_PRESETS = {
    "white": {"hex": "#FFFFFF", "label": "Trắng - Ảnh thẻ phổ thông"},
    "blue": {"hex": "#1C86EE", "label": "Xanh dương - CMND/CCCD"},
    "red": {"hex": "#DC143C", "label": "Đỏ - Một số loại thẻ"},
    "green": {"hex": "#00A86B", "label": "Xanh lá - Hộ chiếu"},
    "light_gray": {"hex": "#E8E8E8", "label": "Xám nhạt - Professional"},
    "custom": {"hex": "#FFFFFF", "label": "Custom"}
}


class ConfigManager:
    """Manages application configuration with load/save support."""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or self._default_config_path()
        self.config = deepcopy(DEFAULT_CONFIG)
        self.load()

    @staticmethod
    def _default_config_path() -> str:
        base = Path(__file__).parent.parent
        return str(base / "config.json")

    def load(self) -> dict:
        """Load config from file, merge with defaults for missing keys."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                self._merge(self.config, saved)
            except (json.JSONDecodeError, IOError):
                pass
        return self.config

    def save(self) -> None:
        """Save current config to file."""
        os.makedirs(os.path.dirname(self.config_path) or ".", exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get(self, section: str, key: str = None):
        """Get config value. Returns section dict if key is None."""
        sec = self.config.get(section, {})
        if key is None:
            return sec
        return sec.get(key)

    def set(self, section: str, key: str, value) -> None:
        """Set a config value."""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value

    def reset(self) -> None:
        """Reset config to defaults."""
        self.config = deepcopy(DEFAULT_CONFIG)

    def get_size_preset(self, name: str) -> dict:
        """Get size preset by name."""
        return SIZE_PRESETS.get(name, SIZE_PRESETS["3x4"])

    def get_bg_color_preset(self, name: str) -> dict:
        """Get background color preset by name."""
        return BG_COLOR_PRESETS.get(name, BG_COLOR_PRESETS["white"])

    def apply_size_preset(self, name: str) -> None:
        """Apply a size preset to current config."""
        preset = self.get_size_preset(name)
        self.config["resize"]["preset"] = name
        self.config["resize"]["width_px"] = preset["width_px"]
        self.config["resize"]["height_px"] = preset["height_px"]

    @staticmethod
    def _merge(base: dict, override: dict) -> None:
        """Recursively merge override into base."""
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                ConfigManager._merge(base[k], v)
            else:
                base[k] = v
