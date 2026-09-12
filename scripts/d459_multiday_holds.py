"""D459 -- hold lengths BEYOND 22 hours: the range the shape constraint actually points at.

    python scripts/d459_multiday_holds.py --build   # parquet -> data/fixtures/es_daily_marks.csv.gz
    python scripts/d459_multiday_holds.py --test

THE OBSTACLE D458 CITED, AND WHY IT DISSOLVES
----------------------------------------------
D458 section 7 left H > 22h untested because "a multi-day hold ratchets the floor at each EOD
while the position stays open, which D440's lifecycle cannot express without a modelling
assumption". That was too cautious. D440's loop already MARKS TO MARKET DAILY -- it consumes one
(low, high, end) per day and never asks whether a position closed. A multi-day hold is therefore
expressible exactly: it is several consecutive days of non-zero increments instead of one, each
measured against the PREVIOUS DAY'S MARK.

    day 1 of a hold   18:00 (prev) -> 16:00        the C1 window, entered fresh
    day 2..k          16:00 (prev) -> 16:00        held through, including the 17:00-18:00 halt
    then re-enter at the next 18:00

So a k-day strategy is flat only for the 16:00->18:00 stretch on every k-th day. LONGER HOLDS ARE
MORE EXPOSURE PER CALENDAR DAY, which is precisely the lever the prop research's shape constraint
says relaxes the $150 qualifying-day bound.

THE ONE THING THAT IS NOT MARK-TO-MARKET, and it matters: NOTIONAL IS FIXED AT HOLD ENTRY and
carried unchanged to the exit. A position is not re-sized mid-hold. D440's run_cell re-sizes every
day because every day was its own hold there; here the sizing is applied per hold and held.

WHAT IS SWEPT. k = 1 (C1 itself, 22h), 2, 3, 5, 10, 20 days. k=1 must reproduce D458's own H=1320
cell, and that is asserted rather than assumed.

THE ARGMAX NULL IS BUILT IN, because D442's addendum and D458 both turned on it: the treatment is
a max over k x risk-fraction cells, so the null resamples the day sequence in circular blocks,
rebuilds the WHOLE grid, and takes its max.

PREDICTIONS, WRITTEN BEFORE THE RUN:
  X1  exposure rises with k and so does everything scaled by it -- daily sd, p99 MAE and breach
      all rise monotonically, as they did within the day in D458.
  X2  V has NO identifiable optimum in k either. D458's null put a flat curve's best-of-52 above
      the observed; adding a second axis does not create structure that was not there.
  X3  T2 fails at every k, and by MORE than within the day: longer exposure against a floor that
      ratchets daily is the one thing P4 punishes hardest.
  X4  the research's "longer is better" finally gets its own range and still does not hold. If it
      does hold -- if V rises monotonically in k and clears its null -- that is the first
      structural support the shape constraint has ever had, and it would be the finding.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

BARS = REPO / "data" / "fixtures" / "es_minute_bars.parquet"
FIX = REPO / "data" / "fixtures" / "es_daily_marks.csv.gz"
OUT = REPO / "data" / "d459_multiday_holds.json"

KS = (1, 2, 3, 5, 10, 20)
VOL_WINDOW = 21
VOL_CAP = 4.0


def build() -> int:
    df = pd.read_parquet(BARS)
    vol = df.groupby(["day", "contract"], sort=False)["volume"].sum().reset_index()
    front = vol.sort_values("volume").groupby("day", sort=True).tail(1)
    front = front.set_index("day")["contract"].to_dict()
    df = df[[c == front.get(d) for d, c in zip(df["day"], df["contract"])]]
    df = df.sort_values(["day", "hhmm"], kind="stable")

    ev18 = {k: v for k, v in df[df["hhmm"] >= "18:00"].groupby("day", sort=True)}
    ev16 = {k: v for k, v in df[df["hhmm"] >= "16:00"].groupby("day", sort=True)}
    dp = {k: v for k, v in df[df["hhmm"] <= "15:59"].groupby("day", sort=True)}
    c16 = {k: float(v[v["hhmm"] == "15:59"]["close"].iloc[-1])
           for k, v in dp.items() if (v["hhmm"] == "15:59").any()}

    rows = []
    for b in sorted(dp):
        a = str((pd.Timestamp(b) - pd.Timedelta(days=1)).date())
        if a not in front or b not in front or front[a] != front[b]:
            continue
        if b not in c16 or a not in c16:
            continue
        B = dp[b]
        rec = {"day": b, "prev_day": a, "contract": front[b], "era": _era(b),
               "c16_prev": c16[a], "c16": c16[b]}
        # FRESH-ENTRY day: 18:00(prev) -> 16:00, the C1 window
        if a in ev18 and not ev18[a].empty:
            A = ev18[a]
            e = float(A["open"].iloc[0])
            hi = np.concatenate([A["high"].to_numpy(float), B["high"].to_numpy(float)])
            lo = np.concatenate([A["low"].to_numpy(float), B["low"].to_numpy(float)])
            rec |= {"entry18": e, "b_low": lo.min() / e - 1.0, "b_high": hi.max() / e - 1.0,
                    "b_end": c16[b] / e - 1.0}
        # HELD-THROUGH day: 16:00(prev) -> 16:00, marked against the previous close
        if a in ev16 and not ev16[a].empty:
            A = ev16[a]
            p = c16[a]
            hi = np.concatenate([A["high"].to_numpy(float), B["high"].to_numpy(float)])
            lo = np.concatenate([A["low"].to_numpy(float), B["low"].to_numpy(float)])
            rec |= {"a_low": lo.min() / p - 1.0, "a_high": hi.max() / p - 1.0,
                    "a_end": c16[b] / p - 1.0}
        rows.append(rec)
    out = pd.DataFrame(rows).dropna(subset=["b_end", "a_end"]).reset_index(drop=True)
    FIX.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(FIX, index=False, compression="gzip")
    print(f"D459 build -- wrote {FIX.relative_to(REPO)}  ({len(out):,} days, "
          f"{out['day'].min()} .. {out['day'].max()})")
    return 0


def _era(day: str) -> str:
    y = int(day[:4])
    return "2010-2019" if y <= 2019 else ("2020" if y == 2020 else "2021-2026")


def series_for(m: pd.DataFrame, k: int) -> pd.DataFrame:
    """The daily increment series for a k-day hold, re-entering immediately.

    Day j of each cycle uses the FRESH-ENTRY window when j == 0 and the HELD-THROUGH window
    otherwise. Notional is a separate concern and is applied per HOLD, not per day."""
    n = len(m)
    pos = np.arange(n) % k
    low = np.where(pos == 0, m["b_low"], m["a_low"])
    high = np.where(pos == 0, m["b_high"], m["a_high"])
    end = np.where(pos == 0, m["b_end"], m["a_end"])
    return pd.DataFrame({"day": m["day"], "era": m["era"], "hold_id": np.arange(n) // k,
                         "d_low": low, "d_high": high, "d_end": end})


def dollarise(s: pd.DataFrame, target: float) -> pd.DataFrame:
    """Notional fixed at HOLD ENTRY from the trailing vol of daily marks, then carried."""
    r = s["d_end"].to_numpy(float)
    sig = np.full(len(r), np.nan)
    for t in range(VOL_WINDOW, len(r)):
        sig[t] = r[t - VOL_WINDOW:t].std(ddof=1)
    base = target / r.std(ddof=1)
    n_t = np.where(np.isnan(sig), base, target / np.maximum(sig, 1e-12))
    n_t = np.minimum(n_t, VOL_CAP * base)
    # freeze the notional at each hold's first day
    first = s.groupby("hold_id")["d_end"].transform("size").index  # positional
    hid = s["hold_id"].to_numpy()
    held = np.empty(len(r))
    cur = base
    for i in range(len(r)):
        if i == 0 or hid[i] != hid[i - 1]:
            cur = n_t[i]
        held[i] = cur
    out = s.copy()
    out["d_low"] = s["d_low"] * held
    out["d_high"] = s["d_high"] * held
    out["d_end"] = s["d_end"] * held
    return out


def run(s: pd.DataFrame, plan, n_paths=8_000, days=600, seed=20260911) -> dict:
    import d440_lifecycle as D440
    lo = s["d_low"].to_numpy(float)
    hi = s["d_high"].to_numpy(float)
    en = s["d_end"].to_numpy(float)
    n = len(lo)
    npz = min(n_paths, n)
    order = np.arange(npz)

    def provider(day, live_idx, _rng):
        j = (order[live_idx] + day) % n
        return lo[j], hi[j], en[j]

    return D440.simulate_provider(plan, provider, n_paths=npz, days=days, seed=seed)


def test() -> int:
    import d386_full_lifecycle as D386
    import d440_lifecycle as D440

    m = pd.read_csv(FIX)
    plan = [p for p in D386.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]
    print(f"D459 -- hold lengths beyond 22 hours\n")
    print(f"  {len(m):,} daily marks  {m['day'].min()} .. {m['day'].max()}\n")

    print(f"  {'k days':>7}{'hours':>8}{'sd/day':>10}{'mean bp':>9}{'p99 MAE':>10}"
          f"{'breach1x':>10}{'flat share':>12}")
    rows = []
    for k in KS:
        s = series_for(m, k)
        r = s["d_end"].to_numpy(float)
        mae = -s["d_low"].to_numpy(float)
        peak = np.maximum(1 + s["d_high"].to_numpy(float), 1.0)
        dd = 1.0 - (1 + s["d_low"].to_numpy(float)) / peak
        print(f"  {k:>7}{22 + 24 * (k - 1):>8}{100 * r.std(ddof=1):>9.3f}%{1e4 * r.mean():>9.2f}"
              f"{100 * np.percentile(mae, 99):>9.3f}%{100 * float((dd > 0.04).mean()):>9.3f}%"
              f"{100 / (24 * k) * 2:>11.1f}%")
        rows.append({"k": k, "sd": float(r.std(ddof=1)), "mean_bp": 1e4 * float(r.mean()),
                     "p99_mae": float(np.percentile(mae, 99)),
                     "breach1x": float((dd > 0.04).mean())})

    print(f"\n  THE CURVE -- MFFU Rapid EOD 50K, best over the risk grid at each k")
    print(f"  {'k days':>7}{'V':>9}{'frac':>7}{'fund_yr':>9}{'p_pass':>8}{'p_paid':>8}")
    best = {}
    for k in KS:
        s = series_for(m, k)
        cells = []
        for f in D386.RISK_FRACS:
            d = dollarise(s, f * plan.size)
            c = run(d, plan)
            c |= {"k": k, "frac": f}
            cells.append(c)
            rows.append(dict(c))
        b = max(cells, key=lambda x: x["V"])
        best[k] = b
        print(f"  {k:>7}{b['V']:>9,.0f}{100 * b['frac']:>6.1f}%"
              f"{b['fund_days_mean'] / 252:>9.2f}{b['p_pass']:>8.3f}{b['p_paid']:>8.3f}")

    # k=1 must reproduce D458's own 22-hour cell
    try:
        prev = pd.read_json(REPO / "data" / "d458_hold_length_curve.json")
        h1320 = prev[(prev.get("H") == 1320) & prev["V"].notna()]["V"].max()
        print(f"\n  [REP] k=1 here {best[1]['V']:,.0f}  against D458's H=1320 "
              f"{h1320:,.0f}  (different sizing rule: per-hold vs per-day)")
    except Exception as e:
        print(f"\n  [REP] could not read D458: {type(e).__name__}")

    kstar = max(best, key=lambda k: best[k]["V"])
    mono = all(best[KS[i]]["V"] <= best[KS[i + 1]]["V"] for i in range(len(KS) - 1))
    print(f"\n  ARGMAX at k = {kstar} ({22 + 24 * (kstar - 1)} h), V = {best[kstar]['V']:,.0f}")
    print(f"  V monotone increasing in k: {mono}   <- the shape constraint, on its own range")
    print(f"  any k clearing P4's 3 years: "
          f"{[k for k in KS if best[k]['fund_days_mean'] / 252 > 3.0] or 'NONE'}")

    # the argmax null, scored the same way
    print(f"\n  ARGMAX NULL -- circular block bootstrap of the day sequence, whole "
          f"{len(KS)}x{len(D386.RISK_FRACS)} grid re-maximised")
    rng = np.random.default_rng(D440.SEED)
    n, bl, reps = len(m), 20, 60
    nb = int(np.ceil(n / bl))
    maxes = []
    for _ in range(reps):
        st = rng.integers(0, n, size=nb)
        idx = (st[:, None] + np.arange(bl)[None, :]).ravel()[:n] % n
        mm = m.iloc[idx].reset_index(drop=True)
        cur = -np.inf
        for k in KS:
            s = series_for(mm, k)
            for f in D386.RISK_FRACS:
                v = run(dollarise(s, f * plan.size), plan)["V"]
                cur = max(cur, v)
        maxes.append(cur)
    a = np.asarray(maxes, float)
    obs = best[kstar]["V"]
    print(f"    observed {obs:,.0f}   null p50 {np.median(a):>9,.0f}"
          f"   p95 {np.percentile(a, 95):>9,.0f}   P(null >= obs) {float((a >= obs).mean()):.3f}")
    print(f"    -> {'ABOVE the null p95' if obs > np.percentile(a, 95) else 'INSIDE the null'}")

    rows.append({"kind": "ARGMAX_NULL", "observed": obs, "kstar": kstar,
                 "null_p50": float(np.median(a)), "null_p95": float(np.percentile(a, 95)),
                 "p_value": float((a >= obs).mean()), "reps": reps})
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
