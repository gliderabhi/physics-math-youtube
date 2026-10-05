import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CACHE_DIR = Path("/home/sevis/ncert_books/_wikipedia")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
USER_AGENT = "physics-math-youtube-edu-project/1.0 (private non-commercial educational tool)"

STOPWORDS = {"and", "of", "the", "in", "a", "to", "for", "on", "with"}
OPEN_LICENSES = {"cc0", "public domain", "pd", "cc by"}  # covers CC-BY and CC-BY-SA too; player.html already shows per-image attribution
NOISE_IMAGE_RE = re.compile(
    r"(icon|logo|ambox|wiktionary|commons[\s_-]|edit[\s_-]|question[\s_-]?book|disambig|p[\s_]vip|folder|wikisource|padlock)",
    re.IGNORECASE,
)
# Commons tags portrait paintings/engravings of a person with these categories -- lets us skip
# "picture of the scientist" in favour of actual diagrams, for free, from metadata already fetched.
PORTRAIT_CATEGORY_RE = re.compile(r"(pd-art|artworks? without|portrait|engravings? of people|paintings of)", re.IGNORECASE)
MIN_REQUEST_GAP = 1.5  # seconds -- shared across BOTH wikipedia.org and commons.wikimedia.org,
# since Wikimedia rate-limits by client IP across its whole infrastructure, not per-subdomain.
_last_request_at = [0.0]
_pacing_lock = threading.Lock()


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOPWORDS and len(w) > 2}


def _rate_limited_get(url: str, retries: int = 5) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        with _pacing_lock:
            wait = MIN_REQUEST_GAP - (time.monotonic() - _last_request_at[0])
            if wait > 0:
                time.sleep(wait)
            _last_request_at[0] = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            raise
    raise RuntimeError("unreachable")


def _api_get(params: dict, retries: int = 5) -> dict:
    return _rate_limited_get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params), retries)


def _cache_path(kind: str, key: str) -> Path:
    safe = re.sub(r"[^a-zA-Z0-9]+", "_", key)[:100]
    return CACHE_DIR / f"{kind}_{safe}.json"


def search_title(query: str) -> str | None:
    cache = _cache_path("search", query)
    if cache.exists():
        return json.loads(cache.read_text())["title"]

    data = _api_get({"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": 3})
    hits = data.get("query", {}).get("search", [])
    query_words = _words(query)
    best_title, best_score = None, 0.0
    for hit in hits:
        overlap = len(query_words & _words(hit["title"])) / max(len(query_words), 1)
        if overlap > best_score:
            best_title, best_score = hit["title"], overlap

    result = best_title if best_score >= 0.3 else None
    cache.write_text(json.dumps({"title": result}))
    return result


def fetch_extract(title: str) -> str | None:
    cache = _cache_path("extract", title)
    if cache.exists():
        return json.loads(cache.read_text())["text"] or None

    data = _api_get({"action": "query", "prop": "extracts", "explaintext": 1, "titles": title, "format": "json"})
    pages = data.get("query", {}).get("pages", {})
    text = None
    for page in pages.values():
        text = page.get("extract")
    if text:
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

    cache.write_text(json.dumps({"text": text or ""}))
    return text or None


def fetch_images(title: str, limit: int = 4) -> list[dict]:
    cache = _cache_path("images", title)
    if cache.exists():
        return json.loads(cache.read_text())

    data = _api_get({"action": "query", "prop": "images", "titles": title, "format": "json", "imlimit": 25})
    pages = data.get("query", {}).get("pages", {})
    filenames = []
    for page in pages.values():
        for img in page.get("images", []):
            name = img["title"]
            if re.search(r"\.(svg|png|jpe?g)$", name, re.IGNORECASE) and not NOISE_IMAGE_RE.search(name):
                filenames.append(name)

    results = []
    for name in filenames:
        if len(results) >= limit:
            break
        info = _api_get(
            {"action": "query", "titles": name, "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 400, "format": "json"}
        )
        for p in info.get("query", {}).get("pages", {}).values():
            imageinfo = p.get("imageinfo")
            if not imageinfo:
                continue
            meta = imageinfo[0].get("extmetadata", {})
            license_short = meta.get("LicenseShortName", {}).get("value", "").lower()
            if not any(lic in license_short for lic in OPEN_LICENSES):
                continue  # skip "fair use"/non-free images -- only keep clearly open-licensed ones
            if PORTRAIT_CATEGORY_RE.search(meta.get("Categories", {}).get("value", "")):
                continue  # skip portrait paintings/engravings of the scientist -- not explanatory
            results.append(
                {
                    # Wikimedia's upload CDN aggressively rate-limits full-resolution originals and
                    # explicitly asks bulk/automated consumers to use thumbnails instead (iiurlwidth
                    # gives a server-generated, cached thumburl) -- also just the right size for a
                    # small square card in the UI, rather than a multi-MB original.
                    "url": imageinfo[0].get("thumburl") or imageinfo[0]["url"],
                    "title": name,
                    "license": meta.get("LicenseShortName", {}).get("value", ""),
                    "artist": re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")) or "Wikimedia Commons",
                }
            )

    cache.write_text(json.dumps(results))
    return results


def _commons_api_get(params: dict) -> dict:
    return _rate_limited_get("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params))


def search_commons_images(query: str, limit: int = 4) -> list[dict]:
    """Falls back to searching all of Wikimedia Commons (not just one article's embedded
    images) when the source article has nothing open-licensed to show -- a much larger pool,
    so a non-free/irrelevant image can be swapped for a real open one instead of going without."""
    cache = _cache_path("commons", query)
    if cache.exists():
        return json.loads(cache.read_text())

    data = _commons_api_get(
        {"action": "query", "list": "search", "srsearch": query, "srnamespace": 6, "format": "json", "srlimit": limit * 3}
    )
    hits = data.get("query", {}).get("search", [])

    results = []
    for hit in hits:
        if len(results) >= limit:
            break
        name = hit["title"]
        if not re.search(r"\.(svg|png|jpe?g)$", name, re.IGNORECASE) or NOISE_IMAGE_RE.search(name):
            continue
        info = _commons_api_get(
            {"action": "query", "titles": name, "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 400, "format": "json"}
        )
        for p in info.get("query", {}).get("pages", {}).values():
            imageinfo = p.get("imageinfo")
            if not imageinfo:
                continue
            meta = imageinfo[0].get("extmetadata", {})
            license_short = meta.get("LicenseShortName", {}).get("value", "").lower()
            if not any(lic in license_short for lic in OPEN_LICENSES):
                continue
            if PORTRAIT_CATEGORY_RE.search(meta.get("Categories", {}).get("value", "")):
                continue
            results.append(
                {
                    "url": imageinfo[0].get("thumburl") or imageinfo[0]["url"],
                    "title": name,
                    "license": meta.get("LicenseShortName", {}).get("value", ""),
                    "artist": re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")) or "Wikimedia Commons",
                }
            )

    cache.write_text(json.dumps(results))
    return results


def content_for_subtopic(subtopic: str) -> dict | None:
    title = search_title(subtopic)
    if not title:
        return None
    text = fetch_extract(title)
    if not text:
        return None
    images = fetch_images(title) or search_commons_images(subtopic)
    return {
        "title": title,
        "text": text,
        "images": images,
        "source_url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
    }
