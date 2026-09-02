"""D292 -- the pre-registered capturability re-check the runner did not run.

    uv run python scripts/d292_capturability.py

D292's pre-registration says "Capturability re-checked at open entry (1e) for
any cell clearing the screen." `run_d292_third_order.py` defined the threshold
and never applied it. That is my omission, and this file closes it rather than
the record quietly dropping a declared check.

TWO NUMBERS PER SURVIVOR, because they answer different things:

  BOOK t at open entry   gate 1e as D290 defined it -- does the confluence
                         book's own edge survive entering at open[t] instead of
                         the close that generated the signal? A book whose edge
                         lives in the overnight gap is not tradeable.
  t_min at open entry    D292's own statistic, recomputed on open-entry returns.
                         Does the second filter still add over the parents once
                         the uncapturable part is removed?

Open-entry returns are built by `d290_entry_test.open_entry`, which subtracts
the entry night from the price path rather than re-accumulating it, so the two
series cannot drift apart.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


D = _load("d292", "run_d292_third_order.py")
ET = _load("d290et", "d290_entry_test.py")
R, M = D.R, D.M
OUT = REPO / "data" / "d292_capturability.json"


def book_t(sums, T):
    """The book's OWN spread t, not a difference against anything."""
    m = (sums[1] > 0) & (sums[3] > 0)
    if int(m.sum()) < M.MIN_BARS:
        return None
    d = sums[0][m] / sums[1][m] - sums[2][m] / sums[3][m]
    sd = d.std(ddof=1)
    if sd == 0:
        return None
    return (float(d.mean() * 1e4),
            float(d.mean() / (sd / np.sqrt(d.size))), int(d.size))


def main() -> int:
    res = json.loads((REPO / "data" / "d292_third_order.json").read_text())
    survivors = [r for r in res["rows"] if r["screen"] or r["promote"]]
    if not survivors:
        print("no screen survivors; nothing to re-check")
        return 0

    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & live
    N, k = res["N"], res["k"]
    fwd_c = M.forward_returns(panel, live)
    g = M.P1.build_grids(panel, cleaned)
    on, idr = ET.segments(g, live, panel)
    fwd_o = ET.open_entry(on, idr, live, (k,))

    order_a, cnt_a, _ = R.ranked(z[D.PRIMARY], base)
    plan = R.LegPlan(order_a, cnt_a, N, T)
    pcts = {}
    for b in D.PARTNERS:
        _, cb, pb = R.ranked(z[b], base)
        pcts[b] = (R.pct_at(pb, cb, plan.lo, plan.cols),
                   R.pct_at(pb, cb, plan.hi, plan.cols))

    print(f"CAPTURABILITY RE-CHECK on {len(survivors)} screen survivors "
          f"(gate 1e: open-entry t >= {D.CAPTURABLE_T})\n")
    print(f"  {'B1':13s} {'B2':13s} {'op':9s} {'f':>5s} | "
          f"{'close bp':>9s} {'close t':>8s} | {'open bp':>9s} {'open t':>7s} "
          f"{'kept':>6s} | {'t_min o':>8s} | 1e")
    out = []
    for r in survivors:
        b1, b2, opn, f = r["B1"], r["B2"], r["op"], r["f"]
        p1lo, p1hi = pcts[b1]
        p2lo, p2hi = pcts[b2]
        klo, khi = D.OPS[opn](p1lo, p1hi, p2lo, p2hi, f, N)
        rows = {}
        for tag, fk in (("close", fwd_c[k]), ("open", fwd_o[k])):
            conf = R.spread_sums(fk, plan, klo, khi, T)
            rows[tag] = book_t(conf, T)
            if tag == "open":
                ts = []
                for plo, phi in ((p1lo, p1hi), (p2lo, p2hi)):
                    mlo, mhi = D.parent_masks(plo, phi, klo, khi)
                    par = R.spread_sums(fk, plan, mlo, mhi, T)
                    st = R.paired_t(conf[0], conf[1], par[0], par[1],
                                    conf[2], conf[3], par[2], par[3])
                    ts.append(None if st is None else st[1])
                tmin_o = None if any(v is None for v in ts) else min(ts)
        cb, ob = rows["close"], rows["open"]
        kept = (ob[0] / cb[0]) if (ob and cb and cb[0]) else None
        cap = ob is not None and ob[1] >= D.CAPTURABLE_T
        print(f"  {b1:13s} {b2:13s} {opn:9s} {f:5.2f} | "
              f"{D.fmt(cb[0] if cb else None, 9, 1)} "
              f"{D.fmt(cb[1] if cb else None, 8)} | "
              f"{D.fmt(ob[0] if ob else None, 9, 1)} "
              f"{D.fmt(ob[1] if ob else None, 7)} "
              f"{(f'{kept:+6.0%}' if kept is not None else '    --')} | "
              f"{D.fmt(tmin_o, 8)} | {'PASS' if cap else 'FAIL'}")
        out.append(dict(B1=b1, B2=b2, op=opn, f=f, void=r["void"],
                        promote=r["promote"], t_min_close=r["t_min"],
                        close_bp=cb[0] if cb else None,
                        close_t=cb[1] if cb else None,
                        open_bp=ob[0] if ob else None,
                        open_t=ob[1] if ob else None,
                        retained=kept, t_min_open=tmin_o, capturable=cap))
    npass = sum(1 for o in out if o["capturable"])
    print(f"\n  {npass} of {len(out)} survivors are capturable at open entry")
    print(f"  and {sum(1 for o in out if o['capturable'] and not o['void'])} of "
          f"those are also not void by the turnover audit")
    json.dump({"purpose": "D292's pre-registered gate-1e re-check, run "
                          "separately because the runner omitted it.",
               "capturable_t": D.CAPTURABLE_T, "rows": out},
              open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
