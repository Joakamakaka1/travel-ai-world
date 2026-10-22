"""The readiness gate: what a city corpus must hold before it is indexed.

`report.gate` measures a corpus against these; `python -m city_corpus report`
fails when any is missed. A city short of one needs more sources (Wikipedia
categories, a wider bbox, a lower district admin level), not luck.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Thresholds:
    # `see` + `history` + `do` listings with coordinates: what fills the days
    located_sights: int = 150
    # `eat` listings with coordinates: lunch and dinner near the day's route
    located_eat: int = 100
    # `sleep` documents, and how many of them the hotel step can place on a map
    sleep: int = 20
    located_sleep: int = 10
    # located `sleep` places with an `image_url`: a stay is never offered without
    # a photo (ADR 0022)
    pictured_sleep: int = 10
    # distinct districts: the neighbourhood carousel offers three
    districts: int = 5
    # districts with a `neighbourhood` document (Wikivoyage district page or the
    # district's Wikipedia article): what the carousel ranks
    described_districts: int = 5
    # share of `see` + `history` listings with an `image_url`: cards need photos
    pictured_sights_share: float = 0.5
    # monthly climate normals (`om:climate:<slug>:MM`)
    climate_normals: int = 12
    # curated tours (`curated/<slug>/tours.toml`) and `tour` documents of any
    # source: every city ships its free walking tours and the notable paid ones
    curated_tours: int = 3
    tour_documents: int = 3


DEFAULT_THRESHOLDS = Thresholds()
