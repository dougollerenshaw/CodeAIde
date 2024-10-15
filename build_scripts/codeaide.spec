# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_data_files

# Add the path to your conda environment's site-packages
sys.path.append('/Users/dollerenshaw/opt/anaconda3/envs/codeaide_arm64_new/lib/python3.11/site-packages')

import whisper

block_cipher = None

whisper_path = os.path.dirname(whisper.__file__)
whisper_assets = os.path.join(whisper_path, 'assets')

# Determine the path to your project root
project_root = os.path.abspath(os.path.join(SPECPATH, '..'))

# Collect data files
datas = [
    (os.path.join(project_root, 'codeaide', 'examples.yaml'), 'codeaide'),
    (os.path.join(project_root, 'codeaide', 'assets'), 'codeaide/assets'),
    (whisper_assets, 'whisper/assets'),
]

# Add assets directory
assets_dir = os.path.join(project_root, 'codeaide', 'assets')
for root, dirs, files in os.walk(assets_dir):
    for file in files:
        file_path = os.path.join(root, file)
        relative_path = os.path.relpath(root, project_root)
        datas.append((file_path, relative_path))

a = Analysis(
    ['../codeaide/__main__.py'],
    pathex=[],
    binaries=[],
    datas=datas + collect_data_files('whisper'),
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'anthropic',
        'google.generativeai',
        'decouple',
        'numpy',
        'keyring',
        'openai',
        'hjson',
        'yaml',
        'pygments',
        'sounddevice',
        'scipy',
        'openai-whisper',
        'whisper',
        'whisper.tokenizer',
        'whisper.audio',
        'whisper.model',
        'whisper.transcribe',
    ],
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
    [],
    exclude_binaries=True,
    name='CodeAide',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
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
    name='CodeAide',
)

app = BUNDLE(
    coll,
    name='CodeAide.app',
    icon=None,
    bundle_identifier=None,
)
