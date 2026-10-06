import json
from dataclasses import dataclass
from typing import Optional

from . import config
from .db import get_conn


@dataclass
class CurriculumItem:
    subject: str
    class_: int
    chapter: str
    subtopic: str
    content_type: str  # "explainer" | "problem"
    difficulty: Optional[str] = None  # set when content_type == "problem"

    def chapter_key(self) -> str:
        return f"{self.subject}|class{self.class_}|{self.chapter}"

    def label(self) -> str:
        if self.content_type == "explainer":
            return f"Class {self.class_} {self.subject.title()} | {self.chapter} | {self.subtopic} (Explainer)"
        return f"Class {self.class_} {self.subject.title()} | {self.chapter} | {self.subtopic} ({self.difficulty})"

    def to_dict(self) -> dict:
        return {
            "subject": self.subject,
            "class": self.class_,
            "chapter": self.chapter,
            "subtopic": self.subtopic,
            "content_type": self.content_type,
            "difficulty": self.difficulty,
        }


def item_from_dict(d: dict) -> "CurriculumItem":
    return CurriculumItem(d["subject"], d["class"], d["chapter"], d["subtopic"], d["content_type"], d.get("difficulty"))


def _db_difficulty(difficulty: Optional[str]) -> str:
    """The difficulty column is NOT NULL DEFAULT '' so the UNIQUE key actually
    enforces uniqueness for explainers too (MySQL/SQLite both treat NULL as
    distinct-from-itself in unique indexes, which would let duplicates slip in)."""
    return difficulty or ""


def load_syllabus() -> list[dict]:
    return json.loads(config.SYLLABUS_PATH.read_text())


def _done_keys() -> set[tuple]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT subject, chapter, subtopic, content_type, difficulty "
            "FROM curriculum_progress WHERE status IN ('generated', 'published')"
        )
        rows = cur.fetchall()
    return {
        (r["subject"], r["chapter"], r["subtopic"], r["content_type"], r["difficulty"])
        for r in rows
    }


def get_next_item() -> Optional[CurriculumItem]:
    done = _done_keys()
    for ch in load_syllabus():
        subject, class_, chapter = ch["subject"], ch.get("class", 0), ch["chapter"]
        for subtopic in ch["subtopics"]:
            explainer_key = (subject, chapter, subtopic, "explainer", "")
            if explainer_key not in done:
                return CurriculumItem(subject, class_, chapter, subtopic, "explainer")
            for difficulty in config.PROBLEM_DIFFICULTIES:
                problem_key = (subject, chapter, subtopic, "problem", difficulty)
                if problem_key not in done:
                    return CurriculumItem(subject, class_, chapter, subtopic, "problem", difficulty)
    return None


def mark_done(item: CurriculumItem, run_id: str, status: str = "generated") -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO curriculum_progress (subject, chapter, subtopic, content_type, difficulty, status, run_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE status = VALUES(status), run_id = VALUES(run_id)",
            (item.subject, item.chapter, item.subtopic, item.content_type, _db_difficulty(item.difficulty), status, run_id),
        )


def mark_published(item: CurriculumItem) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE curriculum_progress SET status = 'published' "
            "WHERE subject = %s AND chapter = %s AND subtopic = %s AND content_type = %s AND difficulty = %s",
            (item.subject, item.chapter, item.subtopic, item.content_type, _db_difficulty(item.difficulty)),
        )


def status_report() -> str:
    syllabus = load_syllabus()
    total_items = sum(len(ch["subtopics"]) * (1 + len(config.PROBLEM_DIFFICULTIES)) for ch in syllabus)
    done = _done_keys()
    lines = [f"Total curriculum items: {total_items}, done: {len(done)}", ""]
    for ch in syllabus:
        subject, class_, chapter = ch["subject"], ch.get("class", 0), ch["chapter"]
        chapter_total = len(ch["subtopics"]) * (1 + len(config.PROBLEM_DIFFICULTIES))
        chapter_done = sum(
            1
            for subtopic in ch["subtopics"]
            for content_type, difficulty in [("explainer", "")] + [("problem", d) for d in config.PROBLEM_DIFFICULTIES]
            if (subject, chapter, subtopic, content_type, difficulty) in done
        )
        lines.append(f"{subject.title():8s} {chapter:45s} {chapter_done}/{chapter_total}")
    next_item = get_next_item()
    lines.append("")
    lines.append(f"Next up: {next_item.label() if next_item else 'Curriculum complete!'}")
    return "\n".join(lines)
