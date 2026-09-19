import argparse
import json
import os
import re
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

try:
    from scripts.util import fetch_json
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from util import fetch_json


scrape_url = "https://www.themoviedb.org/search/movie?language={lang}&query={title}"

base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
metadata_path = os.path.join(base, "data", "metadata.json")


def load_metadata(path: str = metadata_path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def get_country_language(country: str) -> str | None:
    mapping = {
        "se": "sv-SE",
        "dk": "da-DK",
    }
    return mapping[country]


def extract_movie_title(page_html: str) -> str | None:
    if not page_html:
        return None
    soup = BeautifulSoup(page_html, "html.parser")

    selectors = [
        "div.title a",
        "div.title h2",
        "h2",
        "h1",
        "meta[property='og:title']",
        "meta[name='twitter:title']",
    ]

    for selector in selectors:
        for element in soup.select(selector):
            if selector.startswith("meta"):
                text = (element.get("content") or "").strip()
            else:
                text = element.get_text(" ", strip=True)
            if not text:
                continue
            text = " ".join(text.split())
            if text.lower() in {"film", "movies", "tv shows"}:
                continue
            if "verify you are human" in text.lower() or "checking your browser" in text.lower():
                continue

            if element.name == "h2":
                spans = element.select("span")
                if spans:
                    text = " ".join(span.get_text(" ", strip=True) for span in spans[:1])
            return text
    return None


def extract_movie_synopsis(page_html: str) -> str | None:
    if not page_html:
        return None
    soup = BeautifulSoup(page_html, "html.parser")

    for overview in soup.select("div.overview"):
        text = overview.get_text(" ", strip=True)
        if text:
            return " ".join(text.split())
    return None


def iter_service_aliases(services):
    if isinstance(services, dict):
        return [(str(long_name).lower(), str(short_name).lower()) for long_name, short_name in services.items()]
    return [(str(service).lower(), str(service).lower()) for service in services]


def is_service_available(page_html: str, services: list[str]) -> bool:
    if not page_html:
        return False
    soup = BeautifulSoup(page_html, "html.parser")
    normalized = {service.lower() for service in services}

    candidates = []
    for element in soup.select('[title], [alt]'):
        for attr in ("title", "alt"):
            value = element.get(attr) or ""
            if value:
                candidates.append(value)

    for text in candidates:
        lower_text = text.lower()
        if any(service in lower_text for service in normalized):
            return True

    for text_node in soup.stripped_strings:
        lower_text = text_node.lower()
        if any(service in lower_text for service in normalized):
            return True

    return False


def fetch_search_page(title: str, lang: str, session: requests.Session | None = None) -> str | None:
    url = scrape_url.format(lang=quote_plus(lang), title=quote_plus(title))
    sess = session or requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": f"{lang},en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Upgrade-Insecure-Requests": "1",
    })
    try:
        resp = sess.get(url, timeout=30)
        resp.raise_for_status()
    except requests.RequestException:
        return None
    return resp.text


def fetch_movie_page(search_page_html: str, session: requests.Session | None = None) -> str | None:
    if not search_page_html:
        return None

    soup = BeautifulSoup(search_page_html, "html.parser")
    candidates = []
    for link in soup.select('a[href]'):
        href = link.get("href") or ""
        if not href or "/movie/" not in href:
            continue
        if not re.search(r"/movie/\d+(-|\?|$)", href):
            continue
        if any(nav in href for nav in ["now-playing", "upcoming", "top-rated", "new", "popular", "genre"]):
            continue
        candidates.append(href)

    for href in candidates:
        full_url = href if href.startswith("http") else f"https://www.themoviedb.org{href}"
        sess = session or requests.Session()
        sess.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Upgrade-Insecure-Requests": "1",
        })
        try:
            resp = sess.get(full_url, timeout=30)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException:
            continue

    return None


def write_country_movies_file(country: str, items):
    out_dir = os.path.join(base, "data", country)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "movies.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(items, fh, indent=2, ensure_ascii=False)


def scrape_movies(start_index: int = 0, end_index: int | None = None):
    metadata = load_metadata()
    countries = metadata.get("countries", [])
    services = metadata.get("services", [])
    service_aliases = list(iter_service_aliases(services))
    if not service_aliases:
        return {}

    rotten_path = os.path.join(base, "data", "rotten_300.json")
    try:
        with open(rotten_path, "r", encoding="utf-8") as fh:
            rotten_movies = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    if start_index < 0:
        start_index = 0
    if end_index is None:
        end_index = len(rotten_movies) - 1
    if end_index < start_index:
        raise ValueError("end_index must be greater than or equal to start_index")

    selected_movies = rotten_movies[start_index:end_index + 1]

    results = {}
    for country in countries:
        lang = get_country_language(country)
        print(f"country: {country}, language: {lang}")
        country_movies = []

        for movie in selected_movies:
            title = (movie or {}).get("title")
            if not title:
                continue
            print(f"Movie: {title}", end=' ', flush=True)
            search_page = fetch_search_page(title, lang)
            if not search_page:
                print("- no page")
                continue
            page_html = fetch_movie_page(search_page)
            if not page_html:
                print("- no movie page found")
                continue
            parsed_title = extract_movie_title(page_html)
            if not parsed_title:
                print("- no title found on page")
                continue

            synopsis = extract_movie_synopsis(page_html) or (movie.get("synopsis") or "")

            available_services = []
            for long_name, short_name in service_aliases:
                if is_service_available(page_html, [long_name]):
                    available_services.append(short_name)

            print("- ok")
            # print(parsed_title)
            # print(synopsis)
            # print(available_services)

            country_movies.append({
                "rank": movie.get("rank"),
                "title": parsed_title,
                "synopsis": synopsis,
                "streams_on": available_services,
            })

        results[country] = country_movies
        write_country_movies_file(country, country_movies)

    return results


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape Rotten Tomatoes movie availability for configured streaming services.")
    parser.add_argument("--start-index", type=int, default=0, help="Start movie index in the Rotten Tomatoes list (inclusive).")
    parser.add_argument("--end-index", type=int, default=None, help="End movie index in the Rotten Tomatoes list (inclusive). Defaults to the last movie.")
    return parser.parse_args()


def main():
    args = parse_args()
    movies = scrape_movies(start_index=args.start_index, end_index=args.end_index)
    print(json.dumps(movies, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
