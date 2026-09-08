#!/usr/bin/env python3
# Shared robots / sitemap / Open Graph / JSON-LD helpers. No invented numbers.
# Builders import these so every public page speaks with one voice.
from datetime import datetime as _dt

# Search engines and citation-oriented fetchers stay open.
# Training / bulk scrapers are asked not to vacuum the site; HTML + llms.txt
# remain the citation path. Do not noindex the whole site.
SEARCH_BOTS = (
    "Googlebot",
    "Bingbot",
    "Applebot",
    "OAI-SearchBot",
    "ChatGPT-User",
    "PerplexityBot",
)

# Known training / bulk crawlers. Hypothesis: disallow their vacuum, keep search.
TRAINING_BOTS = (
    "GPTBot",
    "Google-Extended",
    "ClaudeBot",
    "anthropic-ai",
    "Applebot-Extended",
    "CCBot",
    "Bytespider",
    "Amazonbot",
    "meta-externalagent",
    "FacebookBot",
    "cohere-ai",
    "Diffbot",
    "YouBot",
)

# Large public JSON already on the site; do not add a new dump. Training bots
# are pointed at HTML / llms.txt instead of the bulk files.
BULK_PATHS = (
    "/data.json",
    "/silicon-history.json",
    "/rank-history.json",
    "/campuses.json",
    "/hyperscalers.json",
    "/neoclouds.json",
    "/inference.json",
    "/wire.json",
    "/silicon.json",
)

SITE = "https://compute.world"


def robots_txt():
    lines = [
        "# compute.world robots. Search (Google, Bing, Apple, OAI-SearchBot) is welcome.",
        "# Training / bulk scrapers: use /llms.txt and cite; do not vacuum JSON dumps.",
        "# The site is indexed. This file does not noindex anything.",
        "",
        "User-agent: *",
        "Allow: /",
        "Allow: /llms.txt",
        "Allow: /agents.html",
        "",
    ]
    for bot in SEARCH_BOTS:
        lines.extend([f"User-agent: {bot}", "Allow: /", ""])
    for bot in TRAINING_BOTS:
        lines.append(f"User-agent: {bot}")
        lines.append("Allow: /llms.txt")
        lines.append("Allow: /agents.html")
        for path in BULK_PATHS:
            lines.append(f"Disallow: {path}")
        lines.append("Crawl-delay: 10")
        lines.append("")
    lines.append(f"Sitemap: {SITE}/sitemap.xml")
    lines.append("")
    return "\n".join(lines)


def sitemap_xml(urls):
    """urls: list of dicts with loc, optional lastmod, changefreq, priority."""
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in urls:
        parts.append("<url>")
        parts.append(f"<loc>{u['loc']}</loc>")
        if u.get("lastmod"):
            parts.append(f"<lastmod>{u['lastmod']}</lastmod>")
        if u.get("changefreq"):
            parts.append(f"<changefreq>{u['changefreq']}</changefreq>")
        if u.get("priority"):
            parts.append(f"<priority>{u['priority']}</priority>")
        parts.append("</url>")
    parts.append("</urlset>")
    parts.append("")
    return "\n".join(parts)


DEFAULT_SITEMAP = [
    {"loc": f"{SITE}/", "lastmod": "2026-08-18", "changefreq": "weekly"},
    {"loc": f"{SITE}/silicon.html", "lastmod": "2026-08-18", "changefreq": "weekly"},
    {"loc": f"{SITE}/silicon.json", "lastmod": "2026-08-18", "changefreq": "weekly"},
    {"loc": f"{SITE}/silicon-history.json", "lastmod": "2026-08-18", "changefreq": "weekly"},
    {"loc": f"{SITE}/rank-history.json", "lastmod": "2026-08-19", "changefreq": "daily"},
    {"loc": f"{SITE}/silicon.xml", "lastmod": "2026-08-18", "changefreq": "weekly"},
    {"loc": f"{SITE}/inference.html", "lastmod": "2026-08-19", "changefreq": "weekly"},
    {"loc": f"{SITE}/inference.json", "lastmod": "2026-08-19", "changefreq": "weekly"},
    {"loc": f"{SITE}/inference.xml", "lastmod": "2026-08-19", "changefreq": "weekly"},
    {"loc": f"{SITE}/neoclouds.html", "lastmod": "2026-08-19", "changefreq": "weekly"},
    {"loc": f"{SITE}/neoclouds.json", "lastmod": "2026-08-19", "changefreq": "weekly"},
    {"loc": f"{SITE}/neoclouds.xml", "lastmod": "2026-08-19", "changefreq": "weekly"},
    {"loc": f"{SITE}/hyperscalers.html", "lastmod": "2026-08-19", "changefreq": "weekly"},
    {"loc": f"{SITE}/hyperscalers.json", "lastmod": "2026-08-19", "changefreq": "weekly"},
    {"loc": f"{SITE}/hyperscalers.xml", "lastmod": "2026-08-19", "changefreq": "weekly"},
    {"loc": f"{SITE}/data-centers.html", "lastmod": "2026-08-22", "changefreq": "monthly"},
    {"loc": f"{SITE}/data-centers.json", "lastmod": "2026-08-22", "changefreq": "monthly"},
    {"loc": f"{SITE}/data-centers.xml", "lastmod": "2026-08-22", "changefreq": "monthly"},
    {"loc": f"{SITE}/campuses.html", "lastmod": "2026-08-22", "changefreq": "weekly"},
    {"loc": f"{SITE}/campuses.json", "lastmod": "2026-08-22", "changefreq": "weekly"},
    {"loc": f"{SITE}/brief", "lastmod": "2026-08-18", "changefreq": "daily"},
    {"loc": f"{SITE}/brief.json", "lastmod": "2026-08-18", "changefreq": "daily"},
    {"loc": f"{SITE}/brief.xml", "lastmod": "2026-08-18", "changefreq": "daily"},
    {"loc": f"{SITE}/wire.html", "lastmod": "2026-08-18", "changefreq": "weekly"},
    {"loc": f"{SITE}/agents.html", "lastmod": "2026-08-18", "changefreq": "weekly"},
    {"loc": f"{SITE}/contact.html", "lastmod": "2026-08-22", "changefreq": "monthly"},
    {"loc": f"{SITE}/data.json", "changefreq": "weekly"},
    {"loc": f"{SITE}/llms.txt", "lastmod": "2026-08-18", "changefreq": "weekly"},
    {"loc": f"{SITE}/wire.json", "changefreq": "weekly"},
]


def og_block(title, description, url, image, og_type="website", image_alt=""):
    img = image if image.startswith("http") else f"{SITE}/{image.lstrip('/')}"
    alt = image_alt or title
    return (
        f'<meta property="og:site_name" content="compute.world">\n'
        f'<meta property="og:type" content="{og_type}">\n'
        f'<meta property="og:title" content="{title}">\n'
        f'<meta property="og:description" content="{description}">\n'
        f'<meta property="og:url" content="{url}">\n'
        f'<meta property="og:image" content="{img}">\n'
        f'<meta property="og:image:width" content="1200">\n'
        f'<meta property="og:image:height" content="630">\n'
        f'<meta property="og:image:alt" content="{alt}">\n'
        f'<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:title" content="{title}">\n'
        f'<meta name="twitter:description" content="{description}">\n'
        f'<meta name="twitter:image" content="{img}">\n'
        f'<meta name="author" content="Pukar C. Hamal">\n'
        f'<meta name="citation_title" content="{title}">\n'
        f'<meta name="citation_author" content="Pukar C. Hamal">\n'
        f'<meta name="citation_publisher" content="compute.world">\n'
        f'<meta name="dc.creator" content="Pukar C. Hamal">\n'
        f'<meta name="dc.publisher" content="compute.world">\n'
        f'<meta name="dc.identifier" content="{url}">\n'
        f'<meta name="dc.rights" content="CC BY 4.0">\n'
        f'<link rel="cite-as" href="{url}">'
    )


def breadcrumb_ld(items):
    """items: list of (name, url)."""
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": url}
            for i, (name, url) in enumerate(items)
        ],
    }


def nice_day(iso, kind="long"):
    """Format YYYY-MM-DD. kind=long -> '19 August 2026'; short -> '19 Aug 2026'."""
    if not iso:
        return ""
    s = str(iso)[:10]
    try:
        d = _dt.strptime(s, "%Y-%m-%d")
    except ValueError:
        return s
    if kind == "short":
        return f"{d.day} {d.strftime('%b %Y')}"
    return f"{d.day} {d.strftime('%B %Y')}"


def person_author():
    # Same facts only: name, desk URL, personal site. No email (Turnstile-gated).
    return {
        "@type": "Person",
        "name": "Pukar C. Hamal",
        "url": f"{SITE}/contact.html",
        "sameAs": ["https://pukarhamal.com/"],
    }


def org_publisher():
    return {
        "@type": "Organization",
        "@id": f"{SITE}/#org",
        "name": "compute.world",
        "alternateName": ["Compute World", "The World's Compute & Silicon Index"],
        "url": SITE,
        "founder": person_author(),
        "description": (
            "Pukar C. Hamal's public compute desk: the world's compute & silicon index "
            "(CNW™ + Silicon Tape). Companies inquire via https://compute.world/contact.html."
        ),
        "sameAs": ["https://github.com/pchamal/compute-world"],
    }
