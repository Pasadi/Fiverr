"""Settings loaded from environment variables (and an optional .env file)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: str | Path = ".env") -> None:
    """Minimal .env loader: KEY=VALUE lines; existing env vars win."""
    p = Path(path)
    if not p.is_file():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip().strip('"').strip("'")
        if value:
            os.environ.setdefault(key.strip(), value)


@dataclass
class Settings:
    youtube_api_key: str | None
    pexels_api_key: str | None
    client_secrets_file: Path
    token_file: Path
    output_dir: Path
    claude_model: str
    tts_voice: str
    region_code: str
    language: str
    caption_font: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        env = os.environ.get
        return cls(
            youtube_api_key=env("YOUTUBE_API_KEY") or None,
            pexels_api_key=env("PEXELS_API_KEY") or None,
            client_secrets_file=Path(env("YOUTUBE_CLIENT_SECRETS", "client_secret.json")),
            token_file=Path(env("YOUTUBE_TOKEN_FILE", "token.json")),
            output_dir=Path(env("OUTPUT_DIR", "output")),
            claude_model=env("CLAUDE_MODEL", "claude-opus-5-5"),
            tts_voice=env("TTS_VOICE", "en-US-AndrewMultilingualNeural"),
            region_code=env("REGION_CODE", "US"),
            language=env("LANGUAGE", "en"),
            caption_font=env("CAPTION_FONT", "DejaVu Sans"),
        )


# Starting points for research. Override with --seeds FILE or --brainstorm N.
DEFAULT_SEED_NICHES = [
    "psychology facts",
    "space facts",
    "history mysteries",
    "personal finance tips",
    "ai tools",
    "stoic quotes",
    "ocean creatures",
    "life hacks",
    "true crime stories",
    "ancient civilizations",
    "body facts",
    "productivity tips",
    "animal facts",
    "money mistakes",
    "geography facts",
]
