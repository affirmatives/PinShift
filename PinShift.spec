# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from config.app_info import APP_COPYRIGHT, APP_VERSION

app_icon = 'assets/PinShift.icns' if Path('assets/PinShift.icns').exists() else None
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('web', 'web'),
        ('assets', 'assets'),
        ('LICENSE', '.'),
        ('COPYRIGHT', '.'),
        ('THIRD_PARTY_NOTICES.md', '.'),
        ('build/third-party-licenses', 'third-party-licenses'),
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
    name='PinShift',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=app_icon,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PinShift',
)
app = BUNDLE(
    coll,
    name='PinShift.app',
    icon=app_icon,
    bundle_identifier='com.pinshift.app',
    version=APP_VERSION,
    info_plist={
        'CFBundleShortVersionString': APP_VERSION,
        'CFBundleVersion': APP_VERSION,
        'NSHumanReadableCopyright': APP_COPYRIGHT,
        'NSLocationWhenInUseUsageDescription': 'PinShift 需要获取当前 Mac 位置用于初始化地图中心。',
        'NSLocationUsageDescription': 'PinShift 需要获取当前 Mac 位置用于初始化地图中心。',
    },
)
