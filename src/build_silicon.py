#!/usr/bin/env python3
# The Silicon Tape generator: silicon.json (single source of truth) -> silicon.html + silicon.xml.
# Run from repo root or src/:  python3 src/build_silicon.py
import json, html, os, sys
from datetime import datetime
from fnav import css as fnav_css, markup as fnav_markup, script as fnav_script
from subscribe import css as sub_css, markup as sub_markup, script as sub_script
from seo import og_block, breadcrumb_ld, person_author, org_publisher

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
S = json.load(open(os.path.join(ROOT, "silicon.json")))
SRC = {s["id"]: s for s in S["sources"]}
chips = sorted(S["chips"], key=lambda c: c["rank"])


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
    if d.get("primary") == "CNY" and d.get("cny_per_gpu_hr") is not None:
        return f"¥{d['cny_per_gpu_hr']:.2f}"
    return money(d.get("usd_per_gpu_hr"))


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


for c in chips:
    got, exp = c["score"], expected_score(c)
    if abs(got - exp) > 0.001:
        sys.exit(f"score mismatch {c['id']}: json={got} formula={exp}")

# ---- table rows (static; JS re-sorts / filters the same markup) ----
rows = []
for c in chips:
    d = c["display"]
    also = c.get("also") or {}
    also_text = html.escape(also.get("text") or "—")
    disp_note = html.escape(d.get("note") or "")
    href = src_url(d.get("source_id"))
    src_lab = html.escape(src_name(d.get("source_id")))
    src_a = f'<a href="{href}" rel="noopener">{src_lab}</a>' if href else src_lab
    price_title = f'{d["label"]} · {nice_date(d["as_of"])} · {src_name(d.get("source_id"))}'
    mem = html.escape(c["memory"])
    mem_note = html.escape(c["memory_note"] or "")
    mem_html = f'<span class="mem">{mem}</span>'
    if mem_note:
        mem_html += f'<span class="sub" title="{mem_note}">{mem_note}</span>'
    venues = html.escape(" · ".join(c["venues"]))
    rows.append(f'''<tr class="chiprow" id="{html.escape(c["id"])}" data-id="{html.escape(c["id"])}" data-vendor="{html.escape(c["vendor"])}" data-rank="{c["rank"]}" data-score="{c["score"]}" data-price="{d["usd_per_gpu_hr"] if d.get("usd_per_gpu_hr") is not None else ""}" tabindex="0" role="button" aria-expanded="false" aria-controls="drawer">
  <td class="num" data-col="rank">{c["rank"]}</td>
  <td class="chip" data-col="name"><span class="cn">{html.escape(c["name"])}</span></td>
  <td data-col="vendor">{html.escape(c["vendor"])}</td>
  <td class="memtd" data-col="memory">{mem_html}</td>
  <td class="price" data-col="price" title="{html.escape(price_title)}">
    <span class="px">{html.escape(display_px(d))}</span>
    <span class="term">{html.escape(d["label"])}</span>
    <span class="asof">{html.escape(nice_date(d["as_of"]))} · {src_a}</span>
    {f'<span class="sub">{disp_note}</span>' if disp_note else ""}
  </td>
  <td class="also" data-col="also"><span class="also-t">{also_text}</span></td>
  <td class="venues" data-col="venues">{venues}</td>
  <td class="scarce" data-col="scarcity">{html.escape(c["scarcity_label"])}<span class="sub">{html.escape(c["scarcity"])}</span></td>
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
        {"@type": "Question", "name": "Why does the tape refuse 7-day percent change?",
         "acceptedAnswer": {"@type": "Answer", "text": "There is no sourced 7-day or 30-day percent-change series for these prints. compute.world will not invent a move. A prior dated print is shown only when that same display series already lives in the repo (H100 SemiAnalysis 1y $1.70 in Oct 2025 beside $2.35 in Mar 2026)."}},
        {"@type": "Question", "name": "Why does Cerebras have no $/hour?",
         "acceptedAnswer": {"@type": "Answer", "text": "Cerebras Cloud is sold as a token API and as enterprise. There is no sourced public accelerator-hour in this snapshot. Aggregator ranges such as $0.75–$12.50 are omitted on purpose. Groq is listed the same way: token API, no invented chip-hour."}},
        {"@type": "Question", "name": "What is compute.world?",
         "acceptedAnswer": {"@type": "Answer", "text": "compute.world is the world's compute & silicon index: the Compute Net Worth Index (CNW™) prices 108 countries, and the Silicon Tape prints sourced chips. Created by Pukar C. Hamal."}},
    ],
})
si_title = "The Silicon Tape · AI accelerator rental index · compute.world"
si_desc = (
    f"The Silicon Tape: {len(chips)} sourced AI accelerator prints. "
    f"Snapshot {S['updated']}. B200 $6.69 Lambda OD · H100 $2.35 SA 1y · Ascend 910C ¥10.79/hr. "
    "No market cap. No invented 7-day moves."
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
table.tape{{width:100%;border-collapse:collapse;font-size:13.5px;min-width:980px}}
.tape th{{font-weight:400;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);text-align:left;
padding:11px 10px 10px;border-bottom:1px solid var(--rule2);white-space:nowrap;cursor:pointer;user-select:none}}
.tape th.num,.tape td.num{{text-align:right}}
.tape th:hover{{color:var(--ink)}}
.tape th.sorted{{color:var(--ink)}}
.tape th .arr{{display:inline-block;margin-left:4px;color:var(--faint);font-size:9px}}
.tape td{{padding:13px 10px;border-bottom:1px solid var(--rule);vertical-align:top}}
.tape tr.chiprow{{cursor:pointer}}
.tape tr.chiprow:hover td{{background:var(--tint)}}
.tape tr.chiprow.open td{{background:var(--tint)}}
.tape .cn{{font-weight:600;border-bottom:1px solid transparent}}
.tape tr.chiprow:hover .cn{{color:var(--accent);border-bottom-color:var(--accent)}}
.tape .px{{font-size:16px;font-weight:600;letter-spacing:-.02em;display:block}}
.tape .term,.tape .asof,.tape .sub{{display:block;font-size:11px;letter-spacing:.02em;color:var(--faint);line-height:1.45;margin-top:2px;text-transform:none}}
.tape .asof a{{border:none;color:var(--muted)}}
.tape .asof a:hover{{color:var(--accent)}}
.tape .also-t{{color:var(--muted);font-size:12.5px}}
.tape .venues{{color:var(--muted);font-size:12px;max-width:160px}}
.tape .scarce{{font-size:12.5px}}
.tape .score{{font-weight:600}}
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
      <a href="/silicon.xml">RSS</a>
      <a href="/">Nation-State Index</a>
      <a href="/brief">Daily brief</a>
    </div>
  </div>

  {sub_markup()}

  <div class="chips" role="tablist" aria-label="Vendor filter">
    {vendor_bar}
  </div>

  <div class="tblwrap">
    <table class="tape" id="tape">
      <thead>
        <tr>
          <th class="num sorted" data-sort="rank" data-type="num"># <span class="arr">▼</span></th>
          <th data-sort="name" data-type="str">Chip <span class="arr"></span></th>
          <th data-sort="vendor" data-type="str">Vendor <span class="arr"></span></th>
          <th data-sort="memory" data-type="str">Memory <span class="arr"></span></th>
          <th data-sort="price" data-type="num">Display print <span class="arr"></span></th>
          <th data-sort="also" data-type="str">Range / second quote <span class="arr"></span></th>
          <th data-sort="venues" data-type="str">Venues <span class="arr"></span></th>
          <th data-sort="scarcity" data-type="str">Scarcity <span class="arr"></span></th>
          <th class="num" data-sort="score" data-type="num">Score <span class="arr"></span></th>
        </tr>
      </thead>
      <tbody>
{chr(10).join(rows)}
      </tbody>
    </table>
  </div>
  <p class="hint">Click a row for every sourced quote, dates, and what we will not show. Display prices are labeled terms — not averages.</p>

  <details class="meth" open>
    <summary>How the tape is ranked — and what it refuses to be</summary>
    <div class="mb">
      <p><b>Rank = 0.40 × liquidity + 0.35 × demand + 0.25 × frontier</b>, each scored 0–3. The composite is ordinal hygiene, not a valuation, not a market cap, not a forecast.</p>
      <p><b>Liquidity.</b> 0 none; 1 one primary venue; 2 two–three venues; 3 four or more spanning a neocloud and a hyperscaler.</p>
      <p><b>Demand.</b> 3 named sold-out, booked, or scarce in 2026 trade press; 2 listed but sales-gated or tight; 1 widely listed on-demand; 0 unknown.</p>
      <p><b>Frontier.</b> 3 current training / rack frontier; 2 current workhorse; 1 commodity / prior-gen.</p>
      <p><b>Display-price convention.</b> Prefer a labeled <b>1y contract</b> when SemiAnalysis publishes one (H100). Else a labeled <b>on-demand</b> print from the most liquid public neocloud (Lambda, else CoreWeave). A second venue stays in the row. Capacity Blocks, marketplace floors, and on-demand are never blended into one unlabeled number.</p>
      <p><b>As-of dates.</b> SemiAnalysis public prints <b>stop at April 2026</b> and are labeled that way. August 2026 figures are neocloud and hyperscaler list pages fetched <b>2026-08-18</b>.</p>
      <p><b>Omitted this snapshot</b> — no invented rows:</p>
      <ul>{omitted}</ul>
      <p>Machine-readable: <a href="/silicon.json">silicon.json</a> (CC BY 4.0, attribution to compute.world). Cite as: <code>{html.escape(S["cite"])}</code>. Corrections: <a href="/contact.html">get in touch</a>. Half of <a href="/">the world's compute &amp; silicon index</a>.</p>
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
    <h3>Why is there no 7-day percent change?</h3>
    <p>No source publishes a 7-day or 30-day percent-change series for these prints. We will not invent one. A prior dated print appears only when that same display series already lives in the repo.</p>
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
  if(q.cny_per_gpu_hr!=null) return "¥"+Number(q.cny_per_gpu_hr).toFixed(2)+(q.usd_per_gpu_hr!=null?" · "+money(q.usd_per_gpu_hr):"");
  if(q.range) return money(q.range[0])+"–"+money(q.range[1]);
  var p = money(q.usd_per_gpu_hr);
  if(q.approx && q.usd_per_gpu_hr!=null) p = "~"+p;
  if(q.unit) p += " / "+q.unit;
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
  document.getElementById("dbody").innerHTML =
    "<h3>Quotes</h3><table class=\\"qtable\\"><thead><tr><th>Venue / term</th><th>$ / GPU-hr</th><th>As-of · source</th></tr></thead><tbody>"+qrows+"</tbody></table>"+
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
  r.querySelectorAll("a").forEach(function(a){{ a.addEventListener("click", function(e){{ e.stopPropagation(); }}); }});
}});
document.getElementById("dclose").onclick = closeD;
scrim.onclick = closeD;
document.addEventListener("keydown", function(e){{ if(e.key==="Escape") closeD(); }});
if(location.hash){{ var hid = location.hash.slice(1); if(document.getElementById(hid)) openD(hid); }}

document.querySelectorAll(".chips .chip").forEach(function(ch){{
  ch.onclick = function(){{
    document.querySelectorAll(".chips .chip").forEach(function(x){{ x.classList.remove("on"); }});
    ch.classList.add("on");
    var v = ch.getAttribute("data-v");
    document.querySelectorAll("tr.chiprow").forEach(function(r){{
      r.style.display = (!v || r.dataset.vendor===v) ? "" : "none";
    }});
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
          var an = parseFloat(key==="price"?a.dataset.price: key==="score"?a.dataset.score: a.dataset.rank);
          var bn = parseFloat(key==="price"?b.dataset.price: key==="score"?b.dataset.score: b.dataset.rank);
          if(isNaN(an)) an = -Infinity; if(isNaN(bn)) bn = -Infinity;
          return (an-bn)*state.dir;
        }}
        return (av.textContent.trim().toLowerCase()).localeCompare(bv.textContent.trim().toLowerCase())*state.dir;
      }});
      rows.forEach(function(r){{ tb.appendChild(r); }});
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
