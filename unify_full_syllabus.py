"""
Unify all 4 subjects (Physics, Math, Chemistry, Biology) with clean, cohesive NCERT subtopics.
Reverts Physics and Math from the fragmented subtopic list back to the original clean NCERT list.
Combines with the curated clean Chemistry and Biology syllabi.
"""
import json
import os
import sys

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    if base_dir not in sys.path:
        sys.path.append(base_dir)

    from clean_chembio_syllabus import CHEMISTRY_SYLLABUS, BIOLOGY_SYLLABUS

    # 1. Load clean original Physics and Math from backup
    backup_path = os.path.join(base_dir, "syllabus_original_backup.json")
    with open(backup_path) as f:
        orig_pm = json.load(f)

    # Verify only physics and math
    clean_pm = [ch for ch in orig_pm if ch["subject"] in ("physics", "math")]
    print(f"Loaded {len(clean_pm)} clean physics and math chapters from {backup_path}")

    # 2. Combine with clean Chemistry and Biology
    full_clean_syllabus = []
    full_clean_syllabus.extend(clean_pm)
    full_clean_syllabus.extend(CHEMISTRY_SYLLABUS)
    full_clean_syllabus.extend(BIOLOGY_SYLLABUS)

    total_chapters = len(full_clean_syllabus)
    total_subtopics = sum(len(ch["subtopics"]) for ch in full_clean_syllabus)

    by_subj = {}
    for ch in full_clean_syllabus:
        s = ch["subject"]
        by_subj[s] = by_subj.get(s, 0) + len(ch["subtopics"])

    print(f"\n================== UNIFIED CLEAN SYLLABUS ==================")
    print(f"Total Chapters: {total_chapters}")
    print(f"Total Subtopics: {total_subtopics}")
    for s, count in by_subj.items():
        chaps = len([c for c in full_clean_syllabus if c["subject"] == s])
        avg = count / chaps if chaps else 0
        print(f"  {s.upper():<10}: {chaps:<2} chapters | {count:<3} subtopics (avg {avg:.1f}/chap)")

    # 3. Save to syllabus.json
    syllabus_path = os.path.join(base_dir, "syllabus.json")
    with open(syllabus_path, "w") as f:
        json.dump(full_clean_syllabus, f, indent=2)
    print(f"\nSuccessfully wrote unified clean syllabus to {syllabus_path}!")

    # 4. Restart physics-service
    os.system("systemctl --user restart physics-service")
    print("Restarted physics-service.")

if __name__ == "__main__":
    main()
