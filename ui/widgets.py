"""
Custom widgets for War Thunder Voice Chat interface.

Contains: StatusLED, JoystickButtonSelector, VolumeIndicator, MessageDisplay
"""

import customtkinter as ctk
from typing import Optional


class StatusLED(ctk.CTkFrame):
    """
    Status LED with different colors based on state.

    States: idle (gray), recording (red), transcribing (orange),
            sending (blue), sent (green), error (red)
    """

    COLORS = {
        "idle": "#666666",
        "recording": "#ff4444",
        "transcribing": "#ffaa00",
        "sending": "#4488ff",
        "sent": "#44ff44",
        "error": "#ff4444"
    }

    LABELS = {
        "idle": "Ready",
        "recording": "Recording...",
        "transcribing": "Transcribing...",
        "sending": "Sending...",
        "sent": "Sent!",
        "error": "Error"
    }

    def __init__(self, master, size: int = 40, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._size = size
        self._state = "idle"
        self._blink_job = None

        # Canvas for drawing the LED
        self._canvas = ctk.CTkCanvas(
            self,
            width=size,
            height=size,
            bg=self._get_bg_color(),
            highlightthickness=0
        )
        self._canvas.pack()

        # Status label
        self._label = ctk.CTkLabel(
            self,
            text=self.LABELS["idle"],
            font=ctk.CTkFont(size=14)
        )
        self._label.pack(pady=(5, 0))

        self._draw_led()

    def _get_bg_color(self) -> str:
        """Return background color based on theme."""
        return "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#dbdbdb"

    def _draw_led(self) -> None:
        """Draw the LED on canvas."""
        self._canvas.delete("all")

        color = self.COLORS.get(self._state, self.COLORS["idle"])
        padding = 4
        x0, y0 = padding, padding
        x1, y1 = self._size - padding, self._size - padding

        # Glow effect
        glow_color = self._lighten_color(color, 0.3)
        self._canvas.create_oval(
            x0 - 2, y0 - 2, x1 + 2, y1 + 2,
            fill=glow_color, outline=""
        )

        # Main LED
        self._canvas.create_oval(
            x0, y0, x1, y1,
            fill=color, outline="#333333", width=2
        )

        # Reflection
        self._canvas.create_oval(
            x0 + 6, y0 + 6, x0 + 14, y0 + 14,
            fill=self._lighten_color(color, 0.5), outline=""
        )

    def _lighten_color(self, hex_color: str, factor: float) -> str:
        """Lighten a hexadecimal color."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def set_state(self, state: str) -> None:
        """Change the LED state."""
        if self._blink_job:
            self.after_cancel(self._blink_job)
            self._blink_job = None

        self._state = state
        self._label.configure(text=self.LABELS.get(state, state))
        self._draw_led()

    def get_state(self) -> str:
        """Return current state."""
        return self._state


class JoystickButtonSelector(ctk.CTkFrame):
    """Widget for selecting a joystick button."""

    def __init__(self, master, on_button_set=None, **kwargs):
        super().__init__(master, **kwargs)

        self._on_button_set = on_button_set
        self._is_listening = False
        self._current_button = -1

        # Label showing current button
        self._button_label = ctk.CTkLabel(
            self,
            text="Not assigned",
            width=120,
            font=ctk.CTkFont(size=13)
        )
        self._button_label.pack(side="left", padx=(0, 10))

        # Assign button
        self._set_button = ctk.CTkButton(
            self,
            text="Assign",
            width=80,
            command=self._start_listening
        )
        self._set_button.pack(side="left")

    def _start_listening(self) -> None:
        """Start listening for joystick button."""
        self._is_listening = True
        self._button_label.configure(text="Press...")
        self._set_button.configure(state="disabled")

    def stop_listening(self, button_id: Optional[int] = None) -> None:
        """Stop listening and set the button."""
        self._is_listening = False
        self._set_button.configure(state="normal")

        if button_id is not None:
            self._current_button = button_id
            self._button_label.configure(text=f"Button {button_id}")
            if self._on_button_set:
                self._on_button_set(button_id)
        else:
            self._update_label()

    def _update_label(self) -> None:
        """Update label with current button."""
        if self._current_button >= 0:
            self._button_label.configure(text=f"Button {self._current_button}")
        else:
            self._button_label.configure(text="Not assigned")

    def set_button(self, button_id: int) -> None:
        """Set button without triggering callback."""
        self._current_button = button_id
        self._update_label()

    def get_button(self) -> int:
        """Return current button ID."""
        return self._current_button

    @property
    def is_listening(self) -> bool:
        return self._is_listening


class VolumeIndicator(ctk.CTkFrame):
    """Real-time audio volume indicator."""

    def __init__(self, master, width: int = 200, height: int = 20, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._width = width
        self._height = height
        self._level = 0.0

        self._canvas = ctk.CTkCanvas(
            self,
            width=width,
            height=height,
            bg="#1a1a1a",
            highlightthickness=1,
            highlightbackground="#333333"
        )
        self._canvas.pack()

        self._redraw_volume()

    def _redraw_volume(self) -> None:
        """Draw the volume indicator."""
        self._canvas.delete("all")

        # Background
        self._canvas.create_rectangle(
            0, 0, self._width, self._height,
            fill="#1a1a1a", outline=""
        )

        # Volume bar
        bar_width = int(self._level * self._width)
        if bar_width > 0:
            # Color gradient based on level
            if self._level < 0.6:
                color = "#44ff44"  # Green
            elif self._level < 0.85:
                color = "#ffaa00"  # Orange
            else:
                color = "#ff4444"  # Red

            self._canvas.create_rectangle(
                0, 0, bar_width, self._height,
                fill=color, outline=""
            )

    def set_level(self, level: float) -> None:
        """Set volume level (0.0 to 1.0)."""
        self._level = max(0.0, min(1.0, level))
        self._redraw_volume()


class MessageDisplay(ctk.CTkFrame):
    """Display the last transcribed message."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self._label_title = ctk.CTkLabel(
            self,
            text="Last message:",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self._label_title.pack(fill="x", padx=10, pady=(10, 5))

        self._textbox = ctk.CTkTextbox(
            self,
            height=60,
            font=ctk.CTkFont(size=13),
            state="disabled",
            wrap="word"
        )
        self._textbox.pack(fill="x", padx=10, pady=(0, 10))

    def set_message(self, text: str) -> None:
        """Display a new message."""
        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.insert("1.0", f'"{text}"' if text else "")
        self._textbox.configure(state="disabled")

    def clear(self) -> None:
        """Clear the message."""
        self.set_message("")
