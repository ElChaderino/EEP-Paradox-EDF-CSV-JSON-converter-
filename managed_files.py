"""Managed output folders for standalone conversion and simulation artifacts."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict


ROOT = Path(__file__).resolve().parent
MANAGED_ROOT = ROOT / "managed_outputs"

FOLDERS: Dict[str, str] = {
    "conversions": "Converted EDF and tabular exports",
    "simulations": "Generated simulated EDF recordings",
    "csv_manifests": "CSV plus manifest JSON sidecars",
    "embedded_json": "Embedded JSON recordings",
    "imports": "Optional staging area for source files",
}


def ensure_managed_folders() -> Path:
    MANAGED_ROOT.mkdir(parents=True, exist_ok=True)
    for folder in FOLDERS:
        (MANAGED_ROOT / folder).mkdir(parents=True, exist_ok=True)
    return MANAGED_ROOT


def folder_path(folder: str) -> Path:
    ensure_managed_folders()
    if folder not in FOLDERS:
        raise KeyError(f"Unknown managed folder: {folder}")
    return MANAGED_ROOT / folder


def safe_stem(source: str | Path, fallback: str = "recording") -> str:
    stem = Path(source).stem if source else fallback
    cleaned = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in stem)
    cleaned = cleaned.strip("_")
    return cleaned or fallback


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def suggested_path(folder: str, source: str | Path, suffix: str, label: str = "") -> Path:
    base = safe_stem(source)
    parts = [base]
    if label:
        parts.append(label)
    parts.append(timestamp())
    filename = "_".join(parts) + suffix
    return folder_path(folder) / filename
