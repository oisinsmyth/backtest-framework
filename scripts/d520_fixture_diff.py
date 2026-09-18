"""D520 -- what the mapping-window label fix changed in `fut_sessions_hourly`, per root, cell by cell.

    python scripts/d520_fixture_diff.py --old temp/d520_old --new data/fixtures    # -> data/d520_fixture_diff.json

Data layer only: this measures two tables against each other. Nothing here computes a return, a
signal or an edge.

WHAT IT REPORTS, and why each piece is here
-------------------------------------------
1. Rows GAINED and LOST per root. A session row appears or vanishes when the PRESENT rule
   (h09..h15 >= 200 bars) crosses in one build and not the other, which is exactly what removing a
   foreign instrument's bars can do.
2. For rows present in BOTH builds: how many rows changed, which of the 138 segment columns, and
   the size of the change. Prices are compared in RELATIVE terms (a price level means nothing
   across nine roots whose prices span 0.01 to 24,000) and bar counts and volumes in absolute
   terms, because those are the quantities the contamination adds.
3. The contract LABELS -- `contract`, `front_prev`, `same_front`. A different front month is a
   different instrument, not a different number, and it is the change a study would notice last.
4. CL on its own, because D495 published "CL B2 has the highest GROSS Sharpe measured anywhere --
   +1.09" off this panel: the affected sessions, their dates, the size of the price change, and
   what fraction of them fall inside CL's G5 usable window (2016-01-04), which is the only part of
   the panel a study is allowed to read.

The old fixture must be the committed build (`git show`), not a re-run: R16 -- reproduce a
published number on the build it was published on.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]


def _rel(path: Path) -> str:
    """A path as the repository sees it, so provenance survives leaving this machine."""
    try:
        return path.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return path.as_posix()
SEG = [18, 19, 20, 21, 22, 23] + list(range(0, 17))
SEGN = [f"h{h:02d}" for h in SEG]
PRICE = [f"{s}_{f}" for s in SEGN for f in ("o", "h", "l", "c")]
COUNT = [f"{s}_{f}" for s in SEGN for f in ("v", "n")]
LABEL = ["contract", "front_prev", "same_front", "prev_day", "bars"]
KEY = ["root", "day"]
USABLE = {"ES": "2016-01-04", "NQ": "2016-01-04", "YM": "2016-01-04", "ZN": "2016-01-04",
          "ZB": "2016-01-04", "GC": "2016-01-04", "CL": "2016-01-04", "6E": "2016-01-04",
          "RTY": "2017-07-10"}      # from the committed meta's G5, unchanged by this fix


def load(p: Path) -> pd.DataFrame:
    return pd.read_csv(p, dtype={"root": str, "day": str, "prev_day": str, "contract": str,
                                 "front_prev": str})


def as_text(s: pd.Series) -> np.ndarray:
    """A label column as comparable text, with a MISSING sentinel.

    `.astype(str)` is not enough: under pandas' string dtype a missing value stays NA, `NA != NA`
    is NA, and a mask of NA counted 41 unchanged rows as changed on the first run of this diff --
    every one of them a `front_prev` that is absent in BOTH builds. Filling first is what makes the
    comparison mean what it says."""
    return s.astype(object).where(s.notna(), "<MISSING>").astype(str).to_numpy()


def cell_diff(a: pd.DataFrame, b: pd.DataFrame, cols, relative: bool):
    """(n_cells_differing, per-column counts, the change magnitudes). NaN-vs-NaN counts as equal and
    NaN-vs-number counts as a difference, which is the point: a segment that had a foreign bar and
    now has none is a changed cell."""
    A = a[cols].to_numpy(float)
    B = b[cols].to_numpy(float)
    both = np.isfinite(A) & np.isfinite(B)
    onena = np.isfinite(A) != np.isfinite(B)
    if relative:
        with np.errstate(invalid="ignore", divide="ignore"):
            d = np.where(both, np.abs(B - A) / np.maximum(np.abs(A), 1e-12), 0.0)
        neq = both & (d > 1e-9)
    else:
        d = np.where(both, np.abs(B - A), 0.0)
        neq = both & (d > 0)
    diff = neq | onena
    per = {c: int(n) for c, n in zip(cols, diff.sum(axis=0)) if n}
    mag = d[neq]
    return int(diff.sum()), per, mag, int(onena.sum())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", default="temp/d520_old")
    ap.add_argument("--new", default="data/fixtures")
    ap.add_argument("--out", default="data/d520_fixture_diff.json")
    a = ap.parse_args()
    old_dir, new_dir = REPO / a.old, REPO / a.new
    O = load(old_dir / "fut_sessions_hourly.csv.gz")
    N = load(new_dir / "fut_sessions_hourly.csv.gz")
    OR = pd.read_csv(old_dir / "fut_sessions_rolls.csv.gz", dtype={"day": str})
    NR = pd.read_csv(new_dir / "fut_sessions_rolls.csv.gz", dtype={"day": str})
    assert list(O.columns) == list(N.columns), "the two builds must share a schema or the diff is meaningless"
    print(f"OLD {len(O):,} rows   NEW {len(N):,} rows   ({len(N) - len(O):+,})")

    # RELATIVE TO THE REPO ROOT, NOT ABSOLUTE (D544). The committed
    # `data/d520_fixture_diff.json` records `C:\Users\O\...\temp\d520_old` -- a path
    # inside `temp/`, which this repository declares deletable unasked, on one machine. Nobody
    # can re-resolve it, including its author. That artifact is left as it is because the
    # unresolvable path IS the record of the provenance being unresolvable; what is fixed here
    # is that the next run does not produce another one.
    rep = {"old": _rel(old_dir), "new": _rel(new_dir), "n_old": len(O), "n_new": len(N),
           "columns": len(O.columns), "usable_start": USABLE, "roots": {}}
    print(f"\n{'root':>5} {'old':>6} {'new':>6} {'gain':>5} {'lost':>5} {'rows chg':>9} "
          f"{'price cells':>12} {'count cells':>12} {'label rows':>11} {'p50 |dP|':>10} {'max |dP|':>10}")
    for root in sorted(set(O["root"]) | set(N["root"])):
        o = O[O["root"] == root].set_index("day").sort_index()
        n = N[N["root"] == root].set_index("day").sort_index()
        gained = sorted(set(n.index) - set(o.index))
        lost = sorted(set(o.index) - set(n.index))
        common = sorted(set(o.index) & set(n.index))
        oc, nc = o.loc[common], n.loc[common]
        np_, pper, pmag, pna = cell_diff(oc, nc, PRICE, relative=True)
        nc_, cper, cmag, cna = cell_diff(oc, nc, COUNT, relative=False)
        lab = {c: int((as_text(oc[c]) != as_text(nc[c])).sum()) for c in LABEL}
        lab_rows = int(np.any(np.column_stack([as_text(oc[c]) != as_text(nc[c])
                                               for c in LABEL]), axis=1).sum())
        lab_days = [d for d, f in zip(common, np.any(np.column_stack(
            [as_text(oc[c]) != as_text(nc[c]) for c in LABEL]), axis=1)) if f]
        rowchg = int(np.any(np.column_stack([
            (oc[PRICE + COUNT].to_numpy(float) != nc[PRICE + COUNT].to_numpy(float))
            & ~(pd.isna(oc[PRICE + COUNT].to_numpy(float)) & pd.isna(nc[PRICE + COUNT].to_numpy(float)))]),
            axis=1).sum())
        chg_days = [d for d, f in zip(common, np.any(
            (oc[PRICE + COUNT].to_numpy(float) != nc[PRICE + COUNT].to_numpy(float))
            & ~(pd.isna(oc[PRICE + COUNT].to_numpy(float)) & pd.isna(nc[PRICE + COUNT].to_numpy(float))),
            axis=1)) if f]
        us = USABLE.get(root, "0000")
        rep["roots"][root] = {
            "n_old": len(o), "n_new": len(n), "gained": gained, "lost": lost,
            "n_common": len(common), "rows_changed": rowchg,
            "rows_changed_in_usable_window": int(sum(d >= us for d in chg_days)),
            "changed_days": chg_days[:400], "n_changed_days": len(chg_days),
            "price_cells_changed": np_, "price_cells_nan_flip": pna,
            "price_cols_changed": pper,
            "price_rel_change": {"p50": float(np.median(pmag)) if len(pmag) else None,
                                 "p95": float(np.percentile(pmag, 95)) if len(pmag) else None,
                                 "max": float(pmag.max()) if len(pmag) else None},
            "count_cells_changed": nc_, "count_cells_nan_flip": cna,
            "count_cols_changed": cper,
            "count_abs_change": {"p50": float(np.median(cmag)) if len(cmag) else None,
                                 "max": float(cmag.max()) if len(cmag) else None},
            "label_cells_changed": lab, "label_rows_changed": lab_rows,
            "label_changed_days": lab_days[:400],
        }
        print(f"{root:>5} {len(o):>6} {len(n):>6} {len(gained):>5} {len(lost):>5} {rowchg:>9} "
              f"{np_:>12} {nc_:>12} {lab_rows:>11} "
              f"{(f'{np.median(pmag):.2e}' if len(pmag) else '-'):>10} "
              f"{(f'{pmag.max():.2e}' if len(pmag) else '-'):>10}")

    # ---- rolls ----
    ok = ["root", "day", "from_contract", "to_contract"]
    mo = OR.set_index(ok[:2]) if len(OR) else OR
    rep["rolls"] = {"n_old": len(OR), "n_new": len(NR),
                    "gained": NR.merge(OR, on=ok, how="left", indicator=True)
                                .query('_merge=="left_only"')[ok].to_dict("records"),
                    "lost": OR.merge(NR, on=ok, how="left", indicator=True)
                              .query('_merge=="left_only"')[ok].to_dict("records")}
    print(f"\nrolls: old {len(OR)} new {len(NR)}  gained {len(rep['rolls']['gained'])} "
          f"lost {len(rep['rolls']['lost'])}")
    for r in rep["rolls"]["gained"][:12]:
        print(f"   + {r}")
    for r in rep["rolls"]["lost"][:12]:
        print(f"   - {r}")

    # ---- CL, because D495 published a +1.09 gross Sharpe off this panel ----
    o = O[O["root"] == "CL"].set_index("day").sort_index()
    n = N[N["root"] == "CL"].set_index("day").sort_index()
    common = sorted(set(o.index) & set(n.index))
    oc, nc = o.loc[common], n.loc[common]
    A, B = oc[PRICE].to_numpy(float), nc[PRICE].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        rel = np.where(np.isfinite(A) & np.isfinite(B), np.abs(B - A) / np.maximum(np.abs(A), 1e-12), np.nan)
    rowmax = np.nanmax(np.where(np.isfinite(rel), rel, -1), axis=1)
    flips = (np.isfinite(A) != np.isfinite(B)).sum(axis=1)
    bad = [(d, float(m), int(f)) for d, m, f in zip(common, rowmax, flips) if m > 1e-9 or f]
    cl = {"n_sessions_common": len(common),
          "n_sessions_with_any_price_change": len(bad),
          "n_in_usable_window": int(sum(d >= USABLE["CL"] for d, *_ in bad)),
          "worst": sorted(bad, key=lambda x: -x[1])[:25],
          "by_year": {}}
    for y in sorted({d[:4] for d, *_ in bad}):
        cl["by_year"][y] = int(sum(d[:4] == y for d, *_ in bad))
    print(f"\nCL: {len(bad)} of {len(common)} common sessions carry a changed price cell; "
          f"{cl['n_in_usable_window']} of them are inside the G5 usable window "
          f"({USABLE['CL']} onward)")
    print(f"  by year: {cl['by_year']}")
    print("  worst 12 by max relative price change (day, max |dP|/P, NaN flips):")
    for d, m, f in cl["worst"][:12]:
        print(f"    {d}  {m:11.4%}  flips {f:>3}  old contract {o.loc[d, 'contract']} -> "
              f"{n.loc[d, 'contract']}")
    rep["CL"] = cl

    out = REPO / a.out
    out.write_text(json.dumps(rep, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
