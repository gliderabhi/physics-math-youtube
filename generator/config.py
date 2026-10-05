import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv(ROOT / ".env")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
TTS_VOICE = os.environ.get("TTS_VOICE", "hi-IN-SwaraNeural")
MANIM_QUALITY = os.environ.get("MANIM_QUALITY", "h")

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_NAME = os.environ.get("DB_NAME", "physics_math_youtube_db")
DB_USER = os.environ.get("DB_USER", "")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

# Used by service/deps.py to resolve a caller's email (the gateway forwards
# X-User-Id but not email) and to gate the admin review-queue endpoints.
GATEWAY_BASE = os.environ.get("GATEWAY_BASE", "http://localhost:8080")
ADMIN_EMAILS = {e.strip() for e in os.environ.get("ADMIN_EMAILS", "coolmunnabad@gmail.com").split(",") if e.strip()}

OUTPUT_DIR = ROOT / "output"
VIDEOS_DIR = ROOT / "videos"
THUMBNAILS_DIR = ROOT / "thumbnails"  # permanent, mirrors videos/<language>/ — unlike output/<run_id>/
# (which cleanup_published() deletes after upload), these survive so the site can keep serving them.
SYLLABUS_PATH = ROOT / "syllabus.json"
CREDENTIALS_DIR = ROOT / "credentials"

# One YouTube channel per narration language/channel key (e.g. "hi-en", "en"). Each channel
# gets its own OAuth client + token, since a Google login can own multiple channels/brand
# accounts and the consent flow picks which one to authorize.
CHANNELS = {
    "hi-en": {"name": "Hindi", "voice": "hi-IN-SwaraNeural"},
    "en": {"name": "English", "voice": "en-US-AriaNeural"},
}


def voice_for(language: str) -> str:
    return CHANNELS.get(language, {}).get("voice", TTS_VOICE)


def client_secret_path(channel: str) -> Path:
    return CREDENTIALS_DIR / channel / "client_secret.json"


def token_path(channel: str) -> Path:
    return CREDENTIALS_DIR / channel / "token.json"


PROBLEM_DIFFICULTIES = ["foundation", "jee_main", "jee_advanced_neet"]

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]
YOUTUBE_CATEGORY_EDUCATION = "27"
DEFAULT_PRIVACY_STATUS = "public"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
