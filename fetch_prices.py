import csv, io, json, sys, urllib.request, datetime as dt
START = "2026-05-26"
UA = {"User-Agent": "Mozilla/5.0"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode()

def stooq():
    txt = get("https://stooq.com/q/d/l/?s=iwda.nl&i=d")
    rows = list(csv.DictReader(io.StringIO(txt)))
    out = [[r["Date"], round(float(r["Close"]), 2)] for r in rows if r.get("Close")]
    if not out: raise ValueError("stooq leeg")
    return out

def yahoo():
    d = json.loads(get("https://query1.finance.yahoo.com/v8/finance/chart/IWDA.AS?range=1y&interval=1d"))
    res = d["chart"]["result"][0]
    out = []
    for t, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]):
        if c is not None:
            out.append([dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d"), round(c, 2)])
    if not out: raise ValueError("yahoo leeg")
    return out

new = None
for name, fn in (("stooq", stooq), ("yahoo", yahoo)):
    try:
        new = fn(); src = name; break
    except Exception as e:
        print(f"{name} mislukt: {e}", file=sys.stderr)
if not new:
    sys.exit("Geen bron werkte")

data = json.load(open("data.json"))
prices = {d: p for d, p in data["prices"]}
for d, p in new:
    if d >= START: prices[d] = p
data["prices"] = sorted([d, p] for d, p in prices.items())
data["updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
data["source"] = src
json.dump(data, open("data.json", "w"), indent=1)
print("ok", src, len(data["prices"]), "punten")
