import json, time, urllib.request, urllib.parse, sys, gzip

UA = "Backtest-Framework-Research research@backtest-framework.org"
BASE = "https://efts.sec.gov/LATEST/search-index"

def get(params, path=BASE):
    url = path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            raw = gzip.decompress(raw)
        code = r.status
    except urllib.error.HTTPError as e:
        raw = e.read(); code = e.code
    time.sleep(0.4)
    return code, raw, url

CASES = [
 ("q impossible phrase RETRY",        {"q": '"zzqxvn nonexistent phrase tokenqq"'}),
 ("q impossible single token",        {"q": '"zzqxvnqqwwee"'}),
 ("ciks real UMH RETRY",              {"q": '"declared a quarterly dividend"', "ciks": "0000752642"}),
 ("ciks bogus RETRY",                 {"q": '"declared a quarterly dividend"', "ciks": "0000000001"}),
 ("from=40 RETRY",                    {"q": '"declared a quarterly dividend"', "forms": "8-K", "dateRange":"custom","startdt":"2021-01-01","enddt":"2021-01-31", "from": "40"}),
 ("from=9990",                        {"q": '"declared a quarterly dividend"', "from": "9990"}),
 ("from=10000",                       {"q": '"declared a quarterly dividend"', "from": "10000"}),
 ("locationCodes plural NJ",          {"q": '"declared a quarterly dividend"', "locationCodes": "NJ"}),
 ("locationCodes plural ZZ bogus",    {"q": '"declared a quarterly dividend"', "locationCodes": "ZZ"}),
 ("locationCode=CA",                  {"q": '"declared a quarterly dividend"', "locationCode": "CA"}),
 ("forms=8-K&items plural",           {"q": '"declared a quarterly dividend"', "forms": "8-K", "itemsCode": "9.99"}),
 ("category=form-type bogus",         {"q": '"declared a quarterly dividend"', "category": "not-a-category"}),
 ("bogus param entirely",             {"q": '"declared a quarterly dividend"', "zzgarbageparam": "1"}),
]
for name, p in CASES:
    code, raw, url = get(p)
    try:
        j = json.loads(raw)
        h = j.get("hits", {})
        tot = h.get("total", {})
        print(f"{name:34s} HTTP={code} total={tot} ret={len(h.get('hits',[]))} bytes={len(raw)}")
    except Exception:
        print(f"{name:34s} HTTP={code} bytes={len(raw)} BODY={raw[:300]!r}")
    sys.stdout.flush()
