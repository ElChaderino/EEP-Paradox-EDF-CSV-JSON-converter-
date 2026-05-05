"""Resource path helpers for development and PyInstaller builds."""

from __future__ import annotations

import sys
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "EEG_EDF_Standalone_Tool" / relative_path
    return Path(__file__).resolve().parent / relative_path
