"""
JoystickManager - Gestion des joysticks avec pygame.

Détecte les joysticks connectés et émet des événements
lors des appuis/relâchements de boutons.
"""

import pygame
import threading
import time
from typing import Callable, Optional, Dict, List
from dataclasses import dataclass


@dataclass
class JoystickInfo:
    """Information sur un joystick détecté."""
    id: int
    name: str
    num_buttons: int
    num_axes: int


class JoystickManager:
    """Gestionnaire de joysticks avec détection et événements."""

    def __init__(self):
        self._joysticks: Dict[int, pygame.joystick.Joystick] = {}
        self._running = False
        self._poll_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Callbacks
        self._on_button_down: Optional[Callable[[int, int], None]] = None
        self._on_button_up: Optional[Callable[[int, int], None]] = None
        self._on_any_button: Optional[Callable[[int, int], None]] = None

        # État des boutons (pour détecter les changements)
        self._button_states: Dict[int, Dict[int, bool]] = {}

        # Joystick sélectionné
        self._selected_joystick_id: Optional[int] = None
        self._ptt_button_id: int = -1

        # Initialiser pygame
        pygame.init()
        pygame.joystick.init()

    def refresh(self) -> List[JoystickInfo]:
        """
        Rafraîchit la liste des joysticks connectés.

        Returns:
            Liste des joysticks détectés
        """
        with self._lock:
            # Fermer les anciens joysticks
            for joy in self._joysticks.values():
                joy.quit()
            self._joysticks.clear()
            self._button_states.clear()

            # Ré-initialiser
            pygame.joystick.quit()
            pygame.joystick.init()

            # Détecter les joysticks
            joysticks = []
            for i in range(pygame.joystick.get_count()):
                joy = pygame.joystick.Joystick(i)
                joy.init()
                self._joysticks[i] = joy
                self._button_states[i] = {
                    b: False for b in range(joy.get_numbuttons())
                }
                joysticks.append(JoystickInfo(
                    id=i,
                    name=joy.get_name(),
                    num_buttons=joy.get_numbuttons(),
                    num_axes=joy.get_numaxes()
                ))

            return joysticks

    def get_joysticks(self) -> List[JoystickInfo]:
        """Retourne la liste des joysticks sans rafraîchir."""
        with self._lock:
            return [
                JoystickInfo(
                    id=i,
                    name=joy.get_name(),
                    num_buttons=joy.get_numbuttons(),
                    num_axes=joy.get_numaxes()
                )
                for i, joy in self._joysticks.items()
            ]

    def select_joystick(self, joystick_id: int) -> bool:
        """Sélectionne le joystick à utiliser pour le PTT."""
        with self._lock:
            if joystick_id in self._joysticks:
                self._selected_joystick_id = joystick_id
                return True
            return False

    def select_joystick_by_name(self, name: str) -> bool:
        """Sélectionne un joystick par son nom."""
        with self._lock:
            for i, joy in self._joysticks.items():
                if joy.get_name() == name:
                    self._selected_joystick_id = i
                    return True
            return False

    def set_ptt_button(self, button_id: int) -> None:
        """Définit le bouton PTT."""
        self._ptt_button_id = button_id

    def set_on_button_down(self, callback: Callable[[int, int], None]) -> None:
        """Définit le callback pour l'appui sur le bouton PTT."""
        self._on_button_down = callback

    def set_on_button_up(self, callback: Callable[[int, int], None]) -> None:
        """Définit le callback pour le relâchement du bouton PTT."""
        self._on_button_up = callback

    def set_on_any_button(self, callback: Callable[[int, int], None]) -> None:
        """Définit le callback pour n'importe quel bouton (pour l'assignation)."""
        self._on_any_button = callback

    def start(self) -> None:
        """Démarre le polling des joysticks dans un thread séparé."""
        if self._running:
            return

        self._running = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def stop(self) -> None:
        """Arrête le polling."""
        self._running = False
        if self._poll_thread:
            self._poll_thread.join(timeout=1.0)
            self._poll_thread = None

    def _poll_loop(self) -> None:
        """Boucle de polling des événements joystick."""
        while self._running:
            try:
                # Pomper les événements pygame
                pygame.event.pump()

                with self._lock:
                    for joy_id, joy in self._joysticks.items():
                        for btn_id in range(joy.get_numbuttons()):
                            current = joy.get_button(btn_id)
                            previous = self._button_states[joy_id].get(btn_id, False)

                            if current != previous:
                                self._button_states[joy_id][btn_id] = current

                                # Callback pour n'importe quel bouton
                                if current and self._on_any_button:
                                    self._on_any_button(joy_id, btn_id)

                                # Callbacks PTT (seulement pour le joystick sélectionné)
                                if (joy_id == self._selected_joystick_id and
                                    btn_id == self._ptt_button_id):
                                    if current and self._on_button_down:
                                        self._on_button_down(joy_id, btn_id)
                                    elif not current and self._on_button_up:
                                        self._on_button_up(joy_id, btn_id)

                time.sleep(0.01)  # 100Hz polling

            except Exception as e:
                print(f"Erreur polling joystick: {e}")
                time.sleep(0.1)

    def cleanup(self) -> None:
        """Nettoie les ressources."""
        self.stop()
        with self._lock:
            for joy in self._joysticks.values():
                joy.quit()
            self._joysticks.clear()
        pygame.joystick.quit()

    @property
    def selected_joystick_name(self) -> Optional[str]:
        """Retourne le nom du joystick sélectionné."""
        with self._lock:
            if self._selected_joystick_id is not None:
                joy = self._joysticks.get(self._selected_joystick_id)
                if joy:
                    return joy.get_name()
        return None
