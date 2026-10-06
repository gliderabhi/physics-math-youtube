import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from .db import get_conn

IMAGES_DIR = Path("/home/sevis/ncert_books/_wiki_images")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
USER_AGENT = "physics-math-youtube-edu-project/1.0 (private non-commercial educational tool)"


def _slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()[:60]


def _download_image(url: str, dest_stem: str, retries: int = 4) -> str | None:
    ext = re.search(r"\.(svg|png|jpe?g|gif)(?:\?|$)", url, re.IGNORECASE)
    ext = ext.group(1).lower() if ext else "jpg"
    fname = f"{dest_stem}.{ext}"
    out_path = IMAGES_DIR / fname
    if not out_path.exists():
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        for attempt in range(retries):
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    out_path.write_bytes(resp.read())
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < retries - 1:
                    time.sleep(5 * (attempt + 1))  # upload.wikimedia.org rate-limits separately from the API
                    continue
                return None
            except Exception:
                return None
    return fname


def save_wiki(subject: str, chapter: str, subtopic: str, data: dict, class_: int | None = None) -> None:
    stem_base = f"{subject}-{_slug(chapter)}-{_slug(subtopic)}"
    local_images = []
    for i, img in enumerate(data["images"]):
        fname = _download_image(img["url"], f"{stem_base}-{i}")
        if fname:
            local_images.append({"file": fname, "title": img["title"], "license": img["license"], "artist": img["artist"]})

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO wiki_notes (subject, chapter, subtopic, wiki_title, wiki_text, wiki_source_url, wiki_images) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE wiki_title=VALUES(wiki_title), wiki_text=VALUES(wiki_text), "
            "wiki_source_url=VALUES(wiki_source_url), wiki_images=VALUES(wiki_images)",
            (subject, chapter, subtopic, data["title"], data["text"][:10000], data["source_url"], json.dumps(local_images)),
        )


def _as_url(img: dict) -> dict:
    return {
        "url": f"/physics-service/api/wiki-image/{img['file']}",
        "title": img["title"],
        "license": img["license"],
        "artist": img["artist"],
    }


def wiki_for(subject: str, chapter: str, subtopic: str, class_: int | None = None) -> dict | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT wiki_title, wiki_text, wiki_source_url, wiki_images FROM wiki_notes "
            "WHERE subject=%s AND chapter=%s AND subtopic=%s LIMIT 1",
            (subject, chapter, subtopic),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "title": row["wiki_title"],
        "text": row["wiki_text"],
        "source_url": row["wiki_source_url"],
        "images": [_as_url(img) for img in json.loads(row["wiki_images"])],
    }


def wiki_html_for(subject: str, chapter: str, subtopic: str, class_: int | None = None, language: str = "en") -> dict | None:
    lang_candidates = [language]
    if language in ("hi", "hi-en"):
        lang_candidates = ["hi-en", "hi", "en"]
    elif language != "en":
        lang_candidates.append("en")

    with get_conn() as conn, conn.cursor() as cur:
        for lang in lang_candidates:
            cur.execute(
                "SELECT wiki_title, wiki_url, html_content, has_diagrams FROM subtopic_wiki_html "
                "WHERE subject=%s AND chapter=%s AND subtopic=%s AND language=%s LIMIT 1",
                (subject, chapter, subtopic, lang),
            )
            row = cur.fetchone()
            if row:
                return {
                    "title": row["wiki_title"],
                    "url": row["wiki_url"],
                    "html": row["html_content"],
                    "has_diagrams": bool(row["has_diagrams"]),
                }
    return None


def save_subtopic_html(subject: str, chapter: str, subtopic: str, data: dict, language: str = "en", class_: int | None = None) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO subtopic_wiki_html
                (subject, chapter, subtopic, language, wiki_title, wiki_url, html_content, has_diagrams)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                wiki_title = VALUES(wiki_title),
                wiki_url = VALUES(wiki_url),
                html_content = VALUES(html_content),
                has_diagrams = VALUES(has_diagrams)
            """,
            (
                subject,
                chapter,
                subtopic,
                language,
                data["title"],
                data["source_url"] if "source_url" in data else data.get("url", ""),
                data["html"],
                data["has_diagrams"],
            ),
        )


def update_images(subject: str, chapter: str, subtopic: str, images: list[dict], class_: int | None = None) -> int:
    """Backfills just the wiki_images column for an already-saved row, leaving its
    original-authorship text/title/source_url completely untouched."""
    stem_base = f"{subject}-{_slug(chapter)}-{_slug(subtopic)}"
    local_images = []
    for i, img in enumerate(images):
        fname = _download_image(img["url"], f"{stem_base}-{i}")
        if fname:
            local_images.append({"file": fname, "title": img["title"], "license": img["license"], "artist": img["artist"]})

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE wiki_notes SET wiki_images=%s WHERE subject=%s AND chapter=%s AND subtopic=%s",
            (json.dumps(local_images), subject, chapter, subtopic),
        )
    return len(local_images)


def existing_keys() -> set[tuple]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT subject, chapter, subtopic FROM wiki_notes")
        return {(r["subject"], r["chapter"], r["subtopic"]) for r in cur.fetchall()}


def wiki_parts_for(subject: str, chapter: str, subtopic: str, class_: int | None = None, language: str = "en") -> list[dict]:
    lang_candidates = [language]
    if language in ("hi", "hi-en"):
        lang_candidates = ["hi-en", "hi", "en"]
    elif language != "en":
        lang_candidates.append("en")

    with get_conn() as conn, conn.cursor() as cur:
        for lang in lang_candidates:
            cur.execute(
                "SELECT part_index, heading, paragraph, paragraph_html, diagram_url, diagram_caption "
                "FROM subtopic_wiki_parts "
                "WHERE subject=%s AND chapter=%s AND subtopic=%s AND language=%s "
                "ORDER BY part_index ASC",
                (subject, chapter, subtopic, lang),
            )
            rows = cur.fetchall()
            if rows:
                return [
                    {
                        "part_index": r["part_index"],
                        "heading": r["heading"],
                        "paragraph": r["paragraph"],
                        "paragraph_html": r["paragraph_html"],
                        "diagram_url": r["diagram_url"],
                        "diagram_caption": r["diagram_caption"],
                    }
                    for r in rows
                ]
    return []


def save_subtopic_parts(subject: str, chapter: str, subtopic: str, language: str, parts: list[dict], class_: int | None = None) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM subtopic_wiki_parts WHERE subject=%s AND chapter=%s AND subtopic=%s AND language=%s",
            (subject, chapter, subtopic, language),
        )
        for p in parts:
            cur.execute(
                """
                INSERT INTO subtopic_wiki_parts
                    (subject, chapter, subtopic, language, part_index, heading, paragraph, paragraph_html, diagram_url, diagram_caption)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    subject,
                    chapter,
                    subtopic,
                    language,
                    p["part_index"],
                    p["heading"],
                    p["paragraph"],
                    p.get("paragraph_html", ""),
                    p.get("diagram_url"),
                    p.get("diagram_caption"),
                ),
            )

