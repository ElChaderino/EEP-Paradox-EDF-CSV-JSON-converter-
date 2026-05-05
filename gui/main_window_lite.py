"""Converter-only main window (no simulator or viewer modules)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from EEG_EDF_Standalone_Tool import managed_files
from EEG_EDF_Standalone_Tool.gui.convert_tab_mixin import ConvertTabMixin
from EEG_EDF_Standalone_Tool.gui.styles import application_stylesheet
from EEG_EDF_Standalone_Tool.resources import resource_path

if TYPE_CHECKING:
    from EEG_EDF_Standalone_Tool.gui.file_manager import FileManagerWidget


class MainWindowLite(ConvertTabMixin, QMainWindow):
    """CSV / JSON ↔ EDF conversions only."""

    file_manager: Optional["FileManagerWidget"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        managed_files.ensure_managed_folders()
        self.file_manager = None

        self.setWindowTitle("EEG Paradox - EDF Converter (Lite)")
        icon_path = resource_path("assets/branding/eeg_paradox_edf_icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(960, 720)
        self.resize(1100, 820)
        self.setStyleSheet(application_stylesheet())

        central = QWidget()
        root = QVBoxLayout()
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(16)

        root.addWidget(self._build_header())
        tabs = QTabWidget()
        tabs.addTab(self._build_convert_tab(), "Convert")
        root.addWidget(tabs, 1)

        central.setLayout(root)
        self.setCentralWidget(central)
        self.statusBar().showMessage("Ready — CSV, JSON, and EDF conversions.", 8000)

    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("HeaderFrame")
        row = QHBoxLayout()
        row.setSpacing(14)
        row.setContentsMargins(0, 0, 0, 8)

        mark_path = resource_path("assets/branding/eeg_paradox_edf_icon.png")
        if mark_path.exists():
            mark = QLabel()
            pix = QPixmap(str(mark_path))
            mark.setPixmap(pix.scaled(58, 58, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            mark.setFixedSize(62, 62)
            row.addWidget(mark, alignment=Qt.AlignTop)

        lay = QVBoxLayout()
        lay.setSpacing(4)
        lay.setContentsMargins(0, 0, 0, 0)

        title = QLabel("EEG Paradox EDF Converter (Lite)")
        title.setObjectName("HeaderTitle")
        sub = QLabel(
            "Convert between CSV, JSON manifests, and EDF. No EEG simulator — "
            "smaller footprint for conversion workflows only."
        )
        sub.setObjectName("HeaderSubtitle")
        sub.setWordWrap(True)

        font = QFont()
        font.setPointSize(11)
        sub.setFont(font)

        lay.addWidget(title)
        lay.addWidget(sub)
        row.addLayout(lay, 1)
        frame.setLayout(row)
        return frame
