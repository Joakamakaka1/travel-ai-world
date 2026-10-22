"""The cities manifest `data/cities.json`: what the planner knows about each city.

One entry per city with both a configuration and a built corpus; `ai_api` ships a
copy (`just corpus-manifest`) and takes its destinations from it. The intro comes
from the built corpus and the hero from the TOML, so writing it stays offline.
"""

import json
import re
from pathlib import Path
from typing import Any

from city_corpus.config.cities import CityConfig
from city_corpus.sources.wikidata import thumbnail_url

CITIES_MANIFEST = "cities.json"
DOCUMENTS = "documents.jsonl"

INTRO_DOC_ID = "wv:{lang}:{root}#section:intro:c1"
"""The lead of a Wikivoyage city article, as the builder ids it."""

INTRO_MAX_CHARS = 600
"""How much of the lead the overview gets: a paragraph or two."""

HERO_WIDTH = 1200
"""Hero photos are shown full width; the cards' thumbnails are 640 px."""

_SENTENCE_END = re.compile(
    r"[.!?…][\"”»’)]?(?=\s+[\"“«¡¿(A-ZÁÉÍÓÚÜÑ]|\s*$)"  # noqa: RUF001 — real quotes
)
"""A stop that ends a sentence: what follows starts a new one, or nothing does.

A closing quote or bracket belongs to the sentence it closes."""

_ABBREVIATION = re.compile(r"(?:\b(?:St|Str|Dr|Mr|Mrs|Ms|No|Sq|Ave)|\b[A-ZÁÉÍÓÚÜÑ])\.$")
"""What only looks like one: `home to St. Stephen`, `J. Smith`, `No. 7`."""


def intro_text(text: str) -> str:
    """A Wikivoyage lead as the overview shows it, without its title line.

    Cut at the last whole sentence within `INTRO_MAX_CHARS` (never at an
    abbreviation such as `St.`), paragraph breaks kept; else at a word, plus `…`.
    """
    _, _, body = text.partition("\n")
    body = body.strip()
    if len(body) <= INTRO_MAX_CHARS:
        return body
    window = body[:INTRO_MAX_CHARS]
    ends = [
        match.end()
        for match in _SENTENCE_END.finditer(window)
        if not _ABBREVIATION.search(window[: match.end()])
    ]
    if ends:
        return window[: ends[-1]].rstrip()
    cut = window.rstrip()
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip() + "…"


def city_intro(city: CityConfig, city_dir: Path) -> dict[str, dict[str, str]]:
    """The city's lead per Wikivoyage language, from the built corpus.

    A language whose corpus holds no intro document is absent (the article may
    have none, or the city may not be on that Wikivoyage at all).
    """
    wanted = {
        INTRO_DOC_ID.format(lang=site.lang, root=site.root): site.lang
        for site in city.wikivoyage
    }
    path = city_dir / DOCUMENTS
    if not wanted or not path.exists():
        return {}
    intro: dict[str, dict[str, str]] = {}
    with path.open(encoding="utf-8") as lines:
        for line in lines:
            if "#section:intro:c1" not in line:
                continue
            document = json.loads(line)
            lang = wanted.get(document.get("doc_id", ""))
            if lang is None or lang in intro:
                continue
            text = intro_text(document.get("text", ""))
            if not text:
                continue
            intro[lang] = {
                "text": text,
                "source_url": document.get("source_url", ""),
            }
    return {lang: intro[lang] for lang in sorted(intro)}


def city_entry(
    city: CityConfig, corpus_manifest: dict[str, Any], city_dir: Path
) -> dict[str, Any]:
    # a photo without its credit breaches its licence: half a `[hero]` is none
    hero = city.hero if city.hero and city.hero.file and city.hero.credit else None
    return {
        "slug": city.slug,
        "name": city.name,
        "country": city.country,
        "country_code": city.country_code,
        "aliases": sorted(set(city.aliases) | {city.slug}),
        "centre": [city.centre[0], city.centre[1]],
        "timezone": city.timezone,
        "documents": int(corpus_manifest.get("documents", 0)),
        "built_at": corpus_manifest.get("built_at"),
        "intro": city_intro(city, city_dir),
        "image_url": thumbnail_url(hero.file, HERO_WIDTH) if hero else None,
        "image_credit": hero.credit if hero else None,
    }


def cities_manifest(
    data_dir: Path, cities: dict[str, CityConfig]
) -> list[dict[str, Any]]:
    """Entries for every configured city whose corpus is built, sorted by slug."""
    entries: list[dict[str, Any]] = []
    for slug in sorted(cities):
        city_dir = data_dir / slug
        path = city_dir / "manifest.json"
        if not path.exists():
            continue
        corpus_manifest = json.loads(path.read_text(encoding="utf-8"))
        entries.append(city_entry(cities[slug], corpus_manifest, city_dir))
    return entries


def write_cities_manifest(data_dir: Path, cities: dict[str, CityConfig]) -> Path:
    """Write `data/cities.json` and return its path."""
    entries = cities_manifest(data_dir, cities)
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / CITIES_MANIFEST
    path.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return path
