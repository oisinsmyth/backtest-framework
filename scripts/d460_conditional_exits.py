"""D460 -- CONDITIONAL exits on C1: a stop is a hold length chosen by the market, not by a clock.

    python scripts/d460_conditional_exits.py --build   # parquet -> data/fixtures/es_stop_grid.csv.gz
    python scripts/d460_conditional_exits.py --test

WHAT IS LEFT, AND WHY IT IS DIFFERENT. D458 swept hold length from 30 minutes to 22 hours and
D459 from 22 hours to 20 days; both found no identifiable optimum, and both swept a CLOCK. D459
section 5 named what neither touched: "a hold whose length is CONDITIONAL rather than fixed". A
stop is exactly that -- the exit time is chosen by the path, so the hold is short precisely on the
holds that would have hurt.

WHY IT IS WORTH TESTING DESPITE THIS REPO'S PRIOR. FINDINGS section 5 records that exit overlays
have a measured ceiling on this book; D380 found no exit overlay beats a random cut, D394 that no
exit rule closes the gap and the take-profit inverts, D423-D425 that every structure exit
forfeits. ALL OF THOSE SCORE RETURN. A prop account does not: under R11's ruling P4 is the
ACCOUNT'S LIFE, and an exit that costs return can still raise V if it raises survival by more.
That is the same asymmetry O1 was screened on, and it is the only reason this is not a repeat.

TWO RULES, because they differ in exactly the way the floor does:
    FIXED     exit when price <= entry x (1 - s)          caps MAE from ENTRY
    TRAILING  exit when price <= running peak x (1 - s)   caps drawdown from the PEAK -- which is
                                                          the MLL's own logic, applied inside the
                                                          hold instead of across the account

THE CONTROL IS THE STUDY, AGAIN. A stop mechanically shortens the hold and truncates the left
tail, so ANY stop improves survival for reasons that have nothing to do with state. The control is
a TIME-MATCHED RANDOM EXIT: exit at an elapsed time drawn from the treatment's own exit-time
distribution, so exposure and average holding period match and only the STATE-DEPENDENCE differs.
That is D442's ROT logic in the time domain.

FILL ASSUMPTION, STATED BECAUSE IT IS OPTIMISTIC: a triggered stop fills AT THE STOP LEVEL. Real
fills gap through. The overshoot -- how far below the stop the triggering bar's low actually went
-- is measured and reported, so the size of the optimism is on the record rather than assumed
away.

PREDICTIONS, WRITTEN BEFORE THE RUN:
  E1  every stop raises funded life and lowers mean return. Both are near-mechanical.
  E2  V does NOT clear the time-matched control at any level of either rule. If a stop helps, it
      helps because it is short, not because it is conditional.
  E3  TRAILING beats FIXED on funded life at matched exposure, because it is the rule the floor
      itself uses.
  E4  no rule/level clears P4's three years. Nothing in this chain has moved that bar by an order
      of magnitude and a stop does not create edge.
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
FIX = REPO / "data" / "fixtures" / "es_stop_grid.csv.gz"
OUT = REPO / "data" / "d460_conditional_exits.json"

LEVELS = (0.005, 0.010, 0.015, 0.020, 0.030)
NQ = 20          # path checkpoints, for the time-matched control
NCTRL = 60       # control draws per cell -- one draw is not a null
RULES = ("fixed", "trailing")


def build() -> int:
    df = pd.read_parquet(BARS)
    vol = df.groupby(["day", "contract"], sort=False)["volume"].sum().reset_index()
    front = vol.sort_values("volume").groupby("day", sort=True).tail(1)
    front = front.set_index("day")["contract"].to_dict()
    df = df[[c == front.get(d) for d, c in zip(df["day"], df["contract"])]]
    df = df.sort_values(["day", "hhmm"], kind="stable")

    ev = {k: v for k, v in df[df["hhmm"] >= "18:00"].groupby("day", sort=True)}
    dp = {k: v for k, v in df[df["hhmm"] <= "15:59"].groupby("day", sort=True)}

    rows = []
    for b in sorted(dp):
        a = str((pd.Timestamp(b) - pd.Timedelta(days=1)).date())
        if a not in ev or a not in front or b not in front or front[a] != front[b]:
            continue
        A, B = ev[a], dp[b]
        if A.empty or B.empty:
            continue
        e = float(A["open"].iloc[0])
        hi = np.concatenate([A["high"].to_numpy(float), B["high"].to_numpy(float)]) / e
        lo = np.concatenate([A["low"].to_numpy(float), B["low"].to_numpy(float)]) / e
        cl = np.concatenate([A["close"].to_numpy(float), B["close"].to_numpy(float)]) / e
        n = len(cl)
        peak = np.maximum.accumulate(np.maximum(hi, 1.0))
        rec = {"day": b, "era": _era(b), "n": n,
               "base_low": lo.min() - 1.0, "base_high": hi.max() - 1.0,
               "base_end": cl[-1] - 1.0}
        # CHECKPOINTS ON THE REAL PATH, so a time-matched control can be EXITED AT THE PRICE
        # THAT ACTUALLY OBTAINED rather than at a synthetic fraction of the hold's final return.
        # The first version of this file scaled base_end by the matched time fraction, which
        # keeps a proportional share of a loss where a stop TRUNCATES it -- an asymmetry that
        # favours the treatment for reasons that have nothing to do with state-dependence, and
        # that alone could have produced the whole result.
        for q in range(1, NQ + 1):
            k = max(0, int(round(q * n / NQ)) - 1)
            rec[f"q{q}_end"] = cl[k] - 1.0
            rec[f"q{q}_low"] = lo[:k + 1].min() - 1.0
            rec[f"q{q}_high"] = hi[:k + 1].max() - 1.0
        for s in LEVELS:
            for rule in RULES:
                trig = (lo <= (1.0 - s)) if rule == "fixed" else (lo <= peak * (1.0 - s))
                k = int(np.argmax(trig)) if trig.any() else -1
                tag = f"{rule}_{int(1000 * s)}"
                if k < 0:
                    rec[f"{tag}_end"] = cl[-1] - 1.0
                    rec[f"{tag}_low"] = lo.min() - 1.0
                    rec[f"{tag}_high"] = hi.max() - 1.0
                    rec[f"{tag}_t"] = n
                    rec[f"{tag}_hit"] = 0
                    rec[f"{tag}_over"] = 0.0
                else:
                    stop = (1.0 - s) if rule == "fixed" else peak[k] * (1.0 - s)
                    rec[f"{tag}_end"] = stop - 1.0
                    rec[f"{tag}_low"] = min(lo[:k + 1].min(), stop) - 1.0
                    rec[f"{tag}_high"] = hi[:k + 1].max() - 1.0
                    rec[f"{tag}_t"] = k + 1
                    rec[f"{tag}_hit"] = 1
                    rec[f"{tag}_over"] = float(stop - lo[k])   # how far the bar went past it
        rows.append(rec)
    out = pd.DataFrame(rows)
    FIX.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(FIX, index=False, compression="gzip")
    print(f"D460 build -- wrote {FIX.relative_to(REPO)}  ({len(out):,} holds, "
          f"{out['day'].min()} .. {out['day'].max()})")
    return 0


def _era(day: str) -> str:
    y = int(day[:4])
    return "2010-2019" if y <= 2019 else ("2020" if y == 2020 else "2021-2026")


def frame_for(g: pd.DataFrame, tag: str | None) -> pd.DataFrame:
    if tag is None:
        lo, hi, en = g["base_low"], g["base_high"], g["base_end"]
    else:
        lo, hi, en = g[f"{tag}_low"], g[f"{tag}_high"], g[f"{tag}_end"]
    peak = np.maximum(1 + hi.to_numpy(float), 1.0)
    dd = 1.0 - (1 + lo.to_numpy(float)) / peak
    return pd.DataFrame({"d_low": lo.to_numpy(float), "d_high": hi.to_numpy(float),
                         "d_end": en.to_numpy(float), "max_dd": dd,
                         "era": g["era"].to_numpy(), "day": g["day"].to_numpy()})


def random_exit(g: pd.DataFrame, tag: str, rng) -> pd.DataFrame:
    """TIME-MATCHED control, ON THE REAL PATH. The treatment's own exit times are PERMUTED across
    holds and each hold is exited at the price that actually obtained at its assigned time, read
    from the checkpoint grid. Same exposure, same holding-period distribution, no state
    dependence -- and, crucially, the control CAN truncate a loss when its assigned exit happens
    to land early, which the first version of this control could not."""
    t = g[f"{tag}_t"].to_numpy(float)
    n = np.maximum(g["n"].to_numpy(float), 1.0)
    frac = np.clip(rng.permutation(t) / n, 1e-9, 1.0)
    q = np.clip(np.ceil(frac * NQ).astype(int), 1, NQ)
    end = np.empty(len(g)); lo = np.empty(len(g)); hi = np.empty(len(g))
    for qq in range(1, NQ + 1):
        m = q == qq
        if m.any():
            end[m] = g.loc[m, f"q{qq}_end"].to_numpy(float)
            lo[m] = g.loc[m, f"q{qq}_low"].to_numpy(float)
            hi[m] = g.loc[m, f"q{qq}_high"].to_numpy(float)
    peak = np.maximum(1 + hi, 1.0)
    dd = 1.0 - (1 + lo) / peak
    return pd.DataFrame({"d_low": lo, "d_high": hi, "d_end": end, "max_dd": dd,
                         "era": g["era"].to_numpy(), "day": g["day"].to_numpy()})


def test() -> int:
    import d386_full_lifecycle as D386
    import d440_lifecycle as D440

    g = pd.read_csv(FIX)
    plan = [p for p in D386.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]
    rng = np.random.default_rng(D440.SEED)
    print("D460 -- conditional exits on C1\n")
    print(f"  {len(g):,} holds  {g['day'].min()} .. {g['day'].max()}"
          f"   median bars/hold {g['n'].median():.0f}\n")

    def best(frame):
        cells = [D440.run_cell(frame, plan, f, "voltgt", "MEASURED", 8_000, 600)
                 for f in D386.RISK_FRACS]
        return max(cells, key=lambda x: x["V"])

    base = best(frame_for(g, None))
    br = g["base_end"].to_numpy(float)
    print(f"  {'rule':<10}{'s':>7}{'hit%':>7}{'med bars':>10}{'mean bp':>9}"
          f"{'p99 MAE':>9}{'V':>8}{'fund_yr':>9}{'ctrl V':>8}{'ctrl yr':>9}")
    print(f"  {'BASE':<10}{'-':>7}{'-':>7}{g['n'].median():>10.0f}{1e4 * br.mean():>9.2f}"
          f"{100 * np.percentile(-g['base_low'], 99):>8.2f}%{base['V']:>8,.0f}"
          f"{base['fund_days_mean'] / 252:>9.2f}{'-':>8}{'-':>9}")

    rows, out = [], {}
    for rule in RULES:
        for s in LEVELS:
            tag = f"{rule}_{int(1000 * s)}"
            b = best(frame_for(g, tag))
            # A SINGLE control draw is not a null. D442 enumerated 3,265 rotations; the
            # time-matched exit has no finite group to enumerate, so it is SAMPLED -- and
            # sampled enough that the treatment is compared to a DISTRIBUTION, not to one draw.
            cs = [best(random_exit(g, tag, rng))["V"] for _ in range(NCTRL)]
            cv = np.asarray(cs, float)
            c = {"V": float(np.median(cv)), "p95": float(np.percentile(cv, 95)),
                 "max": float(cv.max()), "p": float((cv >= b["V"]).mean()),
                 "fund_days_mean": float("nan")}
            out[tag] = (b, c)
            r = g[f"{tag}_end"].to_numpy(float)
            print(f"  {rule:<10}{100 * s:>6.1f}%{100 * g[f'{tag}_hit'].mean():>6.1f}%"
                  f"{g[f'{tag}_t'].median():>10.0f}{1e4 * r.mean():>9.2f}"
                  f"{100 * np.percentile(-g[f'{tag}_low'], 99):>8.2f}%{b['V']:>8,.0f}"
                  f"{b['fund_days_mean'] / 252:>9.2f}{c['V']:>8,.0f}"
                  f"{c['p95']:>9,.0f}")
            rows.append({"rule": rule, "s": s, "hit": float(g[f"{tag}_hit"].mean()),
                         "V": b["V"], "fund_yr": b["fund_days_mean"] / 252,
                         "ctrl_V": c["V"], "ctrl_p95": c["p95"], "ctrl_p": c["p"],
                         "mean_bp": 1e4 * float(r.mean()),
                         "overshoot_bp": 1e4 * float(g[f"{tag}_over"].mean())})

    print(f"\n  E2 -- does any stop beat its TIME-MATCHED control?")
    print(f"    {'cell':<16}{'treat':>9}{'ctrl p50':>10}{'ctrl p95':>10}{'ctrl max':>10}{'p':>7}")
    beat = []
    for k, (a, c) in out.items():
        ok = a["V"] > c["p95"]
        beat.append(ok)
        print(f"    {k:<16}{a['V']:>9,.0f}{c['V']:>10,.0f}{c['p95']:>10,.0f}"
              f"{c['max']:>10,.0f}{c['p']:>7.3f}{'  ABOVE p95' if ok else ''}")
    print(f"    {sum(beat)} of {len(out)} cells clear their control's p95")

    print(f"\n  E3 -- trailing against fixed, at matched level")
    for s in LEVELS:
        f_, t_ = out[f"fixed_{int(1000 * s)}"][0], out[f"trailing_{int(1000 * s)}"][0]
        print(f"    s={100 * s:>4.1f}%   fixed V {f_['V']:>7,.0f} life {f_['fund_days_mean'] / 252:.2f}"
              f"   trailing V {t_['V']:>7,.0f} life {t_['fund_days_mean'] / 252:.2f}")

    print(f"\n  E4 -- any cell clearing P4's three years: "
          f"{[k for k, v in out.items() if v[0]['fund_days_mean'] / 252 > 3.0] or 'NONE'}")

    ov = np.mean([r["overshoot_bp"] for r in rows])
    print(f"\n  FILL OPTIMISM -- mean overshoot past the stop within the triggering bar: "
          f"{ov:.2f} bp")

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
