# Top Streaming Picks

Small Flask app that lists top movie picks per streaming service and country. Pages are rendered with Jinja2 and Bootstrap.

Run locally:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Project layout:

- `app.py` — Flask application
- `templates/` — Jinja templates (`base.html`, `index.html`, `service.html`)
- `data/<country>/<service>.json` — JSON files that drive each service page
- `scripts/update_data.py` — helper to download or simulate JSON files

Example update:

```bash
python scripts/update_data.py --country se --service netflix --simulate
```

Then open `http://127.0.0.1:5000/` in your browser.
