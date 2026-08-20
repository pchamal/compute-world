#!/usr/bin/env python3
# The Silicon Tape generator: silicon.json + silicon-history.json -> silicon.html + silicon.xml.
# Run from repo root or src/:  python3 src/build_silicon.py
# Do not invent prices or daily candles. History is append-only dated prints.
import json, html, os, sys
from datetime import datetime
from fnav import css as fnav_css, markup as fnav_markup, script as fnav_script
from subscribe import css as sub_css, markup as sub_markup, script as sub_script
from seo import og_block, breadcrumb_ld, person_author, org_publisher, nice_day
from tape_print import DASH_TITLE, enrich_silicon

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
S = json.load(open(os.path.join(ROOT, "silicon.json")))
HIST_PATH = os.path.join(ROOT, "silicon-history.json")
H = json.load(open(HIST_PATH))
S, H, _appended = enrich_silicon(S, H)
json.dump(H, open(HIST_PATH, "w"), indent=2, ensure_ascii=False)
open(HIST_PATH, "a").write("\n")
json.dump(S, open(os.path.join(ROOT, "silicon.json"), "w"), indent=2, ensure_ascii=False)
open(os.path.join(ROOT, "silicon.json"), "a").write("\n")
SRC = {s["id"]: s for s in S["sources"]}
chips = sorted(S["chips"], key=lambda c: c["rank"])
H100_ASOF = nice_day(S.get("updated"))
_h100 = next((c for c in chips if c.get("id") == "nvidia-h100-sxm-80gb"), {})
_h100_disp = _h100.get("display") or {}
_h100_px = _h100_disp.get("usd_per_gpu_hr")
H100_PX = f"${_h100_px:.2f}" if isinstance(_h100_px, (int, float)) else "$3.99"


def expected_score(c):
    return round(0.40 * c["liquidity"] + 0.35 * c["demand"] + 0.25 * c["frontier"], 2)


def money(x):
    if x is None:
        return "—"
    s = f"{x:.3f}"
    if s.endswith("0"):
        s = s[:-1]
    return f"${s}"


def display_px(d):
    if not d:
        return "—"
    if d.get("primary") == "CNY" and d.get("cny_per_gpu_hr") is not None:
        return f"¥{d['cny_per_gpu_hr']:.2f}"
    if d.get("currency") == "CNY" and d.get("cny_per_gpu_hr") is not None:
        return f"¥{d['cny_per_gpu_hr']:.2f}"
    if d.get("currency") == "CNY" and d.get("price") is not None and d.get("usd_per_gpu_hr") is None:
        return f"¥{d['price']:.2f}"
    if d.get("usd_per_gpu_hr") is not None:
        return money(d.get("usd_per_gpu_hr"))
    if d.get("price") is not None and d.get("currency") != "CNY":
        return money(d.get("price"))
    return money(d.get("usd_per_gpu_hr"))


def lead_mark(d):
    t = ((d.get("term") or "") + " " + (d.get("label") or "")).lower()
    if "spot" in t:
        return "Spot"
    if "on-demand" in t or (d.get("label") or "").endswith(" OD") or " OD" in (d.get("label") or ""):
        return "OD"
    if "capacity" in t or t.strip() == "cb":
        return "CB"
    if "token" in t or "enterprise" in t:
        return "Token"
    if "smm" in t or "1y monthly" in t:
        return "1y"
    return (d.get("label") or d.get("term") or "Print")[:18]


VENDOR_ORDER = ["NVIDIA", "AMD", "Google", "Amazon", "Huawei", "Cerebras", "Groq"]


def vendor_buttons(chips):
    seen = []
    have = {c["vendor"] for c in chips}
    for v in VENDOR_ORDER:
        if v in have:
            seen.append(v)
    for v in sorted(have):
        if v not in seen:
            seen.append(v)
    btns = ['<button class="chip on" data-v="" type="button">All</button>']
    btns += [f'<button class="chip" data-v="{html.escape(v)}" type="button">{html.escape(v)}</button>' for v in seen]
    return "".join(btns)


def nice_date(d):
    if not d:
        return ""
    if d.endswith("-H2"):
        return "2H " + d[:4]
    if len(d) == 7:
        return datetime.strptime(d, "%Y-%m").strftime("%b %Y")
    if len(d) == 10:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%d %b %Y")
    return d


def src_name(sid):
    if not sid:
        return "unlinked"
    return SRC[sid]["name"]


def src_url(sid):
    if not sid:
        return ""
    return SRC[sid]["url"]


def chg_cell(chg, key):
    row = (chg or {}).get(key) or {}
    pct = row.get("pct")
    title = html.escape(row.get("title") or DASH_TITLE, quote=True)
    if pct is None:
        return f'<td class="chg chg-na" data-col="{key}" data-chg="" title="{title}">—</td>'
    cls = "chg-flat"
    caret = ""
    if pct > 0:
        cls = "chg-up"
        caret = '<span class="caret" aria-hidden="true">▲</span>'
        text = f"+{pct:.1f}%"
    elif pct < 0:
        cls = "chg-dn"
        caret = '<span class="caret" aria-hidden="true">▼</span>'
        text = f"{pct:.1f}%"
    else:
        text = "0%"
    return f'<td class="chg {cls}" data-col="{key}" data-chg="{pct}" title="{title}">{caret}{text}</td>'


def spark_cell(c):
    spark = c.get("spark") or {}
    svg = spark.get("svg") or ""
    title = html.escape(spark.get("title") or "Dated step chart.", quote=True)
    n = len(spark.get("points") or [])
    if not svg or n < 2:
        return f'<td class="sparktd" data-col="spark" title="{title}">—</td>'
    return f'<td class="sparktd" data-col="spark" title="{title}">{svg}</td>'


def tape_sub(c):
    tp = c.get("tape_print") or {}
    if not tp.get("show"):
        return ""
    return f'<span class="tape" title="Tape Print is a same-term constellation. We do not publish the sleeve weights.">tape {html.escape(money(tp.get("usd_per_gpu_hr")))} · n={tp.get("n")}</span>'


def price_pop(d, href, src_lab):
    unit = "card-hr" if (d.get("primary") == "CNY" or d.get("currency") == "CNY") else "GPU-hr"
    bits = [
        f'<b>{html.escape(d.get("label") or "Display print")}</b>',
        f'<span>{html.escape(display_px(d))} / {unit}</span>',
        f'<span>{html.escape(d.get("venue") or "—")} · {html.escape(d.get("term") or "")}</span>',
        f'<span>as of {html.escape(nice_date(d.get("as_of")))}</span>',
    ]
    if href:
        bits.append(f'<a href="{href}" rel="noopener">{html.escape(src_lab)}</a>')
    elif src_lab:
        bits.append(f"<span>{html.escape(src_lab)}</span>")
    if d.get("note"):
        bits.append(f'<span class="qnote">{html.escape(d["note"])}</span>')
    return '<div class="pop">' + "".join(bits) + "</div>"


def term_cell(terms, key):
    rec = (terms or {}).get(key)
    title_na = html.escape(
        "No sourced public list for this tenor. We do not impute a discount off on-demand.",
        quote=True,
    )
    if not rec or (rec.get("usd_per_gpu_hr") is None and rec.get("cny_per_gpu_hr") is None and rec.get("price") is None):
        return (
            f'<td class="termx term-na" data-col="{key}" data-px="" title="{title_na}">'
            f'<span class="px">—</span></td>'
        )
    href = rec.get("url") or ""
    src_lab = rec.get("venue") or "source"
    px = rec.get("usd_per_gpu_hr")
    if px is None and rec.get("currency") != "CNY":
        px = rec.get("price")
    pop = price_pop(rec, href, src_lab)
    return (
        f'<td class="termx" data-col="{key}" data-px="{"" if px is None else px}">'
        f'<span class="px">{html.escape(display_px(rec))}</span>'
        f'<span class="tsub">{html.escape(rec.get("label") or rec.get("term") or "")}</span>'
        f"{pop}</td>"
    )


def venue_bar(c):
    n = len(c.get("venues") or [])
    liq = c.get("liquidity") or 0
    width = min(100, max(8, int(round((liq / 3) * 100)))) if liq else (min(100, n * 25) if n else 8)
    title = html.escape(f"{n} venue{'s' if n != 1 else ''} · liquidity {liq}/3 · {c.get('scarcity_label') or ''}", quote=True)
    return (
        f'<span class="vbar" title="{title}"><i style="width:{width}%"></i></span>'
        f'<span class="vcount">{n} venue{"s" if n != 1 else ""}</span>'
        f'<span class="sub">{html.escape(c.get("scarcity_label") or "")}</span>'
    )


def weather_html(items, href_prefix="#"):
    if not items:
        return ""
    parts = ['<div class="weather" aria-label="Tape weather">', '<span class="wlab">Tape</span>']
    for w in items:
        pct = w["pct"]
        if pct > 0:
            cls, mark = "w-up", f"▲ +{pct:.1f}%"
        elif pct < 0:
            cls, mark = "w-dn", f"▼ {pct:.1f}%"
        else:
            cls, mark = "w-flat", "0%"
        title = html.escape(w.get("title") or "", quote=True)
        href = href_prefix + html.escape(w["id"])
        parts.append(
            f'<a class="witem {cls}" href="{href}" title="{title}">'
            f'{html.escape(w["name"])} {html.escape(w["window"])} <b>{mark}</b> '
            f'{html.escape(w.get("venue") or "")}</a>'
        )
    parts.append("</div>")
    return "".join(parts)


for c in chips:
    got, exp = c["score"], expected_score(c)
    if abs(got - exp) > 0.001:
        sys.exit(f"score mismatch {c['id']}: json={got} formula={exp}")

# ---- table rows (static; JS re-sorts / filters the same markup) ----
rows = []
for i, c in enumerate(chips):
    d = c["display"]
    also = c.get("also") or {}
    also_text = html.escape(also.get("text") or "—")
    href = src_url(d.get("source_id"))
    src_lab = src_name(d.get("source_id"))
    tick = html.escape(" · ".join(x for x in (c.get("vendor"), c.get("memory")) if x))
    chg = c.get("changes") or {}
    terms = c.get("terms") or {}
    d30 = (chg.get("d30") or {}).get("pct")
    d90 = (chg.get("d90") or {}).get("pct")
    d1y = (chg.get("d1y") or {}).get("pct")
    d3y = (chg.get("d3y") or {}).get("pct")
    nven = len(c.get("venues") or [])
    def term_px(key):
        rec = terms.get(key) or {}
        v = rec.get("usd_per_gpu_hr")
        if v is None and rec.get("currency") != "CNY":
            v = rec.get("price")
        return "" if v is None else v
    stripe = "odd" if i % 2 == 0 else "even"
    rows.append(f'''<tr class="chiprow {stripe}" id="{html.escape(c["id"])}" data-id="{html.escape(c["id"])}" data-vendor="{html.escape(c["vendor"])}" data-rank="{c["rank"]}" data-score="{c["score"]}" data-price="{d["usd_per_gpu_hr"] if d.get("usd_per_gpu_hr") is not None else ""}" data-m1="{term_px("m1")}" data-q1="{term_px("q1")}" data-y1="{term_px("y1")}" data-y3="{term_px("y3")}" data-d30="{"" if d30 is None else d30}" data-d90="{"" if d90 is None else d90}" data-d1y="{"" if d1y is None else d1y}" data-d3y="{"" if d3y is None else d3y}" data-venues="{nven}" tabindex="0" role="button" aria-expanded="false" aria-controls="drawer">
  <td class="num" data-col="rank">{c["rank"]}</td>
  <td class="chip" data-col="name"><span class="cn">{html.escape(c["name"])}</span><span class="tick">{tick}</span></td>
  <td class="price" data-col="price">
    <span class="px">{html.escape(display_px(d))}</span>
    <span class="term"><span class="leadlab">{html.escape(lead_mark(d))}</span> {html.escape(d.get("label") or "")}</span>
    {tape_sub(c)}
    {price_pop(d, href, src_lab)}
  </td>
  {term_cell(terms, "m1")}
  {term_cell(terms, "q1")}
  {term_cell(terms, "y1")}
  {term_cell(terms, "y3")}
  <td class="chg chg-na" data-col="d7" data-chg="" title="{html.escape(DASH_TITLE)}">—</td>
  {chg_cell(chg, "d30")}
  {chg_cell(chg, "d90")}
  {chg_cell(chg, "d1y")}
  {chg_cell(chg, "d3y")}
  {spark_cell(c)}
  <td class="also" data-col="also"><span class="also-t">{also_text}</span></td>
  <td class="venues" data-col="venues">{venue_bar(c)}</td>
  <td class="num score" data-col="score">{c["score"]:.2f}</td>
</tr>''')

omitted = "".join(
    f"<li><b>{html.escape(o['id'])}</b> — {html.escape(o['reason'])}</li>"
    for o in S["omitted"]
)
source_lis = "".join(
    f'<li><a href="{html.escape(s["url"])}" rel="noopener">{html.escape(s["name"])}</a>'
    f' — {html.escape(s.get("note") or "")}</li>'
    for s in S["sources"]
)

ld = json.dumps({
    "@context": "https://schema.org",
    "@type": "Dataset",
    "name": "The Silicon Tape",
    "alternateName": ["Silicon Tape", "compute.world silicon index"],
    "description": S["thesis"],
    "url": "https://compute.world/silicon.html",
    "version": S["version"],
    "dateModified": S["updated"],
    "datePublished": S["updated"],
    "creator": person_author(),
    "author": person_author(),
    "publisher": org_publisher(),
    "license": "https://creativecommons.org/licenses/by/4.0/",
    "isAccessibleForFree": True,
    "variableMeasured": "Labeled AI accelerator rental prints ($/GPU-hr or token/enterprise)",
    "distribution": {
        "@type": "DataDownload",
        "encodingFormat": "application/json",
        "contentUrl": "https://compute.world/silicon.json",
    },
    "citation": S["cite"],
})
crumb = json.dumps(breadcrumb_ld([
    ("compute.world", "https://compute.world/"),
    ("The Silicon Tape", "https://compute.world/silicon.html"),
]))
faq_ld = json.dumps({
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {"@type": "Question", "name": "What is the Silicon Tape?",
         "acceptedAnswer": {"@type": "Answer", "text": "The Silicon Tape is the silicon half of compute.world, the world's compute & silicon index. It is a public index of sourced AI accelerator rental prints — labeled on-demand, 1y, spot, Capacity Blocks, or token/enterprise. Scores are ordinal hygiene (0.40 liquidity + 0.35 demand + 0.25 frontier). It is not a market cap."}},
        {"@type": "Question", "name": "Why is 7-day percent change a dash?",
         "acceptedAnswer": {"@type": "Answer", "text": "US list prices do not tick daily. 7d lights up after a week of our own scrape. 1M, 1Q, 1Y, and 3Y are computed only from two dated same-venue same-term prints. A missing pair is an em dash, never an invented 0%."}},
        {"@type": "Question", "name": "Why are 1m / 1q / 3y dashes on most US lists?",
         "acceptedAnswer": {"@type": "Answer", "text": "US neoclouds publish on-demand, sometimes spot, and rarely a 12-month reserved card. They do not publish 1-month, 1-quarter, or 3-year list prices. We do not impute a discount off on-demand. A dash means no sourced tenor."}},
        {"@type": "Question", "name": "Why isn't today's H100 $2.35?",
         "acceptedAnswer": {"@type": "Answer", "text": f"SemiAnalysis 1y $2.35 is a March 2026 print. The last public SA period is April 2026 and is labeled STALE. Buy-now is the current Lambda on-demand list: {H100_PX} as of {H100_ASOF}."}},
        {"@type": "Question", "name": "Why are sparklines steps, not candles?",
         "acceptedAnswer": {"@type": "Answer", "text": "The tape has dated observed prints, not a daily market. A sparkline is a step chart of those prints. Carry-forward is for drawing only. We do not invent 1d or 7d candles."}},
        {"@type": "Question", "name": "Why does Cerebras have no $/hour?",
         "acceptedAnswer": {"@type": "Answer", "text": "Cerebras Cloud is sold as a token API and as enterprise. There is no sourced public accelerator-hour in this snapshot. Aggregator ranges such as $0.75–$12.50 are omitted on purpose. Groq is listed the same way: token API, no invented chip-hour."}},
        {"@type": "Question", "name": "What is compute.world?",
         "acceptedAnswer": {"@type": "Answer", "text": "compute.world is Pukar C. Hamal's public compute desk and the world's compute & silicon index: the Compute Net Worth Index (CNW™) prices 108 countries, and the Silicon Tape prints sourced chips. Companies inquire via https://compute.world/contact.html."}},
    ],
})
si_title = "The Silicon Tape · AI accelerator rental index · compute.world"
si_desc = (
    f"The Silicon Tape: {len(chips)} sourced AI accelerator prints. "
    f"Snapshot {S['updated']}. B200 $6.69 Lambda OD · H100 $3.99 Lambda OD · Ascend 910C ¥10.79/hr. "
    "Term book 1m / 1q / 1y / 3y; change windows 1M / 1Q / 1Y / 3Y. No invented tenors or 7-day candles."
)
si_og = og_block(
    si_title, html.escape(si_desc),
    "https://compute.world/silicon.html", "og-silicon.png",
    og_type="website",
    image_alt="The Silicon Tape — sourced B200, H100, Ascend 910C, and Cerebras prints",
)
tape_json = json.dumps({"sources": S["sources"], "chips": chips}, ensure_ascii=False)
vendor_bar = vendor_buttons(chips)

PAGE = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#f7f4ee">
<script>(function(){{try{{var t=localStorage.getItem("cnw_theme");if(t!=="dark"&&t!=="light"){{var h=new Date().getHours();t=(h>=19||h<7)?"dark":"light";}}document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();</script>
<title>{html.escape(si_title)}</title>
<meta name="description" content="{html.escape(si_desc)}">
<link rel="canonical" href="https://compute.world/silicon.html">
<meta name="robots" content="index,follow,max-image-preview:large">
{si_og}
<link rel="alternate" type="application/rss+xml" title="The Silicon Tape · compute.world" href="https://compute.world/silicon.xml">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' fill='%23f7f4ee'/><text x='32' y='44' font-family='Georgia,serif' font-size='36' fill='%23171614' text-anchor='middle'>S</text></svg>">
<script type="application/ld+json">{ld}</script>
<script type="application/ld+json">{crumb}</script>
<script type="application/ld+json">{faq_ld}</script>
<style>
:root{{--paper:#f7f4ee;--ink:#171614;--muted:#62605a;--faint:#8d8a81;--rule:#cdc7b9;--rule2:#171614;
--accent:#7d2027;--tint:#efe9dd;--stripe:color-mix(in srgb,var(--ink) 5.5%,var(--paper));
--row-hover:color-mix(in srgb,var(--ink) 10%,var(--paper));--pr:#4b5f36;--sg:#8a5a2a;--barbg:#e2dcce;
--glass:rgba(247,244,238,.72);--glassborder:rgba(23,22,20,.35);
--serif:'Charter','Bitstream Charter','Sitka Text',Cambria,Georgia,'Times New Roman',serif}}
html[data-theme="dark"]{{--paper:#171511;--ink:#ece7db;--muted:#a49e8f;--faint:#9a9484;--rule:#3a352a;
--rule2:#ded8c8;--accent:#c2564c;--tint:#231f17;--stripe:color-mix(in srgb,var(--ink) 6%,var(--paper));
--row-hover:color-mix(in srgb,var(--ink) 11%,var(--paper));--pr:#8fae72;--sg:#c99a5e;--barbg:#3a352a;
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
@media(max-width:760px){{.tchip{{top:12px;width:40px;height:40px}}}}
{fnav_css()}
{sub_css()}
body{{transition:background-color .35s ease,color .35s ease}}
*{{margin:0;padding:0;box-sizing:border-box}}
html{{background:var(--paper)}}
body{{background:var(--paper);color:var(--ink);font-family:var(--serif);font-size:17px;line-height:1.62;-webkit-font-smoothing:antialiased;font-variant-numeric:lining-nums tabular-nums}}
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
.subrow{{display:flex;flex-wrap:wrap;gap:8px 26px;align-items:baseline;margin:26px 0 0;padding:16px 0;border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule);font-size:13px;letter-spacing:.1em;text-transform:uppercase}}
.subrow .lab{{color:var(--faint);font-size:11px;letter-spacing:.16em}}
.chips{{display:flex;flex-wrap:wrap;gap:8px 20px;margin:22px 0 10px;font-size:13.5px}}
.chip{{cursor:pointer;color:var(--ink);border-bottom:1px solid transparent;letter-spacing:.04em;background:none;font:inherit;padding:0}}
.chip:hover{{border-bottom-color:var(--rule)}}
.chip.on{{color:var(--accent);border-bottom:1px solid var(--accent)}}
.tblwrap{{overflow-x:auto;margin:8px 0 0;border-top:2px solid var(--rule2)}}
.weather{{display:flex;flex-wrap:wrap;align-items:baseline;gap:7px 18px;margin:2px 0 0;padding:10px 0 12px;border-bottom:1px solid var(--rule);font-size:13px}}
.weather .wlab{{font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--faint)}}
.weather .witem{{border:none;color:var(--muted);white-space:nowrap}}
.weather .witem:hover{{color:var(--ink)}}
.weather .witem b{{font-weight:600}}
.weather .w-up,.weather .w-up b{{color:var(--pr)}}
.weather .w-dn,.weather .w-dn b{{color:var(--accent)}}
.weather .w-flat b{{color:var(--ink)}}
table.tape{{width:100%;border-collapse:collapse;font-size:12.5px;min-width:1280px}}
.tape th{{font-weight:400;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);text-align:left;
padding:8px 7px 7px;border-bottom:1px solid var(--rule2);white-space:nowrap;cursor:pointer;user-select:none;
position:sticky;top:0;background:var(--paper);z-index:4;box-shadow:0 1px 0 var(--rule2)}}
.tape th.num,.tape td.num,.tape th.price,.tape td.price,.tape th.chg,.tape td.chg,.tape th.termx,.tape td.termx{{text-align:right}}
.tape th:hover{{color:var(--ink)}}
.tape th.sorted{{color:var(--ink)}}
.tape th .arr{{display:inline-block;margin-left:4px;color:var(--faint);font-size:9px}}
.tape td{{padding:8px 7px;border-bottom:1px solid color-mix(in srgb,var(--rule) 55%,transparent);vertical-align:middle}}
.tape tr.chiprow{{cursor:pointer}}
.tape tbody tr.chiprow.odd td{{background:var(--paper)}}
.tape tbody tr.chiprow.even td{{background:var(--tint)}}
.tape tbody tr.chiprow:hover td,.tape tbody tr.chiprow.open td{{background:var(--row-hover)}}
.tape .cn{{font-weight:600;border-bottom:1px solid transparent}}
.tape tr.chiprow:hover .cn{{color:var(--accent);border-bottom-color:var(--accent)}}
.tape .tick{{display:block;font-size:11px;color:var(--faint);margin-top:2px;letter-spacing:.02em}}
.tape .px{{font-size:15px;font-weight:600;letter-spacing:-.02em;display:block}}
.tape .term,.tape .asof,.tape .sub{{display:block;font-size:11px;letter-spacing:.02em;color:var(--faint);line-height:1.45;margin-top:2px;text-transform:none}}
.tape .leadlab{{display:inline;font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink);margin-right:4px}}
.tape td.termx{{position:relative;font-variant-numeric:tabular-nums}}
.tape td.termx .px{{font-size:13px;font-weight:600;letter-spacing:-.02em;display:block}}
.tape td.termx .tsub{{display:block;font-size:10px;color:var(--faint);margin-top:2px;letter-spacing:.02em;text-transform:none}}
.tape td.term-na .px{{font-weight:400;color:var(--faint);font-size:13px}}
.tape td.termx:hover .pop{{display:block}}
.tape .also-t{{color:var(--muted);font-size:12px}}
.tape .venues{{color:var(--muted);font-size:12px;max-width:120px}}
.tape .vbar{{display:block;height:3px;background:var(--barbg);margin:0 0 6px;max-width:72px}}
.tape .vbar i{{display:block;height:100%;background:var(--ink);opacity:.42}}
.tape .vcount{{display:block}}
.tape .score{{font-weight:600}}
.tape .chg{{font-variant-numeric:tabular-nums;white-space:nowrap;font-size:12.5px}}
.tape .chg .caret{{display:inline-block;margin-right:3px;font-size:9px;transform:translateY(-1px)}}
.tape .chg-up{{color:var(--pr)}}
.tape .chg-dn{{color:var(--accent)}}
.tape .chg-flat,.tape .chg-na{{color:var(--faint)}}
.tape .sparktd{{width:88px;min-width:80px}}
.tape .spark{{display:block;margin-left:auto;color:var(--muted)}}
.tape .spark-up{{color:var(--pr)}}
.tape .spark-dn{{color:var(--accent)}}
.tape .tape{{display:block;margin-top:4px;font-size:10.5px;letter-spacing:.04em;color:var(--muted);text-transform:none}}
.tape td.price,.tape td.termx{{position:relative}}
.tape .pop{{display:none;position:absolute;right:6px;top:calc(100% - 2px);z-index:8;min-width:228px;padding:10px 12px;
background:var(--paper);border:1px solid var(--rule2);box-shadow:0 12px 32px rgba(0,0,0,.14);text-align:left;
font-size:12px;color:var(--muted);line-height:1.45}}
.tape td.price:hover .pop{{display:block}}
.tape .pop b{{color:var(--ink);display:block;margin-bottom:3px}}
.tape .pop span,.tape .pop a{{display:block;margin-top:2px}}
.tape .pop a{{border:none}}
.tape .pop .qnote{{color:var(--faint);font-size:11px}}
.hint{{margin:10px 0 0;font-size:12px;color:var(--faint);letter-spacing:.04em}}
#scrim{{position:fixed;inset:0;background:rgba(23,22,20,.28);opacity:0;pointer-events:none;z-index:80;transition:opacity .3s ease}}
#scrim.on{{opacity:1;pointer-events:auto}}
html[data-theme="dark"] #scrim{{background:rgba(0,0,0,.45)}}
#drawer{{position:fixed;top:0;right:0;height:100%;width:min(520px,100%);background:var(--paper);color:var(--ink);
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
#drawer .qtable .qpx{{font-weight:600;white-space:nowrap}}
#drawer .qnote{{display:block;font-size:11.5px;color:var(--faint);margin-top:2px}}
#drawer .dspark{{margin:8px 0 12px}}
#drawer .dspark svg{{width:220px;height:64px;color:var(--muted)}}
#drawer .spark-up{{color:var(--pr)}}
#drawer .spark-dn{{color:var(--accent)}}
#drawer p{{font-size:14.5px;color:var(--muted);margin-bottom:10px}}
#drawer p b{{color:var(--ink)}}
#drawer ul{{margin:0 0 8px 18px;color:var(--muted);font-size:14px}}
#drawer li{{margin-bottom:5px}}
@media(prefers-reduced-motion:reduce){{#drawer,#scrim{{transition:none}}}}
details.meth{{margin:44px 0;border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule)}}
details.meth summary{{cursor:pointer;padding:13px 4px;font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);list-style:none}}
details.meth summary::before{{content:"+ "}}
details.meth[open] summary::before{{content:"− "}}
details.meth .mb{{padding:4px 4px 18px;font-size:14px;color:var(--muted);max-width:820px}}
details.meth .mb p{{margin-bottom:12px}}
details.meth .mb b{{color:var(--ink)}}
details.meth .mb ul{{margin:0 0 12px 18px}}
details.meth .mb li{{margin-bottom:6px}}
.colophon{{margin-top:56px;border-top:2px solid var(--rule2);padding:24px 0 56px;text-align:center}}
.colophon .c1{{font-size:12px;letter-spacing:.3em;text-transform:uppercase}}
.colophon .c2{{margin-top:10px;font-size:12.5px;color:var(--muted)}}
.faq{{margin:48px 0 0;border-top:2px solid var(--rule2);padding-top:22px}}
.faq h2{{font-weight:400;font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:0 0 16px}}
.faq h3{{font-weight:600;font-size:16px;margin:18px 0 6px}}
.faq p{{font-size:15px;color:var(--muted);max-width:820px}}
.faq p b{{color:var(--ink)}}
@media(max-width:760px){{.wrap{{padding:0 18px}}.lede{{padding:36px 0 8px}}.standfirst{{font-size:16.5px}}
#drawer{{padding:24px 18px 40px}}}}
</style>
</head>
<body class="fnav-inner">
<button id="themetog" class="tchip" aria-label="Switch to night mode" title="Day / Night">
  <svg class="ic-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>
  <svg class="ic-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.9 1.9M19.1 4.9l-1.8 1.8M6.7 17.3l-1.9 1.9"/></svg>
</button>
{fnav_markup("silicon")}
<div class="wrap">
  <div class="masthead">
    <div class="name"><a href="/"><b>COMPUTE</b>.WORLD</a></div>
    <div class="sub">The Silicon Tape · the world's silicon index · snapshot {S["updated"]}</div>
    <div class="mastrule"></div>
  </div>

  <div class="lede">
    <h1>The rental tape, <em>split</em>.</h1>
    <p class="standfirst">{html.escape(S["thesis"])} Announcements are cheap. Megawatts and GPU-hours are not. This is not a market cap. Scores are ordinal hygiene. Sibling of the Compute Net Worth Index&#8482; — together, the world's compute &amp; silicon index.</p>
    <div class="subrow">
      <span class="lab">v0</span>
      <span>Snapshot {S["updated"]}</span>
      <span>{len(chips)} chips</span>
      <span>SA prints as-of April 2026</span>
      <a href="/silicon.json">silicon.json</a>
      <a href="/silicon-history.json">history</a>
      <a href="/rank-history.json">ranks</a>
      <a href="/silicon.xml">RSS</a>
      <a href="/">Nation-State Index</a>
      <a href="/brief">Daily brief</a>
      <a href="/contact.html">The Desk</a>
    </div>
  </div>

  {sub_markup()}

  <div class="chips" role="tablist" aria-label="Vendor filter">
    {vendor_bar}
  </div>
  {weather_html(S.get("weather") or [])}

  <div class="tblwrap">
    <table class="tape" id="tape">
      <thead>
        <tr>
          <th class="num sorted" data-sort="rank" data-type="num"># <span class="arr">▼</span></th>
          <th data-sort="name" data-type="str">Chip <span class="arr"></span></th>
          <th class="price" data-sort="price" data-type="num" title="Buy-now on-demand or labeled spot. Not a reserved tenor.">OD / Spot <span class="arr"></span></th>
          <th class="termx" data-sort="m1" data-type="num" title="1-month contract / monthly lease. Dash if no public list — we do not impute.">1m <span class="arr"></span></th>
          <th class="termx" data-sort="q1" data-type="num" title="1-quarter (3-month) contract. Almost no US public list.">1q <span class="arr"></span></th>
          <th class="termx" data-sort="y1" data-type="num" title="1-year / 12-month reserved, or a labeled 1CC / SA 1y print.">1y <span class="arr"></span></th>
          <th class="termx" data-sort="y3" data-type="num" title="3-year reserved. No Lambda / CoreWeave / DO public 3y card.">3y <span class="arr"></span></th>
          <th class="num" data-sort="d7" data-type="num" title="{html.escape(DASH_TITLE)}">7d <span class="arr"></span></th>
          <th class="num" data-sort="d30" data-type="num" title="1M change: 30d ±5. Same venue + same term + two dated prints.">1M <span class="arr"></span></th>
          <th class="num" data-sort="d90" data-type="num" title="1Q change: 90d ±10. Same venue + same term + two dated prints.">1Q <span class="arr"></span></th>
          <th class="num" data-sort="d1y" data-type="num" title="1Y change: 365d ±21. Same venue + same term + two dated prints.">1Y <span class="arr"></span></th>
          <th class="num" data-sort="d3y" data-type="num" title="3Y change: 1095d ±45. Almost none exist. Em dash is correct.">3Y <span class="arr"></span></th>
          <th data-sort="spark" data-type="str">Sparkline <span class="arr"></span></th>
          <th data-sort="also" data-type="str">Also <span class="arr"></span></th>
          <th data-sort="venues" data-type="num">Venues <span class="arr"></span></th>
          <th class="num" data-sort="score" data-type="num">Score <span class="arr"></span></th>
        </tr>
      </thead>
      <tbody>
{chr(10).join(rows)}
      </tbody>
    </table>
  </div>
  <p class="hint">Hover a filled cell for venue · term · as-of · URL. Lowercase 1m / 1q / 1y / 3y are term prices (sourced $/GPU-hr, or an em dash). Uppercase 1M / 1Q / 1Y / 3Y are percent change from two dated same-venue same-term prints. Missing tenor is never a guessed discount off OD. 7d stays a dash until we have a week of our own scrape. Rank as of {S["updated"]}: snapshotted on publish; machine feed at <a href="/rank-history.json">rank-history.json</a>.</p>

  <details class="meth" open>
    <summary>How the tape is ranked — and what it refuses to be</summary>
    <div class="mb">
      <p><b>Rank = 0.40 × liquidity + 0.35 × demand + 0.25 × frontier</b>, each scored 0–3. The composite is ordinal hygiene, not a valuation, not a market cap, not a forecast.</p>
      <p><b>Liquidity.</b> 0 none; 1 one primary venue; 2 two–three venues; 3 four or more spanning a neocloud and a hyperscaler.</p>
      <p><b>Demand.</b> 3 named sold-out, booked, or scarce in 2026 trade press; 2 listed but sales-gated or tight; 1 widely listed on-demand; 0 unknown.</p>
      <p><b>Frontier.</b> 3 current training / rack frontier; 2 current workhorse; 1 commodity / prior-gen.</p>
      <p><b>Display-price convention.</b> Prefer a labeled <b>on-demand</b> print from the most liquid public neocloud (Lambda, else CoreWeave, else DigitalOcean). The lead column is that buy-now print, marked <b>OD</b> or <b>Spot</b>. SemiAnalysis 1y is a dated series — last public period <b>April 2026, STALE</b> — and is never today's buy-now headline. A second venue stays in the row. Capacity Blocks, marketplace floors, and on-demand are never blended into one unlabeled number. TensorWave is not treated as a public list.</p>
      <p><b>Term book.</b> After the lead print: <b>1m</b> (1-month / monthly lease), <b>1q</b> (1-quarter), <b>1y</b> (1-year / 12-month reserved, or a labeled Lambda 1-Click Cluster 2w–1y, or SA 1y), <b>3y</b> (3-year reserved). Each cell is a sourced labeled $/GPU-hr. Missing tenor = em dash. We do not write 1y = OD × 0.8 or 3y = OD × 0.65.</p>
      <p><b>Change windows.</b> 1M = 30d ±5d, 1Q = 90d ±10d, 1Y = 365d ±21d, 3Y = 1095d ±45d. Percent = 100 × (now/then − 1), only from two real same-chip same-venue same-term same-config prints. A missing pair is an em dash, never an invented 0%. 1h / 24h / 7d stay dashes: US list prices do not tick daily.</p>
      <p><b>Sparklines.</b> Step charts of dated observed prints. Carry-forward is for drawing only. We do not invent 1d or 7d candles.</p>
      <p><b>Tape Print.</b> Tape Print is a same-term constellation. We do not publish the sleeve weights. The big number on the row is always the labeled venue price.</p>
      <p><b>As-of dates.</b> SemiAnalysis public prints <b>stop at April 2026</b> and are labeled that way. August 2026 figures are neocloud and hyperscaler list pages fetched <b>2026-08-18</b>. Dated history lives in <a href="/silicon-history.json">silicon-history.json</a> (append-only). Rank snapshots live in <a href="/rank-history.json">rank-history.json</a> (append-only observed ranks; never interpolated). Inference / Neoclouds / Hyperscalers join that tape once they have a published rank formula.</p>
      <p><b>Omitted this snapshot</b> — no invented rows:</p>
      <ul>{omitted}</ul>
      <p>Machine-readable: <a href="/silicon.json">silicon.json</a> (CC BY 4.0, attribution to compute.world). Cite as: <code>{html.escape(S["cite"])}</code>. The Desk: <a href="/contact.html">briefings, corrections, cite / data</a>. Half of <a href="/">the world's compute &amp; silicon index</a>.</p>
      <p><b>Primary sources</b></p>
      <ul>{source_lis}</ul>
    </div>
  </details>

  <section class="faq" id="faq" aria-labelledby="faq-h">
    <h2 id="faq-h">Questions the tape answers in public</h2>
    <h3>What is the index?</h3>
    <p>compute.world is <b>the world's compute &amp; silicon index</b>. The Compute Net Worth Index&#8482; (CNW™) prices 108 countries. The Silicon Tape prints sourced chips. Gross Domestic Compute (GDC™) is the tapped counterpart to CNW. Two tapes, one index.</p>
    <h3>What is the tape?</h3>
    <p>The Silicon Tape is a public rental index. Every display number is a <b>labeled term</b> — on-demand, 1y, spot, Capacity Blocks, or token/enterprise — from a named venue and date. Rank is 0.40 × liquidity + 0.35 × demand + 0.25 × frontier. It is not a market cap.</p>
    <h3>Why is 7-day a dash?</h3>
    <p>US list prices do not tick daily. 7d lights up after a week of our own scrape. We will not invent a daily coin chart.</p>
    <h3>Why are 1m / 1q / 3y dashes on most US lists?</h3>
    <p>Venues do not publish those tenors. US neoclouds print on-demand, sometimes spot, and rarely a 12-month reserved card. They do not publish 1-month, 1-quarter, or 3-year list prices. We do not impute a discount off on-demand. A dash means no sourced tenor.</p>
    <h3>Why isn't today's H100 $2.35?</h3>
    <p>SemiAnalysis 1y $2.35 is a <b>March 2026</b> print. The last public SA period is April 2026 and is labeled STALE. Buy-now is Lambda on-demand <b>{H100_PX}</b> as of {H100_ASOF}. The SA series still lives in the drawer, as a step chart, not as today's headline.</p>
    <h3>Why are sparklines steps, not candles?</h3>
    <p>The tape has dated observed prints — not a session market. A sparkline is a step chart of those prints. Carry-forward is for drawing only. A percent needs two real same-venue same-term prints. Missing pair = —.</p>
    <h3>What is Tape Print?</h3>
    <p>Tape Print is a same-term constellation. We do not publish the sleeve weights. The auditable number is the labeled venue price.</p>
    <h3>Why does Cerebras have no $/hour?</h3>
    <p>Cerebras Cloud is token and enterprise. There is no sourced public accelerator-hour. Aggregator ranges such as $0.75–$12.50 are omitted on purpose. Groq is the same motion: a token API, not an invented chip-hour.</p>
  </section>

  <div class="colophon">
    <div class="c1">COMPUTE.WORLD</div>
    <div class="c2">The Silicon Tape · v0 · snapshot {S["updated"]} · the world's compute &amp; silicon index · CNW™ · GDC™ · &copy; 2026 Pukar C. Hamal · San Francisco, CA</div>
  </div>
</div>

<div id="scrim" hidden></div>
<aside id="drawer" aria-hidden="true" aria-labelledby="dtitle">
  <button class="dclose" type="button" id="dclose">Close</button>
  <div class="dv" id="dvendor"></div>
  <h2 id="dtitle"></h2>
  <div class="dmeta" id="dmeta"></div>
  <div id="dbody"></div>
</aside>
<script type="application/json" id="tape-data">{tape_json}</script>
<script>
var TAPE = JSON.parse(document.getElementById("tape-data").textContent);
var SRC = {{}}; TAPE.sources.forEach(function(s){{ SRC[s.id] = s; }});
function money(x){{ if(x==null) return "—"; var s=Number(x).toFixed(3); if(s.slice(-1)==="0") s=s.slice(0,-1); return "$"+s; }}
function qPrice(q){{
  if(q.in_per_mtok!=null) return "$"+Number(q.in_per_mtok).toFixed(2)+" / $"+Number(q.out_per_mtok).toFixed(2)+" per 1M tok";
  if(q.cny_per_gpu_hr!=null) return "¥"+Number(q.cny_per_gpu_hr).toFixed(2)+(q.usd_per_gpu_hr!=null?" · "+money(q.usd_per_gpu_hr):"");
  if(q.range) return money(q.range[0])+"–"+money(q.range[1]);
  var p = money(q.usd_per_gpu_hr);
  if(q.approx && q.usd_per_gpu_hr!=null) p = "~"+p;
  if(q.unit && q.usd_per_gpu_hr!=null) p += " / "+q.unit;
  if(q.fx_usdcny) p = "USD/CNY "+q.fx_usdcny;
  return p;
}}
function niceDate(d){{
  if(!d) return "";
  if(/-H2$/.test(d)) return "2H "+d.slice(0,4);
  var m = d.match(/^(\\d{{4}})-(\\d{{2}})$/);
  if(m) return ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][+m[2]-1]+" "+m[1];
  var n = d.match(/^(\\d{{4}})-(\\d{{2}})-(\\d{{2}})$/);
  if(n) return +n[3]+" "+["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][+n[2]-1]+" "+n[1];
  return d;
}}
function srcA(id){{
  if(!id || !SRC[id]) return "unlinked";
  return '<a href="'+SRC[id].url+'" rel="noopener">'+SRC[id].name+'</a>';
}}
var drawer = document.getElementById("drawer"), scrim = document.getElementById("scrim");
function closeD(){{
  drawer.classList.remove("on"); scrim.classList.remove("on");
  drawer.setAttribute("aria-hidden","true"); scrim.hidden = true;
  document.querySelectorAll("tr.chiprow.open").forEach(function(r){{ r.classList.remove("open"); r.setAttribute("aria-expanded","false"); }});
  if(location.hash) history.replaceState(null,"",location.pathname+location.search);
}}
function openD(id){{
  var c = TAPE.chips.filter(function(x){{ return x.id===id; }})[0];
  if(!c) return;
  document.querySelectorAll("tr.chiprow").forEach(function(r){{
    var on = r.dataset.id===id; r.classList.toggle("open", on); r.setAttribute("aria-expanded", on?"true":"false");
  }});
  document.getElementById("dvendor").textContent = c.vendor + (c.process ? " · "+c.process : "");
  document.getElementById("dtitle").textContent = c.name;
  document.getElementById("dmeta").innerHTML =
    "<span><b>Memory</b> "+c.memory+(c.memory_note?" · "+c.memory_note:"")+"</span>"+
    "<span><b>Score</b> "+c.score.toFixed(2)+" · L"+c.liquidity+" D"+c.demand+" F"+c.frontier+"</span>"+
    "<span><b>Rank</b> "+c.rank+"</span>";
  var qrows = c.quotes.map(function(q){{
    var note = q.note ? '<span class="qnote">'+q.note+'</span>' : "";
    return "<tr><td>"+q.venue+"<span class=\\"qnote\\">"+q.term+"</span></td>"+
      "<td class=\\"qpx\\">"+qPrice(q)+note+"</td>"+
      "<td>"+niceDate(q.as_of)+"<span class=\\"qnote\\">"+srcA(q.source_id)+"</span></td></tr>";
  }}).join("");
  var noshow = (c.cannot_show||[]).map(function(x){{ return "<li>"+x+"</li>"; }}).join("");
  var extra = (c.notes||[]).map(function(x){{ return "<p>"+x+"</p>"; }}).join("");
  var spark = c.spark||{{}};
  var sparkH = (spark.svg && (spark.points||[]).length>=2) ? "<h3>Dated tape</h3><p>"+(spark.title||"Step chart of dated prints.")+"</p><div class=\\"dspark\\">"+spark.svg+"</div>" : "";
  var sa = c.spark_sa_1y;
  if(sa && sa.svg){{ sparkH += "<h3>"+sa.label+" (STALE)</h3><p>"+sa.title+"</p><div class=\\"dspark\\">"+sa.svg+"</div>"; }}
  var tp = c.tape_print||{{}};
  var tapeH = tp.show ? "<h3>Tape Print</h3><p>Tape Print is a same-term constellation. We do not publish the sleeve weights. The labeled venue price above is the auditable number. Tape "+money(tp.usd_per_gpu_hr)+" · n="+tp.n+".</p>" : "";
  document.getElementById("dbody").innerHTML =
    "<h3>Quotes</h3><table class=\\"qtable\\"><thead><tr><th>Venue / term</th><th>$ / GPU-hr</th><th>As-of · source</th></tr></thead><tbody>"+qrows+"</tbody></table>"+
    sparkH+tapeH+
    "<h3>Availability</h3><p>"+c.availability+"</p>"+
    "<h3>Demand note</h3><p>"+c.scarcity+"</p>"+
    extra+
    "<h3>What we cannot show</h3><ul>"+noshow+"</ul>";
  scrim.hidden = false;
  requestAnimationFrame(function(){{ drawer.classList.add("on"); scrim.classList.add("on"); }});
  drawer.setAttribute("aria-hidden","false");
  if(location.hash !== "#"+id) history.replaceState(null,"","#"+id);
}}
document.querySelectorAll("tr.chiprow").forEach(function(r){{
  r.addEventListener("click", function(){{ openD(r.dataset.id); }});
  r.addEventListener("keydown", function(e){{ if(e.key==="Enter"||e.key===" "){{ e.preventDefault(); openD(r.dataset.id); }} }});
  r.querySelectorAll("a,.pop,.termx").forEach(function(a){{ a.addEventListener("click", function(e){{ e.stopPropagation(); }}); }});
}});
function restripe(){{
  var i=0;
  document.querySelectorAll("#tape tr.chiprow").forEach(function(r){{
    r.classList.remove("odd","even");
    if(r.style.display==="none") return;
    r.classList.add(i%2?"even":"odd");
    i++;
  }});
}}
restripe();
document.getElementById("dclose").onclick = closeD;
scrim.onclick = closeD;
document.addEventListener("keydown", function(e){{ if(e.key==="Escape") closeD(); }});
function routeChip(){{ var hid=location.hash.slice(1); if(hid && document.getElementById(hid)) openD(hid); }}
if(location.hash) routeChip();
window.addEventListener("hashchange", routeChip);

document.querySelectorAll(".chips .chip").forEach(function(ch){{
  ch.onclick = function(){{
    document.querySelectorAll(".chips .chip").forEach(function(x){{ x.classList.remove("on"); }});
    ch.classList.add("on");
    var v = ch.getAttribute("data-v");
    document.querySelectorAll("tr.chiprow").forEach(function(r){{
      r.style.display = (!v || r.dataset.vendor===v) ? "" : "none";
    }});
    restripe();
  }};
}});

(function(){{
  var tb = document.querySelector("#tape tbody");
  var state = {{ key:"rank", dir:1, type:"num" }};
  document.querySelectorAll("#tape th[data-sort]").forEach(function(th){{
    th.onclick = function(){{
      var key = th.getAttribute("data-sort"), type = th.getAttribute("data-type");
      if(state.key===key) state.dir *= -1; else {{ state.key=key; state.dir = key==="rank"||key==="score"||key==="price" ? 1 : 1; }}
      state.type = type;
      document.querySelectorAll("#tape th").forEach(function(h){{ h.classList.remove("sorted"); h.querySelector(".arr").textContent=""; }});
      th.classList.add("sorted"); th.querySelector(".arr").textContent = state.dir>0 ? "▼" : "▲";
      var rows = [].slice.call(tb.querySelectorAll("tr.chiprow"));
      rows.sort(function(a,b){{
        var av = a.querySelector('[data-col="'+key+'"]');
        var bv = b.querySelector('[data-col="'+key+'"]');
        if(type==="num"){{
          var map={{price:"price",score:"score",rank:"rank",d30:"d30",d90:"d90",d1y:"d1y",d3y:"d3y",d7:"d7",venues:"venues",m1:"m1",q1:"q1",y1:"y1",y3:"y3"}};
          var an = parseFloat(a.dataset[map[key]||"rank"]);
          var bn = parseFloat(b.dataset[map[key]||"rank"]);
          if(isNaN(an)) an = -Infinity; if(isNaN(bn)) bn = -Infinity;
          return (an-bn)*state.dir;
        }}
        return (av.textContent.trim().toLowerCase()).localeCompare(bv.textContent.trim().toLowerCase())*state.dir;
      }});
      rows.forEach(function(r){{ tb.appendChild(r); }});
      restripe();
    }};
  }});
}})();

var tm=document.querySelector('meta[name="theme-color"]'), tg=document.getElementById("themetog");
function cur(){{return document.documentElement.getAttribute("data-theme")==="dark"?"dark":"light"}}
function setT(t,sv){{document.documentElement.setAttribute("data-theme",t);
if(sv){{try{{localStorage.setItem("cnw_theme",t)}}catch(e){{}}}}
tm.content=t==="dark"?"#171511":"#f7f4ee";tg.setAttribute("aria-label",t==="dark"?"Switch to day mode":"Switch to night mode");}}
tg.onclick=function(){{setT(cur()==="dark"?"light":"dark",true)}};
setT(cur(),false);
{fnav_script("silicon")}
{sub_script()}
</script>
</body>
</html>'''

open(os.path.join(ROOT, "silicon.html"), "w").write(PAGE)

rss_items = "".join(f'''
  <item>
    <title>{html.escape(c["name"])} · {html.escape(display_px(c["display"]))} {html.escape(c["display"]["label"])}</title>
    <link>https://compute.world/silicon.html#{c["id"]}</link>
    <guid isPermaLink="false">compute.world/silicon#{c["id"]}</guid>
    <pubDate>{datetime.strptime(S["updated"], "%Y-%m-%d").strftime("%a, %d %b %Y")} 12:00:00 GMT</pubDate>
    <description>{html.escape(c["name"])} ({html.escape(c["vendor"])}, {html.escape(c["memory"])}): display {html.escape(display_px(c["display"]))} {html.escape(c["display"]["label"])} as of {html.escape(nice_date(c["display"]["as_of"]))}. {html.escape(c.get("also", {}).get("text") or "")}. Score {c["score"]:.2f}. {html.escape(c["scarcity"])} More: https://compute.world/silicon.html#{c["id"]}</description>
  </item>''' for c in chips)

RSS = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>The Silicon Tape · compute.world</title>
  <link>https://compute.world/silicon.html</link>
  <description>Public AI accelerator rental tape. Snapshot {S["updated"]}. SA prints as-of April 2026. Not a market cap.</description>
  <language>en</language>{rss_items}
</channel></rss>'''
open(os.path.join(ROOT, "silicon.xml"), "w").write(RSS)
print(f"silicon.html + silicon.xml generated: {len(chips)} chips, snapshot {S['updated']}")
