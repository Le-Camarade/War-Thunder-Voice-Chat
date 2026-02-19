"""
ConfigManager - Persistent configuration management.

Saves and loads user settings from a JSON file.
"""

import json
import os
import sys
from typing import Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class Config:
    """Application configuration structure."""

    # Joystick
    joystick_name: str = ""
    button_id: int = -1

    # Whisper
    model: str = "small"  # "tiny", "small", "medium"
    translate_to_english: bool = True  # Translate any language to English

    # Injection
    injection_delay_ms: int = 100
    chat_key: str = "enter"  # Key to open chat (enter, t, y, etc.)

    # Window
    window_geometry: str = "400x700+100+100"

    # Audio
    audio_device: Optional[int] = None

    # Auto-start
    auto_start: bool = False

    # TTS
    tts_engine_type: str = "offline"  # "offline" (pyttsx3) or "online" (edge-tts)
    tts_enabled: bool = False
    tts_own_username: str = ""
    tts_poll_interval_ms: int = 500
    tts_voice_id: str = ""
    tts_rate: int = 150
    tts_channel_team: bool = True
    tts_channel_all: bool = True
    tts_channel_squadron: bool = False
    tts_translate: bool = False
    tts_translate_lang: str = "en"  # Target language code (auto from voice)


class ConfigManager:
    """Configuration manager with JSON persistence."""

    DEFAULT_FILENAME = "config.json"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Config file path (None = app folder)
        """
        if config_path is None:
            if getattr(sys, 'frozen', False):
                # PyInstaller: save next to the .exe
                app_dir = os.path.dirname(sys.executable)
            else:
                # Normal Python: use script directory
                app_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(app_dir, self.DEFAULT_FILENAME)

        self.config_path = config_path
        self.config = Config()

    def load(self) -> Config:
        """
        Load configuration from file.

        Returns:
            Loaded Config object (or defaults if file missing)
        """
        if not os.path.exists(self.config_path):
            return self.config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Update only fields present in the file
            for key, value in data.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")

        return self.config

    def save(self) -> bool:
        """
        Save configuration to file.

        Returns:
            True if save succeeded
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return getattr(self.config, key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        if hasattr(self.config, key):
            setattr(self.config, key, value)

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.config = Config()
