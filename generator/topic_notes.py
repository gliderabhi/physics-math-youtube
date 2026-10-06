from .db import get_conn


def save_note(subject: str, chapter: str, subtopic: str, language: str, explanation: str, class_: int | None = None) -> None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO topic_notes (subject, chapter, subtopic, language, explanation) "
            "VALUES (%s, %s, %s, %s, %s) "
            "ON DUPLICATE KEY UPDATE explanation = VALUES(explanation)",
            (subject, chapter, subtopic, language, explanation),
        )


def note_for(subject: str, chapter: str, subtopic: str, language: str, class_: int | None = None) -> str | None:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT explanation FROM topic_notes WHERE subject=%s AND chapter=%s AND subtopic=%s AND language=%s",
            (subject, chapter, subtopic, language),
        )
        row = cur.fetchone()
        return row["explanation"] if row else None


def notes_for_chapter(subject: str, chapter: str, class_: int | None = None) -> dict[tuple[str, str], str]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT subtopic, language, explanation FROM topic_notes WHERE subject=%s AND chapter=%s",
            (subject, chapter),
        )
        return {(r["subtopic"], r["language"]): r["explanation"] for r in cur.fetchall()}


def existing_keys() -> set[tuple]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT subject, chapter, subtopic, language FROM topic_notes")
        return {(r["subject"], r["chapter"], r["subtopic"], r["language"]) for r in cur.fetchall()}
