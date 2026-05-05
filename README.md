# EEG Paradox EDF Studio

**EEG Paradox EDF Studio** is a PyQt desktop app built around two jobs: (1) convert tabular EEG ↔ EDF, and (2) simulate synthetic **19-channel** EEG and export it the same way. I/O is **MNE-backed** (`read_raw_edf`, `Raw.export` to EDF)—the same stack many Python EEG pipelines use.

There is also **EEG Paradox EDF Converter (Lite)**—same **Convert** tab UI, smaller footprint: **converter only** (no **Simulate**, **Traces**, or **Files** tab).

**Documentation map:** this README is the **operator’s guide** (UI behaviour, presets, tabs). For **data shapes, scaling math, and pipeline detail**, see **[CONVERTER_MANUAL.md](CONVERTER_MANUAL.md)**.

---

## Converter / interchange (Convert tab)

Use it when data are already in CSV or JSON and you need EDF, or EDF exists and you need research-friendly exports.

| Direction | Behaviour |
|-----------|-----------|
| **CSV → EDF** | Wide matrix + header row of channel names. **Automatic Hz** when the first column is a strictly increasing time column named `time_s`, `time`, `sec`, or `seconds`. Otherwise set **Sampling rate** in the UI (**1–100,000 Hz**). |
| **JSON → EDF** | Either a **manifest** JSON beside a CSV (`csv_file`, `sfreq`, optional `channel_names`, `unit`, optional `delimiter`), or **embedded** JSON (`data` as channel × samples, `sfreq`, `channel_names`, optional `unit`). |
| **EDF → CSV + manifest JSON** | Full recording: CSV with `time_s` + channels; companion manifest (`*_manifest.json` when you choose a `.csv` path). Manifest includes `format: eeg_paradox_tabular_v1`, `sfreq`, names, counts, duration, `source_edf` when exported from conversion. Simulated saves can merge metadata into the manifest when you tick sidecars in **Simulate**. |
| **EDF → embedded JSON** | Single portable JSON; `format: eeg_paradox_embedded_v1`. **Cap ~500,000 samples per channel** dimension; longer sessions should use **CSV + manifest**. |

**Units:** The **µV vs V** combo applies to interpreting CSV/manifest/embed values (**MNE stores volts internally**).

### Guarantees (as stated in-app)

- CSV is interpreted as **µV by default**, with optional volts.
- **EDF export** only trims a **trailing fractional second** (`crop`); it **does not resample**, so waveform shape is preserved.
- **Manifest** exports summarize channels, Hz, duration, unit, and source metadata.

### Operational notes

**Browse** buttons can suggest filenames under **`managed_outputs`** subfolders (`conversions`, `csv_manifests`, `embedded_json`). **Convert** and **Simulate** both append to an **Activity** log and refresh the **Files** tab after successful runs (**full Studio** only).

---

## Simulator

The synthetic generator uses the EEG Paradox **preset catalog** and the same **`generate_comprehensive_signal`** pathway as the main viewer—from minimal/clean EO–EC setups through artifact-heavy and multi-condition scenarios. Outputs land as **EDF**; optionally the same **CSV + manifest** and/or **embedded JSON** paths as conversion (embedded skipped with a log line if too long).

### Simulate → Presets

**Flow:** pick a category (tooltip = short category description), then a preset (filter via **Search**). Preset detail shows narrative description plus duration, sample rate, amplitude, noise, preset eye state, EO/EC transitions flag, and which feature flags apply (abnormal, artifacts, sleep, seizure, eye transitions).

#### Preset library (grouped as in the app)

| Category | Role |
|----------|------|
| **Basic EEG Patterns** | Normal-style baselines (`normal_adult`, `sleep_study`, `epilepsy_monitoring`, `pediatric`, `artifact_heavy`). |
| **Eye State Patterns** | `clean_ec`, `clean_eo`, standard `eyes_closed` / `eyes_open`, `eye_state_transitions`, `grateful_head`. |
| **Advanced Spindles & Transients** | Sleep-like spindles, flattening, random transients, eye-movement emphasis, wickets, mixed “complex” and non-repetitive variants. |
| **Psychiatric Conditions** | ADHD, autism, PTSD/CPTSD, bipolar I/II, BPD, executive dysfunction, learning disability, anxiety, depression, OCD, schizophrenia, concussion, AUDHD (`audhd`), ASD+ADD-style (`add_with_asd`), etc. |
| **Neurological Disorders** | Epilepsy, Parkinson’s, Alzheimer’s, stroke, migraine, MS-style. |
| **Chronic Medical Conditions** | Chemo brain, fibromyalgia, chronic fatigue, lupus. |
| **COVID-Related Conditions** | Separate category: `covid_brain_fog`, `long_covid`. |
| **TBI Conditions** | Mild / moderate / severe TBIs as dedicated presets (`tbi_mild`, …). |
| **Medication Effects** | On stimulants, antidepressants, antipsychotics, benzodiazepines, mood stabilizers. |
| **Real-World Combos** | Common dual-condition / condition+med snapshots (e.g. ADHD + anxiety, depression + concussion, PTSD mild TBI). |
| **Additional Combos** | Extra multi-condition presets. |
| **Condition + Medication** | Triple-style pairings preserved as their own presets. |
| **Condition + TBI** | e.g. ADHD + mild TBI, autism + concussion. |
| **Triple Combos** | Three-way condition mixes. |
| **Condition + Medication + TBI** | Highest-complexity named presets in the catalog. |
| **Specialized Clinical** | Pediatric, geriatric, veteran, athlete overlays. |
| **Research Scenarios** | Control / cohort-style labels. |
| **Educational Scenarios** | Basics, artifacts, abnormals for teaching. |
| **Extreme Cases** | High complexity/amplitude demos and contrasting minimal activity. |

#### Overrides (same sub-tab)

- Optional **duration** (**5–3600 s**) and **amplitude** (µV).
- **Eye state:** follow preset, force EC, or force EO (alpha/beta shaping as modeled in-engine).
- **EO/EC transitions:** same as preset, **on** (alternating segments), or **off**.

**Generate from preset** fills **Generated signal:** duration, sample rate, channels, samples, mean RMS (µV), and a short active features summary. Metadata recorded includes applied eye state/transitions and preset id/description.

### Simulate → Custom

Scrollable form aligned with the viewer **Custom** tab plus clinical toggles:

- **Core:** duration, sample rate **128–2048 Hz**, amplitude, noise, overall artifact probability, wicket probability (temporal benign trains).
- **Components & clinical:** abnormal patterns, classic artifacts, sleep stages, seizure pattern; EO vs EC; optional EO–EC transitions; **psychiatric** pattern (dropdown populated from psychiatric keys present across presets—not every theoretical label), **TBI** severity (mild/moderate/severe or none), **medication** class (stimulants, antidepressants, antipsychotics, benzodiazepines, mood stabilizers—or none).
- **Advanced:** one-click presets **Spindles / Transients / Eye movements / Balanced**, then granular spindle flattening & complexity, random transients/eye movements, blink/EMG/EKG/muscle burst/sweat-drift/saccades/shoulder-neck/movement/line noise, temporal jitter, amplitude variance.

**Load preset into form:** choose any preset name → **Apply** to populate all sliders/checks, then edit.

**Montage:** fixed **19-channel 10–20:** `Fp1`, `Fp2`, `F7`, `F3`, `Fz`, `F4`, `F8`, `T3`, `C3`, `Cz`, `C4`, `T4`, `T5`, `P3`, `Pz`, `P4`, `T6`, `O1`, `O2`.

**Save generated recording:** primary **Save EDF**; optional **CSV + manifest JSON** under `csv_manifests` with stem derived from the EDF file; optional **embedded JSON** under `embedded_json` (same sample cap).

---

## Viewer & workspace (full Studio)

### Traces

EDFbrowser-style scrolling for **`.edf`**, **`.csv`**, **`.json`** (manifest or embedded). CSV fallback Hz applies when **no** time column. Controls include window length and presets (**0.5–120 s**), **µV/div** with presets and ×2 / ÷2 / **Fit** (Fit uses ~98th percentile on the visible window), vertical trace spacing, playback **Play/Pause** with speed **0.25×–4×**, **±1 s** nudges, slider + drag-to-scroll, mouse wheel pan and **Ctrl+wheel** × timescale zoom, optional grid, zero lines, **Invert polarity**, per-channel visibility (**All / None**). Sidebar **Annotations** lists MNE `Raw.annotations` (onset, duration, description) when present (useful after simulator annotation hooks). Opening CSV here assumes **`UNIT_UV`** in code (converter tab still allows volts for ingest).

### Files

Rooted at **`managed_outputs`** next to the tool package, with **`conversions`**, **`simulations`**, **`csv_manifests`**, **`embedded_json`**, and **`imports`** (optional staging folder). Browse all or filter by bucket; columns **Name / Folder / Size / Modified**; **Open**, open containing folder, **Refresh**, delete (only paths under the managed root).

---

## Install & distribution (quick reference)

### Repository layout

| Layout | What it looks like | `python` command |
|--------|-------------------|------------------|
| **Monorepo** (full EEG Paradox Viewer repo) | `EEG_EDF_Standalone_Tool/main.py` inside the repo | From repo root: `python EEG_EDF_Standalone_Tool/main.py` |
| **Flat / standalone GitHub repo** | `main.py`, `gui/`, `tabular_edf.py`, `requirements-standalone.txt` at the **same** project root | From that root: `python main.py` |

`main.py` detects both layouts. **`One_Click_Setup.bat`** and **`Run_EDF_Studio.bat`** also support both (folder name `EEG_EDF_Standalone_Tool` vs flat root).

**Simulate tab (full Studio):** uses **`modules_pyqt5`** (same package as the main EEG Paradox Viewer). In a **flat** repo, copy that folder **next to `main.py`** for full presets/custom simulation. **`python main.py` still starts** without it — **Convert**, **Traces**, and **Files** work; **Simulate** shows setup instructions instead of crashing. For converter-only, use **`main_lite.py`** or the frozen **Lite** build.

| Goal | How |
|------|-----|
| Run from source (monorepo) | `python EEG_EDF_Standalone_Tool/main.py` from repo root |
| Run from source (flat repo) | `python main.py` after `pip install -r requirements-standalone.txt` |
| Dependencies | `pip install -r requirements-standalone.txt` |
| Windows one-click venv | `One_Click_Setup.bat` → `Run_EDF_Studio.bat` |
| Frozen **full** Studio | `build_windows_venv.bat` → `dist/EEGParadox_EDF_Tool/` (ship whole folder) |
| Frozen **Lite** | `build_exe_lite.spec` → `dist/EEGParadox_EDF_Converter_Lite/` |

PyInstaller details and MNE freeze notes: **`build_exe.spec`**, **`build_exe_lite.spec`**, and comments in **`build_windows_venv.bat`**.

### Publishing **only** this folder to a flat GitHub repo

From the **full EEG Paradox repository root** (parent of `EEG_EDF_Standalone_Tool/`):

1. Commit everything you want included **inside** `EEG_EDF_Standalone_Tool/` (nothing else is pushed).
2. Run **`scripts/Publish_Standalone_ToGitHub.ps1`** (default remote: `ElChaderino/EEP-Paradox-EDF-CSV-JSON-converter-`). Use **`-Force`** if the remote history does not match the subtree branch.

That uses **`git subtree split --prefix=EEG_EDF_Standalone_Tool`** so the remote `main` looks like a standalone project (`main.py` at root). It does **not** add **`modules_pyqt5`** — document that in the flat repo README or vendor that folder separately for **Simulate**.

---

## Closing disclaimer

Synthetic data and converters are for **interop, training, teaching, and QA**—not diagnosis or patient care. Converter outputs may represent **real** recordings; simulated exports should always be labeled **synthetic** in your workflow—the app records generation metadata where sidecars allow.

Preset and category names describe **pedagogical and engineering scenarios**; they are not autonomous clinical classifications.
