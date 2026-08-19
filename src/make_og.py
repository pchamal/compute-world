#!/usr/bin/env python3
# Three editorial 1200×630 unfurl cards. Paper / ink / claret. No invented numbers.
# Reads silicon.json + brief.json so prints stay sourced.
from PIL import Image, ImageDraw, ImageFont
import json, os

W, H = 1200, 630
PAPER = (247, 244, 238)
INK = (23, 22, 20)
MUT = (98, 96, 90)
RULE = (205, 199, 185)
ACC = (125, 32, 39)
GOLD = (138, 90, 42)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.makedirs(os.path.join(ROOT, "deploy"), exist_ok=True)

S = json.load(open(os.path.join(ROOT, "silicon.json")))
B = json.load(open(os.path.join(ROOT, "brief.json")))
chips = sorted(S["chips"], key=lambda c: c["rank"])
n_chips = len(chips)
by_id = {c["id"]: c for c in chips}

def catalog_counts(name):
    d = json.load(open(os.path.join(ROOT, f"{name}.json")))
    n_loc = sum(len(p.get("locations") or []) for p in d["providers"])
    return d.get("count") or len(d["providers"]), n_loc, d.get("as_of") or ""


def F(sz, bold=False, italic=False):
    cands = (
        ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"] if bold else
        ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"] if italic else
        ["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"]
    )
    for c in cands:
        try:
            return ImageFont.truetype(c, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def money(x):
    if x is None:
        return "—"
    s = f"{x:.3f}"
    if s.endswith("0"):
        s = s[:-1]
    return f"${s}"


def chip_px(c):
    d = c.get("display") or {}
    if d.get("primary") == "CNY" and d.get("cny_per_gpu_hr") is not None:
        return f"¥{d['cny_per_gpu_hr']:.2f}"
    if d.get("usd_per_gpu_hr") is None:
        return d.get("label") or "—"
    return money(d["usd_per_gpu_hr"])


def new_card():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    return img, d


def ctext(d, y, txt, f, fill, tracking=0):
    if tracking:
        widths = [d.textlength(ch, font=f) + tracking for ch in txt]
        total = sum(widths) - tracking
        x = (W - total) / 2
        for ch, w in zip(txt, widths):
            d.text((x, y), ch, font=f, fill=fill)
            x += w
    else:
        d.text(((W - d.textlength(txt, font=f)) / 2, y), txt, font=f, fill=fill)


def masthead(d, kicker):
    d.rectangle([70, 44, W - 70, 47], fill=INK)
    d.rectangle([70, 51, W - 70, 52], fill=INK)
    ctext(d, 68, "C O M P U T E . W O R L D", F(26, bold=True), INK, tracking=6)
    ctext(d, 108, kicker, F(15), MUT, tracking=4)


def footer(d, line="compute.world"):
    d.rectangle([70, 586, W - 70, 587], fill=RULE)
    ctext(d, 596, line, F(18), MUT)


def stat_strip(d, stats, y=458, h=108):
    d.rectangle([70, y, W - 70, y + 1], fill=RULE)
    n = len(stats)
    xw = (W - 140) / n
    for i, (v, lab, gold) in enumerate(stats):
        cx = 70 + xw * i + xw / 2
        vf = F(40, bold=True) if len(v) > 8 else F(44, bold=True)
        d.text((cx - d.textlength(v, font=vf) / 2, y + 16), v, font=vf, fill=GOLD if gold else INK)
        d.text((cx - d.textlength(lab, font=F(16)) / 2, y + 70), lab, font=F(16), fill=MUT)
        if i:
            d.line([70 + xw * i, y + 14, 70 + xw * i, y + h - 16], fill=RULE, width=1)
    d.rectangle([70, y + h, W - 70, y + h + 1], fill=RULE)


def save(img, name):
    dest = os.path.join(ROOT, name)
    img.save(dest, optimize=True)
    print(name, img.size)


# ---- 1. Hero: the world's compute & silicon index (paired stats, not a lonely $662T) ----
img, d = new_card()
masthead(d, "THE WORLD'S COMPUTE  &  SILICON INDEX")
ctext(d, 168, "The world's compute", F(48, italic=True), INK)
ctext(d, 228, "& silicon index", F(48, italic=True), ACC)
ctext(d, 300, "CNW™ prices the host. The Silicon Tape prints the chip.", F(22), MUT)
ctext(d, 338, "Two tapes. One index. No invented moves.", F(22), MUT)
b200 = by_id["nvidia-b200-sxm6"]
stat_strip(d, [
    ("$662T", "CNW ceiling", False),
    ("108", "countries priced", False),
    (money(b200["display"]["usd_per_gpu_hr"]), "B200 Lambda OD", True),
    (str(n_chips), "chips on the tape", True),
])
footer(d, "compute.world  ·  CNW™  ·  GDC™  ·  Silicon Tape")
save(img, "og.png")

# ---- 2. Silicon Tape: real sourced prints ----
img, d = new_card()
masthead(d, "THE SILICON TAPE")
ctext(d, 160, "The rental tape,", F(44, italic=True), INK)
ctext(d, 216, "as printed.", F(44, italic=True), ACC)
ctext(d, 278, f"Snapshot {S['updated']}  ·  SA prints as-of April 2026  ·  {n_chips} chips", F(18), MUT)

show_ids = [
    "nvidia-b200-sxm6",
    "nvidia-h100-sxm-80gb",
    "huawei-ascend-910c",
    "cerebras-wse3",
]
prints = []
for i in show_ids:
    c = by_id[i]
    lab = c["display"].get("label") or ""
    px = chip_px(c)
    if px == "token / enterprise":
        px = "token / ent."
        lab = "Cerebras Cloud"
    if lab.startswith("SMM Beijing"):
        lab = "SMM Beijing · 1y"
    name = c["name"]
    if name == "H100 SXM 80GB":
        name = "H100 SXM"
    prints.append((name, px, lab, i == "huawei-ascend-910c"))

d.rectangle([70, 330, W - 70, 331], fill=RULE)
xw = (W - 140) / 4
for i, (name, px, lab, gold) in enumerate(prints):
    cx = 70 + xw * i + xw / 2
    d.text((cx - d.textlength(name, font=F(18, bold=True)) / 2, 352), name, font=F(18, bold=True), fill=INK)
    pf = F(36, bold=True) if len(px) < 12 else F(26, bold=True)
    d.text((cx - d.textlength(px, font=pf) / 2, 390), px, font=pf, fill=GOLD if gold else ACC)
    d.text((cx - d.textlength(lab, font=F(15)) / 2, 442), lab, font=F(15), fill=MUT)
    if i:
        d.line([70 + xw * i, 348, 70 + xw * i, 478], fill=RULE, width=1)
d.rectangle([70, 500, W - 70, 501], fill=RULE)
ctext(d, 518, "Labeled terms. Not averages. Not a market cap. Not a 7-day sheet.", F(18, italic=True), MUT)
footer(d, "compute.world/silicon  ·  The Silicon Tape")
save(img, "og-silicon.png")

# ---- 3. Daily tape: do not reuse the $662T poster ----
img, d = new_card()
masthead(d, "THE DAILY TAPE")
title = B.get("title") or "The daily tape"
ctext(d, 168, "The daily tape,", F(46, italic=True), INK)
ctext(d, 226, "as printed.", F(46, italic=True), ACC)
ctext(d, 292, B.get("og_kicker") or "Country conversion signals and sourced silicon prints.", F(20), MUT)
ctext(d, 326, "Labeled terms only. No invented 7-day moves.", F(20), MUT)

si = B.get("silicon") or []
# Four sourced display rows for the strip — prefer B200, H100, 910C, Cerebras when present.
want = ["nvidia-b200-sxm6", "nvidia-h100-sxm-80gb", "huawei-ascend-910c", "cerebras-wse3"]
picked = []
have = {r["id"]: r for r in si}
for i in want:
    if i in have:
        picked.append(have[i])
for r in si:
    if r["id"] not in {p["id"] for p in picked}:
        picked.append(r)
    if len(picked) == 4:
        break
stats = []
for r in picked[:4]:
    cid = r["id"]
    if cid in by_id:
        px = chip_px(by_id[cid])
    elif r.get("display_usd") is None:
        px = "—"
    else:
        px = money(r.get("display_usd"))
    if px == "token / enterprise":
        px = "token / ent."
    name = r["name"]
    if name == "H100 SXM 80GB":
        name = "H100 SXM"
    if name == "B200 SXM6":
        name = "B200"
    stats.append((px, name, False))
if stats:
    stat_strip(d, stats, y=388, h=110)
footer(d, f"compute.world/brief  ·  {B.get('updated', '')}")
save(img, "og-brief.png")

# ---- 4–6. Directory unfurls: sourced counts only. No valuations on a cloud logo. ----
for slug, kicker, line1, line2, sub in (
    ("inference", "THE INFERENCE INDEX", "Who sells", "the tokens.", "Token APIs. China and the EU stay listed when the city is undisclosed."),
    ("neoclouds", "THE NEOCLOUD INDEX", "Who rents", "the GPUs.", "Dedicated clusters. State-only rows stay state-only. Not a market cap."),
    ("hyperscalers", "THE HYPERSCALER INDEX", "Who runs", "the general cloud.", "Full IaaS that also has GPUs. Scaleway and OVH live here, not as neoclouds."),
):
    n_prov, n_loc, as_of = catalog_counts(slug)
    img, d = new_card()
    masthead(d, kicker)
    ctext(d, 168, line1, F(46, italic=True), INK)
    ctext(d, 226, line2, F(46, italic=True), ACC)
    ctext(d, 300, sub, F(20), MUT)
    ctext(d, 334, "Sourced catalogs. No invented cities. No market caps.", F(20), MUT)
    stat_strip(d, [
        (str(n_prov), "providers", False),
        (str(n_loc), "location rows", False),
        (as_of or "—", "snapshot", True),
        ("named", "cities only plotted", True),
    ], y=388, h=110)
    footer(d, f"compute.world/{slug}  ·  {kicker.title()}")
    save(img, f"og-{slug}.png")
