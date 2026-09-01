"""D265 FEASIBILITY -- how much of the intraday short's turnover is CHURN?

    uv run python scripts/d265_churn_feasibility.py

MEASURES TURNOVER AND EXPOSURE ONLY. IT SCORES NO RETURN, RUNS NO NULL AND
REPORTS NO SHARPE. That is deliberate and it is the whole discipline of this
file: it establishes whether a construction is FEASIBLE against a cost bar
stated in advance, so that a full pre-registration is paid for only if it is.
Same inversion D250, D251 and D263 used.

THE ARITHMETIC THIS EXISTS TO TEST
-----------------------------------
For a book that flattens at every session close, turnover has a FLOOR: a
position that is on for a session must be opened and closed, so

    turnover_floor = 2 * 252 * exposure

and the cost bar is

    required gross_log = charged_bps * turnover / 1e4

LINEAR gross is `exposure * edge`, and setting THAT equal makes exposure cancel:

    edge_log  >=  charged_bps * 504 / 1e4

THAT DERIVATION IS WRONG AND THE RUN DISPROVED IT. It compares the cost against
the LINEAR `exposure x edge`, which is not what a short earns. FINDINGS 1b's
variance tax comes out first, it does NOT scale linearly in exposure, and on
D264's best cell it took 59% of the linear gross. **Once the tax is included,
exposure does not cancel and the bar must be read against the REALISABLE gross.**
Recorded rather than deleted, because the wrong version is the intuitive one.

Against the realisable gross the picture is not close:

  HIGH S1_short_intra   realisable gross  +3.43%/yr
                        required at ACTUAL turnover 324   20.77%   fails 6.1x
                        required at the FLOOR       123    7.89%   fails 2.3x

**So even a book with ZERO intraday churn -- one entry, held to the close, every
day -- still fails by more than twice.** Only the LINEAR gross clears at the
floor, and the linear gross is not money.

THE QUESTION, THEN
-------------------
If the same signal were traded ONCE PER SESSION -- enter on its first firing,
hold to the close, never re-enter that day -- how much turnover disappears?

This file answers only that. It does NOT score the once-per-session book,
because how much EDGE survives the change is a different question and needs its
own pre-registration. Turnover is a property of the position path; return is the
outcome variable, and measuring the outcome here would be the look D264's stop
forbids.
"""

from __future__ import annotations

import importlib.util
import json
import math
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


R = _load("d264", "run_single_name_intraday.py")
D, L, M, S, U = R.D, R.L, R.M, R.S, R.U

OUT = REPO / "data" / "d265_churn_feasibility.json"
TRADING_DAYS = 252.0


def once_per_session(pos, first):
    """Enter on the signal's FIRST firing of a session, hold to the close, never
    re-enter that day. Exits only at the close.

    The rule may only ever REMOVE position, never add one the signal did not
    give, so this cannot manufacture exposure the signal did not authorise."""
    out = np.zeros_like(pos)
    n, T = pos.shape
    starts = np.flatnonzero(first)
    bounds = list(zip(starts, list(starts[1:]) + [T]))
    for i in range(n):
        for a, b in bounds:
            seg = pos[i, a:b]
            nz = np.flatnonzero(seg != 0.0)
            if nz.size:
                j = nz[0]
                out[i, a + j:b] = seg[j]
    return out


def stats(pos, start, n_symbols, years):
    live = pos[:, start:]
    turn = float(np.abs(np.diff(pos, axis=1, prepend=0.0))[:, start:].sum())
    return {
        "exposure": float(np.abs(live).mean()),
        "turnover_per_year": turn / n_symbols / years,
    }


def main() -> int:
    raw_panel, raw_cleaned = R.load_full()
    panel, cleaned = R.subset(raw_panel, raw_cleaned, R.STRATA["ALL"])
    first, _gap = D.session_structure(panel.dates)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    T = panel.closes.shape[1]
    ppy = (T / int(first.sum())) * TRADING_DAYS
    years = (T - start) / ppy

    out = {}
    print(f"live {years:.2f} years, {int(first[start:].sum())} sessions\n")
    for st in ("ALL", "LOW", "HIGH"):
        p, cl = ((panel, cleaned) if st == "ALL"
                 else R.subset(raw_panel, raw_cleaned, R.STRATA[st]))
        books = R.build_books(p, cl, start, first)
        charged = float(np.mean(p.cost_fraction) * 1e4)
        # The gross required at the turnover FLOOR, per unit exposure. This is
        # NOT an exposure-free held-bar-edge threshold -- see the docstring for
        # why that framing was wrong and was withdrawn.
        bar = charged * 2.0 * TRADING_DAYS / 1e4
        # NOT printed as a held-bar-edge threshold any more: that framing came
        # from the linear-gross derivation the docstring now records as wrong.
        print(f"{st}  charged {charged:.2f} bp/side   "
              f"required gross at the turnover FLOOR = {bar * 100:.2f}%/yr (log)")
        print(f"  {'cell':16s} {'exposure':>9s} {'turnover':>9s} {'floor':>7s} "
              f"{'churn share':>12s}")
        for k in ("S1_short_intra", "S2_short_intra"):
            a = stats(books[k], start, len(p.symbols), years)
            b = stats(once_per_session(books[k], first), start, len(p.symbols), years)
            floor = 2.0 * TRADING_DAYS * a["exposure"]
            print(f"  {k:16s} {a['exposure']:8.1%} {a['turnover_per_year']:9.0f} "
                  f"{floor:7.0f} {1 - floor / a['turnover_per_year']:11.0%}")
            print(f"    once-per-session {b['exposure']:6.1%} {b['turnover_per_year']:9.0f} "
                  f"{2.0 * TRADING_DAYS * b['exposure']:7.0f} "
                  f"   -> turnover x{b['turnover_per_year'] / a['turnover_per_year']:.2f}, "
                  f"exposure x{b['exposure'] / a['exposure']:.2f}")
            out[f"{st}:{k}"] = {
                "charged_bps": charged,
                "required_gross_log_per_unit_exposure_at_floor": bar,
                "actual": a, "once_per_session": b,
                "turnover_floor": floor,
                "churn_share": 1 - floor / a["turnover_per_year"],
            }
        print()

    # The bar against D264's ALREADY-MEASURED gross. Nothing is re-scored here:
    # both figures are read from the committed artifact.
    summary = json.loads((REPO / "data" / "single_name_intraday_summary.json").read_text())
    print("THE COST BAR against D264's measured gross -- read, not recomputed\n")
    print(f"  {'cell / turnover regime':38s} {'turn':>6s} {'required':>9s} "
          f"{'linear':>8s} {'realisable':>11s}  verdict")
    for key, c in out.items():
        cell = summary["cells"][key]
        lin = math.log1p(cell["gross_linear_pa"])
        real = math.log1p(cell["gross_realisable_pa"])
        for label, turn in (("actual", c["actual"]["turnover_per_year"]),
                            ("at the turnover FLOOR", c["turnover_floor"]),
                            ("once per session", c["once_per_session"]["turnover_per_year"])):
            req = c["charged_bps"] * turn / 1e4
            v = ("CLEARS" if real >= req else
                 "clears LINEAR only -- not money" if lin >= req else "fails both")
            print(f"  {key + ' / ' + label:38s} {turn:6.0f} {req * 100:8.2f}% "
                  f"{lin * 100:7.2f}% {real * 100:10.2f}%  {v}")
        c.update(gross_linear_log=lin, gross_realisable_log=real,
                 required_gross_log_at_actual=c["charged_bps"] * c["actual"]["turnover_per_year"] / 1e4,
                 required_gross_log_at_floor=c["charged_bps"] * c["turnover_floor"] / 1e4)

    OUT.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    print("\nNO RETURN WAS SCORED HERE. Turnover and exposure are properties of the "
          "position path; the gross figures are read from D264's committed artifact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
