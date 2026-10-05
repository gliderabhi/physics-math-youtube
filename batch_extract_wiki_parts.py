import json
import re
import sys
import time
from bs4 import BeautifulSoup
from generator.db import get_conn, init_db
from generator.wiki_store import save_subtopic_parts

NOISE_IMG_RE = re.compile(
    r"(icon|logo|ambox|wiktionary|commons[\s_-]|edit[\s_-]|question[\s_-]?book|disambig|p[\s_]vip|folder|wikisource|padlock|portal|stylised[\s_-]?atom|physics[\s_-]?symbol|crystal[\s_-]?clear|magnify|speaker)",
    re.IGNORECASE,
)

SKIP_HEADINGS = {
    "see also", "references", "external links", "further reading",
    "notes", "bibliography", "sources", "citations", "history",
    "etymology", "in popular culture", "footnotes", "navigation",
    "applications in other fields", "timeline", "notable figures",
    "external media", "gallery"
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

        # Collect paragraphs
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

        # Keep top 1-3 most substantial paragraphs
        chosen_paras = paras[:3]
        combined_text = "\n\n".join(p.get_text(strip=True) for p in chosen_paras)
        combined_html = "".join(str(p) for p in chosen_paras)

        # Look for real diagram
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


def main():
    init_db()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, subject, class, chapter, subtopic, language, wiki_title, html_content FROM subtopic_wiki_html WHERE language='en'")
        rows = cur.fetchall()

    total = len(rows)
    print(f"Extracting subtopic parts for {total} English subtopics...")
    t0 = time.time()
    total_parts_created = 0

    for idx, r in enumerate(rows, 1):
        subj = r["subject"]
        cl = r["class"]
        chap = r["chapter"]
        sub = r["subtopic"]
        lang = r["language"]
        html = r["html_content"]

        parts = extract_parts_from_html(html)
        if not parts:
            # Fallback if no sections/paras caught: create single overview part
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

        save_subtopic_parts(subj, cl, chap, sub, lang, parts)
        total_parts_created += len(parts)
        if idx % 20 == 0 or idx == total:
            print(f"[{idx}/{total}] Processed... (Total parts so far: {total_parts_created})")

    elapsed = time.time() - t0
    print(f"\nDone! Processed {total} subtopics into {total_parts_created} structured parts in {elapsed:.1f}s.")


if __name__ == "__main__":
    main()
