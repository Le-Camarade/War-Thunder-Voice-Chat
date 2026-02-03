#!/usr/bin/env python
"""
Test CLI - Test du flux complet sans interface graphique.

Enregistre 5 secondes d'audio, transcrit avec Whisper, puis injecte dans le chat.
Usage: python test_cli.py [--no-inject] [--duration SECONDS]
"""

import argparse
import time
import sys

from core.recorder import AudioRecorder
from core.transcriber import WhisperTranscriber
from core.injector import ChatInjector


def countdown(seconds: int, message: str = "Début dans") -> None:
    """Affiche un compte à rebours."""
    for i in range(seconds, 0, -1):
        print(f"\r{message} {i}...", end="", flush=True)
        time.sleep(1)
    print("\r" + " " * 30 + "\r", end="")


def main():
    parser = argparse.ArgumentParser(description="Test du flux vocal complet")
    parser.add_argument("--no-inject", action="store_true",
                        help="Ne pas injecter dans le chat (test seulement)")
    parser.add_argument("--duration", type=float, default=5.0,
                        help="Durée d'enregistrement en secondes (défaut: 5)")
    parser.add_argument("--device", type=str, default="cpu",
                        help="Device pour Whisper: cpu ou cuda (défaut: cpu)")
    parser.add_argument("--model", type=str, default="small",
                        help="Modèle Whisper: tiny, small, medium (défaut: small)")
    parser.add_argument("--list-devices", action="store_true",
                        help="Liste les périphériques audio disponibles")
    args = parser.parse_args()

    # Lister les devices audio si demandé
    if args.list_devices:
        print("\nPériphériques audio disponibles:")
        print("-" * 40)
        for dev in AudioRecorder.list_devices():
            print(f"  [{dev['index']}] {dev['name']}")
        print()
        return

    print("=" * 50)
    print("  WAR THUNDER VOICE CHAT - TEST CLI")
    print("=" * 50)
    print()

    # 1. Initialisation
    print("[1/4] Initialisation...")
    recorder = AudioRecorder()
    transcriber = WhisperTranscriber(
        model_size=args.model,
        device=args.device
    )
    injector = ChatInjector()

    print(f"      Mode: {args.device.upper()}")
    print(f"      Modèle: {args.model}")
    print(f"      Durée: {args.duration}s")
    print()

    # 2. Enregistrement
    print("[2/4] Enregistrement audio")
    countdown(3, "Parlez dans")

    print(">>> ENREGISTREMENT EN COURS <<<")
    recorder.start_recording()

    # Afficher la progression
    start_time = time.time()
    while time.time() - start_time < args.duration:
        elapsed = time.time() - start_time
        bar_length = int((elapsed / args.duration) * 20)
        bar = "█" * bar_length + "░" * (20 - bar_length)
        print(f"\r    [{bar}] {elapsed:.1f}s / {args.duration}s", end="", flush=True)
        time.sleep(0.1)

    audio = recorder.stop_recording()
    print(f"\n      Audio capturé: {len(audio)} échantillons ({len(audio)/16000:.2f}s)")
    print()

    # 3. Transcription
    print("[3/4] Transcription en cours...")
    start = time.time()
    text = transcriber.transcribe(audio)
    elapsed = time.time() - start

    print(f"      Temps: {elapsed:.2f}s")
    print()
    print(f'      Résultat: "{text}"')
    print()

    # 4. Injection
    if args.no_inject:
        print("[4/4] Injection désactivée (--no-inject)")
    else:
        print("[4/4] Injection dans le chat")
        if text:
            countdown(3, "Injection dans")
            print(">>> INJECTION <<<")
            success = injector.inject(text)
            if success:
                print("      Message envoyé!")
            else:
                print("      Échec de l'injection")
        else:
            print("      Aucun texte à injecter (transcription vide)")

    print()
    print("=" * 50)
    print("  TEST TERMINÉ")
    print("=" * 50)


if __name__ == "__main__":
    main()
