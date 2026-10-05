import concurrent.futures
import json
import random
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import pymysql

SEP = " ___XSEP___ "
MAX_WORKERS = 5
CLIENTS = ["dict-chrome-ex", "it"]

_lock = threading.Lock()
_counts = {"done": 0, "failed": 0}


def get_conn():
    return pymysql.connect(
        host="127.0.0.1",
        user="physics_yt_app",
        password="abbbc8eff2c24fdae60877758b78885c",
        database="physics_math_youtube_db",
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )


def translate_bundle(items: list[str]) -> list[str]:
    if not items:
        return []
    combined = SEP.join(items)
    
    # If combined string is too long (> 3500 chars), translate individually or in halves
    if len(combined) > 3500 and len(items) > 1:
        mid = len(items) // 2
        return translate_bundle(items[:mid]) + translate_bundle(items[mid:])

    for client in CLIENTS:
        url = f"https://translate.googleapis.com/translate_a/single?client={client}&sl=en&tl=hi&dt=t&q=" + urllib.parse.quote(combined)
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                translated_combined = "".join(part[0] for part in data[0] if part[0])
                parts = re.split(r"\s*___XSEP___\s*", translated_combined)
                if len(parts) == len(items):
                    return [p.strip() for p in parts]
                elif len(parts) > len(items):
                    return [p.strip() for p in parts[:len(items)]]
                else:
                    return [p.strip() for p in parts] + items[len(parts):]
            except Exception:
                time.sleep(0.5 * (attempt + 1))
    return items


def is_protected(tag) -> bool:
    if tag.name in ("math", "svg", "canvas", "picture", "figure", "img", "code", "pre"):
        return True
    classes = tag.get("class", [])
    if any("mwe-math" in c for c in classes) or tag.get("typeof") == "mw:Extension/math":
        return True
    return False


def process_subtopic(subtopic_key: tuple, total: int):
    subj, cl, chap, sub = subtopic_key
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM subtopic_wiki_parts WHERE subject=%s AND class=%s AND chapter=%s AND subtopic=%s AND language='en'",
                (subj, cl, chap, sub)
            )
            part = cur.fetchone()
            if not part:
                with _lock:
                    _counts["failed"] += 1
                return

            cur.execute(
                "SELECT * FROM subtopic_wiki_html WHERE subject=%s AND class=%s AND chapter=%s AND subtopic=%s AND language='en'",
                (subj, cl, chap, sub)
            )
            html_row = cur.fetchone()

        wiki_title = html_row["wiki_title"] if html_row else f"{chap} — {sub}"
        heading = part["heading"]
        caption = part["diagram_caption"]
        raw_ph = part["paragraph_html"]

        # Parse and protect paragraph HTML
        soup = BeautifulSoup(raw_ph, "html.parser")
        blocks = soup.find_all(["p", "li", "h2", "h3", "h4", "h5", "h6", "th", "td", "figcaption"])
        if not blocks:
            blocks = [soup]

        block_placeholders = []
        block_inners = []
        tag_counter = 0

        for block in blocks:
            if not block.get_text().strip():
                continue
            placeholders = {}
            for tag in list(block.find_all(is_protected)):
                if not any(is_protected(parent) for parent in tag.parents if parent != block):
                    key = f"___M{tag_counter}___"
                    placeholders[key] = str(tag)
                    tag.replace_with(soup.new_string(key))
                    tag_counter += 1

            inner = "".join(str(c) for c in block.children)
            block_inners.append(inner)
            block_placeholders.append((block, placeholders))

        # Bundle: [wiki_title, heading, caption (if exists), ...block_inners]
        bundle = [wiki_title, heading]
        has_caption = bool(caption and caption.strip())
        if has_caption:
            bundle.append(caption.strip())
        bundle.extend(block_inners)

        translated_bundle = translate_bundle(bundle)

        hi_title = translated_bundle[0]
        hi_heading = translated_bundle[1]
        offset = 2
        if has_caption:
            hi_caption = translated_bundle[2]
            offset = 3
        else:
            hi_caption = None

        hi_block_inners = translated_bundle[offset:]

        for (block, placeholders), trans_inner in zip(block_placeholders, hi_block_inners):
            for key, orig_tag_str in placeholders.items():
                trans_inner = trans_inner.replace(key, orig_tag_str)
            new_children = BeautifulSoup(trans_inner, "html.parser")
            block.clear()
            block.append(new_children)

        hi_ph = str(soup)
        hi_p = soup.get_text(separator=" ", strip=True)

        # Diag HTML
        diag_html = ""
        if part["diagram_url"]:
            cap_txt = hi_caption or hi_title
            diag_html = f"""
            <figure style="margin: 1.5rem 0; text-align: center;">
                <img src="{part['diagram_url']}" alt="{cap_txt}" style="max-width: 100%; height: auto; border-radius: 8px;" />
                <figcaption style="font-size: 0.85rem; color: #94a3b8; margin-top: 0.5rem; text-align: center;">{cap_txt}</figcaption>
            </figure>
            """
        hi_full_html = f"<div class=\"subtopic-content\">\n{hi_ph}\n{diag_html}\n</div>"

        # Save to DB
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO subtopic_wiki_parts
                    (subject, class, chapter, subtopic, language, part_index, heading, paragraph, paragraph_html, diagram_url, diagram_caption)
                VALUES (%s, %s, %s, %s, 'hi-en', 1, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    heading = VALUES(heading),
                    paragraph = VALUES(paragraph),
                    paragraph_html = VALUES(paragraph_html),
                    diagram_url = VALUES(diagram_url),
                    diagram_caption = VALUES(diagram_caption)
                """,
                (subj, cl, chap, sub, hi_heading, hi_p, hi_ph, part["diagram_url"], hi_caption)
            )

            wiki_url = html_row["wiki_url"] if html_row else ""
            has_diag = html_row["has_diagrams"] if html_row else (1 if part["diagram_url"] else 0)
            cur.execute(
                """
                INSERT INTO subtopic_wiki_html
                    (subject, class, chapter, subtopic, language, wiki_title, wiki_url, html_content, has_diagrams)
                VALUES (%s, %s, %s, %s, 'hi-en', %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    wiki_title = VALUES(wiki_title),
                    wiki_url = VALUES(wiki_url),
                    html_content = VALUES(html_content),
                    has_diagrams = VALUES(has_diagrams)
                """,
                (subj, cl, chap, sub, hi_title, wiki_url, hi_full_html, has_diag)
            )
            conn.commit()

        time.sleep(random.uniform(0.05, 0.15))
        with _lock:
            _counts["done"] += 1
            cur_done = _counts["done"]
            if cur_done % 20 == 0 or cur_done == total:
                print(f"[{cur_done}/{total}] Translated: {chap} -> {sub[:40]}... (Heading: {hi_heading})", flush=True)
    except Exception as e:
        with _lock:
            _counts["failed"] += 1
            print(f"ERROR on {sub}: {e}", flush=True)


def main():
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    syllabus_path = os.path.join(base_dir, "syllabus.json")
    with open(syllabus_path) as f:
        syllabus = json.load(f)

    syllabus_subtopics = []
    for ch in syllabus:
        for st in ch["subtopics"]:
            syllabus_subtopics.append((ch["subject"], ch["class"], ch["chapter"], st))

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT subject, class, chapter, subtopic FROM subtopic_wiki_parts WHERE language='hi-en'")
        existing_hi = {(r["subject"], r["class"], r["chapter"], r["subtopic"]) for r in cur.fetchall()}

    pending = [k for k in syllabus_subtopics if k not in existing_hi]
    total = len(pending)
    print(f"Total syllabus subtopics: {len(syllabus_subtopics)}", flush=True)
    print(f"Already translated to hi-en: {len(existing_hi)}", flush=True)
    print(f"Pending translation: {total}", flush=True)

    if total == 0:
        print("All syllabus subtopics are already translated to Hindi!", flush=True)
        return

    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_subtopic, key, total) for key in pending]
        concurrent.futures.wait(futures)

    elapsed = time.time() - t0
    print(f"\nCompleted! Done: {_counts['done']}, Failed: {_counts['failed']} in {elapsed:.1f}s", flush=True)


if __name__ == "__main__":
    main()
