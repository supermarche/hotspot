# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# Collect data files and dynamic libraries
datas = collect_data_files('pyproj') + collect_data_files('rasterio')
binaries = collect_dynamic_libs('pyproj')

# Exclude 'libproj' from rasterio's .dylibs to prevent conflicts
rasterio_libs = collect_dynamic_libs('rasterio')
rasterio_libs = [lib for lib in rasterio_libs if 'libproj' not in lib[0]]

# Combine binaries
binaries += rasterio_libs

# Add hidden imports if necessary
hiddenimports = ['pyproj', 'rasterio']

a = Analysis(
    ['src/gui_python.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=['.'],
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
    name='gui_python',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Set UPX to False
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='gui_python',
)
app = BUNDLE(
    coll,
    name='gui_python.app',
    icon=None,
    bundle_identifier=None,
)
