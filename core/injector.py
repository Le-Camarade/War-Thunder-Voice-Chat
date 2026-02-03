"""
ChatInjector - Injection de texte dans le chat War Thunder.

Simule les frappes clavier pour envoyer un message dans le chat du jeu:
1. Entrée (ouvre le chat)
2. Ctrl+V (colle le texte)
3. Entrée (envoie le message)
"""

import time
import pyperclip
from pynput.keyboard import Controller, Key


class ChatInjector:
    """Injecteur de messages dans le chat War Thunder."""

    def __init__(self, delay_ms: int = 50):
        """
        Initialise l'injecteur.

        Args:
            delay_ms: Délai en millisecondes entre les actions
        """
        self.delay_ms = delay_ms
        self._keyboard = Controller()

    def _delay(self) -> None:
        """Applique le délai configuré."""
        time.sleep(self.delay_ms / 1000.0)

    def _press_key(self, key) -> None:
        """Appuie et relâche une touche."""
        self._keyboard.press(key)
        self._keyboard.release(key)

    def inject(self, text: str) -> bool:
        """
        Injecte le texte dans le chat War Thunder.

        Séquence:
        1. Appui sur Entrée pour ouvrir le chat
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
            self._press_key(Key.enter)
            self._delay()

            # 2. Copier le texte
            pyperclip.copy(text.strip())

            # 3. Coller (Ctrl+V)
            self._keyboard.press(Key.ctrl)
            self._keyboard.press('v')
            self._keyboard.release('v')
            self._keyboard.release(Key.ctrl)
            self._delay()

            # 4. Envoyer le message
            self._press_key(Key.enter)

            return True

        except Exception as e:
            print(f"Erreur lors de l'injection: {e}")
            return False

    def set_delay(self, delay_ms: int) -> None:
        """Change le délai entre les actions."""
        self.delay_ms = max(0, delay_ms)
