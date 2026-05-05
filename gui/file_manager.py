"""Managed artifact browser for converter and simulator outputs."""

from __future__ import annotations

import os
from pathlib import Path

from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from EEG_EDF_Standalone_Tool import managed_files


class FileManagerWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        managed_files.ensure_managed_folders()
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        root = QVBoxLayout()
        root.setSpacing(12)

        top_box = QGroupBox("Managed workspace")
        top = QVBoxLayout()
        self.root_path = QLineEdit(str(managed_files.MANAGED_ROOT))
        self.root_path.setReadOnly(True)
        self.root_path.setToolTip("All created conversion and simulation artifacts are grouped here.")
        row = QHBoxLayout()
        row.addWidget(QLabel("Root"))
        row.addWidget(self.root_path, 1)
        open_root = QPushButton("Open folder")
        open_root.clicked.connect(lambda: self._open_path(managed_files.MANAGED_ROOT))
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)
        row.addWidget(open_root)
        row.addWidget(refresh)
        top.addLayout(row)

        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Show"))
        self.folder_filter = QComboBox()
        self.folder_filter.addItem("All folders", None)
        for folder, desc in managed_files.FOLDERS.items():
            self.folder_filter.addItem(f"{folder} - {desc}", folder)
        self.folder_filter.currentIndexChanged.connect(self.refresh)
        folder_row.addWidget(self.folder_filter, 1)
        top.addLayout(folder_row)
        top_box.setLayout(top)
        root.addWidget(top_box)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels(["Name", "Folder", "Size", "Modified"])
        self.tree.itemSelectionChanged.connect(self._selection_changed)
        self.tree.itemDoubleClicked.connect(self._open_selected)
        root.addWidget(self.tree, 1)

        action_row = QHBoxLayout()
        self.selected_path = QLineEdit()
        self.selected_path.setReadOnly(True)
        action_row.addWidget(self.selected_path, 1)
        open_item = QPushButton("Open")
        open_item.clicked.connect(self._open_selected)
        open_parent = QPushButton("Open containing folder")
        open_parent.clicked.connect(self._open_selected_parent)
        delete_item = QPushButton("Delete selected")
        delete_item.clicked.connect(self._delete_selected)
        action_row.addWidget(open_item)
        action_row.addWidget(open_parent)
        action_row.addWidget(delete_item)
        root.addLayout(action_row)

        self.setLayout(root)

    def refresh(self) -> None:
        managed_files.ensure_managed_folders()
        self.tree.clear()
        selected_folder = self.folder_filter.currentData() if hasattr(self, "folder_filter") else None
        folders = [selected_folder] if selected_folder else list(managed_files.FOLDERS)
        for folder in folders:
            folder_path = managed_files.folder_path(folder)
            parent = QTreeWidgetItem([folder_path.name, folder, "", ""])
            parent.setData(0, Qt.UserRole, str(folder_path))
            self.tree.addTopLevelItem(parent)
            for path in sorted(folder_path.iterdir(), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True):
                if path.is_dir():
                    continue
                stat = path.stat()
                item = QTreeWidgetItem(
                    [
                        path.name,
                        folder,
                        self._format_size(stat.st_size),
                        self._format_mtime(stat.st_mtime),
                    ]
                )
                item.setData(0, Qt.UserRole, str(path))
                parent.addChild(item)
            parent.setExpanded(True)
        self.tree.resizeColumnToContents(0)
        self.tree.resizeColumnToContents(1)

    @staticmethod
    def _format_size(size: int) -> str:
        value = float(size)
        for unit in ("B", "KB", "MB", "GB"):
            if value < 1024 or unit == "GB":
                return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
            value /= 1024.0
        return f"{size} B"

    @staticmethod
    def _format_mtime(mtime: float) -> str:
        from datetime import datetime

        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

    def _current_path(self) -> Path | None:
        items = self.tree.selectedItems()
        if not items:
            return None
        data = items[0].data(0, Qt.UserRole)
        return Path(data) if data else None

    def _selection_changed(self) -> None:
        path = self._current_path()
        self.selected_path.setText(str(path) if path else "")

    def _open_selected(self) -> None:
        path = self._current_path()
        if path:
            self._open_path(path)

    def _open_selected_parent(self) -> None:
        path = self._current_path()
        if path:
            self._open_path(path if path.is_dir() else path.parent)

    def _open_path(self, path: Path) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _delete_selected(self) -> None:
        path = self._current_path()
        if not path or path.is_dir():
            QMessageBox.information(self, "Files", "Select a managed file to delete.")
            return
        try:
            path.relative_to(managed_files.MANAGED_ROOT)
        except ValueError:
            QMessageBox.warning(self, "Files", "That file is outside the managed workspace.")
            return
        answer = QMessageBox.question(
            self,
            "Delete selected file",
            f"Delete this managed file?\n\n{path}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        os.remove(path)
        self.refresh()
