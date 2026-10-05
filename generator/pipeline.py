import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path

from . import config, content_generator, content_store, curriculum, metadata as metadata_mod, script, thumbnail, tts
from .assembler import build_narration_track, mux
from .curriculum import CurriculumItem
from .db import get_conn, init_db


def _slugify(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return slug[:max_len].rstrip("-")


def _video_slug(item: CurriculumItem, content: dict) -> str:
    suffix = f"-{item.difficulty}" if item.difficulty else ""
    return f"c{item.class_}-{_slugify(item.subject)}-{_slugify(item.chapter)}-{_slugify(content['title'])}{suffix}"


def _find_rendered_video(video_dir: Path) -> Path:
    matches = sorted(video_dir.rglob("ProblemScene.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"Manim did not produce ProblemScene.mp4 under {video_dir}")
    return matches[0]


def _produce_video(item: CurriculumItem, content: dict, quality: str | None = None, language: str = "hi-en") -> tuple[str, Path, Path, Path]:
    """Runs everything from narration through to the final video + thumbnail.
    Returns (run_id, out_dir, final_video_path, thumbnail_path). No Claude API calls happen here."""
    run_id = uuid.uuid4().hex[:12]
    out_dir = config.OUTPUT_DIR / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "content.json").write_text(json.dumps(content, indent=2))

    segments = script.build_segments(content)

    voice = config.voice_for(language)
    print(f"Synthesizing narration for {len(segments)} segments (edge-tts, voice={voice})...")
    enriched = tts.synthesize_steps(segments, out_dir / "audio", voice=voice)

    steps_spec = {
        "header_label": f"Class {item.class_} {item.subject.title()} | {item.chapter}",
        "title": content["title"],
        "segments": [
            {
                "kind": s["kind"],
                "label": s["label"],
                "display_text": s["display_text"],
                "latex": s["latex"],
                "duration": s["duration"],
                "visual": s.get("visual", {}),
            }
            for s in enriched
        ],
    }
    steps_json_path = out_dir / "steps.json"
    steps_json_path.write_text(json.dumps(steps_spec, indent=2))

    print("Rendering animation with Manim...")
    video_dir = out_dir / "video"
    video_dir.mkdir(parents=True, exist_ok=True)
    quality_flag = f"-q{quality or config.MANIM_QUALITY}"
    scene_file = config.ROOT / "generator" / "manim_scenes.py"
    subprocess.run(
        ["manim", quality_flag, "--media_dir", str(video_dir), str(scene_file), "ProblemScene"],
        env={**os.environ, "STEPS_JSON": str(steps_json_path)},
        check=True,
    )
    rendered_video = _find_rendered_video(video_dir)

    print("Assembling final video...")
    narration_path = build_narration_track(enriched, out_dir / "narration.mp3")
    final_path = mux(rendered_video, narration_path, out_dir / "final.mp4")

    print("Generating thumbnail...")
    thumb_path = thumbnail.generate(steps_spec["header_label"], content["title"], out_dir / "thumbnail.png")

    return run_id, out_dir, final_path, thumb_path


def _finalize(
    item: CurriculumItem, content: dict, run_id: str, out_dir: Path, final_path: Path, thumb_path: Path,
    video_metadata: dict, language: str,
) -> None:
    (out_dir / "metadata.json").write_text(json.dumps(video_metadata, indent=2))

    lang_dir = config.VIDEOS_DIR / language
    lang_dir.mkdir(parents=True, exist_ok=True)
    slug = _video_slug(item, content)
    video_dest = lang_dir / f"{slug}.mp4"
    if video_dest.exists():
        video_dest = lang_dir / f"{slug}-{run_id}.mp4"
    shutil.copy2(final_path, video_dest)

    # Permanent copy, mirroring the video — output/<run_id>/thumbnail.png is deleted by
    # cleanup_published() once a run is published, so the site needs its own durable copy.
    thumb_lang_dir = config.THUMBNAILS_DIR / language
    thumb_lang_dir.mkdir(parents=True, exist_ok=True)
    thumb_dest = thumb_lang_dir / f"{slug}.png"
    if thumb_dest.exists():
        thumb_dest = thumb_lang_dir / f"{slug}-{run_id}.png"
    shutil.copy2(thumb_path, thumb_dest)

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO runs (run_id, subject, class, chapter, subtopic, content_type, difficulty, language, title, status, video_path, thumbnail_path) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'generated', %s, %s)",
            (
                run_id, item.subject, item.class_, item.chapter, item.subtopic, item.content_type, item.difficulty or "",
                language, video_metadata["youtube_title"], str(video_dest), str(thumb_dest),
            ),
        )
    curriculum.mark_done(item, run_id, status="generated")
    print(f"\nDone. run_id={run_id}")
    print(f"Video:     {video_dest}")
    print(f"Thumbnail: {thumb_dest}")
    print("Review it, then run `python main.py publish --latest` to upload.")


def generate_next(quality: str | None = None) -> str | None:
    """Fully automatic path: Claude API generates both the script and the metadata.
    Requires ANTHROPIC_API_KEY with available credit."""
    init_db()
    item = curriculum.get_next_item()
    if item is None:
        print("Curriculum complete! Nothing left to generate.")
        return None

    print(f"Next item: {item.label()}")
    print("Generating script with Claude...")
    content = content_generator.generate_content(item, "hi-en")

    run_id, out_dir, final_path, thumb_path = _produce_video(item, content, quality, language="hi-en")

    print("Generating YouTube metadata with Claude...")
    video_metadata = metadata_mod.generate_metadata(item, content)

    _finalize(item, content, run_id, out_dir, final_path, thumb_path, video_metadata, language="hi-en")
    return run_id


def generate_specific(item: CurriculumItem, language: str, quality: str | None = None) -> str:
    # Same as generate_next but for one exact item/language — the admin page's Generate button.
    init_db()
    print(f"Item: {item.label()} [{language}]")
    print("Generating script with Claude...")
    content = content_generator.generate_content(item, language)

    run_id, out_dir, final_path, thumb_path = _produce_video(item, content, quality, language=language)

    print("Generating YouTube metadata with Claude...")
    video_metadata = metadata_mod.generate_metadata(item, content)

    _finalize(item, content, run_id, out_dir, final_path, thumb_path, video_metadata, language=language)
    return run_id


def build_from_manual_file(file_path: Path, quality: str | None = None, language: str = "hi-en") -> str:
    """Manual path: no Anthropic API calls. `file_path` is a JSON file with
    {"item": {...}, "content": {...}, "metadata": {...}} already written out
    (e.g. by Claude inside this chat session) matching the schemas in content_generator.py."""
    init_db()
    data = json.loads(Path(file_path).read_text())
    item = curriculum.item_from_dict(data["item"])
    content = data["content"]
    video_metadata = data["metadata"]

    run_id, out_dir, final_path, thumb_path = _produce_video(item, content, quality, language=language)
    _finalize(item, content, run_id, out_dir, final_path, thumb_path, video_metadata, language=language)
    return run_id


def build_from_db(item: CurriculumItem, language: str, quality: str | None = None) -> str:
    """DB-backed path: content (visuals/structure) + narration (per language) were already
    ingested via `python main.py ingest`. No Anthropic API calls happen here."""
    init_db()
    content, video_metadata = content_store.load_content(item, language)
    run_id, out_dir, final_path, thumb_path = _produce_video(item, content, quality, language=language)
    _finalize(item, content, run_id, out_dir, final_path, thumb_path, video_metadata, language=language)
    return run_id


def _item_from_row(row) -> CurriculumItem:
    return CurriculumItem(row["subject"], row["class"], row["chapter"], row["subtopic"], row["content_type"], row["difficulty"] or None)


def publish_run(run_id: str | None = None) -> None:
    init_db()
    with get_conn() as conn, conn.cursor() as cur:
        if run_id:
            cur.execute("SELECT * FROM runs WHERE run_id = %s", (run_id,))
        else:
            cur.execute("SELECT * FROM runs WHERE status = 'generated' ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
    if row is None:
        print("No generated-but-unpublished run found.")
        return

    from .youtube_uploader import upload_video  # deferred: only needed when publishing

    out_dir = config.OUTPUT_DIR / row["run_id"]
    video_metadata = json.loads((out_dir / "metadata.json").read_text())
    item = _item_from_row(row)

    channel = row["language"]
    print(f"Uploading {row['title']} ({row['run_id']}) to the '{channel}' channel as {config.DEFAULT_PRIVACY_STATUS}...")
    result = upload_video(item, Path(row["video_path"]), Path(row["thumbnail_path"]), video_metadata, channel)

    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE runs SET status = 'published', youtube_video_id = %s, playlist_id = %s, published_at = NOW() WHERE run_id = %s",
            (result["video_id"], result["playlist_id"], row["run_id"]),
        )
    curriculum.mark_published(item)
    print(f"Published: https://youtu.be/{result['video_id']}")


def publish_approved() -> None:
    """Cron entry point (see `python main.py publish-approved`): uploads every run
    an admin has approved from the review-queue page. Each failure is logged and
    skipped so one bad run doesn't block the rest of the batch."""
    init_db()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT run_id FROM runs WHERE status = 'approved' ORDER BY created_at ASC")
        rows = cur.fetchall()

    if not rows:
        print("No approved runs waiting to publish.")
        return

    for row in rows:
        try:
            publish_run(row["run_id"])
        except Exception as e:
            print(f"Failed to publish {row['run_id']}: {e}")


def cleanup_published() -> None:
    """Delete local files for every run already published — the real copy lives on
    YouTube now, so the finalized video and the whole output/<run_id>/ scratch
    directory (audio, Manim cache, thumbnail, intermediates) are safe to remove.
    Never touches 'generated' runs, which are still pending review/publish."""
    init_db()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT run_id, video_path FROM runs WHERE status = 'published'")
        rows = cur.fetchall()

    runs_cleaned = 0
    bytes_freed = 0
    for row in rows:
        touched = False

        video_path = Path(row["video_path"]) if row["video_path"] else None
        if video_path and video_path.exists():
            bytes_freed += video_path.stat().st_size
            video_path.unlink()
            touched = True

        out_dir = config.OUTPUT_DIR / row["run_id"]
        if out_dir.exists():
            bytes_freed += sum(f.stat().st_size for f in out_dir.rglob("*") if f.is_file())
            shutil.rmtree(out_dir)
            touched = True

        if touched:
            runs_cleaned += 1

    print(f"Cleaned local files for {runs_cleaned} published run(s); freed {bytes_freed / 1e6:.1f} MB.")
