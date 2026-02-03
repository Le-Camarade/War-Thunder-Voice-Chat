"""
SettingsFrame - Application settings panel.

Contains controls for:
- Joystick selection
- PTT button assignment
- Whisper model selection
- Chat key selection
"""

import customtkinter as ctk
from typing import Callable, Optional, List
from .widgets import JoystickButtonSelector


class SettingsFrame(ctk.CTkFrame):
    """Settings panel."""

    def __init__(
        self,
        master,
        on_joystick_change: Optional[Callable[[str], None]] = None,
        on_button_change: Optional[Callable[[int], None]] = None,
        on_model_change: Optional[Callable[[str], None]] = None,
        on_chat_key_change: Optional[Callable[[str], None]] = None,
        on_auto_start_change: Optional[Callable[[bool], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)

        self._on_joystick_change = on_joystick_change
        self._on_button_change = on_button_change
        self._on_model_change = on_model_change
        self._on_chat_key_change = on_chat_key_change
        self._on_auto_start_change = on_auto_start_change

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create panel widgets."""

        # === Joystick ===
        joystick_label = ctk.CTkLabel(
            self,
            text="Joystick:",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        joystick_label.grid(row=0, column=0, sticky="w", padx=10, pady=(15, 5))

        joystick_frame = ctk.CTkFrame(self, fg_color="transparent")
        joystick_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        self._joystick_combo = ctk.CTkComboBox(
            joystick_frame,
            values=["No joystick detected"],
            width=220,
            command=self._on_joystick_selected,
            state="readonly"
        )
        self._joystick_combo.pack(side="left", padx=(0, 10))

        self._refresh_btn = ctk.CTkButton(
            joystick_frame,
            text="↻",
            width=30,
            command=self._request_refresh
        )
        self._refresh_btn.pack(side="left")
        self._refresh_callback: Optional[Callable[[], None]] = None

        # === PTT Button ===
        ptt_label = ctk.CTkLabel(
            self,
            text="Push-to-Talk:",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        ptt_label.grid(row=2, column=0, sticky="w", padx=10, pady=(10, 5))

        self._button_selector = JoystickButtonSelector(
            self,
            on_button_set=self._on_button_set
        )
        self._button_selector.grid(row=3, column=0, sticky="w", padx=10, pady=(0, 10))

        # === Whisper Model ===
        model_label = ctk.CTkLabel(
            self,
            text="Model:",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        model_label.grid(row=4, column=0, sticky="w", padx=10, pady=(10, 5))

        self._model_combo = ctk.CTkComboBox(
            self,
            values=["tiny", "small", "medium"],
            width=150,
            command=self._on_model_selected
        )
        self._model_combo.set("small")
        self._model_combo.grid(row=5, column=0, sticky="w", padx=10, pady=(0, 10))

        # === Chat Key ===
        chat_key_label = ctk.CTkLabel(
            self,
            text="Chat Key (in-game):",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        chat_key_label.grid(row=6, column=0, sticky="w", padx=10, pady=(10, 5))

        self._chat_key_combo = ctk.CTkComboBox(
            self,
            values=["enter", "t", "y", "u"],
            width=150,
            command=self._on_chat_key_selected
        )
        self._chat_key_combo.set("enter")
        self._chat_key_combo.grid(row=7, column=0, sticky="w", padx=10, pady=(0, 10))

        # === Auto-start ===
        self._auto_start_var = ctk.BooleanVar(value=False)
        self._auto_start_checkbox = ctk.CTkCheckBox(
            self,
            text="Start with Windows",
            variable=self._auto_start_var,
            command=self._on_auto_start_toggled
        )
        self._auto_start_checkbox.grid(row=8, column=0, sticky="w", padx=10, pady=(5, 15))

        # Configure grid
        self.grid_columnconfigure(0, weight=1)

    def _on_joystick_selected(self, choice: str) -> None:
        """Called when a joystick is selected."""
        if self._on_joystick_change and choice != "No joystick detected":
            self._on_joystick_change(choice)

    def _on_button_set(self, button_id: int) -> None:
        """Called when a PTT button is assigned."""
        if self._on_button_change:
            self._on_button_change(button_id)

    def _on_model_selected(self, choice: str) -> None:
        """Called when the model is changed."""
        if self._on_model_change:
            self._on_model_change(choice)

    def _on_chat_key_selected(self, choice: str) -> None:
        """Called when the chat key is changed."""
        if self._on_chat_key_change:
            self._on_chat_key_change(choice)

    def _on_auto_start_toggled(self) -> None:
        """Called when auto-start is toggled."""
        if self._on_auto_start_change:
            self._on_auto_start_change(self._auto_start_var.get())

    def _request_refresh(self) -> None:
        """Request joystick list refresh."""
        if self._refresh_callback:
            self._refresh_callback()

    def set_refresh_callback(self, callback: Callable[[], None]) -> None:
        """Set the refresh button callback."""
        self._refresh_callback = callback

    def update_joysticks(self, joystick_names: List[str]) -> None:
        """Update the joystick list."""
        if joystick_names:
            self._joystick_combo.configure(values=joystick_names)
            self._joystick_combo.set(joystick_names[0])
        else:
            self._joystick_combo.configure(values=["No joystick detected"])
            self._joystick_combo.set("No joystick detected")

    def set_joystick(self, name: str) -> None:
        """Select a joystick by name."""
        self._joystick_combo.set(name)

    def set_button(self, button_id: int) -> None:
        """Set the displayed PTT button."""
        self._button_selector.set_button(button_id)

    def set_model(self, model: str) -> None:
        """Set the Whisper model."""
        self._model_combo.set(model)

    def set_chat_key(self, key: str) -> None:
        """Set the chat key."""
        self._chat_key_combo.set(key)

    def set_auto_start(self, enabled: bool) -> None:
        """Set the auto-start state."""
        self._auto_start_var.set(enabled)

    @property
    def button_selector(self) -> JoystickButtonSelector:
        """Return the button selector for external listening."""
        return self._button_selector

    def get_settings(self) -> dict:
        """Return current settings."""
        return {
            "joystick": self._joystick_combo.get(),
            "button": self._button_selector.get_button(),
            "model": self._model_combo.get(),
            "chat_key": self._chat_key_combo.get()
        }
