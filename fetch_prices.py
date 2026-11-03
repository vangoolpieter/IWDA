import csv, io, json, os, sys, urllib.request, datetime as dt

UA = {"User-Agent": "Mozilla/5.0"}

# Voeg hier een regel toe per ETF. "file" = bestand in de repo, "start" = eerste datum die bewaard wordt.
# "append_only": True = bestaande koersen (uit je CSV) blijven staan, enkel nieuwe dagen worden toegevoegd.
INSTRUMENTS = [
    {"file": "data.json", "start": "2026-05-26", "stooq": "iwda.nl", "yahoo": "IWDA.AS"},
    {"file": "swrd.json", "start": "2026-08-24", "stooq": "swrd.nl", "yahoo": "SWRD.AS", "append_only": True},
]


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read().decode()


def stooq(sym):
    txt = get(f"https://stooq.com/q/d/l/?s={sym}&i=d")
    rows = list(csv.DictReader(io.StringIO(txt)))
    out = [[r["Date"], round(float(r["Close"]), 3)] for r in rows if r.get("Close")]
    if not out:
        raise ValueError("stooq leeg")
    return out


def yahoo(sym):
    d = json.loads(get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=1y&interval=1d"))
    res = d["chart"]["result"][0]
    out = []
    for t, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]):
        if c is not None:
            out.append([dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d"), round(c, 3)])
    if not out:
        raise ValueError("yahoo leeg")
    return out


def update(inst):
    new, src = None, None
    for name, fn, sym in (("stooq", stooq, inst["stooq"]), ("yahoo", yahoo, inst["yahoo"])):
        try:
            new = fn(sym)
            src = name
            break
        except Exception as e:
            print(f"{inst['file']}: {name} mislukt: {e}", file=sys.stderr)
    if not new:
        return False
    data = json.load(open(inst["file"])) if os.path.exists(inst["file"]) else {"prices": []}
    prices = {d: p for d, p in data.get("prices", [])}
    for d, p in new:
        if d >= inst["start"] and not (inst.get("append_only") and d in prices):
            prices[d] = p
    data["prices"] = sorted([d, p] for d, p in prices.items())
    data["updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    data["source"] = src
    json.dump(data, open(inst["file"], "w"), indent=1)
    print("ok", inst["file"], src, len(data["prices"]), "punten")
    return True


def main():
    results = [update(i) for i in INSTRUMENTS]   # elk instrument apart, \u00e9\u00e9n fout stopt de andere niet
    if not all(results):
        sys.exit("Minstens \u00e9\u00e9n ETF kon niet worden bijgewerkt")


if __name__ == "__main__":
    main()
