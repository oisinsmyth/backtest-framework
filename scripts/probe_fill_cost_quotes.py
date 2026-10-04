"""Price (never buy) the quote history at D776's and L4's own fill timestamps, in-sample only (the principal,
2026-10-04: "Start the fill-cost measurement").

Both frozen lines charge a fixed micro fee plus one tick. Neither measured the spread at its own fills
(D775/D778), and D776 enters four minutes after an 08:30 CPI/jobs-report print. The quote schemas older than 12
months are reachable only while the Standard plan runs (docs/databento_api.md: plans gate schema depth), and it lapses
about 2026-10-11. This script calls ONLY `metadata.get_cost` (a free endpoint) and writes the quote to
data/fill_cost_probe.json. Buying needs the principal's word and a separate fetcher.

The windows (ET), on the lines' in-sample TRADE days only (nothing on or after 2024-01-01):
- D776 (CPI/EMPSIT 08:30 release days with a trade, D775's 186): entry 08:33 -> 08:36, exit 10:58 -> 11:02.
- L4 (D778's base book, 280 trades): entry 18:03 -> 18:07 on the evening the exit session's Globex day opens,
  exit 09:58 -> 10:02 on the exit session.
The symbols: the micros MNQ / M2K (listed 2019-05-06) and the full-size NQ / RTY (the whole in-sample) as the
reference. The schemas: tbbo (the quote at each trade), bbo-1s (top of book each second), mbp-1 (every top-of-book
update). Each (symbol, schema, leg) is priced on a seeded sample of windows and scaled to its full count.

    python scripts/probe_fill_cost_quotes.py --cost
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
OUT = REPO / "data" / "fill_cost_probe.json"
DATASET = "GLBX.MDP3"
NY = ZoneInfo("America/New_York")
SEAL = "2024-01-01"
MICRO_FROM = "2019-05-06"
SCHEMAS = ("tbbo", "bbo-1s", "mbp-1")
SAMPLE, SEED = 25, 2026


def api_key() -> str:
    import fetch_futures_1m as F
    return F.api_key()


def utc(day: str, hh: int, mm: int) -> str:
    return dt.datetime.combine(dt.date.fromisoformat(day), dt.time(hh, mm), tzinfo=NY).astimezone(dt.timezone.utc).isoformat()


def d776_days() -> list[str]:
    import vault_d776_cpi_nfp_fade as Rv
    U, _ = Rv.trades(Rv.in_sample_bars(), Rv.S.release_days())
    R = U[U["is_rel"]]
    days = sorted(str(d)[:10] for d in R.index)
    assert len(days) == 186, len(days)
    return days


def l4_days() -> list[tuple[str, str]]:
    """(entry evening's calendar date, exit session) for D778's 280 base-book trades."""
    import vault_d781_l4_auction_fade as Lv
    D = Lv.frame(Lv.in_sample_bars())
    B = D[D["cvalid"] & D["base"] & (D["s1"] <= "2023-12-31")]
    assert len(B) == 280, len(B)
    out = []
    for s1 in sorted(str(x)[:10] for x in B["s1"]):
        d = dt.date.fromisoformat(s1)
        ev = d - dt.timedelta(days=1)          # the Globex day of s1 opens 18:00 ET the calendar day before (Sunday for Monday)
        out.append((ev.isoformat(), s1))
    return out


def windows() -> dict[str, list[tuple[str, str]]]:
    r, l4 = d776_days(), l4_days()
    w = {"D776_entry": [(utc(d, 8, 33), utc(d, 8, 36)) for d in r],
         "D776_exit": [(utc(d, 10, 58), utc(d, 11, 2)) for d in r],
         "L4_entry": [(utc(e, 18, 3), utc(e, 18, 7)) for e, _ in l4],
         "L4_exit": [(utc(s, 9, 58), utc(s, 10, 2)) for _, s in l4]}
    for k, v in w.items():
        assert all(b < utc(SEAL, 0, 0) for _, b in v), f"seal: {k} reaches 2024"
    return w


def jobs(w: dict[str, list[tuple[str, str]]]) -> list[tuple[str, str, list[tuple[str, str]]]]:
    micro_from = utc(MICRO_FROM, 0, 0)
    out = []
    for leg, v in w.items():
        full, micro = ("NQ.v.0", "MNQ.v.0") if leg.startswith("D776") else ("RTY.v.0", "M2K.v.0")
        out.append((full, leg, v))
        out.append((micro, leg, [x for x in v if x[0] >= micro_from]))
    return out


def cost() -> int:
    import databento as db
    c = db.Historical(api_key())
    rng = np.random.default_rng(SEED)
    rows = []
    for sym, leg, v in jobs(windows()):
        if not v:
            continue
        idx = sorted(rng.choice(len(v), size=min(SAMPLE, len(v)), replace=False))
        for sch in SCHEMAS:
            usd, empty = [], 0
            for i in idx:
                s, e = v[i]
                try:
                    usd.append(float(c.metadata.get_cost(dataset=DATASET, symbols=[sym], schema=sch, start=s, end=e,
                                                         stype_in="continuous")))
                except Exception as ex:  # noqa: BLE001
                    if "symbology" in str(ex) or "no data" in str(ex).lower():
                        empty += 1
                        continue
                    raise
            mean = float(np.mean(usd)) if usd else 0.0
            rows.append({"symbol": sym, "leg": leg, "schema": sch, "windows": len(v), "sampled": len(idx), "empty": empty,
                         "mean_usd_per_window": mean, "projected_usd": mean * len(v)})
            print(f"  {sym:8s} {leg:11s} {sch:7s} {len(v):4d} windows  ${mean:.4f}/window  -> ${mean * len(v):8.2f}", flush=True)
    df = pd.DataFrame(rows)
    tot = {f"{sch}": float(df.loc[df["schema"] == sch, "projected_usd"].sum()) for sch in SCHEMAS}
    micro = {f"{sch}": float(df.loc[(df["schema"] == sch) & df["symbol"].isin(["MNQ.v.0", "M2K.v.0"]), "projected_usd"].sum())
             for sch in SCHEMAS}
    doc = {"what": "a QUOTE only (metadata.get_cost, free); nothing was bought", "dataset": DATASET,
           "quoted_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "sample_per_cell": SAMPLE, "seed": SEED, "rows": rows,
           "projected_total_usd_by_schema": tot, "projected_micro_only_usd_by_schema": micro}
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print("TOTAL (all four symbols):", {k: round(v, 2) for k, v in tot.items()})
    print("MICROS ONLY (MNQ, M2K):  ", {k: round(v, 2) for k, v in micro.items()})
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cost", action="store_true", required=True)
    ap.parse_args()
    return cost()


if __name__ == "__main__":
    sys.exit(main())
