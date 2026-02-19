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
from core.joystick import JoystickManager
from core.recorder import AudioRecorder
from core.transcriber import WhisperTranscriber
from core.injector import ChatInjector
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
        self.geometry("400x700")
        self.resizable(False, False)

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

        # State
        self._is_recording = False
        self._current_state = "idle"
        self._transcribe_thread: Optional[threading.Thread] = None

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

        # Bind close event
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self) -> None:
        """Create interface widgets."""

        # === Status zone ===
        status_frame = ctk.CTkFrame(self)
        status_frame.pack(fill="x", padx=20, pady=20)

        self._status_led = StatusLED(status_frame, size=50)
        self._status_led.pack(pady=15)

        # Volume indicator
        self._volume_indicator = VolumeIndicator(status_frame, width=200, height=15)
        self._volume_indicator.pack(pady=(0, 10))

        # === Settings ===
        self._settings_frame = SettingsFrame(
            self,
            on_joystick_change=self._on_joystick_change,
            on_button_change=self._on_button_change,
            on_model_change=self._on_model_change,
            on_chat_key_change=self._on_chat_key_change,
            on_auto_start_change=self._on_auto_start_change
        )
        self._settings_frame.pack(fill="x", padx=20, pady=(0, 10))
        self._settings_frame.set_refresh_callback(self._refresh_joysticks)

        # === Last message ===
        self._message_display = MessageDisplay(self)
        self._message_display.pack(fill="x", padx=20, pady=(0, 10))

        # === Minimize button ===
        self._minimize_btn = ctk.CTkButton(
            self,
            text="Minimize to Tray",
            command=self._minimize_to_tray
        )
        self._minimize_btn.pack(pady=(10, 20))

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
        try:
            self._recorder.start_recording()
        except Exception as e:
            logger.error(f"Microphone error: {e}")
            self._is_recording = False
            self._set_state("error", "Microphone not available")
            self.after(3000, lambda: self._set_state("idle"))
            return

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
        self._transcribe_thread = threading.Thread(
            target=self._transcribe_and_inject,
            args=(audio,),
            daemon=True
        )
        self._transcribe_thread.start()

        # Timeout: if transcription takes >60s, abort
        self.after(60000, self._check_transcription_timeout)

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

            # Show loading state if model not yet loaded
            if not self._transcriber.is_loaded:
                self.after(0, lambda: self._set_state(
                    "loading_model",
                    f"Downloading/loading {self._config_manager.config.model} model..."
                ))

            # Transcription
            translate = self._config_manager.config.translate_to_english
            text = self._transcriber.transcribe(audio, translate=translate)

            # Check if we were cancelled by timeout
            if self._current_state == "idle":
                return

            self.after(0, lambda: self._set_state("transcribing"))

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
                self.after(0, lambda: self._set_state("error", "Injection failed"))
                self.after(2000, lambda: self._set_state("idle"))

        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            self.after(0, lambda: self._set_state("error", "Whisper not installed correctly"))
            self.after(4000, lambda: self._set_state("idle"))
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Transcription/injection error: {error_msg}")
            # Provide user-friendly messages for common errors
            if "connection" in error_msg.lower() or "url" in error_msg.lower():
                detail = "Model download failed - check internet"
            elif "memory" in error_msg.lower() or "oom" in error_msg.lower():
                detail = "Not enough RAM - try 'tiny' model"
            elif "no such file" in error_msg.lower() or "not found" in error_msg.lower():
                detail = "Model file not found"
            else:
                detail = error_msg[:80]
            self.after(0, lambda d=detail: self._set_state("error", d))
            self.after(4000, lambda: self._set_state("idle"))
        finally:
            self._transcribe_thread = None

    def _check_transcription_timeout(self) -> None:
        """Cancel transcription if it's been running too long."""
        if self._transcribe_thread is not None and self._transcribe_thread.is_alive():
            if self._current_state in ("transcribing", "loading_model"):
                logger.warning("Transcription timeout (60s)")
                self._transcribe_thread = None
                self._set_state("error", "Timeout - model may still be downloading")
                self.after(4000, lambda: self._set_state("idle"))

    def _set_state(self, state: str, detail: str = "") -> None:
        """Change application state."""
        self._current_state = state
        self._status_led.set_state(state, detail)

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

        self.destroy()
