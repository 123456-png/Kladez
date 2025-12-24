# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[('.venv', '.venv'), ('Kladez', 'Kladez'), ('Kladez/Kladez', 'Kladez/Kladez'), ('Kladez/kladez_app', 'Kladez/kladez_app'), ('Kladez/kladez_app/templates', 'Kladez/kladez_app/templates'), ('Kladez/kladez_app/migrations', 'Kladez/kladez_app/migrations')],
    hiddenimports=['Kladez.settings', 'kladez_app.apps', 'kladez_app.models', 'kladez_app.views', 'kladez_app.admin', 'django.core.management', 'django.db.backends.sqlite3', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'django.contrib.admin'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Kladez',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
