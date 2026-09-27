"""The pre-lapse sweep: every CME pull the programme's open models need that is USD 0.00 under the CME Standard
subscription now and billed after it lapses (~2026-10-11). **Metadata calls only: nothing is submitted or
downloaded.** The principal, 2026-09-27: "Yes, do the sweep, then open LETF close-flow".

    python scripts/quote_prelapse_sweep.py        # SYSTEM interpreter (databento is installed only there)

writes `data/prelapse_sweep_quote.json`.

WHAT THE MODELS NEED (deposit docs, read-only) AND WHAT IS ALREADY ON DISK (docs/data-available.md):
- ohlcv-1m, every instrument, 2010-06-06 -> 2026-09-10; tbbo, every instrument, 2025-09-11 -> 2026-09-11;
  statistics + definition, 41 roots, -> 2026-09-11; mbo, 8 roots, 2026-08-11 -> 2026-09-10; ES options
  (quarterly + weeklies) statistics + definition 2016 -> 2026-09-11 (D581).
- LETF close-flow s.3.3: ES/NQ (and MNQ volume) 1-minute bars 2016 -> latest. On disk to 2026-09-10.
- Opening agent-state s.3: ES/NQ 1-minute bars; ES/NQ trades with aggressor (tbbo: last 12 months only);
  **CME options on ES/NQ, daily OI by strike and settlements** (S-H, O-Q2): ES on disk, **NQ not**.
- Shock classifier s.3.2: 1-minute bars for NQ ES RTY ZN 6J CL BZ HO RB GC SI 6E (on disk); trades with
  aggressor for NQ ES CL GC (tbbo: last 12 months).
- Settlement ledger: CL/NG options OI (not on disk; D619 quoted 178 GB at USD 0.00).

So the sweep quotes: (A) NQ options, each candidate family RESOLVED and counted first (D581: ES.OPT was the
quarterlies alone); (B) the CL/NG options re-quoted to date; (C) the forward top-up of everything on disk from its
end to the latest available date, which is what the post-vault recorders (Track 2) would otherwise pay for.
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
OUT = REPO / "data" / "prelapse_sweep_quote.json"
ENERGY_PROBE = REPO / "data" / "energy_options_parents_probe.json"
HIST_START = "2016-01-01"
DISK_END = "2026-09-11"  # the on-disk archives end here (data-available.md)
WINDOWS = (("2016-01-04", "2016-01-08"), ("2026-09-01", "2026-09-10"))

#: NQ option families as CME lists them: the quarterly under NQ, the Friday weeklies QN1-QN4, the end-of-month
#: QNE, and the Monday-Thursday dailies Q{1-5}{A-D}. Every one is resolved; one resolving to nothing is recorded.
NQ_CANDIDATES = ["NQ", "QN1", "QN2", "QN3", "QN4", "QN5", "QNE"] + [f"Q{i}{d}" for d in "ABCD" for i in range(1, 6)]
ES_OPTION_PARENTS = ["ES", "EW", "EW1", "EW2", "EW3", "EW4"] + [f"E{i}{d}" for d in "ABCD" for i in range(1, 6)
                                                               if f"E{i}{d}" != "E5A"]
ROOTS_41 = ["ES", "NQ", "RTY", "YM", "MES", "MNQ", "M2K", "MYM", "CL", "NG", "GC", "SI", "HG", "ZN", "ZB", "ZF",
            "SR3", "ZT", "UB", "TN", "RB", "HO", "BZ", "PL", "PA", "6E", "6J", "6B", "6A", "6C", "6S",
            "ZC", "ZS", "ZW", "ZL", "ZM", "LE", "HE", "NKD", "BTC", "MBT"]
ROOTS_8 = ["ES", "NQ", "RTY", "YM", "CL", "GC", "ZN", "ZB"]


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


def resolve(c, parent: str) -> dict[str, int]:
    out = {}
    for a, b in WINDOWS:
        try:
            r = c.symbology.resolve(dataset=DATASET, symbols=[f"{parent}.OPT"], stype_in="parent",
                                    stype_out="instrument_id", start_date=a, end_date=b)
            out[a[:4]] = len({x["s"] for v in r.get("result", {}).values() for x in v})
        except Exception as e:  # a family that does not exist is an answer, not a crash
            out[a[:4]] = -1
            P(f"    {parent}.OPT {a}: {type(e).__name__}")
    return out


def quote(c, symbols, schema: str, start: str, end: str, stype_in: str) -> dict[str, object]:
    kw = dict(dataset=DATASET, start=start, end=end, symbols=symbols, schema=schema, stype_in=stype_in)
    size = c.metadata.get_billable_size(**kw)
    usd = c.metadata.get_cost(**kw)
    row = {"start": start, "end": end, "billable_bytes": int(size), "billable_gb": round(size / 1e9, 2),
           "usd": float(usd)}
    P(f"    {schema:<11} {start}..{end}  {row['billable_gb']:>9.2f} GB  USD {row['usd']:>10,.2f}")
    return row


def main() -> int:
    import databento as db

    c = db.Historical(api_key())
    t0 = time.time()
    rng = c.metadata.get_dataset_range(dataset=DATASET)
    end = str(rng["end"])[:10] if isinstance(rng, dict) else str(rng.end)[:10]
    P(f"  dataset available to {end}")
    out: dict[str, object] = {"dataset": DATASET, "quoted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                              "submitted": False, "available_end": end,
                              "instruction": "the principal, 2026-09-27: 'Yes, do the sweep, then open LETF close-flow'",
                              "subscription_note": "USD 0.00 under CME Standard until the lapse (~2026-10-11); billed after"}

    P("  (A) NQ options: resolving each candidate family")
    fam = {p: resolve(c, p) for p in NQ_CANDIDATES}
    for p, n in fam.items():
        P(f"    {p + '.OPT':<9} 2016: {n['2016']:>6}  2026: {n['2026']:>6}")
    nq = [f"{p}.OPT" for p, n in fam.items() if max(n.values()) > 0]
    out["nq_options"] = {"families": fam, "resolved": nq, "schemas": {
        s: quote(c, nq, s, HIST_START, end, "parent") for s in ("definition", "statistics")}}

    P("  (B) CL/NG options (D619's resolved parents), re-quoted to date")
    energy = list(json.loads(ENERGY_PROBE.read_text(encoding="utf-8"))["resolved_parents"])
    out["energy_options"] = {"resolved": energy, "schemas": {
        s: quote(c, energy, s, HIST_START, end, "parent") for s in ("definition", "statistics")}}

    P(f"  (C) forward top-ups, {DISK_END} -> {end}")
    es = [f"{p}.OPT" for p in ES_OPTION_PARENTS]
    out["topup"] = {
        "ohlcv-1m ALL_SYMBOLS": quote(c, "ALL_SYMBOLS", "ohlcv-1m", DISK_END, end, "raw_symbol"),
        "tbbo ALL_SYMBOLS": quote(c, "ALL_SYMBOLS", "tbbo", DISK_END, end, "raw_symbol"),
        "statistics 41 roots": quote(c, [f"{r}.FUT" for r in ROOTS_41], "statistics", DISK_END, end, "parent"),
        "definition 41 roots": quote(c, [f"{r}.FUT" for r in ROOTS_41], "definition", DISK_END, end, "parent"),
        "mbo 8 roots": quote(c, [f"{r}.FUT" for r in ROOTS_8], "mbo", DISK_END, end, "parent"),
        "statistics ES options": quote(c, es, "statistics", DISK_END, end, "parent"),
        "definition ES options": quote(c, es, "definition", DISK_END, end, "parent"),
    }
    blocks = [out["nq_options"]["schemas"], out["energy_options"]["schemas"], out["topup"]]  # type: ignore[index]
    out["total_usd"] = sum(v["usd"] for b in blocks for v in b.values())
    out["total_gb"] = round(sum(v["billable_bytes"] for b in blocks for v in b.values()) / 1e9, 2)
    out["timing_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    P(f"  total {out['total_gb']} GB, USD {out['total_usd']:,.2f}; nothing submitted. wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
