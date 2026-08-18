#!/usr/bin/env python3
# Daily brief generator: brief.json (single source of truth) -> brief.html + brief.xml.
# Run from repo root or src/:  python3 src/build_brief.py
# Do not invent prices, chips, or 1d/7d candles. prev_usd / delta stay null unless
# a second dated sourced print already sits in silicon-history.json.
import json, html, os
from datetime import datetime
from fnav import css as fnav_css, markup as fnav_markup, script as fnav_script
from seo import og_block, breadcrumb_ld, person_author, org_publisher

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
B = json.load(open(os.path.join(ROOT, "brief.json")))


def money(x):
    if x is None:
        return "—"
    s = f"{x:.3f}"
    if s.endswith("0"):
        s = s[:-1]
    return f"${s}"


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


def country_li(row):
    name = html.escape(row["name"])
    note = html.escape(row["note"])
    slug = row.get("slug")
    title = f'<a href="/#{html.escape(slug)}">{name}</a>' if slug else f"<b>{name}</b>"
    return f"<li>{title} — {note}</li>"


def watch_li(row):
    name = html.escape(row["name"])
    note = html.escape(row["note"])
    slug = row.get("slug")
    title = f'<a href="/#{html.escape(slug)}">{name}</a>' if slug else f"<b>{name}</b>"
    return f"<li>{title} — {note}</li>"


def silicon_row(row):
    prev = money(row.get("prev_usd"))
    delta = row.get("delta")
    delta_s = "—" if delta is None else html.escape(str(delta))
    note = html.escape(row.get("note") or "")
    return (
        f'<tr id="{html.escape(row["id"])}">'
        f'<td class="chip"><a href="/silicon.html#{html.escape(row["id"])}">{html.escape(row["name"])}</a></td>'
        f'<td class="px">{money(row.get("display_usd"))}</td>'
        f'<td>{html.escape(row.get("venue") or "")}<span class="sub">{html.escape(row.get("term") or "")}</span></td>'
        f'<td>{html.escape(nice_date(row.get("as_of")))}</td>'
        f'<td>{prev}</td>'
        f'<td>{delta_s}</td>'
        f'<td class="note">{note}</td>'
        f"</tr>"
    )


si_rows = "".join(silicon_row(r) for r in B["silicon"])
co_lis = "".join(country_li(r) for r in B["countries"])
wa_lis = "".join(watch_li(r) for r in B["watch"])
src_lis = "".join(
    f'<li><a href="{html.escape(s["url"])}" rel="noopener">{html.escape(s["name"])}</a>'
    f' — {html.escape(s.get("note") or "")}</li>'
    for s in B["sources"]
)

updated = B["updated"]
nice_upd = datetime.strptime(updated, "%Y-%m-%d").strftime("%d %b %Y")
brief_desc = B.get("description") or B["lede"]
ld = json.dumps({
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": B["title"],
    "datePublished": updated,
    "dateModified": updated,
    "description": brief_desc,
    "url": "https://compute.world/brief",
    "author": person_author(),
    "publisher": org_publisher(),
    "isAccessibleForFree": True,
})
crumb = json.dumps(breadcrumb_ld([
    ("compute.world", "https://compute.world/"),
    ("The daily tape", "https://compute.world/brief"),
]))
faq_ld = json.dumps({
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
        {"@type": "Question", "name": "What is the daily tape?",
         "acceptedAnswer": {"@type": "Answer", "text": "The daily tape is the weekday public brief of compute.world, the world's compute & silicon index: country conversion signals already on The Wire, plus today's display prints from the Silicon Tape. Labeled terms only."}},
        {"@type": "Question", "name": "Why is 7-day percent change a dash?",
         "acceptedAnswer": {"@type": "Answer", "text": "US list prices do not tick daily. 7d lights up after a week of our own scrape. prev_usd and delta appear only from two dated same-series prints in silicon-history.json."}},
        {"@type": "Question", "name": "Why does Cerebras have no $/hour?",
         "acceptedAnswer": {"@type": "Answer", "text": "Cerebras is token/enterprise. There is no sourced public accelerator-hour. The brief will not print aggregator $0.75–$12.50 as a Cerebras hour."}},
    ],
})
brief_og = og_block(
    html.escape(B["title"]),
    html.escape(brief_desc),
    "https://compute.world/brief",
    "og-brief.png",
    og_type="article",
    image_alt="The daily tape — sourced country signals and silicon prints",
)

PAGE = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#f7f4ee">
<script>(function(){{try{{var t=localStorage.getItem("cnw_theme");if(t!=="dark"&&t!=="light"){{var h=new Date().getHours();t=(h>=19||h<7)?"dark":"light";}}document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();</script>
<title>{html.escape(B["title"])} · compute.world</title>
<meta name="description" content="{html.escape(brief_desc)}">
<link rel="canonical" href="https://compute.world/brief">
<meta name="robots" content="index,follow,max-image-preview:large">
{brief_og}
<link rel="alternate" type="application/rss+xml" title="The daily tape · compute.world" href="https://compute.world/brief.xml">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' fill='%23f7f4ee'/><text x='32' y='44' font-family='Georgia,serif' font-size='36' fill='%23171614' text-anchor='middle'>B</text></svg>">
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
h2{{font-weight:400;font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:36px 0 12px}}
.prose{{color:var(--muted);font-size:16px}}
.prose li{{margin:0 0 10px 18px}}
.prose b{{color:var(--ink)}}
.tblwrap{{overflow-x:auto;margin:8px 0 0;border-top:2px solid var(--rule2)}}
table.tape{{width:100%;border-collapse:collapse;font-size:13.5px;min-width:720px}}
.tape th{{font-weight:400;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);text-align:left;
padding:11px 10px 10px;border-bottom:1px solid var(--rule2);white-space:nowrap}}
.tape td{{padding:12px 10px;border-bottom:1px solid var(--rule);vertical-align:top}}
.tape .px{{font-weight:600;font-size:15px;letter-spacing:-.02em}}
.tape .sub{{display:block;font-size:11px;color:var(--faint);margin-top:2px}}
.tape .note{{font-size:12.5px;color:var(--muted);max-width:320px}}
.tape a{{border:none}}
.tape a:hover{{color:var(--accent)}}
.hint{{margin:10px 0 0;font-size:12.5px;color:var(--faint)}}
.colophon{{margin-top:56px;border-top:2px solid var(--rule2);padding:24px 0 56px;text-align:center}}
.colophon .c1{{font-size:12px;letter-spacing:.3em;text-transform:uppercase}}
.colophon .c2{{margin-top:10px;font-size:12.5px;color:var(--muted)}}
.faq{{margin:44px 0 0;border-top:1px solid var(--rule2);padding-top:18px}}
.faq h2{{font-weight:400;font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:0 0 14px}}
.faq h3{{font-weight:600;font-size:16px;margin:16px 0 6px}}
.faq p{{font-size:15px;color:var(--muted)}}
.faq p b{{color:var(--ink)}}
@media(max-width:760px){{.wrap{{padding:0 18px}}.lede{{padding:36px 0 8px}}}}
</style>
</head>
<body class="fnav-inner">
<button id="themetog" class="tchip" aria-label="Switch to night mode" title="Day / Night">
  <svg class="ic-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>
  <svg class="ic-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.9 1.9M19.1 4.9l-1.8 1.8M6.7 17.3l-1.9 1.9"/></svg>
</button>
{fnav_markup("brief")}
<div class="wrap">
  <div class="masthead">
    <div class="name"><a href="/"><b>COMPUTE</b>.WORLD</a></div>
    <div class="sub">The daily tape · the world's compute &amp; silicon index · {nice_upd}</div>
    <div class="mastrule"></div>
  </div>

  <div class="lede">
    <h1>{html.escape(B["title"].split(" · ")[0])}, <em>as printed</em>.</h1>
    <p class="standfirst">{html.escape(B["lede"])}</p>
    <div class="subrow">
      <span class="lab">v0</span>
      <span>{nice_upd}</span>
      <a href="/brief.json">brief.json</a>
      <a href="/brief.xml">RSS</a>
      <a href="/#silicon">Silicon tab</a>
      <a href="/#subscribe">Subscribe</a>
    </div>
  </div>

  <h2>Countries</h2>
  <ul class="prose">{co_lis}</ul>

  <h2>Silicon — display prints</h2>
  <div class="tblwrap">
    <table class="tape">
      <thead>
        <tr>
          <th>Chip</th>
          <th>Display print</th>
          <th>Venue / term</th>
          <th>As-of</th>
          <th>Prior sourced</th>
          <th>Delta</th>
          <th>Note</th>
        </tr>
      </thead>
      <tbody>
{si_rows}
      </tbody>
    </table>
  </div>
  <p class="hint">Delta is empty unless a second dated sourced print of the same display series already lives in <a href="/silicon-history.json">silicon-history.json</a>. H100 1y is Lambda $2.99 (12 Aug 2025) → $3.99. That is not a 7-day change. SA 1y $2.35 is STALE.</p>

  <h2>Watch</h2>
  <ul class="prose">{wa_lis}</ul>

  <h2>Sources</h2>
  <ul class="prose">{src_lis}</ul>

  <section class="faq" id="faq">
    <h2>In brief</h2>
    <h3>What is the index?</h3>
    <p>compute.world is <b>the world's compute &amp; silicon index</b>: CNW™ prices 108 countries; the Silicon Tape prints sourced chips.</p>
    <h3>What is the tape?</h3>
    <p>This page is the weekday public brief — country conversion already on The Wire, plus labeled silicon display prints. Not a market cap.</p>
    <h3>Why is 7-day a dash?</h3>
    <p>US list prices do not tick daily. 7d lights up after a week of our own scrape. H100 1y (+33.4%) is Lambda $2.99 → $3.99, not a daily candle. SA 1y $2.35 is STALE.</p>
    <h3>Why does Cerebras have no $/hour?</h3>
    <p>Token / enterprise. No public accelerator-hour. We will not print aggregator $0.75–$12.50 as a Cerebras hour.</p>
  </section>

  <div class="colophon">
    <div class="c1">COMPUTE.WORLD</div>
    <div class="c2">The daily tape · {nice_upd} · the world's compute &amp; silicon index · CNW™ · GDC™ · &copy; 2026 Pukar C. Hamal · San Francisco, CA</div>
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
{fnav_script("brief")}
</script>
</body>
</html>'''

open(os.path.join(ROOT, "brief.html"), "w").write(PAGE)

# RSS: one item for the day's brief, plus silicon rows as short items (display prints only).
pub = datetime.strptime(updated, "%Y-%m-%d").strftime("%a, %d %b %Y") + " 12:00:00 GMT"
si_items = "".join(f'''
  <item>
    <title>{html.escape(r["name"])} · {money(r.get("display_usd"))} {html.escape(r.get("term") or "")}</title>
    <link>https://compute.world/brief#{html.escape(r["id"])}</link>
    <guid isPermaLink="false">compute.world/brief/{updated}/{html.escape(r["id"])}</guid>
    <pubDate>{pub}</pubDate>
    <description>{html.escape(r["name"])}: display {money(r.get("display_usd"))} {html.escape(r.get("term") or "")} at {html.escape(r.get("venue") or "")} as of {html.escape(nice_date(r.get("as_of")))}. {html.escape(r.get("note") or "")}</description>
  </item>''' for r in B["silicon"])

co_block = " ".join(f'{r["name"]}: {r["note"]}' for r in B["countries"])
RSS = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>The daily tape · compute.world</title>
  <link>https://compute.world/brief</link>
  <description>{html.escape(B["lede"])}</description>
  <language>en</language>
  <item>
    <title>{html.escape(B["title"])}</title>
    <link>https://compute.world/brief</link>
    <guid isPermaLink="true">https://compute.world/brief#{updated}</guid>
    <pubDate>{pub}</pubDate>
    <description>{html.escape(B["lede"])} Countries: {html.escape(co_block)}</description>
  </item>{si_items}
</channel></rss>'''
open(os.path.join(ROOT, "brief.xml"), "w").write(RSS)
print(f"brief.html + brief.xml generated: {len(B['silicon'])} silicon rows, {updated}")
