# Smash Movies

A small project for tracking good movies for streaming availability in different countries. You can statically generate and service this anywhere you please.

## Project overview

- `data/metadata.json` the countries and streaming services you want to show.
- `data/rotten_300.json` generated, contains the Rotten Tomatoes master list.
- `data/<country>/movies.json` generated, contains the country-specific scraped movie availability data.
- `scripts/update_rotten_300.py` refreshes the Rotten Tomatoes list.
- `scripts/update_countries.py` updates country availability data for configured services.
- `index.html` and `list.html` are static frontend pages that load the generated JSON files.
- `static/js/list.js` merges the local country data with the Rotten Tomatoes fallback list.

## Screenshot

![Smash Movies screenshot](doc/screenshot.jpg)

## Update the Rotten Tomatoes list

From the project root, run:

```bash
python scripts/update_rotten_300.py
```

This downloads or refreshes the Rotten Tomatoes movie list and writes the data into `data/rotten_300.json`.

## Update the streaming list

Before scraping, make sure the metadata file is configured with the countries and service names you want to process:

```bash
python scripts/update_countries.py
```

This will:

- load the existing per-country movie file
- skip entries already present for the same rank and `en_title`
- fetch new or updated entries only
- write sorted results back into `data/<country>/movies.json`

The default metadata configuration is stored in `data/metadata.json`.

## Run the unit tests

From the project root:

```bash
python -m unittest discover -s tests -v
```

## Test locally with a simple web server

To preview the static pages locally:

```bash
python -m http.server 8000
```

Then open [http://localhost:8000/](http://localhost:8000/).
