"""Add CME-VERIFIED specs for SIL, MNG and MHG to data/futures_contract_specs.json.

Read 2026-09-13 from CME's own contract-specification service,
    https://www.cmegroup.com/CmeWS/mvc/ContractSpecs/List/productId/{product_id}
same route and same session-in-a-browser method the file's `_provenance` records for every existing
entry: WebFetch to cmegroup.com returns ECONNRESET on the XHR endpoint, the contractSpecs.html page
and the rulebook PDF alike, and the request succeeds when issued same-origin from inside the page.
Product ids came from the ProductSlate service in the same session (SIL 6955, MNG 10577, MHG 10142).

`contract_unit` and `min_tick` are CME's wording verbatim. usd_per_point and tick_points are parsed
from them, and the file's own invariant -- usd_per_point * tick_points == tick_usd -- is asserted
here for the new entries AND re-asserted for every pre-existing one.

CROSS-CHECK, not assumed: each tick_points equals the smallest positive price increment actually
printed by that root in the archive (working/stage0_micro_liquidity.py): SIL 0.005, MNG 0.001,
MHG 0.0005.

    python working/add_micro_specs.py [--write]
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
P = REPO / "data" / "futures_contract_specs.json"

NEW = {
    "SIL": {
        "product_id": 6955,
        "name": "Micro Silver Futures",
        "contract_unit": "1,000 troy ounces",
        "usd_per_point": 1000.0,
        "tick_points": 0.005,
        "tick_usd": 5.0,
        "min_tick": "0.005 per troy ounce = $5.00",
        "min_tick_other": "Settlement: 0.001 per troy ounce = $1.00; CALENDAR SPREAD: 0.001 per troy ounce = $1.00",
        "price_quotation": "U.S. dollars and cents per troy ounce",
        "settlement": "Deliverable",
        "termination": "Trading terminates on the third last business day of the contract month.",
        "listed": "Monthly contracts listed for 3 consecutive months and any Jan, Mar, May, July, Sep and Dec within the nearest 12 months.",
        "rulebook": "COMEX 121",
        "parent": "SI",
        "size_ratio_to_parent": 0.2,
    },
    "MNG": {
        "product_id": 10577,
        "name": "Micro Henry Hub Natural Gas Futures",
        "contract_unit": "1,000 MMBtu",
        "usd_per_point": 1000.0,
        "tick_points": 0.001,
        "tick_usd": 1.0,
        "min_tick": "0.001 per MMBtu = $1.00",
        "min_tick_other": "CME Globex intercommodity spreads: 0.00025 per MMBtu = $0.25",
        "price_quotation": "U.S. dollars and cents per MMBtu",
        "settlement": "Financially Settled",
        "termination": "Trading terminates on the 4th last business day of the month prior to the contract month.",
        "listed": "Monthly contracts listed for 24 consecutive months",
        "rulebook": "NYMEX 440",
        "parent": "NG",
        "size_ratio_to_parent": 0.1,
        "note": "PARENT IS DELIVERABLE AND THIS IS NOT. NG settles physical at Henry Hub; MNG is financially settled, so the two are not the same instrument at expiry even though the price series is.",
    },
    "MHG": {
        "product_id": 10142,
        "name": "Micro Copper Futures",
        "contract_unit": "2500 pounds",
        "usd_per_point": 2500.0,
        "tick_points": 0.0005,
        "tick_usd": 1.25,
        "min_tick": "0.0005 per pound = $1.25",
        "price_quotation": "U.S. dollars and cents per pound",
        "settlement": "Financially Settled",
        "termination": "Trading terminates at 12:00 Noon CT on the third last business day of the month prior to the contract month.",
        "listed": "Monthly contracts listed for 23 consecutive months and any Mar, May, Jul, Sep, and Dec in the nearest 63 months.",
        "rulebook": "COMEX 914",
        "parent": "HG",
        "size_ratio_to_parent": 0.1,
        "note": "PARENT IS DELIVERABLE AND THIS IS NOT. And it is the WIDEST of the three micros measured: median quoted spread 2 ticks, one-tick only 32.5% of day-session trades, p90 four ticks.",
    },
}

MEASURED_TICK_PTS = {"SIL": 0.005, "MNG": 0.001, "MHG": 0.0005}     # smallest printed increment, from the archive

PROV = ("SIL/MNG/MHG added 2026-09-13 from the same CME contract-specification service, read "
        "same-origin from inside the product page in a browser (WebFetch returns ECONNRESET to "
        "cmegroup.com on the XHR endpoint, the contractSpecs page and the rulebook PDF alike). "
        "Each tick_points was independently CROSS-CHECKED against the smallest positive price "
        "increment the root actually prints in the ohlcv-1m archive "
        "(working/stage0_micro_liquidity.py) and agrees exactly. The two energy/base-metal micros "
        "are FINANCIALLY SETTLED while their parents are DELIVERABLE; see each entry's note.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    s = json.loads(P.read_text())

    for k, v in NEW.items():
        if k in s:
            raise SystemExit(f"{k} already present -- this script only ADDS; amend in writing instead")
        got = v["usd_per_point"] * v["tick_points"]
        assert abs(got - v["tick_usd"]) < 1e-9, f"{k}: {v['usd_per_point']} * {v['tick_points']} = {got} != {v['tick_usd']}"
        assert abs(v["tick_points"] - MEASURED_TICK_PTS[k]) < 1e-12, f"{k}: spec tick != the tick the archive prints"
        par = s[v["parent"]]
        ratio = v["usd_per_point"] / par["usd_per_point"]
        assert abs(ratio - v["size_ratio_to_parent"]) < 1e-9, f"{k}: size ratio {ratio} != {v['size_ratio_to_parent']}"
        assert abs(v["tick_points"] - par["tick_points"]) < 1e-12, f"{k}: tick in POINTS differs from its parent"
        print(f"  {k:<4} {v['contract_unit']:<20} tick {v['tick_points']:<8} = ${v['tick_usd']:<6} "
              f"= {v['size_ratio_to_parent']:.2f} x {v['parent']}  [invariant ok, archive tick ok]")

    n_ok = 0
    for k, v in s.items():
        if isinstance(v, dict) and "tick_usd" in v:
            assert abs(v["usd_per_point"] * v["tick_points"] - v["tick_usd"]) < 1e-9, f"pre-existing {k} violates the invariant"
            n_ok += 1
    print(f"  re-asserted the invariant on {n_ok} pre-existing entries")

    if not a.write:
        print("\ndry run; pass --write to add them")
        return
    s.update(NEW)
    s["_provenance"]["micros_added_2026_09_13"] = PROV
    P.write_text(json.dumps(s, indent=1))
    print(f"\nwrote {P.relative_to(REPO)}: {len(NEW)} entries added, {len(s)-1} products total")


if __name__ == "__main__":
    main()
