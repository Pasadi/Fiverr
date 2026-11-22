"""Search-optimisation helpers: YouTube autocomplete keywords, tags, titles, descriptions."""
from __future__ import annotations

import re

import requests

SUGGEST_URL = "https://suggestqueries.google.com/complete/search"


def autocomplete(query: str, language: str = "en") -> list[str]:
    """What people actually type into YouTube search (free, no key)."""
    try:
        r = requests.get(SUGGEST_URL, params={"client": "firefox", "ds": "yt", "q": query, "hl": language},
                         timeout=10)
        r.raise_for_status()
        data = r.json()
        return [s for s in data[1] if isinstance(s, str)]
    except Exception:
        return []


def autocomplete_keywords(niche: str, language: str = "en", limit: int = 25) -> list[str]:
    seen: dict[str, None] = {}
    for q in (niche, f"{niche} shorts", f"how {niche}", f"why {niche}", f"{niche} that"):
        for s in autocomplete(q, language):
            seen.setdefault(s.lower(), None)
        if len(seen) >= limit:
            break
    return list(seen)[:limit]


def clean_hashtag(tag: str) -> str:
    return "#" + re.sub(r"[^0-9A-Za-z_]", "", tag.lstrip("#"))


def build_tags(*groups: list[str], max_chars: int = 480) -> list[str]:
    """YouTube allows 500 characters of tags in total (quoted multi-word tags count extra)."""
    out: list[str] = []
    used = 0
    seen = set()
    for group in groups:
        for t in group:
            t = re.sub(r"[<>\"]", "", t.lstrip("#")).strip()
            if not t or t.lower() in seen or len(t) > 100:
                continue
            cost = len(t) + (2 if " " in t else 0) + 1
            if used + cost > max_chars:
                return out
            out.append(t)
            seen.add(t.lower())
            used += cost
    return out


def build_title(title: str) -> str:
    """Keep under YouTube's 100-char limit and add #Shorts when it fits."""
    title = re.sub(r"[<>]", "", title).strip()
    if "#shorts" not in title.lower() and len(title) + 8 <= 100:
        title = f"{title} #Shorts"
    return title[:100]


def build_description(hook: str, body: str, cta_question: str, keywords: list[str],
                      hashtags: list[str]) -> str:
    tags = [clean_hashtag(h) for h in hashtags if clean_hashtag(h) != "#"]
    if "#shorts" not in [t.lower() for t in tags]:
        tags.insert(0, "#Shorts")
    parts = [
        hook.strip(),
        "",
        body.strip(),
        "",
        f"\U0001F4AC {cta_question.strip()} Tell me in the comments!",
        "\U0001F514 Subscribe for a new Short every day.",
        "",
    ]
    if keywords:
        parts += ["Related searches: " + ", ".join(keywords[:12]), ""]
    parts.append(" ".join(tags[:15]))  # first 3 hashtags appear above the title
    desc = "\n".join(parts)
    return re.sub(r"[<>]", "", desc)[:5000]
