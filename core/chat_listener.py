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

# War Thunder T-menu radio commands to ignore in TTS (all client languages)
RADIO_COMMANDS = {
    # ===== ENGLISH =====
    "Attack the A point!", "Attack the B point!", "Attack the C point!",
    "Attack the D point!", "Attack the E point!",
    "Attack the enemy!", "Attack enemy troops!", "Attack hostile base!",
    "Defend the A point!", "Defend the B point!", "Defend the C point!",
    "Defend the D point!", "Defend the E point!",
    "Capture the A point!", "Capture the B point!", "Capture the C point!",
    "Capture the D point!", "Capture the E point!",
    "Cover me!", "Somebody cover me!", "I need backup!", "Need backup!",
    "I need cover!", "Provide air cover for our ground units!",
    "Provide air cover for our ground troops!",
    "Follow me!", "Getting down!", "Returning to the base!", "Returning to base!",
    "Leading for landing!", "Bail out!",
    "Reloading!", "Repairing!", "I'm running low on ammo!", "I'm out of ammo!",
    "Enemy spotted!", "Attention to the map!",
    "Attention to the designated grid square!",
    "An enemy is capturing our point!",
    "Yes!", "No!", "I agree!", "Negative!", "I refuse!", "Never!",
    "Sorry!", "Thank you!", "Gramercy!", "Well done!", "Bravo!", "Excellent!",
    "Engaging!", "Taking the lead!", "Going in!",

    # ===== FRENCH =====
    "Attaquez le point A !", "Attaquez le point B !", "Attaquez le point C !",
    "Attaquez le point D !", "Attaquez le point E !",
    "Attaquez l'ennemi !", "Attaquez les troupes ennemies !",
    "Attaquez la base hostile !",
    "Défendez le point A !", "Défendez le point B !", "Défendez le point C !",
    "Défendez le point D !", "Défendez le point E !",
    "Capturez le point A !", "Capturez le point B !", "Capturez le point C !",
    "Capturez le point D !", "Capturez le point E !",
    "Couvrez-moi !", "Quelqu'un, couvrez-moi !", "J'ai besoin de renfort !",
    "Besoin de renfort !", "J'ai besoin de couverture !",
    "Fournissez une couverture aérienne à nos troupes au sol !",
    "Suivez-moi !", "Je descends !", "Retour à la base !",
    "En approche pour atterrir !", "Évacuez !",
    "Rechargement !", "Réparation !", "Je manque de munitions !",
    "Plus de munitions !",
    "Ennemi repéré !", "Attention à la carte !",
    "Attention au secteur désigné !",
    "Un ennemi capture notre point !",
    "Oui !", "Non !", "D'accord !", "Négatif !", "Je refuse !", "Jamais !",
    "Désolé !", "Merci !", "Bien joué !", "Bravo !", "Excellent !",
    "J'engage !", "Je prends la tête !", "J'y vais !",

    # ===== GERMAN =====
    "Punkt A angreifen!", "Punkt B angreifen!", "Punkt C angreifen!",
    "Punkt D angreifen!", "Punkt E angreifen!",
    "Greift den Feind an!", "Feindliche Truppen angreifen!",
    "Feindliche Basis angreifen!",
    "Punkt A verteidigen!", "Punkt B verteidigen!", "Punkt C verteidigen!",
    "Punkt D verteidigen!", "Punkt E verteidigen!",
    "Punkt A einnehmen!", "Punkt B einnehmen!", "Punkt C einnehmen!",
    "Punkt D einnehmen!", "Punkt E einnehmen!",
    "Deckung!", "Gebt mir Deckung!", "Ich brauche Verstärkung!",
    "Verstärkung nötig!", "Ich brauche Deckung!",
    "Luftunterstützung für unsere Bodentruppen!",
    "Folgt mir!", "Ich gehe runter!", "Rückkehr zur Basis!",
    "Landeanflug!", "Aussteigen!",
    "Nachladen!", "Reparatur!", "Munition wird knapp!", "Keine Munition mehr!",
    "Feind gesichtet!", "Achtung auf die Karte!",
    "Achtung auf das markierte Planquadrat!",
    "Ein Feind erobert unseren Punkt!",
    "Ja!", "Nein!", "Einverstanden!", "Negativ!", "Ich lehne ab!", "Niemals!",
    "Entschuldigung!", "Danke!", "Gut gemacht!", "Ausgezeichnet!",
    "Angriff!", "Ich übernehme die Führung!", "Ich greife an!",

    # ===== RUSSIAN =====
    "Атакуйте точку A!", "Атакуйте точку B!", "Атакуйте точку C!",
    "Атакуйте точку D!", "Атакуйте точку E!",
    "Атакуйте противника!", "Атакуйте вражеские войска!",
    "Атакуйте вражескую базу!",
    "Защищайте точку A!", "Защищайте точку B!", "Защищайте точку C!",
    "Защищайте точку D!", "Защищайте точку E!",
    "Захватите точку A!", "Захватите точку B!", "Захватите точку C!",
    "Захватите точку D!", "Захватите точку E!",
    "Прикройте меня!", "Кто-нибудь, прикройте!", "Нужна поддержка!",
    "Мне нужна помощь!", "Нужно прикрытие!",
    "Обеспечьте воздушное прикрытие наземных войск!",
    "За мной!", "Иду на снижение!", "Возвращаюсь на базу!",
    "Захожу на посадку!", "Покидаю машину!",
    "Перезарядка!", "Ремонт!", "Заканчиваются боеприпасы!",
    "Нет боеприпасов!",
    "Противник обнаружен!", "Внимание на карту!",
    "Внимание на указанный квадрат!",
    "Противник захватывает нашу точку!",
    "Да!", "Нет!", "Согласен!", "Отрицательно!", "Отказываюсь!", "Никогда!",
    "Извините!", "Спасибо!", "Отлично!", "Превосходно!",
    "Вступаю в бой!", "Беру командование!", "Иду в атаку!",

    # ===== SPANISH =====
    "¡Atacad el punto A!", "¡Atacad el punto B!", "¡Atacad el punto C!",
    "¡Atacad el punto D!", "¡Atacad el punto E!",
    "¡Atacad al enemigo!", "¡Atacad a las tropas enemigas!",
    "¡Atacad la base hostil!",
    "¡Defended el punto A!", "¡Defended el punto B!", "¡Defended el punto C!",
    "¡Defended el punto D!", "¡Defended el punto E!",
    "¡Capturad el punto A!", "¡Capturad el punto B!", "¡Capturad el punto C!",
    "¡Capturad el punto D!", "¡Capturad el punto E!",
    "¡Cubridme!", "¡Que alguien me cubra!", "¡Necesito refuerzos!",
    "¡Necesito cobertura!",
    "¡Seguidme!", "¡Desciendo!", "¡Volviendo a la base!",
    "¡Aproximación para aterrizar!", "¡Abandonad el vehículo!",
    "¡Recargando!", "¡Reparando!", "¡Me queda poca munición!",
    "¡Sin munición!",
    "¡Enemigo avistado!", "¡Atención al mapa!",
    "¡Atención al sector designado!",
    "¡Un enemigo está capturando nuestro punto!",
    "¡Sí!", "¡No!", "¡De acuerdo!", "¡Negativo!", "¡Me niego!", "¡Nunca!",
    "¡Lo siento!", "¡Gracias!", "¡Bien hecho!", "¡Excelente!",
    "¡Atacando!", "¡Tomo el mando!", "¡Voy a por ellos!",

    # ===== ITALIAN =====
    "Attaccate il punto A!", "Attaccate il punto B!", "Attaccate il punto C!",
    "Attaccate il punto D!", "Attaccate il punto E!",
    "Attaccate il nemico!", "Attaccate le truppe nemiche!",
    "Copritemi!", "Qualcuno mi copra!", "Ho bisogno di rinforzi!",
    "Seguitemi!", "Sto scendendo!", "Ritorno alla base!",
    "Ricarica!", "Riparazione!",
    "Nemico avvistato!", "Attenzione alla mappa!",
    "Sì!", "No!", "D'accordo!", "Negativo!", "Mi rifiuto!", "Mai!",
    "Scusa!", "Grazie!", "Ben fatto!", "Eccellente!",

    # ===== POLISH =====
    "Atakujcie punkt A!", "Atakujcie punkt B!", "Atakujcie punkt C!",
    "Atakujcie punkt D!", "Atakujcie punkt E!",
    "Atakujcie wroga!", "Brońcie punktu A!", "Brońcie punktu B!",
    "Brońcie punktu C!", "Brońcie punktu D!", "Brońcie punktu E!",
    "Osłaniajcie mnie!", "Potrzebuję wsparcia!", "Za mną!",
    "Wracam do bazy!", "Przeładowanie!", "Naprawa!",
    "Wróg wykryty!", "Uwaga na mapę!",
    "Tak!", "Nie!", "Zgadzam się!", "Negatywnie!", "Odmawiam!", "Nigdy!",
    "Przepraszam!", "Dziękuję!", "Dobra robota!", "Doskonale!",

    # ===== PORTUGUESE =====
    "Ataquem o ponto A!", "Ataquem o ponto B!", "Ataquem o ponto C!",
    "Ataquem o ponto D!", "Ataquem o ponto E!",
    "Ataquem o inimigo!", "Defendam o ponto A!", "Defendam o ponto B!",
    "Defendam o ponto C!", "Defendam o ponto D!", "Defendam o ponto E!",
    "Me cubram!", "Preciso de reforços!", "Sigam-me!",
    "Retornando à base!", "Recarregando!", "Reparando!",
    "Inimigo avistado!", "Atenção ao mapa!",
    "Sim!", "Não!", "Concordo!", "Negativo!", "Recuso!", "Nunca!",
    "Desculpe!", "Obrigado!", "Bem feito!", "Excelente!",
}


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
