import subprocess
from pathlib import Path

from pydub import AudioSegment


def build_narration_track(segments: list[dict], out_path: Path, gap_ms: int = 300) -> Path:
    track = AudioSegment.empty()
    gap = AudioSegment.silent(duration=gap_ms)
    for i, segment in enumerate(segments):
        track += AudioSegment.from_file(segment["audio_path"])
        if i != len(segments) - 1:
            track += gap
    out_path.parent.mkdir(parents=True, exist_ok=True)
    track.export(out_path, format="mp3")
    return out_path


def _duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(out.stdout.strip())


def mux(video_path: Path, audio_path: Path, out_path: Path) -> Path:
    video_dur = _duration(video_path)
    audio_dur = _duration(audio_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if audio_dur > video_dur + 0.05:
        pad = audio_dur - video_dur
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(video_path),
                "-vf", f"tpad=stop_mode=clone:stop_duration={pad}",
                "-c:v", "libx264", "-preset", "veryfast",
                str(video_path.with_name("padded_" + video_path.name)),
            ],
            check=True, capture_output=True,
        )
        video_path = video_path.with_name("padded_" + video_path.name)

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(video_path), "-i", str(audio_path),
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac",
            "-movflags", "+faststart", "-shortest", str(out_path),
        ],
        check=True, capture_output=True,
    )
    return out_path
