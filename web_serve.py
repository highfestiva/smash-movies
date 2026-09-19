#!/usr/bin/env python3

from flask import Flask, render_template, abort, request
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
ROTTEN_IMAGE_DIR = DATA_DIR / "rotten_300" / "img"

app = Flask(
    __name__,
    template_folder="templates",
    static_folder=str(ROTTEN_IMAGE_DIR),
    static_url_path="/movimg",
)


def load_movie_data(country: str):
    rotten_path = DATA_DIR / "rotten_300.json"

    with rotten_path.open("r", encoding="utf-8") as fh:
        movies = json.load(fh)

    for movie in movies:
        movie["services"] = {}

    for service_path in (DATA_DIR / country).glob("*.json"):
        with service_path.open("r", encoding="utf-8") as fh:
            service_movies = json.load(fh)
        for service_movie in service_movies:
            for movie in movies:
                if movie["rank"] == service_movie["rank"]:
                    movie["services"][service_path.stem] = service_movie

    return movies


@app.route("/")
def index():
    countries = []
    for path in sorted(DATA_DIR.glob("*")):
        if path.is_dir() and any(path.glob("*.json")):
            countries.append(path.name)
    return render_template("index.html", countries=countries)


@app.route("/<country>")
def service_page(country):
    movies = load_movie_data(country)
    if movies is None:
        abort(404)

    per_page = 15
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1

    total_pages = max(1, (len(movies) + per_page - 1) // per_page)
    if page > total_pages:
        page = total_pages

    start = (page - 1) * per_page
    end = start + per_page
    paginated = movies[start:end]
    nearby_pages = list(range(max(1, page - 2), min(total_pages, page + 2) + 1))

    return render_template(
        "movie_list.html",
        country=country,
        movies=paginated,
        page=page,
        total_pages=total_pages,
        nearby_pages=nearby_pages,
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
