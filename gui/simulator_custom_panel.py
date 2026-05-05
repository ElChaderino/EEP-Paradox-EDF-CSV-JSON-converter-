"""
Full custom EEG simulator controls (parity with viewer Custom tab + preset-only clinical options).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from modules_pyqt5.eeg_signal_simulator import EEGSimulatorGUI


def _combo_add_none(combo: QComboBox, none_label: str = "None") -> None:
    combo.clear()
    combo.addItem(none_label, None)


class SimulatorCustomPanel(QWidget):
    """Mirrors viewer EEGSimulatorDialog Custom tab + psychiatric / TBI / medication."""

    def __init__(self, sim_gui: EEGSimulatorGUI, parent=None) -> None:
        super().__init__(parent)
        self.sim_gui = sim_gui
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout()
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content = QWidget()
        grid = QGridLayout()
        grid.setSpacing(12)

        # --- Row 0: core signal ---
        params_group = QGroupBox("Signal parameters")
        pl = QGridLayout()
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(5.0, 3600.0)
        self.duration_spin.setValue(60.0)
        self.duration_spin.setSuffix(" s")

        self.sample_rate_spin = QSpinBox()
        self.sample_rate_spin.setRange(128, 2048)
        self.sample_rate_spin.setValue(256)
        self.sample_rate_spin.setSuffix(" Hz")

        self.amplitude_spin = QDoubleSpinBox()
        self.amplitude_spin.setRange(1.0, 300.0)
        self.amplitude_spin.setValue(50.0)

        self.noise_spin = QDoubleSpinBox()
        self.noise_spin.setRange(0.0, 80.0)
        self.noise_spin.setValue(5.0)

        self.artifact_prob_spin = QDoubleSpinBox()
        self.artifact_prob_spin.setRange(0.0, 1.0)
        self.artifact_prob_spin.setSingleStep(0.05)
        self.artifact_prob_spin.setDecimals(2)
        self.artifact_prob_spin.setValue(0.1)

        pl.addWidget(QLabel("Duration"), 0, 0)
        pl.addWidget(self.duration_spin, 0, 1)
        pl.addWidget(QLabel("Sample rate"), 0, 2)
        pl.addWidget(self.sample_rate_spin, 0, 3)
        pl.addWidget(QLabel("Amplitude (uV)"), 1, 0)
        pl.addWidget(self.amplitude_spin, 1, 1)
        pl.addWidget(QLabel("Noise (uV)"), 1, 2)
        pl.addWidget(self.noise_spin, 1, 3)
        pl.addWidget(QLabel("Artifact probability"), 2, 0)
        pl.addWidget(self.artifact_prob_spin, 2, 1)

        self.wicket_spin = QDoubleSpinBox()
        self.wicket_spin.setRange(0.0, 1.0)
        self.wicket_spin.setSingleStep(0.05)
        self.wicket_spin.setDecimals(2)
        self.wicket_spin.setValue(0.0)
        self.wicket_spin.setToolTip("Benign wicket-wave trains (temporal); 0 disables.")
        pl.addWidget(QLabel("Wicket probability"), 2, 2)
        pl.addWidget(self.wicket_spin, 2, 3)

        params_group.setLayout(pl)
        grid.addWidget(params_group, 0, 0, 1, 2)

        # --- Components & clinical ---
        comp_group = QGroupBox("Components & clinical")
        cl = QGridLayout()
        self.include_abnormal_cb = QCheckBox("Abnormal patterns")
        self.include_abnormal_cb.setChecked(True)
        self.include_artifacts_cb = QCheckBox("Classic artifacts")
        self.include_artifacts_cb.setChecked(True)
        self.include_sleep_cb = QCheckBox("Sleep stages")
        self.include_seizure_cb = QCheckBox("Seizure pattern")

        self.eye_state_combo = QComboBox()
        self.eye_state_combo.addItems(["EC (Eyes closed)", "EO (Eyes open)"])
        self.eye_state_combo.setToolTip(
            "EC boosts occipital alpha; EO suppresses posterior alpha and adds beta emphasis (simulator model)."
        )
        self.include_eye_transitions_cb = QCheckBox("Eye open/closed transitions")
        self.include_eye_transitions_cb.setToolTip(
            "Mixes eyes-open and eyes-closed segments across the recording."
        )

        self.psych_combo = QComboBox()
        self._fill_psychiatric_combo()

        self.tbi_combo = QComboBox()
        _combo_add_none(self.tbi_combo)
        for s in ("mild", "moderate", "severe"):
            self.tbi_combo.addItem(s.capitalize(), s)

        self.med_combo = QComboBox()
        _combo_add_none(self.med_combo)
        for m in ("stimulants", "antidepressants", "antipsychotics", "benzodiazepines", "mood_stabilizers"):
            self.med_combo.addItem(m.replace("_", " ").title(), m)

        cl.addWidget(self.include_abnormal_cb, 0, 0)
        cl.addWidget(self.include_artifacts_cb, 0, 1)
        cl.addWidget(self.include_sleep_cb, 1, 0)
        cl.addWidget(self.include_seizure_cb, 1, 1)
        cl.addWidget(QLabel("Eye state"), 2, 0)
        cl.addWidget(self.eye_state_combo, 2, 1)
        cl.addWidget(self.include_eye_transitions_cb, 2, 2, 1, 2)
        eye_hint = QLabel(
            "<b>EC vs EO</b> (simulator): <b>Eyes closed</b> boosts occipital alpha and tones down beta; "
            "<b>Eyes open</b> suppresses posterior alpha and adds frontal/temporal beta emphasis. "
            "These settings apply to custom generation."
        )
        eye_hint.setObjectName("SectionHint")
        eye_hint.setWordWrap(True)
        eye_hint.setTextFormat(Qt.RichText)
        cl.addWidget(eye_hint, 3, 0, 1, 4)
        cl.addWidget(QLabel("Psychiatric / pattern"), 4, 0)
        cl.addWidget(self.psych_combo, 4, 1, 1, 3)
        cl.addWidget(QLabel("TBI severity"), 5, 0)
        cl.addWidget(self.tbi_combo, 5, 1)
        cl.addWidget(QLabel("Medication"), 5, 2)
        cl.addWidget(self.med_combo, 5, 3)

        comp_group.setLayout(cl)
        grid.addWidget(comp_group, 1, 0, 1, 2)

        # --- Advanced (viewer RNG section) ---
        adv_outer = QGroupBox("Advanced features (same knobs as viewer Custom tab)")
        adv_layout = QVBoxLayout()

        preset_row = QHBoxLayout()
        for label, key in (
            ("Spindles", "spindles"),
            ("Transients", "transients"),
            ("Eye movements", "eye_movements"),
            ("Balanced", "balanced"),
        ):
            b = QPushButton(label)
            b.clicked.connect(lambda checked, k=key: self._apply_advanced_preset(k))
            preset_row.addWidget(b)
        adv_layout.addLayout(preset_row)

        inner = QGridLayout()
        self.spindle_flattening_spin = self._prob_spin(0.3)
        self.spindle_complexity_spin = QDoubleSpinBox()
        self.spindle_complexity_spin.setRange(0, 1)
        self.spindle_complexity_spin.setSingleStep(0.1)
        self.spindle_complexity_spin.setDecimals(2)
        self.spindle_complexity_spin.setValue(0.5)

        self.transient_prob_spin = self._prob_spin(0.15)
        self.eye_movement_prob_spin = self._prob_spin(0.2)

        inner.addWidget(QLabel("Spindle flattening"), 0, 0)
        inner.addWidget(self.spindle_flattening_spin, 0, 1)
        inner.addWidget(QLabel("Spindle complexity"), 0, 2)
        inner.addWidget(self.spindle_complexity_spin, 0, 3)
        inner.addWidget(QLabel("Random transients"), 1, 0)
        inner.addWidget(self.transient_prob_spin, 1, 1)
        inner.addWidget(QLabel("Random eye movements"), 1, 2)
        inner.addWidget(self.eye_movement_prob_spin, 1, 3)

        art_row = 2
        artifact_defs = [
            ("Blink", "blink_prob_spin", 0.1),
            ("EMG", "emg_prob_spin", 0.15),
            ("EKG", "ekg_prob_spin", 0.05),
            ("Muscle burst", "muscle_burst_prob_spin", 0.1),
            ("Sweat/drift", "sweat_drift_prob_spin", 0.05),
            ("Saccades", "saccade_prob_spin", 0.1),
            ("Shoulder/neck", "shoulder_neck_emg_prob_spin", 0.08),
            ("Movement", "movement_prob_spin", 0.03),
            ("Line noise", "line_noise_prob_spin", 0.02),
        ]
        self._artifact_spins = {}
        for i, (lab, attr, dv) in enumerate(artifact_defs):
            sp = self._prob_spin(dv)
            setattr(self, attr, sp)
            self._artifact_spins[attr] = sp
            r = art_row + i // 3
            c = (i % 3) * 2
            inner.addWidget(QLabel(lab), r, c)
            inner.addWidget(sp, r, c + 1)

        timing_row = art_row + 4
        self.temporal_jitter_spin = QDoubleSpinBox()
        self.temporal_jitter_spin.setRange(0, 2)
        self.temporal_jitter_spin.setSingleStep(0.1)
        self.temporal_jitter_spin.setDecimals(2)
        self.temporal_jitter_spin.setValue(0.5)
        self.temporal_jitter_spin.setSuffix(" s")

        self.amplitude_variance_spin = QDoubleSpinBox()
        self.amplitude_variance_spin.setRange(0, 1)
        self.amplitude_variance_spin.setSingleStep(0.1)
        self.amplitude_variance_spin.setDecimals(2)
        self.amplitude_variance_spin.setValue(0.3)

        inner.addWidget(QLabel("Temporal jitter"), timing_row, 0)
        inner.addWidget(self.temporal_jitter_spin, timing_row, 1)
        inner.addWidget(QLabel("Amplitude variance"), timing_row, 2)
        inner.addWidget(self.amplitude_variance_spin, timing_row, 3)

        adv_layout.addLayout(inner)

        apply_preset_row = QHBoxLayout()
        apply_preset_row.addWidget(QLabel("Load preset into form:"))
        self.apply_preset_combo = QComboBox()
        for name in sorted(self.sim_gui.presets.keys()):
            self.apply_preset_combo.addItem(name.replace("_", " "), name)
        btn_apply = QPushButton("Apply")
        btn_apply.clicked.connect(self._apply_named_preset_to_form)
        apply_preset_row.addWidget(self.apply_preset_combo, 1)
        apply_preset_row.addWidget(btn_apply)
        adv_layout.addLayout(apply_preset_row)

        adv_outer.setLayout(adv_layout)
        grid.addWidget(adv_outer, 2, 0, 1, 2)

        montage = QLabel(
            "Montage: 19-channel 10-20 - Fp1, Fp2, F7, F3, Fz, F4, F8, T3, C3, Cz, C4, T4, "
            "T5, P3, Pz, P4, T6, O1, O2"
        )
        montage.setWordWrap(True)
        montage.setObjectName("SectionHint")
        grid.addWidget(montage, 3, 0, 1, 2)

        content.setLayout(grid)
        scroll.setWidget(content)
        outer.addWidget(scroll)
        self.setLayout(outer)

    def _fill_psychiatric_combo(self) -> None:
        _combo_add_none(self.psych_combo)
        seen: List[str] = []
        for preset in self.sim_gui.presets.values():
            c = preset.get("psychiatric_condition")
            if c and c not in seen:
                seen.append(c)
        for key in sorted(seen):
            self.psych_combo.addItem(key.replace("_", " "), key)

    def _prob_spin(self, default: float) -> QDoubleSpinBox:
        sp = QDoubleSpinBox()
        sp.setRange(0, 1)
        sp.setSingleStep(0.05)
        sp.setDecimals(2)
        sp.setValue(default)
        return sp

    def _apply_advanced_preset(self, preset_type: str) -> None:
        if preset_type == "spindles":
            self.spindle_flattening_spin.setValue(0.6)
            self.spindle_complexity_spin.setValue(0.8)
            self.transient_prob_spin.setValue(0.05)
            self.eye_movement_prob_spin.setValue(0.1)
        elif preset_type == "transients":
            self.spindle_flattening_spin.setValue(0.1)
            self.spindle_complexity_spin.setValue(0.3)
            self.transient_prob_spin.setValue(0.4)
            self.eye_movement_prob_spin.setValue(0.1)
        elif preset_type == "eye_movements":
            self.spindle_flattening_spin.setValue(0.1)
            self.spindle_complexity_spin.setValue(0.3)
            self.transient_prob_spin.setValue(0.05)
            self.eye_movement_prob_spin.setValue(0.4)
        elif preset_type == "balanced":
            self.spindle_flattening_spin.setValue(0.3)
            self.spindle_complexity_spin.setValue(0.5)
            self.transient_prob_spin.setValue(0.2)
            self.eye_movement_prob_spin.setValue(0.25)

    def _apply_named_preset_to_form(self) -> None:
        name = self.apply_preset_combo.currentData()
        if not name or name not in self.sim_gui.presets:
            return
        preset = self.sim_gui.presets[name]
        p = preset["params"]
        self.duration_spin.setValue(float(p.duration))
        self.sample_rate_spin.setValue(int(p.sample_rate))
        self.amplitude_spin.setValue(float(p.amplitude))
        self.noise_spin.setValue(float(p.noise_level))
        self.artifact_prob_spin.setValue(float(p.artifact_probability))

        self.spindle_flattening_spin.setValue(float(p.spindle_flattening_probability))
        self.spindle_complexity_spin.setValue(float(p.spindle_complexity))
        self.transient_prob_spin.setValue(float(p.transient_probability))
        self.eye_movement_prob_spin.setValue(float(p.eye_movement_probability))

        self.blink_prob_spin.setValue(float(p.blink_probability))
        self.emg_prob_spin.setValue(float(p.emg_probability))
        self.ekg_prob_spin.setValue(float(p.ekg_probability))
        self.muscle_burst_prob_spin.setValue(float(p.muscle_burst_probability))
        self.sweat_drift_prob_spin.setValue(float(p.sweat_drift_probability))
        self.saccade_prob_spin.setValue(float(p.saccade_probability))
        self.shoulder_neck_emg_prob_spin.setValue(float(p.shoulder_neck_emg_probability))
        self.movement_prob_spin.setValue(float(p.movement_probability))
        self.line_noise_prob_spin.setValue(float(p.line_noise_probability))
        self.temporal_jitter_spin.setValue(float(p.temporal_jitter_range))
        self.amplitude_variance_spin.setValue(float(p.amplitude_variance_scale))
        self.wicket_spin.setValue(float(getattr(p, "wicket_probability", 0.0)))

        self.include_abnormal_cb.setChecked(bool(preset["include_abnormal"]))
        self.include_artifacts_cb.setChecked(bool(preset["include_artifacts"]))
        self.include_sleep_cb.setChecked(bool(preset["include_sleep"]))
        self.include_seizure_cb.setChecked(bool(preset["include_seizure"]))
        self.include_eye_transitions_cb.setChecked(bool(preset.get("include_eye_transitions", False)))

        es = preset.get("eye_state", "EC")
        self.eye_state_combo.setCurrentIndex(1 if es == "EO" else 0)

        psych = preset.get("psychiatric_condition")
        self._select_combo_data(self.psych_combo, psych)

        self._select_combo_data(self.tbi_combo, preset.get("tbi_severity"))
        self._select_combo_data(self.med_combo, preset.get("medication"))

    @staticmethod
    def _select_combo_data(combo: QComboBox, value: Any) -> None:
        if value is None:
            combo.setCurrentIndex(0)
            return
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return
        combo.setCurrentIndex(0)

    def collect(self) -> Tuple["SignalParameters", Dict[str, Any]]:
        """Build SignalParameters and kwargs for generate_comprehensive_signal."""
        from modules_pyqt5.eeg_signal_simulator import SignalParameters

        params = SignalParameters(
            duration=float(self.duration_spin.value()),
            amplitude=float(self.amplitude_spin.value()),
            noise_level=float(self.noise_spin.value()),
            artifact_probability=float(self.artifact_prob_spin.value()),
            sample_rate=int(self.sample_rate_spin.value()),
            spindle_flattening_probability=float(self.spindle_flattening_spin.value()),
            spindle_complexity=float(self.spindle_complexity_spin.value()),
            transient_probability=float(self.transient_prob_spin.value()),
            eye_movement_probability=float(self.eye_movement_prob_spin.value()),
            blink_probability=float(self.blink_prob_spin.value()),
            emg_probability=float(self.emg_prob_spin.value()),
            ekg_probability=float(self.ekg_prob_spin.value()),
            muscle_burst_probability=float(self.muscle_burst_prob_spin.value()),
            sweat_drift_probability=float(self.sweat_drift_prob_spin.value()),
            saccade_probability=float(self.saccade_prob_spin.value()),
            shoulder_neck_emg_probability=float(self.shoulder_neck_emg_prob_spin.value()),
            movement_probability=float(self.movement_prob_spin.value()),
            line_noise_probability=float(self.line_noise_prob_spin.value()),
            temporal_jitter_range=float(self.temporal_jitter_spin.value()),
            amplitude_variance_scale=float(self.amplitude_variance_spin.value()),
            wicket_probability=float(self.wicket_spin.value()),
        )

        eye_state = "EO" if self.eye_state_combo.currentIndex() == 1 else "EC"

        gen_kw: Dict[str, Any] = {
            "include_abnormal": self.include_abnormal_cb.isChecked(),
            "include_artifacts": self.include_artifacts_cb.isChecked(),
            "include_sleep": self.include_sleep_cb.isChecked(),
            "include_seizure": self.include_seizure_cb.isChecked(),
            "psychiatric_condition": self.psych_combo.currentData(),
            "tbi_severity": self.tbi_combo.currentData(),
            "medication": self.med_combo.currentData(),
            "eye_state": eye_state,
            "include_eye_transitions": self.include_eye_transitions_cb.isChecked(),
        }

        return params, gen_kw
