#!/usr/bin/env python3
"""Assemble the v1.5 desk DATA payload from live repo JSON.

Numbers come from cnw_computed.json, silicon.json, silicon-history.json,
rank-history.json and wire.json. Editorial chrome (tier copy, readiness
weights, venue domains) is structural, not a frozen snapshot of prices.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime as _dt
from urllib.parse import quote

from gdc_data import GDC_GW

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = "https://compute.world"
# Same scoring epoch as build_page.py so weekday Wire rebuilds stay consistent
# with the published rank-history tape.
SCORE_TODAY = _dt(2026, 8, 11)
FIRST_SNAPSHOT = "2026-08-19"

TIER_CODE = {
    "Sleeping Giant": "SG",
    "Primed": "PR",
    "Incumbent": "IN",
    "Emerging Upside": "EU",
    "Long Road": "LR",
}
TIER = {
    "SG": "Sleeping Giant",
    "PR": "Primed",
    "IN": "Incumbent",
    "EU": "Emerging Upside",
    "LR": "Long Road",
}
TIER_DEF = {
    "SG": "Ceiling at least 10× GDP, readiness under 65%. The endowment is real and the to-do list is long.",
    "PR": "Readiness 65% or better with a ceiling at least 3× GDP. Ready, with real headroom left to build.",
    "IN": "Ready and already priced in. Building now.",
    "EU": "In between: a narrower gap, and a real one.",
    "LR": "The ceiling is modest next to the economy. The option still costs nothing to hold.",
}
TIER_PLAIN = {
    "SG": "a sleeping giant",
    "PR": "primed",
    "IN": "an incumbent",
    "EU": "emerging upside",
    "LR": "on a long road",
}
READINESS = [
    {"k": "Governance", "w": 18, "c": "#1F4FD8", "d": "Transparency International CPI 2025"},
    {"k": "GPU access", "w": 14, "c": "#3A66DE", "d": "Under the August 2026 US export regime"},
    {"k": "Physical", "w": 14, "c": "#5B7FE3", "d": "Cooling × seismic × water"},
    {"k": "Stability", "w": 13, "c": "#7D98E8", "d": "Political stability"},
    {"k": "Grid", "w": 11, "c": "#98ADE9", "d": "Grid quality"},
    {"k": "Fiber", "w": 11, "c": "#AFBFE9", "d": "Fiber and subsea connectivity"},
    {"k": "Capital access", "w": 11, "c": "#C2CEE9", "d": "Sovereign rating plus IMF financial development"},
    {"k": "Momentum", "w": 8, "c": "#D6DDEC", "d": "Live AI and data-center engagement; a US cloud region floors it"},
]
STABV = {"H": 1.0, "M": 0.65, "L": 0.35, "C": 0.10}
TRIV = {"S": 1.0, "M": 0.6, "W": 0.25}
FIBV = {"S": 1.0, "M": 0.6, "W": 0.3}
STATUS_PTS = {"Live": 1.0, "Building": 0.7, "Contracted": 0.5, "Announced": 0.25, "Stalled": 0.1}

# Named campus pins that match a row on the sovereign-factory register.
PREC_CAMPUS = {
    "Johor hub; YTL AI Cloud, Kulai (NVIDIA GB200)": "/campuses.html#ytl-green-data-center-park-kulai",
    "Scala AI City, Eldorado do Sul": "/campuses.html#scala-ai-city-eldorado",
    "Stargate UAE, Abu Dhabi (G42, OpenAI, Oracle)": "/campuses.html#stargate-uae-abu-dhabi",
}

# Sovereign AI factories already on the public register (same catalog as build_page.py).
PREC = [
    ("ARM", "Firebird AI factory, Hrazdan (NVIDIA, Dell)", "300 MW and 70k GPUs by 2027", "Live", "Aug 2026"),
    ("MYS", "Johor hub; YTL AI Cloud, Kulai (NVIDIA GB200)", "1,110 MW live in Johor", "Live", "2025-26"),
    ("KOR", "National GPU program (NVIDIA, Samsung, SK, Naver); AIDC Alliance", "260k+ GPUs; 18.4 GW by 2035 target", "Live", "Oct 2025"),
    ("IND", "IndiaAI Mission GPU commons", "17k+ GPUs installed; 100k+ target", "Live", "2025-26"),
    ("BRA", "Scala AI City, Eldorado do Sul", "54 MW live; 4.75 GW / $50B planned", "Live", "2026"),
    ("QAT", "Ooredoo Syntys sovereign AI cloud", "NVIDIA clusters, national scale", "Live", "Jul 2025"),
    ("CHL", "National Data Centers Plan", "325 MW to 1.2 GW by 2030", "Live", "2024-26"),
    ("ETH", "GERD surplus sold to bitcoin miners", "Compute conversion, crudest form", "Live", "2025-26"),
    ("JPN", "SoftBank Sakai, ex-Sharp plant (Stargate Japan anchor)", "150 to 250 MW, ~100k GPUs", "Building", "2026"),
    ("IND", "Reliance Jamnagar AI campus (Meta JV 168 MW)", "$110B plan; 120+ MW live H2 2026", "Building", "2026"),
    ("BRA", "ByteDance Pecém campus (wind PPA)", "300 MW first phase, ~$39B", "Building", "Jan 2026"),
    ("MEX", "CloudHQ Querétaro", "Up to 900 MW, $4.8B", "Building", "2026"),
    ("SAU", "HUMAIN AI factories (NVIDIA, AMD, AWS)", "6.6 GW by 2034 target", "Building", "2025-26"),
    ("ARE", "Stargate UAE, Abu Dhabi (G42, OpenAI, Oracle)", "First 200 MW of 1 GW / 5 GW campus", "Building", "2026"),
    ("UZB", "DataVolt Tashkent (DFI-financed, NVIDIA)", "12 MW, $150M", "Building", "2026"),
    ("KAZ", "Ekibastuz Data Center Valley (NVIDIA, Firebird)", "$10B; 300 MW to 1 GW, 100k GPUs", "Contracted", "Jun 2026"),
    ("IDN", "Zankore 1 GW platform (Indosat, Ooredoo, NVIDIA, Nokia)", "First 200 MW H1 2027", "Contracted", "Aug 2026"),
    ("VNM", "G42 + FPT sovereign AI framework", "$1B+, HCMC hyperscale", "Contracted", "Feb 2026"),
    ("NOR", "Stargate Norway, Narvik (Nscale, Aker; Microsoft 30k Rubin)", "230 MW+, hydro-powered", "Contracted", "2025-26"),
    ("IND", "OpenAI for India (Tata)", "100 MW scaling to 1 GW", "Announced", "Feb 2026"),
    ("MAR", "Nexus AI factory, Casablanca (NVIDIA, Naver)", "$1.2B, sovereign platform", "Announced", "2026"),
    ("EU", "AI Gigafactories tender (EuroHPC)", "Up to 7 sites, €10B public", "Announced", "Jul 2026"),
    ("PAK", "2 GW surplus power allocated to mining and AI", "Policy allocation", "Announced", "2025"),
    ("GBR", "Stargate UK (OpenAI, NVIDIA, Nscale)", "31k GPUs planned; paused on energy costs", "Stalled", "Apr 2026"),
    ("ARG", "Stargate Argentina, Patagonia (Sur Energy)", "$25B / 500 MW; no visible progress", "Stalled", "2025-26"),
    ("KEN", "Microsoft and G42 campus", "Stalled for lack of power", "Stalled", "May 2026"),
]

DOMAINS = {
    "Lambda": "lambda.ai", "CoreWeave": "coreweave.com", "CoreWeave NA": "coreweave.com",
    "CoreWeave EU": "coreweave.com", "Crusoe": "crusoe.ai", "AWS": "aws.amazon.com",
    "GCP": "cloud.google.com", "GCP TPU": "cloud.google.com", "GCP / Azure": "cloud.google.com",
    "Oracle": "oracle.com", "DigitalOcean": "digitalocean.com", "SemiAnalysis": "semianalysis.com",
    "SMM Beijing": "metal.com", "Cerebras": "cerebras.ai", "Groq": "groq.com",
    "Vast": "vast.ai", "TensorWave": "tensorwave.com", "NVIDIA": "nvidia.com",
    "AMD": "amd.com", "Google": "cloud.google.com", "Huawei": "huawei.com", "Amazon": "aws.amazon.com",
}

PATH_SPEC = {
    "H100 SXM": [
        ("nvidia-h100-sxm-80gb", "SemiAnalysis", "composite", True, "SemiAnalysis composite, public prints end Apr 2026"),
        ("nvidia-h100-sxm-80gb", "Lambda", "on-demand", False, "Lambda on-demand, 8× SXM"),
        ("nvidia-h100-sxm-80gb", "DigitalOcean", "on-demand", False, "DigitalOcean on-demand"),
    ],
    "B200 SXM6": [
        ("nvidia-b200-sxm6", "Lambda", "on-demand", False, "Lambda on-demand, 8× SXM6"),
        ("nvidia-b200-sxm6", "CoreWeave", "on-demand", False, "CoreWeave on-demand"),
    ],
    "A100 80GB": [
        ("nvidia-a100-sxm-80gb", "Lambda", "on-demand", False, "Lambda on-demand, 8× SXM"),
        ("nvidia-a100-sxm-80gb", "CoreWeave", "on-demand", False, "CoreWeave on-demand"),
    ],
}

WIKI_SLUG = {
    "United States": "United_States",
    "United Kingdom": "United_Kingdom",
    "United Arab Emirates": "United_Arab_Emirates",
    "South Korea": "South_Korea",
    "Czechia": "Czechia",
    "Congo": "Democratic_Republic_of_the_Congo",
    "Côte d'Ivoire": "Ivory_Coast",
}


def load_json(name, default=None):
    for p in (os.path.join(ROOT, name), os.path.join(HERE, name), name):
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    if default is not None:
        return default
    raise FileNotFoundError(name)


def slugify(n):
    return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")


def chip_slug(chip_id, vendor):
    raw = chip_id or ""
    for prefix in (
        (vendor or "").lower().replace(" ", "-") + "-",
        "nvidia-", "amd-", "google-", "huawei-", "cerebras-", "amazon-", "groq-",
    ):
        if prefix and raw.startswith(prefix):
            return raw[len(prefix):]
    return raw


def iso_day(s):
    s = str(s or "")
    return s[:10] if len(s) >= 10 else s


def weakest(c):
    comps = [
        ("governance", c["cpi"] / 100),
        ("stability", STABV[c["stability"]]),
        ("chip access", c["gpu_access"]),
        ("the grid", TRIV[c["grid"]]),
        ("fiber", FIBV[c["fiber"]]),
        ("momentum", c["momentum"]),
        ("physical conditions", c["physical"]),
        ("capital markets", c["capital_access"]),
    ]
    comps.sort(key=lambda x: x[1])
    return comps[0][0], comps[1][0]


def wiki_url(name):
    slug = WIKI_SLUG.get(name) or name.replace(" ", "_")
    return "https://en.wikipedia.org/wiki/" + quote(slug)


def venue_urls(silicon):
    urls = {
        "Lambda": "https://lambda.ai/pricing",
        "CoreWeave": "https://www.coreweave.com/pricing",
        "CoreWeave NA": "https://www.coreweave.com/pricing",
        "CoreWeave EU": "https://www.coreweave.com/pricing",
        "Crusoe": "https://www.crusoe.ai/cloud/pricing",
        "AWS": "https://aws.amazon.com/ec2/capacityblocks/pricing/",
        "GCP": "https://cloud.google.com/products/compute/pricing/accelerator-optimized",
        "GCP TPU": "https://cloud.google.com/tpu/pricing",
        "DigitalOcean": "https://www.digitalocean.com/pricing/gpu-droplets",
        "SemiAnalysis": "https://gpu-index.semianalysis.com/",
        "Vast": "https://vast.ai/",
        "Cerebras": "https://www.cerebras.ai/",
        "Groq": "https://groq.com/",
    }
    for src in silicon.get("sources") or []:
        name, url = src.get("name") or "", src.get("url") or ""
        if not url:
            continue
        for key in list(urls):
            if key.lower() in name.lower() or name.lower() in key.lower():
                urls.setdefault(key, url)
        short = name.split()[0] if name else ""
        if short and short not in urls:
            urls[short] = url
    return urls


def rank_maps(history):
    snaps = [s for s in (history.get("snapshots") or []) if s.get("index") == "countries"]
    snaps.sort(key=lambda s: s.get("date") or "")
    dates = [s["date"] for s in snaps if s.get("date")]
    first = {r["id"]: r.get("rz") for r in (snaps[0].get("rows") or [])} if snaps else {}
    last = {r["id"]: r.get("rz") for r in (snaps[-1].get("rows") or [])} if snaps else {}
    return dates, first, last


def precedent_href(iso, name, slug_by_iso):
    if name in PREC_CAMPUS:
        return PREC_CAMPUS[name]
    if iso == "EU":
        return "/campuses.html"
    slug = slug_by_iso.get(iso)
    if slug:
        return f"/country/{slug}/#projects"
    return "/#projects"


def prec_status():
    out = {}
    for iso, _p, _s, st, _d in PREC:
        if iso == "EU":
            continue
        best, cnt, stall = out.get(iso, (0.0, 0, False))
        out[iso] = (max(best, STATUS_PTS.get(st, 0)), cnt + 1, stall or st == "Stalled")
    return out


def conversion_score(c, live_gw, wire, prec):
    tap = (live_gw / c["ceiling_GW"]) if c["ceiling_GW"] else 0
    conv = min(1.0, tap / 0.10)
    bpts, cnt, has_stall = prec.get(c["iso3"], (0.0, 0, False))
    pipeline = max(min(1.0, bpts + 0.1 * (cnt - 1)) if cnt else 0.0, c["momentum"] * 0.6)
    vel = 0.0
    latest = None
    for it in wire:
        if c["iso3"] not in it.get("countries", []):
            continue
        try:
            days = (SCORE_TODAY - _dt.strptime(it["date"][:10], "%Y-%m-%d")).days
        except ValueError:
            continue
        decay = max(0.0, 1 - days / 120)
        sgn = -0.5 if "Stall" in it.get("tags", []) else 1.0
        vel += sgn * (it.get("score") or 0) / 100 * decay
        if latest is None or it["date"] > latest["date"]:
            latest = it
    sig = min(1.0, max(0.0, vel) / 1.5)
    execu = min(1.0, c["built_pct"] / 0.5)
    rz = round(100 * (0.35 * conv + 0.25 * pipeline + 0.25 * sig + 0.15 * execu))
    return rz, latest


def signal_dir(latest, rz, rz0):
    if latest:
        if "Stall" in (latest.get("tags") or []):
            return "down", latest.get("title") or ""
        return "up", latest.get("title") or ""
    if rz > rz0:
        return "up", ""
    if rz < rz0:
        return "down", ""
    return "flat", ""


def countries_payload(model, wire, history):
    dates, rz0_map, _rz_pub = rank_maps(history)
    prec = prec_status()
    rows = []
    for c in model:
        live_gw, gflag = GDC_GW.get(c["iso3"], (0.0, "E"))
        rz, latest = conversion_score(c, live_gw, wire, prec)
        rz0 = rz0_map.get(c["iso3"], rz)
        w1, w2 = weakest(c)
        direction, signal = signal_dir(latest, rz, rz0)
        lo_t = round(c["cnw_ceiling_lo_B"] / 1000, 1)
        hi_t = round(c["cnw_ceiling_hi_B"] / 1000, 1)
        gdc = round(live_gw * 50, 1)
        rows.append({
            "id": c["iso3"],
            "iso2": (c.get("iso2") or "").upper(),
            "name": c["name"],
            "region": c["region"],
            "tier": TIER_CODE[c["tier"]],
            "ceilGW": round(c["ceiling_GW"], 1) if c["ceiling_GW"] < 10 else round(c["ceiling_GW"]),
            "ceilLo": lo_t,
            "ceilHi": hi_t,
            "xgdp": int(round(c["gdp_multiple"])) if c["gdp_multiple"] >= 2 else round(c["gdp_multiple"], 1),
            "unlock": int(round(c["cnw_unlockable_B"])),
            "perPerson": int(round(c["unlock_pc"])),
            "built": round(c["built_pct"] * 100, 1),
            "liveGW": live_gw,
            "gdc": gdc,
            "gdp": int(round(c["gdp_B"])),
            "readiness": round(c["readiness"], 3),
            "rz": rz,
            "rz0": rz0,
            "rank": 0,
            "dir": direction,
            "signal": signal,
            "disc": f"{w1} and {w2}",
            "slug": slugify(c["name"]),
            "wiki": wiki_url(c["name"]),
            "flag": (c.get("iso2") or "").lower(),
            "democracy": c.get("dem3") or c.get("eiu_class") or "",
        })
    rows.sort(key=lambda r: (-r["unlock"], r["name"]))
    for i, r in enumerate(rows, 1):
        r["rank"] = i
    for i, r in enumerate(sorted(rows, key=lambda x: -x["gdc"])):
        r["gdcEst"] = i >= 35
    return rows, dates


def money_note(q):
    bits = []
    if q.get("config") and q.get("config") not in ("list", "od"):
        bits.append(str(q["config"]).replace("x", "×").replace("-", " "))
    if q.get("note"):
        bits.append(q["note"])
    return " · ".join(bits)


def chip_quotes(chip):
    disp = chip.get("display") or {}
    out = []
    seen = set()

    def add(q, lead=False):
        key = (q.get("venue"), q.get("term"), q.get("usd_per_gpu_hr"), q.get("as_of") or q.get("date"))
        if key in seen:
            return
        seen.add(key)
        usd = q.get("usd_per_gpu_hr")
        if usd is None and q.get("currency") != "CNY":
            usd = q.get("price")
        row = [
            q.get("venue") or "",
            q.get("term") or "",
            usd,
            iso_day(q.get("as_of") or q.get("date") or ""),
            money_note(q),
        ]
        if lead:
            out.insert(0, row)
        else:
            out.append(row)

    add({
        "venue": disp.get("venue"),
        "term": disp.get("term"),
        "usd_per_gpu_hr": disp.get("usd_per_gpu_hr"),
        "as_of": disp.get("as_of"),
        "note": disp.get("note") or disp.get("config") or "",
        "config": disp.get("config"),
    }, lead=True)
    for q in chip.get("quotes") or []:
        add(q)
    return out


def change_block(changes, key):
    row = (changes or {}).get(key) or {}
    if row.get("pct") is None:
        return {"pct": None, "note": row.get("title") or "No dated same-venue pair."}
    return {
        "pct": row["pct"],
        "then": row.get("then"),
        "thenDate": iso_day(row.get("then_date")),
        "note": row.get("title") or "",
    }


def first_print(chip, points):
    spark = ((chip.get("spark") or {}).get("points")) or []
    if spark:
        p0 = spark[0]
        return {"price": p0.get("price"), "date": iso_day(p0.get("date"))}
    own = [p for p in points if p.get("chip") == chip["id"] and p.get("price") is not None]
    own.sort(key=lambda p: p.get("date") or "")
    if own:
        return {"price": own[0]["price"], "date": iso_day(own[0]["date"])}
    return None


def spark_pts(chip):
    pts = []
    for p in ((chip.get("spark") or {}).get("points")) or []:
        if p.get("price") is None or not p.get("date"):
            continue
        pts.append([iso_day(p["date"]), p["price"]])
    return pts


def term_book(chip):
    terms = chip.get("terms") or {}
    out = {}
    for key in ("y1", "y3"):
        slot = terms.get(key)
        if not slot:
            continue
        out[key] = {
            "price": slot.get("usd_per_gpu_hr") if slot.get("usd_per_gpu_hr") is not None else slot.get("price"),
            "venue": slot.get("venue") or "",
            "label": slot.get("label") or slot.get("term") or "",
        }
    return out


def chips_payload(silicon, history_points):
    chips = []
    for c in sorted(silicon.get("chips") or [], key=lambda x: x.get("rank") or 99):
        disp = c.get("display") or {}
        cfg = disp.get("note") or disp.get("config") or ""
        if cfg:
            cfg = str(cfg).replace("8x", "8×").replace("x ", "× ")
        chips.append({
            "id": c["id"],
            "slug": chip_slug(c["id"], c.get("vendor")),
            "name": c.get("name"),
            "vendor": c.get("vendor"),
            "rank": c.get("rank"),
            "score": c.get("score"),
            "liq": c.get("liquidity"),
            "dem": c.get("demand"),
            "fr": c.get("frontier"),
            "mem": c.get("memory") or "",
            "disp": {
                "usd": disp.get("usd_per_gpu_hr"),
                "cny": disp.get("cny_per_gpu_hr"),
                "venue": disp.get("venue") or "",
                "term": disp.get("term") or "",
                "asOf": iso_day(disp.get("as_of") or silicon.get("updated")),
                "cfg": cfg,
            },
            "quotes": chip_quotes(c),
            "terms": term_book(c),
            "chg": {
                "q": change_block(c.get("changes"), "d90"),
                "y": change_block(c.get("changes"), "d1y"),
            },
            "first": first_print(c, history_points),
            "spark": spark_pts(c),
            "avail": c.get("availability") or "",
            "scar": c.get("scarcity_label") or c.get("scarcity") or "",
            "cannot": c.get("cannot_show") or [],
        })
    return chips


def series_points(points, chip_id, venue, term):
    rows = []
    for p in points:
        if p.get("chip") != chip_id:
            continue
        if (p.get("venue") or "") != venue:
            continue
        if term.lower() not in (p.get("term") or "").lower():
            continue
        if p.get("price") is None:
            continue
        day = iso_day(p.get("date"))
        if not day or "H2" in str(day) and len(str(day)) < 8:
            # keep half-year prints as YYYY-H2 so the step chart can show them
            day = str(p.get("date") or "")
        rows.append([day, p["price"]])
    # collapse same-price runs to the first and last of each step
    rows.sort(key=lambda r: r[0])
    seen = []
    last_px = object()
    for d, px in rows:
        if px != last_px:
            seen.append([d, px])
            last_px = px
    return seen


def price_paths(points):
    paths = {}
    captions = {}
    for title, specs in PATH_SPEC.items():
        series = []
        bits = []
        for chip_id, venue, term, stale, name in specs:
            pts = series_points(points, chip_id, venue, term)
            if not pts:
                continue
            series.append({
                "name": name,
                "short": name.split(",")[0],
                "pts": pts,
                **({"stale": True} if stale else {}),
            })
            first, last = pts[0], pts[-1]
            hold = " and has held" if first[1] == last[1] and first[0] != last[0] else ""
            bits.append(
                f"{venue} {term} printed ${first[1]:.2f} on {first[0]} and ${last[1]:.2f} on {last[0]}{hold}."
            )
        if series:
            paths[title] = series
            captions[title] = " ".join(bits) + " Dated prints only; nothing between them is inferred."
    return paths, captions


def as_of(silicon, brief, history):
    cands = [
        iso_day(silicon.get("updated")),
        iso_day(silicon.get("snapshot")),
        iso_day(brief.get("updated")),
        iso_day(history.get("as_of")),
    ]
    return max((d for d in cands if len(d) == 10), default="2026-08-10")


def assemble():
    try:
        model = load_json("src/cnw_computed.json")
    except FileNotFoundError:
        model = load_json("cnw_computed.json")
    silicon = load_json("silicon.json")
    hist = load_json("silicon-history.json", {"points": []})
    ranks = load_json("rank-history.json", {"snapshots": []})
    brief = load_json("brief.json", {})
    wire = load_json("wire.json", {"items": []}).get("items") or []
    countries, snap_dates = countries_payload(model, wire, ranks)
    if not snap_dates:
        snap_dates = [FIRST_SNAPSHOT]
    chips = chips_payload(silicon, hist.get("points") or [])
    paths, captions = price_paths(hist.get("points") or [])
    asof = as_of(silicon, brief, ranks)
    payload = {
        "config": {
            "site": SITE,
            "asOf": asof,
            "firstSnapshot": snap_dates[0] if snap_dates else FIRST_SNAPSHOT,
            "live": False,
            "endpoints": {"countries": "/data.json", "silicon": "/silicon.json", "history": "/rank-history.json"},
        },
        "tier": TIER,
        "tierDef": TIER_DEF,
        "countries": countries,
        "chips": chips,
        "venueUrl": venue_urls(silicon),
        "domains": DOMAINS,
        "pricePaths": paths,
        "priceCaptions": captions,
        "snapshotDates": snap_dates,
        "precedents": [
            list(p) + [precedent_href(p[0], p[1], {c["id"]: c["slug"] for c in countries})]
            for p in PREC
        ],
        "readiness": READINESS,
    }
    return payload, model


def headline_rail(countries, chips):
    ceil = sum(c["ceilHi"] for c in countries)
    unlock = sum(c["unlock"] for c in countries) / 1000
    gdc = sum(c["gdc"] for c in countries) / 1000
    tap = (sum(c["gdc"] for c in countries) / (sum(c["ceilHi"] for c in countries) * 1000)) if ceil else 0
    top2 = sorted(countries, key=lambda c: -c["gdc"])[:2]
    share = sum(c["gdc"] for c in top2) / sum(c["gdc"] for c in countries) * 100 if countries else 0
    def t(v):
        return f"${v:.0f}T" if v >= 10 or abs(v - round(v)) < 0.05 else f"${v:.1f}T"
    return {
        "ceiling": t(ceil),
        "unlockable": t(unlock) if unlock >= 10 else f"${unlock:.0f}T",
        "live": f"${gdc:.1f}T",
        "tap_pct": f"{tap * 100:.1f}%",
        "top2_share": f"{share:.0f}%",
        "n_countries": len(countries),
        "n_chips": len(chips),
        "ceil_raw": ceil,
        "unlock_raw": unlock,
        "gdc_raw": gdc,
    }
