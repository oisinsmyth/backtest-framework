"""Count GICS SECTOR migrations with S&P 500 membership unchanged.

Method: the 11 plain Select Sector SPDR funds partition the S&P 500 by GICS
sector.  A CUSIP that appears in fund A at quarter t-1 and in fund B (B != A) at
quarter t has changed GICS sector while STAYING in the S&P 500 -- which is
exactly the event territory K2 is about, and excludes index add/delete by
construction (the name must be present at both dates).
"""
import json, re, sys, collections
sys.stdout.reconfigure(encoding='utf-8')
rows = json.load(open('K2_nport_rows.json'))

SEC = {'Technology': 'InfoTech', 'Financial': 'Financials', 'Health Care': 'HealthCare',
       'Energy': 'Energy', 'Industrial': 'Industrials', 'Materials': 'Materials',
       'Consumer Discretionary': 'ConsDisc', 'Consumer Staples': 'ConsStaples',
       'Utilities': 'Utilities', 'Real Estate': 'RealEstate',
       'Communication Services': 'CommSvcs'}


def sector_of(series):
    if series is None or 'Premium Income' in series:
        return None          # covered-call variants: same sector, separate fund
    for k, v in SEC.items():
        if k in series:
            return v
    return None


# date -> cusip -> (sector, name, ticker, pct)
snap = collections.defaultdict(dict)
meta = collections.defaultdict(dict)
for r in rows:
    s = sector_of(r['series'])
    if not s:
        continue
    d = r['repdate']
    meta[d][s] = r['netAssets']
    for h in r['hold']:
        cu = h['cusip']
        if not cu or cu in ('N/A', '000000000') or not h['name']:
            continue
        if h['pct'] is not None and h['pct'] < 0.0001:
            continue
        # Cash-sweep / collateral lines carry the SAME cusip in every sector fund,
        # so they masquerade as migrations.  Drop them -- this is the artefact that
        # inflated the first pass from 18 real events to 50.
        nm = h['name'].lower()
        if ('state street' in nm or 'ssga' in nm or 'money market' in nm
                or 'govt' in nm or 'treasury bill' in nm or 'cash' in nm
                or 'deposit' in nm):
            continue
        snap[d][cu] = (s, h['name'], h['ticker'], h['pct'])

dates = sorted(snap)
print('quarters with a full sector partition: %d  (%s .. %s)'
      % (len(dates), dates[0], dates[-1]))
for d in dates:
    print('  %s  %2d sectors, %4d cusips' % (d, len(meta[d]), len(snap[d])))

print('\n=== SECTOR MIGRATIONS, consecutive available quarters ===')
print('(name present at BOTH dates, in a DIFFERENT sector fund -> GICS sector change,')
print(' index membership unchanged.  Gaps in the quarter series are flagged.)\n')
allm = []
for a, b in zip(dates, dates[1:]):
    if len(meta[a]) < 11 or len(meta[b]) < 11:
        print('  %s -> %s  SKIPPED (incomplete partition: %d / %d sectors)'
              % (a, b, len(meta[a]), len(meta[b])))
        continue
    mig = []
    for cu, (sa, na, ta, pa) in snap[a].items():
        if cu in snap[b]:
            sb, nb, tb, pb = snap[b][cu]
            if sb != sa:
                mig.append((na, ta or tb, sa, sb, pa, pb))
    gap = ''
    y0, m0 = int(a[:4]), int(a[5:7])
    y1, m1 = int(b[:4]), int(b[5:7])
    nq = (y1 - y0) * 4 + (m1 - m0) // 3
    if nq != 1:
        gap = '  [GAP: %d quarters]' % nq
    print('  %s -> %s : %3d migrations%s' % (a, b, len(mig), gap))
    for m in sorted(mig, key=lambda x: -(x[4] or 0))[:40]:
        print('        %-34s %-6s %-12s -> %-12s  old wt %.3f%%  new wt %.3f%%'
              % (m[0][:34], m[1] or '?', m[2], m[3], m[4] or 0, m[5] or 0))
    allm.append((a, b, mig, nq))

json.dump([[a, b, m, nq] for a, b, m, nq in allm], open('K2_migrations.json', 'w'))
tot = sum(len(m) for _, _, m, _ in allm)
span_q = sum(nq for _, _, _, nq in allm)
print('\nTOTAL migrations observed: %d over %d quarters of coverage = %.1f per year'
      % (tot, span_q, tot / (span_q / 4.0)))
