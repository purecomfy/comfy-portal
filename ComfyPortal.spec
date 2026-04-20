# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\14\\comfy_portal_py\\comfy_portal.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('C:\\Users\\14\\comfy_portal_py\\assets\\comfy_portal.ico', 'assets'),
        ('C:\\Users\\14\\comfy_portal_py\\assets\\comfy_portal_icon.png', 'assets'),
        ('C:\\Users\\14\\comfy_portal_py\\assets\\telegram_brand.png', 'assets'),
        ('C:\\Users\\14\\comfy_portal_py\\assets\\settings_brand.png', 'assets'),
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
    icon=['C:\\Users\\14\\comfy_portal_py\\assets\\comfy_portal.ico'],
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
