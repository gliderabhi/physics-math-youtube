import concurrent.futures
import threading

from generator.curriculum import load_syllabus
from generator.db import init_db
from generator.wiki_store import existing_keys, save_wiki
from generator.wikipedia_source import content_for_subtopic

MAX_WORKERS = 4
_lock = threading.Lock()
_counts = {"done": 0, "skipped": 0, "failed": 0}


def pending_jobs():
    done = existing_keys()
    jobs = []
    for ch in load_syllabus():
        for subtopic in ch["subtopics"]:
            key = (ch["subject"], ch["chapter"], subtopic)
            if key not in done:
                jobs.append(key)
    return jobs


def run_job(job, total):
    subject, chapter, subtopic = job
    label = f"{subject} | {chapter} | {subtopic}"
    try:
        data = content_for_subtopic(subtopic)
        with _lock:
            if not data:
                _counts["skipped"] += 1
                print(f"SKIP ({_counts['done']+_counts['skipped']+_counts['failed']}/{total}): {label} -- no good Wikipedia match")
                return
        save_wiki(subject, chapter, subtopic, data)
        with _lock:
            _counts["done"] += 1
            print(f"OK ({_counts['done']+_counts['skipped']+_counts['failed']}/{total}): {label} -> {data['title']}")
    except Exception as e:
        with _lock:
            _counts["failed"] += 1
            print(f"FAILED ({_counts['done']+_counts['skipped']+_counts['failed']}/{total}): {label} -- {e}")


def main():
    init_db()
    jobs = pending_jobs()
    total = len(jobs)
    print(f"{total} wiki jobs pending.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        list(pool.map(lambda job: run_job(job, total), jobs))

    print(f"Wiki batch complete. {_counts['done']} done, {_counts['skipped']} skipped (no match), {_counts['failed']} failed.")


if __name__ == "__main__":
    main()
