"""Command line entry point.

  python -m shorts_agent research            # rank niches
  python -m shorts_agent create              # script + voice + video for the best niche
  python -m shorts_agent upload output/<run> # publish a rendered Short
  python -m shorts_agent run                 # all of the above
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from . import render, research, scriptwriter, seo
from .config import DEFAULT_SEED_NICHES, Settings
from .scriptwriter import ShortScript


def log(msg: str) -> None:
    print(msg, flush=True)


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "short"


def ask(prompt: str, default: str = "") -> str:
    try:
        ans = input(f"{prompt} " + (f"[{default}] " if default else "")).strip()
    except EOFError:
        ans = ""
    return ans or default


def history_path(s: Settings) -> Path:
    return s.output_dir / "history.json"


def load_history(s: Settings) -> list[dict]:
    p = history_path(s)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def append_history(s: Settings, entry: dict) -> None:
    h = load_history(s)
    h.append(entry)
    history_path(s).parent.mkdir(parents=True, exist_ok=True)
    history_path(s).write_text(json.dumps(h, indent=2), encoding="utf-8")


# ------------------------------------------------------------------ steps --

def step_research(s: Settings, args) -> list[research.NicheReport]:
    if not s.youtube_api_key:
        sys.exit("YOUTUBE_API_KEY is not set (see .env.example).")
    if args.seeds:
        niches = [l.strip() for l in Path(args.seeds).read_text(encoding="utf-8").splitlines()
                  if l.strip() and not l.startswith("#")]
    elif args.brainstorm:
        log(f"Asking Claude for {args.brainstorm} niche ideas...")
        niches = scriptwriter.brainstorm_niches(s.claude_model, args.brainstorm, args.interests)
    else:
        niches = list(DEFAULT_SEED_NICHES)
    log(f"Researching {len(niches)} niches (Shorts from the last {args.days} days)...")
    reports = research.research_niches(niches, s.youtube_api_key, days=args.days, region=s.region_code,
                                       language=s.language, log=log)
    path = research.save_reports(reports, s.output_dir / f"research_{datetime.now():%Y%m%d_%H%M%S}.json")
    log("\n" + research.format_table(reports))
    log(f"\nSaved {path}")
    return reports


def pick_reports(s: Settings, args) -> list[dict]:
    """Return niche report dicts to make videos for."""
    if args.niche:
        if s.youtube_api_key:
            videos, total = research.fetch_shorts(args.niche, s.youtube_api_key, region=s.region_code,
                                                  language=s.language)
            rep = research.summarize(args.niche, videos, total)
        else:
            rep = research.NicheReport(args.niche, 0, 0, 0, 0, 0, 0)
        rep.keywords = seo.autocomplete_keywords(args.niche, s.language)
        return [rep.to_dict()]
    if args.research:
        reports = research.load_reports(Path(args.research))
    else:
        reports = step_research(s, args)
    reports = [r for r in reports if r.sample_size]
    if not reports:
        sys.exit("No niche data available.")
    if args.interactive:
        choice = ask(f"\nPick niche number(s), comma separated (1-{len(reports)}):", "1")
        idx = [int(x) - 1 for x in choice.split(",") if x.strip().isdigit()]
        return [reports[i].to_dict() for i in idx if 0 <= i < len(reports)]
    return [r.to_dict() for r in reports[: args.count]]


def print_script(sc: ShortScript) -> None:
    log(f"\n  TITLE: {sc.title}\n  KEYWORD: {sc.primary_keyword}")
    for i, b in enumerate(sc.beats, 1):
        log(f"  {i}. [{b.on_screen_text}] {b.narration}")
    log(f"  CTA: {sc.cta_question}\n  PINNED COMMENT: {sc.pinned_comment}\n")


def step_create(s: Settings, args, report: dict) -> Path:
    run_dir = s.output_dir / f"{datetime.now():%Y%m%d_%H%M%S}_{slugify(report['niche'])}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "research.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    if args.script_file:
        sc = ShortScript.model_validate_json(Path(args.script_file).read_text(encoding="utf-8"))
    else:
        avoid = [h["title"] for h in load_history(s) if h.get("niche") == report["niche"]][-20:]
        log(f"Writing script for '{report['niche']}' with {s.claude_model}...")
        sc = scriptwriter.write_script(s.claude_model, report, avoid)
        while args.interactive:
            print_script(sc)
            choice = ask("Use this script? (y = yes, r = regenerate, or type revision notes):", "y")
            if choice.lower() in ("y", "yes"):
                break
            sc = scriptwriter.write_script(s.claude_model, report, avoid,
                                           feedback=None if choice.lower() == "r" else choice)
    if not args.interactive:
        print_script(sc)
    (run_dir / "script.json").write_text(sc.model_dump_json(indent=2), encoding="utf-8")

    keywords = report.get("keywords", [])
    metadata = {
        "title": seo.build_title(sc.title),
        "description": seo.build_description(sc.hook, sc.description_body, sc.cta_question, keywords, sc.hashtags),
        "tags": seo.build_tags([sc.primary_keyword], sc.tags, keywords, report.get("common_tags", [])),
        "category_id": sc.category_id,
        "pinned_comment": sc.pinned_comment,
        "playlist": report["niche"].title(),
        "niche": report["niche"],
    }
    (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    art_pngs = None
    if args.visuals == "cartoon":
        from . import art

        art_dir = run_dir / "art"
        if args.art_dir:
            shutil.copytree(args.art_dir, art_dir, dirs_exist_ok=True)
        log("Drawing cartoon scenes...")
        art_pngs = art.generate_art(s.claude_model, sc, art_dir, log=log)

    log("Rendering video...")
    info = render.build_short(sc, run_dir, voice=s.tts_voice, font=s.caption_font,
                              pexels_key=s.pexels_api_key if args.visuals == "stock" else None,
                              music=Path(args.music) if args.music else None, art=art_pngs, log=log)
    log(f"Done: {info['video']} ({info['duration_s']}s)")
    return run_dir


def step_upload(s: Settings, args, run_dir: Path) -> str | None:
    from . import uploader  # google libs only needed here

    meta = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    video = run_dir / "short.mp4"
    if args.interactive:
        log(f"\n  Title: {meta['title']}\n  Tags: {', '.join(meta['tags'][:10])}...")
        new_title = ask("Press Enter to keep the title, or type a new one:")
        if new_title:
            meta["title"] = seo.build_title(new_title)
        if ask(f"Upload {video} as {args.privacy}? (y/n)", "y").lower() not in ("y", "yes"):
            log("Skipped upload.")
            return None
    yt = uploader.get_service(s.client_secrets_file, s.token_file)
    log("Uploading to YouTube...")
    vid = uploader.upload_video(yt, video, title=meta["title"], description=meta["description"], tags=meta["tags"],
                                category_id=meta["category_id"], language=s.language, privacy=args.privacy,
                                publish_at=args.publish_at, log=log)
    url = f"https://youtube.com/shorts/{vid}"
    log(f"  uploaded: {url}")
    for label, fn in (
        ("captions", lambda: uploader.upload_captions(yt, vid, run_dir / "captions.srt", s.language)),
        ("comment", None if args.no_comment else lambda: uploader.post_comment(yt, vid, meta["pinned_comment"])),
        ("playlist", None if args.no_playlist else lambda: uploader.add_to_playlist(yt, vid, meta["playlist"])),
    ):
        if fn is None:
            continue
        try:
            fn()
            log(f"  + {label}")
        except Exception as exc:  # non-fatal extras
            log(f"  ! {label} failed: {exc}")
    if not args.no_comment:
        log("  Tip: pin the comment in YouTube Studio (the API cannot pin comments).")
    meta.update({"video_id": vid, "url": url, "uploaded_at": datetime.now().isoformat(timespec="seconds")})
    (run_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    append_history(s, {"niche": meta["niche"], "title": meta["title"], "url": url, "uploaded_at": meta["uploaded_at"]})
    return url


# ------------------------------------------------------------------- main --

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="shorts_agent", description="YouTube Shorts niche research + auto-publishing agent")
    sub = p.add_subparsers(dest="cmd", required=True)

    def research_opts(sp):
        sp.add_argument("--seeds", help="text file with one niche per line")
        sp.add_argument("--brainstorm", type=int, metavar="N", help="let Claude propose N niches to research")
        sp.add_argument("--interests", help="steer brainstorming, e.g. 'science, money'")
        sp.add_argument("--days", type=int, default=30, help="only count Shorts published in the last N days")

    def create_opts(sp):
        sp.add_argument("--niche", help="skip ranking and make a Short for this niche")
        sp.add_argument("--research", help="reuse a saved research_*.json instead of re-querying")
        sp.add_argument("--count", type=int, default=1, help="make Shorts for the top N niches")
        sp.add_argument("--script-file", help="use an existing script.json instead of calling Claude")
        sp.add_argument("--visuals", choices=["cartoon", "stock", "gradient"], default="cartoon",
                        help="cartoon: Claude-drawn character scenes (default); stock: Pexels footage; gradient: plain")
        sp.add_argument("--art-dir", help="reuse SVG art from a previous run's art/ folder (or examples/)")
        sp.add_argument("--music", help="optional background music file (mixed quietly under the voice)")
        sp.add_argument("-i", "--interactive", action="store_true", help="choose niches and approve scripts yourself")

    def upload_opts(sp):
        sp.add_argument("--privacy", choices=["public", "unlisted", "private"], default="public")
        sp.add_argument("--publish-at", help="schedule, ISO 8601 UTC e.g. 2026-12-01T15:00:00Z")
        sp.add_argument("--no-comment", action="store_true", help="don't post the engagement comment")
        sp.add_argument("--no-playlist", action="store_true", help="don't add to a niche playlist")

    r = sub.add_parser("research", help="rank niches by opportunity")
    research_opts(r)

    c = sub.add_parser("create", help="write script, generate voice and render the Short")
    research_opts(c)
    create_opts(c)

    u = sub.add_parser("upload", help="upload a rendered run directory")
    u.add_argument("run_dir")
    u.add_argument("-i", "--interactive", action="store_true")
    upload_opts(u)

    a = sub.add_parser("run", help="research -> create -> upload")
    research_opts(a)
    create_opts(a)
    upload_opts(a)
    a.add_argument("--no-upload", action="store_true", help="stop after rendering")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    s = Settings.from_env()
    s.output_dir.mkdir(parents=True, exist_ok=True)

    if args.cmd == "research":
        step_research(s, args)
    elif args.cmd == "create":
        for rep in pick_reports(s, args):
            step_create(s, args, rep)
    elif args.cmd == "upload":
        step_upload(s, args, Path(args.run_dir))
    elif args.cmd == "run":
        for rep in pick_reports(s, args):
            run_dir = step_create(s, args, rep)
            if not args.no_upload:
                step_upload(s, args, run_dir)
    return 0
