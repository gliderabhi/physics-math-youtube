"""
Complete pipeline to ingest, extract, expand, and translate Chemistry and Biology topics.
"""
import concurrent.futures
import json
import os
import random
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import pymysql

USER_AGENT = "physics-math-youtube-edu/2.0 (educational tool; contact@sevis.local)"
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "physics_yt_app",
    "password": "abbbc8eff2c24fdae60877758b78885c",
    "database": "physics_math_youtube_db",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit": True,
}

DISCARD_SECTION_TITLES = {
    "see also", "references", "external links", "further reading",
    "notes", "bibliography", "sources", "citations"
}

NOISE_IMG_RE = re.compile(
    r"(icon|logo|ambox|wiktionary|commons[\s_-]|edit[\s_-]|question[\s_-]?book|disambig|p[\s_]vip|folder|wikisource|padlock|portal|stylised[\s_-]?atom|crystal[\s_-]?clear|magnify|speaker)",
    re.IGNORECASE,
)

SKIP_HEADINGS = {
    "see also", "references", "external links", "further reading",
    "notes", "bibliography", "sources", "citations", "history",
    "etymology", "in popular culture", "footnotes", "navigation",
    "applications in other fields", "timeline", "notable figures",
    "external media", "gallery"
}

def get_conn():
    return pymysql.connect(**DB_CONFIG)

_last_request_time = 0.0
_req_lock = threading.Lock()

def rate_limited_get(url: str, retries: int = 4, delay: float = 0.4) -> str | None:
    global _last_request_time
    with _req_lock:
        now = time.time()
        elapsed = now - _last_request_time
        if elapsed < delay:
            time.sleep(delay - elapsed)
        _last_request_time = time.time()

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                sleep_time = (attempt + 1) * 2
                time.sleep(sleep_time)
                continue
            elif e.code == 404:
                return None
            time.sleep(1)
        except Exception:
            time.sleep(1)
    return None

def search_wikipedia_title(subtopic: str, chapter: str, subject: str) -> str | None:
    queries = [
        subtopic,
        f"{subtopic} {chapter}",
        f"{subtopic} {subject}",
    ]
    for q in queries:
        api_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query",
            "list": "search",
            "srsearch": q,
            "format": "json",
            "srlimit": 3,
        })
        raw = rate_limited_get(api_url, delay=0.2)
        if not raw:
            continue
        try:
            data = json.loads(raw)
            hits = data.get("query", {}).get("search", [])
            if hits:
                return hits[0]["title"]
        except Exception:
            continue
    return None

def fetch_and_clean_html(title: str) -> dict | None:
    encoded_title = urllib.parse.quote(title.replace(" ", "_"))
    rest_url = f"https://en.wikipedia.org/api/rest_v1/page/html/{encoded_title}"
    raw_html = rate_limited_get(rest_url, delay=0.2)
    if not raw_html:
        return None

    soup = BeautifulSoup(raw_html, "html.parser")

    for tag in soup(["script", "style", "link", "noscript"]):
        tag.decompose()

    for selector in [
        ".mw-ref", "sup.reference", ".mw-editsection", ".navbox", ".vertical-navbox",
        ".noprint", ".metadata", ".mw-empty-elt", ".hatnote", ".side-box",
        ".infobox", ".ambox", "header", "footer"
    ]:
        for el in soup.select(selector):
            el.decompose()

    for sec in soup.find_all("section"):
        header = sec.find(["h2", "h3", "h4"])
        if header:
            h_text = header.get_text(strip=True).lower()
            if any(term in h_text for term in DISCARD_SECTION_TITLES):
                sec.decompose()

    has_diagrams = False
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src or NOISE_IMG_RE.search(src):
            if img.parent and img.parent.name == "figure":
                img.parent.decompose()
            else:
                img.decompose()
            continue

        if src.startswith("//"):
            img["src"] = "https:" + src
        elif src.startswith("/"):
            img["src"] = "https://en.wikipedia.org" + src

        img["style"] = "max-width: 100%; height: auto; border-radius: 8px;"
        has_diagrams = True

    for fig in soup.find_all("figure"):
        fig["style"] = "margin: 1.5rem 0; text-align: center;"
        cap = fig.find("figcaption")
        if cap:
            cap["style"] = "font-size: 0.85rem; color: #94a3b8; margin-top: 0.5rem; text-align: center;"

    for a in soup.find_all("a"):
        href = a.get("href", "")
        if href.startswith("./"):
            a["href"] = f"https://en.wikipedia.org/wiki/{href[2:]}"
        elif href.startswith("/"):
            a["href"] = f"https://en.wikipedia.org{href}"
        a["target"] = "_blank"
        a["rel"] = "noopener noreferrer"

    body = soup.find("body") or soup
    clean_html = "".join(str(child) for child in body.children if child.name).strip()

    return {
        "title": title,
        "source_url": f"https://en.wikipedia.org/wiki/{encoded_title}",
        "html": clean_html,
        "has_diagrams": 1 if has_diagrams else 0,
    }

def extract_parts_from_html(html_content: str, max_parts: int = 7) -> list[dict]:
    soup = BeautifulSoup(html_content, "html.parser")
    sections = soup.find_all("section")
    if not sections:
        sections = [soup]

    parts = []
    part_idx = 1

    for sec in sections:
        h = sec.find(["h2", "h3", "h4"])
        if h:
            raw_h = h.get_text(strip=True)
            heading = re.sub(r"\[edit\]|\#.*", "", raw_h, flags=re.IGNORECASE).strip()
        else:
            heading = "Overview & Core Concept"

        if not heading or any(skip in heading.lower() for skip in SKIP_HEADINGS):
            continue

        paras = []
        for p in sec.find_all("p", recursive=False):
            txt = p.get_text(strip=True)
            if len(txt) >= 40:
                paras.append(p)
        if not paras:
            for p in sec.find_all("p"):
                txt = p.get_text(strip=True)
                if len(txt) >= 40 and p not in paras:
                    paras.append(p)

        if not paras:
            continue

        chosen_paras = paras[:3]
        combined_text = "\n\n".join(p.get_text(strip=True) for p in chosen_paras)
        combined_html = "".join(str(p) for p in chosen_paras)

        diagram_url = None
        diagram_caption = None
        for fig in sec.find_all("figure"):
            img = fig.find("img")
            if img and img.get("src"):
                src = img["src"]
                if ("commons" in src or "upload.wikimedia.org" in src) and not NOISE_IMG_RE.search(src):
                    diagram_url = src
                    cap = fig.find("figcaption")
                    if cap:
                        diagram_caption = cap.get_text(strip=True)
                    break

        if not diagram_url:
            for img in sec.find_all("img"):
                src = img.get("src", "")
                if ("commons" in src or "upload.wikimedia.org" in src) and "math/render" not in src:
                    if not NOISE_IMG_RE.search(src):
                        diagram_url = src
                        diagram_caption = img.get("alt")
                        break

        parts.append({
            "part_index": part_idx,
            "heading": heading,
            "paragraph": combined_text,
            "paragraph_html": combined_html,
            "diagram_url": diagram_url,
            "diagram_caption": diagram_caption,
        })
        part_idx += 1
        if len(parts) >= max_parts:
            break

    return parts

# ----------------- STAGE 1: PULL WIKI HTML -----------------
def stage1_pull_wiki_html(items: list[tuple[str, str, str]]):
    print(f"\n=== STAGE 1: PULL WIKIPEDIA HTML ({len(items)} subtopics) ===")
    
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT subject, chapter, subtopic FROM subtopic_wiki_html WHERE language='en'")
        existing = {(r["subject"], r["chapter"], r["subtopic"]) for r in cur.fetchall()}

    pending = [it for it in items if it not in existing]
    print(f"Total: {len(items)}, Already in DB: {len(existing)}, Pending: {len(pending)}")
    if not pending:
        print("Stage 1 already complete!")
        return

    lock = threading.Lock()
    done_count = 0
    fail_count = 0

    def worker(item):
        nonlocal done_count, fail_count
        subj, chap, sub = item
        wiki_title = search_wikipedia_title(sub, chap, subj)
        if not wiki_title:
            with lock:
                fail_count += 1
            print(f"  [MISS] No title for: {subj} | {chap} | {sub}")
            return

        data = fetch_and_clean_html(wiki_title)
        if not data or not data["html"]:
            with lock:
                fail_count += 1
            print(f"  [FAIL] Failed HTML for: {wiki_title}")
            return

        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO subtopic_wiki_html
                    (subject, chapter, subtopic, language, wiki_title, wiki_url, html_content, has_diagrams)
                VALUES (%s, %s, %s, 'en', %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    wiki_title = VALUES(wiki_title),
                    wiki_url = VALUES(wiki_url),
                    html_content = VALUES(html_content),
                    has_diagrams = VALUES(has_diagrams)
            """, (
                subj, chap, sub,
                data["title"], data["source_url"], data["html"], data["has_diagrams"]
            ))

        with lock:
            done_count += 1
            cnt = done_count
            if cnt % 10 == 0 or cnt == len(pending):
                print(f"  [{cnt}/{len(pending)}] Saved: {subj} | {chap} | {sub} -> {data['title']}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, it) for it in pending]
        concurrent.futures.wait(futures)

    print(f"Stage 1 done! Saved: {done_count}, Missed/Failed: {fail_count}")

# ----------------- STAGE 2: EXTRACT WIKI PARTS -----------------
def stage2_extract_wiki_parts(subjects: list[str]):
    print(f"\n=== STAGE 2: EXTRACT WIKI PARTS (Subjects: {subjects}) ===")
    with get_conn() as conn, conn.cursor() as cur:
        subj_placeholders = ",".join(["%s"] * len(subjects))
        cur.execute(f"""
            SELECT h.id, h.subject, h.chapter, h.subtopic, h.language, h.wiki_title, h.html_content
            FROM subtopic_wiki_html h
            WHERE h.language = 'en' AND h.subject IN ({subj_placeholders})
            AND NOT EXISTS (
                SELECT 1 FROM subtopic_wiki_parts p
                WHERE p.subject = h.subject AND p.chapter = h.chapter AND p.subtopic = h.subtopic AND p.language = h.language
            )
        """, subjects)
        rows = cur.fetchall()

    print(f"Rows pending part extraction: {len(rows)}")
    if not rows:
        print("Stage 2 already complete!")
        return

    total_parts = 0
    for idx, r in enumerate(rows, 1):
        subj = r["subject"]
        chap = r["chapter"]
        sub = r["subtopic"]
        lang = r["language"]
        html = r["html_content"]

        parts = extract_parts_from_html(html)
        if not parts:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            parts = [{
                "part_index": 1,
                "heading": sub,
                "paragraph": text[:1500],
                "paragraph_html": f"<p>{text[:1500]}</p>",
                "diagram_url": None,
                "diagram_caption": None,
            }]

        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM subtopic_wiki_parts WHERE subject=%s AND chapter=%s AND subtopic=%s AND language=%s",
                (subj, chap, sub, lang),
            )
            for p in parts:
                cur.execute("""
                    INSERT INTO subtopic_wiki_parts
                        (subject, chapter, subtopic, language, part_index, heading, paragraph, paragraph_html, diagram_url, diagram_caption)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    subj, chap, sub, lang,
                    p["part_index"], p["heading"], p["paragraph"], p["paragraph_html"],
                    p["diagram_url"][:2000] if p["diagram_url"] else None, p["diagram_caption"]
                ))

        total_parts += len(parts)
        if idx % 20 == 0 or idx == len(rows):
            print(f"  [{idx}/{len(rows)}] Extracted parts for {subj} | {chap} | {sub} (Total parts: {total_parts})")

    print(f"Stage 2 done! Extracted {total_parts} parts across {len(rows)} subtopics.")

# ----------------- STAGE 3: EXPAND GRANULAR SUBTOPICS -----------------
def stage3_expand_granular_subtopics(syllabus_file: str, new_subjects: list[str]):
    print(f"\n=== STAGE 3: EXPAND GRANULAR SUBTOPICS FOR {new_subjects} ===")
    with open(syllabus_file) as f:
        syllabus = json.load(f)

    with get_conn() as conn, conn.cursor() as cur:
        subj_placeholders = ",".join(["%s"] * len(new_subjects))
        cur.execute(f"SELECT subject, chapter, subtopic, wiki_title, wiki_url FROM subtopic_wiki_html WHERE language='en' AND subject IN ({subj_placeholders})", new_subjects)
        parent_meta = {(r["subject"], r["chapter"], r["subtopic"]): r for r in cur.fetchall()}

        cur.execute(f"""
            SELECT subject, chapter, subtopic, part_index, heading, paragraph, paragraph_html, diagram_url, diagram_caption
            FROM subtopic_wiki_parts
            WHERE language='en' AND subject IN ({subj_placeholders})
            ORDER BY subject, chapter, subtopic, part_index
        """, new_subjects)
        all_parts = cur.fetchall()

    from collections import defaultdict
    parts_by_sub = defaultdict(list)
    for r in all_parts:
        parts_by_sub[(r["subject"], r["chapter"], r["subtopic"])].append(r)

    new_syllabus = []
    granular_entries = []

    for entry in syllabus:
        subj = entry["subject"]
        cl = entry["class"]
        chap = entry["chapter"]

        if subj not in new_subjects:
            # Keep existing physics/math chapters as-is!
            new_syllabus.append(entry)
            continue

        chapter_subtopics = []
        seen_in_chapter = set()

        for parent_sub in entry["subtopics"]:
            key = (subj, chap, parent_sub)
            parts = parts_by_sub.get(key, [])
            meta = parent_meta.get(key, {"wiki_title": parent_sub, "wiki_url": ""})

            if not parts:
                if parent_sub not in seen_in_chapter:
                    chapter_subtopics.append(parent_sub)
                    seen_in_chapter.add(parent_sub)
                continue

            for p in parts:
                h = p["heading"].strip()
                if h.lower() in ("overview & core concept", "overview", "introduction"):
                    name = f"{parent_sub}: Overview & Foundations"
                else:
                    name = f"{parent_sub}: {h}"

                orig_name = name
                suffix = 2
                while name in seen_in_chapter:
                    name = f"{orig_name} (Part {suffix})"
                    suffix += 1

                seen_in_chapter.add(name)
                chapter_subtopics.append(name)

                diag_html = ""
                if p["diagram_url"]:
                    cap_txt = p["diagram_caption"] or name
                    diag_html = f"""
                    <figure style="margin: 1.5rem 0; text-align: center;">
                        <img src="{p['diagram_url']}" alt="{cap_txt}" style="max-width: 100%; height: auto; border-radius: 8px;" />
                        <figcaption style="font-size: 0.85rem; color: #94a3b8; margin-top: 0.5rem; text-align: center;">{cap_txt}</figcaption>
                    </figure>
                    """
                full_html = f"<div class=\"subtopic-content\">\n{p['paragraph_html']}\n{diag_html}\n</div>"

                granular_entries.append({
                    "subject": subj,
                    "class": cl,
                    "chapter": chap,
                    "subtopic": name,
                    "wiki_title": f"{meta['wiki_title']} — {p['heading']}",
                    "wiki_url": meta["wiki_url"],
                    "html_content": full_html,
                    "has_diagrams": 1 if p["diagram_url"] else 0,
                    "part": p,
                })

        new_syllabus.append({
            "class": cl,
            "subject": subj,
            "chapter": chap,
            "subtopics": chapter_subtopics
        })

    # Save new syllabus.json
    with open(syllabus_file, "w") as f:
        json.dump(new_syllabus, f, indent=2)

    print(f"Updated {syllabus_file}: {len(granular_entries)} granular subtopics created for {new_subjects}.")
    print(f"Total chapters in new syllabus: {len(new_syllabus)}")

    # Insert granular entries into subtopic_wiki_html and subtopic_wiki_parts
    print(f"Inserting {len(granular_entries)} granular subtopics into DB...")
    with get_conn() as conn, conn.cursor() as cur:
        for idx, entry in enumerate(granular_entries, 1):
            cur.execute("""
                INSERT INTO subtopic_wiki_html
                    (subject, chapter, subtopic, language, wiki_title, wiki_url, html_content, has_diagrams)
                VALUES (%s, %s, %s, 'en', %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    wiki_title = VALUES(wiki_title),
                    wiki_url = VALUES(wiki_url),
                    html_content = VALUES(html_content),
                    has_diagrams = VALUES(has_diagrams)
            """, (
                entry["subject"], entry["chapter"], entry["subtopic"],
                entry["wiki_title"], entry["wiki_url"], entry["html_content"], entry["has_diagrams"]
            ))

            p = entry["part"]
            cur.execute("""
                INSERT INTO subtopic_wiki_parts
                    (subject, chapter, subtopic, language, part_index, heading, paragraph, paragraph_html, diagram_url, diagram_caption)
                VALUES (%s, %s, %s, 'en', 1, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    heading = VALUES(heading),
                    paragraph = VALUES(paragraph),
                    paragraph_html = VALUES(paragraph_html),
                    diagram_url = VALUES(diagram_url),
                    diagram_caption = VALUES(diagram_caption)
            """, (
                entry["subject"], entry["chapter"], entry["subtopic"],
                p["heading"], p["paragraph"], p["paragraph_html"], p["diagram_url"][:2000] if p["diagram_url"] else None, p["diagram_caption"]
            ))

            if idx % 100 == 0 or idx == len(granular_entries):
                print(f"  [{idx}/{len(granular_entries)}] Granular rows written to DB...")

    print("Stage 3 done!")

# ----------------- STAGE 4: TRANSLATE TO HINDI (hi-en) -----------------
SEP = " ___XSEP___ "
CLIENTS = ["dict-chrome-ex", "it"]

def translate_bundle(items: list[str]) -> list[str]:
    if not items:
        return []
    combined = SEP.join(items)
    if len(combined) > 3500 and len(items) > 1:
        mid = len(items) // 2
        return translate_bundle(items[:mid]) + translate_bundle(items[mid:])

    for client in CLIENTS:
        url = f"https://translate.googleapis.com/translate_a/single?client={client}&sl=en&tl=hi&dt=t&q=" + urllib.parse.quote(combined)
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
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

def stage4_translate_to_hindi(syllabus_file: str, target_subjects: list[str]):
    print(f"\n=== STAGE 4: TRANSLATE GRANULAR SUBTOPICS TO HINDI (hi-en) FOR {target_subjects} ===")
    with open(syllabus_file) as f:
        syllabus = json.load(f)

    target_items = []
    for entry in syllabus:
        if entry["subject"] in target_subjects:
            for st in entry["subtopics"]:
                target_items.append((entry["subject"], entry["chapter"], st))

    with get_conn() as conn, conn.cursor() as cur:
        subj_placeholders = ",".join(["%s"] * len(target_subjects))
        cur.execute(f"SELECT subject, chapter, subtopic FROM subtopic_wiki_parts WHERE language='hi-en' AND subject IN ({subj_placeholders})", target_subjects)
        existing_hi = {(r["subject"], r["chapter"], r["subtopic"]) for r in cur.fetchall()}

    pending = [k for k in target_items if k not in existing_hi]
    print(f"Total target subtopics: {len(target_items)}, Already translated: {len(existing_hi)}, Pending: {len(pending)}")
    if not pending:
        print("Stage 4 already complete!")
        return

    lock = threading.Lock()
    done_count = 0
    fail_count = 0

    def worker(item):
        nonlocal done_count, fail_count
        subj, chap, sub = item
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM subtopic_wiki_parts WHERE subject=%s AND chapter=%s AND subtopic=%s AND language='en' LIMIT 1",
                    (subj, chap, sub)
                )
                part = cur.fetchone()
                if not part:
                    with lock:
                        fail_count += 1
                    return

                cur.execute(
                    "SELECT * FROM subtopic_wiki_html WHERE subject=%s AND chapter=%s AND subtopic=%s AND language='en' LIMIT 1",
                    (subj, chap, sub)
                )
                html_row = cur.fetchone()

            wiki_title = html_row["wiki_title"] if html_row else f"{chap} — {sub}"
            heading = part["heading"]
            caption = part["diagram_caption"]
            raw_ph = part["paragraph_html"]

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

            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO subtopic_wiki_parts
                        (subject, chapter, subtopic, language, part_index, heading, paragraph, paragraph_html, diagram_url, diagram_caption)
                    VALUES (%s, %s, %s, 'hi-en', 1, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        heading = VALUES(heading),
                        paragraph = VALUES(paragraph),
                        paragraph_html = VALUES(paragraph_html),
                        diagram_url = VALUES(diagram_url),
                        diagram_caption = VALUES(diagram_caption)
                """, (subj, chap, sub, hi_heading, hi_p, hi_ph, part["diagram_url"][:2000] if part["diagram_url"] else None, hi_caption))

                wiki_url = html_row["wiki_url"] if html_row else ""
                has_diag = html_row["has_diagrams"] if html_row else (1 if part["diagram_url"] else 0)
                cur.execute("""
                    INSERT INTO subtopic_wiki_html
                        (subject, chapter, subtopic, language, wiki_title, wiki_url, html_content, has_diagrams)
                    VALUES (%s, %s, %s, 'hi-en', %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        wiki_title = VALUES(wiki_title),
                        wiki_url = VALUES(wiki_url),
                        html_content = VALUES(html_content),
                        has_diagrams = VALUES(has_diagrams)
                """, (subj, chap, sub, hi_title, wiki_url, hi_full_html, has_diag))

            with lock:
                done_count += 1
                cur_done = done_count
                if cur_done % 20 == 0 or cur_done == len(pending):
                    print(f"  [{cur_done}/{len(pending)}] Translated: {chap} -> {sub[:40]}... (Heading: {hi_heading})", flush=True)

        except Exception as e:
            with lock:
                fail_count += 1
            print(f"  ERROR on {sub}: {e}", flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(worker, it) for it in pending]
        concurrent.futures.wait(futures)

    print(f"Stage 4 done! Translated: {done_count}, Failed: {fail_count}")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    syllabus_path = os.path.join(base_dir, "syllabus.json")

    # Load chemistry and biology parent subtopics
    with open(os.path.join(base_dir, "chemistry_syllabus.json")) as f:
        chem = json.load(f)
    with open(os.path.join(base_dir, "biology_syllabus.json")) as f:
        bio = json.load(f)

    # 1. First merge parent entries into syllabus.json if not already merged
    with open(syllabus_path) as f:
        existing_s = json.load(f)

    existing_keys = {(e["subject"], e["class"], e["chapter"]) for e in existing_s}
    added = False
    for entry in chem + bio:
        key = (entry["subject"], entry["class"], entry["chapter"])
        if key not in existing_keys:
            existing_s.append(entry)
            existing_keys.add(key)
            added = True

    if added:
        with open(syllabus_path, "w") as f:
            json.dump(existing_s, f, indent=2)
        print(f"Merged parent entries into {syllabus_path}")

    # Gather items for Stage 1
    items_stage1 = []
    for ch in chem + bio:
        for st in ch["subtopics"]:
            items_stage1.append((ch["subject"], ch["chapter"], st))

    # STAGE 1
    stage1_pull_wiki_html(items_stage1)

    # STAGE 2
    stage2_extract_wiki_parts(["chemistry", "biology"])

    # STAGE 3
    stage3_expand_granular_subtopics(syllabus_path, ["chemistry", "biology"])

    # STAGE 4
    stage4_translate_to_hindi(syllabus_path, ["chemistry", "biology"])

    print("\n🎉 ALL 4 PIPELINE STAGES COMPLETED FOR CHEMISTRY & BIOLOGY!")

if __name__ == "__main__":
    main()
