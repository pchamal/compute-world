#!/usr/bin/env python3
"""Schema + builder guards for the capacity book. No invented numbers."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from build_capacity import (  # noqa: E402
    COUNT_STATUSES,
    METRIC_KEYS,
    campus_rollup,
    load_book,
    load_campuses,
    portfolio_totals,
    validate_book,
    build,
)


class Schema(unittest.TestCase):
    def setUp(self):
        self.book = load_book()

    def test_book_validates(self):
        self.assertTrue(validate_book(self.book))

    def test_non_null_cells_are_cited(self):
        for c in self.book["companies"]:
            for key in METRIC_KEYS:
                field = c[key]
                if field["value"] is None:
                    self.assertEqual(field["status"], "undisclosed", c["id"] + "." + key)
                    continue
                self.assertTrue(field.get("source_url"), c["id"] + "." + key)
                self.assertTrue(field.get("quote"), c["id"] + "." + key)
                self.assertTrue(field.get("as_of"), c["id"] + "." + key)
                self.assertLessEqual(len(field["quote"]), 200, c["id"] + "." + key)
                self.assertTrue(field["source_url"].startswith("https://"))

    def test_no_density_inferred_gpus(self):
        for c in self.book["companies"]:
            g = c["deployed_gpus"]
            self.assertEqual(g["status"], "undisclosed", c["id"])
            self.assertIsNone(g["value"], c["id"])

    def test_required_filers_present(self):
        ids = {c["id"] for c in self.book["companies"]}
        for slug in (
            "coreweave",
            "nebius",
            "iren",
            "applied-digital",
            "cleanspark",
            "cipher",
            "hut8",
            "core-scientific",
            "terawulf",
            "mara",
            "riot",
            "digital-realty",
            "equinix",
        ):
            self.assertIn(slug, ids)

    def test_coreweave_points_at_sec(self):
        crwv = next(c for c in self.book["companies"] if c["id"] == "coreweave")
        url = crwv["live_mw"]["source_url"]
        self.assertIn("sec.gov", url)
        self.assertEqual(crwv["live_mw"]["value"], 1500)
        self.assertEqual(crwv["live_mw"]["status"], "reported")

    def test_estimated_excluded_from_totals(self):
        totals = portfolio_totals(self.book["companies"])
        for c in self.book["companies"]:
            for key in totals:
                field = c[key]
                if field.get("status") == "estimated":
                    # 885 CLSK Texas LOI must not sit in the portfolio sum.
                    self.assertNotIn(field["status"], COUNT_STATUSES)
        self.assertGreater(totals["live_mw"]["n"], 0)
        self.assertGreater(totals["live_mw"]["mw"], 0)
        clsk = next(c for c in self.book["companies"] if c["id"] == "cleanspark")
        self.assertEqual(clsk["pipeline_mw"]["status"], "estimated")
        self.assertEqual(clsk["pipeline_mw"]["value"], 885)
        expected_pipe = sum(
            float(c["pipeline_mw"]["value"])
            for c in self.book["companies"]
            if c["pipeline_mw"].get("status") in COUNT_STATUSES
            and c["pipeline_mw"].get("value") is not None
        )
        self.assertAlmostEqual(totals["pipeline_mw"]["mw"], expected_pipe)
        self.assertNotAlmostEqual(totals["pipeline_mw"]["mw"], expected_pipe + 885)


class Builder(unittest.TestCase):
    def test_builder_writes_page_without_inventing(self):
        book = load_book()
        campuses = load_campuses()
        with tempfile.TemporaryDirectory() as tmp:
            html_path = os.path.join(tmp, "capacity.html")
            xml_path = os.path.join(tmp, "capacity.xml")
            build(book, campuses, html_path, xml_path)
            with open(html_path, encoding="utf-8") as fh:
                html = fh.read()
            with open(xml_path, encoding="utf-8") as fh:
                xml = fh.read()
        self.assertIn("Power is the", html)
        self.assertIn("Issuer-disclosed capacity", html)
        self.assertIn("Named campuses in our register", html)
        self.assertIn("sec.gov", html)
        self.assertIn("coreweave2q26earningspress.htm", html)
        self.assertNotIn("neocloudstocks.com/", html.lower())
        # Disclaimer copy may say we omit these; they must not be columns.
        self.assertNotIn(">EV/MW<", html)
        self.assertNotIn(">Revenue/MW<", html)
        self.assertNotIn(">Revenue / MW<", html)
        self.assertNotRegex(html, r"<th[^>]*>\s*EV/MW")
        self.assertIn("capacity.xml", html)
        self.assertIn("CoreWeave", xml)
        # Drawer payload must be real JSON (null, not -Infinity).
        start = html.index('id="cap-data">') + len('id="cap-data">')
        end = html.index("</script>", start)
        blob = html[start:end]
        self.assertNotIn("Infinity", blob)
        payload = json.loads(blob)
        self.assertTrue(payload["companies"])
        for c in payload["companies"]:
            if c["id"] in ("equinix", "lambda", "crusoe", "fluidstack"):
                self.assertIsNone(c.get("live_sort"))
        # Campus rollup must not invent a MW where the pin has none.
        rollup = campus_rollup(campuses)
        self.assertEqual(rollup["n_pins"], len(campuses["projects"]))
        null_ops = [
            p["operator"]
            for p in campuses["projects"]
            if p.get("mw") is None
        ]
        self.assertTrue(null_ops)
        for row in rollup["operators"]:
            if row["mw_pins"] == 0:
                self.assertEqual(row["mw_sum"], 0.0)


if __name__ == "__main__":
    unittest.main()
