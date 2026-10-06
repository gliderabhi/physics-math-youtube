import subprocess

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from generator.db import get_conn

from .deps import require_admin

router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])


class CommentBody(BaseModel):
    comment: str


@router.get("/review-queue")
def review_queue():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT run_id, subject, chapter, subtopic, content_type, difficulty, "
            "language, title, review_comment, created_at FROM runs "
            "WHERE status = 'generated' ORDER BY created_at ASC"
        )
        rows = cur.fetchall()
    for r in rows:
        r["created_at"] = r["created_at"].isoformat()
    return rows


@router.post("/review/{run_id}/approve")
def approve(run_id: str):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE runs SET status = 'approved', review_comment = NULL "
            "WHERE run_id = %s AND status = 'generated'",
            (run_id,),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Run not found or not awaiting review")
    return {"status": "approved"}


@router.post("/review/{run_id}/comment")
def comment(run_id: str, body: CommentBody):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE runs SET review_comment = %s WHERE run_id = %s AND status = 'generated'",
            (body.comment, run_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Run not found or not awaiting review")
    return {"status": "comment_saved"}


class GenerateBody(BaseModel):
    subject: str
    class_: int = Field(0, alias="class")
    chapter: str
    subtopic: str
    content_type: str
    difficulty: str = ""
    language: str


@router.post("/generate")
def generate(body: GenerateBody):
    cmd = [
        "/home/sevis/projects/physics-math-youtube/.venv/bin/python", "main.py", "generate-item",
        "--subject", body.subject, "--class", str(body.class_), "--chapter", body.chapter,
        "--subtopic", body.subtopic, "--content-type", body.content_type, "--language", body.language,
    ]
    if body.difficulty:
        cmd += ["--difficulty", body.difficulty]

    log = open("/home/sevis/projects/local-logs/physics-generate.log", "a")
    subprocess.Popen(
        cmd, cwd="/home/sevis/projects/physics-math-youtube",
        stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
    )
    return {"status": "started"}
