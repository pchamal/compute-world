# compute.world · The Compute Net Worth Index™

Every country has a Compute Net Worth: the value of AI compute its own energy and geography
could host. This repo is the site, the data, and the model behind it. 108 countries, priced
three ways: the CNW Ceiling, the CNW Unlockable, and Gross Domestic Compute (GDC™).

Created by **Pukar C. Hamal**. First published August 10, 2026, San Francisco, CA.

## What is in here

```
index.html      the site: Countries tab (board, index, essay) and Silicon tab (the tape)
silicon.html    The Silicon Tape — standalone shareable rental index (from silicon.json)
silicon.json    Silicon Tape source of truth (CC BY 4.0)
brief.json      daily briefing source of truth (country signals + sourced silicon prints)
brief.html      public brief page (from brief.json)
params.json     the $/GW value of compute. Reviewed weekly. Edit this file, the site reprices.
data.json       the full machine-readable dataset (CC BY 4.0)
og.png          the social share card
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
- **Silicon Tape prices:** edit `silicon.json`, then `python3 src/build_silicon.py`. Do not
  invent chips, averages, or 7d/30d changes.
- **Daily brief:** edit `brief.json`, then `python3 src/build_brief.py`. Same motion as
  Wire / Silicon. Seed display prints from `silicon.json`. Leave `prev_usd` and `delta`
  null unless a second dated sourced print already exists in the repo. Do not invent a
  7-day change.
- **Data or copy changes:** edit the inputs in `src/` (country rows in `cnw_model.py`,
  ratings and democracy in `aux_data.py`, macro in `macro_data.py`, live capacity in
  `gdc_data.py`, page template and blurbs in `build_page.py`), then rebuild:

  ```
  cd src
  python3 cnw_model.py      # recompute the model
  python3 build_page.py     # regenerates the site into src/deploy/
  python3 build_silicon.py  # regenerates silicon.html + silicon.xml from silicon.json
  python3 build_brief.py    # regenerates brief.html + brief.xml from brief.json
  cp deploy/index.html deploy/data.json deploy/params.json deploy/llms.txt deploy/sitemap.xml deploy/agents.html ..
  ```

- **Subscribe list (email):** the form posts to `/api/subscribe` (`functions/api/subscribe.js`).
  In Cloudflare Pages → Settings, either set env `SUBSCRIBE_WEBHOOK` to a HubSpot /
  Buttondown / Zapier URL, or bind a KV namespace as `SUBSCRIBERS`. Until one of those
  is connected the endpoint still returns 200 with `stored: "pending"` — the public brief
  and RSS are live; do not promise email. No secrets belong in this repo.

  The OG image (`make_og.py`) needs Pillow: `pip install pillow`.

- The live macro layer (GDP, debt, current account, reserves) refreshes itself in the
  browser from the IMF and World Bank APIs. No rebuild needed for that, ever.

## License and credit

Index data and methodology: **CC BY 4.0** with attribution to compute.world.
Cite as: `Hamal, P. (2026). The Compute Net Worth Index. compute.world.`

"Compute Net Worth", "The Compute Net Worth Index" and "Gross Domestic Compute" (GDC)
are trademarks of Pukar C. Hamal. Corrections and better data: hello@compute.world.
