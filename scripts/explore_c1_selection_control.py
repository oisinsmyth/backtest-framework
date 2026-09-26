"""POST HOC, after D632's one run: is Stage C1's higher mean per trade the creation forecast, or only a stricter
filter? Nothing here changes the verdict.

D632: C1 traded 404 out-of-sample days at $119 a trade (t 4.47), against Stage A's 1,010 at $68 (t 5.08), with
the same direction on every common day. C1's gate passes fewer days because the forecast creations net against P1
and shrink |μ|. A stricter filter on Stage A alone might do the same: D630's H3 found $137 a trade in Stage A's top
|I| quintile.

The control: on the same out-of-sample days, Stage A's traded days restricted to its own top 404 by |I| at τ*_A
(the same count as C1). Also reported: C1's 404 days' Stage A |I| rank, and the overlap of the two 404-day sets.
Output: `data/ledger_stage_c1_posthoc.json`.

    uv run python -W error::RuntimeWarning scripts/explore_c1_selection_control.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import run_stage_c1_ng as C  # noqa: E402

OUT = REPO / "data" / "ledger_stage_c1_posthoc.json"


def main() -> int:
    b = C.build(read_signed=True)
    d = b["d"]
    fc = C.forecasts(list(d["day"]), b["ret"], b["flows"])
    sc = C.score(d, lambda _t: fc)
    n = len(d)
    ta, tc, g_a, g_c = sc["ta"], sc["tc"], sc["g_a"], sc["g_c"]
    idx_a = d["tau_star_a"].map({t: i for i, t in enumerate(C.T0)}).to_numpy()
    absI = np.column_stack([np.abs(d[f"I_{C.k_of(t)}"].to_numpy(float)) for t in C.T0])[np.arange(n), idx_a]
    k = int(tc.sum())
    cand = np.flatnonzero(ta)
    top = cand[np.argsort(absI[cand])[::-1][:k]]
    m_top = np.zeros(n, dtype=bool)
    m_top[top] = True
    out = {"note": "POST HOC, after D632's run; the verdict is unchanged",
           "c1": C.R2.mean_t(g_c[tc]), "stage_a_all": C.R2.mean_t(g_a[ta]),
           "stage_a_top_by_absI_same_count": C.R2.mean_t(g_a[m_top]),
           "overlap_c1_with_top_absI_set": float((m_top & tc).sum() / k),
           "c1_days_median_absI_percentile_in_stage_a": float(np.median(
               [np.mean(absI[cand] <= absI[i]) for i in np.flatnonzero(tc & ta)]))}
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
