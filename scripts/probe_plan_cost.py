"""What the chosen plan ACTUALLY costs and weighs, from Databento. FREE calls only.

    uv run python scripts/probe_plan_cost.py [--json]

This replaces every estimate in data/subscription_entitlement.json with vendor
figures. `metadata.get_billable_size` and `metadata.get_cost` are free metadata
endpoints; nothing here submits a job or spends anything.

WHY IT EXISTS: --verify FAILED a load-bearing assumption on 2026-09-11.
`list_unit_prices(GLBX.MDP3)` returns a PER-SCHEMA table, not one rate:

    ohlcv-1d 190.0   ohlcv-1h 190.0   ohlcv-1m 70.0   ohlcv-1s 70.0
    tbbo 28.0        trades 28.0      bbo-1m 18.0     bbo-1s 18.0
    status 4.0       definition 1.7   mbo 1.8         mbp-1 1.8
    statistics 1.0   mbp-10 0.5

The programme's derived $28.00/GiB was the TRADES rate and it was applied to
everything. Pricing runs INVERSE to density: a 1-minute bar costs 39x more per byte
than a raw order-book message, because the aggregate is the processed product.

TWO CONSEQUENCES, BOTH RECORDED BEFORE THE NUMBERS COME BACK:
  1. every usage-based figure this programme has published is wrong, in both
     directions -- ohlcv-1m was understated 2.5x, mbo overstated 15.6x
  2. "derive the cheap schema from the expensive one" now runs the OTHER WAY.
     Databento's derivation matrix says OHLCV derives from MBO. At 1.8 vs 70.0
     per GB, buying MBO and aggregating locally may be cheaper than buying bars,
     if the byte ratio is under 39x.

THE SUBSCRIPTION IS THE REAL QUESTION. CME Standard includes 16+ yr of L0, 12 mo of
L1 and 1 mo of L2/L3. If the entitlement is applied at quote time, get_cost returns
~0 for everything below. IF IT DOES NOT, this plan is a five-figure purchase and
nothing may be submitted. That is the single thing this probe exists to settle.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "plan_cost_probe.json"
KEY_FILE = Path.home() / ".config" / "databento" / "key"
DATASET = "GLBX.MDP3"

L0_START = "2010-06-06"
L1_MONTHS = 12

# THE FREE L2/L3 BOUNDARY IS REAL AND IT WAS MEASURED, ONE WEEKDAY AT A TIME.
# Standard includes "1 month" of L2/L3. Probed against ES MBO on 2026-09-11:
#   32 days back (2026-08-10)  0.48 GiB  FREE
#   35 days back (2026-08-07)  0.67 GiB  CHARGED $1.21
# So the free window is the last ~34 days and A REQUEST THAT STRADDLES THE BOUNDARY
# IS BILLED. L3_DAYS is deliberately inside it with margin.
L3_DAYS = 32

# AND THE DEEP SCHEMAS END EARLIER THAN THE DATASET DOES. get_dataset_range returns a
# PER-SCHEMA map: mbo and mbp-10 end 2026-09-10T16:34, everything else 2026-09-11.
# Requesting up to the dataset end 422s with dataset_unavailable_range -- which is what
# the first run of this probe hit. mbo also only starts 2017-05-21, not 2010-06-06.
L3_END_BACKOFF_DAYS = 1

ROOTS_41 = ["ES", "NQ", "RTY", "YM", "MES", "MNQ", "M2K", "MYM",
            "CL", "NG", "GC", "SI", "HG", "ZN", "ZB", "ZF",
            "SR3", "ZT", "UB", "TN", "RB", "HO", "BZ", "PL", "PA",
            "6E", "6J", "6B", "6A", "6C", "6S",
            "ZC", "ZS", "ZW", "ZL", "ZM", "LE", "HE", "NKD", "BTC", "MBT"]
ROOTS_8 = ["ES", "NQ", "RTY", "YM", "CL", "GC", "ZN", "ZB"]


def api_key() -> str:
    k = os.environ.get("DATABENTO_API_KEY") or (
        KEY_FILE.read_text(encoding="utf-8").strip() if KEY_FILE.exists() else "")
    if not k:
        raise SystemExit(f"No key. Set DATABENTO_API_KEY or write {KEY_FILE}.")
    return k


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    import databento as db
    import pandas as pd
    c = db.Historical(api_key())

    rng = c.metadata.get_dataset_range(DATASET)
    end = str(rng["end"])[:10]
    per_schema = {k: {"start": str(v["start"])[:10], "end": str(v["end"])[:19]}
                  for k, v in rng.get("schema", {}).items()}
    l1_start = (pd.Timestamp(end) - pd.DateOffset(months=L1_MONTHS)).date().isoformat()
    l3_start = (pd.Timestamp(end) - pd.Timedelta(days=L3_DAYS)).date().isoformat()
    l3_end = (pd.Timestamp(end) - pd.Timedelta(days=L3_END_BACKOFF_DAYS)).date().isoformat()
    print(f"dataset range {str(rng['start'])[:10]} .. {end}")
    if per_schema:
        print("per-schema ends: " + "  ".join(
            f"{k}={v['end'][:10]}" for k, v in sorted(per_schema.items())
            if v["end"][:10] != end))
    print(f"L0 {L0_START}..{end}   L1 {l1_start}..{end}   L3 {l3_start}..{l3_end}\n")

    prices = {e["mode"]: e["unit_prices"] for e in c.metadata.list_unit_prices(DATASET)}
    hist = prices.get("historical", {})

    # (label, schema, symbols, stype_in, start, end)
    P41 = [f"{r}.FUT" for r in ROOTS_41]
    P8 = [f"{r}.FUT" for r in ROOTS_8]
    # bbo-1m IS SCOPED TO 41 ROOTS AND THAT IS NOT A PREFERENCE.
    # At ALL_SYMBOLS it measured 3,190.6 GiB over 12 months -- 12.5 GiB PER DAY -- because
    # it snapshots every instrument every minute whether or not it trades, and the dataset
    # is mostly option strikes. Scoped to 41 roots it is 30.2 GiB, a 105x reduction, and
    # it keeps every symbol the prop track could trade. The estimate in
    # subscription_entitlement.json had this at 17.7 GiB: wrong by 180x, because it
    # modelled a TIME-sampled schema as if it scaled with trades.
    PLAN = [
        ("ohlcv-1m  ALL_SYMBOLS  16yr", "ohlcv-1m", "ALL_SYMBOLS", "raw_symbol", L0_START, end),
        ("tbbo      ALL_SYMBOLS  12mo", "tbbo", "ALL_SYMBOLS", "raw_symbol", l1_start, end),
        ("bbo-1m    41 roots     12mo", "bbo-1m", P41, "parent", l1_start, end),
        ("mbo       top 8 roots  free", "mbo", P8, "parent", l3_start, l3_end),
        ("definition 41 roots    16yr", "definition", P41, "parent", L0_START, end),
        ("statistics 41 roots    16yr", "statistics", P41, "parent", L0_START, end),
        ("status     41 roots    16yr", "status", P41, "parent", L0_START, end),
    ]

    GIB = 1024 ** 3
    rows, tot_b, tot_usd, tot_list = [], 0, 0.0, 0.0
    print(f"  {'item':30}{'BILLABLE GiB':>14}{'get_cost $':>12}{'list-rate $':>13}  schema $/GB")
    for label, schema, syms, stype, s, e in PLAN:
        try:
            size = c.metadata.get_billable_size(DATASET, start=s, end=e, symbols=syms,
                                                schema=schema, stype_in=stype)
            time.sleep(0.4)
            cost = c.metadata.get_cost(DATASET, start=s, end=e, symbols=syms,
                                       schema=schema, stype_in=stype)
            time.sleep(0.4)
            gib = size / GIB
            rate = float(hist.get(schema, float("nan")))
            listed = gib * rate                     # what the published table implies
            rows.append({"item": label, "schema": schema, "stype_in": stype,
                         "start": s, "end": e, "billable_bytes": int(size),
                         "billable_gib": gib, "get_cost_usd": float(cost),
                         "list_rate_usd_per_gb": rate, "list_rate_implied_usd": listed})
            tot_b += size; tot_usd += float(cost); tot_list += listed
            print(f"  {label:30}{gib:14,.1f}{float(cost):12,.2f}{listed:13,.0f}  {rate}")
        except Exception as exc:
            rows.append({"item": label, "schema": schema, "error": f"{type(exc).__name__}: {exc}"[:300]})
            print(f"  {label:30}{'ERROR':>14}  {type(exc).__name__}: {str(exc)[:70]}")
    print(f"  {'TOTAL':30}{tot_b/GIB:14,.1f}{tot_usd:12,.2f}{tot_list:13,.0f}")

    covered = tot_usd < 1.0
    print(f"\n  SUBSCRIPTION VERDICT: get_cost totals ${tot_usd:,.2f} against a published-rate")
    print(f"  value of ${tot_list:,.0f}.")
    print("  -> the CME Standard entitlement IS being applied at quote time; the plan is"
          "\n     covered by the $199 and nothing further is owed."
          if covered else
          "  -> NOT COVERED. The entitlement is not zeroing these quotes. DO NOT SUBMIT."
          "\n     Re-scope the plan or confirm the plan status in the Databento portal.")

    if a.json:
        OUT.write_text(json.dumps({
            "probed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "purpose": "vendor figures for the chosen plan, replacing the estimates in subscription_entitlement.json. Free metadata calls only; nothing submitted.",
            "dataset": DATASET, "dataset_range": {"start": str(rng["start"])[:10], "end": end},
            "dataset_range_per_schema": per_schema,
            "windows": {"L0": [L0_START, end], "L1": [l1_start, end], "L3": [l3_start, l3_end]},
            "measured_free_l3_boundary": {
                "free_at_days_back": 32, "charged_at_days_back": 35,
                "charge_observed_usd_per_es_day": 1.21,
                "method": "ES.FUT mbo, one weekday at a time, get_cost on each"},
            "est_disk_gib_at_zstd_2_6": tot_b / GIB / 2.6,
            "est_download_hours_at_3_04_MBps": tot_b / 2.6 / 3.04e6 / 3600,
            "unit_prices_historical": hist,
            "correction": "the programme's derived $28.00/GiB is the TRADES rate. Rates are per-schema and span 0.5 (mbp-10) to 190.0 (ohlcv-1d). ohlcv-1m is 70.0.",
            "items": rows,
            "total_billable_gib": tot_b / GIB,
            "total_get_cost_usd": tot_usd,
            "total_at_list_rates_usd": tot_list,
            "subscription_covers_plan": covered,
        }, indent=1) + "\n", encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0 if covered else 2


if __name__ == "__main__":
    raise SystemExit(main())
