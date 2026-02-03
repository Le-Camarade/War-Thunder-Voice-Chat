"""
ConfigManager - Gestion de la configuration persistante.

Sauvegarde et charge les paramètres utilisateur depuis un fichier JSON.
"""

import json
import os
from typing import Any, Optional
from dataclasses import dataclass, asdict, field


@dataclass
class Config:
    """Structure de configuration de l'application."""

    # Joystick
    joystick_name: str = ""
    button_id: int = -1

    # Whisper
    mode: str = "cpu"  # "cpu" ou "gpu"
    model: str = "small"  # "tiny", "small", "medium"

    # Injection
    injection_delay_ms: int = 50

    # Fenêtre
    window_geometry: str = "400x820+100+100"

    # Audio
    audio_device: Optional[int] = None


class ConfigManager:
    """Gestionnaire de configuration avec persistence JSON."""

    DEFAULT_FILENAME = "config.json"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialise le gestionnaire de configuration.

        Args:
            config_path: Chemin du fichier de config (None = dossier de l'app)
        """
        if config_path is None:
            # Utiliser le dossier de l'application
            app_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(app_dir, self.DEFAULT_FILENAME)

        self.config_path = config_path
        self.config = Config()

    def load(self) -> Config:
        """
        Charge la configuration depuis le fichier.

        Returns:
            L'objet Config chargé (ou les valeurs par défaut si fichier absent)
        """
        if not os.path.exists(self.config_path):
            return self.config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Mettre à jour uniquement les champs présents dans le fichier
            for key, value in data.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

        except (json.JSONDecodeError, IOError) as e:
            print(f"Erreur lors du chargement de la config: {e}")

        return self.config

    def save(self) -> bool:
        """
        Sauvegarde la configuration dans le fichier.

        Returns:
            True si la sauvegarde a réussi
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Erreur lors de la sauvegarde de la config: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Récupère une valeur de configuration."""
        return getattr(self.config, key, default)

    def set(self, key: str, value: Any) -> None:
        """Définit une valeur de configuration."""
        if hasattr(self.config, key):
            setattr(self.config, key, value)

    def reset(self) -> None:
        """Réinitialise la configuration aux valeurs par défaut."""
        self.config = Config()
