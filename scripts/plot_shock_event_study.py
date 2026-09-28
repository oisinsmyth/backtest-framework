"""D642's event-study figure: the mean curve c_k (k = 0..60 minutes after t0) per instrument and class, with its 95%
day-block-bootstrap band, read from `data/shock/phase3_signal.json` (nothing is recomputed).

    python scripts/plot_shock_event_study.py      # -> data/shock/phase3_event_study.svg (deterministic)

INFO and LIQ are in their TRADE direction (INFO with the shock, LIQ against it), so a curve above zero is a move the
class's trade earns. ALL (every z = 4 shock) and NONE are in the SHOCK direction. The dotted line is the cost at one
micro in bp (s.5.1), and the grey rule marks k = 5, the latency H2 asks about.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("svg")
import matplotlib.pyplot as plt  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "shock" / "phase3_signal.json"
OUT = REPO / "data" / "shock" / "phase3_event_study.svg"
STYLE = {"INFO": ("#1f6fb2", "INFO (trade dir.)"), "LIQ": ("#c0392b", "LIQ (trade dir.)"),
         "ALL": ("#555555", "all shocks (shock dir.)"), "NONE": ("#999999", "NONE (shock dir.)")}


def main() -> int:
    doc = json.loads(SRC.read_text(encoding="utf-8"))
    plt.rcParams.update({"svg.hashsalt": "d642", "font.size": 9, "svg.fonttype": "none"})
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True)
    for ax, r in zip(axes.flat, ("NQ", "ES", "CL", "GC")):
        inst = doc["instruments"][r]
        for c in ("ALL", "INFO", "LIQ"):
            cv = inst["curves"][c]
            if "mean_bp" not in cv:
                continue
            k = range(len(cv["mean_bp"]))
            col, lab = STYLE[c]
            ax.plot(k, cv["mean_bp"], color=col, lw=1.4, label=f"{lab}, n={cv['n']:,}")
            ax.fill_between(k, cv["ci95_lo"], cv["ci95_hi"], color=col, alpha=0.15, lw=0)
        cost = inst["groups"]["INFO"]["mean_cost_bp"]
        ax.axhline(0, color="black", lw=0.6)
        ax.axhline(cost, color="black", lw=0.8, ls=":", label=f"cost, one micro ({cost:.1f} bp)")
        ax.axvline(5, color="#bbbbbb", lw=0.8)
        h1 = inst["H1"]
        ax.set_title(f"{r}: H1 {h1['verdict'].split(' (')[0]} (Δ {h1['delta_bp']:+.1f} bp, t {h1['t']:.2f})", fontsize=10)
        ax.legend(fontsize=7, loc="best", frameon=False)
        ax.set_ylabel("c_k, bp from t0")
    for ax in axes[1]:
        ax.set_xlabel("minutes after the shock bar's close (k)")
    fig.suptitle("D642 event study: mean curve after a z = 4 shock, 2016-01 → 2025-02, 95% day-block bands", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT, format="svg", metadata={"Date": None})
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
