#!/usr/bin/env python3
"""Refresh sitemap.xml lastmod from artifact dates.

Weekday publishers (brief, silicon, wire) used to rewrite sitemap.xml from
DEFAULT_SITEMAP, whose lastmod strings were frozen in August. This script
stamps lastmod from the file the URL actually serves:

- Daily JSON desks (silicon, brief, wire): top-level updated / snapshot
  (never a nested quote date). A workflow may have rebuilt the HTML and not
  committed it yet, so this date can be newer than git log.
- Catalog desks (inference, neoclouds, hyperscalers, data-centers, campuses)
  and physical-stack: git commit date of the built HTML
  (`git log -1 --format=%cs`). Their JSON as_of and JSON-LD dateModified stay
  on the catalog snapshot and must not freeze lastmod after a later rebuild.
  Sitemap workflows check out with fetch-depth 0. A shallow checkout has no
  history for that file; fall back to the masthead Updated chip, not today.
- Other HTML desks (contact, agents): dateModified, else the masthead
  Updated line, else the file's last commit
- llms.txt: the banner "Snapshot YYYY-MM-DD", else the homepage content date
- homepage: latest real change among country pages, chip pages, and the
  silicon / brief / wire artifact dates. rank-history as_of is not used:
  the weekday rank job writes a new snapshot date even when no row changed.
- country profile: last rank-row change, or a newer Wire signal on that page
- chip profile: last price change on a venue/term series, or last rank-row
  change. A repeated scrape of the same price does not move lastmod.
- undated HTML: git commit date of that file

Does not invent prices, ranks, or copy. Does not stamp today's date onto a
page whose own record did not change.
"""
from __future__ import annotations

import os
import re
import subprocess

from desk_data import chip_slug, slugify
from seo import public_path, sitemap_xml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Canonical HTML path -> (artifact, top-level keys in preference order).
# Dumps and feeds are not sitemap entries; do not add them back here.
JSON_SOURCES = {
    "/silicon": ("silicon.json", ("updated", "snapshot")),
    "/brief": ("brief.json", ("updated",)),
    "/wire": ("wire.json", ("updated",)),
    "/inference": ("inference.json", ("as_of", "updated", "snapshot")),
    "/neoclouds": ("neoclouds.json", ("as_of", "updated", "snapshot")),
    "/hyperscalers": ("hyperscalers.json", ("as_of", "updated", "snapshot")),
    "/data-centers": ("data-centers.json", ("updated", "as_of", "snapshot")),
    "/campuses": ("campuses.json", ("as_of", "updated", "snapshot")),
}

# Masthead date, else the file's last commit date.
HTML_SOURCES = {
    "/contact": "contact.html",
    "/agents": "agents.html",
    "/physical-stack": "physical-stack.html",
}

# Served HTML whose catalog snapshot (as_of / dateModified) lags a rebuild.
# lastmod is the HTML commit day, not that frozen snapshot.
BUILT_HTML = {
    "/inference": "inference.html",
    "/neoclouds": "neoclouds.html",
    "/hyperscalers": "hyperscalers.html",
    "/data-centers": "data-centers.html",
    "/campuses": "campuses.html",
    "/physical-stack": "physical-stack.html",
}

_MONTHS = {}
for _i, (_short, _long) in enumerate(
    zip(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        ["January", "February", "March", "April", "May", "June", "July", "August",
         "September", "October", "November", "December"],
    ),
    1,
):
    _MONTHS[_short.lower()] = _i
    _MONTHS[_long.lower()] = _i


def iso_day(value):
    s = str(value or "")[:10]
    return s if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) else ""


def parse_nice_day(text):
    m = re.fullmatch(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", str(text or "").strip())
    if not m:
        return ""
    mon = _MONTHS.get(m.group(2).lower())
    day = int(m.group(1))
    if not mon or not 1 <= day <= 31:
        return ""
    return f"{int(m.group(3)):04d}-{mon:02d}-{day:02d}"


def json_day(data, keys):
    if not isinstance(data, dict):
        return ""
    for key in keys:
        day = iso_day(data.get(key))
        if day:
            return day
    return ""


def html_updated_day(text):
    """Content date printed on the page. Ignores checkout mtime."""
    if not text:
        return ""
    m = re.search(r'dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})"', text)
    if m:
        return m.group(1)
    return masthead_day(text)


def masthead_day(text):
    """As-of chip on the page. Ignores JSON-LD dateModified."""
    if not text:
        return ""
    m = re.search(r"Updated <b>(\d{1,2}\s+[A-Za-z]+\s+\d{4})</b>", text)
    if m:
        return parse_nice_day(m.group(1))
    m = re.search(r"Updated (\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    return ""


def built_html_day(root, rel):
    """Last change of a served HTML file.

    Commit day when history contains the file. Otherwise the masthead Updated
    chip. Does not invent today's date.
    """
    committed = git_day(root, rel)
    if committed:
        return committed
    return masthead_day(_read(root, rel))


def llms_day(text):
    """Banner snapshot only. A later 'snapshot 2026-08-25' MTS cite is not this file's date."""
    if not text:
        return ""
    m = re.search(r"Snapshot (\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    m = re.search(r"As of (\d{1,2}\s+[A-Za-z]+\s+\d{4})", text)
    if m:
        return parse_nice_day(m.group(1))
    m = re.search(r"As of (\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    return ""


def git_day(root, rel):
    try:
        out = subprocess.check_output(
            ["git", "-C", root, "log", "-1", "--format=%cs", "--", rel],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""
    return iso_day(out)


def _read(root, name):
    path = os.path.join(root, name)
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _load_json(root, name):
    import json
    path = os.path.join(root, name)
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def url_path(loc):
    return public_path(loc)


def _latest_change(history_rows):
    """history_rows: iterable of (day, id, signature) in date order.

    Returns id -> day of the latest signature change. The first row for an id
    counts. A later row with the same signature does not.
    """
    prev = {}
    last = {}
    for day, rid, sig in history_rows:
        if not day or not rid:
            continue
        if prev.get(rid) != sig:
            prev[rid] = sig
            last[rid] = day
    return last


def chip_price_change_days(history):
    """Last date a chip's venue+term price actually changed. Same price again is ignored."""
    points = list((history or {}).get("points") or [])
    points.sort(key=lambda p: (str(p.get("date") or ""), p.get("venue") or "", p.get("term") or ""))
    series = {}
    rows = []
    for p in points:
        day = iso_day(p.get("date"))
        cid = p.get("chip")
        if not day or not cid:
            continue
        key = (cid, p.get("venue") or "", p.get("term") or "")
        px = p.get("price")
        prev = series.get(key, (None, None))
        if prev[1] != px:
            series[key] = (day, px)
            rows.append((day, cid, (key, px)))
    return _latest_change(rows)


def rank_change_days(history, index, fields):
    snaps = [s for s in ((history or {}).get("snapshots") or []) if s.get("index") == index]
    snaps.sort(key=lambda s: s.get("date") or "")
    rows = []
    for snap in snaps:
        day = iso_day(snap.get("date"))
        if not day:
            continue
        for row in snap.get("rows") or []:
            rid = row.get("id")
            sig = tuple(row.get(field) for field in fields)
            rows.append((day, rid, sig))
    return _latest_change(rows)


def wire_country_days(wire):
    """Latest Wire item date per country. The country page prints that signal."""
    last = {}
    for item in (wire or {}).get("items") or []:
        day = iso_day(item.get("date"))
        if not day:
            continue
        for iso in item.get("countries") or []:
            if iso not in last or day > last[iso]:
                last[iso] = day
    return last


def profile_days(root=None):
    """Path -> lastmod for /country/{slug}/ and /silicon/{slug}/ only."""
    root = root or ROOT
    silicon = _load_json(root, "silicon.json")
    hist = _load_json(root, "silicon-history.json")
    ranks = _load_json(root, "rank-history.json")
    wire = _load_json(root, "wire.json")
    data = _load_json(root, "data.json")
    days = {}
    if not isinstance(silicon, dict):
        silicon = {}
    price_chg = chip_price_change_days(hist if isinstance(hist, dict) else {})
    rank_si = rank_change_days(
        ranks if isinstance(ranks, dict) else {},
        "silicon",
        ("rank", "score", "display_usd", "venue", "term", "liquidity", "demand", "frontier"),
    )
    for chip in silicon.get("chips") or []:
        cid = chip.get("id")
        slug = chip_slug(cid, chip.get("vendor"))
        if not slug:
            continue
        cands = [price_chg.get(cid), rank_si.get(cid)]
        if not any(cands):
            disp = (chip.get("display") or {}).get("as_of")
            cands.append(iso_day(disp))
            for quote in chip.get("quotes") or []:
                cands.append(iso_day(quote.get("as_of") or quote.get("date")))
        best = max((d for d in cands if d), default="")
        if best:
            days[f"/silicon/{slug}/"] = best
    rank_co = rank_change_days(
        ranks if isinstance(ranks, dict) else {},
        "countries",
        ("rank", "t", "u", "gdc", "re", "rz"),
    )
    signals = wire_country_days(wire if isinstance(wire, dict) else {})
    for country in (data.get("countries") or []) if isinstance(data, dict) else []:
        iso = country.get("i3")
        name = country.get("n") or ""
        slug = slugify(name) if name else (country.get("sl") or "")
        if not iso or not slug:
            continue
        best = max((d for d in (rank_co.get(iso), signals.get(iso)) if d), default="")
        if best:
            days[f"/country/{slug}/"] = best
    return days


def content_dates(root=None):
    """Map sitemap path -> YYYY-MM-DD drawn from the artifact, not a frozen constant."""
    root = root or ROOT
    days = {}
    loaded = {}
    for path, (name, keys) in JSON_SOURCES.items():
        if name not in loaded:
            loaded[name] = _load_json(root, name)
        day = json_day(loaded[name], keys)
        if day:
            days[path] = day

    for path, rel in HTML_SOURCES.items():
        day = html_updated_day(_read(root, rel)) or git_day(root, rel)
        if day:
            days[path] = day

    # Snapshot dates stay on the catalog vintage. A later edit of the served
    # HTML is the change crawlers should see, and it is not a date after that
    # commit. Full history is required for the git day; see built_html_day.
    for path, rel in BUILT_HTML.items():
        built = built_html_day(root, rel)
        if built:
            days[path] = built

    profiles = profile_days(root)
    days.update(profiles)
    home_cands = [days.get(path) for path in ("/silicon", "/brief", "/wire")]
    home_cands.extend(profiles.values())
    home = max((d for d in home_cands if d), default="")
    if home:
        days["/"] = home

    llms = llms_day(_read(root, "llms.txt")) or days.get("/")
    if llms:
        days["/llms.txt"] = llms
    return days


def stamp_lastmod(urls, root=None):
    """Copy url dicts, replacing lastmod where the artifact has a content date."""
    days = content_dates(root)
    out = []
    for url in urls:
        path = url_path(url["loc"])
        day = days.get(path)
        if day:
            out.append({**url, "lastmod": day})
        else:
            out.append(dict(url))
    return out


def parse_sitemap(text):
    urls = []
    for block in re.findall(r"<url>(.*?)</url>", text, re.S):
        loc = re.search(r"<loc>(.*?)</loc>", block)
        if not loc:
            continue
        url = {"loc": loc.group(1).strip()}
        for key in ("lastmod", "changefreq", "priority"):
            found = re.search(rf"<{key}>(.*?)</{key}>", block)
            if found:
                url[key] = found.group(1).strip()
        urls.append(url)
    return urls


def refresh_sitemap(path, root=None):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    urls = parse_sitemap(text)
    stamped = stamp_lastmod(urls, root)
    xml = sitemap_xml(stamped)
    changed = [
        (url_path(new["loc"]), old.get("lastmod"), new.get("lastmod"))
        for old, new in zip(urls, stamped)
        if old.get("lastmod") != new.get("lastmod")
    ]
    before = [u["loc"] for u in urls]
    after = [u["loc"] for u in parse_sitemap(xml)]
    if xml != text:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(xml)
    return changed, before != after


def main():
    targets = [os.path.join(ROOT, "sitemap.xml")]
    deploy = os.path.join(HERE, "deploy", "sitemap.xml")
    if os.path.isfile(deploy):
        targets.append(deploy)
    for path in targets:
        changed, membership = refresh_sitemap(path)
        if not changed and not membership:
            print(f"sitemap lastmod already current: {path}")
            continue
        if membership:
            print(f"sitemap membership refreshed: {path}")
        if changed:
            print(f"sitemap lastmod refreshed: {path}")
            for loc, old, new in changed:
                print(f"  {loc}: {old or '—'} -> {new}")


if __name__ == "__main__":
    main()
