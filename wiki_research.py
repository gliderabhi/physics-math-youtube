import json
import sys

from generator.wikipedia_source import fetch_extract, fetch_images, search_commons_images, search_title


def main():
    subtopic = sys.argv[1]
    title = search_title(subtopic)
    if not title:
        print(json.dumps({"found": False}))
        return

    text = fetch_extract(title) or ""
    images = fetch_images(title) or search_commons_images(subtopic)

    print(
        json.dumps(
            {
                "found": True,
                "title": title,
                "source_url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                "reference_text": text[:8000],
                "images": images,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
