# compute.world redesign v1.5 reference (7 Sep 2026)

Visual + structural target for the public desk. Do not merge this branch as-is into main.

## What to match
- Light desk chrome (Schibsted Grotesk + Newsreader), soft paper `#F3F5F2`, accent `#1F4FD8`
- Masthead: Countries · Silicon prices · Trends · Projects · Method · Country profiles · Data · More
- Homepage: lede + metric rail (Ceiling / Unlockable / Live / 108+20), board with Countries|Silicon + List|Map, Movers + Latest signals rail
- Country pages at `/country/{slug}/` (certificate voice, numbers table, cite)
- Silicon chip pages at `/silicon/{slug}/` (every sourced quote, price path)
- Trends small-multiples, map Equal Earth tier shading
- Mobile board compact

## Files
- `01`–`06` PNGs: target screenshots
- `build.mjs`: intended static generator (imports missing `data.mjs` / `styles.css` / `app.js` — reconstruct from built HTML)
- `compute-world-home.html`, `sample-*.html`: built samples
- `compute-world-site.zip`: full built dist (129 pages) for pixel/IA reference

## Constraints (desk law)
- Keep weekday Wire/brief/campus pipelines and Cloudflare Pages deploy from main
- Sourced prints only; no invented tape moves
- Public vocab: CNW, GDC, Tiers (Sleeping Giant, Primed, Incumbent, Emerging Upside, Long Road)
- Open PR; do not merge until Pukar says ship it
