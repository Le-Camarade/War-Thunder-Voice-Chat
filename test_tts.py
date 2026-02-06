#!/usr/bin/env python
"""
Test CLI - Test du TTS Engine (Phase 2 TTS).

Mode 1: Lit un message hardcodé pour tester le moteur vocal.
Mode 2: Lit les messages du chat War Thunder en temps réel.

Usage:
  python test_tts.py                    # Test voix avec phrase par défaut
  python test_tts.py --text "Hello!"    # Test voix avec texte custom
  python test_tts.py --live             # Lecture du chat WT en temps réel
  python test_tts.py --list-voices      # Liste les voix disponibles
"""

import argparse
import time
import logging

from core.tts_engine import TTSEngine
from core.chat_listener import ChatListener, ChatMessage


def list_voices(engine: TTSEngine) -> None:
    """Affiche les voix disponibles."""
    voices = engine.get_available_voices()
    print(f"  Voix disponibles: {len(voices)}")
    print()
    for i, v in enumerate(voices):
        print(f"  [{i}] {v.name}")
        print(f"      Lang: {v.language}")
        print(f"      ID: {v.id}")
        print()


def test_hardcoded(engine: TTSEngine, text: str) -> None:
    """Test avec un message hardcodé."""
    print(f'  Lecture: "{text}"')
    print()
    engine.speak(text)
    # Attendre que la lecture soit terminée
    time.sleep(1)
    while not engine._queue.empty():
        time.sleep(0.5)
    # Laisser le temps au dernier message de finir
    time.sleep(2)


def test_live(engine: TTSEngine, url: str, username: str, interval: int) -> None:
    """Test en temps réel avec le chat War Thunder."""
    listener = ChatListener(
        base_url=url,
        poll_interval=interval / 1000.0,
        own_username=username
    )

    def on_message(msg: ChatMessage) -> None:
        # Formater pour le TTS: "sender dit: message"
        tts_text = f"{msg.sender} dit: {msg.content}"
        print(f"  [{msg.channel}] {msg.sender}: {msg.content}")
        engine.speak(tts_text)

    # Vérifier connexion
    print("  Vérification de la connexion...")
    if listener.is_game_running():
        print("  War Thunder détecté!")
    else:
        print("  War Thunder non détecté.")
        print(f"  En attente sur {url}...")
    print()

    print("  Écoute du chat + lecture TTS en cours...")
    print("  " + "-" * 40)

    listener.set_on_new_message(on_message)
    listener.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print(f"  Messages traités: {listener.seen_count}")
        listener.stop()


def main():
    parser = argparse.ArgumentParser(description="Test du TTS Engine")
    parser.add_argument("--text", type=str,
                        default="Enemy tank spotted on the left flank. Need backup!",
                        help="Texte à lire (mode test)")
    parser.add_argument("--live", action="store_true",
                        help="Mode live: lire le chat War Thunder en temps réel")
    parser.add_argument("--list-voices", action="store_true",
                        help="Liste les voix disponibles")
    parser.add_argument("--voice", type=int, default=None,
                        help="Index de la voix à utiliser (voir --list-voices)")
    parser.add_argument("--rate", type=int, default=150,
                        help="Vitesse de lecture en mots/min (défaut: 150)")
    parser.add_argument("--url", type=str, default="http://localhost:8111",
                        help="URL War Thunder (défaut: http://localhost:8111)")
    parser.add_argument("--username", type=str, default=None,
                        help="Votre pseudo WT (pour filtrer vos messages)")
    parser.add_argument("--interval", type=int, default=500,
                        help="Intervalle de polling en ms (défaut: 500)")
    parser.add_argument("--debug", action="store_true",
                        help="Activer les logs de debug")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    print("=" * 50)
    print("  WAR THUNDER TTS - TEST CLI")
    print("=" * 50)
    print()

    # Démarrer le moteur TTS
    print("[1/2] Initialisation du moteur TTS...")
    engine = TTSEngine()
    engine.set_rate(args.rate)
    engine.start()
    print(f"      Vitesse: {args.rate} mots/min")

    # Sélectionner la voix
    if args.voice is not None:
        voices = engine.get_available_voices()
        if 0 <= args.voice < len(voices):
            engine.set_voice(voices[args.voice].id)
            print(f"      Voix: {voices[args.voice].name}")
        else:
            print(f"      Voix [{args.voice}] invalide, utilise la voix par défaut")
    else:
        voices = engine.get_available_voices()
        if voices:
            print(f"      Voix: {voices[0].name} (défaut)")

    print()

    # Mode liste des voix
    if args.list_voices:
        print("[2/2] Voix disponibles:")
        list_voices(engine)
        engine.stop()
        return

    # Mode test ou live
    print("[2/2] Lecture...")
    print()

    if args.live:
        test_live(engine, args.url, args.username, args.interval)
    else:
        test_hardcoded(engine, args.text)

    engine.stop()
    print()
    print("=" * 50)
    print("  TEST TERMINÉ")
    print("=" * 50)


if __name__ == "__main__":
    main()
