import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup

from generator.curriculum import load_syllabus
from generator.db import get_conn, init_db

USER_AGENT = "physics-math-youtube-edu/2.0 (educational tool; contact@sevis.local)"
REQUEST_DELAY = 1.2  # seconds between Wikimedia requests
_last_request_time = 0.0

DISCARD_SECTION_TITLES = {
    "see also", "references", "external links", "further reading",
    "notes", "bibliography", "sources", "citations"
}

NOISE_IMG_RE = re.compile(
    r"(icon|logo|ambox|wiktionary|commons[\s_-]|edit[\s_-]|question[\s_-]?book|disambig|p[\s_]vip|folder|wikisource|padlock|portal)",
    re.IGNORECASE,
)


def _rate_limited_get(url: str, retries: int = 4) -> str | None:
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < REQUEST_DELAY:
        time.sleep(REQUEST_DELAY - elapsed)

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        try:
            _last_request_time = time.time()
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 429:
                sleep_time = (attempt + 1) * 3
                print(f" [Rate-limited 429, sleeping {sleep_time}s...]", end="", flush=True)
                time.sleep(sleep_time)
                continue
            elif e.code == 404:
                return None
            print(f" [HTTP {e.code}]", end="", flush=True)
            return None
        except Exception as e:
            print(f" [Req error: {e}]", end="", flush=True)
            time.sleep(2)
    return None


def search_wikipedia_title(subtopic: str, chapter: str, subject: str) -> str | None:
    # Try searching subtopic directly, then with chapter/subject context if needed
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
        raw = _rate_limited_get(api_url)
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
    raw_html = _rate_limited_get(rest_url)
    if not raw_html:
        return None

    soup = BeautifulSoup(raw_html, "html.parser")

    # Remove non-content tags
    for tag in soup(["script", "style", "link", "noscript"]):
        tag.decompose()

    # Remove Wikipedia UI elements, navigation, citations, and maintenance templates
    for selector in [
        ".mw-ref", "sup.reference", ".mw-editsection", ".navbox", ".vertical-navbox",
        ".noprint", ".metadata", ".mw-empty-elt", ".hatnote", ".side-box",
        ".infobox", ".ambox", "header", "footer"
    ]:
        for el in soup.select(selector):
            el.decompose()

    # Strip out trailing sections like "See also", "References", "External links"
    for sec in soup.find_all("section"):
        header = sec.find(["h2", "h3", "h4"])
        if header:
            h_text = header.get_text(strip=True).lower()
            if any(term in h_text for term in DISCARD_SECTION_TITLES):
                sec.decompose()

    has_diagrams = False
    # Clean images and diagrams
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src or NOISE_IMG_RE.search(src):
            # Check if parent is a figure, if so remove figure or img
            if img.parent and img.parent.name == "figure":
                img.parent.decompose()
            else:
                img.decompose()
            continue

        # Convert to absolute URL
        if src.startswith("//"):
            img["src"] = "https:" + src
        elif src.startswith("/"):
            img["src"] = "https://en.wikipedia.org" + src

        # Ensure responsive display
        img["style"] = "max-width: 100%; height: auto; border-radius: 8px;"
        has_diagrams = True

    # Style figures and captions
    for fig in soup.find_all("figure"):
        fig["style"] = "margin: 1.5rem 0; text-align: center;"
        cap = fig.find("figcaption")
        if cap:
            cap["style"] = "font-size: 0.85rem; color: #94a3b8; margin-top: 0.5rem; text-align: center;"

    # Clean links (open in new tab and style nicely)
    for a in soup.find_all("a"):
        href = a.get("href", "")
        if href.startswith("./"):
            a["href"] = f"https://en.wikipedia.org/wiki/{href[2:]}"
        elif href.startswith("/"):
            a["href"] = f"https://en.wikipedia.org{href}"
        a["target"] = "_blank"
        a["rel"] = "noopener noreferrer"

    # Find the main container
    body = soup.find("body") or soup
    clean_html = "".join(str(child) for child in body.children if child.name).strip()

    return {
        "title": title,
        "source_url": f"https://en.wikipedia.org/wiki/{encoded_title}",
        "html": clean_html,
        "has_diagrams": 1 if has_diagrams else 0,
    }


def get_existing_saved() -> set[tuple]:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT subject, chapter, subtopic FROM subtopic_wiki_html")
        return {(r["subject"], r["chapter"], r["subtopic"]) for r in cur.fetchall()}


def save_subtopic_html(subject: str, chapter: str, subtopic: str, data: dict):
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO subtopic_wiki_html
                (subject, chapter, subtopic, wiki_title, wiki_url, html_content, has_diagrams)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                wiki_title = VALUES(wiki_title),
                wiki_url = VALUES(wiki_url),
                html_content = VALUES(html_content),
                has_diagrams = VALUES(has_diagrams)
            """,
            (
                subject,
                chapter,
                subtopic,
                data["title"],
                data["source_url"],
                data["html"],
                data["has_diagrams"],
            ),
        )


def main():
    init_db()
    syllabus = load_syllabus()
    existing = get_existing_saved()

    all_jobs = []
    for ch in syllabus:
        for subtopic in ch["subtopics"]:
            key = (ch["subject"], ch["chapter"], subtopic)
            if key not in existing:
                all_jobs.append((ch["subject"], ch["chapter"], subtopic))

    total = len(all_jobs)
    print(f"Total subtopics pending: {total} (Already in DB: {len(existing)})")

    if total == 0:
        print("All subtopics are already populated in subtopic_wiki_html!")
        return

    success_count = 0
    fail_count = 0

    for idx, (subject, chapter, subtopic) in enumerate(all_jobs, 1):
        print(f"[{idx}/{total}] {subject} | {chapter} | {subtopic}...", end="", flush=True)

        wiki_title = search_wikipedia_title(subtopic, chapter, subject)
        if not wiki_title:
            print(" [No Wikipedia title match - SKIPPED]")
            fail_count += 1
            continue

        data = fetch_and_clean_html(wiki_title)
        if not data or not data["html"]:
            print(f" [Found '{wiki_title}' but failed to fetch clean HTML - SKIPPED]")
            fail_count += 1
            continue

        save_subtopic_html(subject, chapter, subtopic, data)
        success_count += 1
        print(f" OK -> '{wiki_title}' ({len(data['html'])} bytes, diagrams: {bool(data['has_diagrams'])})")

    print(f"\nDone! Successfully pulled: {success_count}, Skipped/Failed: {fail_count}")


if __name__ == "__main__":
    main()
