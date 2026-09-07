#!/usr/bin/env python3
"""Shared v1.5 desk chrome: masthead, footer, head tags, share dock, citations.

Homepage and profile pages use this. Market pages (wire, silicon tape,
campuses, …) import the same masthead through fnav.py so More still
reaches every existing surface.
"""
from html import escape as esc

SITE = "https://compute.world"
TAGLINE = "Countries. Compute."
CITE_HOUSE = "compute.world · Compute Net Worth Index"

NAV = [
    ("Countries", "#board", "countries", ""),
    ("Silicon prices", "#board", "silicon", ""),
    ("Trends", "#trends", None, ""),
    ("Projects", "#projects", None, ""),
    ("Method", "#method", None, "mid"),
    ("Country profiles", "#profiles", None, "mid"),
    ("Data", "#data", None, "mid"),
    ("Contact Us", "/contact.html", None, "cta"),
]

MORE = [
    (f"{SITE}/wire.html", "Signals", "The Wire: credibility-scored feed"),
    (f"{SITE}/neoclouds.html", "GPU clouds", "Who rents GPUs, by region"),
    (f"{SITE}/hyperscalers.html", "Hyperscalers", "271 cloud locations"),
    (f"{SITE}/inference.html", "Inference providers", "Who sells tokens"),
    (f"{SITE}/data-centers.html", "Data centers", "Power, water, land, tax, jobs"),
    (f"{SITE}/campuses.html", "Campuses", "Named sites on a globe"),
    (f"{SITE}/agents.html", "For agents", "Machine-readable edition"),
    (f"{SITE}/brief.html", "The brief", "Weekday public tape"),
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


def cite_line(work, url, as_of):
    """Copy-citation: work + house style + URL + as-of date."""
    dated = fmt_date(as_of)
    return (
        f"Hamal, P. (2026). {work}. {CITE_HOUSE}. {url} "
        f"As of {dated}."
    )


def citation_meta(title, url, as_of):
    dated = str(as_of or "2026")[:10]
    year = dated[:4] if dated else "2026"
    return (
        f'<meta name="citation_title" content="{esc(title)}">\n'
        f'<meta name="citation_author" content="Pukar C. Hamal">\n'
        f'<meta name="citation_publication_date" content="{esc(year)}">\n'
        f'<meta name="citation_publisher" content="compute.world">\n'
        f'<meta name="citation_online_date" content="{esc(dated)}">\n'
        f'<meta name="dc.creator" content="Pukar C. Hamal">\n'
        f'<meta name="dc.publisher" content="compute.world">\n'
        f'<meta name="dc.title" content="{esc(title)}">\n'
        f'<meta name="dc.identifier" content="{esc(url)}">\n'
        f'<meta name="dc.rights" content="CC BY 4.0">\n'
        f'<link rel="cite-as" href="{esc(url)}">'
    )


def icons(root):
    mark = f"{root}mark.svg"
    touch = f"{root}apple-touch-icon.png"
    return (
        f'<link rel="icon" href="{mark}" type="image/svg+xml">\n'
        f'<link rel="icon" href="{root}favicon-32.png" type="image/png" sizes="32x32">\n'
        f'<link rel="apple-touch-icon" href="{touch}">'
    )


def home_href(root, href):
    if href.startswith("http") or href.startswith("/") or href.endswith(".html"):
        return href
    return f"{root}index.html{href}" if root else f"/{href}" if href.startswith("#") else href


def brand_mark(root):
    return (
        f'<img class="mark" src="{root}mark.svg" width="28" height="28" alt="" '
        f'decoding="async">'
    )


def masthead(root, as_of, current=None, home="index.html"):
    brand_href = f"{root}{home}" if root or home != "/" else "/"
    if not root and home == "index.html":
        brand_href = "/"
    links = []
    for label, href, tab, kind in NAV:
        cls = []
        if current == label:
            cls.append("current")
        if kind:
            cls.append(kind)
        cattr = f' class="{" ".join(cls)}"' if cls else ""
        tab_attr = f' data-tab="{tab}"' if tab else ""
        links.append(f'<a href="{home_href(root, href)}"{tab_attr}{cattr}>{label}</a>')
    more = []
    for href, label, small in MORE:
        extra = f"<small>{esc(small)}</small>" if small else ""
        more.append(f'<a href="{esc(href)}">{esc(label)}{extra}</a>')
    dated = fmt_date(as_of)
    mark = brand_mark(root)
    extra_m = (
        f'<a href="{SITE}/wire.html">Signals</a>'
        f'<a href="{SITE}/neoclouds.html">GPU clouds</a>'
        f'<a href="{SITE}/data-centers.html">Data centers</a>'
        f'<a href="{SITE}/campuses.html">Campuses</a>'
        f'<a href="{SITE}/agents.html">For agents</a>'
    )
    nav_m = "".join(
        '<a href="%s"%s%s>%s</a>' % (
            home_href(root, href),
            (f" data-tab={tab!r}" if tab else ""),
            ' class="cta"' if kind == "cta" else "",
            label,
        )
        for label, href, tab, kind in NAV
    )
    return f'''<div class="chrome">
<header class="masthead"><div class="wrap">
  <a class="brand" href="{brand_href}">{mark}<b>compute.world</b><span>{TAGLINE}</span></a>
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
  {nav_m}
  {extra_m}
</div></nav>
</div>'''


def share_dock(label="Share this desk", url="", title="", citation=""):
    """Thumb-reach share/cite control. Mobile dock; desktop uses the same markup, restyled."""
    return f'''<div class="share-dock" role="region" aria-label="Share and cite" data-share-url="{esc(url)}" data-share-title="{esc(title)}" data-share-cite="{esc(citation)}">
  <button type="button" class="share-btn primary" data-share="native">{esc(label)}</button>
  <button type="button" class="share-btn" data-share="copy">Copy link</button>
  <button type="button" class="share-btn" data-share="cite">Cite</button>
</div>'''


def footer():
    return f'''<footer><div class="wrap"><div class="cols">
  <div><p class="tag">{TAGLINE} And the wires between them.</p><b>The Compute Net Worth Index</b>, version 1.5, created by Pukar C. Hamal and first published at compute.world on 10 August 2026. A public compute desk: weekday updates, sourced prints only. Country macros refresh from the IMF and World Bank. Compute Net Worth, The Compute Net Worth Index and Gross Domestic Compute are trademarks of Pukar C. Hamal. This site is an analytical framework and an invitation to argue with its inputs in public. It is not investment advice.</div>
  <div><b>Sources</b><br>NVIDIA earnings and keynotes, SemiAnalysis, Epoch AI, IEA, IMF WEO, World Bank, EIU, Transparency International, IHA, ESMAP, Cushman &amp; Wakefield, Rystad, Knight Frank, BNEF, and venue list pages fetched each snapshot. Flags: flag-icons (MIT). Vendor marks belong to their owners.</div>
  <div><b>Desk</b><br>San Francisco, CA<br><a href="{SITE}/contact.html">Contact Us</a><br><a href="{SITE}/agents.html">Agent edition</a><br><a href="{SITE}/llms.txt">llms.txt</a> · <a href="{SITE}/sitemap.xml">Sitemap</a></div>
</div></div></footer>'''


def tiny_js():
    return '''<script>
window.flagFail=function(i){var s=document.createElement("span");s.className="code";s.textContent=i.dataset.code||"";i.replaceWith(s)};
window.logoFail=function(i){i.parentElement.classList.add("fallback")};
document.addEventListener("click",function(e){var b=e.target.closest("[data-copy]");if(!b)return;var t=document.querySelector(b.dataset.copy).textContent.trim();navigator.clipboard.writeText(t).then(function(){var o=b.textContent;b.textContent="Copied";setTimeout(function(){b.textContent=o},1400)})});
(function(){
  var m=document.getElementById("menuBtn"), n=document.getElementById("mnav");
  function setOpen(o){ if(!n||!m)return; n.classList.toggle("open",o); m.setAttribute("aria-expanded",o); document.body.classList.toggle("nav-open",o); }
  if(m) m.addEventListener("click",function(){ setOpen(!n.classList.contains("open")); });
  document.addEventListener("click",function(e){
    if(e.target.closest(".mnav a")) setOpen(false);
    var more=document.querySelector("header.masthead .more, header.deskhead .more");
    if(more && more.open && !e.target.closest(".more")) more.removeAttribute("open");
  });
  function toast(msg){ var t=document.getElementById("toast"); if(!t){ t=document.createElement("div"); t.className="toast"; t.id="toast"; document.body.appendChild(t);} t.textContent=msg; t.classList.add("show"); setTimeout(function(){t.classList.remove("show")},1600); }
  function copyText(text, ok){ if(navigator.clipboard&&navigator.clipboard.writeText){ navigator.clipboard.writeText(text).then(function(){toast(ok||"Copied")}).catch(function(){toast("Copy failed")}); return; } var ta=document.createElement("textarea"); ta.value=text; document.body.appendChild(ta); ta.select(); try{document.execCommand("copy"); toast(ok||"Copied");}catch(e){toast("Copy failed");} ta.remove(); }
  document.addEventListener("click",function(e){
    var b=e.target.closest("[data-share]"); if(!b) return;
    var dock=b.closest(".share-dock")||document.querySelector(".share-dock");
    var url=(dock&&dock.dataset.shareUrl)||location.href;
    var title=(dock&&dock.dataset.shareTitle)||document.title;
    var cite=(dock&&dock.dataset.shareCite)||(title+" "+url);
    var act=b.getAttribute("data-share");
    if(act==="native"){
      if(navigator.share){ navigator.share({title:title,url:url,text:title}).catch(function(){}); }
      else copyText(url,"Link copied");
    } else if(act==="copy") copyText(url,"Link copied");
    else if(act==="cite") copyText(cite,"Citation copied");
  });
})();
</script>'''


def head(title, description, canonical, root, css, jsonld=None, og_type="website", image=None, as_of=""):
    css_out = css.replace("{{root}}", root)
    ld = f'<script type="application/ld+json">{jsonld}</script>\n' if jsonld else ""
    img = image or f"{SITE}/og.png"
    cite = citation_meta(title, canonical, as_of)
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#F3F5F2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0F1216" media="(prefers-color-scheme: dark)">
<meta name="author" content="Pukar C. Hamal">
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
{cite}
{icons(root)}
<link rel="alternate" type="application/rss+xml" title="compute.world brief" href="{SITE}/brief.xml">
<link rel="preload" href="{root}fonts/SchibstedGrotesk-wght.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{root}fonts/Newsreader-opsz-wght.woff2" as="font" type="font/woff2" crossorigin>
{ld}<style>{css_out}</style>
</head>'''


# v1.5 paper/ink/accent for market pages that still carry their own layout CSS.
MARKET_THEME_CSS = r"""
@font-face{font-family:"Schibsted Grotesk";src:url("/fonts/SchibstedGrotesk-wght.woff2") format("woff2");font-weight:400 900;font-style:normal;font-display:swap}
@font-face{font-family:"Newsreader";src:url("/fonts/Newsreader-opsz-wght.woff2") format("woff2");font-weight:200 800;font-style:normal;font-display:swap}
:root{--paper:#F3F5F2;--ink:#1B222A;--muted:#4E5862;--faint:#7C8690;--rule:#D8DED9;--rule2:#1B222A;
--accent:#1F4FD8;--tint:#F6F8F5;--pr:#1E7B4F;--sg:#8A5A12;--barbg:#E7ECE7;
--glass:rgba(243,245,242,.78);--glassborder:rgba(27,34,42,.22);
--serif:"Newsreader",Georgia,"Times New Roman",serif;
--sans:"Schibsted Grotesk",ui-sans-serif,system-ui,sans-serif}
html[data-theme="dark"]{--paper:#0F1216;--ink:#E9EDF1;--muted:#AAB4BE;--faint:#7E8893;--rule:#2A323B;
--rule2:#E9EDF1;--accent:#6C8FF0;--tint:#1B2129;--pr:#4FBF86;--sg:#E0B060;--barbg:#222931;
--glass:rgba(15,18,22,.78);--glassborder:rgba(233,237,241,.22)}
"""

# Compact chrome for market pages that already have their own body styles.
# Scoped under header.deskhead so silicon.html .masthead (page title) is untouched.
DESKHEAD_CSS = r"""
@font-face{font-family:"Schibsted Grotesk";src:url("/fonts/SchibstedGrotesk-wght.woff2") format("woff2");font-weight:400 900;font-style:normal;font-display:swap}
@font-face{font-family:"Newsreader";src:url("/fonts/Newsreader-opsz-wght.woff2") format("woff2");font-weight:200 800;font-style:normal;font-display:swap}
.chrome{position:sticky;top:0;z-index:80;padding-top:env(safe-area-inset-top,0px);background:color-mix(in srgb,#F3F5F2 88%,transparent);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px)}
@supports not (background:color-mix(in srgb,red 50%,blue)){.chrome{background:#F3F5F2}}
header.deskhead{--paper:#F3F5F2;--panel:#FFFFFF;--panel-2:#F6F8F5;--ink:#1B222A;--ink-2:#4E5862;--ink-3:#7C8690;--line:#D8DED9;--line-2:#E7ECE7;--accent:#1F4FD8;--up:#1E7B4F;--sans:"Schibsted Grotesk",ui-sans-serif,system-ui,sans-serif;--serif:"Newsreader",Georgia,serif;--r-md:8px;--shadow:0 1px 2px rgba(27,34,42,.04),0 8px 24px rgba(27,34,42,.05);
position:relative;top:auto;z-index:80;background:transparent;border-bottom:1px solid #D8DED9;color:#1B222A;font-family:var(--sans)}
header.deskhead .wrap{max-width:1240px;margin:0 auto;padding:0 24px;display:flex;align-items:center;gap:18px;height:60px}
header.deskhead .brand{display:flex;align-items:center;gap:10px;color:#1B222A;white-space:nowrap;text-decoration:none;border:none}
header.deskhead .brand .mark{width:28px;height:28px;border-radius:7px;flex:none;display:block}
header.deskhead .brand b{font-weight:700;font-size:18px;letter-spacing:-.02em}
header.deskhead .brand span{font-family:var(--serif);font-size:15px;color:#4E5862}
header.deskhead .nav{display:flex;gap:14px;align-items:center}
header.deskhead .nav a{color:#4E5862;font-size:14.5px;font-weight:500;white-space:nowrap;padding:6px 0;border:none;text-decoration:none}
header.deskhead .nav a:hover{color:#1B222A}
header.deskhead .nav a.current{color:#1B222A;box-shadow:inset 0 -2px 0 #1B222A}
header.deskhead .nav a.cta{color:#1F4FD8;font-weight:600}
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
nav.desk-mnav.open{display:block;max-height:calc(100dvh - 60px - env(safe-area-inset-top,0px));overflow:auto;padding-bottom:env(safe-area-inset-bottom,0px)}
nav.desk-mnav .wrap{max-width:1240px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:2px 20px;padding:10px 24px 16px}
nav.desk-mnav a{padding:12px 0;min-height:44px;display:flex;align-items:center;color:#1B222A;font-weight:500;border-bottom:1px solid #E7ECE7;font-size:15px;text-decoration:none;border-top:none;border-left:none;border-right:none}
nav.desk-mnav a.cta{color:#1F4FD8;font-weight:600}
nav.desk-mnav .asof-m{grid-column:1/-1;font-size:14px;color:#4E5862;padding:8px 0 6px}
body.nav-open{overflow:hidden}
@media(max-width:1180px){
  header.deskhead .nav a.mid{display:none}
}
@media(max-width:1100px){
  header.deskhead .nav,header.deskhead .asof{display:none}
  header.deskhead .menu-btn{display:inline-flex;margin-left:auto}
}
@media(max-width:860px){
  header.deskhead .brand span{display:none}
}
html{scroll-padding-top:calc(72px + env(safe-area-inset-top,0px))}
body.fnav-inner{padding-top:0}
.share-dock{position:fixed;left:0;right:0;bottom:0;z-index:70;display:none;gap:8px;padding:10px 16px calc(10px + env(safe-area-inset-bottom,0px));background:color-mix(in srgb,#F3F5F2 92%,transparent);backdrop-filter:blur(10px);border-top:1px solid #D8DED9;font-family:"Schibsted Grotesk",ui-sans-serif,system-ui,sans-serif}
.share-dock .share-btn{flex:1;min-height:48px;border:1px solid #D8DED9;border-radius:10px;background:#fff;color:#1B222A;font:inherit;font-weight:600;font-size:15px;cursor:pointer}
.share-dock .share-btn.primary{background:#1F4FD8;color:#fff;border-color:#1F4FD8}
@media(max-width:860px){.share-dock{display:flex}body{padding-bottom:calc(72px + env(safe-area-inset-bottom,0px))}}
@media(prefers-color-scheme:dark){
  .chrome{background:color-mix(in srgb,#0F1216 88%,transparent)}
  header.deskhead{border-bottom-color:#2A323B;color:#E9EDF1}
  header.deskhead .brand,header.deskhead .nav a.current,header.deskhead .asof b{color:#E9EDF1}
  header.deskhead .brand span,header.deskhead .nav a,header.deskhead .asof{color:#AAB4BE}
  header.deskhead .nav a.cta,nav.desk-mnav a.cta{color:#6C8FF0}
  header.deskhead .menu-btn{background:#151A20;border-color:#2A323B;color:#E9EDF1}
  header.deskhead .more .menu{background:#151A20;border-color:#2A323B}
  header.deskhead .more .menu a{color:#E9EDF1}
  header.deskhead .more .menu a:hover{background:#1B2129}
  nav.desk-mnav{background:#151A20;border-bottom-color:#2A323B}
  nav.desk-mnav a{color:#E9EDF1;border-bottom-color:#222931}
  .share-dock{background:color-mix(in srgb,#0F1216 92%,transparent);border-top-color:#2A323B}
  .share-dock .share-btn{background:#151A20;border-color:#2A323B;color:#E9EDF1}
  .share-dock .share-btn.primary{background:#6C8FF0;border-color:#6C8FF0;color:#0F1216}
}
"""


SHARE_PAGES = {
    "index": (f"{SITE}/", "compute.world — Countries. Compute.", "The Compute Net Worth Index"),
    "silicon": (f"{SITE}/silicon.html", "The Silicon Tape — compute.world", "The Silicon Tape"),
    "brief": (f"{SITE}/brief.html", "The daily tape — compute.world", "The daily tape"),
    "wire": (f"{SITE}/wire.html", "The Wire — compute.world", "The Wire"),
    "inference": (f"{SITE}/inference.html", "The Inference Index — compute.world", "The Inference Index"),
    "neoclouds": (f"{SITE}/neoclouds.html", "The Neocloud Index — compute.world", "The Neocloud Index"),
    "hyperscalers": (f"{SITE}/hyperscalers.html", "The Hyperscaler Index — compute.world", "The Hyperscaler Index"),
    "datacenters": (f"{SITE}/data-centers.html", "Data centers FAQ — compute.world", "Data centers FAQ"),
    "campuses": (f"{SITE}/campuses.html", "Campuses — compute.world", "Campuses"),
    "contact": (f"{SITE}/contact.html", "The Desk — compute.world", "The Desk"),
    "agents": (f"{SITE}/agents.html", "Agent edition — compute.world", "Agent edition"),
}


def deskhead_markup(page, as_of):
    """Market-page masthead. `page` is the fnav page key."""
    current = {
        "index": "Countries",
        "silicon": "Silicon prices",
        "brief": None,
        "wire": None,
        "contact": "Contact Us",
    }.get(page)
    html = masthead("", as_of, current=current, home="/")
    html = html.replace('class="masthead"', 'class="deskhead"').replace('class="mnav"', 'class="desk-mnav"')
    share = SHARE_PAGES.get(page)
    if share:
        url, title, work = share
        html += share_dock("Share this desk", url, title, cite_line(work, url, as_of))
    return html


def deskhead_script():
    return """(function(){
  var m=document.getElementById("menuBtn"), n=document.getElementById("mnav");
  function setOpen(o){ if(!n||!m)return; n.classList.toggle("open",o); m.setAttribute("aria-expanded",o); document.body.classList.toggle("nav-open",o); }
  if(m) m.addEventListener("click",function(){ setOpen(!n.classList.contains("open")); });
  document.addEventListener("click",function(e){
    if(e.target.closest("nav.desk-mnav a")) setOpen(false);
    var more=document.querySelector("header.deskhead .more, header.masthead .more");
    if(more && more.open && !e.target.closest(".more")) more.removeAttribute("open");
  });
  function toast(msg){ var t=document.getElementById("toast"); if(!t){ t=document.createElement("div"); t.id="toast"; t.setAttribute("role","status"); t.style.cssText="position:fixed;left:50%;bottom:88px;transform:translateX(-50%);background:#1B222A;color:#F3F5F2;padding:10px 16px;border-radius:8px;font:500 14px Schibsted Grotesk,sans-serif;z-index:90;opacity:0;transition:opacity .15s"; document.body.appendChild(t);} t.textContent=msg; t.style.opacity="1"; setTimeout(function(){t.style.opacity="0"},1600); }
  function copyText(text, ok){ if(navigator.clipboard&&navigator.clipboard.writeText){ navigator.clipboard.writeText(text).then(function(){toast(ok||"Copied")}); return; } var ta=document.createElement("textarea"); ta.value=text; document.body.appendChild(ta); ta.select(); document.execCommand("copy"); ta.remove(); toast(ok||"Copied"); }
  document.addEventListener("click",function(e){
    var b=e.target.closest("[data-share]"); if(!b) return;
    var dock=b.closest(".share-dock")||document.querySelector(".share-dock");
    var url=(dock&&dock.dataset.shareUrl)||location.href.split("#")[0];
    var title=(dock&&dock.dataset.shareTitle)||document.title;
    var cite=(dock&&dock.dataset.shareCite)||(title+" — compute.world · Compute Net Worth Index. "+url);
    var act=b.getAttribute("data-share");
    if(act==="native"){ if(navigator.share){ navigator.share({title:title,url:url,text:title}).catch(function(){}); } else copyText(url,"Link copied"); }
    else if(act==="copy") copyText(url,"Link copied");
    else if(act==="cite") copyText(cite,"Citation copied");
  });
})();
"""
