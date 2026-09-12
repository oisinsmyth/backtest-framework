"""D2 lane: download SEC Financial Statement Data Sets quarterly zips.

Endpoint: https://www.sec.gov/files/dera/data/financial-statement-data-sets/<q>.zip
Paced 0.5s (SEC's limit is CUMULATIVE across hosts, not burst).
Contact string per campaign rule: research@backtest-framework.org
Reports real bytes + magic for each, so a 200 carrying HTML is visible.
"""
import os, time, urllib.request, urllib.error, hashlib

QUARTERS = [f"{y}q{q}" for y in (2021, 2022, 2023, 2024) for q in (1, 2, 3, 4)]
QUARTERS = QUARTERS[3:]  # 2021q4 .. 2024q4 = 13 zips
BASE = "https://www.sec.gov/files/dera/data/financial-statement-data-sets/"
UA = "backtest-framework-research research@backtest-framework.org"
OUT = os.path.dirname(os.path.abspath(__file__))

print("quarters:", QUARTERS, flush=True)
total = 0
for q in QUARTERS:
    dest = os.path.join(OUT, f"D2_fsds_{q}.zip")
    if os.path.exists(dest) and os.path.getsize(dest) > 1_000_000:
        print(f"{q}: have {os.path.getsize(dest):,}", flush=True)
        total += os.path.getsize(dest)
        continue
    req = urllib.request.Request(BASE + q + ".zip", headers={"User-Agent": UA})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            body = r.read()
            code, ctype = r.status, r.headers.get("Content-Type")
    except urllib.error.HTTPError as e:
        print(f"{q}: HTTP {e.code} {e.headers.get('Content-Type')} "
              f"body={len(e.read())}B -- NOT SAVED", flush=True)
        time.sleep(0.5)
        continue
    except Exception as e:
        print(f"{q}: EXC {type(e).__name__}: {e}", flush=True)
        time.sleep(0.5)
        continue
    ok = body[:2] == b"PK"
    print(f"{q}: HTTP {code} ctype={ctype} bytes={len(body):,} "
          f"magic={body[:4]!r} zip={ok} sha1={hashlib.sha1(body).hexdigest()[:12]} "
          f"{time.time()-t0:.1f}s", flush=True)
    if not ok:
        print(f"  !! WRONG-200: {q}.zip did not return PK magic -- NOT SAVED", flush=True)
        time.sleep(0.5)
        continue
    with open(dest, "wb") as f:
        f.write(body)
    total += len(body)
    time.sleep(0.5)

# NEGATIVE CONTROL: a quarter that CANNOT exist must not return a zip.
for bogus in ("2099q1", "2021q5"):
    req = urllib.request.Request(BASE + bogus + ".zip", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            b = r.read()
        print(f"CONTROL {bogus}: HTTP {r.status} bytes={len(b):,} magic={b[:4]!r} "
              f"<-- EXPECTED A FAILURE", flush=True)
    except urllib.error.HTTPError as e:
        print(f"CONTROL {bogus}: HTTP {e.code} (expected non-200) OK", flush=True)
    except Exception as e:
        print(f"CONTROL {bogus}: {type(e).__name__} (expected failure) OK", flush=True)
    time.sleep(0.5)

print(f"TOTAL BYTES {total:,}", flush=True)
