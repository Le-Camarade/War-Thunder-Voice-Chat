# Community Post - War Thunder Voice Chat

---

## Reddit Post (r/WarThunderSim)

**Title:** I made a free voice-to-chat tool for Sim - Push joystick button, speak, message sent automatically

---

Hey fellow sim pilots,

I got tired of trying to type in chat while flying with HOTAS, so I made a small tool that lets you send chat messages using your voice.

**How it works:**
1. Assign any joystick button as push-to-talk
2. Hold the button and speak (in English)
3. Release - your message is transcribed and typed into War Thunder chat automatically

**Features:**
- Works with any joystick/HOTAS
- Runs 100% locally (no internet, no cloud, no account)
- Uses OpenAI Whisper for speech recognition
- Minimizes to system tray
- Free and open source

**Why I made this:**
In sim battles, communication is key but typing while flying is dangerous. With this tool, I can call out enemy positions, coordinate with squadmates, or just chat without taking my hands off the stick.

**Download:** [GitHub link]

**Requirements:**
- Windows 10/11
- A microphone
- A joystick

The first transcription takes a few seconds while the AI model loads, but after that it's pretty quick.

Let me know if you have any questions or suggestions!

---

## War Thunder Forum Post

**Title:** [Tool] Voice-to-Chat for Simulator Battles - Free HOTAS-friendly communication

---

**Description:**

War Thunder Voice Chat is a free Windows application that allows you to send chat messages using your voice and joystick.

**The Problem:**
In Simulator Battles, typing chat messages while flying is difficult and dangerous. You have to take your hands off the controls, look at the keyboard, and hope you don't crash in the meantime.

**The Solution:**
This tool lets you assign any joystick button as a push-to-talk key. Hold the button, speak your message in English, release, and the message is automatically typed into the War Thunder chat.

**Technical Details:**
- Speech recognition powered by OpenAI Whisper (runs locally, no internet required)
- Keyboard simulation via Windows SendInput API (works even when War Thunder has focus)
- Supports different chat keybindings (Enter, T, Y, U)
- Configurable Whisper models (tiny/small/medium) for speed vs accuracy tradeoff

**Features:**
- Push-to-talk with any joystick button
- Local speech-to-text (no data sent anywhere)
- System tray support
- Auto-start with Windows option
- Dark theme UI
- Open source (MIT license)

**Download:**
- Standalone .exe (no Python required): [Release link]
- Source code: [GitHub link]

**How to Use:**
1. Download and run the application
2. Select your joystick from the dropdown
3. Click "Assign" and press your desired PTT button
4. Set the chat key to match your in-game keybinding
5. Hold button → Speak → Release → Message sent!

**Screenshots:**
[Insert application screenshot]

**Notes:**
- First transcription may take a moment while the AI model loads (~500MB download on first run)
- Some antivirus software may flag the application due to keyboard simulation - this is a false positive
- Currently English only for transcription

**Feedback Welcome:**
This is a personal project I made for my own use, but I thought the sim community might find it useful. Let me know if you encounter any issues or have suggestions for improvements.

See you in the skies!

---

## Short Version (for Discord/quick shares)

**War Thunder Voice Chat** - Free voice-to-text for sim players

Hold joystick button → Speak → Message typed in chat automatically

- Works with any HOTAS
- Runs locally (no internet)
- Open source

Download: [link]
