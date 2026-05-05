"""
CSV / JSON manifest ↔ MNE Raw ↔ EDF helpers for the standalone tool.

CSV convention (export default):
  - Header: time_s,<ch1>,<ch2>,... (channel labels)
  - Units in CSV default to microvolts (uV); MNE stores volts internally.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

import mne
import numpy as np


UNIT_UV = "uV"
UNIT_V = "V"


def _scale_to_volts(data_uv_or_v: np.ndarray, unit: str) -> np.ndarray:
    unit_l = (unit or UNIT_UV).strip().lower()
    if unit_l in ("uv", "µv", "microvolt", "microvolts"):
        return np.asarray(data_uv_or_v, dtype=np.float64) * 1e-6
    if unit_l in ("v", "volt", "volts"):
        return np.asarray(data_uv_or_v, dtype=np.float64)
    raise ValueError(f"Unknown unit {unit!r}; use 'uV' or 'V'")


def _scale_from_volts(data_v: np.ndarray, unit: str) -> np.ndarray:
    unit_l = (unit or UNIT_UV).strip().lower()
    if unit_l in ("uv", "µv", "microvolt", "microvolts"):
        return np.asarray(data_v, dtype=np.float64) / 1e-6
    if unit_l in ("v", "volt", "volts"):
        return np.asarray(data_v, dtype=np.float64)
    raise ValueError(f"Unknown unit {unit!r}; use 'uV' or 'V'")


def load_csv_to_array(
    csv_path: Path,
    delimiter: str = ",",
) -> Tuple[np.ndarray, Optional[np.ndarray], List[str], float]:
    """
    Load numeric CSV. Returns:
      data_ch_by_samples (n_channels, n_samples),
      time_s (n_samples,) or None if no time column,
      channel_names,
      inferred or placeholder sfreq (0 if must be supplied externally).
    """
    path = Path(csv_path)
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f, delimiter=delimiter)
        rows = list(reader)
    if len(rows) < 2:
        raise ValueError("CSV must have a header and at least one data row")

    header = [h.strip() for h in rows[0]]
    data_rows = rows[1:]

    def _float_row(r: Sequence[str]) -> List[float]:
        out = []
        for x in r:
            x = x.strip()
            if x == "":
                raise ValueError("Empty cell in numeric region")
            out.append(float(x))
        return out

    lower0 = header[0].lower()
    has_time = lower0 in ("time_s", "time", "sec", "seconds")

    if has_time:
        ch_names = header[1:]
        times: List[float] = []
        blocks: List[List[float]] = []
        for r in data_rows:
            if len(r) != len(header):
                raise ValueError("Ragged CSV row length")
            times.append(float(r[0].strip()))
            blocks.append(_float_row(r[1:]))
        time_arr = np.asarray(times, dtype=np.float64)
        data_T = np.asarray(blocks, dtype=np.float64)
        data = data_T.T
        diffs = np.diff(time_arr)
        if np.any(diffs <= 0):
            raise ValueError("time_s must be strictly increasing")
        sfreq = float(1.0 / np.median(diffs)) if len(time_arr) > 1 else 256.0
        return data, time_arr, ch_names, sfreq

    ch_names = header
    blocks = [_float_row(r) for r in data_rows]
    data_T = np.asarray(blocks, dtype=np.float64)
    data = data_T.T
    return data, None, ch_names, 0.0


def csv_to_raw(
    csv_path: Union[str, Path],
    sfreq: Optional[float] = None,
    unit: str = UNIT_UV,
    channel_names: Optional[List[str]] = None,
    delimiter: str = ",",
) -> mne.io.Raw:
    """Build RawArray from CSV (with optional time_s column)."""
    path = Path(csv_path)
    data, time_arr, names, inferred_sf = load_csv_to_array(path, delimiter=delimiter)
    if channel_names:
        names = list(channel_names)
        if len(names) != data.shape[0]:
            raise ValueError(
                f"channel_names length {len(names)} != data rows {data.shape[0]}"
            )

    # If CSV includes time_s, derive sfreq from timestamps (most accurate).
    if inferred_sf > 0:
        use_sf = inferred_sf
    else:
        use_sf = float(sfreq) if sfreq is not None else 0.0
    if use_sf <= 0:
        raise ValueError(
            "Sampling rate (sfreq) is required when CSV has no time_s column."
        )

    data_v = _scale_to_volts(data, unit)
    info = mne.create_info(names, use_sf, ch_types=["eeg"] * len(names))
    raw = mne.io.RawArray(data_v, info, verbose=False)
    return raw


def load_json_manifest(path: Union[str, Path]) -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def json_manifest_to_raw(
    json_path: Union[str, Path],
    sfreq_override: Optional[float] = None,
    unit_override: Optional[str] = None,
    channel_names_override: Optional[List[str]] = None,
    delimiter: str = ",",
) -> mne.io.Raw:
    """
    Manifest JSON keys:
      sfreq (required unless CSV has time_s),
      channel_names (optional if CSV header has names),
      unit: 'uV' | 'V' (default uV),
      csv_file: relative path to CSV next to this JSON,
      delimiter: optional CSV delimiter
    """
    jp = Path(json_path).resolve()
    meta = load_json_manifest(jp)
    unit = unit_override or meta.get("unit", UNIT_UV)
    csv_rel = meta.get("csv_file")
    if not csv_rel:
        raise ValueError("JSON manifest must include 'csv_file' pointing to CSV data")

    csv_path = (jp.parent / csv_rel).resolve()
    if not csv_path.is_file():
        raise FileNotFoundError(csv_path)

    sfreq = sfreq_override if sfreq_override is not None else meta.get("sfreq")
    ch_from_meta = channel_names_override or meta.get("channel_names")
    delim = meta.get("delimiter", delimiter)

    raw = csv_to_raw(
        csv_path,
        sfreq=float(sfreq) if sfreq is not None else None,
        unit=unit,
        channel_names=ch_from_meta,
        delimiter=str(delim),
    )
    return raw


def embedded_json_to_raw(json_path: Union[str, Path]) -> mne.io.Raw:
    """JSON with 'data': list of channels, each a list of samples; plus sfreq, channel_names."""
    jp = Path(json_path)
    meta = load_json_manifest(jp)
    if "data" not in meta:
        raise ValueError("Embedded JSON requires 'data' field (channels x samples)")
    sfreq = float(meta["sfreq"])
    names: List[str] = list(meta["channel_names"])
    data_list = meta["data"]
    data = np.asarray(data_list, dtype=np.float64)
    if data.ndim != 2:
        raise ValueError("'data' must be 2D [n_channels x n_samples]")
    if len(names) != data.shape[0]:
        raise ValueError("channel_names length does not match data")
    unit = meta.get("unit", UNIT_UV)
    data_v = _scale_to_volts(data, unit)
    info = mne.create_info(names, sfreq, ch_types=["eeg"] * len(names))
    return mne.io.RawArray(data_v, info, verbose=False)


def load_json_auto(
    json_path: Union[str, Path],
    **kwargs: Any,
) -> mne.io.Raw:
    meta = load_json_manifest(Path(json_path))
    if "data" in meta and isinstance(meta["data"], list):
        return embedded_json_to_raw(json_path)
    return json_manifest_to_raw(json_path, **kwargs)


def read_edf(edf_path: Union[str, Path]) -> mne.io.Raw:
    return mne.io.read_raw_edf(str(edf_path), preload=True, verbose=False)


def prepare_raw_for_edf_export(raw: mne.io.Raw) -> mne.io.Raw:
    """
    Trim trailing fractional second so duration is a whole number of seconds.
    Uses crop only — does not call resample(), so no extra low-pass / FIR filtering
    is applied to the full recording (preserves simulated or imported waveforms).

    Duration uses n_times / sfreq (full sample span). Do not use times[-1], which is
    (n_times - 1) / sfreq and mis-classifies integer-second recordings as fractional.
    """
    raw = raw.copy()
    sfreq = float(raw.info["sfreq"])
    if sfreq <= 0:
        return raw
    dur = raw.n_times / sfreq
    if dur <= 0:
        return raw
    if abs(dur - round(dur)) <= 0.001:
        return raw
    tmax = float(np.floor(dur))
    if tmax > 0:
        raw.crop(tmin=0.0, tmax=tmax)
    return raw


def export_edf(raw: mne.io.Raw, edf_path: Union[str, Path], overwrite: bool = True) -> Path:
    out = Path(edf_path)
    to_save = prepare_raw_for_edf_export(raw)
    to_save.export(str(out), fmt="edf", overwrite=overwrite)
    return out


def raw_to_csv_and_manifest(
    raw: mne.io.Raw,
    csv_path: Union[str, Path],
    json_path: Union[str, Path],
    unit: str = UNIT_UV,
    extra_meta: Optional[Dict[str, Any]] = None,
) -> Tuple[Path, Path]:
    """Write full recording as CSV + sidecar JSON manifest."""
    csv_p = Path(csv_path)
    json_p = Path(json_path)
    data = raw.get_data()
    times = raw.times
    ch_names = raw.ch_names
    sfreq = raw.info["sfreq"]

    csv_p.parent.mkdir(parents=True, exist_ok=True)
    with csv_p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["time_s"] + list(ch_names))
        data_out = _scale_from_volts(data, unit)
        for i in range(data.shape[1]):
            row = [f"{times[i]:.9f}"]
            row.extend(f"{data_out[c, i]:.9f}" for c in range(data.shape[0]))
            w.writerow(row)

    manifest: Dict[str, Any] = {
        "format": "eeg_paradox_tabular_v1",
        "sfreq": sfreq,
        "channel_names": list(ch_names),
        "unit": unit,
        "csv_file": csv_p.name,
        "n_channels": len(ch_names),
        "n_samples": int(data.shape[1]),
        "duration_s": float(times[-1]) if len(times) else 0.0,
    }
    if extra_meta:
        manifest.update(extra_meta)

    with json_p.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)

    return csv_p, json_p


def raw_to_embedded_json(
    raw: mne.io.Raw,
    json_path: Union[str, Path],
    unit: str = UNIT_UV,
    max_samples: Optional[int] = None,
) -> Path:
    """Small recordings only: embed data array in JSON."""
    jp = Path(json_path)
    data = raw.get_data()
    if max_samples is not None and data.shape[1] > max_samples:
        raise ValueError(
            f"Recording too long for embedded JSON ({data.shape[1]} samples); "
            "use raw_to_csv_and_manifest instead."
        )
    data_out = _scale_from_volts(data, unit)
    payload = {
        "format": "eeg_paradox_embedded_v1",
        "sfreq": raw.info["sfreq"],
        "channel_names": list(raw.ch_names),
        "unit": unit,
        "data": data_out.tolist(),
    }
    with jp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, default=str)
    return jp
