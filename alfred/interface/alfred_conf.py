"""
Alfred configuration management. Reads/writes alfred.conf as key=value pairs.
Used by Flask interface and automation scripts to share configuration state.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional


class AlfredConfig:
    """Simple key=value config file reader/writer."""

    # Expected configuration keys and their defaults
    DEFAULT_CONFIG = {
        'user_name': '',
        'context_type': '',  # 'home' or 'work'
        'primary_pain_point': '',
        'automation_type': '',  # 'morning_briefing', 'file_organizer', 'daily_checklist', 'email_draft', 'reminder_system'
        'automation_description': '',
        'first_action': '',
        'model_name': 'smollm2:1.7b',
        'briefing_time': '06:00',
        'watch_folder': '~/Documents/Alfred/notes',
        'output_method': 'file',  # 'file', 'notification', 'obsidian'
        'install_date': '',
        'last_update_check': '',
    }

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.expanduser('~/Alfred/config/alfred.conf')
        self.path = Path(config_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create config file with defaults if it doesn't exist."""
        if not self.path.exists():
            self.write(self.DEFAULT_CONFIG)

    def read(self) -> Dict[str, str]:
        """Read config file and return dict of key=value pairs."""
        config = self.DEFAULT_CONFIG.copy()
        if self.path.exists():
            with open(self.path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        if key in config:
                            config[key] = value
        return config

    def write(self, config: Dict[str, Any]) -> None:
        """Write config dict to file as key=value pairs."""
        lines = []
        lines.append('# Alfred Configuration')
        lines.append('')
        for key in sorted(self.DEFAULT_CONFIG.keys()):
            value = config.get(key, self.DEFAULT_CONFIG[key])
            lines.append(f'{key}="{value}"')

        with open(self.path, 'w') as f:
            f.write('\n'.join(lines) + '\n')

    def get(self, key: str, default: str = '') -> str:
        """Get a single config value."""
        config = self.read()
        return config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a single config value."""
        config = self.read()
        config[key] = str(value)
        self.write(config)

    def update(self, **kwargs) -> None:
        """Update multiple config values at once."""
        config = self.read()
        for key, value in kwargs.items():
            if key in self.DEFAULT_CONFIG:
                config[key] = str(value)
        self.write(config)


def read_conf(path: str = None) -> Dict[str, str]:
    """Convenience function: read entire config."""
    return AlfredConfig(path).read()


def write_conf(path: str = None, config: Dict[str, Any] = None) -> None:
    """Convenience function: write entire config."""
    if config is None:
        config = {}
    AlfredConfig(path).write(config)


def get_conf_value(key: str, path: str = None) -> str:
    """Convenience function: get single value."""
    return AlfredConfig(path).get(key)


def set_conf_value(key: str, value: Any, path: str = None) -> None:
    """Convenience function: set single value."""
    AlfredConfig(path).set(key, value)
