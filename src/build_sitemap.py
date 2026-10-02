#!/usr/bin/env python3
"""Refresh sitemap.xml lastmod from artifact dates.

Weekday publishers (brief, silicon, wire) used to rewrite sitemap.xml from
DEFAULT_SITEMAP, whose lastmod strings were frozen in August. This script
stamps lastmod from the file the URL actually serves:

- JSON desks: top-level updated / snapshot / as_of (never a nested quote date)
- HTML desks: dateModified, else the masthead "Updated" line
- llms.txt: the banner "Snapshot YYYY-MM-DD", else the desk as-of
- homepage: same as-of as the desk (silicon / brief / rank-history)
- undated HTML: git commit date of that file

Country and chip URLs are left alone. Does not invent prices, ranks, or copy.
"""
from __future__ import annotations

import os
import re
import subprocess

from desk_data import as_of
from seo import SITE, sitemap_xml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# path -> (filename, top-level keys in preference order)
JSON_SOURCES = {
    "/silicon.html": ("silicon.json", ("updated", "snapshot")),
    "/silicon.json": ("silicon.json", ("updated", "snapshot")),
    "/silicon.xml": ("silicon.json", ("updated", "snapshot")),
    "/silicon-history.json": ("silicon-history.json", ("as_of", "updated")),
    "/rank-history.json": ("rank-history.json", ("as_of", "updated")),
    "/brief": ("brief.json", ("updated",)),
    "/brief.json": ("brief.json", ("updated",)),
    "/brief.xml": ("brief.json", ("updated",)),
    "/wire.html": ("wire.json", ("updated",)),
    "/wire.json": ("wire.json", ("updated",)),
    "/inference.html": ("inference.json", ("as_of", "updated", "snapshot")),
    "/inference.json": ("inference.json", ("as_of", "updated", "snapshot")),
    "/inference.xml": ("inference.json", ("as_of", "updated", "snapshot")),
    "/neoclouds.html": ("neoclouds.json", ("as_of", "updated", "snapshot")),
    "/neoclouds.json": ("neoclouds.json", ("as_of", "updated", "snapshot")),
    "/neoclouds.xml": ("neoclouds.json", ("as_of", "updated", "snapshot")),
    "/hyperscalers.html": ("hyperscalers.json", ("as_of", "updated", "snapshot")),
    "/hyperscalers.json": ("hyperscalers.json", ("as_of", "updated", "snapshot")),
    "/hyperscalers.xml": ("hyperscalers.json", ("as_of", "updated", "snapshot")),
    "/data-centers.html": ("data-centers.json", ("updated", "as_of", "snapshot")),
    "/data-centers.json": ("data-centers.json", ("updated", "as_of", "snapshot")),
    "/data-centers.xml": ("data-centers.json", ("updated", "as_of", "snapshot")),
    "/campuses.html": ("campuses.json", ("as_of", "updated", "snapshot")),
    "/campuses.json": ("campuses.json", ("as_of", "updated", "snapshot")),
}

# Masthead date, else the file's last commit date.
HTML_SOURCES = {
    "/contact.html": "contact.html",
    "/agents.html": "agents.html",
    "/physical-stack.html": "physical-stack.html",
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
    m = re.search(r"Updated <b>(\d{1,2}\s+[A-Za-z]+\s+\d{4})</b>", text)
    if m:
        return parse_nice_day(m.group(1))
    m = re.search(r"Updated (\d{4}-\d{2}-\d{2})", text)
    if m:
        return m.group(1)
    return ""


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
    if loc.startswith(SITE):
        rest = loc[len(SITE):] or "/"
        return rest if rest.startswith("/") else "/" + rest
    return loc


def content_dates(root=None):
    """Map sitemap path -> YYYY-MM-DD drawn from the artifact, not a frozen constant."""
    root = root or ROOT
    silicon = _load_json(root, "silicon.json")
    brief = _load_json(root, "brief.json")
    ranks = _load_json(root, "rank-history.json")
    home = as_of(silicon, brief, ranks)
    days = {}
    if iso_day(home):
        days["/"] = iso_day(home)

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
    if xml != text:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(xml)
    return changed


def main():
    targets = [os.path.join(ROOT, "sitemap.xml")]
    deploy = os.path.join(HERE, "deploy", "sitemap.xml")
    if os.path.isfile(deploy):
        targets.append(deploy)
    for path in targets:
        changed = refresh_sitemap(path)
        if not changed:
            print(f"sitemap lastmod already current: {path}")
            continue
        print(f"sitemap lastmod refreshed: {path}")
        for loc, old, new in changed:
            print(f"  {loc}: {old or '—'} -> {new}")


if __name__ == "__main__":
    main()
