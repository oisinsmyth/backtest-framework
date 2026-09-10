import time, urllib.request, sys, gzip, json

UA = "Backtest-Framework-Research research@backtest-framework.org"

def head(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
    try:
        r = urllib.request.urlopen(req, timeout=90)
        cl = r.headers.get("Content-Length"); ct = r.headers.get("Content-Type")
        lm = r.headers.get("Last-Modified"); ar = r.headers.get("Accept-Ranges")
        code = r.status
    except urllib.error.HTTPError as e:
        cl = ct = lm = ar = None; code = e.code
    except Exception as e:
        cl = ct = lm = ar = None; code = "ERR:"+str(e)[:40]
    time.sleep(0.4)
    return code, cl, ct, lm, ar

URLS = [
 # full-text search JSON / docs
 "https://www.sec.gov/Archives/edgar/full-index/2021/QTR1/form.idx",
 "https://www.sec.gov/Archives/edgar/full-index/2021/QTR1/master.idx",
 "https://www.sec.gov/Archives/edgar/full-index/2021/QTR1/company.idx",
 "https://www.sec.gov/Archives/edgar/full-index/2010/QTR1/master.idx",
 "https://www.sec.gov/Archives/edgar/full-index/2026/QTR1/master.idx",
 "https://www.sec.gov/Archives/edgar/full-index/2021/QTR1/master.gz",
 "https://www.sec.gov/Archives/edgar/full-index/2021/QTR1/master.zip",
 "https://www.sec.gov/Archives/edgar/daily-index/2021/QTR1/master.20210104.idx",
 "https://www.sec.gov/Archives/edgar/daily-index/2021/QTR1/form.20210104.idx",
 # dissemination feed (full text of every filing for one day)
 "https://www.sec.gov/Archives/edgar/Feed/2021/QTR1/20210104.nc.tar.gz",
 "https://www.sec.gov/Archives/edgar/Feed/2010/QTR1/20100104.nc.tar.gz",
 "https://www.sec.gov/Archives/edgar/Feed/2026/QTR1/20260105.nc.tar.gz",
 "https://www.sec.gov/Archives/edgar/Oldloads/20210104.nc.tar.gz",
 # bulk data
 "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip",
 "https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip",
 # one 8-K primary doc & its index
 "https://www.sec.gov/Archives/edgar/data/752642/000149315221000953/0001493152-21-000953-index.htm",
 "https://www.sec.gov/Archives/edgar/data/752642/000149315221000953.txt",
 "https://www.sec.gov/Archives/edgar/data/752642/000149315221000953/0001493152-21-000953.txt",
 "https://www.sec.gov/Archives/edgar/data/752642/000149315221000953/ex99-1.htm",
 "https://www.sec.gov/cgi-bin/srqsb?text=test",
]
for u in URLS:
    code, cl, ct, lm, ar = head(u)
    print(f"HTTP={code} len={cl} ct={ct} ranges={ar} lm={lm}  {u}")
    sys.stdout.flush()
