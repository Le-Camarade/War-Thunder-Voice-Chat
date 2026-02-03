# War Thunder Voice Chat

A standalone Windows application for sending voice messages in War Thunder chat using joystick push-to-talk. Voice is transcribed to English using local Whisper AI, then automatically injected into the game chat.

## Features

- **Push-to-Talk with Joystick**: Use any joystick button to trigger voice recording
- **Local Speech-to-Text**: Powered by OpenAI Whisper - no internet required
- **Automatic Chat Injection**: Messages are typed directly into War Thunder chat
- **Dark Theme UI**: Modern interface that matches gaming setups
- **System Tray**: Minimize to system tray to keep the app running in the background
- **Auto-Start**: Option to launch automatically with Windows
- **Configurable Chat Key**: Support for different in-game chat keybindings (Enter, T, Y, U)

## Requirements

- Windows 10/11
- Python 3.11+ (tested on 3.14)
- A joystick/gamepad
- A microphone

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

Simply run `WT-VoiceChat.exe`.

### First Launch

1. Connect your joystick before launching
2. Select your joystick from the dropdown
3. Click "Assign" and press the button you want to use for push-to-talk
4. Choose your Whisper model (small recommended)
5. Set the chat key to match your in-game keybinding (default: Enter)

### Using Voice Chat

1. Press and hold your assigned joystick button
2. Speak your message in English
3. Release the button
4. The message will be transcribed and sent to War Thunder chat

### System Tray

Click "Minimize to Tray" to hide the application to the system tray. The app continues running in the background.

- **Double-click** the tray icon to restore the window
- **Right-click** for options: Restore or Quit

## Configuration

Settings are automatically saved to `config.json`:

- Joystick and button assignment
- Whisper model size (tiny, small, medium)
- Chat key (Enter, T, Y, U)
- Auto-start with Windows
- Window position

## Whisper Models

| Model | Speed | Accuracy | Use Case |
|-------|-------|----------|----------|
| tiny | Fastest | Basic | Quick responses, simple phrases |
| small | Balanced | Good | Recommended for most users |
| medium | Slower | Best | Maximum accuracy |

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
│   ├── transcriber.py   # Whisper integration
│   ├── injector.py      # Keyboard simulation (SendInput)
│   ├── joystick.py      # Joystick handling
│   └── autostart.py     # Windows auto-start registry
└── ui/
    ├── app.py           # Main window
    ├── widgets.py       # Custom widgets
    └── settings_frame.py
```

## Troubleshooting

**No joystick detected**: Connect your joystick and click the refresh button

**Antivirus blocking**: Add an exception for the application (uses keyboard simulation via SendInput)

**Transcription slow**: Use "tiny" model for faster results

**Chat not working in War Thunder**: Make sure the chat key setting matches your in-game keybinding

**System tray icon not showing**: Install `pystray` and `Pillow` packages

## License

MIT License