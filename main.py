import argparse
import json

from generator import config, curriculum
from generator.db import init_db


def main():
    parser = argparse.ArgumentParser(description="Physics/Math YouTube channel pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="Fully automatic: Claude API generates script+metadata, then builds the video (needs API credit)")
    gen.add_argument("--publish", action="store_true", help="Also upload to YouTube immediately after generating")
    gen.add_argument("--quality", choices=["l", "m", "h"], default=None, help="Manim render quality (l=fast/low, h=1080p)")

    sub.add_parser("next", help="Print the next curriculum item as JSON (no API calls, no DB writes)")

    man = sub.add_parser("manual", help="Build a video from a manually-written content JSON file (no Anthropic API calls, no DB storage)")
    man.add_argument("--file", required=True, help="Path to a JSON file with {item, content, metadata} keys")
    man.add_argument("--publish", action="store_true", help="Also upload to YouTube immediately after building")
    man.add_argument("--quality", choices=["l", "m", "h"], default=None)
    man.add_argument("--language", default="hi-en", help="Channel/language tag to record for this run (default: hi-en)")

    ing = sub.add_parser("ingest", help="Store a content/narration JSON file in the DB (content once, narration per language)")
    ing.add_argument("--file", required=True, help="{item, content, metadata} for a first ingest, or {item, narration} to add another language")
    ing.add_argument("--language", required=True, help="e.g. 'en' or 'hi-en' (Hinglish)")

    bld = sub.add_parser("build", help="Build a video from DB-stored content for one curriculum item + language (no files needed)")
    bld.add_argument("--subject", required=True)
    bld.add_argument("--class", dest="class_", required=True, type=int)
    bld.add_argument("--chapter", required=True)
    bld.add_argument("--subtopic", required=True)
    bld.add_argument("--content-type", dest="content_type", required=True, choices=["explainer", "problem"])
    bld.add_argument("--difficulty", default=None)
    bld.add_argument("--language", required=True)
    bld.add_argument("--publish", action="store_true")
    bld.add_argument("--quality", choices=["l", "m", "h"], default=None)

    gi = sub.add_parser("generate-item", help="Claude generates script+visuals for one exact subtopic/difficulty/language — the admin page's Generate button")
    gi.add_argument("--subject", required=True)
    gi.add_argument("--class", dest="class_", required=True, type=int)
    gi.add_argument("--chapter", required=True)
    gi.add_argument("--subtopic", required=True)
    gi.add_argument("--content-type", dest="content_type", required=True, choices=["explainer", "problem"])
    gi.add_argument("--difficulty", default=None)
    gi.add_argument("--language", required=True)
    gi.add_argument("--quality", choices=["l", "m", "h"], default=None)

    pub = sub.add_parser("publish", help="Upload a previously generated run to YouTube")
    pub.add_argument("--latest", action="store_true", help="Publish the most recent generated-but-unpublished run")
    pub.add_argument("--run-id", default=None, help="Publish a specific run by id")

    sub.add_parser("publish-approved", help="Upload every admin-approved run (from the review-queue page) to YouTube — cron entry point")

    auth = sub.add_parser("auth", help="Run the one-time (or periodic) YouTube OAuth flow for one channel")
    auth.add_argument("--channel", required=True, choices=list(config.CHANNELS), help="Which channel's credentials to authorize")
    auth.add_argument("--port", type=int, default=8080, help="Fixed local port for the OAuth callback (tunnel this port over SSH)")
    sub.add_parser("status", help="Show curriculum progress")
    sub.add_parser("cleanup", help="Delete local video/output files for every published run (the real copy lives on YouTube)")

    args = parser.parse_args()
    if args.command != "auth":
        init_db()

    if args.command == "generate":
        from generator.pipeline import generate_next, publish_run

        run_id = generate_next(quality=args.quality)
        if run_id and args.publish:
            publish_run(run_id)

    elif args.command == "next":
        item = curriculum.get_next_item()
        print(json.dumps(item.to_dict(), indent=2) if item else "null")

    elif args.command == "manual":
        from generator.pipeline import build_from_manual_file, publish_run

        run_id = build_from_manual_file(args.file, quality=args.quality, language=args.language)
        if run_id and args.publish:
            publish_run(run_id)

    elif args.command == "ingest":
        from generator.content_store import ingest_file

        content_item_id = ingest_file(args.file, args.language)
        print(f"Ingested content_item_id={content_item_id} language={args.language}")

    elif args.command == "build":
        from generator.curriculum import CurriculumItem
        from generator.pipeline import build_from_db, publish_run

        item = CurriculumItem(args.subject, args.class_, args.chapter, args.subtopic, args.content_type, args.difficulty)
        run_id = build_from_db(item, args.language, quality=args.quality)
        if run_id and args.publish:
            publish_run(run_id)

    elif args.command == "generate-item":
        from generator.curriculum import CurriculumItem
        from generator.pipeline import generate_specific

        item = CurriculumItem(args.subject, args.class_, args.chapter, args.subtopic, args.content_type, args.difficulty)
        generate_specific(item, args.language, quality=args.quality)

    elif args.command == "publish":
        from generator.pipeline import publish_run

        publish_run(args.run_id)

    elif args.command == "publish-approved":
        from generator.pipeline import publish_approved

        publish_approved()

    elif args.command == "auth":
        from generator.youtube_auth import run_auth_flow

        run_auth_flow(args.channel, port=args.port)

    elif args.command == "status":
        print(curriculum.status_report())

    elif args.command == "cleanup":
        from generator.pipeline import cleanup_published

        cleanup_published()


if __name__ == "__main__":
    main()
