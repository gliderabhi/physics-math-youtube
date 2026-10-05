import json
import re
from pathlib import Path

import fitz

from .curriculum import load_syllabus

NCERT_DIR = Path("/home/sevis/ncert_books")
MAP_CACHE = NCERT_DIR / "_chapter_map.json"

FOLDER_FOR = {
    ("math", 9): "c9_math",
    ("math", 10): "c10_math",
    ("math", 11): "c11_math",
    ("math", 12): "c12_math",
    ("physics", 9): "c9_science",
    ("physics", 10): "c10_science",
    ("physics", 11): "c11_physics",
    ("physics", 12): "c12_physics",
}

# Hand-verified against the actual downloaded books (titles/content read directly) --
# the automated keyword scorer below gets these wrong often enough (merged/renumbered
# chapters, generic words like "physics" matching everywhere) that physics, the subject
# this project actually generates for right now, is worth mapping by hand. Math falls
# back to the scorer. Empty list = confirmed not present in this edition (falls back to
# Claude's own knowledge at generation time).
OVERRIDES: dict[tuple[str, int, str], list[str]] = {
    ("physics", 9, "Motion"): ["c9_science/iesc104.pdf"],
    ("physics", 9, "Force and Laws of Motion"): ["c9_science/iesc106.pdf"],
    ("physics", 9, "Gravitation"): ["c9_science/iesc106.pdf"],
    ("physics", 9, "Work and Energy"): ["c9_science/iesc107.pdf"],
    ("physics", 9, "Sound"): ["c9_science/iesc110.pdf"],
    ("physics", 10, "Light - Reflection and Refraction"): ["c10_science/jesc109.pdf"],
    ("physics", 10, "Human Eye and Colourful World"): ["c10_science/jesc110.pdf"],
    ("physics", 10, "Electricity"): ["c10_science/jesc111.pdf"],
    ("physics", 10, "Magnetic Effects of Electric Current"): ["c10_science/jesc112.pdf"],
    ("physics", 10, "Sources of Energy"): [],
    ("physics", 11, "Units, Dimensions and Vectors"): ["c11_physics/keph101.pdf"],
    ("physics", 11, "Motion in a Straight Line"): ["c11_physics/keph102.pdf"],
    ("physics", 11, "Motion in a Plane"): ["c11_physics/keph103.pdf"],
    ("physics", 11, "Laws of Motion"): ["c11_physics/keph104.pdf"],
    ("physics", 11, "Work, Energy and Power"): ["c11_physics/keph105.pdf"],
    ("physics", 11, "System of Particles and Rotational Motion"): ["c11_physics/keph106.pdf"],
    ("physics", 11, "Gravitation"): ["c11_physics/keph107.pdf"],
    ("physics", 11, "Mechanical Properties of Solids and Fluids"): ["c11_physics/keph201.pdf", "c11_physics/keph202.pdf"],
    ("physics", 11, "Thermal Properties and Thermodynamics"): ["c11_physics/keph203.pdf", "c11_physics/keph204.pdf"],
    ("physics", 11, "Oscillations and Waves"): ["c11_physics/keph206.pdf", "c11_physics/keph207.pdf"],
    ("physics", 12, "Electrostatics"): ["c12_physics/leph101.pdf", "c12_physics/leph102.pdf"],
    ("physics", 12, "Current Electricity"): ["c12_physics/leph103.pdf"],
    ("physics", 12, "Magnetism and Matter"): ["c12_physics/leph104.pdf", "c12_physics/leph105.pdf"],
    ("physics", 12, "Electromagnetic Induction and AC"): ["c12_physics/leph106.pdf", "c12_physics/leph107.pdf"],
    ("physics", 12, "Ray Optics and Optical Instruments"): ["c12_physics/leph201.pdf"],
    ("physics", 12, "Wave Optics"): ["c12_physics/leph202.pdf"],
    ("physics", 12, "Modern Physics"): [
        "c12_physics/leph203.pdf", "c12_physics/leph204.pdf", "c12_physics/leph205.pdf", "c12_physics/leph206.pdf",
    ],
}

STOPWORDS = {"and", "of", "the", "in", "a", "to", "for", "on", "with", "two", "variables"}


def _words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOPWORDS and len(w) > 2]


def _extract_text(pdf_path: Path) -> str:
    cache_path = pdf_path.with_suffix(".txt")
    if cache_path.exists():
        return cache_path.read_text()
    doc = fitz.open(str(pdf_path))
    text = "\n".join(page.get_text() for page in doc)
    cache_path.write_text(text)
    return text


def _score(chapter_words: list[str], text_lower: str, head: str) -> float:
    if not chapter_words:
        return 0.0
    hits = sum(1 for w in chapter_words if re.search(rf"\b{re.escape(w)}\b", text_lower))
    score = hits / len(chapter_words)
    if " ".join(chapter_words) in head:
        score += 2.0
    head_hits = sum(1 for w in chapter_words if w in head)
    score += 0.3 * head_hits
    return score


def _best_match(chapter: str, folder_texts: list[tuple[Path, str]], min_score: float) -> list[Path]:
    chapter_words = _words(chapter)
    best_pdf, best_score = None, 0.0
    for pdf, text_lower in folder_texts:
        head = text_lower[:1500]
        score = _score(chapter_words, text_lower, head)
        if score > best_score:
            best_pdf, best_score = pdf, score
    return [best_pdf] if best_pdf is not None and best_score >= min_score else []


def build_map(min_score: float = 0.5) -> dict[str, list[str]]:
    syllabus = load_syllabus()
    folder_texts: dict[str, list[tuple[Path, str]]] = {}
    result: dict[str, list[str]] = {}

    for ch in syllabus:
        subject, class_, chapter = ch["subject"], ch["class"], ch["chapter"]
        map_key = f"{subject}|{class_}|{chapter}"

        override = OVERRIDES.get((subject, class_, chapter))
        if override is not None:
            result[map_key] = override
            continue

        folder = FOLDER_FOR.get((subject, class_))
        if folder is None:
            continue
        folder_path = NCERT_DIR / folder
        if folder not in folder_texts:
            texts = []
            for pdf in sorted(folder_path.glob("*.pdf")):
                try:
                    text = _extract_text(pdf)
                except Exception:
                    continue
                texts.append((pdf, text.lower()))
            folder_texts[folder] = texts

        matches = _best_match(chapter, folder_texts[folder], min_score)
        if matches:
            result[map_key] = [str(p.relative_to(NCERT_DIR)) for p in matches]

    MAP_CACHE.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def _load_map() -> dict[str, list[str]]:
    if not MAP_CACHE.exists():
        return build_map()
    return json.loads(MAP_CACHE.read_text())


def text_for_chapter(subject: str, class_: int, chapter: str) -> str | None:
    chapter_map = _load_map()
    rels = chapter_map.get(f"{subject}|{class_}|{chapter}")
    if not rels:
        return None
    raw = "\n\n".join(_extract_text(NCERT_DIR / rel) for rel in rels)
    # Deduped once here, at the whole-chapter level, before section-splitting -- a run can
    # straddle a heading line itself (truncated shadow copies before it, tail fragments after),
    # so dedup has to see the full run in context, not just one section's already-split body.
    lines = _dedupe_stutter([ln.strip() for ln in raw.split("\n") if ln.strip()])
    return "\n".join(lines)


HEADING_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\s+([A-Z][A-Za-z‘’'(),.\-\s]{2,60})$")
# Standalone lines that are sidebar-box labels/cross-references, not body prose -- NCERT's
# newer books interleave "Think It Over" / "Grade N Curiosity" boxes right into the extracted
# text with no visual marker, so they have to be matched and dropped by content, not position.
NOISE_LINE_RE = re.compile(
    r"^(\d+|reprint\s*\d*[\-\s]*\d*|physics|mathematics|science"
    r"|grade\s*\d+|curiosity|ganita\s*prakash|part\s*[ivx]+|chapter\s*\d*"
    r"|think\s*it\s*over|ready\s*to\s*go\s*beyond|next\s*level\s*up|note)$",
    re.IGNORECASE,
)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
SENTENCES_PER_PARAGRAPH = 3


def _is_formula_line(line: str) -> bool:
    """Mirrors the frontend's classifier: a real standalone equation has identifiable content
    on both sides of '=' and no prose word, vs. a line that's just regular sentence text."""
    if not line or len(line) > 70:
        return False
    eq_index = line.find("=")
    if eq_index == -1:
        return False
    before = line[:eq_index].strip()
    after = line[eq_index + 1 :].strip()
    has_long_word = bool(re.search(r"[A-Za-z]{4,}", line))
    return len(before) >= 1 and len(after) >= 2 and not has_long_word


def _is_stutter_pair(a: str, b: str) -> bool:
    """True if a and b are the same decorative-heading artifact: one is a prefix/suffix/
    substring of the other (handles truncated shadow-text copies like '11.6 RESIST' vs the
    full '11.6 RESISTANCE OF A SYSTEM OF RESISTORS', not just exact repeats)."""
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if len(shorter) < 3:
        return False
    return shorter in longer


def _dedupe_stutter(lines: list[str]) -> list[str]:
    """Several of this edition's PDFs draw headings/figure captions as multiple overlapping
    offset copies for a bold/shadow visual effect -- plain text extraction faithfully pulls out
    every layer, so 'Figure 11.6' or a heading can repeat 4-6 times in a row. Collapses any run
    of short, mutually-overlapping lines down to the single longest (most complete) one."""
    result: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        j = i
        while j + 1 < n and len(lines[j + 1]) < 80 and _is_stutter_pair(lines[j], lines[j + 1]):
            j += 1
        if j > i:
            result.append(max(lines[i : j + 1], key=len))
            i = j + 1
        else:
            result.append(lines[i])
            i += 1
    return result


def _clean(text: str) -> str:
    """Strips sidebar-box noise, then rebuilds real paragraph structure: PDF extraction has no
    blank lines at paragraph boundaries (wrapped lines within AND between paragraphs look the
    same), so paragraphs are regrouped by sentence count instead. Formula-shaped lines are kept
    standalone (never folded into a sentence-blob) so the UI can box them distinctly."""
    lines = [ln.strip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln and not NOISE_LINE_RE.match(ln)]

    paragraphs: list[str] = []
    prose_buffer: list[str] = []

    def flush_prose() -> None:
        if not prose_buffer:
            return
        blob = re.sub(r"\s+", " ", " ".join(prose_buffer)).strip()
        prose_buffer.clear()
        if not blob:
            return
        sentences = [s for s in SENTENCE_RE.split(blob) if s]
        chunk: list[str] = []
        for sentence in sentences:
            chunk.append(sentence)
            if len(chunk) >= SENTENCES_PER_PARAGRAPH:
                paragraphs.append(" ".join(chunk))
                chunk = []
        if chunk:
            paragraphs.append(" ".join(chunk))

    for line in lines:
        if _is_formula_line(line):
            flush_prose()
            paragraphs.append(line)
        else:
            prose_buffer.append(line)
    flush_prose()

    return "\n\n".join(paragraphs)


def split_sections(text: str) -> list[tuple[str, str]]:
    """Splits chapter text on NCERT's own numbered section headings (e.g. '8.1 Introduction'),
    found by the pattern, into real text, no LLM call needed."""
    sections: list[tuple[str, list[str]]] = []
    current: tuple[str, list[str]] | None = None
    for line in text.split("\n"):
        stripped = line.strip()
        if HEADING_RE.match(stripped):
            if current:
                sections.append(current)
            current = (stripped, [])
        elif current:
            current[1].append(line)
    if current:
        sections.append(current)
    return [(heading, _clean("\n".join(body))) for heading, body in sections]


def text_for_subtopic(subject: str, class_: int, chapter: str, subtopic: str, max_chars: int = 6000) -> str | None:
    """No-API fallback: finds the NCERT section within the mapped chapter(s) that best matches
    this subtopic by keyword overlap, and returns its cleaned body text directly."""
    chapter_text = text_for_chapter(subject, class_, chapter)
    if not chapter_text:
        return None

    sections = split_sections(chapter_text)
    if not sections:
        return _clean(chapter_text)[:max_chars]

    subtopic_words = _words(subtopic)
    best_body, best_score = None, 0.0
    for heading, body in sections:
        head = (heading + " " + body[:300]).lower()
        score = _score(subtopic_words, body.lower(), head)
        if score > best_score:
            best_body, best_score = body, score

    if best_body and best_score >= 0.34 and len(best_body) > 200:
        return best_body[:max_chars]
    return _clean(chapter_text)[:max_chars]
