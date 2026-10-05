def build_segments(content: dict) -> list[dict]:
    """Flattens generated content into a single ordered list of narrated segments:
    opening card -> solution/explanation steps -> closing card. Each segment carries
    a short 'label' (header shown above the main text) and the 'display_text' body
    actually shown on screen while its 'narration' is spoken.
    """
    steps = [
        {
            "kind": "step",
            "label": f"Step {i + 1}",
            "narration": s["narration"],
            "display_text": s["display_text"],
            "latex": s.get("latex", ""),
            "visual": s.get("visual", {}),
        }
        for i, s in enumerate(content["steps"])
    ]
    opening_visual = content.get("opening_visual", {})
    closing_visual = content.get("closing_visual", {})
    if content["content_type"] == "explainer":
        opening = {"kind": "intro", "label": "", "narration": content["intro"], "display_text": content["title"], "latex": "", "visual": opening_visual}
        closing = {
            "kind": "summary",
            "label": "Key Takeaway",
            "narration": content["summary"],
            "display_text": content["summary"],
            "latex": content.get("summary_latex", ""),
            "visual": closing_visual,
        }
    else:
        opening = {
            "kind": "problem",
            "label": "Problem",
            "narration": content["problem_statement"],
            "display_text": content["problem_statement"],
            "latex": "",
            "visual": opening_visual,
        }
        closing = {
            "kind": "answer",
            "label": "Final Answer",
            "narration": content["final_answer"],
            "display_text": content["final_answer"],
            "latex": content.get("final_answer_latex", ""),
            "visual": closing_visual,
        }
    return [opening, *steps, closing]
