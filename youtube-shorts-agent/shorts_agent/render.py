"""Assemble a vertical 1080x1920 Short: per-beat voiceover + backgrounds + animated captions."""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import tts, visuals
from .scriptwriter import ShortScript

W, H, FPS = visuals.W, visuals.H, visuals.FPS
BEAT_GAP = 0.12          # pause between beats (seconds)
MAX_SHORT_SECONDS = 59.5


def _ff(args: list[str], cwd: Path | None = None) -> None:
    proc = subprocess.run(["ffmpeg", "-y", "-v", "error", *args], cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {proc.stderr[-1500:]}")


# ---------------------------------------------------------------- captions --

@dataclass
class Chunk:
    words: list[tts.Word]

    @property
    def start(self) -> float:
        return self.words[0].start

    @property
    def end(self) -> float:
        return self.words[-1].end


def chunk_words(words: list[tts.Word], max_words: int = 3, max_chars: int = 18) -> list[Chunk]:
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or len(" ".join(x.text for x in cur + [w])) > max_chars):
            chunks.append(Chunk(cur))
            cur = []
        cur.append(w)
        if w.text[-1:] in ".!?,;:":
            chunks.append(Chunk(cur))
            cur = []
    if cur:
        chunks.append(Chunk(cur))
    return chunks


def _ass_time(t: float) -> str:
    t = max(t, 0)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _srt_time(t: float) -> str:
    ms = int(round(max(t, 0) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _ass_text(s: str) -> str:
    return re.sub(r"[{}\\]", "", s).replace("\n", " ").strip()


def _wrap(text: str, width: int = 16) -> str:
    lines, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    return r"\N".join(lines)


def build_ass(words: list[tts.Word], headlines: list[tuple[float, float, str]], font: str) -> str:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font},88,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,3,5,60,140,0,1
Style: Headline,{font},70,&H00FFFFFF,&H00FFFFFF,&H00000000,&HB4000000,-1,0,0,0,100,100,0,0,3,18,0,8,80,80,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for start, end, text in headlines:
        events.append(f"Dialogue: 1,{_ass_time(start)},{_ass_time(end)},Headline,,0,0,0,,"
                      rf"{{\pos({W // 2},300)\fad(150,100)}}{_wrap(_ass_text(text).upper())}")
    highlight = r"{\c&H0000D4FF&}"
    white = r"{\c&H00FFFFFF&}"
    for chunk in chunk_words(words):
        n = len(chunk.words)
        for i, w in enumerate(chunk.words):
            start = w.start
            end = chunk.words[i + 1].start if i + 1 < n else chunk.end + 0.08
            pieces = []
            for j, x in enumerate(chunk.words):
                t = _ass_text(x.text).upper()
                pieces.append(f"{highlight}{t}{white}" if j == i else t)
            pop = r"\fscx85\fscy85\t(0,90,\fscx100\fscy100)" if i == 0 else ""
            events.append(f"Dialogue: 2,{_ass_time(start)},{_ass_time(end)},Caption,,0,0,0,,"
                          rf"{{\pos({W // 2 - 40},1180){pop}}}" + " ".join(pieces))
    return header + "\n".join(events) + "\n"


def build_srt(words: list[tts.Word]) -> str:
    out = []
    for i, ch in enumerate(chunk_words(words, max_words=7, max_chars=42), 1):
        out.append(f"{i}\n{_srt_time(ch.start)} --> {_srt_time(ch.end + 0.05)}\n"
                   + " ".join(w.text for w in ch.words) + "\n")
    return "\n".join(out)


# ------------------------------------------------------------------- video --

def build_short(script: ShortScript, run_dir: Path, *, voice: str, font: str,
                pexels_key: str | None = None, music: Path | None = None, log=print) -> dict:
    work = run_dir / "work"
    work.mkdir(parents=True, exist_ok=True)

    # 1) voiceover, one file per beat so beat timing is exact
    speeches, all_words, headlines = [], [], []
    t = 0.0
    for i, beat in enumerate(script.beats):
        sp = tts.synthesize(beat.narration.strip(), work / f"voice_{i:02d}", voice)
        speeches.append(sp)
        dur = sp.duration + BEAT_GAP
        all_words += [tts.Word(w.text, w.start + t, w.end + t) for w in sp.words]
        headlines.append((t, t + dur, beat.on_screen_text))
        t += dur
    total = t
    log(f"  voiceover: {total:.1f}s via {speeches[0].engine}")
    if total > MAX_SHORT_SECONDS:
        log(f"  ! narration is {total:.1f}s; Shorts over 60s get less reach. Consider a shorter script.")

    inputs, filt = [], []
    for i, sp in enumerate(speeches):
        inputs += ["-i", str(sp.audio_path)]
        filt.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=mono,apad=pad_dur={BEAT_GAP}[a{i}]")
    filt.append("".join(f"[a{i}]" for i in range(len(speeches))) + f"concat=n={len(speeches)}:v=0:a=1[out]")
    voice_path = work / "voice.m4a"
    _ff([*inputs, "-filter_complex", ";".join(filt), "-map", "[out]", "-c:a", "aac", "-b:a", "192k",
         str(voice_path)])

    # 2) one background segment per beat, with a slow pan
    used: set[int] = set()
    segments, sources = [], []
    for i, (beat, (start, end, _)) in enumerate(zip(script.beats, headlines)):
        dur = end - start
        src, kind = visuals.background_for_beat(beat.visual_query, dur, work, i, pexels_key, used)
        sources.append(kind)
        seg = work / f"seg_{i:02d}.mp4"
        vf = (f"scale={int(W * 1.12)}:{int(H * 1.12)}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H}:x='(iw-ow)*t/{dur:.3f}':y='(ih-oh)/2',fps={FPS},"
              "eq=brightness=-0.07:saturation=1.12,format=yuv420p")
        _ff(["-stream_loop", "-1", "-i", str(src), "-t", f"{dur:.3f}", "-vf", vf, "-an",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", str(seg)])
        segments.append(seg)
    concat_list = work / "segments.txt"
    concat_list.write_text("".join(f"file '{s.name}'\n" for s in segments), encoding="utf-8")
    bg_path = work / "background.mp4"
    _ff(["-f", "concat", "-safe", "0", "-i", concat_list.name, "-c", "copy", bg_path.name], cwd=work)
    log(f"  backgrounds: {', '.join(sorted(set(sources)))}")

    # 3) captions
    ass_path = run_dir / "captions.ass"
    srt_path = run_dir / "captions.srt"
    ass_path.write_text(build_ass(all_words, headlines, font), encoding="utf-8")
    srt_path.write_text(build_srt(all_words), encoding="utf-8")

    # 4) final mix: captions + progress bar + voice (+ optional music bed)
    out = run_dir / "short.mp4"
    args = ["-i", str(bg_path.relative_to(run_dir)), "-i", str(voice_path.relative_to(run_dir))]
    vchain = (f"[0:v]ass={ass_path.name}[cap];color=c=0xFFD400:s={W}x12:r={FPS}[bar];"
              f"[cap][bar]overlay=x='-W+W*t/{total:.3f}':y=0:shortest=1[v]")
    if music:
        args += ["-stream_loop", "-1", "-i", str(Path(music).resolve())]
        achain = ("[2:a]volume=0.12,aresample=48000[m];[1:a]aresample=48000[vo];"
                  "[vo][m]amix=inputs=2:duration=first:dropout_transition=0[a]")
    else:
        achain = "[1:a]aresample=48000[a]"
    _ff([*args, "-filter_complex", f"{vchain};{achain}", "-map", "[v]", "-map", "[a]",
         "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
         "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out.name], cwd=run_dir)

    info = {"video": str(out), "captions_srt": str(srt_path), "duration_s": round(total, 2),
            "tts_engine": speeches[0].engine, "backgrounds": sources}
    (run_dir / "render.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    return info
