"""Haftalık trend taraması: bu ay yükselen çocuk videoları ve yeni, hızlı büyüyen kanallar.

  python trends.py trends.json
"""
import json, re, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-US,en"}
# sp=CAMSAggE: sort by views, uploaded this month; CAMSAggD: this week
FILTERS = ["CAMSAggE", "CAMSBAgEGAM", "CAMSBAgEGAI"]  # bu ay: tümü, 4-20 dk, >20 dk
QUERIES = [
    "nursery rhymes", "kids songs", "baby songs", "toddler learning", "cartoon for kids", "kids songs compilation",
    "bedtime songs for babies", "learn colors", "abc song", "kids story",
    "canciones infantiles", "canciones para niños", "dibujos animados para niños", "videos para bebés", "cuentos infantiles",
    "musica infantil", "desenho animado infantil", "musicas para bebe",
    "hindi rhymes", "बच्चों के गाने", "अंग्रेजी कविता",
    "أغاني أطفال", "lagu anak", "kinderlieder", "comptines", "детские песни", "童谣", "子供 歌",
]

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")

def initial_data(html):
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.S)
    return json.loads(m.group(1)) if m else {}

def walk(o, key):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == key: yield v
            yield from walk(v, key)
    elif isinstance(o, list):
        for i in o: yield from walk(i, key)

def views(t):
    t = re.sub(r"[^\d]", "", t or "")
    return int(t) if t else 0

def search(q, sp):
    url = "https://www.youtube.com/results?" + urllib.parse.urlencode({"search_query": q, "sp": sp})
    try: d = initial_data(get(url))
    except Exception as e: return []
    out = []
    for v in walk(d, "videoRenderer"):
        try:
            ch = v["ownerText"]["runs"][0]
            out.append({
                "q": q, "title": v["title"]["runs"][0]["text"],
                "vid": v["videoId"], "views": views(v.get("viewCountText", {}).get("simpleText")),
                "pub": v.get("publishedTimeText", {}).get("simpleText", ""),
                "len": v.get("lengthText", {}).get("simpleText", ""),
                "cid": ch["navigationEndpoint"]["browseEndpoint"]["browseId"], "ch": ch["text"],
            })
        except KeyError: pass
    return out

def about(cid):
    try: h = get(f"https://www.youtube.com/channel/{cid}/about")
    except Exception: return cid, {}
    g = lambda p: (re.search(p, h) or [None, None])[1]
    return cid, {
        "joined": g(r'"joinedDateText":\{"content":"Joined ([^"]+)"'),
        "subs": g(r'"subscriberCountText":"([^"]+)"'),
        "videos": g(r'"videoCountText":"([^"]+)"'),
        "totalviews": g(r'"viewCountText":"([\d,]+) views"'),
        "country": g(r'"country":"([^"]+)"'),
    }

jobs = [(q, sp) for q in QUERIES for sp in FILTERS]
with ThreadPoolExecutor(8) as ex:
    vids = [v for r in ex.map(lambda a: search(*a), jobs) for v in r]
chans = {}
for v in vids:
    c = chans.setdefault(v["cid"], {"ch": v["ch"], "vids": {}, "qs": set()})
    c["vids"][v["vid"]] = v; c["qs"].add(v["q"])
with ThreadPoolExecutor(8) as ex:
    for cid, info in ex.map(about, list(chans)):
        chans[cid].update(info)
res = []
for cid, c in chans.items():
    top = sorted(c["vids"].values(), key=lambda x: -x["views"])
    res.append({"cid": cid, "ch": c["ch"], **{k: c.get(k) for k in ["joined", "subs", "videos", "totalviews", "country"]},
                "qs": sorted(c["qs"]), "recent_views": sum(v["views"] for v in top),
                "top": [{k: v[k] for k in ["title", "views", "pub", "len", "vid"]} for v in top[:3]]})
json.dump(res, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
print(len(vids), "videos", len(res), "channels")
