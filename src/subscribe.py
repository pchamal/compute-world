# Shared subscribe strip for public compute.world pages (index, silicon).
# embed.html stays free of this chrome. No secrets; the form posts to /api/subscribe.

def css():
    return """/* daily tape — subscribe strip */
.daily{margin:28px 0 6px;padding:18px 0 16px;border-top:1px solid var(--rule2);border-bottom:1px solid var(--rule);
display:grid;grid-template-columns:minmax(0,1.2fr) minmax(220px,.9fr);gap:16px 32px;align-items:end}
.daily .kicker{font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted)}
.daily h2{font-weight:400;font-size:clamp(20px,2.4vw,26px);line-height:1.2;margin:6px 0 8px}
.daily .lede-s{font-size:14.5px;color:var(--muted);max-width:560px}
.daily .lede-s a{border-bottom-color:transparent}
.daily .lede-s a:hover{border-bottom-color:var(--accent)}
.daily form{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.daily input[type=email]{flex:1 1 180px;min-width:0;font:inherit;font-size:15px;padding:10px 12px;
border:1px solid var(--rule2);background:var(--paper);color:var(--ink);border-radius:0}
.daily input[type=email]:focus{outline:2px solid var(--accent);outline-offset:1px}
.daily button[type=submit]{font:inherit;font-size:12px;letter-spacing:.14em;text-transform:uppercase;
padding:11px 16px;background:var(--ink);color:var(--paper);border:1px solid var(--rule2);cursor:pointer}
.daily button[type=submit]:hover{background:var(--accent);border-color:var(--accent)}
.daily button[type=submit]:disabled{opacity:.55;cursor:wait}
.daily .lists{display:flex;flex-wrap:wrap;gap:10px 16px;width:100%;font-size:13px;color:var(--muted);margin-top:2px}
.daily .lists label{display:flex;align-items:center;gap:6px;cursor:pointer}
.daily .feeds{margin-top:8px;font-size:12.5px;color:var(--faint);letter-spacing:.02em}
.daily .feeds a{border:none;color:var(--muted)}
.daily .feeds a:hover{color:var(--accent)}
.daily .submsg{margin-top:8px;font-size:13.5px;color:var(--ink);min-height:1.3em}
.daily .submsg.err{color:var(--accent)}
.daily .submsg.ok{color:var(--pr)}
@media(max-width:760px){.daily{grid-template-columns:1fr;gap:14px}.daily button[type=submit]{width:100%}}
"""


def markup():
    return """<section class="daily" id="subscribe" aria-label="Subscribe to the daily tape">
  <div>
    <div class="kicker">Weekday briefing</div>
    <h2>The daily tape</h2>
    <p class="lede-s">Country conversion signals and sourced silicon prints. Labeled terms only — no invented deltas. Read it on the <a href="/brief">public brief</a>, or take the RSS.</p>
  </div>
  <div>
    <form id="subform" action="/api/subscribe" method="post" novalidate>
      <input type="email" name="email" id="subemail" required autocomplete="email" placeholder="you@domain" aria-label="Email">
      <button type="submit">Subscribe</button>
      <div class="lists">
        <label><input type="checkbox" name="lists" value="countries" checked> Countries</label>
        <label><input type="checkbox" name="lists" value="silicon" checked> Silicon</label>
      </div>
    </form>
    <p class="feeds">RSS: <a href="/brief.xml">/brief.xml</a> · <a href="/silicon.xml">/silicon.xml</a> · <a href="/wire.xml">/wire.xml</a></p>
    <p class="submsg" id="submsg" role="status" aria-live="polite"></p>
  </div>
</section>
"""


def script():
    return """(function(){
  var form=document.getElementById("subform"), msg=document.getElementById("submsg");
  if(!form||!msg) return;
  function setMsg(t, kind){ msg.textContent=t; msg.className="submsg"+(kind?" "+kind:""); }
  form.addEventListener("submit", function(e){
    e.preventDefault();
    var email=(form.email.value||"").trim();
    var lists=[].slice.call(form.querySelectorAll('input[name="lists"]:checked')).map(function(c){ return c.value; });
    if(!email || email.indexOf("@")<1 || email.indexOf(".")<3){ setMsg("A real address, if you please.", "err"); return; }
    if(!lists.length){ setMsg("Choose Countries, Silicon, or both.", "err"); return; }
    var btn=form.querySelector('button[type="submit"]');
    btn.disabled=true; setMsg("Sending…", "");
    fetch("/api/subscribe", {
      method:"POST",
      headers:{"content-type":"application/json"},
      body:JSON.stringify({email:email, lists:lists})
    }).then(function(r){ return r.json().then(function(j){ return {ok:r.ok, status:r.status, j:j}; }); })
    .then(function(res){
      if(!res.ok){ setMsg((res.j&&res.j.error)||"That did not take. Try again, or use the RSS.", "err"); return; }
      var stored=res.j&&res.j.stored;
      if(stored==="pending"){
        setMsg("Noted. The public brief and RSS are live now. Email delivery wires when the list is connected.", "ok");
      } else {
        setMsg("You're on the list. Today's brief is public; the weekday feed is /brief.xml.", "ok");
      }
      form.reset();
      form.querySelectorAll('input[name="lists"]').forEach(function(c){ c.checked=true; });
    }).catch(function(){
      setMsg("The list is unreachable from here. The brief and RSS still are.", "err");
    }).finally(function(){ btn.disabled=false; });
  });
})();
"""
