"""D619 — what a CL/NG options and TAS pull from Databento GLBX.MDP3 would cost. **QUOTE ONLY.**

    python scripts/quote_energy_options_pull.py      # SYSTEM interpreter (databento 0.86)

`metadata.get_billable_size` and `metadata.get_cost` and nothing else. **`batch.submit_job` is
not called, is not imported and does not appear in this file.** The principal's decision of
2026-09-22: no batch job is submitted and nothing is downloaded from Databento in this round,
**even at a $0.00 quote**. Write the quote and stop.

SHAPED ON `scripts/quote_es_options_pull.py` (D581), and inheriting its lesson: a parent symbol
is whatever the venue hangs under that root, so the symbol list here is not guessed. It is the
set `scripts/probe_energy_options_parents.py` RESOLVED, read out of
`data/energy_options_parents_probe.json` at run time — fifteen option parents (`LO`, `LO1`-`LO5`
for CL; `ON`, `ON1`-`ON5` and `LN1`-`LN3` for NG), with `CL.OPT`, `NG.OPT`, `LN.OPT` and `WA.OPT`
excluded because the venue refuses them as symbols.

WHAT IT IS FOR. Deposit job 9 is `options_oi` — *"NG and CL options open interest by strike"* —
and unit test 50 joins it point-in-time. `statistics` is where open interest lives and
`definition` is where the strike and expiry table lives, which is why those are the two schemas
quoted. The TAS block answers deposit Q3's second half: the symbology probe settled that
`CLT.FUT` and `NGT.FUT` RESOLVE, and this says what their history would cost.

THE SUBSCRIPTION WINDOW. The CME Standard subscription's free re-fetch window runs to roughly
2026-10-11. A quote of $0.00 today is not a quote of $0.00 in November, and that is the fact the
record carries beside the number.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEY_FILE = Path.home() / ".config" / "databento" / "key"
DATASET = "GLBX.MDP3"
START, END = "2016-01-01", "2026-09-10"
LAST_12M_START = "2025-09-10"
PROBE = REPO / "data" / "energy_options_parents_probe.json"
OUT = REPO / "data" / "energy_options_pull_quote.json"

#: Open interest lives in `statistics`; the strike/expiry table for the option ids lives in
#: `definition`. Both, for the options. See the module docstring.
OPTION_SCHEMAS = ("definition", "statistics")
#: TAS: the deposit wants "TAS volume, aggressor split, premium ticks" (13A.3 line 821), which is
#: `trades`; `definition` is what names the TAS instruments and `statistics` carries their OI.
TAS_SYMBOLS = ("CLT.FUT", "NGT.FUT")
TAS_SCHEMAS = ("definition", "statistics", "trades")

SUBMITTED = False
DECISION = "No batch job submitted: the principal's decision of 2026-09-22 was quote only."


def P(*a: object) -> None:
    print(*a, flush=True)


def api_key() -> str:
    """The principal's key. Never printed, never logged, never placed in a URL."""
    k = os.environ.get("DATABENTO_API_KEY")
    if k:
        return k.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"no key: set DATABENTO_API_KEY or write {KEY_FILE}")


def resolved_parents() -> list[str]:
    """The parents the probe RESOLVED. Raises if the probe has not run — this file never guesses
    a symbol list, which is the whole of D581's lesson."""
    if not PROBE.exists():
        raise SystemExit(
            f"{PROBE} does not exist. Run scripts/probe_energy_options_parents.py first: the "
            f"symbol list here is the probe's output and is never written by hand (D581)."
        )
    probe = json.loads(PROBE.read_text(encoding="utf-8"))
    parents = list(probe["resolved_parents"])
    if not parents:
        raise SystemExit(f"{PROBE} resolved no parents; there is nothing to quote")
    return parents


def quote(client, symbols: list[str], schema: str, start: str, end: str) -> dict[str, object]:
    size = client.metadata.get_billable_size(
        DATASET, start=start, end=end, symbols=symbols, schema=schema, stype_in="parent"
    )
    usd = client.metadata.get_cost(
        DATASET, start=start, end=end, symbols=symbols, schema=schema, stype_in="parent"
    )
    row = {"billable_bytes": int(size), "billable_gb": round(size / 1e9, 2), "usd": float(usd)}
    P(f"    {schema:<11} {start}..{end}  {row['billable_gb']:>9.2f} GB  USD {row['usd']:>10,.2f}")
    return row


def main() -> int:
    import databento as db

    c = db.Historical(api_key())
    t0 = time.time()
    parents = resolved_parents()
    out: dict[str, object] = {
        "dataset": DATASET,
        "record": "D619",
        "stype_in": "parent",
        "start": START,
        "end": END,
        "quoted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "submitted": SUBMITTED,
        "decision": DECISION,
        "subscription_note": "The CME Standard subscription's free re-fetch window runs to about "
                             "2026-10-11; a USD 0.00 quote today is not a USD 0.00 quote after it.",
        "symbol_source": "data/energy_options_parents_probe.json#resolved_parents (D619 probe); "
                         "never written by hand (D581: ES.OPT was the quarterlies alone)",
        "options": {"symbols": parents, "schemas": {}, "last_12_months": {}},
        "tas": {"symbols": list(TAS_SYMBOLS), "schemas": {}, "last_12_months": {},
                "question": "deposit Q3; the symbology probe concluded CLT.FUT and NGT.FUT resolve"},
    }

    P(f"  options parents ({len(parents)}): {', '.join(parents)}")
    for schema in OPTION_SCHEMAS:
        out["options"]["schemas"][schema] = quote(c, parents, schema, START, END)  # type: ignore[index]
    for schema in OPTION_SCHEMAS:
        out["options"]["last_12_months"][schema] = quote(c, parents, schema, LAST_12M_START, END)  # type: ignore[index]

    P(f"  TAS parents ({len(TAS_SYMBOLS)}): {', '.join(TAS_SYMBOLS)}")
    for schema in TAS_SCHEMAS:
        out["tas"]["schemas"][schema] = quote(c, list(TAS_SYMBOLS), schema, START, END)  # type: ignore[index]
    for schema in TAS_SCHEMAS:
        out["tas"]["last_12_months"][schema] = quote(c, list(TAS_SYMBOLS), schema, LAST_12M_START, END)  # type: ignore[index]

    for block in ("options", "tas"):
        b = out[block]
        b["total_usd"] = sum(v["usd"] for v in b["schemas"].values())  # type: ignore[index]
        b["total_gb"] = round(sum(v["billable_bytes"] for v in b["schemas"].values()) / 1e9, 2)  # type: ignore[index]
    out["total_usd"] = out["options"]["total_usd"] + out["tas"]["total_usd"]  # type: ignore[index]
    out["total_gb"] = round(out["options"]["total_gb"] + out["tas"]["total_gb"], 2)  # type: ignore[index]
    out["timing_s"] = round(time.time() - t0, 1)

    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    P(f"  total {out['total_gb']} GB, USD {out['total_usd']:,.2f}; submitted={SUBMITTED}")
    P(f"  {DECISION}")
    P(f"  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
