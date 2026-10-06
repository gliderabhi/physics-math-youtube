import anthropic

from . import config
from .curriculum import CurriculumItem

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


VISUAL_SCHEMA = {
    "type": "object",
    "description": (
        "What's drawn on screen for this step. Every concept word in narration/display_text needs a "
        "real drawn object here — never leave a step with no visual unless it's a pure formula/derivation "
        "step following one that already set up the diagram. Omit this key entirely (not {}) for those."
    ),
    "properties": {
        "type": {
            "type": "string",
            "enum": ["free_body_diagram", "function_graph", "reference_frames"],
        },
        "ground": {"type": "boolean", "description": "free_body_diagram only: draw a hatched ground/surface line. Required whenever friction is mentioned."},
        "rope": {
            "type": "array",
            "description": "free_body_diagram only: [[x,y],...] polyline for a visible string/rope, required whenever a pulley or tension is mentioned.",
            "items": {"type": "array", "items": {"type": "number"}},
        },
        "objects": {
            "type": "array",
            "description": "free_body_diagram only.",
            "items": {
                "type": "object",
                "properties": {
                    "pos": {"type": "array", "items": {"type": "number"}, "description": "[x,y] offset, roughly -3..3 each axis"},
                    "kind": {"type": "string", "enum": ["block", "pulley", "lift", "observer"], "description": "lift for elevator problems, observer for outside-observer/frame problems"},
                    "color": {"type": "string", "enum": ["BLUE", "RED", "GREEN", "YELLOW", "ORANGE", "GRAY", "PURPLE", "WHITE"]},
                    "label": {"type": "string"},
                    "arrows": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "dx": {"type": "number"}, "dy": {"type": "number"},
                                "color": {"type": "string"}, "label": {"type": "string"},
                                "at_surface": {"type": "boolean", "description": "true for friction — anchors the arrow at the object's bottom edge, not its center"},
                            },
                        },
                    },
                },
            },
        },
        "x_range": {"type": "array", "items": {"type": "number"}, "description": "function_graph only: [min, max, step]"},
        "y_range": {"type": "array", "items": {"type": "number"}, "description": "function_graph only: [min, max, step]"},
        "x_label": {"type": "string"},
        "y_label": {"type": "string"},
        "curves": {
            "type": "array",
            "description": "function_graph only.",
            "items": {
                "type": "object",
                "properties": {
                    "points": {"type": "array", "items": {"type": "array", "items": {"type": "number"}}},
                    "color": {"type": "string"},
                    "label": {"type": "string"},
                    "shade_under": {"type": "boolean"},
                    "tangent_at": {"type": "number", "description": "x-value to draw a real tangent line at — required whenever narration mentions slope/steepness/instantaneous rate of change"},
                    "tangent_label": {"type": "string"},
                },
            },
        },
        "frames": {
            "type": "array",
            "description": "reference_frames only: for inertial-vs-non-inertial-frame problems, one entry per observer.",
            "items": {
                "type": "object",
                "properties": {
                    "pos": {"type": "array", "items": {"type": "number"}},
                    "label": {"type": "string"},
                    "moving": {"type": "boolean"},
                    "velocity_label": {"type": "string"},
                },
            },
        },
        "keep_previous": {"type": "boolean", "description": "function_graph only: reuse the still-visible graph from the prior step instead of redrawing it"},
    },
}

STEP_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "narration": {"type": "string", "description": "Spoken narration for this step, natural teaching tone, 1-3 sentences."},
            "display_text": {"type": "string", "description": "Short on-screen text/label for this step (<= 8 words), plain language, no LaTeX."},
            "latex": {"type": "string", "description": "LaTeX math expression for this step if relevant, WITHOUT surrounding $ signs. Empty string if not applicable."},
            "visual": VISUAL_SCHEMA,
        },
        "required": ["narration", "display_text", "latex"],
    },
}

VISUAL_GUIDE = (
    "\n\nVisual rules — this is a graphical channel, not text-to-speech-with-slides:\n"
    "- Every step needs a `visual` with a real drawn object matching every concept word in its narration, "
    "EXCEPT pure algebra/plug-in-numbers steps that immediately follow a step which already drew the setup "
    "(omit `visual` entirely there — the prior diagram stays on screen while the formula shows on the right).\n"
    "- Friction: `free_body_diagram` with `ground: true` and the friction arrow `at_surface: true`. Never a "
    "friction arrow with no surface drawn.\n"
    "- Tension/pulleys: `free_body_diagram` with a `pulley`-kind object AND a `rope` polyline actually "
    "connecting the objects — never just floating tension arrows.\n"
    "- Lift/elevator problems: a `lift`-kind object, not a plain block.\n"
    "- An outside/ground observer: an `observer`-kind object.\n"
    "- Inertial vs. non-inertial frame problems: `reference_frames` with one entry per observer, the "
    "accelerating one marked `moving: true`.\n"
    "- Any mention of slope/steepness/instantaneous rate of change on a graph: set `tangent_at` on that curve.\n"
    "- Keep `display_text` to a short label, never a restated sentence — the formula/diagram carries the "
    "meaning, narration carries the explanation."
)


EXPLAINER_TOOL = {
    "name": "emit_explainer_script",
    "description": "Emit a structured script for a concept-explanation video.",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "intro": {"type": "string", "description": "1-2 sentence hook introducing the concept."},
            "opening_visual": VISUAL_SCHEMA,
            "steps": STEP_SCHEMA,
            "summary": {"type": "string", "description": "1-2 sentence recap of the key takeaway, spoken naturally."},
            "summary_latex": {"type": "string", "description": "LaTeX of the key formula to display with the summary, without $ signs. Empty string if none."},
        },
        "required": ["title", "intro", "steps", "summary", "summary_latex"],
    },
}

PROBLEM_TOOL = {
    "name": "emit_problem_script",
    "description": "Emit a structured script for a problem-solving video.",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "problem_statement": {"type": "string"},
            "opening_visual": VISUAL_SCHEMA,
            "steps": STEP_SCHEMA,
            "final_answer": {"type": "string", "description": "Final answer spoken naturally, e.g. 'the escape velocity is about 11.2 kilometres per second'."},
            "final_answer_latex": {"type": "string", "description": "LaTeX of the final answer/result, without $ signs. Empty string if not applicable."},
        },
        "required": ["title", "problem_statement", "steps", "final_answer", "final_answer_latex"],
    },
}

DIFFICULTY_GUIDANCE = {
    "foundation": "an easy, foundational problem suitable for a student just learning this subtopic",
    "jee_main": "a moderately challenging problem in the style of JEE Main / NEET",
    "jee_advanced_neet": "a hard, multi-concept problem in the style of JEE Advanced, requiring deeper insight",
}

NARRATION_STYLE = {
    "hi-en": (
        "Write `narration` in natural Hinglish, exactly as an Indian tutor speaks out loud: Hindi in "
        "Devanagari script for connecting words and explanation, with physics/math technical terms and "
        "common nouns kept in English (e.g. 'force', 'acceleration', 'object', 'triangle') the way Indian "
        "teachers actually mix languages. `display_text` stays a short, plain-English on-screen label."
    ),
    "en": "Write `narration` and `display_text` in clear, plain English.",
}


def _call_tool(system: str, user: str, tool: dict) -> dict:
    client = _get_client()
    response = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": user}],
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == tool["name"]:
            return block.input
    raise RuntimeError(f"Claude did not return a {tool['name']} tool call")


def generate_explainer(item: CurriculumItem, language: str) -> dict:
    system = (
        "You are writing the script for a YouTube video on an Indian physics/math education channel "
        "covering foundational concepts and JEE/NEET prep. Explain the concept clearly and rigorously, "
        "assuming the student has covered earlier chapters but not this one. Keep each step's narration "
        "concise and natural for voice narration. Produce 5-9 steps that build up the concept logically. "
        "Do not refer to class numbers (e.g. Class 9/10/11/12) in titles or content.\n\n"
        + NARRATION_STYLE.get(language, NARRATION_STYLE["en"])
        + VISUAL_GUIDE
    )
    user = (
        f"Subject: {item.subject}\nChapter: {item.chapter}\n"
        f"Subtopic to explain: {item.subtopic}\n\n"
        "Create the explainer video script now."
    )
    return _call_tool(system, user, EXPLAINER_TOOL)


def generate_problem(item: CurriculumItem, language: str) -> dict:
    difficulty_note = DIFFICULTY_GUIDANCE[item.difficulty]
    system = (
        "You are writing the script for a YouTube video on an Indian physics/math education channel "
        "covering foundational concepts and JEE/NEET prep. Pose an original problem on the given subtopic "
        "at the specified difficulty, then solve it step by step. Keep each step's narration concise "
        "and natural for voice narration. Produce 4-8 solution steps. "
        "Do not refer to class numbers (e.g. Class 9/10/11/12) in titles or content.\n\n"
        + NARRATION_STYLE.get(language, NARRATION_STYLE["en"])
        + VISUAL_GUIDE
    )
    user = (
        f"Subject: {item.subject}\nChapter: {item.chapter}\n"
        f"Subtopic: {item.subtopic}\nDifficulty: {item.difficulty} -> {difficulty_note}\n\n"
        "Create an original problem and its full step-by-step solution now."
    )
    return _call_tool(system, user, PROBLEM_TOOL)


def generate_content(item: CurriculumItem, language: str) -> dict:
    if item.content_type == "explainer":
        content = generate_explainer(item, language)
    else:
        content = generate_problem(item, language)
    content["content_type"] = item.content_type
    return content


NOTE_STYLE = {
    "hi-en": (
        "Write in natural Hinglish -- Hindi (Devanagari script) for the explanation and connecting "
        "sentences, with physics/math technical terms kept in English, matching how an Indian textbook "
        "companion guide actually reads."
    ),
    "en": "Write in clear, plain English.",
}

NOTE_TOOL = {
    "name": "emit_topic_note",
    "description": "Emit a short written explanation of one curriculum subtopic for a reading page.",
    "input_schema": {
        "type": "object",
        "properties": {
            "explanation": {
                "type": "string",
                "description": (
                    "3-6 short paragraphs of plain prose explaining the subtopic, grounded in the actual "
                    "NCERT textbook's treatment (same definitions, derivation order, conventions). Formulas "
                    "written as plain readable text, not LaTeX."
                ),
            },
        },
        "required": ["explanation"],
    },
}


def generate_topic_note(item: CurriculumItem, language: str) -> str:
    from .ncert_source import text_for_chapter

    system = (
        f"You are writing a short reading-page explanation of one {item.subject} "
        f"subtopic from the chapter '{item.chapter}', grounded in foundational textbook treatment of "
        "this topic.\n\n" + NOTE_STYLE.get(language, NOTE_STYLE["en"])
    )
    excerpt = text_for_chapter(item.subject, item.class_, item.chapter)
    if excerpt:
        system += (
            "\n\nBelow is the actual NCERT chapter text. Base your explanation on it -- same definitions, "
            "derivation order, and conventions -- picking out and adapting only the part relevant to the "
            "requested subtopic.\n\n---\n" + excerpt[:40000] + "\n---"
        )
    user = f"Subtopic: {item.subtopic}\n\nWrite the explanation now."
    return _call_tool(system, user, NOTE_TOOL)["explanation"]


PROBLEMS_TOOL = {
    "name": "emit_topic_problems",
    "description": "Emit short practice problems with worked solutions for one curriculum subtopic, for a reading page.",
    "input_schema": {
        "type": "object",
        "properties": {
            "problems": {
                "type": "array",
                "minItems": 2,
                "maxItems": 4,
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string", "description": "The problem statement, plain text, formulas written out readably, not LaTeX."},
                        "solution": {"type": "string", "description": "Full worked solution, step by step, plain text."},
                    },
                    "required": ["question", "solution"],
                },
            },
        },
        "required": ["problems"],
    },
}


def generate_topic_problems(item: CurriculumItem, language: str) -> list[dict]:
    from .ncert_source import text_for_chapter

    system = (
        f"You are selecting and writing short practice problems for one "
        f"{item.subject} subtopic from the chapter '{item.chapter}', for a reading page (not a video). "
        "Prefer adapting standard practice problems for this subtopic over inventing unrelated "
        "ones.\n\n" + NOTE_STYLE.get(language, NOTE_STYLE["en"])
    )
    excerpt = text_for_chapter(item.subject, item.class_, item.chapter)
    if excerpt:
        system += (
            "\n\nBelow is the actual NCERT chapter text, including its exercises. Prefer adapting problems "
            "from it for the requested subtopic over inventing new ones.\n\n---\n" + excerpt[:40000] + "\n---"
        )
    user = f"Subtopic: {item.subtopic}\n\nWrite 2-4 practice problems with full solutions now."
    return _call_tool(system, user, PROBLEMS_TOOL)["problems"]
