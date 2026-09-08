"""Independent verification of the ETF fixture before any study touches it.

Checks the three things that would make it unfit: the gates are real and empty, the two data-quality exclusions are actually absent,
and the loader accepts it. Also measures the breadth D382 will actually get, and the mining/reserved split.
"""
import gzip
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
FIX = REPO / "data" / "fixtures" / "etf_wide_daily_raw.csv.gz"
EV = REPO / "data" / "fixtures" / "etf_wide_daily_raw_events.json"

meta = json.loads((REPO / "data" / "fixtures" / "etf_wide_daily_raw.meta.json").read_text())
gates = meta["gates"]
real = {k: len(v["failures"]) for k, v in gates.items() if isinstance(v, dict) and "failures" in v}
print(f"[GATE] real gates {real}  -- a gate with a non-empty failures list would refuse the load")
assert real and not any(real.values()), "gates are not clean"

excluded = {r["symbol"] if isinstance(r, dict) else r for r in gates.get("excluded_for_data_quality", [])}
print(f"[EXCL] excluded for data quality: {sorted(excluded) if excluded else '(none listed in that key)'}")

syms = set()
with gzip.open(FIX, "rt") as f:
    next(f)
    for line in f:
        syms.add(line.split(",", 2)[1])
print(f"[FIX ] {len(syms)} symbols in the fixture")
for bad in ("EGLE", "PHD"):
    print(f"       {bad} present in fixture: {bad in syms}   <- must be False")
    assert bad not in syms, f"{bad} carries an unexplained x24 move and is IN the fixture"

panel, cleaned = RP.load_ragged(FIX, EV, fee_bps=0.0)
print(f"[LOAD] accepted. {panel.shape[0]} names x {panel.shape[1]} bars")
dates = [str(d) for d in panel.dates]
print(f"       span {dates[0]} -> {dates[-1]}")

cut = next((i for i, d in enumerate(dates) if d >= "2020-01-01"), len(dates))
live = panel.live
print(f"[SPLIT] D382's boundary 2020-01-01 is index {cut} of {len(dates)}  "
      f"({100 * cut / len(dates):.1f}% mined / {100 * (1 - cut / len(dates)):.1f}% reserved)")
print(f"[BREADTH] live names per bar -- mining median {np.median(live[:, :cut].sum(axis=0)):.0f}, "
      f"min {live[:, :cut].sum(axis=0).min()}, at boundary {live[:, cut - 1].sum()}")
print(f"          reserved median {np.median(live[:, cut:].sum(axis=0)):.0f}")

r = panel.log_returns[:, :cut]
fin = np.isfinite(r) & live[:, :cut]
print(f"[SANITY] mining log-returns: n {int(fin.sum()):,}  max |r| {np.abs(r[fin]).max():.4f} "
      f"(= x{np.exp(np.abs(r[fin]).max()):.2f} in one session)")
