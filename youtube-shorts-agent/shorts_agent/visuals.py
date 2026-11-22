"""Background footage: Pexels portrait stock video when a key is set, animated gradients otherwise."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import requests

W, H, FPS = 1080, 1920, 30

PALETTES = [
    ("0x0f2027", "0x2c5364"), ("0x41295a", "0x2f0743"), ("0x1e3c72", "0x2a5298"),
    ("0x232526", "0x414345"), ("0x16222a", "0x3a6073"), ("0x3a1c71", "0xd76d77"),
    ("0x0b486b", "0xf56217"), ("0x134e5e", "0x71b280"),
]


def pexels_clip(query: str, api_key: str, dest: Path, exclude: set[int] | None = None) -> Path | None:
    exclude = exclude if exclude is not None else set()
    try:
        r = requests.get("https://api.pexels.com/videos/search",
                         params={"query": query, "orientation": "portrait", "size": "medium", "per_page": 10},
                         headers={"Authorization": api_key}, timeout=20)
        r.raise_for_status()
        for video in r.json().get("videos", []):
            if video["id"] in exclude:
                continue
            files = [f for f in video.get("video_files", [])
                     if f.get("width") and f.get("height") and f["height"] > f["width"] and f["height"] >= 1280]
            if not files:
                continue
            best = min(files, key=lambda f: abs(f["height"] - 1920))
            with requests.get(best["link"], stream=True, timeout=60) as dl:
                dl.raise_for_status()
                with open(dest, "wb") as fh:
                    for chunk in dl.iter_content(1 << 16):
                        fh.write(chunk)
            exclude.add(video["id"])
            return dest
    except Exception:
        return None
    return None


def gradient_clip(seed: str, duration: float, dest: Path) -> Path:
    idx = int(hashlib.md5(seed.encode()).hexdigest(), 16) % len(PALETTES)
    c0, c1 = PALETTES[idx]
    src = f"gradients=s={W}x{H}:c0={c0}:c1={c1}:speed=0.015:r={FPS}:d={duration + 1:.2f}"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", src, "-t", f"{duration + 0.5:.2f}",
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(dest)], check=True)
    return dest


def background_for_beat(query: str, duration: float, dest_dir: Path, index: int,
                        pexels_key: str | None, used_ids: set[int]) -> tuple[Path, str]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    if pexels_key:
        clip = pexels_clip(query, pexels_key, dest_dir / f"bg_{index:02d}_src.mp4", used_ids)
        if clip:
            return clip, "pexels"
    return gradient_clip(query, duration, dest_dir / f"bg_{index:02d}_src.mp4"), "gradient"
