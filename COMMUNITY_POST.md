# Community Post - War Thunder Voice Chat

---

## Reddit Post (r/WarThunderSim)

**Title:** I made a free voice-to-chat tool for Sim with TTS chat reader - Push joystick button, speak, message sent automatically

---

Hey fellow sim pilots,

I got tired of trying to type in chat while flying with HOTAS, so I made a small tool that lets you send chat messages using your voice. I've just added a chat reader feature too - the app reads incoming chat messages aloud so you never miss a callout.

**How it works:**
1. Assign any joystick button as push-to-talk
2. Hold the button and speak (in any language - it translates to English automatically)
3. Release - your message is transcribed and typed into War Thunder chat automatically

**NEW - Chat Reader (TTS):**
- The app reads incoming War Thunder chat messages aloud
- Choose between offline Windows voices or high-quality Microsoft Edge neural voices
- Filter by channel (Team, All, Squadron) and skip your own messages
- 9 neural voices available (EN, FR, DE, RU, JP, CN)

**Features:**
- Works with any joystick/HOTAS
- Runs 100% locally for voice recognition (no internet, no cloud, no account)
- Auto-translation from any language to English (toggleable)
- Uses OpenAI Whisper for speech recognition
- Minimizes to system tray
- Free and open source

**Why I made this:**
In sim battles, communication is key but typing while flying is dangerous. With this tool, I can call out enemy positions, coordinate with squadmates, or just chat without taking my hands off the stick. And now with TTS, I don't even need to look at the chat window.

**Download:** [GitHub link]

**Requirements:**
- Windows 10/11
- A microphone
- A joystick
- Internet (only for Edge TTS neural voices, everything else works offline)

The first transcription takes a few seconds while the AI model loads, but after that it's pretty quick.

Let me know if you have any questions or suggestions!

---

## War Thunder Forum Post

**Title:** [Tool] Voice-to-Chat + Chat Reader for Simulator Battles - Free HOTAS-friendly communication

---

**Description:**

War Thunder Voice Chat is a free Windows application that allows you to send chat messages using your voice and joystick, and hear incoming chat messages read aloud.

**The Problem:**
In Simulator Battles, typing chat messages while flying is difficult and dangerous. You have to take your hands off the controls, look at the keyboard, and hope you don't crash in the meantime. Reading the chat is equally distracting.

**The Solution:**
This tool lets you assign any joystick button as a push-to-talk key. Hold the button, speak your message in any language, release, and the message is automatically translated to English and typed into the War Thunder chat. Incoming messages are read aloud by TTS so you never need to look at the chat window.

**Technical Details:**
- Speech recognition powered by OpenAI Whisper (runs locally, no internet required)
- Auto-translation from any language to English (can be disabled)
- Keyboard simulation via Windows SendInput API (works even when War Thunder has focus)
- Supports different chat keybindings (Enter, T, Y, U)
- Configurable Whisper models (tiny/small/medium) for speed vs accuracy tradeoff
- Chat reader uses War Thunder's local API (localhost:8111) to read incoming messages

**Features:**
- Push-to-talk with any joystick button
- Local speech-to-text (no data sent anywhere)
- Translate to English toggle (speak in your native language)
- Chat reader with 2 TTS engines:
  - Offline: Windows SAPI5 voices (no internet)
  - Online: Microsoft Edge neural voices (9 voices, higher quality)
- Channel filtering (Team, All, Squadron)
- Own message filtering (enter your username)
- System tray support
- Auto-start with Windows option
- Dark theme UI
- Settings persist between launches
- Open source (MIT license)

**Download:**
- Standalone .exe (no Python required): [Release link]
- Source code: [GitHub link]

**How to Use:**
1. Download and run the application
2. Select your joystick from the dropdown
3. Click "Assign" and press your desired PTT button
4. Set the chat key to match your in-game keybinding
5. Enable/disable "Translate to English" depending on your language
6. (Optional) Enable TTS: scroll down, pick a voice, toggle ON
7. Hold button → Speak → Release → Message sent!

**Screenshots:**
[Insert application screenshot]

**Notes:**
- First transcription may take a moment while the AI model loads (~500MB download on first run)
- Some antivirus software may flag the application due to keyboard simulation - this is a false positive
- Translation works best with European languages on the "small" model. Use "medium" for Asian languages
- Online TTS voices require an internet connection; offline voices work without

**Feedback Welcome:**
This is a personal project I made for my own use, but I thought the sim community might find it useful. Let me know if you encounter any issues or have suggestions for improvements.

See you in the skies!

---

## Short Version (for Discord/quick shares)

**War Thunder Voice Chat** - Free voice-to-text + chat reader for sim players

Hold joystick button → Speak in any language → Message translated & typed in chat automatically
+ TTS reads incoming chat aloud with neural voices

- Works with any HOTAS
- Runs locally (no internet needed for voice, optional for TTS)
- Auto-translate to English
- Open source

Download: [link]
