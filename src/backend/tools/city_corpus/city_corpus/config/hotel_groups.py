"""The hotel groups the photo stage must tell apart from parked or sold domains.

A chain's site redirects to the group's booking platform, may show the group's logo
as its `og:image` and carries the group's name; this is the data, and the rules
that read it live in `sources/photos.py`.
"""

import re

GROUP_DOMAINS: tuple[str, ...] = (
    "accor.com",
    "adinahotels.com",
    "aohostels.com",
    "barcelo.com",
    "bestwestern.com",
    "cataloniahotels.com",
    "eurostarshotels.com",
    "hilton.com",
    "hotel-bb.com",
    "hyatt.com",
    "iberostar.com",
    "ihg.com",
    "kempinski.com",
    "leonardo-hotels.com",
    "marriott.com",
    "melia.com",
    "motel-one.com",
    "nh-hotels.com",
    "petitpalace.com",
    "premierinn.com",
    "radissonhotels.com",
    "ritzcarlton.com",
    "room-matehotels.com",
    "scandichotels.com",
    "steigenberger.com",
    "vinccihoteles.com",
)
"""Registrable domains a brand's own domain may redirect to (`ibis.com` → Accor).

Every subdomain counts; a hotel domain redirecting anywhere else is parked, sold or
gone. Copied, in this order, into `ai_api/infrastructure/site_previews.py`, which
cannot import this package: change one, change the other.
"""

BRAND_ASSET_PATH = re.compile(
    r"logo|brand|generic|default|placeholder|maldives", re.IGNORECASE
)
"""A group's preview that is not the house: logo, brand asset, campaign banner.

Checked on top of `LOGO_PATH`, and only on a group domain: `brand` and `generic`
are ordinary words in an independent hotel's file names."""

OG_SKIPPED_DOMAINS: frozenset[str] = frozenset()
"""Groups whose `og:image` is one picture on every page; the page body is read instead.

Empty on purpose: skipping IHG or a&o cost more hotels than it saved (IHG's banner
is a `BRAND_ASSET_PATH` match, a&o loads its gallery by script). Add a group only
when its preview repeats across two hotels and its pages carry the house's photo
in their markup."""

CHAIN_NAMES = re.compile(
    r"\b("
    r"a&o|ac hotel|accor|adagio|adina|aloft|autograph collection|"
    r"barcel[oó]|b&b hotel|best western|campanile|catalonia|citadines|"
    r"conrad|courtyard|crowne plaza|doubletree|eurostars|exe hotel|"
    r"four points|four seasons|h10|hampton|hilton|holiday inn|hotel indigo|"
    r"hyatt|ibis|iberostar|intercontinental|kempinski|le m[eé]ridien|"
    r"leonardo|marriott|meininger|meli[aá]|mercure|motel one|moxy|"
    r"nh collection|nh hotel|novotel|park inn|park plaza|petit palace|"
    r"premier inn|pullman|radisson|riu|ritz-?carlton|room mate|scandic|"
    r"sheraton|sofitel|st\.? regis|steigenberger|travelodge|tryp|vincci|"
    r"waldorf astoria|westin"
    r")\b|\bnh\b",
    re.IGNORECASE,
)
"""A chain hotel, by its name.

Only feeds the report's list of chain hotels without a photo; it decides nothing
about the corpus."""


def host_of(url_or_host: str) -> str:
    """The bare host of a URL, or a host as it is."""
    host = url_or_host.split("://", 1)[-1].split("/", 1)[0].split("?", 1)[0]
    return host.rsplit("@", 1)[-1].split(":", 1)[0].lower().rstrip(".")


def _under(host: str, domains: "frozenset[str] | tuple[str, ...]") -> bool:
    return any(host == domain or host.endswith(f".{domain}") for domain in domains)


def is_group_site(url_or_host: str) -> bool:
    """Whether this URL or host belongs to one of the listed groups.

    Subdomains included: `all.accor.com` is Accor, `notaccor.com` is not.
    """
    return _under(host_of(url_or_host), GROUP_DOMAINS)


def skips_preview(url_or_host: str) -> bool:
    """Whether this group's `og:image` is a banner rather than the hotel."""
    return _under(host_of(url_or_host), OG_SKIPPED_DOMAINS)


def is_chain(name: str | None) -> bool:
    """Whether this hotel's name is a chain's."""
    return bool(name and CHAIN_NAMES.search(name))
