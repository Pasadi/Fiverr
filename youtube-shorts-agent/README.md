# YouTube Shorts Niche Agent

An end-to-end pipeline that:

1. **Finds niches**: searches YouTube for recent Shorts in each candidate niche and ranks them by
   demand (views/day), how often small channels go viral (views ÷ subscribers), engagement,
   and competition.
2. **Writes the script**: Claude writes a 40–50 second script built for retention (hook in the
   first second, an open loop, an ending that loops back), plus a search-optimised title,
   description, tags, hashtags and a pinned-comment prompt. It works from real YouTube
   autocomplete searches and the best-performing competitor titles.
3. **Makes the voiceover**: natural neural voice via `edge-tts`, with timings for every word.
4. **Draws the visuals**: Claude invents a recurring cartoon character for the topic (for example
   *Ollie*, a purple octopus in a sailor cap, for octopus facts). For every line of the script it
   draws Ollie acting out exactly what's being said, with a funny twist: juggling three heart
   balloons for "three hearts", sipping a juice box labelled *Cu* for "copper blood", and so on.
   The art is SVG drawn by Claude, so no extra image API or key is needed.
5. **Renders the video**: 1080×1920, 30 fps, H.264/AAC. The character pops in, bobs and sways
   over each scene, with word-by-word highlighted captions, a headline per beat, a progress bar,
   and optional background music. Use `--visuals stock` for Pexels footage instead.
6. **Publishes it**: uploads to your channel with the title, description and tags, uploads an
   SRT caption track (YouTube indexes it for search), posts the engagement comment, and adds
   the video to a playlist for the niche.

## How it helps search and engagement

| Feature | Why it matters |
|---|---|
| Primary keyword taken from real YouTube autocomplete | Ranks for what people actually type |
| Keyword at the start of the title, spoken in the first beat, used in description and tags | Title, transcript and metadata all match |
| Uploaded SRT captions | Lets YouTube read the whole transcript |
| `#Shorts` plus niche hashtags | The first 3 hashtags show above the title |
| Niche playlists | More ways to be found, and viewers watch several videos in a row |
| Comment question in the narration, description and first comment | More comments, which helps ranking |
| Looping ending, progress bar, captions that pop word by word | Better watch-through and rewatch rates |
| `--interactive` mode | You choose the niche, approve or revise the script, and edit the title before upload |

## Setup

Requires Python 3.10+ and `ffmpeg` (with libass, which most builds include). The SVG art is rendered with
`cairosvg`, which needs the Cairo library (`brew install cairo`, `apt install libcairo2`; on Windows
install GTK3 runtime or Playwright's Chromium, which is used as a fallback).

```bash
cd youtube-shorts-agent
pip install -r requirements.txt
cp .env.example .env   # then fill in the keys
```

### 1. Claude API key
Get one at https://console.anthropic.com/ and set `ANTHROPIC_API_KEY` in `.env`.

### 2. YouTube Data API key (research)
1. Go to https://console.cloud.google.com/ and create a project.
2. Enable **YouTube Data API v3** (APIs & Services → Library).
3. Go to Credentials → Create credentials → **API key**, then put it in `YOUTUBE_API_KEY`.

### 3. OAuth client (uploading to your channel)
1. In the same project, open the **OAuth consent screen**. Choose External and add your Google
   account as a test user.
2. Go to Credentials → Create credentials → **OAuth client ID** → *Desktop app*.
3. Download the JSON and save it as `client_secret.json` in this folder.
4. On the first upload a browser opens. Pick the channel's account, and `token.json` is saved
   for later runs.

> Videos uploaded through an **unverified** API project are locked to *private* by YouTube.
> To publish publicly, submit your project for the YouTube API audit
> (https://support.google.com/youtube/contact/yt_api_form). Until it's approved, upload with
> `--privacy private` and switch videos to public in YouTube Studio.

### 4. Optional: Pexels key (only for `--visuals stock`)
A free key from https://www.pexels.com/api/ goes in `PEXELS_API_KEY`.

## Usage

```bash
# Rank the built-in seed niches
python -m shorts_agent research

# Let Claude suggest 20 niches (optionally steered), then rank them
python -m shorts_agent research --brainstorm 20 --interests "science, money"

# Make a Short for the top-ranked niche (renders to output/<timestamp>_<niche>/short.mp4)
python -m shorts_agent create

# Choose the niche and approve or revise the script yourself
python -m shorts_agent create --interactive

# Reuse saved research and make Shorts for the top 3 niches
python -m shorts_agent create --research output/research_20261122_120000.json --count 3

# Make a Short for a niche you choose
python -m shorts_agent create --niche "octopus facts"

# Stock footage instead of cartoons
python -m shorts_agent create --visuals stock

# Re-render using art from an earlier run (no new Claude art calls)
python -m shorts_agent create --script-file output/<run>/script.json --art-dir output/<run>/art

# Upload a rendered Short
python -m shorts_agent upload output/20261122_194200_octopus-facts --privacy public

# Do everything in one go (research → script → video → upload)
python -m shorts_agent run --privacy public
python -m shorts_agent run --interactive
python -m shorts_agent run --publish-at 2026-12-01T15:00:00Z   # scheduled premiere
```

Each run folder contains `script.json`, `art/` (character and scene SVGs and PNGs), `metadata.json` (title, description, tags),
`captions.srt`/`.ass`, `short.mp4`, and a `work/` folder of intermediate files.
`output/history.json` keeps track of published titles so Claude doesn't repeat an angle.

### Try it without any API keys
```bash
python -m shorts_agent create --niche "octopus facts" --script-file examples/sample_script.json --art-dir examples/octopus_art
```

### Post every day
Use cron (or Task Scheduler on Windows), for example every day at 15:00:
```
0 15 * * * cd /path/to/youtube-shorts-agent && python -m shorts_agent run --privacy public >> agent.log 2>&1
```

## Quotas and costs
- **YouTube Data API**: 10,000 units/day by default. Research costs about 100 units per niche
  (15 niches ≈ 1,500). Uploads cost a lot more (video insert, captions 400, comment 50,
  playlist 50–100), so only a few uploads fit in a day. You can ask Google for more quota.
- **Claude**: per Short, one call for the script, one for the character, and one per scene
  (6–8, run in parallel). The default model is `claude-opus-5-5`; set `CLAUDE_MODEL` to change it.
  The SVG art is the largest part of the cost. Requests use server-side fallback, so a request declined by a
  safety filter is retried on a fallback model automatically.
- **edge-tts, Pexels and autocomplete** are free.

## Notes and policies
- Uploads are marked `containsSyntheticMedia: true` because the voice is AI-generated. YouTube
  asks creators to disclose AI-generated content.
- YouTube's monetisation rules require **original, valuable content**. Repetitive, mass-produced
  videos can get a channel demonetised. Use `--interactive`, check facts, and add your own touch.
- The API can't pin comments. Pin the posted comment in YouTube Studio.
- If `edge-tts` can't be reached, the agent falls back to `espeak-ng` (robotic, offline) if it's installed.

## Project layout
```
shorts_agent/
  research.py     YouTube search + niche scoring
  seo.py          autocomplete keywords, title/description/tag builders
  scriptwriter.py Claude: niche brainstorming + structured script generation
  tts.py          edge-tts voiceover with word timings (espeak-ng fallback)
  visuals.py      Pexels footage / gradient backgrounds
  art.py          Claude-drawn cartoon character + scenes (SVG → PNG, sanitised)
  render.py       ffmpeg assembly, animated ASS captions, SRT
  uploader.py     OAuth, upload, captions, comment, playlist
  cli.py          research / create / upload / run commands
```
