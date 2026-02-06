#!/usr/bin/env python
"""
Test CLI - Test du ChatListener (Phase 1 TTS).

Écoute le chat War Thunder via localhost:8111 et affiche les messages en console.
Usage: python test_chat_listener.py [--url URL] [--interval MS] [--username NAME]
"""

import argparse
import time
import logging

from core.chat_listener import ChatListener, ChatMessage


def on_message(msg: ChatMessage) -> None:
    """Callback pour afficher les nouveaux messages."""
    channel_colors = {
        "Équipe": "\033[33m",     # Jaune
        "Team": "\033[33m",
        "Tous": "\033[37m",       # Blanc
        "All": "\033[37m",
        "Escadron": "\033[36m",   # Cyan
        "Squadron": "\033[36m",
    }
    reset = "\033[0m"
    color = channel_colors.get(msg.channel, "\033[37m")

    meta = f" {msg.metadata}" if msg.metadata else ""
    print(f"  {color}[{msg.channel}]{reset} {msg.sender}: {msg.content}{meta}")


def main():
    parser = argparse.ArgumentParser(description="Test du ChatListener TTS")
    parser.add_argument("--url", type=str, default="http://localhost:8111/",
                        help="URL du serveur War Thunder (défaut: http://localhost:8111/)")
    parser.add_argument("--interval", type=int, default=500,
                        help="Intervalle de polling en ms (défaut: 500)")
    parser.add_argument("--username", type=str, default=None,
                        help="Votre pseudo WT (pour filtrer vos messages)")
    parser.add_argument("--debug", action="store_true",
                        help="Activer les logs de debug")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    print("=" * 50)
    print("  WAR THUNDER CHAT LISTENER - TEST CLI")
    print("=" * 50)
    print()

    listener = ChatListener(
        base_url=args.url,
        poll_interval=args.interval / 1000.0,
        own_username=args.username
    )

    # Vérifier si le jeu est lancé
    print("[1/2] Vérification de la connexion...")
    if listener.is_game_running():
        print("      War Thunder détecté!")
    else:
        print("      War Thunder non détecté.")
        print(f"      En attente sur {args.url}...")
        print("      (Lancez une partie pour voir les messages)")
    print()

    # Démarrer l'écoute
    print("[2/2] Écoute du chat en cours...")
    print(f"      URL: {args.url}")
    print(f"      Intervalle: {args.interval}ms")
    if args.username:
        print(f"      Filtrage: {args.username}")
    print()
    print("  Messages:")
    print("  " + "-" * 40)

    listener.set_on_new_message(on_message)
    listener.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        print()
        print(f"  Messages vus: {listener.seen_count}")
        print()
        listener.stop()
        print("=" * 50)
        print("  TEST TERMINÉ")
        print("=" * 50)


if __name__ == "__main__":
    main()
