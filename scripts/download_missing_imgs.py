import argparse
import json
import os
import re

from bs4 import BeautifulSoup

try:
    from scripts.util import download_image
    from scripts.update_countries import fetch_search_page, fetch_movie_page
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from util import download_image
    from update_countries import fetch_search_page, fetch_movie_page


base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
json_path = os.path.join(base, "data", "rotten_300.json")
image_root = os.path.join(base, "data", "img")


def slugify_title(title: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", (title or "").lower())
    return cleaned.strip("-") or "untitled"


def find_tmdb_poster_url(title: str, year: int | None = None) -> str | None:
    search_page = fetch_search_page(title, "en-US")
    movie_page = fetch_movie_page(search_page, year=year)

    soup = BeautifulSoup(movie_page, "html.parser")
    for img in soup.select('img.poster'):
        src = img.get("src") or ""
        if "/t/p/" in src:
            return src

    return None


def ensure_local_image(title: str, image_path: str, year: int | None = None, *, dry_run: bool = False) -> str | None:
    if os.path.exists(image_path):
        return image_path

    image_url = find_tmdb_poster_url(title, year)
    if not image_url:
        return None

    if dry_run:
        return image_url

    try:
        download_image(image_url, image_path)
    except Exception:
        return None
    return image_path


def iter_movie_items(path: str = json_path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    return data


def main():
    parser = argparse.ArgumentParser(description="Download any missing movie poster images to data/img.")
    parser.add_argument("--dry-run", action="store_true", help="Only report what would be downloaded without writing files.")
    parser.add_argument("--json", default=json_path, help="Path to the Rotten Tomatoes JSON list; defaults to data/rotten_300.json.")
    args = parser.parse_args()

    os.makedirs(image_root, exist_ok=True)

    downloaded = 0
    missing = 0
    for item in iter_movie_items(args.json):
        title = item.get("title")
        image = item.get("image")
        if not image:
            continue

        local_path = "." + image
        if os.path.exists(local_path):
            continue

        missing += 1
        dest = ensure_local_image(title, local_path, item.get("year"), dry_run=args.dry_run)
        if dest:
            downloaded += 1
            print(f"Downloaded: {title} -> {dest}")
        else:
            print(f"Missing: {title} (no poster found)")

    print(f"Missing images checked: {missing}; downloaded: {downloaded}")


if __name__ == "__main__":
    main()
