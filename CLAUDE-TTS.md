# War Thunder Voice Chat - TTS Feature Branch

## Contexte

Cette branche ajoute la fonctionnalité **Text-to-Speech** : lecture vocale des messages du chat en temps réel. Elle s'ajoute au module STT existant (voix → chat).

**Branche Git** : `feature/tts`
**Base** : `main` (v1.0.0)

## Découverte technique

War Thunder expose un serveur HTTP local sur `http://localhost:8111/` avec :
- Carte tactique
- Télémétrie avion
- **API JSON `/gamechat`** ← c'est ça qui nous intéresse

### API JSON /gamechat

L'endpoint `GET /gamechat?lastId=N` retourne les messages depuis l'ID N :

```json
[
  { "id": 3, "msg": "Suivez-moi !<color=#FF96966E> [F4, alt. 2100 m]</color>", "sender": "PVC_Atorpine", "enemy": false, "mode": "Équipe", "time": 1645 },
  { "id": 4, "msg": "Need backup!", "sender": "Le_Camarade", "enemy": false, "mode": "Équipe", "time": 1978 }
]
```

### Données extraites par message

| Champ | Source JSON | Exemple |
|-------|-----------|---------|
| ID | `id` | `3` (auto-incrémenté, sert de curseur) |
| Canal | `mode` | `Équipe`, `Tous`, `Escadron` |
| Pseudo | `sender` | `PVC_Atorpine` |
| Message | `msg` (nettoyé des tags `<color>`) | `Suivez-moi !` |
| Ennemi | `enemy` | `false` |
| Metadata | Tags `<color>` dans `msg` | `[F4, alt. 2100 m]` (position carte) |
| Temps | `time` | `1645` (secondes de jeu) |

## Architecture du module TTS

### Nouveaux fichiers

```
war-thunder-voice-chat/
├── core/
│   ├── ... (existants)
│   ├── chat_listener.py    # API JSON /gamechat
│   └── tts_engine.py       # Synthèse vocale
├── ui/
│   ├── ... (existants)
│   └── tts_settings.py     # Panel config TTS
```

### chat_listener.py (IMPLÉMENTÉ)

Utilise l'API JSON `/gamechat?lastId=N` au lieu du scraping HTML.
Déduplication native par `lastId` incrémental (pas besoin de set).
Voir `core/chat_listener.py` pour le code complet.

### tts_engine.py

```python
"""
Synthèse vocale pour les messages chat
Options: pyttsx3 (offline) ou edge-tts (online, meilleure qualité)
"""
from abc import ABC, abstractmethod
from typing import Optional
import threading
import queue

class TTSEngine(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:
        pass
    
    @abstractmethod
    def stop(self) -> None:
        pass
    
    @abstractmethod
    def set_voice(self, voice_id: str) -> None:
        pass
    
    @abstractmethod
    def set_rate(self, rate: int) -> None:
        pass

class Pyttsx3Engine(TTSEngine):
    """TTS offline via pyttsx3 - voix Windows"""
    
    def __init__(self):
        import pyttsx3
        self._engine = pyttsx3.init()
        self._queue = queue.Queue()
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
    
    def _worker(self):
        while self._running:
            try:
                text = self._queue.get(timeout=0.5)
                self._engine.say(text)
                self._engine.runAndWait()
            except queue.Empty:
                continue
    
    def speak(self, text: str) -> None:
        self._queue.put(text)
    
    def stop(self) -> None:
        self._engine.stop()
        # Vider la queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
    
    def set_voice(self, voice_id: str) -> None:
        self._engine.setProperty('voice', voice_id)
    
    def set_rate(self, rate: int) -> None:
        self._engine.setProperty('rate', rate)
    
    def get_available_voices(self) -> list:
        return self._engine.getProperty('voices')
    
    def shutdown(self):
        self._running = False
        self._thread.join(timeout=2)


class EdgeTTSEngine(TTSEngine):
    """TTS online via edge-tts - voix Microsoft naturelles"""
    
    def __init__(self, voice: str = "en-US-GuyNeural"):
        self._voice = voice
        self._rate = "+0%"
        self._queue = queue.Queue()
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
    
    def _worker(self):
        import asyncio
        import edge_tts
        import io
        from pydub import AudioSegment
        from pydub.playback import play
        
        async def speak_async(text):
            communicate = edge_tts.Communicate(text, self._voice, rate=self._rate)
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            if audio_data:
                audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
                play(audio)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while self._running:
            try:
                text = self._queue.get(timeout=0.5)
                loop.run_until_complete(speak_async(text))
            except queue.Empty:
                continue
    
    def speak(self, text: str) -> None:
        self._queue.put(text)
    
    def stop(self) -> None:
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
    
    def set_voice(self, voice_id: str) -> None:
        self._voice = voice_id
    
    def set_rate(self, rate: int) -> None:
        # Convertir rate en pourcentage pour edge-tts
        # rate=150 → "+50%", rate=80 → "-20%"
        percent = rate - 100
        self._rate = f"{percent:+d}%"
    
    def shutdown(self):
        self._running = False
        self._thread.join(timeout=2)
```

## Intégration UI

### Nouveaux éléments dans l'interface

```
┌─────────────────────────────────────┐
│  War Thunder Voice Chat        [_][X]│
├─────────────────────────────────────┤
│         ◉  STATUS LED               │
├─────────────────────────────────────┤
│  ▼ Push-to-Talk (STT)               │
│    [Config existante...]            │
├─────────────────────────────────────┤
│  ▼ Chat Reader (TTS)         [ON/OFF]│
│                                     │
│    Engine: ○ Offline (Windows)      │
│            ○ Online (Edge - better) │
│                                     │
│    Voice:  [en-US-GuyNeural    ▼]   │
│    Speed:  [====●=====] 100%        │
│                                     │
│    Read channels:                   │
│      ☑ Team    ☑ All    ☐ Squadron  │
│                                     │
│    Your username: [Le_Camarade    ] │
│    (to filter your own messages)    │
│                                     │
│    Status: 🟢 Connected to WT       │
│            🔴 Game not detected     │
├─────────────────────────────────────┤
│  Last heard:                        │
│  "moon_marble: Suivez moi!"         │
└─────────────────────────────────────┘
```

### Fonctionnalités

1. **Toggle ON/OFF** : Activer/désactiver le TTS indépendamment du STT
2. **Choix du moteur** :
   - Offline (pyttsx3) : Pas de latence réseau, voix Windows basiques
   - Online (edge-tts) : Latence ~200ms, voix naturelles Microsoft
3. **Sélection de voix** : Liste déroulante des voix disponibles
4. **Vitesse** : Slider 50%-200%
5. **Filtrage par canal** : Checkboxes pour Team/All/Squadron
6. **Username** : Pour ne pas lire ses propres messages
7. **Indicateur de connexion** : Vert si localhost:8111 répond

## Configuration étendue (config.json)

```json
{
    "joystick_name": "Thrustmaster T.16000M",
    "button_id": 4,
    "mode": "cpu",
    "model": "small",
    "injection_delay_ms": 50,
    "window_geometry": "400x600+100+100",
    
    "tts": {
        "enabled": true,
        "engine": "edge",
        "voice": "en-US-GuyNeural",
        "rate": 100,
        "channels": {
            "team": true,
            "all": true,
            "squadron": false
        },
        "own_username": "Le_Camarade",
        "poll_interval_ms": 500
    }
}
```

## Dépendances additionnelles

```
# Ajouter à requirements.txt
requests>=2.31.0      # Phase 1 (déjà ajouté)
pyttsx3>=2.90         # Phase 2
edge-tts>=6.1.0       # Phase 4 (optionnel)
pydub>=0.25.1         # Phase 4 (optionnel)
```

Note: `pydub` nécessite ffmpeg pour la lecture audio avec edge-tts.

## Priorités d'implémentation

### Phase 1 - Chat Listener ✅
1. [x] Implémenter `chat_listener.py` (API JSON `/gamechat`)
2. [x] Test CLI : `test_chat_listener.py`
3. [x] Parsing vérifié en live (70 messages, metadata, filtrage)

### Phase 2 - TTS Engine ✅
4. [x] Implémenter `TTSEngine` dans `core/tts_engine.py` (pyttsx3, queue limitée, thread dédié)
5. [x] Test CLI : `test_tts.py --text "..."` + `--list-voices` + `--voice N`
6. [x] Intégration ChatListener + TTS : `test_tts.py --live` (74 messages lus en live)

### Phase 3 - UI Integration ✅
7. [x] Créer `ui/tts_settings.py` (toggle, voix, vitesse, canaux, username, statut WT)
8. [x] Intégrer dans `app.py` (ChatListener + TTSEngine + callbacks + cleanup)
9. [x] Sauvegarder/charger les settings TTS (8 champs dans config.py)

### Phase 4 - Polish ✅
10. [x] Implémenter `EdgeTTSEngine` (edge-tts + pygame.mixer, 9 voix neurales)
11. [x] Indicateur de statut connexion WT (check toutes les 5s)
12. [x] Sélecteur moteur Offline/Online dans l'UI + config
13. [x] Gestion des erreurs (queue limitée, truncation, cleanup temp files)

## Edge Cases à gérer

| Situation | Comportement |
|-----------|--------------|
| War Thunder pas lancé | Indicateur rouge, TTS désactivé, retry toutes les 5s |
| Partie terminée (menu) | localhost:8111 peut ne plus répondre, gérer gracieusement |
| Message très long | Tronquer à ~200 caractères pour le TTS |
| Spam chat | Queue avec limite, drop les messages si > 5 en attente |
| Caractères spéciaux | Tags `<color>` nettoyés par regex dans `_parse_message()` |
| Messages système | L'API `/gamechat` ne retourne QUE les messages chat joueur |

## Commandes Git

```bash
# Créer la branche feature
git checkout -b feature/tts

# Développer...

# Une fois stable, merger
git checkout main
git merge feature/tts
git tag v1.1.0
git push --all
git push --tags
```

## Notes

- Le TTS ne doit pas bloquer le STT — threads séparés
- Tester en VR : le son doit sortir sur le bon device audio
- Prévoir un raccourci pour mute/unmute le TTS rapidement (bouton joystick ?)
