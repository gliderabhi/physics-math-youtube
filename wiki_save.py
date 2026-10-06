import json
import sys
from pathlib import Path

from generator.db import init_db
from generator.wiki_store import save_wiki


def main():
    data = json.loads(Path(sys.argv[1]).read_text())
    init_db()
    save_wiki(
        data["subject"],
        data["chapter"],
        data["subtopic"],
        {
            "title": data["title"],
            "text": data["text"],
            "source_url": data["source_url"],
            "images": data.get("images", []),
        },
    )
    print(f"saved: {data['subtopic']}")


if __name__ == "__main__":
    main()
