# Shared floating nav for public compute.world pages (index, wire, silicon, contact, agents, data-centers, campuses).
# Builders import css/markup/script. contact.html inlines the same snippets by hand
# so a rebuild of generated pages cannot drop the bar on that page.
# embed.html is an embeddable widget — do not add this chrome there.
# The contact href stays labeled "Contact": the bar already wraps to a burger at 1520px;
# "Desk" would not uncrowd it. contact.html is The Desk; the URL is unchanged.

LINKS = (
    ("board", "Board", "#board"),
    ("index", "Index", "#index"),
    ("shape", "Charts", "#shape"),
    ("objections", "Objections", "#objections"),
    ("precedents", "Precedents", "#precedents"),
    ("gazetteer", "Gazetteer", "#gazetteer"),
    ("wire", "Wire", "/wire.html"),
    ("silicon", "Silicon", "#silicon"),  # homepage tab; inner pages become /#silicon
    ("inference", "Inference", "#inference"),
    ("neoclouds", "Neoclouds", "#neoclouds"),
    ("hyperscalers", "Hyperscalers", "#hyperscalers"),
    ("datacenters", "Data centers", "/data-centers.html"),
    ("campuses", "Campuses", "/campuses.html"),
    ("credit", "Cite", "#credit"),
    ("contact", "Contact", "/contact.html"),
    ("agents", "Agents", "/agents.html"),
)

# Homepage hashes for the three new indexes; dedicated pages on inner pages.
PAGE_HREF = {
    "inference": "/inference.html",
    "neoclouds": "/neoclouds.html",
    "hyperscalers": "/hyperscalers.html",
}

# Homepage section hashes stay in-page; inner pages point at the homepage anchors.
HOME_CURRENT = ("silicon",)  # Silicon is the home mark; JS marks Index when Countries is open
INNER = {
    "wire": "wire",
    "silicon": "silicon",
    "inference": "inference",
    "neoclouds": "neoclouds",
    "hyperscalers": "hyperscalers",
    "datacenters": "datacenters",
    "campuses": "campuses",
    "contact": "contact",
    "agents": "agents",
    "brief": "brief",
}


def is_home(page):
    return page == "index"


def current_keys(page):
    if is_home(page):
        return set(HOME_CURRENT)
    key = INNER.get(page)
    return {key} if key else set()


def href(dest, page):
    if dest.startswith("#") and not is_home(page):
        key = dest[1:]
        if key in PAGE_HREF:
            return PAGE_HREF[key]
        return "/" + dest
    return dest


def css():
    return """/* floating nav — shared via src/fnav.py */
body,#fnav{transition:background-color .35s ease,color .35s ease,border-color .35s ease}
body.fnav-inner{padding-top:64px}
#fnav-hit{position:fixed;top:0;left:0;right:0;height:28px;z-index:59}
#fnav{position:fixed;top:14px;left:50%;transform:translate(-50%,-160%);z-index:60;display:flex;gap:20px;align-items:center;
padding:10px 22px;--glass:rgba(247,244,238,.90);background:var(--glass);backdrop-filter:blur(14px) saturate(1.1);-webkit-backdrop-filter:blur(14px) saturate(1.1);
border:1px solid var(--glassborder,rgba(23,22,20,.35));border-radius:99px;box-shadow:0 10px 34px rgba(0,0,0,.12);
transition:transform .55s cubic-bezier(.22,.8,.26,1),background-color .35s ease;
font-family:var(--serif,'Charter','Bitstream Charter','Sitka Text',Cambria,Georgia,'Times New Roman',serif);color:var(--ink,#171614)}
#fnav.show,#fnav:hover,#fnav:focus-within,#fnav-hit:hover+#fnav{transform:translate(-50%,0)}
#fnav .nb{font-size:11px;letter-spacing:.22em;text-transform:uppercase;font-weight:600}
#fnav a{border:none;color:var(--ink,#171614);font-size:11px;letter-spacing:.14em;text-transform:uppercase;text-decoration:none}
#fnav a:hover{color:var(--accent,#7d2027)}
#fnav a.here{color:var(--accent,#7d2027)}
#fnav .ndot{width:6px;height:6px;border-radius:50%;background:var(--pr,#4b5f36);flex:0 0 auto}
#fnav .nlinks{display:flex;gap:20px;align-items:center}
#nburger{display:none;font-family:inherit;font-size:11px;letter-spacing:.18em;text-transform:uppercase;
background:none;border:none;color:inherit;cursor:pointer;padding:2px 0}
#nburger:hover{color:var(--accent,#7d2027)}
html[data-theme="dark"] #fnav{--glass:rgba(23,21,17,.90);background:var(--glass);border-color:var(--glassborder,rgba(236,231,219,.28));color:var(--ink,#ece7db)}
html[data-theme="dark"] #fnav a{color:var(--ink,#ece7db)}
html[data-theme="dark"] #fnav a:hover,html[data-theme="dark"] #fnav a.here,html[data-theme="dark"] #nburger:hover{color:var(--accent,#c2564c)}
html[data-theme="dark"] #fnav .ndot{background:var(--pr,#8fae72)}
@media(max-width:1520px){
  #nburger{display:block}
  #fnav .nlinks{display:none;position:absolute;top:calc(100% + 10px);right:0;flex-direction:column;
  align-items:flex-end;gap:13px;background:var(--glass);backdrop-filter:blur(16px) saturate(1.1);
  -webkit-backdrop-filter:blur(16px) saturate(1.1);border:1px solid var(--glassborder,rgba(23,22,20,.35));border-radius:16px;
  padding:18px 24px;box-shadow:0 14px 40px rgba(0,0,0,.16);min-width:170px}
  #fnav .nlinks.open{display:flex;animation:navdrop .35s cubic-bezier(.22,.8,.26,1)}
  html[data-theme="dark"] #fnav .nlinks{background:var(--glass);border-color:var(--glassborder,rgba(236,231,219,.28))}
  @keyframes navdrop{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
}
@media(prefers-reduced-motion:reduce){#fnav{transition:none}#fnav .nlinks.open{animation:none}}
"""


def markup(page):
    here = current_keys(page)
    sticky = "1" if not is_home(page) else "0"
    shown = ' class="show"' if not is_home(page) else ""
    threshold = "80"  # small scroll; inner pages are also data-sticky
    links = []
    for key, label, dest in LINKS:
        cls = ' class="here"' if key in here else ""
        cur = ' aria-current="page"' if key in here else ""
        links.append(f'<a href="{href(dest, page)}" data-nav="{key}"{cls}{cur}>{label}</a>')
    return (
        f'<div id="fnav-hit" aria-hidden="true"></div>\n'
        f'<nav id="fnav"{shown} aria-label="Sections" data-show-at="{threshold}" data-sticky="{sticky}">\n'
        f'  <a class="nb" href="/" aria-label="compute.world home">CW</a><span class="ndot" title="Live data"></span>\n'
        f'  <button id="nburger" aria-label="Open menu" aria-expanded="false">Menu</button>\n'
        f'  <div class="nlinks" id="nlinks">\n'
        f'    {"".join(links)}\n'
        f'  </div>\n'
        f'</nav>\n'
    )


def script(page):
    # page is accepted so callers stay symmetric; behavior is data-attribute driven.
    return """(function(){
  var nav=document.getElementById("fnav"), nb=document.getElementById("nburger"), nl=document.getElementById("nlinks");
  if(!nav) return;
  var threshold=parseInt(nav.getAttribute("data-show-at")||"80",10);
  var sticky=nav.getAttribute("data-sticky")==="1";
  function sync(){ if(sticky){ nav.classList.add("show"); return; } nav.classList.toggle("show", window.scrollY>threshold); }
  sync();
  window.addEventListener("scroll",sync,{passive:true});
  if(nb&&nl){
    nb.onclick=function(e){ e.stopPropagation(); var open=nl.classList.toggle("open"); nb.setAttribute("aria-expanded",open); nav.classList.add("show"); };
    nl.querySelectorAll("a").forEach(function(a){ a.addEventListener("click",function(){ nl.classList.remove("open"); }); });
    document.addEventListener("click",function(e){ if(!nl.contains(e.target)&&e.target!==nb) nl.classList.remove("open"); });
  }
})();
"""
