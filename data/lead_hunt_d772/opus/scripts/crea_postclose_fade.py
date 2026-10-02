"""Premise C5b: the POST-CASH-CLOSE hour (16:00->17:00 ET) of the index futures reverts by the next morning.
Fade it from the 18:05 reopen of the NEXT session to 09:30 / 10:00 / 12:00. One micro. Placebo windows: 14:00-15:00,
15:00-16:00 (same entry, same exits). Size gate: |move| above the trailing 250-session 80th/90th pct of |move| in
that window (pre-entry: only sessions strictly before). Sessions 2016..2023 (seal asserted).
"""
import sys
import numpy as np, pandas as pd

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"
SPEC = {"NQ": ("fut_opening_globex_1m.csv.gz", 2.0, 4.07), "ES": ("fut_opening_globex_1m.csv.gz", 5.0, 4.42),
        "YM": ("fut_opening_globex_1m_ym_rty.csv.gz", 0.5, 3.80), "RTY": ("fut_opening_globex_1m_ym_rty.csv.gz", 5.0, 3.76)}
WIN = {"post 16-17": ("15:59", "16:59"), "pc 16:00-16:15": ("15:59", "16:14"), "pc 16:15-17": ("16:14", "16:59"),
       "plc 15-16": ("14:59", "15:59"), "plc 14-15": ("13:59", "14:59"), "plc 13-14": ("12:59", "13:59")}
EXITS = {"09:30": "09:29", "10:00": "09:59", "12:00": "11:59", "15:00": "14:59"}
cache = {}
allrows = []
for root, (fn, usd, rt) in SPEC.items():
    if fn not in cache:
        d = pd.read_csv(f"{FXD}\\{fn}", usecols=["root", "session", "hhmm", "close"])
        d = d[(d.session >= "2016-01-01") & (d.session < SEAL)]
        need = set(sum([list(v) for v in WIN.values()], [])) | set(EXITS.values()) | {"18:04", "16:58"}
        cache[fn] = d[d.hhmm.isin(need)]
    d = cache[fn][cache[fn].root == root]
    assert d.session.max() < SEAL
    P = d.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    if "16:59" in P:
        P["16:59"] = P["16:59"].fillna(P["16:58"])
    nxt = P.shift(-1)  # next session's bars (18:04 of next session = evening of this day)
    # guard: next session's 18:04 must be the evening right after this session (calendar gap <= 4 days)
    gap_days = (pd.to_datetime(pd.Series(P.index).shift(-1)) - pd.to_datetime(pd.Series(P.index))).dt.days.values
    ent = nxt["18:04"].where(gap_days <= 4)
    print(f"\n==== {root}  usd/pt {usd}  RT ${rt}  sessions {len(P)}")
    for wname, (a, b) in WIN.items():
        mv = P[b] - P[a]
        thr80 = mv.abs().shift(1).rolling(250, min_periods=120).quantile(0.8)
        thr90 = mv.abs().shift(1).rolling(250, min_periods=120).quantile(0.9)
        for lab, thr in [("q80", thr80), ("q90", thr90)]:
            sel = (mv.abs() >= thr) & np.isfinite(ent) & (mv != 0)
            outs = []
            for ex, col in EXITS.items():
                pnl = (-np.sign(mv) * (nxt[col] - ent) * usd)[sel].dropna()
                outs.append(f"{ex}: ${pnl.mean():+6.2f} med {pnl.median():+6.2f} t {pnl.mean() / pnl.std() * np.sqrt(len(pnl)):+.2f}")
                if ex == "10:00":
                    allrows.append(pd.DataFrame({"root": root, "win": wname, "lab": lab, "session": pnl.index, "pnl": pnl.values,
                                                 "mv": mv[pnl.index].values * usd}))
            n = int(sel.sum())
            print(f" {wname:15s} {lab} n={n:4d} ({n / 8:.0f}/yr) mean|mv| ${(mv.abs()[sel]).mean() * usd:6.1f} :: " + " | ".join(outs))
A = pd.concat(allrows)
A.to_csv(sys.path[0] + r"\..\out\crea_postclose_fade_rows.csv", index=False)
for root in SPEC:
    s = A[(A.root == root) & (A.win == "post 16-17") & (A.lab == "q80")]
    yr = s.groupby(s.session.str[:4]).pnl.agg(["count", "mean"]).round(2)
    p = s.pnl.sort_values()
    k = max(1, int(round(0.01 * len(p))))
    print(f"\n{root} post 16-17 q80 exit 10:00: by year {yr.to_dict('index')}")
    print(f"  ex-2020 ${s[s.session.str[:4] != '2020'].pnl.mean():+.2f}  ex-2022 ${s[s.session.str[:4] != '2022'].pnl.mean():+.2f}"
          f"  ex-top1% ${p.iloc[:-k].mean():+.2f} ex-bot1% ${p.iloc[k:].mean():+.2f} trimmed ${p.iloc[k:-k].mean():+.2f}"
          f"  win {100 * (s.pnl > 0).mean():.1f}%  skew {s.pnl.skew():+.2f}")
    print("  top trades:", s.sort_values("pnl").iloc[[-1, -2, 0, 1]][["session", "pnl", "mv"]].to_dict("records"))
