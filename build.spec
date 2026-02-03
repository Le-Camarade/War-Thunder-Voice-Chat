# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for War Thunder Voice Chat.
Build command: pyinstaller build.spec
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect whisper model data
whisper_datas = collect_data_files('whisper')

# App resources (logo, icon)
app_datas = [
    ('wt_radio_logo_minimalism.png', '.'),
    ('icon.ico', '.'),
]

# Hidden imports for all dependencies
hidden_imports = [
    'customtkinter',
    'pygame',
    'sounddevice',
    'numpy',
    'whisper',
    'pystray',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'pyperclip',
    'ctypes',
    'winreg',
]
hidden_imports += collect_submodules('whisper')
hidden_imports += collect_submodules('customtkinter')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=whisper_datas + app_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WT-VoiceChat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
