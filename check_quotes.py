"""Send each job from your quotes file to the running API and compare with the quoted price.
Start the server first (uvicorn app:app --port 8000 in another terminal), then just run this file.
It looks for ../data/nairobi_quotes.csv next to the engine folder; pass a .csv path to use another file.
"""
import os, sys, csv, json, urllib.request

URL = "http://localhost:8000/diagnose"
here = os.path.dirname(os.path.abspath(__file__))
args = [a for a in sys.argv[1:] if a.lower().endswith(".csv")]
path = args[0] if args else os.path.join(here, "..", "data", "nairobi_quotes.csv")
if not os.path.exists(path):
    sys.exit(f"Quotes file not found: {path}")
rows = list(csv.DictReader(open(path, encoding="utf-8")))
print(f"{'job':45s} {'trade ok':8s} {'group':24s} {'conf':>5s} {'range':>14s} {'mid':>6s} {'quote':>6s} {'in range':>8s}")
inside = trade_ok = n = 0
for r in rows:
    req = urllib.request.Request(URL, json.dumps({"text": r["ask_the_fundi"]}).encode(), {"Content-Type": "application/json"})
    out = json.load(urllib.request.urlopen(req))
    quote = float(r["price_kes"]); n += 1
    if out["status"] != "ok":
        print(f"{r['ask_the_fundi'][:44]:45s} unknown (conf {out['confidence']})"); continue
    p = out["price"]; ok_t = out["trade"] == r["trade"]; ok_r = p["low"] <= quote <= p["high"]
    trade_ok += ok_t; inside += ok_r
    print(f"{r['ask_the_fundi'][:44]:45s} {str(ok_t):8s} {out['group']:24s} {out['confidence']:5.2f} {str(p['low'])+'-'+str(p['high']):>14s} {p['mid']:6d} {quote:6.0f} {str(ok_r):>8s}")
print(f"\ntrade correct: {trade_ok}/{n} | quote inside the range: {inside}/{n}")
print("Note: these quotes were also used to calibrate the rupee-to-shilling conversion, so this is a check of the whole pipeline, not an independent test.")
