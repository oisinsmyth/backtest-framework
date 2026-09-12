"""Harvest every public NPORT-P of the Select Sector SPDR Trust (CIK 1064641).

Each filing = one sector fund's holdings at one quarter end.  The 11 funds
partition the S&P 500 by GICS sector, so the set of (period, series, ticker)
tuples reconstructs a free, point-in-time GICS SECTOR assignment for S&P 500
constituents -- and a name that appears in fund A at t-1 and fund B at t has
been GICS-reclassified with index membership unchanged.

Projected wall time: 352 fetches, 4 threads, ~0.2 s each -> ~30-60 s.
Optimisations applied before launch: (1) primary_doc.xml URL constructed
directly, so no index-page round trip; (2) regex extraction of only the three
fields needed instead of a full XML parse; (3) on-disk cache so a rerun is free.
"""
import json, os, re, sys, urllib.request, concurrent.futures as cf, time
sys.stdout.reconfigure(encoding='utf-8')

UA = 'backtest-framework-research research@backtest-framework.org'
CIK = '1064641'
CACHE = 'K2_nport_cache'
os.makedirs(CACHE, exist_ok=True)


def get(url, timeout=40):
    req = urllib.request.Request(url, headers={'User-Agent': UA,
                                              'Accept-Encoding': 'gzip, deflate'})
    import gzip, io
    r = urllib.request.urlopen(req, timeout=timeout)
    raw = r.read()
    if r.headers.get('Content-Encoding') == 'gzip':
        raw = gzip.decompress(raw)
    return raw


# ---- 1. assemble the full filing list (recent + older index files) ----
sub = json.loads(get('https://data.sec.gov/submissions/CIK%s.json' % CIK.zfill(10)))
recs = []


def add(block):
    for f, d, acc in zip(block['form'], block['reportDate'], block['accessionNumber']):
        if f == 'NPORT-P':
            recs.append((d, acc))


add(sub['filings']['recent'])
for extra in sub['filings'].get('files', []):
    add(json.loads(get('https://data.sec.gov/submissions/' + extra['name'])))
recs = sorted(set(recs))
print('NPORT-P filings found: %d, report dates %s .. %s'
      % (len(recs), recs[0][0], recs[-1][0]))


import threading
_lock = threading.Lock()
_last = [0.0]
ERRS = []


def paced():
    # SEC throttles bursts; hold the global rate at ~6 req/s
    with _lock:
        dt = time.time() - _last[0]
        if dt < 0.17:
            time.sleep(0.17 - dt)
        _last[0] = time.time()


def fetch_one(rec):
    d, acc = rec
    path = os.path.join(CACHE, acc + '.xml')
    if os.path.exists(path) and os.path.getsize(path) > 2000:
        return d, acc, open(path, 'rb').read()
    url = ('https://www.sec.gov/Archives/edgar/data/%s/%s/primary_doc.xml'
           % (CIK, acc.replace('-', '')))
    for attempt in range(5):
        paced()
        try:
            raw = get(url)
            if len(raw) > 2000:
                open(path, 'wb').write(raw)
                return d, acc, raw
            ERRS.append((acc, 'short %d' % len(raw)))
        except Exception as ex:
            if attempt == 4:
                ERRS.append((acc, repr(ex)[:70]))
                return d, acc, b''
            time.sleep(1.5 * (attempt + 1))
    return d, acc, b''


t0 = time.time()
out = []
with cf.ThreadPoolExecutor(2) as ex:
    for d, acc, raw in ex.map(fetch_one, recs):
        out.append((d, acc, raw))
print('fetched in %.1f s (sum of %d items); errors %d' % (time.time() - t0, len(out), len(ERRS)))
print('sample errors:', ERRS[:5])

rows = []
bad = 0
for d, acc, raw in out:
    if not raw:
        bad += 1
        continue
    t = raw.decode('utf-8', 'replace')
    sn = re.search(r'<seriesName>([^<]*)</seriesName>', t)
    pd = re.search(r'<repPdDate>([^<]*)</repPdDate>', t)
    na = re.search(r'<netAssets>([^<]*)</netAssets>', t)
    blocks = re.findall(r'<invstOrSec>(.*?)</invstOrSec>', t, re.S)
    names = []
    for b in blocks:
        nm = re.search(r'<name>([^<]*)</name>', b)
        cu = re.search(r'<cusip>([^<]*)</cusip>', b)
        ti = re.search(r'<ticker>([^<]*)</ticker>', b)
        pc = re.search(r'<pctVal>([^<]*)</pctVal>', b)
        if nm:
            names.append({'name': nm.group(1), 'cusip': cu.group(1) if cu else None,
                          'ticker': ti.group(1) if ti else None,
                          'pct': float(pc.group(1)) if pc else None})
    rows.append({'repdate': d, 'acc': acc,
                 'series': sn.group(1) if sn else None,
                 'pdDate': pd.group(1) if pd else None,
                 'netAssets': float(na.group(1)) if na else None,
                 'n': len(names), 'hold': names})
print('parsed %d, unreadable %d' % (len(rows), bad))
json.dump(rows, open('K2_nport_rows.json', 'w'))

import collections
print('\nseries seen:')
for s, c in collections.Counter(r['series'] for r in rows).most_common():
    print('  %-70s %d filings' % (str(s)[:70], c))
print('\nreport dates:', sorted({r['repdate'] for r in rows}))
