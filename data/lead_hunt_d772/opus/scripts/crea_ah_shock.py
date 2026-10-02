"""Premise C5: an NQ-SPECIFIC after-hours shock (16:00-17:00 ET, the constituent-earnings hour) is an overshoot in a thin
book; fade it from the 18:00 reopen to the next cash open / 10:00 / 16:00. One MNQ ($2/pt, RT $4.07).
Data: fut_opening_globex_1m (ES, NQ), sessions 2016-01..2023-12 (seal asserted).
Session S holds bars 18:00(S-1) .. 17:00(S). Predictor uses only bars <= 17:00 of S. Entry at P(18:05) of session S+1.
"""
import numpy as np, pandas as pd

FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures\fut_opening_globex_1m.csv.gz"
SEAL = "2024-01-01"
d = pd.read_csv(FX, usecols=["root", "session", "hhmm", "close"])
d = d[(d.session >= "2016-01-01") & (d.session < SEAL)]
assert d.session.max() < SEAL
need = {"15:59", "16:59", "16:58", "16:55", "18:04", "18:00", "09:29", "09:59", "11:59", "15:58"}
d = d[d.hhmm.isin(need)]
P = d.pivot_table(index=["session"], columns=["root", "hhmm"], values="close", aggfunc="last")
S = P.index.tolist()
rows = []
for i in range(len(S) - 1):
    s, n = S[i], S[i + 1]
    r = P.loc[s]; q = P.loc[n]
    try:
        nq16, nq17 = r[("NQ", "15:59")], r[("NQ", "16:59")] if np.isfinite(r[("NQ", "16:59")]) else r[("NQ", "16:58")]
        es16, es17 = r[("ES", "15:59")], r[("ES", "16:59")] if np.isfinite(r[("ES", "16:59")]) else r[("ES", "16:58")]
        ent = q[("NQ", "18:04")]
    except KeyError:
        continue
    rows.append(dict(s=s, n=n, nq16=nq16, nq17=nq17, es16=es16, es17=es17, ent=ent, ent_es=q[("ES", "18:04")],
                     x930=q[("NQ", "09:29")], x1000=q[("NQ", "09:59")], x1200=q[("NQ", "11:59")], x1600=q[("NQ", "15:58")]))
R = pd.DataFrame(rows).dropna()
R["rnq"] = np.log(R.nq17 / R.nq16); R["res"] = np.log(R.es17 / R.es16)
R["rel"] = R.rnq - 1.15 * R.res
R["gap"] = np.log(R.ent / R.nq17)
usd = 2.0
for side, col in [("AH NQ move", "rnq"), ("NQ-specific rel", "rel")]:
    q = R[col].abs().rank(pct=True)
    for lo in [0.0, 0.8, 0.9, 0.95]:
        sel = R[q >= lo]
        sg = -np.sign(sel[col])
        out = []
        for xc in ["x930", "x1000", "x1200", "x1600"]:
            pnl = sg * (sel[xc] - sel.ent) * usd
            out.append(f"{xc}: ${pnl.mean():+.2f} med {pnl.median():+.2f} t {pnl.mean() / pnl.std() * np.sqrt(len(pnl)):+.2f}")
        print(f"{side:16s} |q|>={lo:.2f} n={len(sel):4d} mean|move| ${sel[col].abs().mean() * sel.nq16.mean() * usd:6.1f} :: " + " | ".join(out))
# year split for rel top decile, exit 09:30 and 16:00
q = R.rel.abs().rank(pct=True); sel = R[q >= 0.9].copy()
sel["p930"] = -np.sign(sel.rel) * (sel.x930 - sel.ent) * usd
sel["p1600"] = -np.sign(sel.rel) * (sel.x1600 - sel.ent) * usd
print(sel.groupby(sel.s.str[:4])[["p930", "p1600"]].agg(["count", "mean"]).round(2).to_string())
print("month distribution of top-decile rel:", sel.s.str[5:7].value_counts().sort_index().to_dict())
print(sel.sort_values("p1600").iloc[[0, 1, -2, -1]][["s", "rel", "p930", "p1600"]])
