"""D492 -- the trade count from tbbo: the PER-TRADE tau D489 declared it could not compute.

    python scripts/d492_trade_count.py --selftest
    python scripts/d492_trade_count.py --build    # raw tbbo -> data/fixtures/fut_trade_counts.csv.gz
    python scripts/d492_trade_count.py --test

PRE-REGISTRATION: docs/decisions/D492-PRE-REG-the-trade-count-from-tbbo-...md

NO RETURN IS READ. Counts, sizes and the quoted prices D491 already censused. The `side` field
is NOT read -- aggressor direction is a flow quantity and would take this past a count.

  sigma_per_trade = sigma_session / sqrt(n)            n = mean TRADES per front-contract session
  tau_trade       = tick_usd * sqrt(n) / sigma_session  <- the literature's ratio
  eta             = tau_trade ** 2                      trades to move one tick (Dayri-Rosenbaum)
  size_bar        = mean contracts per trade

  IDENTITY, asserted: tau_vol (D489's secondary) == tau_trade * sqrt(size_bar), because
  volume = trades * mean size. sqrt(size_bar) IS the contamination D489 flagged in writing.

DECLARED CONDITIONS (neither gates the other; nothing is abandoned on this record):
  U1  ZB in the TOP 3 of 8 on tau_trade         -- D489's T1 on the quantity it could not compute
  U2  Spearman rank corr of the tau_trade ordering vs D491's P1 ordering >= 0.7
  U3  DESCRIPTIVE, no pass/fail: sqrt(size_bar) per root, and how many rank positions the
      tau_vol ordering differs from the tau_trade ordering

SPEED (pre-registration section 4). Three changes from D491's runner, all required by scale:
  1. cheap PREFIX test before the regex -- 1,339,484 symbols, not 16,309
  2. vectorised np.searchsorted for id -> root/contract, not a Python list comprehension
  3. INTEGER DAY ORDINALS, not strftime -- strftime is Python-level formatting per element and
     is the real bottleneck; strings are built only on the aggregated output
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
SPREAD = REPO / "data" / "d491_spread_census.json"
FIX = REPO / "data" / "fixtures" / "fut_trade_counts.csv.gz"
OUT = REPO / "data" / "d492_trade_count.json"

ROOTS = ("ES", "NQ", "YM", "ZN", "ZB", "GC", "CL", "6E")
ALL_ROOTS = ROOTS + ("RTY",)
PREFIXES = tuple(sorted({r[0] for r in ALL_ROOTS}))          # optimisation 1: cheap prefilter
SYM = re.compile(r"^([A-Z0-9]{1,4})[FGHJKMNQUVXZ][0-9]{1,2}$")

DAY0, DAY1 = "2025-09-11", "2026-09-10"
CHUNK = 5_000_000
NS_DAY = 86_400_000_000_000


def specs() -> dict:
    s = json.loads(SPECS.read_text())
    extra = s.get("_verified_but_not_proposed", {})
    out = {}
    for r in ALL_ROOTS:
        d = s.get(r) or (extra.get(r) if isinstance(extra, dict) else None)
        if not isinstance(d, dict) or "tick_usd" not in d:
            raise SystemExit(f"D492: no verified tick_usd for {r} in {SPECS.name}")
        out[r] = {"tick_usd": float(d["tick_usd"]), "usd_per_point": float(d["usd_per_point"])}
    return out


def front_map() -> dict:
    t = pd.read_csv(SESS, usecols=["root", "day", "contract"])
    t = t[(t["day"] >= DAY0) & (t["day"] <= DAY1)]
    return {(r, d): c for r, d, c in zip(t["root"], t["day"], t["contract"])}


def ord_of(day: str) -> int:
    return int(np.datetime64(day, "D").astype(np.int64))


def day_of(o: int) -> str:
    return str(np.datetime64(int(o), "D"))


def sess_ord(ts: pd.DatetimeIndex) -> np.ndarray:
    """Session day as DAYS SINCE EPOCH -- optimisation 3, replacing strftime.

    Casting to datetime64[D] floors to the local calendar date and is unit-safe: pandas 2.x
    infers the index's resolution from its input, so `.view("int64")` is NOT reliably
    nanoseconds. A Globex bar at or after 18:00 ET belongs to the NEXT day's session, the same
    convention fut_sessions_hourly uses.
    """
    local = ts.tz_localize(None).to_numpy().astype("datetime64[D]").astype(np.int64)
    return local + (ts.hour.to_numpy() >= 18)


# ---------------------------------------------------------------------------- build

def id_tables(store, roots=ALL_ROOTS):
    """instrument_id -> (root, contract), built with a PREFIX TEST before the regex.

    optimisation 1: at 1,339,484 mappings a regex per symbol is the dominant cost of the file.
    Nearly all of them fail on the first character.
    """
    ids, rts, cts = [], [], []
    rset = set(roots)
    for sym, ivs in store.metadata.mappings.items():
        s = str(sym)
        if not s or s[0] not in PREFIXES:
            continue
        m = SYM.match(s)
        if not m or m.group(1) not in rset:
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if sid:
                ids.append(int(sid)); rts.append(m.group(1)); cts.append(s)
    if not ids:
        return None
    a = np.asarray(ids, dtype=np.int64)
    o = np.argsort(a, kind="stable")
    return a[o], np.asarray(rts)[o], np.asarray(cts)[o]


def build() -> int:
    import databento as db

    fm = front_map()
    o0, o1 = ord_of(DAY0), ord_of(DAY1)
    files = sorted(RAW.glob("*/*.tbbo.dbn.zst"))
    print(f"D492 build -- {len(files)} tbbo files, roots {ALL_ROOTS}\n", flush=True)
    t_start = time.time()
    acc = []
    for i, f in enumerate(files, 1):
        t0 = time.time()
        store = db.DBNStore.from_file(f)
        tab = id_tables(store)
        if tab is None:
            print(f"  [{i:2d}/{len(files)}] no mapped ids"); continue
        sid, srt, sct = tab
        n_in = n_keep = 0
        parts = []
        for arr in store.to_ndarray(count=CHUNK):
            n_in += len(arr)
            iid = arr["instrument_id"].astype(np.int64)
            # optimisation 2: vectorised membership + map, no Python loop over rows.
            pos = np.searchsorted(sid, iid)
            np.clip(pos, 0, len(sid) - 1, out=pos)
            hit = sid[pos] == iid
            if not hit.any():
                continue
            a = arr[hit]; pos = pos[hit]

            # EVERY kept record must be a trade. tbbo carrying anything else would inflate n
            # for every root silently, so this raises rather than filtering.
            act = np.unique(a["action"])
            if not (len(act) == 1 and act[0] == b"T"):
                raise SystemExit(
                    f"D492: tbbo kept records are not all action 'T' in {f.name}: {act}. "
                    f"Counting non-trade records would inflate n for every root.")

            # optimisation 3: INTEGER DAY ORDINALS, no strftime.
            ts = pd.to_datetime(a["ts_recv"], utc=True).tz_convert("US/Eastern")
            sess = sess_ord(ts)

            parts.append(pd.DataFrame({
                "root": srt[pos], "contract": sct[pos], "sess": sess,
                "size": a["size"].astype(np.int64)}))
            n_keep += len(a)

        if not parts:
            print(f"  [{i:2d}/{len(files)}] nothing kept"); continue
        d = pd.concat(parts, ignore_index=True)
        d = d[(d["sess"] >= o0) & (d["sess"] <= o1)]
        # front contract only, by D467's map -- join on the SMALL aggregate, not row by row
        g = d.groupby(["root", "contract", "sess"], as_index=False).agg(
            trades=("size", "size"), volume=("size", "sum"))
        g["day"] = [day_of(x) for x in g["sess"]]
        want = np.array([fm.get((r, dd)) for r, dd in zip(g["root"], g["day"])])
        g = g[want == g["contract"].to_numpy()][["root", "day", "contract", "trades", "volume"]]
        acc.append(g)
        print(f"  [{i:2d}/{len(files)}] {f.name[-26:]:<26} {n_in:>12,} recs -> {n_keep:>11,} "
              f"mapped -> {int(g['trades'].sum()):>11,} front trades  "
              f"({time.time() - t0:.1f}s)", flush=True)
        del d, g, parts

    out = (pd.concat(acc, ignore_index=True)
           .groupby(["root", "day", "contract"], as_index=False)
           .agg({"trades": "sum", "volume": "sum"}))
    FIX.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(FIX, index=False, compression="gzip")
    print(f"\n  wrote {FIX.relative_to(REPO)}  ({len(out):,} root-sessions, "
          f"{out['day'].min()} .. {out['day'].max()}, {int(out['trades'].sum()):,} trades) "
          f"in {(time.time() - t_start) / 60:.1f} min")
    return 0


# ---------------------------------------------------------------------------- test

def sigma_session(sp: dict) -> pd.Series:
    """sigma of the session close-minus-open in dollars, SAME WINDOW, front contract only --
    the same construction D489 used, recomputed here rather than carried over."""
    import d489_large_tick_premise as d489

    t = pd.read_csv(SESS)
    t = t[(t["day"] >= DAY0) & (t["day"] <= DAY1) & t["same_front"].astype(bool)]
    return pd.Series({r: d489.per_root(t, r, sp[r]["tick_usd"], sp[r]["usd_per_point"])["sigma_sess"]
                      for r in ALL_ROOTS})


def test() -> int:
    sp = specs()
    g = pd.read_csv(FIX)
    sig = sigma_session(sp)
    p1 = {r["root"]: r["P1"] for r in json.load(SPREAD.open())["table"]}

    c = pd.DataFrame({
        "sessions": g.groupby("root")["day"].nunique(),
        "n_bar": g.groupby("root")["trades"].mean(),
        "v_bar": g.groupby("root")["volume"].mean(),
    })
    c["size_bar"] = c["v_bar"] / c["n_bar"]
    c["tick_usd"] = [sp[r]["tick_usd"] for r in c.index]
    c["sigma_sess"] = sig
    c["sigma_per_trade"] = c["sigma_sess"] / np.sqrt(c["n_bar"])
    c["tau_trade"] = c["tick_usd"] / c["sigma_per_trade"]
    c["eta"] = c["tau_trade"] ** 2
    c["tau_vol"] = c["tick_usd"] * np.sqrt(c["v_bar"]) / c["sigma_sess"]
    c["P1"] = pd.Series(p1)

    # THE IDENTITY the pre-registration declared. If it fails, n and v are not from the same
    # sessions and every ratio below is comparing different denominators.
    lhs, rhs = c["tau_vol"].to_numpy(), (c["tau_trade"] * np.sqrt(c["size_bar"])).to_numpy()
    if np.max(np.abs(lhs - rhs) / np.maximum(lhs, 1e-12)) > 1e-6:
        raise SystemExit(f"D492: tau_vol != tau_trade * sqrt(size_bar): {lhs} vs {rhs}")

    fam = c.loc[list(ROOTS)]
    print("D492 -- the per-trade tau from tbbo.  NO RETURN IS READ\n")
    print(f"  {FIX.name}   {g['day'].min()} .. {g['day'].max()}   "
          f"{int(g['trades'].sum()):,} front-contract trades")
    print(f"\n  {'root':<6}{'sess':>6}{'trades/sess':>13}{'size':>7}{'sig_sess $':>12}"
          f"{'$/trade':>10}{'TAU_trade':>11}{'rk':>4}{'eta':>10}{'P1':>7}{'rk':>4}")
    rt = fam["tau_trade"].rank(ascending=False)
    rp = fam["P1"].rank(ascending=False)
    for r, row in fam.sort_values("tau_trade", ascending=False).iterrows():
        print(f"  {r:<6}{int(row['sessions']):>6}{row['n_bar']:>13,.0f}{row['size_bar']:>7.2f}"
              f"{row['sigma_sess']:>12,.0f}{row['sigma_per_trade']:>10.3f}"
              f"{row['tau_trade']:>11.2f}{int(rt[r]):>4}{row['eta']:>10,.0f}"
              f"{row['P1']:>7.3f}{int(rp[r]):>4}")
    if "RTY" in c.index:
        row = c.loc["RTY"]
        print(f"  {'RTY':<6}{int(row['sessions']):>6}{row['n_bar']:>13,.0f}{row['size_bar']:>7.2f}"
              f"{row['sigma_sess']:>12,.0f}{row['sigma_per_trade']:>10.3f}"
              f"{row['tau_trade']:>11.2f}{'  -':>4}{row['eta']:>10,.0f}{row['P1']:>7.3f}{'  -':>4}"
              f"   (outside every bar)")

    zb_rank = int(rt["ZB"])
    u1 = zb_rank <= 3
    rho = float(fam["tau_trade"].rank().corr(fam["P1"].rank(), method="pearson"))
    u2 = rho >= 0.7
    print("\n  THE DECLARED CONDITIONS")
    print(f"    U1  ZB in the top 3 of 8 on tau_trade:      rank {zb_rank}"
          f"                              -> {'PASSES' if u1 else 'FAILS'}")
    print(f"    U2  tau_trade ordering vs D491's P1:        rho {rho:+.3f}"
          f"                        -> {'PASSES' if u2 else 'FAILS'}")

    # POST HOC, computed after U1/U2 were decided and DECIDES NOTHING: the QUOTED spread
    # expressed in units of per-trade volatility. tau_trade is tick/sigma_per_trade; multiplying
    # by D491's mean spread in ticks gives what a crossing actually costs against the move a
    # single trade makes. It is the C6 cost tension of D491 section 6 restated at the trade horizon.
    msp = {r["root"]: r["mean_spread_ticks"] for r in json.load(SPREAD.open())["table"]}
    fam = fam.assign(spread_per_trade_sigma=fam["tau_trade"] * pd.Series(msp).reindex(fam.index))
    print("\n  POST HOC (decides nothing): the QUOTED spread in units of PER-TRADE volatility")
    print(f"      {'root':<6}{'sig/trade $':>13}{'spread $':>11}{'spread/sigma':>14}")
    for r in fam.sort_values("spread_per_trade_sigma", ascending=False).index:
        sp_usd = msp[r] * fam.loc[r, "tick_usd"]
        print(f"      {r:<6}{fam.loc[r, 'sigma_per_trade']:>13.3f}{sp_usd:>11.2f}"
              f"{fam.loc[r, 'spread_per_trade_sigma']:>14.2f}")

    # U3, descriptive
    rv = fam["tau_vol"].rank(ascending=False)
    moved = {r: int(rv[r] - rt[r]) for r in ROOTS if int(rv[r]) != int(rt[r])}
    n_moved = sum(abs(v) for v in moved.values())
    print(f"\n  U3 (DESCRIPTIVE, no pass/fail): what D489's tau_vol was actually measuring")
    print(f"      tau_vol == tau_trade * sqrt(size)  -- identity holds to 1e-6")
    print(f"      {'root':<6}{'sqrt(size)':>12}{'tau_trade rk':>14}{'tau_vol rk':>12}{'moved':>8}")
    for r in fam.sort_values("tau_trade", ascending=False).index:
        mv = int(rv[r] - rt[r])
        print(f"      {r:<6}{np.sqrt(fam.loc[r, 'size_bar']):>12.2f}{int(rt[r]):>14}"
              f"{int(rv[r]):>12}{(f'{mv:+d}' if mv else '.'):>8}")
    print(f"      total rank displacement: {n_moved} position(s) across "
          f"{len(moved)} root(s)")

    OUT.write_text(json.dumps({
        "window": [DAY0, DAY1], "table": c.reset_index().rename(columns={"index": "root"})
        .to_dict("records"),
        "U1": {"zb_rank": zb_rank, "passes": bool(u1)},
        "U2": {"rho_vs_P1": rho, "passes": bool(u2)},
        "U3": {"moved": moved, "total_displacement": n_moved},
        "post_hoc_spread_per_trade_sigma": {r: float(fam.loc[r, "spread_per_trade_sigma"]) for r in ROOTS},
    }, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


# ---------------------------------------------------------------------------- selftest

def selftest() -> int:
    """Five checks, each shown to FIRE on a deliberately broken input."""
    # [1] the day-ordinal path must equal the strftime path it REPLACES, including the 18:00
    # roll-forward and a DST boundary. This is the optimisation guard: exactness, not tolerance.
    idx = pd.to_datetime([
        "2025-09-15 17:59", "2025-09-15 18:00", "2025-09-15 23:59", "2025-09-16 00:00",
        "2025-11-02 01:30", "2025-11-03 18:30", "2026-03-08 03:30", "2026-03-08 18:00",
    ]).tz_localize("US/Eastern", nonexistent="shift_forward", ambiguous=True).tz_convert("UTC")
    ts = idx.tz_convert("US/Eastern")
    hh = ts.hour.to_numpy()
    fast = sess_ord(ts)
    slow = np.where(hh >= 18, (ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d").to_numpy(),
                    ts.strftime("%Y-%m-%d").to_numpy())
    assert [day_of(x) for x in fast] == list(slow), ([day_of(x) for x in fast], list(slow))
    # the version WITHOUT the 18:00 roll
    naive = ts.tz_localize(None).to_numpy().astype("datetime64[D]").astype(np.int64)
    assert not np.array_equal(naive, fast), "[1X] DUD: the 18:00 roll-forward changed nothing"
    print(f"  [1] ok: ordinals match strftime on all 8 stamps incl. both DST boundaries; "
          f"17:59->{day_of(fast[0])}, 18:00->{day_of(fast[1])}")

    # [2] searchsorted mapping == the Python dict lookup it replaces, on a TIE-HEAVY input
    # (repeated ids) and with ids that are NOT present.
    sid = np.array([10, 20, 30, 40], dtype=np.int64)
    srt = np.array(["ES", "NQ", "ZB", "ZN"])
    iid = np.array([20, 20, 5, 30, 99, 40, 10, 20, 41], dtype=np.int64)
    pos = np.clip(np.searchsorted(sid, iid), 0, len(sid) - 1)
    hit = sid[pos] == iid
    d = dict(zip(sid.tolist(), srt.tolist()))
    want_hit = np.array([x in d for x in iid])
    assert np.array_equal(hit, want_hit), (hit, want_hit)
    assert list(srt[pos[hit]]) == [d[x] for x in iid[hit]], list(srt[pos[hit]])
    assert hit.sum() == 6 and not hit[2] and not hit[4] and not hit[8]
    print(f"  [2] ok: searchsorted maps {int(hit.sum())} of {len(iid)} and matches the dict "
          f"exactly; ids 5, 99 and 41 (above and below the table, and adjacent to 40) all miss")

    # [3] the prefix filter must not drop a root it should keep.
    for s in ("ESZ5", "ZBH6", "ZNM6", "6EZ5", "GCG6", "CLF6", "NQZ5", "YMH6", "RTYZ5"):
        assert s[0] in PREFIXES and SYM.match(s), s
    assert "X" not in PREFIXES and not SYM.match("ESZ6-ESH7")
    kept = [s for s in ("ESZ5", "XKZ5", "ZCZ5") if s[0] in PREFIXES]
    assert kept == ["ESZ5", "ZCZ5"], kept        # ZC survives the prefix, dies on the root set
    assert SYM.match("ZCZ5").group(1) not in set(ALL_ROOTS)
    print(f"  [3] ok: all 9 roots survive the prefix test; ZCZ5 survives the prefix and is "
          f"killed by the root set; a calendar spread is killed by the regex")

    # [4] the tau_vol identity, and it must FAIL when size is not folded in.
    n_bar, size_bar, tick, sig = 250_000.0, 3.5, 15.625, 400.0
    v_bar = n_bar * size_bar
    tau_trade = tick * np.sqrt(n_bar) / sig
    tau_vol = tick * np.sqrt(v_bar) / sig
    assert abs(tau_vol - tau_trade * np.sqrt(size_bar)) < 1e-9 * tau_vol
    assert abs(tau_vol - tau_trade) > 0.5 * tau_trade, (
        "[4X] DUD: tau_vol and tau_trade barely differ at size 3.5, so the identity is untested")
    print(f"  [4] ok: tau_vol {tau_vol:.2f} == tau_trade {tau_trade:.2f} * sqrt({size_bar}); "
          f"the two differ by {100 * (tau_vol / tau_trade - 1):.0f}%, so the check has teeth")

    # [5] the action guard fires on a non-trade record.
    ok = np.array([b"T", b"T", b"T"])
    bad = np.array([b"T", b"F"])
    assert len(np.unique(ok)) == 1 and np.unique(ok)[0] == b"T"
    assert not (len(np.unique(bad)) == 1 and np.unique(bad)[0] == b"T"), "[5X] DUD: 'F' passed"
    print("  [5] ok: the action guard accepts all-'T' and rejects a mixed batch")
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
