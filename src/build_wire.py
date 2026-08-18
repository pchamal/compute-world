#!/usr/bin/env python3
# The Wire generator: wire.json (single source of truth) -> wire.html + wire.xml (RSS).
# Run from src/:  python3 build_wire.py
# The GitHub Action runs this on every push that touches wire.json, so editing the JSON
# on github.com is all it takes to publish; the HTML and RSS regenerate themselves.
import json, html, os
from datetime import datetime
from fnav import css as fnav_css, markup as fnav_markup, script as fnav_script
from seo import og_block, breadcrumb_ld

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
W = json.load(open(os.path.join(ROOT, "wire.json")))
items = sorted(W["items"], key=lambda x: x["date"], reverse=True)

TIER_LABEL = {1: "Primary", 2: "Wire / major", 3: "Trade press", 4: "Regional", 5: "Aggregator"}
def score_label(s): return "Strong" if s >= 80 else "Solid" if s >= 60 else "Developing" if s >= 40 else "Weak"
def nice_date(d): return datetime.strptime(d, "%Y-%m-%d").strftime("%b %d, %Y")

TAGS = sorted({t for it in items for t in it["tags"]})
tag_chips = "".join(f'<span class="chip" data-t="{t}">{t}</span>' for t in TAGS)

rows = []
for it in items:
    e = {k: html.escape(str(it[k])) for k in ("title", "summary", "source")}
    corr = it["corroboration"]
    rows.append(f'''<article class="witem rv" id="{it["id"]}" data-tags="{' '.join(it["tags"])}">
  <div class="wmeta"><span class="wdate">{nice_date(it["date"])}</span><span class="wflags">{it["flags"]}</span>
    <span class="wtags">{' · '.join(it["tags"])}</span></div>
  <h3><a href="{it["url"]}" rel="noopener">{e["title"]}</a></h3>
  <p>{e["summary"]}</p>
  <div class="wsig"><span class="wsrc">{e["source"]} · <i>{TIER_LABEL[it["tier"]]}</i></span>
    <span class="wcorr c-{corr.lower().replace('-', '')}">{corr}</span>
    <span class="wscore"><span class="bar"><i style="width:{it["score"]}%"></i></span>{it["score"]} · {score_label(it["score"])}</span></div>
</article>''')

ld_items = [{"@type": "ListItem", "position": i + 1,
             "item": {"@type": "NewsArticle", "headline": it["title"], "datePublished": it["date"],
                      "url": it["url"], "description": it["summary"],
                      "publisher": {"@type": "Organization", "name": it["source"]}}}
            for i, it in enumerate(items[:20])]
LD = json.dumps({"@context": "https://schema.org", "@type": "ItemList",
                 "name": "The Wire: sovereign AI and compute infrastructure signals",
                 "url": "https://compute.world/wire.html", "itemListElement": ld_items})

PAGE = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#f7f4ee">
<script>(function(){{try{{var t=localStorage.getItem("cnw_theme");if(t!=="dark"&&t!=="light"){{var h=new Date().getHours();t=(h>=19||h<7)?"dark":"light";}}document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();</script>
<title>The Wire · Sovereign AI &amp; Compute Infrastructure News, Rated · compute.world</title>
<meta name="description" content="Rated signals on sovereign AI and compute infrastructure: country announcements, AI factory buildouts, chip policy, and compute capital, each scored for credibility. Updated {W["updated"]}.">
<link rel="canonical" href="https://compute.world/wire.html">
<meta name="robots" content="index,follow,max-image-preview:large">
{og_block("The Wire · compute news, rated",
    "Sovereign AI and compute infrastructure signals, scored for credibility. From the world's compute &amp; silicon index.",
    "https://compute.world/wire.html", "og.png", image_alt="compute.world — the world's compute & silicon index")}
<script type="application/ld+json">{json.dumps(breadcrumb_ld([("compute.world","https://compute.world/"),("The Wire","https://compute.world/wire.html")]))}</script>
<link rel="alternate" type="application/rss+xml" title="The Wire · compute.world" href="https://compute.world/wire.xml">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' fill='%23f7f4ee'/><text x='32' y='44' font-family='Georgia,serif' font-size='36' fill='%23171614' text-anchor='middle'>W</text></svg>">
<script type="application/ld+json">{LD}</script>
<style>
:root{{--paper:#f7f4ee;--ink:#171614;--muted:#62605a;--faint:#8d8a81;--rule:#cdc7b9;--rule2:#171614;
--accent:#7d2027;--tint:#efe9dd;--pr:#4b5f36;--sg:#8a5a2a;--barbg:#e2dcce;
--glass:rgba(247,244,238,.72);--glassborder:rgba(23,22,20,.35);
--serif:'Charter','Bitstream Charter','Sitka Text',Cambria,Georgia,'Times New Roman',serif}}
html[data-theme="dark"]{{--paper:#171511;--ink:#ece7db;--muted:#a49e8f;--faint:#9a9484;--rule:#3a352a;
--rule2:#ded8c8;--accent:#c2564c;--tint:#231f17;--pr:#8fae72;--sg:#c99a5e;--barbg:#3a352a;
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
body{{transition:background-color .35s ease,color .35s ease}}
*{{margin:0;padding:0;box-sizing:border-box}}
html{{background:var(--paper)}}
body{{background:var(--paper);color:var(--ink);font-family:var(--serif);font-size:17px;line-height:1.62;-webkit-font-smoothing:antialiased}}
a{{color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(125,32,39,.35)}}
a:hover{{border-bottom-color:var(--accent)}}
.wrap{{max-width:860px;margin:0 auto;padding:0 28px}}
.masthead{{padding:34px 0 0;text-align:center}}
.masthead .name{{font-size:15px;letter-spacing:.34em;text-transform:uppercase}}
.masthead .name a{{border:none;color:var(--ink)}}
.masthead .name b{{font-weight:600}}
.masthead .sub{{margin-top:8px;font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
.mastrule{{margin-top:20px;border-top:2px solid var(--rule2);border-bottom:1px solid var(--rule2);height:5px}}
.lede{{padding:56px 0 8px}}
h1{{font-weight:400;font-size:clamp(30px,4.6vw,44px);line-height:1.16}}
h1 em{{font-style:italic}}
.standfirst{{margin-top:18px;font-size:18px;color:var(--muted);max-width:720px}}
.standfirst b{{color:var(--ink)}}
.subrow{{display:flex;flex-wrap:wrap;gap:8px 26px;align-items:baseline;margin:26px 0 0;padding:16px 0;border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule);font-size:13px;letter-spacing:.1em;text-transform:uppercase}}
.subrow .lab{{color:var(--faint);font-size:11px;letter-spacing:.16em}}
.chips{{display:flex;flex-wrap:wrap;gap:8px 20px;margin:22px 0 6px;font-size:13.5px}}
.chip{{cursor:pointer;color:var(--ink);border-bottom:1px solid transparent;letter-spacing:.04em}}
.chip:hover{{border-bottom-color:var(--rule)}}
.chip.on{{color:var(--accent);border-bottom:1px solid var(--accent)}}
.witem{{border-bottom:1px solid var(--rule);padding:24px 0 20px}}
.witem:first-of-type{{border-top:1px solid var(--rule2)}}
.wmeta{{display:flex;gap:14px;align-items:baseline;font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);margin-bottom:8px}}
.wdate{{color:var(--muted)}}
.wtags{{margin-left:auto}}
.witem h3{{font-weight:600;font-size:20px;line-height:1.35;margin-bottom:8px}}
.witem h3 a{{color:var(--ink);border-bottom:none}}
.witem h3 a:hover{{color:var(--accent)}}
.witem p{{color:var(--muted);max-width:760px;margin-bottom:12px}}
.wsig{{display:flex;flex-wrap:wrap;gap:10px 22px;align-items:baseline;font-size:12.5px}}
.wsrc{{color:var(--muted)}}
.wsrc i{{color:var(--faint);font-style:normal;font-size:11px;letter-spacing:.08em;text-transform:uppercase;margin-left:4px}}
.wcorr{{font-size:10.5px;letter-spacing:.1em;text-transform:uppercase}}
.c-confirmed{{color:var(--pr)}}.c-corroborated{{color:var(--sg)}}.c-singlesource{{color:var(--faint)}}.c-disputed{{color:var(--accent)}}
.wscore{{font-variant-numeric:lining-nums tabular-nums;color:var(--muted);font-size:12.5px}}
.bar{{display:inline-block;width:44px;height:4px;background:var(--barbg);margin-right:7px;vertical-align:2px}}
.bar i{{display:block;height:4px;background:var(--ink);transform-origin:left;animation:growx .7s ease-out}}
@keyframes growx{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
.rv{{opacity:0;transform:translateY(14px);transition:opacity .7s ease,transform .7s cubic-bezier(.22,.8,.26,1)}}
.rv.in{{opacity:1;transform:none}}
@media(prefers-reduced-motion:reduce){{.rv{{opacity:1;transform:none;transition:none}}}}
details.meth{{margin:44px 0;border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule)}}
details.meth summary{{cursor:pointer;padding:13px 4px;font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);list-style:none}}
details.meth summary::before{{content:"+ "}}
details.meth[open] summary::before{{content:"− "}}
details.meth .mb{{padding:4px 4px 18px;font-size:14px;color:var(--muted);max-width:780px}}
details.meth .mb p{{margin-bottom:12px}}
details.meth .mb b{{color:var(--ink)}}
.colophon{{margin-top:56px;border-top:2px solid var(--rule2);padding:24px 0 56px;text-align:center}}
.colophon .c1{{font-size:12px;letter-spacing:.3em;text-transform:uppercase}}
.colophon .c2{{margin-top:10px;font-size:12.5px;color:var(--muted)}}
@media(max-width:760px){{.wrap{{padding:0 18px}}.lede{{padding:40px 0 8px}}.standfirst{{font-size:16.5px}}
.witem h3{{font-size:18px}}.wmeta{{flex-wrap:wrap}}.wtags{{margin-left:0}}.witem p{{text-align:left;hyphens:none}}}}
</style>
</head>
<body class="fnav-inner">
<button id="themetog" class="tchip" aria-label="Switch to night mode" title="Day / Night">
  <svg class="ic-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>
  <svg class="ic-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.9 1.9M19.1 4.9l-1.8 1.8M6.7 17.3l-1.9 1.9"/></svg>
</button>
{fnav_markup("wire")}
<div class="wrap">
  <div class="masthead">
    <div class="name"><a href="/"><b>COMPUTE</b>.WORLD</a></div>
    <div class="sub">The Wire · Sovereign AI &amp; compute signals, rated · Updated {W["updated"]}</div>
    <div class="mastrule"></div>
  </div>

  <div class="lede">
    <h1>The news, <em>priced</em>.</h1>
    <p class="standfirst">Every week, governments and giants announce AI factories, chip deals, and gigawatt ambitions. Most announcements die quietly. The Wire tracks the signals that matter to the <a href="/">Compute Net Worth Index</a> and scores each one for credibility: <b>the source, the corroboration, the specificity, and the track record of whoever is claiming it</b>. Announcements are cheap. Megawatts are not.</p>
    <div class="subrow">
      <span class="lab">Follow</span>
      <a href="/wire.xml">RSS</a>
      <a href="https://x.com/intent/post?text=The%20Wire%3A%20sovereign%20AI%20and%20compute%20signals%2C%20rated.&url=https%3A%2F%2Fcompute.world%2Fwire.html" rel="noopener">Share on X</a>
      <a href="/contact.html">Submit a signal</a>
    </div>
  </div>

  <div class="chips"><span class="chip on" data-t="">All</span>{tag_chips}</div>

  <main id="wlist">
{chr(10).join(rows)}
  </main>

  <details class="meth">
    <summary>How the Signal Score works</summary>
    <div class="mb">
      <p><b>Signal Score, 0 to 100, four disclosed components.</b> Source tier, 40%: primary documents (government registers, regulator rulings, company releases) score highest, then wire services and majors, trade press, regional outlets, aggregators. Corroboration, 30%: Confirmed means a primary source plus at least two independents; Corroborated means multiple independents; Single-source and Disputed are labeled as exactly that. Specificity, 20%: announcements that name megawatts, dollars, GPU counts, sites, and dates outrank ones that name a vision. Delivery context, 10%: claims from actors with live or building projects in the <a href="/#precedents">precedents table</a> outrank first announcements, and actors with stalled projects are discounted.</p>
      <p>The Wire rates claims and publication types. It does not rate the honesty of outlets or of named individuals. Items are gathered by machine (GDELT and Google News queries across 108 countries), scored, and curated by a human before publication. Corrections: <a href="/contact.html">get in touch</a>. Summaries are original; headlines link to their sources. Feed: <a href="/wire.xml">wire.xml</a> · data: <a href="/wire.json">wire.json</a> (CC BY 4.0, attribution to compute.world).</p>
    </div>
  </details>

  <div class="colophon">
    <div class="c1">COMPUTE.WORLD</div>
    <div class="c2">The Wire · part of The Compute Net Worth Index&#8482; · &copy; 2026 Pukar C. Hamal · San Francisco, CA</div>
  </div>
</div>
<script>
document.querySelectorAll(".chip").forEach(function(ch){{
  ch.onclick = function(){{
    document.querySelectorAll(".chip").forEach(function(x){{x.classList.remove("on")}});
    ch.classList.add("on");
    var t = ch.dataset.t;
    document.querySelectorAll(".witem").forEach(function(w){{
      w.style.display = (!t || w.dataset.tags.indexOf(t) >= 0) ? "" : "none";
    }});
  }};
}});
var io = new IntersectionObserver(function(es){{es.forEach(function(e){{if(e.isIntersecting){{e.target.classList.add("in");io.unobserve(e.target);}}}})}},{{threshold:0,rootMargin:"0px 0px -60px 0px"}});
document.querySelectorAll(".rv").forEach(function(el){{io.observe(el)}});
var tm=document.querySelector('meta[name="theme-color"]'), tg=document.getElementById("themetog");
function cur(){{return document.documentElement.getAttribute("data-theme")==="dark"?"dark":"light"}}
function setT(t,sv){{document.documentElement.setAttribute("data-theme",t);
if(sv){{try{{localStorage.setItem("cnw_theme",t)}}catch(e){{}}}}
tm.content=t==="dark"?"#171511":"#f7f4ee";tg.setAttribute("aria-label",t==="dark"?"Switch to day mode":"Switch to night mode");}}
tg.onclick=function(){{setT(cur()==="dark"?"light":"dark",true)}};
setT(cur(),false);
{fnav_script("wire")}
</script>
</body>
</html>'''

open(os.path.join(ROOT, "wire.html"), "w").write(PAGE)

rss_items = "".join(f'''
  <item>
    <title>{html.escape(it["title"])}</title>
    <link>{html.escape(it["url"])}</link>
    <guid isPermaLink="false">compute.world/wire#{it["id"]}</guid>
    <pubDate>{datetime.strptime(it["date"], "%Y-%m-%d").strftime("%a, %d %b %Y")} 12:00:00 GMT</pubDate>
    <description>{html.escape(it["summary"])} [Signal {it["score"]}, {html.escape(it["corroboration"])}, via {html.escape(it["source"])}] More: https://compute.world/wire.html</description>
  </item>''' for it in items[:30])
RSS = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>The Wire · compute.world</title>
  <link>https://compute.world/wire.html</link>
  <description>Sovereign AI and compute infrastructure signals, scored for credibility. From The Compute Net Worth Index.</description>
  <language>en</language>{rss_items}
</channel></rss>'''
open(os.path.join(ROOT, "wire.xml"), "w").write(RSS)
print(f"wire.html + wire.xml generated: {len(items)} items, updated {W['updated']}")
