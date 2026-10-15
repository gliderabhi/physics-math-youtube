import json
import pymysql
import re
import time

def main():
    conn = pymysql.connect(
        host="127.0.0.1",
        user="physics_yt_app",
        password="abbbc8eff2c24fdae60877758b78885c",
        database="physics_math_youtube_db"
    )

    with open("syllabus.json") as f:
        orig_syllabus = json.load(f)

    # 1. Fetch parent wiki URLs and titles from subtopic_wiki_html
    parent_meta = {}
    with conn.cursor() as cur:
        cur.execute("SELECT subject, class, chapter, subtopic, wiki_title, wiki_url FROM subtopic_wiki_html WHERE language='en'")
        for r in cur.fetchall():
            parent_meta[(r[0], r[1], r[2], r[3])] = {"wiki_title": r[4], "wiki_url": r[5]}

    # 2. Query all parts from subtopic_wiki_parts
    with conn.cursor() as cur:
        cur.execute("""
            SELECT subject, class, chapter, subtopic, part_index, heading, paragraph, paragraph_html, diagram_url, diagram_caption
            FROM subtopic_wiki_parts
            WHERE language='en'
            ORDER BY subject, class, chapter, subtopic, part_index
        """)
        all_parts = cur.fetchall()

    from collections import defaultdict
    parts_by_sub = defaultdict(list)
    for r in all_parts:
        key = (r[0], r[1], r[2], r[3])
        parts_by_sub[key].append({
            "part_index": r[4],
            "heading": r[5],
            "paragraph": r[6],
            "paragraph_html": r[7],
            "diagram_url": r[8],
            "diagram_caption": r[9]
        })

    # Backup original syllabus
    with open("syllabus_original_backup.json", "w") as f:
        json.dump(orig_syllabus, f, indent=2)

    new_syllabus = []
    granular_entries = []

    for ch in orig_syllabus:
        subj = ch["subject"]
        cl = ch["class"]
        chap = ch["chapter"]
        chapter_subtopics = []
        seen_in_chapter = set()

        for parent_sub in ch["subtopics"]:
            key = (subj, cl, chap, parent_sub)
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
                suffix_num = 2
                while name in seen_in_chapter:
                    name = f"{orig_name} (Part {suffix_num})"
                    suffix_num += 1

                seen_in_chapter.add(name)
                chapter_subtopics.append(name)

                # Construct rich HTML for this granular subtopic
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
    with open("syllabus.json", "w") as f:
        json.dump(new_syllabus, f, indent=2)

    print(f"Written new syllabus.json with {len(granular_entries)} granular subtopics across {len(new_syllabus)} chapters.")

    # Insert granular subtopics into subtopic_wiki_html and subtopic_wiki_parts
    print(f"Inserting {len(granular_entries)} granular subtopics into DB...")
    with conn.cursor() as cur:
        for idx, entry in enumerate(granular_entries, 1):
            cur.execute("""
                INSERT INTO subtopic_wiki_html
                    (subject, class, chapter, subtopic, language, wiki_title, wiki_url, html_content, has_diagrams)
                VALUES (%s, %s, %s, %s, 'en', %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    wiki_title = VALUES(wiki_title),
                    wiki_url = VALUES(wiki_url),
                    html_content = VALUES(html_content),
                    has_diagrams = VALUES(has_diagrams)
            """, (
                entry["subject"],
                entry["class"],
                entry["chapter"],
                entry["subtopic"],
                entry["wiki_title"],
                entry["wiki_url"],
                entry["html_content"],
                entry["has_diagrams"],
            ))

            # Also insert single part into subtopic_wiki_parts for consistency
            p = entry["part"]
            cur.execute("""
                INSERT INTO subtopic_wiki_parts
                    (subject, class, chapter, subtopic, language, part_index, heading, paragraph, paragraph_html, diagram_url, diagram_caption)
                VALUES (%s, %s, %s, %s, 'en', 1, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    heading = VALUES(heading),
                    paragraph = VALUES(paragraph),
                    paragraph_html = VALUES(paragraph_html),
                    diagram_url = VALUES(diagram_url),
                    diagram_caption = VALUES(diagram_caption)
            """, (
                entry["subject"],
                entry["class"],
                entry["chapter"],
                entry["subtopic"],
                p["heading"],
                p["paragraph"],
                p["paragraph_html"],
                p["diagram_url"],
                p["diagram_caption"],
            ))

    conn.commit()
    conn.close()
    print("Database populate complete!")


if __name__ == "__main__":
    main()
