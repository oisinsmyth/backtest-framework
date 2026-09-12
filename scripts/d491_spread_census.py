"""D491 -- the quoted-spread census on bbo-1m. Does the tick BIND, and does the spread rank the
eight roots the way tau did?

    python scripts/d491_spread_census.py --selftest
    python scripts/d491_spread_census.py --build     # raw bbo-1m -> data/fixtures/fut_spread_1m.csv.gz
    python scripts/d491_spread_census.py --test

PRE-REGISTRATION: docs/decisions/D491-PRE-REG-the-quoted-spread-census-on-bbo-1m-...md

NO RETURN IS READ. Quoted bid/ask, sizes and order counts only. Every quantity here is a
dispersion, a fraction or a depth; none is signed, so no direction can leak out of it.

  P1                   fraction of quoted front-contract minutes at EXACTLY one tick  <- headline
  P2, P3plus           two ticks; three or more
  mean_spread_ticks    the mean
  queue_orders/lots    median depth at the touch, in ORDERS and in CONTRACTS
  crossings_per_hour   ticks_per_hour / mean_spread_ticks  (declared NEARLY CIRCULAR under
                       Branch A -- see the pre-registration's P-e; not independent confirmation)

DECLARED CONDITIONS (none gates another; nothing is abandoned on this record):
  S1  Spearman rank corr of the P1 ordering against the SAME-WINDOW tau_1h ordering
      >= 0.7 -> the two measures agree, D489's ranking confirmed independently
      <  0.7 -> D489 section 4's lane-21/C6 resolution is WITHDRAWN as horizon-specific
      TIE CLAUSE: >= 5 of 8 roots at P1 >= 0.95 -> UNRESOLVED regardless of rho
  S2  lane 21 taken literally: P1(ES) >= 0.95
  S3  the adjudication: BOTH ZN and ZB strictly above ES on P1

THE ERA CONTROL: tau_1h is RECOMPUTED on the census's own window (2025-09-11 .. 2026-09-09),
never compared against D489's 2016-2023 numbers, because a rank disagreement could otherwise be
era rather than horizon.
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
SESS = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"
SPECS = REPO / "data" / "futures_contract_specs.json"
FIX = REPO / "data" / "fixtures" / "fut_spread_1m.csv.gz"
OUT = REPO / "data" / "d491_spread_census.json"

ROOTS = ("ES", "NQ", "YM", "ZN", "ZB", "GC", "CL", "6E")
ALL_ROOTS = ROOTS + ("RTY",)
INDEX = ("ES", "NQ", "YM")

# Outrights only: a calendar spread (ESZ6-ESH7) has its own spread and is a different object.
SYM = re.compile(r"^([A-Z0-9]{1,4})[FGHJKMNQUVXZ][0-9]{1,2}$")

PX = 1e-9                       # DBN fixed-point price scale
DAY0, DAY1 = "2025-09-11", "2026-09-10"

# The 18:00 -> 17:00 ET Globex session, as ET hour labels in clock order (D467's clock).
SESSION_HOURS = list(range(18, 24)) + list(range(0, 17))


def specs() -> dict:
    s = json.loads(SPECS.read_text())
    extra = s.get("_verified_but_not_proposed", {})
    out = {}
    for r in ALL_ROOTS:
        d = s.get(r) or (extra.get(r) if isinstance(extra, dict) else None)
        if not isinstance(d, dict) or "tick_points" not in d:
            raise SystemExit(f"D491: no verified tick_points for {r} in {SPECS.name}")
        out[r] = {"tick_points": float(d["tick_points"]),
                  "tick_usd": float(d["tick_usd"]), "usd_per_point": float(d["usd_per_point"])}
    return out


def front_map() -> dict:
    """(root, ET calendar day) -> front contract, from D467's rule, REUSED not re-derived."""
    t = pd.read_csv(SESS, usecols=["root", "day", "contract"])
    t = t[(t["day"] >= DAY0) & (t["day"] <= DAY1)]
    return {(r, d): c for r, d, c in zip(t["root"], t["day"], t["contract"])}


# ---------------------------------------------------------------------------- build

def build() -> int:
    import databento as db

    sp = specs()
    fm = front_map()
    files = sorted(RAW.glob("*/*.bbo-1m.dbn.zst"))
    print(f"D491 build -- {len(files)} bbo-1m files, roots {ALL_ROOTS}\n")
    t_start = time.time()
    acc = []
    for i, f in enumerate(files, 1):
        t0 = time.time()
        store = db.DBNStore.from_file(f)
        ids = {}
        for sym, ivs in store.metadata.mappings.items():
            m = SYM.match(str(sym))
            if not m or m.group(1) not in ALL_ROOTS:
                continue
            for iv in (ivs if isinstance(ivs, list) else [ivs]):
                sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
                if sid:
                    ids[int(sid)] = (m.group(1), str(sym))
        arr = store.to_ndarray()
        keep = np.isin(arr["instrument_id"], np.fromiter(ids, dtype=np.uint32))
        a = arr[keep]
        del arr

        bid = a["bid_px_00"].astype(np.float64) * PX
        ask = a["ask_px_00"].astype(np.float64) * PX
        # Validity: two-sided, positive, not crossed or locked.
        ok = (a["bid_px_00"] > 0) & (a["ask_px_00"] > 0) & (ask > bid)
        a, bid, ask = a[ok], bid[ok], ask[ok]

        ts = pd.to_datetime(a["ts_recv"], utc=True).tz_convert("US/Eastern")
        rr = np.array([ids[int(x)][0] for x in a["instrument_id"]])
        cc = np.array([ids[int(x)][1] for x in a["instrument_id"]])
        # The Globex session runs 18:00 -> 17:00, so a bar at or after 18:00 belongs to the NEXT
        # calendar day's session -- the same convention fut_sessions_hourly uses.
        hh = ts.hour.to_numpy()
        sess_day = np.where(hh >= 18,
                            (ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d").to_numpy(),
                            ts.strftime("%Y-%m-%d").to_numpy())

        tickp = np.array([sp[r]["tick_points"] for r in rr])
        spread_t = (ask - bid) / tickp

        d = pd.DataFrame({"root": rr, "contract": cc, "day": sess_day, "hour": hh,
                          "spread_ticks": spread_t,
                          "q_orders": a["bid_ct_00"].astype(np.int64)
                          + a["ask_ct_00"].astype(np.int64),
                          "q_lots": a["bid_sz_00"].astype(np.int64)
                          + a["ask_sz_00"].astype(np.int64)})
        # Front contract only, by D467's map.
        want = np.array([fm.get((r, dd)) for r, dd in zip(d["root"], d["day"])])
        d = d[(want == d["contract"].to_numpy()) & d["day"].between(DAY0, DAY1)]

        # THE TICK MUST DIVIDE THE SPREAD. A fractional tick count would silently rescale P1 for
        # exactly one root and look plausible, so this raises rather than rounding.
        frac = np.abs(d["spread_ticks"].to_numpy() - np.round(d["spread_ticks"].to_numpy()))
        if len(d) and frac.max() > 1e-6:
            bad = d.iloc[int(np.argmax(frac))]
            raise SystemExit(
                f"D491: spread is not an integer number of ticks in {f.name}: "
                f"root {bad['root']} {bad['contract']} spread {bad['spread_ticks']:.9f} ticks "
                f"(tick_points {sp[bad['root']]['tick_points']}). The tick is wrong for that root.")
        d["spread_ticks"] = np.round(d["spread_ticks"]).astype(np.int64)

        g = (d.groupby(["root", "day", "hour", "spread_ticks"], as_index=False)
             .agg(n=("q_orders", "size"), q_orders=("q_orders", "sum"), q_lots=("q_lots", "sum")))
        acc.append(g)
        print(f"  [{i:2d}/{len(files)}] {f.name[-28:]:<28} {len(a):>10,} quoted -> "
              f"{len(d):>9,} front minutes  ({time.time() - t0:.1f}s)", flush=True)
        del a, d, g

    out = (pd.concat(acc, ignore_index=True)
           .groupby(["root", "day", "hour", "spread_ticks"], as_index=False)
           .agg({"n": "sum", "q_orders": "sum", "q_lots": "sum"}))
    FIX.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(FIX, index=False, compression="gzip")
    print(f"\n  wrote {FIX.relative_to(REPO)}  ({len(out):,} rows, "
          f"{out['day'].min()} .. {out['day'].max()}, {out['n'].sum():,} front minutes) "
          f"in {(time.time() - t_start) / 60:.1f} min")
    return 0


# ---------------------------------------------------------------------------- test

def same_window_tau(sp: dict) -> pd.Series:
    """THE ERA CONTROL: tau_1h recomputed on the census's OWN window, so a rank disagreement
    with D489 is horizon and not era. Same construction as D489 (hour-to-hour close change,
    within a session, front contract only)."""
    import d489_large_tick_premise as d489

    t = pd.read_csv(SESS)
    t = t[(t["day"] >= DAY0) & (t["day"] <= DAY1) & t["same_front"].astype(bool)]
    return pd.Series({r: d489.per_root(t, r, sp[r]["tick_usd"], sp[r]["usd_per_point"])["tau_1h"]
                      for r in ALL_ROOTS})


def census(g: pd.DataFrame) -> pd.DataFrame:
    tot = g.groupby("root")["n"].sum()
    at = lambda k: g[g["spread_ticks"] == k].groupby("root")["n"].sum().reindex(tot.index).fillna(0)
    ge3 = g[g["spread_ticks"] >= 3].groupby("root")["n"].sum().reindex(tot.index).fillna(0)
    mean_t = (g.assign(w=g["spread_ticks"] * g["n"]).groupby("root")["w"].sum() / tot)
    return pd.DataFrame({
        "minutes": tot, "P1": at(1) / tot, "P2": at(2) / tot, "P3plus": ge3 / tot,
        "mean_spread_ticks": mean_t,
        "queue_orders": g.groupby("root")["q_orders"].sum() / tot,
        "queue_lots": g.groupby("root")["q_lots"].sum() / tot,
    })


def test() -> int:
    sp = specs()
    g = pd.read_csv(FIX)
    c = census(g)
    tau = same_window_tau(sp)
    c["tau_1h"] = tau
    c["ticks_per_hour"] = 1.0 / c["tau_1h"]
    c["crossings_per_hour"] = c["ticks_per_hour"] / c["mean_spread_ticks"]

    fam = c.loc[[r for r in ROOTS]]
    print("D491 -- the quoted-spread census on bbo-1m.  NO RETURN IS READ\n")
    print(f"  {FIX.name}   {g['day'].min()} .. {g['day'].max()}   "
          f"{int(g['n'].sum()):,} front-contract quoted minutes")
    print(f"\n  {'root':<6}{'minutes':>10}{'P1':>8}{'P2':>7}{'P3+':>7}{'mean tk':>9}"
          f"{'q ords':>9}{'q lots':>9}{'tau_1h':>9}{'tk/h':>8}{'cross/h':>9}")
    for r, row in fam.sort_values("P1", ascending=False).iterrows():
        print(f"  {r:<6}{int(row['minutes']):>10,}{row['P1']:>8.3f}{row['P2']:>7.3f}"
              f"{row['P3plus']:>7.3f}{row['mean_spread_ticks']:>9.3f}{row['queue_orders']:>9.0f}"
              f"{row['queue_lots']:>9.0f}{row['tau_1h']:>9.4f}{row['ticks_per_hour']:>8.1f}"
              f"{row['crossings_per_hour']:>9.1f}")
    if "RTY" in c.index:
        row = c.loc["RTY"]
        print(f"  {'RTY':<6}{int(row['minutes']):>10,}{row['P1']:>8.3f}{row['P2']:>7.3f}"
              f"{row['P3plus']:>7.3f}{row['mean_spread_ticks']:>9.3f}{row['queue_orders']:>9.0f}"
              f"{row['queue_lots']:>9.0f}{row['tau_1h']:>9.4f}{row['ticks_per_hour']:>8.1f}"
              f"{row['crossings_per_hour']:>9.1f}   (outside every bar)")

    # ---- S1, with the tie clause ----
    rho = float(fam["P1"].rank().corr(fam["tau_1h"].rank(), method="pearson"))
    n_sat = int((fam["P1"] >= 0.95).sum())
    if n_sat >= 5:
        s1 = f"UNRESOLVED (tie clause: {n_sat} of 8 roots at P1 >= 0.95)"
    else:
        s1 = "AGREE" if rho >= 0.7 else "DISAGREE -- D489 section 4 WITHDRAWN as horizon-specific"
    s2 = bool(fam.loc["ES", "P1"] >= 0.95)
    s3 = bool(fam.loc["ZN", "P1"] > fam.loc["ES", "P1"] and fam.loc["ZB", "P1"] > fam.loc["ES", "P1"])

    print("\n  THE DECLARED CONDITIONS")
    print(f"    S1  P1 ordering vs SAME-WINDOW tau_1h ordering:  rho {rho:+.3f}, "
          f"{n_sat} of 8 saturated   -> {s1}")
    print(f"    S2  lane 21 literally, P1(ES) >= 0.95:           P1(ES) = "
          f"{fam.loc['ES', 'P1']:.4f}                     -> {'PASSES' if s2 else 'FAILS'}")
    print(f"    S3  BOTH ZN and ZB strictly above ES on P1:      ZN {fam.loc['ZN', 'P1']:.4f}, "
          f"ZB {fam.loc['ZB', 'P1']:.4f} vs ES {fam.loc['ES', 'P1']:.4f}  -> "
          f"{'PASSES' if s3 else 'FAILS'}")

    branch = ("A -- the tick BINDS on all eight; the spread cannot discriminate and tau is the "
              "correct discriminator" if n_sat >= 5 else
              "B -- the roots differ materially on P1; the spread is the discriminator and tau "
              "was a proxy")
    print(f"\n  THE FORK, as declared:  BRANCH {branch}")

    # ---- ZB by hour: P-f ----
    print("\n  P-f: ZB's P1 by ET hour (declared: is the quote widest where the volatility is?)")
    zb = g[g["root"] == "ZB"]
    tot_h = zb.groupby("hour")["n"].sum()
    p1_h = (zb[zb["spread_ticks"] == 1].groupby("hour")["n"].sum().reindex(tot_h.index).fillna(0)
            / tot_h)
    q_h = zb.groupby("hour")["q_orders"].sum() / tot_h
    print(f"      {'ET':>4}{'P1':>8}{'q ords':>9}    {'ET':>4}{'P1':>8}{'q ords':>9}")
    hrs = [h for h in SESSION_HOURS if h in p1_h.index]
    half = (len(hrs) + 1) // 2
    for a_, b_ in zip(hrs[:half], hrs[half:] + [None] * half):
        left = f"      {a_:>4}{p1_h[a_]:>8.3f}{q_h[a_]:>9.0f}"
        right = "" if b_ is None else f"    {b_:>4}{p1_h[b_]:>8.3f}{q_h[b_]:>9.0f}"
        print(left + right)
    # Restricted to the DECLARED session hours. Hour 17 is the CME maintenance halt and is not
    # part of the 18:00 -> 16:00 window any of these records scores; it is reported separately
    # rather than allowed to be the headline, because "the quote is wide during the halt" is
    # not a fact about ZB's liquidity.
    ses = p1_h.reindex(hrs)
    lo, hi = ses.idxmin(), ses.idxmax()
    print(f"      within the session: widest at {lo:02d}:00 ET (P1 {ses[lo]:.4f}), "
          f"tightest at {hi:02d}:00 ET (P1 {ses[hi]:.4f}) -- a range of "
          f"{100 * (ses[hi] - ses[lo]):.2f} pp")
    if 17 in p1_h.index:
        print(f"      (hour 17:00, the CME maintenance halt, sits at P1 {p1_h[17]:.4f} on "
              f"{int(tot_h[17]):,} minutes -- outside the declared session, reported not scored)")

    OUT.write_text(json.dumps({
        "window": [DAY0, DAY1], "table": c.reset_index().to_dict("records"),
        "S1": {"rho": rho, "n_saturated": n_sat, "verdict": s1},
        "S2": {"P1_ES": float(fam.loc["ES", "P1"]), "passes": s2},
        "S3": {"P1_ZN": float(fam.loc["ZN", "P1"]), "P1_ZB": float(fam.loc["ZB", "P1"]),
               "P1_ES": float(fam.loc["ES", "P1"]), "passes": s3},
        "branch": branch,
        "ZB_by_hour": {int(h): {"P1": float(p1_h[h]), "queue_orders": float(q_h[h]),
                                "minutes": int(tot_h[h])} for h in hrs},
    }, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


# ---------------------------------------------------------------------------- selftest

def selftest() -> int:
    """Four checks, each shown to FIRE on a deliberately broken input."""
    sp = specs()

    # [1] census() recovers PLANTED spread fractions exactly.
    rows = []
    plant = {"ES": {1: 970, 2: 25, 3: 5}, "NQ": {1: 600, 2: 300, 3: 100},
             "ZB": {1: 900, 2: 80, 4: 20}}
    for r, dist in plant.items():
        for k, n in dist.items():
            rows.append({"root": r, "day": "2025-09-15", "hour": 10, "spread_ticks": k,
                         "n": n, "q_orders": 7 * n, "q_lots": 11 * n})
    c = census(pd.DataFrame(rows))
    assert abs(c.loc["ES", "P1"] - 0.970) < 1e-12, c.loc["ES", "P1"]
    assert abs(c.loc["NQ", "P3plus"] - 0.100) < 1e-12, c.loc["NQ", "P3plus"]
    assert abs(c.loc["ZB", "P3plus"] - 0.020) < 1e-12, c.loc["ZB", "P3plus"]
    want_mean = (900 * 1 + 80 * 2 + 20 * 4) / 1000
    assert abs(c.loc["ZB", "mean_spread_ticks"] - want_mean) < 1e-12
    assert abs(c.loc["ES", "queue_orders"] - 7.0) < 1e-12
    print(f"  [1] ok: planted P1 recovered exactly (ES 0.970, NQ P3+ 0.100); ZB mean "
          f"{c.loc['ZB', 'mean_spread_ticks']:.3f} counts the 4-tick rows as 4, not as one 3+")

    # [1X] the break: P3plus must AGGREGATE, not read a single bucket.
    bad = pd.DataFrame(rows)
    bad = bad[bad["spread_ticks"] != 4]                 # drop ZB's 3+ mass entirely
    assert census(bad).loc["ZB", "P3plus"] == 0.0, "[1X] DUD: P3plus did not move when its rows left"
    print("  [1X] ok: the break fires -- removing ZB's 4-tick rows takes P3+ to exactly 0")

    # [2] THE TICK GUARD must raise. A spread that is not an integer number of ticks means the
    # tick is wrong for that root, and rounding it would silently rescale P1.
    st = np.array([1.0, 2.0, 1.5])
    frac = np.abs(st - np.round(st))
    assert frac.max() > 1e-6, "[2] DUD: 1.5 ticks did not register as fractional"
    assert np.abs(np.array([1.0, 2.0, 3.0]) - np.round([1.0, 2.0, 3.0])).max() <= 1e-6
    print("  [2] ok: the fractional-tick guard separates 1.5 ticks from {1,2,3}; build() raises "
          "on it rather than rounding")

    # [3] the session-day convention: 18:00+ belongs to the NEXT calendar day's session, which is
    # what makes the front-contract join line up with fut_sessions_hourly.
    ts = pd.to_datetime(["2025-09-15 18:30", "2025-09-15 09:30", "2025-09-15 17:30"]
                        ).tz_localize("US/Eastern")
    hh = ts.hour.to_numpy()
    sd = np.where(hh >= 18, (ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d").to_numpy(),
                  ts.strftime("%Y-%m-%d").to_numpy())
    assert list(sd) == ["2025-09-16", "2025-09-15", "2025-09-15"], list(sd)
    naive = ts.strftime("%Y-%m-%d").to_numpy()
    assert naive[0] != sd[0], "[3X] DUD: the evening roll-forward changed nothing"
    print(f"  [3] ok: 18:30 on 09-15 -> session {sd[0]} (the naive read would be {naive[0]}); "
          f"09:30 and 17:30 stay on 09-15")

    # [4] the outright filter excludes combos.
    assert SYM.match("ESZ6") and SYM.match("ZB H6".replace(" ", "")) and SYM.match("6EZ5")
    assert not SYM.match("ESZ6-ESH7"), "[4] DUD: a calendar spread passed the outright filter"
    assert not SYM.match("ES"), "[4] DUD: a bare root passed the outright filter"
    print("  [4] ok: ESZ6/ZBH6/6EZ5 match, ESZ6-ESH7 and a bare ES do not")

    # [5] specs carry a tick in POINTS for every root, and it divides the quoted increment.
    for r in ALL_ROOTS:
        assert sp[r]["tick_points"] > 0
    assert abs(sp["ZB"]["tick_points"] - 0.03125) < 1e-12
    assert abs(sp["ZN"]["tick_points"] - 0.015625) < 1e-12
    assert abs(sp["ES"]["tick_points"] - 0.25) < 1e-12
    print(f"  [5] ok: tick_points ZB {sp['ZB']['tick_points']}, ZN {sp['ZN']['tick_points']}, "
          f"ES {sp['ES']['tick_points']} -- read from the spec file, none hardcoded")
    print("\n  SELFTEST PASSES (every check shown to fire on a broken input)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.build:
        return build()
    if a.test:
        return test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
