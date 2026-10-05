import json
from pathlib import Path

from .curriculum import CurriculumItem
from .db import get_conn


def split_content(content: dict) -> tuple[dict, dict]:
    """Splits a flat content dict (the shape content_generator.py / manual_content/*.json use)
    into (body, narration). body holds everything visual/structural (language-independent);
    narration holds only the spoken text, so a new language is just a new narration row,
    never a duplicate of the whole script."""
    steps = [
        {"display_text": s.get("display_text", ""), "latex": s.get("latex", ""), "visual": s.get("visual", {})}
        for s in content["steps"]
    ]
    narration_steps = [s["narration"] for s in content["steps"]]

    body = {
        "content_type": content["content_type"],
        "title": content["title"],
        "steps": steps,
        "opening_visual": content.get("opening_visual", {}),
        "closing_visual": content.get("closing_visual", {}),
    }
    if content["content_type"] == "explainer":
        body["closing_latex"] = content.get("summary_latex", "")
        narration = {"opening": content["intro"], "steps": narration_steps, "closing": content["summary"]}
    else:
        body["closing_latex"] = content.get("final_answer_latex", "")
        narration = {"opening": content["problem_statement"], "steps": narration_steps, "closing": content["final_answer"]}
    return body, narration


def merge_content(body: dict, narration: dict) -> dict:
    """Inverse of split_content: reconstructs the flat content dict script.py expects."""
    steps = [{**s, "narration": n} for s, n in zip(body["steps"], narration["steps"])]
    content = {
        "content_type": body["content_type"],
        "title": body["title"],
        "steps": steps,
        "opening_visual": body.get("opening_visual", {}),
        "closing_visual": body.get("closing_visual", {}),
    }
    if body["content_type"] == "explainer":
        content["intro"] = narration["opening"]
        content["summary"] = narration["closing"]
        content["summary_latex"] = body.get("closing_latex", "")
    else:
        content["problem_statement"] = narration["opening"]
        content["final_answer"] = narration["closing"]
        content["final_answer_latex"] = body.get("closing_latex", "")
    return content


def save_content_item(item: CurriculumItem, body: dict, metadata: dict) -> int:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO content_items (subject, class, chapter, subtopic, content_type, difficulty, title, body, metadata) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE title = VALUES(title), body = VALUES(body), metadata = VALUES(metadata)",
            (
                item.subject, item.class_, item.chapter, item.subtopic, item.content_type, item.difficulty or "",
                body["title"], json.dumps(body), json.dumps(metadata),
            ),
        )
        cur.execute(
            "SELECT id FROM content_items WHERE subject=%s AND class=%s AND chapter=%s AND subtopic=%s AND content_type=%s AND difficulty=%s",
            (item.subject, item.class_, item.chapter, item.subtopic, item.content_type, item.difficulty or ""),
        )
        return cur.fetchone()["id"]


def save_narration(content_item_id: int, language: str, narration: dict) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO narrations (content_item_id, language, narration) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE narration = VALUES(narration)",
            (content_item_id, language, json.dumps(narration)),
        )


def get_content_item_id(item: CurriculumItem) -> int | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM content_items WHERE subject=%s AND class=%s AND chapter=%s AND subtopic=%s AND content_type=%s AND difficulty=%s",
            (item.subject, item.class_, item.chapter, item.subtopic, item.content_type, item.difficulty or ""),
        )
        row = cur.fetchone()
        return row["id"] if row else None


def load_content(item: CurriculumItem, language: str) -> tuple[dict, dict]:
    """Returns (content, metadata) merged from DB, ready for script.build_segments()."""
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, body, metadata FROM content_items WHERE subject=%s AND class=%s AND chapter=%s AND subtopic=%s AND content_type=%s AND difficulty=%s",
            (item.subject, item.class_, item.chapter, item.subtopic, item.content_type, item.difficulty or ""),
        )
        row = cur.fetchone()
        if row is None:
            raise LookupError(f"No content_item stored for {item.label()}")
        cur.execute(
            "SELECT narration FROM narrations WHERE content_item_id=%s AND language=%s", (row["id"], language)
        )
        nrow = cur.fetchone()
        if nrow is None:
            raise LookupError(f"No '{language}' narration stored for {item.label()}")
    body = json.loads(row["body"])
    metadata = json.loads(row["metadata"])
    narration = json.loads(nrow["narration"])
    return merge_content(body, narration), metadata


def ingest_file(file_path: str, language: str) -> int:
    """Reads either a full authoring file ({item, content, metadata} - same shape as the old
    manual_content/*.json files) or a narration-only file ({item, narration}) for a content_item
    that was already ingested once. Stores/updates accordingly. Returns content_item_id."""
    from .curriculum import item_from_dict

    data = json.loads(Path(file_path).read_text())
    item = item_from_dict(data["item"])
    if "content" in data:
        body, narration = split_content(data["content"])
        content_item_id = save_content_item(item, body, data.get("metadata", {}))
    else:
        content_item_id = get_content_item_id(item)
        if content_item_id is None:
            raise LookupError(f"No existing content_item for {item.label()} — ingest a full 'content' file first")
        narration = data["narration"]
    save_narration(content_item_id, language, narration)
    return content_item_id
