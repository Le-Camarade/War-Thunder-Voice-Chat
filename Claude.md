# War Thunder Voice Chat - Project Context

## Vision

Application standalone Windows permettant d'envoyer des messages vocaux dans le chat de War Thunder via push-to-talk sur joystick. La voix est transcrite en anglais par Whisper local, puis injectée automatiquement dans le chat du jeu.

## Contraintes techniques critiques

- **GPU partagé** : RTX 4060 Laptop utilisé simultanément pour la VR → minimiser l'impact GPU
- **Mode par défaut** : CPU (int8) avec modèle `small` pour préserver les performances VR
- **Mode optionnel** : GPU (CUDA) avec modèle `medium` pour meilleure qualité quand la VR n'est pas active

## Stack technique

| Composant | Librairie | Justification |
|-----------|-----------|---------------|
| GUI | `customtkinter` | Interface moderne, thème sombre natif |
| Joystick | `pygame` | Support universel des contrôleurs, événements fiables |
| Audio | `sounddevice` + `numpy` | Léger, pas de dépendances système lourdes |
| Transcription | `faster-whisper` | 3-4x plus rapide que Whisper vanilla, support int8 CPU |
| Simulation clavier | `pynput` | Fonctionne même quand le jeu a le focus |
| Presse-papier | `pyperclip` | Cross-platform, simple |
| Config | `json` standard | Sauvegarde des paramètres utilisateur |

## Architecture

```
war-thunder-voice-chat/
├── main.py                 # Entry point, initialisation
├── ui/
│   ├── __init__.py
│   ├── app.py              # Fenêtre principale CTk
│   ├── widgets.py          # StatusLED, JoystickButton, etc.
│   └── settings_frame.py   # Panel de configuration
├── core/
│   ├── __init__.py
│   ├── joystick.py         # JoystickManager: détection, événements, mapping
│   ├── recorder.py         # AudioRecorder: capture micro, buffer numpy
│   ├── transcriber.py      # WhisperTranscriber: wrapper faster-whisper
│   └── injector.py         # ChatInjector: simulation Entrée → Ctrl+V → Entrée
├── config.py               # ConfigManager: load/save JSON, chemins, defaults
├── requirements.txt
└── README.md
```

## Flux utilisateur détaillé

### Configuration initiale (premier lancement)
1. Détection automatique des joysticks connectés
2. L'utilisateur sélectionne son joystick dans un dropdown
3. Clic sur "Assigner touche" → l'app attend un input joystick → capture le bouton
4. Sélection du mode (Performance CPU / Qualité GPU)
5. Téléchargement automatique du modèle Whisper si absent
6. Sauvegarde auto dans `config.json`

### Utilisation normale
```
[État: IDLE - LED grise]
         ↓
[Appui bouton joystick]
         ↓
[État: RECORDING - LED rouge]
    - Capture audio en continu dans un buffer
    - Affichage du temps d'enregistrement
         ↓
[Relâchement bouton]
         ↓
[État: TRANSCRIBING - LED orange]
    - Envoi buffer audio à faster-whisper
    - Transcription en anglais (language="en")
         ↓
[État: SENDING - LED bleue]
    - Simulation: Entrée (ouvre chat War Thunder)
    - Délai 50ms
    - Copie texte dans presse-papier
    - Simulation: Ctrl+V
    - Délai 50ms
    - Simulation: Entrée (envoie message)
         ↓
[État: SENT - LED verte pendant 1.5s]
    - Affichage du texte transcrit
         ↓
[Retour IDLE]
```

## Spécifications de l'interface

### Fenêtre principale (400x500px environ)
```
┌─────────────────────────────────────┐
│  War Thunder Voice Chat        [_][X]│
├─────────────────────────────────────┤
│                                     │
│         ◉  STATUS LED               │
│         "Ready" / "Recording..."    │
│                                     │
├─────────────────────────────────────┤
│  Joystick: [Dropdown selection ▼]   │
│                                     │
│  Push-to-talk: [Button 4    ] [Set] │
│                                     │
│  Mode: ○ Performance (CPU)          │
│        ○ Quality (GPU)              │
│                                     │
│  Model: [small ▼] (auto selon mode) │
│                                     │
├─────────────────────────────────────┤
│  Last message:                      │
│  ┌─────────────────────────────────┐│
│  │ "Enemy tank on the left flank" ││
│  └─────────────────────────────────┘│
│                                     │
│  [Minimize to tray]                 │
└─────────────────────────────────────┘
```

### Thème
- Thème sombre (customtkinter: `set_appearance_mode("dark")`)
- Couleurs LED: gris (#666), rouge (#ff4444), orange (#ffaa00), bleu (#4488ff), vert (#44ff44)

## Détails d'implémentation

### joystick.py
```python
# Utiliser pygame.joystick en mode polling dans un thread séparé
# Événements à émettre: on_button_down(joystick_id, button_id), on_button_up(...)
# Méthode pour rafraîchir la liste des joysticks connectés
# Supporter le hot-plug si possible
```

### recorder.py
```python
# sounddevice.InputStream en callback mode
# Buffer: collections.deque ou numpy array pré-alloué
# Sample rate: 16000 Hz (requis par Whisper)
# Channels: 1 (mono)
# Format: float32
# Méthodes: start_recording(), stop_recording() -> np.ndarray
```

### transcriber.py
```python
# Initialisation lazy du modèle (pas au démarrage de l'app)
# Paramètres faster-whisper:
#   - model_size: "small" ou "medium"
#   - device: "cpu" ou "cuda"
#   - compute_type: "int8" (CPU) ou "float16" (GPU)
#   - language: "en" (forcer anglais, pas d'auto-detect)
#   - beam_size: 5
#   - vad_filter: True (filtrer les silences)
# Retourner le texte concaténé de tous les segments
```

### injector.py
```python
# Utiliser pynput.keyboard.Controller
# Séquence avec délais configurables:
#   1. press/release Key.enter
#   2. sleep(0.05)
#   3. pyperclip.copy(text)
#   4. press/release ctrl+v
#   5. sleep(0.05)
#   6. press/release Key.enter
# Option pour délai custom si War Thunder lag
```

### config.py
```python
# Fichier: config.json dans le même dossier que l'exe (ou AppData)
# Structure:
{
    "joystick_name": "Thrustmaster T.16000M",
    "button_id": 4,
    "mode": "cpu",  // "cpu" ou "gpu"
    "model": "small",  // "tiny", "small", "medium"
    "injection_delay_ms": 50,
    "window_geometry": "400x500+100+100"
}
```

## Gestion des erreurs

- **Pas de joystick** : Message clair, bouton "Rafraîchir"
- **Pas de micro** : Popup d'erreur au démarrage, liste des devices disponibles
- **Modèle Whisper absent** : Progress bar de téléchargement, ~500MB pour medium
- **Échec transcription** : Notification discrète, pas de crash, log l'erreur
- **War Thunder pas focus** : L'injection clavier fonctionne quand même (pynput)

## Priorités de développement

### Phase 1 - MVP fonctionnel
1. [ ] Structure du projet, requirements.txt
2. [ ] recorder.py - capture audio basique
3. [ ] transcriber.py - wrapper faster-whisper
4. [ ] injector.py - simulation clavier
5. [ ] Test CLI sans GUI: enregistre 5s → transcrit → injecte

### Phase 2 - Interface
6. [ ] app.py - fenêtre principale avec StatusLED
7. [ ] joystick.py - détection et événements
8. [ ] Intégration complète du flux
9. [ ] config.py - persistence des settings

### Phase 3 - Polish
10. [ ] Minimize to system tray
11. [ ] Indicateur de volume micro en temps réel
12. [ ] Auto-start avec Windows (optionnel)
13. [ ] Packaging en .exe avec PyInstaller

## Dépendances (requirements.txt)

```
customtkinter>=5.2.0
pygame>=2.5.0
sounddevice>=0.4.6
numpy>=1.24.0
faster-whisper>=0.10.0
pynput>=1.7.6
pyperclip>=1.8.2
```

Note: `faster-whisper` nécessite `ctranslate2` qui s'installe automatiquement.
Pour le support CUDA: installer séparément `nvidia-cublas-cu11` et `nvidia-cudnn-cu11`.

## Commandes utiles

```bash
# Créer l'environnement
python -m venv venv
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Pour support GPU (optionnel)
pip install nvidia-cublas-cu11 nvidia-cudnn-cu11

# Lancer l'app
python main.py

# Build exe
pip install pyinstaller
pyinstaller --onefile --windowed --name="WT-VoiceChat" main.py
```

## Notes pour le développeur

- Tester sur Windows 10/11 uniquement (cible gaming)
- Le joystick doit être branché AVANT de lancer l'app (ou implémenter hot-plug)
- War Thunder utilise un chat standard, Entrée ouvre/ferme, pas de commandes spéciales
- Attention aux antivirus qui peuvent bloquer pynput (simulation clavier)