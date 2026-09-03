#!/usr/bin/env python3
# Shared Compute Net Worth helpers for Phase 1 builders.
# Numbers come from existing JSON only. No invented prices, ranks, or deltas.
import html
import json
import os
import re
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SITE = "https://compute.world"
N_COUNTRIES = 108

STABV = {"H": 1.0, "M": 0.65, "L": 0.35, "C": 0.10}
TRIV = {"S": 1.0, "M": 0.6, "W": 0.25}
FIBV = {"S": 1.0, "M": 0.6, "W": 0.3}

TIER_COLOR = {
    "Sleeping Giant": "#2f4a6d",
    "Primed": "#2e6b4f",
    "Incumbent": "#5a5752",
    "Emerging Upside": "#9a6b1c",
    "Long Road": "#a89a7f",
}
TIER_CLASS = {
    "Sleeping Giant": "sg",
    "Primed": "pr",
    "Incumbent": "in",
    "Emerging Upside": "eu",
    "Long Road": "lr",
}
TIER_SLUG = {
    "Sleeping Giant": "sleeping_giant",
    "Primed": "primed",
    "Incumbent": "incumbent",
    "Emerging Upside": "emerging_upside",
    "Long Road": "long_road",
}

LABEL_CEILING = "at full build-out"
LABEL_UNLOCK = "bankable today"
LABEL_GDC = "running today"

STATUS_PTS = {"Live": 1.0, "Building": 0.7, "Contracted": 0.5, "Announced": 0.25, "Stalled": 0.1}
PREC_ALIAS = {"UK": "United Kingdom"}

# Same precedents catalog as build_page.py / data.json. Do not invent rows.
PREC = [
    ("🇦🇲", "Armenia", "Firebird AI factory, Hrazdan (NVIDIA, Dell)", "300 MW + 70k GPUs by 2027", "Live", "Aug 2026"),
    ("🇲🇾", "Malaysia", "Johor hub; YTL AI Cloud, Kulai (NVIDIA GB200)", "1,110 MW live in Johor", "Live", "2025-26"),
    ("🇰🇷", "South Korea", "National GPU program (NVIDIA, Samsung, SK, Naver); AIDC Alliance", "260k+ GPUs; 18.4 GW by 2035 target", "Live", "Oct 2025"),
    ("🇮🇳", "India", "IndiaAI Mission GPU commons", "17k+ GPUs installed; 100k+ target", "Live", "2025-26"),
    ("🇧🇷", "Brazil", "Scala AI City, Eldorado do Sul", "54 MW live; 4.75 GW / $50B planned", "Live", "2026"),
    ("🇶🇦", "Qatar", "Ooredoo Syntys sovereign AI cloud", "NVIDIA clusters, national scale", "Live", "Jul 2025"),
    ("🇨🇱", "Chile", "National Data Centers Plan", "325 MW to 1.2 GW by 2030", "Live", "2024-26"),
    ("🇪🇹", "Ethiopia", "GERD surplus sold to bitcoin miners", "Compute conversion, crudest form", "Live", "2025-26"),
    ("🇯🇵", "Japan", "SoftBank Sakai, ex-Sharp plant (Stargate Japan anchor)", "150 to 250 MW, ~100k GPUs", "Building", "2026"),
    ("🇮🇳", "India", "Reliance Jamnagar AI campus (Meta JV 168 MW)", "$110B plan; 120+ MW live H2 2026", "Building", "2026"),
    ("🇧🇷", "Brazil", "ByteDance Pecém campus (wind PPA)", "300 MW first phase, ~$39B", "Building", "Jan 2026"),
    ("🇲🇽", "Mexico", "CloudHQ Querétaro", "Up to 900 MW, $4.8B", "Building", "2026"),
    ("🇸🇦", "Saudi Arabia", "HUMAIN AI factories (NVIDIA, AMD, AWS)", "6.6 GW by 2034 target", "Building", "2025-26"),
    ("🇦🇪", "UAE", "Stargate UAE, Abu Dhabi (G42, OpenAI, Oracle)", "First 200 MW of 1 GW / 5 GW campus", "Building", "2026"),
    ("🇺🇿", "Uzbekistan", "DataVolt Tashkent (DFI-financed, NVIDIA)", "12 MW, $150M", "Building", "2026"),
    ("🇰🇿", "Kazakhstan", "Ekibastuz Data Center Valley (NVIDIA, Firebird)", "$10B; 300 MW to 1 GW, 100k GPUs", "Contracted", "Jun 2026"),
    ("🇮🇩", "Indonesia", "Zankore 1 GW platform (Indosat, Ooredoo, NVIDIA, Nokia)", "First 200 MW H1 2027", "Contracted", "Aug 2026"),
    ("🇻🇳", "Vietnam", "G42 + FPT sovereign AI framework", "$1B+, HCMC hyperscale", "Contracted", "Feb 2026"),
    ("🇳🇴", "Norway", "Stargate Norway, Narvik (Nscale, Aker; Microsoft 30k Rubin)", "230 MW+, hydro-powered", "Contracted", "2025-26"),
    ("🇮🇳", "India", "OpenAI for India (Tata)", "100 MW scaling to 1 GW", "Announced", "Feb 2026"),
    ("🇲🇦", "Morocco", "Nexus AI factory, Casablanca (NVIDIA, Naver)", "$1.2B, sovereign platform", "Announced", "2026"),
    ("🇪🇺", "EU", "AI Gigafactories tender (EuroHPC)", "Up to 7 sites, €10B public", "Announced", "Jul 2026"),
    ("🇵🇰", "Pakistan", "2 GW surplus power allocated to mining and AI", "Policy allocation", "Announced", "2025"),
    ("🇬🇧", "UK", "Stargate UK (OpenAI, NVIDIA, Nscale)", "31k GPUs planned; paused on energy costs", "Stalled", "Apr 2026"),
    ("🇦🇷", "Argentina", "Stargate Argentina, Patagonia (Sur Energy)", "$25B / 500 MW; no visible progress", "Stalled", "2025-26"),
    ("🇰🇪", "Kenya", "Microsoft and G42 campus", "Stalled for lack of power", "Stalled", "May 2026"),
]


def load_root_json(name, default=None):
    for p in (os.path.join(ROOT, name), os.path.join(HERE, name), name):
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    return {} if default is None else default


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def esc(s):
    return html.escape("" if s is None else str(s), quote=True)


def money_b(b, missing="—"):
    """Format a $B figure. Missing / zero live-compute reads as an em dash."""
    if b is None:
        return missing
    try:
        b = float(b)
    except (TypeError, ValueError):
        return missing
    if b <= 0:
        return missing
    if b >= 1000:
        return f"${b / 1000:.1f}T"
    if b >= 100:
        return f"${b:.0f}B"
    if b >= 10:
        return f"${b:.0f}B"
    if b >= 1:
        return f"${b:.1f}B"
    return f"${b:.1f}B"


def money_pc(v, missing="—"):
    if v is None:
        return missing
    try:
        v = float(v)
    except (TypeError, ValueError):
        return missing
    if v <= 0:
        return missing
    if v >= 100000:
        return f"${v / 1000:,.0f}k"
    if v >= 1000:
        return f"${v / 1000:,.1f}k"
    return f"${v:,.0f}"


def fmt_gdp(g):
    return money_b(g)


def fmt_mult(m, missing="—"):
    if m is None:
        return missing
    try:
        m = float(m)
    except (TypeError, ValueError):
        return missing
    if m <= 0:
        return missing
    if m >= 100:
        return f"{m:.0f}×"
    return f"{m:.1f}×"


def fmt_rank_serial(rank, n=N_COUNTRIES):
    if rank is None:
        return "—"
    return f"No. {rank} of {n}"


def delta_mark(delta):
    """Triangle up/down, dot unchanged. None when two dated prints do not exist."""
    if delta is None:
        return None
    if delta > 0:
        return "up", "▲", delta
    if delta < 0:
        return "down", "▼", delta
    return "flat", "●", 0


def readiness_parts(c):
    """Eight readiness components as 0–1 scores. Same weights as cnw_model.py."""
    return [
        ("governance", c.get("cpi", 0) / 100),
        ("stability", STABV.get(c.get("stability"), 0)),
        ("chip access", c.get("gpu_access", 0)),
        ("the grid", TRIV.get(c.get("grid"), 0)),
        ("fiber", FIBV.get(c.get("fiber"), 0)),
        ("momentum", c.get("momentum", 0)),
        ("physical", c.get("physical", 0)),
        ("capital", c.get("capital_access", 0)),
    ]


def weakest_two(c):
    parts = readiness_parts(c)
    parts.sort(key=lambda x: x[1])
    return parts[0][0], parts[1][0]


def one_line_verdict(c, max_len=90):
    t = c["tier"]
    m = c.get("gdp_multiple") or 0
    if t == "Sleeping Giant":
        text = f"A sleeping giant: the endowment runs {m:.0f} times the economy."
    elif t == "Primed":
        text = "Primed: readiness clears 65 percent, and there is real headroom."
    elif t == "Incumbent":
        text = "An incumbent: already priced in, already building."
    elif t == "Emerging Upside":
        text = "Emerging upside: a narrower gap, and a real one."
    else:
        text = "A long road: a modest ceiling, and a free option to hold."
    if len(text) > max_len:
        text = text[: max_len - 1].rstrip() + "…"
    return text


def country_h1(c):
    name = c["name"]
    t = TIER_SLUG[c["tier"]]
    gdp = fmt_gdp(c.get("gdp_B"))
    ceiling = money_b(c.get("cnw_ceiling_hi_B"))
    gdc = money_b(c.get("cnw_gdc_B"))
    headroom = money_b((c.get("cnw_ceiling_hi_B") or 0) - (c.get("cnw_unlockable_B") or 0))
    if t == "sleeping_giant":
        return f"{name}: a {gdp} economy on a {ceiling} compute ceiling"
    if t == "primed":
        return f"{name}: ready to build, with {headroom} of headroom"
    if t == "incumbent":
        return f"{name}: {gdc} of compute running today"
    if t == "emerging_upside":
        return f"{name}: a narrower gap, and a real one"
    return f"{name}: a modest ceiling and a free option"


def gazetteer_blurb(c):
    w1, w2 = weakest_two(c)
    lo, hi, u, g = c["cnw_ceiling_lo_B"], c["cnw_ceiling_hi_B"], c["cnw_unlockable_B"], c["gdp_B"]
    m = c["gdp_multiple"]
    b = (c.get("built_pct") or 0) * 100
    upc = c.get("unlock_pc") or 0
    lg = c.get("lg") or 0
    ig = c.get("installed_gw")
    grid = f" on a grid of roughly {ig:.0f} GW" if ig and ig >= 10 else (f" on a grid of roughly {ig} GW" if ig else "")
    if lg >= 1:
        live = f"{lg:.1f} GW" + grid
    elif lg > 0:
        live = f"about {max(1, round(lg * 1000))} MW" + grid
    else:
        live = "no sourced live datacenter capacity"
    gdc = c.get("cnw_gdc_B") or 0
    gdcS = money_b(gdc) if gdc >= 1 else "under $1B"
    tl = one_line_verdict(c, 200)
    return (
        f"{c['name']} sits on a resource ceiling of roughly {c['ceiling_GW']:.0f} GW, worth {money_b(lo)} to {money_b(hi)} "
        f"of AI compute at today's prices, about {m:.0f} times its {fmt_gdp(g)} GDP. The bankable slice today is "
        f"{money_b(u)}, which is {money_pc(upc)} for every citizen, discounted mainly for {w1} and {w2}. It has built "
        f"{b:.1f}% of the ceiling and runs {live}, a Gross Domestic Compute of {gdcS}. {tl}"
    )


def share_text(c):
    m = c.get("gdp_multiple") or 0
    x = f"{m:.0f}" if m >= 100 else f"{m:.1f}"
    return (
        f"{c['name']}'s compute ceiling is {x} times its GDP: {c['tier']}, "
        f"{fmt_rank_serial(c.get('rank'))} on the Compute Net Worth Index. "
        f"{SITE}/{c['slug']}"
    )


def page_description(c):
    m = c.get("gdp_multiple") or 0
    x = f"{m:.0f}" if m >= 10 else f"{m:.1f}"
    return (
        f"{c['name']}'s Compute Net Worth: {money_b(c.get('cnw_unlockable_B'))} {LABEL_UNLOCK}, "
        f"{money_b(c.get('cnw_ceiling_hi_B'))} {LABEL_CEILING}, "
        f"{money_b(c.get('cnw_gdc_B'))} {LABEL_GDC}. "
        f"Ceiling {x}× GDP. {c['tier']}, {fmt_rank_serial(c.get('rank'))}."
    )


def parse_day(s):
    s = str(s or "")[:10]
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return None


def nice_day(iso, kind="long"):
    d = parse_day(iso)
    if not d:
        return str(iso or "")
    if kind == "short":
        return f"{d.day} {d.strftime('%b %Y')}"
    return f"{d.day} {d.strftime('%B %Y')}"


def load_computed():
    path = os.path.join(HERE, "cnw_computed.json")
    if not os.path.isfile(path):
        path = os.path.join(ROOT, "src", "cnw_computed.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_wire_items():
    return load_root_json("wire.json").get("items") or []


def wire_for_iso3(items, iso3):
    out = []
    for it in items:
        if iso3 in (it.get("countries") or []):
            out.append(it)
    out.sort(key=lambda x: x.get("date") or "", reverse=True)
    return out


def corroboration_label(raw):
    allowed = ("Confirmed", "Corroborated", "Single-source", "Disputed")
    s = (raw or "").strip()
    if s in allowed:
        return s
    return None


def live_signals_empty(items, as_of):
    if not items:
        return "No signals scored yet. Send one to the Desk."
    latest = parse_day(items[0].get("date"))
    today = parse_day(as_of) or datetime(2026, 9, 3)
    if not latest:
        return "No signals scored yet. Send one to the Desk."
    n = max(0, (today - latest).days)
    if n <= 0:
        return "Last signal today."
    if n == 1:
        return "Last signal 1 day ago"
    return f"Last signal {n} days ago"


def country_rank_snapshots(history):
    snaps = [s for s in (history.get("snapshots") or []) if s.get("index") == "countries"]
    snaps.sort(key=lambda s: s.get("date") or "")
    return snaps


def ranks_by_iso(snaps):
    """iso3 -> list of (date, rank) in date order."""
    series = {}
    for s in snaps:
        date = s.get("date")
        for row in s.get("rows") or []:
            iso = row.get("id")
            r = row.get("rank")
            if iso and r is not None:
                series.setdefault(iso, []).append((date, r))
    return series


def weekly_delta(series, as_of=None):
    """Rank change vs the print ~7 days earlier. None if two dated prints do not exist."""
    if not series or len(series) < 2:
        return None
    latest_date, latest_rank = series[-1]
    latest = parse_day(latest_date)
    if not latest:
        return None
    target = latest - timedelta(days=7)
    prev = None
    for date, rank in series[:-1]:
        d = parse_day(date)
        if d and d <= target:
            prev = (d, rank)
    if prev is None:
        # Two dated prints exist but none is a week old — still a real pair; use the prior print.
        prev_date, prev_rank = series[-2]
        if parse_day(prev_date) is None:
            return None
        return prev_rank - latest_rank
    return prev[1] - latest_rank


def current_rank(series):
    if not series:
        return None
    return series[-1][1]


def precedents_for(name):
    rows = []
    for fg, c, project, scale, status, date in PREC:
        if PREC_ALIAS.get(c, c) == name:
            rows.append({"flag": fg, "country": c, "project": project, "scale": scale, "status": status, "date": date})
    return rows


def peers_for(country, countries, n=3):
    """Three peers: same region first, then nearest unlockable."""
    others = [c for c in countries if c["iso3"] != country["iso3"]]
    region = [c for c in others if c["region"] == country["region"]]
    region.sort(key=lambda c: abs((c.get("cnw_unlockable_B") or 0) - (country.get("cnw_unlockable_B") or 0)))
    picked = region[:n]
    if len(picked) < n:
        rest = [c for c in others if c not in picked]
        rest.sort(key=lambda c: abs((c.get("cnw_unlockable_B") or 0) - (country.get("cnw_unlockable_B") or 0)))
        picked.extend(rest[: n - len(picked)])
    return picked[:n]


def movers_from_wire(countries, items, limit=12):
    """Countries with at least one cited Wire signal, newest first. Never empty-signal rows."""
    by_iso = {c["iso3"]: c for c in countries}
    seen = []
    used = set()
    for it in sorted(items, key=lambda x: x.get("date") or "", reverse=True):
        for iso in it.get("countries") or []:
            if iso in used or iso not in by_iso:
                continue
            used.add(iso)
            seen.append({"country": by_iso[iso], "item": it})
            if len(seen) >= limit:
                return seen
    return seen


def as_of_date():
    brief = load_root_json("brief.json")
    silicon = load_root_json("silicon.json")
    hist = load_root_json("rank-history.json")
    cands = []
    for s in (brief.get("updated"), silicon.get("updated"), hist.get("as_of")):
        d = str(s or "")[:10]
        if len(d) == 10:
            cands.append(d)
    return max(cands) if cands else "2026-08-10"


def assemble_countries():
    """Join computed model + GDC + rank history + wire. Source of numbers: existing JSON only."""
    from gdc_data import GDC_GW, LATLNG

    computed = load_computed()
    wire = load_wire_items()
    history = load_root_json("rank-history.json")
    snaps = country_rank_snapshots(history)
    series = ranks_by_iso(snaps)
    as_of = as_of_date()

    countries = []
    for c in computed:
        iso3 = c["iso3"]
        gw_live, gflag = GDC_GW.get(iso3, (None, "E"))
        lat, lng = LATLNG.get(iso3, (None, None))
        gdc_b = None if gw_live is None else round(gw_live * 50, 1)
        # A true zero live-GW print is missing, not a priced zero.
        if gdc_b is not None and gdc_b <= 0:
            gdc_b = None
            gw_live = None
        ser = series.get(iso3) or []
        rank = current_rank(ser)
        delta = weekly_delta(ser)
        items = wire_for_iso3(wire, iso3)
        row = dict(c)
        row.update({
            "slug": slugify(c["name"]),
            "lg": gw_live,
            "lgE": (gflag == "E"),
            "cnw_gdc_B": gdc_b,
            "lat": lat,
            "lng": lng,
            "rank": rank,
            "rank_delta": delta,
            "rank_series": ser,
            "wire": items,
            "precedents": precedents_for(c["name"]),
            "blurb": None,
            "verdict": one_line_verdict(c),
            "as_of": as_of,
        })
        row["blurb"] = gazetteer_blurb(row)
        row["h1"] = country_h1(row)
        row["share"] = share_text(row)
        row["description"] = page_description(row)
        countries.append(row)

    # If rank-history is missing a country, fall back to unlockable order (same published formula).
    ranked = [c for c in countries if c["rank"]]
    if len(ranked) < len(countries):
        by_u = sorted(countries, key=lambda x: -(x.get("cnw_unlockable_B") or 0))
        for i, c in enumerate(by_u, 1):
            if not c["rank"]:
                c["rank"] = i
                c["share"] = share_text(c)
                c["description"] = page_description(c)

    countries.sort(key=lambda x: (x.get("rank") or 999, -(x.get("cnw_unlockable_B") or 0)))
    for c in countries:
        c["peers"] = peers_for(c, countries, 3)
    return countries, as_of, wire, snaps


def global_stats(countries):
    hi = sum(c.get("cnw_ceiling_hi_B") or 0 for c in countries)
    u = sum(c.get("cnw_unlockable_B") or 0 for c in countries)
    gdc = sum(c.get("cnw_gdc_B") or 0 for c in countries)
    tap = (gdc / hi) if hi else 0
    return {
        "ceiling_T": hi / 1000,
        "unlock_T": u / 1000,
        "gdc_T": gdc / 1000,
        "tap_pct": tap * 100,
    }


def slim_payload(countries):
    """Compact JSON for homepage filters / geo card. No invented fields."""
    out = []
    for c in countries:
        out.append({
            "n": c["name"],
            "sl": c["slug"],
            "fg": c.get("femoji") or "",
            "i2": c.get("iso2") or "",
            "i3": c["iso3"],
            "r": c["region"],
            "t": c["tier"],
            "rk": c.get("rank"),
            "dd": c.get("rank_delta"),
            "lo": c.get("cnw_ceiling_lo_B"),
            "hi": c.get("cnw_ceiling_hi_B"),
            "u": c.get("cnw_unlockable_B"),
            "gdc": c.get("cnw_gdc_B"),
            "lgE": c.get("lgE"),
            "m": c.get("gdp_multiple"),
            "upc": c.get("unlock_pc"),
            "g": c.get("gdp_B"),
            "re": c.get("readiness"),
            "v": c.get("verdict"),
            "asof": c.get("as_of"),
            "coupon": [(lab, round(val, 3)) for lab, val in readiness_parts(c)],
        })
    return out
