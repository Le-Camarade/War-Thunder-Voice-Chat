"""
AudioRecorder - Capture audio depuis le microphone.

Utilise sounddevice en mode callback pour capturer l'audio
au format requis par Whisper (16kHz, mono, float32).
"""

import numpy as np
import sounddevice as sd
from typing import Optional, Callable
import threading


class AudioRecorder:
    """Gestionnaire d'enregistrement audio pour la transcription vocale."""

    SAMPLE_RATE = 16000  # Requis par Whisper
    CHANNELS = 1  # Mono
    DTYPE = np.float32

    def __init__(self, device: Optional[int] = None):
        """
        Initialise le recorder.

        Args:
            device: Index du périphérique audio (None = défaut système)
        """
        self.device = device
        self._buffer: list[np.ndarray] = []
        self._stream: Optional[sd.InputStream] = None
        self._is_recording = False
        self._lock = threading.Lock()

    @staticmethod
    def list_devices() -> list[dict]:
        """Retourne la liste des périphériques d'entrée audio disponibles."""
        devices = []
        for i, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0:
                devices.append({
                    "index": i,
                    "name": dev["name"],
                    "channels": dev["max_input_channels"],
                    "sample_rate": dev["default_samplerate"]
                })
        return devices

    def _audio_callback(self, indata: np.ndarray, frames: int,
                        time_info, status) -> None:
        """Callback appelé par sounddevice pour chaque bloc audio."""
        if status:
            print(f"Audio status: {status}")
        with self._lock:
            if self._is_recording:
                self._buffer.append(indata.copy())

    def start_recording(self) -> None:
        """Démarre l'enregistrement audio."""
        if self._is_recording:
            return

        with self._lock:
            self._buffer = []
            self._is_recording = True

        self._stream = sd.InputStream(
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype=self.DTYPE,
            device=self.device,
            callback=self._audio_callback
        )
        self._stream.start()

    def stop_recording(self) -> np.ndarray:
        """
        Arrête l'enregistrement et retourne l'audio capturé.

        Returns:
            numpy array contenant l'audio (shape: (samples,), dtype: float32)
        """
        with self._lock:
            self._is_recording = False

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            if not self._buffer:
                return np.array([], dtype=self.DTYPE)
            audio = np.concatenate(self._buffer, axis=0)
            self._buffer = []

        # Flatten to 1D si nécessaire
        if audio.ndim > 1:
            audio = audio.flatten()

        return audio

    @property
    def is_recording(self) -> bool:
        """Retourne True si un enregistrement est en cours."""
        return self._is_recording

    def get_duration(self) -> float:
        """Retourne la durée actuelle de l'enregistrement en secondes."""
        with self._lock:
            if not self._buffer:
                return 0.0
            total_samples = sum(chunk.shape[0] for chunk in self._buffer)
            return total_samples / self.SAMPLE_RATE
