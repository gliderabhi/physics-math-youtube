import asyncio
import subprocess
from pathlib import Path

import edge_tts

from . import config


def _probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(out.stdout.strip())


async def _synth_one(text: str, path: Path, voice: str) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(path))


async def _synth_all(texts: list[str], out_dir: Path, voice: str) -> list[Path]:
    paths = [out_dir / f"step_{i:02d}.mp3" for i in range(len(texts))]
    await asyncio.gather(*(_synth_one(t, p, voice) for t, p in zip(texts, paths)))
    return paths


def synthesize_steps(steps: list[dict], out_dir: Path, voice: str = config.TTS_VOICE) -> list[dict]:
    """Synthesizes narration audio for each step and measures its duration.

    Returns the input steps with 'audio_path' and 'duration' added to each.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    texts = [step["narration"] for step in steps]
    paths = asyncio.run(_synth_all(texts, out_dir, voice))
    enriched = []
    for step, path in zip(steps, paths):
        enriched.append({**step, "audio_path": str(path), "duration": _probe_duration(path)})
    return enriched
