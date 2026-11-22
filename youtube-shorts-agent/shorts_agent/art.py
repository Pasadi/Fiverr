"""Cartoon visuals drawn by Claude as SVG.

1. Claude designs the channel's character once (character.svg).
2. For each beat, Claude redraws that same character acting out the line with a funny
   twist (beat_XX_char.svg, transparent) plus a matching background scene (beat_XX_bg.svg).
3. The SVGs are rasterised to PNG; render.py animates the character over the background.

Everything is cached in the run's art/ folder, so re-rendering costs nothing.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .scriptwriter import FALLBACK_BETA, ShortScript, _client

CHAR_BOX = 800          # character canvas (square, transparent)
BG_W, BG_H = 1080, 1920  # background canvas

STYLE_GUIDE = f"""Art style rules (follow exactly):
- Flat 2D cartoon, like a modern animated explainer: simple bold shapes, thick dark outlines (#1b1b1b, stroke-width 8-12, round joins/caps), saturated friendly colours, big expressive eyes.
- Valid standalone SVG with xmlns="http://www.w3.org/2000/svg" and an explicit viewBox. Keep it under ~250 elements.
- Allowed: path, circle, ellipse, rect, polygon, polyline, line, g, linearGradient, radialGradient, defs, use (internal #ids only), text (max 3 words, bold sans-serif, only when a sign or label is the joke).
- Not allowed: <image>, <script>, <foreignObject>, <filter>, <mask>, CSS @import, external links, embedded fonts or bitmaps.
- No real people, celebrities, brands, logos or copyrighted characters."""

CHARACTER_SCHEMA = {
    "type": "object",
    "properties": {"svg": {"type": "string", "description": "Complete SVG document"}},
    "required": ["svg"],
    "additionalProperties": False,
}

SCENE_SCHEMA = {
    "type": "object",
    "properties": {
        "background_svg": {"type": "string", "description": f"Full scene, viewBox 0 0 {BG_W} {BG_H}"},
        "character_svg": {"type": "string", "description": f"The character only, transparent, viewBox 0 0 {CHAR_BOX} {CHAR_BOX}"},
    },
    "required": ["background_svg", "character_svg"],
    "additionalProperties": False,
}


def _call(model: str, prompt: str, schema: dict) -> dict:
    with _client().beta.messages.stream(
        model=model,
        max_tokens=64000,
        betas=[FALLBACK_BETA],
        fallbacks="default",
        system="You are an illustrator who draws funny, clean cartoon art directly as SVG code.\n\n" + STYLE_GUIDE,
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason in ("refusal", "max_tokens"):
        raise RuntimeError(f"art generation stopped: {msg.stop_reason}")
    return json.loads(next(b.text for b in msg.content if b.type == "text"))


# ------------------------------------------------------------- sanitising --

_BAD_TAGS = {"script", "foreignObject", "image", "iframe", "object", "embed", "audio", "video", "filter", "mask"}


def sanitize_svg(svg: str) -> str:
    """Parse and strip anything that could load external resources or run code."""
    svg = svg.strip()
    svg = svg[svg.find("<svg"):] if "<svg" in svg else svg
    if re.search(r"<!DOCTYPE|<!ENTITY", svg, re.I):
        raise ValueError("DOCTYPE/ENTITY not allowed")
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    root = ET.fromstring(svg)
    if not root.tag.endswith("svg"):
        raise ValueError("root element is not <svg>")
    for parent in list(root.iter()):
        for child in list(parent):
            if child.tag.split("}")[-1] in _BAD_TAGS:
                parent.remove(child)
    for el in root.iter():
        for attr in list(el.attrib):
            name, val = attr.split("}")[-1], el.attrib[attr]
            if name.lower().startswith("on"):
                del el.attrib[attr]
            elif name == "href" and not val.startswith("#"):
                del el.attrib[attr]
            elif "url(" in val and not re.fullmatch(r"\s*url\(#[\w\-.:]+\)\s*", val):
                del el.attrib[attr]
        if el.tag.split("}")[-1] == "style" and el.text:
            el.text = re.sub(r"@import[^;]*;?|url\((?!#)[^)]*\)", "", el.text)
    return ET.tostring(root, encoding="unicode")


# ---------------------------------------------------------- rasterising --

def rasterize(svg_path: Path, png_path: Path, width: int, height: int) -> Path:
    """SVG -> PNG with cairosvg, falling back to rsvg-convert or Playwright's Chromium."""
    try:
        import cairosvg

        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=width, output_height=height,
                         unsafe=False)
        return png_path
    except (ImportError, OSError):
        pass
    if shutil.which("rsvg-convert"):
        subprocess.run(["rsvg-convert", "-w", str(width), "-h", str(height), "-o", str(png_path), str(svg_path)],
                       check=True)
        return png_path
    from playwright.sync_api import sync_playwright  # last resort

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.set_content(f"<html><body style='margin:0;background:transparent'>"
                         f"<img src='{svg_path.resolve().as_uri()}' width='{width}' height='{height}'></body></html>")
        page.screenshot(path=str(png_path), omit_background=True)
        browser.close()
    return png_path


# ------------------------------------------------------------ generation --

def _write_svg(path: Path, svg: str) -> None:
    path.write_text(sanitize_svg(svg), encoding="utf-8")


def design_character(model: str, script: ShortScript, out: Path) -> str:
    prompt = (f"Design the recurring character for a YouTube Shorts channel about \"{script.primary_keyword}\".\n"
              f"Character: {script.character_name}, {script.character_look}\n\n"
              f"Draw them front-facing in a neutral happy pose, centred, filling most of a transparent "
              f"{CHAR_BOX}x{CHAR_BOX} canvas (viewBox 0 0 {CHAR_BOX} {CHAR_BOX}). Give every body part a clear "
              "id (head, eyes, mouth, body, limbs) so it can be re-posed later.")
    svg = _call(model, prompt, CHARACTER_SCHEMA)["svg"]
    _write_svg(out, svg)
    return out.read_text(encoding="utf-8")


def draw_scene(model: str, script: ShortScript, index: int, base_svg: str, art_dir: Path) -> None:
    beat = script.beats[index]
    prompt = f"""Draw beat {index + 1} of {len(script.beats)} of a funny YouTube Short about "{script.primary_keyword}".

Narration for this beat: "{beat.narration}"
Visual gag to draw: {beat.scene or "the character acting out this line literally, with a funny exaggerated twist"}

Here is the character's model sheet. Keep the same colours, proportions and features so they are
recognisable, but change the pose, expression and props to act out the gag:
<character_svg>
{base_svg}
</character_svg>

Return two SVGs:
1. character_svg: only {script.character_name} with any props they hold or wear, on a TRANSPARENT
   background, viewBox 0 0 {CHAR_BOX} {CHAR_BOX}, character centred and filling about 85% of the canvas.
2. background_svg: a full-bleed setting that fits the narration (viewBox 0 0 {BG_W} {BG_H}, no
   transparent areas). Use slightly softer colours than the character so they stand out. The character
   will be placed over the region x 140-940, y 600-1360, so keep that region simple. Put supporting jokes
   (signs, side characters, objects) around it. Keep y 0-420 and y 1380-1540 visually calm because
   headline text and captions go there."""
    data = _call(model, prompt, SCENE_SCHEMA)
    _write_svg(art_dir / f"beat_{index:02d}_bg.svg", data["background_svg"])
    _write_svg(art_dir / f"beat_{index:02d}_char.svg", data["character_svg"])


def generate_art(model: str, script: ShortScript, art_dir: Path, log=print, workers: int = 4) -> list[tuple[Path, Path]]:
    """Return [(background_png, character_png)] per beat, generating only what's missing."""
    art_dir.mkdir(parents=True, exist_ok=True)
    base = art_dir / "character.svg"
    if not base.exists():
        log(f"  designing character: {script.character_name}")
        design_character(model, script, base)
    base_svg = base.read_text(encoding="utf-8")

    todo = [i for i in range(len(script.beats))
            if not (art_dir / f"beat_{i:02d}_bg.svg").exists() or not (art_dir / f"beat_{i:02d}_char.svg").exists()]
    if todo:
        log(f"  drawing {len(todo)} scenes...")

        def job(i: int) -> None:
            for attempt in range(2):
                try:
                    draw_scene(model, script, i, base_svg, art_dir)
                    return
                except (ValueError, ET.ParseError, json.JSONDecodeError) as exc:
                    if attempt:
                        log(f"  ! scene {i + 1} failed ({exc}); using the base character")
                        shutil.copy(base, art_dir / f"beat_{i:02d}_char.svg")

        with ThreadPoolExecutor(max_workers=workers) as pool:
            list(pool.map(job, todo))

    out = []
    for i in range(len(script.beats)):
        bg_svg, ch_svg = art_dir / f"beat_{i:02d}_bg.svg", art_dir / f"beat_{i:02d}_char.svg"
        bg_png = bg_svg.with_suffix(".png") if bg_svg.exists() else None
        if bg_png:
            rasterize(bg_svg, bg_png, BG_W, BG_H)
        ch_png = rasterize(ch_svg, ch_svg.with_suffix(".png"), CHAR_BOX, CHAR_BOX)
        out.append((bg_png, ch_png))
    return out
