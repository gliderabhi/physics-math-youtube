#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from generator.youtube_auth import get_credentials


def upload_video(video_path: Path, channel: str, title: str, description: str, tags: list[str], privacy: str = "public") -> str:
    print(f"Connecting to YouTube API for channel '{channel}'...")
    creds = get_credentials(channel)
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        }
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024 * 8  # 8MB chunks
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    print(f"Starting upload for {video_path.name} ({video_path.stat().st_size / (1024 * 1024):.1f} MB)...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            progress = int(status.progress() * 100)
            print(f"Uploading: {progress}%...")

    video_id = response.get("id")
    video_url = f"https://www.youtube.com/shorts/{video_id}"
    print(f"Successfully uploaded to '{channel}' channel!")
    print(f"Video URL: {video_url} (Standard: https://youtu.be/{video_id})")
    return video_url


def main():
    parser = argparse.ArgumentParser(description="Upload a reel / short to YouTube.")
    parser.add_argument("--video", required=True, type=Path, help="Path to mp4 video")
    parser.add_argument("--channel", required=True, choices=["en", "hi-en"], help="Target channel ('en' or 'hi-en')")
    parser.add_argument("--title", required=True, help="YouTube title (include #shorts)")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"], help="Privacy status")

    args = parser.parse_args()

    tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]
    if "#shorts" not in args.title.lower():
        title = f"{args.title} #shorts"
    else:
        title = args.title

    upload_video(
        video_path=args.video,
        channel=args.channel,
        title=title,
        description=args.description,
        tags=tags_list,
        privacy=args.privacy
    )


if __name__ == "__main__":
    main()
