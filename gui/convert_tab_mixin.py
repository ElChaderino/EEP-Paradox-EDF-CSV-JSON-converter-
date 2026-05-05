"""Convert tab UI and runners shared by full Studio and lite converter windows."""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from EEG_EDF_Standalone_Tool import managed_files, tabular_edf

if TYPE_CHECKING:
    from EEG_EDF_Standalone_Tool.gui.file_manager import FileManagerWidget

_MODE_HINTS = {
    "CSV -> EDF": (
        "Load a comma-separated matrix: header row plus samples. Use a time_s "
        "column for automatic Hz, or set sampling rate below."
    ),
    "JSON -> EDF": (
        "Load a manifest JSON that points to CSV, or an embedded JSON with "
        "channel-by-sample data arrays."
    ),
    "EDF -> CSV + manifest JSON": (
        "Export the full recording as wide CSV plus a sidecar manifest JSON."
    ),
    "EDF -> embedded JSON (short clips)": (
        "Write one JSON file with embedded arrays. Best for short clips under "
        "about 500k samples."
    ),
}

_MODE_INPUT_FILTERS = {
    "CSV -> EDF": ("Select CSV", "CSV (*.csv);;All (*)"),
    "JSON -> EDF": ("Select JSON", "JSON (*.json);;All (*)"),
    "EDF -> CSV + manifest JSON": ("Select EDF", "EDF (*.edf);;All (*)"),
    "EDF -> embedded JSON (short clips)": ("Select EDF", "EDF (*.edf);;All (*)"),
}


class ConvertTabMixin:
    """Expects host QMainWindow with statusBar(), optional file_manager with refresh()."""

    conv_mode: QComboBox
    conv_hint: QLabel
    conv_input: QLineEdit
    conv_output: QLineEdit
    conv_sfreq: QDoubleSpinBox
    conv_unit: QComboBox
    conv_log: QTextEdit
    file_manager: Optional["FileManagerWidget"]

    def _build_convert_tab(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(14)
        right = QVBoxLayout()
        right.setSpacing(14)

        mode_card = QGroupBox("Direction")
        mode_lay = QVBoxLayout()
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Flow"))
        self.conv_mode = QComboBox()
        self.conv_mode.addItems(list(_MODE_HINTS.keys()))
        self.conv_mode.currentTextChanged.connect(self._update_convert_hint)
        self.conv_mode.currentTextChanged.connect(self._refresh_convert_placeholders)
        mode_row.addWidget(self.conv_mode, 1)
        mode_lay.addLayout(mode_row)

        self.conv_hint = QLabel()
        self.conv_hint.setObjectName("SectionHint")
        self.conv_hint.setWordWrap(True)
        self._update_convert_hint(self.conv_mode.currentText())
        mode_lay.addWidget(self.conv_hint)
        mode_card.setLayout(mode_lay)
        left.addWidget(mode_card)

        paths = QGroupBox("Files")
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)
        self.conv_input = QLineEdit()
        self.conv_output = QLineEdit()
        btn_in = QPushButton("Browse...")
        btn_out = QPushButton("Browse...")
        btn_in.setToolTip("Choose source file")
        btn_out.setToolTip("Choose destination file")
        btn_in.clicked.connect(self._pick_convert_input)
        btn_out.clicked.connect(self._pick_convert_output)

        grid.addWidget(QLabel("Input"), 0, 0)
        grid.addWidget(self.conv_input, 0, 1)
        grid.addWidget(btn_in, 0, 2)
        grid.addWidget(QLabel("Output"), 1, 0)
        grid.addWidget(self.conv_output, 1, 1)
        grid.addWidget(btn_out, 1, 2)
        paths.setLayout(grid)
        left.addWidget(paths)

        opt = QGroupBox("CSV and units")
        og = QGridLayout()
        og.setHorizontalSpacing(12)
        og.setVerticalSpacing(10)
        og.addWidget(QLabel("Sampling rate"), 0, 0)
        self.conv_sfreq = QDoubleSpinBox()
        self.conv_sfreq.setRange(1.0, 100000.0)
        self.conv_sfreq.setValue(256.0)
        self.conv_sfreq.setSuffix(" Hz")
        self.conv_sfreq.setToolTip(
            "Used when CSV has no time_s column. Ignored when time_s is present."
        )
        og.addWidget(self.conv_sfreq, 0, 1)
        lbl_sf = QLabel(
            "Required only when CSV columns are channels without a time_s column."
        )
        lbl_sf.setObjectName("SectionHint")
        lbl_sf.setWordWrap(True)
        og.addWidget(lbl_sf, 0, 2)
        og.addWidget(QLabel("Amplitude unit"), 1, 0)
        self.conv_unit = QComboBox()
        self.conv_unit.addItems(["uV", "V"])
        self.conv_unit.setToolTip("Values in CSV or manifest; MNE stores volts.")
        og.addWidget(self.conv_unit, 1, 1)
        opt.setLayout(og)
        left.addWidget(opt)

        run = QPushButton("Run conversion")
        run.setObjectName("PrimaryButton")
        run.setCursor(Qt.PointingHandCursor)
        run.clicked.connect(self._run_convert)
        left.addWidget(run, alignment=Qt.AlignLeft)
        left.addStretch()

        log_box = QGroupBox("Activity log")
        log_lay = QVBoxLayout()
        self.conv_log = QTextEdit()
        self.conv_log.setReadOnly(True)
        self.conv_log.setMinimumHeight(330)
        self.conv_log.setPlaceholderText("Conversion output and tracebacks appear here...")
        log_lay.addWidget(self.conv_log)
        log_box.setLayout(log_lay)
        right.addWidget(log_box, 1)

        help_box = QGroupBox("Conversion guarantees")
        help_lay = QVBoxLayout()
        for line in (
            "CSV values are interpreted as uV by default, with optional volts input.",
            "EDF export trims only a trailing fractional second; it does not resample.",
            "Manifest exports include channel names, sample rate, duration, unit, and source metadata.",
        ):
            label = QLabel(line)
            label.setObjectName("ChecklistLine")
            label.setWordWrap(True)
            help_lay.addWidget(label)
        help_box.setLayout(help_lay)
        right.addWidget(help_box)

        layout.addLayout(left, 5)
        layout.addLayout(right, 4)
        w.setLayout(layout)
        self._refresh_convert_placeholders(self.conv_mode.currentText())
        return w

    def _update_convert_hint(self, mode: str) -> None:
        self.conv_hint.setText(_MODE_HINTS.get(mode, ""))

    def _refresh_convert_placeholders(self, mode: str) -> None:
        if not hasattr(self, "conv_input"):
            return
        if mode.startswith("CSV"):
            self.conv_input.setPlaceholderText("Choose source .csv")
            self.conv_output.setPlaceholderText("Destination .edf")
        elif mode.startswith("JSON"):
            self.conv_input.setPlaceholderText("Choose manifest or embedded .json")
            self.conv_output.setPlaceholderText("Destination .edf")
        elif "embedded JSON" in mode:
            self.conv_input.setPlaceholderText("Choose source .edf")
            self.conv_output.setPlaceholderText("Destination .json")
        else:
            self.conv_input.setPlaceholderText("Choose source .edf")
            self.conv_output.setPlaceholderText("Destination .csv")

    def _pick_convert_input(self) -> None:
        mode = self.conv_mode.currentText()
        title, filter_text = _MODE_INPUT_FILTERS.get(mode, ("Select file", "All (*)"))
        path, _ = QFileDialog.getOpenFileName(self, title, "", filter_text)
        if path:
            self.conv_input.setText(path)
            if not self.conv_output.text():
                p = Path(path)
                if mode.startswith("CSV") or mode.startswith("JSON"):
                    self.conv_output.setText(
                        str(managed_files.suggested_path("conversions", p, ".edf", "converted"))
                    )
                elif "embedded JSON" in mode:
                    self.conv_output.setText(
                        str(managed_files.suggested_path("embedded_json", p, ".json", "embedded"))
                    )
                else:
                    self.conv_output.setText(
                        str(managed_files.suggested_path("csv_manifests", p, ".csv", "tabular"))
                    )
            self._status(f"Input: {path}")

    def _pick_convert_output(self) -> None:
        mode = self.conv_mode.currentText()
        if mode.endswith("EDF") or "-> EDF" in mode:
            start_dir = str(managed_files.folder_path("conversions"))
            path, _ = QFileDialog.getSaveFileName(
                self, "Save EDF as", start_dir, "EDF (*.edf);;All (*)"
            )
        elif "embedded" in mode:
            start_dir = str(managed_files.folder_path("embedded_json"))
            path, _ = QFileDialog.getSaveFileName(
                self, "Save JSON as", start_dir, "JSON (*.json);;All (*)"
            )
        else:
            start_dir = str(managed_files.folder_path("csv_manifests"))
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save CSV (manifest uses same base name)",
                start_dir,
                "CSV (*.csv);;All (*)",
            )
        if path:
            self.conv_output.setText(path)
            self._status(f"Output: {path}")

    def _run_convert(self) -> None:
        self.conv_log.clear()
        inp = self.conv_input.text().strip()
        out = self.conv_output.text().strip()
        if not inp or not out:
            QMessageBox.warning(self, "Convert", "Select input and output paths.")
            return

        mode = self.conv_mode.currentText()
        unit = self.conv_unit.currentText()
        try:
            if mode == "CSV -> EDF":
                raw = tabular_edf.csv_to_raw(inp, sfreq=self.conv_sfreq.value(), unit=unit)
                tabular_edf.export_edf(raw, out)
                self._log(self.conv_log, f"OK - wrote EDF:\n{out}")
                self._status("CSV -> EDF completed.")
                self._refresh_files_tab()

            elif mode == "JSON -> EDF":
                raw = tabular_edf.load_json_auto(Path(inp))
                tabular_edf.export_edf(raw, out)
                self._log(self.conv_log, f"OK - wrote EDF:\n{out}")
                self._status("JSON -> EDF completed.")
                self._refresh_files_tab()

            elif mode == "EDF -> CSV + manifest JSON":
                raw = tabular_edf.read_edf(inp)
                outp = Path(out)
                if outp.suffix.lower() == ".csv":
                    csv_p = outp
                    json_p = outp.with_name(outp.stem + "_manifest.json")
                else:
                    csv_p = outp.with_suffix(".csv")
                    json_p = outp.with_suffix(".json")
                tabular_edf.raw_to_csv_and_manifest(
                    raw,
                    csv_p,
                    json_p,
                    unit=unit,
                    extra_meta={"source_edf": str(Path(inp).resolve())},
                )
                self._log(self.conv_log, f"OK - CSV:\n{csv_p}\nManifest:\n{json_p}")
                self._status("EDF -> tabular export completed.")
                self._refresh_files_tab()

            elif mode == "EDF -> embedded JSON (short clips)":
                raw = tabular_edf.read_edf(inp)
                tabular_edf.raw_to_embedded_json(raw, out, unit=unit, max_samples=500_000)
                self._log(self.conv_log, f"OK - embedded JSON:\n{out}")
                self._status("EDF -> embedded JSON completed.")
                self._refresh_files_tab()

        except Exception as e:
            self._log(self.conv_log, traceback.format_exc())
            self._status("Conversion failed - see log.", 8000)
            QMessageBox.critical(self, "Convert", str(e))

    def _status(self, msg: str, ms: int = 6000) -> None:
        self.statusBar().showMessage(msg, ms)

    def _log(self, widget: QTextEdit, msg: str) -> None:
        widget.append(msg)
        widget.verticalScrollBar().setValue(widget.verticalScrollBar().maximum())

    def _refresh_files_tab(self) -> None:
        fm = getattr(self, "file_manager", None)
        if fm is not None:
            fm.refresh()
