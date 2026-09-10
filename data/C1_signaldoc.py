import csv
rows = list(csv.DictReader(open('C1_SignalDoc.csv', encoding='utf-8-sig')))
want = ['GP', 'GPlag', 'GPlag_q', 'OperProfRD', 'OperProfRDLagAT', 'OperProfRDLagAT_q',
        'CBOperProf', 'CBOperProfLagAT', 'CBOperProfLagAT_q', 'OperProfLag_q',
        'roaq', 'RoE', 'AssetGrowth_q']
cols = ['Acronym', 'Cat.Signal', 'Authors', 'Year', 'Journal', 'Cat.Data',
        'SampleStartYear', 'SampleEndYear', 'Sign', 'Return', 'T-Stat',
        'Stock Weight', 'LS Quantile', 'Portfolio Period', 'Start Month', 'Filter']
by = {r['Acronym']: r for r in rows}
for w in want:
    r = by.get(w)
    if not r:
        print(f"--- {w}: NOT IN SignalDoc.csv")
        continue
    print(f"--- {w}")
    for c in cols:
        print(f"     {c:<18} {r.get(c)}")
    print(f"     Notes            {(r.get('Notes') or '')[:300]}")
    print(f"     DetailedDef      {(r.get('Detailed Definition') or '')[:400]}")

# how many quarterly-data signals overall, and how they are classified
qd = [r for r in rows if 'quarter' in (r.get('Cat.Data') or '').lower()]
print("\nSignals whose Cat.Data mentions 'quarter':", len(qd))
print(sorted(set(r['Cat.Data'] for r in rows)))
print("\nCat.Signal values:", sorted(set(r['Cat.Signal'] for r in rows)))
print("count by Cat.Signal:",
      {k: sum(1 for r in rows if r['Cat.Signal'] == k) for k in sorted(set(r['Cat.Signal'] for r in rows))})
print("\n_q-suffixed acronyms:", sorted(r['Acronym'] for r in rows if r['Acronym'].endswith('_q')))
