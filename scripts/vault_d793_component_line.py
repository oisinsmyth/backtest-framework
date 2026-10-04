"""D793's in-sample component line (for docs/COMPONENTS_PROP.md): D791's walk-forward passive book, 2018-2023.

    python scripts/vault_d793_component_line.py        # SYSTEM interpreter (D777's bar loader)

Net Sharpe and Sortino annualised by the book's own trades a year, hit rate, skew, gross beside net, and the daily
correlation with D775's MNQ book and D777's MNQ post-close book (as D780 and D786 computed them; the other ledger
lines' daily P&L is not rebuilt here). In-sample only. Writes data/vault_d793_component_line.json.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import vault_d793_gold_china_open_model as V  # noqa: E402

OUT = REPO / "data" / "vault_d793_component_line.json"


def main() -> int:
    import stage0_d777_post_close_fade as P7
    ref = V.load_cache()
    with open(V.REHEARSAL, encoding="utf-8") as fh:
        cost = float(json.load(fh)["cost_passive"])
    wf = V.walk_forward_numpy(ref)
    yr = ref["year"].to_numpy()
    k = wf["take"] & np.isin(yr, V.TEST_YEARS) & ref["filled"].to_numpy(bool)
    days = ref["day"].to_numpy()[k]
    gross = ref["gross_p"].to_numpy(float)[k]
    net = gross - cost
    span = (pd.Timestamp(days[-1]) - pd.Timestamp(days[0])).days / 365.25
    tpy = len(net) / span
    down = math.sqrt(float(np.mean(np.minimum(net, 0) ** 2)))
    out = {"book": "D791 walk-forward passive top third, 2018-2023 (out-of-sample in the model's fit)",
           "n": int(len(net)), "trades_per_year": tpy, "mean_gross": float(gross.mean()), "mean_net": float(net.mean()),
           "net_sharpe_ann": float(net.mean() / net.std(ddof=1) * math.sqrt(tpy)),
           "net_sortino_ann": float(net.mean() / down * math.sqrt(tpy)),
           "gross_sharpe_ann": float(gross.mean() / gross.std(ddof=1) * math.sqrt(tpy)),
           "hit_rate": float((net > 0).mean()), "skew": float(pd.Series(net).skew()),
           "max_drawdown": float((np.maximum.accumulate(np.cumsum(net)) - np.cumsum(net)).max())}
    b = P7.load_bars()
    d775 = P7.d775_daily(b)
    _, d777 = P7.daily_book(P7.panel(b, "NQ"), 4.07)
    d777 = d777.groupby(level=0).sum()
    daily = pd.Series(net, index=days)
    out["daily_rho"] = {nm: round(float(pd.concat([daily, o], axis=1).fillna(0.0).corr().iloc[0, 1]), 3)
                        for nm, o in (("d775_cpi_nfp_fade", d775), ("d777_mnq_post_close", d777))}
    out["not_computed"] = "NQ F2 (#5), D737's twin (#6) and base L4 (#8): their daily P&L is not rebuilt here"
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
