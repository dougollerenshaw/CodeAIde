# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

whisper_path = '/Users/dollerenshaw/opt/anaconda3/envs/codeaide/lib/python3.11/site-packages/whisper'

a = Analysis(
    ['../codeaide.py'],
    pathex=[],
    binaries=[],
    datas=[('../codeaide/examples.yaml', 'codeaide'),
           ('../codeaide/assets/*', 'codeaide/assets'),
           ('../models', 'models'),
           (os.path.join(whisper_path, 'assets'), 'whisper/assets')],
    hiddenimports=['whisper'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CodeAide',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

info_plist = {
    'NSHighResolutionCapable': True,
    'NSRequiresAquaSystemAppearance': False,  # For dark mode support
}

app = BUNDLE(
    exe,
    name='CodeAide.app',
    bundle_identifier='com.codeaide',
    info_plist={
        'NSMicrophoneUsageDescription': 'CodeAide needs access to your microphone for speech-to-text functionality.',
    },
    entitlements_file='build_scripts/entitlements.plist',
)
