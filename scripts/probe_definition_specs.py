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
import ast
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
DEF_JOB = RAW / "GLBX-20260911-LEFUEVLPSR"
DEF_FILE = DEF_JOB / "glbx-mdp3-20260101-20260910.definition.dbn.zst"
OUT = REPO / "data" / "fut_specs_from_definition.json"
BREADTH_BUILDER = REPO / "scripts" / "build_fut_breadth_hourly.py"
BREADTH_META = REPO / "data" / "fixtures" / "fut_breadth_hourly.meta.json"

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


# --------------------------------------------------------------------------------------------
# D609 -- THE SCALING, DECIDED BY THE NOTIONAL AND NOT BY `unit_of_measure`
#
# `do_specs` below divides by 100 when `unit_of_measure == "USD"` and never otherwise. Its own
# docstring says that rule is not the rule -- "`HG` and `ZL` share `UOM == "LBS"` and differ by a
# factor of 100 ... the decidable test is the NOTIONAL" -- and the code never caught up. The
# committed table is therefore 100x wrong on ZC, ZS, ZW (BU), ZL, LE, HE (LBS) and 100x LOW on
# SR3, where the percent-of-par divide fires on a `uom_qty` that is ALREADY dollars per point.
# Seven roots, every one of them with `known_tick_usd: null`: nothing had ever verified them.
#
# The fix does not retype a number. `decide_scaling` is compiled out of
# `scripts/build_fut_breadth_hourly.py`, which has decided this correctly for 36 roots since
# D519, and its answers are asserted equal to the breadth meta's committed `scaling_divisor`,
# `scaling_reason` and `tick_usd_full_contract` on every shared root.
#
# WHAT IS ADDED, AND WHAT IS NOT TOUCHED. `tick_usd` stays exactly as it was written: D591's and
# D604's records quote it, and a record's evidence is not edited under it. The corrected value
# is a NEW key, `tick_usd_full_contract`, and `Future.from_specs` reads that one and raises if
# it is absent.
# --------------------------------------------------------------------------------------------

def _from_breadth_builder():
    """`decide_scaling`, `NOTIONAL_LO/HI` and `MICRO_OF`, compiled out of the breadth builder.

    Compiled rather than imported: `scripts/` is not a package, and importing a runner runs its
    module body (D606's lesson -- `run_d365` installs an audit hook CPython cannot remove). This
    reuses the builder's own committed bytes, so an edit to `decide_scaling` moves this table.
    """
    source = BREADTH_BUILDER.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
    tree = ast.parse(source, filename=str(BREADTH_BUILDER))
    ns = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                name = getattr(target, "id", "")
                if name in ("NOTIONAL_LO", "NOTIONAL_HI", "MICRO_OF"):
                    ns[name] = ast.literal_eval(node.value)
        elif isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "":
            continue
    # NOTIONAL_LO, NOTIONAL_HI are assigned on one line as a tuple target
    if "NOTIONAL_LO" not in ns:
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Tuple):
                names = [getattr(e, "id", "") for e in node.targets[0].elts]
                if names == ["NOTIONAL_LO", "NOTIONAL_HI"]:
                    lo, hi = ast.literal_eval(node.value)
                    ns["NOTIONAL_LO"], ns["NOTIONAL_HI"] = lo, hi
    found = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "decide_scaling"]
    gate = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "GateError"]
    if len(found) != 1 or len(gate) != 1:
        raise SystemExit(f"[SCALE] {BREADTH_BUILDER.name} no longer defines decide_scaling/GateError alone")
    for key in ("NOTIONAL_LO", "NOTIONAL_HI", "MICRO_OF"):
        if key not in ns:
            raise SystemExit(f"[SCALE] {BREADTH_BUILDER.name} no longer defines {key}")
    exec(compile(ast.Module(body=gate + found, type_ignores=[]), str(BREADTH_BUILDER), "exec"), ns)
    return ns


def rescale(table: dict) -> tuple[dict, list[str]]:
    """Add `tick_usd_raw_formula`, `scaling_divisor`, `scaling_reason`, `tick_usd_full_contract`.

    The NOTIONAL test needs an observed PRICE, which the `definition` schema does not carry, so
    the prices are the breadth fixture's own last bar per root (`fut_breadth_hourly.meta.json`,
    `specs.<ROOT>.last_price`) -- the same numbers the breadth builder decided on. A micro
    INHERITS ITS PARENT'S divisor, exactly as `build_fut_breadth_hourly.specs_for` does, because
    a micro quotes the same price as its parent and its own notional is too small for the band.

    Returns the table and the list of roots whose corrected value differs from `tick_usd`.
    """
    ns = _from_breadth_builder()
    decide = ns["decide_scaling"]
    parent_of = {micro: parent for parent, micro in ns["MICRO_OF"].items()}
    meta = json.loads(BREADTH_META.read_text(encoding="utf-8"))["specs"]

    corrected = []
    divisors = {}
    for root in ROOTS:
        entry = table["specs"].get(root)
        if not entry or not entry.get("present"):
            continue
        tick_px = float(entry["tick_price_units"])
        uomq = float(entry["unit_of_measure_qty"])
        raw = tick_px * uomq
        if root in meta:
            div, why = decide(root, tick_px, uomq, float(meta[root]["last_price"]))
            source = "NOTIONAL test on fut_breadth_hourly.meta.json#specs.%s.last_price" % root
        else:
            parent = parent_of.get(root)
            if parent is None or parent not in divisors:
                raise SystemExit(
                    f"[SCALE] {root} is in neither the breadth fixture nor the micro map, so "
                    "its quotation convention is undecided. A guessed divisor is a 100x error "
                    "in every dollar figure and it does not look like a failure."
                )
            div, why = divisors[parent], f"inherits {parent}'s scaling (a micro quotes its parent's price)"
            source = f"parent {parent}"
        divisors[root] = div
        full = raw / div
        entry["tick_usd_raw_formula"] = raw
        entry["scaling_divisor"] = div
        entry["scaling_reason"] = why
        entry["scaling_source"] = source
        entry["tick_usd_full_contract"] = full
        if abs(full - float(entry["tick_usd"])) > 1e-12 * max(full, 1.0):
            entry["tick_usd_superseded"] = True
            corrected.append(root)

    table["scaling_rule"] = (
        "tick_usd_full_contract = tick_price_units * unit_of_measure_qty / scaling_divisor, "
        "where the divisor is decided by the NOTIONAL test in "
        "scripts/build_fut_breadth_hourly.py:decide_scaling (/100 where the notional says the "
        "quote is percent or cents; ambiguity raises). `tick_usd` is the ORIGINAL field and is "
        "left unchanged because D591 and D604 quote it; it applies /100 on "
        "unit_of_measure == 'USD' alone, which is wrong for the roots listed in "
        "scaling_corrections. Read tick_usd_full_contract."
    )
    table["scaling_corrections"] = sorted(corrected)
    table["scaling_decided_by"] = "D609"
    return table, sorted(corrected)


def check_rescaled(table: dict) -> list[str]:
    """Known-answer first, then the seven. Returns the list of failures."""
    meta = json.loads(BREADTH_META.read_text(encoding="utf-8"))["specs"]
    bad = []
    n_known = 0
    for root, entry in table["specs"].items():
        if not entry.get("present"):
            continue
        known = entry.get("known_tick_usd")
        if known is not None:
            n_known += 1
            if abs(entry["tick_usd_full_contract"] - float(known)) > 1e-9 * float(known):
                bad.append(f"{root}: full {entry['tick_usd_full_contract']} != known {known}")
        if root in meta:
            for key in ("scaling_divisor", "scaling_reason", "tick_usd_full_contract"):
                if entry[key] != meta[root][key]:
                    bad.append(f"{root}.{key}: {entry[key]!r} != breadth meta {meta[root][key]!r}")
    P(f"  known-answer: {n_known} roots carry a CME tick value; every one must reproduce")
    want = {"ZC": 100.0, "ZS": 100.0, "ZW": 100.0, "ZL": 100.0, "LE": 100.0, "HE": 100.0,
            "SR3": 1.0}
    got = {r: table["specs"][r]["scaling_divisor"] for r in want}
    if got != want:
        bad.append(f"the seven corrected divisors are {got}, expected {want}")
    if table["scaling_corrections"] != sorted(want):
        bad.append(f"corrections {table['scaling_corrections']} != {sorted(want)}")
    return bad


def do_rescale() -> int:
    """Transform the COMMITTED table in place. Deterministic; no archive read.

    The NOTIONAL test needs a price and the `definition` archive carries none, so a full
    regeneration (`--specs`, which re-reads 166 MB of DBN under the system python) would still
    have to reach for the breadth meta for exactly these numbers. Everything this adds is a
    function of the committed table and the committed breadth meta, so it is done here, without
    the archive, and the record says so.
    """
    table = json.loads(OUT.read_text(encoding="utf-8"))
    table, corrected = rescale(table)
    bad = check_rescaled(table)
    P("   root   tick_usd(old)   raw formula   divisor   tick_usd_full   known   corrected")
    for root in ROOTS:
        e = table["specs"].get(root)
        if not e or not e.get("present"):
            continue
        known = e.get("known_tick_usd")
        P(f"   {root:>4}{e['tick_usd']:>15.6f}{e['tick_usd_raw_formula']:>14.4f}"
          f"{e['scaling_divisor']:>10.0f}{e['tick_usd_full_contract']:>16.6f}"
          + (f"{known:>8.4f}" if known is not None else " " * 8)
          + ("   ***" if root in corrected else ""))
    P("")
    if bad:
        for b in bad:
            P(f"  *** {b}")
        P(f"  {len(bad)} CHECK(S) FAILED -- nothing written")
        return 1
    P(f"  corrected: {corrected}")
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(table, indent=2))
    P(f"  wrote {OUT.relative_to(REPO)}")
    return 0


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
    out = {"source": str(DEF_FILE.relative_to(REPO)),
           "snapshot_day_index": day, "formula":
           "tick_usd = mpi*1e-9*display_factor * uom_qty*1e-9",
           "verified_against": repo,
           "formula_mismatches": bad, "specs": table}
    # D609: the scaling is added HERE too, so a regeneration from the archive produces the same
    # keys a `--rescale` of the committed table does, rather than silently dropping them.
    out, corrected = rescale(out)
    failures = check_rescaled(out)
    if failures:
        for f in failures:
            P(f"  *** {f}")
        raise SystemExit("[SCALE] the rescaled table failed its own checks -- nothing written")
    P(f"  scaling corrections (D609): {corrected}")
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, indent=2))
    P(f"\n  wrote {OUT.relative_to(REPO)}")
    return 1 if bad else 0


EXP_OUT = REPO / "data" / "fut_expiries_from_definition.json"


def do_expiries() -> int:
    """(root, symbol) -> expiration, for every outright in every year's first snapshot.

    WHY THIS EXISTS. The breadth builder's G2 (roll monotonicity) and G4 (the front must be a
    near month) both need each contract's expiry, and I first DERIVED it by parsing the symbol's
    year digit. That is the same ambiguity that caused the CLN9 bug: a single-digit year cannot
    distinguish July 2019 from July 2029, so `CLN9` was read as 2029 in 2019 data. G2 then fired
    spuriously on NG/SR3/ZT and G4 failed on ALL 36 ROOTS -- a gate everything fails is a broken
    gate, R7's corollary in reverse.

    `definition` carries `expiration` per instrument and it is unambiguous. One snapshot per year
    file covers every contract listed in that year.
    """
    import databento as db
    files = sorted(DEF_JOB.glob("*.definition.dbn.zst"))
    P(f"  {len(files)} definition files, "
      f"{sum(f.stat().st_size for f in files) / 2**30:.2f} GiB")
    out, seen = {}, set()
    for i, f in enumerate(files, 1):
        store = db.DBNStore.from_file(f)
        first, n = None, 0
        for rec in store:
            d = getattr(rec, "ts_event", None)
            if d is None:
                continue
            day = int(d) // 86_400_000_000_000
            if first is None:
                first = day
            if day != first:
                break
            sym = str(getattr(rec, "raw_symbol", ""))
            rt = root_of(sym)
            if rt is None:
                continue
            exp = getattr(rec, "expiration", None)
            if not exp:
                continue
            # KEEP EVERY EXPIRY PER SYMBOL, as a list. A symbol->one-expiry map cannot represent
            # the ambiguous cases, which are the only ones that need it: CLN9 is July-2019 and,
            # after that expires, July-2029. A consumer resolves it from the SESSION DATE -- the
            # nearest expiry at or after it -- which is information the symbol string does not
            # carry and a front month always satisfies.
            key = (rt, sym, int(exp))
            if key in seen:
                continue
            seen.add(key)
            out.setdefault(rt, {}).setdefault(sym, []).append(int(exp))
            n += 1
        P(f"  [{i}/{len(files)}] {f.name[:42]:<42} +{n} new outrights "
          f"({sum(len(v) for v in out.values()):,} total)")
    EXP_OUT.write_text(json.dumps({"source": str(DEF_JOB.relative_to(REPO)),
                                   "field": "expiration (ns since epoch, UTC)",
                                   "n_roots": len(out),
                                   "n_symbols": sum(len(v) for v in out.values()),
                                   "resolve": "a symbol may carry several expiries; pick the "
                                              "nearest at or after the session date",
                                   "expiries": out}, indent=2), encoding="utf-8")
    P(f"\n  {len(out)} roots, {sum(len(v) for v in out.values()):,} outrights")
    P(f"  wrote {EXP_OUT.relative_to(REPO)}")
    # a sanity read: the ambiguous CLN9 case, both contracts, from the authoritative field
    amb = {r: {k: v for k, v in d.items() if len(v) > 1} for r, d in out.items()}
    amb = {r: d for r, d in amb.items() if d}
    P(f"  symbols carrying MORE THAN ONE expiry (the ambiguous ones): "
      f"{sum(len(d) for d in amb.values())} across {len(amb)} roots")
    for r in sorted(amb)[:6]:
        k = sorted(amb[r])[0]
        P(f"    {r}: e.g. {k} -> {[pd_ts(x) for x in sorted(amb[r][k])]}")
    return 0


def pd_ts(ns: int) -> str:
    import pandas as pd
    return str(pd.Timestamp(ns, unit="ns", tz="UTC").date())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fields", action="store_true")
    ap.add_argument("--specs", action="store_true")
    ap.add_argument("--expiries", action="store_true")
    ap.add_argument("--rescale", action="store_true",
                    help="D609: add the NOTIONAL-decided scaling to the COMMITTED table")
    a = ap.parse_args()
    if a.fields:
        return do_fields()
    if a.specs:
        return do_specs()
    if a.expiries:
        return do_expiries()
    if a.rescale:
        return do_rescale()
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
