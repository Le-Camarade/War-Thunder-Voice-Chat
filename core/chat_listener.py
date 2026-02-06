"""
ChatListener - Écoute du chat War Thunder via l'API JSON localhost:8111.

Interroge l'endpoint /gamechat pour détecter
les nouveaux messages de chat en temps réel.
"""

import re
import time
import threading
import logging
from dataclasses import dataclass
from typing import List, Callable, Optional

import requests

logger = logging.getLogger(__name__)

# Pattern pour extraire les coordonnées depuis les tags <color>
_COLOR_TAG_PATTERN = re.compile(r'<color=[^>]*>\s*(\[[^\]]*\])\s*</color>')


@dataclass
class ChatMessage:
    """Représente un message de chat War Thunder."""
    id: int                 # ID unique du serveur WT
    time: int               # Timestamp serveur (secondes de jeu)
    channel: str            # "Équipe", "Tous", "Escadron"
    sender: str             # "moon_marble@psn"
    content: str            # "Suivez moi !"
    enemy: bool             # True si message ennemi
    metadata: Optional[str] # "[D3, alt. 1800 m]" ou None


class ChatListener:
    """Écoute du chat War Thunder via l'API JSON /gamechat."""

    def __init__(
        self,
        base_url: str = "http://localhost:8111",
        poll_interval: float = 0.5,
        own_username: Optional[str] = None
    ):
        """
        Initialise le listener.

        Args:
            base_url: URL de base du serveur HTTP local War Thunder
            poll_interval: Intervalle de polling en secondes
            own_username: Pseudo du joueur (pour filtrer ses propres messages)
        """
        self._base_url = base_url.rstrip('/')
        self._poll_interval = poll_interval
        self._own_username = own_username

        self._last_id = 0
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._msg_count = 0

        # Callback
        self._on_new_message: Optional[Callable[[ChatMessage], None]] = None

    def set_on_new_message(self, callback: Callable[[ChatMessage], None]) -> None:
        """Définit le callback pour les nouveaux messages."""
        self._on_new_message = callback

    def set_own_username(self, username: str) -> None:
        """Définit le pseudo du joueur pour filtrer ses propres messages."""
        self._own_username = username

    def set_poll_interval(self, interval_ms: int) -> None:
        """Change l'intervalle de polling en millisecondes."""
        self._poll_interval = max(100, interval_ms) / 1000.0

    @staticmethod
    def _parse_message(record: dict) -> Optional[ChatMessage]:
        """
        Parse un enregistrement JSON de l'API /gamechat en ChatMessage.

        Args:
            record: Dict JSON avec les clés id, msg, sender, enemy, mode, time

        Returns:
            ChatMessage si le parsing réussit, None sinon
        """
        try:
            msg_text = record.get("msg", "")
            content = msg_text
            metadata = None

            # Extraire les coordonnées depuis les tags <color>
            meta_match = _COLOR_TAG_PATTERN.search(content)
            if meta_match:
                metadata = meta_match.group(1)
                content = _COLOR_TAG_PATTERN.sub('', content).strip()

            if not content:
                return None

            return ChatMessage(
                id=record.get("id", 0),
                time=record.get("time", 0),
                channel=record.get("mode", ""),
                sender=record.get("sender", ""),
                content=content,
                enemy=record.get("enemy", False),
                metadata=metadata
            )

        except Exception as e:
            logger.debug(f"Erreur parsing message: {e}")
            return None

    def _fetch_new_messages(self) -> List[ChatMessage]:
        """
        Récupère les nouveaux messages depuis l'API /gamechat.

        Returns:
            Liste des nouveaux ChatMessage
        """
        try:
            url = f"{self._base_url}/gamechat?lastId={self._last_id}"
            response = requests.get(url, timeout=2)
            response.raise_for_status()

            data = response.json()
            if not data:
                return []

            messages = []
            for record in data:
                msg = self._parse_message(record)
                if msg:
                    messages.append(msg)

            # Mettre à jour le dernier ID vu
            with self._lock:
                self._last_id = data[-1]["id"]

            return messages

        except requests.ConnectionError:
            return []
        except requests.Timeout:
            logger.debug("Timeout lors de la requête à /gamechat")
            return []
        except (requests.RequestException, ValueError) as e:
            logger.debug(f"Erreur API gamechat: {e}")
            return []

    def _poll_loop(self) -> None:
        """Boucle de polling dans un thread séparé."""
        while self._running:
            messages = self._fetch_new_messages()

            for msg in messages:
                # Ignorer ses propres messages
                if (self._own_username and
                        self._own_username.lower() == msg.sender.lower()):
                    with self._lock:
                        self._msg_count += 1
                    continue

                with self._lock:
                    self._msg_count += 1

                # Notifier le callback
                if self._on_new_message:
                    try:
                        self._on_new_message(msg)
                    except Exception as e:
                        logger.error(f"Erreur dans le callback on_new_message: {e}")

            time.sleep(self._poll_interval)

    def start(self) -> None:
        """Démarre le polling du chat."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Arrête le polling du chat."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def clear_history(self) -> None:
        """Remet le curseur à zéro (utile entre les parties)."""
        with self._lock:
            self._last_id = 0
            self._msg_count = 0

    def is_game_running(self) -> bool:
        """
        Vérifie si War Thunder est lancé (localhost:8111 répond).

        Returns:
            True si le serveur HTTP local répond
        """
        try:
            response = requests.get(self._base_url, timeout=0.5)
            return response.status_code == 200
        except requests.RequestException:
            return False

    @property
    def is_running(self) -> bool:
        """Retourne True si le polling est actif."""
        return self._running

    @property
    def seen_count(self) -> int:
        """Retourne le nombre de messages traités."""
        with self._lock:
            return self._msg_count
