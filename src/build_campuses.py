#!/usr/bin/env python3
# Campuses globe: campuses.json -> campuses.html.
# Run from repo root or src/:  python3 src/build_campuses.py
# Do not invent cities, MW, ranks, or statuses. Pins are the JSON, verbatim.
# Cloudflare Pages has no build command — generated HTML is committed.
import json, html, os
from datetime import datetime
from fnav import css as fnav_css, markup as fnav_markup, script as fnav_script
from seo import og_block, breadcrumb_ld, person_author, org_publisher, nice_day

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = json.load(open(os.path.join(ROOT, "campuses.json")))

updated = D["as_of"]
nice_upd = nice_day(updated)
nice_short = datetime.strptime(updated, "%Y-%m-%d").strftime("%d %b %Y")
projects = D["projects"]
if len(projects) != 82:
    raise SystemExit(f"expected 82 projects, got {len(projects)}")

GRAIN_LABEL = {
    "it_capacity": "IT capacity",
    "facility_power": "facility power",
    "interconnection_request": "interconnection request",
    "not_disclosed": "not disclosed",
}
STATUS_LABEL = {
    "announced": "announced",
    "in_progress": "in progress",
    "operational": "operational",
    "paused": "paused",
    "canceled": "canceled",
    "undisclosed": "undisclosed",
}
REGIONS = [
    ("NORAM", "NORAM"),
    ("LATAM", "LATAM"),
    ("EU", "EU"),
    ("MENA", "MENA"),
    ("SSA", "SSA"),
    ("SASIA", "South ASIA"),
    ("APAC", "APAC"),
    ("OCEANIA", "OCEANIA"),
]


def mw_text(p):
    mw = p.get("mw")
    if mw is None:
        return "not disclosed"
    if mw >= 1000 and mw % 1000 == 0:
        return f"{mw // 1000} GW"
    if mw >= 1000:
        g = mw / 1000
        s = f"{g:.2f}".rstrip("0").rstrip(".")
        return f"{s} GW"
    return f"{mw} MW"


def grain_lab(g):
    return GRAIN_LABEL.get(g, g or "—")


def asof(s):
    return nice_day(s, "short") if s else ""


def register_row(p):
    mw = mw_text(p)
    grain = grain_lab(p.get("mw_grain"))
    st = STATUS_LABEL.get(p["status"], p["status"])
    mw_as = asof(p.get("mw_as_of"))
    st_as = asof(p.get("status_as_of"))
    mw_bit = f"{mw} · {grain}" + (f" · {mw_as}" if mw_as else "")
    st_bit = st + (f" · {st_as}" if st_as else "")
    return (
        f'<tr id="row-{html.escape(p["id"])}" data-id="{html.escape(p["id"])}">'
        f'<td><button type="button" class="cn" data-open="{html.escape(p["id"])}">{html.escape(p["name"])}</button>'
        f'<span class="tick">{html.escape(p["operator"])}</span></td>'
        f"<td>{html.escape(p['place'])}</td>"
        f"<td>{html.escape(p['region'])}</td>"
        f"<td>{html.escape(mw_bit)}</td>"
        f"<td>{html.escape(st_bit)}</td>"
        f"</tr>"
    )


reg_rows = "\n".join(register_row(p) for p in projects)
region_btns = "".join(
    f'<button class="chip" type="button" data-region="{html.escape(k)}">{html.escape(lab)}</button>'
    for k, lab in REGIONS
)
mw_floors = [
    (5, ">5"),
    (10, ">10"),
    (25, "25"),
    (50, "50"),
    (100, "100"),
    (250, "250"),
    (500, "500"),
    (1000, "1 GW"),
]
mw_btns = "".join(
    f'<button class="chip" type="button" data-mw="{n}">{html.escape(lab)}</button>'
    for n, lab in mw_floors
)
status_btns = "".join(
    f'<button class="chip" type="button" data-status="{html.escape(k)}">{html.escape(lab)}</button>'
    for k, lab in STATUS_LABEL.items()
)

book_notes = "".join(f"<li>{html.escape(n)}</li>" for n in D.get("notes") or [])
held = D.get("held") or []
held_html = "".join(
    f"<li>{html.escape(h['name'])} — {html.escape(h['reason'])}.</li>" for h in held
)

ld = json.dumps({
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": D["title"],
    "datePublished": updated,
    "dateModified": updated,
    "description": D["description"],
    "url": "https://compute.world/campuses.html",
    "author": person_author(),
    "publisher": org_publisher(),
    "isAccessibleForFree": True,
    "citation": D["cite"],
}, ensure_ascii=False)
crumb = json.dumps(breadcrumb_ld([
    ("compute.world", "https://compute.world/"),
    ("Campuses", "https://compute.world/campuses.html"),
]), ensure_ascii=False)
camp_og = og_block(
    html.escape(D["title"] + " · compute.world"),
    html.escape(D["description"]),
    "https://compute.world/campuses.html",
    "og.png",
    og_type="article",
    image_alt="Campuses — desk-curated named-project globe, not a census",
)
BOOK = json.dumps({
    "as_of": D["as_of"],
    "lede": D["lede"],
    "coverage_holes": D.get("coverage_holes") or [],
    "projects": projects,
}, ensure_ascii=False)

PAGE = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#f7f4ee">
<script>(function(){{try{{var t=localStorage.getItem("cnw_theme");if(t!=="dark"&&t!=="light"){{var h=new Date().getHours();t=(h>=19||h<7)?"dark":"light";}}document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();</script>
<title>{html.escape(D["title"])} · compute.world</title>
<meta name="description" content="{html.escape(D["description"])}">
<link rel="canonical" href="https://compute.world/campuses.html">
<meta name="robots" content="index,follow,max-image-preview:large">
{camp_og}
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' fill='%23f7f4ee'/><text x='32' y='44' font-family='Georgia,serif' font-size='36' fill='%23171614' text-anchor='middle'>C</text></svg>">
<script type="application/ld+json">{ld}</script>
<script type="application/ld+json">{crumb}</script>
<style>
:root{{--paper:#f7f4ee;--ink:#171614;--muted:#62605a;--faint:#8d8a81;--rule:#cdc7b9;--rule2:#171614;
--accent:#7d2027;--tint:#efe9dd;--pr:#4b5f36;--sg:#8a5a2a;
--glass:rgba(247,244,238,.72);--glassborder:rgba(23,22,20,.35);
--serif:'Charter','Bitstream Charter','Sitka Text',Cambria,Georgia,'Times New Roman',serif}}
html[data-theme="dark"]{{--paper:#171511;--ink:#ece7db;--muted:#a49e8f;--faint:#9a9484;--rule:#3a352a;
--rule2:#ded8c8;--accent:#c2564c;--tint:#231f17;--pr:#8fae72;--sg:#c99a5e;
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
.wrap{{max-width:1100px;margin:0 auto;padding:0 28px}}
.masthead{{padding:34px 0 0;text-align:center}}
.masthead .name{{font-size:15px;letter-spacing:.34em;text-transform:uppercase}}
.masthead .name a{{border:none;color:var(--ink)}}
.masthead .name b{{font-weight:600}}
.masthead .sub{{margin-top:8px;font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
.mastrule{{margin-top:20px;border-top:2px solid var(--rule2);border-bottom:1px solid var(--rule2);height:5px}}
.lede{{padding:48px 0 8px}}
h1{{font-weight:400;font-size:clamp(28px,4.4vw,40px);line-height:1.16}}
h1 em{{font-style:italic}}
.standfirst{{margin-top:18px;font-size:17.5px;color:var(--muted);max-width:820px}}
.subrow{{display:flex;flex-wrap:wrap;gap:8px 26px;align-items:baseline;margin:26px 0 0;padding:16px 0;border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule);font-size:13px;letter-spacing:.1em;text-transform:uppercase}}
.subrow .lab{{color:var(--faint);font-size:11px;letter-spacing:.16em}}
.controls{{margin:22px 0 8px}}
.crow{{margin:0 0 12px}}
.crow .lab{{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}}
.chips{{display:flex;flex-wrap:wrap;gap:8px}}
.chip{{font-family:inherit;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink);
background:transparent;border:1px solid var(--rule);border-radius:99px;padding:6px 12px;cursor:pointer}}
.chip:hover{{border-color:var(--ink)}}
.chip.on{{background:var(--ink);color:var(--paper);border-color:var(--ink)}}
html[data-theme="dark"] .chip.on{{background:var(--ink);color:var(--paper)}}
.count{{margin:10px 0 0;font-size:13.5px;color:var(--muted)}}
.count b{{color:var(--ink);font-weight:600}}
.count.empty{{color:var(--sg)}}
.globewrap{{position:relative;margin:18px 0 8px;min-height:420px;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}}
#globe{{width:100%;height:min(640px, max(420px, 62vw));}}
#globemsg{{position:absolute;left:16px;bottom:14px;font-size:13px;color:var(--muted);max-width:70%}}
.reg{{margin:36px 0 0}}
.reg h2{{font-weight:400;font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:0 0 12px}}
table{{width:100%;border-collapse:collapse;font-size:14.5px}}
th{{text-align:left;font-weight:400;font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--faint);
padding:8px 10px 8px 0;border-bottom:1px solid var(--rule2)}}
td{{padding:10px 12px 10px 0;border-bottom:1px solid var(--rule);vertical-align:top;color:var(--muted)}}
tr.even td{{background:transparent}}
tr.off{{display:none}}
.cn{{font-family:inherit;background:none;border:none;border-bottom:1px solid rgba(125,32,39,.35);color:var(--accent);
cursor:pointer;font-size:15px;text-align:left;padding:0}}
.cn:hover{{border-bottom-color:var(--accent)}}
.tick{{display:block;font-size:12px;color:var(--faint);margin-top:2px}}
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
#drawer .dmeta{{display:flex;flex-wrap:wrap;gap:8px 18px;margin:14px 0 18px;padding:12px 0;border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule);font-size:13px;color:var(--muted)}}
#drawer .dmeta b{{color:var(--ink);font-weight:600}}
#drawer .chip{{pointer-events:none;margin:0 6px 0 0}}
#drawer blockquote{{margin:0 0 14px;padding:0 0 0 14px;border-left:2px solid var(--rule2);color:var(--ink);font-size:15.5px}}
#drawer p{{font-size:14.5px;color:var(--muted);margin:0 0 10px}}
#drawer p b{{color:var(--ink)}}
.notes{{margin:48px 0 0;border-top:2px solid var(--rule2);padding-top:22px}}
.notes h2{{font-weight:400;font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:0 0 14px}}
.notes ul{{margin:0 0 0 18px;color:var(--muted);font-size:14.5px}}
.notes li{{margin:0 0 8px}}
.colophon{{margin-top:56px;border-top:2px solid var(--rule2);padding:24px 0 56px;text-align:center}}
.colophon .c1{{font-size:12px;letter-spacing:.3em;text-transform:uppercase}}
.colophon .c2{{margin-top:10px;font-size:12.5px;color:var(--muted)}}
@media(max-width:760px){{.wrap{{padding:0 18px}}.lede{{padding:36px 0 8px}}#globe{{height:420px}}}}
@media(prefers-reduced-motion:reduce){{#drawer,#scrim{{transition:none}}}}
</style>
</head>
<body class="fnav-inner">
<button id="themetog" class="tchip" aria-label="Switch to night mode" title="Day / Night">
  <svg class="ic-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>
  <svg class="ic-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.9 1.9M19.1 4.9l-1.8 1.8M6.7 17.3l-1.9 1.9"/></svg>
</button>
{fnav_markup("campuses")}
<div class="wrap">
  <div class="masthead">
    <div class="name"><a href="/"><b>COMPUTE</b>.WORLD</a></div>
    <div class="sub">Campuses · named projects · the world's compute &amp; silicon index · {nice_upd}</div>
    <div class="mastrule"></div>
  </div>

  <div class="lede">
    <h1>Named campuses, <em>not a census</em>.</h1>
    <p class="standfirst">{html.escape(D["lede"])}</p>
    <div class="subrow">
      <span class="lab">Register</span>
      <span>{nice_short}</span>
      <span>{len(projects)} named projects</span>
      <a href="/campuses.json">campuses.json</a>
      <a href="/data-centers.html">Data centers FAQ</a>
      <a href="/contact.html">The Desk</a>
    </div>
  </div>

  <div class="controls" id="filters">
    <div class="crow">
      <div class="lab">Region</div>
      <div class="chips" role="group" aria-label="Region">
        <button class="chip on" type="button" data-region="">All</button>
        {region_btns}
      </div>
    </div>
    <div class="crow">
      <div class="lab">Announced MW</div>
      <div class="chips" role="group" aria-label="Megawatt floor">
        <button class="chip on" type="button" data-mw="">All</button>
        {mw_btns}
      </div>
    </div>
    <div class="crow">
      <div class="lab">Status</div>
      <div class="chips" role="group" aria-label="Status">
        <button class="chip on" type="button" data-status="">All</button>
        {status_btns}
      </div>
    </div>
    <p class="count" id="count"></p>
  </div>

  <div class="globewrap" id="globewrap">
    <div id="globe" aria-label="Globe of named campus projects"></div>
    <div id="globemsg">Drawing the globe…</div>
  </div>

  <section class="reg" aria-labelledby="reg-h">
    <h2 id="reg-h">The book</h2>
    <table>
      <thead><tr><th>Campus</th><th>Place</th><th>Region</th><th>MW · grain</th><th>Status</th></tr></thead>
      <tbody id="regbody">
{reg_rows}
      </tbody>
    </table>
  </section>

  <section class="notes" id="notes">
    <h2>How to read this</h2>
    <ul>
      {book_notes}
      {held_html}
    </ul>
    <p style="margin-top:18px;font-size:14px;color:var(--muted)">Cite as: <code>{html.escape(D["cite"])}</code>. A wrong pin: <a href="/contact.html">The Desk</a>. The slogans live on the <a href="/data-centers.html">Data centers FAQ</a>.</p>
  </section>

  <div class="colophon">
    <div class="c1">COMPUTE.WORLD</div>
    <div class="c2">Campuses · {nice_upd} · the world's compute &amp; silicon index · CNW™ · GDC™ · &copy; 2026 Pukar C. Hamal · San Francisco, CA</div>
  </div>
</div>

<div id="scrim" hidden></div>
<aside id="drawer" hidden aria-labelledby="dname">
  <button class="dclose" type="button" id="dclose">Close</button>
  <div class="dv" id="dop"> </div>
  <h2 id="dname"></h2>
  <div class="dmeta" id="dmeta"></div>
  <div id="dbody"></div>
</aside>

<script>
var BOOK = {BOOK};
var PROJECTS = BOOK.projects;
var GRAIN = {{it_capacity:"IT capacity",facility_power:"facility power",interconnection_request:"interconnection request",not_disclosed:"not disclosed"}};
var STATUS = {{announced:"announced",in_progress:"in progress",operational:"operational",paused:"paused",canceled:"canceled",undisclosed:"undisclosed"}};
var STCOL = {{announced:"#8a5a2a",in_progress:"#4b5f36",operational:"#3c5568",paused:"#8d8a81",canceled:"#7d2027",undisclosed:"#62605a"}};
var STCOL_D = {{announced:"#c99a5e",in_progress:"#8fae72",operational:"#7da3bd",paused:"#8d8a81",canceled:"#c2564c",undisclosed:"#a49e8f"}};
var REGION_VIEW = {{
  NORAM: {{lat:39.8, lng:-98.5, altitude:1.85}},
  LATAM: {{lat:-15.5, lng:-56.0, altitude:2.05}},
  EU: {{lat:50.0, lng:10.0, altitude:1.7}},
  MENA: {{lat:26.0, lng:45.0, altitude:1.75}},
  SSA: {{lat:1.0, lng:20.0, altitude:2.0}},
  SASIA: {{lat:22.0, lng:80.0, altitude:1.85}},
  APAC: {{lat:15.0, lng:110.0, altitude:2.0}},
  OCEANIA: {{lat:-26.0, lng:134.0, altitude:1.85}}
}};
var state = {{region:"", mw:null, status:""}};

function curTheme(){{ return document.documentElement.getAttribute("data-theme")==="dark" ? "dark" : "light"; }}
function stColor(s){{ return (curTheme()==="dark" ? STCOL_D : STCOL)[s] || "#8d8a81"; }}
function niceDay(iso){{
  if(!iso) return "";
  var p = String(iso).slice(0,10).split("-");
  if(p.length<3) return iso;
  var months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  var m = months[parseInt(p[1],10)-1];
  return (m? (parseInt(p[2],10)+" "+m+" "+p[0]) : iso);
}}
function mwLabel(p){{
  if(p.mw==null) return "not disclosed";
  if(p.mw>=1000 && p.mw%1000===0) return (p.mw/1000)+" GW";
  if(p.mw>=1000) return (Math.round(p.mw/10)/100)+" GW";
  return p.mw+" MW";
}}
function pinKey(p){{ return p.lat.toFixed(5)+","+p.lon.toFixed(5); }}
function withOffsets(rows){{
  var groups = {{}};
  rows.forEach(function(p){{ var k=pinKey(p); (groups[k]=groups[k]||[]).push(p); }});
  var out = [];
  Object.keys(groups).forEach(function(k){{
    var g = groups[k];
    if(g.length===1){{ out.push(Object.assign({{}}, g[0], {{plat:g[0].lat, plng:g[0].lon}})); return; }}
    g.forEach(function(p,i){{
      var a = (i/g.length)*Math.PI*2 + 0.4;
      var d = 0.22;
      out.push(Object.assign({{}}, p, {{plat:p.lat + d*Math.cos(a), plng:p.lon + d*Math.sin(a)}}));
    }});
  }});
  return out;
}}
function passes(p){{
  if(state.region && p.region!==state.region) return false;
  if(state.status && p.status!==state.status) return false;
  if(state.mw!=null){{
    if(p.mw==null) return false;
    if(p.mw < state.mw) return false;
  }}
  return true;
}}
function visible(){{ return PROJECTS.filter(passes); }}

function countCopy(n, total){{
  var bits = [n+" of "+total+" named campuses"];
  if(state.region){{
    var hole = (BOOK.coverage_holes||[]).indexOf(state.region)>=0;
    if(n===0) bits.push(state.region+" has no pins in this book"+(hole?" — a coverage hole, not a load of zero":""));
  }}
  if(state.mw!=null){{
    if(n===0) bits.push("no primary in this book clears "+(state.mw>=1000?"1 GW":(">"+state.mw+" MW"))+". Empty is a coverage hole, not a bug");
    if(state.mw>=250) bits.push("the 250 MW floor is a filter, not a delete; sub-250 disclosed pins stay in the book");
  }}
  if(state.status && n===0) bits.push("no "+(STATUS[state.status]||state.status)+" pin in this book");
  if(state.mw!=null) bits.push("MW-null pins cannot pass a numeric floor");
  return bits.join(". ") + ".";
}}

function setCount(){{
  var rows = visible();
  var el = document.getElementById("count");
  el.textContent = countCopy(rows.length, PROJECTS.length);
  el.classList.toggle("empty", rows.length===0);
  var show = {{}};
  rows.forEach(function(p){{ show[p.id]=1; }});
  document.querySelectorAll("#regbody tr").forEach(function(tr){{
    tr.classList.toggle("off", !show[tr.getAttribute("data-id")]);
  }});
}}

function esc(s){{ return String(s==null?"":s).replace(/[&<>"]/g, function(c){{ return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]; }}); }}

function openDrawer(p){{
  if(!p) return;
  var d = document.getElementById("drawer"), s = document.getElementById("scrim");
  document.getElementById("dop").textContent = p.operator;
  document.getElementById("dname").textContent = p.name;
  var grain = GRAIN[p.mw_grain] || p.mw_grain;
  var mwAs = niceDay(p.mw_as_of);
  var stAs = niceDay(p.status_as_of);
  var meta = [];
  meta.push("<span><b>Place</b> "+esc(p.place)+"</span>");
  meta.push("<span><b>MW</b> "+esc(mwLabel(p))+(mwAs?" · "+esc(mwAs):"")+"</span>");
  meta.push('<span class="chip on">'+esc(grain)+"</span>");
  meta.push("<span><b>Status</b> "+esc(STATUS[p.status]||p.status)+(stAs?" · "+esc(stAs):"")+"</span>");
  if(p.geo) meta.push("<span><b>Geo</b> "+esc(p.geo)+"</span>");
  document.getElementById("dmeta").innerHTML = meta.join("");
  var body = "";
  var quotes = [p.mw_phrase, p.status_phrase].filter(function(q,i,a){{ return q && a.indexOf(q)===i; }});
  quotes.forEach(function(q){{ body += "<blockquote>“"+esc(q)+"”</blockquote>"; }});
  if(p.status==="operational"){{
    body += "<p>Status is <b>operational</b> because the primary said so. That is not an energized-MW print"+(p.mw==null?" — this desk has no campus MW from that page":"")+".</p>";
  }} else {{
    body += "<p>Do not read this pin as live load. Status is <b>"+esc(STATUS[p.status]||p.status)+"</b>.</p>";
  }}
  if(p.mw_grain==="interconnection_request"){{
    body += "<p>The megawatt figure is an <b>interconnection request</b>, not IT capacity.</p>";
  }}
  if(p.mw_grain==="facility_power"){{
    body += "<p>The megawatt figure is <b>facility power</b>, not a published IT-capacity print.</p>";
  }}
  if(p.notes) body += "<p>"+esc(p.notes)+"</p>";
  if(p.url) body += '<p><a href="'+esc(p.url)+'" rel="noopener">Read the primary</a></p>';
  document.getElementById("dbody").innerHTML = body;
  d.hidden = false; s.hidden = false;
  requestAnimationFrame(function(){{ d.classList.add("on"); s.classList.add("on"); }});
  if(history.replaceState) history.replaceState(null, "", "#"+p.id);
}}
function closeDrawer(){{
  var d = document.getElementById("drawer"), s = document.getElementById("scrim");
  d.classList.remove("on"); s.classList.remove("on");
  setTimeout(function(){{ d.hidden = true; s.hidden = true; }}, 320);
  if(history.replaceState && location.hash) history.replaceState(null, "", location.pathname);
}}
document.getElementById("dclose").onclick = closeDrawer;
document.getElementById("scrim").onclick = closeDrawer;
document.addEventListener("keydown", function(e){{ if(e.key==="Escape") closeDrawer(); }});
document.querySelectorAll("[data-open]").forEach(function(btn){{
  btn.onclick = function(){{
    var p = PROJECTS.filter(function(x){{ return x.id===btn.getAttribute("data-open"); }})[0];
    openDrawer(p);
  }};
}});

function bindChips(sel, key, parse){{
  var bar = document.querySelector(sel);
  bar.querySelectorAll(".chip").forEach(function(ch){{
    ch.onclick = function(){{
      bar.querySelectorAll(".chip").forEach(function(x){{ x.classList.remove("on"); }});
      ch.classList.add("on");
      var raw = ch.getAttribute(key) || "";
      state[parse.field] = parse.fn(raw);
      setCount();
      plotPins();
      if(parse.field==="region" && raw && REGION_VIEW[raw] && window._globe){{
        window._globe.pointOfView(REGION_VIEW[raw], 900);
      }}
    }};
  }});
}}
bindChips('[aria-label="Region"]', "data-region", {{field:"region", fn:function(v){{ return v; }}}});
bindChips('[aria-label="Megawatt floor"]', "data-mw", {{field:"mw", fn:function(v){{ return v===""?null:parseInt(v,10); }}}});
bindChips('[aria-label="Status"]', "data-status", {{field:"status", fn:function(v){{ return v; }}}});

function script(src){{ return new Promise(function(res,rej){{ var s=document.createElement("script"); s.src=src; s.onload=res; s.onerror=rej; document.head.appendChild(s); }}); }}
function loadGlobeLibs(){{
  return (async function(){{
    await script("https://unpkg.com/globe.gl@2");
    if(typeof Globe==="undefined") throw new Error("no Globe");
    await script("https://unpkg.com/topojson-client@3.1.0/dist/topojson-client.min.js");
    var world = await (await fetch("https://unpkg.com/world-atlas@2.0.2/countries-110m.json")).json();
    return topojson.feature(world, world.objects.countries).features;
  }})();
}}
function initGlobe(el, w, h, land){{
  var g = Globe()(el).width(w).height(h)
    .backgroundColor("rgba(0,0,0,0)")
    .showAtmosphere(true).atmosphereColor("#bdb5a2").atmosphereAltitude(0.10)
    .hexPolygonsData(land)
    .hexPolygonResolution(3)
    .hexPolygonMargin(0.68)
    .hexPolygonColor(function(){{ return curTheme()==="dark" ? "rgba(222,216,200,0.55)" : "rgba(23,22,20,0.42)"; }});
  g.globeMaterial().color.set("#ddd4c2");
  g.globeMaterial().shininess = 2;
  g.controls().autoRotate = true;
  g.controls().enableZoom = true;
  el.addEventListener("pointerenter", function(){{ g.controls().autoRotate = false; }});
  el.addEventListener("pointerleave", function(){{ g.controls().autoRotate = true; }});
  return g;
}}
function applyGlobeTheme(){{
  if(!window._globe) return;
  window._globe.hexPolygonColor(function(){{ return curTheme()==="dark" ? "rgba(222,216,200,0.55)" : "rgba(23,22,20,0.42)"; }});
  window._globe.atmosphereColor(curTheme()==="dark" ? "#8a8374" : "#bdb5a2");
  plotPins();
}}
function pinRadius(p){{
  if(p.mw==null) return 0.62;
  return 0.48 + 0.95*Math.sqrt(p.mw/5000);
}}
function pinCard(p){{
  return '<div style="font-family:Georgia,\\'Times New Roman\\',serif;background:#f7f4ee;color:#171614;border:1px solid #171614;padding:8px 12px;font-size:13px;line-height:1.45;max-width:260px"><b>'+esc(p.name)+'</b><br>'+esc(p.operator)+'<br>'+esc(mwLabel(p))+' · '+esc(GRAIN[p.mw_grain]||p.mw_grain)+'<br>'+esc(STATUS[p.status]||p.status)+'</div>';
}}
function plotPins(){{
  if(!window._globe) return;
  var rows = withOffsets(visible());
  window._globe.labelsData(rows)
    .labelLat(function(d){{ return d.plat; }})
    .labelLng(function(d){{ return d.plng; }})
    .labelText(function(){{ return ""; }})
    .labelDotRadius(pinRadius)
    .labelColor(function(d){{ return stColor(d.status); }})
    .labelAltitude(0.01)
    .labelLabel(pinCard)
    .onLabelClick(function(d){{ openDrawer(d); }});
}}
function gsize(){{
  var el = document.getElementById("globe");
  return {{w: el.clientWidth, h: Math.min(640, Math.max(420, Math.round(window.innerWidth*0.52)))}};
}}
(async function showGlobe(){{
  var msg = document.getElementById("globemsg");
  try{{
    var land = await loadGlobeLibs();
    var el = document.getElementById("globe");
    var s0 = gsize();
    window._globe = initGlobe(el, s0.w, s0.h, land);
    window._globe.controls().autoRotateSpeed = 0.45;
    window._globe.pointOfView({{lat:24, lng:-20, altitude:2.15}});
    applyGlobeTheme();
    plotPins();
    msg.textContent = "";
    window.addEventListener("resize", function(){{ var s=gsize(); window._globe.width(s.w).height(s.h); }});
  }}catch(e){{
    msg.textContent = "The globe needs a network connection. The register below has every pin.";
  }}
}})();

var tm=document.querySelector('meta[name="theme-color"]'), tg=document.getElementById("themetog");
function cur(){{return document.documentElement.getAttribute("data-theme")==="dark"?"dark":"light"}}
function setT(t,sv){{document.documentElement.setAttribute("data-theme",t);
if(sv){{try{{localStorage.setItem("cnw_theme",t)}}catch(e){{}}}}
tm.content=t==="dark"?"#171511":"#f7f4ee";tg.setAttribute("aria-label",t==="dark"?"Switch to day mode":"Switch to night mode");
applyGlobeTheme();}}
tg.onclick=function(){{setT(cur()==="dark"?"light":"dark",true)}};
setT(cur(),false);
{fnav_script("campuses")}
setCount();
(function deep(){{
  var id = (location.hash||"").replace("#","");
  if(!id) return;
  var p = PROJECTS.filter(function(x){{ return x.id===id; }})[0];
  if(p) openDrawer(p);
}})();
</script>
</body>
</html>'''

open(os.path.join(ROOT, "campuses.html"), "w").write(PAGE)
print(f"campuses.html generated: {len(projects)} projects, {updated}")
