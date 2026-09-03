#!/usr/bin/env python3
# Phase 1 homepage: the Compute Net Worth Index.
# Also writes /thesis, /license, /data, sitemap, llms.txt.
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from cnw_lib import (
    LABEL_CEILING, LABEL_GDC, LABEL_UNLOCK, N_COUNTRIES, SITE, TIER_CLASS,
    assemble_countries, esc, fmt_mult, fmt_rank_serial, global_stats, money_b,
    money_pc, movers_from_wire, nice_day, slim_payload,
)
from chrome import (
    cert_html, footer, head, masthead, subscribe_markup, subscribe_script,
)
from seo import (
    DEFAULT_SITEMAP, breadcrumb_ld, org_publisher,
    person_author, robots_txt, sitemap_xml,
)


def home_css():
    return """
.hero{padding:48px 0 12px;max-width:72ch}
.hero .stat{margin:22px 0 8px;font-size:28px;line-height:1.25}
.hero .stat b{font-weight:600}
.hero .tip{border-bottom:1px dotted var(--rule);cursor:help}
.hero-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}
.geo{margin:28px 0 8px}
.geo-head{display:flex;flex-wrap:wrap;justify-content:space-between;gap:10px;align-items:end;margin-bottom:10px}
.geo select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--rule);background:var(--paper);border-radius:4px}
.privacy{margin-top:8px}
.movers{margin:40px 0 8px}
.movers-list{display:flex;gap:12px;overflow-x:auto;padding:8px 0 12px}
.mover{flex:0 0 240px;border:1px solid var(--rule);border-radius:4px;padding:12px 14px}
.mover a{border:none;color:var(--ink);font-weight:600}
.mover .why{font-size:14px;color:var(--muted);margin-top:6px}
.index{margin:48px 0 8px}
.controls{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;margin:14px 0}
.chip{font-family:var(--sans);font-size:14px;padding:5px 10px;border:1px solid var(--rule);
  border-radius:4px;background:var(--paper);color:var(--ink);cursor:pointer}
.chip.on{border-color:var(--ink)}
#q{font:inherit;font-size:16px;padding:6px 8px;border:none;border-bottom:1px solid var(--rule);background:transparent;min-width:180px}
#q:focus{outline:none;border-bottom-color:var(--ink)}
.ix{width:100%;border-collapse:collapse;font-size:15px;margin-top:8px}
.ix th{font-weight:400;font-size:13px;color:var(--muted);text-align:right;padding:8px 8px 8px 0;
  border-bottom:1px solid var(--ink);cursor:pointer}
.ix th.l{text-align:left}
.ix td{padding:8px 8px 8px 0;border-bottom:1px solid var(--rule);text-align:right;white-space:nowrap}
.ix td.l{text-align:left;white-space:normal}
.ix a.cname{border:none;color:var(--ink);font-weight:600}
.ix a.cname:hover{color:var(--stall)}
.cards{display:none}
.card{border:1px solid var(--rule);border-radius:4px;padding:14px 16px;margin:10px 0}
.card .nm{font-size:20px}
.card .row{display:flex;justify-content:space-between;gap:12px;padding:4px 0;font-size:15px}
.sig-lists{display:grid;grid-template-columns:1fr 1fr;gap:32px;margin:48px 0}
.slist ol{list-style:none;counter-reset:s}
.slist li{counter-increment:s;display:flex;gap:10px;padding:7px 0;border-bottom:1px solid var(--rule)}
.slist li::before{content:counter(s);font-family:var(--sans);color:var(--muted);width:1.4em}
#globewrap{display:none;margin-top:12px;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
#globe{height:560px}
@media(max-width:768px){
  .tblwrap{display:none}
  .cards{display:block}
  .sig-lists{grid-template-columns:1fr}
}
"""


def table_rows(countries):
    bits = []
    for c in countries:
        gdc = money_b(c.get("cnw_gdc_B"))
        gdc_cls = " est" if c.get("lgE") and c.get("cnw_gdc_B") else ""
        bits.append(
            f"<tr data-sl='{c['slug']}' data-t='{esc(c['tier'])}' data-r='{esc(c['region'])}' "
            f"data-n='{esc(c['name']).lower()}'>"
            f"<td class='tnum'>{c.get('rank') or '—'}</td>"
            f"<td class='l'><a class='cname' href='/{c['slug']}'>{esc(c.get('femoji') or '')} {esc(c['name'])}</a></td>"
            f"<td class='l'>{esc(c['tier'])}</td>"
            f"<td class='tnum'>{money_b(c.get('cnw_unlockable_B'))}</td>"
            f"<td class='tnum'>{money_b(c.get('cnw_ceiling_hi_B'))}</td>"
            f"<td class='tnum{gdc_cls}'>{gdc}</td>"
            f"<td class='tnum'>{fmt_mult(c.get('gdp_multiple'))}</td>"
            f"<td class='tnum'>{money_pc(c.get('unlock_pc'))}</td>"
            f"</tr>"
        )
    return "".join(bits)


def card_html(c):
    gdc = money_b(c.get("cnw_gdc_B"))
    return (
        f"<article class='card' data-sl='{c['slug']}' data-t='{esc(c['tier'])}' "
        f"data-r='{esc(c['region'])}' data-n='{esc(c['name']).lower()}'>"
        f"<div class='nm'><a class='cname' href='/{c['slug']}'>{esc(c.get('femoji') or '')} {esc(c['name'])}</a></div>"
        f"<p class='micro'>{esc(c['tier'])} · {fmt_rank_serial(c.get('rank'))}</p>"
        f"<div class='row'><span>{LABEL_UNLOCK}</span><span class='tnum'>{money_b(c.get('cnw_unlockable_B'))}</span></div>"
        f"<div class='row'><span>{LABEL_CEILING}</span><span class='tnum'>{money_b(c.get('cnw_ceiling_hi_B'))}</span></div>"
        f"<div class='row'><span>{LABEL_GDC}</span><span class='tnum'>{gdc}</span></div>"
        f"<div class='row'><span>Ceiling × GDP</span><span class='tnum'>{fmt_mult(c.get('gdp_multiple'))}</span></div>"
        f"<div class='row'><span>Bankable per person</span><span class='tnum'>{money_pc(c.get('unlock_pc'))}</span></div>"
        f"</article>"
    )


def movers_html(countries, wire):
    rows = movers_from_wire(countries, wire, 12)
    if not rows:
        return ""
    bits = []
    for row in rows:
        c, it = row["country"], row["item"]
        bits.append(
            f"<article class='mover'><a href='/{c['slug']}'>{esc(c.get('femoji') or '')} {esc(c['name'])}</a>"
            f"<p class='why'>{esc(it.get('title') or '')}</p></article>"
        )
    return f"<div class='movers-list'>{''.join(bits)}</div>"


def list_html(title, rows, value_fn):
    items = "".join(
        f"<li><a href='/{c['slug']}'>{esc(c.get('femoji') or '')} {esc(c['name'])}</a> "
        f"<span class='tnum'>{value_fn(c)}</span></li>"
        for c in rows
    )
    return f"<div class='slist'><h2>{title}</h2><ol>{items}</ol></div>"


def home_js(slugs):
    slug_json = json.dumps(sorted(slugs))
    return f"""
(function(){{
  var slugs = {slug_json};
  var hash = (location.hash||"").replace(/^#/,"");
  if(hash && slugs.indexOf(hash)>=0){{ location.replace("/"+hash); return; }}
  var tabs = {{silicon:"/silicon.html",countries:"/#index",inference:"/inference.html",
    neoclouds:"/neoclouds.html",hyperscalers:"/hyperscalers.html",
    board:"/#movers",index:"/#index",gazetteer:"/#index",credit:"/#cite"}};
  if(hash && tabs[hash]){{ location.replace(tabs[hash]); return; }}

  var D = window.CNW || [];
  var bySl = {{}}; D.forEach(function(c){{ bySl[c.sl]=c; }});
  var byI2 = {{}}; D.forEach(function(c){{ if(c.i2) byI2[c.i2.toUpperCase()]=c; }});

  function cookieGet(){{
    var m = document.cookie.match(/(?:^|; )cnw_country=([^;]*)/);
    return m ? decodeURIComponent(m[1]) : "";
  }}
  function cookieSet(sl){{
    document.cookie = "cnw_country="+encodeURIComponent(sl)+";path=/;max-age=31536000;samesite=lax";
  }}
  function fillCert(c){{
    var host = document.getElementById("geo-cert");
    if(!host||!c) return;
    var gdc = (c.gdc==null||c.gdc<=0) ? "—" : (c.gdc>=1000?("$"+(c.gdc/1000).toFixed(1)+"T"):("$"+Math.round(c.gdc)+"B"));
    var ceil = c.hi>=1000?("$"+(c.hi/1000).toFixed(1)+"T"):("$"+Math.round(c.hi)+"B");
    var unlock = c.u>=1000?("$"+(c.u/1000).toFixed(1)+"T"):("$"+Math.round(c.u)+"B");
    var mult = c.m>=100?Math.round(c.m)+"×":(c.m?c.m.toFixed(1)+"×":"—");
    var pc = c.upc>=1000?("$"+(c.upc/1000).toFixed(c.upc>=100000?0:1)+"k"):(c.upc?("$"+Math.round(c.upc)):"—");
    var delta = "";
    if(c.dd!=null){{
      delta = c.dd>0?('<span class="delta up">▲ '+c.dd+"</span>"):c.dd<0?('<span class="delta down">▼ '+Math.abs(c.dd)+"</span>"):'<span class="delta flat">●</span>';
    }}
    var coupons = (c.coupon||[]).map(function(p){{
      return "<i class='"+(p[1]>=0.65?"on":"")+"'>"+p[0]+" "+Math.round(p[1]*100)+"</i>";
    }}).join("");
    var tc = {{"Sleeping Giant":"sg",Primed:"pr",Incumbent:"in","Emerging Upside":"eu","Long Road":"lr"}}[c.t]||"lr";
    host.innerHTML = '<article class="cert settle"><span class="cert-flag">'+c.fg+'</span>'
      +'<div class="cert-name">'+c.n+'</div><span class="seal '+tc+'">'+c.t+'</span>'
      +'<div class="cert-serial tnum">No. '+(c.rk||"—")+' of {N_COUNTRIES} '+delta+'</div>'
      +'<div class="cert-nums"><div><div class="v tnum">'+ceil+'</div><div class="l">{LABEL_CEILING}</div></div>'
      +'<div><div class="v tnum">'+unlock+'</div><div class="l">{LABEL_UNLOCK}</div></div>'
      +'<div><div class="v tnum'+(c.lgE&&c.gdc?" est":"")+'">'+gdc+'</div><div class="l">{LABEL_GDC}</div></div></div>'
      +'<div class="cert-extra"><span>Ceiling × GDP <b class="tnum">'+mult+'</b></span>'
      +'<span>Bankable per person <b class="tnum">'+pc+'</b></span></div>'
      +'<div class="coupon">'+coupons+'</div>'
      +'<p class="cert-verdict">'+(c.v||"")+'</p>'
      +'<p class="cert-asof"><a href="/'+c.sl+'">Open '+c.n+'</a></p></article>';
    var sel = document.getElementById("geo-pick");
    if(sel) sel.value = c.sl;
  }}
  function pick(sl, save){{
    var c = bySl[sl]; if(!c) return;
    fillCert(c);
    if(save) cookieSet(sl);
  }}
  var sel = document.getElementById("geo-pick");
  if(sel) sel.addEventListener("change", function(){{ pick(sel.value, true); }});

  var saved = cookieGet();
  if(saved && bySl[saved]){{ pick(saved, false); }}
  else {{
    fetch("/cdn-cgi/trace", {{credentials:"omit"}}).then(function(r){{ return r.text(); }}).then(function(t){{
      var m = t.match(/loc=([A-Z]{{2}})/);
      if(m && byI2[m[1]]) pick(byI2[m[1]].sl, false);
    }}).catch(function(){{}});
  }}

  var state = {{q:"", tier:"", region:"", sort:"rk", dir:1}};
  function apply(){{
    var q = state.q, t = state.tier, r = state.region;
    document.querySelectorAll(".ix tbody tr, .cards .card").forEach(function(el){{
      var ok = (!q || (el.dataset.n||"").indexOf(q)>=0)
        && (!t || el.dataset.t===t)
        && (!r || el.dataset.r===r);
      el.hidden = !ok;
    }});
  }}
  document.querySelectorAll(".tierf").forEach(function(b){{
    b.addEventListener("click", function(){{
      document.querySelectorAll(".tierf").forEach(function(x){{ x.classList.remove("on"); }});
      b.classList.add("on"); state.tier = b.getAttribute("data-t")||""; apply();
    }});
  }});
  var rs = document.getElementById("region");
  if(rs) rs.addEventListener("change", function(){{ state.region = rs.value; apply(); }});
  var q = document.getElementById("q");
  if(q) q.addEventListener("input", function(){{ state.q = q.value.toLowerCase(); apply(); }});

  var vtab = document.getElementById("vtab"), vglobe = document.getElementById("vglobe");
  var tablewrap = document.getElementById("tablewrap"), globewrap = document.getElementById("globewrap");
  var cards = document.querySelector(".cards");
  if(vtab) vtab.addEventListener("click", function(){{
    vtab.classList.add("on"); if(vglobe) vglobe.classList.remove("on");
    if(tablewrap) tablewrap.style.display=""; if(cards) cards.style.display="";
    if(globewrap) globewrap.style.display="none";
  }});
  if(vglobe) vglobe.addEventListener("click", function(){{
    vglobe.classList.add("on"); if(vtab) vtab.classList.remove("on");
    if(tablewrap) tablewrap.style.display="none"; if(cards) cards.style.display="none";
    if(globewrap){{ globewrap.style.display="block"; showGlobe(); }}
  }});

  function showGlobe(){{
    if(window._globe || window._gloading) return;
    window._gloading = true;
    function script(src){{ return new Promise(function(res,rej){{ var s=document.createElement("script"); s.src=src; s.onload=res; s.onerror=rej; document.head.appendChild(s); }}); }}
    Promise.all([
      script("https://unpkg.com/globe.gl@2"),
      script("https://unpkg.com/topojson-client@3.1.0/dist/topojson-client.min.js")
    ]).then(function(){{
      return fetch("https://unpkg.com/world-atlas@2.0.2/countries-110m.json").then(function(r){{ return r.json(); }});
    }}).then(function(world){{
      var land = topojson.feature(world, world.objects.countries).features;
      var el = document.getElementById("globe");
      var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      window._globe = Globe()(el)
        .backgroundColor("rgba(0,0,0,0)")
        .globeImageUrl(null)
        .showGlobe(true)
        .showAtmosphere(false)
        .hexPolygonsData(land)
        .hexPolygonResolution(3)
        .hexPolygonMargin(0.2)
        .hexPolygonColor(function(){{ return "rgba(23,22,20,0.35)"; }})
        .width(el.clientWidth).height(560);
      window._globe.globeMaterial().color.set("#ddd4c2");
      window._globe.controls().autoRotate = !reduce;
      window._globe.controls().autoRotateSpeed = 0.35;
      window._gloading = false;
    }}).catch(function(){{
      document.getElementById("globemsg").textContent = "The globe needs a network connection. The table has everything.";
      window._gloading = false;
    }});
  }}
}})();
"""


def render_home(countries, as_of, wire, stats):
    tap = f"{stats['tap_pct']:.1f}"
    regions = sorted({c["region"] for c in countries})
    region_opts = "".join(f'<option value="{esc(r)}">{esc(r)}</option>' for r in regions)
    picker = "".join(f'<option value="{c["slug"]}">{esc(c["name"])}</option>' for c in sorted(countries, key=lambda x: x["name"]))
    sg = sorted([c for c in countries if c["tier"] == "Sleeping Giant"], key=lambda c: -(c.get("gdp_multiple") or 0))[:10]
    gdc = sorted([c for c in countries if c.get("cnw_gdc_B")], key=lambda c: -(c.get("cnw_gdc_B") or 0))[:10]
    title = "The Compute Net Worth Index · compute.world"
    desc = (
        f"Every country has a Compute Net Worth. {tap}% of the world's compute ceiling is running today. "
        f"{N_COUNTRIES} countries on the index."
    )
    extra = f"<style>{home_css()}</style>"
    ld = json.dumps({"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "url": f"{SITE}/", "name": "compute.world",
         "publisher": org_publisher(), "author": person_author()},
        breadcrumb_ld([("compute.world", f"{SITE}/")]),
    ]})
    payload = json.dumps(slim_payload(countries), ensure_ascii=False)
    return f"""{head(title, desc, f"{SITE}/", "og.png", extra)}
<body>
{masthead(as_of, current="index")}
<section class="hero wrap">
  <h1 class="display">Every country has a Compute Net Worth. Only a handful are converting theirs.</h1>
  <p>The index prices what a country's own energy and geography could host, and what is already running.</p>
  <p class="stat"><b>{tap}% of the world's compute ceiling is running today</b>
    <span class="tip micro" title="Denominator: global ceiling {stats['ceiling_T']:.0f} trillion dollars at the high end of the weekly-reviewed band.">what that means</span></p>
  <div class="hero-actions">
    <a class="btn btn-ink" href="#subscribe">Get the weekday brief</a>
    <a class="btn" href="#index">Open the index</a>
  </div>
</section>

<section class="geo wrap" id="geo" aria-label="Your country's certificate">
  <div class="geo-head">
    <h2>Your country</h2>
    <label class="small">Or pick one
      <select id="geo-pick" aria-label="Choose a country">{picker}</select>
    </label>
  </div>
  <div id="geo-cert"><p class="micro">Country-level only. One cookie if you pick a country.</p></div>
  <p class="privacy micro">Country-level only. One cookie if you pick a country.</p>
</section>

<section class="movers wrap" id="movers">
  <h2>Movers</h2>
  <p class="micro">Cited Wire signals only. No empty rows.</p>
  {movers_html(countries, wire)}
</section>

<section class="index wrap" id="index">
  <h2>The index</h2>
  <div class="controls">
    <button type="button" class="chip on" id="vtab">Table</button>
    <button type="button" class="chip" id="vglobe">Globe</button>
    <button type="button" class="chip tierf on" data-t="">All</button>
    <button type="button" class="chip tierf" data-t="Sleeping Giant">Sleeping Giants</button>
    <button type="button" class="chip tierf" data-t="Primed">Primed</button>
    <button type="button" class="chip tierf" data-t="Incumbent">Incumbents</button>
    <button type="button" class="chip tierf" data-t="Emerging Upside">Emerging Upside</button>
    <select id="region" aria-label="Region"><option value="">All regions</option>{region_opts}</select>
    <input id="q" placeholder="Search a country" aria-label="Search">
  </div>
  <div class="tblwrap" id="tablewrap">
    <table class="ix">
      <thead><tr>
        <th class="l">Rank</th>
        <th class="l">Country</th>
        <th class="l">Tier</th>
        <th>{LABEL_UNLOCK}</th>
        <th>{LABEL_CEILING}</th>
        <th>{LABEL_GDC}</th>
        <th>Ceiling × GDP</th>
        <th>Bankable per person</th>
      </tr></thead>
      <tbody>{table_rows(countries)}</tbody>
    </table>
  </div>
  <div class="cards">{"".join(card_html(c) for c in countries)}</div>
  <div id="globewrap"><div id="globe"></div><p class="micro" id="globemsg"></p></div>
</section>

<section class="sig-lists wrap">
  {list_html("Sleeping Giants, by ceiling × GDP", sg, lambda c: fmt_mult(c.get("gdp_multiple")))}
  {list_html("Running today", gdc, lambda c: money_b(c.get("cnw_gdc_B")))}
</section>

{subscribe_markup()}
{footer()}
<script>window.CNW = {payload};</script>
<script>{home_js([c["slug"] for c in countries])}</script>
<script>{subscribe_script()}</script>
<script type="application/ld+json">{ld}</script>
</body></html>"""


THESIS = r"""
<section class="wrap prose" style="padding:48px 0 24px">
  <h1>The thesis</h1>
  <p class="small">This is the essay that used to open compute.world. The index now lives on the <a href="/">homepage</a>. Roman numerals stay here.</p>

  <h2>I. Three numbers, read together</h2>
  <p>The index prices each country three ways. The honesty lives in reading them together.</p>
  <p>Compute Net Worth at full build-out is the resource ceiling in gigawatts times the market value of an AI factory per gigawatt, currently $60 to $80 billion. Bankable today is firm untapped gigawatts times $50 billion times readiness: the slice underwriters could sign this decade. Running today is live datacenter capacity times $50 billion — Gross Domestic Compute, the tapped counterpart to the ceiling.</p>
  <p>Readiness is a discount rate on the future. Built and running today are facts about the present. The spread between the numbers is the country's reform agenda, priced.</p>

  <h2>II. The index</h2>
  <p>One hundred and eight countries, ranked by the bankable slice. Tiers name the shape of the gap: Sleeping Giant, Primed, Incumbent, Emerging Upside, Long Road. The live table is on the <a href="/#index">homepage</a>. Every country now has its own URL.</p>

  <h2>III. The shape of the map</h2>
  <p>Nearly half the world's ceiling belongs to sleeping giants: countries below 65 percent readiness holding endowments above ten times their GDP. Two countries run most of the world's live compute. Every other chart is about what that concentration leaves on the table.</p>

  <h2>IV. Inside the readiness score</h2>
  <p>18% governance (Transparency International CPI 2025) + 13% political stability + 14% GPU access under the August 2026 export regime + 11% grid + 11% fiber + 8% momentum + 14% physical (cooling × seismic × water) + 11% capital access (rating + IMF financial development). Democracy is shown and deliberately unweighted.</p>

  <h2>V. What the index refuses to hide</h2>
  <p>The ceiling is a ceiling. Analyst build costs run $35 to $42 billion per gigawatt today. The $60 to $80 billion band is NVIDIA's own all-in figure, re-reviewed weekly. Revenue and capture are different things. Chip access is policy, and policy moves. Credit is destiny, until it moves.</p>

  <h2>VI. The abundance question</h2>
  <p>If every country built toward its ceiling, energy for compute would become abundant, and the $60 to $80 billion per gigawatt would collapse. Correct. Three things survive the decay: the cost advantage, the fact that demand has never once behaved, and that what decays fastest is bargaining power. The index is a queue, priced at today's scarcity, and the queue fills.</p>

  <h2>VII. Objections, taken seriously</h2>
  <p>"GPUs depreciate in five years." The index prices the host. Power, shell, cooling, substations, and fiber live 15 to 30 years. Silicon refreshes on top of them the way aircraft refresh on an airport.</p>
  <p>"Chips are the binding constraint." Transmission has not scaled: a fab takes three years, a rich-country grid interconnection now takes five to fifteen. Power is where the buildout actually fails today.</p>
  <p>"This is a bubble." A host country's downside is the status quo: it keeps selling electrons at commodity prices. The option to convert costs the sovereign almost nothing to hold.</p>
  <p>"Inference needs to sit near users." Training tolerates latency and follows cheap, cold, firm power. Inference is drifting toward batch work that tolerates it too.</p>
  <p>"The resource curse." Weak institutions already discount the unlockable number. That is the score doing its job.</p>
  <p>"Washington can revoke the premise." That risk is priced at 14 percent of readiness. The rivers do not repeal.</p>
</section>
"""

LICENSE = r"""
<section class="wrap prose" style="padding:48px 0 24px">
  <h1>License</h1>
  <p>The scores, ratings, valuations, and methodology of The Compute Net Worth Index — including ceiling, bankable today, Gross Domestic Compute (GDC), the Readiness Score, the Signal Score, and CNW Realized — are proprietary to <b>Pukar C. Hamal</b>, © 2026. All rights reserved.</p>

  <h2>Attribution-free uses</h2>
  <p>You may quote, cite, screenshot, chart, and republish the index's scores and findings for <b>personal, academic, research, and journalistic</b> purposes, free of charge, provided you attribute <b>compute.world</b> with a link where the medium allows.</p>
  <p>Suggested attribution: <code>Hamal, P. (2026). The Compute Net Worth Index. compute.world.</code></p>
  <p>The official embed widget (<a href="/embed.html">embed.html</a>) carries its attribution built in and may be placed on any website, including commercial ones, unmodified.</p>

  <h2>Commercial license</h2>
  <p>Any of the following requires a commercial license (write via <a href="/contact.html">the Desk</a>): use of the scores or dataset in a commercial product, service, API, model training corpus sold to third parties, terminal, or paid publication; bulk or systematic redistribution of the dataset; or derivative indexes marketed under or against the names below.</p>

  <h2>What stays free</h2>
  <p>Underlying public facts are facts: a country's GDP, its installed capacity, a published news event. No claim is made over them, only over this index's original scores, selections, arrangements, and expression.</p>

  <h2>Trademarks</h2>
  <p>“Compute Net Worth”, “The Compute Net Worth Index” and “Gross Domestic Compute” (GDC) are trademarks of Pukar C. Hamal. Reuse of the data with credit is welcome; presenting a derivative work under these names is not. This page and the site footer are the only places the mark is asserted.</p>
</section>
"""

DATA_PAGE = r"""
<section class="wrap prose" style="padding:48px 0 24px">
  <h1>Data feeds</h1>
  <p>Machine-readable sources of truth. No invented prices or interpolated ranks.</p>
  <ul>
    <li><a href="/data.json">data.json</a> — 108 countries, all metrics, precedents</li>
    <li><a href="/params.json">params.json</a> — weekly $/GW band</li>
    <li><a href="/rank-history.json">rank-history.json</a> — dated observed ranks</li>
    <li><a href="/wire.json">wire.json</a> — scored conversion signals</li>
    <li><a href="/silicon.json">silicon.json</a> — the Silicon Tape</li>
    <li><a href="/silicon-history.json">silicon-history.json</a> — dated chip prints</li>
    <li><a href="/brief.json">brief.json</a> — the weekday brief</li>
    <li><a href="/inference.json">inference.json</a>, <a href="/neoclouds.json">neoclouds.json</a>, <a href="/hyperscalers.json">hyperscalers.json</a></li>
    <li><a href="/data-centers.json">data-centers.json</a>, <a href="/campuses.json">campuses.json</a></li>
  </ul>
  <p>RSS: <a href="/brief.xml">brief</a>, <a href="/silicon.xml">silicon</a>, <a href="/wire.xml">wire</a>, <a href="/inference.xml">inference</a>, <a href="/neoclouds.xml">neoclouds</a>, <a href="/hyperscalers.xml">hyperscalers.xml</a>.</p>
  <p>Plain-text country siblings live at <code>/{slug}.txt</code> and are listed in <a href="/llms.txt">llms.txt</a>.</p>
</section>
"""


def simple_page(title, desc, url, as_of, current, body, image="og.png"):
    return f"""{head(title, desc, url, image)}
<body>
{masthead(as_of, current=current)}
{body}
{footer()}
</body></html>"""


def llms_txt(countries, as_of, stats):
    lines = [
        "# compute.world · The Compute Net Worth Index",
        "",
        "Every country has a Compute Net Worth. The homepage is the index.",
        f"{stats['tap_pct']:.1f}% of the world's compute ceiling is running today.",
        "",
        "compute.world is Pukar C. Hamal's public compute desk.",
        "Companies inquire via https://compute.world/contact.html.",
        "Cite as: Hamal, P. (2026). The Compute Net Worth Index. compute.world.",
        "",
        "## Country pages",
        "Each of the 108 countries has a URL and a plain-text sibling:",
    ]
    for c in countries:
        lines.append(f"- https://compute.world/{c['slug']}  text: https://compute.world/{c['slug']}.txt")
    lines += [
        "",
        "## Other pages",
        "- https://compute.world/ — the index",
        "- https://compute.world/thesis — the essay",
        "- https://compute.world/license — license and trademarks",
        "- https://compute.world/data — feeds",
        "- https://compute.world/silicon.html — the Silicon Tape",
        "- https://compute.world/wire.html — the Wire",
        "- https://compute.world/brief — the weekday brief",
        "- https://compute.world/contact.html — the Desk",
        "- https://compute.world/data.json — full dataset",
        "",
        "Legacy homepage hash anchors such as #nepal redirect to /nepal.",
        "",
    ]
    return "\n".join(lines)


def sitemap(countries, as_of):
    urls = [
        {"loc": f"{SITE}/", "lastmod": as_of, "changefreq": "daily", "priority": "1.0"},
        {"loc": f"{SITE}/thesis", "lastmod": as_of, "changefreq": "monthly"},
        {"loc": f"{SITE}/license", "lastmod": as_of, "changefreq": "yearly"},
        {"loc": f"{SITE}/data", "lastmod": as_of, "changefreq": "weekly"},
    ]
    for c in countries:
        urls.append({"loc": f"{SITE}/{c['slug']}", "lastmod": as_of, "changefreq": "weekly"})
        urls.append({"loc": f"{SITE}/{c['slug']}.txt", "lastmod": as_of, "changefreq": "weekly"})
    urls.extend(DEFAULT_SITEMAP)
    # de-dupe homepage
    seen, out = set(), []
    for u in urls:
        if u["loc"] in seen:
            continue
        seen.add(u["loc"])
        out.append(u)
    return sitemap_xml(out)


def write(path, text):
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text if text.endswith("\n") else text + "\n")


def build(root=ROOT, countries=None, as_of=None, wire=None):
    if countries is None:
        countries, as_of, wire, _ = assemble_countries()
    stats = global_stats(countries)
    write(os.path.join(root, "index.html"), render_home(countries, as_of, wire, stats))
    write(os.path.join(root, "thesis.html"), simple_page(
        "The thesis · compute.world",
        "The essay behind the Compute Net Worth Index.",
        f"{SITE}/thesis", as_of, "thesis", THESIS,
    ))
    write(os.path.join(root, "license.html"), simple_page(
        "License · compute.world",
        "Attribution-free uses, commercial license, and the trademark notice.",
        f"{SITE}/license", as_of, "index", LICENSE,
    ))
    write(os.path.join(root, "data.html"), simple_page(
        "Data feeds · compute.world",
        "Machine-readable feeds for the Compute Net Worth Index.",
        f"{SITE}/data", as_of, "data", DATA_PAGE,
    ))
    write(os.path.join(root, "llms.txt"), llms_txt(countries, as_of, stats))
    write(os.path.join(root, "sitemap.xml"), sitemap(countries, as_of))
    write(os.path.join(root, "robots.txt"), robots_txt())
    print(f"home: index + thesis + license + data + sitemap ({len(countries)} countries)")
    return countries, as_of


if __name__ == "__main__":
    build()
