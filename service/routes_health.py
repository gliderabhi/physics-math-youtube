from fastapi import APIRouter, HTTPException

from generator.db import get_conn

router = APIRouter()


@router.get("/health")
def health():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
    except Exception:
        raise HTTPException(status_code=503, detail="db unreachable")
    return {"status": "ok"}
