"""Does the BREADTH fixture pool expiries on CL, the way the D467 fixture does?

A FIRST VERSION OF THIS CHECK COULD NOT FIRE and is recorded here so it is not rebuilt: it flagged any
contract LABEL whose rows span more than a year. That flags 34 of 36 roots including NQ, ES and YM,
which the D467 note calls clean -- because "CLZ5" legitimately denotes December 2015 crude AND
December 2025 crude under CME's single-digit-year convention. A shared label is expected. The defect
is bars from two contracts being ATTRIBUTED TO THE SAME SESSION, not a label recurring.

Three tests that can discriminate:
  A  the two fixtures disagree on CL's price for the same day -- one of them is mislabelled
  B  a session whose own hourly bars span an impossible price range (two contracts merged inside a day)
  C  2019 specifically, where the D467 note measured 16 of 140 CL symbols mapping to >1 instrument_id

    uv run python -u working/check_breadth_cl_expiry_pooling.py
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
NEW = REPO / "data" / "fixtures" / "fut_breadth_hourly.csv.gz"
OLD = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"
SEGN = [f"h{h:02d}" for h in [18, 19, 20, 21, 22, 23] + list(range(0, 17))]

meta = json.loads((REPO / "data" / "fixtures" / "fut_breadth_hourly.meta.json").read_text(encoding="utf-8"))
print(f"breadth meta all_gates_pass: {meta.get('all_gates_pass')}")
cols = ["root", "day", "contract"] + [f"{s}_{f}" for s in SEGN for f in ("h", "l", "c")]
n = pd.read_csv(NEW, dtype={"root": str, "day": str, "contract": str})
o = pd.read_csv(OLD, dtype={"root": str, "day": str, "contract": str})
ncl = n[n.root == "CL"].set_index("day"); ocl = o[o.root == "CL"].set_index("day")
common = sorted(set(ncl.index) & set(ocl.index))
print(f"CL: breadth {len(ncl):,} sessions, D467 {len(ocl):,}, {len(common):,} days in both\n")

print("A. DO THE TWO FIXTURES DISAGREE ON CL's PRICE FOR THE SAME DAY?")
a = ncl.loc[common, "h12_c"].to_numpy(float); b = ocl.loc[common, "h12_c"].to_numpy(float)
m = np.isfinite(a) & np.isfinite(b)
rel = np.abs(a[m] - b[m]) / b[m]
days = np.array(common)[m]
print(f"   {m.sum():,} comparable days; identical on {100*np.mean(rel < 1e-9):.2f}%")
print(f"   |relative difference|: p50 {np.median(rel):.2e}  p99 {np.quantile(rel, .99):.2e}  max {rel.max():.4f}")
big = rel > 0.02
print(f"   days differing by more than 2%: {int(big.sum())}")
if big.any():
    idx = np.argsort(rel)[::-1][:8]
    print("   the largest disagreements (breadth vs D467):")
    for i in idx:
        d0 = days[i]
        print(f"      {d0}  breadth ${a[m][i]:>8.2f} ({ncl.loc[d0,'contract']})   D467 ${b[m][i]:>8.2f} ({ocl.loc[d0,'contract']})   {100*rel[i]:.1f}%")
cdiff = (ncl.loc[common, "contract"].to_numpy() != ocl.loc[common, "contract"].to_numpy())
print(f"   days where the two fixtures give a DIFFERENT contract label: {int(cdiff.sum())} of {len(common):,}")

print("\nB. WITHIN-SESSION COHERENCE -- can a single session's own hourly bars span an impossible range?")
for lab, df in (("breadth", ncl), ("D467", ocl)):
    hi = df[[f"{s}_h" for s in SEGN if f"{s}_h" in df.columns]].to_numpy(float)
    lo = df[[f"{s}_l" for s in SEGN if f"{s}_l" in df.columns]].to_numpy(float)
    with np.errstate(invalid="ignore"):
        rng = np.nanmax(hi, axis=1) / np.nanmin(np.where(lo > 0, lo, np.nan), axis=1)
    rng = rng[np.isfinite(rng)]
    over = rng > 1.5
    print(f"   {lab:8s} session high/low ratio: p50 {np.median(rng):.4f}  p99 {np.quantile(rng, .99):.4f}  max {rng.max():.3f};  sessions over 1.5x: {int(over.sum())}")

print("\nC. 2019 SPECIFICALLY -- where the D467 note measured 16 of 140 CL symbols mapping to >1 id")
for lab, df in (("breadth", ncl), ("D467", ocl)):
    x = df[(df.index >= "2019-01-01") & (df.index <= "2019-12-31")]
    p = x["h12_c"].to_numpy(float); p = p[np.isfinite(p)]
    print(f"   {lab:8s} 2019: {len(x)} sessions, {x['contract'].nunique()} labels, midday close ${p.min():.2f}..${p.max():.2f}")
x19n = ncl[(ncl.index >= "2019-01-01") & (ncl.index <= "2019-12-31")]
x19o = ocl[(ocl.index >= "2019-01-01") & (ocl.index <= "2019-12-31")]
cm = sorted(set(x19n.index) & set(x19o.index))
d19 = np.abs(x19n.loc[cm, "h12_c"].to_numpy(float) - x19o.loc[cm, "h12_c"].to_numpy(float))
print(f"   2019 days where the two disagree by more than $0.01: {int(np.nansum(d19 > 0.01))} of {len(cm)}")

print("\nD. THE JUMP FOUND IN THE FIRST PASS -- when did CL's 60% session move happen?")
x = n[n.root == "CL"].sort_values("day")
p = x["h12_c"].to_numpy(float); dd = x["day"].to_numpy()
with np.errstate(invalid="ignore", divide="ignore"):
    j = np.abs(np.diff(np.log(np.where(p > 0, p, np.nan))))
k = np.nanargmax(j)
print(f"   largest |log move| {j[k]:.4f} between {dd[k]} (${p[k]:.2f}) and {dd[k+1]} (${p[k+1]:.2f})")
