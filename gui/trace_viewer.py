"""EDFbrowser-style trace viewer for EDF, CSV, and JSON recordings."""

from __future__ import annotations

import traceback
from pathlib import Path
from typing import List, Optional

import numpy as np
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from EEG_EDF_Standalone_Tool import tabular_edf


TRACE_COLORS = [
    QColor("#f2e600"),
    QColor("#00ff3b"),
    QColor("#ff2727"),
    QColor("#00d8ff"),
    QColor("#ff00ff"),
    QColor("#2768ff"),
]


class TraceCanvas(QWidget):
    positionChanged = pyqtSignal(float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(520)
        self.setMouseTracking(True)
        self.raw = None
        self.data_uv: Optional[np.ndarray] = None
        self.channel_names: List[str] = []
        self.selected_channels: List[int] = []
        self.start_s = 0.0
        self.window_s = 10.0
        self.gain_uv = 100.0
        self.vertical_scale = 1.0
        self.inverted = False
        self.show_grid = True
        self.show_zero_lines = True
        self._drag_x: Optional[int] = None
        self._drag_start_s = 0.0

    def set_recording(self, raw) -> None:
        self.raw = raw
        self.channel_names = list(raw.ch_names)
        self.data_uv = raw.get_data() * 1e6
        self.selected_channels = list(range(len(self.channel_names)))
        self.start_s = 0.0
        self.update()

    def clear(self) -> None:
        self.raw = None
        self.data_uv = None
        self.channel_names = []
        self.selected_channels = []
        self.start_s = 0.0
        self.update()

    def duration_s(self) -> float:
        if self.raw is None:
            return 0.0
        return max(0.0, float(self.raw.times[-1])) if len(self.raw.times) else 0.0

    def set_channels(self, indices: List[int]) -> None:
        self.selected_channels = indices
        self.update()

    def set_start(self, start_s: float) -> None:
        max_start = max(0.0, self.duration_s() - self.window_s)
        self.start_s = min(max(0.0, start_s), max_start)
        self.positionChanged.emit(self.start_s)
        self.update()

    def set_window(self, window_s: float) -> None:
        self.window_s = max(0.25, float(window_s))
        self.set_start(self.start_s)

    def set_gain(self, gain_uv: float) -> None:
        self.gain_uv = max(1.0, float(gain_uv))
        self.update()

    def set_vertical_scale(self, scale: float) -> None:
        self.vertical_scale = min(max(0.25, float(scale)), 2.5)
        self.update()

    def set_inverted(self, inverted: bool) -> None:
        self.inverted = inverted
        self.update()

    def fit_gain_for_view(self) -> float:
        if self.raw is None or self.data_uv is None:
            return self.gain_uv
        channels = self.selected_channels or list(range(len(self.channel_names)))
        if not channels:
            return self.gain_uv
        sfreq = float(self.raw.info["sfreq"])
        start_i = max(0, int(self.start_s * sfreq))
        end_i = min(self.data_uv.shape[1], int((self.start_s + self.window_s) * sfreq))
        if end_i <= start_i:
            return self.gain_uv
        segment = self.data_uv[np.asarray(channels), start_i:end_i]
        if segment.size == 0:
            return self.gain_uv
        robust_peak = float(np.percentile(np.abs(segment), 98.0))
        return max(5.0, robust_peak)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.fillRect(self.rect(), QColor("#3b3b3b"))

        if self.raw is None or self.data_uv is None:
            self._paint_empty(painter)
            return

        left = 58
        right = 12
        top = 18
        bottom = 34
        width = max(1, self.width() - left - right)
        height = max(1, self.height() - top - bottom)
        channels = self.selected_channels or list(range(len(self.channel_names)))
        n_ch = max(1, len(channels))
        row_h = height / n_ch

        if self.show_grid:
            self._paint_grid(painter, left, top, width, height, row_h)

        sfreq = float(self.raw.info["sfreq"])
        start_i = max(0, int(self.start_s * sfreq))
        end_i = min(self.data_uv.shape[1], int((self.start_s + self.window_s) * sfreq))
        if end_i <= start_i:
            return
        segment_len = end_i - start_i
        step = max(1, int(segment_len / max(1, width * 2)))
        sample_indices = np.arange(start_i, end_i, step)
        x = left + ((sample_indices / sfreq - self.start_s) / self.window_s) * width

        font = QFont("Consolas", 9)
        painter.setFont(font)
        label_pen = QPen(QColor("#e4e8ee"))
        zero_pen = QPen(QColor("#777777"))
        zero_pen.setWidth(1)

        for row, ch_idx in enumerate(channels):
            center = top + row_h * (row + 0.5)
            color = TRACE_COLORS[row % len(TRACE_COLORS)]
            painter.setPen(QPen(color, 1))
            polarity = -1.0 if self.inverted else 1.0
            y = center - polarity * (self.data_uv[ch_idx, sample_indices] / self.gain_uv) * (
                row_h * 0.38 * self.vertical_scale
            )
            points = []
            for px, py in zip(x, y):
                points.append((int(px), int(py)))
            for i in range(1, len(points)):
                painter.drawLine(points[i - 1][0], points[i - 1][1], points[i][0], points[i][1])

            if self.show_zero_lines:
                painter.setPen(zero_pen)
                painter.drawLine(left, int(center), left + width, int(center))
                painter.setPen(QPen(color, 1))

            painter.setPen(label_pen)
            painter.drawText(4, int(center + 4), self.channel_names[ch_idx])

        self._paint_time_ruler(painter, left, top + height, width)

    def _paint_empty(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#aab3c2")))
        painter.setFont(QFont("Segoe UI", 12))
        painter.drawText(self.rect(), Qt.AlignCenter, "Open an EDF, CSV, or JSON recording to view traces")

    def _paint_grid(self, painter: QPainter, left: int, top: int, width: int, height: int, row_h: float) -> None:
        minor = QPen(QColor("#505050"))
        major = QPen(QColor("#777777"))
        for i in range(int(self.window_s) + 1):
            x = left + int((i / self.window_s) * width)
            painter.setPen(major if i % 5 == 0 else minor)
            painter.drawLine(x, top, x, top + height)
        rows = max(1, int(height / row_h))
        painter.setPen(minor)
        for i in range(rows + 1):
            y = top + int(i * row_h)
            painter.drawLine(left, y, left + width, y)

    def _paint_time_ruler(self, painter: QPainter, left: int, y: int, width: int) -> None:
        painter.setPen(QPen(QColor("#e4e8ee")))
        painter.setFont(QFont("Consolas", 9))
        painter.drawLine(left, y, left + width, y)
        seconds = max(1, int(self.window_s))
        for i in range(seconds + 1):
            x = left + int((i / self.window_s) * width)
            painter.drawLine(x, y, x, y + 5)
            if i % 5 == 0 or seconds <= 10:
                painter.drawText(x + 3, y + 18, f"{self.start_s + i:0.1f}s")

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._drag_x = event.x()
            self._drag_start_s = self.start_s

    def mouseMoveEvent(self, event) -> None:
        if self._drag_x is None or self.raw is None:
            return
        dx = event.x() - self._drag_x
        seconds = -(dx / max(1, self.width())) * self.window_s
        self.set_start(self._drag_start_s + seconds)

    def mouseReleaseEvent(self, event) -> None:
        self._drag_x = None

    def wheelEvent(self, event) -> None:
        if self.raw is None:
            return
        delta = event.angleDelta().y()
        if event.modifiers() & Qt.ControlModifier:
            factor = 0.85 if delta > 0 else 1.15
            self.set_window(self.window_s * factor)
        else:
            step = self.window_s * (0.08 if delta < 0 else -0.08)
            self.set_start(self.start_s + step)


class TraceViewerWidget(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.raw = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick_playback)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout()
        root.setSpacing(12)

        file_box = QGroupBox("Recording")
        fg = QGridLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Open EDF, CSV, or JSON")
        btn_open = QPushButton("Open...")
        btn_open.clicked.connect(self._open_file)
        self.csv_sfreq = QDoubleSpinBox()
        self.csv_sfreq.setRange(1.0, 100000.0)
        self.csv_sfreq.setValue(256.0)
        self.csv_sfreq.setSuffix(" Hz")
        self.csv_sfreq.setToolTip("Used only when a CSV has no time_s column.")
        fg.addWidget(QLabel("File"), 0, 0)
        fg.addWidget(self.path_edit, 0, 1)
        fg.addWidget(btn_open, 0, 2)
        fg.addWidget(QLabel("CSV fallback Hz"), 1, 0)
        fg.addWidget(self.csv_sfreq, 1, 1)
        file_box.setLayout(fg)

        control_box = QGroupBox("View")
        cg = QGridLayout()
        self.window_spin = QDoubleSpinBox()
        self.window_spin.setRange(0.5, 120.0)
        self.window_spin.setValue(10.0)
        self.window_spin.setSuffix(" s")
        self.window_spin.valueChanged.connect(self._set_window)
        self.gain_spin = QDoubleSpinBox()
        self.gain_spin.setRange(5.0, 1000.0)
        self.gain_spin.setValue(100.0)
        self.gain_spin.setSuffix(" uV/div")
        self.gain_spin.valueChanged.connect(self._set_gain)
        self.amp_preset_combo = QComboBox()
        self.amp_preset_combo.addItem("Preset...", None)
        for gain in (50000, 20000, 10000, 5000, 2000, 1000, 500, 200, 100, 50, 20, 10, 5):
            self.amp_preset_combo.addItem(str(gain), float(gain))
        for gain in (2, 1, 0.5, 0.2, 0.1):
            self.amp_preset_combo.addItem(str(gain), float(gain))
        self.amp_preset_combo.currentIndexChanged.connect(self._apply_gain_preset)
        amp_x2 = QPushButton("x2")
        amp_half = QPushButton("/2")
        amp_fit = QPushButton("Fit")
        amp_x2.setToolTip("Double trace amplitude")
        amp_half.setToolTip("Halve trace amplitude")
        amp_fit.setToolTip("Fit visible traces to the pane")
        amp_x2.clicked.connect(lambda: self._scale_amplitude(2.0))
        amp_half.clicked.connect(lambda: self._scale_amplitude(0.5))
        amp_fit.clicked.connect(self._fit_amplitude)
        self.timescale_combo = QComboBox()
        self.timescale_combo.addItem("Preset...", None)
        for seconds in (0.5, 1, 2, 5, 10, 15, 20, 30, 60, 120):
            label = f"{seconds:g} s"
            self.timescale_combo.addItem(label, float(seconds))
        self.timescale_combo.currentIndexChanged.connect(self._apply_timescale_preset)
        self.spacing_spin = QDoubleSpinBox()
        self.spacing_spin.setRange(0.25, 2.5)
        self.spacing_spin.setSingleStep(0.05)
        self.spacing_spin.setValue(1.0)
        self.spacing_spin.setToolTip("Vertical deflection scale inside each channel row.")
        self.spacing_spin.valueChanged.connect(self._set_vertical_scale)
        self.speed_combo = QComboBox()
        for label, speed in (("0.25x", 0.25), ("0.5x", 0.5), ("1x", 1.0), ("2x", 2.0), ("4x", 4.0)):
            self.speed_combo.addItem(label, speed)
        self.speed_combo.setCurrentIndex(2)
        self.grid_check = QCheckBox("Grid")
        self.grid_check.setChecked(True)
        self.grid_check.toggled.connect(self._toggle_grid)
        self.zero_check = QCheckBox("Zero lines")
        self.zero_check.setChecked(True)
        self.zero_check.toggled.connect(self._toggle_zero_lines)
        self.invert_check = QCheckBox("Invert")
        self.invert_check.setToolTip("Flip trace polarity.")
        self.invert_check.toggled.connect(self._toggle_invert)
        cg.addWidget(QLabel("Timescale"), 0, 0)
        cg.addWidget(self.window_spin, 0, 1)
        cg.addWidget(self.timescale_combo, 0, 2)
        cg.addWidget(QLabel("Amplitude"), 1, 0)
        cg.addWidget(self.gain_spin, 1, 1)
        cg.addWidget(self.amp_preset_combo, 1, 2)
        amp_buttons = QHBoxLayout()
        amp_buttons.setSpacing(6)
        amp_buttons.addWidget(amp_x2)
        amp_buttons.addWidget(amp_half)
        amp_buttons.addWidget(amp_fit)
        cg.addLayout(amp_buttons, 1, 3)
        cg.addWidget(QLabel("Trace scale"), 2, 0)
        cg.addWidget(self.spacing_spin, 2, 1)
        cg.addWidget(QLabel("Playback"), 2, 2)
        cg.addWidget(self.speed_combo, 2, 3)
        cg.addWidget(self.grid_check, 3, 0)
        cg.addWidget(self.zero_check, 3, 1)
        cg.addWidget(self.invert_check, 3, 2)
        control_box.setLayout(cg)

        top = QHBoxLayout()
        top.addWidget(file_box, 3)
        top.addWidget(control_box, 2)
        root.addLayout(top)

        mid = QHBoxLayout()
        self.canvas = TraceCanvas()
        self.canvas.positionChanged.connect(self._sync_position_controls)
        mid.addWidget(self.canvas, 1)

        side = QVBoxLayout()
        channel_box = QGroupBox("Channels")
        ch_lay = QVBoxLayout()
        ch_btns = QHBoxLayout()
        btn_all = QPushButton("All")
        btn_none = QPushButton("None")
        btn_all.clicked.connect(lambda: self._set_all_channels(True))
        btn_none.clicked.connect(lambda: self._set_all_channels(False))
        ch_btns.addWidget(btn_all)
        ch_btns.addWidget(btn_none)
        self.channel_list = QListWidget()
        self.channel_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.channel_list.itemChanged.connect(self._channels_changed)
        ch_lay.addLayout(ch_btns)
        ch_lay.addWidget(self.channel_list, 1)
        channel_box.setLayout(ch_lay)
        side.addWidget(channel_box, 3)

        anno_box = QGroupBox("Annotations")
        anno_lay = QVBoxLayout()
        self.annotation_log = QTextEdit()
        self.annotation_log.setReadOnly(True)
        self.annotation_log.setPlaceholderText("EDF annotations appear here...")
        anno_lay.addWidget(self.annotation_log)
        anno_box.setLayout(anno_lay)
        side.addWidget(anno_box, 2)
        mid.addLayout(side, 0)
        root.addLayout(mid, 1)

        transport = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self._toggle_playback)
        back = QPushButton("< 1s")
        back.clicked.connect(lambda: self._nudge(-1.0))
        fwd = QPushButton("1s >")
        fwd.clicked.connect(lambda: self._nudge(1.0))
        self.time_label = QLabel("0.000 s / 0.000 s")
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setRange(0, 1000)
        self.time_slider.sliderMoved.connect(self._slider_moved)
        transport.addWidget(self.play_btn)
        transport.addWidget(back)
        transport.addWidget(fwd)
        transport.addWidget(self.time_slider, 1)
        transport.addWidget(self.time_label)
        root.addLayout(transport)

        self.setLayout(root)

    def _open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open recording",
            "",
            "EEG recordings (*.edf *.csv *.json);;EDF (*.edf);;CSV (*.csv);;JSON (*.json);;All (*)",
        )
        if path:
            self.load_path(path)

    def load_path(self, path: str) -> None:
        try:
            p = Path(path)
            suffix = p.suffix.lower()
            if suffix == ".edf":
                raw = tabular_edf.read_edf(p)
            elif suffix == ".csv":
                raw = tabular_edf.csv_to_raw(p, sfreq=self.csv_sfreq.value(), unit=tabular_edf.UNIT_UV)
            elif suffix == ".json":
                raw = tabular_edf.load_json_auto(p)
            else:
                raise ValueError(f"Unsupported recording format: {suffix}")

            self.raw = raw
            self.path_edit.setText(str(p))
            self.canvas.set_recording(raw)
            self._populate_channels()
            self._populate_annotations()
            self._sync_position_controls(0.0)
        except Exception as exc:
            self.annotation_log.setPlainText(traceback.format_exc())
            QMessageBox.critical(self, "Open recording", str(exc))

    def _populate_channels(self) -> None:
        self.channel_list.blockSignals(True)
        self.channel_list.clear()
        if self.raw is None:
            self.channel_list.blockSignals(False)
            return
        for name in self.raw.ch_names:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            self.channel_list.addItem(item)
        self.channel_list.blockSignals(False)
        self._channels_changed()

    def _populate_annotations(self) -> None:
        self.annotation_log.clear()
        if self.raw is None:
            return
        annotations = getattr(self.raw, "annotations", None)
        if annotations is None or len(annotations) == 0:
            self.annotation_log.setPlainText("No annotations found.")
            return
        lines = []
        for onset, duration, desc in zip(annotations.onset, annotations.duration, annotations.description):
            lines.append(f"{float(onset):9.3f}s  +{float(duration):7.3f}s  {desc}")
        self.annotation_log.setPlainText("\n".join(lines))

    def _channels_changed(self) -> None:
        indices = []
        for i in range(self.channel_list.count()):
            if self.channel_list.item(i).checkState() == Qt.Checked:
                indices.append(i)
        self.canvas.set_channels(indices)

    def _set_all_channels(self, checked: bool) -> None:
        self.channel_list.blockSignals(True)
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.channel_list.count()):
            self.channel_list.item(i).setCheckState(state)
        self.channel_list.blockSignals(False)
        self._channels_changed()

    def _set_window(self, value: float) -> None:
        self.canvas.set_window(value)
        self._sync_position_controls(self.canvas.start_s)

    def _set_gain(self, value: float) -> None:
        self.canvas.set_gain(value)

    def _apply_gain_preset(self, index: int) -> None:
        value = self.amp_preset_combo.itemData(index)
        if value is None:
            return
        self.gain_spin.setValue(float(value))
        self.amp_preset_combo.blockSignals(True)
        self.amp_preset_combo.setCurrentIndex(0)
        self.amp_preset_combo.blockSignals(False)

    def _scale_amplitude(self, factor: float) -> None:
        # Smaller uV/div means larger visible amplitude.
        self.gain_spin.setValue(max(self.gain_spin.minimum(), min(self.gain_spin.maximum(), self.gain_spin.value() / factor)))

    def _fit_amplitude(self) -> None:
        self.gain_spin.setValue(max(self.gain_spin.minimum(), min(self.gain_spin.maximum(), self.canvas.fit_gain_for_view())))

    def _apply_timescale_preset(self, index: int) -> None:
        value = self.timescale_combo.itemData(index)
        if value is None:
            return
        self.window_spin.setValue(float(value))
        self.timescale_combo.blockSignals(True)
        self.timescale_combo.setCurrentIndex(0)
        self.timescale_combo.blockSignals(False)

    def _set_vertical_scale(self, value: float) -> None:
        self.canvas.set_vertical_scale(value)

    def _toggle_grid(self, checked: bool) -> None:
        self.canvas.show_grid = checked
        self.canvas.update()

    def _toggle_zero_lines(self, checked: bool) -> None:
        self.canvas.show_zero_lines = checked
        self.canvas.update()

    def _toggle_invert(self, checked: bool) -> None:
        self.canvas.set_inverted(checked)

    def _toggle_playback(self) -> None:
        if self.raw is None:
            QMessageBox.information(self, "Playback", "Open a recording first.")
            return
        if self.timer.isActive():
            self.timer.stop()
            self.play_btn.setText("Play")
        else:
            self.timer.start(80)
            self.play_btn.setText("Pause")

    def _tick_playback(self) -> None:
        speed = float(self.speed_combo.currentData() or 1.0)
        next_start = self.canvas.start_s + 0.08 * speed
        if next_start >= max(0.0, self.canvas.duration_s() - self.canvas.window_s):
            self.timer.stop()
            self.play_btn.setText("Play")
        self.canvas.set_start(next_start)

    def _nudge(self, seconds: float) -> None:
        self.canvas.set_start(self.canvas.start_s + seconds)

    def _slider_moved(self, value: int) -> None:
        if self.raw is None:
            return
        max_start = max(0.0, self.canvas.duration_s() - self.canvas.window_s)
        self.canvas.set_start((value / 1000.0) * max_start)

    def _sync_position_controls(self, start_s: float) -> None:
        dur = self.canvas.duration_s()
        max_start = max(0.0, dur - self.canvas.window_s)
        slider_value = int((start_s / max_start) * 1000) if max_start else 0
        self.time_slider.blockSignals(True)
        self.time_slider.setValue(max(0, min(1000, slider_value)))
        self.time_slider.blockSignals(False)
        self.time_label.setText(f"{start_s:0.3f} s / {dur:0.3f} s")
