"""K1 fetcher, shard N of 3.  usage: python K1_fetch_shard.py <shard>

One connection per shard at 2 req/s each (~6 req/s aggregate, under SEC's 10/s
fair-access ceiling).  Resumable: every document is cached on disk, so an
interruption or a 429 window costs nothing.
"""
import os, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "backtest-framework-research research@backtest-framework.org"
CACHE = os.path.join(HERE, "K1_doccache")
CAP = 30_000
RATE = 2.0
shard = sys.argv[1]

todo = [l.strip() for l in open(os.path.join(HERE, f"K1_tofetch_{shard}.txt"))
        if l.strip()]
print(f"shard {shard}: {len(todo)} docs", flush=True)
t0 = time.time(); ok = err = skip = 0; backoff_total = 0.0
for i, path in enumerate(todo):
    key = os.path.join(CACHE, path.replace("/", "_"))
    if os.path.exists(key):
        skip += 1
        continue
    url = "https://www.sec.gov/Archives/" + path
    for attempt in range(6):
        resp = None
        try:
            time.sleep(1.0 / RATE)
            resp = urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": UA}),
                timeout=30)
            data = resp.read(CAP)
            with open(key, "w", encoding="utf-8") as fh:
                fh.write(data.decode("utf-8", "replace"))
            ok += 1
            break
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                b = min(90, 8 * (2 ** attempt)); backoff_total += b
                print(f"  [{e.code}] backoff {b}s at {i}", flush=True)
                time.sleep(b); continue
            with open(key, "w", encoding="utf-8") as fh:
                fh.write(f"__HTTPERROR_{e.code}__")
            err += 1; break
        except Exception as e:
            if attempt < 3:
                time.sleep(3); continue
            with open(key, "w", encoding="utf-8") as fh:
                fh.write(f"__ERROR_{type(e).__name__}__")
            err += 1; break
        finally:
            try:
                if resp is not None: resp.close()
            except Exception:
                pass
    if (i + 1) % 100 == 0:
        el = time.time() - t0
        print(f"  s{shard} {i+1}/{len(todo)} ok={ok} err={err} {el:.0f}s "
              f"({(i+1)/el:.2f}/s) backoff={backoff_total:.0f}s", flush=True)
print(f"SHARD {shard} DONE ok={ok} err={err} skip={skip} "
      f"wall={time.time()-t0:.0f}s backoff={backoff_total:.0f}s")
