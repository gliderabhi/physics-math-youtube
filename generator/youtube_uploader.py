from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from . import config
from .curriculum import CurriculumItem
from .db import get_conn
from .youtube_auth import get_credentials


def _client(channel: str):
    return build("youtube", "v3", credentials=get_credentials(channel))


def get_or_create_playlist(youtube, item: CurriculumItem, channel: str) -> str:
    chapter_key = f"{channel}:{item.chapter_key()}"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT youtube_playlist_id FROM playlists WHERE chapter_key = %s", (chapter_key,))
        row = cur.fetchone()
        if row:
            return row["youtube_playlist_id"]

    title = f"Class {item.class_} {item.subject.title()} | {item.chapter}"
    response = (
        youtube.playlists()
        .insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": f"{title} - full chapter coverage, explanations and JEE/NEET-style problems.",
                },
                "status": {"privacyStatus": config.DEFAULT_PRIVACY_STATUS},
            },
        )
        .execute()
    )
    playlist_id = response["id"]
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO playlists (chapter_key, youtube_playlist_id) VALUES (%s, %s) "
            "ON DUPLICATE KEY UPDATE youtube_playlist_id = VALUES(youtube_playlist_id)",
            (chapter_key, playlist_id),
        )
    return playlist_id


def upload_video(item: CurriculumItem, video_path: Path, thumbnail_path: Path, metadata: dict, channel: str) -> dict:
    youtube = _client(channel)

    video_response = (
        youtube.videos()
        .insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": metadata["youtube_title"],
                    "description": metadata["description"],
                    "tags": metadata["tags"],
                    "categoryId": config.YOUTUBE_CATEGORY_EDUCATION,
                },
                "status": {"privacyStatus": config.DEFAULT_PRIVACY_STATUS, "selfDeclaredMadeForKids": False},
            },
            media_body=MediaFileUpload(str(video_path), chunksize=-1, resumable=True),
        )
        .execute()
    )
    video_id = video_response["id"]

    try:
        youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(str(thumbnail_path))).execute()
    except HttpError as e:
        print(f"Warning: could not set custom thumbnail ({e}). "
              f"This channel likely needs phone verification (youtube.com/verify) to upload custom thumbnails. "
              f"Continuing without it — YouTube will use an auto-generated thumbnail for now.")

    playlist_id = get_or_create_playlist(youtube, item, channel)
    youtube.playlistItems().insert(
        part="snippet",
        body={"snippet": {"playlistId": playlist_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}},
    ).execute()

    return {"video_id": video_id, "playlist_id": playlist_id}
