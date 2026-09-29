"""Quote, never download: the data the opening-range line could run on next (after D662). Metadata calls only -- no
bytes move, nothing is billed.

    python scripts/quote_opening_opra_imbalance.py      # SYSTEM interpreter (databento); writes data/opening/opra_imbalance_quote.json

1. SPX-complex dealer gamma: OPRA.PILLAR parents SPX.OPT, SPXW.OPT, SPY.OPT -- `statistics` (open interest),
   `definition` (strike, expiry, right) and `ohlcv-1d` (a daily price, for implied vol; the alternative is the ES option
   settlement vols already on disk).
2. The NQ equivalent: NDX.OPT, NDXP.OPT, QQQ.OPT, same schemas.
3. Opening-auction imbalance: `imbalance` on XNYS.PILLAR (NYSE), XNAS.ITCH (Nasdaq) and ARCX.PILLAR (NYSE Arca, where
   SPY and QQQ auction), ALL_SYMBOLS.
Each over the in-sample span (to 2025-02-28) and the vault span (2025-03-01 -> 2026-09-18) separately. Every OPRA parent
is first RESOLVED on one date (memory: probe what a parent symbol resolves to before quoting a pull).
The key is the principal's (env DATABENTO_API_KEY or ~/.config/databento/key); it is never printed.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "opening" / "opra_imbalance_quote.json"
KEY_FILE = Path.home() / ".config" / "databento" / "key"
SPANS = {"in_sample": ("2016-01-01", "2025-03-01"), "vault": ("2025-03-01", "2026-09-19")}
OPRA = {"spx_complex": ["SPX.OPT", "SPXW.OPT", "SPY.OPT"], "ndx_complex": ["NDX.OPT", "NDXP.OPT", "QQQ.OPT"]}
OPRA_SCHEMAS = ("statistics", "definition", "ohlcv-1d")
IMB = ("XNYS.PILLAR", "XNAS.ITCH", "ARCX.PILLAR")
IMB_START = "2018-05-01"  # Databento's imbalance history (C3, D661 sources)
PROBE_DATE = ("2024-06-03", "2024-06-04")


def api_key() -> str:
    k = os.environ.get("DATABENTO_API_KEY")
    if k:
        return k.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"no key: set DATABENTO_API_KEY or write {KEY_FILE}")


def quote(c, dataset: str, symbols, schema: str, start: str, end: str, stype_in: str) -> dict:
    try:
        size = c.metadata.get_billable_size(dataset, start=start, end=end, symbols=symbols, schema=schema, stype_in=stype_in)
        usd = c.metadata.get_cost(dataset, start=start, end=end, symbols=symbols, schema=schema, stype_in=stype_in)
        return {"billable_gb": round(size / 1e9, 3), "usd": round(float(usd), 2)}
    except Exception as e:  # noqa: BLE001 -- a refused quote is reported, not skipped
        return {"error": f"{type(e).__name__}: {str(e)[:300]}"}


def main() -> int:
    import databento as db

    c = db.Historical(api_key())
    t0 = time.time()
    out: dict = {"quoted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "spans": SPANS, "probe": {},
                 "opra": {}, "imbalance": {}, "note": "on-demand (pay-as-you-go) prices from metadata.get_cost; "
                 "plan entitlements are not applied"}
    for grp, parents in OPRA.items():
        for p in parents:
            try:
                r = c.symbology.resolve(dataset="OPRA.PILLAR", symbols=[p], stype_in="parent", stype_out="instrument_id",
                                        start_date=PROBE_DATE[0], end_date=PROBE_DATE[1])
                res = r.get("result", {}) if isinstance(r, dict) else {}
                n = sum(len(v) for v in res.values())
                out["probe"][p] = {"instruments_on_" + PROBE_DATE[0]: n, "not_found": r.get("not_found", []) if isinstance(r, dict) else None}
            except Exception as e:  # noqa: BLE001
                out["probe"][p] = {"error": f"{type(e).__name__}: {str(e)[:300]}"}
            print(f"probe {p}: {out['probe'][p]}")
        for span, (a, b) in SPANS.items():
            for schema in OPRA_SCHEMAS:
                q = quote(c, "OPRA.PILLAR", parents, schema, a, b, "parent")
                out["opra"].setdefault(grp, {}).setdefault(span, {})[schema] = q
                print(f"{grp:<12} {span:<9} {schema:<11} {q}")
    for ds in IMB:
        for span, (a, b) in SPANS.items():
            q = quote(c, ds, "ALL_SYMBOLS", "imbalance", max(a, IMB_START), b, "raw_symbol")
            out["imbalance"].setdefault(ds, {})[span] = q
            print(f"imbalance {ds:<12} {span:<9} {q}")
    out["timing_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)} in {out['timing_s']} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
