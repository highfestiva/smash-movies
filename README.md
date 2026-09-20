# Smash Movies

A small project for tracking good movies for streaming availability in different countries. You can statically generate
and service this anywhere you please.

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

## Update the whole data set

```bash
# fetch rotten tomatoes list
python scripts/update_rotten_300.py

# fetch images missing from rotten tomatoes
python scripts/download_missing_imgs.py

# update national movies
python scripts/update_countries.py

# improve service coverage (tmdb is not reliable)
python scripts/update_countries.py
```

This will:

- fill up `data/rotten_300.json`
- download images to `data/img/`
- create per-country movie file in `data/<country>/movies.json`

## Run the unit tests

From the project root:

```bash
python -m unittest discover -s tests -v
```

## Test locally with a simple web server

```bash
python -m http.server 8000
```

Then open [http://localhost:8000/](http://localhost:8000/).

## Web implementation

The JavaScript code will download the complete (English) movie list,
the national movie list and the metadata file.


## AI

This was a free CoPilot experiment. In a few ways, it really made me faster. Like when pivoting to a new architecture
from having a Python backend server to doing everything in the JavaScript frontend. Or throwing together a unit or
integration test. But most of the time, it was really a sink with a lot of boilerplate.

I actually didn't notice much improvement from 6 months ago, which is a relief! Perhaps we're at the top of the S-curve
this time around. :)
