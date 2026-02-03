"""
Test simple de l'injection clavier.
Lance ce script, puis clique dans un éditeur de texte.
Après 3 secondes, "TEST MESSAGE" sera injecté.
"""

import time
from core.injector import ChatInjector

print("Test d'injection clavier")
print("=" * 40)
print("1. Lance ce script")
print("2. Clique dans un éditeur de texte (Notepad)")
print("3. Attend 3 secondes...")
print()

time.sleep(3)

injector = ChatInjector(delay_ms=100, chat_key="enter")

# Test simple: juste Ctrl+V
print("Test: Copie + Ctrl+V...")
import pyperclip
pyperclip.copy("TEST MESSAGE")
time.sleep(0.1)
injector._press_ctrl_v()

print()
print("Si 'TEST MESSAGE' est apparu, le Ctrl+V fonctionne!")
print()
print("Test complet dans 3 secondes (Enter + message + Enter)...")
time.sleep(3)

# Test complet
success = injector.inject("Hello from injector!")
print(f"Injection: {'OK' if success else 'ECHEC'}")
