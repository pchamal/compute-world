#!/usr/bin/env python3
# Data centers FAQ: data-centers.json -> data-centers.html + data-centers.xml.
# Run from repo root or src/:  python3 src/build_datacenters.py
# Do not invent acres/MW, household-bill dollars, job multipliers, or ranks.
import json, html, os
from datetime import datetime
from fnav import css as fnav_css, markup as fnav_markup, script as fnav_script
from seo import og_block, breadcrumb_ld, person_author, org_publisher, nice_day

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = json.load(open(os.path.join(ROOT, "data-centers.json")))

updated = D["updated"]
nice_upd = nice_day(updated)
nice_short = datetime.strptime(updated, "%Y-%m-%d").strftime("%d %b %Y")


def note_sups(ids):
    if not ids:
        return ""
    bits = []
    for i in ids:
        bits.append(f'<sup><a href="#n{i}">{i}</a></sup>')
    return "".join(bits)


def para_html(p):
    runin = p.get("runin")
    text = html.escape(p["text"])
    # Allow italics already escaped; keep plain.
    head = f'<span class="runin">"{html.escape(runin)}"</span> ' if runin else ""
    return f"<p>{head}{text}{note_sups(p.get('notes') or [])}</p>"


def q_html(q):
    paras = "".join(para_html(p) for p in q["paragraphs"])
    return (
        f'<article class="qa" id="{html.escape(q["id"])}">\n'
        f'  <h2>{html.escape(q["q"])}</h2>\n'
        f"  {paras}\n"
        f"</article>"
    )


def note_li(n):
    name = html.escape(n["name"])
    url = html.escape(n["url"])
    text = html.escape(n["text"])
    return (
        f'<li id="n{n["id"]}">'
        f'<a href="{url}" rel="noopener">{name}</a> — {text}</li>'
    )


q_block = "\n".join(q_html(q) for q in D["questions"])
note_block = "".join(note_li(n) for n in D["notes"])
toc = "".join(
    f'<li><a href="#{html.escape(q["id"])}">{html.escape(q["q"])}</a></li>'
    for q in D["questions"]
)

ld = json.dumps({
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": D["title"],
    "datePublished": updated,
    "dateModified": updated,
    "description": D["description"],
    "url": "https://compute.world/data-centers.html",
    "author": person_author(),
    "publisher": org_publisher(),
    "isAccessibleForFree": True,
    "citation": D["cite"],
}, ensure_ascii=False)
crumb = json.dumps(breadcrumb_ld([
    ("compute.world", "https://compute.world/"),
    ("Data centers FAQ", "https://compute.world/data-centers.html"),
]), ensure_ascii=False)
faq_ld = json.dumps({
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {
            "@type": "Question",
            "name": q["q"],
            "url": f"https://compute.world/data-centers.html#{q['id']}",
            "acceptedAnswer": {"@type": "Answer", "text": q["ld"]},
        }
        for q in D["questions"]
    ],
}, ensure_ascii=False)
dc_og = og_block(
    html.escape(D["title"] + " · compute.world"),
    html.escape(D["description"]),
    "https://compute.world/data-centers.html",
    "og.png",
    og_type="article",
    image_alt="Data centers FAQ — sourced grain on campus power, water, land, tax, jobs",
)

PAGE = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#f7f4ee">
<script>(function(){{try{{var t=localStorage.getItem("cnw_theme");if(t!=="dark"&&t!=="light"){{var h=new Date().getHours();t=(h>=19||h<7)?"dark":"light";}}document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();</script>
<title>{html.escape(D["title"])} · compute.world</title>
<meta name="description" content="{html.escape(D["description"])}">
<link rel="canonical" href="https://compute.world/data-centers.html">
<meta name="robots" content="index,follow,max-image-preview:large">
{dc_og}
<link rel="alternate" type="application/rss+xml" title="Data centers FAQ · compute.world" href="https://compute.world/data-centers.xml">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' fill='%23f7f4ee'/><text x='32' y='44' font-family='Georgia,serif' font-size='36' fill='%23171614' text-anchor='middle'>D</text></svg>">
<script type="application/ld+json">{ld}</script>
<script type="application/ld+json">{crumb}</script>
<script type="application/ld+json">{faq_ld}</script>
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
.wrap{{max-width:920px;margin:0 auto;padding:0 28px}}
.masthead{{padding:34px 0 0;text-align:center}}
.masthead .name{{font-size:15px;letter-spacing:.34em;text-transform:uppercase}}
.masthead .name a{{border:none;color:var(--ink)}}
.masthead .name b{{font-weight:600}}
.masthead .sub{{margin-top:8px;font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
.mastrule{{margin-top:20px;border-top:2px solid var(--rule2);border-bottom:1px solid var(--rule2);height:5px}}
.lede{{padding:48px 0 8px}}
h1{{font-weight:400;font-size:clamp(28px,4.4vw,40px);line-height:1.16}}
h1 em{{font-style:italic}}
.standfirst{{margin-top:18px;font-size:17.5px;color:var(--muted)}}
.subrow{{display:flex;flex-wrap:wrap;gap:8px 26px;align-items:baseline;margin:26px 0 0;padding:16px 0;border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule);font-size:13px;letter-spacing:.1em;text-transform:uppercase}}
.subrow .lab{{color:var(--faint);font-size:11px;letter-spacing:.16em}}
.toc{{margin:28px 0 8px}}
.toc .lab{{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}}
.toc ol{{margin:0 0 0 18px;color:var(--muted);font-size:15.5px}}
.toc li{{margin:0 0 7px}}
.qa{{margin:36px 0 0;padding-top:22px;border-top:1px solid var(--rule)}}
.qa h2{{font-weight:400;font-size:22px;line-height:1.28;margin:0 0 14px}}
.qa p{{color:var(--muted);font-size:16.5px;margin:0 0 12px}}
.qa p .runin{{font-weight:600;color:var(--ink)}}
.qa p b{{color:var(--ink)}}
sup{{font-size:11px;line-height:0;color:var(--accent)}}
sup a{{border-bottom:none}}
.notes{{margin:48px 0 0;border-top:2px solid var(--rule2);padding-top:22px}}
.notes h2{{font-weight:400;font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:0 0 14px}}
.notes ol{{margin:0 0 0 18px;color:var(--muted);font-size:13.5px}}
.notes li{{margin:0 0 10px}}
.colophon{{margin-top:56px;border-top:2px solid var(--rule2);padding:24px 0 56px;text-align:center}}
.colophon .c1{{font-size:12px;letter-spacing:.3em;text-transform:uppercase}}
.colophon .c2{{margin-top:10px;font-size:12.5px;color:var(--muted)}}
@media(max-width:760px){{.wrap{{padding:0 18px}}.lede{{padding:36px 0 8px}}.qa h2{{font-size:20px}}}}
</style>
</head>
<body class="fnav-inner">
<button id="themetog" class="tchip" aria-label="Switch to night mode" title="Day / Night">
  <svg class="ic-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>
  <svg class="ic-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.9 1.9M19.1 4.9l-1.8 1.8M6.7 17.3l-1.9 1.9"/></svg>
</button>
{fnav_markup("datacenters")}
<div class="wrap">
  <div class="masthead">
    <div class="name"><a href="/"><b>COMPUTE</b>.WORLD</a></div>
    <div class="sub">Data centers · FAQ · the world's compute &amp; silicon index · {nice_upd}</div>
    <div class="mastrule"></div>
  </div>

  <div class="lede">
    <h1>Data centers, <em>as asked</em>.</h1>
    <p class="standfirst">{html.escape(D["lede"])}</p>
    <div class="subrow">
      <span class="lab">FAQ</span>
      <span>{nice_short}</span>
      <a href="/data-centers.json">data-centers.json</a>
      <a href="/data-centers.xml">RSS</a>
      <a href="/wire.html">The Wire</a>
      <a href="/contact.html">The Desk</a>
    </div>
  </div>

  <nav class="toc" aria-label="Questions">
    <div class="lab">The book</div>
    <ol>{toc}</ol>
  </nav>

{q_block}

  <section class="notes" id="notes" aria-labelledby="notes-h">
    <h2 id="notes-h">Sources</h2>
    <ol>{note_block}</ol>
    <p style="margin-top:18px;font-size:14px;color:var(--muted)">Cite as: <code>{html.escape(D["cite"])}</code>. A wrong number: <a href="/contact.html">The Desk</a>.</p>
  </section>

  <div class="colophon">
    <div class="c1">COMPUTE.WORLD</div>
    <div class="c2">Data centers FAQ · {nice_upd} · the world's compute &amp; silicon index · CNW™ · GDC™ · &copy; 2026 Pukar C. Hamal · San Francisco, CA</div>
  </div>
</div>
<script>
var tm=document.querySelector('meta[name="theme-color"]'), tg=document.getElementById("themetog");
function cur(){{return document.documentElement.getAttribute("data-theme")==="dark"?"dark":"light"}}
function setT(t,sv){{document.documentElement.setAttribute("data-theme",t);
if(sv){{try{{localStorage.setItem("cnw_theme",t)}}catch(e){{}}}}
tm.content=t==="dark"?"#171511":"#f7f4ee";tg.setAttribute("aria-label",t==="dark"?"Switch to day mode":"Switch to night mode");}}
tg.onclick=function(){{setT(cur()==="dark"?"light":"dark",true)}};
setT(cur(),false);
{fnav_script("datacenters")}
</script>
</body>
</html>'''

# fnav must exist before PAGE is formatted — update fnav first, then rebuild.
open(os.path.join(ROOT, "data-centers.html"), "w").write(PAGE)

pub = datetime.strptime(updated, "%Y-%m-%d").strftime("%a, %d %b %Y") + " 12:00:00 GMT"
items = "".join(f'''
  <item>
    <title>{html.escape(q["q"])}</title>
    <link>https://compute.world/data-centers.html#{html.escape(q["id"])}</link>
    <guid isPermaLink="true">https://compute.world/data-centers.html#{html.escape(q["id"])}</guid>
    <pubDate>{pub}</pubDate>
    <description>{html.escape(q["ld"])}</description>
  </item>''' for q in D["questions"])

RSS = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Data centers FAQ · compute.world</title>
  <link>https://compute.world/data-centers.html</link>
  <description>{html.escape(D["lede"])}</description>
  <language>en</language>
  <lastBuildDate>{pub}</lastBuildDate>{items}
</channel></rss>'''
open(os.path.join(ROOT, "data-centers.xml"), "w").write(RSS)
print(f"data-centers.html + data-centers.xml generated: {len(D['questions'])} questions, {updated}")
