# City scraper

Data ingestion scripts that turn a city into JSON files ready to be embedded for retrieval
(the future `Retriever` port of `ai_api`). Madrid is the configured city; another city is a
matter of changing the coordinates and the Wikipedia pages in `config/`.

Sources:

- **Google Places API (New)** for points of interest by category (bars, restaurants, hotels,
  museums, ...) around each zone in `config/city_zones.py`, filtered by the type lists in
  `config/categories.py`.
- **Wikipedia** for Metro, Cercanías and EMT stations, churches and palaces, and long-form
  "documentary" articles (history, culture, gastronomy, climate) listed in `config/info_documental.py`.
- **Fusion** steps merge the Google and Wikipedia records of the same station or monument.

## Run

```bash
cp .env.example .env         # GOOGLE_API_KEY (Google Places sources only)
just scrape                  # from the repo root; or, from this directory: uv run python main.py
```

`main.py` runs every step in sequence through `run_safe`, so one failing source does not stop the
pipeline. Output lands in `data/` (ignored by git); `sources/resources/linesemt.csv` is the only
input file.

## Layout

```text
main.py                       pipeline order
config/  env.py               GOOGLE_API_KEY from .env
         city_zones.py        search centres (lat/lng) per zone
         categories.py        Google Places categories and type filters
         info_documental.py   Wikipedia pages to extract
core/    http_client.py, utils.py
sources/ scraper_general.py   generic Google Places engine (one function, any category)
         *_wiki.py, *_google.py, *_fusion.py   per-domain extractors and merges
         documentales.py, documental_general.py   Wikipedia article extraction
```

The scraper is a member of the backend uv workspace (`package = false`): same virtualenv, same
lockfile, same ruff rules, no image. Add dependencies in this `pyproject.toml`, then `uv lock` at
`src/backend/`.
