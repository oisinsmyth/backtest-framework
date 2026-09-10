import json, time, urllib.request, urllib.parse, sys

UA = "Backtest-Framework-Research research@backtest-framework.org"
BASE = "https://efts.sec.gov/LATEST/search-index"

def get(params, path=BASE):
    url = path + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate", "Host": "efts.sec.gov"})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        raw = r.read()
        if r.headers.get("Content-Encoding") == "gzip":
            import gzip; raw = gzip.decompress(raw)
        code = r.status
    except urllib.error.HTTPError as e:
        raw = e.read(); code = e.code
    time.sleep(0.35)
    return code, raw, url

def count(params):
    code, raw, url = get(params)
    try:
        j = json.loads(raw)
        tot = j.get("hits", {}).get("total", {}).get("value")
        nret = len(j.get("hits", {}).get("hits", []))
    except Exception as e:
        tot = "PARSE_FAIL:" + str(e)[:60]; nret = None
    return code, tot, nret, len(raw), url

CASES = [
 ("baseline q only",                       {"q": '"declared a quarterly dividend"'}),
 ("+ forms=8-K",                           {"q": '"declared a quarterly dividend"', "forms": "8-K"}),
 ("+ forms=ZZ-NOTAFORM (must be 0)",       {"q": '"declared a quarterly dividend"', "forms": "ZZ-NOTAFORM"}),
 ("+ forms=10-K",                          {"q": '"declared a quarterly dividend"', "forms": "10-K"}),
 ("+ items=8.01",                          {"q": '"declared a quarterly dividend"', "forms": "8-K", "items": "8.01"}),
 ("+ items=9.99 impossible (must be 0)",   {"q": '"declared a quarterly dividend"', "forms": "8-K", "items": "9.99"}),
 ("+ items=5.02 (wrong item)",             {"q": '"declared a quarterly dividend"', "forms": "8-K", "items": "5.02"}),
 ("+ items=GARBAGE (must be 0)",           {"q": '"declared a quarterly dividend"', "forms": "8-K", "items": "GARBAGE"}),
 ("dates 2021-01",                         {"q": '"declared a quarterly dividend"', "forms": "8-K", "dateRange": "custom", "startdt": "2021-01-01", "enddt": "2021-01-31"}),
 ("dates 1995 (pre-2001, must be 0)",      {"q": '"declared a quarterly dividend"', "forms": "8-K", "dateRange": "custom", "startdt": "1995-01-01", "enddt": "1995-12-31"}),
 ("dates 2000 (pre-coverage?)",            {"q": '"declared a quarterly dividend"', "forms": "8-K", "dateRange": "custom", "startdt": "2000-01-01", "enddt": "2000-12-31"}),
 ("dates 2001 (claimed start)",            {"q": '"declared a quarterly dividend"', "forms": "8-K", "dateRange": "custom", "startdt": "2001-01-01", "enddt": "2001-12-31"}),
 ("dates 2004",                            {"q": '"declared a quarterly dividend"', "forms": "8-K", "dateRange": "custom", "startdt": "2004-01-01", "enddt": "2004-12-31"}),
 ("dates inverted (must be 0)",            {"q": '"declared a quarterly dividend"', "forms": "8-K", "dateRange": "custom", "startdt": "2021-12-31", "enddt": "2021-01-01"}),
 ("ciks bogus 0000000000 (must be 0)",     {"q": '"declared a quarterly dividend"', "ciks": "0000000000"}),
 ("ciks real 0000752642 UMH",              {"q": '"declared a quarterly dividend"', "ciks": "0000752642"}),
 ("locationCode=NJ",                       {"q": '"declared a quarterly dividend"', "locationCode": "NJ"}),
 ("locationCode=ZZ bogus (must be 0)",     {"q": '"declared a quarterly dividend"', "locationCode": "ZZ"}),
 ("q impossible phrase (must be 0)",       {"q": '"zzqxvn nonexistent phrase tokenqq"'}),
 ("from=9990 deep paging",                 {"q": '"declared a quarterly dividend"', "forms": "8-K", "dateRange": "custom", "startdt": "2021-01-01", "enddt": "2021-01-31", "from": "9990"}),
 ("from=40 paging",                        {"q": '"declared a quarterly dividend"', "forms": "8-K", "dateRange": "custom", "startdt": "2021-01-01", "enddt": "2021-01-31", "from": "40"}),
 ("hits=100 (page size param?)",           {"q": '"declared a quarterly dividend"', "forms": "8-K", "dateRange": "custom", "startdt": "2021-01-01", "enddt": "2021-01-31", "hits": "100"}),
]

for name, p in CASES:
    code, tot, nret, nb, url = count(p)
    print(f"{name:42s} HTTP={code} total={tot} returned={nret} bytes={nb}")
    sys.stdout.flush()
