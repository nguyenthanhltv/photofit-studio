"""Template management system for PhotoFit Studio.

Allows saving, loading, and applying processing presets as templates.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from copy import deepcopy

# Default template structure
DEFAULT_TEMPLATE = {
    "name": "",
    "description": "",
    "version": "1.0",
    "beautify": {
        "enabled": True,
        "level": "medium",
        "skin_smoothing": True,
        "brightness_auto": True,
        "hair_smoothing": True
    },
    "background": {
        "enabled": True,
        "mode": "solid_color",
        "color": "#FFFFFF",
        "edge_refinement": True,
        "refine_level": "high"
    },
    "ai_enhance": {
        "enabled": True,
        "level": "medium",
        "enhance_sharpness": True,
        "enhance_colors": True,
        "denoise": True,
        "super_resolution": False,
        "scale": 2,
        "auto_exposure": True
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
    }
}

# Built-in templates
BUILTIN_TEMPLATES = {
    "cmnd_cccd": {
        "name": "CMND/CCCD",
        "description": "Ảnh thẻ căn cước công dân - 3x4 - Nền xanh",
        "beautify": {"enabled": True, "level": "medium"},
        "background": {"enabled": True, "color": "#1C86EE"},
        "resize": {"preset": "3x4"},
        "ai_enhance": {"enabled": True, "level": "medium"}
    },
    "passport": {
        "name": "Hộ chiếu",
        "description": "Ảnh passport quốc tế - 3.5x4.5 - Nền trắng",
        "beautify": {"enabled": True, "level": "light"},
        "background": {"enabled": True, "color": "#FFFFFF"},
        "resize": {"preset": "passport"},
        "ai_enhance": {"enabled": True, "level": "medium"}
    },
    "visa": {
        "name": "Visa",
        "description": "Ảnh visa - 4x6 - Nền trắng",
        "beautify": {"enabled": True, "level": "medium"},
        "background": {"enabled": True, "color": "#FFFFFF"},
        "resize": {"preset": "4x6"},
        "ai_enhance": {"enabled": True, "level": "strong"}
    },
    "the_nho": {
        "name": "Thẻ nhỏ",
        "description": "Ảnh thẻ nhỏ - 2x3 - Nền trắng",
        "beautify": {"enabled": True, "level": "light"},
        "background": {"enabled": True, "color": "#FFFFFF"},
        "resize": {"preset": "2x3"},
        "ai_enhance": {"enabled": True, "level": "light"}
    },
    "professional": {
        "name": "Professional",
        "description": "Ảnh headshot chuyên nghiệp - Nền xám",
        "beautify": {"enabled": True, "level": "medium"},
        "background": {"enabled": True, "color": "#E8E8E8"},
        "resize": {"preset": "3x4"},
        "ai_enhance": {"enabled": True, "level": "strong"}
    }
}


class TemplateManager:
    """Manages processing templates - save, load, apply."""

    def __init__(self, templates_folder: str = None):
        self.templates_folder = templates_folder or self._default_templates_folder()
        os.makedirs(self.templates_folder, exist_ok=True)

    @staticmethod
    def _default_templates_folder() -> str:
        base = Path(__file__).parent.parent
        return str(base / "templates")

    def get_builtin_templates(self) -> Dict[str, dict]:
        """Get all built-in templates."""
        return deepcopy(BUILTIN_TEMPLATES)

    def get_builtin_template(self, template_id: str) -> Optional[dict]:
        """Get a specific built-in template."""
        return deepcopy(BUILTIN_TEMPLATES.get(template_id))

    def list_templates(self) -> List[Dict[str, str]]:
        """List all available templates (built-in + custom)."""
        templates = []
        
        # Add built-in templates
        for tid, tpl in BUILTIN_TEMPLATES.items():
            templates.append({
                "id": tid,
                "name": tpl["name"],
                "description": tpl.get("description", ""),
                "type": "builtin"
            })
        
        # Add custom templates
        if os.path.exists(self.templates_folder):
            for filename in os.listdir(self.templates_folder):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.templates_folder, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        templates.append({
                            "id": f"custom_{filename[:-5]}",
                            "name": data.get("name", filename[:-5]),
                            "description": data.get("description", ""),
                            "type": "custom",
                            "filename": filename
                        })
                    except:
                        pass
        
        return templates

    def save_template(self, name: str, config: dict, description: str = "") -> str:
        """Save a custom template.
        
        Args:
            name: Template name
            config: Configuration dict to save
            description: Optional description
            
        Returns:
            Path to saved template file
        """
        # Create safe filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        filename = f"{safe_name}.json"
        filepath = os.path.join(self.templates_folder, filename)
        
        template = {
            "name": name,
            "description": description,
            "version": "1.0",
            "created_at": str(Path(__file__).stat().st_ctime),
            "config": config
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        return filepath

    def load_template(self, template_id: str) -> Optional[dict]:
        """Load a template by ID.
        
        Args:
            template_id: Template ID (builtin id or custom_{filename})
            
        Returns:
            Template config dict or None if not found
        """
        # Check built-in templates
        if template_id in BUILTIN_TEMPLATES:
            return self._build_full_config(BUILTIN_TEMPLATES[template_id])
        
        # Check custom templates
        if template_id.startswith("custom_"):
            filename = template_id[7:] + ".json"
            filepath = os.path.join(self.templates_folder, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    return self._build_full_config(data.get("config", {}))
                except:
                    pass
        
        return None

    def delete_template(self, template_id: str) -> bool:
        """Delete a custom template.
        
        Args:
            template_id: Template ID to delete
            
        Returns:
            True if deleted, False if not found or is builtin
        """
        if template_id.startswith("custom_"):
            filename = template_id[7:] + ".json"
            filepath = os.path.join(self.templates_folder, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
        return False

    def apply_template_to_config(self, template_id: str, config: dict) -> dict:
        """Apply a template to existing config.
        
        Args:
            template_id: Template ID to apply
            config: Current config to merge with template
            
        Returns:
            Merged config dict
        """
        template_config = self.load_template(template_id)
        if template_config is None:
            return config
        
        # Merge template with existing config
        return self._merge_config(config, template_config)

    def _build_full_config(self, partial: dict) -> dict:
        """Build full config from partial template config."""
        full = deepcopy(DEFAULT_TEMPLATE)
        self._merge_config(full, partial)
        return full

    def _merge_config(self, base: dict, override: dict) -> dict:
        """Recursively merge override into base."""
        for key, value in override.items():
            if key == "config":
                # Handle custom template format
                self._merge_config(base, value)
            elif key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = deepcopy(value)
        return base

    def export_template(self, template_id: str, filepath: str) -> bool:
        """Export a template to a specific path.
        
        Args:
            template_id: Template ID to export
            filepath: Destination path
            
        Returns:
            True if successful
        """
        template_config = self.load_template(template_id)
        if template_config is None:
            return False
        
        # Get template info
        info = {}
        if template_id in BUILTIN_TEMPLATES:
            info = BUILTIN_TEMPLATES[template_id].copy()
        else:
            filename = template_id[7:] + ".json"
            fpath = os.path.join(self.templates_folder, filename)
            if os.path.exists(fpath):
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                except:
                    pass
        
        export_data = {
            "name": info.get("name", template_id),
            "description": info.get("description", ""),
            "version": "1.0",
            "config": template_config
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return True

    def import_template(self, filepath: str) -> Optional[str]:
        """Import a template from a file.
        
        Args:
            filepath: Path to template file
            
        Returns:
            Template ID if successful
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            name = data.get("name", "Imported")
            config = data.get("config", {})
            
            if config:
                return self.save_template(name, config, data.get("description", ""))
        except:
            pass
        
        return None
