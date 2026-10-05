import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1280, 720
ACCENT_COLOR = (255, 196, 0)
TEXT_COLOR = (255, 255, 255)
BAND_TOP = 536  # leaves the circular logo + brand name fully visible above
BAND_COLOR = (0, 0, 0)
BAND_OPACITY = 200  # out of 255

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "assets" / "thumbnail_template.png"

FONT_CANDIDATES_BOLD = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
FONT_CANDIDATES_REGULAR = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
]


def _load_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def generate(label: str, title: str, out_path: Path) -> Path:
    base = Image.open(TEMPLATE_PATH).convert("RGBA").resize((WIDTH, HEIGHT), Image.LANCZOS)

    band = Image.new("RGBA", (WIDTH, HEIGHT - BAND_TOP), (*BAND_COLOR, BAND_OPACITY))
    base.alpha_composite(band, (0, BAND_TOP))

    draw = ImageDraw.Draw(base)

    label_font = _load_font(FONT_CANDIDATES_REGULAR, 26)
    draw.text((50, BAND_TOP + 16), label.upper(), font=label_font, fill=ACCENT_COLOR)

    title_font = _load_font(FONT_CANDIDATES_BOLD, 40)
    wrapped = textwrap.fill(title, width=38)
    draw.multiline_text((50, BAND_TOP + 56), wrapped, font=title_font, fill=TEXT_COLOR, spacing=10)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(out_path)
    return out_path
