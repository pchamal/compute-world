#!/usr/bin/env python3
"""v1.5 public desk: homepage, country pages, silicon chip pages.

Run from repo root or src/:
  python3 src/build_desk.py

Writes index.html, country/{slug}/index.html, silicon/{slug}/index.html,
map.svg, fonts/, flags/ into the repo root (Cloudflare Pages output) and
src/deploy/. Data is assembled from live JSON — not the sample HTML literals.
"""
from __future__ import annotations

import json
import os
import re
import shutil
from html import escape as esc

from desk_chrome import (
    SITE,
    footer,
    fmt_date,
    fmt_date_long,
    head,
    masthead,
    mon_year,
    tiny_js,
)
from desk_data import TIER, TIER_DEF, TIER_PLAIN, assemble, headline_rail
from seo import DEFAULT_SITEMAP, robots_txt, sitemap_xml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DESK = os.path.join(HERE, "desk")


def read(name):
    with open(os.path.join(DESK, name), encoding="utf-8") as f:
        return f.read()


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def num(n):
    return f"{int(n):,}"


def fmt_b(b):
    if b >= 1000:
        return f"${b / 1000:.1f}T"
    if b >= 10:
        return f"${round(b)}B"
    if b >= 1:
        return f"${b:.1f}B"
    return "under $1B"


def fmt_t(t):
    return f"${t}T" if t >= 1 else f"${round(t * 1000)}B"


def fmt_range(c):
    if c["ceilHi"] == 0:
        return "$0"
    if c["ceilLo"] >= 1:
        return f"${c['ceilLo']} to {c['ceilHi']}T"
    return f"{fmt_t(c['ceilLo'])} to {fmt_t(c['ceilHi'])}"


def fmt_gw(gw):
    return f"{gw:.1f} GW" if gw >= 1 else f"{round(gw * 1000)} MW"


def fmt_usd(v):
    if v is None:
        return "—"
    return f"${round(v * 100) / 100:.2f}"


def flag_img(c, root, cls=""):
    return (
        f'<img class="flag {cls}" src="{root}flags/{esc(c["flag"])}.svg" '
        f'alt="Flag of {esc(c["name"])}" width="24" height="18" loading="lazy" '
        f'data-code="{esc(c["iso2"])}" onerror="flagFail(this)">'
    )


VENDOR_CODE = {
    "NVIDIA": "NV", "AMD": "AMD", "Google": "G", "Huawei": "HW",
    "Cerebras": "CB", "Amazon": "AWS", "Groq": "GQ",
}


def logo_el(name, domains, cls=""):
    d = domains.get(name)
    ini = VENDOR_CODE.get(name) or re.sub(r"[^A-Z0-9]", "", name)[:3] or name[:2].upper()
    img = (
        f'<img src="https://www.google.com/s2/favicons?domain={esc(d)}&sz=64" alt="" '
        f'loading="lazy" onerror="logoFail(this)">'
        if d else ""
    )
    return f'<span class="logo {cls}" title="{esc(name)}">{img}<span>{esc(ini)}</span></span>'


def venue_el(name, domains):
    return f'<span class="venue">{logo_el(name, domains)}<span>{esc(name)}</span></span>'


def map_svg():
    p = os.path.join(DESK, "map.svg")
    with open(p, encoding="utf-8") as f:
        return f.read().strip()


def homepage(data, css, app_js, rail, svg):
    asof = data["config"]["asOf"]
    countries = data["countries"]
    chips = data["chips"]
    top10 = sorted(countries, key=lambda c: c["rank"])[:10]
    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": SITE + "/#website",
                "url": SITE + "/",
                "name": "compute.world",
                "alternateName": ["The Compute Net Worth Index", "The Silicon Tape"],
                "description": "Countries, compute and silicon: the world's compute index. "
                               f"{rail['n_countries']} countries priced by compute net worth; "
                               f"{rail['n_chips']} AI accelerators with sourced rental prices.",
                "publisher": {"@id": SITE + "/#org"},
                "inLanguage": "en",
            },
            {
                "@type": "Organization",
                "@id": SITE + "/#org",
                "name": "compute.world",
                "url": SITE + "/",
                "logo": SITE + "/og.png",
                "founder": {"@type": "Person", "name": "Pukar C. Hamal"},
                "foundingDate": "2026-08-10",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "San Francisco",
                    "addressRegion": "CA",
                    "addressCountry": "US",
                },
            },
            {
                "@type": "ItemList",
                "name": "Countries by unlockable compute value",
                "itemListOrder": "https://schema.org/ItemListOrderDescending",
                "numberOfItems": len(countries),
                "itemListElement": [
                    {"@type": "ListItem", "position": i + 1, "name": c["name"],
                     "url": f"{SITE}/country/{c['slug']}/"}
                    for i, c in enumerate(top10)
                ],
            },
        ],
    }, ensure_ascii=False)
    body = f'''
<body>
<a class="sr" href="#board">Skip to the rankings</a>
{masthead("", asof)}
<main id="top"><div class="wrap">

<section class="lede" aria-label="Introduction">
  <div>
    <h1>Countries. Compute. Silicon.<span class="soft">And the wires between them.</span></h1>
    <p>Every country has a compute net worth: the AI compute its own energy could host. <span class="more-lede">A kilowatt-hour sold as raw power earns about five cents; run through a contracted GPU cloud it earns one to two dollars. </span>This index prices what each nation could host, counts what it actually runs, and prints what the silicon rents for, from sourced, dated quotes only.</p>
  </div>
  <div class="ledger" aria-label="Headline figures"><dl>
    <div><dt>{esc(rail["ceiling"])}</dt><dd>Ceiling: every identified watt hosting compute at today's price of a gigawatt, $60 to 80B.</dd></div>
    <div><dt>{esc(rail["unlockable"])}</dt><dd>Unlockable: the slice of that ceiling underwriters could credibly sign today.</dd></div>
    <div><dt>{esc(rail["live"])}</dt><dd>Live compute: what actually runs. {esc(rail["tap_pct"])} of the ceiling, {esc(rail["top2_share"])} of it in two countries.</dd></div>
    <div><dt>{rail["n_countries"]} + {rail["n_chips"]}</dt><dd>Countries priced, and accelerators on the price tape. Updated every weekday.</dd></div>
  </dl></div>
</section>

<section id="board" class="board-grid" aria-label="Rankings">
  <div class="board">
    <div class="board-head">
      <div class="tabs" role="tablist" aria-label="Index">
        <button class="tab" role="tab" id="tab-countries" aria-selected="true" aria-controls="panel-board" data-tab="countries">Countries</button>
        <button class="tab" role="tab" id="tab-silicon" aria-selected="false" aria-controls="panel-board" data-tab="silicon">Silicon prices</button>
      </div>
      <div class="seg" id="viewSeg" role="group" aria-label="View"><button data-view="list" aria-pressed="true">List</button><button data-view="map" aria-pressed="false">Map</button></div>
      <div class="tools">
        <label class="sr" for="lens">Sort by</label><select class="select" id="lens"></select>
        <label class="sr" for="topn">Rows</label><select class="select" id="topn"><option value="10">Top 10</option><option value="25">Top 25</option><option value="all">All</option></select>
        <button class="btn" id="csvBtn" title="Download the rows you are looking at as CSV"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2v8m0 0L5 7m3 3l3-3M3 12v2h10v-2" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>CSV</button>
        <button class="btn" id="linkBtn" title="Copy a link to this view"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6.5 9.5a3 3 0 004.2 0l2-2a3 3 0 00-4.2-4.2l-1 1M9.5 6.5a3 3 0 00-4.2 0l-2 2a3 3 0 004.2 4.2l1-1" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>Link</button>
      </div>
    </div>
    <div id="panel-board" role="tabpanel" aria-labelledby="tab-countries">
      <div id="listWrap"><div class="colhead" id="colhead"></div><ol class="rows" id="rows"></ol></div>
      <div id="mapWrap" class="mapview" hidden>{svg}<div class="maplegend" id="maplegend"></div><div class="maptip" id="maptip"></div></div>
    </div>
    <div class="board-foot" id="boardFoot"></div>
  </div>
  <aside class="rail" aria-label="Movers and signals">
    <div class="rail-block"><h3>Movers</h3><p class="sub">Conversion score, change since the 19 Aug snapshot</p><ol class="movers" id="movers"></ol></div>
    <div class="rail-block"><h3>Latest signals</h3><p class="sub">What moved a country this week</p><ul class="wire" id="wire"></ul><a class="rail-more" href="{SITE}/wire.html">All signals on the Wire</a></div>
  </aside>
</section>

<section id="trends" class="section">
  <div class="section-head"><div><h2>Trends</h2><p class="deck">Observed snapshots only. The index never interpolates between prints, so a line here is a set of dated facts, not a curve fitted to them.</p></div><div class="side" id="histDepth"></div></div>
  <div class="charts">
    <div class="chart wide">
      <div class="chart-head"><div><h3>Conversion score: who is actually converting</h3><p>0 to 100. Moves when a country does something in public.</p></div><div class="chips" id="rzChips"></div></div>
      <div id="rzChart"></div>
      <div class="scrub"><span>As of</span><input type="range" id="rzScrub" min="0" max="1" value="1" step="1" aria-label="Snapshot date"><b id="rzDate"></b></div>
      <p class="caption" id="rzCaption"></p>
    </div>
    <div class="chart wide">
      <div class="chart-head"><div><h3>What an hour of silicon costs</h3><p>Same scale across the three, so the eye can compare. Dated prints, same venue, same term. Steps, not candles.</p></div></div>
      <div class="multiples" id="multiples"></div>
    </div>
  </div>
</section>

<section id="projects" class="section">
  <div class="section-head"><div><h2>Projects on the ground</h2><p class="deck">Sovereign AI factories, as reported. The three stalled projects all stalled on power, which is the whole thesis in three rows.</p></div></div>
  <div class="feed"><div class="feed-head"><div class="chips" id="statusChips"></div><span class="count" id="precCount"></span></div><ul class="plist" id="plist"></ul></div>
</section>

<section id="method" class="section">
  <div class="section-head"><div><h2>How the numbers are made</h2><p class="deck">Three prices per country, read together. One is an option, two are counts. The gap between them is the country's reform agenda, priced.</p></div><div class="side"><a href="{SITE}/params.json">Every parameter is an editable cell</a></div></div>
  <div class="defs">
    <div class="def"><h3>Ceiling</h3><p class="plain">What the endowment could host</p><div class="formula">Resource ceiling (GW) × $60 to 80B per GW</div><p>Every technically identified watt, built and hosting compute at today's prices. Called a ceiling because that is what it is. Rerun it at the analyst build cost of $35B and the ordering survives.</p></div>
    <div class="def"><h3>Unlockable</h3><p class="plain">The bankable slice</p><div class="formula">Firm untapped GW × $50B × Readiness</div><p>Nameplate power converted to 24/7-grade by source, valued at build cost, then discounted by everything that makes an underwriter hesitate. An asset value, not revenue, and not a forecast that anyone builds it.</p></div>
    <div class="def"><h3>Live compute</h3><p class="plain">Gross Domestic Compute, GDC</p><div class="formula">Live datacenter GW × $50B</div><p>What actually runs today. GDC is to compute what GDP is to output. Markets below the top 35 are estimates and shown in grey. Valuing old colocation halls at the AI-factory price is a disclosed simplification.</p></div>
  </div>
  <div class="method-grid">
    <div class="stack"><h3>Readiness is a discount rate</h3><p>Eight components, weights summing to 100. Democracy is shown but unweighted, on purpose.</p><div class="stackbar" id="stackbar"></div><div class="stacklegend" id="stacklegend"></div></div>
    <div class="rules"><h3>Rules of the price tape</h3><ol>
      <li><b>Every price carries its label.</b> Venue, term, date. On-demand, spot, reserved and capacity blocks are never averaged together.</li>
      <li><b>A missing number is a dash.</b> Never an invented 0%, never a guessed discount off on-demand, never a converted token price.</li>
      <li><b>Change needs two dated prints.</b> Same venue, same term, same configuration, or it does not print.</li>
      <li><b>Ranks are ordinal hygiene.</b> Liquidity 40, demand 35, frontier 25. Not a valuation.</li>
      <li><b>History is append-only.</b> One snapshot per index per day, kept forever, never rewritten.</li>
    </ol></div>
  </div>
</section>

<section id="profiles" class="section">
  <div class="section-head"><div><h2>Country profiles</h2><p class="deck">All {rail["n_countries"]} countries, each with a page of its own: the three numbers, what holds it back, projects on the ground, and a line you can cite.</p></div></div>
  <div class="gaz-tools"><input class="search" id="gazSearch" type="search" placeholder="Search a country (press /)" aria-label="Search countries"><div class="chips" id="regionChips"></div></div>
  <div class="cards" id="cards"></div>
</section>

<section id="data" class="section">
  <div class="section-head"><div><h2>Use this data</h2><p class="deck">Free with attribution for research, journalism and personal use. Commercial products, APIs and bulk redistribution take a licence.</p></div><div class="side"><a href="https://github.com/pchamal/compute-world/blob/main/LICENSE.md">The one-page licence</a></div></div>
  <div class="use">
    <div class="use-block"><h3>Cite</h3><p>One line, any style guide.</p><div class="codebox" id="citeBox"></div><button class="btn" data-copy="#citeBox">Copy citation</button></div>
    <div class="use-block"><h3>Embed the rankings</h3><p>Attribution built in, updates itself.</p><div class="codebox" id="embedBox">&lt;iframe src="{SITE}/embed.html?n=10&amp;sort=u" width="100%" height="520" style="border:1px solid #1B222A" title="The Compute Net Worth Index"&gt;&lt;/iframe&gt;</div><button class="btn" data-copy="#embedBox">Copy embed code</button></div>
    <div class="use-block"><h3>Download</h3><p>CSV exports the rows you are looking at. JSON is the full record, machine-readable.</p><div class="links"><a href="{SITE}/data.json">data.json, countries</a><a href="{SITE}/silicon.json">silicon.json, prices</a><a href="{SITE}/silicon-history.json">silicon-history.json</a><a href="{SITE}/rank-history.json">rank-history.json</a><a href="{SITE}/params.json">params.json</a><a href="{SITE}/llms.txt">llms.txt</a></div></div>
    <div class="use-block"><h3>Follow</h3><p>Weekday brief, one feed per index. Corrections and new prints go to the desk.</p><div class="links"><a href="{SITE}/brief">The brief</a><a href="{SITE}/brief.xml">RSS, brief</a><a href="{SITE}/silicon.xml">RSS, silicon</a><a href="{SITE}/wire.xml">RSS, signals</a><a href="{SITE}/contact.html">Send a correction</a></div></div>
  </div>
</section>

<section class="section" aria-label="Also on compute.world">
  <div class="section-head"><h2>Also on compute.world</h2></div>
  <div class="also">
    <a href="{SITE}/silicon.html"><b>The full price tape</b><small>Term book, every venue quote, dated history</small></a>
    <a href="{SITE}/neoclouds.html"><b>GPU clouds</b><small>Who rents GPUs, by region and silicon</small></a>
    <a href="{SITE}/hyperscalers.html"><b>Hyperscalers</b><small>271 cloud locations with GPUs</small></a>
    <a href="{SITE}/inference.html"><b>Inference providers</b><small>Who sells tokens, on what</small></a>
    <a href="{SITE}/campuses.html"><b>Campuses</b><small>Named sites on a globe, a register not a census</small></a>
    <a href="{SITE}/data-centers.html"><b>Data centers</b><small>Campus power, water, land, tax, jobs</small></a>
  </div>
</section>

</div></main>
{footer()}
<dialog class="sheet" id="sheet" aria-labelledby="sheetTitle">
  <div class="sheet-head"><span id="sheetMark"></span><span class="name" id="sheetTitle"></span><button class="x" id="sheetClose" aria-label="Close"><svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true"><path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></button></div>
  <div class="sheet-body" id="sheetBody"></div>
  <div class="sheet-foot" id="sheetFoot"></div>
</dialog>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script>const DATA={json.dumps(data, ensure_ascii=False)};</script>
<script>{app_js}</script>
</body>
</html>'''
    return head(
        "compute.world — Countries. Compute. Silicon. The world's compute index",
        "Which countries hold the electrons, what the silicon rents for, and who is converting. "
        f"{rail['n_countries']} countries priced by compute net worth, {rail['n_chips']} AI accelerators "
        "with sourced rental prices, updated weekdays.",
        SITE + "/",
        "",
        css,
        jsonld=jsonld,
    ) + body


def three_bars(c):
    rows = [
        ("Ceiling, high end", c["ceilHi"] * 1000, fmt_t(c["ceilHi"]), "ceil"),
        ("Unlockable", c["unlock"], fmt_b(c["unlock"]), ""),
        ("Live compute", c["gdc"], fmt_b(c["gdc"]), ""),
    ]
    mx = max(r[1] for r in rows) or 1
    w, h, left, right = 720, 112, 150, 90
    parts = []
    for i, r in enumerate(rows):
        y = 10 + i * 34
        bw = max(0, (r[1] / mx) * (w - left - right))
        parts.append(
            f'<text class="lab" x="{left - 10}" y="{y + 13}" text-anchor="end">{esc(r[0])}</text>'
            f'<rect class="{r[3]}" x="{left}" y="{y}" width="{bw:.1f}" height="18" rx="2"/>'
            f'<text class="val" x="{left + bw + 8:.1f}" y="{y + 13}">{esc(r[2])}</text>'
        )
    return (
        f'<div class="threebars"><svg viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="Ceiling, unlockable and live compute for {esc(c["name"])}, same scale">'
        f'{"".join(parts)}</svg></div>'
    )


def answer_text(c, asof):
    if c["id"] == "SGP":
        return (
            f"<b>Singapore runs about {fmt_gw(c['liveGW'])} of live datacenter capacity</b> as of "
            f"{fmt_date_long(asof)}, a Gross Domestic Compute of {fmt_b(c['gdc'])}, with no domestic "
            f"energy resource ceiling to speak of. It is an incumbent: already running significant compute, "
            f"already priced in, ranked {c['rank']} of 108 by unlockable value because there is nothing "
            f"left to unlock at home."
        )
    est = " (an estimate)" if c.get("gdcEst") else ""
    return (
        f"<b>{esc(c['name'])} runs about {fmt_gw(c['liveGW'])} of live datacenter capacity</b> as of "
        f"{fmt_date_long(asof)}, a Gross Domestic Compute of {fmt_b(c['gdc'])}{est}. Its identified energy "
        f"resource could host about {c['ceilGW']} GW of AI compute, a ceiling worth {fmt_range(c)} at today's "
        f"price of a gigawatt, about {c['xgdp']} times its ${num(c['gdp'])}B GDP. The bankable slice today, "
        f"discounted mainly for {esc(c['disc'])}, is {fmt_b(c['unlock'])}, or ${num(c['perPerson'])} per person. "
        f"{esc(c['name'])} is {TIER_PLAIN[c['tier']]}, ranked {c['rank']} of 108 countries by unlockable value."
    )


def country_page(c, data, css, domains):
    asof = data["config"]["asOf"]
    countries = data["countries"]
    chips = data["chips"]
    root = "../../"
    url = f"{SITE}/country/{c['slug']}/"
    title = (
        f"{c['name']} compute capacity ({mon_year(asof)}): {fmt_gw(c['liveGW'])} live, "
        f"{c['ceilGW']} GW ceiling | compute.world"
    )
    description = (
        f"{c['name']} runs about {fmt_gw(c['liveGW'])} of live datacenter capacity as of {fmt_date(asof)}, "
        f"against an identified ceiling of {c['ceilGW']} GW worth {fmt_range(c)}. Rank {c['rank']} of 108 "
        f"by unlockable value; {TIER[c['tier']].lower()}."
    )
    if len(description) > 158:
        description = re.sub(r"[,;: ]+\S*$", "", description[:155]) + "…"
    peers = sorted([x for x in countries if x["region"] == c["region"]], key=lambda x: x["rank"])
    region_rank = next(i for i, x in enumerate(peers, 1) if x["id"] == c["id"])
    projects = [p for p in data["precedents"] if p[0] == c["id"]]
    ranked = sorted(countries, key=lambda x: x["rank"])
    idx = next(i for i, x in enumerate(ranked) if x["id"] == c["id"])
    prev = ranked[idx - 1] if idx else None
    nxt = ranked[idx + 1] if idx + 1 < len(ranked) else None
    dlt = c["rz"] - c["rz0"]
    faqs = [
        (
            f"How much data center capacity does {c['name']} have?",
            f"{c['name']} runs about {fmt_gw(c['liveGW'])} of live datacenter IT capacity as of {fmt_date(asof)}"
            + (
                ", an estimate: country totals below the top 35 markets are estimated"
                if c.get("gdcEst")
                else ", compiled from SemiAnalysis, Cushman & Wakefield, Rystad, Knight Frank and national reports"
            )
            + f". Valued at $50B per gigawatt, that is a Gross Domestic Compute of {fmt_b(c['gdc'])}.",
        ),
        (
            f"What is {c['name']}'s compute net worth?",
            (
                f"{c['name']} has no meaningful domestic energy resource ceiling, so its compute net worth is "
                f"counted entirely in what it already runs: {fmt_b(c['gdc'])} of live compute."
                if c["ceilHi"] == 0
                else (
                    f"The ceiling is {fmt_range(c)}: {c['ceilGW']} GW of identified hydro, geothermal, solar, wind "
                    f"and surplus fossil resource valued at $60 to 80B per gigawatt, NVIDIA's all-in figure for an "
                    f"AI factory. That is {c['xgdp']} times {c['name']}'s ${num(c['gdp'])}B GDP. The bankable slice "
                    f"today, after a readiness discount of {round(c['readiness'] * 100)}%, is {fmt_b(c['unlock'])}."
                )
            ),
        ),
        (
            f"What holds {c['name']} back from converting its energy into compute?",
            f"Readiness scores {round(c['readiness'] * 100)}% on an eight-part discount stack (governance, stability, "
            f"GPU access, grid, fiber, momentum, physical conditions and capital access). For {c['name']} the binding "
            f"discounts are {c['disc']}. It has built {c['built']}% of its ceiling as generating capacity, and its "
            f"conversion score is {c['rz']} of 100"
            + (f" ({'+' if dlt > 0 else ''}{dlt} since 19 August)" if dlt else "")
            + ".",
        ),
        (
            f"How does {c['name']} compare with its neighbours?",
            f"{c['name']} ranks {c['rank']} of 108 countries by unlockable value, and {region_rank} of {len(peers)} "
            f"in {c['region']}. The regional leader is {peers[0]['name']} at {fmt_b(peers[0]['unlock'])} unlockable "
            f"and {fmt_b(peers[0]['gdc'])} of live compute.",
        ),
    ]
    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": url,
                "url": url,
                "name": title,
                "description": description,
                "datePublished": "2026-08-10",
                "dateModified": asof,
                "isPartOf": {"@id": SITE + "/#website"},
                "about": {"@id": url + "#place"},
                "inLanguage": "en",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "compute.world", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Countries", "item": SITE + "/#countries"},
                    {"@type": "ListItem", "position": 3, "name": c["name"], "item": url},
                ],
            },
            {"@type": "Country", "@id": url + "#place", "name": c["name"], "sameAs": [c["wiki"]]},
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in faqs
                ],
            },
        ],
    }, ensure_ascii=False)
    chg = (
        f"{'+' if dlt > 0 else ''}{dlt} since 19 Aug."
        if dlt
        else "Unchanged since 19 Aug."
    )
    kv = [
        ["Live datacenter capacity", fmt_gw(c["liveGW"]),
         "IT capacity, mid-2026. Estimate: below the top 35 markets." if c.get("gdcEst")
         else "IT capacity, mid-2026, compiled from industry and national sources."],
        ["Live compute (GDC)", fmt_b(c["gdc"]), "Live GW × $50B, the central price of an AI factory."],
        ["Resource ceiling", f"{c['ceilGW']} GW", "Identified hydro, geothermal, solar, wind and surplus fossil resource."],
        ["Ceiling value", fmt_range(c), "Ceiling GW × $60 to 80B per GW, NVIDIA's all-in figure."],
        ["Ceiling as a multiple of GDP", f"{c['xgdp']}×", f"High end over nominal GDP of ${num(c['gdp'])}B (IMF)."],
        ["Unlockable value", fmt_b(c["unlock"]), "Firm untapped GW × $50B × readiness. The bankable slice."],
        ["Unlockable per person", f"${num(c['perPerson'])}", "IMF population, 2026."],
        ["Built", f"{c['built']}%", "Hydro and geothermal already installed, over the ceiling."],
        ["Readiness", f"{round(c['readiness'] * 100)}%", f"Eight-part discount. Binding: {c['disc']}."],
        ["Conversion score", str(c["rz"]), f"0 to 100. {chg}"],
        ["Tier", TIER[c["tier"]], TIER_DEF[c["tier"]]],
        ["Rank", f"{c['rank']} of 108", f"By unlockable value. {region_rank} of {len(peers)} in {c['region']}."],
    ]
    kv_rows = []
    for r in kv:
        extra = " est" if r[0].startswith("Live") and c.get("gdcEst") else ""
        kv_rows.append(
            f'<tr><th scope="row">{esc(r[0])}</th><td class="v{extra}">{esc(r[1])}</td><td class="d">{esc(r[2])}</td></tr>'
        )
    kv_html = "".join(kv_rows)
    if projects:
        proj_html = (
            '<table class="peers"><thead><tr><th>Project</th><th>Scale</th><th>Status</th><th class="r">Date</th></tr></thead><tbody>'
            + "".join(
                f'<tr><td>{esc(p[1])}</td><td>{esc(p[2])}</td><td><span class="status {p[3]}">{p[3]}</span></td>'
                f'<td class="r">{esc(p[4])}</td></tr>'
                for p in projects
            )
            + "</tbody></table>"
        )
    else:
        proj_html = (
            f'<p class="small">No sovereign AI factory for {esc(c["name"])} is on the register yet. '
            f'Announcements, contracts and stalls are tracked as reported; '
            f'<a href="{SITE}/contact.html">send one to the desk</a>.</p>'
        )
    peer_rows = []
    for x in peers:
        me = ' class="me"' if x["id"] == c["id"] else ""
        gest = " est" if x.get("gdcEst") else ""
        peer_rows.append(
            f'<tr{me}><td>{x["rank"]}</td>'
            f'<td><span class="who">{flag_img(x, root)}<a href="{root}country/{x["slug"]}/">{esc(x["name"])}</a></span></td>'
            f'<td class="r">{fmt_b(x["unlock"])}</td>'
            f'<td class="r{gest}">{fmt_b(x["gdc"])}</td>'
            f'<td class="r">{round(x["readiness"] * 100)}%</td>'
            f'<td><span class="tier tier-{x["tier"]}">{TIER[x["tier"]]}</span></td></tr>'
        )
    peers_html = "".join(peer_rows)
    wanted = ["nvidia-h100-sxm-80gb", "nvidia-b200-sxm6", "nvidia-a100-sxm-80gb"]
    strip = []
    for cid in wanted:
        s = next((x for x in chips if x["id"] == cid), None)
        if not s:
            continue
        strip.append(
            f'<a href="{root}silicon/{s["slug"]}/">{logo_el(s["vendor"], domains, "lg")}'
            f'<span><b>{esc(s["name"])} {fmt_usd(s["disp"]["usd"])}/hr</b>'
            f'<small>{esc(s["disp"]["venue"])}, {esc(s["disp"]["term"])}, {fmt_date(s["disp"]["asOf"])}</small></span></a>'
        )
    sig_html = ""
    if c.get("signal"):
        sig_html = (
            f'<h2>Latest signal</h2><div class="signal {c["dir"]}"><span class="dot"></span>'
            f'<div>{esc(c["signal"])}<span class="m">Arrows mark direction from recent items on the Wire.</span></div></div>'
        )
    prev_html = (
        f'<a href="{root}country/{prev["slug"]}/">{flag_img(prev, root)}'
        f'<span><small>Rank {prev["rank"]}</small><b>{esc(prev["name"])}</b></span></a>'
        if prev else "<span></span>"
    )
    next_html = (
        f'<a class="next" href="{root}country/{nxt["slug"]}/"><span><small>Rank {nxt["rank"]}</small>'
        f'<b>{esc(nxt["name"])}</b></span>{flag_img(nxt, root)}</a>'
        if nxt else ""
    )
    body = f'''
<body>
{masthead(root, asof, current="Countries")}
<main><div class="wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="{root}index.html">compute.world</a><span>›</span><a href="{root}index.html#board">Countries</a><span>›</span><span>{esc(c["name"])}</span></nav>
<article class="article">
  <p class="kicker" style="margin-top:18px">Country profile · Rank {c["rank"]} of 108 · <span class="tier tier-{c["tier"]}">{TIER[c["tier"]]}</span></p>
  <div class="title">{flag_img(c, root, "xl")}<h1>{esc(c["name"])} compute capacity</h1></div>
  <p class="answer">{answer_text(c, asof)}</p>
  <div class="meta"><span>Updated {fmt_date(asof)}</span><span>·</span><a href="#cite">Cite this page</a><span>·</span><a href="{SITE}/data.json">Data</a><span>·</span><a href="{esc(c["wiki"])}" rel="noopener">{esc(c["name"])} on Wikipedia</a></div>

  <h2>Key numbers</h2>
  <table class="kv"><tbody>{kv_html}</tbody></table>

  <h2>Three numbers, one scale</h2>
  <p class="small">Ceiling is what the endowment could host; unlockable is the slice underwriters would sign today; live compute is what runs. Drawn on one linear scale on purpose: the gap is the point.</p>
  {three_bars(c)}

  {sig_html}

  <h2>Projects on the ground</h2>
  {proj_html}

  <h2>{esc(c["region"])}: how {esc(c["name"])} compares</h2>
  <table class="peers"><thead><tr><th>#</th><th>Country</th><th class="r">Unlockable</th><th class="r">Live compute</th><th class="r">Readiness</th><th>Tier</th></tr></thead><tbody>{peers_html}</tbody></table>

  <h2>What compute costs right now</h2>
  <p class="small">The price of the silicon a country would host, from the tape. Labeled buy-now prints from named venues.</p>
  <div class="pricestrip">{"".join(strip)}</div>

  <h2>Questions people ask</h2>
  <div class="faq">{"".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faqs)}</div>

  <h2 id="cite">Cite this page</h2>
  <div class="cite"><div class="codebox" id="citeBox">Hamal, P. (2026). The Compute Net Worth Index: {esc(c["name"])}. compute.world. {url} Retrieved {fmt_date(asof)}.</div><button class="btn primary" data-copy="#citeBox">Copy citation</button></div>
  <p class="small" style="margin-top:12px">Free with attribution for research, journalism and personal use. Method, sources and every parameter: <a href="{root}index.html#method">how the numbers are made</a>.</p>

  <nav class="nextprev" aria-label="Neighbouring ranks">{prev_html}{next_html}</nav>
</article>
</div></main>
{footer()}
{tiny_js()}
</body>
</html>'''
    return head(title, description, url, root, css, jsonld=jsonld, og_type="article",
                image=f"{SITE}/og.png") + body


def _date_num(iso):
    return int(_dt_from(iso).timestamp() * 1000)


def _dt_from(iso):
    from datetime import datetime, timezone
    s = str(iso or "")
    if "H2" in s:
        year = "".join(ch for ch in s if ch.isdigit())[:4] or "2023"
        return datetime(int(year), 10, 1, tzinfo=timezone.utc)
    p = s.split("-")
    if len(p) == 2 and p[0].isdigit() and p[1].isdigit():
        return datetime(int(p[0]), int(p[1]), 15, tzinfo=timezone.utc)
    if len(p) >= 3 and p[0].isdigit() and p[1].isdigit() and p[2][:2].isdigit():
        return datetime(int(p[0]), int(p[1]), int(p[2][:2]), tzinfo=timezone.utc)
    return datetime(2020, 1, 1, tzinfo=timezone.utc)


def path_chart(s, data):
    asof = data["config"]["asOf"]
    key = next((k for k in data["pricePaths"] if k.split()[0] == s["name"].split()[0]), None)
    series = data["pricePaths"][key] if key else (
        [{"name": f"{s['disp']['venue']} {s['disp']['term']}", "short": s["disp"]["venue"], "pts": s["spark"]}]
        if s.get("spark") else []
    )
    if not series:
        return ""
    w, h, left, right, top, bottom = 720, 240, 44, 120, 14, 28
    all_pts = [p for sr in series for p in sr["pts"]]
    xs = [_date_num(p[0]) for p in all_pts]
    x0, x1 = min(xs), _date_num(asof)
    y_max = max(1, int((max(p[1] for p in all_pts) + 1) // 2 * 2) or 2)

    def sx(iso):
        return left + (_date_num(iso) - x0) / max(1, (x1 - x0)) * (w - left - right)

    def sy(v):
        return top + (h - top - bottom) - v / y_max * (h - top - bottom)

    cols = ["#1F4FD8", "#9B2C2C", "#1E7B4F", "#8A5A12"]
    g = (
        f'<g class="frame"><line x1="{sx(all_pts[0][0]):.1f}" x2="{sx(asof):.1f}" y1="{sy(0):.1f}" y2="{sy(0):.1f}"/>'
        f'<line x1="{left}" x2="{left}" y1="{sy(0):.1f}" y2="{sy(y_max):.1f}"/></g><g class="tick">'
    )
    for v in (0, y_max / 2, y_max):
        g += f'<text x="{left - 8}" y="{sy(v) + 4:.1f}" text-anchor="end">${v:g}</text>'
    y0 = _dt_from(all_pts[0][0]).year
    y1 = _dt_from(asof).year
    for yy in range(y0, y1 + 1):
        iso = f"{yy}-01-01"
        if x0 <= _date_num(iso) <= x1:
            g += f'<text x="{sx(iso):.1f}" y="{sy(0) + 17:.1f}" text-anchor="middle">{yy}</text>'
    g += '</g><g class="series">'
    labels = []
    for i, sr in enumerate(series):
        col = cols[i % len(cols)]
        d = ""
        for j, p in enumerate(sr["pts"]):
            x, y = sx(p[0]), sy(p[1])
            d += f"M{x:.1f},{y:.1f}" if j == 0 else f" H{x:.1f} V{y:.1f}"
        if not sr.get("stale"):
            d += f" H{sx(asof):.1f}"
        dash = ' stroke-dasharray="4 3"' if sr.get("stale") else ""
        g += f'<path d="{d}" stroke="{col}"{dash}/>'
        for p in sr["pts"]:
            g += f'<circle cx="{sx(p[0]):.1f}" cy="{sy(p[1]):.1f}" r="3" stroke="{col}"/>'
        last = sr["pts"][-1]
        lx = (sx(last[0]) if sr.get("stale") else sx(asof)) + 8
        labels.append({
            "x": lx, "y": sy(last[1]),
            "t": f"{fmt_usd(last[1])} {sr.get('short', '')}{' (ended)' if sr.get('stale') else ''}",
            "col": col,
        })
    labels.sort(key=lambda a: a["y"])
    for i in range(1, len(labels)):
        if labels[i]["y"] - labels[i - 1]["y"] < 14:
            labels[i]["y"] = labels[i - 1]["y"] + 14
    for lab in labels:
        g += f'<text class="lbl" x="{lab["x"]:.1f}" y="{lab["y"] + 4:.1f}" fill="{lab["col"]}">{esc(lab["t"])}</text>'
    g += "</g>"
    note = data["priceCaptions"].get(key, "Dated prints only; the flat line is the list holding, not an assumption.") if key else "Dated prints only; the flat line is the list holding, not an assumption."
    return (
        f'<div class="pathchart"><svg viewBox="0 0 {w} {h}" role="img" '
        f'aria-label="{esc(s["name"])} price per GPU-hour over dated prints">{g}</svg>'
        f'<p class="note" style="margin:10px 0 0">{esc(note)}</p></div>'
    )


def chip_page(s, data, css, domains, venue_url):
    asof = data["config"]["asOf"]
    chips = data["chips"]
    root = "../../"
    url = f"{SITE}/silicon/{s['slug']}/"
    if s["disp"]["usd"] is None:
        price_str = "token pricing"
        title = f"{s['name']} pricing ({mon_year(asof)}): token API, no public chip-hour | compute.world"
        description = (
            f"{s['vendor']} {s['name']} is sold as tokens, not chip-hours. {s['disp'].get('cfg') or ''}. "
            f"What the tape can and cannot show, as of {fmt_date(asof)}."
        )
    else:
        price_str = f"¥{s['disp']['cny']:.2f} (about {fmt_usd(s['disp']['usd'])})" if s["disp"].get("cny") else fmt_usd(s["disp"]["usd"])
        title = (
            f"{s['name']} rental price ({mon_year(asof)}): {price_str}/hr {s['disp']['term']} "
            f"at {s['disp']['venue']} | compute.world"
        )
        description = (
            f"{s['vendor']} {s['name']} rents for {price_str} per GPU-hour {s['disp']['term']} at "
            f"{s['disp']['venue']} as of {fmt_date(asof)}. Every sourced quote by venue and term, dated history."
        )
    if len(description) > 158:
        description = re.sub(r"[,;: ]+\S*$", "", description[:155]) + "…"
    ranked = sorted(chips, key=lambda x: x["rank"])
    idx = next(i for i, x in enumerate(ranked) if x["id"] == s["id"])
    prev = ranked[idx - 1] if idx else None
    nxt = ranked[idx + 1] if idx + 1 < len(ranked) else None
    q, y = s["chg"]["q"], s["chg"]["y"]
    alt = ", ".join(
        f"{fmt_usd(qq[2])} {qq[1]} at {qq[0]}"
        for qq in s["quotes"][1:4]
        if qq[2] is not None
    )
    cfg = s["disp"].get("cfg") or ""
    faqs = [
        (
            f"How much does {s['name']} cost per hour?",
            (
                f"{s['vendor']} does not publish a public accelerator-hour for the {s['name']}. {cfg}."
                if s["disp"]["usd"] is None
                else f"{price_str} per GPU-hour {s['disp']['term']} at {s['disp']['venue']} as of {fmt_date(asof)}"
                     + (f" ({cfg})" if cfg else "") + "."
                     + (f" Other sourced prints: {alt}." if alt else "")
            ),
        ),
        (
            f"Why do {s['name']} prices differ so much between clouds?",
            "Because the terms differ. On-demand is a list price with no commitment; spot is interruptible and priced "
            "to fill idle capacity; reserved and one-year contracts trade a commitment for a lower rate; AWS Capacity "
            "Blocks are scheduled reservations, not on-demand. The tape never averages these: each print carries its "
            "venue, term and date.",
        ),
        (
            f"Has the {s['name']} price gone up or down?",
            " ".join(x for x in [
                (
                    f"Over one quarter, {s['disp']['venue']} {s['disp']['term']} moved "
                    f"{'+' if q.get('pct', 0) > 0 else ''}{q['pct']:.1f}% ({fmt_usd(q.get('then'))} on "
                    f"{fmt_date(q.get('thenDate'))} to {fmt_usd(s['disp']['usd'])})."
                    if q.get("pct") is not None
                    else "No dated same-venue pair exists for a one-quarter change, so none is printed."
                ),
                (f"Over one year: {'+' if y.get('pct', 0) > 0 else ''}{y['pct']:.1f}%." if y.get("pct") is not None else ""),
            ] if x),
        ),
        (f"Is the {s['name']} available to rent right now?", s.get("avail") or "See the sourced notes on this page."),
    ]
    jsonld = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage", "@id": url, "url": url, "name": title, "description": description,
                "datePublished": "2026-08-10", "dateModified": asof,
                "isPartOf": {"@id": SITE + "/#website"}, "inLanguage": "en",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "compute.world", "item": SITE + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Silicon prices", "item": SITE + "/#silicon"},
                    {"@type": "ListItem", "position": 3, "name": s["name"], "item": url},
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": qq, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for qq, a in faqs
                ],
            },
        ],
    }, ensure_ascii=False)
    kv = [
        ["Buy-now price", price_str + ("" if s["disp"]["usd"] is None else " per GPU-hour"),
         f"{s['disp']['venue']}, {s['disp']['term']}{', ' + cfg if cfg else ''}. As of {fmt_date(asof)}."],
    ]
    if s["terms"].get("y1"):
        kv.append(["1-year term book", fmt_usd(s["terms"]["y1"]["price"]),
                   f"{s['terms']['y1']['venue']}, {s['terms']['y1']['label']}."])
    if s["terms"].get("y3"):
        kv.append(["3-year term book", fmt_usd(s["terms"]["y3"]["price"]),
                   f"{s['terms']['y3']['venue']}, {s['terms']['y3']['label']}."])
    kv.append(["Change, 1 quarter",
               (f"{'+' if q['pct'] > 0 else ''}{q['pct']:.1f}%" if q.get("pct") is not None else "—"),
               (f"{s['disp']['venue']} {fmt_usd(q.get('then'))} on {fmt_date(q.get('thenDate'))} to {fmt_usd(s['disp']['usd'])}."
                if q.get("pct") is not None else q.get("note") or "")])
    kv.append(["Change, 1 year",
               (f"{'+' if y['pct'] > 0 else ''}{y['pct']:.1f}%" if y.get("pct") is not None else "—"),
               (f"{s['disp']['venue']} {fmt_usd(y.get('then'))} on {fmt_date(y.get('thenDate'))} to {fmt_usd(s['disp']['usd'])}."
                if y.get("pct") is not None else y.get("note") or "")])
    if s.get("first") and s["disp"]["usd"] is not None:
        pct = round((s["disp"]["usd"] - s["first"]["price"]) / s["first"]["price"] * 100) if s["first"]["price"] else 0
        kv.append(["Since first print", f"{'+' if pct >= 0 else ''}{pct}%",
                   f"{fmt_usd(s['first']['price'])} on {fmt_date(s['first']['date'])}."])
    kv += [
        ["Availability", s.get("scar") or "", s.get("avail") or ""],
        ["Memory", s.get("mem") or "", ""],
        ["Tape rank", f"{s['rank']} of {len(chips)}",
         f"Score {s['score']:.2f}: liquidity {s['liq']}, demand {s['dem']}, frontier {s['fr']}, each 0 to 3. "
         f"Ordinal hygiene, not a valuation."],
    ]
    kv_html = "".join(
        f'<tr><th scope="row">{esc(r[0])}</th><td class="v">{esc(r[1])}</td><td class="d">{esc(r[2])}</td></tr>'
        for r in kv
    )
    qrows = []
    for i, qq in enumerate(s["quotes"]):
        u = venue_url.get(qq[0])
        vhtml = f'<a href="{esc(u)}" rel="noopener">{venue_el(qq[0], domains)}</a>' if u else venue_el(qq[0], domains)
        stale = bool(re.search(r"stale", qq[4] or "", re.I) or re.search(r"SemiAnalysis", qq[0] or ""))
        price = '<span class="dash">—</span>' if qq[2] is None else fmt_usd(qq[2])
        lead = ' class="lead"' if i == 0 else ""
        stale_cls = " stale" if stale else ""
        qrows.append(
            f'<tr{lead}><td>{vhtml}</td><td>{esc(qq[1])}</td>'
            f'<td class="r price{stale_cls}">{price}</td>'
            f'<td>{fmt_date(qq[3])}</td><td class="note tiny">{esc(qq[4] or "")}</td></tr>'
        )
    others = [x for x in ranked if x["id"] != s["id"]][:6]
    others_html = "".join(
        f'<a href="{root}silicon/{x["slug"]}/">{logo_el(x["vendor"], domains, "lg")}'
        f'<span><b>{esc(x["name"])} {"" if x["disp"]["usd"] is None else fmt_usd(x["disp"]["usd"]) + "/hr"}</b>'
        f'<small>{esc(x["disp"]["venue"])}, {esc(x["disp"]["term"])}</small></span></a>'
        for x in others
    )
    if s["disp"]["usd"] is None:
        lede = (
            f"<b>The {esc(s['vendor'])} {esc(s['name'])} is sold as tokens, not chip-hours.</b> {esc(cfg)}. "
            f"The tape shows no dollars per hour because none is published, and it will not invent one from a token price."
        )
    else:
        lede = (
            f"<b>The {esc(s['vendor'])} {esc(s['name'])} rents for {esc(price_str)} per GPU-hour</b> "
            f"{esc(s['disp']['term'])} at {esc(s['disp']['venue'])} as of {fmt_date_long(s['disp']['asOf'])}"
            + (f" ({esc(cfg)})" if cfg else "")
            + "."
            + (f" Other sourced prints: {esc(alt)}." if alt else "")
            + f" {esc(s.get('scar') or '')}."
        )
    chart = path_chart(s, data)
    cannot = ""
    if s.get("cannot"):
        cannot = (
            '<h2>What this page refuses to show</h2>'
            '<ul class="note" style="padding-left:20px;font-size:15px">'
            + "".join(f'<li style="margin:6px 0">{esc(x)}</li>' for x in s["cannot"])
            + "</ul>"
        )
    prev_html = (
        f'<a href="{root}silicon/{prev["slug"]}/">{logo_el(prev["vendor"], domains)}'
        f'<span><small>Rank {prev["rank"]}</small><b>{esc(prev["name"])}</b></span></a>'
        if prev else "<span></span>"
    )
    next_html = (
        f'<a class="next" href="{root}silicon/{nxt["slug"]}/"><span><small>Rank {nxt["rank"]}</small>'
        f'<b>{esc(nxt["name"])}</b></span>{logo_el(nxt["vendor"], domains)}</a>'
        if nxt else ""
    )
    body = f'''
<body>
{masthead(root, asof, current="Silicon prices")}
<main><div class="wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="{root}index.html">compute.world</a><span>›</span><a href="{root}index.html#silicon">Silicon prices</a><span>›</span><span>{esc(s["name"])}</span></nav>
<article class="article">
  <p class="kicker" style="margin-top:18px">Accelerator · Tape rank {s["rank"]} of {len(chips)} · {esc(s["vendor"])}</p>
  <div class="title">{logo_el(s["vendor"], domains, "xl")}<h1>{esc(s["name"])} {"pricing" if s["disp"]["usd"] is None else "rental price"}</h1></div>
  <p class="answer">{lede}</p>
  <div class="meta"><span>Updated {fmt_date(asof)}</span><span>·</span><a href="#cite">Cite this page</a><span>·</span><a href="{SITE}/silicon.json">Data</a><span>·</span><a href="{SITE}/silicon.html">Full tape</a></div>

  <h2>Key numbers</h2>
  <table class="kv"><tbody>{kv_html}</tbody></table>

  <h2>Every sourced quote</h2>
  <p class="small">Venue, term, price, date. The highlighted row is the display print: the most liquid public on-demand list, or a labeled spot print where on-demand is contact-sales.</p>
  <table class="quotes"><thead><tr><th>Venue</th><th>Term</th><th class="r">$ per hour</th><th>As of</th><th>Note</th></tr></thead><tbody>{"".join(qrows)}</tbody></table>

  {f'<h2>Price path</h2><p class="small">Steps, not candles. Each dot is a dated print; the line carries the last print forward until the next one. A dashed line is a series that stopped publishing.</p>{chart}' if chart else ""}

  {cannot}

  <h2>Questions people ask</h2>
  <div class="faq">{"".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faqs)}</div>

  <h2>Other accelerators on the tape</h2>
  <div class="pricestrip">{others_html}</div>

  <h2 id="cite">Cite this page</h2>
  <div class="cite"><div class="codebox" id="citeBox">Hamal, P. (2026). The Silicon Tape: {esc(s["name"])}. compute.world. {url} Retrieved {fmt_date(asof)}.</div><button class="btn primary" data-copy="#citeBox">Copy citation</button></div>
  <p class="small" style="margin-top:12px">CC BY 4.0 with attribution to compute.world. Vendor names and marks belong to their owners and identify the source of each quote.</p>

  <nav class="nextprev" aria-label="Neighbouring ranks">{prev_html}{next_html}</nav>
</article>
</div></main>
{footer()}
{tiny_js()}
</body>
</html>'''
    return head(title, description, url, root, css, jsonld=jsonld, og_type="article",
                image=f"{SITE}/og-silicon.png") + body


def copy_assets(dest):
    fonts_src = os.path.join(ROOT, "fonts")
    flags_src = os.path.join(ROOT, "flags")
    for name in ("fonts", "flags"):
        src = os.path.join(ROOT, name)
        tgt = os.path.join(dest, name)
        if os.path.isdir(src) and os.path.abspath(src) != os.path.abspath(tgt):
            if os.path.isdir(tgt):
                shutil.rmtree(tgt)
            shutil.copytree(src, tgt)
    svg = map_svg()
    write(os.path.join(dest, "map.svg"), svg)
    return svg


def llms_txt(data, rail):
    asof = data["config"]["asOf"]
    top = sorted(data["countries"], key=lambda c: c["rank"])
    chips = sorted(data["chips"], key=lambda s: s["rank"])
    lines = [
        "# compute.world",
        "",
        f"> Countries. Compute. Silicon. The world's compute index: {rail['n_countries']} countries priced by compute net worth, {rail['n_chips']} AI accelerators with sourced rental prices. Updated weekdays. Snapshot {asof}.",
        "",
        "## Definitions",
        "- Ceiling: resource ceiling (GW) × $60 to 80B per GW. What a country's identified energy could host, at today's price of a gigawatt.",
        "- Unlockable: firm untapped GW × $50B × readiness. The bankable slice.",
        "- Live compute (Gross Domestic Compute, GDC): live datacenter GW × $50B. What actually runs.",
        "- Readiness: eight-part discount (governance 18, GPU access 14, physical 14, stability 13, grid 11, fiber 11, capital access 11, momentum 8).",
        "- Conversion score: 0 to 100; moves with public signals. Rank is by unlockable value.",
        "- Price tape rule: every price carries venue, term and date; missing numbers are dashes; change needs two dated same-venue prints.",
        "",
        "## Cite",
        "Hamal, P. (2026). The Compute Net Worth Index. compute.world. Free with attribution for research and press.",
        "",
        "## Data",
        f"- {SITE}/data.json (countries)",
        f"- {SITE}/silicon.json (prices), {SITE}/silicon-history.json (dated prints)",
        f"- {SITE}/rank-history.json (append-only daily snapshots)",
        f"- {SITE}/params.json (every assumption)",
        "",
        "## Country pages (live capacity, ceiling, unlockable, rank)",
    ]
    for c in top:
        lines.append(
            f"- [{c['name']}]({SITE}/country/{c['slug']}/): {fmt_gw(c['liveGW'])} live, "
            f"{c['ceilGW']} GW ceiling ({fmt_range(c)}), unlockable {fmt_b(c['unlock'])}, "
            f"rank {c['rank']}, {TIER[c['tier']]}"
        )
    lines += ["", "## Accelerator pages (buy-now price, venue, term, date)"]
    for s in chips:
        if s["disp"]["usd"] is None:
            lines.append(f"- [{s['name']}]({SITE}/silicon/{s['slug']}/): token pricing, no chip-hour")
        else:
            lines.append(
                f"- [{s['name']}]({SITE}/silicon/{s['slug']}/): {fmt_usd(s['disp']['usd'])} per GPU-hour, "
                f"{s['disp']['venue']} {s['disp']['term']}, {s['disp']['asOf']}"
            )
    lines.append("")
    return "\n".join(lines)


def write_site(dests=None):
    data, _model = assemble()
    rail = headline_rail(data["countries"], data["chips"])
    css = read("styles.css")
    app_js = read("app.js")
    if dests is None:
        dests = [ROOT, os.path.join(HERE, "deploy")]
    svg = map_svg()
    home = homepage(data, css, app_js, rail, svg)
    asof = data["config"]["asOf"]
    extra = [
        {"loc": f"{SITE}/country/{c['slug']}/", "lastmod": asof, "changefreq": "weekly", "priority": "0.8"}
        for c in data["countries"]
    ] + [
        {"loc": f"{SITE}/silicon/{s['slug']}/", "lastmod": asof, "changefreq": "weekly", "priority": "0.8"}
        for s in data["chips"]
    ]
    sm = sitemap_xml(
        [{**u, "lastmod": asof} if u["loc"] == f"{SITE}/" else u for u in DEFAULT_SITEMAP] + extra
    )
    llms = llms_txt(data, rail)
    for dest in dests:
        os.makedirs(dest, exist_ok=True)
        copy_assets(dest)
        write(os.path.join(dest, "index.html"), home)
        for c in data["countries"]:
            write(os.path.join(dest, "country", c["slug"], "index.html"), country_page(c, data, css, data["domains"]))
        for s in data["chips"]:
            write(os.path.join(dest, "silicon", s["slug"], "index.html"),
                  chip_page(s, data, css, data["domains"], data["venueUrl"]))
        write(os.path.join(dest, "sitemap.xml"), sm)
        write(os.path.join(dest, "robots.txt"), robots_txt())
        write(os.path.join(dest, "llms.txt"), llms)
    n = len(data["countries"]) + len(data["chips"]) + 1
    print(f"desk v1.5: {n} pages · {rail['ceiling']} ceiling · {rail['unlockable']} unlockable · {rail['live']} live · as of {asof}")
    return data, rail


if __name__ == "__main__":
    write_site()
