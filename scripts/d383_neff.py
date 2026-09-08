"""D383 -- n_eff, concurrency and the fully-costed net, for the RESULT record.

    uv run python scripts/d383_neff.py

NOTHING HERE SCORES A NEW CELL. It reads `data/d383_observed.json` and the cached mining panel
and answers three questions the headline numbers are uninterpretable without:

  1. n_eff INSTRUMENTS -- `ragged_panel.effective_instruments` on the mining panel. FINDINGS s4
     puts this near 2.2 on the 57-ETF DAILY universe; it has never been measured at 15 minutes.
  2. n_eff TRADES -- R10: a pooled trade count is not a sample size. Concurrency (mean and max
     names held at once, and the share of bars above a crowding line) is measured against a
     PER-SYMBOL-ROTATED book of identical exposure, and `trades / mean concurrency` is reported
     as the deflated count.
  3. THE FULLY-COSTED NET -- `net_mean_bp` in the observed artifact charges IBKR commission only.
     Here the MEASURED Corwin-Schultz half-spread of the names actually HELD is charged as well,
     which is D285's lesson (a guessed 15 bp/side bar missed by 0.65; the held names measured
     33.8).

The reserved window is not read: this reads the same mining cache the runner built.
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


RP = _load("ragged_panel", "ragged_panel.py")
D = _load("d383", "run_d383_ts_structure_screen.py")

OUT = REPO / "data" / "d383_neff.json"
CROWD = 20          # R10's crowding line on this universe, as D249 used it


def main() -> int:
    panel, g, sp = D.load_mined()
    n, T = panel.shape
    ppy = panel.ppy
    print(f"mining panel {n} x {T:,}  {sp['first']} -> {sp['last']}  ppy {ppy:,.0f}")

    eff = RP.effective_instruments(panel, D.WARMUP, min_overlap=250)
    print(f"\n  [n_eff INSTRUMENTS] {eff:.2f} of {n} at 15 minutes "
          f"(FINDINGS s4 puts the 57-ETF DAILY figure near 2.2)")

    obs = json.loads((REPO / "data" / "d383_observed.json").read_text())
    rep = json.loads((REPO / "data" / "d383_ts_structure_screen.json").read_text())
    cells = obs["cells"]
    cs_half = D.corwin_schultz(g["high"], g["low"]) / 2.0 * 1e4
    C = D.trade_cumsum(panel)
    z = np.load(D.EVENT_CACHE, allow_pickle=False)

    # The cells the record actually quotes: the best on each statistic at each hold, the ten that
    # clear the pre-registered floor, and the own-null survivors at the primary hold.
    want = set()
    grid = {k: v for k, v in rep["cells"].items() if v["group"] == "grid"}
    for h in D.HOLDS:
        cs = [v for v in grid.values() if v["hold"] == h]
        want.add(max(cs, key=lambda v: v["mean_bp"])["feature"] + f"|{max(cs, key=lambda v: v['mean_bp'])['window']}"
                 + f"|{h}|" + max(cs, key=lambda v: v["mean_bp"])["tail"])
        b = max(cs, key=lambda v: v["bp_per_bar"])
        want.add(f"{b['feature']}|{b['window']}|{h}|{b['tail']}")
    for k, v in grid.items():
        if v["clears_both_mean"]:
            want.add(k)
        if v["hold"] == D.PRIMARY_HOLD and len(v["own_null"]) == 2 \
                and all(x["beats_own_rate_p95"] for x in v["own_null"].values()):
            want.add(k)

    out = {}
    print(f"\n  {len(want)} quoted cells\n")
    hdr = (f"{'cell':<26}{'trades':>8}{'conc':>7}{'max':>5}{'rotmx':>6}{'>20':>7}{'sdrat':>7}"
           f"{'n_eff tr':>10}{'gross':>10}{'net(all)':>10}{'RTcost':>8}")
    print(hdr)
    for k in sorted(want):
        c = grid[k]
        f, W, h, tag = c["feature"], c["window"], c["hold"], c["tail"]
        rows, cols = D._ev(z, f, W, tag)
        pos = D.positions_grid(rows, cols, n, T, h).astype(float)
        con = RP.concurrency(panel, pos, D.WARMUP, seed=0)
        r, s, L = D.runs_from_events(rows, cols, n, T, h)
        tr, ln, trow, tstart = D.trades_of_runs(r, s, L, C, T)
        half = cs_half[trow, tstart]
        rt = 2.0 * (np.nan_to_num(half, nan=float(np.nanmedian(cs_half)))
                    + panel.cost_fraction[trow] * 1e4)
        net = tr - rt
        # R10: a pooled count is not a sample size. Deflate by the mean concurrency.
        neff_tr = float(tr.size) / max(con["mean_held"], 1.0)
        held_ct = (pos[:, D.WARMUP:] != 0.0).sum(axis=0)
        row = dict(
            trades=int(tr.size), mean_names=con["mean_held"], max_names=con["max_held"],
            rotated_max_names=con["rot_max_held"], rotated_mean_names=con["rot_mean_held"],
            sd_ratio=con["sd_ratio"],
            share_bars_over_crowd=float((held_ct > CROWD).mean()),
            n_eff_trades=neff_tr, gross_mean_bp=float(tr.mean()),
            net_mean_bp_full_cost=float(net.mean()),
            round_trip_cost_bp=float(np.median(rt)),
            held_cs_half_bp=float(np.nanmedian(half)),
            bp_per_bar=c["bp_per_bar"], exposure=c["exposure"],
            excess_over_bh_cagr=c["excess_over_bh_cagr"],
            clears_both_mean=c["clears_both_mean"], clears_both_rate=c["clears_both_rate"])
        out[k] = row
        print(f"{k:<26}{row['trades']:>8,}{row['mean_names']:>7.1f}{row['max_names']:>5}"
              f"{row['rotated_max_names']:>6}{row['share_bars_over_crowd']:>7.1%}"
              f"{row['sd_ratio']:>7.2f}{row['n_eff_trades']:>10,.0f}"
              f"{row['gross_mean_bp']:>10,.1f}{row['net_mean_bp_full_cost']:>10,.1f}"
              f"{row['round_trip_cost_bp']:>8.2f}")

    nul = json.loads((REPO / "data" / "d383_nulls.json").read_text())
    payload = dict(
        study=383, note=__doc__.split("\n")[0], split=sp, ppy=ppy,
        n_eff_instruments=dict(value=eff, of=n, min_overlap=250, start=D.WARMUP,
                               reference="FINDINGS s4: ~2.2 on the 57-ETF DAILY universe"),
        n_eff_null_draws=nul["draws"],
        crowding_line=CROWD, cells=out)
    OUT.write_text(json.dumps(payload, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
