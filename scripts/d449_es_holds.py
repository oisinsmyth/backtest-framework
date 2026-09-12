"""D449 -- C1's hold measured on ES ITSELF, and D440's lifecycle re-run on it.

    python scripts/d449_es_holds.py --build     # DBN -> data/fixtures/es_c1_holds.csv.gz
    python scripts/d449_es_holds.py --test      # D440's lifecycle, ES vs the equity proxy

RUN WITH THE SYSTEM INTERPRETER for --build (databento lives there and is not a project
dependency). --test runs under either.

WHAT THIS ANSWERS. D440 section 8a states its own largest limitation: the equity fixture's
20:00-04:00 window is UNOBSERVED, contributing exactly one observation per hold -- the reopen
price -- so "every MAE in this study understates the true excursion, and V is correspondingly an
upper bound." ES trades that window continuously. This is the measurement that removes the
caveat instead of restating it.

    D259/D440 equity proxy   16 of 23 hours; the untraded window is ONE point
    D449 ES                  the whole window, minute by minute

THE COMPARISON IS ON MATCHED DATES. ES covers 2010-06 to 2022-08 and the equity fixture covers
2010-01 to 2026-08, so the proxy is re-scored on exactly the dates ES supplies. Any difference is
then the INSTRUMENT and not the sample.

NO ROLL ADJUSTMENT, SAME AS D448. Entry, path and exit all come from ONE contract, and a hold
whose front month differs between its two days is dropped. Nothing is stitched.

PREDICTIONS, WRITTEN BEFORE THE RUN:
  Z1  ES MAE is LARGER than the proxy's at every quantile, because the untraded window becomes
      visible. D259 measured the gap ALONE breaching 4% on 0.10% of holds at 1x with a p99 of
      1.58%; seeing its interior can only add excursion, never remove it.
  Z2  the p99 rises by 15-60% -- above D259's gap-alone p99 of 1.58% added in quadrature, below
      a doubling.
  Z3  V FALLS and funded life SHORTENS on ES against the matched proxy. D440's numbers are upper
      bounds and this is the direction the caveat named.
  Z4  hold RETURNS are nearly identical -- corr > 0.98, and the mean differs by about q-r, the
      carry term D448 measured at +1.49%/yr. The path changes; the destination does not.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

RAW = REPO / "temp" / "databento"
FIX = REPO / "data" / "fixtures" / "es_c1_holds.csv.gz"
OUT = REPO / "data" / "d449_es_lifecycle.json"

OUTRIGHT = re.compile(r"^ES[FGHJKMNQUVXZ]\d{1,2}$")
PX = 1e-9
ENTRY_HHMM = "18:00"        # the Globex reopen -- C1's entry, per BOOK_PROP
EXIT_HHMM = "15:59"         # covers [15:59,16:00); its close IS the 16:00 print


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

    files = sorted(RAW.glob("*/*.ohlcv-1m.dbn.zst"))
    print(f"D449 build -- {len(files)} files, keeping HIGH and LOW this time\n")
    frames = []
    for i, f in enumerate(files, 1):
        store = db.DBNStore.from_file(f)
        ids = es_ids(store)
        arr = store.to_ndarray()
        a = arr[np.isin(arr["instrument_id"], np.fromiter(ids, dtype=np.uint32))]
        ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern")
        frames.append(pd.DataFrame({
            "day": ts.strftime("%Y-%m-%d"), "hhmm": ts.strftime("%H:%M"),
            "contract": [ids[int(x)] for x in a["instrument_id"]],
            "open": a["open"] * PX, "high": a["high"] * PX,
            "low": a["low"] * PX, "close": a["close"] * PX,
            "volume": a["volume"].astype(np.int64),
        }))
        print(f"  [{i:2d}/{len(files)}] ES {len(a):>8,}")
    df = pd.concat(frames, ignore_index=True)
    del frames

    vol = df.groupby(["day", "contract"], sort=False)["volume"].sum().reset_index()
    front = vol.sort_values("volume").groupby("day", sort=True).tail(1)
    front = front.set_index("day")["contract"].to_dict()
    df = df[[c == front.get(d) for d, c in zip(df["day"], df["contract"])]]
    df = df.sort_values(["day", "hhmm"], kind="stable")

    # THE WALK IS DONE HERE, IN ORDER, because a TRAILING drawdown needs the running peak to
    # PRECEDE the trough. Taking (global high, global low) and dividing is not a trailing
    # drawdown -- it is an upper bound on one, and the first version of this file made exactly
    # that error. D259's `walk` is reproduced: the peak INCLUDES the current bar's high, which
    # is the adverse assumption and the right one for a ratcheting barrier.
    ev = {k: v for k, v in df[df["hhmm"] >= ENTRY_HHMM].groupby("day", sort=True)}
    dp = {k: v for k, v in df[df["hhmm"] <= EXIT_HHMM].groupby("day", sort=True)}
    # PAIR BY CALENDAR, NOT BY POSITION IN A LIST OF EVENING DAYS. ES is SHUT on Friday evening,
    # so a Friday has no 18:00+ bars and never appears in `ev`. Pairing consecutive entries of
    # sorted(ev) therefore skipped Thursday->Friday entirely -- 418 holds, a fifth of the sample,
    # every one of them a Friday. D259's rule excludes Friday->MONDAY (Globex shut over the
    # weekend); it does not exclude Thursday->Friday, which is a perfectly tradeable hold.
    rows = []
    for b in sorted(dp):
        a = str((pd.Timestamp(b) - pd.Timedelta(days=1)).date())
        if a not in ev or a not in front or b not in front:
            continue
        if front[a] != front[b]:
            continue                                      # the roll -- dropped, never adjusted
        A, B = ev[a], dp[b]
        if A.empty or B.empty:
            continue
        entry = float(A["open"].iloc[0])
        his = np.concatenate([A["high"].to_numpy(float), B["high"].to_numpy(float)])
        los = np.concatenate([A["low"].to_numpy(float), B["low"].to_numpy(float)])
        peak = np.maximum.accumulate(np.maximum(his / entry, 1.0))
        dd = 1.0 - (los / entry) / peak
        rows.append({"symbol": "ES", "day": b, "prev_day": a,
                     "dow": pd.Timestamp(b).day_name(),
                     "contract": front[a], "era": _era(b),
                     "entry": entry,
                     "d_end": float(B["close"].iloc[-1]) / entry - 1.0,
                     "d_high": float(his.max()) / entry - 1.0,
                     "d_low": float(los.min()) / entry - 1.0,
                     "max_dd": float(dd.max()),
                     "bars": int(len(A) + len(B)),
                     "night_bars": int(((A["hhmm"] >= "20:00").sum())
                                       + ((B["hhmm"] < "04:00").sum()))})
    panel = pd.DataFrame(rows)
    panel["mae"] = panel["d_low"]
    FIX.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(FIX, index=False, compression="gzip")
    print(f"\n  wrote {FIX.relative_to(REPO)}  ({len(panel):,} holds, "
          f"{panel['day'].min()} .. {panel['day'].max()})")
    print(f"  median bars/hold {panel['bars'].median():.0f}, of which "
          f"{panel['night_bars'].median():.0f} are in 20:00-04:00 -- the window the proxy "
          f"cannot see")
    return 0


def es_holds() -> pd.DataFrame:
    """The holds, already walked in order at build time. See build() for why that matters."""
    return pd.read_csv(FIX)


def _era(day: str) -> str:
    y = int(day[:4])
    return "2010-2019" if y <= 2019 else ("2020" if y == 2020 else "2021-2026")


def test() -> int:
    import d386_full_lifecycle as D386
    import d440_lifecycle as D440

    es = es_holds()
    spy = pd.read_csv(D440.HOLDS_CSV)
    spy = spy[spy["symbol"] == "SPY"]
    both = sorted(set(es["day"]) & set(spy["day"]))
    es_m = es[es["day"].isin(both)].sort_values("day").reset_index(drop=True)
    spy_m = spy[spy["day"].isin(both)].sort_values("day").reset_index(drop=True)

    # --- the ordering check that the first version of this file failed -------------------
    naive = 1.0 - (1.0 + es_m["d_low"]) / np.maximum(1.0 + es_m["d_high"], 1.0)
    assert (es_m["max_dd"] >= -es_m["d_low"] - 1e-12).all(), \
        "trailing DD below MAE: the running peak is not being tracked"
    assert (es_m["max_dd"] <= naive + 1e-12).all(), \
        "trailing DD above the unordered bound: the walk is not in order"
    # dip to 0.90 FIRST, then rise to 1.20 and stay: ordered DD is 0.10 (the dip, against a
    # peak of 1.0); the unordered bound is 1 - 0.90/1.20 = 0.25, a peak that came AFTERWARDS.
    lo, hi = np.array([1.0, 0.90, 1.20]), np.array([1.0, 0.92, 1.20])
    pk = np.maximum.accumulate(np.maximum(hi, 1.0))
    assert abs((1.0 - lo / pk).max() - 0.10) < 1e-12, "synthetic walk wrong"
    assert abs((1.0 - lo.min() / max(hi.max(), 1.0)) - 0.25) < 1e-12, "synthetic bound wrong"

    print("D449 -- C1's hold on ES itself, against the equity proxy on MATCHED DATES\n")
    print(f"  [ORDERING] trailing DD mean {100 * es_m['max_dd'].mean():.3f}% against the "
          f"UNORDERED bound {100 * naive.mean():.3f}% -- the first version of this runner "
          f"reported the second and called it a trailing drawdown")
    print(f"  [ORDERING] breach 1x ordered {100 * (es_m['max_dd'] > 0.04).mean():.3f}% "
          f"against unordered {100 * (naive > 0.04).mean():.3f}%\n")
    print(f"  ES holds {len(es):,}   matched {len(both):,}   "
          f"{both[0]} .. {both[-1]}")
    print(f"  median bars per ES hold: {es_m['bars'].median():.0f}  "
          f"(the proxy sees ~40 and cannot see 20:00-04:00 at all)\n")

    print(f"  {'':<22}{'ES':>12}{'proxy':>12}{'ratio':>9}")
    mae_e = -es_m["d_low"].to_numpy()
    mae_s = -spy_m["d_low"].to_numpy()
    for lab, f in (("mean MAE", np.mean), ("p50", lambda x: np.percentile(x, 50)),
                   ("p90", lambda x: np.percentile(x, 90)),
                   ("p95", lambda x: np.percentile(x, 95)),
                   ("p99", lambda x: np.percentile(x, 99)),
                   ("worst", np.max)):
        a, b = f(mae_e), f(mae_s)
        print(f"  {lab:<22}{100 * a:>11.3f}%{100 * b:>11.3f}%{a / b:>9.2f}")
    for k in (1, 2, 3):
        a = float((es_m["max_dd"] > 0.04 / k).mean())
        b = float((spy_m["max_dd"] > 0.04 / k).mean())
        print(f"  {'breach ' + str(k) + 'x':<22}{100 * a:>11.3f}%{100 * b:>11.3f}%"
              f"{(a / b if b else float('nan')):>9.2f}")

    r_e, r_s = es_m["d_end"].to_numpy(), spy_m["d_end"].to_numpy()
    print(f"\n  [Z4] corr(hold return) {np.corrcoef(r_e, r_s)[0, 1]:.4f}"
          f"   mean ES {1e4 * r_e.mean():+.2f} bp   proxy {1e4 * r_s.mean():+.2f} bp"
          f"   diff {1e4 * (r_e.mean() - r_s.mean()):+.2f} bp"
          f" = {252 * (r_e.mean() - r_s.mean()) * 100:+.2f}%/yr")

    plan = [p for p in D386.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]
    print("\n  THE LIFECYCLE, MFFU Rapid EOD 50K, best over the risk grid")
    print(f"  {'series':<10}{'rule':<9}{'V':>8}{'frac':>7}{'fund_yr':>9}"
          f"{'p_pass':>8}{'p_paid':>8}")
    rows = []
    for name, frame in (("ES", es_m), ("proxy", spy_m)):
        for rule in ("static", "voltgt"):
            cells = [D440.run_cell(frame, plan, f, rule, "MEASURED", 8_000, 600)
                     for f in D386.RISK_FRACS]
            b = max(cells, key=lambda x: x["V"])
            rows += [dict(c, series=name, rule=rule) for c in cells]
            print(f"  {name:<10}{rule:<9}{b['V']:>8,.0f}{100 * b['frac']:>6.1f}%"
                  f"{b['fund_days_mean'] / 252:>9.2f}{b['p_pass']:>8.3f}{b['p_paid']:>8.3f}")

    pd.DataFrame(rows).to_json(OUT, orient="records", indent=1)
    es.to_csv(REPO / "data" / "d449_es_holds.csv.gz", index=False, compression="gzip")
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
