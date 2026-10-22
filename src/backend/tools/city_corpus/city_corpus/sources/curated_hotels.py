"""Curated hotel photos: `curated/<city>/hotels.toml`, for hotels no rule can picture.

A person reads the photo on the hotel's own site (never a reseller) and records the
page and the date, as in `tours.toml`; the image is hot-linked and credited like the
site's own preview (ADR 0021, ADR 0022). `sources/photos.py` binds and verifies it.
"""

import datetime as dt
import logging
import tomllib
from pathlib import Path
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

logger = logging.getLogger(__name__)

STALE_AFTER_DAYS = 400
"""A photo outlives a tour's schedule: a yearly check is enough, and a stale entry
only warns (the card hides itself when the URL stops answering)."""

OSM_PREFIX = "osm:"
"""`match = "osm:node/4553094489"`: the hotel by its OpenStreetMap element,
for the second `Hotel Madrid` on the same street. Any other `match` is a name,
folded (lower case, accents dropped) before it is compared."""

NonEmpty = Annotated[str, Field(min_length=1)]


class HotelDataError(ValueError):
    """The curated file is malformed, or an entry names no hotel (or several).

    The message lists every problem, with the file it came from."""


class CuratedHotel(BaseModel):
    """One `[[hotel]]` table."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    match: NonEmpty
    image_url: NonEmpty | None = None
    credit: NonEmpty | None = None
    """What the card prints beside the photo: the bare domain it was read from
    (`marriott.com`), or a Commons credit line for a file from Commons."""
    source_url: NonEmpty
    """The page the picture was read on, in a browser, by a person."""
    checked: dt.date
    drop: bool = False
    """The hotel leaves the corpus: a person looked and found no picture of it
    that is its own (the site is gone, or only a reseller shows it), so the
    picture a rule would find is someone else's. `note` says why."""
    note: str | None = None  # for maintainers; never published

    @field_validator("image_url", "source_url")
    @classmethod
    def _http(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith(("https://", "http://")):
            raise ValueError("must be an http(s) URL")
        return value

    @model_validator(mode="after")
    def _photo_or_drop(self) -> "CuratedHotel":
        if self.drop and (self.image_url or self.credit):
            raise ValueError("a dropped hotel takes no image_url or credit")
        if not self.drop and not (self.image_url and self.credit):
            raise ValueError("image_url and credit are required unless drop = true")
        return self

    @property
    def osm_id(self) -> str | None:
        """The OpenStreetMap element this entry names, or None for a name match."""
        return (
            self.match.removeprefix(OSM_PREFIX)
            if self.match.startswith(OSM_PREFIX)
            else None
        )


def load(path: Path) -> list[CuratedHotel]:
    """Parse and validate the file; raise `HotelDataError` listing every problem.

    A city without the file has no curated photos, which is the normal case.
    """
    if not path.exists():
        return []
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise HotelDataError(f"{path}: {exc}") from exc
    unknown = sorted(set(raw) - {"hotel"})
    if unknown:
        raise HotelDataError(f"{path}: unknown table(s) {', '.join(unknown)}")
    problems: list[str] = []
    hotels: list[CuratedHotel] = []
    for index, entry in enumerate(raw.get("hotel", []), start=1):
        label = (
            entry.get("match", f"#{index}") if isinstance(entry, dict) else f"#{index}"
        )
        try:
            hotels.append(CuratedHotel.model_validate(entry))
        except ValidationError as exc:
            problems += [
                f"{label}.{'.'.join(map(str, e['loc']))}: {e['msg']}"
                for e in exc.errors()
            ]
    matches = [h.match for h in hotels]
    problems += [
        f"{m}: duplicate match"
        for m in sorted({m for m in matches if matches.count(m) > 1})
    ]
    if problems:
        raise HotelDataError(f"{path}:\n  " + "\n  ".join(problems))
    return sorted(hotels, key=lambda h: h.match)


def warn_stale(hotels: list[CuratedHotel], today: dt.date) -> list[str]:
    """The matches checked more than `STALE_AFTER_DAYS` ago (logged, not fatal)."""
    stale = [h.match for h in hotels if (today - h.checked).days > STALE_AFTER_DAYS]
    if stale:
        logger.warning(
            "curated hotel photos not checked for %d+ days: %s",
            STALE_AFTER_DAYS,
            ", ".join(stale),
        )
    return stale
