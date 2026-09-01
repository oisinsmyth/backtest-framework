"""D279 defect fix -- E-prime was measured over the PANEL, not over the HELD BOOK.

    uv run python scripts/d279_fix_eprime.py

WHAT WENT WRONG. D279's pre-registration specifies E-prime as "effective
independent instruments >= 3.0 OVER THE HELD BOOK". The runner called
`RP.effective_instruments(panel, 0)`, which measures the whole 1,573-name
panel. It returned 5.44 for every cell, so the hurdle was CONSTANT across the
grid and discriminated nothing -- a top-10 book and a 1,200-name book scored
identically on a hurdle whose entire purpose is to tell them apart.

This is the same class of defect D230 and D270 found: a hurdle that is computed,
reported, and not actually applied to the thing it names. It is fixed here
rather than in a re-run because the rotation nulls are unaffected -- they are a
function of the positions, and no position changed.

WHAT E-PRIME IS SUPPOSED TO CATCH, and why the panel version cannot. A book
holding ten names that all trade together is one bet, not ten. Measuring the
panel answers "how many independent things exist in the universe"; the hurdle
asks "how many independent things is this book actually holding". For a
rotating top-N book those are different numbers and the difference is the whole
point of the substitution D279 declared in advance.

Correlations are taken on bars where BOTH names were HELD, not merely live.
Two names held in different years are not a diversified pair and must not be
scored as one, which is exactly what `live` overlap would have allowed.

NO CELL IS ADDED AND NO NULL IS RE-RUN. The ledger is unchanged.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
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


B = _load("d256", "run_book_single_names.py")
C = _load("d279", "run_concentrated_short.py")
RP, U = B.RP, B.U

SUMMARY = REPO / "data" / "d279_concentrated_summary.json"
MIN_OVERLAP = 250


def eff_over_book(panel, pos, start=0, min_overlap=MIN_OVERLAP):
    """1 / (w' R w) at equal weights, over the bars each name was HELD.

    `RP.effective_instruments` is this computation over `panel.live`. The only
    change is the mask: a pair counts only where BOTH names were in the book at
    the same time, so names the book rotated through in different years are not
    credited as a diversified pair."""
    r = panel.log_returns[:, start:]
    h = (pos[:, start:] != 0.0) & panel.live[:, start:]
    keep = np.flatnonzero(h.sum(axis=1) >= min_overlap)
    n = keep.size
    if n == 0:
        return 0.0, 0
    R = np.eye(n)
    for a in range(n):
        i = keep[a]
        for b in range(a + 1, n):
            j = keep[b]
            m = h[i] & h[j]
            if m.sum() >= min_overlap:
                x, y = r[i][m], r[j][m]
                if x.std() > 0 and y.std() > 0:
                    R[a, b] = R[b, a] = float(np.corrcoef(x, y)[0, 1])
    return float(n * n / R.sum()), n


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=C.FEE)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    ok = ~(np.isnan(md) | np.isnan(hs)) & warm
    sok = ~(np.isnan(g_lo) | np.isnan(g_hi) | np.isnan(atr)) & warm
    s1 = -B.hold_book((hs < 0) & (md >= 0) & ok, warm)
    s2 = -B.walk_state(panel, (g_lo < 0) & (g_hi < 0) & sok, warm, U.AGE_CAP)
    arms = {"S1_short": (s1, hs), "S2_short": (s2, g_lo)}

    rng = np.random.default_rng(C.SEED)
    books = {}
    for arm, (base, score) in arms.items():
        books[f"{arm}|all"] = base
        for N in C.N_LEVELS:
            books[f"{arm}|top{N}"] = C.top_n(base, score, N)
            books[f"{arm}|rnd{N}"] = C.top_n(base, score, N, rng=rng)
    print(f"rebuilt the 14 books {time.time() - t0:.0f}s "
          f"(same seed, same order -- positions are identical)\n", flush=True)

    d = json.loads(SUMMARY.read_text())
    panel_eff = d["effective_instruments"]
    print(f"  panel-wide value the runner used for every cell: {panel_eff:.2f}\n")
    print(f"  {'cell':16s} {'names>=250 held':>16s} {'E-prime(book)':>14s} "
          f"{'entries':>8s}  {'E-prime':>8s}  was  now")
    for k, p in books.items():
        e, n_kept = eff_over_book(panel, p)
        c = d["cells"][k]
        was = c["Eprime"]
        now = bool(e >= 3.0 and c["entries"] >= 500)
        c["effective_instruments_book"] = e
        c["names_held_over_min_overlap"] = n_kept
        c["Eprime_panel_defect"] = was
        c["Eprime"] = now
        c["clears_all"] = bool(c["H"] and c["V"] and c["C"] and c["F"] and now)
        flag = "  <-- CHANGED" if was != now else ""
        print(f"  {k:16s} {n_kept:16d} {e:14.2f} {c['entries']:8,d}  "
              f"{'YES' if now else 'no':>8s}  {'Y' if was else '.'}    "
              f"{'Y' if now else '.'}{flag}", flush=True)

    surv = [k for k, c in d["cells"].items() if c["clears_all"]]
    d["survivors"] = surv
    d["eprime_defect"] = (
        "The runner measured E-prime with RP.effective_instruments(panel, 0), "
        "which is the whole 1,573-name panel and returned 5.44 for every cell. "
        "D279 specifies E-prime over the HELD BOOK. Recomputed here on bars "
        "where both names were held; nulls and positions are unchanged.")
    SUMMARY.write_text(json.dumps(d, indent=1))
    print(f"\n  SURVIVORS after the fix: {surv or 'NONE'}")
    print(f"  updated {SUMMARY.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
