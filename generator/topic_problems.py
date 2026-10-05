import json

from .db import get_conn


def save_problems(subject: str, class_: int, chapter: str, subtopic: str, language: str, problems: list[dict]) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO topic_problems (subject, class, chapter, subtopic, language, problems) "
            "VALUES (%s, %s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE problems = VALUES(problems)",
            (subject, class_, chapter, subtopic, language, json.dumps(problems)),
        )


def problems_for(subject: str, class_: int, chapter: str, subtopic: str, language: str) -> list[dict]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT problems FROM topic_problems WHERE subject=%s AND class=%s AND chapter=%s AND subtopic=%s AND language=%s",
            (subject, class_, chapter, subtopic, language),
        )
        row = cur.fetchone()
        return json.loads(row["problems"]) if row else []


def problems_for_chapter(subject: str, class_: int, chapter: str) -> dict[tuple[str, str], list[dict]]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT subtopic, language, problems FROM topic_problems WHERE subject=%s AND class=%s AND chapter=%s",
            (subject, class_, chapter),
        )
        return {(r["subtopic"], r["language"]): json.loads(r["problems"]) for r in cur.fetchall()}


def existing_keys() -> set[tuple]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT subject, class, chapter, subtopic, language FROM topic_problems")
        return {(r["subject"], r["class"], r["chapter"], r["subtopic"], r["language"]) for r in cur.fetchall()}
