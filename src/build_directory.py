#!/usr/bin/env python3
# Shared directory builder for Inference / Neoclouds / Hyperscalers.
# Reads the matching JSON (sourced 2026-08-19) and writes {slug}.html + {slug}.xml.
# Do not invent cities, prices, or fleet counts. Plot lat/lon only when a named city exists.
import json, html, os, sys
from datetime import datetime
from fnav import css as fnav_css, markup as fnav_markup, script as fnav_script
from subscribe import css as sub_css, markup as sub_markup, script as sub_script
from seo import og_block, breadcrumb_ld, person_author, org_publisher

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# Natural Earth 1:110m land (public domain), via world-atlas@2.0.2 (ISC).
# Same source the homepage globe uses — baked into the SVG at build time so
# the directory pages never fetch unpkg. Do not substitute a photo globe.
LAND_TOPO = os.path.join(HERE, "world-110m-land.json")
_LAND_PATH_CACHE = {}

# EU chip = EU27 plus the usual European compute geography (UK, Norway, Iceland, Switzerland, Liechtenstein).
EU_ISO3 = {
    "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA", "DEU",
    "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD", "POL", "PRT",
    "ROU", "SVK", "SVN", "ESP", "SWE", "NOR", "GBR", "CHE", "ISL", "LIE",
}

INDEXES = {
    "inference": {
        "slug": "inference",
        "letter": "I",
        "nav": "inference",
        "name": "The Inference Index",
        "kicker": "Who sells the tokens",
        "h1": "Who sells the <em>tokens</em>.",
        "question": "Who sells tokens / APIs?",
        "not_here": "Bare-metal clusters — except dual-list notes already in the catalog.",
        "chip_label": "Models / silicon",
        "kind_filter": False,
        "og": "og-inference.png",
        "og_alt": "The Inference Index — sourced token and API vendors, not a cluster catalog",
        "cite": "Hamal, P. (2026). The Inference Index. compute.world.",
        "thesis": (
            "Token APIs and inference endpoints, as the operator publishes them. "
            "China and the EU stay on the list even when the city is sales-gated. "
            "This is not a bare-metal catalog, and it is not a market cap."
        ),
    },
    "neoclouds": {
        "slug": "neoclouds",
        "letter": "N",
        "nav": "neoclouds",
        "name": "The Neocloud Index",
        "kicker": "Who rents the GPUs",
        "h1": "Who rents the <em>GPUs</em>.",
        "question": "Who rents GPUs / dedicated clusters?",
        "not_here": "Token-only shops; full IaaS catalogs (those live with Hyperscalers).",
        "chip_label": "Silicon",
        "kind_filter": True,
        "og": "og-neoclouds.png",
        "og_alt": "The Neocloud Index — sourced GPU rental operators, not a market cap",
        "cite": "Hamal, P. (2026). The Neocloud Index. compute.world.",
        "thesis": (
            "GPU rental and dedicated clusters. Token-only shops live on the Inference index. "
            "Full IaaS catalogs live with the Hyperscalers. "
            "State-only rows stay state-only — Texas is not upgraded to Dallas."
        ),
    },
    "hyperscalers": {
        "slug": "hyperscalers",
        "letter": "H",
        "nav": "hyperscalers",
        "name": "The Hyperscaler Index",
        "kicker": "Who runs the general cloud",
        "h1": "Who runs the <em>general</em> cloud.",
        "question": "Who runs a general-purpose cloud that also has GPUs?",
        "not_here": "GPU-only specialists — those are Neoclouds.",
        "chip_label": "Silicon",
        "kind_filter": True,
        "og": "og-hyperscalers.png",
        "og_alt": "The Hyperscaler Index — sourced general-purpose clouds, not a market cap",
        "cite": "Hamal, P. (2026). The Hyperscaler Index. compute.world.",
        "thesis": (
            "General-purpose clouds that also rent GPUs. GPU-only specialists are Neoclouds. "
            "Scaleway and OVH are regional hyperscalers — full IaaS, not a neocloud. "
            "China and the EU stay visible even when a city is undisclosed."
        ),
    },
}


def loc_bucket(loc):
    iso = (loc.get("iso3") or "").upper()
    if iso == "USA":
        return "us"
    if iso == "CHN":
        return "china"
    if iso in EU_ISO3:
        return "eu"
    if iso:
        return "rest"
    return ""


def named_city(loc):
    city = (loc.get("city") or "").strip()
    if not city:
        return False
    return loc.get("lat") is not None and loc.get("lon") is not None


def city_label(loc):
    city = (loc.get("city") or "").strip()
    if city:
        return city
    region = (loc.get("region") or "").strip()
    if region:
        return f"{region} (state/region only)"
    return "undisclosed"


def hq_text(p):
    hq = p.get("hq") or {}
    bits = [x for x in (hq.get("city"), hq.get("country")) if x]
    return " · ".join(bits) if bits else "—"


def silicon_list(p):
    items = list(p.get("silicon") or [])
    if p.get("models"):
        for m in p["models"]:
            if m not in items:
                items.append(m)
    return items


def source_href(p):
    urls = p.get("source_urls") or []
    if urls:
        return urls[0]
    return p.get("website") or ""


def provider_meta(p):
    locs = p.get("locations") or []
    cities = []
    seen = set()
    n_named = n_state = n_und = 0
    buckets = set()
    dots = []
    for loc in locs:
        b = loc_bucket(loc)
        if b:
            buckets.add(b)
        city = (loc.get("city") or "").strip()
        if city:
            n_named += 1
            if city not in seen:
                seen.add(city)
                cities.append(city)
        elif (loc.get("region") or "").strip():
            n_state += 1
        else:
            n_und += 1
        if named_city(loc):
            dots.append({
                "lat": loc["lat"],
                "lon": loc["lon"],
                "city": city,
                "country": loc.get("country") or "",
                "iso3": loc.get("iso3") or "",
                "provider": p["name"],
                "pid": p["id"],
            })
    return {
        "n_rows": len(locs),
        "n_named": n_named,
        "n_state": n_state,
        "n_und": n_und,
        "cities": cities,
        "buckets": sorted(buckets),
        "dots": dots,
    }


def cities_cell(meta):
    if not meta["cities"]:
        if meta["n_state"] and not meta["n_und"]:
            return "state/region only"
        if meta["n_state"]:
            return f"state/region only · {meta['n_und']} undisclosed"
        return "undisclosed"
    if len(meta["cities"]) <= 3:
        text = ", ".join(meta["cities"])
    else:
        text = f"{len(meta['cities'])} named"
    extra = []
    if meta["n_state"]:
        extra.append(f"{meta['n_state']} state/region only")
    if meta["n_und"]:
        extra.append(f"{meta['n_und']} undisclosed")
    if extra and len(meta["cities"]) > 3:
        text += " · " + " · ".join(extra)
    return text


def kind_label(k):
    return (k or "").replace("-", " ")


def nice_date(d):
    if not d:
        return ""
    if len(d) == 10:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%d %b %Y")
    return d


def _lonlat_to_xy(lon, lat, width, height):
    """Equirectangular — same formula as the city pins, so land and dots share a plate."""
    return (lon + 180) / 360 * width, (90 - lat) / 180 * height


def _decode_topo_arcs(topo):
    tr = topo.get("transform") or {}
    sx, sy = tr.get("scale") or [1, 1]
    tx, ty = tr.get("translate") or [0, 0]
    decoded = []
    for arc in topo["arcs"]:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        decoded.append(pts)
    return decoded


def _stitch_arc_ring(decoded, indices):
    pts = []
    for i in indices:
        seg = decoded[~i][::-1] if i < 0 else decoded[i]
        if pts:
            seg = seg[1:]
        pts.extend(seg)
    return pts


def _split_antimeridian(ring):
    """Cut rings that jump ±180 so a fill never draws a bar across the plate."""
    if len(ring) < 2:
        return []
    lines = [[ring[0]]]
    for pt in ring[1:]:
        prev = lines[-1][-1]
        if abs(pt[0] - prev[0]) > 180:
            lat = (prev[1] + pt[1]) / 2
            if prev[0] > 0:
                lines[-1].append((180.0, lat))
                lines.append([(-180.0, lat), pt])
            else:
                lines[-1].append((-180.0, lat))
                lines.append([(180.0, lat), pt])
        else:
            lines[-1].append(pt)
    if len(lines) > 1:
        a, b = lines[0][0], lines[-1][-1]
        if abs(a[0] - b[0]) < 1e-4 and abs(a[1] - b[1]) < 1e-4:
            lines[-1].pop()
            lines[0] = lines[-1] + lines[0]
            lines.pop()
    return lines


def _svg_coord(n):
    s = f"{n:.1f}".rstrip("0").rstrip(".")
    return s or "0"


def _polyline_d(pts, width, height):
    if len(pts) >= 2 and abs(pts[0][0] - pts[-1][0]) < 1e-6 and abs(pts[0][1] - pts[-1][1]) < 1e-6:
        pts = pts[:-1]
    if len(pts) < 3:
        return ""
    cmds = []
    for i, (lon, lat) in enumerate(pts):
        x, y = _lonlat_to_xy(lon, lat, width, height)
        cmds.append(("M" if i == 0 else "L") + f"{_svg_coord(x)} {_svg_coord(y)}")
    cmds.append("Z")
    return "".join(cmds)


def _land_object(topo):
    obj = (topo.get("objects") or {}).get("land")
    if not obj:
        raise ValueError("world-110m-land.json has no land object")
    if obj.get("type") == "GeometryCollection":
        geoms = obj.get("geometries") or []
        if not geoms:
            raise ValueError("world-110m-land.json land collection is empty")
        return geoms[0]
    return obj


def _iter_rings(geom, decoded):
    t = geom.get("type")
    if t == "Polygon":
        for ring in geom["arcs"]:
            yield _stitch_arc_ring(decoded, ring)
    elif t == "MultiPolygon":
        for poly in geom["arcs"]:
            for ring in poly:
                yield _stitch_arc_ring(decoded, ring)
    elif t == "GeometryCollection":
        for child in geom.get("geometries") or []:
            yield from _iter_rings(child, decoded)
    else:
        raise ValueError(f"unsupported land geometry {t}")


def land_svg_path(width=720, height=360):
    """Bake Natural Earth 110m land into an equirectangular SVG path (viewBox units)."""
    key = (width, height)
    cached = _LAND_PATH_CACHE.get(key)
    if cached is not None:
        return cached
    if not os.path.isfile(LAND_TOPO):
        raise FileNotFoundError(f"missing self-hosted atlas {LAND_TOPO}")
    topo = json.load(open(LAND_TOPO))
    decoded = _decode_topo_arcs(topo)
    parts = []
    for ring in _iter_rings(_land_object(topo), decoded):
        for line in _split_antimeridian(ring):
            d = _polyline_d(line, width, height)
            if d:
                parts.append(d)
    path = "".join(parts)
    if path.count("M") < 20:
        raise ValueError("baked land path is too thin — continents would not read")
    _LAND_PATH_CACHE[key] = path
    return path


def map_svg(dots, width=720, height=360):
    """Equirectangular atlas: 110m land under named-city pins. No state or undisclosed pins."""
    parts = [
        f'<svg class="atlas" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Named cities only. State-only and undisclosed rows are not plotted.">',
        f'<rect class="ocean" width="{width}" height="{height}" fill="var(--tint)"/>',
        f'<path class="land" fill-rule="evenodd" d="{land_svg_path(width, height)}"/>',
    ]
    # meridians / parallels — a ruled atlas, not a GIS product
    for lon in range(-180, 181, 30):
        x = (lon + 180) / 360 * width
        parts.append(f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{height}" class="grid"/>')
    for lat in range(-60, 61, 30):
        y = (90 - lat) / 180 * height
        parts.append(f'<line x1="0" y1="{y:.1f}" x2="{width}" y2="{y:.1f}" class="grid"/>')
    parts.append(f'<line x1="0" y1="{height/2}" x2="{width}" y2="{height/2}" class="eq"/>')
    for d in dots:
        x = (d["lon"] + 180) / 360 * width
        y = (90 - d["lat"]) / 180 * height
        title = html.escape(f'{d["city"]}, {d["country"]} · {d["provider"]}', quote=True)
        parts.append(
            f'<circle class="dot" cx="{x:.2f}" cy="{y:.2f}" r="3.2" data-pid="{html.escape(d["pid"])}" '
            f'data-iso="{(d.get("iso3") or "").upper()}">'
            f'<title>{title}</title></circle>'
        )
    parts.append("</svg>")
    return "".join(parts)


def rows_html(providers):
    out = []
    for i, p in enumerate(providers):
        meta = p["_meta"]
        chips = silicon_list(p)
        chip_txt = ", ".join(chips[:4]) if chips else "—"
        if len(chips) > 4:
            chip_txt += f" · +{len(chips) - 4}"
        href = source_href(p)
        src = f'<a href="{html.escape(href)}" rel="noopener">source</a>' if href else "—"
        stripe = "odd" if i % 2 == 0 else "even"
        buckets = " ".join(meta["buckets"])
        city_txt = cities_cell(meta)
        city_title = html.escape(", ".join(meta["cities"]) if meta["cities"] else "No named city in the source.", quote=True)
        out.append(
            f'<tr class="dirrow {stripe}" id="{html.escape(p["id"])}" data-id="{html.escape(p["id"])}" '
            f'data-name="{html.escape(p["name"])}" data-kind="{html.escape(p.get("kind") or "")}" '
            f'data-hq="{html.escape(hq_text(p))}" data-rows="{meta["n_rows"]}" data-named="{meta["n_named"]}" '
            f'data-regions="{buckets}" data-silicon="{html.escape(", ".join(chips))}" '
            f'tabindex="0" role="button" aria-expanded="false">'
            f'<td class="name" data-col="name"><span class="cn">{html.escape(p["name"])}</span>'
            f'<span class="tick">{html.escape(p.get("id"))}</span></td>'
            f'<td data-col="kind">{html.escape(kind_label(p.get("kind")))}</td>'
            f'<td data-col="hq">{html.escape(hq_text(p))}</td>'
            f'<td class="num" data-col="rows">{meta["n_rows"]}</td>'
            f'<td data-col="cities" title="{city_title}">{html.escape(city_txt)}</td>'
            f'<td data-col="silicon" title="{html.escape(", ".join(chips), quote=True)}">{html.escape(chip_txt)}</td>'
            f'<td data-col="source">{src}</td>'
            f"</tr>"
        )
    return "\n".join(out)


def kind_buttons(providers):
    kinds = []
    seen = set()
    for p in providers:
        k = p.get("kind") or ""
        if k and k not in seen:
            seen.add(k)
            kinds.append(k)
    if len(kinds) <= 1:
        return ""
    btns = ['<button class="chip on" data-kind="" type="button">All kinds</button>']
    for k in kinds:
        btns.append(
            f'<button class="chip" data-kind="{html.escape(k)}" type="button">{html.escape(kind_label(k))}</button>'
        )
    return f'<div class="chips kinds" role="group" aria-label="Kind filter">{"".join(btns)}</div>'


def build(slug):
    cfg = INDEXES[slug]
    data = json.load(open(os.path.join(ROOT, f"{slug}.json")))
    providers = data["providers"]
    as_of = data.get("as_of") or ""
    all_dots = []
    n_named = n_state = n_und = 0
    for p in providers:
        meta = provider_meta(p)
        p["_meta"] = meta
        all_dots.extend(meta["dots"])
        n_named += meta["n_named"]
        n_state += meta["n_state"]
        n_und += meta["n_und"]
    n_rows = sum(p["_meta"]["n_rows"] for p in providers)
    n_china = sum(1 for p in providers if "china" in p["_meta"]["buckets"])
    n_eu = sum(1 for p in providers if "eu" in p["_meta"]["buckets"])

    title = f"{cfg['name']} · compute.world"
    desc = (
        f"{cfg['name']}: {len(providers)} sourced providers, {n_rows} location rows "
        f"(snapshot {as_of}). {cfg['question']} Named cities only when the primary page names them. "
        f"Not a market cap."
    )
    og = og_block(
        title, html.escape(desc),
        f"https://compute.world/{slug}.html", cfg["og"],
        og_type="website", image_alt=cfg["og_alt"],
    )
    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": cfg["name"],
        "description": cfg["thesis"],
        "url": f"https://compute.world/{slug}.html",
        "dateModified": as_of,
        "datePublished": as_of,
        "creator": person_author(),
        "author": person_author(),
        "publisher": org_publisher(),
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "isAccessibleForFree": True,
        "variableMeasured": "Sourced provider locations (named city, state/region, or undisclosed)",
        "distribution": {
            "@type": "DataDownload",
            "encodingFormat": "application/json",
            "contentUrl": f"https://compute.world/{slug}.json",
        },
        "citation": cfg["cite"],
    })
    crumb = json.dumps(breadcrumb_ld([
        ("compute.world", "https://compute.world/"),
        (cfg["name"], f"https://compute.world/{slug}.html"),
    ]))
    faq_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": f"What is {cfg['name']}?",
             "acceptedAnswer": {"@type": "Answer", "text": f"{cfg['thesis']} {cfg['question']} Do not put here: {cfg['not_here']}"}},
            {"@type": "Question", "name": "Do you invent cities?",
             "acceptedAnswer": {"@type": "Answer", "text": "No. A named city is plotted only when the official page names it and a Wikipedia centroid exists. State-only rows (CoreWeave Texas) stay state-only. Sales-gated lists stay undisclosed. China and the EU still appear as rows."}},
            {"@type": "Question", "name": "Is this a market cap?",
             "acceptedAnswer": {"@type": "Answer", "text": "No. compute.world does not publish market caps on a cloud logo. These directories are sourced catalogs."}},
        ],
    })

    # slim payload for the drawer (no invented fields)
    slim = []
    for p in providers:
        slim.append({
            "id": p["id"],
            "name": p["name"],
            "kind": p.get("kind"),
            "hq": p.get("hq"),
            "website": p.get("website"),
            "pricing": p.get("pricing"),
            "silicon": p.get("silicon") or [],
            "models": p.get("models") or [],
            "notes": p.get("notes") or "",
            "source_urls": p.get("source_urls") or [],
            "as_of": p.get("as_of") or as_of,
            "locations": p.get("locations") or [],
        })
    payload = json.dumps({"index": slug, "as_of": as_of, "providers": slim}, ensure_ascii=False)

    kinds_bar = kind_buttons(providers) if cfg["kind_filter"] else ""
    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#f7f4ee">
<script>(function(){{try{{var t=localStorage.getItem("cnw_theme");if(t!=="dark"&&t!=="light"){{var h=new Date().getHours();t=(h>=19||h<7)?"dark":"light";}}document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();</script>
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="https://compute.world/{slug}.html">
<meta name="robots" content="index,follow,max-image-preview:large">
{og}
<link rel="alternate" type="application/rss+xml" title="{html.escape(cfg['name'])} · compute.world" href="https://compute.world/{slug}.xml">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' fill='%23f7f4ee'/><text x='32' y='44' font-family='Georgia,serif' font-size='36' fill='%23171614' text-anchor='middle'>{cfg['letter']}</text></svg>">
<script type="application/ld+json">{ld}</script>
<script type="application/ld+json">{crumb}</script>
<script type="application/ld+json">{faq_ld}</script>
<style>
:root{{--paper:#f7f4ee;--ink:#171614;--muted:#62605a;--faint:#8d8a81;--rule:#cdc7b9;--rule2:#171614;
--accent:#7d2027;--tint:#efe9dd;--stripe:color-mix(in srgb,var(--ink) 5.5%,var(--paper));
--row-hover:color-mix(in srgb,var(--ink) 10%,var(--paper));--pr:#4b5f36;--sg:#8a5a2a;
--glass:rgba(247,244,238,.72);--glassborder:rgba(23,22,20,.35);
--serif:'Charter','Bitstream Charter','Sitka Text',Cambria,Georgia,'Times New Roman',serif}}
html[data-theme="dark"]{{--paper:#171511;--ink:#ece7db;--muted:#a49e8f;--faint:#9a9484;--rule:#3a352a;
--rule2:#ded8c8;--accent:#c2564c;--tint:#231f17;--stripe:color-mix(in srgb,var(--ink) 6%,var(--paper));
--row-hover:color-mix(in srgb,var(--ink) 11%,var(--paper));--pr:#8fae72;--sg:#c99a5e;
--glass:rgba(23,21,17,.72);--glassborder:rgba(236,231,219,.28)}}
.tchip{{position:fixed;top:14px;right:max(14px,env(safe-area-inset-right));z-index:70;width:42px;height:42px;
border-radius:50%;background:var(--glass);border:1px solid var(--glassborder);
backdrop-filter:blur(14px) saturate(1.1);-webkit-backdrop-filter:blur(14px) saturate(1.1);
color:var(--ink);cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0;
box-shadow:0 8px 26px rgba(0,0,0,.12);transition:background-color .35s ease,transform .2s ease}}
.tchip:hover{{transform:scale(1.07)}}.tchip:active{{transform:scale(.93)}}
.tchip svg{{position:absolute;width:18px;height:18px;transition:opacity .35s ease,transform .5s cubic-bezier(.22,.8,.26,1)}}
.tchip .ic-sun{{opacity:0;transform:rotate(-90deg) scale(.6)}}
.tchip .ic-moon{{opacity:1;transform:none}}
html[data-theme="dark"] .tchip .ic-sun{{opacity:1;transform:none}}
html[data-theme="dark"] .tchip .ic-moon{{opacity:0;transform:rotate(90deg) scale(.6)}}
{fnav_css()}
{sub_css()}
*{{margin:0;padding:0;box-sizing:border-box}}
html{{background:var(--paper)}}
body{{background:var(--paper);color:var(--ink);font-family:var(--serif);font-size:17px;line-height:1.62;
-webkit-font-smoothing:antialiased;font-variant-numeric:lining-nums tabular-nums;
transition:background-color .35s ease,color .35s ease}}
a{{color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(125,32,39,.35)}}
a:hover{{border-bottom-color:var(--accent)}}
.wrap{{max-width:1280px;margin:0 auto;padding:0 28px}}
.masthead{{padding:34px 0 0;text-align:center}}
.masthead .name{{font-size:15px;letter-spacing:.34em;text-transform:uppercase}}
.masthead .name a{{border:none;color:var(--ink)}}
.masthead .name b{{font-weight:600}}
.masthead .sub{{margin-top:8px;font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
.mastrule{{margin-top:20px;border-top:2px solid var(--rule2);border-bottom:1px solid var(--rule2);height:5px}}
.lede{{padding:48px 0 8px}}
h1{{font-weight:400;font-size:clamp(30px,4.6vw,44px);line-height:1.16}}
h1 em{{font-style:italic}}
.standfirst{{margin-top:18px;font-size:18px;color:var(--muted);max-width:820px}}
.standfirst b{{color:var(--ink)}}
.subrow{{display:flex;flex-wrap:wrap;gap:8px 26px;align-items:baseline;margin:26px 0 0;padding:16px 0;
border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule);font-size:13px;letter-spacing:.1em;text-transform:uppercase}}
.subrow .lab{{color:var(--faint);font-size:11px;letter-spacing:.16em}}
.chips{{display:flex;flex-wrap:wrap;gap:8px 20px;margin:18px 0 8px;font-size:13.5px}}
.chip{{cursor:pointer;color:var(--ink);border:none;border-bottom:1px solid transparent;letter-spacing:.04em;background:none;font:inherit;padding:0}}
.chip:hover{{border-bottom-color:var(--rule)}}
.chip.on{{color:var(--accent);border-bottom:1px solid var(--accent)}}
.atlaswrap{{margin:8px 0 18px;border:1px solid var(--rule);background:var(--tint)}}
.atlas{{display:block;width:100%;height:auto}}
.atlas .land{{fill:color-mix(in srgb,var(--ink) 10%,var(--tint));stroke:var(--ink);stroke-width:.4;stroke-opacity:.4}}
.atlas .grid{{stroke:var(--rule);stroke-width:.4}}
.atlas .eq{{stroke:var(--rule2);stroke-width:.7;opacity:.35}}
.atlas .dot{{fill:var(--accent);opacity:.82}}
.atlas .dot.on{{fill:var(--pr);opacity:1}}
.atlascap{{font-size:12px;color:var(--faint);letter-spacing:.04em;margin:8px 0 0}}
.tblwrap{{overflow-x:auto;margin:8px 0 0;border-top:2px solid var(--rule2)}}
table.dir{{width:100%;border-collapse:collapse;font-size:13px;min-width:860px}}
.dir th{{font-weight:400;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);text-align:left;
padding:8px 8px 7px;border-bottom:1px solid var(--rule2);white-space:nowrap;cursor:pointer;user-select:none;
position:sticky;top:0;background:var(--paper);z-index:4}}
.dir th.num,.dir td.num{{text-align:right}}
.dir th.sorted{{color:var(--ink)}}
.dir th .arr{{display:inline-block;margin-left:4px;color:var(--faint);font-size:9px}}
.dir td{{padding:9px 8px;border-bottom:1px solid color-mix(in srgb,var(--rule) 55%,transparent);vertical-align:middle}}
.dir tr.dirrow{{cursor:pointer}}
.dir tbody tr.dirrow.odd td{{background:var(--paper)}}
.dir tbody tr.dirrow.even td{{background:var(--tint)}}
.dir tbody tr.dirrow:hover td,.dir tbody tr.dirrow.open td{{background:var(--row-hover)}}
.dir .cn{{font-weight:600}}
.dir tr.dirrow:hover .cn{{color:var(--accent)}}
.dir .tick{{display:block;font-size:11px;color:var(--faint);margin-top:2px}}
.hint{{margin:10px 0 0;font-size:12px;color:var(--faint);letter-spacing:.04em}}
#scrim{{position:fixed;inset:0;background:rgba(23,22,20,.28);opacity:0;pointer-events:none;z-index:80;transition:opacity .3s ease}}
#scrim.on{{opacity:1;pointer-events:auto}}
html[data-theme="dark"] #scrim{{background:rgba(0,0,0,.45)}}
#drawer{{position:fixed;top:0;right:0;height:100%;width:min(560px,100%);background:var(--paper);color:var(--ink);
z-index:90;transform:translateX(104%);transition:transform .4s cubic-bezier(.22,.8,.26,1);
box-shadow:-18px 0 50px rgba(0,0,0,.16);overflow:auto;padding:28px 28px 48px}}
#drawer.on{{transform:none}}
#drawer h2{{font-weight:400;font-size:26px;line-height:1.2;margin:6px 0 4px}}
#drawer .dv{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
#drawer .dclose{{position:absolute;top:16px;right:18px;background:none;border:none;font:inherit;font-size:13px;
letter-spacing:.12em;text-transform:uppercase;color:var(--muted);cursor:pointer}}
#drawer .dclose:hover{{color:var(--accent)}}
#drawer .dmeta{{display:flex;flex-wrap:wrap;gap:8px 18px;margin:14px 0 18px;padding:12px 0;border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule);font-size:12.5px;color:var(--muted)}}
#drawer .dmeta b{{color:var(--ink);font-weight:600}}
#drawer h3{{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:22px 0 8px;font-weight:400}}
#drawer .qtable{{width:100%;border-collapse:collapse;font-size:13px}}
#drawer .qtable th{{text-align:left;font-weight:400;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint);padding:6px 8px 6px 0;border-bottom:1px solid var(--rule2)}}
#drawer .qtable td{{padding:8px 8px 8px 0;border-bottom:1px solid var(--rule);vertical-align:top}}
#drawer .qnote{{display:block;font-size:11.5px;color:var(--faint);margin-top:2px}}
#drawer p{{font-size:14.5px;color:var(--muted);margin-bottom:10px}}
#drawer p b{{color:var(--ink)}}
#drawer ul{{margin:0 0 8px 18px;color:var(--muted);font-size:14px}}
#drawer li{{margin-bottom:5px}}
details.meth{{margin:44px 0;border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule)}}
details.meth summary{{cursor:pointer;padding:13px 4px;font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);list-style:none}}
details.meth summary::before{{content:"+ "}}
details.meth[open] summary::before{{content:"− "}}
details.meth .mb{{padding:4px 4px 18px;font-size:14px;color:var(--muted);max-width:820px}}
details.meth .mb p{{margin-bottom:12px}}
details.meth .mb b{{color:var(--ink)}}
.faq{{margin:48px 0 0;border-top:2px solid var(--rule2);padding-top:22px}}
.faq h2{{font-weight:400;font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:0 0 16px}}
.faq h3{{font-weight:600;font-size:16px;margin:18px 0 6px}}
.faq p{{font-size:15px;color:var(--muted);max-width:820px}}
.faq p b{{color:var(--ink)}}
.colophon{{margin-top:56px;border-top:2px solid var(--rule2);padding:24px 0 56px;text-align:center}}
.colophon .c1{{font-size:12px;letter-spacing:.3em;text-transform:uppercase}}
.colophon .c2{{margin-top:10px;font-size:12.5px;color:var(--muted)}}
@media(max-width:760px){{.wrap{{padding:0 18px}}.lede{{padding:36px 0 8px}}}}
@media(prefers-reduced-motion:reduce){{#drawer,#scrim{{transition:none}}}}
</style>
</head>
<body class="fnav-inner">
<button id="themetog" class="tchip" aria-label="Switch to night mode" title="Day / Night">
  <svg class="ic-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>
  <svg class="ic-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.9 1.9M19.1 4.9l-1.8 1.8M6.7 17.3l-1.9 1.9"/></svg>
</button>
{fnav_markup(cfg["nav"])}
<div class="wrap">
  <div class="masthead">
    <div class="name"><a href="/"><b>COMPUTE</b>.WORLD</a></div>
    <div class="sub">{html.escape(cfg["name"])} · {html.escape(cfg["kicker"])} · snapshot {html.escape(as_of)}</div>
    <div class="mastrule"></div>
  </div>
  <div class="lede">
    <h1>{cfg["h1"]}</h1>
    <p class="standfirst">{html.escape(cfg["thesis"])} <b>{len(providers)} providers</b> · <b>{n_rows} location rows</b> · {n_named} named cities plotted · {n_state} state/region-only · {n_und} undisclosed. China: {n_china} operators. Europe: {n_eu} operators. Sibling of the Silicon Tape and the Compute Net Worth Index&#8482;.</p>
    <div class="subrow">
      <span class="lab">v0</span>
      <span>Snapshot {html.escape(as_of)}</span>
      <span>{len(providers)} providers</span>
      <span>{n_rows} rows</span>
      <a href="/{slug}.json">{slug}.json</a>
      <a href="/{slug}.xml">RSS</a>
      <a href="/#silicon">Silicon</a>
      <a href="/#countries">Countries</a>
    </div>
  </div>
  {sub_markup()}
  <div class="chips regions" role="group" aria-label="Region filter">
    <button class="chip on" data-region="" type="button">All</button>
    <button class="chip" data-region="us" type="button">US</button>
    <button class="chip" data-region="eu" type="button" title="EU27 plus UK, Norway, Iceland, Switzerland">EU</button>
    <button class="chip" data-region="china" type="button">China</button>
    <button class="chip" data-region="rest" type="button">Rest</button>
  </div>
  {kinds_bar}
  <div class="atlaswrap">{map_svg(all_dots)}</div>
  <p class="atlascap">Named cities only — Wikipedia centroids where the official page names a city. State-only and undisclosed rows are not plotted as fake points.</p>
  <div class="tblwrap">
    <table class="dir" id="dir">
      <thead>
        <tr>
          <th class="sorted" data-sort="name" data-type="str">Name <span class="arr">▼</span></th>
          <th data-sort="kind" data-type="str">Kind <span class="arr"></span></th>
          <th data-sort="hq" data-type="str">HQ <span class="arr"></span></th>
          <th class="num" data-sort="rows" data-type="num" title="Sourced location rows — city, state/region, or undisclosed. Not invented.">Regions <span class="arr"></span></th>
          <th data-sort="cities" data-type="str">Named cities <span class="arr"></span></th>
          <th data-sort="silicon" data-type="str">{html.escape(cfg["chip_label"])} <span class="arr"></span></th>
          <th data-sort="source" data-type="str">Source <span class="arr"></span></th>
        </tr>
      </thead>
      <tbody>
{rows_html(providers)}
      </tbody>
    </table>
  </div>
  <p class="hint">Click a row for the sourced location list. A missing city is <b>undisclosed</b>, never a guessed metro. Grain of the source: CoreWeave US rows stay state-only.</p>
  <details class="meth" open>
    <summary>How this directory is kept honest</summary>
    <div class="mb">
      <p><b>The question.</b> {html.escape(cfg["question"])} Do not put here: {html.escape(cfg["not_here"])}</p>
      <p><b>No invented cities.</b> If a provider is real but the city list is sales-gated, the record exists with undisclosed. lat/lon only when a named city exists (Wikipedia centroid). State-only rows are not upgraded to a metro.</p>
      <p><b>No market caps.</b> No fake fleet counts. Marketing GW figures appear only if they already sit in the JSON notes.</p>
      <p><b>China and the EU</b> appear even when the city is undisclosed. Classification is already in the JSON — Scaleway and OVH are regional hyperscalers; DigitalOcean / Vultr stay neoclouds because the product we care about is GPU Droplets / Cloud GPU.</p>
      <p>Machine-readable: <a href="/{slug}.json">{slug}.json</a> (CC BY 4.0, attribution to compute.world). Cite as: <code>{html.escape(cfg["cite"])}</code>. Corrections: <a href="/contact.html">get in touch</a>.</p>
    </div>
  </details>
  <section class="faq" id="faq">
    <h2>Questions this index answers in public</h2>
    <h3>What is the question?</h3>
    <p>{html.escape(cfg["question"])} <b>Do not put here:</b> {html.escape(cfg["not_here"])}</p>
    <h3>Do you invent cities?</h3>
    <p>No. A pin is a named city with a sourced lat/lon. Texas stays Texas. A sales-gated list stays <b>undisclosed</b>. China and the EU still appear as rows.</p>
    <h3>Is this a market cap?</h3>
    <p>No. compute.world does not print a CoinMarketCap number on a cloud logo. These are sourced catalogs beside the Silicon Tape and the Compute Net Worth Index&#8482;.</p>
  </section>
  <div class="colophon">
    <div class="c1">COMPUTE.WORLD</div>
    <div class="c2">{html.escape(cfg["name"])} · v0 · snapshot {html.escape(as_of)} · the world's compute &amp; silicon index · CNW™ · GDC™ · &copy; 2026 Pukar C. Hamal · San Francisco, CA</div>
  </div>
</div>
<div id="scrim" hidden></div>
<aside id="drawer" aria-hidden="true">
  <button class="dclose" type="button" id="dclose">Close</button>
  <div class="dv" id="dvendor"></div>
  <h2 id="dtitle"></h2>
  <div class="dmeta" id="dmeta"></div>
  <div id="dbody"></div>
</aside>
<script type="application/json" id="dir-data">{payload}</script>
<script>
var DIR = JSON.parse(document.getElementById("dir-data").textContent);
var BY = {{}}; DIR.providers.forEach(function(p){{ BY[p.id] = p; }});
var filt = {{region:"", kind:""}};
function restripe(){{
  var i=0;
  document.querySelectorAll("#dir tr.dirrow").forEach(function(r){{
    r.classList.remove("odd","even");
    if(r.style.display==="none") return;
    r.classList.add(i%2?"even":"odd");
    i++;
  }});
}}
function applyFilt(){{
  document.querySelectorAll("#dir tr.dirrow").forEach(function(r){{
    var okR = !filt.region || (" "+r.dataset.regions+" ").indexOf(" "+filt.region+" ")>=0;
    var okK = !filt.kind || r.dataset.kind===filt.kind;
    r.style.display = (okR && okK) ? "" : "none";
  }});
  document.querySelectorAll(".atlas .dot").forEach(function(c){{
    var row = document.getElementById(c.getAttribute("data-pid"));
    var show = row && row.style.display!=="none";
    if(filt.region==="us") show = show && c.getAttribute("data-iso")==="USA";
    if(filt.region==="china") show = show && c.getAttribute("data-iso")==="CHN";
    if(filt.region==="eu") show = show && "AUT BEL BGR HRV CYP CZE DNK EST FIN FRA DEU GRC HUN IRL ITA LVA LTU LUX MLT NLD POL PRT ROU SVK SVN ESP SWE NOR GBR CHE ISL LIE".split(" ").indexOf(c.getAttribute("data-iso"))>=0;
    if(filt.region==="rest") show = show && c.getAttribute("data-iso") && c.getAttribute("data-iso")!=="USA" && c.getAttribute("data-iso")!=="CHN" && "AUT BEL BGR HRV CYP CZE DNK EST FIN FRA DEU GRC HUN IRL ITA LVA LTU LUX MLT NLD POL PRT ROU SVK SVN ESP SWE NOR GBR CHE ISL LIE".split(" ").indexOf(c.getAttribute("data-iso"))<0;
    c.style.display = show ? "" : "none";
  }});
  restripe();
}}
document.querySelectorAll(".chips.regions .chip").forEach(function(ch){{
  ch.onclick=function(){{
    document.querySelectorAll(".chips.regions .chip").forEach(function(x){{x.classList.remove("on");}});
    ch.classList.add("on"); filt.region=ch.getAttribute("data-region")||""; applyFilt();
  }};
}});
document.querySelectorAll(".chips.kinds .chip").forEach(function(ch){{
  ch.onclick=function(){{
    document.querySelectorAll(".chips.kinds .chip").forEach(function(x){{x.classList.remove("on");}});
    ch.classList.add("on"); filt.kind=ch.getAttribute("data-kind")||""; applyFilt();
  }};
}});
function locLabel(l){{
  if(l.city) return l.city;
  if(l.region) return l.region+" (state/region only)";
  return "undisclosed";
}}
var drawer=document.getElementById("drawer"), scrim=document.getElementById("scrim");
function closeD(){{
  drawer.classList.remove("on"); scrim.classList.remove("on");
  drawer.setAttribute("aria-hidden","true"); scrim.hidden=true;
  document.querySelectorAll("tr.dirrow.open").forEach(function(r){{ r.classList.remove("open"); r.setAttribute("aria-expanded","false"); }});
  document.querySelectorAll(".atlas .dot").forEach(function(c){{ c.classList.remove("on"); }});
  if(location.hash) history.replaceState(null,"",location.pathname+location.search);
}}
function openD(id){{
  var p=BY[id]; if(!p) return;
  document.querySelectorAll("tr.dirrow").forEach(function(r){{
    var on=r.dataset.id===id; r.classList.toggle("open",on); r.setAttribute("aria-expanded",on?"true":"false");
  }});
  document.querySelectorAll(".atlas .dot").forEach(function(c){{ c.classList.toggle("on", c.getAttribute("data-pid")===id); }});
  document.getElementById("dvendor").textContent = (p.kind||"").replace(/-/g," ")+" · as of "+(p.as_of||"");
  document.getElementById("dtitle").textContent = p.name;
  var hq = p.hq ? [p.hq.city,p.hq.country].filter(Boolean).join(" · ") : "—";
  var site = p.website ? '<a href="'+p.website+'" rel="noopener">website</a>' : "";
  var price = p.pricing ? (String(p.pricing).indexOf("http")===0 ? '<a href="'+p.pricing+'" rel="noopener">pricing</a>' : p.pricing) : "";
  document.getElementById("dmeta").innerHTML =
    "<span><b>HQ</b> "+hq+"</span>"+(site?"<span>"+site+"</span>":"")+(price?"<span>"+price+"</span>":"");
  var chips=(p.silicon||[]).concat(p.models||[]);
  var locRows=(p.locations||[]).map(function(l){{
    var src=l.source_url?'<a href="'+l.source_url+'" rel="noopener">source</a>':"";
    var pin=(l.city && l.lat!=null && l.lon!=null) ? (l.lat+", "+l.lon) : "—";
    return "<tr><td>"+locLabel(l)+'<span class="qnote">'+(l.az||l.note||"")+"</span></td><td>"+(l.country||"—")+'</td><td>'+(l.status||"")+'<span class="qnote">'+pin+"</span></td><td>"+src+"</td></tr>";
  }}).join("");
  var srcs=(p.source_urls||[]).map(function(u){{ return '<li><a href="'+u+'" rel="noopener">'+u.replace(/^https?:\\/\\//,"")+"</a></li>"; }}).join("");
  document.getElementById("dbody").innerHTML =
    (p.notes?"<h3>Note</h3><p>"+p.notes+"</p>":"")+
    (chips.length?"<h3>Silicon / models</h3><p>"+chips.join(" · ")+"</p>":"")+
    "<h3>Sourced locations</h3>"+
    ((p.locations||[]).length?
      '<table class="qtable"><thead><tr><th>City / grain</th><th>Country</th><th>Status</th><th>Source</th></tr></thead><tbody>'+locRows+"</tbody></table>"
      :"<p>No location rows — the operator is listed; the city is undisclosed.</p>")+
    "<h3>Sources</h3><ul>"+srcs+"</ul>";
  scrim.hidden=false;
  requestAnimationFrame(function(){{ drawer.classList.add("on"); scrim.classList.add("on"); }});
  drawer.setAttribute("aria-hidden","false");
  if(location.hash!=="#"+id) history.replaceState(null,"","#"+id);
}}
document.querySelectorAll("tr.dirrow").forEach(function(r){{
  r.addEventListener("click", function(){{ openD(r.dataset.id); }});
  r.addEventListener("keydown", function(e){{ if(e.key==="Enter"||e.key===" "){{ e.preventDefault(); openD(r.dataset.id); }} }});
  r.querySelectorAll("a").forEach(function(a){{ a.addEventListener("click", function(e){{ e.stopPropagation(); }}); }});
}});
document.getElementById("dclose").onclick=closeD;
scrim.onclick=closeD;
document.addEventListener("keydown", function(e){{ if(e.key==="Escape") closeD(); }});
function routeRow(){{ var hid=location.hash.slice(1); if(hid && document.getElementById(hid)) openD(hid); }}
if(location.hash) routeRow();
window.addEventListener("hashchange", routeRow);
(function(){{
  var tb=document.querySelector("#dir tbody");
  var state={{key:"name", dir:1, type:"str"}};
  document.querySelectorAll("#dir th[data-sort]").forEach(function(th){{
    th.onclick=function(){{
      var key=th.getAttribute("data-sort"), type=th.getAttribute("data-type");
      if(state.key===key) state.dir*=-1; else {{ state.key=key; state.dir=1; }}
      state.type=type;
      document.querySelectorAll("#dir th").forEach(function(h){{ h.classList.remove("sorted"); var a=h.querySelector(".arr"); if(a) a.textContent=""; }});
      th.classList.add("sorted"); th.querySelector(".arr").textContent = state.dir>0?"▼":"▲";
      var rows=[].slice.call(tb.querySelectorAll("tr.dirrow"));
      rows.sort(function(a,b){{
        if(type==="num"){{
          var an=parseFloat(a.dataset[key==="rows"?"rows":key]); var bn=parseFloat(b.dataset[key==="rows"?"rows":key]);
          if(isNaN(an)) an=-Infinity; if(isNaN(bn)) bn=-Infinity;
          return (an-bn)*state.dir;
        }}
        var av=(a.dataset[key]||a.querySelector('[data-col="'+key+'"]').textContent).toLowerCase();
        var bv=(b.dataset[key]||b.querySelector('[data-col="'+key+'"]').textContent).toLowerCase();
        return av.localeCompare(bv)*state.dir;
      }});
      rows.forEach(function(r){{ tb.appendChild(r); }});
      restripe();
    }};
  }});
}})();
restripe();
var tm=document.querySelector('meta[name="theme-color"]'), tg=document.getElementById("themetog");
function cur(){{return document.documentElement.getAttribute("data-theme")==="dark"?"dark":"light"}}
function setT(t,sv){{document.documentElement.setAttribute("data-theme",t);
if(sv){{try{{localStorage.setItem("cnw_theme",t)}}catch(e){{}}}}
tm.content=t==="dark"?"#171511":"#f7f4ee";tg.setAttribute("aria-label",t==="dark"?"Switch to day mode":"Switch to night mode");}}
tg.onclick=function(){{setT(cur()==="dark"?"light":"dark",true)}};
setT(cur(),false);
{fnav_script(cfg["nav"])}
{sub_script()}
</script>
</body>
</html>'''

    open(os.path.join(ROOT, f"{slug}.html"), "w").write(page)

    items = []
    for p in providers:
        meta = p["_meta"]
        city = cities_cell(meta)
        chips = ", ".join(silicon_list(p)[:6])
        items.append(f'''
  <item>
    <title>{html.escape(p["name"])} · {html.escape(kind_label(p.get("kind")))}</title>
    <link>https://compute.world/{slug}.html#{html.escape(p["id"])}</link>
    <guid isPermaLink="false">compute.world/{slug}#{html.escape(p["id"])}</guid>
    <pubDate>{datetime.strptime(as_of, "%Y-%m-%d").strftime("%a, %d %b %Y") if len(as_of)==10 else as_of} 12:00:00 GMT</pubDate>
    <description>{html.escape(p["name"])} ({html.escape(kind_label(p.get("kind")))}). HQ {html.escape(hq_text(p))}. {meta["n_rows"]} sourced location rows. Cities: {html.escape(city)}. {html.escape(chips)}. {html.escape((p.get("notes") or "")[:280])}</description>
  </item>''')
    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>{html.escape(cfg["name"])} · compute.world</title>
  <link>https://compute.world/{slug}.html</link>
  <description>{html.escape(cfg["thesis"])} Snapshot {html.escape(as_of)}. {len(providers)} providers. Not a market cap.</description>
  <language>en</language>{"".join(items)}
</channel></rss>'''
    open(os.path.join(ROOT, f"{slug}.xml"), "w").write(rss)
    print(f"{slug}.html + {slug}.xml generated: {len(providers)} providers, {n_rows} rows, {len(all_dots)} named-city pins, snapshot {as_of}")
    return len(providers), n_rows, len(all_dots)


def main(slug=None):
    targets = [slug] if slug else list(INDEXES)
    for s in targets:
        if s not in INDEXES:
            sys.exit(f"unknown index {s}")
        build(s)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
