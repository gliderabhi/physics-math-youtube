import json
import pymysql
import re

# Connect to DB to get all parts from subtopic_wiki_parts
conn = pymysql.connect(
    host="127.0.0.1",
    user="physics_yt_app",
    password="abbbc8eff2c24fdae60877758b78885c",
    database="physics_math_youtube_db"
)

with open("syllabus.json") as f:
    orig_syllabus = json.load(f)

# Query parts grouped by (subject, class, chapter, subtopic)
with conn.cursor() as cur:
    cur.execute("""
        SELECT subject, class, chapter, subtopic, part_index, heading, paragraph, paragraph_html, diagram_url, diagram_caption
        FROM subtopic_wiki_parts
        WHERE language='en'
        ORDER BY subject, class, chapter, subtopic, part_index
    """)
    all_parts = cur.fetchall()

conn.close()

from collections import defaultdict
parts_by_sub = defaultdict(list)
for r in all_parts:
    key = (r[0], r[1], r[2], r[3])  # subj, cl, chap, sub
    parts_by_sub[key].append({
        "part_index": r[4],
        "heading": r[5],
        "paragraph": r[6],
        "paragraph_html": r[7],
        "diagram_url": r[8],
        "diagram_caption": r[9]
    })

print(f"Total parent subtopics in DB: {len(parts_by_sub)}")

# Build new granular syllabus
new_syllabus = []
total_granular_subtopics = 0

for ch in orig_syllabus:
    subj = ch["subject"]
    cl = ch["class"]
    chap = ch["chapter"]
    
    chapter_subtopics = []
    seen_in_chapter = set()

    for parent_sub in ch["subtopics"]:
        key = (subj, cl, chap, parent_sub)
        parts = parts_by_sub.get(key, [])
        
        if not parts:
            # Fallback if no parts: keep parent subtopic
            if parent_sub not in seen_in_chapter:
                chapter_subtopics.append(parent_sub)
                seen_in_chapter.add(parent_sub)
            continue

        for p in parts:
            h = p["heading"].strip()
            # If heading is generic Overview, give nice name
            if h.lower() in ("overview & core concept", "overview", "introduction"):
                name = f"{parent_sub}: Overview & Foundations"
            elif h.lower() in parent_sub.lower():
                name = f"{parent_sub}: {h}"
            else:
                name = f"{parent_sub}: {h}"

            # Ensure uniqueness within chapter
            orig_name = name
            suffix_num = 2
            while name in seen_in_chapter:
                name = f"{orig_name} (Part {suffix_num})"
                suffix_num += 1

            seen_in_chapter.add(name)
            chapter_subtopics.append(name)

    new_syllabus.append({
        "class": cl,
        "subject": subj,
        "chapter": chap,
        "subtopics": chapter_subtopics
    })
    total_granular_subtopics += len(chapter_subtopics)

print(f"Total chapters: {len(new_syllabus)}")
print(f"Total granular subtopics created: {total_granular_subtopics}")

# Print Sound as sample
for ch in new_syllabus:
    if ch["chapter"] == "Sound":
        print(f"\n=== Sample Chapter: Sound ({len(ch['subtopics'])} subtopics) ===")
        for s in ch["subtopics"]:
            print(f"  • {s}")
