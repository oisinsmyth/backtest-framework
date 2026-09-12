import time, urllib.request, sys, datetime, json

UA = "Backtest-Framework-Research research@backtest-framework.org"

def head(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
    try:
        r = urllib.request.urlopen(req, timeout=90)
        time.sleep(0.4)
        return r.status, r.headers.get("Content-Length")
    except urllib.error.HTTPError as e:
        time.sleep(0.4); return e.code, None
    except Exception as e:
        time.sleep(0.4); return "ERR", None

# sample: first wednesday-ish mid-month trading days, 2 per year
samples = []
for y in range(2010, 2027):
    for (m, d) in [(3, 10), (9, 15)]:
        if y == 2026 and m == 9: continue
        samples.append(datetime.date(y, m, d))

rows = []
for dt in samples:
    # walk forward to a day the feed exists (weekend/holiday)
    for off in range(0, 5):
        dd = dt + datetime.timedelta(days=off)
        q = (dd.month - 1)//3 + 1
        url = f"https://www.sec.gov/Archives/edgar/Feed/{dd.year}/QTR{q}/{dd.strftime('%Y%m%d')}.nc.tar.gz"
        code, cl = head(url)
        if code == 200 and cl:
            rows.append((str(dd), int(cl)))
            print(f"{dd}  {int(cl):>12,}  ({int(cl)/1e6:.0f} MB)")
            sys.stdout.flush()
            break
    else:
        print(f"{dt}  NOT FOUND in 5-day window")
        sys.stdout.flush()

json.dump(rows, open("A4_feed_sizes.json","w"))
if rows:
    import statistics
    vals = [v for _, v in rows]
    print(f"\nn={len(vals)} mean={statistics.mean(vals)/1e6:.0f} MB median={statistics.median(vals)/1e6:.0f} MB")
    print(f"implied total over ~4187 trading days at mean: {statistics.mean(vals)*4187/1e12:.2f} TB")
