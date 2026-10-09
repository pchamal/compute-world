#!/usr/bin/env python3
# Dated-print hygiene for The Silicon Tape.
# Sleeve weights stay in this file. Do not print them on silicon.html / FAQ / llms.txt.
"""Tape Print + change windows from dated observed prints only.

A percent is computed only from two real same-chip, same-venue, same-term,
same-config-family prints. Carry-forward is for sparkline *drawing* only.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta

AS_OF = date(2026, 8, 18)
WINDOWS = {"d30": (30, 5), "d90": (90, 10), "d1y": (365, 21), "d3y": (1095, 45)}
DASH_TITLE = "US list prices do not tick daily. 7d lights up after a week of our own scrape."
TERM_KEYS = ("m1", "q1", "y1", "y3")

# Internal sleeve weights. Never serialize these onto a public page.
_OD_W = {"Lambda": 5, "CoreWeave": 4, "Crusoe": 3, "DigitalOcean": 3, "GCP": 2}
_SPOT_W = {"CoreWeave": 4, "CoreWeave NA": 4, "CoreWeave EU": 3, "DigitalOcean": 2}
_CB_W = {"AWS": 5}
_Y1_W = {"SemiAnalysis": 5, "GCP": 3, "DigitalOcean": 3, "SMM Beijing": 4}
_TOKEN_W = {"Cerebras": 5, "Groq": 5}

_REJECT_VENUE = {
    "voltage park",
    "vast",
    "tensorwave",
    "gpus.io",
    "gpusio",
    "aggregator",
}
_REJECT_NOTE = ("aggregator", "gpus.io", "voltage park", "tensorwave")

_FAMILY_WEIGHTS = {
    "on-demand": _OD_W,
    "spot": _SPOT_W,
    "capacity-blocks": _CB_W,
    "1y": _Y1_W,
    "cny-monthly": _Y1_W,
    "token": _TOKEN_W,
}

_TERM_FAMILY = (
    ("capacity-blocks", ("capacity block", "capacity blocks", "cb")),
    ("cny-monthly", ("1y monthly", "cny monthly")),
    ("token", ("token", "enterprise")),
    ("spot", ("spot",)),
    ("3y", ("3y", "3-year", "36m", "36-month")),
    ("1y", ("1y", "1-year", "12m", "12-month", "1cc", "1-click", "2w–1y", "2w-1y", "reserved")),
    ("1q", ("1q", "1-quarter", "3-month", "quarterly")),
    ("1m", ("1-month", "monthly lease", "monthly index")),
    ("on-demand", ("on-demand", "od", "from")),
)


def parse_date(s):
    if not s:
        return None
    s = str(s)
    if s.endswith("-H2"):
        return date(int(s[:4]), 10, 1)
    if len(s) == 7 and s[4] == "-":
        return date(int(s[:4]), int(s[5:7]), 15)
    if len(s) == 10 and s[4] == "-" and s[7] == "-":
        return datetime.strptime(s, "%Y-%m-%d").date()
    return None


def fmt_date(d):
    if isinstance(d, date):
        return d.isoformat()
    return d or ""


def term_family(term):
    t = (term or "").lower()
    for fam, keys in _TERM_FAMILY:
        if any(k in t for k in keys):
            return fam
    return (term or "unknown").lower()


def norm_venue(v):
    return (v or "").strip()


def norm_config(cfg):
    return (cfg or "list").strip().lower()


def rejected(venue, note=""):
    v = (venue or "").lower()
    n = (note or "").lower()
    if any(x in v for x in _REJECT_VENUE):
        return True
    if any(x in n for x in _REJECT_NOTE) and "tensorwave" in (v + n):
        return True
    if "aggregator" in n or "voltage park" in n:
        return True
    return False


def config_of(obj, fallback="list"):
    return norm_config(obj.get("config") or fallback)


def point_key(p):
    return (
        p.get("chip") or p.get("id"),
        norm_venue(p.get("venue")),
        term_family(p.get("term")),
        norm_config(p.get("config")),
        p.get("date") or p.get("as_of"),
        p.get("price") if p.get("price") is not None else p.get("usd_per_gpu_hr"),
    )


def harvest_quotes(silicon):
    """Dated dollar prints already sitting on silicon.json quotes / display."""
    out = []
    for c in silicon.get("chips") or []:
        cid = c["id"]
        disp = c.get("display") or {}
        dcfg = config_of(disp)
        seen = set()

        def add(venue, term, price, as_of, url, cfg, currency="USD", unit="gpu-hr"):
            if price is None or as_of is None:
                return
            rec = {
                "id": f"{cid}|{venue}|{term}|{as_of}|{price}",
                "chip": cid,
                "date": as_of if len(str(as_of)) >= 7 else as_of,
                "price": float(price),
                "currency": currency,
                "unit": unit,
                "term": term,
                "venue": venue,
                "config": cfg,
                "url": url or "",
            }
            k = point_key(rec)
            if k in seen:
                return
            seen.add(k)
            out.append(rec)

        srcs = {s["id"]: s for s in silicon.get("sources") or []}
        if disp.get("usd_per_gpu_hr") is not None or disp.get("cny_per_gpu_hr") is not None:
            sid = disp.get("source_id")
            url = (srcs.get(sid) or {}).get("url") or ""
            if disp.get("cny_per_gpu_hr") is not None and disp.get("primary") == "CNY":
                add(
                    disp.get("venue"),
                    disp.get("term"),
                    disp.get("cny_per_gpu_hr"),
                    disp.get("as_of"),
                    url,
                    dcfg,
                    currency="CNY",
                    unit="card-hr",
                )
            elif disp.get("usd_per_gpu_hr") is not None:
                add(
                    disp.get("venue"),
                    disp.get("term"),
                    disp.get("usd_per_gpu_hr"),
                    disp.get("as_of"),
                    url,
                    dcfg,
                )
        for q in c.get("quotes") or []:
            if rejected(q.get("venue"), q.get("note") or ""):
                continue
            sid = q.get("source_id")
            url = (srcs.get(sid) or {}).get("url") or ""
            cfg = config_of(q, dcfg if q.get("venue") == disp.get("venue") else "list")
            if q.get("cny_per_gpu_hr") is not None:
                add(
                    q.get("venue"),
                    q.get("term"),
                    q.get("cny_per_gpu_hr"),
                    q.get("as_of"),
                    url,
                    cfg,
                    currency="CNY",
                    unit=q.get("unit") or "card-hr",
                )
            elif q.get("usd_per_gpu_hr") is not None:
                add(
                    q.get("venue"),
                    q.get("term"),
                    q.get("usd_per_gpu_hr"),
                    q.get("as_of"),
                    url,
                    cfg,
                    currency=q.get("currency") or "USD",
                    unit=q.get("unit") or "gpu-hr",
                )
    return out


def merge_history(history, harvested):
    points = list(history.get("points") or [])
    seen = {point_key(p) for p in points}
    appended = 0
    for p in harvested:
        k = point_key(p)
        if k in seen:
            continue
        points.append(p)
        seen.add(k)
        appended += 1
    history = dict(history)
    history["points"] = points
    history["as_of"] = history.get("as_of") or AS_OF.isoformat()
    history["rule"] = history.get("rule") or "dated observed prints only"
    return history, appended


def series_for(points, chip, venue, term, config):
    fam = term_family(term)
    cfg = norm_config(config)
    ven = norm_venue(venue)
    rows = []
    for p in points:
        if (p.get("chip") or p.get("id")) != chip:
            continue
        if norm_venue(p.get("venue")) != ven:
            continue
        if term_family(p.get("term")) != fam:
            continue
        if norm_config(p.get("config")) != cfg:
            continue
        price = p.get("price")
        if price is None:
            price = p.get("usd_per_gpu_hr")
        dt = parse_date(p.get("date") or p.get("as_of"))
        if price is None or dt is None:
            continue
        rows.append((dt, float(price), p))
    rows.sort(key=lambda x: x[0])
    return rows


def window_pair(rows, now, lookback, tol):
    if not rows:
        return None
    now_d = rows[-1][0] if now is None else now
    # Prefer a print on/near today; else the latest print
    latest = rows[-1]
    target = now_d - timedelta(days=lookback)
    lo, hi = target - timedelta(days=tol), target + timedelta(days=tol)
    cands = [r for r in rows if lo <= r[0] <= hi]
    if not cands:
        return None
    then = min(cands, key=lambda r: (abs((r[0] - target).days), -r[0].toordinal()))
    if latest[1] == 0:
        return None
    pct = 100.0 * (latest[1] / then[1] - 1.0)
    return {
        "pct": round(pct, 1),
        "now": latest[1],
        "now_date": fmt_date(latest[0]),
        "then": then[1],
        "then_date": fmt_date(then[0]),
        "venue": (then[2] or {}).get("venue"),
        "term": (then[2] or {}).get("term"),
    }


def change_title(pair, missing="No two dated same-venue same-term prints in this window."):
    if not pair:
        return missing
    sign = "+" if pair["pct"] > 0 else ""
    return (
        f"{pair.get('venue') or ''} {pair.get('term') or ''} "
        f"${pair['then']:g} on {pair['then_date']} → ${pair['now']:g} on {pair['now_date']} "
        f"({sign}{pair['pct']}%)"
    ).strip()


def changes_for(points, chip, venue, term, config, now):
    rows = series_for(points, chip, venue, term, config)
    out = {
        "d7": {"pct": None, "title": DASH_TITLE},
        "d30": {"pct": None, "title": "No dated pair in the 1M window (30d ±5d)."},
        "d90": {"pct": None, "title": "No dated pair in the 1Q window (90d ±10d)."},
        "d1y": {"pct": None, "title": "No dated pair in the 1Y window (365d ±21d)."},
        "d3y": {"pct": None, "title": "No dated pair in the 3Y window (1095d ±45d)."},
    }
    for key, (lb, tol) in WINDOWS.items():
        pair = window_pair(rows, now, lb, tol)
        if pair:
            pct = pair["pct"]
            if abs(pct) < 0.05:
                pct = 0.0
            out[key] = {
                "pct": pct,
                "then": pair["then"],
                "then_date": pair["then_date"],
                "now": pair["now"],
                "now_date": pair["now_date"],
                "title": change_title({**pair, "pct": pct}),
            }
    return out


def spark_points(rows):
    pts = []
    last = None
    for dt, price, _ in rows:
        rec = {"date": fmt_date(dt), "price": price}
        if last == (rec["date"], rec["price"]):
            continue
        pts.append(rec)
        last = (rec["date"], rec["price"])
    return pts


def spark_steps(pts, n=10):
    """Carry-forward samples for drawing only. Not additional prints."""
    if not pts:
        return []
    if len(pts) == 1:
        return list(pts)
    dates = [parse_date(p["date"]) for p in pts]
    if any(d is None for d in dates):
        return list(pts)
    start, end = dates[0], dates[-1]
    span = max((end - start).days, 1)
    n = max(7, min(12, n))
    out = []
    i = 0
    for k in range(n):
        day = start + timedelta(days=round(span * k / (n - 1)))
        while i + 1 < len(dates) and dates[i + 1] <= day:
            i += 1
        out.append({"date": fmt_date(day), "price": pts[i]["price"]})
    return out


def longest_window(chg):
    """Prefer 3Y, then 1Y, then 1Q, then 1M — the longest honest pair."""
    for key, lab in (("d3y", "3Y"), ("d1y", "1Y"), ("d90", "1Q"), ("d30", "1M")):
        pct = (chg.get(key) or {}).get("pct")
        if pct is not None:
            return key, lab, pct
    return None, None, None


def spark_direction(chg, pts):
    _, lab, pct = longest_window(chg)
    if pct is not None:
        if pct > 0:
            return "up", lab, pct
        if pct < 0:
            return "down", lab, pct
        return "flat", lab, pct
    if pts and pts[-1]["price"] > pts[0]["price"]:
        return "up", None, None
    if pts and pts[-1]["price"] < pts[0]["price"]:
        return "down", None, None
    return "flat", None, None


def spark_svg(steps, width=80, height=28, direction="flat"):
    if not steps:
        return ""
    prices = [s["price"] for s in steps]
    lo, hi = min(prices), max(prices)
    pad = 2
    if hi == lo:
        ys = [height / 2.0] * len(steps)
    else:
        ys = [pad + (1 - (p - lo) / (hi - lo)) * (height - 2 * pad) for p in prices]
    xs = [pad + i * (width - 2 * pad) / max(len(steps) - 1, 1) for i in range(len(steps))]
    d = [f"M{xs[0]:.1f},{ys[0]:.1f}"]
    for i in range(1, len(steps)):
        d.append(f"H{xs[i]:.1f}")
        d.append(f"V{ys[i]:.1f}")
    cls = {"up": "spark spark-up", "down": "spark spark-dn"}.get(direction, "spark")
    return (
        f'<svg class="{cls}" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.5" '
        f'stroke-linejoin="miter" stroke-linecap="butt" d="{" ".join(d)}"/></svg>'
    )


def weather_items(chips, limit=4):
    """Slim tape-weather: only real dated windows. No Fear & Greed."""
    prefer = (
        ("nvidia-h100-sxm-80gb", "d1y"),
        ("nvidia-b200-sxm6", "d90"),
        ("nvidia-h200-sxm-141gb", "d1y"),
        ("nvidia-a100-sxm-80gb", "d90"),
    )
    by = {c["id"]: c for c in chips}
    labs = {"d3y": "3Y", "d1y": "1Y", "d90": "1Q", "d30": "1M"}
    items = []
    seen = set()

    def add(c, key):
        row = (c.get("changes") or {}).get(key) or {}
        if row.get("pct") is None:
            return False
        disp = c.get("display") or {}
        items.append({
            "id": c["id"],
            "name": c["name"],
            "window": labs[key],
            "pct": row["pct"],
            "venue": disp.get("label") or disp.get("venue") or "",
            "title": row.get("title") or "",
        })
        seen.add((c["id"], key))
        return True

    for cid, key in prefer:
        c = by.get(cid)
        if c:
            add(c, key)
        if len(items) >= limit:
            return items
    for c in chips:
        if len(items) >= limit:
            break
        for key in ("d3y", "d1y", "d90", "d30"):
            if (c["id"], key) in seen:
                continue
            if add(c, key):
                break
    return items


def last_print_before(rows, venue, as_of):
    prior = [r for r in rows if r[0] < as_of and norm_venue((r[2] or {}).get("venue")) == venue]
    return prior[-1] if prior else None


def weighted_median(pairs):
    """pairs: (price, weight). Weights stay here."""
    if not pairs:
        return None
    rows = sorted((float(p), float(w)) for p, w in pairs if w > 0)
    if not rows:
        return None
    total = sum(w for _, w in rows)
    acc = 0.0
    for price, w in rows:
        acc += w
        if acc >= total / 2.0:
            return price
    return rows[-1][0]


def tape_print_for(chip, points, now):
    """Same-term constellation. n==1 → that print. No 'index' language."""
    disp = chip.get("display") or {}
    fam = term_family(disp.get("term"))
    if fam in ("token",) or disp.get("usd_per_gpu_hr") is None and disp.get("cny_per_gpu_hr") is None:
        if fam != "token" and disp.get("usd_per_gpu_hr") is None:
            return {"usd_per_gpu_hr": None, "n": 0, "term_family": fam, "as_of": fmt_date(now), "show": False}
    weights = _FAMILY_WEIGHTS.get(fam) or {}
    # Latest print per venue on this chip + term family (any config in family)
    latest = {}
    for p in points:
        if p.get("chip") != chip["id"]:
            continue
        if term_family(p.get("term")) != fam:
            continue
        if rejected(p.get("venue"), p.get("note") or ""):
            continue
        ven = norm_venue(p.get("venue"))
        if ven not in weights:
            # CoreWeave NA counts as CoreWeave for OD; keep distinct for spot if weighted
            if ven.startswith("CoreWeave") and "CoreWeave" in weights:
                ven_key = "CoreWeave"
            else:
                continue
        else:
            ven_key = ven
        dt = parse_date(p.get("date") or p.get("as_of"))
        price = p.get("price")
        if price is None or dt is None:
            continue
        prev = latest.get(ven_key)
        if prev is None or dt > prev[0]:
            latest[ven_key] = (dt, float(price), ven)

    # Circuit breaker: drop >25% jump vs own last print unless a second venue confirms
    confirmed_move = False
    jumps = []
    for ven_key, (dt, price, ven) in latest.items():
        rows = [
            (parse_date(p.get("date") or p.get("as_of")), float(p["price"]), p)
            for p in points
            if p.get("chip") == chip["id"]
            and term_family(p.get("term")) == fam
            and norm_venue(p.get("venue")) in (ven, ven_key)
            and p.get("price") is not None
            and parse_date(p.get("date") or p.get("as_of"))
        ]
        rows = [r for r in rows if r[0]]
        rows.sort(key=lambda x: x[0])
        prior = last_print_before(rows, ven, dt)
        if prior and prior[1] > 0 and abs(price / prior[1] - 1) > 0.25:
            jumps.append(ven_key)
    if len(jumps) >= 2:
        confirmed_move = True
    if jumps and not confirmed_move:
        for ven_key in jumps:
            latest.pop(ven_key, None)

    pairs = [(price, weights.get(ven_key, 1)) for ven_key, (_, price, _) in latest.items()]
    n = len(pairs)
    value = weighted_median(pairs) if n else None
    if value is not None:
        value = round(value, 3)
    return {
        "usd_per_gpu_hr": value,
        "n": n,
        "term_family": fam,
        "as_of": fmt_date(now),
        "show": n >= 2,
    }


def alt_1y(points, chip_id, term, now):
    """If display venue lacks a 1y pair, note another same-term venue that has one."""
    venues = {}
    for p in points:
        if p.get("chip") != chip_id:
            continue
        if term_family(p.get("term")) != term_family(term):
            continue
        venues.setdefault(norm_venue(p.get("venue")), norm_config(p.get("config")))
    found = []
    for ven, cfg in venues.items():
        pair = window_pair(series_for(points, chip_id, ven, term, cfg), now, 365, 21)
        if pair:
            found.append((ven, pair))
    return found


def tenor_slot(term):
    """Map a labeled quote term onto the 1m / 1q / 1y / 3y book. None = not a tenor."""
    t = (term or "").lower()
    if not t:
        return None
    if any(k in t for k in ("3y", "3-year", "36m", "36-month")):
        return "y3"
    if any(k in t for k in ("1cc", "1-click", "2w–1y", "2w-1y")):
        return "y1"
    if "1y monthly" in t or "cny monthly" in t:
        return "y1"
    if any(k in t for k in ("12m", "12-month", "1-year")) or t == "1y" or t.startswith("1y "):
        return "y1"
    if "reserved" in t and "spot" not in t:
        return "y1"
    if any(k in t for k in ("1q", "1-quarter", "3-month", "quarterly")):
        return "q1"
    if any(k in t for k in ("monthly lease", "monthly index", "1-month")) or t in ("1m", "1m contract"):
        return "m1"
    return None


def _term_priority(quote, slot):
    """Prefer current public reserved lists; never invent a rank to fill a dash."""
    v = (quote.get("venue") or "").lower()
    t = (quote.get("term") or "").lower()
    cfg = (quote.get("config") or "").lower()
    if slot == "y1":
        if "digitalocean" in v and ("12m" in t or "reserved" in t):
            return 0
        if "1cc" in t or "1-click" in t or "1cc" in cfg:
            # Prefer the 16-GPU 1-Click Cluster row.
            if "16" in cfg or "16" in (quote.get("note") or ""):
                return 1
            return 2
        if "semianalysis" in v and "1y" in t and "composite" not in t and "p25" not in t:
            return 3
        if v.startswith("gcp"):
            return 4
        if "smm" in v:
            return 5
        return 6
    return 5


def _quote_url(quote, sources):
    if quote.get("url"):
        return quote["url"]
    sid = quote.get("source_id")
    return ((sources or {}).get(sid) or {}).get("url") or None


def _term_label(quote, slot):
    v = quote.get("venue") or ""
    t = quote.get("term") or ""
    tl = t.lower()
    if "digitalocean" in v.lower() and ("12m" in tl or "reserved" in tl):
        return "DO 12m"
    if "1cc" in tl or "1-click" in tl:
        return "1CC 2w–1y"
    if "semianalysis" in v.lower():
        return "SA 1y · as_of 2026-03/04"
    if v.lower().startswith("gcp") and slot == "y3":
        return "GCP 3y"
    if v.lower().startswith("gcp"):
        return "GCP 1y"
    if "smm" in v.lower():
        return "SMM 1y"
    return t or slot


def _term_record(quote, sources, slot, primary=None):
    price = quote.get("usd_per_gpu_hr")
    cny = quote.get("cny_per_gpu_hr")
    if price is None and cny is None:
        return None
    is_cny = (
        quote.get("primary") == "CNY"
        or primary == "CNY"
        or (cny is not None and "smm" in (quote.get("venue") or "").lower())
    )
    rec = {
        "price": cny if (is_cny and cny is not None) else (price if price is not None else cny),
        "venue": quote.get("venue"),
        "term": quote.get("term"),
        "label": _term_label(quote, slot),
        "as_of": quote.get("as_of"),
        "url": _quote_url(quote, sources),
        "currency": "CNY" if (is_cny and cny is not None) else (quote.get("currency") or "USD"),
    }
    if cny is not None:
        rec["cny_per_gpu_hr"] = cny
    if price is not None:
        rec["usd_per_gpu_hr"] = price
    if quote.get("note"):
        rec["note"] = quote["note"]
    return rec


def attach_terms(chip, sources=None):
    """Fill terms.m1 / q1 / y1 / y3 from sourced quotes only. Missing tenor = null."""
    sources = sources or {}
    buckets = {k: [] for k in TERM_KEYS}
    for q in chip.get("quotes") or []:
        if rejected(q.get("venue"), q.get("note") or ""):
            continue
        if q.get("usd_per_gpu_hr") is None and q.get("cny_per_gpu_hr") is None:
            continue
        slot = tenor_slot(q.get("term"))
        if slot not in buckets:
            continue
        buckets[slot].append(q)
    # SMM 910C display is a 1y monthly print when quotes already carry it.
    disp = chip.get("display") or {}
    dslot = tenor_slot(disp.get("term"))
    if dslot in buckets and (disp.get("usd_per_gpu_hr") is not None or disp.get("cny_per_gpu_hr") is not None):
        if not any(
            (x.get("venue") == disp.get("venue") and x.get("term") == disp.get("term"))
            for x in buckets[dslot]
        ):
            buckets[dslot].append({**disp, "primary": disp.get("primary")})
    out = {}
    for slot in TERM_KEYS:
        cands = buckets[slot]
        if not cands:
            out[slot] = None
            continue
        cands = sorted(cands, key=lambda q: _term_priority(q, slot))
        rec = _term_record(cands[0], sources, slot, primary=(chip.get("display") or {}).get("primary"))
        out[slot] = rec
    chip["terms"] = out
    return chip


def enrich_chip(chip, points, now):
    disp = chip.get("display") or {}
    venue = disp.get("venue")
    term = disp.get("term")
    cfg = config_of(disp)
    chg = changes_for(points, chip["id"], venue, term, cfg, now)
    # Honest secondary 1y (e.g. CoreWeave B200 0%) lives in the title, not as a fake display %.
    if chg["d1y"].get("pct") is None:
        alts = [a for a in alt_1y(points, chip["id"], term, now) if a[0] != norm_venue(venue)]
        if alts:
            ven, pair = alts[0]
            sign = "+" if pair["pct"] > 0 else ""
            chg["d1y"]["title"] = (
                f"{venue} {term}: no print a year ago. "
                f"{ven} {pair.get('term') or term} 1y: {sign}{pair['pct']}% "
                f"(${pair['then']:g} → ${pair['now']:g})."
            )
            chg["d1y"]["alt_venue"] = ven
            chg["d1y"]["alt_pct"] = pair["pct"]
    rows = series_for(points, chip["id"], venue, term, cfg)
    pts = spark_points(rows)
    steps = spark_steps(pts)
    direction, wlab, wpct = spark_direction(chg, pts)
    if wlab is not None:
        sign = "+" if wpct > 0 else ""
        title = (
            f"Colored by {wlab} ({sign}{wpct:g}%). "
            "Step chart of dated prints. Carry-forward is for drawing only."
        )
    else:
        title = "Step chart of dated prints. Carry-forward is for drawing only."
    chip["changes"] = chg
    chip["spark"] = {
        "points": pts,
        "steps": steps,
        "direction": direction,
        "window": wlab,
        "svg": spark_svg(steps, direction=direction) if steps else "",
        "title": title,
    }
    # SA 1y drawer series (H100): labeled, stale, not today's OD %
    sa_rows = series_for(points, chip["id"], "SemiAnalysis", "1y contract", "1y-mid")
    if not sa_rows:
        sa_rows = series_for(points, chip["id"], "SemiAnalysis", "1y", "1y-mid")
    if sa_rows:
        sa_pts = spark_points(sa_rows)
        chip["spark_sa_1y"] = {
            "label": "SA 1y",
            "stale": True,
            "as_of": "2026-04",
            "points": sa_pts,
            "steps": spark_steps(sa_pts),
            "svg": spark_svg(
                spark_steps(sa_pts),
                direction="up" if sa_pts[-1]["price"] > sa_pts[0]["price"] else (
                    "down" if sa_pts[-1]["price"] < sa_pts[0]["price"] else "flat"
                ),
            ),
            "title": "SemiAnalysis 1y — last public period Apr 2026, STALE. Not today's on-demand %.",
        }
    chip["tape_print"] = tape_print_for(chip, points, now)
    return chip


SNAPSHOT_NOTE = "Last sourced confirm day, not the last price tick."


def _slot_config(slot, fallback="list"):
    return norm_config((slot or {}).get("config") or fallback)


def _confirm_index(points, day):
    """chip + venue + term + config → history point on `day`."""
    out = {}
    for p in points or []:
        if (p.get("date") or p.get("as_of")) != day:
            continue
        k = (p.get("chip"), norm_venue(p.get("venue")), p.get("term"), _slot_config(p))
        out[k] = p
    return out


def _confirm_key(chip_id, slot, fallback="list"):
    return (chip_id, norm_venue(slot.get("venue")), slot.get("term"), _slot_config(slot, fallback))


def _series_key(chip_id, venue, term):
    return (chip_id, norm_venue(venue), term)


def _num(value):
    if value is None:
        return None
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None


def _slot_price(slot):
    if not isinstance(slot, dict):
        return None
    for key in ("usd_per_gpu_hr", "cny_per_gpu_hr", "price"):
        got = _num(slot.get(key))
        if got is not None:
            return got
    return None


def _same_price(a, b):
    aa, bb = _num(a), _num(b)
    return aa is not None and aa == bb


def _price_tokens(value):
    """Dollar spellings already used in also-text and quote notes."""
    raw = f"{float(value):.3f}"
    stripped = raw.rstrip("0").rstrip(".")
    toks = {stripped, raw}
    two = f"{float(value):.2f}"
    if _num(two) == _num(value):
        toks.add(two)
    return toks


def _replace_price_token(text, old, new):
    if not text or old is None or new is None:
        return text
    new_s = f"{float(new):.3f}".rstrip("0").rstrip(".")
    out = text
    for tok in sorted(_price_tokens(old), key=len, reverse=True):
        out = out.replace(f"${tok}", f"${new_s}")
    return out


def _write_usd(slot, new_price):
    """Write a history price onto the USD fields the slot already has."""
    wrote = False
    for key in ("usd_per_gpu_hr", "price"):
        if slot.get(key) is not None and _num(slot.get(key)) is not None:
            slot[key] = new_price
            wrote = True
    if not wrote:
        slot["usd_per_gpu_hr"] = new_price
    return True


# Source notes that say "List page fetched …" and that the history note names
# on a full re-read. Other fetched dates (SA, TensorWave, token APIs) stay.
_REREAD_SOURCES = (
    ("lambda", "lambda"),
    ("coreweave", "coreweave"),
    ("crusoe", "crusoe"),
    ("digitalocean", "digitalocean"),
    ("gcp-tpu", "gcp tpu"),
    ("aws-cb", "aws cb"),
)
_FETCHED_RE = re.compile(r"List page fetched (\d{4}-\d{2}-\d{2})")


def _day_series(points, day):
    """chip + venue + term → confirm-day history points. Config is not part of the key."""
    out = {}
    for p in points or []:
        if (p.get("date") or p.get("as_of")) != day:
            continue
        if _num(p.get("price")) is None:
            continue
        key = _series_key(p.get("chip"), p.get("venue"), p.get("term"))
        out.setdefault(key, []).append(p)
    return out


def _prior_series_price(points, day):
    """Latest pre-day price of chip+venue+term, if that day has one price."""
    by_date = {}
    for p in points or []:
        dt = p.get("date") or p.get("as_of")
        if not dt or dt >= day:
            continue
        price = _num(p.get("price"))
        if price is None:
            continue
        key = _series_key(p.get("chip"), p.get("venue"), p.get("term"))
        by_date.setdefault(key, {}).setdefault(dt, set()).add(price)
    out = {}
    for key, dates in by_date.items():
        last = max(dates)
        prices = dates[last]
        if len(prices) == 1:
            out[key] = next(iter(prices))
    return out


def _stamp_as_of(slot, day, stamped_box):
    if slot.get("as_of") != day:
        slot["as_of"] = day
        stamped_box[0] += 1
    return True


def _refresh_snapshot_note(silicon, history):
    hist_note = (history.get("note") or "").strip()
    if hist_note:
        silicon["snapshot_note"] = f"{SNAPSHOT_NOTE} {hist_note}"
    elif not silicon.get("snapshot_note"):
        silicon["snapshot_note"] = SNAPSHOT_NOTE


def _refresh_fetched_notes(silicon, history, day):
    """Move list-page fetched dates up to the confirm day when history records the re-read.

    Does not touch sources the re-read clause does not name, and does not move
    a fetched date forward of the confirm day.
    """
    note = (history.get("note") or "").lower()
    if "full re-read" not in note:
        return
    clause = note.split("full re-read", 1)[1]
    for src in silicon.get("sources") or []:
        label = next((lab for sid, lab in _REREAD_SOURCES if sid == src.get("id")), None)
        if not label or label not in clause:
            continue
        old = src.get("note") or ""
        match = _FETCHED_RE.search(old)
        if not match or match.group(1) >= day:
            continue
        src["note"] = _FETCHED_RE.sub(f"List page fetched {day}", old, count=1)


def _priced_row(slot):
    return (
        isinstance(slot, dict)
        and slot.get("venue")
        and slot.get("term")
        and _slot_price(slot) is not None
    )


def apply_history_confirms(silicon, history):
    """Stamp slot as_of from history's last confirm day.

    A same-price confirm advances as_of even when the scrape config label
    disagrees with the slot (`list` / `cb` / `8x` vs `HGX 8x /8`, `trn2`,
    `us-east1`). Price is unchanged on a confirm.

    A price change is applied only when history already has exactly one
    confirm-day dollar for that chip + venue + term, every priced display/quote
    on that series still shares the previous dollar, and that previous dollar
    is the latest pre-day print. The new dollar is copied from history. It is
    not invented. Sibling SKUs that share a term but not a price (Lambda 1CC
    16 / 64 / 256) are left alone.
    """
    day = (history.get("as_of") or "").strip()
    if not day or not parse_date(day):
        return 0
    points = history.get("points") or []
    day_points = _day_series(points, day)
    prior = _prior_series_price(points, day)
    stamped_box = [0]

    def series_points(chip_id, slot):
        return day_points.get(_series_key(chip_id, slot.get("venue"), slot.get("term"))) or []

    for c in silicon.get("chips") or []:
        cid = c["id"]
        disp = c.get("display") or {}
        rows = []
        if _priced_row(disp):
            rows.append(disp)
        for q in c.get("quotes") or []:
            if _priced_row(q):
                rows.append(q)
        groups = {}
        for slot in rows:
            groups.setdefault(_series_key(cid, slot.get("venue"), slot.get("term")), []).append(slot)

        display_ok = False
        for key, group in groups.items():
            prints = day_points.get(key) or []
            if not prints:
                continue
            day_prices = {_num(p.get("price")) for p in prints}
            for slot in group:
                if any(_same_price(_slot_price(slot), p.get("price")) for p in prints):
                    _stamp_as_of(slot, day, stamped_box)
                    if slot is disp:
                        display_ok = True
            if any(
                slot.get("cny_per_gpu_hr") is not None and slot.get("usd_per_gpu_hr") is None
                for slot in group
            ):
                continue
            slot_prices = {_slot_price(slot) for slot in group}
            if len(day_prices) != 1 or len(slot_prices) != 1:
                continue
            new_price = next(iter(day_prices))
            old_price = next(iter(slot_prices))
            if old_price == new_price:
                continue
            if prior.get(key) != old_price:
                continue
            # Copy the history point's own number so JSON keeps its decimals.
            raw_new = next(p.get("price") for p in prints if _same_price(p.get("price"), new_price))
            for slot in group:
                if slot.get("note"):
                    slot["note"] = _replace_price_token(slot.get("note"), old_price, raw_new)
                _write_usd(slot, raw_new)
                _stamp_as_of(slot, day, stamped_box)
                if slot is disp:
                    display_ok = True
            also = c.get("also")
            if also and also.get("text"):
                also["text"] = _replace_price_token(also.get("text"), old_price, raw_new)

        for rec in (c.get("terms") or {}).values():
            if not _priced_row(rec):
                continue
            if any(_same_price(_slot_price(rec), p.get("price")) for p in series_points(cid, rec)):
                _stamp_as_of(rec, day, stamped_box)

        also = c.get("also")
        # `also` has no venue/term/config; it is the companion date on the display row.
        if display_ok and also and also.get("as_of") and also.get("as_of") != day:
            also["as_of"] = day
            stamped_box[0] += 1

        if display_ok and c.get("as_of") and c.get("as_of") != day:
            c["as_of"] = day
            stamped_box[0] += 1
        note = c.get("note")
        if display_ok and isinstance(note, str):
            if "Spots not re-fetched today" in note and any(
                p.get("chip") == cid
                and "spot" in (p.get("term") or "").lower()
                and (p.get("date") or p.get("as_of")) == day
                for p in points
            ):
                note = note.replace(" Spots not re-fetched today.", "").replace("Spots not re-fetched today.", "")
            if "Confirm vs 9 Sep" in note:
                dt = parse_date(day)
                if dt is not None:
                    note = note.replace("Confirm vs 9 Sep", f"Confirm vs {dt.day} {dt.strftime('%b')}")
                    # 1Q aged out of the ±10d window once the snapshot passed mid-September.
                    # The live pair on this tape is the 1M confirm.
                    note = note.replace("1Q is 0%", "1M is 0%")
            c["note"] = note.strip()

    prev = (silicon.get("updated") or silicon.get("snapshot") or "").strip()
    if not prev or day >= prev:
        silicon["updated"] = day
        silicon["snapshot"] = day
    _refresh_snapshot_note(silicon, history)
    _refresh_fetched_notes(silicon, history, day)
    return stamped_box[0]


def enrich_silicon(silicon, history):
    apply_history_confirms(silicon, history)
    now = parse_date(silicon.get("updated") or history.get("as_of")) or AS_OF
    harvested = harvest_quotes(silicon)
    history, appended = merge_history(history, harvested)
    points = history["points"]
    sources = {s["id"]: s for s in silicon.get("sources") or []}
    for c in silicon.get("chips") or []:
        enrich_chip(c, points, now)
        attach_terms(c, sources)
    silicon["weather"] = weather_items(silicon.get("chips") or [])
    return silicon, history, appended


def expected_grid_pcts(silicon, history):
    """Sanity checks for the honest grid numbers in the prompt."""
    now = parse_date(silicon.get("updated")) or AS_OF
    points = history["points"]
    checks = []

    def pct(chip_id, venue, term, cfg, key):
        chg = changes_for(points, chip_id, venue, term, cfg, now)
        return chg[key].get("pct")

    # Windows are anchored on the snapshot day. By 2026-10-09 the Aug 2025 H100
    # print is outside 365d ±21d, and the June prints are outside 90d ±10d.
    # 1M still pairs with the 9 Sep print.
    checks.append(("h100-90d", pct("nvidia-h100-sxm-80gb", "Lambda", "on-demand", "8x-sxm", "d90"), None))
    checks.append(("h100-1y", pct("nvidia-h100-sxm-80gb", "Lambda", "on-demand", "8x-sxm", "d1y"), None))
    checks.append(("h100-30d", pct("nvidia-h100-sxm-80gb", "Lambda", "on-demand", "8x-sxm", "d30"), 0.0))
    checks.append(("b200-90d", pct("nvidia-b200-sxm6", "Lambda", "on-demand", "8x-sxm", "d90"), None))
    checks.append(("b200-1y-lambda", pct("nvidia-b200-sxm6", "Lambda", "on-demand", "8x-sxm", "d1y"), None))
    checks.append(("b200-1y-cw", pct("nvidia-b200-sxm6", "CoreWeave", "on-demand", "list", "d1y"), None))
    checks.append(("a100-90d", pct("nvidia-a100-sxm-80gb", "Lambda", "on-demand", "8x-sxm", "d90"), None))
    checks.append(("cw-h100-1y", pct("nvidia-h100-sxm-80gb", "CoreWeave", "on-demand", "list", "d1y"), None))
    checks.append(("cw-h200-1y", pct("nvidia-h200-sxm-141gb", "CoreWeave", "on-demand", "list", "d1y"), None))
    checks.append(("h100-3y", pct("nvidia-h100-sxm-80gb", "Lambda", "on-demand", "8x-sxm", "d3y"), None))
    return checks


def expected_terms(silicon):
    by = {c["id"]: c for c in silicon.get("chips") or []}

    def price(cid, key):
        rec = ((by.get(cid) or {}).get("terms") or {}).get(key)
        if not rec:
            return None
        return rec.get("usd_per_gpu_hr", rec.get("price"))

    return [
        ("h100-y1-do", price("nvidia-h100-sxm-80gb", "y1"), 3.26),
        ("h100-m1", price("nvidia-h100-sxm-80gb", "m1"), None),
        ("h100-q1", price("nvidia-h100-sxm-80gb", "q1"), None),
        ("h100-y3", price("nvidia-h100-sxm-80gb", "y3"), None),
        ("h200-y1-do", price("nvidia-h200-sxm-141gb", "y1"), 3.40),
        ("b200-y1-1cc", price("nvidia-b200-sxm6", "y1"), 9.86),
        ("b300-y1-do", price("nvidia-b300-hgx", "y1"), 7.94),
        ("mi300-y1", price("amd-mi300x", "y1"), 1.91),
        ("mi325-y1", price("amd-mi325x", "y1"), 2.88),
        ("mi350-y1", price("amd-mi350x", "y1"), 4.76),
        ("mi355-y1", price("amd-mi355x", "y1"), None),
        ("gb200-y1", price("nvidia-gb200-nvl72", "y1"), None),
        ("tpuv7-y1", price("google-tpu-v7-ironwood", "y1"), 8.4),
        ("tpuv7-y3", price("google-tpu-v7-ironwood", "y3"), 5.4),
        ("a100-y1", price("nvidia-a100-sxm-80gb", "y1"), None),
    ]


def _confirm_self_check():
    """Config-label confirms stamp as_of. A unique history tick copies that dollar. Sibling SKUs do not."""
    silicon = {
        "updated": "2026-09-15",
        "snapshot": "2026-09-15",
        "snapshot_note": "Confirm day 2026-09-15",
        "sources": [
            {"id": "coreweave", "note": "List page fetched 2026-09-07."},
            {"id": "cerebras", "note": "Token / enterprise. Fetched 2026-08-18. No public accelerator-hour."},
        ],
        "chips": [
            {
                "id": "chip-a",
                "display": {
                    "venue": "CoreWeave",
                    "term": "on-demand",
                    "config": "list",
                    "usd_per_gpu_hr": 6.31,
                    "as_of": "2026-09-15",
                },
                "also": {"text": "AWS CB $12.355", "as_of": "2026-09-15"},
                "quotes": [
                    {
                        "venue": "CoreWeave",
                        "term": "on-demand",
                        "config": "list",
                        "usd_per_gpu_hr": 6.31,
                        "as_of": "2026-09-15",
                    },
                    {
                        "venue": "AWS",
                        "term": "Capacity Blocks",
                        "config": "cb",
                        "usd_per_gpu_hr": 12.355,
                        "as_of": "2026-09-15",
                        "note": "p6, $12.355 / accelerator-hr.",
                    },
                    {
                        "venue": "Lambda",
                        "term": "1CC 2w–1y",
                        "config": "1cc-16",
                        "usd_per_gpu_hr": 9.86,
                        "as_of": "2026-09-15",
                    },
                    {
                        "venue": "Lambda",
                        "term": "1CC 2w–1y",
                        "config": "1cc-256",
                        "usd_per_gpu_hr": 8.87,
                        "as_of": "2026-09-15",
                    },
                ],
            }
        ],
    }
    history = {
        "as_of": "2026-10-09",
        "note": (
            "Tape day 2026-10-09: 1 confirms, 1 ticks, 0 NEW. "
            "Full re-read Lambda/CoreWeave NA+EU/Crusoe/DigitalOcean/GCP TPU/AWS CB."
        ),
        "points": [
            {
                "chip": "chip-a",
                "venue": "CoreWeave",
                "term": "on-demand",
                "config": "HGX 8x /8",
                "price": 6.31,
                "date": "2026-10-09",
            },
            {
                "chip": "chip-a",
                "venue": "AWS",
                "term": "Capacity Blocks",
                "config": "p6-b200 US",
                "price": 12.355,
                "date": "2026-10-07",
            },
            {
                "chip": "chip-a",
                "venue": "AWS",
                "term": "Capacity Blocks",
                "config": "p6-b200 US",
                "price": 14.208,
                "date": "2026-10-09",
            },
            {
                "chip": "chip-a",
                "venue": "Lambda",
                "term": "1CC 2w–1y",
                "config": "256+-sxm",
                "price": 8.87,
                "date": "2026-10-09",
            },
        ],
    }
    apply_history_confirms(silicon, history)
    chip = silicon["chips"][0]
    quotes = chip["quotes"]
    assert chip["display"]["as_of"] == "2026-10-09", chip["display"]
    assert chip["display"]["usd_per_gpu_hr"] == 6.31
    assert quotes[0]["as_of"] == "2026-10-09" and quotes[0]["usd_per_gpu_hr"] == 6.31
    assert quotes[1]["usd_per_gpu_hr"] == 14.208 and quotes[1]["as_of"] == "2026-10-09", quotes[1]
    assert quotes[1]["note"] == "p6, $14.208 / accelerator-hr.", quotes[1]["note"]
    assert chip["also"]["text"] == "AWS CB $14.208", chip["also"]
    assert chip["also"]["as_of"] == "2026-10-09"
    assert quotes[2]["usd_per_gpu_hr"] == 9.86 and quotes[2]["as_of"] == "2026-09-15", quotes[2]
    assert quotes[3]["usd_per_gpu_hr"] == 8.87 and quotes[3]["as_of"] == "2026-10-09", quotes[3]
    assert silicon["sources"][0]["note"] == "List page fetched 2026-10-09."
    assert "2026-08-18" in silicon["sources"][1]["note"]
    assert "2026-09-15" not in silicon["snapshot_note"]
    assert "2026-10-09" in silicon["snapshot_note"]


if __name__ == "__main__":
    import json
    import os
    import sys

    _confirm_self_check()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    silicon = json.load(open(os.path.join(root, "silicon.json")))
    history = json.load(open(os.path.join(root, "silicon-history.json")))
    silicon, history, n = enrich_silicon(silicon, history)
    bad = []
    for name, got, exp in expected_grid_pcts(silicon, history):
        if got != exp:
            bad.append(f"{name}: got {got} expected {exp}")
    if bad:
        print("FAIL")
        print("\n".join(bad))
        sys.exit(1)
    wx = {f"{w['id']}:{w['window']}": w["pct"] for w in silicon.get("weather") or []}
    if wx.get("nvidia-h100-sxm-80gb:1M") != 0.0:
        sys.exit(f"weather H100 1M: {wx}")
    if wx.get("nvidia-b200-sxm6:1M") != 0.0:
        sys.exit(f"weather B200 1M: {wx}")
    for name, got, exp in expected_terms(silicon):
        if got != exp:
            bad.append(f"{name}: got {got} expected {exp}")
    if bad:
        print("FAIL")
        print("\n".join(bad))
        sys.exit(1)
    by = {c["id"]: c for c in silicon.get("chips") or []}
    day = history.get("as_of")
    if silicon.get("updated") != day or silicon.get("snapshot") != day:
        sys.exit(f"snapshot {silicon.get('updated')}/{silicon.get('snapshot')} != history {day}")
    h200_w = next((w for w in silicon.get("weather") or [] if w.get("id") == "nvidia-h200-sxm-141gb"), {})
    if day not in (h200_w.get("title") or ""):
        sys.exit(f"H200 weather still off the confirm day: {h200_w}")
    h100 = (by.get("nvidia-h100-sxm-80gb") or {}).get("display") or {}
    b200 = (by.get("nvidia-b200-sxm6") or {}).get("display") or {}
    if h100.get("usd_per_gpu_hr") != 3.99 or h100.get("as_of") != day:
        sys.exit(f"H100 display {h100}")
    if b200.get("usd_per_gpu_hr") != 6.69 or b200.get("as_of") != day:
        sys.exit(f"B200 display {b200}")
    sa = next(q for q in by["nvidia-h100-sxm-80gb"]["quotes"] if q.get("term") == "1y contract")
    if sa.get("as_of") != "2026-03" or sa.get("usd_per_gpu_hr") != 2.35:
        sys.exit(f"SA 1y must stay March 2026 STALE: {sa}")
    smm = (by.get("huawei-ascend-910c") or {}).get("display") or {}
    if smm.get("as_of") != "2026-07-29":
        sys.exit(f"SMM 910C as_of {smm.get('as_of')}")
    frozen = [
        "nvidia-h200-sxm-141gb",
        "nvidia-gb200-nvl72",
        "google-tpu-v7-ironwood",
        "nvidia-l40s-48gb",
        "google-tpu-v6e-trillium",
        "amazon-trainium2",
        "nvidia-gh200",
        "nvidia-rtx-pro-6000-blackwell",
        "google-tpu-v5p",
    ]
    for cid in frozen:
        disp = (by.get(cid) or {}).get("display") or {}
        if disp.get("as_of") != day:
            sys.exit(f"{cid} display still {disp.get('as_of')}: {disp}")
    aws_expect = {
        ("nvidia-b200-sxm6", "Capacity Blocks"): 14.208,
        ("nvidia-b300-hgx", "Capacity Blocks"): 16.146,
        ("nvidia-h100-sxm-80gb", "Capacity Blocks"): 5.97,
        ("nvidia-h200-sxm-141gb", "Capacity Blocks p5e"): 6.866,
        ("nvidia-h200-sxm-141gb", "Capacity Blocks p5en"): 7.895,
        ("nvidia-gb200-nvl72", "Capacity Blocks u-p6e-gb200x72"): 10.582,
        ("amazon-trainium2", "Capacity Blocks"): 2.235,
    }
    for (cid, term), px in aws_expect.items():
        slot = next(
            (
                q
                for q in (by[cid].get("quotes") or [])
                if q.get("venue") == "AWS" and q.get("term") == term
            ),
            by[cid].get("display") if (by[cid].get("display") or {}).get("term") == term else None,
        )
        if slot is None or slot.get("usd_per_gpu_hr") != px or slot.get("as_of") != day:
            sys.exit(f"AWS {cid} {term}: {slot}")
    b200_also = (by["nvidia-b200-sxm6"].get("also") or {}).get("text") or ""
    b300_also = (by["nvidia-b300-hgx"].get("also") or {}).get("text") or ""
    if "$12.355" in b200_also or "$14.208" not in b200_also:
        sys.exit(f"B200 also: {b200_also}")
    if "$14.04" in b300_also or "$16.146" not in b300_also:
        sys.exit(f"B300 also: {b300_also}")
    if "2026-09-15" in (silicon.get("snapshot_note") or "") or day not in (silicon.get("snapshot_note") or ""):
        sys.exit(f"snapshot_note: {silicon.get('snapshot_note')}")
    fetched = {s["id"]: s.get("note") or "" for s in silicon.get("sources") or []}
    for sid in ("lambda", "coreweave", "crusoe", "aws-cb", "gcp-tpu", "digitalocean"):
        if f"List page fetched {day}" not in fetched.get(sid, ""):
            sys.exit(f"{sid} fetched note: {fetched.get(sid)}")
    if "2026-08-18" not in fetched.get("cerebras", ""):
        sys.exit(f"cerebras note moved: {fetched.get('cerebras')}")
    print(f"ok · {len(history['points'])} dated points · harvested+{n}")
    for name, got, exp in expected_grid_pcts(silicon, history):
        print(f"  {name}: {got}")
    print("  weather", wx)
    for name, got, exp in expected_terms(silicon):
        print(f"  {name}: {got}")
