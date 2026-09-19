import json
import os
import re
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup

try:
    from util import download_image
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from scripts.util import download_image


scrape_url = "https://editorial.rottentomatoes.com/guide/best-movies-of-all-time/"

base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
out = os.path.join(base, "data", "rotten_300.json")
image_root = os.path.join(base, "data", "rotten_300", "img")


def slugify_title(title: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", (title or "").lower())
    return cleaned.strip("-") or "untitled"


def _extract_year(anchor) -> int | None:
    year_node = anchor.find_next_sibling(class_="meta-year")
    if year_node is None:
        return None
    match = re.search(r"(19|20)\d{2}", year_node.get_text(" ", strip=True))
    if match is None:
        return None
    return int(match.group(0))


def _extract_rank(anchor) -> int | None:
    node = anchor
    for _ in range(3):
        if node is None:
            return None
        node = node.parent

    if getattr(node, "name", None) != "td":
        return None

    prev_td = node.find_previous_sibling("td")
    if prev_td is None:
        return None
    match = re.search(r"\d+", prev_td.get_text(" ", strip=True))
    if match is None:
        return None
    return int(match.group(0))


def _image_extension(url: str) -> str:
    path = urlsplit(url).path or "/image.jpg"
    ext = os.path.splitext(path)[1].lower()
    if ext in {".jpg", ".jpeg", ".png", ".webp"}:
        return ext
    return ".jpg"


def ensure_local_image(image_url: str | None, dest_path: str, *, skip_if_exists: bool = True, session: requests.Session | None = None) -> str | None:
    if not image_url:
        return None
    if skip_if_exists and os.path.exists(dest_path):
        return dest_path
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    try:
        download_image(image_url, dest_path, session=session)
    except Exception:
        return None
    return dest_path


def fetch_movie_data(movie_url: str, session: requests.Session | None = None) -> tuple[str | None, str]:
    if not movie_url:
        return None, ""
    try:
        response = (session or requests).get(movie_url, timeout=20)
        response.raise_for_status()
    except Exception:
        return None, ""

    soup = BeautifulSoup(response.text, "html.parser")
    for style in soup.select("style"):
        style.extract()

    synopsis = ""
    description = soup.select_one('div[slot="description"] rt-text[slot="content"]')
    if description is not None:
        text = description.get_text(" ", strip=True)
        if text:
            synopsis = text

    image_url = None
    for selector in ["meta[property='og:image']", "meta[name='twitter:image']", "meta[property='twitter:image']"]:
        meta = soup.select_one(selector)
        if meta and meta.get("content"):
            image_url = meta["content"]
            break

    if image_url is None:
        for img in soup.select("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
            if not src:
                continue
            lower = src.lower()
            if any(x in lower for x in ("poster", "movie", "image")) and any(lower.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")):
                image_url = src
                break

    return image_url, synopsis


def scrape_rotten_300(url: str = scrape_url, limit: int = 300):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    data = []
    seen_titles = set()
    for anchor in soup.select("a.meta-title"):
        title = anchor.get_text(" ", strip=True)
        if not title or title in seen_titles:
            continue
        print(title)
        seen_titles.add(title)

        rank = _extract_rank(anchor) or len(data) + 1
        year = _extract_year(anchor)

        movie_url = anchor.get("href")
        image_url, synopsis = fetch_movie_data(movie_url)

        path_image = None
        if image_url:
            slug = slugify_title(title)
            ext = _image_extension(image_url)
            path_image = f"/movimg/{slug}{ext}"

        item = {
            "rank": rank,
            "title": title,
            "year": year,
            "synopsis": synopsis,
            "image": path_image,
        }
        data.append(item)
        if len(data) >= limit:
            break

    return data


def main():
    os.makedirs(image_root, exist_ok=True)
    data = scrape_rotten_300()
    if 100 < len(data) < 500:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        print(f"Wrote {len(data)} items to {out}")
    else:
        print(f"Scraped {len(data)} items; not writing because the result was outside the expected range.")


if __name__ == "__main__":
    main()
