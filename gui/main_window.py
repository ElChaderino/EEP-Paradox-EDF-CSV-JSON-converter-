"""Main window for the standalone converter and EEG simulator."""

from __future__ import annotations

import traceback
from dataclasses import replace
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from EEG_EDF_Standalone_Tool import managed_files, tabular_edf
from EEG_EDF_Standalone_Tool.gui.convert_tab_mixin import ConvertTabMixin
from EEG_EDF_Standalone_Tool.gui.file_manager import FileManagerWidget
from EEG_EDF_Standalone_Tool.gui.styles import application_stylesheet
from EEG_EDF_Standalone_Tool.gui.trace_viewer import TraceViewerWidget
from EEG_EDF_Standalone_Tool.resources import resource_path


class MainWindow(ConvertTabMixin, QMainWindow):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        try:
            from modules_pyqt5.eeg_signal_simulator import EEGSimulatorGUI

            self.sim_gui = EEGSimulatorGUI()
        except ImportError:
            self.sim_gui = None

        managed_files.ensure_managed_folders()
        self._last_signal: Optional[Dict[str, Any]] = None
        self.file_manager: Optional[FileManagerWidget] = None

        self.setWindowTitle("EEG Paradox - EDF Studio")
        icon_path = resource_path("assets/branding/eeg_paradox_edf_icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(1180, 820)
        self.resize(1280, 900)
        self.setStyleSheet(application_stylesheet())

        central = QWidget()
        root = QVBoxLayout()
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(16)

        root.addWidget(self._build_header())
        tabs = QTabWidget()
        tabs.addTab(self._build_convert_tab(), "Convert")
        tabs.addTab(TraceViewerWidget(), "Traces")
        tabs.addTab(self._build_simulate_tab(), "Simulate")
        self.file_manager = FileManagerWidget()
        tabs.addTab(self.file_manager, "Files")
        root.addWidget(tabs, 1)

        central.setLayout(root)
        self.setCentralWidget(central)
        if self.sim_gui:
            self.statusBar().showMessage("Ready — convert files or generate EEG.", 8000)
        else:
            self.statusBar().showMessage(
                "Simulator unavailable without modules_pyqt5 — Convert & Traces work; see Simulate tab.",
                12000,
            )

    def _build_simulate_unavailable_placeholder(self) -> QWidget:
        """Shown when modules_pyqt5 is not installed (flat GitHub clone)."""
        outer = QWidget()
        lay = QVBoxLayout()
        lay.setSpacing(16)
        lay.setContentsMargins(24, 24, 24, 24)
        title = QLabel("Simulate tab unavailable")
        title.setObjectName("HeaderTitle")
        body = QLabel(
            "<p>The preset &amp; custom EEG simulator lives in the <b>modules_pyqt5</b> package "
            "from the full EEG Paradox Viewer repository.</p>"
            "<p><b>Option A — full simulator:</b> Copy the <code>modules_pyqt5</code> folder "
            "into this project directory (next to <code>main.py</code>), then restart.</p>"
            "<p><b>Option B — converter only:</b> Run <code>python main_lite.py</code> "
            "(Convert tab only, smaller footprint).</p>"
            "<p><b>Monorepo:</b> Run from the parent repo so <code>modules_pyqt5</code> is on PYTHONPATH.</p>"
        )
        body.setWordWrap(True)
        body.setTextFormat(Qt.RichText)
        body.setOpenExternalLinks(False)
        lay.addWidget(title)
        lay.addWidget(body)
        lay.addStretch()
        outer.setLayout(lay)
        return outer

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

        title = QLabel("EEG Paradox EDF Studio")
        title.setObjectName("HeaderTitle")
        sub = QLabel(
            "Convert CSV, JSON, and EDF recordings; generate 19-channel simulated "
            "EEG; export EDF plus tabular sidecars."
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

    def _build_simulate_tab(self) -> QWidget:
        if self.sim_gui is None:
            return self._build_simulate_unavailable_placeholder()

        w = QWidget()
        outer = QVBoxLayout()
        outer.setSpacing(12)

        top = QHBoxLayout()
        hint = QLabel(
            "Generate from the full viewer preset catalog or build a custom signal. "
            "Use EC (eyes closed) vs EO (eyes open) to change alpha/beta balance; optional EO/EC transitions mix both within one recording."
        )
        hint.setObjectName("SectionHint")
        hint.setWordWrap(True)
        top.addWidget(hint, 1)
        outer.addLayout(top)

        main = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_lay = QVBoxLayout()
        left_lay.setContentsMargins(0, 0, 0, 0)
        sim_sub = QTabWidget()
        sim_sub.addTab(self._build_preset_subtab(), "Presets")
        sim_sub.addTab(self._build_custom_subtab(), "Custom")
        left_lay.addWidget(sim_sub, 1)
        left.setLayout(left_lay)
        main.addWidget(left)

        right = QWidget()
        right_lay = QVBoxLayout()
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(12)
        right_lay.addWidget(self._build_signal_summary_box())
        right_lay.addWidget(self._build_export_box())
        right_lay.addWidget(self._build_sim_log_box(), 1)
        right.setLayout(right_lay)
        main.addWidget(right)
        main.setSizes([780, 360])
        outer.addWidget(main, 1)

        w.setLayout(outer)
        self._set_signal_summary(None)

        # Preset sub-tab init calls _on_cat which logs to sim_log — must run after sim_log exists.
        if self.cat_list.count():
            self.cat_list.setCurrentRow(0)
            item0 = self.cat_list.item(0)
            if item0:
                self._on_cat(item0)

        return w

    def _build_signal_summary_box(self) -> QGroupBox:
        box = QGroupBox("Generated signal")
        layout = QVBoxLayout()
        self.signal_title = QLabel("No signal generated")
        self.signal_title.setObjectName("SignalTitle")
        layout.addWidget(self.signal_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        self.summary_labels: Dict[str, QLabel] = {}
        fields = (
            ("duration", "Duration"),
            ("sfreq", "Sample rate"),
            ("channels", "Channels"),
            ("samples", "Samples/ch"),
            ("rms", "Mean RMS"),
            ("features", "Active features"),
        )
        for row, (key, label) in enumerate(fields):
            grid.addWidget(QLabel(label), row, 0)
            value = QLabel("-")
            value.setObjectName("SummaryValue")
            value.setWordWrap(True)
            grid.addWidget(value, row, 1)
            self.summary_labels[key] = value
        layout.addLayout(grid)
        box.setLayout(layout)
        return box

    def _build_export_box(self) -> QGroupBox:
        export_box = QGroupBox("Save generated recording")
        er = QVBoxLayout()
        self.chk_csv = QCheckBox("CSV + manifest JSON")
        self.chk_csv.setToolTip("Recommended for long recordings and external review.")
        self.chk_embed_json = QCheckBox("Embedded JSON")
        self.chk_embed_json.setToolTip("Single JSON file; skipped if recording is too large.")
        er.addWidget(self.chk_csv)
        er.addWidget(self.chk_embed_json)

        save_e = QPushButton("Save EDF...")
        save_e.setObjectName("AccentOutline")
        save_e.setCursor(Qt.PointingHandCursor)
        save_e.clicked.connect(self._save_sim_edf)
        er.addWidget(save_e, alignment=Qt.AlignLeft)
        export_box.setLayout(er)
        return export_box

    def _build_sim_log_box(self) -> QGroupBox:
        log_box = QGroupBox("Activity log")
        log_lay = QVBoxLayout()
        self.sim_log = QTextEdit()
        self.sim_log.setReadOnly(True)
        self.sim_log.setMinimumHeight(180)
        self.sim_log.setPlaceholderText("Generation and save messages appear here...")
        log_lay.addWidget(self.sim_log)
        log_box.setLayout(log_lay)
        return log_box

    def _build_preset_subtab(self) -> QWidget:
        pw = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        splitter = QSplitter(Qt.Horizontal)

        left_container = QVBoxLayout()
        left_container.setSpacing(10)

        cat_box = QGroupBox("Categories")
        cat_lay = QVBoxLayout()
        self.cat_list = QListWidget()
        self.cat_list.setMinimumWidth(280)
        self.cat_list.setMinimumHeight(210)
        self.cat_list.itemClicked.connect(self._on_cat)
        for name, data in self.sim_gui.categories.items():
            item = QListWidgetItem(f"{name} ({len(data.get('presets', []))})")
            item.setData(Qt.UserRole, name)
            item.setToolTip(data.get("description", ""))
            self.cat_list.addItem(item)
        cat_lay.addWidget(self.cat_list)
        cat_box.setLayout(cat_lay)
        left_container.addWidget(cat_box)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search"))
        self.preset_search = QLineEdit()
        self.preset_search.setPlaceholderText("Filter presets...")
        self.preset_search.textChanged.connect(self._filter_presets)
        search_row.addWidget(self.preset_search)
        left_container.addLayout(search_row)

        preset_box = QGroupBox("Presets")
        preset_lay = QVBoxLayout()
        self.preset_list = QListWidget()
        self.preset_list.setMinimumHeight(250)
        self.preset_list.itemClicked.connect(self._on_preset_pick)
        preset_lay.addWidget(self.preset_list)
        preset_box.setLayout(preset_lay)
        left_container.addWidget(preset_box, 1)

        lw = QWidget()
        lw.setLayout(left_container)
        splitter.addWidget(lw)

        right = QVBoxLayout()
        right.setSpacing(12)

        desc_box = QGroupBox("Preset detail")
        desc_lay = QVBoxLayout()
        self.sim_description = QTextEdit()
        self.sim_description.setReadOnly(True)
        self.sim_description.setMinimumHeight(150)
        self.sim_description.setPlaceholderText("Select a preset to see its description...")
        desc_lay.addWidget(self.sim_description)
        desc_box.setLayout(desc_lay)
        right.addWidget(desc_box)

        overrides = QGroupBox("Overrides")
        og = QGridLayout()
        og.setHorizontalSpacing(16)
        og.setVerticalSpacing(10)
        self.chk_ov_dur = QCheckBox("Duration")
        self.ov_duration = QDoubleSpinBox()
        self.ov_duration.setRange(5.0, 3600.0)
        self.ov_duration.setValue(60.0)
        self.ov_duration.setSuffix(" s")
        self.chk_ov_amp = QCheckBox("Amplitude")
        self.ov_amplitude = QDoubleSpinBox()
        self.ov_amplitude.setRange(1.0, 500.0)
        self.ov_amplitude.setValue(50.0)
        self.ov_amplitude.setSuffix(" uV")
        og.addWidget(self.chk_ov_dur, 0, 0)
        og.addWidget(self.ov_duration, 0, 1)
        og.addWidget(self.chk_ov_amp, 1, 0)
        og.addWidget(self.ov_amplitude, 1, 1)
        lbl_ov = QLabel("Unchecked values keep the preset defaults.")
        lbl_ov.setObjectName("SectionHint")
        lbl_ov.setWordWrap(True)
        og.addWidget(lbl_ov, 2, 0, 1, 2)

        og.addWidget(QLabel("Eye state"), 3, 0)
        self.preset_eye_mode_combo = QComboBox()
        self.preset_eye_mode_combo.addItem("Same as preset", "preset")
        self.preset_eye_mode_combo.addItem("EC — eyes closed", "EC")
        self.preset_eye_mode_combo.addItem("EO — eyes open", "EO")
        self.preset_eye_mode_combo.setToolTip(
            "EC: stronger posterior alpha, lower beta. EO: weaker occipital alpha, relatively more beta."
        )
        og.addWidget(self.preset_eye_mode_combo, 3, 1)

        og.addWidget(QLabel("EO/EC transitions"), 4, 0)
        self.preset_transitions_combo = QComboBox()
        self.preset_transitions_combo.addItem("Same as preset", "preset")
        self.preset_transitions_combo.addItem("On — alternate segments", "on")
        self.preset_transitions_combo.addItem("Off — single state", "off")
        self.preset_transitions_combo.setToolTip(
            "When On, the generator mixes eyes-open and eyes-closed segments across the recording."
        )
        og.addWidget(self.preset_transitions_combo, 4, 1)

        eye_hint = QLabel(
            "<b>EC vs EO</b> (simulator): <b>Eyes closed</b> boosts occipital alpha and tones down beta; "
            "<b>Eyes open</b> suppresses posterior alpha and adds frontal/temporal beta emphasis. "
            "Overrides here replace the preset&apos;s stored eye state for this run only."
        )
        eye_hint.setObjectName("SectionHint")
        eye_hint.setWordWrap(True)
        eye_hint.setTextFormat(Qt.RichText)
        og.addWidget(eye_hint, 5, 0, 1, 2)
        overrides.setLayout(og)
        right.addWidget(overrides)

        gen = QPushButton("Generate from preset")
        gen.setObjectName("PrimaryButton")
        gen.setCursor(Qt.PointingHandCursor)
        gen.clicked.connect(self._generate_preset)
        right.addWidget(gen, alignment=Qt.AlignLeft)
        right.addStretch()

        rw = QWidget()
        rw.setLayout(right)
        splitter.addWidget(rw)
        splitter.setSizes([340, 560])

        layout.addWidget(splitter, 1)
        pw.setLayout(layout)

        return pw

    def _build_custom_subtab(self) -> QWidget:
        from EEG_EDF_Standalone_Tool.gui.simulator_custom_panel import SimulatorCustomPanel

        cw = QWidget()
        cv = QVBoxLayout()
        cv.setSpacing(12)
        self.custom_panel = SimulatorCustomPanel(self.sim_gui)
        cv.addWidget(self.custom_panel, 1)

        gen_c = QPushButton("Generate from custom settings")
        gen_c.setObjectName("PrimaryButton")
        gen_c.setCursor(Qt.PointingHandCursor)
        gen_c.clicked.connect(self._generate_custom)
        cv.addWidget(gen_c, alignment=Qt.AlignLeft)

        cw.setLayout(cv)
        return cw

    def _preset_name_from_item(self, item: QListWidgetItem) -> str:
        data = item.data(Qt.UserRole)
        return str(data) if data else item.text()

    def _category_name_from_item(self, item: QListWidgetItem) -> str:
        data = item.data(Qt.UserRole)
        return str(data) if data else item.text().split(" (", 1)[0]

    def _format_preset_label(self, name: str) -> str:
        preset = self.sim_gui.presets.get(name, {})
        params = preset.get("params")
        bits = [name.replace("_", " ").title()]
        if params is not None:
            bits.append(f"{getattr(params, 'duration', '?')}s")
            bits.append(f"{getattr(params, 'sample_rate', '?')}Hz")
        if preset.get("psychiatric_condition"):
            bits.append(str(preset["psychiatric_condition"]).replace("_", " "))
        return "  |  ".join(bits)

    def _on_cat(self, item: QListWidgetItem) -> None:
        if not item:
            return
        cat = self._category_name_from_item(item)
        self.preset_search.clear()
        self._populate_presets(cat)
        count = self.preset_list.count()
        log = getattr(self, "sim_log", None)
        if log is not None:
            self._log(log, f"Category '{cat}' - {count} presets.")
        self._status(f"{count} presets in '{cat}'")

    def _populate_presets(self, cat: str, query: str = "") -> None:
        self.preset_list.clear()
        q = query.strip().lower()
        for name in self.sim_gui.get_presets_in_category(cat):
            desc = self.sim_gui.get_preset_description(name)
            if q and q not in name.lower() and q not in desc.lower():
                continue
            item = QListWidgetItem(self._format_preset_label(name))
            item.setData(Qt.UserRole, name)
            item.setToolTip(desc)
            self.preset_list.addItem(item)
        if self.preset_list.count():
            self.preset_list.setCurrentRow(0)
            self._on_preset_pick(self.preset_list.item(0))

    def _filter_presets(self, text: str) -> None:
        item = self.cat_list.currentItem()
        if not item:
            return
        self._populate_presets(self._category_name_from_item(item), text)

    def _on_preset_pick(self, item: QListWidgetItem) -> None:
        if not item:
            return
        name = self._preset_name_from_item(item)
        preset = self.sim_gui.presets.get(name, {})
        params = preset.get("params")
        desc = self.sim_gui.get_preset_description(name)
        lines = [name.replace("_", " ").title(), "", desc]
        if params is not None:
            lines.extend(
                [
                    "",
                    f"Duration: {params.duration}s",
                    f"Sample rate: {params.sample_rate} Hz",
                    f"Amplitude: {params.amplitude} uV",
                    f"Noise: {params.noise_level} uV",
                ]
            )
        lines.append("")
        lines.append(f"Preset eye state: {preset.get('eye_state', 'EC')}")
        lines.append(
            f"Preset EO/EC transitions: {'yes' if preset.get('include_eye_transitions') else 'no'}"
        )
        active = [
            label
            for label, enabled in (
                ("abnormal", preset.get("include_abnormal")),
                ("artifacts", preset.get("include_artifacts")),
                ("sleep", preset.get("include_sleep")),
                ("seizure", preset.get("include_seizure")),
                ("eye transitions", preset.get("include_eye_transitions")),
            )
            if enabled
        ]
        if active:
            lines.extend(["", "Features: " + ", ".join(active)])
        self.sim_description.setPlainText("\n".join(lines))
        self._status(f"Preset: {name}")

    def _merge_preset_params(self, preset_name: str):
        preset = self.sim_gui.presets[preset_name]
        params = preset["params"]
        if self.chk_ov_dur.isChecked():
            params = replace(params, duration=float(self.ov_duration.value()))
        if self.chk_ov_amp.isChecked():
            params = replace(params, amplitude=float(self.ov_amplitude.value()))
        return preset, params

    def _generate_preset(self) -> None:
        item = self.preset_list.currentItem()
        if not item:
            QMessageBox.information(self, "Simulate", "Select a preset first.")
            return
        name = self._preset_name_from_item(item)
        try:
            preset, params = self._merge_preset_params(name)

            eye_mode = self.preset_eye_mode_combo.currentData()
            if eye_mode == "preset":
                eye_state = preset.get("eye_state", "EC")
            else:
                eye_state = eye_mode

            trans_mode = self.preset_transitions_combo.currentData()
            if trans_mode == "preset":
                include_eye_transitions = preset.get("include_eye_transitions", False)
            elif trans_mode == "on":
                include_eye_transitions = True
            else:
                include_eye_transitions = False

            signal_dict = self.sim_gui.simulator.generate_comprehensive_signal(
                params,
                include_abnormal=preset["include_abnormal"],
                include_artifacts=preset["include_artifacts"],
                include_sleep=preset["include_sleep"],
                include_seizure=preset["include_seizure"],
                psychiatric_condition=preset.get("psychiatric_condition"),
                tbi_severity=preset.get("tbi_severity"),
                medication=preset.get("medication"),
                eye_state=eye_state,
                include_eye_transitions=include_eye_transitions,
            )
            signal_dict["metadata"]["applied_eye_state"] = eye_state
            signal_dict["metadata"]["applied_eye_transitions"] = include_eye_transitions
            signal_dict["metadata"]["preset_name"] = name
            signal_dict["metadata"]["preset_description"] = preset.get("description", "")
            self._last_signal = signal_dict
            self._set_signal_summary(signal_dict)
            meta = signal_dict["metadata"]
            self._log(
                self.sim_log,
                f"Generated '{name}' - {meta.get('duration', '?')}s, "
                f"{meta.get('num_channels', '?')} ch, eyes {eye_state}"
                f"{', EO/EC transitions' if include_eye_transitions else ''}.",
            )
            self._status(f"Generated preset '{name}' - ready to save.")
        except Exception:
            self._log(self.sim_log, traceback.format_exc())
            self._status("Generation failed.", 8000)
            QMessageBox.critical(self, "Simulate", "Generation failed (see log).")

    def _generate_custom(self) -> None:
        try:
            params, gen_kw = self.custom_panel.collect()
            signal_dict = self.sim_gui.simulator.generate_comprehensive_signal(params, **gen_kw)
            md = signal_dict.setdefault("metadata", {})
            md["generation_mode"] = "custom"
            md["applied_eye_state"] = gen_kw.get("eye_state")
            md["applied_eye_transitions"] = bool(gen_kw.get("include_eye_transitions"))
            md["custom_summary"] = (
                f"duration={params.duration}s sfreq={params.sample_rate} "
                f"psych={gen_kw.get('psychiatric_condition')} "
                f"tbi={gen_kw.get('tbi_severity')} med={gen_kw.get('medication')}"
            )
            self._last_signal = signal_dict
            self._set_signal_summary(signal_dict)
            meta = signal_dict["metadata"]
            es = gen_kw.get("eye_state", "?")
            tr = bool(gen_kw.get("include_eye_transitions"))
            self._log(
                self.sim_log,
                f"Generated custom signal - {meta.get('duration', '?')}s, "
                f"{meta.get('num_channels', '?')} ch @ {meta.get('sample_rate', '?')} Hz, "
                f"eyes {es}{', EO/EC transitions' if tr else ''}.",
            )
            self._status("Custom signal ready - save as EDF when you want.")
        except Exception:
            self._log(self.sim_log, traceback.format_exc())
            self._status("Custom generation failed.", 8000)
            QMessageBox.critical(self, "Simulate", "Custom generation failed (see log).")

    def _active_feature_summary(self, metadata: Dict[str, Any]) -> str:
        features = metadata.get("features", {})
        active = []
        es = features.get("eye_state")
        if es:
            active.append(f"eyes {es}")
        if features.get("eye_transitions"):
            active.append("EO/EC transitions")
        for key in ("wickets", "random_transients", "eye_movements"):
            value = features.get(key)
            if value:
                active.append(str(key).replace("_", " "))
        if features.get("abnormal_patterns"):
            active.append("abnormal patterns")
        if features.get("artifacts"):
            active.append("artifacts")
        if metadata.get("psychiatric_condition"):
            active.append(str(metadata["psychiatric_condition"]).replace("_", " "))
        return ", ".join(active[:6]) if active else "normal rhythms"

    def _set_signal_summary(self, signal_dict: Optional[Dict[str, Any]]) -> None:
        if not signal_dict:
            self.signal_title.setText("No signal generated")
            for label in self.summary_labels.values():
                label.setText("-")
            return

        meta = signal_dict.get("metadata", {})
        raw = signal_dict.get("raw")
        data = signal_dict.get("data")
        title = meta.get("preset_name") or meta.get("generation_mode", "custom")
        self.signal_title.setText(str(title).replace("_", " ").title())
        self.summary_labels["duration"].setText(f"{meta.get('duration', '-')} s")
        self.summary_labels["sfreq"].setText(f"{meta.get('sample_rate', '-')} Hz")
        self.summary_labels["channels"].setText(str(meta.get("num_channels", "-")))
        if raw is not None:
            self.summary_labels["samples"].setText(f"{raw.n_times:,}")
        else:
            self.summary_labels["samples"].setText("-")
        if isinstance(data, np.ndarray) and data.size:
            rms = float(np.sqrt(np.mean(np.square(data))))
            self.summary_labels["rms"].setText(f"{rms:.2f} uV")
        else:
            self.summary_labels["rms"].setText("-")
        self.summary_labels["features"].setText(self._active_feature_summary(meta))

    def _save_sim_edf(self) -> None:
        if not self._last_signal:
            QMessageBox.information(self, "Simulate", "Generate a signal before saving.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save simulated recording",
            str(managed_files.suggested_path("simulations", "simulated_eeg", ".edf")),
            "EDF (*.edf);;All (*)",
        )
        if not path:
            return
        if not path.lower().endswith(".edf"):
            path += ".edf"
        try:
            ok = self.sim_gui.simulator.save_simulated_signal(self._last_signal, path)
            if ok:
                self._log(self.sim_log, f"Saved EDF:\n{path}")
                self._status(f"Saved {path}")
            else:
                raise RuntimeError("Simulator save returned False.")
            if self.chk_csv.isChecked():
                raw = self._last_signal["raw"]
                base = managed_files.safe_stem(path)
                csv_dir = managed_files.folder_path("csv_manifests")
                csv_p = csv_dir / f"{base}_tabular.csv"
                json_p = csv_dir / f"{base}_manifest.json"
                tabular_edf.raw_to_csv_and_manifest(
                    raw.copy(),
                    csv_p,
                    json_p,
                    unit=tabular_edf.UNIT_UV,
                    extra_meta=self._last_signal.get("metadata"),
                )
                self._log(self.sim_log, f"Also wrote:\n{csv_p}\n{json_p}")
            if self.chk_embed_json.isChecked():
                raw = self._last_signal["raw"]
                base = managed_files.safe_stem(path)
                emb_p = managed_files.folder_path("embedded_json") / f"{base}_embedded.json"
                try:
                    tabular_edf.raw_to_embedded_json(
                        raw.copy(),
                        emb_p,
                        unit=tabular_edf.UNIT_UV,
                        max_samples=500_000,
                    )
                    self._log(self.sim_log, f"Also wrote embedded JSON:\n{emb_p}")
                except ValueError as exc:
                    self._log(self.sim_log, f"Embedded JSON not written: {exc}")
            if self.chk_csv.isChecked() or self.chk_embed_json.isChecked():
                self._status("Saved EDF plus selected sidecar export(s).")
            self._refresh_files_tab()
        except Exception:
            self._log(self.sim_log, traceback.format_exc())
            self._status("Save failed.", 8000)
            QMessageBox.critical(self, "Simulate", "Save failed (see log).")
