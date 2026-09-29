"""Is it the gap that makes the retest fail? (the principal, 2026-09-29, on D666 / diag_d666). Post hoc, in-sample only
through D666's own sealed functions; changes no verdict. SqueezeMetrics GEX credited; statistics only (licence-guarded).

    uv run python scripts/diag_d666_gap.py --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"

Every session is classed by how it opened against yesterday's level L in the direction of the day's first break:
  gap_through  opened beyond the stop (L +/- 0.25 ATR): the plain break fills at the open
  gap_inside   opened beyond L but inside the stop
  no_gap       opened inside yesterday's range
and by what followed the break: whether price came back to L (the retest the re-break needs) and whether it re-broke.
G1  the plain break's P&L by open class x retest, with each cell's share of the total.
G2  the re-break by open class.
G3  paired: sessions with both trades on the same side, plain vs re-break.
Writes data/diag_d666_gap.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import diag_d666 as G  # noqa: E402
import stage0_d662_gamma_product as S  # noqa: E402
import stage0_d663_per_root_gamma_break as T  # noqa: E402
import stage0_d666_rebreak as X  # noqa: E402

OUT = REPO / "data" / "diag_d666_gap.json"


def flags_job(args: tuple) -> list[dict]:
    """Per session: the open's class against the plain break's side, and whether price retested L after the plain
    entry (the re-break's precondition, read from the bars after the entry, same side)."""
    r, frame, bars_r = args
    out = []
    for s, d in frame.iterrows():
        bb = bars_r.get(s)
        if bb is None:
            continue
        Lh, Ll, A = float(d["prior_high"]), float(d["prior_low"]), float(d["atr20"])
        p = X.plain_break(bb, Lh, Ll, A)
        if p is None:
            continue
        D, L, stop, i = p["D"], p["L"], p["stop"], p["i"]
        o0 = float(bb["o"][0])
        beyond_L = (o0 > L) if D > 0 else (o0 < L)
        beyond_stop = (o0 > stop) if D > 0 else (o0 < stop)
        cls = "gap_through" if beyond_stop else ("gap_inside" if beyond_L else "no_gap")
        m, h, l = bb["m"], bb["h"], bb["l"]
        after = np.arange(i + 1, len(m))
        after = after[m[after] <= X.LAST_ENTRY]
        touched = bool(len(after) and ((l[after] <= L).any() if D > 0 else (h[after] >= L).any()))
        out.append({"root": r, "session": s, "D_plain": D, "open_class": cls, "retest_after_plain": touched})
    return out


def cell(x: pd.Series, total: float, R) -> dict:
    x = x.dropna().to_numpy(float)
    res = {"n": int(len(x)), "sum": float(x.sum()), "share_of_total": float(x.sum() / total) if total else np.nan}
    if len(x) >= 8:
        t, _ = R.nw_t(x)
        res.update(mean=float(x.mean()), t=float(t), median=float(np.median(x)), win=float((x > 0).mean()))
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    V = S.load_v2()
    R = V.R
    b, use, Gd = V.load_inputs(a.data_root, False)
    tabs = R.session_table(b, use)
    bars = R.bar_arrays(b)
    dix = pd.read_csv(a.data_root / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
    gex = dix[dix["date"] < T.RESERVED_FROM].set_index("date")["gex"].astype(float).sort_index()
    frames = {}
    for r in ("ES", "NQ"):
        d = T.root_frame(b, tabs[r], r)
        d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
        d["gd_spx"] = T.gex_prior(gex, d.index)
        short = (d["gd_spx"] < 0) if r == "ES" else (Gd[r].reindex(d.index) < 0)
        d["m_gamma"] = np.where(short.fillna(False), 1.5, 1.0)
        frames[r] = d
    br = {r: {s: bars[(r, s)] for s in frames[r].index if (r, s) in bars} for r in ("ES", "NQ")}
    with ProcessPoolExecutor(max_workers=4) as pool:
        tj = pool.map(G.trades_job, [(r, frames[r], br[r], (R.COST_USD[r], R.USD_PER_POINT[r])) for r in ("ES", "NQ")])
        fj = pool.map(flags_job, [(r, frames[r], br[r]) for r in ("ES", "NQ")])
        tr = pd.DataFrame([x for part in tj for x in part])
        fl = pd.DataFrame([x for part in fj for x in part])
    committed = json.loads((REPO / "data" / "stage0_d666_rebreak.json").read_text(encoding="utf-8"))["cells"]
    for r in ("ES", "NQ"):
        for x in X.EXITS:
            here = float(tr[(tr["root"] == r) & (tr["construct"] == "rebreak")][f"{x}_gross"].mean())
            if abs(here - committed[f"{r}_{x}"]["gate1"]["gross_mean"]) > 1e-9:
                raise SystemExit(f"the rebuild differs from the committed run: {r} {x}")
    tr = tr.merge(fl, on=["root", "session"], how="left")
    pl, rb = tr[tr["construct"] == "plain"], tr[tr["construct"] == "rebreak"].copy()
    # the open class is read against the plain break's side; a re-break on the other side gets its own label
    rb.loc[rb["D"] != rb["D_plain"], "open_class"] = "plain_on_other_side"
    if (pl["D"] != pl["D_plain"]).any():
        raise SystemExit("the flags' plain side disagrees with the trade's")
    rb_sess = rb.set_index(["root", "session"])
    pl = pl.assign(rebreak_same_side=[(k in rb_sess.index and rb_sess.loc[k, "D"] == d_) for k, d_ in
                                      zip(zip(pl["root"], pl["session"]), pl["D"])])
    out: dict = {"spec": "post hoc: is it the gap that makes the retest fail (D666, diag_d666)",
                 "credit": "dealer gamma (GEX): SqueezeMetrics", "G1": {}, "G2": {}, "G3": {}}
    for r in ("ES", "NQ"):
        g = pl[pl["root"] == r]
        out["G1"][r] = {}
        for x in ("E2", "E4"):
            tot = float(g[f"{x}_gross"].sum())
            blk = {"total_sum": tot, "all": cell(g[f"{x}_gross"], tot, R)}
            for c, gc in g.groupby("open_class"):
                blk[c] = cell(gc[f"{x}_gross"], tot, R)
                for rt, gr in gc.groupby("retest_after_plain"):
                    blk[f"{c}|retest={rt}"] = cell(gr[f"{x}_gross"], tot, R)
            for rt, gr in g.groupby("retest_after_plain"):
                blk[f"retest={rt}"] = cell(gr[f"{x}_gross"], tot, R)
            for rt, gr in g.groupby("rebreak_same_side"):
                blk[f"rebreak_same_side={rt}"] = cell(gr[f"{x}_gross"], tot, R)
            out["G1"][r][x] = blk
        out["G1"][r]["class_freq"] = g["open_class"].value_counts(normalize=True).to_dict()
        out["G1"][r]["retest_freq_by_class"] = g.groupby("open_class")["retest_after_plain"].mean().to_dict()
        h = rb[rb["root"] == r]
        out["G2"][r] = {}
        for x in ("E2", "E4"):
            tot = float(h[f"{x}_gross"].sum())
            out["G2"][r][x] = {"all": cell(h[f"{x}_gross"], tot, R),
                               **{c: cell(hc[f"{x}_gross"], tot, R) for c, hc in h.groupby("open_class", dropna=False)}}
        both = g[g["rebreak_same_side"]].set_index("session")
        hb = h.set_index("session").reindex(both.index)
        out["G3"][r] = {x: {"n": int(len(both)), "plain": float(both[f"{x}_gross"].mean()),
                            "rebreak": float(hb[f"{x}_gross"].mean()),
                            "diff": cell(hb[f"{x}_gross"] - both[f"{x}_gross"], 1.0, R)} for x in ("E2", "E4")}
    T.licence_guard(out)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1, default=lambda v: round(v, 3)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
