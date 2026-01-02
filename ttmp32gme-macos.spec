# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building ttmp32gme macOS standalone executable.

This creates a single executable bundle with all dependencies including:
- Python runtime
- Flask web server
- tttool binary
- ffmpeg binary
- All templates, assets, and configuration files
"""

import os
import sys
from pathlib import Path

block_cipher = None

# Get the project root directory
project_root = Path(SPECPATH)
src_dir = project_root / 'src' / 'ttmp32gme'
templates_dir = project_root / 'src' / 'templates'
assets_dir = project_root / 'src' / 'assets'
lib_dir = project_root / 'lib'

# Collect all data files
datas = [
    # Templates (relative to ttmp32gme module)
    (str(templates_dir), 'templates'),
    # Assets (CSS, JS, images) - relative to ttmp32gme module
    (str(assets_dir), 'assets'),
    # OID cache (pre-generated OID images)
    (str(project_root / 'src' / 'oid_cache'), 'oid_cache'),
    # Config database
    (str(src_dir / 'config.sqlite'), 'ttmp32gme'),
    # Top-level HTML files (served from parent directory of ttmp32gme module)
    (str(project_root / 'src' / 'library.html'), '.'),
    (str(project_root / 'src' / 'help.html'), '.'),
    (str(project_root / 'src' / 'config.html'), '.'),
    (str(project_root / 'src' / 'upload.html'), '.'),
]

# Collect bundled binaries for macOS
binaries = []
if (lib_dir / 'mac').exists():
    mac_lib = lib_dir / 'mac'
    for exe in ['tttool', 'ffmpeg']:
        exe_path = mac_lib / exe
        if exe_path.exists():
            binaries.append((str(exe_path), 'lib/mac'))

    # Include required dylibs
    for lib_file in mac_lib.glob('*.dylib'):
        binaries.append((str(lib_file), 'lib/mac'))

# Hidden imports that PyInstaller might miss
hiddenimports = [
    'ttmp32gme',
    'ttmp32gme.ttmp32gme',
    'ttmp32gme.build',
    'ttmp32gme.build.file_handler',
    'ttmp32gme.db_handler',
    'ttmp32gme.tttool_handler',
    'ttmp32gme.print_handler',
    'flask',
    'werkzeug',
    'jinja2',
    'mutagen',
    'PIL',
    'pydantic',
    'packaging',
]

a = Analysis(
    ['src/ttmp32gme/ttmp32gme.py'],
    pathex=[str(project_root / 'src')],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'test',
        'tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ttmp32gme',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console for now to see output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ttmp32gme',
)

# Create macOS .app bundle
app = BUNDLE(
    coll,
    name='ttmp32gme.app',
    icon=None,  # TODO: Create a .icns file for macOS icon
    bundle_identifier='org.korten.ttmp32gme',
    info_plist={
        'CFBundleName': 'ttmp32gme',
        'CFBundleDisplayName': 'TipToi MP3 GME Converter',
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleVersion': '2.0.0',
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.13',
        'NSHumanReadableCopyright': '© 2025 Till Korten',
    },
)
