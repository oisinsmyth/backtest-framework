"""D664 PROBE -- is the spark spread testable on CME? Does Databento's GLBX.MDP3 carry CME's US power futures?

    python scripts/probe_d664_spark_power.py      # -> data/d664_spark_probe.json

Metadata only: `symbology.resolve` is free and reads no market data. The Databento key is read by
`quote_prelapse_sweep.api_key()` and never printed. NG and CL are the controls: a parent that exists resolves to its
instruments; one that does not raises "Could not resolve smart symbols", recorded as absent.

The power codes are CME's own, from its product slate (Energy > Electricity, 121 futures, read in a browser on
2026-09-28 for trade date 2026-09-25; recorded in the JSON's `cme_product_slate` block, not re-read here).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

OUT = REPO / "data" / "d664_spark_probe.json"
CONTROLS = ["NG", "CL"]
POWER = {"WRP": "PJM Western Hub Real-Time Peak Monthly 1 MW", "WRO": "PJM Western Hub Real-Time Off-Peak Monthly 1 MW",
         "WDP": "PJM Western Hub Day-Ahead Peak Monthly 1 MW", "WDO": "PJM Western Hub Day-Ahead Off-Peak Monthly 1 MW",
         "5ZP": "PJM Western Hub Real-Time Peak Monthly 50 MW", "5ZO": "PJM Western Hub Real-Time Off-Peak Monthly 50 MW",
         "SDP": "PJM Northern Illinois Hub Day-Ahead Peak Monthly 1 MW",
         "IRP": "PJM Northern Illinois Hub Real-Time Peak Monthly 1 MW",
         "NRK": "ERCOT North 345KV Real-Time Peak Monthly 1 MW", "EN6": "ERCOT North 345KV Real-Time 2x16 Monthly 1 MW",
         "DP8": "PJM Western Hub Day-Ahead Peak Daily 800 MWh", "RP8": "PJM Western Hub Real-Time Peak Daily 800 MWh"}
WINDOWS = [("2012-06-01", "2012-06-08"), ("2016-06-01", "2016-06-08"), ("2020-06-01", "2020-06-08"),
           ("2024-06-03", "2024-06-10")]
SLATE = {"source": "https://www.cmegroup.com/CmeWS/mvc/ProductSlate/V2/List?group=7&subGroup=11&cleared=Futures "
                   "(read in a browser, one request, 2026-09-28)",
         "trade_date": "2026-09-25", "report_type": "FINAL", "electricity_futures_listed": 121,
         "with_open_interest_above_zero": 0, "with_volume_above_zero": 0,
         "venues_listed": "Globex and ClearPort for every product",
         "field_check": {"NG open interest": 1794933, "CL open interest": 1854775}}


def main() -> int:
    import databento as db
    import quote_prelapse_sweep as q

    c = db.Historical(q.api_key())
    res = {}
    for p in CONTROLS + list(POWER):
        row = {}
        for a, b in WINDOWS:
            try:
                r = c.symbology.resolve(dataset="GLBX.MDP3", symbols=[f"{p}.FUT"], stype_in="parent",
                                        stype_out="instrument_id", start_date=a, end_date=b)
                row[a[:4]] = len({x["s"] for v in r.get("result", {}).values() for x in v})
            except Exception as e:
                row[a[:4]] = "absent" if "Could not resolve" in str(e) else f"error: {type(e).__name__}"
        res[p] = row
        print(p, row, flush=True)
    controls_ok = all(isinstance(v, int) and v > 0 for p in CONTROLS for v in res[p].values())
    power_absent = all(v == "absent" for p in POWER for v in res[p].values())
    out = {"decision_record": "docs/decisions/D664-PROBE-the-spark-spread-is-not-on-cme.md", "reads_no_market_data": True,
           "dataset": "GLBX.MDP3", "windows": WINDOWS, "power_codes": POWER, "resolution": res,
           "controls_resolve": controls_ok, "every_power_code_absent_in_every_window": power_absent,
           "cme_product_slate": SLATE}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print("controls resolve:", controls_ok, "| every power code absent:", power_absent)
    return 0 if controls_ok else 1


if __name__ == "__main__":
    sys.exit(main())
