"""Descriptive only: is D535's era sign-flip carried by a handful of 2020 sessions?

Not a new test -- the pre-registration declared the era split a diagnostic. This is the same
diagnostic at finer resolution, plus the top trade named (the standing rule).
"""
import sys
import importlib.util
from pathlib import Path
import numpy as np
import pandas as pd

# Resolved from this file, not hardcoded: the literal absolute path this line used to
# hold was the author's own checkout, so the script could not run on any other machine.
# `working/` sits directly under the repo root, so parents[1] -- same as scripts/.
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
s = importlib.util.spec_from_file_location("d535", REPO / "scripts" / "run_d535_illiq_ranked.py")
M = importlib.util.module_from_spec(s); sys.modules["d535"] = M; s.loader.exec_module(M)

G = M.D531.load()
B = pd.read_csv(REPO / "data" / "fixtures" / "fut_breadth_hourly.csv.gz",
                dtype={"root": str, "day": str})
rows = []
for r in M.PRIMARY:
    g = G[G.root == r]
    first, last = M.D531.session_span(g)
    days, A = M.D531.grids(g)
    d, ent, _a, _b, _c = M.D533.features(A, first, last, M.OR_N)
    pct, sg, _n = M.night_state(B, r, days)
    usd, gn = M.norm_pnl(A, d, ent, M.PRIMARY_H, M.UPT[r])
    m = (np.isfinite(gn) & np.isfinite(pct) & (d != 0) & (sg != 0) & (pct >= 0.90))
    for i in np.where(m)[0]:
        rows.append(dict(root=r, day=str(days[i]), year=str(days[i])[:4],
                         side="WITH" if d[i] == sg[i] else "AGST",
                         night="up" if sg[i] > 0 else "dn",
                         brk="up" if d[i] > 0 else "dn", gn=gn[i], usd=usd[i]))
T = pd.DataFrame(rows)

print(f"{len(T)} top-decile trades over {T.root.nunique()} roots\n")
print("PER YEAR: contrast = mean(WITH) - mean(AGAINST), equal-weighted over roots")
print(f"{'year':<6}{'n':>6}{'WITH':>9}{'AGST':>9}{'contrast':>10}{'|gn| p99':>10}")
for y, gy in T.groupby("year"):
    cs = []
    for r, gr in gy.groupby("root"):
        w = gr[gr.side == "WITH"]["gn"]; a = gr[gr.side == "AGST"]["gn"]
        if len(w) >= 5 and len(a) >= 5:
            cs.append(w.mean() - a.mean())
    w = gy[gy.side == "WITH"]["gn"]; a = gy[gy.side == "AGST"]["gn"]
    print(f"{y:<6}{len(gy):>6}{w.mean():>+9.3f}{a.mean():>+9.3f}"
          f"{(np.mean(cs) if cs else np.nan):>+10.3f}{gy.gn.abs().quantile(0.99):>10.2f}")

print("\nTHE TOP FIVE TRADES BY |normalised P&L| -- named, per the standing rule")
top = T.reindex(T.gn.abs().sort_values(ascending=False).index).head(5)
for _, t in top.iterrows():
    print(f"  {t.root:<4}{t.day}  night {t.night}  break {t.brk}  {t.side}  "
          f"gn {t.gn:+8.2f}  ${t.usd:+,.0f}")

print("\nDROP 2020 ENTIRELY -- does the second era still read negative?")
for lbl, sub in (("2016-2019", T[T.year < "2020"]), ("2020-2023", T[T.year >= "2020"]),
                 ("2021-2023 (2020 dropped)", T[T.year >= "2021"])):
    cs = []
    for r, gr in sub.groupby("root"):
        w = gr[gr.side == "WITH"]["gn"]; a = gr[gr.side == "AGST"]["gn"]
        if len(w) >= 5 and len(a) >= 5:
            cs.append(w.mean() - a.mean())
    print(f"  {lbl:<26} n {len(sub):>4}  contrast {np.mean(cs):+.4f}")

print("\nG1 BY NIGHT DIRECTION -- the structure the declared contrast is orthogonal to")
print(f"{'night':<7}{'break':<7}{'n':>6}{'mean':>9}{'median':>9}{'trim':>9}")
for (nd, bk), gg in T.groupby(["night", "brk"]):
    v = np.sort(gg.gn.to_numpy()); k = max(1, int(round(0.01 * len(v))))
    print(f"{nd:<7}{bk:<7}{len(gg):>6}{v.mean():>+9.3f}{np.median(v):>+9.3f}"
          f"{v[k:-k].mean():>+9.3f}")
print("\nby NIGHT direction alone (both breaks pooled):")
for nd, gg in T.groupby("night"):
    print(f"  night {nd}: n {len(gg):>4}  mean {gg.gn.mean():+.3f}  median {gg.gn.median():+.3f}")
