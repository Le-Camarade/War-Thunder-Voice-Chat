"""
TTSSettingsFrame - TTS configuration panel.

Contains controls for:
- TTS ON/OFF toggle
- Voice selection
- Speed slider
- Channel filtering (Team, All, Squadron)
- Username filtering
- War Thunder connection status
"""

import customtkinter as ctk
from typing import Callable, Optional, List
from core.tts_engine import VoiceInfo


class TTSSettingsFrame(ctk.CTkFrame):
    """TTS settings panel."""

    def __init__(
        self,
        master,
        on_enabled_change: Optional[Callable[[bool], None]] = None,
        on_engine_change: Optional[Callable[[str], None]] = None,
        on_voice_change: Optional[Callable[[str], None]] = None,
        on_rate_change: Optional[Callable[[int], None]] = None,
        on_channel_change: Optional[Callable[[str, bool], None]] = None,
        on_username_change: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)

        self._on_enabled_change = on_enabled_change
        self._on_engine_change = on_engine_change
        self._on_voice_change = on_voice_change
        self._on_rate_change = on_rate_change
        self._on_channel_change = on_channel_change
        self._on_username_change = on_username_change

        self._voices: List[VoiceInfo] = []

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create panel widgets."""

        # === Header with toggle ===
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(15, 10))

        ctk.CTkLabel(
            header_frame,
            text="Chat Reader (TTS)",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        ).pack(side="left")

        self._enabled_var = ctk.BooleanVar(value=False)
        self._enabled_switch = ctk.CTkSwitch(
            header_frame,
            text="",
            variable=self._enabled_var,
            command=self._on_enabled_toggled,
            width=40
        )
        self._enabled_switch.pack(side="right")

        # === Engine selector ===
        ctk.CTkLabel(
            self,
            text="Engine:",
            font=ctk.CTkFont(size=13),
            anchor="w"
        ).grid(row=1, column=0, sticky="w", padx=10, pady=(5, 3))

        engine_frame = ctk.CTkFrame(self, fg_color="transparent")
        engine_frame.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 8))

        self._engine_var = ctk.StringVar(value="offline")
        ctk.CTkRadioButton(
            engine_frame,
            text="Offline (Windows)",
            variable=self._engine_var,
            value="offline",
            command=self._on_engine_toggled
        ).pack(side="left", padx=(0, 15))

        ctk.CTkRadioButton(
            engine_frame,
            text="Online (Edge - better)",
            variable=self._engine_var,
            value="online",
            command=self._on_engine_toggled
        ).pack(side="left")

        # === Voice ===
        ctk.CTkLabel(
            self,
            text="Voice:",
            font=ctk.CTkFont(size=13),
            anchor="w"
        ).grid(row=3, column=0, sticky="w", padx=10, pady=(5, 3))

        self._voice_combo = ctk.CTkComboBox(
            self,
            values=["Loading..."],
            width=280,
            command=self._on_voice_selected,
            state="readonly"
        )
        self._voice_combo.grid(row=4, column=0, sticky="w", padx=10, pady=(0, 8))

        # === Speed ===
        speed_frame = ctk.CTkFrame(self, fg_color="transparent")
        speed_frame.grid(row=5, column=0, sticky="ew", padx=10, pady=(5, 3))

        ctk.CTkLabel(
            speed_frame,
            text="Speed:",
            font=ctk.CTkFont(size=13),
            anchor="w"
        ).pack(side="left")

        self._rate_label = ctk.CTkLabel(
            speed_frame,
            text="150",
            font=ctk.CTkFont(size=13),
            width=40,
            anchor="e"
        )
        self._rate_label.pack(side="right")

        self._rate_slider = ctk.CTkSlider(
            self,
            from_=80,
            to=250,
            number_of_steps=17,
            command=self._on_rate_changed,
            width=280
        )
        self._rate_slider.set(150)
        self._rate_slider.grid(row=6, column=0, sticky="w", padx=10, pady=(0, 8))

        # === Channels ===
        ctk.CTkLabel(
            self,
            text="Read channels:",
            font=ctk.CTkFont(size=13),
            anchor="w"
        ).grid(row=7, column=0, sticky="w", padx=10, pady=(5, 3))

        channels_frame = ctk.CTkFrame(self, fg_color="transparent")
        channels_frame.grid(row=8, column=0, sticky="w", padx=10, pady=(0, 8))

        self._channel_team_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            channels_frame,
            text="Team",
            variable=self._channel_team_var,
            command=lambda: self._on_channel_toggled("team", self._channel_team_var.get())
        ).pack(side="left", padx=(0, 15))

        self._channel_all_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            channels_frame,
            text="All",
            variable=self._channel_all_var,
            command=lambda: self._on_channel_toggled("all", self._channel_all_var.get())
        ).pack(side="left", padx=(0, 15))

        self._channel_squadron_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            channels_frame,
            text="Squadron",
            variable=self._channel_squadron_var,
            command=lambda: self._on_channel_toggled("squadron", self._channel_squadron_var.get())
        ).pack(side="left")

        # === Username ===
        ctk.CTkLabel(
            self,
            text="Your username:",
            font=ctk.CTkFont(size=13),
            anchor="w"
        ).grid(row=9, column=0, sticky="w", padx=10, pady=(5, 3))

        self._username_entry = ctk.CTkEntry(
            self,
            width=280,
            placeholder_text="e.g. Le_Camarade"
        )
        self._username_entry.grid(row=10, column=0, sticky="w", padx=10, pady=(0, 8))
        self._username_entry.bind("<FocusOut>", self._on_username_focus_out)
        self._username_entry.bind("<Return>", self._on_username_focus_out)

        # === Connection status ===
        self._status_label = ctk.CTkLabel(
            self,
            text="WT: Not checked",
            font=ctk.CTkFont(size=12),
            text_color="#999999",
            anchor="w"
        )
        self._status_label.grid(row=11, column=0, sticky="w", padx=10, pady=(5, 15))

        # Configure grid
        self.grid_columnconfigure(0, weight=1)

    # --- Callbacks ---

    def _on_enabled_toggled(self) -> None:
        enabled = self._enabled_var.get()
        if self._on_enabled_change:
            self._on_enabled_change(enabled)

    def _on_engine_toggled(self) -> None:
        engine_type = self._engine_var.get()
        if self._on_engine_change:
            self._on_engine_change(engine_type)

    def _on_voice_selected(self, choice: str) -> None:
        # Retrouver le voice_id depuis le nom affiché
        for v in self._voices:
            if v.name == choice:
                if self._on_voice_change:
                    self._on_voice_change(v.id)
                return

    def _on_rate_changed(self, value: float) -> None:
        rate = int(value)
        self._rate_label.configure(text=str(rate))
        if self._on_rate_change:
            self._on_rate_change(rate)

    def _on_channel_toggled(self, channel: str, enabled: bool) -> None:
        if self._on_channel_change:
            self._on_channel_change(channel, enabled)

    def _on_username_focus_out(self, event=None) -> None:
        username = self._username_entry.get().strip()
        if self._on_username_change:
            self._on_username_change(username)

    # --- Public methods ---

    def update_voices(self, voices: List[VoiceInfo]) -> None:
        """Update voice dropdown with available voices."""
        self._voices = voices
        if voices:
            names = [v.name for v in voices]
            self._voice_combo.configure(values=names)
            self._voice_combo.set(names[0])
        else:
            self._voice_combo.configure(values=["No voice available"])
            self._voice_combo.set("No voice available")

    def set_enabled(self, enabled: bool) -> None:
        self._enabled_var.set(enabled)

    def set_engine_type(self, engine_type: str) -> None:
        """Set engine type ('offline' or 'online')."""
        self._engine_var.set(engine_type)

    def set_voice(self, voice_id: str) -> None:
        """Select voice by ID."""
        for v in self._voices:
            if v.id == voice_id:
                self._voice_combo.set(v.name)
                return

    def set_rate(self, rate: int) -> None:
        self._rate_slider.set(rate)
        self._rate_label.configure(text=str(rate))

    def set_channels(self, team: bool, all_chat: bool, squadron: bool) -> None:
        self._channel_team_var.set(team)
        self._channel_all_var.set(all_chat)
        self._channel_squadron_var.set(squadron)

    def set_username(self, username: str) -> None:
        self._username_entry.delete(0, "end")
        if username:
            self._username_entry.insert(0, username)

    def set_connection_status(self, connected: bool) -> None:
        if connected:
            self._status_label.configure(
                text="WT: Connected",
                text_color="#44ff44"
            )
        else:
            self._status_label.configure(
                text="WT: Not detected",
                text_color="#ff4444"
            )
