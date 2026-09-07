# Shared masthead for public compute.world pages (wire, silicon tape, campuses, …).
# v1.5 desk chrome: brand + Countries · Silicon prices · Trends · Projects · Method ·
# Country profiles · Data · More. Homepage uses the same markup via desk_chrome.
# embed.html is an embeddable widget — do not add this chrome there.
from desk_chrome import DESKHEAD_CSS, deskhead_markup, deskhead_script
from desk_data import load_json

# Kept so existing builders can still import LINKS if they inspect it.
LINKS = (
    ("board", "Countries", "/#board"),
    ("silicon", "Silicon prices", "/#silicon"),
    ("trends", "Trends", "/#trends"),
    ("projects", "Projects", "/#projects"),
    ("method", "Method", "/#method"),
    ("profiles", "Country profiles", "/#profiles"),
    ("data", "Data", "/#data"),
    ("wire", "Wire", "/wire.html"),
    ("inference", "Inference", "/inference.html"),
    ("neoclouds", "Neoclouds", "/neoclouds.html"),
    ("hyperscalers", "Hyperscalers", "/hyperscalers.html"),
    ("datacenters", "Data centers", "/data-centers.html"),
    ("campuses", "Campuses", "/campuses.html"),
    ("contact", "Contact", "/contact.html"),
    ("agents", "Agents", "/agents.html"),
)

PAGE_HREF = {
    "inference": "/inference.html",
    "neoclouds": "/neoclouds.html",
    "hyperscalers": "/hyperscalers.html",
}
HOME_CURRENT = ("silicon",)
INNER = {
    "wire": "wire",
    "silicon": "silicon",
    "inference": "inference",
    "neoclouds": "neoclouds",
    "hyperscalers": "hyperscalers",
    "datacenters": "datacenters",
    "campuses": "campuses",
    "contact": "contact",
    "agents": "agents",
    "brief": "brief",
}


def _asof():
    for name in ("silicon.json", "brief.json"):
        try:
            meta = load_json(name)
        except FileNotFoundError:
            continue
        day = str(meta.get("updated") or meta.get("snapshot") or "")[:10]
        if len(day) == 10:
            return day
    return "2026-09-07"


def css():
    return DESKHEAD_CSS


def markup(page):
    return deskhead_markup(page, _asof())


def script(page):
    return deskhead_script()
