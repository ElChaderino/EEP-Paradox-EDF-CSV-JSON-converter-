# EEG Paradox EDF Studio — Converter manual

This document describes **how each conversion path works** inside `EEG_EDF_Standalone_Tool`: data shapes, units, file roles, and the software pipeline (Python / MNE-Python).

---

## 1. Architecture overview

```
Tabular files (CSV, JSON)     simulator presets
        │                            │
        ▼                            ▼
   tabular_edf.py              EEGSignalSimulator
        │                            │
        └──────────► MNE Raw ◄───────┘
                         │
              export_edf / read_raw_edf
                         │
                        EDF
```

- **MNE-Python** (`mne.io.Raw`, `mne.io.RawArray`) is the internal representation.
- **Volts** are MNE’s native amplitude unit for EEG channels.
- User-facing CSV exports default to **microvolts (µV)** because that matches clinical EEG conventions.

Implementation entry points live in [`tabular_edf.py`](tabular_edf.py). The GUI (`gui/main_window.py`) calls those functions; it does not implement conversion logic itself.

---

## 2. Units and scaling

| Layer | Unit | Notes |
|--------|------|--------|
| CSV / manifest `unit` field | `uV` (default) or `V` | Declares how numeric cells in CSV are interpreted. |
| MNE `Raw` | **volts** | All internal arrays from `get_data()` are in volts. |
| EDF file | Per EDF spec | Written by MNE’s exporter from volt-scale arrays. |

**Import (tabular → Raw):**

- `uV`: values are multiplied by `1e-6` before building `RawArray`.
- `V`: values are used as-is.

**Export (Raw → CSV):**

- You choose **CSV unit** in the Convert tab (`uV` or `V`).
- Data are converted from volts with `_scale_from_volts()` for the file.

---

## 3. CSV format (full specification)

### 3.1 Required structure

- **First row:** header.
- **Following rows:** one sample per row, numeric only (comma-separated by default).
- Encoding: UTF-8 with optional BOM (`utf-8-sig` when reading).

### 3.2 Two layouts

**A) With time column (recommended)**

First header cell must be one of: `time_s`, `time`, `sec`, `seconds` (case-insensitive after strip).

- Column 0: time in **seconds**, strictly increasing.
- Remaining columns: one column per channel, in the same order as channel names in the header.

**Sampling rate:** not taken from the GUI in this mode. It is **inferred** as:

\[
f_s = 1 / \mathrm{median}(\Delta t)
\]

where \(\Delta t\) are successive differences of the time column.

**B) Without time column**

- Every header cell is a **channel label**.
- Samples are assumed **uniformly spaced** at `sfreq` Hz (from the GUI **Sampling rate** field or from a JSON manifest).
- Implicit times are \(0, 1/f_s, 2/f_s, \ldots\).

### 3.3 Channel names

- Labels are copied from the CSV header (after the optional time column).
- For simulator-compatible workflows, use standard 10–20 names (`Fp1`, `Cz`, …). The simulator itself uses a fixed 19-channel montage.

### 3.4 Validation rules

- Empty numeric cells raise an error.
- Ragged rows (different column counts) raise an error.
- With a time column, non-increasing times raise an error.

---

## 4. JSON formats

### 4.1 Manifest JSON (large recordings)

The manifest is a **small JSON file** that points at a **separate CSV** with the bulk data.

**Required keys:**

- `csv_file` — path relative to the manifest file (same folder recommended).

**Optional keys:**

- `sfreq` — required when the CSV has **no** `time_s` column (constant sampling).
- `channel_names` — if provided and matching channel count, can override CSV header names (see `csv_to_raw()`).
- `unit` — `uV` or `V` (default `uV`).
- `delimiter` — CSV delimiter (default `,`).

**Detection:** `load_json_auto()` chooses manifest mode when there is **no** top-level `"data"` array.

Pipeline:

1. Resolve `csv_file` next to the JSON path.
2. Call `csv_to_raw()` with `sfreq`, `unit`, and optional `channel_names` from the manifest.

### 4.2 Embedded JSON (short clips)

Used for **small** datasets where a single JSON is convenient.

**Required keys:**

- `sfreq` — float, Hz.
- `channel_names` — array of strings, length \(C\).
- `data` — JSON array of shape **channels × samples**: outer length \(C\), each inner array length \(N\).
- `unit` — optional, default `uV`.

**Limit in the GUI:** `EDF → embedded JSON` refuses outputs larger than **500,000 samples** per channel (guardrail for memory and UI). Use CSV + manifest for long recordings.

Pipeline: `embedded_json_to_raw()` builds `numpy` array → scale to volts → `RawArray`.

---

## 5. Conversion paths (pipelines)

### 5.1 CSV → EDF

1. `load_csv_to_array()` → `(data[C,N], time_or_None, names, inferred_sf)`.
2. `csv_to_raw()` applies unit scaling, chooses `sfreq` (time-derived or GUI).
3. `export_edf()` → `prepare_raw_for_edf_export()` then MNE `export(..., fmt='edf')`.

**`prepare_raw_for_edf_export()`:** If the recording length is not essentially an integer number of seconds (floating-point edge at the last sample), the signal is **cropped** to `floor(duration)` seconds. This avoids calling `raw.resample()`, which would run an anti-alias FIR filter over the entire trace and change amplitudes/phases. MNE may still apply minimal **record alignment padding** when writing EDF blocks (see §7).

### 5.2 JSON → EDF

1. `load_json_auto(path)`:
   - If `"data"` present → `embedded_json_to_raw()`.
   - Else → `json_manifest_to_raw()` → CSV path + manifest fields → `csv_to_raw()`.
2. `export_edf()` as above.

### 5.3 EDF → CSV + manifest JSON

1. `read_edf()` → `mne.io.read_raw_edf(..., preload=True)`.
2. `raw_to_csv_and_manifest()`:
   - Writes CSV with columns `time_s`, then each channel.
   - Writes JSON manifest including `format`, `sfreq`, `channel_names`, `unit`, `csv_file`, dimensions, `duration_s`, and any `extra_meta` (e.g. `source_edf`).

This is the **recommended lossless round-trip** format for external tools: CSV holds samples; JSON holds metadata.

### 5.4 EDF → embedded JSON

1. `read_edf()`.
2. `raw_to_embedded_json()` — embeds full `data` arrays as nested lists (suitable only for short clips).

---

## 6. Simulator → EDF (Simulate tab)

This path does **not** use CSV as input. It uses `EEGSimulatorGUI` / `EEGSignalSimulator` from `modules_pyqt5`:

1. **Generate:** `generate_comprehensive_signal()` builds a NumPy array `signal_data` where amplitudes follow **`SignalParameters.amplitude` and all rhythm definitions in microvolts (µV)** — this is the native numeric convention of the generator.
2. **Wrap:** `create_mne_raw()` converts that array to **`mne.io.RawArray` with data in volts** (`signal × 1e-6`), which is what MNE expects for EEG.
3. **Save:** `save_simulated_signal()` exports EDF with **`raw.export(..., fmt='edf')`**. Before export, **`_crop_raw_for_integer_second_edf()`** may crop the tail to a whole-second duration — **no resampling**, so no extra broadband filtering step is applied for that alignment.

The dict field **`signal_dict['data']`** remains in **µV** for UIs that plot numpy directly; **`signal_dict['raw'].get_data()`** is in **volts** after wrapping.

Optional **CSV + manifest** after save calls `raw_to_csv_and_manifest()` on a **copy** of the simulated `Raw`, with metadata merged into the manifest (`default=str` for JSON safety).

### 6.1 What is *not* applied on export

- Tabular conversion and simulator EDF export **do not** high-pass or notch-filter the signal in `tabular_edf.py` or in `save_simulated_signal()`.
- Presets may still **include synthetic artifacts** (blinks, EMG, etc.) because those are part of the simulation recipe — that is intentional content, not an export filter.

---

## 7. Known behaviors and limitations

1. **EDF block alignment:** MNE may pad **slightly** at file end to satisfy EDF record blocking. After `EDF → CSV`, sample counts may differ by a **small** margin from the original CSV round-trip.
2. **Channel types:** Tabular import marks all channels as `eeg`. Non-EEG traces in exotic EDFs are still exported as columns in CSV by `get_data()` on the loaded raw (behavior follows MNE channel pick defaults in `raw_to_csv_and_manifest`).
3. **Clinical disclaimer:** Simulator presets (including “Grateful Head”) are **synthetic** patterns for software testing and education, not diagnostic recordings.

---

## 8. Quick reference — GUI ↔ functions

| GUI selection | Primary functions |
|----------------|---------------------|
| CSV → EDF | `csv_to_raw`, `export_edf` |
| JSON → EDF | `load_json_auto`, `export_edf` |
| EDF → CSV + manifest | `read_edf`, `raw_to_csv_and_manifest` |
| EDF → embedded JSON | `read_edf`, `raw_to_embedded_json` |

---

## 9. Related files

| File | Role |
|------|------|
| [`tabular_edf.py`](tabular_edf.py) | All conversion primitives |
| [`gui/main_window.py`](gui/main_window.py) | Qt UI and wiring |
| [`gui/styles.py`](gui/styles.py) | Application stylesheet |
| [`modules_pyqt5/eeg_signal_simulator.py`](../modules_pyqt5/eeg_signal_simulator.py) | Signal synthesis |

For packaging to a Windows executable, see [`README.md`](README.md) and [`build_exe.spec`](build_exe.spec).
