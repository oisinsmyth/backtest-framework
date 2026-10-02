"""A' follow-up: split MNQ/MES micro-pause events by whether the pause RESUMED inside the event minute (then the minute's
close is a post-resume print and the basis trade is executable) or spanned the minute boundary (the close is the stale
swept print: not executable)."""
import numpy as np, pandas as pd
from pathlib import Path
OUT = Path(__file__).resolve().parents[1] / "out"
ev = pd.read_csv(OUT / "crea_04_status_events.csv", parse_dates=["start_et", "resume_et"])
for mic in ["MNQ", "MES"]:
    T = pd.read_csv(OUT / f"crea_09_{mic}_events.csv", parse_dates=["m0"])
    e = ev[ev["root"] == mic].copy(); e["m0"] = e["start_et"].dt.floor("min"); e = e.drop_duplicates("m0")
    T = T.merge(e[["m0", "resume_et"]], on="m0")
    T["inside"] = T["resume_et"].dt.floor("min") == T["m0"]
    T["b0_abs"] = T["b0_ticks"].abs()
    print(f"== {mic}: n={len(T)} inside-minute resume={int(T['inside'].sum())} spanning={int((~T['inside']).sum())}")
    for nm, s in [("inside", T[T["inside"]]), ("spanning", T[~T["inside"]])]:
        if len(s) < 5:
            continue
        print(f"  {nm}: n={len(s)} mean|b0| ticks={s['b0_abs'].mean():.1f} median|b0|={s['b0_abs'].median():.1f} share|b0|>=2={float((s['b0_abs']>=2).mean()):.2f}")
        for H in (1, 5, 15):
            g = s.loc[s["b0"] != 0, f"gb{H}"]
            gp = s.loc[s["b0"] != 0, f"gpar{H}"]
            print(f"     H{H}: trade-vs-basis gross=${g.mean():+.2f} (t {g.mean()/g.std()*np.sqrt(len(g)):+.1f}, n {len(g)}) median=${g.median():+.2f} win={float((g>0).mean()):.2f} | parent same side=${gp.mean():+.2f} | basis closed share={float((np.sign(s.loc[s['b0']!=0, f'db{H}'])==-np.sign(s.loc[s['b0']!=0,'b0'])).mean()):.2f}")
        print("     years:", s.groupby(s["m0"].dt.year).size().to_dict(), " top gb5:", round(float(s["gb5"].max()), 1))
