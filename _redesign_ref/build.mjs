import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as topojson from "topojson-client";
import { geoEqualEarth, geoPath } from "d3-geo";
import { CONFIG, TIER, TIER_DEF, TIER_PLAIN, COUNTRIES, CHIPS, VENUE_URL, DOMAINS, PRICE_PATHS, PRICE_CAPTIONS, SNAPSHOT_DATES, PRECEDENTS, READINESS } from "./data.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SRC = __dirname, ROOTDIR = path.resolve(__dirname, ".."), DIST = path.join(ROOTDIR, "dist"), VENDOR = path.join(ROOTDIR, "vendor", "node_modules");
const SITE = CONFIG.site, ASOF = CONFIG.asOf;

/* ---------- helpers ---------- */
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], MONTHS_LONG = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const fmtDate = iso => { const p = iso.split("-"); return p.length===2 ? MONTHS[+p[1]-1]+" "+p[0] : (+p[2])+" "+MONTHS[+p[1]-1]+" "+p[0]; };
const fmtDateLong = iso => { const p = iso.split("-"); return (+p[2])+" "+MONTHS_LONG[+p[1]-1]+" "+p[0]; };
const monYear = iso => MONTHS[+iso.split("-")[1]-1]+" "+iso.split("-")[0];
const num = n => Number(n).toLocaleString("en-US");
const fmtB = b => b >= 1000 ? "$"+(b/1000).toFixed(1)+"T" : b >= 10 ? "$"+Math.round(b)+"B" : b >= 1 ? "$"+(+b.toFixed(1))+"B" : "under $1B";
const fmtT = t => t >= 1 ? "$"+t+"T" : "$"+Math.round(t*1000)+"B";
const fmtRange = c => c.ceilHi === 0 ? "$0" : (c.ceilLo >= 1 ? "$"+c.ceilLo+" to "+c.ceilHi+"T" : fmtT(c.ceilLo)+" to "+fmtT(c.ceilHi));
const fmtGW = gw => gw >= 1 ? gw.toFixed(1)+" GW" : Math.round(gw*1000)+" MW";
const fmtUSD = v => v == null ? "—" : "$"+(Math.round(v*100)/100).toFixed(2);
const pct = (a,b) => b ? Math.round((a-b)/b*100) : 0;
const dateNum = iso => new Date(iso+"T00:00:00Z").getTime();
const VENDOR_CODE = {NVIDIA:"NV", AMD:"AMD", Google:"G", Huawei:"HW", Cerebras:"CB", Amazon:"AWS", Groq:"GQ"};
const write = (rel, content) => { const p = path.join(DIST, rel); fs.mkdirSync(path.dirname(p), {recursive:true}); fs.writeFileSync(p, content); };

[...COUNTRIES].sort((a,b)=>b.gdc-a.gdc).forEach((c,i)=>{ c.gdcEst = i >= 35; });
const byId = Object.fromEntries(COUNTRIES.map(c=>[c.id,c]));
const css = fs.readFileSync(path.join(SRC,"styles.css"),"utf8");
const appJs = fs.readFileSync(path.join(SRC,"app.js"),"utf8");

const flagImg = (c, root, cls="") => `<img class="flag ${cls}" src="${root}flags/${c.flag}.svg" alt="Flag of ${esc(c.name)}" width="24" height="18" loading="lazy" data-code="${c.iso2}" onerror="flagFail(this)">`;
const logoEl = (name, cls="") => { const d = DOMAINS[name]; const ini = VENDOR_CODE[name] || name.replace(/[^A-Z0-9]/g,"").slice(0,3) || name.slice(0,2).toUpperCase(); return `<span class="logo ${cls}" title="${esc(name)}">${d?`<img src="https://www.google.com/s2/favicons?domain=${d}&sz=64" alt="" loading="lazy" onerror="logoFail(this)">`:""}<span>${esc(ini)}</span></span>`; };
const venueEl = name => `<span class="venue">${logoEl(name)}<span>${esc(name)}</span></span>`;
const tierPlain = c => TIER_PLAIN[c.tier];

/* ---------- world map (Equal Earth, Natural Earth 110m) ---------- */
function buildMap(){
  const world = JSON.parse(fs.readFileSync(path.join(VENDOR,"world-atlas","countries-110m.json"),"utf8"));
  const fc = topojson.feature(world, world.objects.countries);
  const W=960, H=470;
  const proj = geoEqualEarth().fitSize([W,H], {type:"Sphere"});
  const pathGen = geoPath(proj).digits(1);
  const ALIAS = {"United States of America":"USA","Dem. Rep. Congo":"COD","Bosnia and Herz.":"BIH","Czechia":"CZE","Czech Rep.":"CZE","South Korea":"KOR","Korea":"KOR","Lao PDR":"LAO","Türkiye":"TUR","United Arab Emirates":"ARE","Viet Nam":"VNM","Iran":"IRN","Russia":"RUS","Tanzania":"TZA","Bolivia":"BOL","Venezuela":"VEN","Syria":null,"Dominican Rep.":null,"Central African Rep.":null,"S. Sudan":null,"Eq. Guinea":null,"Solomon Is.":null,"Falkland Is.":null,"Fr. S. Antarctic Lands":null,"W. Sahara":null,"eSwatini":null,"North Korea":null,"Macedonia":null,"North Macedonia":null,"Timor-Leste":null,"Brunei":null,"Puerto Rico":null,"Bahamas":null,"Trinidad and Tobago":null,"Guinea-Bissau":null,"Somaliland":null,"Congo":null,"Antarctica":null,"Greenland":null,"New Caledonia":null,"Vanuatu":null,"Fiji":null};
  const byName = Object.fromEntries(COUNTRIES.map(c=>[c.name.toLowerCase(), c.id]));
  const matched = new Set(); let paths = "", dots = "";
  for(const f of fc.features){
    const n = f.properties.name; let id = ALIAS.hasOwnProperty(n) ? ALIAS[n] : (byName[n.toLowerCase()] || null);
    const d = pathGen(f); if(!d) continue;
    if(id && byId[id]){ matched.add(id); const c = byId[id];
      paths += `<path class="c idx t-${c.tier}" data-id="${id}" d="${d}"><title>${esc(c.name)}</title></path>`;
      if(pathGen.area(f) < 60){ const [cx,cy] = pathGen.centroid(f); dots += `<circle class="dot" data-id="${id}" cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="3.2"><title>${esc(c.name)}</title></circle>`; }
    } else paths += `<path class="c" d="${d}"/>`;
  }
  const FALLBACK = { SGP:[103.82,1.35], BHR:[50.55,26.07] };
  for(const c of COUNTRIES){ if(!matched.has(c.id)){ const ll = FALLBACK[c.id]; if(ll){ const [x,y]=proj(ll); dots += `<circle class="dot" data-id="${c.id}" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3.2"><title>${esc(c.name)}</title></circle>`; matched.add(c.id); } else console.warn("map: unmatched", c.id, c.name); } }
  const sphere = pathGen({type:"Sphere"});
  return `<svg id="mapsvg" viewBox="0 0 ${W} ${H}" role="img" aria-label="World map of the 108 indexed countries, shaded by tier"><path d="${sphere}" fill="none" stroke="var(--line)" stroke-width="1"/>${paths}${dots}</svg>`;
}

/* ---------- shared chrome ---------- */
const NAV = [["Countries","#board","countries"],["Silicon prices","#board","silicon"],["Trends","#trends"],["Projects","#projects"],["Method","#method"],["Country profiles","#profiles"],["Data","#data"]];
function head({title, description, canonical, root, ogType="website", jsonld, image}){
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<meta name="description" content="${esc(description)}">
<link rel="canonical" href="${canonical}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">
<meta name="theme-color" content="#F3F5F2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#0F1216" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="${ogType}">
<meta property="og:site_name" content="compute.world">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(description)}">
<meta property="og:url" content="${canonical}">
<meta property="og:image" content="${image||SITE+"/og.png"}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(description)}">
<meta name="twitter:image" content="${image||SITE+"/og.png"}">
<link rel="alternate" type="application/rss+xml" title="compute.world brief" href="${SITE}/brief.xml">
<link rel="preload" href="${root}fonts/SchibstedGrotesk-wght.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="${root}fonts/Newsreader-opsz-wght.woff2" as="font" type="font/woff2" crossorigin>
<script type="application/ld+json">${JSON.stringify(jsonld)}</script>
<style>${css.replace(/\{\{root\}\}/g, root)}</style>
</head>`;
}
function masthead(root, current){
  const links = NAV.map(([label,href,tab])=>`<a href="${root}index.html${href}"${tab?` data-tab="${tab}"`:""}${current===label?' class="current"':''}>${label}</a>`).join("");
  return `<header class="masthead"><div class="wrap">
  <a class="brand" href="${root}index.html"><b>compute.world</b><span>Countries. Compute. Silicon.</span></a>
  <nav class="nav" aria-label="Sections">${links}
    <details class="more"><summary>More <svg width="10" height="6" viewBox="0 0 10 6" aria-hidden="true"><path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.5"/></svg></summary>
      <div class="menu">
        <a href="${SITE}/wire.html">Signals<small>The Wire: credibility-scored feed</small></a>
        <a href="${SITE}/neoclouds.html">GPU clouds<small>Who rents GPUs, by region</small></a>
        <a href="${SITE}/hyperscalers.html">Hyperscalers<small>271 cloud locations</small></a>
        <a href="${SITE}/inference.html">Inference providers<small>Who sells tokens</small></a>
        <a href="${SITE}/data-centers.html">Data centers<small>Power, water, land, tax, jobs</small></a>
        <a href="${SITE}/campuses.html">Campuses<small>Named sites on a globe</small></a>
        <a href="${SITE}/agents.html">For agents<small>Machine-readable edition</small></a>
        <a href="${SITE}/contact.html">Contact the desk</a>
      </div></details>
  </nav>
  <div class="asof"><span class="live" aria-hidden="true"></span>Updated <b>${fmtDate(ASOF)}</b></div>
  <button class="menu-btn" id="menuBtn" aria-expanded="false" aria-controls="mnav">Menu <svg width="12" height="10" viewBox="0 0 12 10" aria-hidden="true"><path d="M0 1h12M0 5h12M0 9h12" stroke="currentColor" stroke-width="1.5"/></svg></button>
</div></header>
<nav class="mnav" id="mnav" aria-label="Sections"><div class="wrap">
  <div class="asof-m">Updated <b>${fmtDate(ASOF)}</b></div>
  ${NAV.map(([label,href,tab])=>`<a href="${root}index.html${href}"${tab?` data-tab="${tab}"`:""}>${label}</a>`).join("")}
  <a href="${SITE}/wire.html">Signals</a><a href="${SITE}/neoclouds.html">GPU clouds</a><a href="${SITE}/data-centers.html">Data centers</a><a href="${SITE}/contact.html">Contact</a>
</div></nav>`;
}
function footer(){
  return `<footer><div class="wrap"><div class="cols">
  <div><p class="tag">Countries. Compute. Silicon. And the wires between them.</p><b>The Compute Net Worth Index</b>, version 1.5, created by Pukar C. Hamal and first published at compute.world on 10 August 2026. A public compute desk: weekday updates, sourced prints only. Country macros refresh from the IMF and World Bank. Compute Net Worth, The Compute Net Worth Index and Gross Domestic Compute are trademarks of Pukar C. Hamal. This site is an analytical framework and an invitation to argue with its inputs in public. It is not investment advice.</div>
  <div><b>Sources</b><br>NVIDIA earnings and keynotes, SemiAnalysis, Epoch AI, IEA, IMF WEO, World Bank, EIU, Transparency International, IHA, ESMAP, Cushman &amp; Wakefield, Rystad, Knight Frank, BNEF, and venue list pages fetched each snapshot. Flags: flag-icons (MIT). Vendor marks belong to their owners.</div>
  <div><b>Desk</b><br>San Francisco, CA<br><a href="${SITE}/contact.html">Briefings, corrections, licensing</a><br><a href="${SITE}/agents.html">Agent edition</a><br><a href="${SITE}/llms.txt">llms.txt</a> · <a href="${SITE}/sitemap.xml">Sitemap</a></div>
</div></div></footer>`;
}
const tinyJs = `<script>window.flagFail=function(i){var s=document.createElement("span");s.className="code";s.textContent=i.dataset.code||"";i.replaceWith(s)};window.logoFail=function(i){i.parentElement.classList.add("fallback")};document.addEventListener("click",function(e){var b=e.target.closest("[data-copy]");if(!b)return;var t=document.querySelector(b.dataset.copy).textContent.trim();navigator.clipboard.writeText(t).then(function(){var o=b.textContent;b.textContent="Copied";setTimeout(function(){b.textContent=o},1400)})});var m=document.getElementById("menuBtn");if(m)m.addEventListener("click",function(){var n=document.getElementById("mnav");var o=!n.classList.contains("open");n.classList.toggle("open",o);m.setAttribute("aria-expanded",o)});</script>`;

/* ---------- homepage ---------- */
function homepage(mapSvg){
  const top10 = [...COUNTRIES].sort((a,b)=>a.rank-b.rank).slice(0,10);
  const pricePaths = Object.fromEntries(Object.entries(PRICE_PATHS).map(([k,v])=>[k, v.map(s=>({...s, short:s.name.split(",")[0]}))]));
  const data = { config:CONFIG, tier:TIER, tierDef:TIER_DEF, countries:COUNTRIES, chips:CHIPS, venueUrl:VENUE_URL, domains:DOMAINS, pricePaths, priceCaptions:PRICE_CAPTIONS, snapshotDates:SNAPSHOT_DATES, precedents:PRECEDENTS, readiness:READINESS };
  const jsonld = {"@context":"https://schema.org","@graph":[
    {"@type":"WebSite","@id":SITE+"/#website","url":SITE+"/","name":"compute.world","alternateName":["The Compute Net Worth Index","The Silicon Tape"],"description":"Countries, compute and silicon: the world's compute index. 108 countries priced by compute net worth; 20 AI accelerators with sourced rental prices.","publisher":{"@id":SITE+"/#org"},"inLanguage":"en"},
    {"@type":"Organization","@id":SITE+"/#org","name":"compute.world","url":SITE+"/","logo":SITE+"/og.png","founder":{"@type":"Person","name":"Pukar C. Hamal"},"foundingDate":"2026-08-10","address":{"@type":"PostalAddress","addressLocality":"San Francisco","addressRegion":"CA","addressCountry":"US"}},
    {"@type":"Dataset","@id":SITE+"/#cnw","name":"The Compute Net Worth Index","alternateName":"CNW Index","url":SITE+"/","description":"Compute net worth for 108 countries: resource ceiling (GW and USD), unlockable value, live datacenter capacity and Gross Domestic Compute, readiness and conversion scores. Updated weekdays; append-only history.","creator":{"@id":SITE+"/#org"},"license":"https://github.com/pchamal/compute-world/blob/main/LICENSE.md","isAccessibleForFree":true,"dateModified":ASOF,"datePublished":"2026-08-10","temporalCoverage":"2026-08-10/..","spatialCoverage":"World","keywords":["compute capacity","data center capacity by country","AI compute","compute net worth","gross domestic compute","sovereign AI"],"variableMeasured":[{"@type":"PropertyValue","name":"Live datacenter IT capacity","unitText":"GW"},{"@type":"PropertyValue","name":"Resource ceiling","unitText":"GW"},{"@type":"PropertyValue","name":"CNW ceiling","unitText":"USD trillions"},{"@type":"PropertyValue","name":"CNW unlockable","unitText":"USD billions"},{"@type":"PropertyValue","name":"Gross Domestic Compute","unitText":"USD billions"},{"@type":"PropertyValue","name":"Readiness","unitText":"0 to 1"},{"@type":"PropertyValue","name":"Conversion score","unitText":"0 to 100"}],"distribution":[{"@type":"DataDownload","encodingFormat":"application/json","contentUrl":SITE+"/data.json"},{"@type":"DataDownload","encodingFormat":"application/json","contentUrl":SITE+"/rank-history.json"}]},
    {"@type":"Dataset","@id":SITE+"/#silicon","name":"The Silicon Tape","url":SITE+"/silicon.html","description":"Sourced AI accelerator rental prices in USD per GPU-hour, by venue and term (on-demand, spot, reserved, capacity blocks), with dated history. No averages, no imputed tenors.","creator":{"@id":SITE+"/#org"},"license":"https://creativecommons.org/licenses/by/4.0/","isAccessibleForFree":true,"dateModified":ASOF,"keywords":["GPU rental price","H100 price per hour","B200 price","AI accelerator pricing"],"distribution":[{"@type":"DataDownload","encodingFormat":"application/json","contentUrl":SITE+"/silicon.json"},{"@type":"DataDownload","encodingFormat":"application/json","contentUrl":SITE+"/silicon-history.json"}]},
    {"@type":"ItemList","name":"Countries by unlockable compute value","itemListOrder":"https://schema.org/ItemListOrderDescending","numberOfItems":COUNTRIES.length,"itemListElement":top10.map((c,i)=>({"@type":"ListItem","position":i+1,"name":c.name,"url":SITE+"/country/"+c.slug+"/"}))}
  ]};
  const root = "";
  const body = `
<body>
<a class="sr" href="#board">Skip to the rankings</a>
${masthead(root)}
<main id="top"><div class="wrap">

<section class="lede" aria-label="Introduction">
  <div>
    <h1>Countries. Compute. Silicon.<span class="soft">And the wires between them.</span></h1>
    <p>Every country has a compute net worth: the AI compute its own energy could host. <span class="more-lede">A kilowatt-hour sold as raw power earns about five cents; run through a contracted GPU cloud it earns one to two dollars. </span>This index prices what each nation could host, counts what it actually runs, and prints what the silicon rents for, from sourced, dated quotes only.</p>
  </div>
  <div class="ledger" aria-label="Headline figures"><dl>
    <div><dt>$662T</dt><dd>Ceiling: every identified watt hosting compute at today's price of a gigawatt, $60 to 80B.</dd></div>
    <div><dt>$64T</dt><dd>Unlockable: the slice of that ceiling underwriters could credibly sign today.</dd></div>
    <div><dt>$4.7T</dt><dd>Live compute: what actually runs. 0.7% of the ceiling, 68% of it in two countries.</dd></div>
    <div><dt>108 + 20</dt><dd>Countries priced, and accelerators on the price tape. Updated every weekday.</dd></div>
  </dl></div>
</section>

<section id="board" class="board-grid" aria-label="Rankings">
  <div class="board">
    <div class="board-head">
      <div class="tabs" role="tablist" aria-label="Index">
        <button class="tab" role="tab" id="tab-countries" aria-selected="true" aria-controls="panel-board" data-tab="countries">Countries</button>
        <button class="tab" role="tab" id="tab-silicon" aria-selected="false" aria-controls="panel-board" data-tab="silicon">Silicon prices</button>
      </div>
      <div class="seg" id="viewSeg" role="group" aria-label="View"><button data-view="list" aria-pressed="true">List</button><button data-view="map" aria-pressed="false">Map</button></div>
      <div class="tools">
        <label class="sr" for="lens">Sort by</label><select class="select" id="lens"></select>
        <label class="sr" for="topn">Rows</label><select class="select" id="topn"><option value="10">Top 10</option><option value="25">Top 25</option><option value="all">All</option></select>
        <button class="btn" id="csvBtn" title="Download the rows you are looking at as CSV"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2v8m0 0L5 7m3 3l3-3M3 12v2h10v-2" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>CSV</button>
        <button class="btn" id="linkBtn" title="Copy a link to this view"><svg viewBox="0 0 16 16" aria-hidden="true"><path d="M6.5 9.5a3 3 0 004.2 0l2-2a3 3 0 00-4.2-4.2l-1 1M9.5 6.5a3 3 0 00-4.2 0l-2 2a3 3 0 004.2 4.2l1-1" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>Link</button>
      </div>
    </div>
    <div id="panel-board" role="tabpanel" aria-labelledby="tab-countries">
      <div id="listWrap"><div class="colhead" id="colhead"></div><ol class="rows" id="rows"></ol></div>
      <div id="mapWrap" class="mapview" hidden>${mapSvg}<div class="maplegend" id="maplegend"></div><div class="maptip" id="maptip"></div></div>
    </div>
    <div class="board-foot" id="boardFoot"></div>
  </div>
  <aside class="rail" aria-label="Movers and signals">
    <div class="rail-block"><h3>Movers</h3><p class="sub">Conversion score, change since the 19 Aug snapshot</p><ol class="movers" id="movers"></ol></div>
    <div class="rail-block"><h3>Latest signals</h3><p class="sub">What moved a country this week</p><ul class="wire" id="wire"></ul><a class="rail-more" href="${SITE}/wire.html">All signals on the Wire</a></div>
  </aside>
</section>

<section id="trends" class="section">
  <div class="section-head"><div><h2>Trends</h2><p class="deck">Observed snapshots only. The index never interpolates between prints, so a line here is a set of dated facts, not a curve fitted to them.</p></div><div class="side" id="histDepth"></div></div>
  <div class="charts">
    <div class="chart wide">
      <div class="chart-head"><div><h3>Conversion score: who is actually converting</h3><p>0 to 100. Moves when a country does something in public.</p></div><div class="chips" id="rzChips"></div></div>
      <div id="rzChart"></div>
      <div class="scrub"><span>As of</span><input type="range" id="rzScrub" min="0" max="1" value="1" step="1" aria-label="Snapshot date"><b id="rzDate"></b></div>
      <p class="caption" id="rzCaption"></p>
    </div>
    <div class="chart wide">
      <div class="chart-head"><div><h3>What an hour of silicon costs</h3><p>Same scale across the three, so the eye can compare. Dated prints, same venue, same term. Steps, not candles.</p></div></div>
      <div class="multiples" id="multiples"></div>
    </div>
  </div>
</section>

<section id="projects" class="section">
  <div class="section-head"><div><h2>Projects on the ground</h2><p class="deck">Sovereign AI factories, as reported. The three stalled projects all stalled on power, which is the whole thesis in three rows.</p></div></div>
  <div class="feed"><div class="feed-head"><div class="chips" id="statusChips"></div><span class="count" id="precCount"></span></div><ul class="plist" id="plist"></ul></div>
</section>

<section id="method" class="section">
  <div class="section-head"><div><h2>How the numbers are made</h2><p class="deck">Three prices per country, read together. One is an option, two are counts. The gap between them is the country's reform agenda, priced.</p></div><div class="side"><a href="${SITE}/params.json">Every parameter is an editable cell</a></div></div>
  <div class="defs">
    <div class="def"><h3>Ceiling</h3><p class="plain">What the endowment could host</p><div class="formula">Resource ceiling (GW) × $60 to 80B per GW</div><p>Every technically identified watt, built and hosting compute at today's prices. Called a ceiling because that is what it is. Rerun it at the analyst build cost of $35B and the ordering survives.</p></div>
    <div class="def"><h3>Unlockable</h3><p class="plain">The bankable slice</p><div class="formula">Firm untapped GW × $50B × Readiness</div><p>Nameplate power converted to 24/7-grade by source, valued at build cost, then discounted by everything that makes an underwriter hesitate. An asset value, not revenue, and not a forecast that anyone builds it.</p></div>
    <div class="def"><h3>Live compute</h3><p class="plain">Gross Domestic Compute, GDC</p><div class="formula">Live datacenter GW × $50B</div><p>What actually runs today. GDC is to compute what GDP is to output. Markets below the top 35 are estimates and shown in grey. Valuing old colocation halls at the AI-factory price is a disclosed simplification.</p></div>
  </div>
  <div class="method-grid">
    <div class="stack"><h3>Readiness is a discount rate</h3><p>Eight components, weights summing to 100. Democracy is shown but unweighted, on purpose.</p><div class="stackbar" id="stackbar"></div><div class="stacklegend" id="stacklegend"></div></div>
    <div class="rules"><h3>Rules of the price tape</h3><ol>
      <li><b>Every price carries its label.</b> Venue, term, date. On-demand, spot, reserved and capacity blocks are never averaged together.</li>
      <li><b>A missing number is a dash.</b> Never an invented 0%, never a guessed discount off on-demand, never a converted token price.</li>
      <li><b>Change needs two dated prints.</b> Same venue, same term, same configuration, or it does not print.</li>
      <li><b>Ranks are ordinal hygiene.</b> Liquidity 40, demand 35, frontier 25. Not a valuation.</li>
      <li><b>History is append-only.</b> One snapshot per index per day, kept forever, never rewritten.</li>
    </ol></div>
  </div>
</section>

<section id="profiles" class="section">
  <div class="section-head"><div><h2>Country profiles</h2><p class="deck">All 108 countries, each with a page of its own: the three numbers, what holds it back, projects on the ground, and a line you can cite.</p></div></div>
  <div class="gaz-tools"><input class="search" id="gazSearch" type="search" placeholder="Search a country (press /)" aria-label="Search countries"><div class="chips" id="regionChips"></div></div>
  <div class="cards" id="cards"></div>
</section>

<section id="data" class="section">
  <div class="section-head"><div><h2>Use this data</h2><p class="deck">Free with attribution for research, journalism and personal use. Commercial products, APIs and bulk redistribution take a licence.</p></div><div class="side"><a href="https://github.com/pchamal/compute-world/blob/main/LICENSE.md">The one-page licence</a></div></div>
  <div class="use">
    <div class="use-block"><h3>Cite</h3><p>One line, any style guide.</p><div class="codebox" id="citeBox"></div><button class="btn" data-copy="#citeBox">Copy citation</button></div>
    <div class="use-block"><h3>Embed the rankings</h3><p>Attribution built in, updates itself.</p><div class="codebox" id="embedBox">&lt;iframe src="${SITE}/embed.html?n=10&amp;sort=u" width="100%" height="520" style="border:1px solid #1B222A" title="The Compute Net Worth Index"&gt;&lt;/iframe&gt;</div><button class="btn" data-copy="#embedBox">Copy embed code</button></div>
    <div class="use-block"><h3>Download</h3><p>CSV exports the rows you are looking at. JSON is the full record, machine-readable.</p><div class="links"><a href="${SITE}/data.json">data.json, countries</a><a href="${SITE}/silicon.json">silicon.json, prices</a><a href="${SITE}/silicon-history.json">silicon-history.json</a><a href="${SITE}/rank-history.json">rank-history.json</a><a href="${SITE}/params.json">params.json</a><a href="${SITE}/llms.txt">llms.txt</a></div></div>
    <div class="use-block"><h3>Follow</h3><p>Weekday brief, one feed per index. Corrections and new prints go to the desk.</p><div class="links"><a href="${SITE}/brief">The brief</a><a href="${SITE}/brief.xml">RSS, brief</a><a href="${SITE}/silicon.xml">RSS, silicon</a><a href="${SITE}/wire.xml">RSS, signals</a><a href="${SITE}/contact.html">Send a correction</a></div></div>
  </div>
</section>

<section class="section" aria-label="Also on compute.world">
  <div class="section-head"><h2>Also on compute.world</h2></div>
  <div class="also">
    <a href="${SITE}/silicon.html"><b>The full price tape</b><small>Term book, every venue quote, dated history</small></a>
    <a href="${SITE}/neoclouds.html"><b>GPU clouds</b><small>Who rents GPUs, by region and silicon</small></a>
    <a href="${SITE}/hyperscalers.html"><b>Hyperscalers</b><small>271 cloud locations with GPUs</small></a>
    <a href="${SITE}/inference.html"><b>Inference providers</b><small>Who sells tokens, on what</small></a>
    <a href="${SITE}/campuses.html"><b>Campuses</b><small>Named sites on a globe, a register not a census</small></a>
    <a href="${SITE}/data-centers.html"><b>Data centers</b><small>Campus power, water, land, tax, jobs</small></a>
  </div>
</section>

</div></main>
${footer()}
<dialog class="sheet" id="sheet" aria-labelledby="sheetTitle">
  <div class="sheet-head"><span id="sheetMark"></span><span class="name" id="sheetTitle"></span><button class="x" id="sheetClose" aria-label="Close"><svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true"><path d="M2 2l10 10M12 2L2 12" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></button></div>
  <div class="sheet-body" id="sheetBody"></div>
  <div class="sheet-foot" id="sheetFoot"></div>
</dialog>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script>const DATA=${JSON.stringify(data)};</script>
<script>${appJs}</script>
</body>
</html>`;
  return head({title:"compute.world — Countries. Compute. Silicon. The world's compute index", description:"Which countries hold the electrons, what the silicon rents for, and who is converting. 108 countries priced by compute net worth, 20 AI accelerators with sourced rental prices, updated weekdays.", canonical:SITE+"/", root, jsonld}) + body;
}

/* ---------- country pages ---------- */
function threeBars(c){
  const rows = [["Ceiling, high end", c.ceilHi*1000, fmtT(c.ceilHi), "ceil"],["Unlockable", c.unlock, fmtB(c.unlock), ""],["Live compute", c.gdc, fmtB(c.gdc), ""]];
  const max = Math.max(...rows.map(r=>r[1]), 1); const W=720, H=112, L=150, R=90;
  let s = "";
  rows.forEach((r,i)=>{ const y=10+i*34; const w=Math.max(0,(r[1]/max)*(W-L-R)); s += `<text class="lab" x="${L-10}" y="${y+13}" text-anchor="end">${esc(r[0])}</text><rect class="${r[3]}" x="${L}" y="${y}" width="${w.toFixed(1)}" height="18" rx="2"/><text class="val" x="${(L+w+8).toFixed(1)}" y="${y+13}">${esc(r[2])}</text>`; });
  return `<div class="threebars"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Ceiling, unlockable and live compute for ${esc(c.name)}, same scale">${s}</svg></div>`;
}
function answerText(c){
  if(c.id==="SGP") return `<b>Singapore runs about 1.1 GW of live datacenter capacity</b> as of ${fmtDateLong(ASOF)}, a Gross Domestic Compute of $55B, with no domestic energy resource ceiling to speak of. It is an incumbent: already running significant compute, already priced in, ranked ${c.rank} of 108 by unlockable value because there is nothing left to unlock at home.`;
  return `<b>${esc(c.name)} runs about ${fmtGW(c.liveGW)} of live datacenter capacity</b> as of ${fmtDateLong(ASOF)}, a Gross Domestic Compute of ${fmtB(c.gdc)}${c.gdcEst?" (an estimate)":""}. Its identified energy resource could host about ${c.ceilGW} GW of AI compute, a ceiling worth ${fmtRange(c)} at today's price of a gigawatt, about ${c.xgdp} times its $${num(c.gdp)}B GDP. The bankable slice today, discounted mainly for ${esc(c.disc)}, is ${fmtB(c.unlock)}, or $${num(c.perPerson)} per person. ${esc(c.name)} is ${tierPlain(c)}, ranked ${c.rank} of 108 countries by unlockable value.`;
}
function countryPage(c){
  const root = "../../", url = SITE+"/country/"+c.slug+"/";
  const title = `${c.name} compute capacity (${monYear(ASOF)}): ${fmtGW(c.liveGW)} live, ${c.ceilGW} GW ceiling | compute.world`;
  let description = `${c.name} runs about ${fmtGW(c.liveGW)} of live datacenter capacity as of ${fmtDate(ASOF)}, against an identified ceiling of ${c.ceilGW} GW worth ${fmtRange(c)}. Rank ${c.rank} of 108 by unlockable value; ${TIER[c.tier].toLowerCase()}.`;
  if(description.length>158) description = description.slice(0,155).replace(/[,;: ]+\S*$/,"")+"…";
  const peers = COUNTRIES.filter(x=>x.region===c.region).sort((a,b)=>a.rank-b.rank);
  const regionRank = peers.findIndex(x=>x.id===c.id)+1;
  const projects = PRECEDENTS.filter(p=>p[0]===c.id);
  const sorted = [...COUNTRIES].sort((a,b)=>a.rank-b.rank); const idx = sorted.findIndex(x=>x.id===c.id); const prev = sorted[idx-1], next = sorted[idx+1];
  const d = c.rz - c.rz0;
  const faqs = [
    [`How much data center capacity does ${c.name} have?`, `${c.name} runs about ${fmtGW(c.liveGW)} of live datacenter IT capacity as of ${fmtDate(ASOF)}${c.gdcEst?", an estimate: country totals below the top 35 markets are estimated":", compiled from SemiAnalysis, Cushman & Wakefield, Rystad, Knight Frank and national reports"}. Valued at $50B per gigawatt, that is a Gross Domestic Compute of ${fmtB(c.gdc)}.`],
    [`What is ${c.name}'s compute net worth?`, c.ceilHi===0 ? `${c.name} has no meaningful domestic energy resource ceiling, so its compute net worth is counted entirely in what it already runs: ${fmtB(c.gdc)} of live compute.` : `The ceiling is ${fmtRange(c)}: ${c.ceilGW} GW of identified hydro, geothermal, solar, wind and surplus fossil resource valued at $60 to 80B per gigawatt, NVIDIA's all-in figure for an AI factory. That is ${c.xgdp} times ${c.name}'s $${num(c.gdp)}B GDP. The bankable slice today, after a readiness discount of ${Math.round(c.readiness*100)}%, is ${fmtB(c.unlock)}.`],
    [`What holds ${c.name} back from converting its energy into compute?`, `Readiness scores ${Math.round(c.readiness*100)}% on an eight-part discount stack (governance, stability, GPU access, grid, fiber, momentum, physical conditions and capital access). For ${c.name} the binding discounts are ${c.disc}. It has built ${c.built}% of its ceiling as generating capacity, and its conversion score is ${c.rz} of 100${d?` (${d>0?"+":""}${d} since 19 August)`:""}.`],
    [`How does ${c.name} compare with its neighbours?`, `${c.name} ranks ${c.rank} of 108 countries by unlockable value, and ${regionRank} of ${peers.length} in ${c.region}. The regional leader is ${peers[0].name} at ${fmtB(peers[0].unlock)} unlockable and ${fmtB(peers[0].gdc)} of live compute.`]
  ];
  const jsonld = {"@context":"https://schema.org","@graph":[
    {"@type":"WebPage","@id":url,"url":url,"name":title,"description":description,"datePublished":"2026-08-10","dateModified":ASOF,"isPartOf":{"@id":SITE+"/#website"},"about":{"@id":url+"#place"},"breadcrumb":{"@id":url+"#crumbs"},"inLanguage":"en"},
    {"@type":"BreadcrumbList","@id":url+"#crumbs","itemListElement":[{"@type":"ListItem","position":1,"name":"compute.world","item":SITE+"/"},{"@type":"ListItem","position":2,"name":"Countries","item":SITE+"/#countries"},{"@type":"ListItem","position":3,"name":c.name,"item":url}]},
    {"@type":"Country","@id":url+"#place","name":c.name,"sameAs":[c.wiki]},
    {"@type":"Dataset","name":`${c.name} compute capacity and compute net worth`,"description":description,"url":url,"isPartOf":{"@id":SITE+"/#cnw"},"creator":{"@id":SITE+"/#org"},"dateModified":ASOF,"license":"https://github.com/pchamal/compute-world/blob/main/LICENSE.md","isAccessibleForFree":true,"spatialCoverage":{"@type":"Country","name":c.name},"variableMeasured":[
      {"@type":"PropertyValue","name":"Live datacenter IT capacity","value":c.liveGW,"unitText":"GW"},{"@type":"PropertyValue","name":"Gross Domestic Compute","value":c.gdc,"unitText":"USD billions"},{"@type":"PropertyValue","name":"Resource ceiling","value":c.ceilGW,"unitText":"GW"},{"@type":"PropertyValue","name":"CNW ceiling, high end","value":c.ceilHi,"unitText":"USD trillions"},{"@type":"PropertyValue","name":"CNW unlockable","value":c.unlock,"unitText":"USD billions"},{"@type":"PropertyValue","name":"Readiness","value":c.readiness},{"@type":"PropertyValue","name":"Conversion score","value":c.rz},{"@type":"PropertyValue","name":"Rank by unlockable value","value":c.rank}],
      "distribution":[{"@type":"DataDownload","encodingFormat":"application/json","contentUrl":SITE+"/data.json"}]},
    {"@type":"FAQPage","mainEntity":faqs.map(([q,a])=>({"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}}))}
  ]};
  const kv = [
    ["Live datacenter capacity", fmtGW(c.liveGW), c.gdcEst?"IT capacity, mid-2026. Estimate: below the top 35 markets.":"IT capacity, mid-2026, compiled from industry and national sources."],
    ["Live compute (GDC)", fmtB(c.gdc), "Live GW × $50B, the central price of an AI factory."],
    ["Resource ceiling", c.ceilGW+" GW", "Identified hydro, geothermal, solar, wind and surplus fossil resource."],
    ["Ceiling value", fmtRange(c), "Ceiling GW × $60 to 80B per GW, NVIDIA's all-in figure."],
    ["Ceiling as a multiple of GDP", c.xgdp+"×", `High end over nominal GDP of $${num(c.gdp)}B (IMF).`],
    ["Unlockable value", fmtB(c.unlock), "Firm untapped GW × $50B × readiness. The bankable slice."],
    ["Unlockable per person", "$"+num(c.perPerson), "IMF population, 2026."],
    ["Built", c.built+"%", "Hydro and geothermal already installed, over the ceiling."],
    ["Readiness", Math.round(c.readiness*100)+"%", `Eight-part discount. Binding: ${c.disc}.`],
    ["Conversion score", String(c.rz), `0 to 100. ${d?(d>0?"+":"")+d+" since 19 Aug.":"Unchanged since 19 Aug."}`],
    ["Tier", TIER[c.tier], TIER_DEF[c.tier]],
    ["Rank", `${c.rank} of 108`, `By unlockable value. ${regionRank} of ${peers.length} in ${c.region}.`]
  ];
  const body = `
<body>
${masthead(root)}
<main><div class="wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="${root}index.html">compute.world</a><span>›</span><a href="${root}index.html#board">Countries</a><span>›</span><span>${esc(c.name)}</span></nav>
<article class="article">
  <p class="kicker" style="margin-top:18px">Country profile · Rank ${c.rank} of 108 · <span class="tier tier-${c.tier}">${TIER[c.tier]}</span></p>
  <div class="title">${flagImg(c, root, "xl")}<h1>${esc(c.name)} compute capacity</h1></div>
  <p class="answer">${answerText(c)}</p>
  <div class="meta"><span>Updated ${fmtDate(ASOF)}</span><span>·</span><a href="#cite">Cite this page</a><span>·</span><a href="${SITE}/data.json">Data</a><span>·</span><a href="${c.wiki}" rel="noopener">${esc(c.name)} on Wikipedia</a></div>

  <h2>Key numbers</h2>
  <table class="kv"><tbody>${kv.map(r=>`<tr><th scope="row">${esc(r[0])}</th><td class="v${r[0].startsWith("Live")&&c.gdcEst?' est':''}">${esc(r[1])}</td><td class="d">${esc(r[2])}</td></tr>`).join("")}</tbody></table>

  <h2>Three numbers, one scale</h2>
  <p class="small">Ceiling is what the endowment could host; unlockable is the slice underwriters would sign today; live compute is what runs. Drawn on one linear scale on purpose: the gap is the point.</p>
  ${threeBars(c)}

  ${c.signal ? `<h2>Latest signal</h2><div class="signal ${c.dir}"><span class="dot"></span><div>${esc(c.signal)}<span class="m">Arrows mark direction from recent items on the Wire.</span></div></div>` : ""}

  <h2>Projects on the ground</h2>
  ${projects.length ? `<table class="peers"><thead><tr><th>Project</th><th>Scale</th><th>Status</th><th class="r">Date</th></tr></thead><tbody>${projects.map(p=>`<tr><td>${esc(p[1])}</td><td>${esc(p[2])}</td><td><span class="status ${p[3]}">${p[3]}</span></td><td class="r">${esc(p[4])}</td></tr>`).join("")}</tbody></table>` : `<p class="small">No sovereign AI factory for ${esc(c.name)} is on the register yet. Announcements, contracts and stalls are tracked as reported; <a href="${SITE}/contact.html">send one to the desk</a>.</p>`}

  <h2>${esc(c.region)}: how ${esc(c.name)} compares</h2>
  <table class="peers"><thead><tr><th>#</th><th>Country</th><th class="r">Unlockable</th><th class="r">Live compute</th><th class="r">Readiness</th><th>Tier</th></tr></thead><tbody>${peers.map(x=>`<tr${x.id===c.id?' class="me"':''}><td>${x.rank}</td><td><span class="who">${flagImg(x, root)}<a href="${root}country/${x.slug}/">${esc(x.name)}</a></span></td><td class="r">${fmtB(x.unlock)}</td><td class="r${x.gdcEst?' est':''}">${fmtB(x.gdc)}</td><td class="r">${Math.round(x.readiness*100)}%</td><td><span class="tier tier-${x.tier}">${TIER[x.tier]}</span></td></tr>`).join("")}</tbody></table>

  <h2>What compute costs right now</h2>
  <p class="small">The price of the silicon a country would host, from the tape. Labeled buy-now prints from named venues.</p>
  <div class="pricestrip">${["nvidia-h100-sxm-80gb","nvidia-b200-sxm6","nvidia-a100-sxm-80gb"].map(id=>{ const s=CHIPS.find(x=>x.id===id); return `<a href="${root}silicon/${s.slug}/">${logoEl(s.vendor,"lg")}<span><b>${esc(s.name)} ${fmtUSD(s.disp.usd)}/hr</b><small>${esc(s.disp.venue)}, ${esc(s.disp.term)}, ${fmtDate(s.disp.asOf)}</small></span></a>`; }).join("")}</div>

  <h2>Questions people ask</h2>
  <div class="faq">${faqs.map(([q,a])=>`<details><summary>${esc(q)}</summary><p>${esc(a)}</p></details>`).join("")}</div>

  <h2 id="cite">Cite this page</h2>
  <div class="cite"><div class="codebox" id="citeBox">Hamal, P. (2026). The Compute Net Worth Index: ${esc(c.name)}. compute.world. ${url} Retrieved ${fmtDate(ASOF)}.</div><button class="btn primary" data-copy="#citeBox">Copy citation</button></div>
  <p class="small" style="margin-top:12px">Free with attribution for research, journalism and personal use. Method, sources and every parameter: <a href="${root}index.html#method">how the numbers are made</a>.</p>

  <nav class="nextprev" aria-label="Neighbouring ranks">${prev?`<a href="${root}country/${prev.slug}/">${flagImg(prev,root)}<span><small>Rank ${prev.rank}</small><b>${esc(prev.name)}</b></span></a>`:'<span></span>'}${next?`<a class="next" href="${root}country/${next.slug}/"><span><small>Rank ${next.rank}</small><b>${esc(next.name)}</b></span>${flagImg(next,root)}</a>`:''}</nav>
</article>
</div></main>
${footer()}
${tinyJs}
</body>
</html>`;
  return head({title, description, canonical:url, root, ogType:"article", jsonld, image:SITE+"/og/country/"+c.slug+".png"}) + body;
}

/* ---------- chip pages ---------- */
function pathChart(s){
  const key = Object.keys(PRICE_PATHS).find(k=>k.split(" ")[0]===s.name.split(" ")[0]);
  const series = key ? PRICE_PATHS[key].map(x=>({...x, short:x.name.split(",")[0]})) : (s.spark.length ? [{name:s.disp.venue+" "+s.disp.term, short:s.disp.venue, pts:s.spark}] : []);
  if(!series.length) return "";
  const W=720,H=240,L=44,R=120,T=14,B=28;
  const all = series.flatMap(x=>x.pts); const xs = all.map(p=>dateNum(p[0])); const x0 = Math.min(...xs), x1 = dateNum(ASOF);
  const yMax = Math.max(1, Math.ceil(Math.max(...all.map(p=>p[1]))/2)*2);
  const sx = iso => L + (dateNum(iso)-x0)/Math.max(1,(x1-x0))*(W-L-R);
  const sy = v => T + (H-T-B) - v/yMax*(H-T-B);
  const cols = ["#1F4FD8","#9B2C2C","#1E7B4F","#8A5A12"];
  let g = `<g class="frame"><line x1="${sx(new Date(x0).toISOString().slice(0,10))}" x2="${sx(ASOF)}" y1="${sy(0)}" y2="${sy(0)}"/><line x1="${L}" x2="${L}" y1="${sy(0)}" y2="${sy(yMax)}"/></g><g class="tick">`;
  [0,yMax/2,yMax].forEach(v=>{ g += `<text x="${L-8}" y="${(sy(v)+4).toFixed(1)}" text-anchor="end">$${v}</text>`; });
  for(let yy=new Date(x0).getUTCFullYear(); yy<=new Date(x1).getUTCFullYear(); yy++){ const iso=yy+"-01-01"; if(dateNum(iso)>=x0&&dateNum(iso)<=x1) g += `<text x="${sx(iso).toFixed(1)}" y="${sy(0)+17}" text-anchor="middle">${yy}</text>`; }
  g += `</g><g class="series">`; const labels=[];
  series.forEach((sr,i)=>{ const col=cols[i%cols.length]; let d=""; sr.pts.forEach((p,j)=>{ const x=sx(p[0]),y=sy(p[1]); d += j===0?`M${x.toFixed(1)},${y.toFixed(1)}`:` H${x.toFixed(1)} V${y.toFixed(1)}`; }); if(!sr.stale) d += ` H${sx(ASOF).toFixed(1)}`;
    g += `<path d="${d}" stroke="${col}"${sr.stale?' stroke-dasharray="4 3"':''}/>`; sr.pts.forEach(p=>{ g += `<circle cx="${sx(p[0]).toFixed(1)}" cy="${sy(p[1]).toFixed(1)}" r="3" stroke="${col}"/>`; });
    const last = sr.pts[sr.pts.length-1]; labels.push({x: (sr.stale?sx(last[0]):sx(ASOF))+8, y:sy(last[1]), t:`${fmtUSD(last[1])} ${sr.short}${sr.stale?" (ended)":""}`, col}); });
  labels.sort((a,b)=>a.y-b.y); for(let i=1;i<labels.length;i++){ if(labels[i].y-labels[i-1].y<14) labels[i].y=labels[i-1].y+14; }
  labels.forEach(l=>{ g += `<text class="lbl" x="${l.x.toFixed(1)}" y="${(l.y+4).toFixed(1)}" fill="${l.col}">${esc(l.t)}</text>`; });
  g += `</g>`;
  return `<div class="pathchart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(s.name)} price per GPU-hour over dated prints">${g}</svg><p class="note" style="margin:10px 0 0">${esc(key ? PRICE_CAPTIONS[key] : "Dated prints only; the flat line is the list holding, not an assumption.")}</p></div>`;
}
function chipPage(s){
  const root = "../../", url = SITE+"/silicon/"+s.slug+"/";
  const priceStr = s.disp.usd==null ? "token pricing" : (s.disp.cny ? `¥${s.disp.cny.toFixed(2)} (about ${fmtUSD(s.disp.usd)})` : fmtUSD(s.disp.usd));
  const title = s.disp.usd==null ? `${s.name} pricing (${monYear(ASOF)}): token API, no public chip-hour | compute.world` : `${s.name} rental price (${monYear(ASOF)}): ${priceStr}/hr ${s.disp.term} at ${s.disp.venue} | compute.world`;
  let description = s.disp.usd==null ? `${s.vendor} ${s.name} is sold as tokens, not chip-hours. ${s.disp.cfg}. What the tape can and cannot show, as of ${fmtDate(ASOF)}.` : `${s.vendor} ${s.name} rents for ${priceStr} per GPU-hour ${s.disp.term} at ${s.disp.venue} as of ${fmtDate(ASOF)}. Every sourced quote by venue and term, dated history, availability.`;
  if(description.length>158) description = description.slice(0,155).replace(/[,;: ]+\S*$/,"")+"…";
  const others = CHIPS.filter(x=>x.id!==s.id).sort((a,b)=>a.rank-b.rank);
  const sorted = [...CHIPS].sort((a,b)=>a.rank-b.rank); const idx = sorted.findIndex(x=>x.id===s.id); const prev = sorted[idx-1], next = sorted[idx+1];
  const q=s.chg.q, y=s.chg.y;
  const alt = s.quotes.filter(qq=>qq[2]!=null).slice(1,4).map(qq=>`${fmtUSD(qq[2])} ${qq[1]} at ${qq[0]}`).join(", ");
  const faqs = [
    [`How much does ${s.name} cost per hour?`, s.disp.usd==null ? `${s.vendor} does not publish a public accelerator-hour for the ${s.name}. ${s.disp.cfg}. Aggregator chip-hour ranges are omitted on purpose.` : `${priceStr} per GPU-hour ${s.disp.term} at ${s.disp.venue} as of ${fmtDate(ASOF)}${s.disp.cfg?` (${s.disp.cfg})`:""}.${alt?` Other sourced prints: ${alt}.`:""}`],
    [`Why do ${s.name} prices differ so much between clouds?`, `Because the terms differ. On-demand is a list price with no commitment; spot is interruptible and priced to fill idle capacity; reserved and one-year contracts trade a commitment for a lower rate; AWS Capacity Blocks are scheduled reservations, not on-demand. Hyperscaler list prices also run well above neocloud lists. The tape never averages these: each print carries its venue, term and date.`],
    [`Has the ${s.name} price gone up or down?`, [q.pct!=null?`Over one quarter, ${s.disp.venue} ${s.disp.term} moved ${q.pct>0?"+":""}${q.pct.toFixed(1)}% (${fmtUSD(q.then)} on ${fmtDate(q.thenDate)} to ${fmtUSD(s.disp.usd)}).`:`No dated same-venue pair exists for a one-quarter change, so none is printed.`, y.pct!=null?`Over one year: ${y.pct>0?"+":""}${y.pct.toFixed(1)}%.`:``, s.first&&s.disp.usd!=null?`Since the first print on the tape (${fmtUSD(s.first.price)} on ${fmtDate(s.first.date)}) the display price is ${pct(s.disp.usd,s.first.price)>=0?"up":"down"} ${Math.abs(pct(s.disp.usd,s.first.price))}%.`:``].filter(Boolean).join(" ")],
    [`Is the ${s.name} available to rent right now?`, s.avail]
  ];
  const jsonld = {"@context":"https://schema.org","@graph":[
    {"@type":"WebPage","@id":url,"url":url,"name":title,"description":description,"datePublished":"2026-08-10","dateModified":ASOF,"isPartOf":{"@id":SITE+"/#website"},"breadcrumb":{"@id":url+"#crumbs"},"inLanguage":"en"},
    {"@type":"BreadcrumbList","@id":url+"#crumbs","itemListElement":[{"@type":"ListItem","position":1,"name":"compute.world","item":SITE+"/"},{"@type":"ListItem","position":2,"name":"Silicon prices","item":SITE+"/#silicon"},{"@type":"ListItem","position":3,"name":s.name,"item":url}]},
    {"@type":"Dataset","name":`${s.name} rental price history`,"description":description,"url":url,"isPartOf":{"@id":SITE+"/#silicon"},"creator":{"@id":SITE+"/#org"},"dateModified":ASOF,"license":"https://creativecommons.org/licenses/by/4.0/","isAccessibleForFree":true,"variableMeasured":[{"@type":"PropertyValue","name":"Rental price, buy-now","value":s.disp.usd,"unitText":"USD per GPU-hour"},{"@type":"PropertyValue","name":"Tape rank","value":s.rank}],"distribution":[{"@type":"DataDownload","encodingFormat":"application/json","contentUrl":SITE+"/silicon.json"},{"@type":"DataDownload","encodingFormat":"application/json","contentUrl":SITE+"/silicon-history.json"}]},
    {"@type":"FAQPage","mainEntity":faqs.map(([qq,a])=>({"@type":"Question","name":qq,"acceptedAnswer":{"@type":"Answer","text":a}}))}
  ]};
  const kv = [
    ["Buy-now price", priceStr+(s.disp.usd==null?"":" per GPU-hour"), `${s.disp.venue}, ${s.disp.term}${s.disp.cfg?", "+s.disp.cfg:""}. As of ${fmtDate(ASOF)}.`],
    s.terms.y1 ? ["1-year term book", fmtUSD(s.terms.y1.price), `${s.terms.y1.venue}, ${s.terms.y1.label}.`] : null,
    s.terms.y3 ? ["3-year term book", fmtUSD(s.terms.y3.price), `${s.terms.y3.venue}, ${s.terms.y3.label}.`] : null,
    ["Change, 1 quarter", q.pct!=null?(q.pct>0?"+":"")+q.pct.toFixed(1)+"%":"—", q.pct!=null?`${s.disp.venue} ${fmtUSD(q.then)} on ${fmtDate(q.thenDate)} to ${fmtUSD(s.disp.usd)}.`:q.note],
    ["Change, 1 year", y.pct!=null?(y.pct>0?"+":"")+y.pct.toFixed(1)+"%":"—", y.pct!=null?`${s.disp.venue} ${fmtUSD(y.then)} on ${fmtDate(y.thenDate)} to ${fmtUSD(s.disp.usd)}.`:y.note],
    s.first&&s.disp.usd!=null ? ["Since first print", (pct(s.disp.usd,s.first.price)>=0?"+":"")+pct(s.disp.usd,s.first.price)+"%", `${fmtUSD(s.first.price)} on ${fmtDate(s.first.date)}.`] : null,
    ["Availability", s.scar, s.avail],
    ["Memory", s.mem, ""],
    ["Tape rank", `${s.rank} of ${CHIPS.length}`, `Score ${s.score.toFixed(2)}: liquidity ${s.liq}, demand ${s.dem}, frontier ${s.fr}, each 0 to 3. Ordinal hygiene, not a valuation.`]
  ].filter(Boolean);
  const body = `
<body>
${masthead(root)}
<main><div class="wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="${root}index.html">compute.world</a><span>›</span><a href="${root}index.html#silicon">Silicon prices</a><span>›</span><span>${esc(s.name)}</span></nav>
<article class="article">
  <p class="kicker" style="margin-top:18px">Accelerator · Tape rank ${s.rank} of ${CHIPS.length} · ${esc(s.vendor)}</p>
  <div class="title">${logoEl(s.vendor,"xl")}<h1>${esc(s.name)} ${s.disp.usd==null?"pricing":"rental price"}</h1></div>
  <p class="answer">${s.disp.usd==null ? `<b>The ${esc(s.vendor)} ${esc(s.name)} is sold as tokens, not chip-hours.</b> ${esc(s.disp.cfg)}. The tape shows no dollars per hour because none is published, and it will not invent one from a token price.` : `<b>The ${esc(s.vendor)} ${esc(s.name)} rents for ${esc(priceStr)} per GPU-hour</b> ${esc(s.disp.term)} at ${esc(s.disp.venue)} as of ${fmtDateLong(s.disp.asOf)}${s.disp.cfg?` (${esc(s.disp.cfg)})`:""}.${alt?` Other sourced prints: ${esc(alt)}.`:""} ${esc(s.scar)}.`}</p>
  <div class="meta"><span>Updated ${fmtDate(ASOF)}</span><span>·</span><a href="#cite">Cite this page</a><span>·</span><a href="${SITE}/silicon.json">Data</a><span>·</span><a href="${SITE}/silicon.html">Full tape</a></div>

  <h2>Key numbers</h2>
  <table class="kv"><tbody>${kv.map(r=>`<tr><th scope="row">${esc(r[0])}</th><td class="v">${esc(r[1])}</td><td class="d">${esc(r[2])}</td></tr>`).join("")}</tbody></table>

  <h2>Every sourced quote</h2>
  <p class="small">Venue, term, price, date. The highlighted row is the display print: the most liquid public on-demand list, or a labeled spot print where on-demand is contact-sales.</p>
  <table class="quotes"><thead><tr><th>Venue</th><th>Term</th><th class="r">$ per hour</th><th>As of</th><th>Note</th></tr></thead><tbody>${s.quotes.map((qq,i)=>{ const u=VENUE_URL[qq[0]]; const v = u?`<a href="${esc(u)}" rel="noopener">${venueEl(qq[0])}</a>`:venueEl(qq[0]); const stale=/stale/i.test(qq[4]||"")||/SemiAnalysis/.test(qq[0]); return `<tr${i===0?' class="lead"':''}><td>${v}</td><td>${esc(qq[1])}</td><td class="r price${stale?' stale':''}">${qq[2]==null?'<span class="dash">—</span>':fmtUSD(qq[2])}</td><td>${fmtDate(qq[3])}</td><td class="note tiny">${esc(qq[4]||"")}</td></tr>`; }).join("")}</tbody></table>

  ${pathChart(s) ? `<h2>Price path</h2><p class="small">Steps, not candles. Each dot is a dated print; the line carries the last print forward until the next one. A dashed line is a series that stopped publishing.</p>${pathChart(s)}` : ""}

  ${s.cannot.length ? `<h2>What this page refuses to show</h2><ul class="note" style="padding-left:20px;font-size:15px">${s.cannot.map(x=>`<li style="margin:6px 0">${esc(x)}</li>`).join("")}</ul>` : ""}

  <h2>Questions people ask</h2>
  <div class="faq">${faqs.map(([qq,a])=>`<details><summary>${esc(qq)}</summary><p>${esc(a)}</p></details>`).join("")}</div>

  <h2>Other accelerators on the tape</h2>
  <div class="pricestrip">${others.slice(0,6).map(x=>`<a href="${root}silicon/${x.slug}/">${logoEl(x.vendor,"lg")}<span><b>${esc(x.name)} ${x.disp.usd==null?"":fmtUSD(x.disp.usd)+"/hr"}</b><small>${esc(x.disp.venue)}, ${esc(x.disp.term)}</small></span></a>`).join("")}</div>

  <h2 id="cite">Cite this page</h2>
  <div class="cite"><div class="codebox" id="citeBox">Hamal, P. (2026). The Silicon Tape: ${esc(s.name)}. compute.world. ${url} Retrieved ${fmtDate(ASOF)}.</div><button class="btn primary" data-copy="#citeBox">Copy citation</button></div>
  <p class="small" style="margin-top:12px">CC BY 4.0 with attribution to compute.world. Vendor names and marks belong to their owners and identify the source of each quote.</p>

  <nav class="nextprev" aria-label="Neighbouring ranks">${prev?`<a href="${root}silicon/${prev.slug}/">${logoEl(prev.vendor)}<span><small>Rank ${prev.rank}</small><b>${esc(prev.name)}</b></span></a>`:'<span></span>'}${next?`<a class="next" href="${root}silicon/${next.slug}/"><span><small>Rank ${next.rank}</small><b>${esc(next.name)}</b></span>${logoEl(next.vendor)}</a>`:''}</nav>
</article>
</div></main>
${footer()}
${tinyJs}
</body>
</html>`;
  return head({title, description, canonical:url, root, ogType:"article", jsonld, image:SITE+"/og/silicon/"+s.slug+".png"}) + body;
}

/* ---------- discovery files ---------- */
function sitemap(){
  const urls = [[SITE+"/", "1.0"], ...COUNTRIES.map(c=>[SITE+"/country/"+c.slug+"/", "0.8"]), ...CHIPS.map(s=>[SITE+"/silicon/"+s.slug+"/", "0.8"])];
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.map(([u,p])=>`  <url><loc>${u}</loc><lastmod>${ASOF}</lastmod><changefreq>daily</changefreq><priority>${p}</priority></url>`).join("\n")}\n</urlset>\n`;
}
const robots = `# compute.world — the index is built to be cited. Crawl it.
User-agent: *
Allow: /

# AI and answer engines, explicitly welcome
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: anthropic-ai
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: Applebot-Extended
Allow: /
User-agent: CCBot
Allow: /

Sitemap: ${SITE}/sitemap.xml
`;
function llms(){
  const top = [...COUNTRIES].sort((a,b)=>a.rank-b.rank);
  return `# compute.world

> Countries. Compute. Silicon. The world's compute index: 108 countries priced by compute net worth, 20 AI accelerators with sourced rental prices. Updated weekdays. Snapshot ${ASOF}.

## Definitions
- Ceiling: resource ceiling (GW) × $60 to 80B per GW. What a country's identified energy could host, at today's price of a gigawatt.
- Unlockable: firm untapped GW × $50B × readiness. The bankable slice.
- Live compute (Gross Domestic Compute, GDC): live datacenter GW × $50B. What actually runs.
- Readiness: eight-part discount (governance 18, GPU access 14, physical 14, stability 13, grid 11, fiber 11, capital access 11, momentum 8).
- Conversion score: 0 to 100; moves with public signals. Rank is by unlockable value.
- Price tape rule: every price carries venue, term and date; missing numbers are dashes; change needs two dated same-venue prints.

## Cite
Hamal, P. (2026). The Compute Net Worth Index. compute.world. Free with attribution for research and press.

## Data
- ${SITE}/data.json (countries)
- ${SITE}/silicon.json (prices), ${SITE}/silicon-history.json (dated prints)
- ${SITE}/rank-history.json (append-only daily snapshots)
- ${SITE}/params.json (every assumption)

## Country pages (live capacity, ceiling, unlockable, rank)
${top.map(c=>`- [${c.name}](${SITE}/country/${c.slug}/): ${fmtGW(c.liveGW)} live, ${c.ceilGW} GW ceiling (${fmtRange(c)}), unlockable ${fmtB(c.unlock)}, rank ${c.rank}, ${TIER[c.tier]}`).join("\n")}

## Accelerator pages (buy-now price, venue, term, date)
${[...CHIPS].sort((a,b)=>a.rank-b.rank).map(s=>`- [${s.name}](${SITE}/silicon/${s.slug}/): ${s.disp.usd==null?"token pricing, no chip-hour":fmtUSD(s.disp.usd)+" per GPU-hour, "+s.disp.venue+" "+s.disp.term+", "+s.disp.asOf}`).join("\n")}
`;
}

/* ---------- run ---------- */
fs.rmSync(DIST, {recursive:true, force:true}); fs.mkdirSync(DIST, {recursive:true});
const mapSvg = buildMap();
write("index.html", homepage(mapSvg));
COUNTRIES.forEach(c => write(`country/${c.slug}/index.html`, countryPage(c)));
CHIPS.forEach(s => write(`silicon/${s.slug}/index.html`, chipPage(s)));
write("sitemap.xml", sitemap()); write("robots.txt", robots); write("llms.txt", llms());
write("data.json", JSON.stringify({as_of:ASOF, countries:COUNTRIES, chips:CHIPS, precedents:PRECEDENTS}, null, 1));
write("map.svg", mapSvg);
fs.mkdirSync(path.join(DIST,"fonts"), {recursive:true});
for(const f of fs.readdirSync(path.join(SRC,"fonts")).filter(f=>f.endsWith(".woff2"))) fs.copyFileSync(path.join(SRC,"fonts",f), path.join(DIST,"fonts",f));
fs.mkdirSync(path.join(DIST,"flags"), {recursive:true});
for(const iso of [...new Set(COUNTRIES.map(c=>c.flag).concat(["eu"]))]) fs.copyFileSync(path.join(VENDOR,"flag-icons","flags","4x3",iso+".svg"), path.join(DIST,"flags",iso+".svg"));
fs.copyFileSync(path.join(VENDOR,"flag-icons","LICENSE"), path.join(DIST,"flags","LICENSE"));
const count = (dir) => fs.readdirSync(dir,{withFileTypes:true}).reduce((n,e)=> n + (e.isDirectory()? count(path.join(dir,e.name)) : 1), 0);
console.log("built", count(DIST), "files;", "index.html", (fs.statSync(path.join(DIST,"index.html")).size/1024).toFixed(0)+"KB;", "map", (mapSvg.length/1024).toFixed(0)+"KB");
