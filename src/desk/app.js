/* compute.world — homepage app. DATA is injected at build time. */
(function(){
"use strict";
const ROOT = "";
const CFG = DATA.config, COUNTRIES = DATA.countries, CHIPS = DATA.chips, TIER = DATA.tier, TIER_DEF = DATA.tierDef;
const $ = (s, el=document) => el.querySelector(s);
const $$ = (s, el=document) => Array.from(el.querySelectorAll(s));
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const fmtDate = iso => { if(!iso) return ""; const p = iso.split("-"); if(p.length===2) return MONTHS[+p[1]-1]+" "+p[0]; return (+p[2])+" "+MONTHS[+p[1]-1]+" "+p[0]; };
const fmtDateShort = iso => { const p = iso.split("-"); return (+p[2])+" "+MONTHS[+p[1]-1]; };
const num = n => Number(n).toLocaleString("en-US");
const fmtB = b => b >= 1000 ? "$"+(b/1000).toFixed(1)+"T" : b >= 10 ? "$"+Math.round(b)+"B" : b >= 1 ? "$"+(+b.toFixed(1))+"B" : "under $1B";
const fmtT = t => t >= 1 ? "$"+t+"T" : "$"+Math.round(t*1000)+"B";
const fmtRange = c => c.ceilHi === 0 ? "$0" : (c.ceilLo >= 1 ? "$"+c.ceilLo+" to "+c.ceilHi+"T" : fmtT(c.ceilLo)+" to "+fmtT(c.ceilHi));
const fmtGW = gw => gw >= 1 ? gw.toFixed(1)+" GW" : Math.round(gw*1000)+" MW";
const fmtUSD = v => v == null ? "—" : "$"+(Math.round(v*100)/100).toFixed(2);
const pct = (a,b) => b ? Math.round((a-b)/b*100) : 0;
const dateNum = iso => new Date(iso+"T00:00:00Z").getTime();
const cssVar = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const palette = () => ["--s1","--s2","--s3","--s4","--s5","--s6","--s7","--s8"].map(cssVar);
const VENDOR_CODE = {NVIDIA:"NV", AMD:"AMD", Google:"G", Huawei:"HW", Cerebras:"CB", Amazon:"AWS", Groq:"GQ"};

[...COUNTRIES].sort((a,b)=>b.gdc-a.gdc).forEach((c,i)=>{ c.gdcEst = i >= 35; });
const byId = Object.fromEntries(COUNTRIES.map(c=>[c.id,c]));
const chipById = Object.fromEntries(CHIPS.map(s=>[s.id,s]));

/* brand assets */
window.flagFail = img => { const s=document.createElement("span"); s.className="code"; s.textContent=img.dataset.code||""; img.replaceWith(s); };
window.logoFail = img => { img.parentElement.classList.add("fallback"); };
const flag = (c, cls="") => '<img class="flag '+cls+'" src="'+ROOT+'flags/'+c.flag+'.svg" alt="" width="24" height="18" loading="lazy" data-code="'+c.iso2+'" onerror="flagFail(this)">';
const logo = (name, cls="") => { const d = DATA.domains[name]; const ini = VENDOR_CODE[name] || name.replace(/[^A-Z0-9]/g,"").slice(0,3) || name.slice(0,2).toUpperCase(); return '<span class="logo '+cls+'" title="'+esc(name)+'">'+(d?'<img src="https://www.google.com/s2/favicons?domain='+d+'&sz=64" alt="" loading="lazy" onerror="logoFail(this)">':'')+'<span>'+esc(ini)+'</span></span>'; };
const venue = name => '<span class="venue">'+logo(name)+'<span>'+esc(name)+'</span></span>';

/* state */
const state = { tab:"countries", view:"list", lens:{countries:"unlock", silicon:"rank"}, topn:"10", open:null, status:"All", region:"All", q:"", rzSel:null, rzIdx:DATA.snapshotDates.length-1 };

/* lenses */
function priceStr(s){ if(s.disp.usd==null) return "token"; if(s.disp.cny) return "¥"+s.disp.cny.toFixed(2); return fmtUSD(s.disp.usd); }
function priceSub(s){ if(s.disp.usd==null) return s.disp.venue+", "+s.disp.term; if(s.disp.cny) return "about "+fmtUSD(s.disp.usd)+", "+s.disp.venue; return s.disp.venue+", "+s.disp.term+", "+fmtDateShort(s.disp.asOf); }
const LENS = {
  countries: {
    unlock:{ label:"Unlockable value", head:"Unlockable", key:c=>c.unlock, fmt:c=>fmtB(c.unlock), sub:()=>"Unlockable" },
    ceil:{ label:"Ceiling", head:"Ceiling, high", key:c=>c.ceilHi, fmt:c=>fmtT(c.ceilHi), sub:()=>"Ceiling, high end" },
    gdc:{ label:"Live compute", head:"Live compute", key:c=>c.gdc, fmt:c=>fmtB(c.gdc), sub:c=>c.gdcEst?"Live compute, estimate":"Live compute" },
    livegw:{ label:"Live capacity (GW)", head:"Live GW", key:c=>c.liveGW, fmt:c=>fmtGW(c.liveGW), sub:c=>c.gdcEst?"Datacenter capacity, estimate":"Datacenter capacity" },
    xgdp:{ label:"Ceiling as × GDP", head:"× GDP", key:c=>c.xgdp, fmt:c=>c.xgdp+"×", sub:()=>"Ceiling over GDP" },
    pp:{ label:"Unlockable per person", head:"Per person", key:c=>c.perPerson, fmt:c=>"$"+num(c.perPerson), sub:()=>"Unlockable per person" },
    rz:{ label:"Conversion score", head:"Conversion", key:c=>c.rz, fmt:c=>String(c.rz), sub:()=>"Conversion score, 0 to 100" },
    movers:{ label:"Movers since 19 Aug", head:"Change", key:c=>Math.abs(c.rz-c.rz0), filter:c=>c.rz!==c.rz0, fmt:c=>(c.rz>c.rz0?"+":"")+(c.rz-c.rz0), sub:c=>"Conversion "+c.rz0+" to "+c.rz },
    ready:{ label:"Readiness", head:"Readiness", key:c=>c.readiness, fmt:c=>Math.round(c.readiness*100)+"%", sub:()=>"Readiness" }
  },
  silicon: {
    rank:{ label:"Tape rank", head:"Buy-now price", key:s=>-s.rank, fmt:priceStr, sub:priceSub },
    price:{ label:"Priciest per hour", head:"Buy-now price", key:s=>s.disp.usd ?? -1, fmt:priceStr, sub:priceSub },
    cheap:{ label:"Cheapest per hour", head:"Buy-now price", key:s=>s.disp.usd == null ? -Infinity : -s.disp.usd, filter:s=>s.disp.usd!=null, fmt:priceStr, sub:priceSub },
    first:{ label:"Change since first print", head:"Since first print", key:s=>s.first&&s.disp.usd!=null?pct(s.disp.usd,s.first.price):-Infinity, filter:s=>s.first&&s.disp.usd!=null, fmt:s=>(pct(s.disp.usd,s.first.price)>=0?"+":"")+pct(s.disp.usd,s.first.price)+"%", sub:s=>"from "+fmtUSD(s.first.price)+" on "+fmtDate(s.first.date) }
  }
};

/* toast + clipboard */
let toastT;
function toast(msg){ const t=$("#toast"); t.textContent=msg; t.classList.add("show"); clearTimeout(toastT); toastT=setTimeout(()=>t.classList.remove("show"),1800); }
async function copy(text, label){ try{ await navigator.clipboard.writeText(text); toast(label||"Copied"); }catch(e){ const ta=document.createElement("textarea"); ta.value=text; document.body.appendChild(ta); ta.select(); try{document.execCommand("copy"); toast(label||"Copied");}catch(_){toast("Copy failed. Select the text and copy it by hand.");} ta.remove(); } }

/* links + text */
const pageFor = (type,obj) => CFG.site+"/"+(type==="country"?"country/":"silicon/")+obj.slug+"/";
const citeFor = (name, url) => "Hamal, P. (2026). The Compute Net Worth Index"+(name?": "+name:"")+". compute.world · Compute Net Worth Index. "+(url||CFG.site+"/")+" As of "+fmtDate(CFG.asOf)+".";
const xFor = (text,url) => "https://x.com/intent/post?text="+encodeURIComponent(text)+"&url="+encodeURIComponent(url);
function countryText(c){
  const tierLine = { SG:"A sleeping giant: the endowment runs "+c.xgdp+" times the economy, and the readiness gap is the to-do list.", PR:"Primed: readiness clears 65 percent, and there is real headroom left to build.", IN:"An incumbent: already priced in, already building.", EU:"Emerging upside: a narrower gap, and a real one.", LR:"A long road: the ceiling is modest next to the economy, and the option still costs nothing to hold." }[c.tier];
  if(c.id==="SGP") return "Singapore has no domestic resource ceiling to speak of and runs 1.1 GW of live datacenter capacity, a Gross Domestic Compute of $55B. An incumbent: already priced in, already building.";
  return c.name+" sits on a resource ceiling of roughly "+c.ceilGW+" GW, worth "+fmtRange(c)+" of AI compute at today's prices, about "+c.xgdp+" times its $"+num(c.gdp)+"B GDP. The bankable slice today is "+fmtB(c.unlock)+", which is $"+num(c.perPerson)+" for every citizen, discounted mainly for "+c.disc+". It has built "+c.built+"% of the ceiling and runs "+fmtGW(c.liveGW)+" of live datacenter capacity, a Gross Domestic Compute of "+fmtB(c.gdc)+". "+tierLine;
}
function chipText(s){ return s.name+" ("+s.vendor+"): "+(s.disp.usd==null?"no public accelerator-hour; "+s.disp.cfg:priceStr(s)+" per GPU-hour, "+s.disp.venue+" "+s.disp.term+", as of "+fmtDate(s.disp.asOf))+". Tape rank "+s.rank+" of "+CHIPS.length+". "+s.avail; }

/* sparkline (step) */
function sparkSVG(pts, w=92, h=28){
  if(!pts || pts.length===0) return null;
  const xs = pts.map(p=>dateNum(p[0])), ys = pts.map(p=>p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(dateNum(CFG.asOf), ...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const sx = x => x1===x0 ? 2 : 2 + (x-x0)/(x1-x0)*(w-4);
  const sy = y => y1===y0 ? h/2 : (h-3) - (y-y0)/(y1-y0)*(h-6);
  let d = "";
  pts.forEach((p,i)=>{ const x=sx(xs[i]), y=sy(ys[i]); d += i===0 ? "M"+x.toFixed(1)+","+y.toFixed(1) : " H"+x.toFixed(1)+" V"+y.toFixed(1); });
  d += " H"+(w-2);
  const dots = pts.map((p,i)=>'<circle cx="'+sx(xs[i]).toFixed(1)+'" cy="'+sy(ys[i]).toFixed(1)+'" r="2.2"/>').join("");
  const dir = ys[ys.length-1] > ys[0] ? "up" : ys[ys.length-1] < ys[0] ? "down" : "flat";
  return {svg:'<svg viewBox="0 0 '+w+' '+h+'" aria-hidden="true"><path d="'+d+'"/>'+dots+'</svg>', dir};
}

/* board */
const COLS = {
  countries: { grid:"52px minmax(0,1fr) 132px 108px 140px 20px", head:["#","Country",null,"Conversion","Readiness",""] },
  silicon: { grid:"52px minmax(0,1fr) 150px 84px 92px 124px 20px", head:["#","Accelerator",null,"1 quarter","Path","Availability",""] }
};
function currentLens(){ return LENS[state.tab][state.lens[state.tab]]; }
function currentRows(){
  const L = currentLens();
  let arr = state.tab==="countries" ? COUNTRIES.slice() : CHIPS.slice();
  if(L.filter) arr = arr.filter(L.filter);
  arr.sort((a,b)=>L.key(b)-L.key(a) || (a.rank-b.rank));
  return arr;
}
function renderLens(){
  const sel = $("#lens"); sel.innerHTML = "";
  Object.entries(LENS[state.tab]).forEach(([k,v])=>{ const o=document.createElement("option"); o.value=k; o.textContent=v.label; sel.appendChild(o); });
  sel.value = state.lens[state.tab];
}
function renderColhead(){
  const c = COLS[state.tab], L = currentLens(), el = $("#colhead");
  el.style.gridTemplateColumns = c.grid;
  el.innerHTML = c.head.map((h,i)=> i===2 ? '<div class="r on">'+esc(L.head)+'</div>' : '<div'+(i>=3?' class="r"':'')+'>'+esc(h||"")+'</div>').join("");
}
function renderBoard(){
  renderLens(); renderColhead();
  const isMap = state.tab==="countries" && state.view==="map";
  $("#viewSeg").hidden = state.tab!=="countries";
  $("#listWrap").hidden = isMap; $("#mapWrap").hidden = !isMap;
  $("#panel-board").setAttribute("aria-labelledby","tab-"+state.tab);
  const rows = currentRows();
  const n = state.topn==="all" ? rows.length : Math.min(+state.topn, rows.length);
  const L = currentLens(), list = $("#rows");
  if(rows.length===0){ list.innerHTML='<li class="empty"><b>Nothing has moved yet.</b>Scores change only when a country does something in public. Check the signals, or switch the lens.</li>'; }
  else list.innerHTML = rows.slice(0,n).map((r,i)=> state.tab==="countries" ? countryRow(r,i+1,L) : chipRow(r,i+1,L)).join("");
  const foot = $("#boardFoot");
  if(state.tab==="countries"){
    foot.innerHTML = '<span>'+esc(L.label)+', '+(rows.length===COUNTRIES.length?'all 108 countries':rows.length+' of 108 countries')+'. Grey figures are estimate fills.</span><span class="spacer"></span><span>Snapshot '+fmtDate(CFG.asOf)+'. Macros refresh from the IMF and World Bank.</span>';
  } else {
    foot.innerHTML = '<span>Buy-now list from the most liquid public venue. Labeled terms only; on-demand, spot and reserved are never blended.</span><span class="spacer"></span><a href="https://compute.world/silicon.html">Full tape with the term book</a>';
  }
  if(isMap) paintMap();
  if(state.open){ const li = $("#row-"+CSS.escape(state.open)); if(li) openRow(li, true); }
}
function countryRow(c, ord, L){
  const arrow = c.dir==="up" ? "▲ " : c.dir==="down" ? "▼ " : "";
  const dcls = c.dir==="up"?"up":c.dir==="down"?"down":"flat";
  const dsub = c.rz!==c.rz0 ? ((c.rz>c.rz0?"+":"")+(c.rz-c.rz0)+" since 19 Aug") : (c.signal ? "signal this week" : "no new signal");
  const est = state.lens.countries==="gdc"||state.lens.countries==="livegw" ? c.gdcEst : false;
  return '<li class="row" id="row-'+c.id+'" data-type="country" data-id="'+c.id+'">'
    +'<button class="row-main" style="grid-template-columns:'+COLS.countries.grid+'" aria-expanded="false" aria-controls="det-'+c.id+'">'
    +'<span class="ord">'+ord+'</span>'
    +'<span class="who">'+flag(c)+'<span class="name">'+esc(c.name)+'</span><span class="tier tier-'+c.tier+'">'+TIER[c.tier]+'</span><span class="mdelta '+dcls+'">'+arrow+'Conversion '+c.rz+'</span></span>'
    +'<span class="metric"><span class="val'+(est?' est':'')+'">'+esc(L.fmt(c))+'</span><span class="sub">'+esc(L.sub(c))+'</span></span>'
    +'<span class="delta '+dcls+'">'+arrow+c.rz+'<small>'+esc(dsub)+'</small></span>'
    +'<span class="ready"><i class="bar"><i style="width:'+Math.round(c.readiness*100)+'%"></i></i><span>'+Math.round(c.readiness*100)+'%</span></span>'
    +chev()+'</button><div class="row-detail" id="det-'+c.id+'" hidden></div></li>';
}
function chipRow(s, ord, L){
  const sp = sparkSVG(s.spark);
  const q = s.chg.q, y = s.chg.y;
  let dval, dcls="flat", dsub;
  if(q.pct!=null){ dval=(q.pct>0?"+":"")+q.pct.toFixed(1)+"%"; dcls=q.pct>0?"up":q.pct<0?"down":"flat"; dsub="1Q, "+s.disp.venue; }
  else if(y.pct!=null){ dval=(y.pct>0?"+":"")+y.pct.toFixed(1)+"%"; dcls=y.pct>0?"up":y.pct<0?"down":"flat"; dsub="1Y, no 1Q pair"; }
  else { dval="—"; dsub=s.disp.usd==null?"no chip-hour":"no dated pair"; }
  return '<li class="row" id="row-'+s.id+'" data-type="chip" data-id="'+s.id+'">'
    +'<button class="row-main" style="grid-template-columns:'+COLS.silicon.grid+'" aria-expanded="false" aria-controls="det-'+s.id+'">'
    +'<span class="ord">'+ord+'</span>'
    +'<span class="who">'+logo(s.vendor)+'<span class="name">'+esc(s.name)+'<small>'+esc(s.vendor+", "+s.mem)+'</small></span><span class="mdelta">'+esc(s.scar)+'</span></span>'
    +'<span class="metric"><span class="val">'+esc(L.fmt(s))+'</span><span class="sub">'+esc(L.sub(s))+'</span></span>'
    +'<span class="delta '+dcls+'" title="'+esc((q.pct!=null?"":q.note||"")+(y.pct!=null?"":" "+(y.note||"")))+'">'+dval+'<small>'+esc(dsub)+'</small></span>'
    +'<span class="spark '+(sp?sp.dir:"")+'">'+(sp?sp.svg:'<span class="note tiny">no prints</span>')+'</span>'
    +'<span class="scar">'+esc(s.scar)+'</span>'
    +chev()+'</button><div class="row-detail" id="det-'+s.id+'" hidden></div></li>';
}
const chev = () => '<svg class="chev" viewBox="0 0 16 16" aria-hidden="true"><path d="M3 6l5 5 5-5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
function fact(b, s, est){ return '<div class="fact"><b'+(est?' class="est"':'')+'>'+b+'</b><span>'+s+'</span></div>'; }
function actionsHTML(type, obj){
  const url = pageFor(type, obj);
  const share = type==="country" ? obj.name+": compute net worth "+fmtRange(obj)+", unlockable "+fmtB(obj.unlock)+", live "+fmtB(obj.gdc)+"." : obj.name+" rents at "+priceStr(obj)+" per GPU-hour ("+obj.disp.venue+", "+obj.disp.term+").";
  const local = (type==="country"?"country/":"silicon/")+obj.slug+"/";
  return '<div class="actions">'
    +'<a class="btn small primary" href="'+ROOT+local+'">Open full profile</a>'
    +'<button class="btn small" data-act="link" data-url="'+esc(url)+'">Copy link</button>'
    +'<button class="btn small" data-act="cite" data-name="'+esc(obj.name)+'" data-url="'+esc(url)+'">Copy citation</button>'
    +'<button class="btn small" data-act="text" data-type="'+type+'" data-id="'+esc(obj.id)+'">Copy summary</button>'
    +'<button class="btn small" data-act="card" data-type="'+type+'" data-id="'+esc(obj.id)+'">Share card</button>'
    +'<a class="btn small" href="'+esc(xFor(share,url))+'" target="_blank" rel="noopener">Post on X</a></div>';
}
function countryDetail(c){
  const d = c.rz-c.rz0;
  return '<div class="facts">'
    + fact(fmtRange(c), "Ceiling. "+c.ceilGW+" GW of identified resource at $60 to 80B per GW.")
    + fact(fmtB(c.unlock), "Unlockable. Firm untapped power × $50B × readiness of "+Math.round(c.readiness*100)+"%.")
    + fact(fmtB(c.gdc), "Live compute. "+fmtGW(c.liveGW)+" of datacenter capacity running today"+(c.gdcEst?", estimate":"")+".", c.gdcEst)
    + fact(c.xgdp+"×", "Ceiling as a multiple of GDP, $"+num(c.gdp)+"B, IMF.")
    + fact("$"+num(c.perPerson), "Unlockable per person.")
    + fact(c.built+"%", "Built: hydro and geothermal already installed, against the ceiling.")
    + fact(String(c.rz), "Conversion score, 0 to 100. "+(d?((d>0?"+":"")+d+" since the 19 Aug snapshot."):"Unchanged since the 19 Aug snapshot."))
    +'</div>'
    + (c.signal ? '<div class="signal '+c.dir+'"><span class="dot"></span><div>'+esc(c.signal)+'<span class="m">Latest signal. Arrows mark direction from recent items.</span></div></div>' : '')
    +'<p class="note" style="margin:0 0 14px"><b>'+TIER[c.tier]+'.</b> '+esc(TIER_DEF[c.tier])+' Discounted mainly for '+esc(c.disc)+'.</p>'
    + actionsHTML("country", c);
}
function chipDetail(s){
  const q=s.chg.q, y=s.chg.y;
  let facts = fact(priceStr(s), esc(s.disp.venue+", "+s.disp.term+(s.disp.cfg?", "+s.disp.cfg:"")+". As of "+fmtDate(s.disp.asOf)+"."));
  if(s.disp.cny) facts += fact(fmtUSD(s.disp.usd), "USD label at PBOC parity "+s.disp.fx+" on "+fmtDate(s.disp.fxDate)+". CNY is the primary print.");
  if(s.terms.y1) facts += fact(fmtUSD(s.terms.y1.price), "1-year term book: "+esc(s.terms.y1.venue+", "+s.terms.y1.label)+".");
  if(s.terms.y3) facts += fact(fmtUSD(s.terms.y3.price), "3-year term book: "+esc(s.terms.y3.venue+", "+s.terms.y3.label)+".");
  facts += fact(q.pct!=null?(q.pct>0?"+":"")+q.pct.toFixed(1)+"%":"—", q.pct!=null ? "1 quarter. "+s.disp.venue+" "+fmtUSD(q.then)+" on "+fmtDate(q.thenDate)+" to "+fmtUSD(s.disp.usd)+" on "+fmtDate(s.disp.asOf)+"." : "1 quarter. "+esc(q.note));
  facts += fact(y.pct!=null?(y.pct>0?"+":"")+y.pct.toFixed(1)+"%":"—", y.pct!=null ? "1 year. "+s.disp.venue+" "+fmtUSD(y.then)+" on "+fmtDate(y.thenDate)+" to "+fmtUSD(s.disp.usd)+"." : "1 year. "+esc(y.note));
  if(s.first && s.disp.usd!=null) facts += fact((pct(s.disp.usd,s.first.price)>=0?"+":"")+pct(s.disp.usd,s.first.price)+"%", "Since the first print on the tape: "+fmtUSD(s.first.price)+" on "+fmtDate(s.first.date)+".");
  facts += fact(s.score.toFixed(2), "Tape rank score. Liquidity "+s.liq+", demand "+s.dem+", frontier "+s.fr+", each 0 to 3.");
  const rows = s.quotes.map((qq,i)=>{
    const url = DATA.venueUrl[qq[0]];
    const v = url ? '<a href="'+esc(url)+'" target="_blank" rel="noopener">'+venue(qq[0])+'</a>' : venue(qq[0]);
    const stale = /stale/i.test(qq[4]||"") || /SemiAnalysis/.test(qq[0]);
    return '<tr'+(i===0?' class="lead"':'')+'><td>'+v+'</td><td>'+esc(qq[1])+'</td><td class="r price'+(stale?' stale':'')+'">'+(qq[2]==null?'<span class="dash">—</span>':fmtUSD(qq[2]))+'</td><td>'+fmtDate(qq[3])+'</td><td class="note tiny">'+esc(qq[4]||"")+'</td></tr>';
  }).join("");
  return '<div class="facts">'+facts+'</div>'
    +'<table class="quotes"><thead><tr><th>Venue</th><th>Term</th><th class="r">$ per hour</th><th>As of</th><th>Note</th></tr></thead><tbody>'+rows+'</tbody></table>'
    +'<p class="note">'+esc(s.avail)+'</p>'
    + (s.cannot.length ? '<details class="why"><summary>Not shown on this row, and why</summary><ul>'+s.cannot.map(x=>'<li>'+esc(x)+'</li>').join("")+'</ul></details>' : '<div style="height:10px"></div>')
    + actionsHTML("chip", s);
}
function openRow(li, silent){
  const btn = $(".row-main", li), det = $(".row-detail", li);
  const isOpen = li.classList.contains("open");
  $$("#rows .row.open").forEach(o=>{ if(o!==li){ o.classList.remove("open"); $(".row-main",o).setAttribute("aria-expanded","false"); $(".row-detail",o).hidden=true; } });
  if(isOpen && !silent){ li.classList.remove("open"); btn.setAttribute("aria-expanded","false"); det.hidden=true; state.open=null; return; }
  const type = li.dataset.type, id = li.dataset.id;
  det.innerHTML = type==="country" ? countryDetail(byId[id]) : chipDetail(chipById[id]);
  li.classList.add("open"); btn.setAttribute("aria-expanded","true"); det.hidden=false; state.open=id;
  if(!silent) history.replaceState(null,"","#"+type+"/"+id);
}
function revealRow(type, id){
  const tab = type==="country" ? "countries" : "silicon";
  if(state.tab!==tab) switchTab(tab);
  state.view = "list";
  if(currentRows().findIndex(r=>r.id===id)<0){ state.lens[state.tab] = tab==="countries"?"unlock":"rank"; }
  const need = currentRows().findIndex(r=>r.id===id)+1;
  if(state.topn!=="all" && need > +state.topn){ state.topn = need<=25 ? "25" : "all"; $("#topn").value = state.topn; }
  state.open = id; renderBoard(); syncSeg();
  const li = $("#row-"+CSS.escape(id)); if(li){ li.scrollIntoView({block:"center"}); }
}
function switchTab(tab){
  state.tab = tab; state.open = null;
  $$(".tab").forEach(t=>t.setAttribute("aria-selected", t.dataset.tab===tab ? "true":"false"));
  $$(".nav a[data-tab], .mnav a[data-tab]").forEach(a=>a.classList.toggle("current", a.dataset.tab===tab));
  renderBoard();
}
function syncSeg(){ $$("#viewSeg button").forEach(b=>b.setAttribute("aria-pressed", b.dataset.view===state.view?"true":"false")); }

/* map */
function paintMap(){
  const svg = $("#mapsvg"); if(!svg) return;
  const L = currentLens();
  $$("path.c", svg).forEach(p=>{ const id=p.dataset.id; if(!id||!byId[id]) return; const c=byId[id]; p.setAttribute("class","c idx t-"+c.tier); });
  $("#maplegend").innerHTML = ["SG","PR","IN","EU","LR"].map(t=>'<span><i style="background:'+({SG:"#B9A7DD",PR:"#8FCBBE",IN:"#9AA6B2",EU:"#E8C27E",LR:"#C5CCC5"})[t]+'"></i>'+TIER[t]+'</span>').join("")+'<span style="margin-left:auto">Hover for '+esc(L.label.toLowerCase())+'. Click to open.</span>';
}
function mapTip(e, id){
  const tip = $("#maptip"), c = byId[id], L = currentLens();
  if(!c){ tip.classList.remove("show"); return; }
  const r = $("#mapWrap").getBoundingClientRect();
  tip.innerHTML = '<b>'+esc(c.name)+'</b>'+esc(L.fmt(c))+' '+esc(L.sub(c).toLowerCase())+' · '+TIER[c.tier];
  tip.style.left = (e.clientX - r.left)+"px"; tip.style.top = (e.clientY - r.top)+"px"; tip.classList.add("show");
}

/* rail */
function renderRail(){
  const movers = COUNTRIES.filter(c=>c.rz!==c.rz0).sort((a,b)=>Math.abs(b.rz-b.rz0)-Math.abs(a.rz-a.rz0));
  $("#movers").innerHTML = movers.length ? movers.map(c=>{ const d=c.rz-c.rz0; return '<li>'+flag(c)+'<button class="name" style="text-align:left" data-reveal="country:'+c.id+'">'+esc(c.name)+'</button><span class="d '+(d>0?"up":"down")+'">'+(d>0?"+":"")+d+'</span></li>'; }).join("")
    : '<li class="note tiny">No score has changed between snapshots yet.</li>';
  const wire = COUNTRIES.filter(c=>c.signal).sort((a,b)=> (b.dir!=="flat")-(a.dir!=="flat") || b.rz-a.rz).slice(0,8);
  $("#wire").innerHTML = wire.map(c=>'<li>'+flag(c)+'<div><button class="t" data-reveal="country:'+c.id+'">'+esc(c.signal)+'</button><span class="m">'+esc(c.name)+', conversion '+c.rz+(c.dir==="up"?" ▲":c.dir==="down"?" ▼":"")+'</span></li>').join("");
}

/* charts (Tufte: range frames, no grid, direct labels) */
function chartSize(el, base){ const w = Math.max(320, el.clientWidth || base.W); return {W:w, H:base.H, narrow:w<480}; }
function thinXTicks(ticks, sx, minPx){
  /* Keep first + last (as-of / cursor wins). Drop intermediates that collide. */
  if(!ticks || ticks.length<=2) return ticks.slice();
  const last = ticks[ticks.length-1];
  const out = [ticks[0]];
  for(let i=1;i<ticks.length-1;i++){
    const x = sx(ticks[i]);
    if(x - sx(out[out.length-1]) >= minPx && sx(last) - x >= minPx) out.push(ticks[i]);
  }
  out.push(last);
  return out;
}
function rangeFrame(sx, sy, xDom, yDom, yTicks, xTicks, fmtY, fmtX, xLabelAnchor){
  let g = '<g class="frame">';
  g += '<line x1="'+sx(xDom[0]).toFixed(1)+'" x2="'+sx(xDom[1]).toFixed(1)+'" y1="'+sy(yDom[0]).toFixed(1)+'" y2="'+sy(yDom[0]).toFixed(1)+'"/>';
  g += '<line x1="'+sx(xDom[0]).toFixed(1)+'" x2="'+sx(xDom[0]).toFixed(1)+'" y1="'+sy(yDom[0]).toFixed(1)+'" y2="'+sy(yDom[1]).toFixed(1)+'"/></g><g class="tick">';
  yTicks.forEach(v=>{ g += '<line x1="'+(sx(xDom[0])-4).toFixed(1)+'" x2="'+sx(xDom[0]).toFixed(1)+'" y1="'+sy(v).toFixed(1)+'" y2="'+sy(v).toFixed(1)+'" stroke="currentColor" stroke-width="1" style="stroke:var(--ink-3)"/><text x="'+(sx(xDom[0])-8).toFixed(1)+'" y="'+(sy(v)+4).toFixed(1)+'" text-anchor="end">'+fmtY(v)+'</text>'; });
  const shown = thinXTicks(xTicks, sx, 72);
  shown.forEach((t,i)=>{ const a = xLabelAnchor ? xLabelAnchor(t,i,shown.length) : "middle"; g += '<line y1="'+sy(yDom[0]).toFixed(1)+'" y2="'+(sy(yDom[0])+4).toFixed(1)+'" x1="'+sx(t).toFixed(1)+'" x2="'+sx(t).toFixed(1)+'" style="stroke:var(--ink-3)"/><text x="'+sx(t).toFixed(1)+'" y="'+(sy(yDom[0])+17).toFixed(1)+'" text-anchor="'+a+'">'+fmtX(t)+'</text>'; });
  return g+'</g>';
}
function renderRz(){
  const el = $("#rzChart"); const {W,H,narrow} = chartSize(el,{W:900,H:280});
  const padL=narrow?36:40,padR=narrow?88:80,padT=16,padB=30;
  const obs = ["2026-08-19","2026-09-04"];
  const asOf = DATA.snapshotDates[state.rzIdx]; $("#rzDate").textContent = fmtDate(asOf);
  const dates = DATA.snapshotDates; const x0=dateNum(dates[0]), x1=dateNum(dates[dates.length-1]);
  const sx = iso => padL + (dateNum(iso)-x0)/(x1-x0)*(W-padL-padR);
  const sy = v => padT + (H-padT-padB) - v/100*(H-padT-padB);
  const pal = palette();
  let s = '<g class="series">'; const labels=[];
  state.rzSel.forEach((id,i)=>{
    const c = byId[id], col = pal[i%pal.length];
    const pts = obs.filter(d=>dateNum(d)<=dateNum(asOf)).map(d=>[d, d===obs[0]?c.rz0:c.rz]);
    if(!pts.length) return;
    s += '<path d="'+pts.map((p,j)=>(j?"L":"M")+sx(p[0]).toFixed(1)+","+sy(p[1]).toFixed(1)).join(" ")+'" stroke="'+col+'" stroke-dasharray="3 3"/>';
    pts.forEach(p=>{ s += '<circle cx="'+sx(p[0]).toFixed(1)+'" cy="'+sy(p[1]).toFixed(1)+'" r="3.2" stroke="'+col+'"/>'; });
    const last = pts[pts.length-1]; labels.push({x:sx(last[0])+8, y:sy(last[1]), y0:sy(last[1]), text:c.iso2+" "+last[1], col});
  });
  const gap = narrow?18:16; labels.sort((a,b)=>a.y-b.y);
  for(let i=1;i<labels.length;i++){ if(labels[i].y-labels[i-1].y<gap) labels[i].y = labels[i-1].y+gap; }
  const over = labels.length ? labels[labels.length-1].y-(H-padB-4) : 0; if(over>0) labels.forEach(l=>l.y-=over);
  const under = labels.length ? padT+8-labels[0].y : 0; if(under>0) labels.forEach(l=>l.y+=under);
  labels.forEach(l=>{ if(Math.abs(l.y-l.y0)>1) s += '<line x1="'+(l.x-6).toFixed(1)+'" x2="'+(l.x-2).toFixed(1)+'" y1="'+l.y0.toFixed(1)+'" y2="'+l.y.toFixed(1)+'" stroke="'+l.col+'" opacity=".6"/>'; s += '<text class="lbl" x="'+l.x.toFixed(1)+'" y="'+(l.y+4).toFixed(1)+'" fill="'+l.col+'">'+l.text+'</text>'; });
  s += '</g>';
  /* Axis: first print + as-of only. 4 Sep and 7 Sep are 3 days apart; labeling
     both stacks them at the right edge. The 4 Sep read stays on the line and in the caption. */
  const xTicks = [obs[0], asOf].filter((t, i, a) => a.indexOf(t) === i);
  const frame = rangeFrame(sx, sy, [dates[0], dates[dates.length-1]], [0,100], [0,25,50,75,100], xTicks, v=>String(v), fmtDateShort, (t,i,n)=> i===0?"start":(i===n-1?"end":"middle"));
  const cursor = '<line x1="'+sx(asOf).toFixed(1)+'" x2="'+sx(asOf).toFixed(1)+'" y1="'+padT+'" y2="'+(H-padB)+'" style="stroke:var(--ink)" stroke-dasharray="2 3"/>';
  el.innerHTML = '<svg viewBox="0 0 '+W+' '+H+'"'+(narrow?' class="narrow"':'')+' role="img" aria-label="Conversion score by country over observed snapshots">'+frame+cursor+s+'</svg>';
  const movers = COUNTRIES.filter(c=>c.rz!==c.rz0).sort((a,b)=>Math.abs(b.rz-b.rz0)-Math.abs(a.rz-a.rz0));
  $("#rzCaption").textContent = dateNum(asOf) < dateNum(obs[1]) ? "One observed snapshot at this date. Drag forward to see the 4 September reads." :
    "Two observed reads, "+fmtDateShort(obs[0])+" and "+fmtDateShort(obs[1])+". "+movers.map(c=>c.name+" "+(c.rz>c.rz0?"+":"")+(c.rz-c.rz0)).join(", ")+". Dotted connectors join observations; nothing between them is inferred.";
}
function renderRzChips(){
  const cands = COUNTRIES.filter(c=>c.rz!==c.rz0).map(c=>c.id).concat(["USA","KOR","GBR","DEU","MYS"]).filter((v,i,a)=>a.indexOf(v)===i);
  if(!state.rzSel) state.rzSel = cands.slice(0,7);
  $("#rzChips").innerHTML = cands.map(id=>'<button class="chip" aria-pressed="'+(state.rzSel.includes(id)?"true":"false")+'" data-rz="'+id+'">'+flag(byId[id])+byId[id].iso2+'</button>').join("");
}
function renderMultiples(){
  const wrap = $("#multiples"); const keys = Object.keys(DATA.pricePaths);
  const all = keys.flatMap(k=>DATA.pricePaths[k].flatMap(s=>s.pts.map(p=>p[1])));
  const yMax = Math.ceil(Math.max(...all)/2)*2; // shared scale across the multiples
  const xs = keys.flatMap(k=>DATA.pricePaths[k].flatMap(s=>s.pts.map(p=>dateNum(p[0]))));
  const x0 = Math.min(...xs), x1 = dateNum(CFG.asOf);
  const pal = palette();
  const wrapW = Math.max(320, wrap.clientWidth || 960); const cols = wrapW >= 900 ? 3 : 1; const panelW = Math.floor((wrapW - (cols-1)*20)/cols);
  wrap.innerHTML = keys.map(k=>{
    const el = document.createElement("div"); el.className="multiple";
    const W=panelW,H=220,padL=40,padR=54,padT=14,padB=28;
    const sx = iso => padL + (dateNum(iso)-x0)/(x1-x0)*(W-padL-padR);
    const sy = v => padT + (H-padT-padB) - v/yMax*(H-padT-padB);
    let s = '<g class="series">'; const labels=[];
    DATA.pricePaths[k].forEach((sr,i)=>{
      const col = pal[i%pal.length]; let d="";
      sr.pts.forEach((p,j)=>{ const x=sx(p[0]), y=sy(p[1]); d += j===0 ? "M"+x.toFixed(1)+","+y.toFixed(1) : " H"+x.toFixed(1)+" V"+y.toFixed(1); });
      if(!sr.stale) d += " H"+sx(CFG.asOf).toFixed(1);
      s += '<path d="'+d+'" stroke="'+col+'"'+(sr.stale?' stroke-dasharray="4 3"':'')+'/>';
      sr.pts.forEach(p=>{ s += '<circle cx="'+sx(p[0]).toFixed(1)+'" cy="'+sy(p[1]).toFixed(1)+'" r="2.8" stroke="'+col+'"/>'; });
      const last = sr.pts[sr.pts.length-1];
      labels.push({x: (sr.stale ? sx(last[0]) : sx(CFG.asOf))+7, y: sy(last[1]), y0: sy(last[1]), text: fmtUSD(last[1]), col});
    });
    labels.sort((a,b)=>a.y-b.y); for(let i=1;i<labels.length;i++){ if(labels[i].y-labels[i-1].y<14) labels[i].y=labels[i-1].y+14; }
    const overflow = labels.length ? labels[labels.length-1].y-(H-padB-4) : 0; if(overflow>0) labels.forEach(l=>l.y-=overflow);
    labels.forEach(l=>{ if(Math.abs(l.y-l.y0)>2) s += '<line x1="'+(l.x-5).toFixed(1)+'" x2="'+(l.x-1).toFixed(1)+'" y1="'+l.y0.toFixed(1)+'" y2="'+l.y.toFixed(1)+'" stroke="'+l.col+'" opacity=".55"/>'; s += '<text class="lbl" x="'+l.x.toFixed(1)+'" y="'+(l.y+4).toFixed(1)+'" fill="'+l.col+'">'+l.text+'</text>'; });
    s += '</g>';
    const years = []; for(let yy=new Date(x0).getUTCFullYear(); yy<=new Date(x1).getUTCFullYear(); yy++){ const iso=yy+"-01-01"; if(dateNum(iso)>=x0 && dateNum(iso)<=x1) years.push(iso); }
    const frame = rangeFrame(sx, sy, [new Date(x0).toISOString().slice(0,10), CFG.asOf], [0,yMax], [0,yMax/2,yMax], years, v=>"$"+v, iso=>iso.slice(0,4));
    const legend = DATA.pricePaths[k].map((sr,i)=>'<span class="lbl" style="color:'+pal[i%pal.length]+';font-size:12px">'+esc(sr.short)+(sr.stale?' (ended)':'')+'</span>').join(' <span class="note tiny">·</span> ');
    el.innerHTML = '<h4>'+esc(k)+'<small>$ per GPU-hour</small></h4><svg viewBox="0 0 '+W+' '+H+'" role="img" aria-label="'+esc(k)+' price path">'+frame+s+'</svg><div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:4px">'+legend+'</div><p class="caption">'+esc(DATA.priceCaptions[k])+'</p>';
    return el.outerHTML;
  }).join("");
}

/* projects */
const STATUSES = ["All","Live","Building","Contracted","Announced","Stalled"];
function renderProjects(){
  $("#statusChips").innerHTML = STATUSES.map(s=>'<button class="chip" aria-pressed="'+(state.status===s?"true":"false")+'" data-status="'+s+'">'+s+'</button>').join("");
  const rows = DATA.precedents.filter(p=>state.status==="All"||p[3]===state.status);
  $("#precCount").textContent = rows.length+" of "+DATA.precedents.length;
  $("#plist").innerHTML = rows.map(p=>{
    const c = byId[p[0]];
    const href = p[5] || (c ? ROOT+"country/"+c.slug+"/#projects" : "/campuses.html");
    const who = c ? flag(c)+'<span class="name" style="font-size:15px">'+esc(c.name)+'</span>' : '<img class="flag" src="'+ROOT+'flags/eu.svg" alt="" width="24" height="18" data-code="EU" onerror="flagFail(this)"><span class="name" style="font-size:15px">European Union</span>';
    return '<li><a class="proj-row" href="'+esc(href)+'"><span class="who">'+who+'</span><span class="proj">'+esc(p[1])+'</span><span class="scale">'+esc(p[2])+'</span><span class="status '+p[3]+'">'+p[3]+'</span><span class="date">'+esc(p[4])+'</span></a></li>';
  }).join("");
}

/* method */
function renderMethod(){
  $("#stackbar").innerHTML = DATA.readiness.map(r=>'<div style="flex:'+r.w+';background:'+r.c+(r.w<11?';color:#1B222A':'')+'" title="'+esc(r.k+" "+r.w+"%: "+r.d)+'">'+r.w+'</div>').join("");
  $("#stacklegend").innerHTML = DATA.readiness.map(r=>'<span><i style="background:'+r.c+'"></i>'+esc(r.k)+' '+r.w+'%<small>'+esc(r.d)+'</small></span>').join("");
}

/* country profiles */
const REGIONS = ["All","Americas","Europe","MENA","Africa","South Asia","Central Asia","East Asia","SE Asia","Oceania"];
function renderProfiles(){
  $("#regionChips").innerHTML = REGIONS.map(r=>'<button class="chip" aria-pressed="'+(state.region===r?"true":"false")+'" data-region="'+r+'">'+r+'</button>').join("");
  const q = state.q.trim().toLowerCase();
  const rows = COUNTRIES.filter(c=>(state.region==="All"||c.region===state.region)&&(!q||c.name.toLowerCase().includes(q)||c.id.toLowerCase()===q||c.iso2.toLowerCase()===q)).sort((a,b)=>a.rank-b.rank);
  $("#cards").innerHTML = rows.length ? rows.map(c=>'<a class="card" href="'+ROOT+'country/'+c.slug+'/"><span class="top">'+flag(c)+'<span class="name">'+esc(c.name)+'</span><span class="rank">#'+c.rank+'</span></span><span class="line">Ceiling <b>'+fmtRange(c)+'</b>, '+c.xgdp+'× GDP. Unlockable <b>'+fmtB(c.unlock)+'</b>. Live <b>'+fmtB(c.gdc)+'</b>.</span><span class="tier tier-'+c.tier+'">'+TIER[c.tier]+'</span></a>').join("")
    : '<div class="empty" style="grid-column:1/-1"><b>No country matches.</b>Try the ISO code, or clear the region filter.</div>';
}

/* share sheet */
function openSheet(type, id){
  const dlg = $("#sheet"), obj = type==="country" ? byId[id] : chipById[id];
  if(!obj) return;
  $("#sheetMark").innerHTML = type==="country" ? flag(obj,"lg") : logo(obj.vendor,"lg");
  $("#sheetTitle").textContent = obj.name;
  const url = pageFor(type,obj);
  if(type==="country"){
    const c = obj;
    $("#sheetBody").innerHTML = '<p class="lead">'+esc(countryText(c))+'</p><div class="facts">'+fact(fmtRange(c),"Ceiling")+fact(fmtB(c.unlock),"Unlockable")+fact(fmtB(c.gdc),"Live compute"+(c.gdcEst?", estimate":""),c.gdcEst)+fact(Math.round(c.readiness*100)+"%","Readiness")+fact(String(c.rz),"Conversion")+fact(c.xgdp+"×","Ceiling over GDP")+'</div><p class="note tiny">Snapshot '+fmtDate(CFG.asOf)+'. '+esc(TIER[c.tier])+'. Rank '+c.rank+' of 108 by unlockable value.</p>';
  } else {
    const s = obj;
    $("#sheetBody").innerHTML = '<p class="lead">'+esc(chipText(s))+'</p><div class="facts">'+fact(priceStr(s), esc(s.disp.venue+", "+s.disp.term))+(s.terms.y1?fact(fmtUSD(s.terms.y1.price),"1-year term book"):"")+fact(String(s.rank),"Tape rank of "+CHIPS.length)+fact(esc(s.scar),"Availability")+'</div><p class="note tiny">As of '+fmtDate(s.disp.asOf)+'. Labeled term from a named venue; never an average.</p>';
  }
  const share = type==="country" ? obj.name+": compute net worth "+fmtRange(obj)+", unlockable "+fmtB(obj.unlock)+"." : obj.name+" rents at "+priceStr(obj)+" per GPU-hour.";
  $("#sheetFoot").innerHTML = '<a class="btn primary" href="'+ROOT+(type==="country"?"country/":"silicon/")+obj.slug+'/">Open full profile</a><button class="btn" data-act="link" data-url="'+esc(url)+'">Copy link</button><button class="btn" data-act="text" data-type="'+type+'" data-id="'+esc(id)+'">Copy text</button><button class="btn" data-act="cite" data-name="'+esc(obj.name)+'" data-url="'+esc(url)+'">Copy citation</button><a class="btn" href="'+esc(xFor(share,url))+'" target="_blank" rel="noopener">Post on X</a>';
  if(typeof dlg.showModal==="function"){ if(!dlg.open) dlg.showModal(); } else dlg.setAttribute("open","");
}

/* CSV */
function downloadCSV(){
  const rows = currentRows(); const n = state.topn==="all"?rows.length:Math.min(+state.topn,rows.length);
  let csv;
  if(state.tab==="countries"){
    csv = ["rank_in_view,iso3,country,tier,ceiling_low_usd_t,ceiling_high_usd_t,ceiling_x_gdp,unlockable_usd_b,unlockable_per_person_usd,live_compute_gdc_usd_b,gdc_is_estimate,live_gw,built_pct,readiness,conversion_score,conversion_prev_19aug,latest_signal,profile_url"]
      .concat(rows.slice(0,n).map((c,i)=>[i+1,c.id,'"'+c.name+'"',TIER[c.tier],c.ceilLo,c.ceilHi,c.xgdp,c.unlock,c.perPerson,c.gdc,c.gdcEst,c.liveGW,c.built,c.readiness,c.rz,c.rz0,'"'+c.signal.replace(/"/g,'""')+'"',pageFor("country",c)].join(","))).join("\n");
  } else {
    csv = ["rank_in_view,id,accelerator,vendor,memory,display_usd_per_gpu_hr,display_term,display_venue,display_as_of,chg_1q_pct,chg_1y_pct,first_print_usd,first_print_date,tape_score,availability,profile_url"]
      .concat(rows.slice(0,n).map((s,i)=>[i+1,s.id,'"'+s.name+'"',s.vendor,'"'+s.mem+'"',s.disp.usd??"",'"'+s.disp.term+'"','"'+s.disp.venue+'"',s.disp.asOf,s.chg.q.pct??"",s.chg.y.pct??"",s.first?s.first.price:"",s.first?s.first.date:"",s.score,'"'+s.scar+'"',pageFor("chip",s)].join(","))).join("\n");
  }
  csv = "# compute.world, "+(state.tab==="countries"?"The Compute Net Worth Index":"The Silicon Tape")+", snapshot "+CFG.asOf+". Free with attribution. "+CFG.site+"\n"+csv;
  const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([csv],{type:"text/csv"})); a.download = "compute-world-"+state.tab+"-"+CFG.asOf+".csv"; document.body.appendChild(a); a.click(); a.remove();
  toast("CSV downloaded");
}

/* events */
function handleAct(el){
  const a = el.dataset.act;
  if(a==="link") copy(el.dataset.url, "Link copied");
  else if(a==="cite") copy(citeFor(el.dataset.name, el.dataset.url), "Citation copied");
  else if(a==="text") copy(el.dataset.type==="country" ? countryText(byId[el.dataset.id]) : chipText(chipById[el.dataset.id]), "Summary copied");
  else if(a==="card") openSheet(el.dataset.type, el.dataset.id);
}
function bind(){
  $$(".tab").forEach(t=>t.addEventListener("click",()=>{ switchTab(t.dataset.tab); history.replaceState(null,"","#"+t.dataset.tab); }));
  $("#lens").addEventListener("change", e=>{ state.lens[state.tab]=e.target.value; state.open=null; renderBoard(); });
  $("#topn").addEventListener("change", e=>{ state.topn=e.target.value; renderBoard(); });
  $("#csvBtn").addEventListener("click", downloadCSV);
  $("#linkBtn").addEventListener("click", ()=>copy(CFG.site+"/#"+state.tab+"?lens="+state.lens[state.tab]+"&n="+state.topn, "Link to this view copied"));
  $("#rows").addEventListener("click", e=>{
    if(e.target.closest("a")) return;
    const act = e.target.closest("[data-act]"); if(act){ handleAct(act); return; }
    const main = e.target.closest(".row-main"); if(main) openRow(main.closest(".row"));
  });
  $("#viewSeg").addEventListener("click", e=>{ const b=e.target.closest("button"); if(!b) return; state.view=b.dataset.view; syncSeg(); renderBoard(); });
  const svg = $("#mapsvg");
  if(svg){
    svg.addEventListener("mousemove", e=>{ const t=e.target.closest("[data-id]"); if(t && byId[t.dataset.id]) mapTip(e,t.dataset.id); else $("#maptip").classList.remove("show"); });
    svg.addEventListener("mouseleave", ()=>$("#maptip").classList.remove("show"));
    svg.addEventListener("click", e=>{ const t=e.target.closest("[data-id]"); if(t && byId[t.dataset.id]) openSheet("country", t.dataset.id); });
  }
  document.addEventListener("click", e=>{
    const rv = e.target.closest("[data-reveal]"); if(rv){ const [t,id]=rv.dataset.reveal.split(":"); revealRow(t,id); return; }
    const act = e.target.closest("[data-act]"); if(act && !act.closest("#rows")){ handleAct(act); return; }
    const cp = e.target.closest("[data-copy]"); if(cp){ copy($(cp.dataset.copy).textContent.trim(), "Copied"); return; }
    const rz = e.target.closest("[data-rz]"); if(rz){ const id=rz.dataset.rz; const i=state.rzSel.indexOf(id); if(i>=0) state.rzSel.splice(i,1); else if(state.rzSel.length<8) state.rzSel.push(id); else toast("Eight lines is the limit. Turn one off first."); renderRzChips(); renderRz(); return; }
    const st = e.target.closest("[data-status]"); if(st){ state.status=st.dataset.status; renderProjects(); return; }
    const rg = e.target.closest("[data-region]"); if(rg){ state.region=rg.dataset.region; renderProfiles(); return; }
    const nav = e.target.closest(".nav a[data-tab], .mnav a[data-tab]"); if(nav){ switchTab(nav.dataset.tab); }
    if(e.target.closest(".mnav a")){ $("#mnav").classList.remove("open"); $("#menuBtn").setAttribute("aria-expanded","false"); document.body.classList.remove("nav-open"); }
    const sh = e.target.closest("[data-share]");
    if(sh){
      const dock = sh.closest(".share-dock") || $(".share-dock");
      const url = (dock && dock.dataset.shareUrl) || location.href;
      const title = (dock && dock.dataset.shareTitle) || document.title;
      const cite = (dock && dock.dataset.shareCite) || citeFor("");
      const act = sh.getAttribute("data-share");
      if(act==="native"){ if(navigator.share){ navigator.share({title, url, text:title}).catch(()=>{}); } else copy(url, "Link copied"); }
      else if(act==="copy") copy(url, "Link copied");
      else if(act==="cite") copy(cite, "Citation copied");
      return;
    }
    const more = $(".more"); if(more && more.open && !e.target.closest(".more")) more.removeAttribute("open");
  });
  $("#menuBtn").addEventListener("click", ()=>{ const m=$("#mnav"); const open=!m.classList.contains("open"); m.classList.toggle("open",open); $("#menuBtn").setAttribute("aria-expanded",open?"true":"false"); document.body.classList.toggle("nav-open",open); });
  $("#sheetClose").addEventListener("click", ()=>$("#sheet").close());
  $("#sheet").addEventListener("click", e=>{ if(e.target===$("#sheet")) $("#sheet").close(); });
  $("#rzScrub").addEventListener("input", e=>{ state.rzIdx=+e.target.value; renderRz(); });
  $("#gazSearch").addEventListener("input", e=>{ state.q=e.target.value; renderProfiles(); });
  window.addEventListener("hashchange", routeHash);
  let rt; window.addEventListener("resize", ()=>{ clearTimeout(rt); rt=setTimeout(()=>{ renderRz(); renderMultiples(); },150); });
  if(window.matchMedia){ window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", ()=>{ renderRz(); renderMultiples(); }); }
  document.addEventListener("keydown", e=>{ if(e.key==="/" && !/input|select|textarea/i.test(document.activeElement.tagName)){ e.preventDefault(); $("#gazSearch").focus(); } });
}
function routeHash(){
  const h = decodeURIComponent(location.hash.replace(/^#/,""));
  if(!h) return;
  const [head, rest] = h.split("?");
  if(head==="silicon"||head==="countries"){ switchTab(head); if(rest){ const p=new URLSearchParams(rest); if(p.get("lens")&&LENS[head][p.get("lens")]) state.lens[head]=p.get("lens"); if(p.get("n")) { state.topn=p.get("n"); $("#topn").value=state.topn; } renderBoard(); } return; }
  const m = head.match(/^(country|chip)\/(.+)$/);
  if(m){ const type=m[1], id=m[2]; if(type==="country"?byId[id]:chipById[id]){ revealRow(type,id); } return; }
  const slug = COUNTRIES.find(c=>c.slug===head || c.name.toLowerCase().replace(/[^a-z]+/g,"")===head.toLowerCase());
  if(slug) revealRow("country", slug.id);
}

/* init */
function init(){
  const sc = $("#rzScrub"); sc.max = DATA.snapshotDates.length-1; sc.value = state.rzIdx;
  $("#histDepth").textContent = DATA.snapshotDates.length+" daily snapshots since "+fmtDate(CFG.firstSnapshot)+", append-only";
  $("#citeBox").textContent = citeFor("", CFG.site+"/");
  window.thinXTicks = thinXTicks;
  bind(); renderBoard(); syncSeg(); renderRail(); renderRzChips(); renderRz(); renderMultiples(); renderProjects(); renderMethod(); renderProfiles(); routeHash();
  $$(".nav a[data-tab]").forEach(a=>a.classList.toggle("current", a.dataset.tab===state.tab));
}
document.addEventListener("DOMContentLoaded", init);
})();
