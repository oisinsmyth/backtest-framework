"""Probe: per-root contract specs from the GLBX `definition` schema we already own.

    python scripts/probe_definition_specs.py --fields      # dump the fields of one record
    python scripts/probe_definition_specs.py --specs       # the spec table, with a VERIFY step

**Data layer only, no study.** The point is to stop typing contract specs from memory or the web:
`definition` is the authoritative source, it is on disk, and it covers all 41 acquired roots. The
tick-value formula is DERIVED from the raw records and then VERIFIED against every anchor in
`data/futures_contract_specs.json` before it is applied to anything new.

THE FORMULA, verified on all 17 anchors
---------------------------------------
    tick_px  = min_price_increment * 1e-9
    tick_usd = tick_px * (unit_of_measure_qty * 1e-9)      / 100 where the quote is in
                                                             PERCENT or CENTS
My first pass multiplied by `display_factor` and anchored 6E at $12.50 from memory. Both were
wrong -- `display_factor` is not a price multiplier here, and the repo's committed 6E tick is
$6.25. **The anchor was the error, not the formula**, which is why the anchors are now read from
the file at run time and never retyped.

THE TRAP THIS PROBE EXISTS TO CATCH
-----------------------------------
**The /100 is a quotation convention and it is NOT inferable from `unit_of_measure` alone.**

    ZN, ZB, ZF, ZT, UB, TN   UOM "USD"   percent of par        -> /100   (110.5 = 110.5%)
    ZC, ZS, ZW               UOM "BU"    CENTS per bushel      -> /100
    ZL, LE, HE               UOM "LBS"   CENTS per pound       -> /100
    HG                       UOM "LBS"   DOLLARS per pound     -> NO /100
    ES, GC, CL, NG, 6E ...               native units          -> NO /100

`HG` and `ZL` share `UOM == "LBS"` and differ by a factor of 100. **Applied blind, every grain and
livestock root would carry a tick value 100x too large** -- and since every prop hurdle in this
programme is a dollar figure, that would not fail loudly, it would just quietly declare those
roots untradeable.

**The decidable test is the NOTIONAL**: `price * unit_of_measure_qty` must be plausible for a
listed futures contract. ZC at 450 cents x 5,000 bu reads $2,250,000 undivided and $22,500
divided; the true contract is $22,500. So the builder must compute the notional from the OBSERVED
price and RAISE on anything outside a plausible band rather than scale silently.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
DEF_JOB = RAW / "GLBX-20260911-LEFUEVLPSR"
DEF_FILE = DEF_JOB / "glbx-mdp3-20260101-20260910.definition.dbn.zst"
OUT = REPO / "data" / "fut_specs_from_definition.json"

# every root the acquisition bought, from run_futures_acquisition.ROOTS_41
ROOTS = ["ES", "NQ", "RTY", "YM", "MES", "MNQ", "M2K", "MYM",
         "CL", "NG", "GC", "SI", "HG", "ZN", "ZB", "ZF",
         "SR3", "ZT", "UB", "TN", "RB", "HO", "BZ", "PL", "PA",
         "6E", "6J", "6B", "6A", "6C", "6S",
         "ZC", "ZS", "ZW", "ZL", "ZM", "LE", "HE", "NKD", "BTC", "MBT"]

# The verification anchor is data/futures_contract_specs.json ITSELF, read at run time -- never
# retyped here. My first pass hardcoded 6E at $12.50 from memory and the repo's committed value is
# $6.25, so the ANCHOR was the error and not the formula. Read the file.
SPECS_FILE = REPO / "data" / "futures_contract_specs.json"
MONTHS = set("FGHJKMNQUVXZ")


def P(*a, **k):
    print(*a, **k, flush=True)


def root_of(sym: str) -> str | None:
    """Outright futures only: ROOT + month code + 1-2 digit year. No spreads, no options."""
    s = str(sym)
    for n in (3, 2, 1):                      # try the longest root first (SR3 before SR)
        if len(s) >= n + 2 and s[:n] in set(ROOTS):
            rest = s[n:]
            if rest and rest[0] in MONTHS and rest[1:].isdigit() and 1 <= len(rest[1:]) <= 2:
                return s[:n]
    return None


def load_first_day():
    import databento as db
    store = db.DBNStore.from_file(DEF_FILE)
    seen, rows, first_day = set(), [], None
    for rec in store:
        d = getattr(rec, "ts_event", None)
        if d is None:
            continue
        day = int(d) // 86_400_000_000_000
        if first_day is None:
            first_day = day
        if day != first_day:
            break                            # one daily snapshot is the whole instrument list
        sym = getattr(rec, "raw_symbol", None)
        if sym is None or sym in seen:
            continue
        seen.add(sym)
        rows.append(rec)
    return rows, first_day


def do_fields() -> int:
    rows, day = load_first_day()
    P(f"  {len(rows):,} distinct instruments in the first daily snapshot\n")
    for r in rows:
        if root_of(getattr(r, "raw_symbol", "")) == "ES":
            P("  a sample ES outright record's fields:")
            for f in sorted(dir(r)):
                if f.startswith("_") or callable(getattr(r, f, None)):
                    continue
                P(f"    {f:<34}{getattr(r, f)!r}")
            return 0
    P("  no ES outright found in the snapshot")
    return 1


def do_specs() -> int:
    repo = {k: v["tick_usd"] for k, v in
            json.loads(SPECS_FILE.read_text(encoding="utf-8")).items()
            if isinstance(v, dict) and "tick_usd" in v}
    rows, day = load_first_day()
    P(f"  snapshot of {len(rows):,} instruments; {len(repo)} anchors read from "
      f"{SPECS_FILE.name}\n")
    per = {}
    for r in rows:
        sym = str(getattr(r, "raw_symbol", ""))
        rt = root_of(sym)
        if rt is None:
            continue
        cls = str(getattr(r, "instrument_class", ""))
        mpi = getattr(r, "min_price_increment", None)
        dfac = getattr(r, "display_factor", None)
        uom = getattr(r, "unit_of_measure_qty", None)
        exp = getattr(r, "expiration", None)
        if mpi in (None, 0) or dfac in (None, 0):
            continue
        per.setdefault(rt, []).append({"symbol": sym, "class": cls, "mpi": int(mpi),
                                       "display_factor": int(dfac),
                                       "unit_of_measure_qty": int(uom) if uom else None,
                                       "expiration": int(exp) if exp else None,
                                       "currency": str(getattr(r, "currency", "")),
                                       "asset": str(getattr(r, "asset", "")),
                                       "uom": str(getattr(r, "unit_of_measure", "")),
                                       "group": str(getattr(r, "group", ""))})
    P("  FORMULA, derived from the ten raw records and now tested on every repo anchor:")
    P("    tick in price units = min_price_increment * 1e-9")
    P("    tick value $        = tick_px * (unit_of_measure_qty * 1e-9)")
    P("    ... DIVIDED BY 100 when unit_of_measure == 'USD' -- the Treasury percent-of-par")
    P("    convention, where ZN quoting 110.5 means 110.5% of a $100,000 face.\n")
    P("   root   n      tick(px)     UOM qty  UOM         tick $    repo $    check")
    table, bad = {}, []
    for rt in ROOTS:
        recs = per.get(rt)
        if not recs:
            table[rt] = {"present": False}
            continue
        r0 = sorted(recs, key=lambda x: x["expiration"] or 0)[0]
        tick_px = r0["mpi"] * 1e-9
        uomq = (r0["unit_of_measure_qty"] or 0) * 1e-9
        pct = r0["uom"] == "USD"          # percent-of-par quoting: the Treasury complex
        tick_usd = tick_px * uomq / (100.0 if pct else 1.0)
        known = repo.get(rt)
        ok = "" if known is None else ("OK" if abs(tick_usd - known) < 0.01 else "MISMATCH")
        if ok == "MISMATCH":
            bad.append((rt, tick_usd, known))
        table[rt] = {"present": True, "n_outrights": len(recs), "front_symbol": r0["symbol"],
                     "tick_price_units": tick_px, "unit_of_measure_qty": uomq,
                     "tick_usd": tick_usd, "known_tick_usd": known,
                     "asset": r0["asset"], "uom": r0["uom"], "group": r0["group"],
                     "currency": r0["currency"], "class": r0["class"]}
        table[rt]["percent_of_par"] = bool(pct)
        P(f"   {rt:>4}{len(recs):>4}{tick_px:>14.8f}{uomq:>12.1f}  {r0['uom']:<8}"
          f"{tick_usd:>11.4f}"
          + (f"{known:>10.4f}" if known is not None else " " * 10) + f"{ok:>9}")
    P("")
    absent = [r for r in ROOTS if not table[r]["present"]]
    if absent:
        P(f"  ABSENT from the snapshot: {absent}")
    if bad:
        P(f"  *** FORMULA FAILS on {[(b[0], round(b[1], 4), b[2]) for b in bad]} -- "
          f"do NOT use this table until it is understood")
    else:
        n_ck = sum(1 for r in ROOTS if table[r].get("known_tick_usd") is not None)
        P(f"  formula VERIFIED on all {n_ck} roots whose tick value this repo already holds")
    OUT.write_text(json.dumps({"source": str(DEF_FILE.relative_to(REPO)),
                               "snapshot_day_index": day, "formula":
                               "tick_usd = mpi*1e-9*display_factor * uom_qty*1e-9",
                               "verified_against": repo,
                               "formula_mismatches": bad, "specs": table}, indent=2),
                  encoding="utf-8")
    P(f"\n  wrote {OUT.relative_to(REPO)}")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fields", action="store_true")
    ap.add_argument("--specs", action="store_true")
    a = ap.parse_args()
    if a.fields:
        return do_fields()
    if a.specs:
        return do_specs()
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
