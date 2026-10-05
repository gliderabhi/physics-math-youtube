from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from generator import config, content_store
from generator.curriculum import CurriculumItem, load_syllabus
from generator.db import get_conn
from generator.topic_notes import note_for
from generator.topic_problems import problems_for
from generator.wiki_store import IMAGES_DIR, wiki_for

from .deps import require_user

router = APIRouter(dependencies=[Depends(require_user)])


@lru_cache(maxsize=1)
def _syllabus() -> list[dict]:
    return load_syllabus()


def _find_chapter(subject: str, class_: int, chapter: str) -> dict:
    for ch in _syllabus():
        if ch["subject"] == subject and ch["class"] == class_ and ch["chapter"] == chapter:
            return ch
    raise HTTPException(status_code=404, detail="Chapter not found")


@router.get("/api/languages")
def languages():
    return [{"code": code, "name": meta["name"]} for code, meta in config.CHANNELS.items()]


@router.get("/api/chapters")
def chapters():
    return [
        {
            "subject": ch["subject"],
            "class": ch["class"],
            "chapter": ch["chapter"],
            "subtopic_count": len(ch["subtopics"]),
        }
        for ch in _syllabus()
    ]


@router.get("/api/subtopics")
def subtopics(subject: str, chapter: str, class_: int = Query(..., alias="class")):
    ch = _find_chapter(subject, class_, chapter)

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT run_id, subtopic, content_type, difficulty, language, status, title "
            "FROM runs WHERE subject=%s AND class=%s AND chapter=%s",
            (subject, class_, chapter),
        )
        rows = cur.fetchall()

    by_key: dict[tuple, list[dict]] = {}
    for r in rows:
        by_key.setdefault((r["subtopic"], r["content_type"], r["difficulty"]), []).append(r)

    slots = [("explainer", "")] + [("problem", d) for d in config.PROBLEM_DIFFICULTIES]
    result = []
    for subtopic in ch["subtopics"]:
        items = []
        for content_type, difficulty in slots:
            matches = by_key.get((subtopic, content_type, difficulty), [])
            items.append(
                {
                    "content_type": content_type,
                    "difficulty": difficulty or None,
                    "exists": bool(matches),
                    "title": matches[0]["title"] if matches else None,
                    "languages": sorted({m["language"] for m in matches}),
                    # One run_id per language, so the UI can fetch /api/thumbnail/<run_id>
                    # for whichever language is currently selected.
                    "run_ids": {m["language"]: m["run_id"] for m in matches},
                }
            )
        result.append({"subtopic": subtopic, "items": items})

    return {"subject": subject, "class": class_, "chapter": chapter, "subtopics": result}


@router.get("/api/resolve")
def resolve(
    subject: str,
    chapter: str,
    subtopic: str,
    content_type: str,
    language: str,
    class_: int = Query(..., alias="class"),
    difficulty: str = Query(""),
):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT run_id, status, youtube_video_id, title FROM runs "
            "WHERE subject=%s AND class=%s AND chapter=%s AND subtopic=%s "
            "AND content_type=%s AND difficulty=%s AND language=%s "
            "ORDER BY (status='published') DESC, created_at DESC LIMIT 1",
            (subject, class_, chapter, subtopic, content_type, difficulty, language),
        )
        row = cur.fetchone()

        cur.execute(
            "SELECT DISTINCT language FROM runs "
            "WHERE subject=%s AND class=%s AND chapter=%s AND subtopic=%s "
            "AND content_type=%s AND difficulty=%s",
            (subject, class_, chapter, subtopic, content_type, difficulty),
        )
        available = sorted(r["language"] for r in cur.fetchall())

    if row and row["status"] == "published" and row["youtube_video_id"]:
        status = "published"
    elif row:
        status = "local"
    else:
        status = "not_available"

    explanation = None
    if row:
        try:
            item = CurriculumItem(subject, class_, chapter, subtopic, content_type, difficulty or None)
            content, _ = content_store.load_content(item, language)
            explanation = {
                "intro": content.get("intro"),
                "summary": content.get("summary"),
                "problem_statement": content.get("problem_statement"),
                "final_answer": content.get("final_answer"),
                "steps": [
                    {"text": s.get("narration", ""), "label": s.get("display_text", ""), "latex": s.get("latex", "")}
                    for s in content.get("steps", [])
                ],
            }
        except LookupError:
            pass

    ncert_note = note_for(subject, class_, chapter, subtopic, language)
    ncert_problems = problems_for(subject, class_, chapter, subtopic, language)

    wiki = None
    if not ncert_note and language == "en":
        wiki = wiki_for(subject, class_, chapter, subtopic)

    return {
        "status": status,
        "run_id": row["run_id"] if row else None,
        "youtube_video_id": row["youtube_video_id"] if row else None,
        "title": row["title"] if row else None,
        "available_languages": available,
        "explanation": explanation,
        "ncert_note": ncert_note,
        "ncert_problems": ncert_problems,
        "wiki_title": wiki["title"] if wiki else None,
        "wiki_text": wiki["text"] if wiki else None,
        "wiki_source_url": wiki["source_url"] if wiki else None,
        "wiki_images": wiki["images"] if wiki else [],
    }


@router.get("/api/wiki-image/{filename}")
def wiki_image(filename: str):
    path = (IMAGES_DIR / filename).resolve()
    if not path.is_relative_to(IMAGES_DIR.resolve()) or not path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path)


@router.get("/api/stream/{run_id}")
def stream(run_id: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT video_path FROM runs WHERE run_id=%s", (run_id,))
        row = cur.fetchone()

    if not row or not row["video_path"]:
        raise HTTPException(status_code=404, detail="Video not found")

    video_path = Path(row["video_path"]).resolve()
    if not video_path.is_relative_to(config.VIDEOS_DIR.resolve()):
        raise HTTPException(status_code=403, detail="Invalid video path")
    if not video_path.is_file():
        raise HTTPException(status_code=404, detail="Video file missing on disk")

    return FileResponse(video_path, media_type="video/mp4")


@router.get("/api/thumbnail/{run_id}")
def thumbnail_file(run_id: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT thumbnail_path FROM runs WHERE run_id=%s", (run_id,))
        row = cur.fetchone()

    if not row or not row["thumbnail_path"]:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    thumb_path = Path(row["thumbnail_path"]).resolve()
    # Defense in depth: accept the new permanent location, and the legacy ephemeral
    # output/<run_id>/ one for any row the backfill script hasn't touched.
    valid_root = thumb_path.is_relative_to(config.THUMBNAILS_DIR.resolve()) or thumb_path.is_relative_to(config.OUTPUT_DIR.resolve())
    if not valid_root:
        raise HTTPException(status_code=403, detail="Invalid thumbnail path")
    if not thumb_path.is_file():
        raise HTTPException(status_code=404, detail="Thumbnail file missing on disk")

    return FileResponse(thumb_path, media_type="image/png")
