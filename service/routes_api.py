from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from generator import config, content_store
from generator.curriculum import CurriculumItem, load_syllabus
from generator.db import get_conn
from generator.topic_notes import note_for
from generator.topic_problems import problems_for
from generator.wiki_store import IMAGES_DIR, wiki_for, wiki_html_for, wiki_parts_for

from .deps import require_user

router = APIRouter(dependencies=[Depends(require_user)])


@lru_cache(maxsize=1)
def _syllabus() -> list[dict]:
    return load_syllabus()


def _find_topics(subject: str, chapter: str, class_: int | None = None) -> list[str]:
    subtopics = []
    found = False
    for ch in _syllabus():
        if ch["subject"].lower() == subject.lower() and ch["chapter"].lower() == chapter.lower():
            if class_ is not None and ch["class"] != class_:
                continue
            subtopics.extend(ch["subtopics"])
            found = True
    if not found:
        for ch in _syllabus():
            if ch["subject"].lower() == subject.lower() and ch["chapter"].lower() == chapter.lower():
                subtopics.extend(ch["subtopics"])
                found = True
    if not found:
        raise HTTPException(status_code=404, detail="Topic not found")

    seen = set()
    ordered = []
    for st in subtopics:
        if st not in seen:
            seen.add(st)
            ordered.append(st)
    return ordered


@router.get("/api/languages")
def languages():
    return [{"code": code, "name": meta["name"]} for code, meta in config.CHANNELS.items()]


@router.get("/api/chapters")
def chapters():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT DISTINCT subject, chapter, subtopic FROM runs "
            "WHERE status IN ('published', 'local') OR video_path IS NOT NULL OR youtube_video_id IS NOT NULL"
        )
        video_rows = cur.fetchall()

    video_map: dict[tuple[str, str], set[str]] = {}
    for r in video_rows:
        video_map.setdefault((r["subject"].lower(), r["chapter"].lower()), set()).add(r["subtopic"].lower())

    merged: dict[tuple[str, str], dict] = {}
    for ch in _syllabus():
        key = (ch["subject"], ch["chapter"])
        if key not in merged:
            merged[key] = {
                "subject": ch["subject"],
                "class": ch["class"],
                "chapter": ch["chapter"],
                "subtopics": list(ch["subtopics"]),
                "subtopic_count": len(ch["subtopics"]),
            }
        else:
            merged[key]["subtopics"].extend(ch["subtopics"])
            merged[key]["subtopic_count"] = len(merged[key]["subtopics"])

    for item in merged.values():
        ch_key = (item["subject"].lower(), item["chapter"].lower())
        ch_video_subs = video_map.get(ch_key, set())
        video_subs = [
            st for st in item["subtopics"]
            if st.lower() in ch_video_subs or st.split(":")[0].strip().lower() in ch_video_subs
        ]
        item["video_subtopics"] = video_subs
        item["video_count"] = len(video_subs)
        item["has_video"] = len(video_subs) > 0

    return list(merged.values())


@router.get("/api/subtopics")
def subtopics(subject: str, chapter: str, class_: int | None = Query(None, alias="class")):
    subtopic_list = _find_topics(subject, chapter, class_)

    with get_conn() as conn, conn.cursor() as cur:
        if class_ is not None:
            cur.execute(
                "SELECT run_id, subtopic, content_type, difficulty, language, status, title "
                "FROM runs WHERE subject=%s AND `class`=%s AND chapter=%s",
                (subject, class_, chapter),
            )
        else:
            cur.execute(
                "SELECT run_id, subtopic, content_type, difficulty, language, status, title "
                "FROM runs WHERE subject=%s AND chapter=%s",
                (subject, chapter),
            )
        rows = cur.fetchall()

    by_key: dict[tuple, list[dict]] = {}
    for r in rows:
        by_key.setdefault((r["subtopic"], r["content_type"], r["difficulty"]), []).append(r)

    slots = [("explainer", "")] + [("problem", d) for d in config.PROBLEM_DIFFICULTIES]
    result = []
    for subtopic in subtopic_list:
        parent_sub = subtopic.split(":")[0].strip() if ":" in subtopic else subtopic
        items = []
        for content_type, difficulty in slots:
            matches = by_key.get((subtopic, content_type, difficulty), [])
            if not matches and parent_sub != subtopic:
                matches = by_key.get((parent_sub, content_type, difficulty), [])
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
        has_video = any(it["exists"] for it in items)
        result.append({"subtopic": subtopic, "items": items, "has_video": has_video})

    return {"subject": subject, "class": class_ or 0, "chapter": chapter, "subtopics": result}


@router.get("/api/resolve")
def resolve(
    subject: str,
    chapter: str,
    subtopic: str,
    content_type: str,
    language: str,
    class_: int | None = Query(None, alias="class"),
    difficulty: str = Query(""),
):
    parent_sub = subtopic.split(":")[0].strip() if ":" in subtopic else subtopic
    with get_conn() as conn, conn.cursor() as cur:
        if class_ is not None:
            cur.execute(
                "SELECT run_id, status, youtube_video_id, title, subtopic, `class` FROM runs "
                "WHERE subject=%s AND `class`=%s AND chapter=%s AND (subtopic=%s OR subtopic=%s) "
                "AND content_type=%s AND difficulty=%s AND language=%s "
                "ORDER BY (subtopic=%s) DESC, (status='published') DESC, created_at DESC LIMIT 1",
                (subject, class_, chapter, subtopic, parent_sub, content_type, difficulty, language, subtopic),
            )
        else:
            cur.execute(
                "SELECT run_id, status, youtube_video_id, title, subtopic, `class` FROM runs "
                "WHERE subject=%s AND chapter=%s AND (subtopic=%s OR subtopic=%s) "
                "AND content_type=%s AND difficulty=%s AND language=%s "
                "ORDER BY (subtopic=%s) DESC, (status='published') DESC, created_at DESC LIMIT 1",
                (subject, chapter, subtopic, parent_sub, content_type, difficulty, language, subtopic),
            )
        row = cur.fetchone()

        if class_ is not None:
            cur.execute(
                "SELECT DISTINCT language FROM runs "
                "WHERE subject=%s AND `class`=%s AND chapter=%s AND (subtopic=%s OR subtopic=%s) "
                "AND content_type=%s AND difficulty=%s",
                (subject, class_, chapter, subtopic, parent_sub, content_type, difficulty),
            )
        else:
            cur.execute(
                "SELECT DISTINCT language FROM runs "
                "WHERE subject=%s AND chapter=%s AND (subtopic=%s OR subtopic=%s) "
                "AND content_type=%s AND difficulty=%s",
                (subject, chapter, subtopic, parent_sub, content_type, difficulty),
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
        candidates = []
        for s in [subtopic, row.get("subtopic"), parent_sub]:
            if s and s not in candidates:
                candidates.append(s)

        cls = class_ if class_ is not None else row.get("class", 0)
        lang_candidates = [language]
        for l in ["hi-en", "en"]:
            if l not in lang_candidates:
                lang_candidates.append(l)

        for candidate_sub in candidates:
            for candidate_lang in lang_candidates:
                try:
                    item = CurriculumItem(subject, cls or 0, chapter, candidate_sub, content_type, difficulty or None)
                    content, _ = content_store.load_content(item, candidate_lang)
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
                    break
                except LookupError:
                    continue
            if explanation:
                break

    ncert_note = note_for(subject, class_ or 0, chapter, subtopic, language) if class_ else None
    ncert_problems = problems_for(subject, class_ or 0, chapter, subtopic, language) if class_ else []

    wiki_html = wiki_html_for(subject, chapter, subtopic, class_, language)
    wiki = wiki_for(subject, chapter, subtopic, class_) if not wiki_html else None
    parts = wiki_parts_for(subject, chapter, subtopic, class_, language)

    return {
        "status": status,
        "run_id": row["run_id"] if row else None,
        "youtube_video_id": row["youtube_video_id"] if row else None,
        "title": row["title"] if row else None,
        "available_languages": available,
        "explanation": explanation,
        "ncert_note": ncert_note,
        "ncert_problems": ncert_problems,
        "wiki_title": wiki_html["title"] if wiki_html else (wiki["title"] if wiki else None),
        "wiki_text": wiki["text"] if wiki else None,
        "wiki_html": wiki_html["html"] if wiki_html else None,
        "parts": parts,
        "has_diagrams": wiki_html["has_diagrams"] if wiki_html else bool(parts and any(p.get("diagram_url") for p in parts)),
        "wiki_source_url": wiki_html["url"] if wiki_html else (wiki["source_url"] if wiki else None),
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
