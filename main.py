#!/usr/bin/env python3
"""
EEG Paradox — Standalone CSV/JSON ↔ EDF converter + simulator launcher.

Run (full EEG Paradox repo — monorepo layout):
  python EEG_EDF_Standalone_Tool/main.py

Run (standalone / flattened repo — main.py at project root next to gui/, tabular_edf.py):
  python main.py

Frozen builds use PyInstaller _MEIPASS (see build_exe.spec).
"""

from __future__ import annotations

import importlib.machinery
import sys
import types
from pathlib import Path


def _ensure_repo_on_path() -> Path:
    """Prepare sys.path and optional package alias for EEG_EDF_Standalone_Tool."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        root = Path(sys._MEIPASS)
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        return root

    here = Path(__file__).resolve().parent
    gui_dir = here / "gui"
    tabular = here / "tabular_edf.py"
    if not gui_dir.is_dir() or not tabular.is_file():
        repo_root = here.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        return repo_root

    # This folder is the tool package root (contains gui/, tabular_edf.py, …).
    if here.name == "EEG_EDF_Standalone_Tool":
        # Monorepo: .../<repo>/EEG_EDF_Standalone_Tool/main.py — parent must be on PYTHONPATH.
        repo_root = here.parent
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))
        return repo_root

    # Flat standalone checkout (e.g. GitHub repo root): expose this directory as package EEG_EDF_Standalone_Tool.
    pkg_name = "EEG_EDF_Standalone_Tool"
    if pkg_name not in sys.modules:
        pkg = types.ModuleType(pkg_name)
        pkg.__path__ = [str(here)]
        # ModuleSpec() cannot take submodule_search_locations on older Python; assign after create.
        spec = importlib.machinery.ModuleSpec(pkg_name, loader=None, is_package=True)
        try:
            spec.submodule_search_locations = [str(here)]
        except (AttributeError, TypeError):
            pass
        pkg.__spec__ = spec
        sys.modules[pkg_name] = pkg
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    return here


def main() -> int:
    _ensure_repo_on_path()
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QApplication

    from EEG_EDF_Standalone_Tool.gui.main_window import MainWindow
    from EEG_EDF_Standalone_Tool.resources import resource_path

    app = QApplication(sys.argv)
    app.setApplicationName("EEG Paradox EDF Tool")
    icon_path = resource_path("assets/branding/eeg_paradox_edf_icon.ico")
    png_fallback = resource_path("assets/branding/eeg_paradox_edf_icon.png")
    icon = QIcon()
    if icon_path.exists():
        icon = QIcon(str(icon_path))
    elif png_fallback.exists():
        icon = QIcon(str(png_fallback))
    if not icon.isNull():
        app.setWindowIcon(icon)
    win = MainWindow()
    if not icon.isNull():
        win.setWindowIcon(icon)
    win.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
