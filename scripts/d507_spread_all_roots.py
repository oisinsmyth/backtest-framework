"""D507 -- the quoted-spread census on bbo-1m for ALL 41 acquired roots, INCLUDING THE MICROS.

    python scripts/d507_spread_all_roots.py --self-test
    python scripts/d507_spread_all_roots.py --build    # SYSTEM interpreter (databento)
    python scripts/d507_spread_all_roots.py --report

**NO RETURN IS READ.** Quoted bid/ask, sizes and order counts only. Every quantity is a
dispersion, a fraction or a depth; none is signed.

WHY THIS EXISTS WHEN D510 ALREADY RAN A CENSUS
----------------------------------------------
[D510](../docs/decisions/) measured the quoted spread on bbo-1m for **nine roots** and found the
thing that makes this urgent:

    ZN 1.000 · ZB 1.002 · ES 1.120 · 6E 1.297 · CL 1.678 · RTY 2.377 · YM 2.583 · NQ 3.768 · GC 4.435

**Every net figure in the prop line assumed 1.009 ticks** -- D471's ES measurement, applied to
every root. **NQ's full-contract spread is 3.768 ticks.** D495, D503, D504 and D506 all costed the
admitted arm at 1.009.

Two gaps D510 leaves, and both bite the book directly:

1. **IT MEASURED THE FULL CONTRACTS AND THE ARM TRADES A MICRO.** MNQ is a separate instrument
   with a separate book; NQ's 3.768 ticks says nothing about MNQ's. MES, MNQ, M2K, MYM and MBT
   are in the acquired 41 and were never measured. (MGC, MCL and M6E were not acquired, so
   GC, CL and 6E keep a full-contract proxy, flagged.)
2. **IT AVERAGED OVER ALL SESSION MINUTES.** The arm executes at HOUR OPENS. The spread at
   10:00:00 is not the spread at 10:37, and only the former is a cost.

WHAT THIS RUNNER ADDS
---------------------
All 41 roots; the micros; and an `is_open` dimension so the spread at the execution instants can
be read separately from the session average. Front-month determination, the session-day
convention and the integer-tick guard are D510's, reused rather than re-derived.

THE TICK GUARD IS THE LOAD-BEARING CHECK. A spread that is not a whole number of ticks means the
tick is wrong for that root, and it would silently rescale every figure for exactly that root
while looking plausible. It raises. Specs come from the definition-derived table whose formula was
verified on all 17 repo anchors.
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
SPECS_DEF = REPO / "data" / "fut_specs_from_definition.json"
FIX = REPO / "data" / "fixtures" / "fut_spread_all_1m.csv.gz"
OUT = REPO / "data" / "d507_spread_all_roots.json"

ROOTS = ("ES", "NQ", "RTY", "YM", "MES", "MNQ", "M2K", "MYM",
         "CL", "NG", "GC", "SI", "HG", "ZN", "ZB", "ZF",
         "SR3", "ZT", "UB", "TN", "RB", "HO", "BZ", "PL", "PA",
         "6E", "6J", "6B", "6A", "6C", "6S",
         "ZC", "ZS", "ZW", "ZL", "ZM", "LE", "HE", "NKD", "BTC", "MBT")
# a micro's front month is its parent's expiry: they roll together, so the symbol is the
# parent's with the root prefix swapped. Asserted in --self-test.
PARENT_OF = {"MES": "ES", "MNQ": "NQ", "M2K": "RTY", "MYM": "YM", "MBT": "BTC"}
SYM = re.compile(r"^([A-Z0-9]{1,4})([FGHJKMNQUVXZ])([0-9]{1,2})$")
PX = 1e-9
UNDEF_PRICE = 2**63 - 1        # Databento encodes an absent price as INT64_MAX
DAY0, DAY1 = "2025-09-11", "2026-09-10"
EXEC_HOURS = tuple(range(10, 16))     # the arm executes at the open of h10..h15


def P(*a, **k):
    print(*a, **k, flush=True)


class GateError(AssertionError):
    pass


def specs() -> dict:
    """The tick in PRICE units, plus the tick VALUE where a verified one exists.

    THE CENSUS ONLY NEEDS `tick_points`, and that is scaling-independent: it is
    `min_price_increment * 1e-9` straight from `definition`, untouched by the percent/cents
    question. The tick VALUE does depend on that scaling, and the probe's own `tick_usd` used a
    `unit_of_measure == "USD"` rule that is WRONG for SR3 and for the cents-quoted grains -- the
    verified values live in the breadth fixture's meta, decided by the notional test. So dollars
    are read from the meta and are optional; ticks are read from the probe and are required.
    """
    sd = json.loads(SPECS_DEF.read_text(encoding="utf-8"))["specs"]
    meta = json.loads((REPO / "data" / "fixtures"
                       / "fut_breadth_hourly.meta.json").read_text(encoding="utf-8"))["specs"]
    usd = {}
    for root, m in meta.items():
        usd[root] = float(m["tick_usd_full_contract"])
        if m.get("sized_as") and m["sized_as"] != root:
            usd[m["sized_as"]] = float(m["tick_usd"])       # the micro's verified value
    out = {}
    for r in ROOTS:
        d = sd.get(r)
        if not d or not d.get("present"):
            raise GateError(f"[SPEC] {r} absent from {SPECS_DEF.name}")
        out[r] = {"tick_points": float(d["tick_price_units"]),
                  "tick_usd": usd.get(r), "uom": d["uom"]}
    return out


def micro_symbol(parent_sym: str, micro_root: str) -> str:
    """ESZ5 -> MESZ5. The month and year are the parent's; only the root prefix changes."""
    m = SYM.match(str(parent_sym))
    if not m:
        raise GateError(f"[SYM] {parent_sym!r} is not an outright symbol")
    return f"{micro_root}{m.group(2)}{m.group(3)}"


def front_map() -> dict:
    """(root, session day) -> front contract. The 36 underlyings come from the breadth fixture's
    volume rule; the 5 micros inherit their parent's expiry with the prefix swapped."""
    t = pd.read_csv(BREADTH, usecols=["root", "day", "contract"])
    t = t[t["day"].between(DAY0, DAY1)]
    fm = {(r, d): c for r, d, c in zip(t["root"], t["day"], t["contract"])}
    for micro, parent in PARENT_OF.items():
        for (r, d), c in list(fm.items()):
            if r == parent and isinstance(c, str):
                fm[(micro, d)] = micro_symbol(c, micro)
    return fm


# ---------------------------------------------------------------------------- build

def build() -> int:
    import databento as db

    sp = specs()
    fm = front_map()
    files = sorted(RAW.glob("*/*.bbo-1m.dbn.zst"))
    if not files:
        raise GateError("[FILES] no bbo-1m files found")
    P(f"D507 build -- {len(files)} bbo-1m files, "
      f"{sum(f.stat().st_size for f in files) / 2**30:.2f} GiB, {len(ROOTS)} roots\n")
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
        arr = store.to_ndarray()
        keep = np.isin(arr["instrument_id"], np.fromiter(ids, dtype=np.uint32))
        a = arr[keep]
        del arr
        n_raw = len(a)
        # THE UNDEFINED-PRICE SENTINEL PASSES A `> 0` TEST, WHICH IS HOW THIS RAN AGROUND.
        # Databento encodes an absent price as INT64_MAX, and INT64_MAX > 0, so a one-sided
        # book survived the validity filter and produced a spread of 1,844,659,239 ticks on
        # MBTK6. The integer-tick guard caught it and refused to write the census -- but the
        # filter is where it belongs. D510's nine roots never hit it because they are liquid
        # enough to always quote two-sided; Micro Bitcoin is not.
        undef = np.logical_or(a["bid_px_00"] == UNDEF_PRICE, a["ask_px_00"] == UNDEF_PRICE)
        n_undef = int(undef.sum())
        bid = a["bid_px_00"].astype(np.float64) * PX
        ask = a["ask_px_00"].astype(np.float64) * PX
        ok = np.logical_and(np.logical_and(a["bid_px_00"] > 0, a["ask_px_00"] > 0),
                            np.logical_and(~undef, ask > bid))
        n_bad = int((~ok).sum()) - n_undef
        a, bid, ask = a[ok], bid[ok], ask[ok]
        ts = pd.to_datetime(a["ts_recv"], utc=True).tz_convert("US/Eastern")
        rr = np.array([ids[int(x)][0] for x in a["instrument_id"]])
        cc = np.array([ids[int(x)][1] for x in a["instrument_id"]])
        hh = ts.hour.to_numpy()
        mm = ts.minute.to_numpy()
        sess_day = np.where(hh >= 18,
                            (ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d").to_numpy(),
                            ts.strftime("%Y-%m-%d").to_numpy())
        tickp = np.array([sp[r]["tick_points"] for r in rr])
        spread_t = (ask - bid) / tickp
        d = pd.DataFrame({"root": rr, "contract": cc, "day": sess_day, "hour": hh,
                          "is_open": (mm == 0).astype(np.int8),
                          "spread_ticks": spread_t,
                          "q_orders": a["bid_ct_00"].astype(np.int64)
                          + a["ask_ct_00"].astype(np.int64),
                          "q_lots": a["bid_sz_00"].astype(np.int64)
                          + a["ask_sz_00"].astype(np.int64)})
        want = np.array([fm.get((r, dd)) for r, dd in zip(d["root"], d["day"])])
        d = d[(want == d["contract"].to_numpy()) & d["day"].between(DAY0, DAY1)]
        # THE TICK MUST DIVIDE THE SPREAD, for every one of the 41 roots.
        if len(d):
            frac = np.abs(d["spread_ticks"].to_numpy() - np.round(d["spread_ticks"].to_numpy()))
            if frac.max() > 1e-6:
                bad = d.iloc[int(np.argmax(frac))]
                raise GateError(
                    f"[TICK] the spread is not a whole number of ticks in {f.name}: "
                    f"{bad['root']} {bad['contract']} spread {bad['spread_ticks']:.9f} ticks "
                    f"at tick_points {sp[bad['root']]['tick_points']}. The tick is WRONG for "
                    f"that root and every figure derived from it would be rescaled.")
            d["spread_ticks"] = np.round(d["spread_ticks"]).astype(np.int64)
        g = (d.groupby(["root", "day", "hour", "is_open", "spread_ticks"], as_index=False)
             .agg(n=("q_orders", "size"), q_orders=("q_orders", "sum"),
                  q_lots=("q_lots", "sum")))
        acc.append(g)
        P(f"  [{i:2d}/{len(files)}] {f.name[-30:]:<30} {n_raw:>10,} quoted, "
          f"{n_undef:>7,} one-sided, {n_bad:>6,} crossed -> "
          f"{len(d):>9,} front minutes, {d['root'].nunique():>2} roots  "
          f"({time.time() - t0:.1f}s)")
    out = (pd.concat(acc, ignore_index=True)
           .groupby(["root", "day", "hour", "is_open", "spread_ticks"], as_index=False)
           .agg(n=("n", "sum"), q_orders=("q_orders", "sum"), q_lots=("q_lots", "sum")))
    FIX.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(FIX, index=False, compression="gzip")
    P(f"\n  wrote {FIX.relative_to(REPO)}  ({len(out):,} rows, {out['root'].nunique()} roots, "
      f"{out['n'].sum():,} front minutes) in {(time.time() - t_start) / 60:.1f} min")
    return 0


# ---------------------------------------------------------------------------- report

def census(g: pd.DataFrame) -> dict:
    """P1/P2/P3+, mean and median spread, and median touch depth, from a histogram frame."""
    tot = g["n"].sum()
    if tot == 0:
        return {}
    by = g.groupby("spread_ticks")["n"].sum()
    mean = float((by.index.to_numpy() * by.to_numpy()).sum() / tot)
    cum = by.cumsum() / tot
    med = float(cum.index[np.searchsorted(cum.to_numpy(), 0.5)])
    return {"minutes": int(tot), "P1": float(by.get(1, 0) / tot),
            "P2": float(by.get(2, 0) / tot),
            "P3plus": float(by[by.index >= 3].sum() / tot),
            "mean_spread_ticks": mean, "median_spread_ticks": med,
            "q_orders": float(g["q_orders"].sum() / tot),
            "q_lots": float(g["q_lots"].sum() / tot)}


def do_report(as_json: bool) -> int:
    sp = specs()
    d = pd.read_csv(FIX)
    P("D507 -- the quoted spread on bbo-1m, all acquired roots, 2025-09-11 .. 2026-09-10\n")
    P("  SESSION AVERAGE vs THE EXECUTION INSTANTS (the open of h10..h15, where the arm trades)")
    P("     root  minutes   mean tk  median   P1     P2   P3+   | exec: min  mean tk    P1"
      "   | q lots")
    rows = {}
    for r in sorted(d["root"].unique()):
        g = d[d["root"] == r]
        allh = census(g)
        ex = census(g[(g["is_open"] == 1) & g["hour"].isin(EXEC_HOURS)])
        if not allh:
            continue
        rows[r] = {"all_session": allh, "execution_instants": ex,
                   "tick_points": sp[r]["tick_points"],
                   "tick_usd_full": sp[r]["tick_usd"]}
        P(f"     {r:>4}{allh['minutes']:>9,}{allh['mean_spread_ticks']:>10.3f}"
          f"{allh['median_spread_ticks']:>8.0f}{allh['P1']:>7.3f}{allh['P2']:>7.3f}"
          f"{allh['P3plus']:>6.3f}   |{ex.get('minutes', 0):>10,}"
          f"{ex.get('mean_spread_ticks', float('nan')):>9.3f}"
          f"{ex.get('P1', float('nan')):>7.3f}   |{allh['q_lots']:>8.0f}")

    P("\n  MICRO vs PARENT -- the arm trades the micro and every prior net figure used the "
      "parent's\n     pair        parent mean   micro mean   ratio   parent exec   micro exec")
    pairs = {}
    for micro, parent in PARENT_OF.items():
        if micro in rows and parent in rows:
            pm = rows[parent]["all_session"]["mean_spread_ticks"]
            mm = rows[micro]["all_session"]["mean_spread_ticks"]
            pe = rows[parent]["execution_instants"].get("mean_spread_ticks", float("nan"))
            me = rows[micro]["execution_instants"].get("mean_spread_ticks", float("nan"))
            pairs[f"{micro}/{parent}"] = {"parent_mean": pm, "micro_mean": mm,
                                          "ratio": mm / pm if pm else float("nan"),
                                          "parent_exec": pe, "micro_exec": me}
            P(f"     {micro:>4}/{parent:<4}{pm:>13.3f}{mm:>13.3f}{mm / pm:>8.2f}"
              f"{pe:>14.3f}{me:>13.3f}")

    # ---- what it does to D506's cells, computed rather than asserted
    recost = {}
    d506 = REPO / "data" / "d506_macd_breadth.json"
    if d506.exists():
        a6 = json.loads(d506.read_text(encoding="utf-8"))
        P("\n  RE-COSTING D506's CELLS AT THE MEASURED EXECUTION-INSTANT SPREAD")
        P("     root  sized   gross tk  assumed cost   MEASURED cost   net tk assumed"
          "   net tk MEASURED   verdict")
        for r, c in sorted(a6["primary"].items()):
            sized = c["sized_as"]
            src = sized if sized in rows else r          # the micro's own book where we have it
            ex = rows.get(src, {}).get("execution_instants", {})
            sp_meas = ex.get("mean_spread_ticks")
            if sp_meas is None:
                continue
            comm_tk = c["cost_ticks"] - 1.0               # the 1.00 crossing that was assumed
            new_cost = comm_tk + sp_meas
            g = c["gross"]["mean_ticks_per_trade"]
            old_net = c["net"]["mean_ticks_per_trade"]
            new_net = g - new_cost
            recost[r] = {"sized_as": sized, "spread_source": src,
                         "measured_spread_ticks": sp_meas,
                         "assumed_cost_ticks": c["cost_ticks"], "measured_cost_ticks": new_cost,
                         "gross_ticks_per_trade": g, "net_assumed": old_net,
                         "net_measured": new_net, "tick_usd": c["tick_usd"],
                         "net_measured_usd": new_net * c["tick_usd"],
                         "sign_flips": bool((old_net > 0) != (new_net > 0))}
            flag = ("  SIGN FLIPS" if (old_net > 0) != (new_net > 0)
                    else ("  still +" if new_net > 0 else ""))
            P(f"     {r:>4}{sized:>7}{g:>11.3f}{c['cost_ticks']:>14.3f}{new_cost:>16.3f}"
              f"{old_net:>16.3f}{new_net:>17.3f}{flag}")
        flips = [r for r, v in recost.items() if v["sign_flips"]]
        pos = [r for r, v in recost.items() if v["net_measured"] > 0]
        P(f"\n     net POSITIVE after measuring: {sorted(pos)}")
        P(f"     SIGN FLIPS caused by the measurement: {sorted(flips)}")

    art = {"purpose": "D507: the quoted spread on bbo-1m for every acquired root, including the "
                      "micros the prop arm actually trades, and conditioned on the execution "
                      "instants. NO RETURN READ. Nothing admitted.",
           "window": [DAY0, DAY1], "exec_hours": list(EXEC_HOURS),
           "cost_convention": "cost_ticks = commission/tick_usd + quoted spread in ticks; a "
                              "round trip crosses once in and once out, which is one full "
                              "spread, matching D471's 1.009 on ES",
           "per_root": rows, "micro_vs_parent": pairs, "d506_recost": recost,
           "limitations": [
               "the window is 2025-09-11 .. 2026-09-10, ONE YEAR, and every study it re-costs "
               "runs on 2016-2023 or 2016-2026; a tick is fixed in price terms so as a "
               "contract's price rose the same tick became a smaller share of the move, which "
               "makes a recent spread OPTIMISTIC when applied to an older window",
               "the quoted spread is a FLOOR on the real cost: queue position, partial fills "
               "and slippage on a flip sit on top of it",
               "MGC, MCL and M6E were not acquired, so GC, CL and 6E keep a full-contract "
               "proxy and are flagged",
               "front-month determination is D467/D506's volume rule, reused; the micros "
               "inherit their parent's expiry"]}
    OUT.write_text(json.dumps(art, indent=2, default=float), encoding="utf-8")
    P(f"\n  wrote {OUT.relative_to(REPO)}")
    if as_json:
        P(json.dumps(art, indent=2, default=float))
    return 0


# ---------------------------------------------------------------------------- self-test

def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:60} {detail}")
        if not cond:
            fails.append(label)

    chk("the micro symbol is the parent's month and year with the prefix swapped",
        micro_symbol("ESZ5", "MES") == "MESZ5"
        and micro_symbol("NQH26", "MNQ") == "MNQH26",
        f"ESZ5->{micro_symbol('ESZ5', 'MES')}, NQH26->{micro_symbol('NQH26', 'MNQ')}")
    try:
        micro_symbol("ESZ5-ESH6", "MES")
        raised = False
    except GateError:
        raised = True
    chk("[X] a calendar spread is NOT an outright and raises", raised)
    chk("[X] and the swap does not silently keep the parent prefix",
        micro_symbol("ESZ5", "MES") != "ESZ5")

    chk("the outright regex takes 1-2 digit years and rejects spreads",
        bool(SYM.match("ESZ5")) and bool(SYM.match("MNQH26")) and bool(SYM.match("SR3M6"))
        and not SYM.match("ESZ5-ESH6") and not SYM.match("ESZ5 C5000"))

    # --- the census arithmetic, on a hand-built histogram ----------------------------------
    g = pd.DataFrame({"root": "X", "day": "d", "hour": 10, "is_open": 1,
                      "spread_ticks": [1, 2, 3], "n": [70, 20, 10],
                      "q_orders": [700, 100, 20], "q_lots": [7000, 800, 100]})
    c = census(g)
    chk("P1/P2/P3+ are the histogram's shares and sum to 1",
        abs(c["P1"] - 0.7) < 1e-12 and abs(c["P2"] - 0.2) < 1e-12
        and abs(c["P3plus"] - 0.1) < 1e-12
        and abs(c["P1"] + c["P2"] + c["P3plus"] - 1.0) < 1e-12)
    chk("the mean is size-weighted, not a mean of the distinct widths",
        abs(c["mean_spread_ticks"] - 1.4) < 1e-12,
        f"{c['mean_spread_ticks']:.4f} (a naive mean of 1,2,3 would be 2.0)")
    chk("the median is the 50th-percentile WIDTH",
        c["median_spread_ticks"] == 1.0, f"{c['median_spread_ticks']}")
    chk("[X] shifting the mass changes the mean, so it is not a constant",
        abs(census(pd.DataFrame({**{k: g[k] for k in g.columns if k != 'n'},
                                 "n": [10, 20, 70]}))["mean_spread_ticks"] - 2.6) < 1e-12)

    # --- the cost convention, against D471's measured ES figure ----------------------------
    sp = specs()
    chk("every root has a tick in PRICE units, which is all the census needs",
        all(sp[r]["tick_points"] > 0 for r in ROOTS),
        f"{sum(1 for r in ROOTS if sp[r]['tick_points'] > 0)} of {len(ROOTS)}")
    chk("a MICRO shares its parent's tick in price units, which is why the spread in TICKS "
        "is comparable between them",
        all(abs(sp[m]["tick_points"] - sp[p]["tick_points"]) < 1e-15
            for m, p in PARENT_OF.items()),
        ", ".join(f"{m}={sp[m]['tick_points']:g}/{p}={sp[p]['tick_points']:g}"
                  for m, p in PARENT_OF.items()))
    n_usd = sum(1 for r in ROOTS if sp[r]["tick_usd"])
    chk("and a verified tick VALUE exists for most roots, from the breadth meta not the probe",
        n_usd >= 36, f"{n_usd} of {len(ROOTS)} have one")
    es_cost_assumed = 3.0 / sp["MES"]["tick_usd"] + 1.009
    es_cost_at_112 = 3.0 / sp["MES"]["tick_usd"] + 1.120
    chk("cost_ticks = commission/tick_usd + spread, and D510's ES spread RAISES it",
        es_cost_at_112 > es_cost_assumed,
        f"MES at 1.009 -> {es_cost_assumed:.3f} tk; at D510's measured 1.120 -> "
        f"{es_cost_at_112:.3f} tk")
    nq_assumed = 3.0 / 0.50 + 1.009
    nq_at_nq = 3.0 / 0.50 + 3.768
    chk("[X] and NQ's full-contract 3.768 would raise MNQ's cost by 40% if it applied",
        nq_at_nq / nq_assumed > 1.35,
        f"{nq_assumed:.3f} -> {nq_at_nq:.3f} ticks, +{nq_at_nq / nq_assumed - 1:.0%}")

    # --- the sentinel, which is what actually broke the first build --------------------
    px = np.array([100_000_000, UNDEF_PRICE, 0, 250_000_000], dtype=np.int64)
    chk("[X] the UNDEFINED-price sentinel PASSES a  test, which is the whole bug",
        bool((px > 0)[1]), f"INT64_MAX > 0 is {bool((px > 0)[1])}")
    good = np.logical_and(px > 0, px != UNDEF_PRICE)
    chk("and the corrected filter rejects it while keeping the real prices",
        list(good) == [True, False, False, True], f"{list(good)}")
    chk("a sentinel on ONE side alone makes the spread absurd -- 1.8 billion ticks on MBT",
        abs((UNDEF_PRICE * 1e-9 - 0.1) / 5.0 - 1_844_674_407.27) < 1.0,
        f"{(UNDEF_PRICE * 1e-9 - 0.1) / 5.0:,.0f} ticks at MBT's 5.0-point tick")

    chk(f"{len(ROOTS)} roots declared, {len(PARENT_OF)} micro/parent pairs measurable",
        len(ROOTS) == 41 and len(PARENT_OF) == 5)
    chk("[X] MGC, MCL and M6E are NOT measurable -- they were never acquired",
        not any(m in ROOTS for m in ("MGC", "MCL", "M6E")))

    P(f"\n  {len(fails)} failed: {fails}" if fails else "\n  all checks pass")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.build:
        return build()
    if a.report:
        return do_report(a.json)
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
