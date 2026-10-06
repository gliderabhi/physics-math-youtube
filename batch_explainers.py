import subprocess
import time
from pathlib import Path

from generator import config
from generator.curriculum import load_syllabus
from generator.db import get_conn, init_db

MAX_CONCURRENT = 2
LOG_DIR = Path("/home/sevis/projects/local-logs/batch_explainers")
SUMMARY_LOG = LOG_DIR / "_summary.log"


def pending_jobs():
    init_db()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT DISTINCT subject, chapter, subtopic, language FROM runs WHERE content_type='explainer'")
        done = {(r["subject"], r["chapter"], r["subtopic"], r["language"]) for r in cur.fetchall()}

    jobs = []
    for ch in load_syllabus():
        for subtopic in ch["subtopics"]:
            for language in config.CHANNELS:
                key = (ch["subject"], ch["chapter"], subtopic, language)
                if key not in done:
                    jobs.append((ch["subject"], ch.get("class", 0), ch["chapter"], subtopic, language))
    return jobs


def _slug(job, index: int) -> str:
    subject, class_, chapter, subtopic, language = job
    raw = f"{index:04d}-{language}-{chapter}-{subtopic}"
    safe = "".join(c if c.isalnum() else "-" for c in raw).strip("-").lower()
    return safe[:120]


def launch(job, index: int):
    subject, class_, chapter, subtopic, language = job
    log_path = LOG_DIR / f"{_slug(job, index)}.log"
    cmd = [
        str(config.ROOT / ".venv" / "bin" / "python"), "main.py", "generate-item",
        "--subject", subject, "--class", str(class_), "--chapter", chapter,
        "--subtopic", subtopic, "--content-type", "explainer", "--language", language,
    ]
    log = open(log_path, "w")
    proc = subprocess.Popen(cmd, cwd=str(config.ROOT), stdout=log, stderr=subprocess.STDOUT)
    return proc, log


def main():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    jobs = pending_jobs()
    total = len(jobs)
    print(f"{total} explainer jobs pending.")

    running = []
    next_index = 0
    done_count = 0
    fail_count = 0

    while jobs or running:
        while jobs and len(running) < MAX_CONCURRENT:
            job = jobs.pop(0)
            proc, log = launch(job, next_index)
            running.append((proc, job, log))
            with open(SUMMARY_LOG, "a") as f:
                f.write(f"STARTED {job}\n")
            next_index += 1

        time.sleep(10)
        still_running = []
        for proc, job, log in running:
            ret = proc.poll()
            if ret is None:
                still_running.append((proc, job, log))
                continue
            log.close()
            done_count += 1
            if ret != 0:
                fail_count += 1
            status = "OK" if ret == 0 else f"FAILED(rc={ret})"
            with open(SUMMARY_LOG, "a") as f:
                f.write(f"{status} {job}\n")
            print(f"{status}: {job} ({done_count}/{total} done, {fail_count} failed, {len(jobs)} queued)")
        running = still_running

    print(f"Batch complete. {done_count} done, {fail_count} failed.")


if __name__ == "__main__":
    main()
