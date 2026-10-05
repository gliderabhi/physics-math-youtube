import time
import sys
from curated_wiki_mapping import FIXES
from batch_pull_wiki_html import fetch_and_clean_html
from generator.db import get_conn

def update_english_and_clear_hindi(subject: str, class_: int, chapter: str, subtopic: str, data: dict):
    with get_conn() as conn, conn.cursor() as cur:
        # 1. Update English row
        cur.execute(
            """
            INSERT INTO subtopic_wiki_html
                (subject, class, chapter, subtopic, language, wiki_title, wiki_url, html_content, has_diagrams)
            VALUES (%s, %s, %s, %s, 'en', %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                wiki_title = VALUES(wiki_title),
                wiki_url = VALUES(wiki_url),
                html_content = VALUES(html_content),
                has_diagrams = VALUES(has_diagrams)
            """,
            (
                subject,
                class_,
                chapter,
                subtopic,
                data["title"],
                data["source_url"],
                data["html"],
                data["has_diagrams"],
            ),
        )
        # 2. Delete old Hindi row so it can be cleanly re-translated
        cur.execute(
            """
            DELETE FROM subtopic_wiki_html
            WHERE subject=%s AND class=%s AND chapter=%s AND subtopic=%s AND language='hi-en'
            """,
            (subject, class_, chapter, subtopic),
        )


def main():
    items = list(FIXES.items())
    total = len(items)
    print(f"Beginning update of {total} curated Wikipedia articles in DB...")
    
    success = 0
    failed = 0
    t0 = time.time()
    
    for idx, ((subj, cl, chap, sub), wiki_title) in enumerate(items, 1):
        print(f"[{idx}/{total}] [{cl} {subj}] {chap} | {sub} -> '{wiki_title}'...", end="", flush=True)
        try:
            data = fetch_and_clean_html(wiki_title)
            if not data or not data["html"]:
                print(" [ERROR: Failed to fetch clean HTML]")
                failed += 1
                continue
            
            update_english_and_clear_hindi(subj, cl, chap, sub, data)
            success += 1
            print(f" OK ({len(data['html'])} bytes, diagrams: {bool(data['has_diagrams'])})")
        except Exception as e:
            print(f" [EXCEPTION: {e}]")
            failed += 1
            time.sleep(2)

    elapsed = time.time() - t0
    print(f"\nFinished updating curated Wikipedia articles in {elapsed:.1f}s.")
    print(f"Success: {success}, Failed: {failed}")

if __name__ == "__main__":
    main()
