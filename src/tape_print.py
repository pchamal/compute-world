#!/usr/bin/env python3
# Dated-print hygiene for The Silicon Tape.
# Sleeve weights stay in this file. Do not print them on silicon.html / FAQ / llms.txt.
"""Tape Print + change windows from dated observed prints only.

A percent is computed only from two real same-chip, same-venue, same-term,
same-config-family prints. Carry-forward is for sparkline *drawing* only.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

AS_OF = date(2026, 8, 18)
WINDOWS = {"d30": (30, 5), "d90": (90, 10), "d1y": (365, 21)}
DASH_TITLE = "US list prices do not tick daily. 7d lights up after a week of our own scrape."

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
    ("1y", ("1y", "1-year", "12m", "12-month", "reserved")),
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
        "d30": {"pct": None, "title": "No dated pair in the 30-day window (±5d)."},
        "d90": {"pct": None, "title": "No dated pair in the 90-day window (±10d)."},
        "d1y": {"pct": None, "title": "No dated pair in the 1-year window (365d ±21d)."},
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


def spark_svg(steps, width=88, height=26, up=True):
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
    # Step path: horizontal then vertical
    d = [f"M{xs[0]:.1f},{ys[0]:.1f}"]
    for i in range(1, len(steps)):
        d.append(f"H{xs[i]:.1f}")
        d.append(f"V{ys[i]:.1f}")
    cls = "spark"
    if prices[-1] > prices[0]:
        cls = "spark spark-up"
    elif prices[-1] < prices[0]:
        cls = "spark spark-dn"
    return (
        f'<svg class="{cls}" viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="1.4" '
        f'stroke-linejoin="miter" stroke-linecap="butt" d="{" ".join(d)}"/></svg>'
    )


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
    up = True
    if pts and pts[-1]["price"] < pts[0]["price"]:
        up = False
    chip["changes"] = chg
    chip["spark"] = {
        "points": pts,
        "steps": steps,
        "svg": spark_svg(steps, up=up) if steps else "",
        "title": "Step chart of dated prints. Carry-forward is for drawing only.",
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
            "svg": spark_svg(spark_steps(sa_pts), up=sa_pts[-1]["price"] >= sa_pts[0]["price"]),
            "title": "SemiAnalysis 1y — last public period Apr 2026, STALE. Not today's on-demand %.",
        }
    chip["tape_print"] = tape_print_for(chip, points, now)
    return chip


def enrich_silicon(silicon, history):
    now = parse_date(silicon.get("updated") or history.get("as_of")) or AS_OF
    harvested = harvest_quotes(silicon)
    history, appended = merge_history(history, harvested)
    points = history["points"]
    for c in silicon.get("chips") or []:
        enrich_chip(c, points, now)
    return silicon, history, appended


def expected_grid_pcts(silicon, history):
    """Sanity checks for the honest grid numbers in the prompt."""
    now = parse_date(silicon.get("updated")) or AS_OF
    points = history["points"]
    checks = []

    def pct(chip_id, venue, term, cfg, key):
        chg = changes_for(points, chip_id, venue, term, cfg, now)
        return chg[key].get("pct")

    checks.append(("h100-90d", pct("nvidia-h100-sxm-80gb", "Lambda", "on-demand", "8x-sxm", "d90"), 0.0))
    checks.append(("h100-1y", pct("nvidia-h100-sxm-80gb", "Lambda", "on-demand", "8x-sxm", "d1y"), 33.4))
    checks.append(("h100-30d", pct("nvidia-h100-sxm-80gb", "Lambda", "on-demand", "8x-sxm", "d30"), None))
    checks.append(("b200-90d", pct("nvidia-b200-sxm6", "Lambda", "on-demand", "8x-sxm", "d90"), 0.0))
    checks.append(("b200-1y-lambda", pct("nvidia-b200-sxm6", "Lambda", "on-demand", "8x-sxm", "d1y"), None))
    checks.append(("b200-1y-cw", pct("nvidia-b200-sxm6", "CoreWeave", "on-demand", "list", "d1y"), 0.0))
    checks.append(("a100-90d", pct("nvidia-a100-sxm-80gb", "Lambda", "on-demand", "8x-sxm", "d90"), 0.0))
    checks.append(("cw-h100-1y", pct("nvidia-h100-sxm-80gb", "CoreWeave", "on-demand", "list", "d1y"), 0.0))
    checks.append(("cw-h200-1y", pct("nvidia-h200-sxm-141gb", "CoreWeave", "on-demand", "list", "d1y"), 0.0))
    return checks


if __name__ == "__main__":
    import json
    import os
    import sys

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
    print(f"ok · {len(history['points'])} dated points · harvested+{n}")
    for name, got, exp in expected_grid_pcts(silicon, history):
        print(f"  {name}: {got}")
