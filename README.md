# compute.world · The World's Compute & Silicon Index

Every country has a Compute Net Worth: the value of AI compute its own energy and geography
could host. This repo is the site, the data, and the model behind it — CNW™ (108 countries)
and the Silicon Tape (sourced accelerator prints). Gross Domestic Compute (GDC™) is the
tapped counterpart to CNW.

Created by **Pukar C. Hamal**. First published August 10, 2026, San Francisco, CA.

## What is in here

```
index.html      the Compute Net Worth Index (geo certificate, movers, table)
nepal/          country pages at /{slug} (108); plain text at /nepal.txt
og/nepal.png    per-country Open Graph image (1200×630)
thesis.html     the essay (sections I–VII)
license.html    attribution-free uses, commercial license, trademark notice
data.html       machine-readable feeds
silicon.html    The Silicon Tape — standalone shareable rental index (from silicon.json)
silicon.json    Silicon Tape source of truth (CC BY 4.0)
silicon-history.json  append-only dated observed prints (no interpolations; each scrape adds a point)
rank-history.json     append-only dated observed rank snapshots (silicon + countries; no interpolation)
brief.json      daily briefing source of truth (country signals + sourced silicon prints)
brief.html      public brief page (from brief.json)
params.json     the $/GW value of compute. Reviewed weekly. Edit this file, the site reprices.
data.json       the full machine-readable dataset (CC BY 4.0)
og.png          homepage unfurl card (the world's compute & silicon index)
og-silicon.png  Silicon Tape unfurl card
og-brief.png    daily-tape unfurl card
llms.txt        plain-language guide for AI agents
robots.txt, sitemap.xml
functions/      Cloudflare Pages Functions (POST /api/subscribe)
src/            the model and build scripts (Python)
```

## Deploying with Cloudflare Pages

1. Cloudflare dashboard → Workers & Pages → Create → Pages → **Connect to Git** → pick this repo.
2. Build command: **none**. Build output directory: **/** (root). Save and deploy.
3. Custom domains → add **compute.world** (and www.compute.world). Done.

Every push to `main` redeploys automatically. The weekly value-of-compute review then becomes:
edit `params.json`, commit, done.

## Making changes

- **Weekly $/GW update:** edit `params.json` (lo, hi, central, reviewed date, basis). Nothing
  else needs to change; the page reads it at load.
- **Silicon Tape prices:** edit `silicon.json`, append a dated point to
  `silicon-history.json` (append-only on each scrape — never interpolate a candle),
  then `python3 src/build_silicon.py`. Do not invent chips, averages, or 1d/7d candles.
  1M / 1Q / 1Y / 3Y light up only from two dated same-venue same-term prints.
  Term-book 1m / 1q / 1y / 3y are sourced labeled $/GPU-hr — never an imputed discount.
- **Rank history:** `python3 src/snapshot_ranks.py` upserts today's observed
  silicon and country ranks into `rank-history.json`. One snapshot per index per
  calendar date; a second run the same day replaces that date in place. Never
  interpolate a rank. Never invent a 7-day rank candle. Inference / Neoclouds /
  Hyperscalers join once they have a published rank formula.
- **Daily brief:** edit `brief.json`, then `python3 src/build_brief.py`. Same motion as
  Wire / Silicon. Seed display prints from `silicon.json`. Leave `prev_usd` and `delta`
  null unless a second dated sourced print already exists in the repo. Do not invent a
  7-day change.
- **Data centers FAQ:** edit `data-centers.json`, then `python3 src/build_datacenters.py`.
  Do not invent acres/MW, household-bill dollars, job multipliers, or ranks. Label
  derived arithmetic as derived.
- **Campuses globe:** edit `campuses.json`, then `python3 src/build_campuses.py`.
  Do not invent cities, MW, ranks, or statuses. Every pin is the JSON. Grain stays
  on the pin. Empty regions and empty small-MW filters are coverage holes, not bugs.
- **Homepage and country pages (Phase 1):** `python3 src/build_all.py` writes
  `index.html`, `thesis.html`, `license.html`, `data.html`, `{slug}/index.html`,
  `{slug}.txt`, `og/{slug}.png`, `llms.txt`, and `sitemap.xml` into the repo
  root. Needs Pillow and CairoSVG (`pip install pillow cairosvg`). Flag SVGs
  cache in `src/flags/`.
  Cloudflare Pages has no build command; a GitHub Action (`.github/workflows/index.yml`)
  commits the generated files the same way `silicon.yml` rebuilds the tape.

- **Data or copy changes:** edit the inputs in `src/` (country rows in `cnw_model.py`,
  ratings and democracy in `aux_data.py`, macro in `macro_data.py`, live capacity in
  `gdc_data.py`, page template and blurbs in `build_page.py`), then rebuild:

  ```
  cd src
  python3 cnw_model.py      # recompute the model
  python3 build_all.py      # homepage, 108 country pages, OG images, thesis, license
  python3 build_page.py     # regenerates data.json / agents / embed into src/deploy/
  python3 build_silicon.py  # regenerates silicon.html + silicon.xml from silicon.json
  python3 build_brief.py    # regenerates brief.html + brief.xml from brief.json
  python3 make_og.py        # regenerates og.png, og-silicon.png, og-brief.png
  cp deploy/data.json deploy/params.json deploy/agents.html deploy/embed.html ..
  ```

- **Subscribe list (email):** the form posts to `/api/subscribe` (`functions/api/subscribe.js`).
  Signups persist to a free Cloudflare D1 database (`DB` → `compute-world-subscribers`),
  with KV (`SUBSCRIBERS`) as fallback. No paid tool. The public brief and RSS remain
  the delivery — do not promise email. The roster is not on a public URL. No secrets
  belong in this repo.

  The OG image (`make_og.py`) needs Pillow: `pip install pillow`.

- The live macro layer (GDP, debt, current account, reserves) refreshes itself in the
  browser from the IMF and World Bank APIs. No rebuild needed for that, ever.

## License and credit

Index data and methodology: **CC BY 4.0** with attribution to compute.world.
Cite as: `Hamal, P. (2026). The Compute Net Worth Index. compute.world.`

"Compute Net Worth", "The Compute Net Worth Index" and "Gross Domestic Compute" (GDC)
are trademarks of Pukar C. Hamal. Corrections and better data: hello@compute.world.
