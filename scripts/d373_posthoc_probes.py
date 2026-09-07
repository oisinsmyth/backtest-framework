"""D373 POST-HOC — the two reads the RESULT record quotes that the runner itself does not produce.

    uv run python scripts/d373_posthoc_probes.py        writes data/d373_posthoc.json

NEITHER IS PRE-REGISTERED. Both were written after the fact and are labelled post-hoc wherever quoted. They live in
`scripts/` and persist to `data/` rather than staying in `temp/` because a file a record quotes is evidence (CLAUDE.md).

PROBE 1 -- HOW WIDE IS H1's MARGIN, REALLY?
H1's only meaningful leg is B_c, the same-day same-cohort name swap, and the observed mean clears its p95 by +4.95 bp per
trade. The four-groups block names the top trade as GME entered 2021-01-04 at $17.25, held 40 bars, +40,029 bp -- 6.34%
of the whole ledger. One trade worth ~+10 bp of the mean against a +4.95 margin is not a rhetorical concern, so this
recomputes the mean under progressive removals and re-tests it against the SAME stored control percentiles.

PROBE 2 -- IS H7's 0.935 SHARED NAMES, OR SHARED HEDGE RESIDUAL?
Two independent readings: the partial correlation of the two deployed series controlling for the floored market (does
beta explain it?), and the direct name-bar overlap of the two trade ledgers (do they literally hold the same positions?).

Both probes re-derive D373's ledger THROUGH THE RUNNER and assert it reproduces the committed report before cutting
anything, so neither can silently measure a different book than the one the record reports.
"""

from __future__ import annotations

import collections
import csv
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d373_posthoc.json"
SQUEEZE = ("2020-11-01", "2021-03-31")


def load_runner():
    sys.path.insert(0, str(REPO / "src"))
    spec = importlib.util.spec_from_file_location("d373", REPO / "scripts" / "run_d373_winners_dip_long.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["d373"] = m
    spec.loader.exec_module(m)
    return m


def corr(x, y):
    return float(np.corrcoef(x, y)[0, 1])


def resid(y, x):
    A = np.vstack([np.ones_like(x), x]).T
    return y - A @ np.linalg.lstsq(A, y, rcond=None)[0]


def probe_margin(pnl, syms, dates, rep):
    """[TT] progressive removals, re-tested against the committed control percentiles -- not against re-drawn nulls."""
    bc95 = rep["hurdles"]["H1"]["legs"]["Bc"]["p95"]
    a95 = rep["hurdles"]["H1"]["legs"]["A"]["p95"]
    rows = []

    def row(label, keep, n_removed):
        mu = float(pnl[keep].mean())
        rows.append(dict(cut=label, removed=int(n_removed), n=int(keep.sum()), mean_bp=mu,
                         vs_Bc_p95=mu - bc95, above_Bc=bool(mu > bc95),
                         vs_A_p95=mu - a95, above_A=bool(mu > a95)))

    row("observed", np.ones(len(pnl), bool), 0)
    order = np.argsort(pnl)[::-1]
    for k in (1, 2, 3, 5, 10, 20):
        keep = np.ones(len(pnl), bool)
        keep[order[:k]] = False
        row(f"drop top {k} trades", keep, k)
    keep = syms != "GME"
    row("drop all GME", keep, (~keep).sum())
    sq = (dates >= SQUEEZE[0]) & (dates <= SQUEEZE[1])
    row(f"drop entries {SQUEEZE[0]}..{SQUEEZE[1]}", ~sq, sq.sum())
    return dict(Bc_p95=bc95, A_p95=a95, rows=rows)


def probe_h7(m, P, res, rep):
    """[H7] partial correlation against the market, and the literal name-bar overlap of the two ledgers."""
    mine = np.asarray(res["book_dep_x"], float)
    mask = np.asarray(res["mask_dep"], bool)
    ix = {str(d): i for i, d in enumerate(P["dates"])}

    rows = [r for r in csv.DictReader((REPO / "data" / "d365_series_95_80.csv").open())]
    sel = [(ix[r["date"]], float(r["net_PUB_bp"]), float(r["market_bp"])) for r in rows if r["date"] in ix]
    idx = np.array([p[0] for p in sel])
    oth = np.array([p[1] for p in sel])
    mkt = np.array([p[2] for p in sel])
    k = mask[idx] & np.isfinite(oth) & np.isfinite(mine[idx]) & np.isfinite(mkt)
    a, b, mk = mine[idx][k], oth[k], mkt[k]

    symbols = list(P["symbols"])
    sym_ix = {s: i for i, s in enumerate(symbols)}
    held365 = np.zeros((P["T"], P["n"]), bool)
    cnt, unmatched = collections.Counter(), 0
    for r in csv.DictReader((REPO / "data" / "d365_trades_95_80.csv").open()):
        cnt[r["symbol"]] += 1
        j = sym_ix.get(r["symbol"])
        if j is None:
            unmatched += 1
            continue
        e0, h = int(r["bar_entry"]), int(r["hold_bars"])
        held365[e0:e0 + h, j] = True
    held373 = np.zeros((P["T"], P["n"]), bool)
    for row_, e0, age, _p, _side in res["trades"]:
        held373[e0:e0 + age, row_] = True

    inter = int((held365 & held373).sum())
    n373 = {symbols[t[0]] for t in res["trades"]}
    out = dict(bars=int(k.sum()),
               corr_raw=corr(a, b), corr_D373_market=corr(a, mk), corr_D365_market=corr(b, mk),
               corr_partial_controlling_market=corr(resid(a, mk), resid(b, mk)),
               d365_name_bars=int(held365.sum()), d373_name_bars=int(held373.sum()), intersection=inter,
               share_of_d373=inter / max(1, int(held373.sum())), share_of_d365=inter / max(1, int(held365.sum())),
               jaccard=inter / max(1, int((held365 | held373).sum())),
               names_d365=len(cnt), names_d373=len(n373), names_shared=len(set(cnt) & n373),
               unmatched_d365_symbols=unmatched)
    assert abs(out["corr_raw"] - rep["hurdles"]["H7"]["arms"]["d365_momentum_buffer/net_PUB"]["corr"]) < 1e-6, \
        "[H7] the probe's raw correlation does not match the runner's -- it is reading a different series"
    return out


def main() -> int:
    m = load_runner()
    P = m.PREP.prep(need_grids=False)
    P["rsi_pct_ok"] = np.isfinite(np.asarray(P["PCT"]["rsi"]))
    P["elig_b"] = np.asarray(P["elig"]) & P["rsi_pct_ok"]
    (c, s), (e, cap) = m.CELLS[m.PRIMARY_IX]
    res = m.run_long(P, m.mirror(P, c, s), m.V59.grids(P)[1], e, cap)

    pnl = np.asarray(m.V47.pnl_bp(res), float)
    syms = np.asarray([P["symbols"][t[0]] for t in res["trades"]])
    dates = np.asarray([str(P["dates"][t[1]]) for t in res["trades"]])
    rep = json.loads((REPO / "data" / "d373_winners_dip_long.json").read_text())
    assert abs(float(pnl.mean()) - rep["observed"]["trade_mean_bp"]) < 1e-9, \
        "[TT] the re-derived ledger does not reproduce the committed report -- refusing to probe a different book"
    assert len(pnl) == rep["observed"]["trades"], "[TT] trade count does not match the committed report"

    margin, h7 = probe_margin(pnl, syms, dates, rep), probe_h7(m, P, res, rep)
    out = dict(study=373, kind="POST-HOC, not pre-registered",
               observed=dict(trades=len(pnl), mean_bp=float(pnl.mean())),
               probe1_h1_margin_sensitivity=margin, probe2_h7_decomposition=h7)
    OUT.write_text(json.dumps(out, indent=2))                     # [P] PERSIST BEFORE RENDERING
    print(f"wrote {OUT}")

    print(f"\n  PROBE 1 -- how wide is H1's margin?   B_c p95 {margin['Bc_p95']:+.2f}   A' p95 {margin['A_p95']:+.2f}")
    for r in margin["rows"]:
        print(f"    {r['cut']:<34} n {r['n']:>6,}  mean {r['mean_bp']:+8.2f}   "
              f"vs B_c {r['vs_Bc_p95']:+7.2f} {'ABOVE' if r['above_Bc'] else 'BELOW'}   "
              f"vs A' {r['vs_A_p95']:+7.2f} {'ABOVE' if r['above_A'] else 'BELOW'}")

    print(f"\n  PROBE 2 -- H7 decomposed, over {h7['bars']:,} shared bars")
    print(f"    corr raw {h7['corr_raw']:+.4f}   D373 vs market {h7['corr_D373_market']:+.4f}   "
          f"D365 vs market {h7['corr_D365_market']:+.4f}   PARTIAL {h7['corr_partial_controlling_market']:+.4f}")
    print(f"    name-bars: D365 {h7['d365_name_bars']:,}  D373 {h7['d373_name_bars']:,}  shared {h7['intersection']:,} "
          f"({h7['share_of_d373']:.1%} of D373)  Jaccard {h7['jaccard']:.3f}")
    print(f"    distinct names: D365 {h7['names_d365']:,}  D373 {h7['names_d373']:,}  shared {h7['names_shared']:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
