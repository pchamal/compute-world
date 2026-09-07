#!/usr/bin/env python3
"""Shared v1.5 desk chrome: masthead, footer, head tags.

Homepage and profile pages use this. Market pages (wire, silicon tape,
campuses, …) import the same masthead through fnav.py so More still
reaches every existing surface.
"""
from html import escape as esc

SITE = "https://compute.world"

NAV = [
    ("Countries", "#board", "countries"),
    ("Silicon prices", "#board", "silicon"),
    ("Trends", "#trends", None),
    ("Projects", "#projects", None),
    ("Method", "#method", None),
    ("Country profiles", "#profiles", None),
    ("Data", "#data", None),
]

MORE = [
    (f"{SITE}/wire.html", "Signals", "The Wire: credibility-scored feed"),
    (f"{SITE}/neoclouds.html", "GPU clouds", "Who rents GPUs, by region"),
    (f"{SITE}/hyperscalers.html", "Hyperscalers", "271 cloud locations"),
    (f"{SITE}/inference.html", "Inference providers", "Who sells tokens"),
    (f"{SITE}/data-centers.html", "Data centers", "Power, water, land, tax, jobs"),
    (f"{SITE}/campuses.html", "Campuses", "Named sites on a globe"),
    (f"{SITE}/agents.html", "For agents", "Machine-readable edition"),
    (f"{SITE}/contact.html", "Contact the desk", ""),
]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_LONG = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def fmt_date(iso):
    if not iso:
        return ""
    s = str(iso)
    if s.endswith("-H2"):
        return f"2H {s[:4]}"
    p = s.split("-")
    if len(p) == 2 and p[1].isdigit():
        return f"{MONTHS[int(p[1]) - 1]} {p[0]}"
    if len(p) >= 3 and p[1].isdigit() and p[2].isdigit():
        return f"{int(p[2])} {MONTHS[int(p[1]) - 1]} {p[0]}"
    return iso


def fmt_date_long(iso):
    if not iso:
        return ""
    s = str(iso)
    if s.endswith("-H2"):
        return f"second half of {s[:4]}"
    p = s.split("-")
    if len(p) >= 3 and p[1].isdigit() and p[2].isdigit():
        return f"{int(p[2])} {MONTHS_LONG[int(p[1]) - 1]} {p[0]}"
    return fmt_date(iso)


def mon_year(iso):
    s = str(iso)
    if s.endswith("-H2"):
        return f"2H {s[:4]}"
    p = s.split("-")
    if len(p) >= 2 and p[1].isdigit():
        return f"{MONTHS[int(p[1]) - 1]} {p[0]}"
    return s


def home_href(root, href):
    if href.startswith("http") or href.endswith(".html"):
        return href
    return f"{root}index.html{href}" if root else f"/{href}" if href.startswith("#") else href


def masthead(root, as_of, current=None, home="index.html"):
    brand_href = f"{root}{home}" if root or home != "/" else "/"
    if not root and home == "index.html":
        brand_href = "/"
    links = []
    for label, href, tab in NAV:
        cls = ' class="current"' if current == label else ""
        tab_attr = f' data-tab="{tab}"' if tab else ""
        links.append(f'<a href="{home_href(root, href)}"{tab_attr}{cls}>{label}</a>')
    more = []
    for href, label, small in MORE:
        extra = f"<small>{esc(small)}</small>" if small else ""
        more.append(f'<a href="{esc(href)}">{esc(label)}{extra}</a>')
    dated = fmt_date(as_of)
    return f'''<header class="masthead"><div class="wrap">
  <a class="brand" href="{brand_href}"><b>compute.world</b><span>Countries. Compute. Silicon.</span></a>
  <nav class="nav" aria-label="Sections">{"".join(links)}
    <details class="more"><summary>More <svg width="10" height="6" viewBox="0 0 10 6" aria-hidden="true"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.5"/></svg></summary>
      <div class="menu">
        {"".join(more)}
      </div></details>
  </nav>
  <div class="asof"><span class="live" aria-hidden="true"></span>Updated <b>{esc(dated)}</b></div>
  <button class="menu-btn" id="menuBtn" aria-expanded="false" aria-controls="mnav">Menu <svg width="12" height="10" viewBox="0 0 12 10" aria-hidden="true"><path d="M0 1h12M0 5h12M0 9h12" stroke="currentColor" stroke-width="1.5"/></svg></button>
</div></header>
<nav class="mnav" id="mnav" aria-label="Sections"><div class="wrap">
  <div class="asof-m">Updated <b>{esc(dated)}</b></div>
  {"".join(f'<a href="{home_href(root, href)}"{(f" data-tab={tab!r}" if tab else "")}>{label}</a>' for label, href, tab in NAV)}
  <a href="{SITE}/wire.html">Signals</a><a href="{SITE}/neoclouds.html">GPU clouds</a><a href="{SITE}/data-centers.html">Data centers</a><a href="{SITE}/contact.html">Contact</a>
</div></nav>'''


def footer():
    return f'''<footer><div class="wrap"><div class="cols">
  <div><p class="tag">Countries. Compute. Silicon. And the wires between them.</p><b>The Compute Net Worth Index</b>, version 1.5, created by Pukar C. Hamal and first published at compute.world on 10 August 2026. A public compute desk: weekday updates, sourced prints only. Country macros refresh from the IMF and World Bank. Compute Net Worth, The Compute Net Worth Index and Gross Domestic Compute are trademarks of Pukar C. Hamal. This site is an analytical framework and an invitation to argue with its inputs in public. It is not investment advice.</div>
  <div><b>Sources</b><br>NVIDIA earnings and keynotes, SemiAnalysis, Epoch AI, IEA, IMF WEO, World Bank, EIU, Transparency International, IHA, ESMAP, Cushman &amp; Wakefield, Rystad, Knight Frank, BNEF, and venue list pages fetched each snapshot. Flags: flag-icons (MIT). Vendor marks belong to their owners.</div>
  <div><b>Desk</b><br>San Francisco, CA<br><a href="{SITE}/contact.html">Briefings, corrections, licensing</a><br><a href="{SITE}/agents.html">Agent edition</a><br><a href="{SITE}/llms.txt">llms.txt</a> · <a href="{SITE}/sitemap.xml">Sitemap</a></div>
</div></div></footer>'''


def tiny_js():
    return '''<script>window.flagFail=function(i){var s=document.createElement("span");s.className="code";s.textContent=i.dataset.code||"";i.replaceWith(s)};window.logoFail=function(i){i.parentElement.classList.add("fallback")};document.addEventListener("click",function(e){var b=e.target.closest("[data-copy]");if(!b)return;var t=document.querySelector(b.dataset.copy).textContent.trim();navigator.clipboard.writeText(t).then(function(){var o=b.textContent;b.textContent="Copied";setTimeout(function(){b.textContent=o},1400)})});var m=document.getElementById("menuBtn");if(m)m.addEventListener("click",function(){var n=document.getElementById("mnav");var o=!n.classList.contains("open");n.classList.toggle("open",o);m.setAttribute("aria-expanded",o)});</script>'''


def head(title, description, canonical, root, css, jsonld=None, og_type="website", image=None):
    css_out = css.replace("{{root}}", root)
    ld = f'<script type="application/ld+json">{jsonld}</script>\n' if jsonld else ""
    img = image or f"{SITE}/og.png"
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#F3F5F2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0F1216" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="compute.world">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(img)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{esc(img)}">
<link rel="alternate" type="application/rss+xml" title="compute.world brief" href="{SITE}/brief.xml">
<link rel="preload" href="{root}fonts/SchibstedGrotesk-wght.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{root}fonts/Newsreader-opsz-wght.woff2" as="font" type="font/woff2" crossorigin>
{ld}<style>{css_out}</style>
</head>'''


# Compact chrome for market pages that already have their own body styles.
# Scoped under header.deskhead so silicon.html .masthead (page title) is untouched.
DESKHEAD_CSS = r"""
@font-face{font-family:"Schibsted Grotesk";src:url("/fonts/SchibstedGrotesk-wght.woff2") format("woff2");font-weight:400 900;font-style:normal;font-display:swap}
@font-face{font-family:"Newsreader";src:url("/fonts/Newsreader-opsz-wght.woff2") format("woff2");font-weight:200 800;font-style:normal;font-display:swap}
header.deskhead{--paper:#F3F5F2;--panel:#FFFFFF;--panel-2:#F6F8F5;--ink:#1B222A;--ink-2:#4E5862;--ink-3:#7C8690;--line:#D8DED9;--line-2:#E7ECE7;--accent:#1F4FD8;--up:#1E7B4F;--sans:"Schibsted Grotesk",ui-sans-serif,system-ui,sans-serif;--serif:"Newsreader",Georgia,serif;--r-md:8px;--shadow:0 1px 2px rgba(27,34,42,.04),0 8px 24px rgba(27,34,42,.05);
position:sticky;top:0;z-index:80;background:color-mix(in srgb,#F3F5F2 88%,transparent);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border-bottom:1px solid #D8DED9;color:#1B222A;font-family:var(--sans)}
header.deskhead .wrap{max-width:1240px;margin:0 auto;padding:0 24px;display:flex;align-items:center;gap:24px;height:60px}
header.deskhead .brand{display:flex;align-items:baseline;gap:10px;color:#1B222A;white-space:nowrap;text-decoration:none;border:none}
header.deskhead .brand b{font-weight:700;font-size:18px;letter-spacing:-.02em}
header.deskhead .brand span{font-family:var(--serif);font-size:15px;color:#4E5862}
header.deskhead .nav{display:flex;gap:18px;align-items:center}
header.deskhead .nav a{color:#4E5862;font-size:14.5px;font-weight:500;white-space:nowrap;padding:6px 0;border:none;text-decoration:none}
header.deskhead .nav a:hover{color:#1B222A}
header.deskhead .nav a.current{color:#1B222A;box-shadow:inset 0 -2px 0 #1B222A}
header.deskhead .more{position:relative}
header.deskhead .more summary{list-style:none;cursor:pointer;color:#4E5862;font-size:14.5px;font-weight:500;padding:6px 0;display:flex;align-items:center;gap:5px}
header.deskhead .more summary::-webkit-details-marker{display:none}
header.deskhead .more .menu{position:absolute;top:calc(100% + 8px);right:0;background:#fff;border:1px solid #D8DED9;border-radius:8px;padding:6px;min-width:250px;box-shadow:var(--shadow);z-index:90}
header.deskhead .more .menu a{display:block;padding:9px 10px;border-radius:5px;color:#1B222A;font-size:14.5px;border:none}
header.deskhead .more .menu a:hover{background:#F6F8F5}
header.deskhead .more .menu small{display:block;color:#7C8690;font-size:12.5px}
header.deskhead .asof{margin-left:auto;font-size:14px;color:#4E5862;white-space:nowrap;display:flex;align-items:center;gap:8px}
header.deskhead .asof b{color:#1B222A;font-weight:600}
header.deskhead .live{width:7px;height:7px;border-radius:50%;background:#1E7B4F}
header.deskhead .menu-btn{display:none;align-items:center;gap:6px;border:1px solid #D8DED9;border-radius:8px;padding:7px 11px;font-size:14px;font-weight:500;background:#fff;color:#1B222A;cursor:pointer}
nav.desk-mnav{display:none;border-bottom:1px solid #D8DED9;background:#fff;font-family:"Schibsted Grotesk",ui-sans-serif,system-ui,sans-serif}
nav.desk-mnav.open{display:block}
nav.desk-mnav .wrap{max-width:1240px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:2px 20px;padding:10px 24px 16px}
nav.desk-mnav a{padding:11px 0;color:#1B222A;font-weight:500;border-bottom:1px solid #E7ECE7;font-size:15px;text-decoration:none;border-top:none;border-left:none;border-right:none}
nav.desk-mnav .asof-m{grid-column:1/-1;font-size:14px;color:#4E5862;padding:8px 0 6px}
@media(max-width:1100px){
  header.deskhead .nav,header.deskhead .asof{display:none}
  header.deskhead .menu-btn{display:inline-flex;margin-left:auto}
}
body.fnav-inner{padding-top:0}
"""


def deskhead_markup(page, as_of):
    """Market-page masthead. `page` is the fnav page key."""
    current = {
        "index": "Countries",
        "silicon": "Silicon prices",
        "brief": None,
        "wire": None,
    }.get(page)
    html = masthead("", as_of, current=current, home="/")
    return html.replace('class="masthead"', 'class="deskhead"').replace('class="mnav"', 'class="desk-mnav"').replace('id="mnav"', 'id="mnav"')


def deskhead_script():
    return """(function(){
  var m=document.getElementById("menuBtn");
  if(m) m.addEventListener("click",function(){
    var n=document.getElementById("mnav");
    var o=!n.classList.contains("open");
    n.classList.toggle("open",o);
    m.setAttribute("aria-expanded",o);
  });
  document.addEventListener("click",function(e){
    var more=document.querySelector("header.deskhead .more, header.masthead .more");
    if(more && more.open && !e.target.closest(".more")) more.removeAttribute("open");
  });
})();
"""
