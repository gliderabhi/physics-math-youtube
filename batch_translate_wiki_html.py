import concurrent.futures
import json
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup

from generator.db import get_conn, init_db

MAX_WORKERS = 4
REQUEST_TIMEOUT = 25
SEP_PATTERN = "__X_SEP_{}__"
_lock = threading.Lock()
_counts = {"done": 0, "failed": 0, "skipped": 0}


def _translate_batch(text_list: list[str]) -> list[str]:
    if not text_list:
        return []

    # Pack items with unique separators into size-limited chunks (< 3500 chars)
    chunks = []
    current_chunk = []
    current_len = 0

    for idx, text in enumerate(text_list):
        item_str = f"\n\n{SEP_PATTERN.format(idx)}\n\n{text}"
        if current_len + len(item_str) > 3500 and current_chunk:
            chunks.append(current_chunk)
            current_chunk = [(idx, text)]
            current_len = len(item_str)
        else:
            current_chunk.append((idx, text))
            current_len += len(item_str)
    if current_chunk:
        chunks.append(current_chunk)

    results = {}
    for chunk in chunks:
        payload_parts = []
        for idx, text in chunk:
            payload_parts.append(f"\n\n{SEP_PATTERN.format(idx)}\n\n{text}")
        payload = "".join(payload_parts)

        url = "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode({
            "client": "tw-ob",
            "sl": "en",
            "tl": "hi",
            "dt": "t",
            "q": payload,
        })
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

        trans_full = payload
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                trans_full = "".join(part[0] for part in data[0] if part[0])
                break
            except Exception as e:
                time.sleep(1.5 * (attempt + 1))

        # Extract pieces using regex
        for idx, orig_text in chunk:
            m = re.search(r"__X_SEP_" + str(idx) + r"__\s*(.*?)(?=(?:__X_SEP_\d+__|$))", trans_full, re.DOTALL)
            if m:
                results[idx] = m.group(1).strip()
            else:
                results[idx] = orig_text

    return [results.get(i, text_list[i]) for i in range(len(text_list))]


def _translate_single_text(text: str) -> str:
    if not text or not text.strip():
        return text
    url = "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode({
        "client": "tw-ob", "sl": "en", "tl": "hi", "dt": "t", "q": text
    })
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return "".join(part[0] for part in data[0] if part[0])
        except Exception:
            time.sleep(1)
    return text


def is_protected(tag) -> bool:
    if tag.name in ("math", "svg", "canvas", "picture", "figure", "img", "code", "pre"):
        return True
    classes = tag.get("class", [])
    if any("mwe-math" in c for c in classes) or tag.get("typeof") == "mw:Extension/math":
        return True
    return False


def translate_wiki_html(html_str: str) -> str:
    soup = BeautifulSoup(html_str, "html.parser")

    # Find block-level text containers
    blocks = soup.find_all([
        "h1", "h2", "h3", "h4", "h5", "h6",
        "p", "li", "th", "td", "figcaption", "dt", "dd", "blockquote"
    ])

    items_to_translate = []
    block_info = []

    for block in blocks:
        # Skip if no meaningful text inside
        if not block.get_text().strip():
            continue

        placeholders = {}
        idx = 0
        for tag in list(block.find_all(is_protected)):
            # Protect only if parent is not already protected
            if not any(is_protected(parent) for parent in tag.parents if parent != block):
                key = f"__MATHIMG_{idx}__"
                placeholders[key] = str(tag)
                tag.replace_with(soup.new_string(key))
                idx += 1

        inner = "".join(str(c) for c in block.children)
        items_to_translate.append(inner)
        block_info.append((block, placeholders))

    if not items_to_translate:
        return html_str

    translated_items = _translate_batch(items_to_translate)

    # Restore placeholders into translated blocks
    for (block, placeholders), trans_inner in zip(block_info, translated_items):
        for key, orig_tag_str in placeholders.items():
            trans_inner = trans_inner.replace(key, orig_tag_str)
        new_children = BeautifulSoup(trans_inner, "html.parser")
        block.clear()
        block.append(new_children)

    return str(soup)


def get_jobs_to_process():
    with get_conn() as conn, conn.cursor() as cur:
        # Get all English rows
        cur.execute(
            "SELECT id, subject, class, chapter, subtopic, wiki_title, wiki_url, html_content, has_diagrams "
            "FROM subtopic_wiki_html WHERE language = 'en'"
        )
        en_rows = cur.fetchall()

        # Get existing Hindi subtopic keys
        cur.execute("SELECT subject, class, chapter, subtopic FROM subtopic_wiki_html WHERE language = 'hi-en'")
        existing_hi = {(r["subject"], r["class"], r["chapter"], r["subtopic"]) for r in cur.fetchall()}

    pending = [r for r in en_rows if (r["subject"], r["class"], r["chapter"], r["subtopic"]) not in existing_hi]
    return pending, len(existing_hi), len(en_rows)


def save_hindi_row(subject: str, class_: int, chapter: str, subtopic: str, wiki_title: str, wiki_url: str, html: str, has_diagrams: int):
    with get_conn() as conn, conn.cursor() as cur:
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
            (subject, class_, chapter, subtopic, wiki_title, wiki_url, html, has_diagrams)
        )


def process_subtopic(row, total: int):
    subtopic = row["subtopic"]
    chapter = row["chapter"]
    subject = row["subject"]
    class_ = row["class"]
    title = row["wiki_title"]
    html = row["html_content"]
    url = row["wiki_url"]
    has_diagrams = row["has_diagrams"]

    try:
        # 1. Translate title
        hi_title = _translate_single_text(title)

        # 2. Translate HTML while preserving formulas and diagrams
        hi_html = translate_wiki_html(html)

        # 3. Save duplicate row for Hindi ('hi-en')
        save_hindi_row(subject, class_, chapter, subtopic, hi_title, url, hi_html, has_diagrams)

        with _lock:
            _counts["done"] += 1
            idx = _counts["done"] + _counts["failed"]
            print(f"[{idx}/{total}] OK: {subject} c{class_} | {chapter} | {subtopic} -> '{hi_title}' ({len(hi_html)} bytes)")
    except Exception as e:
        with _lock:
            _counts["failed"] += 1
            idx = _counts["done"] + _counts["failed"]
            print(f"[{idx}/{total}] FAILED: {subject} c{class_} | {chapter} | {subtopic} -- {e}")


def main():
    init_db()
    pending, existing_count, total_en = get_jobs_to_process()
    total = len(pending)
    print(f"Total English subtopics in DB: {total_en}")
    print(f"Already translated to Hindi: {existing_count}")
    print(f"Pending translation to Hindi: {total}")

    if total == 0:
        print("All subtopics already have duplicate Hindi rows!")
        return

    t_start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(process_subtopic, row, total) for row in pending]
        concurrent.futures.wait(futures)

    t_total = time.time() - t_start
    print(f"\nBatch Hindi translation complete in {t_total:.1f}s!")
    print(f"Done: {_counts['done']}, Failed: {_counts['failed']}")


if __name__ == "__main__":
    main()
