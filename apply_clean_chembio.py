"""
Apply clean, cohesive NCERT subtopics for Chemistry and Biology.
"""
import concurrent.futures
import json
import os
import re
import sys
import threading
import time
import urllib.parse
import urllib.request
from bs4 import BeautifulSoup
import pymysql

from clean_chembio_syllabus import CHEMISTRY_SYLLABUS, BIOLOGY_SYLLABUS

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

CURATED_OVERRIDES = {
    ("chemistry", "Acids Bases and Salts", "Lewis Acids and Bases"): "Lewis acids and bases",
    ("chemistry", "Equilibrium", "Lewis Acids and Bases"): "Lewis acids and bases",
    ("biology", "Tissues", "Meristematic Tissue"): "Meristem",
    ("biology", "Tissues", "Permanent Tissue"): "Plant tissue",
    ("biology", "Anatomy of Flowering Plants", "Meristematic Tissue"): "Meristem",
    ("biology", "Anatomy of Flowering Plants", "Permanent Tissue"): "Plant tissue",
    ("biology", "Anatomy of Flowering Plants", "Permanent Tissues in Plants"): "Plant tissue",
}

def get_conn():
    return pymysql.connect(**DB_CONFIG)

_last_request_time = 0.0
_req_lock = threading.Lock()

def rate_limited_get(url: str, retries: int = 4, delay: float = 0.3) -> str | None:
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
    if (subject, chapter, subtopic) in CURATED_OVERRIDES:
        return CURATED_OVERRIDES[(subject, chapter, subtopic)]

    # Clean subtopic of extra parentheses for search
    clean_sub = re.sub(r"\(.*?\)", "", subtopic).strip()
    queries = [
        clean_sub,
        subtopic,
        f"{clean_sub} {chapter}",
        f"{clean_sub} {subject}",
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

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    syllabus_path = os.path.join(base_dir, "syllabus.json")

    # 1. Load current syllabus and filter out bloated chemistry/biology
    with open(syllabus_path) as f:
        current_syllabus = json.load(f)

    clean_syllabus = [e for e in current_syllabus if e["subject"] not in ("chemistry", "biology")]
    print(f"Preserved {len(clean_syllabus)} physics/math chapters.")

    # 2. Add curated clean chemistry and biology
    clean_syllabus.extend(CHEMISTRY_SYLLABUS)
    clean_syllabus.extend(BIOLOGY_SYLLABUS)

    total_chapters = len(clean_syllabus)
    total_subtopics = sum(len(e["subtopics"]) for e in clean_syllabus)
    print(f"New Clean Syllabus: {total_chapters} chapters, {total_subtopics} subtopics")

    # 3. Save new syllabus.json
    with open(syllabus_path, "w") as f:
        json.dump(clean_syllabus, f, indent=2)
    print(f"Saved {syllabus_path}!")

    # 4. Check missing Wikipedia HTML for Chemistry and Biology
    target_items = []
    for ch in CHEMISTRY_SYLLABUS + BIOLOGY_SYLLABUS:
        for st in ch["subtopics"]:
            target_items.append((ch["subject"], ch["chapter"], st))

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT subject, chapter, subtopic FROM subtopic_wiki_html WHERE language='en'")
        existing_en = {(r["subject"], r["chapter"], r["subtopic"]) for r in cur.fetchall()}

    pending = [it for it in target_items if it not in existing_en]
    print(f"Total clean subtopics: {len(target_items)}, Already have English HTML: {len(target_items) - len(pending)}, Pending: {len(pending)}")

    if pending:
        print(f"Fetching Wikipedia HTML for {len(pending)} subtopics...")
        lock = threading.Lock()
        done = 0

        def fetch_worker(it):
            nonlocal done
            subj, chap, sub = it
            wtitle = search_wikipedia_title(sub, chap, subj)
            if not wtitle:
                print(f"  [MISS] No title for: {subj} | {chap} | {sub}")
                return
            data = fetch_and_clean_html(wtitle)
            if not data or not data["html"]:
                print(f"  [FAIL] Failed HTML for: {wtitle}")
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
                done += 1
                if done % 10 == 0 or done == len(pending):
                    print(f"  [{done}/{len(pending)}] Saved clean HTML: {subj} | {chap} | {sub} -> {data['title']}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(fetch_worker, it) for it in pending]
            concurrent.futures.wait(futures)

    print("\nRestarting physics-service to reload syllabus...")
    os.system("systemctl --user restart physics-service")
    time.sleep(1)
    print("Clean curriculum successfully applied!")

if __name__ == "__main__":
    main()
