"""
App - Main window for War Thunder Voice Chat.

Integrates all components: joystick, audio, transcription, injection.
"""

import customtkinter as ctk
import threading
import os
import sys
from typing import Optional

from .widgets import StatusLED, MessageDisplay, VolumeIndicator
from .settings_frame import SettingsFrame
from .tts_settings import TTSSettingsFrame
from core.joystick import JoystickManager
from core.recorder import AudioRecorder
from core.transcriber import WhisperTranscriber
from core.injector import ChatInjector
from core.chat_listener import ChatListener, ChatMessage
from core.tts_engine import TTSEngine, EdgeTTSEngine
from core.autostart import set_auto_start
from config import ConfigManager

# System tray
try:
    import pystray
    from PIL import Image
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False


def get_resource_path(filename: str) -> str:
    """Return the path to a resource (PyInstaller compatible)."""
    if getattr(sys, 'frozen', False):
        # PyInstaller: resources in temp folder
        base_path = sys._MEIPASS
    else:
        # Python script: parent folder (project root)
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, filename)


def load_app_icon():
    """Load the application icon."""
    if not TRAY_AVAILABLE:
        return None

    # Try to load the logo
    logo_path = get_resource_path("wt_radio_logo_minimalism.png")
    if os.path.exists(logo_path):
        try:
            return Image.open(logo_path)
        except Exception:
            pass

    # Fallback: generated icon
    from PIL import ImageDraw
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse([8, 8, 56, 56], fill="#4488ff")
    draw.ellipse([21, 21, 43, 43], fill="#1a1a1a")
    return image


class App(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("War Thunder Voice Chat")
        self.geometry("400x750")
        self.resizable(False, True)
        self.minsize(400, 400)

        # Window icon
        icon_path = get_resource_path("icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        # Dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # System tray
        self._tray_icon = None
        self._is_hidden = False

        # Configuration manager
        self._config_manager = ConfigManager()
        self._config_manager.load()

        # Core components
        self._joystick_manager = JoystickManager()
        self._recorder = AudioRecorder()
        self._transcriber: Optional[WhisperTranscriber] = None
        self._injector = ChatInjector(
            delay_ms=self._config_manager.config.injection_delay_ms,
            chat_key=self._config_manager.config.chat_key
        )

        # TTS components (engine created in _setup_tts based on config)
        self._tts_engine = None
        self._chat_listener = ChatListener()

        # State
        self._is_recording = False
        self._current_state = "idle"

        # Create interface
        self._create_widgets()

        # Initialize joysticks
        self._refresh_joysticks()

        # Load saved configuration
        self._load_saved_config()

        # Setup joystick callbacks
        self._setup_joystick_callbacks()

        # Start joystick polling
        self._joystick_manager.start()

        # Initialize TTS
        self._setup_tts()

        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self) -> None:
        """Create interface widgets."""

        # === Scrollable container ===
        self._scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # === Status zone ===
        status_frame = ctk.CTkFrame(self._scroll_frame)
        status_frame.pack(fill="x", padx=15, pady=(15, 10))

        self._status_led = StatusLED(status_frame, size=50)
        self._status_led.pack(pady=15)

        # Volume indicator
        self._volume_indicator = VolumeIndicator(status_frame, width=200, height=15)
        self._volume_indicator.pack(pady=(0, 10))

        # === Settings ===
        self._settings_frame = SettingsFrame(
            self._scroll_frame,
            on_joystick_change=self._on_joystick_change,
            on_button_change=self._on_button_change,
            on_model_change=self._on_model_change,
            on_chat_key_change=self._on_chat_key_change,
            on_auto_start_change=self._on_auto_start_change,
            on_translate_change=self._on_translate_change
        )
        self._settings_frame.pack(fill="x", padx=15, pady=(0, 10))
        self._settings_frame.set_refresh_callback(self._refresh_joysticks)

        # === TTS Settings ===
        self._tts_settings = TTSSettingsFrame(
            self._scroll_frame,
            on_enabled_change=self._on_tts_enabled_change,
            on_engine_change=self._on_tts_engine_change,
            on_voice_change=self._on_tts_voice_change,
            on_rate_change=self._on_tts_rate_change,
            on_channel_change=self._on_tts_channel_change,
            on_username_change=self._on_tts_username_change
        )
        self._tts_settings.pack(fill="x", padx=15, pady=(0, 10))

        # === Last message ===
        self._message_display = MessageDisplay(self._scroll_frame)
        self._message_display.pack(fill="x", padx=15, pady=(0, 10))

        # === Minimize button ===
        self._minimize_btn = ctk.CTkButton(
            self._scroll_frame,
            text="Minimize to Tray",
            command=self._minimize_to_tray
        )
        self._minimize_btn.pack(pady=(10, 15))

    def _refresh_joysticks(self) -> None:
        """Refresh joystick list."""
        joysticks = self._joystick_manager.refresh()
        names = [j.name for j in joysticks]
        self._settings_frame.update_joysticks(names)

        if not names:
            return

        # Re-select saved joystick if available
        saved_name = self._config_manager.config.joystick_name
        if saved_name and saved_name in names:
            self._settings_frame.set_joystick(saved_name)
            self._joystick_manager.select_joystick_by_name(saved_name)
        else:
            # Select first joystick by default
            self._joystick_manager.select_joystick_by_name(names[0])
            self._config_manager.config.joystick_name = names[0]

    def _load_saved_config(self) -> None:
        """Load saved configuration."""
        config = self._config_manager.config

        # Joystick and button
        if config.joystick_name:
            self._settings_frame.set_joystick(config.joystick_name)
            self._joystick_manager.select_joystick_by_name(config.joystick_name)
        if config.button_id >= 0:
            self._settings_frame.set_button(config.button_id)
            self._joystick_manager.set_ptt_button(config.button_id)

        # Model
        self._settings_frame.set_model(config.model)

        # Chat key
        self._settings_frame.set_chat_key(config.chat_key)
        self._injector.set_chat_key(config.chat_key)

        # Translate
        self._settings_frame.set_translate(config.translate_to_english)

        # Auto-start
        self._settings_frame.set_auto_start(config.auto_start)

        # Geometry
        if config.window_geometry:
            try:
                self.geometry(config.window_geometry)
            except:
                pass

    def _setup_joystick_callbacks(self) -> None:
        """Setup joystick callbacks."""
        self._joystick_manager.set_on_button_down(self._on_ptt_press)
        self._joystick_manager.set_on_button_up(self._on_ptt_release)
        self._joystick_manager.set_on_any_button(self._on_any_button)

    def _on_joystick_change(self, name: str) -> None:
        """Called when selected joystick changes."""
        self._joystick_manager.select_joystick_by_name(name)
        self._config_manager.config.joystick_name = name
        self._config_manager.save()

    def _on_button_change(self, button_id: int) -> None:
        """Called when PTT button changes."""
        self._joystick_manager.set_ptt_button(button_id)
        self._config_manager.config.button_id = button_id
        self._config_manager.save()

    def _on_model_change(self, model: str) -> None:
        """Called when Whisper model changes."""
        self._config_manager.config.model = model
        self._config_manager.save()

        # Update transcriber if loaded
        if self._transcriber:
            self._transcriber.change_settings(model_size=model)

    def _on_chat_key_change(self, key: str) -> None:
        """Called when chat key changes."""
        self._injector.set_chat_key(key)
        self._config_manager.config.chat_key = key
        self._config_manager.save()

    def _on_translate_change(self, enabled: bool) -> None:
        """Called when translate toggle changes."""
        self._config_manager.config.translate_to_english = enabled
        self._config_manager.save()

    def _on_auto_start_change(self, enabled: bool) -> None:
        """Called when auto-start is toggled."""
        set_auto_start(enabled)
        self._config_manager.config.auto_start = enabled
        self._config_manager.save()

    def _on_any_button(self, joystick_id: int, button_id: int) -> None:
        """Called when any button is pressed (for assignment)."""
        selector = self._settings_frame.button_selector
        if selector.is_listening:
            # Use after() to update UI from main thread
            self.after(0, lambda: selector.stop_listening(button_id))

    def _on_ptt_press(self, joystick_id: int, button_id: int) -> None:
        """Called when PTT button is pressed (from pygame thread)."""
        # Execute on main Tkinter thread
        self.after(0, self._do_ptt_press)

    def _do_ptt_press(self) -> None:
        """Start recording (main thread)."""
        if self._is_recording or self._current_state != "idle":
            return

        self._is_recording = True
        self._set_state("recording")

        # Start recording
        self._recorder.start_recording()

        # Start volume update
        self._update_volume()

    def _on_ptt_release(self, joystick_id: int, button_id: int) -> None:
        """Called when PTT button is released (from pygame thread)."""
        # Execute on main Tkinter thread
        self.after(0, self._do_ptt_release)

    def _do_ptt_release(self) -> None:
        """Stop recording and start transcription (main thread)."""
        if not self._is_recording:
            return

        self._is_recording = False

        # Stop recording and get audio
        audio = self._recorder.stop_recording()

        # Reset volume indicator
        self._volume_indicator.set_level(0)

        if audio.size == 0:
            self._set_state("idle")
            return

        # Start transcription in thread
        self._set_state("transcribing")
        thread = threading.Thread(
            target=self._transcribe_and_inject,
            args=(audio,),
            daemon=True
        )
        thread.start()

    def _update_volume(self) -> None:
        """Update volume indicator during recording."""
        if not self._is_recording:
            return

        # Calculate volume level from buffer
        import numpy as np
        try:
            if self._recorder._buffer:
                # Get recent samples
                recent = self._recorder._buffer[-1] if self._recorder._buffer else np.array([0])
                rms = np.sqrt(np.mean(recent ** 2))
                # Normalize (0.0 to 1.0)
                level = min(1.0, rms * 10)
                self._volume_indicator.set_level(level)
        except:
            pass

        # Continue update
        if self._is_recording:
            self.after(50, self._update_volume)

    def _transcribe_and_inject(self, audio) -> None:
        """Transcribe audio and inject text (in thread)."""
        try:
            # Initialize transcriber if needed
            if self._transcriber is None:
                config = self._config_manager.config
                self._transcriber = WhisperTranscriber(
                    model_size=config.model,
                    device="cpu"
                )

            # Transcription
            translate = self._config_manager.config.translate_to_english
            text = self._transcriber.transcribe(audio, translate=translate)

            if not text:
                self.after(0, lambda: self._set_state("idle"))
                return

            # Update message display
            self.after(0, lambda: self._message_display.set_message(text))

            # Injection
            self.after(0, lambda: self._set_state("sending"))
            success = self._injector.inject(text)

            if success:
                self.after(0, lambda: self._set_state("sent"))
                # Return to idle after 1.5s
                self.after(1500, lambda: self._set_state("idle"))
            else:
                self.after(0, lambda: self._set_state("error"))
                self.after(2000, lambda: self._set_state("idle"))

        except Exception as e:
            print(f"Transcription/injection error: {e}")
            self.after(0, lambda: self._set_state("error"))
            self.after(2000, lambda: self._set_state("idle"))

    def _set_state(self, state: str) -> None:
        """Change application state."""
        self._current_state = state
        self._status_led.set_state(state)

    # === TTS ===

    def _setup_tts(self) -> None:
        """Initialize TTS engine and load TTS config."""
        config = self._config_manager.config

        # Create and start engine based on saved type
        self._create_tts_engine(config.tts_engine_type)

        # Set engine selector in UI
        self._tts_settings.set_engine_type(config.tts_engine_type)

        # Load saved TTS settings
        if config.tts_voice_id:
            self._tts_engine.set_voice(config.tts_voice_id)
            self._tts_settings.set_voice(config.tts_voice_id)

        self._tts_engine.set_rate(config.tts_rate)
        self._tts_settings.set_rate(config.tts_rate)

        self._tts_settings.set_channels(
            config.tts_channel_team,
            config.tts_channel_all,
            config.tts_channel_squadron
        )

        self._tts_settings.set_username(config.tts_own_username)

        # Configure chat listener
        self._chat_listener.set_on_new_message(self._on_chat_message)
        if config.tts_own_username:
            self._chat_listener.set_own_username(config.tts_own_username)
        if config.tts_poll_interval_ms:
            self._chat_listener.set_poll_interval(config.tts_poll_interval_ms)

        # Enable TTS if it was enabled
        self._tts_settings.set_enabled(config.tts_enabled)
        if config.tts_enabled:
            self._start_tts()

        # Start WT connection check
        self._check_wt_connection()

    def _create_tts_engine(self, engine_type: str) -> None:
        """Create and start a TTS engine of the given type."""
        # Stop existing engine if running
        if self._tts_engine:
            self._tts_engine.stop()

        # Create new engine
        if engine_type == "online":
            self._tts_engine = EdgeTTSEngine()
        else:
            self._tts_engine = TTSEngine()

        # Start and load voices
        self._tts_engine.start()
        voices = self._tts_engine.get_available_voices()
        self._tts_settings.update_voices(voices)

    def _start_tts(self) -> None:
        """Start the chat listener."""
        self._chat_listener.start()

    def _stop_tts(self) -> None:
        """Stop the chat listener and clear TTS queue."""
        self._chat_listener.stop()
        self._tts_engine.clear_queue()

    def _on_chat_message(self, msg: ChatMessage) -> None:
        """Called when a new chat message arrives (from listener thread)."""
        config = self._config_manager.config

        # Filter by channel
        channel_lower = msg.channel.lower()
        if any(k in channel_lower for k in ("équipe", "team")):
            if not config.tts_channel_team:
                return
        elif any(k in channel_lower for k in ("tous", "all")):
            if not config.tts_channel_all:
                return
        elif any(k in channel_lower for k in ("escadron", "squadron")):
            if not config.tts_channel_squadron:
                return

        # Format and speak
        tts_text = f"{msg.sender} says: {msg.content}"
        self._tts_engine.speak(tts_text)

        # Update last heard display on main thread
        display_text = f"{msg.sender}: {msg.content}"
        self.after(0, lambda: self._message_display.set_message(display_text))

    def _check_wt_connection(self) -> None:
        """Periodically check if War Thunder is running."""
        connected = self._chat_listener.is_game_running()
        self._tts_settings.set_connection_status(connected)
        # Check again in 5 seconds
        self.after(5000, self._check_wt_connection)

    def _on_tts_enabled_change(self, enabled: bool) -> None:
        """Called when TTS is toggled."""
        self._config_manager.config.tts_enabled = enabled
        self._config_manager.save()
        if enabled:
            self._start_tts()
        else:
            self._stop_tts()

    def _on_tts_engine_change(self, engine_type: str) -> None:
        """Called when TTS engine type changes (offline/online)."""
        config = self._config_manager.config

        # Recreate engine with new type
        self._create_tts_engine(engine_type)

        # Re-apply rate setting
        self._tts_engine.set_rate(config.tts_rate)

        # Save config (voice_id reset since voices differ between engines)
        config.tts_engine_type = engine_type
        config.tts_voice_id = ""
        self._config_manager.save()

    def _on_tts_voice_change(self, voice_id: str) -> None:
        """Called when TTS voice changes."""
        self._tts_engine.set_voice(voice_id)
        self._config_manager.config.tts_voice_id = voice_id
        self._config_manager.save()

    def _on_tts_rate_change(self, rate: int) -> None:
        """Called when TTS speed changes."""
        self._tts_engine.set_rate(rate)
        self._config_manager.config.tts_rate = rate
        self._config_manager.save()

    def _on_tts_channel_change(self, channel: str, enabled: bool) -> None:
        """Called when a channel filter changes."""
        config = self._config_manager.config
        if channel == "team":
            config.tts_channel_team = enabled
        elif channel == "all":
            config.tts_channel_all = enabled
        elif channel == "squadron":
            config.tts_channel_squadron = enabled
        self._config_manager.save()

    def _on_tts_username_change(self, username: str) -> None:
        """Called when username changes."""
        self._chat_listener.set_own_username(username)
        self._config_manager.config.tts_own_username = username
        self._config_manager.save()

    def _minimize_to_tray(self) -> None:
        """Minimize application to system tray."""
        if not TRAY_AVAILABLE:
            # Fallback: minimize normally
            self.iconify()
            return

        # Create tray icon if not done yet
        if self._tray_icon is None:
            self._create_tray_icon()

        # Hide window
        self.withdraw()
        self._is_hidden = True

        # Show tray icon
        if self._tray_icon and not self._tray_icon.visible:
            threading.Thread(target=self._tray_icon.run, daemon=True).start()

    def _create_tray_icon(self) -> None:
        """Create system tray icon."""
        if not TRAY_AVAILABLE:
            return

        # Load logo
        image = load_app_icon()
        if image:
            # Resize for tray (64x64 max)
            image = image.resize((64, 64), Image.Resampling.LANCZOS)

        menu = pystray.Menu(
            pystray.MenuItem("Restore", self._restore_from_tray, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._quit_from_tray)
        )

        self._tray_icon = pystray.Icon(
            "WT Voice Chat",
            image,
            "War Thunder Voice Chat",
            menu
        )

    def _restore_from_tray(self, icon=None, item=None) -> None:
        """Restore window from system tray."""
        self._is_hidden = False

        # Restore window on main thread
        self.after(0, self._do_restore)

    def _do_restore(self) -> None:
        """Perform restoration (main thread)."""
        self.deiconify()
        self.lift()
        self.focus_force()

    def _quit_from_tray(self, icon=None, item=None) -> None:
        """Quit application from tray."""
        # Stop tray icon
        if self._tray_icon:
            self._tray_icon.stop()

        # Close application on main thread
        self.after(0, self._on_close)

    def _on_close(self) -> None:
        """Called when closing the application."""
        # Save geometry
        self._config_manager.config.window_geometry = self.geometry()
        self._config_manager.save()

        # Stop tray icon
        if self._tray_icon:
            try:
                self._tray_icon.stop()
            except:
                pass

        # Cleanup resources
        self._joystick_manager.cleanup()
        if self._transcriber:
            self._transcriber.unload_model()
        self._chat_listener.stop()
        if self._tts_engine:
            self._tts_engine.stop()

        self.destroy()
