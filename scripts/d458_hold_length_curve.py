"""D458 -- the hold-length curve: both 4% bounds, drawn against each other at last.

    python scripts/d458_hold_length_curve.py --build    # DBN -> data/fixtures/es_hold_ladder.csv.gz
    python scripts/d458_hold_length_curve.py --test     # the curve

--build needs the system interpreter (databento); --test runs under either.

THE QUESTION, AND IT HAS TWO SOURCES THAT NEVER MET
----------------------------------------------------
The prop research's shape constraint: "THE SCISSORS CLOSE ON LONG WINDOWS, NOT ON SMALL EDGES."
Every prop rejection is a SIZE rejection -- a short holding window forces contract count up
against a fixed $2,000 floor -- so widening the window relaxes the lower bound ($150 qualifying
days) without touching the upper.

D259 and D440, from the other side: C1's 22-hour window failed on MAE, with p99 sitting exactly
on the 4% floor. A longer window is more path, and more path is more excursion.

BOTH BOUNDS ARE THE SAME 4%, AND THEY MOVE IN OPPOSITE DIRECTIONS WITH HOLD LENGTH. Nobody has
drawn the curve, because until the ES minute series landed nobody could hold for anything but the
22 hours C1 fixes.

WHAT IS SWEPT. Entry is C1's 18:00 ET Globex reopen, unchanged. The hold is closed after H
minutes of CLOCK time rather than at 16:00, for H from 30 minutes to the full 1,320. Each H gets
its own (d_low, d_high, d_end) from the ordered minute path, and then D440's lifecycle, unchanged,
with the risk grid free to choose its own size at every H -- which is what makes the comparison a
comparison of SHAPE rather than of leverage.

WHAT IS NOT SWEPT, and why. H > 22h needs a multi-day hold, where the floor ratchets at each EOD
while the position stays open. D440's lifecycle steps one day at a time and a multi-day hold is
not expressible in it without a modelling assumption this study would then be testing rather than
using. The sub-C1 range is measured; the super-C1 range is named as not run.

PREDICTIONS, WRITTEN BEFORE THE RUN:
  U1  V is NOT monotone increasing in H. The research's "longer is better" is an argument about
      CONTRACT COUNT at fixed vol, and the risk grid already adapts size at every H, so the
      blade it relaxes has already been priced.
  U2  funded life FALLS as H rises -- longer exposure per session is more chance to touch a floor
      that ratchets whether or not you are in the trade.
  U3  the V argmax is INTERIOR and well below 1,320 minutes.
  U4  T2 fails at EVERY H. No hold length reaches three years; the best cell in D452 was 0.86
      years at the smallest size and this sweep does not have an order of magnitude in it.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

RAW = REPO / "data" / "raw" / "databento"   # moved 2026-09-12 out of deletable temp/
FIX = REPO / "data" / "fixtures" / "es_hold_ladder.csv.gz"
OUT = REPO / "data" / "d458_hold_length_curve.json"

OUTRIGHT = re.compile(r"^ES[FGHJKMNQUVXZ]\d{1,2}$")
PX = 1e-9
ENTRY_HHMM = "18:00"
EXIT_HHMM = "15:59"
# elapsed CLOCK minutes from the 18:00 entry. 1,320 is C1's own 22-hour hold.
LADDER = (30, 60, 120, 240, 360, 480, 600, 720, 840, 960, 1080, 1200, 1320)


def es_ids(store) -> dict:
    out = {}
    for sym, ivs in store.metadata.mappings.items():
        if not OUTRIGHT.match(str(sym)):
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if sid:
                out[int(sid)] = str(sym)
    return out


def build() -> int:
    import databento as db

    bars = REPO / "data" / "fixtures" / "es_minute_bars.parquet"
    if bars.exists():
        # THE DURABLE PATH. Once the ES minute bars are preserved, temp/ is never touched again.
        df = pd.read_parquet(bars)
        df["ts"] = pd.to_datetime(df["day"] + " " + df["hhmm"])
        df = df.sort_values("ts", kind="stable")
        print(f"D458 build -- {len(df):,} ES minute bars from {bars.relative_to(REPO)}")
        print(f"  {df['day'].min()} .. {df['day'].max()}, {df['day'].nunique():,} days\n")
        return _ladder(df)

    files = sorted(RAW.glob("*/*.ohlcv-1m.dbn.zst"))
    print(f"D458 build -- {len(files)} files visible, ladder {LADDER}\n")
    # THE RAW LIVES IN data/raw/, WHICH IS GITIGNORED -- durable on this machine, absent from the
    # repo. So the ES subset is PRESERVED into data/fixtures/ as a committed artifact: 4.9M rows
    # against 625M raw, and it is what makes every ES study reproducible without the 104 GB.
    # Files are still tolerated going missing, because this build caught the temp/ -> data/raw/
    # move in flight and lost 8 of 14 files mid-read.
    frames, got, lost = [], [], []
    for i, f in enumerate(files, 1):
        try:
            store = db.DBNStore.from_file(f)
            ids = es_ids(store)
            arr = store.to_ndarray()
        except Exception as e:
            lost.append(f.name)
            print(f"  [{i:2d}/{len(files)}] GONE  {f.name[:44]}  ({type(e).__name__})")
            continue
        a = arr[np.isin(arr["instrument_id"], np.fromiter(ids, dtype=np.uint32))]
        ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern")
        frames.append(pd.DataFrame({
            "ts": ts, "day": ts.strftime("%Y-%m-%d"), "hhmm": ts.strftime("%H:%M"),
            "contract": [ids[int(x)] for x in a["instrument_id"]],
            "high": a["high"] * PX, "low": a["low"] * PX, "close": a["close"] * PX,
            "open": a["open"] * PX, "volume": a["volume"].astype(np.int64),
        }))
        got.append(f.name)
        print(f"  [{i:2d}/{len(files)}] ES {len(a):>8,}")
    if not frames:
        raise SystemExit("every file vanished -- the raw DBN is gone, see the record")
    df = pd.concat(frames, ignore_index=True)
    del frames
    print(f"\n  survived {len(got)}, lost {len(lost)} mid-read")

    df.drop(columns=["ts"]).to_parquet(bars, compression="zstd", index=False)
    print(f"  PRESERVED {len(df):,} ES minute bars -> {bars.relative_to(REPO)} "
          f"({bars.stat().st_size / 1e6:.0f} MB)")
    return _ladder(df)


def _ladder(df: pd.DataFrame) -> int:

    vol = df.groupby(["day", "contract"], sort=False)["volume"].sum().reset_index()
    front = vol.sort_values("volume").groupby("day", sort=True).tail(1)
    front = front.set_index("day")["contract"].to_dict()
    df = df[[c == front.get(d) for d, c in zip(df["day"], df["contract"])]]
    df = df.sort_values("ts", kind="stable")

    ev = {k: v for k, v in df[df["hhmm"] >= ENTRY_HHMM].groupby("day", sort=True)}
    dp = {k: v for k, v in df[df["hhmm"] <= EXIT_HHMM].groupby("day", sort=True)}

    rows = []
    for b in sorted(dp):
        a = str((pd.Timestamp(b) - pd.Timedelta(days=1)).date())
        if a not in ev or a not in front or b not in front or front[a] != front[b]:
            continue
        A, B = ev[a], dp[b]
        if A.empty or B.empty:
            continue
        t0 = A["ts"].iloc[0]
        ts = np.concatenate([A["ts"].to_numpy(), B["ts"].to_numpy()])
        el = (ts.astype('datetime64[ns]') - np.datetime64(t0)) / np.timedelta64(1, "m")
        hi = np.concatenate([A["high"].to_numpy(float), B["high"].to_numpy(float)])
        lo = np.concatenate([A["low"].to_numpy(float), B["low"].to_numpy(float)])
        cl = np.concatenate([A["close"].to_numpy(float), B["close"].to_numpy(float)])
        entry = float(A["open"].iloc[0])
        rec = {"day": b, "prev_day": a, "contract": front[a], "era": _era(b), "entry": entry}
        for H in LADDER:
            m = el <= H
            if not m.any():
                rec[f"end_{H}"] = np.nan
                continue
            peak = np.maximum.accumulate(np.maximum(hi[m] / entry, 1.0))
            rec[f"low_{H}"] = float(lo[m].min()) / entry - 1.0
            rec[f"high_{H}"] = float(hi[m].max()) / entry - 1.0
            rec[f"end_{H}"] = float(cl[m][-1]) / entry - 1.0
            rec[f"dd_{H}"] = float((1.0 - (lo[m] / entry) / peak).max())
            rec[f"n_{H}"] = int(m.sum())
        rows.append(rec)
    out = pd.DataFrame(rows)
    FIX.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(FIX, index=False, compression="gzip")
    print(f"\n  wrote {FIX.relative_to(REPO)}  ({len(out):,} holds, "
          f"{out['day'].min()} .. {out['day'].max()})")
    return 0


def _era(day: str) -> str:
    y = int(day[:4])
    return "2010-2019" if y <= 2019 else ("2020" if y == 2020 else "2021-2026")


def test() -> int:
    import d386_full_lifecycle as D386
    import d440_lifecycle as D440

    lad = pd.read_csv(FIX)
    plan = [p for p in D386.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]
    print("D458 -- the hold-length curve\n")
    print(f"  {len(lad):,} holds  {lad['day'].min()} .. {lad['day'].max()}\n")

    # the path statistics first -- this is the blade D259 and D440 measured
    print(f"  {'H min':>7}{'hours':>7}{'bars':>7}{'sd/hold':>10}{'mean bp':>9}"
          f"{'p99 MAE':>10}{'breach1x':>10}")
    rows = []
    for H in LADDER:
        g = lad.dropna(subset=[f"end_{H}"])
        r = g[f"end_{H}"].to_numpy(float)
        mae = -g[f"low_{H}"].to_numpy(float)
        br = float((g[f"dd_{H}"].to_numpy(float) > 0.04).mean())
        print(f"  {H:>7}{H / 60:>7.1f}{g[f'n_{H}'].median():>7.0f}"
              f"{100 * r.std(ddof=1):>9.3f}%{1e4 * r.mean():>9.2f}"
              f"{100 * np.percentile(mae, 99):>9.3f}%{100 * br:>9.3f}%")
        rows.append({"H": H, "n": len(g), "sd": float(r.std(ddof=1)),
                     "mean_bp": 1e4 * float(r.mean()),
                     "p99_mae": float(np.percentile(mae, 99)), "breach1x": br})

    # the lifecycle at every H, with the risk grid free to re-size
    print(f"\n  THE CURVE -- MFFU Rapid EOD 50K, voltgt, best over the risk grid at each H")
    print(f"  {'H min':>7}{'hours':>7}{'V':>9}{'frac':>7}{'fund_yr':>9}"
          f"{'p_pass':>8}{'p_paid':>8}{'payouts':>9}")
    best = {}
    for H in LADDER:
        g = lad.dropna(subset=[f"end_{H}"]).copy()
        frame = pd.DataFrame({"d_end": g[f"end_{H}"], "d_low": g[f"low_{H}"],
                              "d_high": g[f"high_{H}"], "max_dd": g[f"dd_{H}"],
                              "era": g["era"], "day": g["day"]}).reset_index(drop=True)
        cells = [D440.run_cell(frame, plan, f, "voltgt", "MEASURED", 8_000, 600)
                 for f in D386.RISK_FRACS]
        b = max(cells, key=lambda x: x["V"])
        best[H] = b
        for c in cells:
            rows.append(dict(c, H=H))
        print(f"  {H:>7}{H / 60:>7.1f}{b['V']:>9,.0f}{100 * b['frac']:>6.1f}%"
              f"{b['fund_days_mean'] / 252:>9.2f}{b['p_pass']:>8.3f}{b['p_paid']:>8.3f}"
              f"{b['n_payouts_mean']:>9.2f}")

    hstar = max(best, key=lambda h: best[h]["V"])
    print(f"\n  ARGMAX at H = {hstar} min ({hstar / 60:.1f} h), V = {best[hstar]['V']:,.0f}"
          f"   against C1's own 1,320 min at V = {best[1320]['V']:,.0f}")
    interior = hstar not in (LADDER[0], LADDER[-1])
    print(f"  interior optimum: {interior}")
    mono = all(best[LADDER[i]]["V"] <= best[LADDER[i + 1]]["V"] for i in range(len(LADDER) - 1))
    print(f"  V monotone increasing in H: {mono}  "
          f"(the research's 'longer is better', tested)")
    lives = [best[H]["fund_days_mean"] / 252 for H in LADDER]
    print(f"  funded life monotone FALLING in H: "
          f"{all(lives[i] >= lives[i + 1] for i in range(len(lives) - 1))}")
    print(f"  any H clearing P4's 3 years: "
          f"{[H for H in LADDER if best[H]['fund_days_mean'] / 252 > 3.0] or 'NONE'}")

    # ----------------------------------------------------------------------------------
    # THE NULL THE ARGMAX NEEDS, and D442's addendum is why it is here. That record found two
    # apparent wins that cleared a null scored at ONE fixed grid point while the treatment was
    # an argmax over four -- and the selection premium was larger than the effect. Here the
    # treatment is an argmax over 13 hold lengths x 4 risk fractions = 52 cells. So the null is
    # scored the SAME way: resample the hold sequence in circular blocks, rebuild the whole
    # grid, and take its max. If a flat curve produces 507 this often, there is no optimum.
    # ----------------------------------------------------------------------------------
    print(f"\n  THE ARGMAX NULL -- circular block bootstrap of the hold sequence, "
          f"whole {len(LADDER)}x{len(D386.RISK_FRACS)} grid re-maximised each time")
    rng = np.random.default_rng(D440.SEED)
    n = len(lad)
    reps, bl = 100, 20
    nb = int(np.ceil(n / bl))
    maxes, at_h = [], []
    for _ in range(reps):
        starts = rng.integers(0, n, size=nb)
        idx = (starts[:, None] + np.arange(bl)[None, :]).ravel()[:n] % n
        g0 = lad.iloc[idx].reset_index(drop=True)
        cur, cur_h = -np.inf, None
        for H in LADDER:
            g = g0.dropna(subset=[f"end_{H}"])
            if len(g) < 100:
                continue
            fr = pd.DataFrame({"d_end": g[f"end_{H}"], "d_low": g[f"low_{H}"],
                               "d_high": g[f"high_{H}"], "max_dd": g[f"dd_{H}"],
                               "era": g["era"], "day": g["day"]}).reset_index(drop=True)
            for f in D386.RISK_FRACS:
                v = D440.run_cell(fr, plan, f, "voltgt", "MEASURED", 8_000, 600)["V"]
                if v > cur:
                    cur, cur_h = v, H
        maxes.append(cur)
        at_h.append(cur_h)
    m = np.asarray(maxes, dtype=float)
    obs = best[hstar]["V"]
    print(f"    observed argmax V {obs:,.0f} at H={hstar}")
    print(f"    null max-over-grid: p50 {np.median(m):>8,.0f}   p95 {np.percentile(m, 95):>8,.0f}"
          f"   max {m.max():>8,.0f}")
    print(f"    P(null max >= observed) = {float((m >= obs).mean()):.3f}")
    vc = pd.Series(at_h).value_counts()
    print(f"    where the NULL's argmax lands: {dict(vc.head(6))}")
    print(f"    -> the observed optimum is "
          f"{'ABOVE the null p95' if obs > np.percentile(m, 95) else 'INSIDE the null'}")

    rows.append({"kind": "ARGMAX_NULL", "observed": obs, "hstar": hstar, "reps": reps,
                 "block": bl, "null_p50": float(np.median(m)),
                 "null_p95": float(np.percentile(m, 95)), "null_max": float(m.max()),
                 "p_value": float((m >= obs).mean()),
                 "null_argmax_h": {str(k): int(v) for k, v in vc.items()}})
    pd.DataFrame(rows).to_json(OUT, orient="records", indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.build:
        return build()
    if a.test:
        return test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
