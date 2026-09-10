"""For every observed S&P 500 GICS sector migration 2019Q3-2026Q2, measure:

  SELL leg = (weight in the OLD sector fund at t-1) x (that fund's net assets at t-1)
  BUY  leg = (weight in the NEW sector fund at t)   x (that fund's net assets at t)

both straight out of the SEC N-PORT filings, then divide by the name's median
daily dollar volume over the quarter in which the change happened, and report
the name's PRICE at that time.
"""
import json, re, sys, collections, urllib.request, time, datetime
sys.stdout.reconfigure(encoding='utf-8')
rows = json.load(open('K2_nport_rows.json'))
SEC = {'Technology': 'InfoTech', 'Financial': 'Financials', 'Health Care': 'HealthCare',
       'Energy': 'Energy', 'Industrial': 'Industrials', 'Materials': 'Materials',
       'Consumer Discretionary': 'ConsDisc', 'Consumer Staples': 'ConsStaples',
       'Utilities': 'Utilities', 'Real Estate': 'RealEstate',
       'Communication Services': 'CommSvcs'}


def sector_of(s):
    if s is None or 'Premium Income' in s:
        return None
    for k, v in SEC.items():
        if k in s:
            return v
    return None


snap = collections.defaultdict(dict)
na = collections.defaultdict(dict)
for r in rows:
    s = sector_of(r['series'])
    if not s:
        continue
    na[r['repdate']][s] = r['netAssets']
    for h in r['hold']:
        cu, nm = h['cusip'], h['name']
        if not cu or not nm:
            continue
        # Foreign-domiciled issuers are filed with a PLACEHOLDER cusip ("000000000"
        # / "N/A"); several different companies then share one key and fabricate
        # migrations (CME -> Health Care, Norwegian Cruise -> Info Tech, ...).
        # Key on (cusip, name) is not enough -- drop placeholder cusips outright.
        if cu.strip().upper() in ('N/A', 'NA', '000000000', '0', '') or set(cu.strip()) == {'0'}:
            continue
        low = nm.lower()
        if any(k in low for k in ('state street', 'ssga', 'money market', 'govt',
                                  'treasury bill', 'cash', 'deposit')):
            continue
        if h['pct'] is not None and h['pct'] < 0.0001:
            continue
        snap[r['repdate']][cu] = (s, nm, h['ticker'], h['pct'])

dates = sorted(snap)
TK = {'Visa Inc': 'V', 'Mastercard Inc': 'MA', 'Target Corp': 'TGT',
      'Dollar General Corp': 'DG', 'Automatic Data Processing Inc': 'ADP',
      'PayPal Holdings Inc': 'PYPL', 'Dollar Tree Inc': 'DLTR', 'Fiserv Inc': 'FISV',
      'Fidelity National Information Serv': 'FIS', 'Paychex Inc': 'PAYX',
      'Global Payments Inc': 'GPN', 'Broadridge Financial Solutions Inc': 'BR',
      'FleetCor Technologies Inc': 'FLT', 'Jack Henry &amp; Associates Inc': 'JKHY',
      'CoStar Group Inc': 'CSGP', 'Paycom Software Inc': 'PAYC',
      'Ceridian HCM Holding Inc': 'CDAY', 'Roper Technologies Inc': 'ROP',
      'Leidos Holdings Inc': 'LDOS', 'Teledyne Technologies Inc': 'TDY'}
UA = 'Mozilla/5.0 (backtest-framework-research; research@backtest-framework.org)'
cache = {}


def hist(tk, d0, d1):
    key = (tk, d0, d1)
    if key in cache:
        return cache[key]
    p1 = int(time.mktime(datetime.datetime.strptime(d0, '%Y-%m-%d').timetuple()))
    p2 = int(time.mktime(datetime.datetime.strptime(d1, '%Y-%m-%d').timetuple()))
    url = ('https://query1.finance.yahoo.com/v8/finance/chart/%s?period1=%d&period2=%d'
           '&interval=1d' % (tk, p1, p2))
    try:
        j = json.loads(urllib.request.urlopen(
            urllib.request.Request(url, headers={'User-Agent': UA}), timeout=30).read())
        q = j['chart']['result'][0]['indicators']['quote'][0]
        pr = [(c, v) for c, v in zip(q['close'], q['volume'])
              if c is not None and v is not None]
        if not pr:
            cache[key] = None
            return None
        dvs = sorted(c * v for c, v in pr)
        res = {'px_end': pr[-1][0], 'px_min': min(c for c, v in pr),
               'median_dv': dvs[len(dvs) // 2], 'n': len(pr)}
    except Exception as ex:
        res = None
    cache[key] = res
    time.sleep(0.25)
    return res


print('%-34s %-6s %-11s %-11s %-11s %8s %9s %9s %8s %8s %8s'
      % ('name', 'tkr', 'quarter', 'from', 'to', 'px', 'ADV$M', 'sell$M',
         'buy$M', 'sell/AD', 'net/AD'))
out = []
for a, b in zip(dates, dates[1:]):
    if len(na[a]) < 11 or len(na[b]) < 11:
        continue
    for cu, (sa, nm, ta, pa) in snap[a].items():
        if cu not in snap[b]:
            continue
        sb, nm2, tb, pb = snap[b][cu]
        if sb == sa:
            continue
        tk = TK.get(nm) or ta or tb
        h = hist(tk, a, b) if tk else None
        sell = (pa or 0) / 100.0 * (na[a].get(sa) or 0)
        buy = (pb or 0) / 100.0 * (na[b].get(sb) or 0)
        px = h['px_end'] if h else None
        adv = h['median_dv'] if h else None
        out.append({'name': nm, 'tk': tk, 'q': b, 'from': sa, 'to': sb,
                    'px': px, 'adv': adv, 'sell': sell, 'buy': buy})
        print('%-34s %-6s %-11s %-11s %-11s %8s %9s %9.0f %8.0f %8s %8s'
              % (nm[:34], tk or '?', b, sa, sb,
                 ('%.2f' % px) if px else '?',
                 ('%.0f' % (adv / 1e6)) if adv else '?',
                 sell / 1e6, buy / 1e6,
                 ('%.2f' % (sell / adv)) if adv else '?',
                 ('%.2f' % (abs(buy - sell) / adv)) if adv else '?'))

json.dump(out, open('K2_event_flow.json', 'w'))
px = [o['px'] for o in out if o['px']]
if px:
    px.sort()
    print('\nPRICE of the 20 migrating names at the migration quarter:')
    print('  min $%.2f   q25 $%.2f   median $%.2f   q75 $%.2f   max $%.2f   under $5: %d'
          % (px[0], px[len(px)//4], px[len(px)//2], px[3*len(px)//4], px[-1],
             sum(1 for p in px if p < 5)))
rat = [(o['sell']/o['adv'], o['net'] if 'net' in o else abs(o['buy']-o['sell'])/o['adv'],
        o['tk']) for o in out if o['adv']]
if rat:
    s = sorted(r[0] for r in rat)
    n = sorted(r[1] for r in rat)
    print('\nSELL leg / ADV : min %.2f  median %.2f  max %.2f' % (s[0], s[len(s)//2], s[-1]))
    print('NET  flow / ADV: min %.2f  median %.2f  max %.2f' % (n[0], n[len(n)//2], n[-1]))
    print('  (SPDR family only -- one issuer. Other GICS families move on other dates.)')
