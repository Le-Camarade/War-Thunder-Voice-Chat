# War Thunder Voice Chat - TTS Feature Branch

## Contexte

Cette branche ajoute la fonctionnalité **Text-to-Speech** : lecture vocale des messages du chat en temps réel. Elle s'ajoute au module STT existant (voix → chat).

**Branche Git** : `feature/tts`
**Base** : `main` (v1.0.0)

## Découverte technique

War Thunder expose un serveur HTTP local sur `http://localhost:8111/` qui affiche une interface web avec :
- Carte tactique
- Télémétrie avion
- **Chat en temps réel** ← c'est ça qui nous intéresse

### Structure HTML du chat

```html
<div id="game-chat-root" class="ui-draggable ui-resizable">
  <div class="caption">...</div>
  <div id="textlines">
    <div class="chat-line">
      <span class="chat-time">85:56</span>
      "[Équipe] moon_marble@psn: Suivez moi !"
      <color=#ff96966e>[D3, alt. 1800 m]</color>
    </div>
    <div class="chat-line">
      <span class="chat-time">86:21</span>
      "[Équipe] Le_Camarade: Besoin de protection!"
    </div>
    <!-- ... -->
  </div>
</div>
```

### Données extraites par message

| Champ | Source | Exemple |
|-------|--------|---------|
| Timestamp | `.chat-time` | `85:56` |
| Canal | Texte entre `[]` | `Équipe`, `Tous`, `Escadron` |
| Pseudo | Après `]` avant `:` | `moon_marble@psn` |
| Message | Après `:` | `Suivez moi !` |
| Metadata | Tags `<color>` | `[D3, alt. 1800 m]` (position carte) |

## Architecture du module TTS

### Nouveaux fichiers

```
war-thunder-voice-chat/
├── core/
│   ├── ... (existants)
│   ├── chat_listener.py    # Scraping localhost:8111
│   └── tts_engine.py       # Synthèse vocale
├── ui/
│   ├── ... (existants)
│   └── tts_settings.py     # Panel config TTS
```

### chat_listener.py

```python
"""
Polling du chat War Thunder via localhost:8111
"""
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Callable, Optional
import threading
import time
import re

@dataclass
class ChatMessage:
    timestamp: str          # "85:56"
    channel: str            # "Équipe", "Tous", "Escadron"
    sender: str             # "moon_marble@psn"
    content: str            # "Suivez moi !"
    metadata: Optional[str] # "[D3, alt. 1800 m]" ou None
    
    @property
    def unique_id(self) -> str:
        """Pour détecter les doublons"""
        return f"{self.timestamp}:{self.sender}:{self.content[:20]}"

class ChatListener:
    def __init__(self, 
                 url: str = "http://localhost:8111/",
                 poll_interval: float = 0.5,
                 own_username: str = None):
        self.url = url
        self.poll_interval = poll_interval
        self.own_username = own_username
        self._seen_ids: set = set()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._on_new_message: Optional[Callable[[ChatMessage], None]] = None
    
    def set_own_username(self, username: str):
        """Pour filtrer ses propres messages"""
        self.own_username = username
    
    def on_new_message(self, callback: Callable[[ChatMessage], None]):
        """Register callback pour nouveaux messages"""
        self._on_new_message = callback
    
    def _parse_chat_line(self, element) -> Optional[ChatMessage]:
        """Parse un élément .chat-line en ChatMessage"""
        try:
            time_el = element.select_one('.chat-time')
            if not time_el:
                return None
            
            timestamp = time_el.text.strip()
            full_text = element.get_text()
            
            # Retirer le timestamp du texte
            text = full_text.replace(timestamp, '', 1).strip()
            
            # Pattern: [Canal] Pseudo: Message
            match = re.match(r'\[([^\]]+)\]\s*([^:]+):\s*(.+)', text)
            if not match:
                return None
            
            channel = match.group(1)
            sender = match.group(2).strip()
            content = match.group(3).strip()
            
            # Extraire metadata (coordonnées) si présent
            metadata = None
            color_match = re.search(r'\[([A-H]\d+[^\]]*)\]', content)
            if color_match:
                metadata = color_match.group(0)
                content = content.replace(metadata, '').strip()
            
            return ChatMessage(
                timestamp=timestamp,
                channel=channel,
                sender=sender,
                content=content,
                metadata=metadata
            )
        except Exception:
            return None
    
    def _fetch_messages(self) -> List[ChatMessage]:
        """Récupère tous les messages actuels"""
        try:
            response = requests.get(self.url, timeout=1)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            messages = []
            for line in soup.select('#textlines .chat-line'):
                msg = self._parse_chat_line(line)
                if msg:
                    messages.append(msg)
            return messages
        except requests.RequestException:
            return []
    
    def _poll_loop(self):
        """Boucle de polling dans un thread séparé"""
        while self._running:
            messages = self._fetch_messages()
            
            for msg in messages:
                # Ignorer les messages déjà vus
                if msg.unique_id in self._seen_ids:
                    continue
                
                # Ignorer ses propres messages
                if self.own_username and self.own_username.lower() in msg.sender.lower():
                    self._seen_ids.add(msg.unique_id)
                    continue
                
                self._seen_ids.add(msg.unique_id)
                
                if self._on_new_message:
                    self._on_new_message(msg)
            
            time.sleep(self.poll_interval)
    
    def start(self):
        """Démarre le polling"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Arrête le polling"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
    
    def is_game_running(self) -> bool:
        """Vérifie si War Thunder est lancé (localhost:8111 répond)"""
        try:
            requests.get(self.url, timeout=0.5)
            return True
        except requests.RequestException:
            return False
```

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
beautifulsoup4>=4.12.0
pyttsx3>=2.90
edge-tts>=6.1.0
pydub>=0.25.1
```

Note: `pydub` nécessite ffmpeg pour la lecture audio avec edge-tts.

## Priorités d'implémentation

### Phase 1 - Chat Listener
1. [ ] Implémenter `chat_listener.py`
2. [ ] Test CLI : afficher les nouveaux messages en console
3. [ ] Vérifier le parsing sur différents formats de message

### Phase 2 - TTS Engine
4. [ ] Implémenter `Pyttsx3Engine` (plus simple)
5. [ ] Test CLI : lire un message hardcodé
6. [ ] Intégrer ChatListener + TTS : lire les messages en temps réel

### Phase 3 - UI Integration
7. [ ] Créer `tts_settings.py` avec les contrôles
8. [ ] Intégrer dans la fenêtre principale (section dépliable)
9. [ ] Sauvegarder/charger les settings TTS

### Phase 4 - Polish
10. [ ] Implémenter `EdgeTTSEngine` (optionnel, meilleure qualité)
11. [ ] Indicateur de statut connexion WT
12. [ ] Gestion des erreurs (jeu fermé, connexion perdue)

## Edge Cases à gérer

| Situation | Comportement |
|-----------|--------------|
| War Thunder pas lancé | Indicateur rouge, TTS désactivé, retry toutes les 5s |
| Partie terminée (menu) | localhost:8111 peut ne plus répondre, gérer gracieusement |
| Message très long | Tronquer à ~200 caractères pour le TTS |
| Spam chat | Queue avec limite, drop les messages si > 5 en attente |
| Caractères spéciaux | Nettoyer les tags `<color>` et autres markup |
| Messages système | Filtrer "Eau en surchauffe", "Moteur détruit" (pas du chat joueur) |

## Messages système à filtrer

Ces messages apparaissent dans le log mais ne sont pas du chat joueur :

```
- "Eau en surchauffe"
- "Huile en surchauffe"  
- "Moteur détruit"
- "X (Avion) abattu Y (Avion)"
- "X (Avion) Sévèrement endommagé Y (Avion)"
```

**Règle de filtrage** : Ne lire que les messages qui matchent le pattern `[Canal] Pseudo: Message`

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
