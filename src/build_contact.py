#!/usr/bin/env python3
"""The Desk (contact.html). Theme and chrome stay in lockstep with the v1.5 desk."""
import os
from fnav import css as fnav_css, markup as fnav_markup, script as fnav_script
from desk_chrome import MARKET_THEME_CSS, cite_line, SITE
from seo import og_block

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASOF = "2026-09-07"
CITE = cite_line("The Desk", f"{SITE}/contact.html", ASOF)

PAGE = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="theme-color" content="#F3F5F2">
<script>(function(){{try{{var t=localStorage.getItem("cnw_theme");if(t!=="dark"&&t!=="light"){{var h=new Date().getHours();t=(h>=19||h<7)?"dark":"light";}}document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();</script>
<title>The Desk · Contact Us · compute.world</title>
<meta name="description" content="Contact Us at The Desk: briefings, corrections, cite / data, and speaking. Pukar C. Hamal's public compute desk.">
<link rel="canonical" href="https://compute.world/contact.html">
<meta name="robots" content="index,follow,max-image-preview:large">
{og_block("The Desk · Contact Us · compute.world",
    "Briefings, corrections, cite / data, and speaking. Pukar C. Hamal's public compute desk.",
    "https://compute.world/contact.html", "og.png", image_alt="compute.world — Countries. Compute.")}
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"ContactPage","name":"The Desk","url":"https://compute.world/contact.html","description":"Pukar C. Hamal's public compute desk. Briefings, corrections, cite / data, and speaking.","author":{{"@type":"Person","name":"Pukar C. Hamal","url":"https://compute.world/contact.html","sameAs":["https://pukarhamal.com/"]}},"publisher":{{"@id":"https://compute.world/#org"}}}}
</script>
<link rel="icon" href="/mark.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
<style>
{MARKET_THEME_CSS}
{fnav_css()}
.tchip{{position:fixed;top:14px;right:max(14px,env(safe-area-inset-right));z-index:70;width:42px;height:42px;
border-radius:50%;background:var(--glass);border:1px solid var(--glassborder);
backdrop-filter:blur(14px) saturate(1.1);-webkit-backdrop-filter:blur(14px) saturate(1.1);
color:var(--ink);cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0;
box-shadow:0 8px 26px rgba(0,0,0,.12)}}
.tchip svg{{position:absolute;width:18px;height:18px}}
.tchip .ic-sun{{opacity:0}} html[data-theme="dark"] .tchip .ic-sun{{opacity:1}} html[data-theme="dark"] .tchip .ic-moon{{opacity:0}}
*{{margin:0;padding:0;box-sizing:border-box}}
html{{background:var(--paper)}}
body{{background:var(--paper);color:var(--ink);font-family:var(--serif);font-size:17px;line-height:1.62;
-webkit-font-smoothing:antialiased;min-height:100vh;display:flex;flex-direction:column}}
a{{color:var(--accent);text-decoration:none;border-bottom:1px solid rgba(31,79,216,.35)}}
a:hover{{border-bottom-color:var(--accent)}}
.wrap{{max-width:720px;margin:0 auto;padding:0 28px;width:100%}}
.masthead{{padding:34px 0 0;text-align:center}}
.masthead .name{{font-size:15px;letter-spacing:.34em;text-transform:uppercase}}
.masthead .name b{{font-weight:600}}
.masthead .name a{{border:none;color:var(--ink)}}
.masthead .sub{{margin-top:8px;font-size:12.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}}
.mastrule{{margin-top:20px;border-top:2px solid var(--rule2);border-bottom:1px solid var(--rule2);height:5px}}
main{{flex:1 0 auto;padding:48px 0 40px}}
.eyebrow{{font-size:11.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--muted);margin-bottom:16px;font-family:var(--sans)}}
h1{{font-weight:400;font-size:clamp(30px,5vw,44px);line-height:1.16;margin-bottom:22px}}
h1 em{{font-style:italic}}
.prose{{max-width:600px}}
.prose p{{margin-bottom:16px;color:var(--muted)}}
.prose p b{{color:var(--ink);font-weight:600}}
.lanes{{margin:8px 0;max-width:600px}}
.lane{{padding:16px 0;border-top:1px solid var(--rule)}}
.lane:last-child{{border-bottom:1px solid var(--rule)}}
.lane .k{{font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink);margin-bottom:6px;font-family:var(--sans)}}
.lane p{{font-size:15.5px;color:var(--muted);margin:0;line-height:1.55}}
.gate{{border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule);margin:30px 0;padding:26px 0}}
.gate .lbl{{font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin-bottom:16px;font-family:var(--sans)}}
#reveal{{display:none;opacity:0;transform:translateY(10px);transition:all .6s cubic-bezier(.22,.8,.26,1)}}
#reveal.in{{display:block;opacity:1;transform:none}}
.mailbtn{{display:inline-block;border:1px solid var(--rule2);background:var(--ink);color:var(--paper);
padding:13px 26px;font-family:var(--serif);font-size:16px;letter-spacing:.02em;border-bottom:1px solid var(--rule2)}}
.mailbtn:hover{{color:var(--paper)}}
.addr{{margin-top:14px;font-size:15px;color:var(--ink);font-family:var(--sans)}}
.addr .copy{{margin-left:12px;cursor:pointer;color:var(--accent);border-bottom:1px solid transparent}}
.citebox{{margin:24px 0;padding:16px 18px;border:1px solid var(--rule);background:var(--tint);border-radius:8px}}
.citebox .k{{font-family:var(--sans);font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}}
.citebox code{{display:block;font-size:14px;line-height:1.5;color:var(--ink);word-break:break-word}}
.back{{margin-top:28px;font-size:14px}}
footer{{flex-shrink:0;border-top:2px solid var(--rule2);padding:22px 0 40px;text-align:center}}
footer .c1{{font-size:12px;letter-spacing:.3em;text-transform:uppercase;font-family:var(--sans)}}
footer .c2{{margin-top:10px;font-size:12px;color:var(--muted)}}
.fallback{{font-size:14px;color:var(--muted);margin-top:12px}}
</style>
</head>
<body class="fnav-inner">
<button id="themetog" class="tchip" aria-label="Switch to night mode" title="Day / Night">
  <svg class="ic-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z"/></svg>
  <svg class="ic-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.9 1.9M19.1 4.9l-1.8 1.8M6.7 17.3l-1.9 1.9"/></svg>
</button>
{fnav_markup("contact")}
<div class="wrap">
  <div class="masthead">
    <div class="name"><a href="/"><b>COMPUTE</b>.WORLD</a></div>
    <div class="sub">Countries. Compute. · The Desk</div>
    <div class="mastrule"></div>
  </div>
  <main>
    <div class="eyebrow">The Desk · Contact Us</div>
    <h1>Briefings, corrections, and <em>better data</em>.</h1>
    <div class="prose">
      <p>This is <b>Pukar C. Hamal</b>'s public compute desk, written from San Francisco. Companies write when they want a briefing, a sourced print checked, a country conversion question, or to cite or license the tapes. Researchers write when a number is wrong. Campus power, water, land, tax, and jobs have a sourced clerk's book at the <a href="/data-centers.html">Data centers FAQ</a>. Named campuses sit on a desk-curated globe at <a href="/campuses.html">Campuses</a> — a register, not a census.</p>
      <p>A light pointer: <a href="https://pukarhamal.com/">pukarhamal.com</a>. The address is kept behind a quick human check, so it reaches a person and not a scraper. Confirm below and it appears.</p>
    </div>
    <div class="lanes">
      <div class="lane"><div class="k">Briefing</div><p>A sourced compute briefing: country conversion, a silicon print, a tape read. Write with the question.</p></div>
      <div class="lane"><div class="k">Correction</div><p>A number is wrong, a country's endowment is mismeasured, a sovereign deal belongs in the precedents table. Write. The index is only as good as the arguments people bring to it.</p></div>
      <div class="lane"><div class="k">Cite / data</div><p>Quote and chart under CC BY 4.0 with attribution to compute.world. Commercial products, APIs, and bulk redistribution need a license. The dataset is <a href="/data.json">data.json</a>.</p></div>
      <div class="lane"><div class="k">Speaking</div><p>Invitations to talk about the five tapes. Write with the occasion and the date.</p></div>
    </div>
    <div class="citebox" id="cite">
      <div class="k">Cite this desk</div>
      <code id="citeBox">{CITE}</code>
    </div>
    <div class="gate">
      <div class="lbl">One quick check that you're human</div>
      <div class="cf-turnstile" data-sitekey="1x00000000000000000000AA" data-callback="onHuman" data-theme="auto"></div>
      <div id="reveal">
        <a class="mailbtn" id="mailbtn" href="#">Email Pukar</a>
        <div class="addr"><span class="a" id="addr"></span><span class="copy" id="copy">Copy</span></div>
      </div>
      <noscript><p class="fallback">This check needs JavaScript enabled. Write to pchamal [at] alumni [dot] stanford [dot] edu.</p></noscript>
    </div>
    <div class="prose">
      <p>You can also cite or build on the index freely under <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a> with attribution to compute.world, and the full dataset lives at <a href="/data.json">data.json</a>.</p>
    </div>
    <div class="back"><a href="/">&larr; Back to the index</a></div>
  </main>
</div>
<footer>
  <div class="wrap">
    <div class="c1">COMPUTE.WORLD</div>
    <div class="c2">Countries. Compute. · The Compute Net Worth Index&#8482; · &copy; 2026 Pukar C. Hamal · San Francisco, CA · Data CC BY 4.0</div>
  </div>
</footer>
<script>
var _e = "Y0Ncoaha".length ? "cGNoYW1hbEBhbHVtbmkuc3RhbmZvcmQuZWR1" : "";
function onHuman(){{
  var addr = atob("cGNoYW1hbEBhbHVtbmkuc3RhbmZvcmQuZWR1");
  var subject = encodeURIComponent("The Desk · compute.world");
  document.getElementById("mailbtn").href = "mailto:" + addr + "?subject=" + subject;
  document.getElementById("addr").textContent = addr;
  var r = document.getElementById("reveal");
  r.style.display = "block"; requestAnimationFrame(function(){{ r.classList.add("in"); }});
  var copy = document.getElementById("copy");
  copy.onclick = function(){{ navigator.clipboard.writeText(addr).then(function(){{
    copy.textContent = "Copied"; setTimeout(function(){{ copy.textContent = "Copy"; }}, 1400); }}); }};
}}
var _tg=document.getElementById("themetog");
function _setT(t,sv){{document.documentElement.setAttribute("data-theme",t);
  if(sv){{try{{localStorage.setItem("cnw_theme",t)}}catch(e){{}}}}
  _tg.setAttribute("aria-label",t==="dark"?"Switch to day mode":"Switch to night mode");}}
_tg.onclick=function(){{_setT(document.documentElement.getAttribute("data-theme")==="dark"?"light":"dark",true)}};
_setT(document.documentElement.getAttribute("data-theme")==="dark"?"dark":"light",false);
{fnav_script("contact")}
setTimeout(function(){{
  if(!window.turnstile){{
    var g = document.querySelector(".cf-turnstile");
    if(g && !g.dataset.done){{ g.dataset.done="1";
      g.innerHTML = '<a href="#" id="manual" style="font-size:14px">I\\'m human, show the address &rarr;</a>';
      document.getElementById("manual").onclick = function(e){{ e.preventDefault(); onHuman(); }};
    }}
  }}
}}, 4000);
</script>
</body>
</html>
'''

open(os.path.join(ROOT, "contact.html"), "w").write(PAGE)
print("contact.html generated")
