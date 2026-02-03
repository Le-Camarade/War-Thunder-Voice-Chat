"""
SettingsFrame - Panneau de configuration de l'application.

Contient les contrôles pour:
- Sélection du joystick
- Assignation du bouton PTT
- Mode CPU/GPU
- Sélection du modèle Whisper
"""

import customtkinter as ctk
from typing import Callable, Optional, List
from .widgets import JoystickButtonSelector


class SettingsFrame(ctk.CTkFrame):
    """Panneau de configuration."""

    def __init__(
        self,
        master,
        on_joystick_change: Optional[Callable[[str], None]] = None,
        on_button_change: Optional[Callable[[int], None]] = None,
        on_mode_change: Optional[Callable[[str], None]] = None,
        on_model_change: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)

        self._on_joystick_change = on_joystick_change
        self._on_button_change = on_button_change
        self._on_mode_change = on_mode_change
        self._on_model_change = on_model_change

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Crée les widgets du panneau."""

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
            values=["Aucun joystick détecté"],
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

        # === Bouton PTT ===
        ptt_label = ctk.CTkLabel(
            self,
            text="Push-to-talk:",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        ptt_label.grid(row=2, column=0, sticky="w", padx=10, pady=(10, 5))

        self._button_selector = JoystickButtonSelector(
            self,
            on_button_set=self._on_button_set
        )
        self._button_selector.grid(row=3, column=0, sticky="w", padx=10, pady=(0, 10))

        # === Mode CPU/GPU ===
        mode_label = ctk.CTkLabel(
            self,
            text="Mode:",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        mode_label.grid(row=4, column=0, sticky="w", padx=10, pady=(10, 5))

        self._mode_var = ctk.StringVar(value="cpu")

        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.grid(row=5, column=0, sticky="w", padx=10, pady=(0, 5))

        self._cpu_radio = ctk.CTkRadioButton(
            mode_frame,
            text="Performance (CPU)",
            variable=self._mode_var,
            value="cpu",
            command=self._on_mode_selected
        )
        self._cpu_radio.pack(anchor="w")

        self._gpu_radio = ctk.CTkRadioButton(
            mode_frame,
            text="Qualité (GPU)",
            variable=self._mode_var,
            value="gpu",
            command=self._on_mode_selected
        )
        self._gpu_radio.pack(anchor="w", pady=(5, 0))

        # === Modèle Whisper ===
        model_label = ctk.CTkLabel(
            self,
            text="Modèle:",
            font=ctk.CTkFont(size=13),
            anchor="w"
        )
        model_label.grid(row=6, column=0, sticky="w", padx=10, pady=(10, 5))

        self._model_combo = ctk.CTkComboBox(
            self,
            values=["tiny", "small", "medium"],
            width=150,
            command=self._on_model_selected
        )
        self._model_combo.set("small")
        self._model_combo.grid(row=7, column=0, sticky="w", padx=10, pady=(0, 15))

        # Configurer le grid
        self.grid_columnconfigure(0, weight=1)

    def _on_joystick_selected(self, choice: str) -> None:
        """Appelé quand un joystick est sélectionné."""
        if self._on_joystick_change and choice != "Aucun joystick détecté":
            self._on_joystick_change(choice)

    def _on_button_set(self, button_id: int) -> None:
        """Appelé quand un bouton PTT est assigné."""
        if self._on_button_change:
            self._on_button_change(button_id)

    def _on_mode_selected(self) -> None:
        """Appelé quand le mode est changé."""
        mode = self._mode_var.get()
        # Auto-sélection du modèle recommandé
        if mode == "cpu":
            self._model_combo.set("small")
        else:
            self._model_combo.set("medium")

        if self._on_mode_change:
            self._on_mode_change(mode)
        if self._on_model_change:
            self._on_model_change(self._model_combo.get())

    def _on_model_selected(self, choice: str) -> None:
        """Appelé quand le modèle est changé."""
        if self._on_model_change:
            self._on_model_change(choice)

    def _request_refresh(self) -> None:
        """Demande un rafraîchissement des joysticks."""
        if self._refresh_callback:
            self._refresh_callback()

    def set_refresh_callback(self, callback: Callable[[], None]) -> None:
        """Définit le callback pour le bouton rafraîchir."""
        self._refresh_callback = callback

    def update_joysticks(self, joystick_names: List[str]) -> None:
        """Met à jour la liste des joysticks."""
        if joystick_names:
            self._joystick_combo.configure(values=joystick_names)
            self._joystick_combo.set(joystick_names[0])
        else:
            self._joystick_combo.configure(values=["Aucun joystick détecté"])
            self._joystick_combo.set("Aucun joystick détecté")

    def set_joystick(self, name: str) -> None:
        """Sélectionne un joystick par son nom."""
        self._joystick_combo.set(name)

    def set_button(self, button_id: int) -> None:
        """Définit le bouton PTT affiché."""
        self._button_selector.set_button(button_id)

    def set_mode(self, mode: str) -> None:
        """Définit le mode (cpu/gpu)."""
        self._mode_var.set(mode)

    def set_model(self, model: str) -> None:
        """Définit le modèle Whisper."""
        self._model_combo.set(model)

    @property
    def button_selector(self) -> JoystickButtonSelector:
        """Retourne le sélecteur de bouton pour l'écoute externe."""
        return self._button_selector

    def get_settings(self) -> dict:
        """Retourne les paramètres actuels."""
        return {
            "joystick": self._joystick_combo.get(),
            "button": self._button_selector.get_button(),
            "mode": self._mode_var.get(),
            "model": self._model_combo.get()
        }
