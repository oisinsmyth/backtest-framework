"""A' step 4: the micro's own pause, measured on ONE-SECOND bars. For every MNQ/MES (and MYM/M2K via parent events? no: micro
events only) front-contract pause event: resume time r (from the status feed). Executable entry = the micro's first 1-s close at
t >= r + 2 s (within 60 s). Parent reference = the parent's last 1-s close at or before that second. basis_r = micro - parent
(ticks). Trade against basis_r: side = -sign(basis_r); outcome = micro close at entry + {30, 60, 300, 900} s minus entry, dollars.
Controls: the same rule on the basis at random seconds in the pre-event window (m0-10..-5 min) with |basis| >= 2 ticks; the
parent's own move over the same horizons. Reports the |basis_r| distribution (ticks).

    python crea_13_micro_pause_1s.py
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "out"
MULT = {"MNQ": 2.0, "MES": 5.0}; COST = {"MNQ": 4.07, "MES": 4.42}; PARENT = {"MNQ": "NQ", "MES": "ES"}; TICK = 0.25
HS = [30, 60, 300, 900]


def stats(g, cost):
    g = np.asarray(g, float); g = g[np.isfinite(g)]
    if len(g) < 8:
        return dict(n=len(g))
    q = np.quantile(g, [0.01, 0.99]) if len(g) >= 50 else (g.min() - 1, g.max() + 1)
    return dict(n=len(g), gross=round(float(g.mean()), 2), t=round(float(g.mean() / g.std() * np.sqrt(len(g))), 1), median=round(float(np.median(g)), 2),
                net=round(float(g.mean() - cost), 2), win=round(float((g > 0).mean()), 3), trim=round(float(g[(g >= q[0]) & (g <= q[1])].mean()), 2), top=round(float(g.max()), 1))


def series(b, root):
    s = b[b["root"] == root].sort_values("ts")
    return s["ts"].to_numpy(), s["close"].to_numpy(), s["contract"].to_numpy()


def last_at(ts_arr, px_arr, t):
    i = np.searchsorted(ts_arr, t, side="right") - 1
    return (px_arr[i], ts_arr[i]) if i >= 0 else (np.nan, None)


def first_at_or_after(ts_arr, px_arr, t, t_max):
    i = np.searchsorted(ts_arr, t, side="left")
    if i < len(ts_arr) and ts_arr[i] <= t_max:
        return px_arr[i], ts_arr[i], i
    return np.nan, None, None


def main():
    b = pd.read_parquet(OUT / "crea_1s_events.parquet")
    ev = pd.read_csv(OUT / "crea_04_status_events.csv", parse_dates=["start_et", "resume_et"])
    ev = ev[(ev["start_et"] >= "2019-05-01") & (ev["start_et"] < "2024-01-01") & (ev["secs"] >= 1) & (ev["secs"] <= 120)]
    res = {}
    for mic in ["MNQ", "MES"]:
        mts, mpx, mcon = series(b, mic); pts, ppx, pcon = series(b, PARENT[mic])
        e = ev[ev["root"] == mic].copy()
        e["r_utc"] = e["resume_et"].dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
        e["s_utc"] = e["start_et"].dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
        e = e.dropna(subset=["r_utc"]).drop_duplicates("r_utc").sort_values("r_utc")
        rows = []
        for r in e.itertuples():
            rt = np.int64(r.r_utc.value); st = np.int64(r.s_utc.value)
            px0, t0, i0 = first_at_or_after(mts, mpx, rt + 2_000_000_000, rt + 60_000_000_000)
            if i0 is None or mcon[i0] != r.contract:
                continue
            pp0, pt0 = last_at(pts, ppx, t0)
            if not np.isfinite(pp0) or (t0 - pt0) > 30_000_000_000:
                continue
            # pre-pause prices: micro last trade before the pause start, parent at that second
            pre_m, _ = last_at(mts, mpx, st - 1); pre_p, _ = last_at(pts, ppx, st - 1)
            rec = dict(mic=mic, start_et=r.start_et, secs=r.secs, entry_lag_s=(t0 - rt) / 1e9, px0=px0, pp0=pp0, basis_ticks=(px0 - pp0) / TICK,
                       pre_basis_ticks=(pre_m - pre_p) / TICK if np.isfinite(pre_m) and np.isfinite(pre_p) else np.nan,
                       sweep_ticks=(pre_m - px0) / TICK if np.isfinite(pre_m) else np.nan, parent_move_during_ticks=(pp0 - pre_p) / TICK if np.isfinite(pre_p) else np.nan)
            sd = -np.sign(px0 - pp0)
            for H in HS:
                pxH, tH = last_at(mts, mpx, t0 + H * 1_000_000_000)
                ppH, _ = last_at(pts, ppx, t0 + H * 1_000_000_000)
                ok = tH is not None and tH > t0 - 1 and (t0 + H * 1_000_000_000 - tH) < 120_000_000_000
                rec[f"g{H}"] = sd * (pxH - px0) * MULT[mic] if ok else np.nan
                rec[f"gp{H}"] = sd * (ppH - pp0) * MULT[mic] if ok else np.nan
                rec[f"db{H}"] = ((pxH - ppH) - (px0 - pp0)) / TICK if ok else np.nan
            rows.append(rec)
        T = pd.DataFrame(rows)
        if len(T) == 0:
            print(mic, "none"); continue
        T["year"] = T["start_et"].dt.year; T["rth"] = (T["start_et"].dt.strftime("%H:%M") >= "09:30") & (T["start_et"].dt.strftime("%H:%M") < "16:00")
        ab = T["basis_ticks"].abs()
        out = dict(mic=mic, n=len(T), per_year=round(len(T) / 4.65, 1), years=T.groupby("year").size().to_dict(), rth_share=round(float(T["rth"].mean()), 2),
                   entry_lag_s_median=round(float(T["entry_lag_s"].median()), 1),
                   basis_abs_ticks=dict(p25=float(ab.quantile(.25)), p50=float(ab.median()), p75=float(ab.quantile(.75)), p90=float(ab.quantile(.9)), mean=round(float(ab.mean()), 2),
                                        share_ge2=round(float((ab >= 2).mean()), 2), share_ge4=round(float((ab >= 4).mean()), 2), share_ge6=round(float((ab >= 6).mean()), 2)),
                   pre_basis_abs_median=float(T["pre_basis_ticks"].abs().median()), sweep_ticks_abs_median=float(T["sweep_ticks"].abs().median()),
                   parent_move_during_abs_median=float(T["parent_move_during_ticks"].abs().median()))
        Tb = T[ab >= 1]
        for H in HS:
            out[f"H{H}"] = dict(trade_vs_basis_ge1=stats(Tb[f"g{H}"], COST[mic]), trade_vs_basis_ge2=stats(T.loc[ab >= 2, f"g{H}"], COST[mic]),
                                trade_vs_basis_ge4=stats(T.loc[ab >= 4, f"g{H}"], COST[mic]), parent_same_side_ge2=stats(T.loc[ab >= 2, f"gp{H}"], COST[mic]),
                                basis_closed_share_ge2=round(float((np.sign(T.loc[ab >= 2, f"db{H}"]) == -np.sign(T.loc[ab >= 2, "basis_ticks"])).mean()), 2),
                                rth_ge2=stats(T.loc[(ab >= 2) & T["rth"], f"g{H}"], COST[mic]), off_ge2=stats(T.loc[(ab >= 2) & ~T["rth"], f"g{H}"], COST[mic]))
        out["years_g60_ge2"] = {int(y): [len(g), round(float(g["g60"].mean()), 2)] for y, g in T[ab >= 2].groupby("year")}
        # control: pre-event seconds with |basis| >= 2 ticks (no pause), same rule
        ctl = []
        rng = np.random.default_rng(1)
        for r in e.itertuples():
            st = np.int64(r.s_utc.value)
            for k in range(3):
                t = st - np.int64(rng.integers(300, 600)) * 1_000_000_000
                px0, t0, i0 = first_at_or_after(mts, mpx, t, t + 30_000_000_000)
                if i0 is None:
                    continue
                pp0, pt0 = last_at(pts, ppx, t0)
                if not np.isfinite(pp0) or abs(px0 - pp0) < 2 * TICK:
                    continue
                sd = -np.sign(px0 - pp0); rec = {}
                for H in HS:
                    pxH, tH = last_at(mts, mpx, t0 + H * 1_000_000_000)
                    rec[f"g{H}"] = sd * (pxH - px0) * MULT[mic] if tH is not None and tH > t0 - 1 else np.nan
                ctl.append(rec)
        C = pd.DataFrame(ctl)
        out["control_pre_event_basis_ge2"] = {f"H{H}": stats(C[f"g{H}"], COST[mic]) for H in HS} if len(C) else {}
        res[mic] = out
        print(json.dumps(out, indent=1, default=str), flush=True)
        T.to_csv(OUT / f"crea_13_{mic}_1s.csv", index=False)
    (OUT / "crea_13_micro_pause_1s.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
