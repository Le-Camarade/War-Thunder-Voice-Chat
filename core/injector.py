"""
ChatInjector - Injection de texte dans le chat War Thunder.

Utilise SendInput avec scancodes pour compatibilité DirectInput.
"""

import time
import ctypes
from ctypes import wintypes
import pyperclip

# Windows API
user32 = ctypes.windll.user32

# Input type
INPUT_KEYBOARD = 1

# Key event flags
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# Scancodes (hardware scancodes)
SCANCODES = {
    'enter': 0x1C,
    'return': 0x1C,
    't': 0x14,
    'y': 0x15,
    'u': 0x16,
    'v': 0x2F,
    'ctrl': 0x1D,
    'lctrl': 0x1D,
}


# Proper Windows structures for SendInput
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk', wintypes.WORD),
        ('wScan', wintypes.WORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(wintypes.ULONG))
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ('dx', wintypes.LONG),
        ('dy', wintypes.LONG),
        ('mouseData', wintypes.DWORD),
        ('dwFlags', wintypes.DWORD),
        ('time', wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(wintypes.ULONG))
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ('uMsg', wintypes.DWORD),
        ('wParamL', wintypes.WORD),
        ('wParamH', wintypes.WORD)
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ('mi', MOUSEINPUT),
        ('ki', KEYBDINPUT),
        ('hi', HARDWAREINPUT)
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ('type', wintypes.DWORD),
        ('union', INPUT_UNION)
    ]


class ChatInjector:
    """Injecteur de messages dans le chat War Thunder via SendInput."""

    def __init__(self, delay_ms: int = 100, chat_key: str = "enter"):
        """
        Initialise l'injecteur.

        Args:
            delay_ms: Délai en millisecondes entre les actions
            chat_key: Touche pour ouvrir le chat (enter, t, y, etc.)
        """
        self.delay_ms = delay_ms
        self.chat_key = chat_key

    def _delay(self) -> None:
        """Applique le délai configuré."""
        time.sleep(self.delay_ms / 1000.0)

    def _send_key(self, scancode: int, key_up: bool = False) -> None:
        """Envoie une touche via SendInput avec scancode."""
        flags = KEYEVENTF_SCANCODE
        if key_up:
            flags |= KEYEVENTF_KEYUP

        inp = INPUT()
        inp.type = INPUT_KEYBOARD
        inp.union.ki.wVk = 0
        inp.union.ki.wScan = scancode
        inp.union.ki.dwFlags = flags
        inp.union.ki.time = 0
        inp.union.ki.dwExtraInfo = None

        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def _press_key(self, key: str) -> None:
        """Appuie et relâche une touche."""
        scancode = SCANCODES.get(key.lower(), SCANCODES.get('enter'))
        self._send_key(scancode, key_up=False)
        time.sleep(0.02)
        self._send_key(scancode, key_up=True)
        time.sleep(0.02)

    def _press_ctrl_v(self) -> None:
        """Appuie sur Ctrl+V."""
        ctrl_scan = SCANCODES['ctrl']
        v_scan = SCANCODES['v']

        # Ctrl down
        self._send_key(ctrl_scan, key_up=False)
        time.sleep(0.02)
        # V down
        self._send_key(v_scan, key_up=False)
        time.sleep(0.02)
        # V up
        self._send_key(v_scan, key_up=True)
        time.sleep(0.02)
        # Ctrl up
        self._send_key(ctrl_scan, key_up=True)
        time.sleep(0.02)

    def inject(self, text: str) -> bool:
        """
        Injecte le texte dans le chat War Thunder.

        Séquence:
        1. Appui sur la touche chat pour ouvrir le chat
        2. Délai
        3. Copie du texte dans le presse-papier
        4. Ctrl+V pour coller
        5. Délai
        6. Appui sur Entrée pour envoyer

        Args:
            text: Le texte à injecter

        Returns:
            True si l'injection a réussi, False sinon
        """
        if not text or not text.strip():
            return False

        try:
            # 1. Ouvrir le chat
            self._press_key(self.chat_key)
            self._delay()

            # 2. Copier le texte
            pyperclip.copy(text.strip())
            time.sleep(0.05)  # Délai pour le presse-papier

            # 3. Coller (Ctrl+V)
            self._press_ctrl_v()
            self._delay()

            # 4. Envoyer le message
            self._press_key('enter')

            return True

        except Exception as e:
            print(f"Erreur lors de l'injection: {e}")
            return False

    def set_delay(self, delay_ms: int) -> None:
        """Change le délai entre les actions."""
        self.delay_ms = max(0, delay_ms)

    def set_chat_key(self, key: str) -> None:
        """Change la touche pour ouvrir le chat."""
        self.chat_key = key
