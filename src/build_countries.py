#!/usr/bin/env python3
# Country pages, OG images, and plain-text siblings for the Compute Net Worth Index.
# Run from repo root or src/:  python3 src/build_countries.py
# Writes {slug}/index.html, {slug}.txt, og/{slug}.png into the repo.
import io
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from cnw_lib import (
    LABEL_CEILING, LABEL_GDC, LABEL_UNLOCK, N_COUNTRIES, SITE, TIER_CLASS, TIER_COLOR,
    assemble_countries, corroboration_label, delta_mark, esc, fmt_mult, fmt_rank_serial,
    live_signals_empty, money_b, money_pc, nice_day, readiness_parts,
)
from chrome import cert_html, coupon_html, delta_html, footer, head, masthead, subscribe_script
from seo import breadcrumb_ld, person_author

FLAGS_DIR = os.path.join(HERE, "flags")
OG_DIR = os.path.join(ROOT, "og")
MAX_OG_BYTES = 200 * 1024


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
        if not text.endswith("\n"):
            f.write("\n")


def flag_svg_path(iso2):
    os.makedirs(FLAGS_DIR, exist_ok=True)
    dest = os.path.join(FLAGS_DIR, f"{iso2.lower()}.svg")
    if os.path.isfile(dest) and os.path.getsize(dest) > 40:
        return dest
    url = f"https://flagcdn.com/{iso2.lower()}.svg"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "compute.world-builder/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        if data.startswith(b"<") or data.startswith(b"<?"):
            open(dest, "wb").write(data)
            return dest
    except Exception as e:
        print("flag svg miss", iso2, e)
    return dest if os.path.isfile(dest) else None


def raster_flag(iso2, w=72, h=48):
    """Rasterize an SVG flag. Never draw an emoji flag."""
    from PIL import Image
    svg = flag_svg_path(iso2)
    if svg:
        try:
            import cairosvg
            png = cairosvg.svg2png(url=svg, output_width=w * 2, output_height=h * 2)
            im = Image.open(io.BytesIO(png)).convert("RGBA")
            return im.resize((w, h), Image.Resampling.LANCZOS)
        except Exception:
            pass
        # flagcdn also serves PNGs derived from the same SVGs
        dest = os.path.join(FLAGS_DIR, f"{iso2.lower()}-{w}.png")
        if not os.path.isfile(dest):
            try:
                url = f"https://flagcdn.com/w160/{iso2.lower()}.png"
                req = urllib.request.Request(url, headers={"User-Agent": "compute.world-builder/1.0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    open(dest, "wb").write(r.read())
            except Exception as e:
                print("flag png miss", iso2, e)
        if os.path.isfile(dest):
            im = Image.open(dest).convert("RGBA")
            return im.resize((w, h), Image.Resampling.LANCZOS)
    # Last resort: a ruled rectangle with the ISO2 — still not an emoji.
    im = Image.new("RGBA", (w, h), (217, 212, 202, 255))
    return im


def _font(sz, bold=False, italic=False, sans=False):
    from PIL import ImageFont
    if sans:
        cands = (
            ["/usr/share/fonts/truetype/macos/Inter-Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else
            ["/usr/share/fonts/truetype/macos/Inter-Regular.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
        )
    elif italic:
        cands = ["/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
                 "/usr/share/fonts/truetype/noto/NotoSerif-Italic.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"]
    elif bold:
        cands = ["/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
                 "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"]
    else:
        cands = ["/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
                 "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"]
    for p in cands:
        if os.path.isfile(p):
            try:
                return ImageFont.truetype(p, sz)
            except OSError:
                pass
    return ImageFont.load_default()


def draw_og(c):
    from PIL import Image, ImageDraw
    W, H = 1200, 630
    PAPER = (247, 244, 238)
    INK = (23, 22, 20)
    MUT = (107, 103, 95)
    RULE = (217, 212, 202)
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    d.rectangle([48, 36, W - 48, 38], fill=INK)
    d.rectangle([48, H - 38, W - 48, H - 36], fill=RULE)

    flag = raster_flag(c.get("iso2") or "un", 84, 56)
    img.paste(flag, (56, 56), flag if flag.mode == "RGBA" else None)

    d.text((156, 54), "compute.world", font=_font(18, sans=True), fill=MUT)
    d.text((156, 78), c["name"], font=_font(44, bold=True), fill=INK)

    # tier seal: filled roundel with the name
    seal = TIER_COLOR.get(c["tier"], "#a89a7f")
    rgb = tuple(int(seal[i:i + 2], 16) for i in (1, 3, 5))
    tw = _font(16, sans=True, bold=True)
    label = c["tier"]
    twid = d.textlength(label, font=tw)
    sx, sy = 56, 132
    d.rounded_rectangle([sx, sy, sx + twid + 28, sy + 32], radius=16, fill=rgb)
    d.text((sx + 14, sy + 6), label, font=tw, fill=PAPER)

    mark = delta_mark(c.get("rank_delta"))
    serial = fmt_rank_serial(c.get("rank"))
    if mark:
        kind, glyph, n = mark
        extra = f"  {glyph}" + (f" {abs(n)}" if kind != "flat" else "")
    else:
        extra = ""
    d.text((56, 176), serial + extra, font=_font(22, sans=True), fill=INK)

    nums = [
        (money_b(c.get("cnw_ceiling_hi_B")), LABEL_CEILING),
        (money_b(c.get("cnw_unlockable_B")), LABEL_UNLOCK),
        (money_b(c.get("cnw_gdc_B")), LABEL_GDC),
    ]
    y = 230
    d.line([56, y, W - 56, y], fill=RULE, width=1)
    xw = (W - 112) / 3
    for i, (val, lab) in enumerate(nums):
        x = 56 + xw * i
        d.text((x, y + 16), val, font=_font(40, bold=True, sans=True), fill=INK)
        d.text((x, y + 70), lab, font=_font(18, sans=True), fill=MUT)
        if i:
            d.line([x - 16, y + 14, x - 16, y + 96], fill=RULE, width=1)
    d.line([56, y + 112, W - 56, y + 112], fill=RULE, width=1)

    extra = f"Ceiling × GDP  {fmt_mult(c.get('gdp_multiple'))}     Bankable per person  {money_pc(c.get('unlock_pc'))}"
    d.text((56, 360), extra, font=_font(20, sans=True), fill=INK)

    # readiness coupon strip
    cx, cy = 56, 404
    for lab, val in readiness_parts(c):
        txt = f"{lab} {round(val * 100)}"
        fw = _font(13, sans=True)
        ww = d.textlength(txt, font=fw) + 16
        d.rounded_rectangle([cx, cy, cx + ww, cy + 26], radius=4, outline=RULE)
        d.text((cx + 8, cy + 5), txt, font=fw, fill=MUT)
        cx += ww + 6

    verdict = c.get("verdict") or ""
    if len(verdict) > 90:
        verdict = verdict[:89].rstrip() + "…"
    d.text((56, 452), verdict, font=_font(22, italic=True), fill=INK)
    d.text((56, 500), f"As of {nice_day(c.get('as_of'))}", font=_font(16, sans=True), fill=MUT)
    return img


def save_og(c):
    os.makedirs(OG_DIR, exist_ok=True)
    dest = os.path.join(OG_DIR, f"{c['slug']}.png")
    img = draw_og(c)
    quality = 88
    while quality >= 55:
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        data = buf.getvalue()
        if len(data) <= MAX_OG_BYTES:
            open(dest, "wb").write(data)
            return dest, len(data)
        # shrink via JPEG-in-PNG isn't useful; downsample slightly
        img = img.resize((1100, 578), Image_Resampling())
        quality -= 10
    open(dest, "wb").write(data)
    return dest, len(data)


def Image_Resampling():
    from PIL import Image
    return Image.Resampling.LANCZOS


def signals_html(c):
    items = c.get("wire") or []
    if not items:
        return f'<p class="empty">{esc(live_signals_empty(items, c.get("as_of")))}</p>'
    bits = ["<ol class='signals'>"]
    for it in items:
        corr = corroboration_label(it.get("corroboration"))
        corr_h = f'<span class="corr">{esc(corr)}</span>' if corr else ""
        bits.append(
            f"<li><time datetime='{esc(it.get('date'))}'>{esc(nice_day(it.get('date'), 'short'))}</time> "
            f"<a href='{esc(it.get('url') or '/wire.html')}'>{esc(it.get('title'))}</a> "
            f"<span class='src'>{esc(it.get('source') or '')}</span> {corr_h}</li>"
        )
    bits.append("</ol>")
    return "".join(bits)


def precedents_html(c):
    rows = c.get("precedents") or []
    if not rows:
        return ""
    body = "".join(
        f"<tr><td>{esc(r['project'])}</td><td>{esc(r['scale'])}</td>"
        f"<td>{esc(r['status'])}</td><td>{esc(r['date'])}</td></tr>"
        for r in rows
    )
    return (
        "<section class='block' id='precedents'><h2>Precedents</h2>"
        "<table class='ix'><thead><tr><th>Project</th><th>Scale</th><th>Status</th><th>Date</th></tr></thead>"
        f"<tbody>{body}</tbody></table></section>"
    )


def peers_html(c):
    peers = c.get("peers") or []
    if not peers:
        return ""
    cards = []
    for p in peers:
        href = f"/{c['slug']}?compare={p['slug']}"
        cards.append(
            f"<li><a href='/{p['slug']}'>{esc(p.get('femoji') or '')} {esc(p['name'])}</a> "
            f"<span class='micro'>{esc(p['tier'])} · {fmt_rank_serial(p.get('rank'))}</span> "
            f"<a class='btn' href='{href}'>Compare countries</a></li>"
        )
    return "<section class='block' id='peers'><h2>Peers</h2><ul class='peers'>" + "".join(cards) + "</ul></section>"


def spark_data(c):
    ser = c.get("rank_series") or []
    return json.dumps([{"d": d, "r": r} for d, r in ser])


def country_page_css():
    return """
.page{display:grid;grid-template-columns:minmax(0,720px) 320px;gap:40px;align-items:start;margin:36px auto 0;max-width:1120px;padding:0 28px}
.side{position:sticky;top:16px}
.block{margin:36px 0}
.block h2{margin-bottom:12px}
.signals{list-style:none}
.signals li{padding:10px 0;border-bottom:1px solid var(--rule);font-size:16px}
.signals time,.signals .src,.signals .corr{font-family:var(--sans);font-size:13px;color:var(--muted);margin-right:8px}
.empty{color:var(--muted)}
.peers{list-style:none}
.peers li{padding:12px 0;border-bottom:1px solid var(--rule);display:flex;flex-wrap:wrap;gap:8px 14px;align-items:baseline}
.sharebar{display:flex;flex-wrap:wrap;gap:10px;margin-top:12px}
.share-fixed{display:none}
.ix{width:100%;border-collapse:collapse;font-size:15px}
.ix th,.ix td{text-align:left;padding:8px 8px 8px 0;border-bottom:1px solid var(--rule)}
.ix th{font-weight:400;color:var(--muted);font-size:13px}
.compare-note{margin-top:12px;padding:10px 12px;border:1px solid var(--rule);border-radius:4px;font-size:15px}
#spark{height:88px;margin-top:8px}
@media(max-width:768px){
  .page{grid-template-columns:1fr;padding:0 18px}
  .side{position:static}
  .share-fixed{display:flex;position:sticky;bottom:0;left:0;right:0;background:var(--paper);
    border-top:1px solid var(--rule);padding:10px 18px;gap:10px;z-index:5}
}
"""


def country_js(c):
    return f"""
(function(){{
  var data = {spark_data(c)};
  var el = document.getElementById("spark");
  if(el && data.length){{
    var w = el.clientWidth || 720, h = 88, p = 8;
    var ranks = data.map(function(d){{ return d.r; }});
    var min = 1, max = {N_COUNTRIES};
    function x(i){{ return p + (w-2*p) * (data.length===1?0.5:i/(data.length-1)); }}
    function y(r){{ return p + (h-2*p) * ((r-min)/(max-min || 1)); }}
    var d = "";
    data.forEach(function(pt,i){{ d += (i?" L":"M") + x(i).toFixed(1) + " " + y(pt.r).toFixed(1); }});
    el.innerHTML = '<svg viewBox="0 0 '+w+' '+h+'" width="100%" height="'+h+'" aria-label="Rank history">'
      + '<path d="'+d+'" fill="none" stroke="#171614" stroke-width="1.5"/></svg>';
  }}
  var share = {json.dumps(c["share"])};
  function flash(btn, ok){{ var t=btn.textContent; btn.textContent=ok; setTimeout(function(){{ btn.textContent=t; }}, 1400); }}
  document.querySelectorAll("[data-copy]").forEach(function(b){{
    b.addEventListener("click", function(){{
      var t = b.getAttribute("data-copy")==="blurb"
        ? document.getElementById("blurb").textContent
        : share;
      navigator.clipboard.writeText(t).then(function(){{ flash(b, "Copied"); }});
    }});
  }});
  var q = new URLSearchParams(location.search).get("compare");
  if(q){{
    var box = document.getElementById("compare-box");
    if(box){{
      box.hidden = false;
      box.innerHTML = "Comparing with <a href='/"+q+"'>"+q.replace(/-/g," ")+"</a>. A dedicated compare page ships in a later phase.";
    }}
  }}
}})();
"""


def render_country(c, as_of):
    title = f"{c['name']}'s Compute Net Worth · compute.world"
    url = f"{SITE}/{c['slug']}"
    og = f"og/{c['slug']}.png"
    extra = f"<style>{country_page_css()}</style>"
    ld = json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            breadcrumb_ld([
                ("compute.world", f"{SITE}/"),
                (c["name"], url),
            ]),
            {
                "@type": "WebPage",
                "name": title,
                "url": url,
                "description": c["description"],
                "author": person_author(),
                "dateModified": as_of,
            },
        ],
    })
    gdc_note = " <span class='est'>est.</span>" if c.get("lgE") and c.get("cnw_gdc_B") else ""
    three = f"""<section class="block" id="three">
  <h2>The three numbers</h2>
  <table class="ix">
    <tbody>
      <tr><th>{LABEL_CEILING}</th><td class="tnum">{money_b(c.get("cnw_ceiling_hi_B"))}</td></tr>
      <tr><th>{LABEL_UNLOCK}</th><td class="tnum">{money_b(c.get("cnw_unlockable_B"))}</td></tr>
      <tr><th>{LABEL_GDC}</th><td class="tnum">{money_b(c.get("cnw_gdc_B"))}{gdc_note}</td></tr>
      <tr><th>Ceiling as a multiple of GDP</th><td class="tnum">{fmt_mult(c.get("gdp_multiple"))}</td></tr>
      <tr><th>Bankable per person</th><td class="tnum">{money_pc(c.get("unlock_pc"))}</td></tr>
    </tbody>
  </table>
</section>"""
    return f"""{head(esc(title), esc(c["description"]), url, og, extra)}
<body>
{masthead(as_of, current="index")}
<div class="page">
  <main>
    {cert_html(c, settle=True)}
    <section class="block" id="verdict">
      <h1>{esc(c["h1"])}</h1>
      <p id="blurb">{esc(c["blurb"])}</p>
      <button class="btn" type="button" data-copy="blurb">Copy</button>
    </section>
    {three}
    <section class="block" id="history">
      <h2>Rank history</h2>
      <p class="micro">Dated observed ranks only. No interpolation.</p>
      <div id="spark"></div>
    </section>
    <section class="block" id="signals">
      <h2>Live signals</h2>
      {signals_html(c)}
    </section>
    {precedents_html(c)}
    {peers_html(c)}
    <div id="compare-box" class="compare-note" hidden></div>
    <section class="block" id="share">
      <h2>Share and cite</h2>
      <p class="small">{esc(c["share"])}</p>
      <div class="sharebar">
        <button class="btn" type="button" data-copy="share">Share this card</button>
        <a class="btn" href="https://x.com/intent/post?text={esc(c['share'])}">Post to X</a>
      </div>
    </section>
    <section class="block" id="briefing">
      <h2>Request a briefing</h2>
      <p class="small">Write the Desk about {esc(c["name"])} — conversion, a sourced print, or a correction.</p>
      <a class="btn btn-ink" href="/contact.html?country={esc(c['slug'])}">Request a briefing</a>
    </section>
  </main>
  <aside class="side">
    <table class="ix">
      <tr><th>{LABEL_CEILING}</th><td class="tnum">{money_b(c.get("cnw_ceiling_hi_B"))}</td></tr>
      <tr><th>{LABEL_UNLOCK}</th><td class="tnum">{money_b(c.get("cnw_unlockable_B"))}</td></tr>
      <tr><th>{LABEL_GDC}</th><td class="tnum">{money_b(c.get("cnw_gdc_B"))}{gdc_note}</td></tr>
    </table>
    <div class="sharebar" style="margin-top:16px">
      <button class="btn" type="button" data-copy="share">Share this card</button>
      <a class="btn btn-ink" href="/contact.html?country={esc(c['slug'])}">Request a briefing</a>
    </div>
  </aside>
</div>
<div class="share-fixed">
  <button class="btn" type="button" data-copy="share">Share this card</button>
  <a class="btn btn-ink" href="/contact.html?country={esc(c['slug'])}">Request a briefing</a>
</div>
{footer()}
<script>{country_js(c)}</script>
<script type="application/ld+json">{ld}</script>
</body></html>"""


def render_txt(c):
    gdc = money_b(c.get("cnw_gdc_B"))
    est = " (estimate)" if c.get("lgE") and c.get("cnw_gdc_B") else ""
    lines = [
        f"{c['name']}'s Compute Net Worth",
        f"compute.world/{c['slug']}",
        f"As of {nice_day(c.get('as_of'))}",
        "",
        f"Tier: {c['tier']}",
        f"Rank: {fmt_rank_serial(c.get('rank'))}",
        f"{LABEL_CEILING}: {money_b(c.get('cnw_ceiling_hi_B'))}",
        f"{LABEL_UNLOCK}: {money_b(c.get('cnw_unlockable_B'))}",
        f"{LABEL_GDC}: {gdc}{est}",
        f"Ceiling × GDP: {fmt_mult(c.get('gdp_multiple'))}",
        f"Bankable per person: {money_pc(c.get('unlock_pc'))}",
        "",
        c["blurb"],
        "",
        c["share"],
        "",
        "Cite as: Hamal, P. (2026). The Compute Net Worth Index. compute.world.",
    ]
    if c.get("wire"):
        lines.append("")
        lines.append("Live signals")
        for it in c["wire"]:
            lines.append(f"- {it.get('date')} {it.get('title')} ({it.get('source') or ''}) {it.get('url') or ''}")
    else:
        lines.append("")
        lines.append(live_signals_empty([], c.get("as_of")))
    return "\n".join(lines) + "\n"


def build(root=ROOT):
    countries, as_of, _wire, _snaps = assemble_countries()
    og_dir = os.path.join(root, "og")
    os.makedirs(og_dir, exist_ok=True)
    n = 0
    for c in countries:
        page = render_country(c, as_of)
        write(os.path.join(root, c["slug"], "index.html"), page)
        write(os.path.join(root, f"{c['slug']}.txt"), render_txt(c))
        dest, sz = save_og(c)
        # save_og writes to ROOT/og; copy if root differs
        target = os.path.join(og_dir, f"{c['slug']}.png")
        if os.path.abspath(dest) != os.path.abspath(target) and os.path.isfile(dest):
            open(target, "wb").write(open(dest, "rb").read())
        n += 1
        if n % 20 == 0:
            print(f"  {n}/{len(countries)} {c['slug']} {sz}B")
    print(f"countries: {n} pages + txt + og as of {as_of}")
    return countries, as_of


if __name__ == "__main__":
    build()
