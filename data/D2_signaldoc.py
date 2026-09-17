"""D2: Chen & Zimmermann Open Source Asset Pricing SignalDoc.csv -- what quarterly
profitability variants exist, how are they constructed, and is ANY of them
seasonally adjusted or trailing-four-quarter?

File: data/D3_SignalDoc.csv (fetched by lane D3 of this same round; shared evidence)
Upstream: https://github.com/OpenSourceAP/CrossSection
"""
from pathlib import Path

import pandas as pd

# The CSV is this script's SIBLING, so address it as one. The absolute path that stood
# here named the author's own checkout and made the script unrunnable anywhere else.
P = Path(__file__).resolve().parent / "D3_SignalDoc.csv"
d = pd.read_csv(P, encoding="utf-8", engine="python", on_bad_lines="skip")
print(f"rows {len(d)}  cols {len(d.columns)}")
print("columns:", list(d.columns))
acr = [c for c in d.columns if "cronym" in c or c.lower() == "signal"]
ac = acr[0] if acr else d.columns[0]
print(f"\nusing '{ac}' as the signal-name column")

# every signal whose NAME ends in _q  (the quarterly family)
q = d[d[ac].astype(str).str.endswith("_q")]
print(f"\n=== signals whose name ends in '_q': {len(q)} ===")
cols = [c for c in ["Acronym", "Authors", "Year", "Journal", "LongDescription",
                    "Cat.Signal", "Cat.Data", "Predictability in OP",
                    "Signal Rep Quality", "Evidence Summary",
                    "Test in OP", "Sample Start Year", "Sample End Year"]
        if c in d.columns]
for _, r in q.iterrows():
    print(f"\n  {r[ac]}")
    for c in cols:
        if c == ac:
            continue
        v = str(r[c])
        if v and v != "nan":
            print(f"     {c:<22}= {v[:170]}")

# seasonality / trailing-four-quarter anywhere in the whole file
print("\n" + "=" * 80)
txt = d.astype(str).apply(lambda s: s.str.lower())
for pat in ["season", "four quarter", "four-quarter", "trailing", "last 4 q",
            "year-over-year", "same quarter"]:
    hit = txt.apply(lambda s: s.str.contains(pat, regex=False, na=False)).any(axis=1)
    names = d.loc[hit, ac].astype(str).tolist()
    print(f"  {pat!r:<18} rows: {int(hit.sum()):>3}   {names[:12]}")
# NEGATIVE CONTROL: a string that cannot appear
for pat in ["zzzz_not_a_string_d2"]:
    hit = txt.apply(lambda s: s.str.contains(pat, regex=False, na=False)).any(axis=1)
    print(f"  CONTROL {pat!r} rows: {int(hit.sum())}  <-- MUST BE 0")

# profitability family generally
print("\n=== rows whose description mentions gross profit / profitability ===")
m = d.astype(str).apply(
    lambda s: s.str.contains("gross profit", case=False, na=False)).any(axis=1)
for _, r in d[m].iterrows():
    ln = str(r.get("LongDescription", ""))[:90]
    print(f"  {str(r[ac]):<22} {ln}")
