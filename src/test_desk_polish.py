#!/usr/bin/env python3
"""Guards for the v1.5 polish punch list. No invented prices."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from desk_chrome import TAGLINE, NAV, cite_line, masthead
from seo import robots_txt, SEARCH_BOTS, TRAINING_BOTS, BULK_PATHS
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
    def test_last_label_priority_drops_4_sep(self):
        ticks = ["2026-08-19", "2026-09-04", "2026-09-07"]
        x0, x1 = 0, 19

        def sx(iso):
            day = {"2026-08-19": 0, "2026-09-04": 16, "2026-09-07": 19}[iso]
            return 36 + (day - x0) / (x1 - x0) * (360 - 36 - 88)

        shown = thin_x_ticks(ticks, sx, 56)
        self.assertIn("2026-08-19", shown)
        self.assertIn("2026-09-07", shown)
        self.assertNotIn("2026-09-04", shown)

    def test_keeps_spaced_ticks(self):
        ticks = ["2026-08-19", "2026-09-04", "2026-09-07"]

        def sx(iso):
            day = {"2026-08-19": 0, "2026-09-04": 16, "2026-09-07": 19}[iso]
            return 40 + day / 19 * 800

        shown = thin_x_ticks(ticks, sx, 56)
        self.assertEqual(shown, ticks)


class Chrome(unittest.TestCase):
    def test_tagline_short(self):
        self.assertEqual(TAGLINE, "Countries. Compute.")
        html = masthead("", "2026-09-07")
        self.assertIn("Countries. Compute.", html)
        self.assertNotIn("Countries. Compute. Silicon.", html)
        self.assertIn("Contact Us", html)
        self.assertIn("class=\"chrome\"", html)
        self.assertIn("mark.svg", html)

    def test_contact_is_primary(self):
        labels = [n[0] for n in NAV]
        self.assertIn("Contact Us", labels)
        hrefs = [n[1] for n in NAV]
        self.assertIn("/contact.html", hrefs)

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


class Projects(unittest.TestCase):
    def test_every_project_has_a_href(self):
        slugs = {"IND": "india", "EU": None, "MYS": "malaysia", "ARE": "united-arab-emirates"}
        for iso, name, *_ in PREC:
            href = precedent_href(iso, name, slugs if iso in slugs else {iso: iso.lower()})
            self.assertTrue(href.startswith("/"), href)
        self.assertTrue(PREC_CAMPUS)


if __name__ == "__main__":
    unittest.main()
