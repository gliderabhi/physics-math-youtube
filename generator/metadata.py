import anthropic

from . import config
from .curriculum import CurriculumItem

METADATA_TOOL = {
    "name": "emit_video_metadata",
    "description": "Emit YouTube title, description and tags for a video.",
    "input_schema": {
        "type": "object",
        "properties": {
            "youtube_title": {"type": "string", "description": "SEO-friendly title, under 100 characters, includes topic, chapter, and subject."},
            "description": {"type": "string", "description": "3-5 sentence YouTube description including the topic, a call to action to subscribe, and relevant keywords."},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "10-15 search tags."},
        },
        "required": ["youtube_title", "description", "tags"],
    },
}


def generate_metadata(item: CurriculumItem, content: dict) -> dict:
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    body_text = content.get("problem_statement") or content.get("intro", "")
    response = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=1024,
        system="You write high-CTR, SEO-optimised YouTube metadata for an Indian physics/math education channel (JEE/NEET and foundation prep). Do not include 'Class 9/10/11/12' in the title or description.",
        tools=[METADATA_TOOL],
        tool_choice={"type": "tool", "name": METADATA_TOOL["name"]},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Video title (internal): {content['title']}\n"
                    f"Class: {item.class_}, Subject: {item.subject}, Chapter: {item.chapter}, Subtopic: {item.subtopic}\n"
                    f"Type: {item.content_type}{' (' + item.difficulty + ')' if item.difficulty else ''}\n"
                    f"Content summary: {body_text}\n\n"
                    "Generate the YouTube metadata now."
                ),
            }
        ],
    )
    for block in response.content:
        if block.type == "tool_use" and block.name == METADATA_TOOL["name"]:
            return block.input
    raise RuntimeError("Claude did not return video metadata")
