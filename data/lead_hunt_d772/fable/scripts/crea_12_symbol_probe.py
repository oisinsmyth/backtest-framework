"""Metadata-only probe: which non-outright ES/NQ/GC/SI/HG/CL instruments (BTIC, TACO, TAS) are in the 2023 ohlcv-1m archive
and in the 1-second index job? Reads metadata only."""
import re, collections
from pathlib import Path
import databento as db
RAW = Path(r"C:/Users/O/Desktop/Projects/Backtest Framework/data/raw/databento")
for p in [RAW / "GLBX-20260911-NF533R6P5T/glbx-mdp3-20230101-20230822.ohlcv-1m.dbn.zst", RAW / "GLBX-20261001-Q949LNXFLK/glbx-mdp3-20230601-20230630.ohlcv-1s.dbn.zst"]:
    st = db.DBNStore.from_file(p)
    md = st.metadata
    syms = list(md.mappings.keys())
    print(p.name, "symbols in:", md.symbols[:50], "n mapped raw symbols", len(syms))
    pat = collections.Counter()
    ex = collections.defaultdict(list)
    for s in syms:
        s = str(s)
        m = re.match(r"^([A-Z0-9]+?)([FGHJKMNQUVXZ]\d{1,2})(.*)$", s)
        key = (m.group(1), "spread" if "-" in s else ("outright" if m and m.group(3) == "" else "other")) if m else (s[:4], "unmatched")
        pat[key] += 1
        if len(ex[key]) < 3:
            ex[key].append(s)
    for k, v in sorted(pat.items()):
        if k[1] != "spread":
            print("  ", k, v, ex[k])
