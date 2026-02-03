"""
App - Fenêtre principale de War Thunder Voice Chat.

Intègre tous les composants: joystick, audio, transcription, injection.
"""

import customtkinter as ctk
import threading
from typing import Optional

from .widgets import StatusLED, MessageDisplay, VolumeIndicator
from .settings_frame import SettingsFrame
from core.joystick import JoystickManager
from core.recorder import AudioRecorder
from core.transcriber import WhisperTranscriber
from core.injector import ChatInjector
from config import ConfigManager


class App(ctk.CTk):
    """Fenêtre principale de l'application."""

    def __init__(self):
        super().__init__()

        # Configuration de la fenêtre
        self.title("War Thunder Voice Chat")
        self.geometry("400x820")
        self.resizable(False, False)

        # Thème sombre
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Gestionnaire de configuration
        self._config_manager = ConfigManager()
        self._config_manager.load()

        # Composants core
        self._joystick_manager = JoystickManager()
        self._recorder = AudioRecorder()
        self._transcriber: Optional[WhisperTranscriber] = None
        self._injector = ChatInjector(
            delay_ms=self._config_manager.config.injection_delay_ms
        )

        # État
        self._is_recording = False
        self._current_state = "idle"

        # Créer l'interface
        self._create_widgets()

        # Initialiser les joysticks
        self._refresh_joysticks()

        # Charger la configuration sauvegardée
        self._load_saved_config()

        # Configurer les callbacks joystick
        self._setup_joystick_callbacks()

        # Démarrer le polling joystick
        self._joystick_manager.start()

        # Bind fermeture
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self) -> None:
        """Crée les widgets de l'interface."""

        # === Zone de statut ===
        status_frame = ctk.CTkFrame(self)
        status_frame.pack(fill="x", padx=20, pady=20)

        self._status_led = StatusLED(status_frame, size=50)
        self._status_led.pack(pady=15)

        # Indicateur de volume
        self._volume_indicator = VolumeIndicator(status_frame, width=200, height=15)
        self._volume_indicator.pack(pady=(0, 10))

        # === Paramètres ===
        self._settings_frame = SettingsFrame(
            self,
            on_joystick_change=self._on_joystick_change,
            on_button_change=self._on_button_change,
            on_mode_change=self._on_mode_change,
            on_model_change=self._on_model_change
        )
        self._settings_frame.pack(fill="x", padx=20, pady=(0, 10))
        self._settings_frame.set_refresh_callback(self._refresh_joysticks)

        # === Dernier message ===
        self._message_display = MessageDisplay(self)
        self._message_display.pack(fill="x", padx=20, pady=(0, 10))

        # === Bouton minimize ===
        self._minimize_btn = ctk.CTkButton(
            self,
            text="Réduire",
            command=self.iconify
        )
        self._minimize_btn.pack(pady=(10, 20))

    def _refresh_joysticks(self) -> None:
        """Rafraîchit la liste des joysticks."""
        joysticks = self._joystick_manager.refresh()
        names = [j.name for j in joysticks]
        self._settings_frame.update_joysticks(names)

        # Re-sélectionner le joystick sauvegardé si disponible
        saved_name = self._config_manager.config.joystick_name
        if saved_name and saved_name in names:
            self._settings_frame.set_joystick(saved_name)
            self._joystick_manager.select_joystick_by_name(saved_name)

    def _load_saved_config(self) -> None:
        """Charge la configuration sauvegardée."""
        config = self._config_manager.config

        # Joystick et bouton
        if config.joystick_name:
            self._settings_frame.set_joystick(config.joystick_name)
            self._joystick_manager.select_joystick_by_name(config.joystick_name)
        if config.button_id >= 0:
            self._settings_frame.set_button(config.button_id)
            self._joystick_manager.set_ptt_button(config.button_id)

        # Mode et modèle
        self._settings_frame.set_mode(config.mode)
        self._settings_frame.set_model(config.model)

        # Géométrie
        if config.window_geometry:
            try:
                self.geometry(config.window_geometry)
            except:
                pass

    def _setup_joystick_callbacks(self) -> None:
        """Configure les callbacks du joystick."""
        self._joystick_manager.set_on_button_down(self._on_ptt_press)
        self._joystick_manager.set_on_button_up(self._on_ptt_release)
        self._joystick_manager.set_on_any_button(self._on_any_button)

    def _on_joystick_change(self, name: str) -> None:
        """Appelé quand le joystick sélectionné change."""
        self._joystick_manager.select_joystick_by_name(name)
        self._config_manager.config.joystick_name = name
        self._config_manager.save()

    def _on_button_change(self, button_id: int) -> None:
        """Appelé quand le bouton PTT change."""
        self._joystick_manager.set_ptt_button(button_id)
        self._config_manager.config.button_id = button_id
        self._config_manager.save()

    def _on_mode_change(self, mode: str) -> None:
        """Appelé quand le mode CPU/GPU change."""
        self._config_manager.config.mode = mode
        self._config_manager.save()

        # Décharger le modèle si chargé (sera rechargé avec les nouveaux params)
        if self._transcriber:
            device = "cuda" if mode == "gpu" else "cpu"
            self._transcriber.change_settings(device=device)

    def _on_model_change(self, model: str) -> None:
        """Appelé quand le modèle Whisper change."""
        self._config_manager.config.model = model
        self._config_manager.save()

        # Mettre à jour le transcriber si chargé
        if self._transcriber:
            self._transcriber.change_settings(model_size=model)

    def _on_any_button(self, joystick_id: int, button_id: int) -> None:
        """Appelé quand n'importe quel bouton est pressé (pour l'assignation)."""
        selector = self._settings_frame.button_selector
        if selector.is_listening:
            # Utiliser after() pour mettre à jour l'UI depuis le thread principal
            self.after(0, lambda: selector.stop_listening(button_id))

    def _on_ptt_press(self, joystick_id: int, button_id: int) -> None:
        """Appelé quand le bouton PTT est pressé."""
        if self._is_recording or self._current_state != "idle":
            return

        self._is_recording = True
        self._set_state("recording")

        # Démarrer l'enregistrement
        self._recorder.start_recording()

        # Démarrer la mise à jour du volume
        self._update_volume()

    def _on_ptt_release(self, joystick_id: int, button_id: int) -> None:
        """Appelé quand le bouton PTT est relâché."""
        if not self._is_recording:
            return

        self._is_recording = False

        # Arrêter l'enregistrement et récupérer l'audio
        audio = self._recorder.stop_recording()

        # Réinitialiser l'indicateur de volume
        self._volume_indicator.set_level(0)

        if audio.size == 0:
            self._set_state("idle")
            return

        # Lancer la transcription dans un thread
        self._set_state("transcribing")
        thread = threading.Thread(
            target=self._transcribe_and_inject,
            args=(audio,),
            daemon=True
        )
        thread.start()

    def _update_volume(self) -> None:
        """Met à jour l'indicateur de volume pendant l'enregistrement."""
        if not self._is_recording:
            return

        # Calculer le niveau de volume à partir du buffer
        import numpy as np
        try:
            if self._recorder._buffer:
                # Prendre les derniers échantillons
                recent = self._recorder._buffer[-1] if self._recorder._buffer else np.array([0])
                rms = np.sqrt(np.mean(recent ** 2))
                # Normaliser (0.0 à 1.0)
                level = min(1.0, rms * 10)
                self._volume_indicator.set_level(level)
        except:
            pass

        # Continuer la mise à jour
        if self._is_recording:
            self.after(50, self._update_volume)

    def _transcribe_and_inject(self, audio) -> None:
        """Transcrit l'audio et injecte le texte (dans un thread)."""
        try:
            # Initialiser le transcriber si nécessaire
            if self._transcriber is None:
                config = self._config_manager.config
                device = "cuda" if config.mode == "gpu" else "cpu"
                self._transcriber = WhisperTranscriber(
                    model_size=config.model,
                    device=device
                )

            # Transcription
            text = self._transcriber.transcribe(audio)

            if not text:
                self.after(0, lambda: self._set_state("idle"))
                return

            # Mettre à jour l'affichage du message
            self.after(0, lambda: self._message_display.set_message(text))

            # Injection
            self.after(0, lambda: self._set_state("sending"))
            success = self._injector.inject(text)

            if success:
                self.after(0, lambda: self._set_state("sent"))
                # Retour à idle après 1.5s
                self.after(1500, lambda: self._set_state("idle"))
            else:
                self.after(0, lambda: self._set_state("error"))
                self.after(2000, lambda: self._set_state("idle"))

        except Exception as e:
            print(f"Erreur transcription/injection: {e}")
            self.after(0, lambda: self._set_state("error"))
            self.after(2000, lambda: self._set_state("idle"))

    def _set_state(self, state: str) -> None:
        """Change l'état de l'application."""
        self._current_state = state
        self._status_led.set_state(state)

    def _on_close(self) -> None:
        """Appelé lors de la fermeture de l'application."""
        # Sauvegarder la géométrie
        self._config_manager.config.window_geometry = self.geometry()
        self._config_manager.save()

        # Nettoyer les ressources
        self._joystick_manager.cleanup()
        if self._transcriber:
            self._transcriber.unload_model()

        self.destroy()
