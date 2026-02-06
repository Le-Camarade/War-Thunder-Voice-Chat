"""
TTSEngine - Synthèse vocale pour les messages chat.

Supporte deux moteurs:
- Offline: pyttsx3 (voix Windows SAPI5, pas de latence réseau)
- Online: edge-tts (voix Microsoft naturelles via pygame.mixer)
"""

import threading
import queue
import logging
import tempfile
import os
from typing import Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Limite de la queue pour éviter l'accumulation en cas de spam
MAX_QUEUE_SIZE = 5

# Longueur max du texte envoyé au TTS
MAX_TEXT_LENGTH = 200


@dataclass
class VoiceInfo:
    """Information sur une voix disponible."""
    id: str
    name: str
    language: str


class TTSEngine:
    """Synthèse vocale offline via pyttsx3 (voix Windows SAPI5)."""

    def __init__(self):
        """Initialise le moteur TTS dans un thread dédié."""
        self._queue: queue.Queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Propriétés configurées avant le start
        self._voice_id: Optional[str] = None
        self._rate: int = 150  # mots par minute (défaut pyttsx3)

        self._engine_ready = threading.Event()
        self._voices: List[VoiceInfo] = []

    def start(self) -> None:
        """Démarre le thread TTS."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

        # Attendre que le moteur soit initialisé
        self._engine_ready.wait(timeout=5)

    def stop(self) -> None:
        """Arrête le thread TTS."""
        self._running = False
        # Débloquer la queue si elle attend
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        if self._thread:
            self._thread.join(timeout=3)
            self._thread = None

    def _worker(self) -> None:
        """Thread worker qui gère le moteur pyttsx3."""
        import pyttsx3

        # Charger les voix disponibles (engine temporaire)
        try:
            engine = pyttsx3.init()
            raw_voices = engine.getProperty('voices')
            self._voices = []
            for v in raw_voices:
                lang = v.languages[0] if v.languages else ""
                self._voices.append(VoiceInfo(id=v.id, name=v.name, language=lang))
            engine.stop()
            del engine
        except Exception as e:
            logger.error(f"Erreur init pyttsx3: {e}")
            self._engine_ready.set()
            return

        self._engine_ready.set()

        while self._running:
            try:
                text = self._queue.get(timeout=0.5)
                if text is None:
                    continue

                # Tronquer les messages trop longs
                if len(text) > MAX_TEXT_LENGTH:
                    text = text[:MAX_TEXT_LENGTH] + "..."

                # Re-init engine each time to avoid runAndWait() hang bug
                engine = pyttsx3.init()
                if self._voice_id:
                    engine.setProperty('voice', self._voice_id)
                if self._rate:
                    engine.setProperty('rate', self._rate)
                engine.say(text)
                engine.runAndWait()
                engine.stop()
                del engine

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Erreur TTS speak: {e}")

    def speak(self, text: str) -> None:
        """
        Ajoute un texte à la queue de lecture.

        Si la queue est pleine (spam), le message est ignoré.

        Args:
            text: Texte à lire
        """
        if not self._running or not text:
            return

        try:
            self._queue.put_nowait(text)
        except queue.Full:
            logger.debug("Queue TTS pleine, message ignoré")

    def clear_queue(self) -> None:
        """Vide la queue des messages en attente."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def set_voice(self, voice_id: str) -> None:
        """Change la voix."""
        self._voice_id = voice_id

    def set_rate(self, rate: int) -> None:
        """
        Change la vitesse de lecture.

        Args:
            rate: Mots par minute (défaut ~150, range 50-300)
        """
        self._rate = rate

    def get_available_voices(self) -> List[VoiceInfo]:
        """Retourne la liste des voix disponibles."""
        return self._voices

    @property
    def is_running(self) -> bool:
        """Retourne True si le moteur TTS est actif."""
        return self._running


class EdgeTTSEngine:
    """Synthèse vocale online via edge-tts + pygame.mixer."""

    # Voix par défaut par langue
    DEFAULT_VOICES = [
        VoiceInfo(id="en-US-GuyNeural", name="Guy (English US)", language="en-US"),
        VoiceInfo(id="en-US-JennyNeural", name="Jenny (English US)", language="en-US"),
        VoiceInfo(id="en-GB-RyanNeural", name="Ryan (English UK)", language="en-GB"),
        VoiceInfo(id="fr-FR-HenriNeural", name="Henri (French)", language="fr-FR"),
        VoiceInfo(id="fr-FR-DeniseNeural", name="Denise (French)", language="fr-FR"),
        VoiceInfo(id="de-DE-ConradNeural", name="Conrad (German)", language="de-DE"),
        VoiceInfo(id="ru-RU-DmitryNeural", name="Dmitry (Russian)", language="ru-RU"),
        VoiceInfo(id="ja-JP-KeitaNeural", name="Keita (Japanese)", language="ja-JP"),
        VoiceInfo(id="zh-CN-YunxiNeural", name="Yunxi (Chinese)", language="zh-CN"),
    ]

    def __init__(self):
        """Initialise le moteur Edge TTS."""
        self._queue: queue.Queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self._voice: str = "en-US-GuyNeural"
        self._rate: str = "+0%"
        self._voices: List[VoiceInfo] = list(self.DEFAULT_VOICES)

        self._tmp_dir = tempfile.mkdtemp(prefix="wt_tts_")
        self._engine_ready = threading.Event()

    def start(self) -> None:
        """Démarre le thread TTS."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        self._engine_ready.wait(timeout=3)

    def stop(self) -> None:
        """Arrête le thread TTS."""
        self._running = False
        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

        # Nettoyage des fichiers temporaires
        try:
            import shutil
            shutil.rmtree(self._tmp_dir, ignore_errors=True)
        except Exception:
            pass

    def _worker(self) -> None:
        """Thread worker avec boucle asyncio pour edge-tts."""
        import asyncio
        import edge_tts
        import pygame

        # Init pygame.mixer dans ce thread
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        except Exception as e:
            logger.error(f"Erreur init pygame.mixer: {e}")
            self._engine_ready.set()
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._engine_ready.set()

        msg_counter = 0

        while self._running:
            try:
                text = self._queue.get(timeout=0.5)
                if text is None:
                    continue

                # Tronquer
                if len(text) > MAX_TEXT_LENGTH:
                    text = text[:MAX_TEXT_LENGTH] + "..."

                # Unique temp file per message to avoid file lock issues
                msg_counter += 1
                tmp_file = os.path.join(self._tmp_dir, f"tts_{msg_counter}.mp3")

                # Générer l'audio
                async def generate():
                    communicate = edge_tts.Communicate(text, self._voice, rate=self._rate)
                    await communicate.save(tmp_file)

                loop.run_until_complete(generate())

                # Lire avec pygame.mixer
                if os.path.exists(tmp_file) and os.path.getsize(tmp_file) > 0:
                    pygame.mixer.music.load(tmp_file)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy() and self._running:
                        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.1))
                    pygame.mixer.music.unload()

                # Cleanup old temp file
                try:
                    os.remove(tmp_file)
                except OSError:
                    pass

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Erreur Edge TTS: {e}")

        loop.close()

    def speak(self, text: str) -> None:
        """Ajoute un texte à la queue de lecture."""
        if not self._running or not text:
            return
        try:
            self._queue.put_nowait(text)
        except queue.Full:
            logger.debug("Queue TTS pleine, message ignoré")

    def clear_queue(self) -> None:
        """Vide la queue des messages en attente."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break

    def set_voice(self, voice_id: str) -> None:
        """Change la voix (ex: 'en-US-GuyNeural')."""
        self._voice = voice_id

    def set_rate(self, rate: int) -> None:
        """
        Change la vitesse de lecture.

        Args:
            rate: Valeur en pourcentage (100 = normal, 150 = +50%, 80 = -20%)
        """
        percent = rate - 100
        self._rate = f"{percent:+d}%"

    def get_available_voices(self) -> List[VoiceInfo]:
        """Retourne la liste des voix disponibles."""
        return self._voices

    @property
    def is_running(self) -> bool:
        return self._running
