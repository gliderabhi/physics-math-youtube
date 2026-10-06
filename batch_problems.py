import concurrent.futures
import threading

from generator import config
from generator.content_generator import generate_topic_problems
from generator.curriculum import CurriculumItem, load_syllabus
from generator.db import init_db
from generator.topic_problems import existing_keys, save_problems

MAX_WORKERS = 4
_lock = threading.Lock()
_counts = {"done": 0, "failed": 0}


def pending_jobs():
    done = existing_keys()
    jobs = []
    for ch in load_syllabus():
        for subtopic in ch["subtopics"]:
            for language in config.CHANNELS:
                key = (ch["subject"], ch["chapter"], subtopic, language)
                if key not in done:
                    jobs.append((ch["subject"], ch.get("class", 0), ch["chapter"], subtopic, language))
    return jobs


def run_job(job, total):
    subject, class_, chapter, subtopic, language = job
    item = CurriculumItem(subject, class_, chapter, subtopic, "explainer")
    try:
        problems = generate_topic_problems(item, language)
        save_problems(subject, chapter, subtopic, language, problems)
        with _lock:
            _counts["done"] += 1
            print(f"OK ({_counts['done']+_counts['failed']}/{total}): {item.label()} [{language}]")
    except Exception as e:
        with _lock:
            _counts["failed"] += 1
            print(f"FAILED ({_counts['done']+_counts['failed']}/{total}): {item.label()} [{language}] -- {e}")


def main():
    init_db()
    jobs = pending_jobs()
    total = len(jobs)
    print(f"{total} topic-problems jobs pending.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        list(pool.map(lambda job: run_job(job, total), jobs))

    print(f"Problems batch complete. {_counts['done']} done, {_counts['failed']} failed.")


if __name__ == "__main__":
    main()
