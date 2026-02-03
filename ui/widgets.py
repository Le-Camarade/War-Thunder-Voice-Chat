"""
Widgets personnalisés pour l'interface War Thunder Voice Chat.

Contient: StatusLED, JoystickButton, VolumeIndicator
"""

import customtkinter as ctk
from typing import Literal, Optional
import math


class StatusLED(ctk.CTkFrame):
    """
    LED de statut avec différentes couleurs selon l'état.

    États: idle (gris), recording (rouge), transcribing (orange),
           sending (bleu), sent (vert), error (rouge clignotant)
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
        "idle": "Prêt",
        "recording": "Enregistrement...",
        "transcribing": "Transcription...",
        "sending": "Envoi...",
        "sent": "Envoyé!",
        "error": "Erreur"
    }

    def __init__(self, master, size: int = 40, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._size = size
        self._state = "idle"
        self._blink_job = None

        # Canvas pour dessiner la LED
        self._canvas = ctk.CTkCanvas(
            self,
            width=size,
            height=size,
            bg=self._get_bg_color(),
            highlightthickness=0
        )
        self._canvas.pack()

        # Label de statut
        self._label = ctk.CTkLabel(
            self,
            text=self.LABELS["idle"],
            font=ctk.CTkFont(size=14)
        )
        self._label.pack(pady=(5, 0))

        self._draw_led()

    def _get_bg_color(self) -> str:
        """Retourne la couleur de fond selon le thème."""
        return "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#dbdbdb"

    def _draw_led(self) -> None:
        """Dessine la LED sur le canvas."""
        self._canvas.delete("all")

        color = self.COLORS.get(self._state, self.COLORS["idle"])
        padding = 4
        x0, y0 = padding, padding
        x1, y1 = self._size - padding, self._size - padding

        # Effet de lueur
        glow_color = self._lighten_color(color, 0.3)
        self._canvas.create_oval(
            x0 - 2, y0 - 2, x1 + 2, y1 + 2,
            fill=glow_color, outline=""
        )

        # LED principale
        self._canvas.create_oval(
            x0, y0, x1, y1,
            fill=color, outline="#333333", width=2
        )

        # Reflet
        self._canvas.create_oval(
            x0 + 6, y0 + 6, x0 + 14, y0 + 14,
            fill=self._lighten_color(color, 0.5), outline=""
        )

    def _lighten_color(self, hex_color: str, factor: float) -> str:
        """Éclaircit une couleur hexadécimale."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def set_state(self, state: str) -> None:
        """Change l'état de la LED."""
        if self._blink_job:
            self.after_cancel(self._blink_job)
            self._blink_job = None

        self._state = state
        self._label.configure(text=self.LABELS.get(state, state))
        self._draw_led()

    def get_state(self) -> str:
        """Retourne l'état actuel."""
        return self._state


class JoystickButtonSelector(ctk.CTkFrame):
    """Widget pour sélectionner un bouton de joystick."""

    def __init__(self, master, on_button_set=None, **kwargs):
        super().__init__(master, **kwargs)

        self._on_button_set = on_button_set
        self._is_listening = False
        self._current_button = -1

        # Label affichant le bouton actuel
        self._button_label = ctk.CTkLabel(
            self,
            text="Non assigné",
            width=120,
            font=ctk.CTkFont(size=13)
        )
        self._button_label.pack(side="left", padx=(0, 10))

        # Bouton pour assigner
        self._set_button = ctk.CTkButton(
            self,
            text="Assigner",
            width=80,
            command=self._start_listening
        )
        self._set_button.pack(side="left")

    def _start_listening(self) -> None:
        """Démarre l'écoute d'un bouton joystick."""
        self._is_listening = True
        self._button_label.configure(text="Appuyez...")
        self._set_button.configure(state="disabled")

    def stop_listening(self, button_id: Optional[int] = None) -> None:
        """Arrête l'écoute et définit le bouton."""
        self._is_listening = False
        self._set_button.configure(state="normal")

        if button_id is not None:
            self._current_button = button_id
            self._button_label.configure(text=f"Bouton {button_id}")
            if self._on_button_set:
                self._on_button_set(button_id)
        else:
            self._update_label()

    def _update_label(self) -> None:
        """Met à jour le label avec le bouton actuel."""
        if self._current_button >= 0:
            self._button_label.configure(text=f"Bouton {self._current_button}")
        else:
            self._button_label.configure(text="Non assigné")

    def set_button(self, button_id: int) -> None:
        """Définit le bouton sans déclencher le callback."""
        self._current_button = button_id
        self._update_label()

    def get_button(self) -> int:
        """Retourne l'ID du bouton actuel."""
        return self._current_button

    @property
    def is_listening(self) -> bool:
        return self._is_listening


class VolumeIndicator(ctk.CTkFrame):
    """Indicateur de volume audio en temps réel."""

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
        """Dessine l'indicateur de volume."""
        self._canvas.delete("all")

        # Fond
        self._canvas.create_rectangle(
            0, 0, self._width, self._height,
            fill="#1a1a1a", outline=""
        )

        # Barre de volume
        bar_width = int(self._level * self._width)
        if bar_width > 0:
            # Gradient de couleur selon le niveau
            if self._level < 0.6:
                color = "#44ff44"  # Vert
            elif self._level < 0.85:
                color = "#ffaa00"  # Orange
            else:
                color = "#ff4444"  # Rouge

            self._canvas.create_rectangle(
                0, 0, bar_width, self._height,
                fill=color, outline=""
            )

    def set_level(self, level: float) -> None:
        """Définit le niveau de volume (0.0 à 1.0)."""
        self._level = max(0.0, min(1.0, level))
        self._redraw_volume()


class MessageDisplay(ctk.CTkFrame):
    """Affiche le dernier message transcrit."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self._label_title = ctk.CTkLabel(
            self,
            text="Dernier message:",
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
        """Affiche un nouveau message."""
        self._textbox.configure(state="normal")
        self._textbox.delete("1.0", "end")
        self._textbox.insert("1.0", f'"{text}"' if text else "")
        self._textbox.configure(state="disabled")

    def clear(self) -> None:
        """Efface le message."""
        self.set_message("")
