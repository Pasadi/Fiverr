"""Upload to YouTube with the Data API v3 (OAuth), then add captions, a comment and a playlist."""
from __future__ import annotations

import random
import time
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",  # captions, comments, playlists
]
RETRYABLE = {500, 502, 503, 504}


def get_service(client_secrets: Path, token_file: Path):
    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not client_secrets.exists():
                raise FileNotFoundError(
                    f"{client_secrets} not found. Create an OAuth client (Desktop app) in Google Cloud "
                    "Console and download its JSON there. See README.md.")
            flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), SCOPES)
            creds = flow.run_local_server(port=0, open_browser=True)
        token_file.write_text(creds.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload_video(yt, video: Path, *, title: str, description: str, tags: list[str], category_id: str,
                 language: str = "en", privacy: str = "public", publish_at: str | None = None,
                 synthetic_media: bool = True, log=print) -> str:
    status = {
        "privacyStatus": "private" if publish_at else privacy,
        "selfDeclaredMadeForKids": False,
        "containsSyntheticMedia": synthetic_media,
    }
    if publish_at:
        status["publishAt"] = publish_at  # ISO 8601, e.g. 2026-12-01T15:00:00Z
    body = {
        "snippet": {"title": title, "description": description, "tags": tags, "categoryId": category_id,
                    "defaultLanguage": language, "defaultAudioLanguage": language},
        "status": status,
    }
    media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    response, attempt = None, 0
    while response is None:
        try:
            status_, response = request.next_chunk()
            if status_:
                log(f"  uploading... {int(status_.progress() * 100)}%")
        except HttpError as e:
            if e.resp.status not in RETRYABLE or attempt >= 6:
                raise
            attempt += 1
            time.sleep(min(2 ** attempt + random.random(), 60))
    return response["id"]


def upload_captions(yt, video_id: str, srt: Path, language: str = "en") -> None:
    yt.captions().insert(
        part="snippet",
        body={"snippet": {"videoId": video_id, "language": language, "name": "", "isDraft": False}},
        media_body=MediaFileUpload(str(srt), mimetype="application/octet-stream"),
    ).execute()


def post_comment(yt, video_id: str, text: str) -> str:
    resp = yt.commentThreads().insert(
        part="snippet",
        body={"snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": text}}}},
    ).execute()
    return resp["id"]


def add_to_playlist(yt, video_id: str, playlist_title: str, description: str = "") -> str:
    playlist_id = None
    req = yt.playlists().list(part="snippet", mine=True, maxResults=50)
    while req is not None and playlist_id is None:
        resp = req.execute()
        for p in resp.get("items", []):
            if p["snippet"]["title"].lower() == playlist_title.lower():
                playlist_id = p["id"]
                break
        req = yt.playlists().list_next(req, resp)
    if playlist_id is None:
        playlist_id = yt.playlists().insert(
            part="snippet,status",
            body={"snippet": {"title": playlist_title[:150], "description": description[:5000]},
                  "status": {"privacyStatus": "public"}},
        ).execute()["id"]
    yt.playlistItems().insert(
        part="snippet",
        body={"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}},
    ).execute()
    return playlist_id
