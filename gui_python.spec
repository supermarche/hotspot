# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_dynamic_libs, collect_data_files

# Collect data files and binaries for rasterio
rasterio_datas = collect_data_files('rasterio')
rasterio_binaries = collect_dynamic_libs('rasterio')

# Collect data files and binaries for pyproj
pyproj_datas = collect_data_files('pyproj')
pyproj_binaries = collect_dynamic_libs('pyproj')

# Collect hidden imports for rasterio and pyproj
rasterio_hiddenimports = collect_submodules('rasterio')
pyproj_hiddenimports = collect_submodules('pyproj')

a = Analysis(
    ['src/gui_python.py'],
    pathex=[],
    binaries=rasterio_binaries + pyproj_binaries,
    datas=rasterio_datas + pyproj_datas,
    hiddenimports=rasterio_hiddenimports + pyproj_hiddenimports,
    hookspath=[],  # Ensure this includes the path to your custom hooks if not in the default location
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
    exclude_binaries=False,  # Set to False to include binaries
    name='gui_python',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
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
    upx=True,
    upx_exclude=[],
    name='gui_python',
)
