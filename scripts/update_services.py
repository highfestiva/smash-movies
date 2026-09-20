import argparse
import json
import os
from urllib.parse import urlencode

import requests


base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
api_key = os.environ.get("WATCH_MODE_API_KEY")
base_url = "https://api.watchmode.com/v1"


def load_metadata(path: str = os.path.join(base, "data", "metadata.json")):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def filter_sources_for_country(sources, country: str):
    country_code = (country or "").upper()
    return [
        source for source in sources or []
        if (source.get("region") or "").upper() == country_code
    ]


def build_streams_on(sources, metadata_services):
    known = {}
    sorted_tags = []
    for name, short_name in metadata_services.items():
        known[name.lower()] = short_name
        known[short_name.lower()] = short_name
        sorted_tags.append(short_name)

    matched = set()
    for source in sources or []:
        name = source.get("name")
        if not name:
            continue
        lower_name = name.lower()
        tag = known.get(lower_name)
        if tag is None:
            for known_name, short_name in known.items():
                if known_name in lower_name or lower_name in known_name:
                    tag = short_name
                    break
        if tag:
            matched.add(tag)

    return [tag for tag in sorted_tags if tag in matched]


def find_streaming_sources(title: str, year: int, region: str | None = None):
    if year is None:
        raise ValueError("year must not be None")

    params = {
        "apiKey": api_key,
        "search_field": "name",
        "search_value": title,
    }

    search_url = f"{base_url}/search/?{urlencode(params)}"
    search_resp = requests.get(search_url, timeout=30)
    search_resp.raise_for_status()
    data = search_resp.json()

    title_id = None
    if titles := data.get("title_results"):
        for hit in titles:
            if hit.get("resultType") == "title" and abs(int(hit.get("year", 0)) - year) <= 1:
                title_id = hit.get("id")
                break

    if not title_id:
        return []

    sources_url = f"{base_url}/title/{title_id}/sources/?apiKey={api_key}"
    if region:
        sources_url = f"{sources_url}&region={region.upper()}"
    sources_resp = requests.get(sources_url, timeout=30)
    sources_resp.raise_for_status()
    sources = sources_resp.json()
    if region:
        sources = [source for source in sources if (source.get("region") or "").upper() == region.upper()]
    return sources


def update_all_countries(start_index: int = 0, end_index: int | None = None):
    metadata = load_metadata()
    countries = metadata.get("countries", {})
    services = metadata.get("services", {})

    rotten_path = os.path.join(base, "data", "rotten_300.json")
    with open(rotten_path, "r", encoding="utf-8") as fh:
        rotten_movies = json.load(fh)

    if end_index is None:
        end_index = len(rotten_movies) - 1

    selected = rotten_movies[start_index:end_index + 1]
    country_files = {}
    for country in countries:
        movies_path = os.path.join(base, "data", country, "movies.json")
        if not os.path.exists(movies_path):
            continue
        with open(movies_path, "r", encoding="utf-8") as fh:
            country_files[country] = json.load(fh)

    for movie in selected:
        title = movie["title"]
        year = movie["year"]

        print(f"{movie['rank']} {title}")
        sources = find_streaming_sources(title, year)

        for country in countries:
            country_movies = country_files.get(country)
            if country_movies is None:
                continue

            match = None
            for country_movie in country_movies:
                if country_movie.get("en_title") == title:
                    match = country_movie
                    break
            if match is None:
                continue

            country_sources = filter_sources_for_country(sources, country)
            match["streams_on"] = build_streams_on(country_sources, services)

    for country, country_movies in country_files.items():
        out_path = os.path.join(base, "data", country, "movies.json")
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(country_movies, fh, indent=2, ensure_ascii=False)

    return {country: country_files[country] for country in countries if country in country_files}


def parse_args():
    parser = argparse.ArgumentParser(description="Refresh per-country movies.json files using WatchMode streaming metadata.")
    parser.add_argument("--start-index", type=int, default=0, help="Start movie index in rotten_300.json (inclusive).")
    parser.add_argument("--end-index", type=int, default=None, help="End movie index in rotten_300.json (inclusive).")
    return parser.parse_args()


def main():
    args = parse_args()
    update_all_countries(start_index=args.start_index, end_index=args.end_index)


if __name__ == "__main__":
    main()
