"""
WhisperTranscriber - Transcription vocale avec OpenAI Whisper.

Wrapper autour de whisper avec support CPU et GPU.
Le modèle est chargé de manière lazy au premier appel de transcription.
"""

import numpy as np
from typing import Optional, Literal
import whisper
import torch


class WhisperTranscriber:
    """Transcripteur vocal utilisant OpenAI Whisper."""

    def __init__(
        self,
        model_size: Literal["tiny", "small", "medium"] = "small",
        device: Literal["cpu", "cuda"] = "cpu",
        compute_type: Optional[str] = None
    ):
        """
        Initialise le transcripteur.

        Args:
            model_size: Taille du modèle ("tiny", "small", "medium")
            device: "cpu" ou "cuda"
            compute_type: Ignoré (compatibilité avec l'ancienne API)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type  # Gardé pour compatibilité

        self._model = None

    def _ensure_model_loaded(self) -> None:
        """Charge le modèle si pas encore fait (lazy loading)."""
        if self._model is None:
            print(f"Chargement du modèle Whisper {self.model_size} ({self.device})...")
            self._model = whisper.load_model(self.model_size, device=self.device)
            print("Modèle chargé.")

    def transcribe(self, audio: np.ndarray) -> str:
        """
        Transcrit l'audio en texte anglais.

        Args:
            audio: numpy array float32, sample rate 16kHz, mono

        Returns:
            Texte transcrit
        """
        if audio.size == 0:
            return ""

        self._ensure_model_loaded()

        # Convertir en float32 si nécessaire
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        # Transcription
        result = self._model.transcribe(
            audio,
            language="en",
            fp16=(self.device == "cuda")
        )

        return result["text"].strip()

    def unload_model(self) -> None:
        """Décharge le modèle de la mémoire."""
        if self._model is not None:
            del self._model
            self._model = None
            torch.cuda.empty_cache() if torch.cuda.is_available() else None
            print("Modèle Whisper déchargé.")

    @property
    def is_loaded(self) -> bool:
        """Retourne True si le modèle est chargé."""
        return self._model is not None

    def change_settings(
        self,
        model_size: Optional[str] = None,
        device: Optional[str] = None,
        compute_type: Optional[str] = None
    ) -> None:
        """
        Change les paramètres et décharge le modèle.
        Le modèle sera rechargé avec les nouveaux paramètres au prochain appel.
        """
        if model_size is not None:
            self.model_size = model_size
        if device is not None:
            self.device = device

        self.unload_model()
