# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

a = Analysis(
    ['main.py'],
    pathex=[],
    workpath='build',
    distpath='dist',
    binaries=[
        # Update this path to your FFmpeg installation directory
        ('C:\\Program Files\\FFmpeg\\ffmpeg-n7.1-latest-win64-lgpl-shared-7.1\\bin', 'ffmpeg/bin'),
    ],
    datas=[
        ('ui', 'ui'),
        ('core', 'core'),
        ('templates', 'templates'),
        ('splash.png', '.'),
        ('icon.ico', '.'),
        ('venv/Lib/site-packages/torchcodec-0.7.0.dist-info', 'torchcodec-0.7.0.dist-info'),
    ] + collect_data_files('whisperx') + collect_data_files('transformers') + collect_data_files('torchcodec') + collect_data_files('pyannote'),
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'torch',
        'torch._C',
        'torch.utils.cpp_extension',
        'torchvision',
        'torchaudio',
        'torchcodec',
        'whisperx',
        'whisperx.asr',
        'whisperx.diarize',
        'whisperx.alignment',
        'transformers',
        'transformers.models',
        'faster_whisper',
        'ctranslate2',
        'librosa',
        'soundfile',
        'numpy',
        'scipy',
        'pydub',
        'ffmpeg',
        'pyannote.audio.models.segmentation',
    ] + collect_submodules('torch') + collect_submodules('whisperx') + collect_submodules('transformers') + collect_submodules('ctranslate2') + collect_submodules('pyannote'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name='SubtitleGen.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='SubtitleGen'
)
