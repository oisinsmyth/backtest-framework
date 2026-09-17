"""D2: OSAP's own reported numbers for the LEVEL vs SEASONAL-DIFFERENCE pairs, and
for the gross-profitability family. All figures are OSAP's transcription of the
ORIGINAL PAPER's headline test (`Test in OP`), not OSAP's own replication.
"""
from pathlib import Path

import pandas as pd

# The CSV is this script's SIBLING, so address it as one. The absolute path that stood
# here named the author's own checkout and made the script unrunnable anywhere else.
P = Path(__file__).resolve().parent / "D3_SignalDoc.csv"
d = pd.read_csv(P, encoding="utf-8", engine="python", on_bad_lines="skip")
want = ["GP", "GPlag", "GPlag_q", "roaq", "RoE", "ChangeRoA", "ChangeRoE",
        "OperProf", "OperProfLagAT_q", "OperProfRD", "CBOperProf",
        "CBOperProfLagAT_q", "EarningsSurprise", "RevenueSurprise"]
cols = ["Acronym", "Authors", "Year", "Journal", "LongDescription", "Cat.Signal",
        "SampleStartYear", "SampleEndYear", "Sign", "Return", "T-Stat",
        "Stock Weight", "LS Quantile", "Test in OP", "Portfolio Period"]
sub = d[d.Acronym.isin(want)]
print(f"{'Acronym':<20}{'Cat.Signal':<12}{'Ret':>7}{'T-Stat':>8}{'Wt':>5}"
      f"{'Qtile':>7}{'sample':>12}  description")
for _, r in sub.iterrows():
    print(f"{str(r.Acronym):<20}{str(r['Cat.Signal']):<12}"
          f"{str(r['Return'])[:6]:>7}{str(r['T-Stat'])[:6]:>8}"
          f"{str(r['Stock Weight'])[:4]:>5}{str(r['LS Quantile'])[:6]:>7}"
          f"{str(r.SampleStartYear)[:4]}-{str(r.SampleEndYear)[:4]:>4}  "
          f"{str(r.LongDescription)[:55]}")

print("\n=== full detail for the seasonal-difference pair ===")
for a in ["ChangeRoA", "ChangeRoE", "roaq", "RoE", "GPlag_q", "GPlag", "GP"]:
    r = d[d.Acronym == a]
    if not len(r):
        print(f"\n{a}: NOT IN FILE")
        continue
    r = r.iloc[0]
    print(f"\n--- {a}")
    for c in ["Authors", "Year", "Journal", "LongDescription", "Detailed Definition",
              "Cat.Signal", "Evidence Summary", "Test in OP", "Return", "T-Stat",
              "Notes"]:
        v = str(r.get(c, ""))
        if v and v != "nan":
            print(f"   {c:<20}= {v[:260]}")
