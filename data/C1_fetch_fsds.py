"""C1 lane: download SEC Financial Statement Data Sets quarterly zips.

Endpoint: https://www.sec.gov/files/dera/data/financial-statement-data-sets/<q>.zip
Paced at 0.5s between requests (SEC limit is cumulative across hosts).
Contact string in User-Agent per campaign rule.
"""
import os, sys, time, urllib.request, hashlib

QUARTERS = ["2013q3", "2013q4", "2019q3", "2019q4", "2025q3", "2025q4"]
BASE = "https://www.sec.gov/files/dera/data/financial-statement-data-sets/"
UA = "research@backtest-framework.org"
OUT = os.path.dirname(os.path.abspath(__file__))

for q in QUARTERS:
    dest = os.path.join(OUT, f"C1_fsds_{q}.zip")
    if os.path.exists(dest) and os.path.getsize(dest) > 1_000_000:
        print(f"{q}: already have {os.path.getsize(dest):,}", flush=True)
        continue
    req = urllib.request.Request(BASE + q + ".zip", headers={"User-Agent": UA})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=300) as r:
        body = r.read()
        code = r.status
        ctype = r.headers.get("Content-Type")
    with open(dest, "wb") as f:
        f.write(body)
    # byte-level check, not status-level: a zip must start with PK
    magic = body[:2]
    print(f"{q}: HTTP {code} {ctype} {len(body):,} bytes magic={magic!r} "
          f"sha1={hashlib.sha1(body).hexdigest()[:12]} {time.time()-t0:.1f}s", flush=True)
    time.sleep(0.5)
print("DONE", flush=True)
