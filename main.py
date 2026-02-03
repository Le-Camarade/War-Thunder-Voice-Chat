#!/usr/bin/env python
"""
War Thunder Voice Chat - Point d'entrée principal.

Application permettant d'envoyer des messages vocaux dans le chat
de War Thunder via push-to-talk sur joystick.
"""

import sys


def main():
    """Point d'entrée principal de l'application."""
    # Vérifier les arguments CLI
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        # Mode CLI pour les tests
        print("War Thunder Voice Chat - Mode CLI")
        print("Utilisez: python test_cli.py --help")
        return

    # Lancer l'interface graphique
    from ui.app import App
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
