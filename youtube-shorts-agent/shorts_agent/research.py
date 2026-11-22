"""Niche research with the YouTube Data API v3.

For each candidate niche we pull recent, high-view Shorts and score the niche on:
  * demand       - median views per day of the top recent Shorts
  * outlier      - median views / subscribers (small channels winning = easy to break in)
  * engagement   - (likes + comments) / views
  * competition  - how many results the search returns (fewer is better)

Quota note: each niche costs ~102 units (search.list = 100). The default daily
quota is 10,000 units, so ~15 niches per run is comfortable.
"""
from __future__ import annotations

import json
import math
import re
import statistics
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from . import seo

YT_API = "https://www.googleapis.com/youtube/v3"


class YouTubeAPIError(RuntimeError):
    pass


@dataclass
class ShortVideo:
    video_id: str
    title: str
    channel_id: str
    channel_title: str
    views: int
    likes: int
    comments: int
    subscribers: int
    duration_s: int
    age_days: float
    tags: list[str] = field(default_factory=list)

    @property
    def views_per_day(self) -> float:
        return self.views / max(self.age_days, 1.0)

    @property
    def outlier_ratio(self) -> float:
        return self.views / max(self.subscribers, 100)


@dataclass
class NicheReport:
    niche: str
    total_results: int
    sample_size: int
    median_views: float
    median_views_per_day: float
    median_outlier_ratio: float
    engagement_rate: float
    score: float = 0.0
    top_videos: list[dict] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    common_tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _get(endpoint: str, params: dict, api_key: str) -> dict:
    resp = requests.get(f"{YT_API}/{endpoint}", params={**params, "key": api_key}, timeout=30)
    if resp.status_code != 200:
        try:
            msg = resp.json()["error"]["message"]
        except Exception:
            msg = resp.text[:300]
        raise YouTubeAPIError(f"{endpoint}: HTTP {resp.status_code}: {msg}")
    return resp.json()


_DUR_RE = re.compile(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def parse_duration(iso: str) -> int:
    m = _DUR_RE.fullmatch(iso or "")
    if not m:
        return 0
    d, h, mi, s = (int(x) if x else 0 for x in m.groups())
    return d * 86400 + h * 3600 + mi * 60 + s


def _chunks(seq: list, n: int):
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def fetch_shorts(niche: str, api_key: str, *, days: int = 30, max_results: int = 25,
                 region: str = "US", language: str = "en") -> tuple[list[ShortVideo], int]:
    published_after = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    search = _get("search", {
        "part": "snippet",
        "q": f"{niche} #shorts",
        "type": "video",
        "videoDuration": "short",  # < 4 minutes
        "order": "viewCount",
        "publishedAfter": published_after,
        "maxResults": max_results,
        "regionCode": region,
        "relevanceLanguage": language,
    }, api_key)
    total = int(search.get("pageInfo", {}).get("totalResults", 0))
    ids = [it["id"]["videoId"] for it in search.get("items", []) if it.get("id", {}).get("videoId")]
    if not ids:
        return [], total

    videos_raw = _get("videos", {"part": "snippet,statistics,contentDetails", "id": ",".join(ids)}, api_key)["items"]
    channel_ids = list({v["snippet"]["channelId"] for v in videos_raw})
    subs: dict[str, int] = {}
    for batch in _chunks(channel_ids, 50):
        for ch in _get("channels", {"part": "statistics", "id": ",".join(batch)}, api_key).get("items", []):
            st = ch.get("statistics", {})
            subs[ch["id"]] = 0 if st.get("hiddenSubscriberCount") else int(st.get("subscriberCount", 0))

    now = datetime.now(timezone.utc)
    out: list[ShortVideo] = []
    for v in videos_raw:
        dur = parse_duration(v["contentDetails"].get("duration", ""))
        if dur == 0 or dur > 180:  # Shorts are <= 3 minutes
            continue
        sn, st = v["snippet"], v.get("statistics", {})
        published = datetime.fromisoformat(sn["publishedAt"].replace("Z", "+00:00"))
        out.append(ShortVideo(
            video_id=v["id"],
            title=sn["title"],
            channel_id=sn["channelId"],
            channel_title=sn["channelTitle"],
            views=int(st.get("viewCount", 0)),
            likes=int(st.get("likeCount", 0)),
            comments=int(st.get("commentCount", 0)),
            subscribers=subs.get(sn["channelId"], 0),
            duration_s=dur,
            age_days=max((now - published).total_seconds() / 86400, 0.5),
            tags=sn.get("tags", [])[:15],
        ))
    return out, total


def summarize(niche: str, videos: list[ShortVideo], total_results: int) -> NicheReport:
    if not videos:
        return NicheReport(niche, total_results, 0, 0, 0, 0, 0)
    views = sum(v.views for v in videos)
    tag_counts: dict[str, int] = {}
    for v in videos:
        for t in {t.lower() for t in v.tags}:
            tag_counts[t] = tag_counts.get(t, 0) + 1
    top = sorted(videos, key=lambda v: v.views_per_day, reverse=True)[:8]
    return NicheReport(
        niche=niche,
        total_results=total_results,
        sample_size=len(videos),
        median_views=statistics.median(v.views for v in videos),
        median_views_per_day=statistics.median(v.views_per_day for v in videos),
        median_outlier_ratio=statistics.median(v.outlier_ratio for v in videos),
        engagement_rate=(sum(v.likes + v.comments for v in videos) / views) if views else 0.0,
        top_videos=[{
            "title": v.title, "views": v.views, "views_per_day": round(v.views_per_day),
            "channel": v.channel_title, "subscribers": v.subscribers,
            "duration_s": v.duration_s, "url": f"https://youtube.com/shorts/{v.video_id}",
        } for v in top],
        common_tags=[t for t, _ in sorted(tag_counts.items(), key=lambda kv: -kv[1])[:20]],
    )


def score_reports(reports: list[NicheReport]) -> list[NicheReport]:
    """Min-max normalise each signal across niches and combine into a 0-100 score."""
    live = [r for r in reports if r.sample_size >= 5]
    if not live:
        return reports

    def norm(values: list[float]) -> list[float]:
        lo, hi = min(values), max(values)
        return [0.5 if hi == lo else (x - lo) / (hi - lo) for x in values]

    demand = norm([math.log10(r.median_views_per_day + 1) for r in live])
    outlier = norm([math.log10(r.median_outlier_ratio + 1) for r in live])
    engage = norm([r.engagement_rate for r in live])
    compete = norm([-math.log10(r.total_results + 1) for r in live])
    for r, d, o, e, c in zip(live, demand, outlier, engage, compete):
        r.score = round(100 * (0.40 * d + 0.30 * o + 0.15 * e + 0.15 * c), 1)
    return sorted(reports, key=lambda r: r.score, reverse=True)


def research_niches(niches: list[str], api_key: str, *, days: int = 30, region: str = "US",
                    language: str = "en", log=print) -> list[NicheReport]:
    reports = []
    for niche in niches:
        try:
            videos, total = fetch_shorts(niche, api_key, days=days, region=region, language=language)
        except YouTubeAPIError as exc:
            log(f"  ! {niche}: {exc}")
            if "quota" in str(exc).lower():
                break
            continue
        rep = summarize(niche, videos, total)
        rep.keywords = seo.autocomplete_keywords(niche, language=language)
        log(f"  - {niche:<28} {rep.sample_size:>2} shorts, median {rep.median_views_per_day:>10,.0f} views/day")
        reports.append(rep)
    return score_reports(reports)


def save_reports(reports: list[NicheReport], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([r.to_dict() for r in reports], indent=2), encoding="utf-8")
    return path


def load_reports(path: Path) -> list[NicheReport]:
    return [NicheReport(**d) for d in json.loads(Path(path).read_text(encoding="utf-8"))]


def format_table(reports: list[NicheReport]) -> str:
    lines = [f"{'#':>2}  {'Niche':<28} {'Score':>6} {'Views/day':>11} {'Outlier':>8} {'Engage':>7} {'Results':>9}",
             "-" * 78]
    for i, r in enumerate(reports, 1):
        lines.append(f"{i:>2}  {r.niche[:28]:<28} {r.score:>6.1f} {r.median_views_per_day:>11,.0f} "
                     f"{r.median_outlier_ratio:>7.1f}x {r.engagement_rate * 100:>6.1f}% {r.total_results:>9,}")
    return "\n".join(lines)
