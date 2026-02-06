# War Thunder Voice Chat

A standalone Windows application for sending voice messages in War Thunder chat using joystick push-to-talk. Voice is transcribed (and optionally translated) to English using local Whisper AI, then automatically injected into the game chat. Incoming chat messages can also be read aloud via TTS.

## Features

### Voice-to-Chat (Push-to-Talk)
- **Push-to-Talk with Joystick**: Use any joystick button to trigger voice recording
- **Local Speech-to-Text**: Powered by OpenAI Whisper - no internet required
- **Translate to English**: Speak in any language, Whisper translates to English automatically (toggleable)
- **Automatic Chat Injection**: Messages are typed directly into War Thunder chat
- **Configurable Chat Key**: Support for different in-game chat keybindings (Enter, T, Y, U)

### Chat Reader (TTS)
- **Read chat aloud**: Incoming War Thunder chat messages are spoken via TTS
- **Two engines**: Offline (Windows SAPI5) or Online (Microsoft Edge Neural voices - higher quality)
- **9 neural voices**: English, French, German, Russian, Japanese, Chinese
- **Channel filtering**: Choose which channels to read (Team, All, Squadron)
- **Own message filtering**: Skip your own messages by setting your username
- **Anti-spam**: Queue with size limit, long messages truncated

### General
- **Dark Theme UI**: Modern interface that matches gaming setups
- **System Tray**: Minimize to system tray to keep the app running in the background
- **Auto-Start**: Option to launch automatically with Windows
- **Persistent Settings**: All configuration saved and restored between launches

## Requirements

- Windows 10/11
- Python 3.11+ (tested on 3.14)
- A joystick/gamepad
- A microphone
- Internet connection (only for Edge TTS online voices)

## Installation

### From Source

```bash
# Clone or download the project
cd war-thunder-voice-chat

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Standalone Executable

Download `WT-VoiceChat.exe` from the releases page (no Python required).

## Usage

### From Source

```bash
# Activate environment
venv\Scripts\activate

# Run the application
python main.py
```

### From Executable

Simply run `WT-VoiceChat.exe`. Settings are saved in `config.json` next to the executable.

### First Launch

1. Connect your joystick before launching
2. Select your joystick from the dropdown
3. Click "Assign" and press the button you want to use for push-to-talk
4. Choose your Whisper model (small recommended)
5. Set the chat key to match your in-game keybinding (default: Enter)
6. Enable/disable "Translate to English" depending on your language

### Using Voice Chat

1. Press and hold your assigned joystick button
2. Speak your message (in any language if translation is enabled, or in English)
3. Release the button
4. The message will be transcribed and sent to War Thunder chat

### Using Chat Reader (TTS)

1. Scroll down to the "Chat Reader (TTS)" section
2. Choose your engine: Offline (no internet) or Online (better quality)
3. Select a voice and adjust speed
4. Enter your in-game username to filter out your own messages
5. Select which channels to read (Team, All, Squadron)
6. Toggle the switch ON
7. War Thunder must be running - the connection status indicator shows if the game is detected

### System Tray

Click "Minimize to Tray" to hide the application to the system tray. The app continues running in the background.

- **Double-click** the tray icon to restore the window
- **Right-click** for options: Restore or Quit

## Configuration

Settings are automatically saved to `config.json`:

- Joystick and button assignment
- Whisper model size (tiny, small, medium)
- Chat key (Enter, T, Y, U)
- Translate to English toggle
- Auto-start with Windows
- TTS engine type, voice, speed, channels
- Window position

## Whisper Models

| Model | Speed | Accuracy | Use Case |
|-------|-------|----------|----------|
| tiny | Fastest | Basic | Quick responses, simple phrases |
| small | Balanced | Good | Recommended for most users |
| medium | Slower | Best | Maximum accuracy |

## TTS Engines

| Engine | Quality | Latency | Requires Internet |
|--------|---------|---------|-------------------|
| Offline (Windows SAPI5) | Basic | Instant | No |
| Online (Edge Neural) | Excellent | ~200ms | Yes |

## Building the Executable

To create a standalone `.exe` file:

```bash
# Install PyInstaller
pip install pyinstaller

# Build
pyinstaller build.spec --noconfirm
```

Or simply run `build.bat`. The executable will be created in the `dist/` folder.

## Project Structure

```
war-thunder-voice-chat/
├── main.py              # Entry point
├── config.py            # Configuration manager
├── requirements.txt     # Dependencies
├── build.spec           # PyInstaller configuration
├── build.bat            # Build script
├── core/
│   ├── recorder.py      # Audio capture
│   ├── transcriber.py   # Whisper integration (transcribe + translate)
│   ├── injector.py      # Keyboard simulation (SendInput)
│   ├── joystick.py      # Joystick handling
│   ├── chat_listener.py # War Thunder chat API listener
│   ├── tts_engine.py    # TTS engines (offline pyttsx3 + online edge-tts)
│   └── autostart.py     # Windows auto-start registry
└── ui/
    ├── app.py           # Main window
    ├── widgets.py       # Custom widgets (StatusLED, VolumeIndicator, etc.)
    ├── settings_frame.py # Voice-to-chat settings panel
    └── tts_settings.py  # Chat reader (TTS) settings panel
```

## Troubleshooting

**No joystick detected**: Connect your joystick and click the refresh button

**Antivirus blocking**: Add an exception for the application (uses keyboard simulation via SendInput)

**Transcription slow**: Use "tiny" model for faster results

**Translation unreliable**: The "small" model works well for most European languages. Try "medium" for better accuracy

**Chat not working in War Thunder**: Make sure the chat key setting matches your in-game keybinding

**TTS not working**: Make sure War Thunder is running (check the "WT: Connected" indicator). For online voices, ensure you have an internet connection

**Settings not saving (.exe)**: Make sure the .exe is not in a read-only folder (e.g. Program Files). Place it in Documents or Desktop

**System tray icon not showing**: Install `pystray` and `Pillow` packages

## License

MIT License
