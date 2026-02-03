"""
AutoStart - Gestion du démarrage automatique avec Windows.

Utilise le registre Windows pour ajouter/supprimer l'application du démarrage.
"""

import sys
import os

try:
    import winreg
    WINREG_AVAILABLE = True
except ImportError:
    WINREG_AVAILABLE = False

APP_NAME = "WTVoiceChat"
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def get_executable_path() -> str:
    """Retourne le chemin de l'exécutable ou du script."""
    if getattr(sys, 'frozen', False):
        # Application packagée avec PyInstaller
        return sys.executable
    else:
        # Script Python
        return f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'


def is_auto_start_enabled() -> bool:
    """Vérifie si le démarrage automatique est activé."""
    if not WINREG_AVAILABLE:
        return False

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_PATH,
            0,
            winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except WindowsError:
            return False
        finally:
            winreg.CloseKey(key)
    except WindowsError:
        return False


def enable_auto_start() -> bool:
    """Active le démarrage automatique."""
    if not WINREG_AVAILABLE:
        return False

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_PATH,
            0,
            winreg.KEY_SET_VALUE
        )
        try:
            winreg.SetValueEx(
                key,
                APP_NAME,
                0,
                winreg.REG_SZ,
                get_executable_path()
            )
            return True
        finally:
            winreg.CloseKey(key)
    except WindowsError as e:
        print(f"Erreur lors de l'activation de l'auto-start: {e}")
        return False


def disable_auto_start() -> bool:
    """Désactive le démarrage automatique."""
    if not WINREG_AVAILABLE:
        return False

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_PATH,
            0,
            winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, APP_NAME)
            return True
        except WindowsError:
            # La valeur n'existe pas, c'est OK
            return True
        finally:
            winreg.CloseKey(key)
    except WindowsError as e:
        print(f"Erreur lors de la désactivation de l'auto-start: {e}")
        return False


def set_auto_start(enabled: bool) -> bool:
    """Active ou désactive le démarrage automatique."""
    if enabled:
        return enable_auto_start()
    else:
        return disable_auto_start()
