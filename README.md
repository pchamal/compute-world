# compute.world · The Compute Net Worth Index™

Every country has a Compute Net Worth: the value of AI compute its own energy and geography
could host. This repo is the site, the data, and the model behind it. 108 countries, priced
three ways: the CNW Ceiling, the CNW Unlockable, and Gross Domestic Compute (GDC™).

Created by **Pukar C. Hamal**. First published August 10, 2026, San Francisco, CA.

## What is in here

```
index.html      the entire site (single file: table, globe, charts, cards, gazetteer)
params.json     the $/GW value of compute. Reviewed weekly. Edit this file, the site reprices.
data.json       the full machine-readable dataset (CC BY 4.0)
og.png          the social share card
llms.txt        plain-language guide for AI agents
robots.txt, sitemap.xml
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
- **Data or copy changes:** edit the inputs in `src/` (country rows in `cnw_model.py`,
  ratings and democracy in `aux_data.py`, macro in `macro_data.py`, live capacity in
  `gdc_data.py`, page template and blurbs in `build_page.py`), then rebuild:

  ```
  cd src
  python3 cnw_model.py      # recompute the model
  python3 build_page.py     # regenerates the site into src/deploy/
  cp deploy/index.html deploy/data.json deploy/params.json deploy/llms.txt ..
  ```

  The OG image (`make_og.py`) needs Pillow: `pip install pillow`.

- The live macro layer (GDP, debt, current account, reserves) refreshes itself in the
  browser from the IMF and World Bank APIs. No rebuild needed for that, ever.

## License and credit

Index data and methodology: **CC BY 4.0** with attribution to compute.world.
Cite as: `Hamal, P. (2026). The Compute Net Worth Index. compute.world.`

"Compute Net Worth", "The Compute Net Worth Index" and "Gross Domestic Compute" (GDC)
are trademarks of Pukar C. Hamal. Corrections and better data: hello@compute.world.
