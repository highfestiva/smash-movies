import argparse
from bs4 import BeautifulSoup
import json
import os
import requests
from urllib.parse import quote_plus

try:
    from scripts.util import fetch_json, html_to_text
except ModuleNotFoundError:
    from util import fetch_json, html_to_text


scrape_url = "https://netflixguiden.se/search?query={title}"

base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
rotten_path = os.path.join(base, "data", "rotten_300.json")
out_path = os.path.join(base, "data", "se", "netflix.json")


def extract_results_link(html: str, year: int) -> str | None:
    if not html:
        print('no html')
        return None

    soup = BeautifulSoup(html, "html.parser")
    results = soup.select_one("div.results")
    if results is None:
        return None

    for year_offset in (0, 1, -1):
        target_year = year + year_offset
        for item in results.select(".titles li"):
            text = item.get_text(" ", strip=True)
            if str(target_year) not in text:
                continue
            link = item.select_one("a[href]")
            if link is not None:
                return link.get("href")

    return None


def is_available_in_sweden(page_text: str) -> bool:
    page_text = page_text.lower()
    unavailable_text = "är inte tillgänglig på netflix i sverige"
    return unavailable_text not in page_text


def fetch_search_result_page(movie: dict, session: requests.Session | None = None) -> str | None:
    title = movie.get("title")
    url = scrape_url.format(title=quote_plus(title))
    sess = session or requests.Session()

    payload = fetch_json(url, session=sess, timeout=20, retries=3, backoff=1.0)
    html = payload

    if isinstance(payload, dict):
        html = payload.get("data") or payload.get("html") or ""

    if not isinstance(html, str):
        # print(title, 'no result html')
        return None

    year = movie.get("year")
    result_link = extract_results_link(html, year)
    if not result_link:
        # print(title, 'no result link')
        return None

    page_url = result_link if result_link.startswith("http") else f"https://netflixguiden.se{result_link}"
    resp = sess.get(page_url, timeout=20)
    resp.raise_for_status()
    return resp.text


def extract_movie_title(h1):
    strong = h1.find("strong")
    if strong:
        strong.extract()
    title = h1.get_text(" ", strip=True)
    return title


def improve_movie_data(page_html, movie):
    if not page_html or not isinstance(movie, dict):
        return movie

    soup = BeautifulSoup(page_html, "html.parser")

    title_h1 = soup.select_one("div.main h1") or soup.select_one("h1")
    if title_h1:
        title = extract_movie_title(title_h1)
        if title:
            movie["title"] = title

    synopsis = soup.select_one("p.synopsis") or soup.select_one(".synopsis")
    if synopsis:
        text = synopsis.get_text(" ", strip=True)
        if text:
            movie["synopsis"] = text

    return movie


def write_se_netflix(items):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(items, fh, indent=2, ensure_ascii=False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--num-movies", "-n", default=500, type=int)
    args = p.parse_args()

    try:
        with open(rotten_path, "r", encoding="utf-8") as fh:
            rotten = json.load(fh)
    except FileNotFoundError:
        print(f"Missing Rotten Tomatoes file: {rotten_path}")
        return
    except json.JSONDecodeError as exc:
        print(f"Invalid Rotten Tomatoes JSON: {exc}")
        return

    session = requests.Session()
    available = []

    for idx, movie in enumerate(rotten[:args.num_movies]):
        title = (movie or {}).get("title")
        if not title:
            continue

        print(movie.get("rank"), end='. ', flush=True)

        try:
            page_html = fetch_search_result_page(movie, session=session)
            page_text = html_to_text(page_html)
        except Exception as exc:
            print(f"Skipping {title!r}: remote site unavailable or failed: {exc}")
            return

        if not page_html:
            print(f"{title} - no search result")
            continue

        if not is_available_in_sweden(page_text):
            print(f"{title} - not available in Sweden")
            continue

        year = movie.get("year")
        year_seen = False
        for year_offset in [0, +1, -1]: # allow some discrepancy
            year_seen |= str(year+year_offset) in page_text
        if not year_seen:
            print(f"{title} - found wrong version (years don't match)")
            continue

        improve_movie_data(page_html, movie)

        print(f"{title} - ok")
        available.append({
            "rank": movie.get("rank"),
            "title": movie.get("title"),
            "synopsis": movie.get("synopsis") or "",
        })

    write_se_netflix(available)
    print(f"Wrote {len(available)} films to {out_path}")


if __name__ == "__main__":
    main()
