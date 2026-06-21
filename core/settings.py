"""Settings persistence for SubXeta."""
import json
import platform
from pathlib import Path


def get_config_dir() -> Path:
    """Get the config directory for the current OS."""
    if platform.system() == "Windows":
        config_dir = Path.home() / "AppData" / "Roaming" / "SubXeta"
    else:  # Linux/macOS
        config_dir = Path.home() / ".config" / "SubXeta"

    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def load_settings() -> dict:
    """Load settings from config file. Returns defaults if file doesn't exist."""
    config_file = get_config_dir() / "settings.json"
    defaults = {
        "model": "large",
        "force_cpu": False,
        "template": "Zeta Reticuli Template.comp",
        "fps": 24
    }

    if not config_file.exists():
        return defaults

    try:
        with open(config_file) as f:
            return json.load(f)
    except Exception:
        return defaults


def save_settings(settings: dict) -> None:
    """Save settings to config file."""
    config_file = get_config_dir() / "settings.json"
    with open(config_file, 'w') as f:
        json.dump(settings, f, indent=2)
