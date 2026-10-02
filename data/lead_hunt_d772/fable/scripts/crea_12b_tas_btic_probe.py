"""Metadata-only: which TAS / BTIC / TACO-style instruments exist in the 2023 ohlcv-1m archive (ALL_SYMBOLS)?
Looks for raw symbols of the form <ROOT><SUFFIX><MONTH><YEAR> where ROOT is a root we trade and SUFFIX is 1-2 letters."""
import re, collections
from pathlib import Path
import databento as db
p = Path(r"C:/Users/O/Desktop/Projects/Backtest Framework/data/raw/databento/GLBX-20260911-NF533R6P5T/glbx-mdp3-20230101-20230822.ohlcv-1m.dbn.zst")
st = db.DBNStore.from_file(p)
pat = re.compile(r"^(ES|NQ|YM|RTY|GC|SI|HG|CL|NG|BZ|6E|6J|BTC|MES|MNQ|MGC|MCL|ZN|ZB|RB|HO|PL)([A-Z]{1,2})([FGHJKMNQUVXZ])(\d{1,2})$")
cnt = collections.Counter(); ex = collections.defaultdict(list)
for s in st.metadata.mappings.keys():
    m = pat.match(str(s))
    if m:
        k = (m.group(1), m.group(2)); cnt[k] += 1
        if len(ex[k]) < 4:
            ex[k].append(str(s))
for k in sorted(cnt):
    print(k, cnt[k], ex[k])
