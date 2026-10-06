import re
import sys
import urllib.parse

from generator.db import get_conn
from generator.wiki_store import update_images
from generator.wikipedia_source import fetch_images, search_commons_images

IMAGES_PER_TOPIC = 2


def title_from_url(url: str) -> str:
    slug = url.rsplit("/", 1)[-1]
    return urllib.parse.unquote(slug).replace("_", " ")


def process(row: dict) -> tuple[str, int, str]:
    key = f"{row['subject']}/{row['chapter']}/{row['subtopic']}"
    try:
        real_title = title_from_url(row["wiki_source_url"])
        images = fetch_images(real_title, limit=IMAGES_PER_TOPIC)
        if not images:
            images = search_commons_images(row["subtopic"], limit=IMAGES_PER_TOPIC)
        if not images:
            return (key, 0, "no open-licensed images found")
        saved = update_images(row["subject"], row["chapter"], row["subtopic"], images)
        return (key, saved, "ok")
    except Exception as e:
        return (key, 0, f"error: {e}")


def main():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT subject, chapter, subtopic, wiki_source_url FROM wiki_notes "
            "WHERE JSON_LENGTH(wiki_images)=0 ORDER BY subject, chapter, subtopic"
        )
        rows = cur.fetchall()

    print(f"processing {len(rows)} subtopics, {IMAGES_PER_TOPIC} images each, serial...")
    done = 0
    total_images = 0
    zero_count = 0
    for row in rows:
        key, saved, status = process(row)
        done += 1
        total_images += saved
        if saved == 0:
            zero_count += 1
        print(f"[{done}/{len(rows)}] {key}: {saved} images ({status})", flush=True)

    print(f"\ndone. {total_images} images saved across {len(rows)} subtopics; {zero_count} subtopics got zero images.")


if __name__ == "__main__":
    main()
