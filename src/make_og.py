#!/usr/bin/env python3
# Editorial OG card 1200x630 for X/LinkedIn unfurls
from PIL import Image, ImageDraw, ImageFont
W,H = 1200,630
PAPER=(247,244,238); INK=(23,22,20); MUT=(98,96,90); RULE=(205,199,185); ACC=(125,32,39); GOLD=(138,90,42)
img = Image.new("RGB",(W,H),PAPER); d = ImageDraw.Draw(img)
def F(sz, bold=False, italic=False):
    cands = (["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"] if bold else
             ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"] if italic else
             ["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"])
    for c in cands:
        try: return ImageFont.truetype(c, sz)
        except: pass
    return ImageFont.load_default()
def ctext(y, txt, f, fill, tracking=0):
    if tracking:
        widths=[d.textlength(ch,font=f)+tracking for ch in txt]; total=sum(widths)-tracking
        x=(W-total)/2
        for ch,w in zip(txt,widths): d.text((x,y),ch,font=f,fill=fill); x+=w
    else:
        d.text(((W-d.textlength(txt,font=f))/2,y),txt,font=f,fill=fill)
# masthead
d.rectangle([70,54,W-70,57],fill=INK); d.rectangle([70,61,W-70,62],fill=INK)
ctext(84,"C O M P U T E . W O R L D",F(30,bold=True),INK,tracking=6)
ctext(128,"THE COMPUTE NET WORTH INDEX",F(17),MUT,tracking=5)
# hero number
ctext(190,"$662 Trillion",F(120,bold=True),INK)
ctext(330,"Every country has a Compute Net Worth.",F(40,italic=True),INK)
ctext(388,"The world has tapped 0.7% of it.",F(40,italic=True),ACC)
# stat strip
d.rectangle([70,472,W-70,473],fill=RULE)
stats=[("108","countries priced"),("$64T","unlockable today"),("44","sleeping giants"),("836x","Bhutan vs its GDP")]
xw=(W-140)/4
for i,(v,l) in enumerate(stats):
    cx=70+xw*i+xw/2
    d.text((cx-d.textlength(v,font=F(44,bold=True))/2,488),v,font=F(44,bold=True),fill=GOLD if i in (2,3) else INK)
    d.text((cx-d.textlength(l,font=F(19))/2,545),l,font=F(19),fill=MUT)
    if i: d.line([70+xw*i,486,70+xw*i,570],fill=RULE,width=1)
d.rectangle([70,586,W-70,587],fill=RULE)
ctext(596,"compute.world",F(20),MUT)
img.save("deploy/og.png",optimize=True)
print("og.png", img.size)
