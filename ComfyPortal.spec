# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path


ROOT = Path(r"C:\Users\14\ComfyPortalRepo")
ASSETS = ROOT / "assets"


a = Analysis(
    [str(ROOT / "comfy_portal.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ASSETS / "comfy_portal.ico"), "assets"),
        (str(ASSETS / "comfy_portal_icon.png"), "assets"),
        (str(ASSETS / "telegram_brand.png"), "assets"),
        (str(ASSETS / "settings_brand.png"), "assets"),
        (str(ASSETS / "github_brand_light.png"), "assets"),
        (str(ASSETS / "github_brand_dark.png"), "assets"),
    ],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='ComfyPortal',
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
    icon=[str(ASSETS / "comfy_portal.ico")],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ComfyPortal',
)
