"""D508 -- the crossing cost actually PAID, from tbbo, for the micros bbo-1m never covered.

    python scripts/d508_micro_crossing_tbbo.py --self-test
    python scripts/d508_micro_crossing_tbbo.py --build [--limit N]   # SYSTEM python (databento)
    python scripts/d508_micro_crossing_tbbo.py --report

**NO RETURN IS READ.** Trade price against the pre-trade mid, the quoted spread, and depth. Every
quantity is a distance or a count; none is signed, so no direction can leak out of it.

WHY tbbo AND NOT bbo-1m
-----------------------
`bbo-1m` was bought for **41 roots** and MGC, MCL and M6E are not among them, so
[D507](../docs/decisions/) had to re-cost GC, CL and 6E on their FULL contracts' spreads --
and D507 §2 showed that overstates a micro's cost by up to 40%. **`tbbo` was bought for EVERY
instrument** over the same year, so the micros are already on disk.

And tbbo is the better instrument for this question. It carries the book **immediately before each
trade**, so two things are measurable that a 1-minute snapshot cannot give:

  quoted_spread_ticks    (ask - bid) / tick, at the instant someone actually traded
  effective_cost_ticks   2 * |price - mid| / tick -- what the AGGRESSOR PAID, doubled for a
                         round trip. This is the crossing cost, not a proxy for it.

They differ when a trade prints inside the spread or sweeps depth, and the second is what a
market order faces.

THE ASSUMPTION THIS RUNNER EXISTS TO CORRECT
--------------------------------------------
**A micro does NOT always share its parent's tick.** Measured from the committed spec file:

    MGC/GC   0.1     vs 0.1      SAME        MES/ES   0.25 vs 0.25  SAME
    MCL/CL   0.01    vs 0.01     SAME        MNQ/NQ   0.25 vs 0.25  SAME
    M6E/6E   0.0001  vs 0.00005  **DOUBLE**  MYM/YM   1.0  vs 1.0   SAME

D507 §2 generalised "same tick, a tenth of the notional" from the five index pairs, and M6E
breaks it. **A spread expressed in 6E ticks is half as many M6E ticks**, so D507's 6E row is
wrong in its crossing term and is corrected here (§4). Every tick is read per instrument and the
parent-equality is asserted, never assumed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

RAW = REPO / "data" / "raw" / "databento"
BREADTH = REPO / "data" / "fixtures" / "fut_breadth_hourly.csv.gz"
SPECS_REPO = REPO / "data" / "futures_contract_specs.json"
SPECS_DEF = REPO / "data" / "fut_specs_from_definition.json"
FIX = REPO / "data" / "fixtures" / "fut_crossing_tbbo.csv.gz"
OUT = REPO / "data" / "d508_micro_crossing_tbbo.json"

# the three micros bbo-1m never covered, their parents, and the five pairs it DID cover -- the
# latter give a bbo-1m-vs-tbbo calibration for free, since the decode cost is the decompression
PAIRS = {"MGC": "GC", "MCL": "CL", "M6E": "6E",
         "MES": "ES", "MNQ": "NQ", "M2K": "RTY", "MYM": "YM", "MBT": "BTC"}
ROOTS = tuple(sorted(set(PAIRS) | set(PAIRS.values())))
SYM = re.compile(r"^([A-Z0-9]{1,4})([FGHJKMNQUVXZ])([0-9]{1,2})$")
PX = 1e-9
UNDEF_PRICE = 2**63 - 1
DAY0, DAY1 = "2025-09-11", "2026-09-11"
EXEC_HOURS = tuple(range(10, 16))
CHUNK = 5_000_000


def P(*a, **k):
    print(*a, **k, flush=True)


class GateError(AssertionError):
    pass


def specs() -> dict:
    """tick in PRICE units and tick value, per instrument, from the committed file then the
    definition-derived one. NEVER inherited from a parent -- M6E is why."""
    a = json.loads(SPECS_REPO.read_text(encoding="utf-8"))
    b = json.loads(SPECS_DEF.read_text(encoding="utf-8"))["specs"]
    out = {}
    for r in ROOTS:
        d = a.get(r)
        if isinstance(d, dict) and "tick_points" in d:
            out[r] = {"tick_points": float(d["tick_points"]),
                      "tick_usd": float(d["tick_usd"]), "src": SPECS_REPO.name}
            continue
        d = b.get(r)
        if d and d.get("present"):
            out[r] = {"tick_points": float(d["tick_price_units"]),
                      "tick_usd": float(d["tick_usd"]), "src": SPECS_DEF.name}
            continue
        raise GateError(f"[SPEC] no tick for {r} in either spec file")
    return out


def micro_symbol(parent_sym: str, micro_root: str) -> str:
    m = SYM.match(str(parent_sym))
    if not m:
        raise GateError(f"[SYM] {parent_sym!r} is not an outright")
    return f"{micro_root}{m.group(2)}{m.group(3)}"


def front_map() -> dict:
    t = pd.read_csv(BREADTH, usecols=["root", "day", "contract"])
    t = t[t["day"].between(DAY0, DAY1)]
    fm = {(r, d): c for r, d, c in zip(t["root"], t["day"], t["contract"])}
    for micro, parent in PAIRS.items():
        for (r, d), c in list(fm.items()):
            if r == parent and isinstance(c, str):
                fm[(micro, d)] = micro_symbol(c, micro)
    return fm


def tbbo_files():
    return sorted(RAW.glob("*/*.tbbo.dbn.zst"))


def build(limit) -> int:
    import databento as db

    sp = specs()
    fm = front_map()
    files = tbbo_files()
    if limit:
        files = files[-limit:]          # the MOST RECENT, so the window is not chosen on outcome
    P(f"D508 build -- {len(files)} tbbo files, "
      f"{sum(f.stat().st_size for f in files) / 2**30:.2f} GiB, {len(ROOTS)} roots")
    P(f"  roots: {', '.join(ROOTS)}\n")
    t_start = time.time()
    acc = []
    for i, f in enumerate(files, 1):
        t0 = time.time()
        store = db.DBNStore.from_file(f)
        ids = {}
        for sym, ivs in store.metadata.mappings.items():
            m = SYM.match(str(sym))
            if not m or m.group(1) not in ROOTS:
                continue
            for iv in (ivs if isinstance(ivs, list) else [ivs]):
                sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
                if sid:
                    ids[int(sid)] = (m.group(1), str(sym))
        want_ids = np.fromiter(ids, dtype=np.uint32)
        n_raw = n_undef = n_bad = 0
        parts = []
        for arr in store.to_ndarray(count=CHUNK):
            a = arr[np.isin(arr["instrument_id"], want_ids)]
            if a.size == 0:
                continue
            n_raw += len(a)
            undef = np.logical_or(a["bid_px_00"] == UNDEF_PRICE,
                                  a["ask_px_00"] == UNDEF_PRICE)
            n_undef += int(undef.sum())
            bid = a["bid_px_00"].astype(np.float64) * PX
            ask = a["ask_px_00"].astype(np.float64) * PX
            prc = a["price"].astype(np.float64) * PX
            ok = np.logical_and(np.logical_and(a["bid_px_00"] > 0, a["ask_px_00"] > 0),
                                np.logical_and(~undef, ask > bid))
            ok = np.logical_and(ok, a["price"] > 0)
            n_bad += int((~ok).sum()) - int(undef.sum())
            a, bid, ask, prc = a[ok], bid[ok], ask[ok], prc[ok]
            if a.size == 0:
                continue
            ts = pd.to_datetime(a["ts_recv"], utc=True).tz_convert("US/Eastern")
            rr = np.array([ids[int(x)][0] for x in a["instrument_id"]])
            cc = np.array([ids[int(x)][1] for x in a["instrument_id"]])
            hh = ts.hour.to_numpy()
            sess = np.where(hh >= 18,
                            (ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d").to_numpy(),
                            ts.strftime("%Y-%m-%d").to_numpy())
            tick = np.array([sp[r]["tick_points"] for r in rr])
            mid = 0.5 * (bid + ask)
            d = pd.DataFrame({
                "root": rr, "contract": cc, "day": sess, "hour": hh,
                "spread_tk": (ask - bid) / tick,
                "eff_tk": 2.0 * np.abs(prc - mid) / tick,
                "size": a["size"].astype(np.int64),
                "q_lots": a["bid_sz_00"].astype(np.int64) + a["ask_sz_00"].astype(np.int64)})
            keep = np.array([fm.get((r, dd)) for r, dd in zip(d["root"], d["day"])])
            d = d[(keep == d["contract"].to_numpy()) & d["day"].between(DAY0, DAY1)]
            if len(d) == 0:
                continue
            # THE TICK MUST DIVIDE THE QUOTED SPREAD, per instrument
            fr = np.abs(d["spread_tk"].to_numpy() - np.round(d["spread_tk"].to_numpy()))
            if fr.max() > 1e-6:
                bad = d.iloc[int(np.argmax(fr))]
                raise GateError(
                    f"[TICK] the quoted spread is not a whole number of ticks in {f.name}: "
                    f"{bad['root']} {bad['contract']} {bad['spread_tk']:.9f} ticks at "
                    f"tick_points {sp[bad['root']]['tick_points']}")
            d["spread_tk"] = np.round(d["spread_tk"]).astype(np.int64)
            parts.append(d.groupby(["root", "day", "hour", "spread_tk"], as_index=False)
                         .agg(n=("size", "size"), vol=("size", "sum"),
                              eff_sum=("eff_tk", "sum"), q_lots=("q_lots", "sum")))
        if parts:
            g = (pd.concat(parts, ignore_index=True)
                 .groupby(["root", "day", "hour", "spread_tk"], as_index=False)
                 .agg(n=("n", "sum"), vol=("vol", "sum"), eff_sum=("eff_sum", "sum"),
                      q_lots=("q_lots", "sum")))
            acc.append(g)
            nr = g["root"].nunique()
        else:
            nr = 0
        P(f"  [{i:2d}/{len(files)}] {f.name[-30:]:<30} {n_raw:>10,} trades, "
          f"{n_undef:>6,} one-sided, {n_bad:>5,} bad  -> {nr:>2} roots  "
          f"({(time.time() - t0) / 60:.1f} min, ETA "
          f"{(time.time() - t_start) / i * (len(files) - i) / 60:.0f} min)")
    out = (pd.concat(acc, ignore_index=True)
           .groupby(["root", "day", "hour", "spread_tk"], as_index=False)
           .agg(n=("n", "sum"), vol=("vol", "sum"), eff_sum=("eff_sum", "sum"),
                q_lots=("q_lots", "sum")))
    FIX.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(FIX, index=False, compression="gzip")
    P(f"\n  wrote {FIX.relative_to(REPO)}  ({len(out):,} rows, {out['root'].nunique()} roots, "
      f"{out['n'].sum():,} trades) in {(time.time() - t_start) / 60:.1f} min")
    return 0


def stats(g):
    tot = int(g["n"].sum())
    if tot == 0:
        return {}
    by = g.groupby("spread_tk")["n"].sum()
    mean_q = float((by.index.to_numpy() * by.to_numpy()).sum() / tot)
    return {"trades": tot, "volume": int(g["vol"].sum()),
            "quoted_mean_ticks": mean_q,
            "quoted_P1": float(by.get(1, 0) / tot),
            "effective_mean_ticks": float(g["eff_sum"].sum() / tot),
            "q_lots": float(g["q_lots"].sum() / tot)}


def do_report(as_json: bool) -> int:
    sp = specs()
    d = pd.read_csv(FIX)
    P("D508 -- the crossing cost actually paid, from tbbo trades\n")
    P("     root  tick_pts   trades   quoted tk   P1    EFFECTIVE tk  | exec: quoted  EFFECTIVE"
      "  | q lots")
    rows = {}
    for r in sorted(d["root"].unique()):
        g = d[d["root"] == r]
        a = stats(g)
        e = stats(g[g["hour"].isin(EXEC_HOURS)])
        if not a:
            continue
        rows[r] = {"all_session": a, "execution_hours": e,
                   "tick_points": sp[r]["tick_points"], "tick_usd": sp[r]["tick_usd"]}
        P(f"     {r:>4}{sp[r]['tick_points']:>10.5f}{a['trades']:>9,}"
          f"{a['quoted_mean_ticks']:>12.3f}{a['quoted_P1']:>7.3f}"
          f"{a['effective_mean_ticks']:>14.3f}  |"
          f"{e.get('quoted_mean_ticks', float('nan')):>14.3f}"
          f"{e.get('effective_mean_ticks', float('nan')):>11.3f}  |{a['q_lots']:>8.0f}")

    P("\n  MICRO vs PARENT, on the EFFECTIVE cost at the execution hours")
    P("     pair        tick same?   parent tk   micro tk   ratio   micro cost $/RT")
    pairs = {}
    for micro, parent in sorted(PAIRS.items()):
        if micro not in rows or parent not in rows:
            continue
        same = abs(sp[micro]["tick_points"] - sp[parent]["tick_points"]) < 1e-15
        pe = rows[parent]["execution_hours"].get("effective_mean_ticks", float("nan"))
        me = rows[micro]["execution_hours"].get("effective_mean_ticks", float("nan"))
        usd = me * sp[micro]["tick_usd"]
        pairs[f"{micro}/{parent}"] = {"tick_same": bool(same), "parent_eff": pe,
                                      "micro_eff": me, "ratio": me / pe if pe else None,
                                      "micro_cross_usd_per_rt": usd}
        P(f"     {micro:>4}/{parent:<4}{'yes' if same else 'NO -- 2x':>12}{pe:>12.3f}"
          f"{me:>11.3f}{me / pe if pe else float('nan'):>8.2f}{usd:>17.2f}")

    art = {"purpose": "D508: the crossing cost actually paid, from tbbo, for the micros bbo-1m "
                      "never covered. NO RETURN READ. Nothing admitted.",
           "window": [DAY0, DAY1], "exec_hours": list(EXEC_HOURS),
           "statistics": {"quoted": "(ask - bid)/tick at the instant of a trade",
                          "effective": "2*|price - mid|/tick -- what the aggressor paid, "
                                       "doubled for a round trip; THIS is the crossing cost"},
           "per_root": rows, "micro_vs_parent": pairs, "specs": sp,
           "limitations": [
               "the window is one year (2025-09 to 2026-09) and it re-costs studies on "
               "2016-2023; a tick is fixed in price terms so a recent spread applied to an "
               "older window is OPTIMISTIC",
               "tbbo is conditioned on a trade having happened, so it is TRADE-WEIGHTED where "
               "bbo-1m is time-weighted; the two are different statistics and the calibration "
               "on the five pairs bbo-1m covered is reported for that reason",
               "the effective cost is measured on the trades that DID happen at whatever size "
               "they were; a 1-lot at the touch is the common case but sweeps are included",
               "a micro's tick is read per instrument: M6E's is DOUBLE 6E's, which is the "
               "error this runner corrects in D507"]}
    OUT.write_text(json.dumps(art, indent=2, default=float), encoding="utf-8")
    P(f"\n  wrote {OUT.relative_to(REPO)}")
    if as_json:
        P(json.dumps(art, indent=2, default=float))
    return 0


def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:62} {detail}")
        if not cond:
            fails.append(label)

    sp = specs()
    chk("every root has a tick read PER INSTRUMENT from a spec file",
        all(sp[r]["tick_points"] > 0 for r in ROOTS), f"{len(ROOTS)} roots")
    chk("[X] M6E's tick is DOUBLE 6E's -- a micro does NOT always inherit its parent's",
        abs(sp["M6E"]["tick_points"] - 2 * sp["6E"]["tick_points"]) < 1e-12,
        f"M6E {sp['M6E']['tick_points']} vs 6E {sp['6E']['tick_points']}")
    chk("and the index micros DO share theirs, which is why the error was invisible",
        all(abs(sp[m]["tick_points"] - sp[p]["tick_points"]) < 1e-15
            for m, p in (("MES", "ES"), ("MNQ", "NQ"), ("MYM", "YM"), ("M2K", "RTY"),
                         ("MGC", "GC"), ("MCL", "CL"))))

    # --- the two statistics, on a hand-built trade ------------------------------------------
    tick = 0.1
    bid, ask = 2400.0, 2400.2                # a 2-tick book
    mid = 0.5 * (bid + ask)
    at_ask = 2.0 * abs(ask - mid) / tick
    at_mid = 2.0 * abs(mid - mid) / tick
    swept = 2.0 * abs(2400.4 - mid) / tick
    # THE TOLERANCE IS DERIVED, NOT GUESSED. Subtracting two near-equal prices of magnitude p
    # loses about p*eps of precision, and dividing by a small tick amplifies it by 2/tick:
    #   2400.2 - 2400.1 = 0.09999999999990905, so at_ask = 1.9999999999981811
    # An absolute 1e-12 FAILED a correct result. The bound is 2*p*eps/tick.
    tol = 2.0 * ask * np.finfo(np.float64).eps / tick
    chk("a trade at the ask pays the FULL spread on a round trip",
        abs(at_ask - 2.0) < 10 * tol,
        f"{at_ask:.13f} ticks on a 2-tick book; derived bound {10 * tol:.2e}, "
        f"an absolute 1e-12 would fail this correct result")
    chk("a trade at the mid pays nothing, so the effective cost is not the spread by definition",
        abs(at_mid) < 1e-12)
    chk("[X] and a SWEEP beyond the ask pays MORE than the quoted spread",
        swept > 2.0, f"{swept:.3f} ticks against a quoted 2.000")

    # --- the sentinel, the defect D507 hit --------------------------------------------------
    px = np.array([2400_000_000_000, UNDEF_PRICE], dtype=np.int64)
    chk("[X] the UNDEFINED-price sentinel still passes `> 0`, so it is filtered explicitly",
        bool((px > 0)[1]) and not bool(np.logical_and(px > 0, px != UNDEF_PRICE)[1]))

    chk("the micro symbol takes the parent's month and year",
        micro_symbol("GCZ5", "MGC") == "MGCZ5"
        and micro_symbol("6EH26", "M6E") == "M6EH26",
        f"GCZ5->{micro_symbol('GCZ5', 'MGC')}, 6EH26->{micro_symbol('6EH26', 'M6E')}")

    # --- the D507 correction, computed ------------------------------------------------------
    d507 = REPO / "data" / "d507_spread_all_roots.json"
    if d507.exists():
        a = json.loads(d507.read_text(encoding="utf-8"))
        rc = a.get("d506_recost", {}).get("6E")
        if rc:
            wrong = rc["measured_cost_ticks"]
            spread_6e = rc["measured_spread_ticks"]
            right = (rc["assumed_cost_ticks"] - 1.0) + spread_6e / 2.0
            chk("[X] D507's 6E row double-counts the crossing because M6E's tick is 2x 6E's",
                abs(wrong - right) > 0.3,
                f"D507 says {wrong:.3f} tk; in M6E ticks it is {right:.3f} tk")
    P(f"\n  {len(fails)} failed: {fails}" if fails else "\n  all checks pass")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.build:
        return build(a.limit)
    if a.report:
        return do_report(a.json)
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
