"""D675 §9 -- the holdout power of every clock cell, from D675's own in-sample numbers (no new data read).

    uv run python scripts/d675_power.py

For each (root, signal, target clock) cell of data/d675_macd_kernel_decomposition.json:
  z_in = (value - null p50) / sd_null,   sd_null = (p95 - p50) / 1.645   (normal approximation of the
                                                                          exact session-rotation null)
  expected holdout t IF THE EFFECT IS ENTIRELY REAL = |z_in| * sqrt(months_slice / months_in_sample)
  power = Phi(t - 1.645), one-sided at 5%; also at half the effect (selection inflates the in-sample one).
Slices (from the D675 §9 seal inventory): A = 2024-01 -> 2025-02 (14 months), the vault (18.5 months, joint run
only), and both.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import NormalDist

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "d675_macd_kernel_decomposition.json"
OUT = REPO / "data" / "d675_power.json"
ROOTS = ("GC", "CL", "ZN", "ZB", "6E", "ES", "YM")    # NQ has no unread slice (D503)
SIGNALS = ("S", "CONT", "REV")
CLOCKS = ("ASIA", "EUROPE", "US_OPEN", "US_MID", "US_CLOSE")
MONTHS_IN = 96.0
SLICES = {"A_2024_01_to_2025_02": 14.0, "vault": 18.5, "A_plus_vault": 32.5}
T_BAR = 1.5                                            # the power rule's floor on the expected t


def main() -> int:
    nd = NormalDist()
    d = json.loads(SRC.read_text(encoding="utf-8"))["decomposition"]
    cells = []
    for r in ROOTS:
        for s in SIGNALS:
            for g in CLOCKS:
                c = d[r]["cells"][s][f"tgt:{g}"]
                sd = (c["p95"] - c["p50"]) / 1.645
                z = (c["value"] - c["p50"]) / sd
                row = {"root": r, "signal": s, "clock": g, "value": c["value"], "pct": c["pct"], "z_in": z}
                for k, m in SLICES.items():
                    t = abs(z) * math.sqrt(m / MONTHS_IN)
                    row[k] = {"t_full": t, "t_half": t / 2, "power_full": nd.cdf(t - 1.645),
                              "power_half": nd.cdf(t / 2 - 1.645)}
                cells.append(row)
    n_ext = sum(abs(x["z_in"]) >= 1.645 for x in cells)
    best = max(cells, key=lambda x: abs(x["z_in"]))
    clears = [x for x in cells if x["A_2024_01_to_2025_02"]["t_full"] >= T_BAR]
    out = {"source": str(SRC.relative_to(REPO)), "months_in_sample": MONTHS_IN, "slices_months": SLICES,
           "n_cells": len(cells), "n_abs_z_ge_1645": n_ext, "expected_by_chance_two_sided_10pc": 0.10 * len(cells),
           "best_cell": best, "cells_with_t_full_ge_1_5_on_slice_A": len(clears), "cells": cells}
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"{len(cells)} cells; |z| >= 1.645: {n_ext} (chance {0.10 * len(cells):.1f}); best "
          f"{best['root']} {best['signal']} {best['clock']} z {best['z_in']:+.2f} -> slice A t "
          f"{best['A_2024_01_to_2025_02']['t_full']:.2f} full / {best['A_2024_01_to_2025_02']['t_half']:.2f} half; "
          f"cells with t >= {T_BAR} on slice A: {len(clears)}")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
