#!/usr/bin/env python3
# Capacity book: capacity.json + campuses.json rollup -> capacity.html + capacity.xml.
# Run from repo root or src/:  python3 src/build_capacity.py
# Do not invent MW, GPU counts, or EV multiples. Pins and filings stay in their own grain.
import json
import html
import os
from collections import Counter
from datetime import datetime

from fnav import css as fnav_css, markup as fnav_markup, script as fnav_script
from seo import og_block, breadcrumb_ld, person_author, org_publisher, nice_day
from desk_chrome import MARKET_THEME_CSS, SITE, cite_line

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

METRIC_KEYS = (
    "live_mw",
    "contracted_mw",
    "construction_mw",
    "pipeline_mw",
    "secured_mw",
    "deployed_gpus",
)
REQUIRED_COMPANY = ("id", "name", "ticker", "cik", "archetype")
ARCHETYPES = {"neocloud", "miner_ai", "colo", "ground_up", "other"}
STATUSES = {"reported", "calculated", "estimated", "undisclosed"}
LAYERS = {"it_capacity", "facility_power", "secured_utility", "unspecified", None}
SOURCE_LABELS = {"10-Q", "10-K", "8-K", "20-F", "6-K", "IR", "press", None}
COUNT_STATUSES = {"reported", "calculated"}
GRAIN_LABEL = {
    "it_capacity": "IT capacity",
    "facility_power": "facility power",
    "interconnection_request": "interconnection request",
    "not_disclosed": "not disclosed",
    "secured_utility": "secured utility",
    "unspecified": "unspecified",
}
STATUS_CAMPUS = {
    "announced": "announced",
    "in_progress": "in progress",
    "operational": "operational",
    "paused": "paused",
    "canceled": "canceled",
    "undisclosed": "undisclosed",
}
ARCHETYPE_LABEL = {
    "neocloud": "Neocloud",
    "miner_ai": "Miner → AI",
    "colo": "Colo",
    "ground_up": "Ground-up",
    "other": "Other",
}


def load_book(path=None):
    path = path or os.path.join(ROOT, "capacity.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_campuses(path=None):
    path = path or os.path.join(ROOT, "campuses.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def validate_metric(company_id, key, field):
    if not isinstance(field, dict):
        raise ValueError(f"{company_id}.{key} must be an object")
    required = (
        "value",
        "unit",
        "power_layer",
        "status",
        "as_of",
        "quote",
        "source_url",
        "source_label",
    )
    missing = [k for k in required if k not in field]
    if missing:
        raise ValueError(f"{company_id}.{key} missing {missing}")
    status = field["status"]
    if status not in STATUSES:
        raise ValueError(f"{company_id}.{key} bad status {status}")
    if field["power_layer"] not in LAYERS:
        raise ValueError(f"{company_id}.{key} bad power_layer {field['power_layer']}")
    if field["source_label"] not in SOURCE_LABELS:
        raise ValueError(f"{company_id}.{key} bad source_label {field['source_label']}")
    unit = field["unit"]
    if key == "deployed_gpus":
        if unit != "GPUs":
            raise ValueError(f"{company_id}.{key} unit must be GPUs")
    elif unit != "MW":
        raise ValueError(f"{company_id}.{key} unit must be MW")
    value = field["value"]
    if status == "undisclosed":
        if value is not None:
            raise ValueError(f"{company_id}.{key} undisclosed must have value null")
        return
    if value is None:
        raise ValueError(f"{company_id}.{key} {status} needs a numeric value")
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{company_id}.{key} value must be a number")
    quote = field.get("quote") or ""
    if not field.get("source_url") or not quote or not field.get("as_of"):
        raise ValueError(f"{company_id}.{key} non-null value needs source_url + quote + as_of")
    if len(quote) > 200:
        raise ValueError(f"{company_id}.{key} quote exceeds 200 chars")
    if not str(field["source_url"]).startswith("https://"):
        raise ValueError(f"{company_id}.{key} source_url must be https")


def validate_book(book):
    for key in ("as_of", "updated", "note", "companies"):
        if key not in book:
            raise ValueError(f"capacity.json missing {key}")
    companies = book["companies"]
    if not isinstance(companies, list) or not (15 <= len(companies) <= 25):
        raise ValueError(f"expected 15–25 companies, got {len(companies)}")
    seen = set()
    for c in companies:
        for key in REQUIRED_COMPANY:
            if key not in c:
                raise ValueError(f"company missing {key}")
        if c["id"] in seen:
            raise ValueError(f"duplicate id {c['id']}")
        seen.add(c["id"])
        if c["archetype"] not in ARCHETYPES:
            raise ValueError(f"{c['id']} bad archetype {c['archetype']}")
        for key in METRIC_KEYS:
            if key not in c:
                raise ValueError(f"{c['id']} missing {key}")
            validate_metric(c["id"], key, c[key])
    return True


def counts_in_totals(field):
    return (
        field
        and field.get("value") is not None
        and field.get("status") in COUNT_STATUSES
        and field.get("unit") == "MW"
    )


def portfolio_totals(companies):
    totals = {k: 0.0 for k in METRIC_KEYS if k != "deployed_gpus"}
    included = {k: 0 for k in totals}
    for c in companies:
        for key in totals:
            field = c.get(key) or {}
            if counts_in_totals(field):
                totals[key] += float(field["value"])
                included[key] += 1
    return {
        key: {"mw": totals[key], "n": included[key]}
        for key in totals
    }


def campus_rollup(campuses):
    projects = campuses.get("projects") or []
    by_op = {}
    for p in projects:
        op = p.get("operator") or "undisclosed"
        row = by_op.setdefault(
            op,
            {
                "operator": op,
                "pins": 0,
                "mw_sum": 0.0,
                "mw_pins": 0,
                "grains": Counter(),
                "grain_mw": Counter(),
                "statuses": Counter(),
            },
        )
        row["pins"] += 1
        row["statuses"][p.get("status") or "undisclosed"] += 1
        grain = p.get("mw_grain") or "not_disclosed"
        row["grains"][grain] += 1
        mw = p.get("mw")
        if isinstance(mw, (int, float)) and not isinstance(mw, bool):
            row["mw_sum"] += float(mw)
            row["mw_pins"] += 1
            row["grain_mw"][grain] += float(mw)
    rows = sorted(by_op.values(), key=lambda r: (-r["mw_sum"], -r["pins"], r["operator"].lower()))
    return {
        "as_of": campuses.get("as_of"),
        "n_pins": len(projects),
        "n_operators": len(rows),
        "operators": rows,
        "thin": len(projects) < 80,
    }


def fmt_mw(value, unit="MW"):
    if value is None:
        return "—"
    n = float(value)
    if unit == "GPUs":
        if n >= 1000 and abs(n - round(n)) < 1e-9:
            return f"{int(round(n)):,} GPUs"
        return f"{n:g} GPUs"
    if abs(n - round(n)) < 1e-9:
        n = int(round(n))
        if n >= 1000 and n % 1000 == 0:
            return f"{n // 1000} GW"
        return f"{n:,} MW"
    if n >= 1000:
        g = n / 1000
        s = f"{g:.2f}".rstrip("0").rstrip(".")
        return f"{s} GW"
    s = f"{n:.2f}".rstrip("0").rstrip(".")
    return f"{s} MW"


def live_sort_value(company):
    field = company.get("live_mw") or {}
    if field.get("value") is None:
        return float("-inf")
    return float(field["value"])


def cell_payload(field):
    return {
        "value": field.get("value"),
        "unit": field.get("unit"),
        "status": field.get("status"),
        "power_layer": field.get("power_layer"),
        "as_of": field.get("as_of"),
        "quote": field.get("quote"),
        "source_url": field.get("source_url"),
        "source_label": field.get("source_label"),
        "display": fmt_mw(field.get("value"), field.get("unit") or "MW")
        if field.get("status") != "undisclosed"
        else "—",
    }


def build(book=None, campuses=None, dest_html=None, dest_xml=None):
    book = book if book is not None else load_book()
    campuses = campuses if campuses is not None else load_campuses()
    validate_book(book)
    companies = list(book["companies"])
    companies.sort(key=live_sort_value, reverse=True)
    totals = portfolio_totals(companies)
    rollup = campus_rollup(campuses)
    updated = book["updated"]
    nice_upd = nice_day(updated)
    nice_short = nice_day(updated, "short")
    cite = cite_line("Capacity", f"{SITE}/capacity.html", updated)

    page_cos = []
    for c in companies:
        metrics = {k: cell_payload(c[k]) for k in METRIC_KEYS}
        page_cos.append(
            {
                "id": c["id"],
                "name": c["name"],
                "ticker": c.get("ticker"),
                "cik": c.get("cik"),
                "archetype": c["archetype"],
                "notes": c.get("notes") or "",
                "live_sort": live_sort_value(c),
                "metrics": metrics,
            }
        )

    def agg_html(key, label):
        row = totals[key]
        return (
            f'<article class="agg">'
            f'<div class="k">{html.escape(label)}</div>'
            f"<b>{html.escape(fmt_mw(row['mw']))}</b>"
            f'<div class="n">{row["n"]} companies counted</div>'
            f"</article>"
        )

    aggs = "".join(
        [
            agg_html("live_mw", "Live"),
            agg_html("contracted_mw", "Contracted"),
            agg_html("construction_mw", "Construction"),
            agg_html("pipeline_mw", "Pipeline"),
            agg_html("secured_mw", "Secured"),
        ]
    )

    def status_class(st):
        return {
            "reported": "st-rep",
            "calculated": "st-cal",
            "estimated": "st-est",
            "undisclosed": "st-und",
        }.get(st, "st-und")

    def metric_cell(cid, key, field):
        st = field["status"]
        lab = {
            "reported": "reported",
            "calculated": "calculated",
            "estimated": "estimated",
            "undisclosed": "undisclosed",
        }[st]
        shown = "—" if st == "undisclosed" else fmt_mw(field.get("value"), field.get("unit") or "MW")
        return (
            f'<td class="num {status_class(st)}" data-col="{html.escape(key)}" '
            f'data-status="{html.escape(st)}">'
            f'<button type="button" class="mw" data-open="{html.escape(cid)}" '
            f'data-metric="{html.escape(key)}">{html.escape(shown)}'
            f'<span class="sym">{html.escape(lab)}</span></button></td>'
        )

    rows = []
    for c in companies:
        live = c["live_mw"]
        live_n = live["value"] if live.get("value") is not None else ""
        tick = html.escape(c["ticker"]) if c.get("ticker") else "private"
        rows.append(
            f'<tr id="{html.escape(c["id"])}" class="caprow" data-id="{html.escape(c["id"])}" '
            f'data-name="{html.escape(c["name"].lower())}" data-live="{live_n}" '
            f'data-archetype="{html.escape(c["archetype"])}">'
            f'<td><button type="button" class="cn" data-open="{html.escape(c["id"])}">'
            f'{html.escape(c["name"])}</button>'
            f'<span class="tick">{tick} · {html.escape(ARCHETYPE_LABEL[c["archetype"]])}</span></td>'
            + "".join(metric_cell(c["id"], k, c[k]) for k in METRIC_KEYS if k != "deployed_gpus")
            + "</tr>"
        )
    table_rows = "\n".join(rows)

    roll_rows = []
    for r in rollup["operators"]:
        grains = ", ".join(
            f"{GRAIN_LABEL.get(g, g)} {fmt_mw(mw)}"
            for g, mw in sorted(r["grain_mw"].items(), key=lambda kv: -kv[1])
        ) or "no numeric MW"
        mix = ", ".join(
            f"{n} {STATUS_CAMPUS.get(s, s)}"
            for s, n in r["statuses"].most_common()
        )
        mw_bit = fmt_mw(r["mw_sum"]) if r["mw_pins"] else "—"
        roll_rows.append(
            f"<tr>"
            f"<td>{html.escape(r['operator'])}</td>"
            f"<td class='num'>{r['pins']}</td>"
            f"<td class='num'>{html.escape(mw_bit)}</td>"
            f"<td>{html.escape(grains)}</td>"
            f"<td>{html.escape(mix)}</td>"
            f"</tr>"
        )
    campus_table = "\n".join(roll_rows)
    thin_note = (
        "This register is thin: named pins, not a census. Empty operator rows are coverage holes, not a load of zero."
        if rollup["thin"]
        else "Named pins only. Energized MW is almost never published."
    )
    grain_totals = Counter()
    for r in rollup["operators"]:
        grain_totals.update(r["grain_mw"])
    grain_line = ", ".join(
        f"{GRAIN_LABEL.get(g, g)} {fmt_mw(mw)}"
        for g, mw in grain_totals.most_common()
    ) or "no numeric MW on the pins"

    payload = json.dumps(
        {
            "as_of": book["as_of"],
            "updated": book["updated"],
            "note": book["note"],
            "companies": page_cos,
            "totals": totals,
            "campus": {
                "as_of": rollup["as_of"],
                "n_pins": rollup["n_pins"],
                "n_operators": rollup["n_operators"],
                "thin": rollup["thin"],
            },
        },
        ensure_ascii=False,
    )

    ld = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "Dataset",
            "name": "Capacity",
            "description": (
                "Desk-curated company megawatt book for public AI-infra filers, "
                "sourced from SEC EDGAR and official IR. Not a comps product."
            ),
            "url": f"{SITE}/capacity.html",
            "dateModified": updated,
            "datePublished": updated,
            "creator": person_author(),
            "author": person_author(),
            "publisher": org_publisher(),
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "isAccessibleForFree": True,
            "variableMeasured": "Issuer-disclosed live, contracted, construction, pipeline, and secured MW",
            "distribution": {
                "@type": "DataDownload",
                "encodingFormat": "application/json",
                "contentUrl": f"{SITE}/capacity.json",
            },
            "citation": cite,
        },
        ensure_ascii=False,
    )
    crumb = json.dumps(
        breadcrumb_ld(
            [
                ("compute.world", f"{SITE}/"),
                ("Capacity", f"{SITE}/capacity.html"),
            ]
        ),
        ensure_ascii=False,
    )
    og = og_block(
        "Capacity · compute.world",
        "Power is the denominator. Company MW from SEC EDGAR and official IR — not a scrape, not EV/MW.",
        f"{SITE}/capacity.html",
        "og.png",
        og_type="article",
        image_alt="Capacity — issuer-disclosed company MW, compute.world",
    )

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#F3F5F2">
<script>(function(){{try{{var t=localStorage.getItem("cnw_theme");if(t!=="dark"&&t!=="light"){{var h=new Date().getHours();t=(h>=19||h<7)?"dark":"light";}}document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();</script>
<title>Capacity · compute.world</title>
<meta name="description" content="Company megawatt book for public AI-infra filers. Desk-sourced from SEC EDGAR and official IR. Power is the denominator. No EV/MW.">
<link rel="canonical" href="{SITE}/capacity.html">
<meta name="robots" content="index,follow,max-image-preview:large">
{og}
<link rel="alternate" type="application/rss+xml" title="Capacity · compute.world" href="{SITE}/capacity.xml">
<link rel="icon" href="/mark.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<script type="application/ld+json">{ld}</script>
<script type="application/ld+json">{crumb}</script>
<style>
{MARKET_THEME_CSS}
:root{{--paper:#F3F5F2;--ink:#1B222A;--muted:#4E5862;--faint:#7C8690;--rule:#D8DED9;--rule2:#1B222A;
--accent:#1F4FD8;--tint:#F6F8F5;--pr:#1E7B4F;--sg:#8A5A12;
--glass:rgba(243,245,242,.78);--glassborder:rgba(27,34,42,.22);
--serif:"Newsreader",Georgia,"Times New Roman",serif;
--sans:"Schibsted Grotesk",ui-sans-serif,system-ui,sans-serif}}
html[data-theme="dark"]{{--paper:#0F1216;--ink:#E9EDF1;--muted:#AAB4BE;--faint:#7E8893;--rule:#2A323B;
--rule2:#E9EDF1;--accent:#6C8FF0;--tint:#1B2129;--pr:#4FBF86;--sg:#E0B060;
--glass:rgba(15,18,22,.78);--glassborder:rgba(233,237,241,.22)}}
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
@media(max-width:760px){{.tchip{{top:12px;width:40px;height:40px}}}}
{fnav_css()}
body{{transition:background-color .35s ease,color .35s ease}}
*{{margin:0;padding:0;box-sizing:border-box}}
html{{background:var(--paper)}}
body{{background:var(--paper);color:var(--ink);font-family:var(--serif);font-size:17px;line-height:1.62;-webkit-font-smoothing:antialiased}}
a{{color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(31,79,216,.35)}}
a:hover{{border-bottom-color:var(--accent)}}
.wrap{{max-width:1180px;margin:0 auto;padding:0 28px}}
.masthead{{padding:34px 0 0;text-align:center}}
.masthead .name{{font-size:15px;letter-spacing:.34em;text-transform:uppercase;font-family:var(--sans)}}
.masthead .name a{{border:none;color:var(--ink)}}
.masthead .name b{{font-weight:600}}
.masthead .sub{{margin-top:8px;font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-family:var(--sans)}}
.mastrule{{margin-top:20px;border-top:2px solid var(--rule2);border-bottom:1px solid var(--rule2);height:5px}}
.lede{{padding:48px 0 8px}}
h1{{font-weight:400;font-size:clamp(28px,4.4vw,40px);line-height:1.16}}
h1 em{{font-style:italic}}
.standfirst{{margin-top:18px;font-size:17.5px;color:var(--muted);max-width:820px}}
.standfirst b{{color:var(--ink);font-weight:600}}
.subrow{{display:flex;flex-wrap:wrap;gap:8px 26px;align-items:baseline;margin:26px 0 0;padding:16px 0;border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule);font-size:13px;letter-spacing:.1em;text-transform:uppercase;font-family:var(--sans)}}
.subrow .lab{{color:var(--faint);font-size:11px;letter-spacing:.16em}}
.aggs{{margin:28px 0 8px;display:grid;grid-template-columns:repeat(5,1fr);gap:0 22px}}
.aggs .k{{font-family:var(--sans);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--faint);margin-bottom:6px}}
.agg{{padding:14px 0;border-top:1px solid var(--rule)}}
.agg b{{font-weight:400;font-size:26px;letter-spacing:-.02em}}
.agg .n{{margin-top:6px;font-size:12.5px;color:var(--muted)}}
.legend{{margin:22px 0 8px;padding:14px 16px;border:1px dashed var(--rule);border-radius:8px;font-size:14.5px;color:var(--muted)}}
.legend b{{color:var(--ink);font-weight:600}}
.badge{{display:inline-block;font-family:var(--sans);font-size:11px;letter-spacing:.08em;text-transform:uppercase;margin:0 2px}}
.reg{{margin:36px 0 0}}
.reg h2,.campus h2,.notes h2{{font-weight:400;font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:0 0 12px;font-family:var(--sans)}}
.scroll{{overflow:auto}}
table{{width:100%;border-collapse:collapse;font-size:14.5px}}
th{{text-align:left;font-weight:400;font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);
padding:8px 10px 8px 0;border-bottom:1px solid var(--rule2);white-space:nowrap;font-family:var(--sans)}}
th[data-sort]{{cursor:pointer}}
th.sorted{{color:var(--ink)}}
td{{padding:10px 12px 10px 0;border-bottom:1px solid var(--rule);vertical-align:top;color:var(--muted)}}
td.num{{font-variant-numeric:tabular-nums;white-space:nowrap}}
.cn,.mw{{font-family:inherit;background:none;border:none;border-bottom:1px solid rgba(31,79,216,.35);color:var(--accent);
cursor:pointer;text-align:left;padding:0}}
.cn{{font-size:15px}}.mw{{font-size:14.5px}}
.cn:hover,.mw:hover{{border-bottom-color:var(--accent)}}
.tick{{display:block;font-size:12px;color:var(--faint);margin-top:2px}}
.sym{{display:block;font-family:var(--sans);font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:var(--faint);margin-top:2px;border:none}}
.st-est .mw{{color:var(--sg)}}
.campus{{margin:48px 0 0;padding-top:22px;border-top:2px solid var(--rule2)}}
.campus p{{color:var(--muted);font-size:15.5px;margin:0 0 14px;max-width:820px}}
.notes{{margin:48px 0 0;border-top:2px solid var(--rule2);padding-top:22px}}
.notes p,.notes ul{{color:var(--muted);font-size:15px;margin:0 0 12px}}
.notes ul{{margin-left:18px}}
.notes li{{margin:0 0 6px}}
.colophon{{margin-top:56px;border-top:2px solid var(--rule2);padding:24px 0 56px;text-align:center}}
.colophon .c1{{font-size:12px;letter-spacing:.3em;text-transform:uppercase;font-family:var(--sans)}}
.colophon .c2{{margin-top:10px;font-size:12.5px;color:var(--muted)}}
#scrim{{position:fixed;inset:0;background:rgba(23,22,20,.28);opacity:0;pointer-events:none;z-index:80;transition:opacity .3s ease}}
#scrim.on{{opacity:1;pointer-events:auto}}
html[data-theme="dark"] #scrim{{background:rgba(0,0,0,.45)}}
#drawer{{position:fixed;top:0;right:0;height:100%;width:min(520px,100%);background:var(--paper);color:var(--ink);
z-index:90;transform:translateX(104%);transition:transform .4s cubic-bezier(.22,.8,.26,1);
box-shadow:-18px 0 50px rgba(0,0,0,.16);overflow:auto;padding:28px 28px 48px}}
#drawer.on{{transform:none}}
#drawer h2{{font-weight:400;font-size:26px;line-height:1.2;margin:6px 0 4px}}
#drawer .dv{{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-family:var(--sans)}}
#drawer .dclose{{position:absolute;top:16px;right:18px;background:none;border:none;font:inherit;font-size:13px;
letter-spacing:.12em;text-transform:uppercase;color:var(--muted);cursor:pointer;font-family:var(--sans)}}
#drawer .dclose:hover{{color:var(--accent)}}
#drawer .dmeta{{display:flex;flex-wrap:wrap;gap:8px 18px;margin:14px 0 18px;padding:12px 0;border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule);font-size:13px;color:var(--muted)}}
#drawer .dmeta b{{color:var(--ink);font-weight:600}}
#drawer blockquote{{margin:0 0 14px;padding:0 0 0 14px;border-left:2px solid var(--rule2);color:var(--ink);font-size:15.5px}}
#drawer p{{font-size:14.5px;color:var(--muted);margin:0 0 10px}}
#drawer p b{{color:var(--ink)}}
@media(max-width:900px){{.aggs{{grid-template-columns:1fr 1fr}} .wrap{{padding:0 18px}}}}
@media(max-width:760px){{.lede{{padding:36px 0 8px}} .aggs{{grid-template-columns:1fr}}}}
@media(prefers-reduced-motion:reduce){{#drawer,#scrim{{transition:none}}}}
</style>
</head>
<body class="fnav-inner">
<button id="themetog" class="tchip" aria-label="Switch to night mode" title="Day / Night">
  <svg class="ic-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>
  <svg class="ic-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.9 1.9M19.1 4.9l-1.8 1.8M6.7 17.3l-1.9 1.9"/></svg>
</button>
{fnav_markup("capacity")}
<div class="wrap">
  <div class="masthead">
    <div class="name"><a href="/"><b>COMPUTE</b>.WORLD</a></div>
    <div class="sub">Capacity · issuer MW · the world's compute &amp; silicon index · {nice_upd}</div>
    <div class="mastrule"></div>
  </div>

  <div class="lede">
    <h1>Power is the <em>denominator</em>.</h1>
    <p class="standfirst">A company-level megawatt book for public AI-infra, miner-to-AI, and colo filers. Every printed number was folded from <b>SEC EDGAR</b> or official IR — not from a third-party comps table, and not from density math. Live, contracted, construction, pipeline, and secured are different states of the same word. They do not add.</p>
    <div class="subrow">
      <span class="lab">Issuer book</span>
      <span>{nice_short}</span>
      <span>{len(companies)} companies</span>
      <a href="/capacity.json">capacity.json</a>
      <a href="/neoclouds.html">Neoclouds</a>
      <a href="/campuses.html">Campuses</a>
      <a href="/contact.html">The Desk</a>
    </div>
  </div>

  <section class="aggs" aria-label="Portfolio totals">
{aggs}
  </section>
  <p class="legend"><b>How to read the totals.</b> Sums count only cells marked <span class="badge">reported</span> or <span class="badge">calculated</span>. <span class="badge">estimated</span> stays out of the portfolio math. <span class="badge">undisclosed</span> is an em dash, never a silent zero. Click a cell for the filing quote and the URL.</p>

  <section class="reg" aria-labelledby="book-h">
    <h2 id="book-h">Issuer-disclosed capacity</h2>
    <div class="scroll">
    <table id="cap">
      <thead><tr>
        <th data-sort="name" data-type="str">Company <span class="arr"></span></th>
        <th data-sort="live" data-type="num" class="sorted">Live MW <span class="arr">▼</span></th>
        <th>Contracted</th>
        <th>Construction</th>
        <th>Pipeline</th>
        <th>Secured</th>
      </tr></thead>
      <tbody>
{table_rows}
      </tbody>
    </table>
    </div>
  </section>

  <section class="campus" id="campus-rollup" aria-labelledby="campus-h">
    <h2 id="campus-h">Named campuses in our register</h2>
    <p>A different question from the filing ledger above. These are <b>named campus pins</b> in <a href="/campuses.html">Campuses</a>, rolled up by the operator string as published. Megawatts keep their grain — IT, facility power, and interconnection are not silently mixed. {html.escape(thin_note)} {rollup["n_pins"]} pins · {rollup["n_operators"]} operators · numeric MW by grain: {html.escape(grain_line)}.</p>
    <div class="scroll">
    <table>
      <thead><tr><th>Operator</th><th>Pins</th><th>Numeric MW</th><th>Grain mix</th><th>Status mix</th></tr></thead>
      <tbody>
{campus_table}
      </tbody>
    </table>
    </div>
  </section>

  <section class="notes" id="notes">
    <h2>How this page sits on the desk</h2>
    <p>{html.escape(book["note"])}</p>
    <ul>
      <li>Issuer book: company filings. Campus panel: project pins. Do not add the two columns and call it a fleet.</li>
      <li>Prefer critical IT / AI load when the issuer distinguishes it from bitcoin nameplate. When they do not, the power layer stays on the cell.</li>
      <li>No GPU density fill. No EV/MW. No scrape of a third-party capacity explorer.</li>
    </ul>
    <p>Cite as: <code>{html.escape(cite)}</code>. A wrong cell: <a href="/contact.html">The Desk</a>.</p>
  </section>

  <div class="colophon">
    <div class="c1">COMPUTE.WORLD</div>
    <div class="c2">Capacity · {nice_upd} · the world's compute &amp; silicon index · CNW™ · GDC™ · &copy; 2026 Pukar C. Hamal · San Francisco, CA</div>
  </div>
</div>

<div id="scrim" hidden></div>
<aside id="drawer" hidden aria-labelledby="dname">
  <button class="dclose" type="button" id="dclose">Close</button>
  <div class="dv" id="dop"></div>
  <h2 id="dname"></h2>
  <div class="dmeta" id="dmeta"></div>
  <div id="dbody"></div>
</aside>
<script type="application/json" id="cap-data">{payload}</script>
<script>
var BOOK = JSON.parse(document.getElementById("cap-data").textContent);
var COS = BOOK.companies;
var LAYER = {{it_capacity:"IT capacity",facility_power:"facility power",secured_utility:"secured utility",unspecified:"unspecified"}};
var METRIC_LAB = {{live_mw:"Live MW",contracted_mw:"Contracted MW",construction_mw:"Construction MW",pipeline_mw:"Pipeline MW",secured_mw:"Secured MW",deployed_gpus:"Deployed GPUs"}};
function esc(s){{return String(s==null?"":s).replace(/[&<>"']/g,function(c){{return {{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}}[c];}});}}
function findCo(id){{ return COS.filter(function(c){{return c.id===id;}})[0]; }}
var scrim=document.getElementById("scrim"), drawer=document.getElementById("drawer");
function closeD(){{ drawer.classList.remove("on"); scrim.classList.remove("on"); drawer.setAttribute("aria-hidden","true"); setTimeout(function(){{drawer.hidden=true;scrim.hidden=true;}},320); }}
function openD(id, metric){{
  var c=findCo(id); if(!c) return;
  document.getElementById("dop").textContent=(c.ticker||"private")+" · "+(c.archetype||"");
  document.getElementById("dname").textContent=c.name;
  var keys=metric?[metric]:"live_mw,contracted_mw,construction_mw,pipeline_mw,secured_mw,deployed_gpus".split(",");
  var meta=[];
  if(c.cik) meta.push("<span><b>CIK</b> "+esc(c.cik)+"</span>");
  document.getElementById("dmeta").innerHTML=meta.join("");
  var body="";
  keys.forEach(function(k){{
    var f=c.metrics[k]; if(!f) return;
    body+="<h3 style='font-weight:400;font-size:16px;margin:16px 0 8px'>"+esc(METRIC_LAB[k]||k)+"</h3>";
    body+="<p><b>"+esc(f.display)+"</b> · "+esc(f.status);
    if(f.power_layer) body+=" · "+esc(LAYER[f.power_layer]||f.power_layer);
    if(f.as_of) body+=" · as of "+esc(f.as_of);
    body+="</p>";
    if(f.quote) body+="<blockquote>“"+esc(f.quote)+"”</blockquote>";
    if(f.source_url) body+="<p><a href=\\""+esc(f.source_url)+"\\" rel=\\"noopener\\">"+(f.source_label?esc(f.source_label)+" · ":"")+esc(f.source_url.replace(/^https?:\\/\\//,""))+"</a></p>";
    if(f.status==="undisclosed") body+="<p>Undisclosed. The desk did not invent a number.</p>";
  }});
  if(c.notes) body+="<p>"+esc(c.notes)+"</p>";
  document.getElementById("dbody").innerHTML=body;
  scrim.hidden=false; drawer.hidden=false;
  requestAnimationFrame(function(){{ drawer.classList.add("on"); scrim.classList.add("on"); }});
  drawer.setAttribute("aria-hidden","false");
  if(location.hash!=="#"+id) history.replaceState(null,"","#"+id);
}}
document.querySelectorAll("[data-open]").forEach(function(b){{
  b.addEventListener("click", function(e){{ e.stopPropagation(); openD(b.getAttribute("data-open"), b.getAttribute("data-metric")); }});
}});
document.getElementById("dclose").onclick=closeD;
scrim.onclick=closeD;
document.addEventListener("keydown", function(e){{ if(e.key==="Escape") closeD(); }});
function route(){{ var hid=location.hash.slice(1); if(hid && document.getElementById(hid)) openD(hid); }}
if(location.hash) route();
window.addEventListener("hashchange", route);
(function(){{
  var tb=document.querySelector("#cap tbody");
  var state={{key:"live", dir:-1, type:"num"}};
  document.querySelectorAll("#cap th[data-sort]").forEach(function(th){{
    th.onclick=function(){{
      var key=th.getAttribute("data-sort"), type=th.getAttribute("data-type");
      if(state.key===key) state.dir*=-1; else {{ state.key=key; state.dir = key==="live"?-1:1; }}
      state.type=type;
      document.querySelectorAll("#cap th").forEach(function(h){{ h.classList.remove("sorted"); var a=h.querySelector(".arr"); if(a) a.textContent=""; }});
      th.classList.add("sorted"); th.querySelector(".arr").textContent = state.dir>0?"▲":"▼";
      var rows=[].slice.call(tb.querySelectorAll("tr.caprow"));
      rows.sort(function(a,b){{
        if(type==="num"){{
          var an=parseFloat(a.dataset[key]); var bn=parseFloat(b.dataset[key]);
          if(isNaN(an)) an=-Infinity; if(isNaN(bn)) bn=-Infinity;
          return (an-bn)*state.dir;
        }}
        return (a.dataset[key]||"").localeCompare(b.dataset[key]||"")*state.dir;
      }});
      rows.forEach(function(r){{ tb.appendChild(r); }});
    }};
  }});
}})();
var tm=document.querySelector('meta[name="theme-color"]'), tg=document.getElementById("themetog");
function cur(){{return document.documentElement.getAttribute("data-theme")==="dark"?"dark":"light"}}
function setT(t,sv){{document.documentElement.setAttribute("data-theme",t);
if(sv){{try{{localStorage.setItem("cnw_theme",t)}}catch(e){{}}}}
tm.content=t==="dark"?"#0F1216":"#F3F5F2";tg.setAttribute("aria-label",t==="dark"?"Switch to day mode":"Switch to night mode");}}
tg.onclick=function(){{setT(cur()==="dark"?"light":"dark",true)}};
setT(cur(),false);
{fnav_script("capacity")}
</script>
</body>
</html>'''

    dest_html = dest_html or os.path.join(ROOT, "capacity.html")
    dest_xml = dest_xml or os.path.join(ROOT, "capacity.xml")
    with open(dest_html, "w", encoding="utf-8") as fh:
        fh.write(page)

    items = []
    pub = datetime.strptime(updated, "%Y-%m-%d").strftime("%a, %d %b %Y")
    for c in companies:
        live = c["live_mw"]
        shown = "undisclosed" if live["status"] == "undisclosed" else fmt_mw(live.get("value"))
        quote = (live.get("quote") or c.get("notes") or "")[:240]
        items.append(
            f"""
  <item>
    <title>{html.escape(c['name'])} · live {html.escape(shown)}</title>
    <link>{SITE}/capacity.html#{html.escape(c['id'])}</link>
    <guid isPermaLink="false">compute.world/capacity#{html.escape(c['id'])}</guid>
    <pubDate>{pub} 12:00:00 GMT</pubDate>
    <description>{html.escape(c['name'])} ({html.escape(ARCHETYPE_LABEL[c['archetype']])}). Live {html.escape(shown)}. {html.escape(quote)}</description>
  </item>"""
        )
    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Capacity · compute.world</title>
  <link>{SITE}/capacity.html</link>
  <description>Issuer-disclosed company MW, desk-sourced from SEC EDGAR and official IR. Snapshot {html.escape(updated)}. {len(companies)} companies. Not a comps product. Not EV/MW.</description>
  <language>en</language>{"".join(items)}
</channel></rss>'''
    with open(dest_xml, "w", encoding="utf-8") as fh:
        fh.write(rss)

    print(
        f"capacity.html + capacity.xml generated: {len(companies)} companies, "
        f"live counted {totals['live_mw']['n']}, campus operators {rollup['n_operators']}, "
        f"snapshot {updated}"
    )
    return dest_html, dest_xml


if __name__ == "__main__":
    build()
