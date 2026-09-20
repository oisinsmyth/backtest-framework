"""Quote, never download: the ES option family's `statistics` (open interest, settlements) and `definition` (strike, expiry)
history from Databento GLBX.MDP3, for the gamma-conditioned close (D581). Metadata calls only -- no bytes move.

    python scripts/quote_es_options_pull.py            # SYSTEM interpreter (databento); writes data/es_options_pull_quote.json

The key is the principal's (env DATABENTO_API_KEY or ~/.config/databento/key); it is never printed. The archive on disk
holds every ES-family option's one-minute bars already (864,813 option instruments in the 2025 file alone); what it lacks
is open interest, which lives in `statistics`, and the strike/expiry table for the option ids, which lives in `definition`.
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "es_options_pull_quote.json"
KEY_FILE = Path.home() / ".config" / "databento" / "key"
DATASET = "GLBX.MDP3"; SYMBOLS = ["ES.OPT"]; STYPE_IN = "parent"
START = "2016-01-01"; END = "2026-09-11"
SCHEMAS = ("statistics", "definition")


def api_key():
    k = os.environ.get("DATABENTO_API_KEY")
    if k:
        return k.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"no key: set DATABENTO_API_KEY or write {KEY_FILE}")


def main():
    import databento as db
    c = db.Historical(api_key()); t0 = time.time(); out = {"dataset": DATASET, "symbols": SYMBOLS, "stype_in": STYPE_IN, "start": START, "end": END, "quoted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "schemas": {}}
    for schema in SCHEMAS:
        size = c.metadata.get_billable_size(DATASET, start=START, end=END, symbols=SYMBOLS, schema=schema, stype_in=STYPE_IN)
        usd = c.metadata.get_cost(DATASET, start=START, end=END, symbols=SYMBOLS, schema=schema, stype_in=STYPE_IN)
        out["schemas"][schema] = {"billable_bytes": int(size), "billable_gb": round(size / 1e9, 2), "usd": float(usd)}
        print(f"  {schema:<11} {size/1e9:8.2f} GB  USD {usd:,.2f}")
    # the same two schemas for the last twelve months only, in case the full span is a bill
    out["last_12_months"] = {}
    for schema in SCHEMAS:
        size = c.metadata.get_billable_size(DATASET, start="2025-09-11", end=END, symbols=SYMBOLS, schema=schema, stype_in=STYPE_IN)
        usd = c.metadata.get_cost(DATASET, start="2025-09-11", end=END, symbols=SYMBOLS, schema=schema, stype_in=STYPE_IN)
        out["last_12_months"][schema] = {"billable_gb": round(size / 1e9, 2), "usd": float(usd)}
        print(f"  {schema:<11} last 12 months {size/1e9:8.2f} GB  USD {usd:,.2f}")
    out["total_usd"] = sum(v["usd"] for v in out["schemas"].values()); out["total_gb"] = round(sum(v["billable_bytes"] for v in out["schemas"].values()) / 1e9, 2); out["timing_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8"); print(f"  total {out['total_gb']} GB, USD {out['total_usd']:,.2f}; wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    sys.exit(main())
