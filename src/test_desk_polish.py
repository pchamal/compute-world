#!/usr/bin/env python3
"""Guards for the v1.5 polish punch list. No invented prices."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from desk_chrome import TAGLINE, NAV, MORE, cite_line, footer, masthead
from seo import robots_txt, SEARCH_BOTS, TRAINING_BOTS, BULK_PATHS, PRIVATE_PATHS, LICENSE_LINE
from desk_data import PREC, PREC_CAMPUS, precedent_href


def thin_x_ticks(ticks, sx, min_px=56):
    if not ticks or len(ticks) <= 2:
        return list(ticks)
    last = ticks[-1]
    out = [ticks[0]]
    for t in ticks[1:-1]:
        x = sx(t)
        if x - sx(out[-1]) >= min_px and sx(last) - x >= min_px:
            out.append(t)
    out.append(last)
    return out


class TickThinning(unittest.TestCase):
    def test_conversion_axis_is_first_and_asof(self):
        """3-day gap (4 Sep vs 7 Sep) must not both be axis labels."""
        obs, as_of = ["2026-08-19", "2026-09-04"], "2026-09-07"
        ticks = [obs[0], as_of]
        self.assertEqual(ticks, ["2026-08-19", "2026-09-07"])
        self.assertNotIn("2026-09-04", ticks)

    def test_last_label_priority_drops_4_sep(self):
        ticks = ["2026-08-19", "2026-09-04", "2026-09-07"]
        x0, x1 = 0, 19

        def sx(iso):
            day = {"2026-08-19": 0, "2026-09-04": 16, "2026-09-07": 19}[iso]
            return 36 + (day - x0) / (x1 - x0) * (360 - 36 - 88)

        shown = thin_x_ticks(ticks, sx, 72)
        self.assertIn("2026-08-19", shown)
        self.assertIn("2026-09-07", shown)
        self.assertNotIn("2026-09-04", shown)

    def test_keeps_spaced_ticks(self):
        ticks = ["2026-08-19", "2026-09-04", "2026-09-07"]

        def sx(iso):
            day = {"2026-08-19": 0, "2026-09-04": 16, "2026-09-07": 19}[iso]
            return 40 + day / 19 * 800

        shown = thin_x_ticks(ticks, sx, 72)
        self.assertEqual(shown, ticks)


class Chrome(unittest.TestCase):
    def test_tagline_short(self):
        self.assertEqual(TAGLINE, "Countries. Compute.")
        html = masthead("", "2026-09-07")
        self.assertIn("Compute.World", html)
        self.assertNotIn("Countries. Compute. Silicon.", html)
        foot = footer()
        self.assertIn(TAGLINE, foot)
        self.assertNotIn("Countries. Compute. Silicon.", foot)
        self.assertIn("Contact Us", html)
        self.assertIn("class=\"chrome\"", html)
        self.assertIn("mark.svg", html)

    def test_contact_is_primary(self):
        labels = [n[0] for n in NAV]
        self.assertIn("Contact Us", labels)
        hrefs = [n[1] for n in NAV]
        self.assertIn("/contact", hrefs)

    def test_physical_stack_in_more(self):
        hrefs = [row[0] for row in MORE]
        labels = [row[1] for row in MORE]
        self.assertIn("https://compute.world/physical-stack", hrefs)
        self.assertIn("Physical stack", labels)
        html = masthead("", "2026-09-14")
        self.assertIn("https://compute.world/physical-stack", html)
        self.assertNotIn("physical-stack.html", html)
        self.assertNotIn(".html", html)
        self.assertIn("Physical stack", html)

    def test_citation_has_url_and_asof(self):
        line = cite_line("The Compute Net Worth Index", "https://compute.world/", "2026-09-07")
        self.assertIn("https://compute.world/", line)
        self.assertIn("compute.world · Compute Net Worth Index", line)
        self.assertIn("7 Sep 2026", line)


class Robots(unittest.TestCase):
    def test_search_open_training_no_bulk(self):
        txt = robots_txt()
        self.assertIn("User-agent: Googlebot\nAllow: /", txt)
        self.assertIn("User-agent: Bingbot\nAllow: /", txt)
        self.assertIn("The site is indexed", txt)
        self.assertNotIn("User-agent: *\nDisallow: /", txt)
        self.assertIn("User-agent: GPTBot", txt)
        for path in BULK_PATHS:
            self.assertIn(f"Disallow: {path}", txt)
        for bot in SEARCH_BOTS:
            self.assertIn(f"User-agent: {bot}", txt)
        for bot in TRAINING_BOTS:
            self.assertIn(f"User-agent: {bot}", txt)
        self.assertNotIn("Crawl-delay", txt)
        for path in PRIVATE_PATHS:
            self.assertIn(f"Disallow: {path}", txt)
        # Search-bot groups are more specific than User-agent: *, so the
        # private paths have to be repeated there or Googlebot would ignore them.
        google = txt.split("User-agent: Googlebot", 1)[1].split("User-agent:", 1)[0]
        for path in PRIVATE_PATHS:
            self.assertIn(f"Disallow: {path}", google)


class ContactDeskDate(unittest.TestCase):
    def test_contact_tracks_desk_publish_date(self):
        import subprocess
        subprocess.check_call([sys.executable, os.path.join(HERE, "build_contact.py")])
        from fnav import desk_asof
        from desk_chrome import fmt_date
        from desk_data import load_json

        dated = fmt_date(desk_asof())
        brief_dated = fmt_date(str(load_json("brief.json")["updated"])[:10])
        with open(os.path.join(ROOT, "contact.html"), encoding="utf-8") as fh:
            html = fh.read()
        self.assertEqual(html.count(f"Updated <b>{dated}</b>"), 2)
        self.assertIn(f"As of {dated}.", html)
        self.assertEqual(html.count(f"As of {dated}."), 2)
        line = f'<p>Latest desk read: <a href="/brief">Compute brief, {brief_dated}</a>.</p>'
        self.assertIn(line, html)
        start = html.index("Latest desk read:")
        sentence = html[start:html.index("</p>", start)]
        self.assertNotIn("\u2014", sentence)
        self.assertNotIn("\u2122", sentence)
        self.assertNotIn("7 Sep 2026", html)
        self.assertIn("CC BY 4.0", html)
        self.assertIn('data-sitekey="1x00000000000000000000AA"', html)
        self.assertIn("cGNoYW1hbEBhbHVtbmkuc3RhbmZvcmQuZWR1", html)

    def test_weekday_publish_rebuilds_contact(self):
        for name in ("brief.yml", "silicon.yml", "wire.yml"):
            with open(os.path.join(ROOT, ".github", "workflows", name), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("contact.html", text)
            self.assertIn('git pull --rebase origin "${GITHUB_REF_NAME}"', text)
            self.assertIn("git stash pop", text)
        with open(os.path.join(HERE, "build_brief.py"), encoding="utf-8") as fh:
            self.assertIn("build_contact.py", fh.read())
        with open(os.path.join(HERE, "build_desk.py"), encoding="utf-8") as fh:
            self.assertIn("build_contact.py", fh.read())


class SitemapLastmod(unittest.TestCase):
    def test_desk_lastmod_follows_artifacts(self):
        import json
        from build_sitemap import (
            BUILT_HTML, built_html_day, content_dates, html_updated_day, stamp_lastmod,
        )
        from seo import DEFAULT_SITEMAP, SITE

        days = content_dates(ROOT)

        def load(name):
            with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
                return json.load(fh)

        from seo import sitemap_xml

        silicon = load("silicon.json")
        brief = load("brief.json")
        wire = load("wire.json")
        self.assertEqual(days["/silicon"], silicon["updated"][:10])
        self.assertEqual(days["/brief"], brief["updated"][:10])
        self.assertEqual(days["/wire"], wire["updated"][:10])
        self.assertNotIn("/silicon.json", days)
        self.assertNotIn("/silicon.xml", days)
        with open(os.path.join(ROOT, "contact.html"), encoding="utf-8") as fh:
            contact = fh.read()
        self.assertEqual(days["/contact"], html_updated_day(contact))
        self.assertRegex(days["/contact"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertNotEqual(days["/silicon"], "2026-08-18")
        # Catalog as_of / dateModified stay on the source vintage. lastmod
        # follows the built HTML once that file moved past the snapshot.
        snapshots = {
            "/inference": load("inference.json")["as_of"][:10],
            "/neoclouds": load("neoclouds.json")["as_of"][:10],
            "/hyperscalers": load("hyperscalers.json")["as_of"][:10],
            "/campuses": load("campuses.json")["as_of"][:10],
            "/data-centers": load("data-centers.json")["updated"][:10],
            "/physical-stack": "2026-09-14",
        }
        for path, rel in BUILT_HTML.items():
            built = built_html_day(ROOT, rel)
            self.assertEqual(days[path], built, path)
            self.assertRegex(built, r"^\d{4}-\d{2}-\d{2}$")
            if built > snapshots[path]:
                self.assertNotEqual(days[path], snapshots[path], path)
        for name in ("brief.yml", "silicon.yml", "wire.yml", "rank-history.yml"):
            with open(os.path.join(ROOT, ".github", "workflows", name), encoding="utf-8") as fh:
                workflow = fh.read()
            self.assertIn("build_sitemap.py", workflow)
            self.assertIn("fetch-depth: 0", workflow)

        stamped = {u["loc"]: u.get("lastmod") for u in stamp_lastmod(DEFAULT_SITEMAP, ROOT)}
        self.assertEqual(stamped[f"{SITE}/silicon"], days["/silicon"])
        self.assertEqual(stamped[f"{SITE}/brief"], days["/brief"])
        self.assertEqual(stamped[f"{SITE}/contact"], days["/contact"])
        self.assertEqual(stamped[f"{SITE}/inference"], days["/inference"])
        self.assertEqual(stamped[f"{SITE}/physical-stack"], days["/physical-stack"])
        locs = [u["loc"] for u in DEFAULT_SITEMAP]
        for loc in locs:
            self.assertFalse(loc.endswith((".html", ".json", ".xml", ".txt")), loc)
            self.assertNotIn("/embed", loc)
        xml = sitemap_xml(
            DEFAULT_SITEMAP
            + [
                {"loc": f"{SITE}/silicon.json"},
                {"loc": f"{SITE}/silicon.html", "lastmod": "2026-11-11"},
                {"loc": f"{SITE}/embed"},
                {"loc": f"{SITE}/llms.txt"},
                {"loc": f"{SITE}/country/nepal/", "lastmod": "2026-10-02", "changefreq": "weekly"},
                {"loc": f"{SITE}/silicon/h100-sxm-80gb/", "lastmod": "2026-11-11"},
            ]
        )
        self.assertIn(f"<loc>{SITE}/silicon</loc>", xml)
        self.assertIn(f"<loc>{SITE}/country/nepal/</loc>", xml)
        self.assertIn(f"<loc>{SITE}/silicon/h100-sxm-80gb/</loc>", xml)
        self.assertEqual(xml.count(f"<loc>{SITE}/silicon</loc>"), 1)
        self.assertNotIn(".json", xml)
        self.assertNotIn(".html", xml)
        self.assertNotIn(".xml<", xml)
        self.assertNotIn("llms.txt", xml)
        self.assertNotIn("/embed", xml)
        kept = stamp_lastmod(
            [{"loc": f"{SITE}/country/nepal/", "lastmod": "2026-10-02", "changefreq": "weekly"}],
            ROOT,
        )
        self.assertEqual(kept[0]["lastmod"], days["/country/nepal/"])
        self.assertRegex(kept[0]["lastmod"], r"^\d{4}-\d{2}-\d{2}$")
        country_days = [d for p, d in days.items() if p.startswith("/country/")]
        chip_days = [d for p, d in days.items() if p.startswith("/silicon/")]
        self.assertEqual(len(country_days), 108)
        self.assertGreater(len(set(country_days)), 1)
        self.assertGreaterEqual(len(chip_days), 20)
        self.assertGreater(len(set(chip_days)), 1)
        # A placeholder date must not survive once the country's own change date is known.
        self.assertNotEqual(kept[0]["lastmod"], "2026-10-02")

    def test_built_html_day_uses_masthead_without_history(self):
        import tempfile
        from build_sitemap import built_html_day

        with tempfile.TemporaryDirectory() as tmp:
            # Name is not a tracked page, so a parent repo's git log cannot supply this day.
            with open(os.path.join(tmp, "sitemap-lastmod-probe.html"), "w", encoding="utf-8") as fh:
                fh.write(
                    'dateModified": "2026-08-19"\n'
                    '<div class="asof">Updated <b>3 Mar 2024</b></div>\n'
                )
            self.assertEqual(built_html_day(tmp, "sitemap-lastmod-probe.html"), "2024-03-03")

    def test_committed_sitemap_matches_built_html(self):
        from build_sitemap import BUILT_HTML, built_html_day, parse_sitemap
        from seo import public_path

        with open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8") as fh:
            urls = {public_path(u["loc"]): u for u in parse_sitemap(fh.read())}
        for path, rel in BUILT_HTML.items():
            self.assertEqual(urls[path]["lastmod"], built_html_day(ROOT, rel), path)
            self.assertIn("changefreq", urls[path])


class NotFound(unittest.TestCase):
    def test_unknown_paths_are_a_real_404(self):
        with open(os.path.join(ROOT, "404.html"), encoding="utf-8") as fh:
            html = fh.read()
        self.assertIn('name="robots" content="noindex"', html)
        self.assertNotIn('rel="canonical"', html)
        self.assertIn('href="/"', html)
        with open(os.path.join(ROOT, "embed.html"), encoding="utf-8") as fh:
            embed = fh.read()
        self.assertIn('name="robots" content="noindex"', embed)
        with open(os.path.join(ROOT, "_redirects"), encoding="utf-8") as fh:
            redirects = fh.read()
        self.assertNotIn("/campuses /campuses.html", redirects)
        self.assertIn("404.html", redirects)


class Projects(unittest.TestCase):
    def test_every_project_has_a_href(self):
        slugs = {"IND": "india", "EU": None, "MYS": "malaysia", "ARE": "united-arab-emirates"}
        for iso, name, *_ in PREC:
            href = precedent_href(iso, name, slugs if iso in slugs else {iso: iso.lower()})
            self.assertTrue(href.startswith("/"), href)
        self.assertTrue(PREC_CAMPUS)


class PhysicalStack(unittest.TestCase):
    def test_page_credits_mts(self):
        path = os.path.join(ROOT, "physical-stack.html")
        self.assertTrue(os.path.isfile(path), "run src/build_physical_stack.py")
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        self.assertIn("MTS Intelligence (2026). The Physical Stack Behind AI", html)
        self.assertIn("https://intelligence.mts.now/compute", html)
        self.assertIn("https://intelligence.mts.now/api/compute", html)
        self.assertIn("snapshot 2026-08-25", html)
        self.assertIn("Epoch AI", html)
        self.assertIn("MLCommons", html)
        self.assertIn("Grid + power", html)
        self.assertIn("Economics", html)
        self.assertIn("land", html)
        self.assertIn("cooling", html)
        self.assertNotIn("Colossus 2", html)


if __name__ == "__main__":
    unittest.main()
