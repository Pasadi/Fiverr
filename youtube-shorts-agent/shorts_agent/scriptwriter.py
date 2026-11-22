"""Claude-powered niche brainstorming and Shorts script writing (structured JSON output)."""
from __future__ import annotations

import json

import anthropic
from pydantic import BaseModel, Field

FALLBACK_BETA = "server-side-fallback-2026-07-01"

# YouTube category ids the model may choose from.
CATEGORIES = {
    "22": "People & Blogs", "27": "Education", "28": "Science & Technology",
    "24": "Entertainment", "26": "Howto & Style", "23": "Comedy", "17": "Sports",
    "20": "Gaming", "25": "News & Politics", "15": "Pets & Animals", "19": "Travel & Events",
}


class Beat(BaseModel):
    narration: str
    on_screen_text: str
    visual_query: str
    scene: str = ""  # the cartoon gag for this beat


class ShortScript(BaseModel):
    title: str
    primary_keyword: str
    character_name: str = "Pip"
    character_look: str = "a small round cartoon mascot with big eyes"
    hook: str
    beats: list[Beat] = Field(min_length=3)
    cta_question: str
    description_body: str
    tags: list[str]
    hashtags: list[str]
    pinned_comment: str
    category_id: str

    @property
    def full_narration(self) -> str:
        return " ".join(b.narration.strip() for b in self.beats)


_STR = {"type": "string"}
SCRIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Curiosity-driven, keyword-first title, max 70 chars, no hashtags"},
        "primary_keyword": {"type": "string", "description": "The main search phrase this Short should rank for"},
        "character_name": {"type": "string", "description": "Short, catchy name of the cartoon character who stars in every scene"},
        "character_look": {"type": "string", "description": "One-sentence visual design: species/object, colours, signature accessory"},
        "hook": {"type": "string", "description": "The first spoken sentence (also beats[0].narration's opening)"},
        "beats": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "narration": {"type": "string", "description": "Spoken words for this beat (1-2 short sentences)"},
                    "on_screen_text": {"type": "string", "description": "2-5 word headline shown on screen"},
                    "visual_query": {"type": "string", "description": "2-4 word stock-footage search query"},
                    "scene": {"type": "string", "description": "The cartoon gag: what the character is doing, wearing or holding, and the funny twist, in one or two sentences"},
                },
                "required": ["narration", "on_screen_text", "visual_query", "scene"],
                "additionalProperties": False,
            },
        },
        "cta_question": {"type": "string", "description": "A specific question viewers will want to answer in comments"},
        "description_body": {"type": "string", "description": "2-3 keyword-rich sentences summarising the Short"},
        "tags": {"type": "array", "items": _STR, "description": "12-20 search tags, broad to specific"},
        "hashtags": {"type": "array", "items": _STR, "description": "3-6 hashtags without spaces"},
        "pinned_comment": {"type": "string", "description": "First comment that sparks replies (question, poll-style A/B choice)"},
        "category_id": {"type": "string", "enum": list(CATEGORIES)},
    },
    "required": ["title", "primary_keyword", "character_name", "character_look", "hook", "beats", "cta_question", "description_body",
                 "tags", "hashtags", "pinned_comment", "category_id"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You are a YouTube Shorts strategist and scriptwriter who writes faceless, voiceover-driven Shorts that hold viewers to the end and rank in YouTube search.

How a strong Short is built:
- The hook is the first 1-2 seconds of audio. It states a surprising claim, a direct question, or a stake ("You've been doing X wrong"). No greetings, no channel intro.
- Total narration is 110-140 words (about 40-50 seconds spoken), split into 5-8 beats. Each beat is one idea, one or two short sentences, written for the ear: contractions, concrete numbers, no lists of clauses.
- Keep an open loop running (tease the best point, pay it off near the end), and make the last line flow back into the first so the Short loops and gets rewatched.
- End by asking the comment question naturally in the narration; the same question goes in cta_question.
- Every factual statement must be accurate and widely verifiable. If a popular "fact" is a myth, either skip it or debunk it. Never invent statistics, studies, or quotes.
- Search optimisation: put the primary keyword (a phrase from the real autocomplete data you are given) at the start of the title, say it out loud in the first beat, and use it in description_body and tags. Titles create curiosity without clickbait that the video doesn't deliver.
- Visuals are a cartoon. Invent one character who stars in every scene: ideally the topic itself made into a character (an octopus for octopus facts, a nervous piggy bank for money tips, a tiny planet for space facts), with a signature accessory that makes them memorable.
- For each beat, write a scene: the character acting out that exact line, so the picture matches what's being said, with a funny twist (an absurd prop, an exaggerated reaction, a visual pun, a role swap). Example for "the octopus has three hearts": the octopus juggling three tiny heart-shaped balloons, sweating nervously. Each gag should be different and drawable as a simple flat illustration.
- visual_query values are generic stock-footage searches (e.g. "deep ocean jellyfish", "city night timelapse"), never names of real people or brands.
- Don't copy titles or scripts from the competitor examples; use them only to understand what the audience responds to."""


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic()


def _call_json(model: str, system: str, user: str, schema: dict, effort: str = "high") -> dict:
    client = _client()
    response = client.beta.messages.create(
        model=model,
        max_tokens=16000,
        betas=[FALLBACK_BETA],
        fallbacks="default",  # server-side fallback if the request is declined by a safety classifier
        system=system,
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
        messages=[{"role": "user", "content": user}],
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Claude declined to write this script; try a different niche.")
    if response.stop_reason == "max_tokens":
        raise RuntimeError("Response was cut off (max_tokens).")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)


def write_script(model: str, report: dict, avoid_titles: list[str] | None = None,
                 feedback: str | None = None) -> ShortScript:
    """report is a NicheReport.to_dict()."""
    competitors = "\n".join(
        f'- "{v["title"]}" — {v["views"]:,} views ({v["views_per_day"]:,}/day), channel {v["subscribers"]:,} subs'
        for v in report.get("top_videos", [])
    ) or "(no competitor data)"
    keywords = ", ".join(report.get("keywords", [])) or "(none)"
    tags = ", ".join(report.get("common_tags", [])) or "(none)"
    user = f"""Write one YouTube Short for the niche: "{report['niche']}".

<research>
Top-performing recent Shorts in this niche:
{competitors}

Real YouTube autocomplete searches (pick the primary keyword from these when one fits):
{keywords}

Tags competitors use: {tags}
</research>
"""
    if avoid_titles:
        user += "\nAlready published on this channel, pick a different angle:\n" + "\n".join(f"- {t}" for t in avoid_titles) + "\n"
    if feedback:
        user += f"\nRevision notes from the channel owner: {feedback}\n"
    data = _call_json(model, SYSTEM_PROMPT, user, SCRIPT_SCHEMA)
    return ShortScript.model_validate(data)


BRAINSTORM_SCHEMA = {
    "type": "object",
    "properties": {"niches": {"type": "array", "items": _STR}},
    "required": ["niches"],
    "additionalProperties": False,
}


def brainstorm_niches(model: str, count: int, interests: str | None = None) -> list[str]:
    user = (f"List {count} distinct niche topics for a faceless, voiceover-based YouTube Shorts channel. "
            "Each should be a 2-4 word search phrase people actually type (e.g. 'psychology facts'), "
            "with evergreen demand and content that can be made from stock footage plus narration. "
            "Mix proven broad niches with narrower under-served ones.")
    if interests:
        user += f" Lean toward: {interests}."
    data = _call_json(model, "You are a YouTube growth researcher.", user, BRAINSTORM_SCHEMA, effort="medium")
    return [n.strip() for n in data["niches"] if n.strip()][:count]
