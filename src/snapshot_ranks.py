#!/usr/bin/env python3
# Append-only rank snapshots: silicon.json + data.json -> rank-history.json.
# Dated observed ranks only. Never interpolate a rank. Never invent a 7-day
# rank candle. Inference / Neoclouds / Hyperscalers are not on this tape.
import argparse
import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PT = ZoneInfo("America/Los_Angeles")

RULE = "dated observed rank snapshots only"
NOTE = (
    "Append-only. One snapshot per index per calendar date (America/Los_Angeles). "
    "Never interpolate. A weekday brief or a silicon.json / data.json publish "
    "writes today's row; a second run the same day replaces that date in place "
    "rather than duplicating. Inference, Neoclouds, and Hyperscalers are not "
    "on this tape until they have a published rank formula."
)
SILICON_FORMULA = "score = 0.40*liquidity + 0.35*demand + 0.25*frontier"
COUNTRIES_FORMULA = "CNW sort as published (Unlockable descending; r is the live rank)"
INDEX_ORDER = {"silicon": 0, "countries": 1}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")


def today_pt():
    return datetime.now(PT).date().isoformat()


def is_iso_date(s):
    if not s or not isinstance(s, str) or len(s) != 10:
        return False
    try:
        datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def resolve_date(silicon, date_arg=None, publish=False):
    """PT today, or silicon.json updated/snapshot when that is the publish date."""
    if date_arg:
        if not is_iso_date(date_arg):
            raise SystemExit(f"bad --date {date_arg!r}: need YYYY-MM-DD")
        return date_arg
    pub = (silicon.get("updated") or silicon.get("snapshot") or "").strip()
    if publish and is_iso_date(pub):
        return pub
    today = today_pt()
    if pub == today:
        return pub
    return today


def empty_history():
    return {
        "as_of": None,
        "rule": RULE,
        "note": NOTE,
        "snapshots": [],
    }


def load_history(path):
    if not os.path.exists(path):
        return empty_history()
    hist = load_json(path)
    if not isinstance(hist, dict):
        return empty_history()
    snaps = hist.get("snapshots")
    if not isinstance(snaps, list):
        snaps = []
    return {
        "as_of": hist.get("as_of"),
        "rule": RULE,
        "note": NOTE,
        "snapshots": snaps,
    }


def silicon_rows(silicon):
    rows = []
    for chip in silicon.get("chips") or []:
        rank = chip.get("rank")
        if rank is None:
            # Do not invent a rank for an unranked chip.
            continue
        display = chip.get("display") or {}
        rows.append({
            "id": chip.get("id"),
            "rank": rank,
            "score": chip.get("score"),
            "liquidity": chip.get("liquidity"),
            "demand": chip.get("demand"),
            "frontier": chip.get("frontier"),
            "display_usd": display.get("usd_per_gpu_hr"),
            "venue": display.get("venue"),
            "term": display.get("term"),
        })
    rows.sort(key=lambda r: (r["rank"] is None, r["rank"] if r["rank"] is not None else 0, r["id"] or ""))
    return rows


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def country_rows(data):
    # Published board default-sorts by Unlockable (u) descending. The # column
    # is that order. r in data.json is region — the live rank is the sort position.
    scored = []
    for c in data.get("countries") or []:
        i3 = c.get("i3")
        if not i3:
            continue
        scored.append(c)
    scored.sort(key=lambda c: (
        0 if _num(c.get("u")) is not None else 1,
        -(_num(c.get("u")) or 0),
        0 if _num(c.get("gdc")) is not None else 1,
        -(_num(c.get("gdc")) or 0),
        c.get("i3") or "",
    ))
    rows = []
    for i, c in enumerate(scored, start=1):
        rows.append({
            "id": c["i3"],
            "rank": i,
            "r": i,
            "t": c.get("t"),
            "u": c.get("u"),
            "gdc": c.get("gdc"),
            "re": c.get("re"),
            "rz": c.get("rz"),
        })
    return rows


def silicon_formula(silicon):
    raw = (silicon.get("rank_formula") or "").strip()
    if raw.startswith(SILICON_FORMULA):
        return SILICON_FORMULA
    return raw or SILICON_FORMULA


def make_snapshot(date, index, source, formula, rows):
    return {
        "date": date,
        "index": index,
        "source": source,
        "formula": formula,
        "rows": rows,
    }


def upsert(history, snapshots):
    """Replace any (date, index) already present; append the rest. Sort stably."""
    incoming = {(s["date"], s["index"]): s for s in snapshots}
    kept = [s for s in history.get("snapshots") or [] if (s.get("date"), s.get("index")) not in incoming]
    kept.extend(incoming[k] for k in incoming)
    kept.sort(key=lambda s: (s.get("date") or "", INDEX_ORDER.get(s.get("index"), 99), s.get("index") or ""))
    dates = [s["date"] for s in kept if s.get("date")]
    return {
        "as_of": max(dates) if dates else None,
        "rule": RULE,
        "note": NOTE,
        "snapshots": kept,
    }


def snapshot(root=None, date=None, publish=False):
    root = root or ROOT
    silicon = load_json(os.path.join(root, "silicon.json"))
    data = load_json(os.path.join(root, "data.json"))
    hist_path = os.path.join(root, "rank-history.json")
    history = load_history(hist_path)
    day = resolve_date(silicon, date_arg=date, publish=publish)
    snaps = [
        make_snapshot(day, "silicon", "silicon.json", silicon_formula(silicon), silicon_rows(silicon)),
        make_snapshot(day, "countries", "data.json", COUNTRIES_FORMULA, country_rows(data)),
    ]
    history = upsert(history, snaps)
    write_json(hist_path, history)
    return history, day


def main(argv=None):
    p = argparse.ArgumentParser(description="Upsert today's observed rank snapshots. Never interpolate.")
    p.add_argument("--date", help="ISO date override (YYYY-MM-DD). Do not use this to backfill invented ranks.")
    p.add_argument("--publish", action="store_true", help="Use silicon.json updated/snapshot as the date.")
    p.add_argument("--root", default=ROOT, help="Repo root (default: parent of this file).")
    args = p.parse_args(argv)
    history, day = snapshot(root=args.root, date=args.date, publish=args.publish)
    n_si = n_co = 0
    for s in history["snapshots"]:
        if s.get("date") != day:
            continue
        if s.get("index") == "silicon":
            n_si = len(s.get("rows") or [])
        elif s.get("index") == "countries":
            n_co = len(s.get("rows") or [])
    print(f"rank-history.json · {day} · silicon {n_si} · countries {n_co} · {len(history['snapshots'])} snapshots")
    return 0


if __name__ == "__main__":
    sys.exit(main())
