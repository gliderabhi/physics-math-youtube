# Physics/Math YouTube Pipeline

Automated pipeline for an illustrated YouTube channel covering Physics and Math
from foundation through JEE/NEET level: picks the next curriculum item, generates a script
with Claude, narrates it with a free neural TTS voice, animates it with Manim,
assembles the final video, generates a thumbnail + metadata, and (optionally)
publishes it to YouTube into a per-chapter playlist.

Rendering (Manim/ffmpeg/edge-tts) runs fine on either this Mac or the Linux server
(`physics-yt-server`). **Curriculum tracking lives in MySQL on the server only**
(`physics_math_youtube_db`, same convention as the server's other services —
`kids_study_db`, `orders_db`, etc.), reachable only via `127.0.0.1` there. That
means `status`, `generate`, `manual`, and `publish` (anything that reads/writes
progress) only work when run **on the server** — same as your other services.
The Mac can still be used to iterate on code and render test videos manually,
but won't see or affect real curriculum progress.

## One-time setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY; DB_* only needed on the server
```

Manim needs a LaTeX distribution:
- Mac: `brew install --cask basictex`, then `sudo tlmgr install standalone preview doublestroke setspace rsfs relsize ragged2e physics dvisvgm`
- Ubuntu/Debian: `sudo apt-get install texlive-latex-base texlive-latex-extra texlive-fonts-extra texlive-science dvisvgm`

For YouTube publishing, see [docs/YOUTUBE_SETUP.md](docs/YOUTUBE_SETUP.md) first.

## Usage

```
python main.py status              # show curriculum progress, what's next
python main.py generate            # generate the next item -> videos/<topic-slug>.mp4 (no upload)
python main.py generate --publish  # generate AND upload in one go
python main.py publish --latest    # upload the most recently generated (unpublished) run
python main.py auth                # (re-)run YouTube OAuth, needed roughly every 7 days
```

Finished videos always land in a single flat `videos/` folder, named after the
topic (e.g. `c11-physics-gravitation-escape-velocity.mp4`) — no need to dig through
`output/<run_id>/` to find them (that directory still holds intermediate working
files: audio clips, raw Manim render, scripts).

Review `syllabus.json` any time to add/reorder/edit chapters and subtopics — the
pipeline always walks it in order and tracks progress in MySQL
(`curriculum_progress`, `runs`, `playlists` tables — see `src/db.py` for the schema).

Uploads default to `privacyStatus: private` (see `src/config.py`) so you can review
before anything goes public.
