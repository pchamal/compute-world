#!/usr/bin/env python3
# Physical stack page: clerk-voice outline of the eight layers behind AI.
# Framing credited to MTS Intelligence. Do not paste their prose or figures
# we have not checked against their page or /api/compute.
# Run from repo root or src/:  python3 src/build_physical_stack.py
import json
import os
from fnav import css as fnav_css, markup as fnav_markup, script as fnav_script
from desk_chrome import MARKET_THEME_CSS, cite_line, SITE
from seo import og_block, breadcrumb_ld, person_author, org_publisher, nice_day

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# MTS Atlas snapshot we checked. Counts come from GET /api/compute.
MTS_PAGE = "https://intelligence.mts.now/compute"
MTS_API = "https://intelligence.mts.now/api/compute"
MTS_SNAPSHOT = "2026-08-25"
PAGE_ASOF = "2026-09-14"

MTS_CITE = (
    "MTS Intelligence (2026). The Physical Stack Behind AI: an attributed "
    "record of AI compute. MTS Atlas, snapshot 2026-08-25. "
    "https://intelligence.mts.now/compute"
)
CW_CITE = cite_line(
    "The physical stack behind AI",
    f"{SITE}/physical-stack.html",
    PAGE_ASOF,
)

# Verified against MTS GET /api/compute on 2026-09-14 (snapshot_id compute-2026-08-25).
API_COUNTS = {
    "facilities": 83,
    "gpu_clusters": 482,
    "pricing_observations": 2935,
    "company_economics": 53,
}

# Verified on the MTS page (not in the API summary). Keep the attribution glued on.
PAGE_FACTS = [
    (
        "83 facilities, 482 GPU clusters",
        "The 2026-08-25 Atlas snapshot holds 83 facility records and 482 GPU-cluster records. "
        "Those are counts of attributed rows, not a census of every hall on earth.",
        "MTS /api/compute · Epoch AI (CC BY) for facilities and clusters",
    ),
    (
        "2,935 catalog price observations",
        "Official Azure and Google Cloud catalogs supplied 2,935 price observations in that snapshot. "
        "A catalog rate is a public list price, not the bill a buyer actually pays.",
        "MTS /api/compute · Azure Retail Prices API · Google Cloud Billing Catalog",
    ),
    (
        "53 public companies on the SEC tape",
        "Standardized EDGAR facts sit on 53 public companies in the same snapshot. "
        "Capex and depreciation on that tape cover more than AI halls; do not read them as GPU inventory.",
        "MTS /api/compute · SEC EDGAR company facts",
    ),
    (
        "H100 list rates, 4.0× apart",
        "On the MTS page, official H100 catalog rates run from $4.57 to $18.37 per accelerator-hour "
        "across 155 comparable observations — a 4.0× spread inside one generation. "
        "This desk does not reprint their charts.",
        "MTS page · Azure and Google Cloud catalogs",
    ),
]

LAYERS = [
    (
        "01",
        "Grid + power",
        "The site begins at the interconnection, not the rack. Generation, transmission, "
        "substations, and backup set how much electricity can actually arrive, and a headline "
        "megawatt may mean contracted, permitted, energized, or already on the servers — four "
        "different states of the same number.",
    ),
    (
        "02",
        "Facility",
        "A campus is yards, plants, and halls that open in phases. Almost every watt that "
        "reaches a chip becomes heat, so cooling — not floor area — decides how densely racks "
        "can sit and whether they can hold rated load. Commissioning is the step that turns "
        "a finished shell into usable capacity.",
    ),
    (
        "03",
        "Chips",
        "Inside the tray the GPU does the parallel math; the host CPU does the sequential "
        "work around it — tools, code, browsers, orchestration. An agent can cross that "
        "boundary many times in one task. Token claims need a denominator (watt, dollar, "
        "user, factory); public agent-workflow benchmarks are still thin.",
    ),
    (
        "04",
        "Rack",
        "The competitive unit is no longer a lone accelerator. A modern AI cabinet carries "
        "CPUs, GPUs and HBM, the scale-up fabric, local storage, power shelves, and liquid "
        "loops. Multiplying a chip price by seventy-two misses most of the bill of materials.",
    ),
    (
        "05",
        "Cluster",
        "Racks become a cluster only when the scale-out fabric, shared storage, and "
        "scheduler are commissioned and jobs stay up. Ordered, delivered, installed, "
        "networked, and operational are different counts. H100-equivalent figures are a "
        "modeled scale, not a parts inventory.",
    ),
    (
        "06",
        "Virtual machine",
        "Cloud customers meet the stack as a named instance, billed by time. The meter "
        "usually bundles accelerators, host cores, memory, local disk, and network, so two "
        "hourly rates for the same GPU can describe very different machines, regions, and offers.",
    ),
    (
        "07",
        "Workload",
        "A benchmark is a job with a model, a dataset, and a quality target held fixed. "
        "Training time-to-target and inference tokens-per-second describe the whole system — "
        "chips, fabric, storage, and software — under one release of the rules. MLPerf is "
        "the public tape this desk points at; it is not a universal speed score.",
    ),
    (
        "08",
        "Economics",
        "Cash goes out as capex before the hall earns. Purchase commitments become property "
        "and equipment, then depreciation. Return depends on when capacity is energized, "
        "how fully it is used, and what the meter or the token actually clears — not on "
        "nameplate megawatts alone.",
    ),
]


def layer_html(num, title, text):
    return (
        f'<article class="layer" id="l{num}">\n'
        f'  <div class="n">{num}</div>\n'
        f"  <div>\n"
        f"    <h2>{title}</h2>\n"
        f"    <p>{text}</p>\n"
        f"  </div>\n"
        f"</article>"
    )


def fact_html(title, text, source):
    return (
        f'<article class="fact">\n'
        f"  <h3>{title}</h3>\n"
        f"  <p>{text}</p>\n"
        f'  <p class="src">Attributed · {source}</p>\n'
        f"</article>"
    )


layers_block = "\n".join(layer_html(*row) for row in LAYERS)
facts_block = "\n".join(fact_html(*row) for row in PAGE_FACTS)
toc = "".join(
    f'<li><a href="#l{num}">{num} {title}</a></li>' for num, title, _ in LAYERS
)
nice_upd = nice_day(PAGE_ASOF)
nice_short = nice_day(PAGE_ASOF, "short")
mts_snap = nice_day(MTS_SNAPSHOT, "short")

ld = json.dumps(
    {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "The physical stack behind AI",
        "datePublished": PAGE_ASOF,
        "dateModified": PAGE_ASOF,
        "description": (
            "Clerk-voice outline of the physical stack behind AI: land to shell to power "
            "to cooling to compute, then eight layers from grid to economics. Framing "
            "credited to MTS Intelligence; figures attributed."
        ),
        "url": f"{SITE}/physical-stack.html",
        "author": person_author(),
        "publisher": org_publisher(),
        "isAccessibleForFree": True,
        "citation": [MTS_CITE, CW_CITE],
        "creditText": MTS_CITE,
    },
    ensure_ascii=False,
)
crumb = json.dumps(
    breadcrumb_ld(
        [
            ("compute.world", f"{SITE}/"),
            ("Physical stack", f"{SITE}/physical-stack.html"),
        ]
    ),
    ensure_ascii=False,
)

PAGE = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#F3F5F2">
<script>(function(){{try{{var t=localStorage.getItem("cnw_theme");if(t!=="dark"&&t!=="light"){{var h=new Date().getHours();t=(h>=19||h<7)?"dark":"light";}}document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();</script>
<title>The physical stack behind AI · compute.world</title>
<meta name="description" content="The physical stack behind AI, in the desk's clerk voice: land → shell → power → cooling → compute, then eight layers from grid to economics. Framing credited to MTS Intelligence.">
<link rel="canonical" href="{SITE}/physical-stack.html">
<meta name="robots" content="index,follow,max-image-preview:large">
{og_block(
    "The physical stack behind AI · compute.world",
    "Eight layers from grid to economics. Framing credited to MTS Intelligence. Clerk voice, attributed counts only.",
    f"{SITE}/physical-stack.html",
    "og.png",
    og_type="article",
    image_alt="The physical stack behind AI — compute.world, credited to MTS Intelligence",
)}
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
.wrap{{max-width:920px;margin:0 auto;padding:0 28px}}
.masthead{{padding:34px 0 0;text-align:center}}
.masthead .name{{font-size:15px;letter-spacing:.34em;text-transform:uppercase;font-family:var(--sans)}}
.masthead .name a{{border:none;color:var(--ink)}}
.masthead .name b{{font-weight:600}}
.masthead .sub{{margin-top:8px;font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);font-family:var(--sans)}}
.mastrule{{margin-top:20px;border-top:2px solid var(--rule2);border-bottom:1px solid var(--rule2);height:5px}}
.lede{{padding:48px 0 8px}}
h1{{font-weight:400;font-size:clamp(28px,4.4vw,40px);line-height:1.16}}
h1 em{{font-style:italic}}
.standfirst{{margin-top:18px;font-size:17.5px;color:var(--muted)}}
.standfirst b{{color:var(--ink);font-weight:600}}
.subrow{{display:flex;flex-wrap:wrap;gap:8px 26px;align-items:baseline;margin:26px 0 0;padding:16px 0;border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule);font-size:13px;letter-spacing:.1em;text-transform:uppercase;font-family:var(--sans)}}
.subrow .lab{{color:var(--faint);font-size:11px;letter-spacing:.16em}}
.citebox{{margin:28px 0 8px;padding:18px 20px;border:1px solid var(--rule2);background:var(--tint);border-radius:8px}}
.citebox .k{{font-family:var(--sans);font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}}
.citebox blockquote{{margin:0;font-size:16px;line-height:1.5;color:var(--ink)}}
.citebox .upstream{{margin-top:12px;font-size:14.5px;color:var(--muted)}}
.citebox .api{{margin-top:8px;font-size:13.5px;color:var(--muted);font-family:var(--sans)}}
.toc{{margin:28px 0 8px}}
.toc .lab{{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:10px;font-family:var(--sans)}}
.toc ol{{margin:0 0 0 18px;color:var(--muted);font-size:15.5px}}
.toc li{{margin:0 0 7px}}
.seq{{margin:32px 0 8px;padding:16px 18px;border:1px dashed var(--rule);border-radius:8px;font-family:var(--sans);font-size:13.5px;letter-spacing:.04em;text-transform:uppercase;color:var(--ink)}}
.seq span{{color:var(--faint)}}
.facts{{margin:36px 0 8px;display:grid;grid-template-columns:1fr 1fr;gap:0 28px}}
.facts .lab{{grid-column:1/-1;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:4px;font-family:var(--sans)}}
.fact{{padding:16px 0;border-top:1px solid var(--rule)}}
.fact h3{{font-weight:400;font-size:18px;line-height:1.28;margin:0 0 8px}}
.fact p{{color:var(--muted);font-size:15px;margin:0}}
.fact .src{{margin-top:8px;font-size:12px;letter-spacing:.08em;text-transform:uppercase;font-family:var(--sans);color:var(--faint)}}
.layer{{display:grid;grid-template-columns:52px 1fr;gap:16px;margin:36px 0 0;padding-top:22px;border-top:1px solid var(--rule)}}
.layer .n{{font-family:var(--sans);font-size:13px;letter-spacing:.14em;color:var(--faint);padding-top:6px}}
.layer h2{{font-weight:400;font-size:22px;line-height:1.28;margin:0 0 10px}}
.layer p{{color:var(--muted);font-size:16.5px;margin:0}}
.notes{{margin:48px 0 0;border-top:2px solid var(--rule2);padding-top:22px}}
.notes h2{{font-weight:400;font-size:13px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:0 0 14px;font-family:var(--sans)}}
.notes p{{color:var(--muted);font-size:15px;margin:0 0 12px}}
.notes ul{{margin:0 0 12px 18px;color:var(--muted);font-size:15px}}
.notes li{{margin:0 0 6px}}
.colophon{{margin-top:56px;border-top:2px solid var(--rule2);padding:24px 0 56px;text-align:center}}
.colophon .c1{{font-size:12px;letter-spacing:.3em;text-transform:uppercase;font-family:var(--sans)}}
.colophon .c2{{margin-top:10px;font-size:12.5px;color:var(--muted)}}
@media(max-width:760px){{
  .wrap{{padding:0 18px}}.lede{{padding:36px 0 8px}}
  .facts{{grid-template-columns:1fr}}
  .layer{{grid-template-columns:36px 1fr;gap:10px}}
  .layer h2{{font-size:20px}}
}}
</style>
</head>
<body class="fnav-inner">
<button id="themetog" class="tchip" aria-label="Switch to night mode" title="Day / Night">
  <svg class="ic-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>
  <svg class="ic-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.9 1.9M19.1 4.9l-1.8 1.8M6.7 17.3l-1.9 1.9"/></svg>
</button>
{fnav_markup("stack")}
<div class="wrap">
  <div class="masthead">
    <div class="name"><a href="/"><b>COMPUTE</b>.WORLD</a></div>
    <div class="sub">Physical stack · credited outline · the world's compute &amp; silicon index · {nice_upd}</div>
    <div class="mastrule"></div>
  </div>

  <div class="lede">
    <h1>The physical stack <em>behind AI</em>.</h1>
    <p class="standfirst">An AI factory is a site that turns land, a shell, power, and cooling into compute. Jensen Huang's five-layer cake — energy, chips, infrastructure, models, applications — is the wider economy; this page stays inside the building. The eight layers below are this desk's wording. The framing is <b>MTS Intelligence's</b>. Their record, charts, and company tables live on their page. We do not reprint them.</p>
    <div class="subrow">
      <span class="lab">Outline</span>
      <span>{nice_short}</span>
      <a href="{MTS_PAGE}">MTS record</a>
      <a href="{MTS_API}">MTS /api/compute</a>
      <a href="/campuses.html">Campuses globe</a>
      <a href="/data-centers.html">Data centers FAQ</a>
      <a href="/contact.html">The Desk</a>
    </div>
  </div>

  <aside class="citebox" id="cite" aria-labelledby="cite-h">
    <div class="k" id="cite-h">Cite · required, visible</div>
    <blockquote>
      MTS Intelligence (2026). The Physical Stack Behind AI: an attributed record of AI compute. MTS Atlas, snapshot 2026-08-25. <a href="{MTS_PAGE}">{MTS_PAGE}</a>
    </blockquote>
    <p class="upstream">Upstream, as MTS credits them: <a href="https://epoch.ai/data/ai-data-centers">Epoch AI, AI Data Centers</a> and <a href="https://epoch.ai/data/gpu-clusters">GPU Clusters</a> (CC BY); <a href="https://github.com/mlcommons/training_results_v6.0">MLCommons MLPerf</a>; NVIDIA product documentation; official <a href="https://prices.azure.com/api/retail/prices">Azure</a> and <a href="https://cloud.google.com/billing/docs/apis">Google Cloud</a> catalogs; <a href="https://data.sec.gov/api/xbrl/companyfacts/">SEC EDGAR</a>.</p>
    <p class="api">Machine-readable snapshot: <a href="{MTS_API}">{MTS_API}</a> · snapshot_id compute-2026-08-25 · this desk last checked {nice_short}.</p>
  </aside>

  <p class="seq">Build order <span>·</span> land <span>→</span> shell <span>→</span> power <span>→</span> cooling <span>→</span> compute</p>

  <nav class="toc" aria-label="Layers">
    <div class="lab">The eight layers</div>
    <ol>{toc}</ol>
  </nav>

{layers_block}

  <section class="facts" id="record" aria-labelledby="facts-h">
    <div class="lab" id="facts-h">Attributed headlines · MTS snapshot {mts_snap}</div>
{facts_block}
  </section>

  <section class="notes" id="notes" aria-labelledby="notes-h">
    <h2 id="notes-h">How this page sits on the desk</h2>
    <p>This is a credited outline, not a scrape. Prose here is compute.world's. Counts and the H100 spread are marked attributed because we checked them against the MTS page or <code>/api/compute</code>. We do not invent megawatts or dollars, and we do not copy their figures, glyphs, or charts.</p>
    <p>Country conversion, silicon prints, and named campuses stay on this desk's own tapes. Campus slogans have a clerk's book at the <a href="/data-centers.html">Data centers FAQ</a>. Pins sit on <a href="/campuses.html">Campuses</a>.</p>
    <ul>
      <li>This page: <code>{CW_CITE}</code></li>
      <li>The record: <code>{MTS_CITE}</code></li>
    </ul>
    <p>A wrong attribution: <a href="/contact.html">The Desk</a>.</p>
  </section>

  <div class="colophon">
    <div class="c1">COMPUTE.WORLD</div>
    <div class="c2">Physical stack · credited to MTS Intelligence · {nice_upd} · the world's compute &amp; silicon index · CNW™ · GDC™ · &copy; 2026 Pukar C. Hamal · San Francisco, CA</div>
  </div>
</div>
<script>
var tm=document.querySelector('meta[name="theme-color"]'), tg=document.getElementById("themetog");
function cur(){{return document.documentElement.getAttribute("data-theme")==="dark"?"dark":"light"}}
function setT(t,sv){{document.documentElement.setAttribute("data-theme",t);
if(sv){{try{{localStorage.setItem("cnw_theme",t)}}catch(e){{}}}}
tm.content=t==="dark"?"#0F1216":"#F3F5F2";tg.setAttribute("aria-label",t==="dark"?"Switch to day mode":"Switch to night mode");}}
tg.onclick=function(){{setT(cur()==="dark"?"light":"dark",true)}};
setT(cur(),false);
{fnav_script("stack")}
</script>
</body>
</html>'''

open(os.path.join(ROOT, "physical-stack.html"), "w").write(PAGE)
print(
    f"physical-stack.html generated: 8 layers, "
    f"{API_COUNTS['facilities']} facilities / {API_COUNTS['gpu_clusters']} clusters "
    f"(MTS snapshot {MTS_SNAPSHOT})"
)
