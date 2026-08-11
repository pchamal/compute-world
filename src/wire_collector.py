#!/usr/bin/env python3
# The Wire collector: gathers candidate signals from GDELT (free, no key) and Google News RSS,
# dedupes, pre-scores by source tier + specificity, and writes wire-inbox.json for HUMAN review.
# Nothing auto-publishes. Promote items by copying them (edited) into wire.json, then run build_wire.py.
# Run:  python3 src/wire_collector.py     (stdlib only, no dependencies)
import json, re, os, urllib.request, urllib.parse, xml.etree.ElementTree as ET
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
UA = {"User-Agent": "compute-world-wire/1.0 (+https://compute.world; hello contact page)"}

QUERIES = [
    '"AI factory" (gigawatt OR megawatt OR sovereign)',
    '"sovereign AI" (datacenter OR "data center" OR infrastructure)',
    '("AI data center" OR "AI datacenter") (billion OR gigawatt) government',
    'NVIDIA (sovereign OR country OR government) "AI infrastructure"',
    '"compute" (hydropower OR geothermal OR "stranded gas") datacenter',
    '(Stargate OR "AI campus") (MW OR GW) announcement',
]
TIER2 = ["reuters.com","bloomberg.com","ft.com","wsj.com","cnbc.com","nikkei.com","asia.nikkei.com","cnn.com","apnews.com","economist.com"]
TIER1_HINTS = ["gov","europa.eu","federalregister.gov","gao.gov","nvidia.com","openai.com","investor."]
TIER3 = ["datacenterdynamics.com","semianalysis.com","techcrunch.com","theregister.com","datacenterfrontier.com","datacentremagazine.com","tomshardware.com","siliconangle.com"]
SPEC = re.compile(r"(\b\d+(\.\d+)?\s?(MW|GW|megawatt|gigawatt)|\$\s?\d+|\d+[,.]?\d*\s?(billion|million)|\b\d{2,3},?\d{3}\s?(GPU|chip))", re.I)

def tier_of(url):
    d = urllib.parse.urlparse(url).netloc.lower()
    if any(h in d for h in TIER1_HINTS): return 1
    if any(t in d for t in TIER2): return 2
    if any(t in d for t in TIER3): return 3
    return 4

def fetch(url, timeout=25):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
            return r.read().decode("utf-8", "ignore")
    except Exception as e:
        print("  fetch failed:", url[:80], e); return ""

def gdelt(q, days=8):
    u = ("https://api.gdeltproject.org/api/v2/doc/doc?query=" + urllib.parse.quote(q) +
         "&mode=artlist&maxrecords=40&format=json&timespan=" + str(days) + "d&sort=hybridrel")
    raw = fetch(u)
    try: arts = json.loads(raw).get("articles", [])
    except Exception: arts = []
    return [{"title": a.get("title",""), "url": a.get("url",""), "source": a.get("domain",""),
             "date": (a.get("seendate","")[:8] and datetime.strptime(a["seendate"][:8], "%Y%m%d").strftime("%Y-%m-%d")) or "",
             "via": "gdelt", "country_hint": a.get("sourcecountry","")} for a in arts]

def gnews(q, days=8):
    u = "https://news.google.com/rss/search?q=" + urllib.parse.quote(q + " when:" + str(days) + "d") + "&hl=en-US&gl=US&ceid=US:en"
    raw = fetch(u)
    out = []
    try:
        for it in ET.fromstring(raw).iter("item"):
            t = it.findtext("title") or ""; l = it.findtext("link") or ""
            d = it.findtext("pubDate") or ""
            try: d = datetime.strptime(d[:16].strip(), "%a, %d %b %Y").strftime("%Y-%m-%d")
            except Exception: d = ""
            src = (it.findtext("source") or "").strip()
            out.append({"title": t, "url": l, "source": src, "date": d, "via": "gnews", "country_hint": ""})
    except Exception as e:
        print("  gnews parse failed:", e)
    return out

def norm_title(t): return re.sub(r"[^a-z0-9 ]", "", t.lower())[:80]

def main():
    seen, cands = set(), []
    published = {i["url"] for i in json.load(open(os.path.join(ROOT, "wire.json")))["items"]}
    for q in QUERIES:
        print("query:", q)
        for a in gdelt(q) + gnews(q):
            if not a["title"] or not a["url"] or a["url"] in published: continue
            k = norm_title(a["title"])
            if k in seen: continue
            seen.add(k)
            spec = 1.0 if len(SPEC.findall(a["title"])) >= 2 else 0.6 if SPEC.search(a["title"]) else 0.25
            tier = tier_of(a["url"])
            tier_f = {1: 1.0, 2: 0.85, 3: 0.7, 4: 0.5, 5: 0.25}[tier]
            a.update(tier=tier, prescore=round(100 * (0.55 * tier_f + 0.45 * spec)),
                     corroboration="Single-source", note="REVIEW: verify, corroborate, summarize, tag countries")
            cands.append(a)
    cands.sort(key=lambda a: -a["prescore"])
    out = {"generated": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
           "note": "Machine-gathered candidates. Human review required before any item enters wire.json.",
           "candidates": cands[:60]}
    json.dump(out, open(os.path.join(ROOT, "wire-inbox.json"), "w"), indent=1, ensure_ascii=False)
    print(f"wire-inbox.json: {len(out['candidates'])} candidates")

if __name__ == "__main__":
    main()
