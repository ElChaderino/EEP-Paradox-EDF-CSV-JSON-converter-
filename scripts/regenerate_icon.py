"""Rebuild assets/branding/eeg_paradox_edf_icon.ico from eeg_paradox_edf_icon.png (Pillow required)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
PNG = ROOT / "assets" / "branding" / "eeg_paradox_edf_icon.png"
ICO = ROOT / "assets" / "branding" / "eeg_paradox_edf_icon.ico"


def main() -> None:
    im = Image.open(PNG).convert("RGBA")
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    icons = [im.resize(s, Image.Resampling.LANCZOS) for s in sizes]
    icons[0].save(
        ICO,
        format="ICO",
        sizes=[(i.width, i.height) for i in icons],
        append_images=icons[1:],
    )
    print(f"Wrote {ICO} ({ICO.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
