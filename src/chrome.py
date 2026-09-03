#!/usr/bin/env python3
# Shared masthead, footer, and visual system for Phase 1 surfaces.
# Editorial reference. Boldness lives on the country certificate only.
from seo import og_block, nice_day

SITE = "https://compute.world"

NAV = (
    ("Index", "/#index", "index"),
    ("Movers", "/#movers", "movers"),
    ("Markets", "/silicon.html", "markets"),
    ("Thesis", "/thesis", "thesis"),
    ("Data", "/data", "data"),
    ("Desk", "/contact.html", "desk"),
)

MARKETS = (
    ("Silicon Tape", "/silicon.html"),
    ("Inference", "/inference.html"),
    ("Neoclouds", "/neoclouds.html"),
    ("Hyperscalers", "/hyperscalers.html"),
    ("Wire", "/wire.html"),
    ("Brief", "/brief"),
)


def css():
    return """
:root{
  --paper:#f7f4ee;--ink:#171614;--rule:#d9d4ca;--muted:#6b675f;--est:#8e8a82;
  --up:#2e6b4f;--stall:#7a1f2b;
  --sg:#2f4a6d;--pr:#2e6b4f;--in:#5a5752;--eu:#9a6b1c;--lr:#a89a7f;
  --serif:Charter,Georgia,"Iowan Old Style",serif;
  --sans:Inter,"Source Sans 3","Segoe UI",system-ui,sans-serif;
  --max:1120px;--radius:4px;
}
*{margin:0;padding:0;box-sizing:border-box}
html{background:var(--paper)}
body{background:var(--paper);color:var(--ink);font-family:var(--serif);
  font-size:18px;line-height:1.5;-webkit-font-smoothing:antialiased}
a{color:var(--stall);text-decoration:none;border-bottom:1px solid var(--rule)}
a:hover{border-bottom-color:var(--ink)}
.wrap{max-width:var(--max);margin:0 auto;padding:0 28px}
.tnum,.ix td,.ix th,.cert .num,.money,.rk{font-family:var(--sans);
  font-variant-numeric:lining-nums tabular-nums}
.est{color:var(--est)}
.dash{color:var(--muted)}

/* type scale */
.display{font-size:56px;line-height:1.15;font-weight:400;letter-spacing:-0.02em}
h1{font-size:40px;line-height:1.15;font-weight:400}
h2{font-size:28px;line-height:1.2;font-weight:400}
h3{font-size:20px;line-height:1.3;font-weight:400}
.small{font-size:15px}.micro{font-size:13px;color:var(--muted)}
.prose{max-width:72ch}
.prose p{margin:0 0 1em}

/* masthead */
.mast{padding:22px 0 0}
.mast-top{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:10px 24px}
.wordmark{font-size:15px;letter-spacing:.28em;border:none;color:var(--ink);font-weight:600}
.wordmark:hover{border:none}
.mast-meta{font-family:var(--sans);font-size:13px;color:var(--muted)}
.mast-sub{margin-top:6px;font-size:15px;color:var(--muted)}
.mast-rule{margin-top:16px;border-top:1px solid var(--ink);border-bottom:1px solid var(--rule);height:4px}
.nav{display:flex;flex-wrap:wrap;gap:4px 18px;align-items:center;margin-top:12px;font-family:var(--sans);font-size:15px}
.nav a{border:none;color:var(--ink)}
.nav a:hover{color:var(--stall)}
.nav a.here{border-bottom:1px solid var(--ink)}
.nav .drop{position:relative}
.nav .drop summary{list-style:none;cursor:pointer}
.nav .drop summary::-webkit-details-marker{display:none}
.nav .drop-list{position:absolute;top:120%;left:0;background:var(--paper);border:1px solid var(--rule);
  border-radius:var(--radius);padding:8px 0;min-width:160px;z-index:8}
.nav .drop-list a{display:block;padding:6px 14px;white-space:nowrap}

/* footer */
.foot{margin-top:72px;border-top:1px solid var(--ink);padding:28px 0 56px}
.foot-links{display:flex;flex-wrap:wrap;gap:8px 22px;font-family:var(--sans);font-size:15px}
.foot-links a{border:none;color:var(--ink)}
.foot-links a:hover{color:var(--stall)}
.cite{margin-top:16px;font-size:15px;color:var(--muted)}
.cite code{font-family:var(--sans);font-size:14px;color:var(--ink)}
.tm{margin-top:14px;font-size:13px;color:var(--muted);max-width:72ch}

/* buttons / ctas — say what happens; no appended arrows */
.btn{display:inline-block;font-family:var(--sans);font-size:15px;padding:9px 14px;
  border:1px solid var(--ink);border-radius:var(--radius);background:var(--paper);color:var(--ink);
  cursor:pointer}
.btn:hover{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.btn-ink{background:var(--ink);color:var(--paper)}
.btn-ink:hover{background:var(--stall);border-color:var(--stall)}

/* certificate */
.cert{border:1px solid var(--rule);border-radius:var(--radius);padding:22px 24px 20px;
  background:var(--paper)}
.cert.settle{animation:settle .6s ease both}
@keyframes settle{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@media(prefers-reduced-motion:reduce){.cert.settle{animation:none}}
.cert-flag{font-size:28px;line-height:1}
.cert-name{font-size:28px;line-height:1.15;margin:6px 0 10px}
.seal{display:inline-flex;align-items:center;justify-content:center;min-width:28px;height:28px;
  padding:0 10px;border-radius:999px;color:#f7f4ee;font-family:var(--sans);font-size:12px}
.seal.sg{background:var(--sg)}.seal.pr{background:var(--pr)}.seal.in{background:var(--in)}
.seal.eu{background:var(--eu)}.seal.lr{background:var(--lr)}
.cert-serial{margin:10px 0 14px;font-family:var(--sans);font-size:15px}
.delta.up{color:var(--up)}.delta.down{color:var(--stall)}.delta.flat{color:var(--muted)}
.cert-nums{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;border-top:1px solid var(--rule);
  border-bottom:1px solid var(--rule);padding:14px 0;margin:4px 0 12px}
.cert-nums .v{font-size:22px;line-height:1.15}
.cert-nums .l{font-size:13px;color:var(--muted);margin-top:3px}
.cert-extra{display:flex;flex-wrap:wrap;gap:8px 22px;font-family:var(--sans);font-size:14px;margin-bottom:12px}
.coupon{display:flex;flex-wrap:wrap;gap:4px;margin:10px 0}
.coupon i{display:inline-block;font-family:var(--sans);font-style:normal;font-size:11px;
  border:1px solid var(--rule);border-radius:var(--radius);padding:3px 6px;color:var(--muted)}
.coupon i.on{border-color:var(--ink);color:var(--ink)}
.cert-verdict{font-size:15px;margin:8px 0 6px}
.cert-asof{font-size:13px;color:var(--muted)}

/* subscribe */
.sub{margin:48px 0 8px;padding:22px 0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);
  display:grid;grid-template-columns:minmax(0,1.2fr) minmax(220px,.9fr);gap:16px 32px;align-items:end}
.sub form{display:flex;flex-wrap:wrap;gap:8px}
.sub input[type=email]{flex:1 1 180px;min-width:0;font:inherit;font-size:16px;padding:10px 12px;
  border:1px solid var(--rule);background:var(--paper);color:var(--ink);border-radius:var(--radius)}
.sub .lists{display:flex;flex-wrap:wrap;gap:8px 14px;width:100%;font-size:14px;color:var(--muted)}
.sub .submsg{margin-top:8px;font-size:14px;min-height:1.3em}
.sub .submsg.err{color:var(--stall)}.sub .submsg.ok{color:var(--up)}

@media(max-width:768px){
  .wrap{padding:0 18px}
  .display{font-size:36px}
  h1{font-size:28px}
  h2{font-size:22px}
  body{font-size:17px}
  .cert-nums{grid-template-columns:1fr}
  .sub{grid-template-columns:1fr}
}
"""


def theme_boot():
    return """<script>(function(){try{var t=localStorage.getItem("cnw_theme");if(t!=="dark"&&t!=="light"){var h=new Date().getHours();t=(h>=19||h<7)?"dark":"light";}document.documentElement.setAttribute("data-theme",t);}catch(e){}})();</script>"""


def icon():
    return """<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' fill='%23f7f4ee'/><text x='32' y='44' font-family='Georgia,serif' font-size='36' fill='%23171614' text-anchor='middle'>W</text></svg>">"""


def head(title, description, url, image="og.png", extra=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#f7f4ee">
{theme_boot()}
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{url}">
<meta name="robots" content="index,follow,max-image-preview:large">
{og_block(title, description, url, image, image_alt=title)}
{icon()}
<link rel="license" href="/license">
{extra}
<style>{css()}</style>
</head>
"""


def masthead(as_of, current=""):
    day = nice_day(as_of) if as_of else ""
    links = []
    for label, href, key in NAV:
        if key == "markets":
            items = "".join(f'<a href="{h}">{lab}</a>' for lab, h in MARKETS)
            here = ' class="here"' if current == "markets" else ""
            links.append(
                f'<details class="drop"><summary{here}>Markets</summary>'
                f'<div class="drop-list">{items}</div></details>'
            )
        else:
            cls = ' class="here"' if current == key else ""
            cur = ' aria-current="page"' if current == key else ""
            links.append(f'<a href="{href}"{cls}{cur}>{label}</a>')
    return f"""<header class="mast wrap">
  <div class="mast-top">
    <a class="wordmark" href="/">COMPUTE.WORLD</a>
    <div class="mast-meta">{day}</div>
  </div>
  <div class="mast-sub">The Compute Net Worth Index</div>
  <div class="mast-rule"></div>
  <nav class="nav" aria-label="Primary">{"".join(links)}</nav>
</header>
"""


def footer():
    return """<footer class="foot wrap">
  <div class="foot-links">
    <a href="#cite">Cite as</a>
    <a href="/embed.html">Embed</a>
    <a href="/data">Data feeds</a>
    <a href="/license">License</a>
    <a href="/contact.html">Press and contact</a>
    <a href="/agents.html">For agents</a>
  </div>
  <p class="cite" id="cite">Cite as: <code>Hamal, P. (2026). The Compute Net Worth Index. compute.world.</code></p>
  <p class="tm">“Compute Net Worth”, “The Compute Net Worth Index” and “Gross Domestic Compute” (GDC) are trademarks of Pukar C. Hamal. The mark is asserted here and on the <a href="/license">license</a> page. Scores are proprietary; quoting with attribution is free for research and press.</p>
</footer>
"""


def subscribe_markup():
    return """<section class="sub wrap" id="subscribe" aria-label="Get the weekday brief">
  <div>
    <h2>Get the weekday brief</h2>
    <p class="small">Five sourced signals. Two minutes. Every weekday.</p>
    <p class="micro">Read it on the <a href="/brief">public brief</a>, or take the RSS. Companies write via <a href="/contact.html">the Desk</a>.</p>
  </div>
  <div>
    <form id="subform" action="/api/subscribe" method="post" novalidate>
      <input type="email" name="email" id="subemail" required autocomplete="email" placeholder="you@domain" aria-label="Email">
      <button class="btn btn-ink" type="submit">Get the weekday brief</button>
      <div class="lists">
        <label><input type="checkbox" name="lists" value="countries" checked> Countries</label>
        <label><input type="checkbox" name="lists" value="silicon" checked> Silicon</label>
        <label><input type="checkbox" name="lists" value="inference"> Inference</label>
        <label><input type="checkbox" name="lists" value="neoclouds"> Neoclouds</label>
        <label><input type="checkbox" name="lists" value="hyperscalers"> Hyperscalers</label>
      </div>
    </form>
    <p class="micro">RSS: <a href="/brief.xml">brief</a>, <a href="/silicon.xml">silicon</a>, <a href="/wire.xml">wire</a></p>
    <p class="submsg" id="submsg" role="status" aria-live="polite"></p>
  </div>
</section>
"""


def subscribe_script():
    from subscribe import script
    return script()


def coupon_html(parts):
    bits = []
    for lab, val in parts:
        on = " on" if val >= 0.65 else ""
        pct = f"{round(val * 100)}"
        bits.append(f"<i class='{on}' title='{lab}: {pct}%'>{lab} {pct}</i>")
    return "<div class='coupon'>" + "".join(bits) + "</div>"


def delta_html(delta):
    from cnw_lib import delta_mark
    mark = delta_mark(delta)
    if mark is None:
        return ""
    kind, glyph, n = mark
    if kind == "flat":
        return f'<span class="delta flat" title="Unchanged week on week">{glyph}</span>'
    signed = f"+{n}" if n > 0 else str(n)
    title = f"{signed} vs last week"
    return f'<span class="delta {kind}" title="{title}">{glyph} {abs(n)}</span>'


def cert_html(c, settle=False, flag_html=None):
    from cnw_lib import (
        LABEL_CEILING, LABEL_GDC, LABEL_UNLOCK, TIER_CLASS,
        fmt_mult, fmt_rank_serial, money_b, money_pc, nice_day, readiness_parts,
    )
    cls = TIER_CLASS.get(c["tier"], "lr")
    flag = flag_html if flag_html is not None else f'<span class="cert-flag" aria-hidden="true">{c.get("femoji") or ""}</span>'
    gdc = money_b(c.get("cnw_gdc_B"))
    gdc_cls = "est" if c.get("lgE") and c.get("cnw_gdc_B") else ""
    settle_cls = " settle" if settle else ""
    return f"""<article class="cert{settle_cls}" data-slug="{c.get("slug","")}">
  {flag}
  <div class="cert-name">{c["name"]}</div>
  <span class="seal {cls}">{c["tier"]}</span>
  <div class="cert-serial tnum">{fmt_rank_serial(c.get("rank"))} {delta_html(c.get("rank_delta"))}</div>
  <div class="cert-nums">
    <div><div class="v tnum">{money_b(c.get("cnw_ceiling_hi_B"))}</div><div class="l">{LABEL_CEILING}</div></div>
    <div><div class="v tnum">{money_b(c.get("cnw_unlockable_B"))}</div><div class="l">{LABEL_UNLOCK}</div></div>
    <div><div class="v tnum {gdc_cls}">{gdc}{" <span class='micro'>est.</span>" if gdc_cls else ""}</div><div class="l">{LABEL_GDC}</div></div>
  </div>
  <div class="cert-extra">
    <span>Ceiling × GDP <b class="tnum">{fmt_mult(c.get("gdp_multiple"))}</b></span>
    <span>Bankable per person <b class="tnum">{money_pc(c.get("unlock_pc"))}</b></span>
  </div>
  {coupon_html(readiness_parts(c))}
  <p class="cert-verdict">{c.get("verdict") or ""}</p>
  <p class="cert-asof">As of {nice_day(c.get("as_of"))}</p>
</article>"""
