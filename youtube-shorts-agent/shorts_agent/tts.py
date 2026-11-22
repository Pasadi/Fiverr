"""Voiceover generation with word-level timings (for synced captions).

Primary engine: Microsoft Edge neural voices via `edge-tts` (free, natural sounding).
Fallback: `espeak-ng` (offline, robotic) with estimated word timings.
"""
from __future__ import annotations

import asyncio
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Word:
    text: str
    start: float  # seconds
    end: float


@dataclass
class Speech:
    audio_path: Path
    duration: float
    words: list[Word]
    engine: str


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def estimate_word_timings(text: str, duration: float, lead: float = 0.05) -> list[Word]:
    """Spread words over the audio proportionally to their length (+ pause weight for punctuation)."""
    tokens = text.split()
    if not tokens:
        return []
    weights = [len(t) + 2 + (3 if t[-1] in ".!?" else 1.5 if t[-1] in ",;:" else 0) for t in tokens]
    total = sum(weights)
    usable = max(duration - lead, 0.1)
    t, words = lead, []
    for tok, w in zip(tokens, weights):
        span = usable * w / total
        words.append(Word(tok, t, t + span * 0.92))
        t += span
    return words


async def _edge(text: str, voice: str, out: Path, rate: str) -> list[Word]:
    import edge_tts

    comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
    words: list[Word] = []
    with open(out, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7
                words.append(Word(chunk["text"], start, start + chunk["duration"] / 1e7))
    return words


def _attach_punctuation(text: str, words: list[Word]) -> list[Word]:
    """edge-tts boundaries drop punctuation; map them back onto the original tokens when counts match."""
    tokens = text.split()
    if len(tokens) == len(words):
        return [Word(tok, w.start, w.end) for tok, w in zip(tokens, words)]
    return words


def synthesize(text: str, out_base: Path, voice: str, rate: str = "+8%") -> Speech:
    out_base.parent.mkdir(parents=True, exist_ok=True)
    mp3 = out_base.with_suffix(".mp3")
    try:
        words = asyncio.run(_edge(text, voice, mp3, rate))
        if mp3.stat().st_size == 0:
            raise RuntimeError("edge-tts returned no audio")
        duration = probe_duration(mp3)
        words = _attach_punctuation(text, words) if words else estimate_word_timings(text, duration)
        return Speech(mp3, duration, words, "edge-tts")
    except Exception as exc:  # network blocked, service change, etc.
        mp3.unlink(missing_ok=True)
        espeak = shutil.which("espeak-ng") or shutil.which("espeak")
        if not espeak:
            raise RuntimeError(f"edge-tts failed ({exc}) and espeak-ng is not installed") from exc
        wav = out_base.with_suffix(".wav")
        subprocess.run([espeak, "-v", "en-us", "-s", "170", "-w", str(wav), text], check=True,
                       capture_output=True)
        duration = probe_duration(wav)
        return Speech(wav, duration, estimate_word_timings(text, duration), "espeak-ng")
