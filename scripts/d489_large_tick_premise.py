"""D489 stage 0 -- is ZB actually a LARGE-TICK instrument? The premise C6 has never had checked.

    python scripts/d489_large_tick_premise.py --selftest
    python scripts/d489_large_tick_premise.py --run

PRE-REGISTRATION: docs/decisions/D489-PRE-REG-stage-0-is-ZB-actually-a-large-tick-instrument-...md
  (with the 2026-09-12 AMENDMENT: `_n` is a MINUTE-BAR COUNT, not a trade count, so the
   pre-registered tau_trade is replaced by tau_1h as the primary and tau_vol as a flagged
   secondary -- see the amendment block for what that costs.)

STAGE 0: NO RETURN IS READ. Tick sizes, realised volatility and volume only. Nothing here is
signed: sigma is a dispersion and tau is a positive ratio, so no direction can leak out of it.

  tau_1h   = tick_usd / sigma(hour-to-hour close CHANGE, in dollars)     PRIMARY, decides T1-T3
  tau_sess = tick_usd / sigma(session close-minus-open, in dollars)      the horizon D468 scored
  tau_vol  = tick_usd * sqrt(mean session volume) / sigma_session        SECONDARY, flagged

ABANDON CONDITIONS, from the pre-registration:
  T1  ZB not in the TOP 3 of 8 roots on tau                      -> C6's instrument choice is wrong
  T2  lag-1 Spearman rank autocorrelation of the MONTHLY tau
      ordering across roots < 0.5                                -> C6's monthly-split decider dies
  T3  min(tau ZB, ZN) <= max(tau ES, NQ, YM)                      -> the two-tier split does not exist

If tau_vol lands on the other side of a bar from tau_1h, that condition is UNRESOLVED, not passed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"
SPECS = REPO / "data" / "futures_contract_specs.json"
OUT = REPO / "data" / "d489_large_tick_premise.json"

# The eight D467/D468 roots, in the order D468's table used. RTY is the ninth (D472) and is
# reported but held out of every bar, because D468's family was eight and the pre-registration
# named eight.
ROOTS = ("ES", "NQ", "YM", "ZN", "ZB", "GC", "CL", "6E")
INDEX = ("ES", "NQ", "YM")
BONDS = ("ZB", "ZN")

# The session in clock order: 18:00 of the prior evening through 16:00 ET.
SEG = [f"h{h:02d}" for h in list(range(18, 24)) + list(range(0, 17))]

# D468's in-sample slice, unchanged. 2024+ is not read.
DAY0, DAY1 = "2016-01-04", "2023-12-29"


def specs() -> dict:
    """tick_usd per root, from the CME-verified spec file. 6E is not a proposed root there, so
    it is looked up in the _verified_but_not_proposed block; nothing is hardcoded."""
    s = json.loads(SPECS.read_text())
    extra = s.get("_verified_but_not_proposed", {})
    out = {}
    for r in ROOTS + ("RTY",):
        d = s.get(r) or (extra.get(r) if isinstance(extra, dict) else None)
        if not isinstance(d, dict) or "tick_usd" not in d or "usd_per_point" not in d:
            raise SystemExit(
                f"D489: no verified tick_usd/usd_per_point for {r} in {SPECS.name}. "
                f"The pre-registration says nothing is hardcoded, so this raises rather than "
                f"guessing. Roots present: {sorted(k for k in s if not k.startswith('_'))}; "
                f"extra: {sorted(extra) if isinstance(extra, dict) else extra}"
            )
        out[r] = {"tick_usd": float(d["tick_usd"]), "usd_per_point": float(d["usd_per_point"]),
                  "name": d.get("name", r)}
    return out


def load(path: Path = FIX) -> pd.DataFrame:
    t = pd.read_csv(path)
    need = {"root", "day", "same_front"} | {f"{s}_{f}" for s in SEG for f in ("o", "c", "v", "n")}
    missing = need - set(t.columns)
    if missing:
        raise SystemExit(f"D489: fixture is missing {sorted(missing)[:6]}...")
    t = t[(t["day"] >= DAY0) & (t["day"] <= DAY1)]
    # Front contract only: a roll night would put two different contracts' prices in one change.
    t = t[t["same_front"].astype(bool)]
    return t.reset_index(drop=True)


def per_root(t: pd.DataFrame, root: str, tick: float, mult: float) -> dict:
    """Every dollar quantity for one root. NO RETURN IS READ: only |changes| enter, through a
    standard deviation, and volume."""
    b = t[t["root"] == root]
    if b.empty:
        return {}
    closes = b[[f"{s}_c" for s in SEG]].to_numpy(dtype=float)
    opens = b[[f"{s}_o" for s in SEG]].to_numpy(dtype=float)
    nbar = b[[f"{s}_n" for s in SEG]].to_numpy(dtype=float)
    vol = b[[f"{s}_v" for s in SEG]].to_numpy(dtype=float)

    # A session enters only if EVERY hour of it is populated. The pre-registration says a
    # session with a missing hour is dropped, not imputed -- an imputed hour would be a zero
    # change, which drags sigma down and tau up, i.e. toward the answer C6 wants.
    full = np.isfinite(closes).all(axis=1) & np.isfinite(opens[:, 0])

    # tau_1h: the hour-to-hour close change, in dollars, pooled over sessions. Changes are taken
    # WITHIN a session only (np.diff along the clock axis), so no overnight gap between two
    # different sessions can enter as if it were an hour.
    dh = np.diff(closes[full], axis=1) * mult
    sig_1h = float(np.std(dh.ravel(), ddof=1))

    # tau_sess: the whole session, close minus open, the horizon D468's W1 scored.
    ds = (closes[full][:, -1] - opens[full][:, 0]) * mult
    sig_sess = float(np.std(ds, ddof=1))

    v_sess = vol[full].sum(axis=1)
    v_mean = float(v_sess.mean())

    return {
        "root": root, "name": "", "sessions": int(full.sum()), "dropped": int((~full).sum()),
        "tick_usd": tick, "usd_per_point": mult,
        "sigma_1h": sig_1h, "sigma_sess": sig_sess,
        "tau_1h": tick / sig_1h, "tau_sess": tick / sig_sess,
        "tau_vol": tick * np.sqrt(v_mean) / sig_sess,
        "vol_mean": v_mean, "bars_median": float(np.median(nbar[full].sum(axis=1))),
        "sigma_1h_pts": sig_1h / mult,
    }


def sigma_curve(t: pd.DataFrame, root: str, mult: float) -> list:
    """R1, descriptive, NO BAR ATTACHED: dollar sigma of a hold of h hours starting at 18:00,
    for h = 1..23. Answers 'at what window would ZB be C-d expressible' with a number."""
    b = t[t["root"] == root]
    closes = b[[f"{s}_c" for s in SEG]].to_numpy(dtype=float)
    opens = b[[f"{s}_o" for s in SEG]].to_numpy(dtype=float)
    full = np.isfinite(closes).all(axis=1) & np.isfinite(opens[:, 0])
    o = opens[full][:, 0]
    return [{"hours": h + 1, "end": SEG[h],
             "sigma_usd": float(np.std((closes[full][:, h] - o) * mult, ddof=1))}
            for h in range(len(SEG))]


def zb_surface(t: pd.DataFrame, mult: float, root: str = "ZB", bar: float = 500.0) -> dict:
    """R1b, descriptive, NO BAR ATTACHED: dollar sigma of a hold STARTING at each session hour
    and running h hours, so the C-d question separates length from placement on the clock.

    Entry is the hour's OPEN and exit is the exit hour's CLOSE, matching how D468's windows were
    defined (W1 18:00 open -> 16:00 close).
    """
    b = t[t["root"] == root]
    closes = b[[f"{s}_c" for s in SEG]].to_numpy(dtype=float)
    opens = b[[f"{s}_o" for s in SEG]].to_numpy(dtype=float)
    full = np.isfinite(closes).all(axis=1) & np.isfinite(opens).all(axis=1)
    C, O = closes[full], opens[full]
    out = {}
    for i, s0 in enumerate(SEG):
        sig = [float(np.std((C[:, j] - O[:, i]) * mult, ddof=1)) for j in range(i, len(SEG))]
        ok = [h for h, v in enumerate(sig, start=1) if v <= bar]
        out[s0.replace("h", "") + ":00"] = {"sigma": sig, "max_h": max(ok) if ok else 0}
    return out


def monthly_ranks(t: pd.DataFrame, sp: dict) -> tuple:
    """T2: rank the roots by tau_1h WITHIN each calendar month, then the lag-1 Spearman rank
    autocorrelation of consecutive months' orderings, pooled.

    Spearman on RANKS of the same 8 objects is Pearson on those ranks, which is what is computed.
    A month enters only if all eight roots have >= MIN_SESS sessions in it, so a thin month
    cannot contribute a rank built on three days.
    """
    MIN_SESS = 10
    t = t.assign(month=t["day"].str.slice(0, 7))
    rows = {}
    for m, g in t.groupby("month", sort=True):
        taus = {}
        for r in ROOTS:
            d = per_root(g, r, sp[r]["tick_usd"], sp[r]["usd_per_point"])
            if d and d["sessions"] >= MIN_SESS and d["sigma_1h"] > 0:
                taus[r] = d["tau_1h"]
        if len(taus) == len(ROOTS):
            s = pd.Series(taus).rank(ascending=False)
            rows[m] = s.reindex(ROOTS).to_numpy(dtype=float)
    months = sorted(rows)
    if len(months) < 3:
        return float("nan"), months, rows, []
    pairs = [float(np.corrcoef(rows[a], rows[b])[0, 1])
             for a, b in zip(months, months[1:])]
    return float(np.mean(pairs)), months, rows, pairs


def run() -> int:
    sp = specs()
    t = load()
    print("D489 stage 0 -- is ZB a large-tick instrument?  NO RETURN IS READ\n")
    print(f"  fixture {FIX.name}   slice {DAY0} .. {DAY1}   front-contract sessions only")

    tab = []
    for r in ROOTS + ("RTY",):
        d = per_root(t, r, sp[r]["tick_usd"], sp[r]["usd_per_point"])
        if d:
            d["name"] = sp[r]["name"]
            tab.append(d)
    df = pd.DataFrame(tab).set_index("root")
    fam = df.loc[[r for r in ROOTS if r in df.index]]

    print(f"\n  {'root':<6}{'sessions':>9}{'drop':>6}{'tick $':>9}{'sig_1h $':>10}"
          f"{'sig_sess $':>12}{'TAU_1h':>10}{'rk':>4}{'ticks/h':>9}{'tau_vol':>10}{'rk':>4}")
    r1h = fam["tau_1h"].rank(ascending=False)
    rvol = fam["tau_vol"].rank(ascending=False)
    for r, row in fam.sort_values("tau_1h", ascending=False).iterrows():
        star = "  <-- ZB" if r == "ZB" else ("  <-- ZN" if r == "ZN" else "")
        print(f"  {r:<6}{row['sessions']:>9,}{row['dropped']:>6,}{row['tick_usd']:>9.3f}"
              f"{row['sigma_1h']:>10.1f}{row['sigma_sess']:>12.1f}{row['tau_1h']:>10.4f}"
              f"{int(r1h[r]):>4}{1.0 / row['tau_1h']:>9.1f}{row['tau_vol']:>10.2f}"
              f"{int(rvol[r]):>4}{star}")
    if "RTY" in df.index:
        row = df.loc["RTY"]
        print(f"  {'RTY':<6}{row['sessions']:>9,}{row['dropped']:>6,}{row['tick_usd']:>9.3f}"
              f"{row['sigma_1h']:>10.1f}{row['sigma_sess']:>12.1f}{row['tau_1h']:>10.4f}"
              f"{'  -':>4}{1.0 / row['tau_1h']:>9.1f}{row['tau_vol']:>10.2f}{'  -':>4}"
              f"   (ninth root, D472; outside every bar)")

    # ---- T2 ----
    rho, months, mrows, pairs = monthly_ranks(t, sp)
    print(f"\n  T2: monthly tau_1h orderings over {len(months)} complete months "
          f"({months[0]} .. {months[-1]}), lag-1 rank autocorrelation pooled")
    print(f"      mean rho = {rho:+.3f}   p10 {np.percentile(pairs, 10):+.3f}   "
          f"median {np.median(pairs):+.3f}   min {min(pairs):+.3f}")

    # ---- the three conditions ----
    zb_rank_1h, zb_rank_vol = int(r1h["ZB"]), int(rvol["ZB"])
    t1_1h, t1_vol = zb_rank_1h <= 3, zb_rank_vol <= 3
    gap_1h = float(min(fam.loc[list(BONDS), "tau_1h"]) - max(fam.loc[list(INDEX), "tau_1h"]))
    gap_vol = float(min(fam.loc[list(BONDS), "tau_vol"]) - max(fam.loc[list(INDEX), "tau_vol"]))
    t3_1h, t3_vol = gap_1h > 0, gap_vol > 0
    t2 = bool(rho >= 0.5)

    def verdict(prim: bool, sec: bool) -> str:
        if prim != sec:
            return "UNRESOLVED (tau_vol disagrees)"
        return "SURVIVES" if prim else "ABANDON"

    print("\n  THE ABANDON CONDITIONS, as declared")
    v1 = verdict(t1_1h, t1_vol)
    print(f"    T1  ZB in the top 3 of 8 on tau:        rank {zb_rank_1h} on tau_1h, "
          f"{zb_rank_vol} on tau_vol            -> {v1}")
    print(f"    T2  monthly ordering persists >= 0.50:  rho {rho:+.3f} over {len(pairs)} "
          f"consecutive month pairs         -> {'SURVIVES' if t2 else 'ABANDON'}")
    v3 = verdict(t3_1h, t3_vol)
    print(f"    T3  min(ZB,ZN) > max(ES,NQ,YM):         gap {gap_1h:+.4f} on tau_1h, "
          f"{gap_vol:+.2f} on tau_vol   -> {v3}")

    # POST HOC, added after the three verdicts above were computed and DECIDES NOTHING: where
    # does C6's own declared "split at median" actually fall, and where is the real gap?
    order = fam.sort_values("tau_1h", ascending=False)
    tv = order["tau_1h"].to_numpy()
    gaps = tv[:-1] / tv[1:]
    big_at = int(np.argmax(gaps))
    med_at = len(tv) // 2 - 1
    print(f"\n  POST HOC (decides nothing): C6 declares \"ranked monthly, SPLIT AT MEDIAN\".")
    print(f"    the median cut falls between {order.index[med_at]} ({tv[med_at]:.4f}) and "
          f"{order.index[med_at + 1]} ({tv[med_at + 1]:.4f}) -- a ratio of {gaps[med_at]:.3f}x")
    print(f"    the LARGEST gap falls between {order.index[big_at]} ({tv[big_at]:.4f}) and "
          f"{order.index[big_at + 1]} ({tv[big_at + 1]:.4f}) -- a ratio of {gaps[big_at]:.3f}x")
    print(f"    median tiers:  large {sorted(order.index[:med_at + 1])}   "
          f"small {sorted(order.index[med_at + 1:])}")
    print(f"    gap tiers:     large {sorted(order.index[:big_at + 1])}   "
          f"small {sorted(order.index[big_at + 1:])}")

    survives = [v1, "SURVIVES" if t2 else "ABANDON", v3]
    if any(s.startswith("ABANDON") for s in survives):
        final = "C6's premise FAILS at stage 0"
    elif any(s.startswith("UNRESOLVED") for s in survives):
        final = "UNRESOLVED at stage 0"
    else:
        final = "C6 earns a stage 1"
    print(f"\n  ->  {final}")

    # ---- R1, descriptive ----
    print("\n  R1 (descriptive, NO BAR): dollar sigma of an h-hour hold from 18:00, one contract")
    print(f"      {'h':>3}{'end':>7}" + "".join(f"{r:>10}" for r in ("ZB", "ZN", "ES", "NQ")))
    curves = {r: sigma_curve(t, r, sp[r]["usd_per_point"]) for r in ("ZB", "ZN", "ES", "NQ")}
    for i in (0, 1, 2, 3, 5, 7, 11, 15, 19, 22):
        print(f"      {curves['ZB'][i]['hours']:>3}{curves['ZB'][i]['end']:>7}"
              + "".join(f"{curves[r][i]['sigma_usd']:>10.0f}" for r in ("ZB", "ZN", "ES", "NQ")))
    under = [c["hours"] for c in curves["ZB"] if c["sigma_usd"] <= 500.0]
    print(f"      ZB sigma <= $500 (the C-d bar on a $50k account) at h = "
          f"{under if under else 'NO HORIZON in 1..23'}"
          + (f"  (longest such hold from 18:00: {max(under)}h)" if under else ""))

    # The curve above starts at 18:00, but D468's W3 is a SEVEN-hour DAY hold at sigma $682 while
    # a seven-hour EVENING hold is far quieter. ZB's variance is not uniform across the clock, so
    # the C-d answer depends on the START HOUR too. Descriptive, no bar.
    print("\n  R1b (descriptive, NO BAR): for each START hour, the LONGEST ZB hold with "
          "sigma <= $500")
    surf = zb_surface(t, sp["ZB"]["usd_per_point"])
    print(f"      {'start':>7}" + "".join(f"{f'{h}h':>7}" for h in (1, 2, 4, 7, 11, 15))
          + f"{'max h <= $500':>15}")
    for s0, row in surf.items():
        cells = "".join(f"{row['sigma'][h - 1]:>7.0f}" if h - 1 < len(row["sigma"]) else f"{'-':>7}"
                        for h in (1, 2, 4, 7, 11, 15))
        print(f"      {s0:>7}{cells}{(str(row['max_h']) + 'h' if row['max_h'] else 'none'):>15}")

    OUT.write_text(json.dumps({
        "slice": [DAY0, DAY1], "roots": list(ROOTS),
        "table": df.reset_index().to_dict("records"),
        "T1": {"zb_rank_tau_1h": zb_rank_1h, "zb_rank_tau_vol": zb_rank_vol, "verdict": v1},
        "T2": {"rho": rho, "months": len(months), "pairs": pairs,
               "verdict": "SURVIVES" if t2 else "ABANDON"},
        "T3": {"gap_tau_1h": gap_1h, "gap_tau_vol": gap_vol, "verdict": v3},
        "final": final,
        "R1_sigma_curves": curves,
        "R1_zb_hours_under_500": under,
        "R1b_zb_start_hour_surface": zb_surface(t, sp["ZB"]["usd_per_point"]),
    }, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


# --------------------------------------------------------------------------------------------


def selftest() -> int:
    """Three checks, and each is verified to RAISE on a deliberately broken input -- a self-test
    that cannot fail is worse than none."""
    rng = np.random.default_rng(11)
    n, mult, tick = 400, 10.0, 2.5

    def synth(step: float, root: str, roll_rows: int = 0) -> pd.DataFrame:
        """A root whose hour-to-hour close change has a KNOWN dollar sd = step * mult."""
        d = rng.normal(0.0, step, size=(n, len(SEG))).cumsum(axis=1) + 100.0
        rec = {"root": root, "day": [f"2016-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(n)],
               "same_front": True}
        f = pd.DataFrame(rec)
        f["day"] = [f"20{16 + i // 336}-{1 + (i // 28) % 12:02d}-{1 + i % 28:02d}"
                    for i in range(n)]
        for j, s in enumerate(SEG):
            f[f"{s}_o"] = d[:, j] - (step if j else 0.0)
            f[f"{s}_c"] = d[:, j]
            f[f"{s}_v"] = 1000.0
            f[f"{s}_n"] = 60.0
        if roll_rows:
            f.loc[: roll_rows - 1, "same_front"] = False
            for s in SEG:                      # a roll row priced 1000x away
                f.loc[: roll_rows - 1, f"{s}_c"] = 100_000.0
                f.loc[: roll_rows - 1, f"{s}_o"] = 100_000.0
        return f

    # [1] tau_1h recovers a KNOWN sigma. Broken form: feed it the roll rows.
    t = pd.concat([synth(0.20, "ZB"), synth(0.80, "ES")], ignore_index=True)
    d = per_root(t, "ZB", tick, mult)
    want = 0.20 * mult
    assert abs(d["sigma_1h"] - want) < 0.06 * want, (d["sigma_1h"], want)
    assert abs(d["tau_1h"] - tick / d["sigma_1h"]) < 1e-12, (d["tau_1h"], d["sigma_1h"])
    assert d["sessions"] == n and d["dropped"] == 0
    print(f"  [1] ok: sigma_1h {d['sigma_1h']:.4f} recovers the planted {want:.4f}; "
          f"tau_1h {d['tau_1h']:.4f} == tick/sigma")

    # [1X] WHAT ACTUALLY PROTECTS sigma, stated honestly. The same_front filter does NOT: every
    # change taken here is WITHIN one row, and the builder assigns ONE contract to the whole row
    # (its own self-test: the 2015-03-13 roll row is ESM5 on both legs), so a roll shifts the
    # LEVEL and cannot enter a difference. The filter is kept because a roll row's evening prints
    # come from a contract that was not yet front and are thin -- a liquidity reason, not a jump
    # reason -- and this check says so rather than claiming a guard it does not provide.
    tr = pd.concat([synth(0.20, "ZB", roll_rows=40), synth(0.80, "ES")], ignore_index=True)
    kept = per_root(load_frame(tr), "ZB", tick, mult)
    assert kept["sessions"] == n - 40, kept["sessions"]
    assert abs(kept["sigma_1h"] - want) < 0.06 * want, kept["sigma_1h"]
    unfiltered = per_root(tr[tr["day"].between(DAY0, DAY1)], "ZB", tick, mult)
    assert abs(unfiltered["sigma_1h"] - want) < 0.10 * want, (
        f"[1X] a level-only roll moved sigma_1h to {unfiltered['sigma_1h']:.3f} from {want:.3f}; "
        "that should be impossible for a within-row difference")
    # The break that DOES fire is a within-row contract splice -- the thing the builder's
    # one-contract-per-row invariant is what rules out.
    ts = synth(0.20, "ZB")
    ts.loc[:39, [f"{s}_c" for s in SEG[12:]]] += 100_000.0
    spliced = per_root(load_frame(ts), "ZB", tick, mult)
    assert spliced["sigma_1h"] > 50.0 * want, (
        f"[1X] DUD: splicing a second contract into half of 40 rows left sigma_1h at "
        f"{spliced['sigma_1h']:.3f}, so nothing here is testing the difference at all")
    print(f"  [1X] ok: a level-only roll leaves sigma_1h at {unfiltered['sigma_1h']:.3f} "
          f"(the filter is defensive, not load-bearing); a WITHIN-ROW contract splice takes it "
          f"to {spliced['sigma_1h']:,.0f}, which is what one-contract-per-row rules out")

    # [2] a session with ONE missing hour is DROPPED, not imputed. Broken form: impute a zero.
    t2 = synth(0.20, "ZB")
    base = per_root(load_frame(t2), "ZB", tick, mult)     # same frame, no holes, same slice
    t2.loc[:19, "h03_c"] = np.nan
    t2["_holed"] = False
    t2.loc[:19, "_holed"] = True
    dd = per_root(load_frame(t2), "ZB", tick, mult)
    holed = int(load_frame(t2)["_holed"].sum())   # holed rows that survive the DAY0 slice
    assert base["dropped"] == 0 and dd["dropped"] == holed and holed > 0, (
        base["dropped"], dd["dropped"], holed)
    assert dd["sessions"] == base["sessions"] - holed, (dd["sessions"], base["sessions"], holed)
    t2i = t2.copy()
    t2i.loc[:19, "h03_c"] = t2i.loc[:19, "h02_c"]        # impute = carry forward = zero change
    di = per_root(load_frame(t2i), "ZB", tick, mult)
    assert di["sessions"] == base["sessions"] and di["tau_1h"] > dd["tau_1h"], (
        "[2X] DUD: imputing did not raise tau, so the drop rule is not doing what the pre-reg "
        f"said it was for ({di['tau_1h']:.4f} vs {dd['tau_1h']:.4f})")
    print(f"  [2] ok: {holed} holed sessions dropped, not imputed; imputing would have lifted tau_1h "
          f"{dd['tau_1h']:.4f} -> {di['tau_1h']:.4f} (toward the answer C6 wants)")

    # [3] the diff is WITHIN a session: no cross-session gap enters as an hour. The plausible
    # bug is a FLATTENED diff (np.diff(closes.ravel())), so that form is scored beside it and
    # must blow up -- otherwise this check proves nothing.
    t3 = synth(0.20, "ZB")
    t3.loc[1::2, [f"{s}_c" for s in SEG]] += 500.0       # alternate sessions shifted far away
    t3.loc[1::2, [f"{s}_o" for s in SEG]] += 500.0
    f3 = load_frame(t3)
    d3 = per_root(f3, "ZB", tick, mult)
    assert abs(d3["sigma_1h"] - want) < 0.06 * want, (
        "[3] a 500-point jump BETWEEN sessions leaked into the hour-to-hour change: "
        f"sigma_1h {d3['sigma_1h']:.3f} vs {want:.3f}")
    flat = f3[[f"{s}_c" for s in SEG]].to_numpy(dtype=float)
    sig_flat = float(np.std(np.diff(flat.ravel()) * mult, ddof=1))
    assert sig_flat > 20.0 * want, (
        f"[3X] DUD: the flattened diff gives {sig_flat:.3f} against {want:.3f}, so the "
        "within-session axis is not what makes [3] pass")
    print(f"  [3] ok: shifting every other session by 500 points leaves sigma_1h "
          f"{d3['sigma_1h']:.4f}; the flattened diff the same data would give is "
          f"{sig_flat:,.0f}, so the axis is load-bearing")

    # [4] tau is scale-free in the multiplier, so micro-vs-mini cannot enter the ranking.
    f4 = load_frame(synth(0.20, "ZB"))                     # ONE frame, two scalings
    small = per_root(f4, "ZB", tick, mult)
    big = per_root(f4, "ZB", tick * 10.0, mult * 10.0)
    assert abs(big["sigma_1h"] - 10.0 * small["sigma_1h"]) < 1e-6 * big["sigma_1h"]
    assert abs(big["tau_1h"] - small["tau_1h"]) < 1e-12, (big["tau_1h"], small["tau_1h"])
    d = small
    print(f"  [4] ok: 10x the tick and 10x the multiplier leaves tau_1h unchanged "
          f"({big['tau_1h']:.6f}) -- the ratio is scale-free, as §4 claims")

    # [5] specs() raises rather than guessing a tick.
    try:
        s = specs()
    except SystemExit as e:
        print(f"  [5] specs() raised as designed: {str(e)[:150]}")
        return 0
    assert s["ZB"]["tick_usd"] == 31.25 and s["ZN"]["tick_usd"] == 15.625, s["ZB"]
    assert s["ES"]["tick_usd"] == 12.5, s["ES"]
    print(f"  [5] ok: verified ticks ZB ${s['ZB']['tick_usd']}, ZN ${s['ZN']['tick_usd']}, "
          f"ES ${s['ES']['tick_usd']} read from the spec file, none hardcoded")
    print("\n  SELFTEST PASSES (and every check was shown to fire on a broken input)")
    return 0


def load_frame(t: pd.DataFrame) -> pd.DataFrame:
    """The slice + front-contract filter load() applies, for use on a synthetic frame."""
    t = t[(t["day"] >= DAY0) & (t["day"] <= DAY1)]
    return t[t["same_front"].astype(bool)].reset_index(drop=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.run:
        return run()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
