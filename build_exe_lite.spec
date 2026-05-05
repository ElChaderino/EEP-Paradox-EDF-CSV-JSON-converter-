# -*- mode: python ; coding: utf-8 -*-
# Lite build — conversions only (no modules_pyqt5 / simulator).
# From repo root with the same venv as the full build:
#   .venv_edf_build\Scripts\python -m PyInstaller EEG_EDF_Standalone_Tool/build_exe_lite.spec --noconfirm
#
# Output: dist/EEGParadox_EDF_Converter_Lite/

import importlib.util
import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

_sp = Path(os.path.abspath(SPECPATH)).resolve()
SPEC_DIR = _sp.parent if _sp.is_file() else _sp
REPO_ROOT = SPEC_DIR.parent
APP_ICO = SPEC_DIR / "assets" / "branding" / "eeg_paradox_edf_icon.ico"


def _mne_pyi_datas():
    spec = importlib.util.find_spec("mne")
    if spec is None or not spec.origin:
        return []
    pkg_root = Path(spec.origin).parent
    rows = []
    for pyi in pkg_root.rglob("*.pyi"):
        rel = pyi.relative_to(pkg_root)
        dest_dir = Path("mne") / rel.parent
        rows.append((str(pyi), str(dest_dir).replace("\\", "/")))
    return rows


bundle_datas = [
    (str(SPEC_DIR / "assets"), "EEG_EDF_Standalone_Tool/assets"),
]
bundle_datas.extend(_mne_pyi_datas())
# Same Jinja2 template assets as full build (meas_info / HTML repr paths).
bundle_datas.extend(collect_data_files("mne.html_templates"))

a = Analysis(
    [str(SPEC_DIR / "main_lite.py")],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=bundle_datas,
    hiddenimports=[
        "EEG_EDF_Standalone_Tool",
        "EEG_EDF_Standalone_Tool.resources",
        "EEG_EDF_Standalone_Tool.managed_files",
        "EEG_EDF_Standalone_Tool.tabular_edf",
        "EEG_EDF_Standalone_Tool.gui",
        "EEG_EDF_Standalone_Tool.gui.styles",
        "EEG_EDF_Standalone_Tool.gui.convert_tab_mixin",
        "EEG_EDF_Standalone_Tool.gui.main_window_lite",
        "mne",
        "mne.io",
        "mne.io.edf",
        "mne.io.edf.edf",
        "mne.export",
        "mne.export._export",
        "mne.export._edf_bdf",
        "edfio",
        "lazy_loader",
        "mne.html_templates",
        "mne.html_templates._templates",
        "jinja2",
        "markupsafe",
        "numpy",
        "scipy",
        "scipy.signal",
        "scipy.linalg",
        "PyQt5",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.sip",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PySide6",
        "PySide2",
        "torch",
        "torchvision",
        "torchaudio",
        "transformers",
        "tensorflow",
        "jax",
        "jaxlib",
        "gradio",
        "gradio_client",
        "datasets",
        "bitsandbytes",
        "accelerate",
        "timm",
        "vtkmodules",
        "vtk",
        "pygame",
        "pygame_ce",
        "tokenizers",
        "sentencepiece",
        "opencv-python",
        "cv2",
        "sklearn",
        "pytest",
        "IPython",
        "jupyter",
        "notebook",
        "sphinx",
        "modules_pyqt5",
        "EEG_EDF_Standalone_Tool.gui.main_window",
        "EEG_EDF_Standalone_Tool.gui.simulator_custom_panel",
        "EEG_EDF_Standalone_Tool.gui.trace_viewer",
        "EEG_EDF_Standalone_Tool.gui.file_manager",
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
    name="EEGParadox_EDF_Converter_Lite",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(APP_ICO) if APP_ICO.is_file() else None,
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
    name="EEGParadox_EDF_Converter_Lite",
)
