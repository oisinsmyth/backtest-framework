"""Shared helpers: a 'clock test' of pressure-into / response-after a fixed UTC (or ET) clock on a 1-minute panel.

panel: DataFrame with columns root, day (ET session/calendar day str), et (naive ET Timestamp, minute), contract, close.
clock_test(panel_root, clock_hhmm, tz, pre, post, mult, cost, ...) -> dict of statistics + trades frame.
The predictor x is the move over the `pre` minutes INTO the clock (known at the clock); the response y is the move over
the `post` minutes AFTER it. Fade: side = -sign(x); gross = side * y * mult (dollars per one micro). Rotation null:
pair x of day s with y of day s+k. All inputs <= 2023-12-31 (callers assert).
"""
import numpy as np
import pandas as pd


def to_utc_hhmm(et_naive: pd.Series) -> pd.Series:
    t = et_naive.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
    return t


def clock_prices(df: pd.DataFrame, clock: str, tz: str, offsets_min: list[int]) -> pd.DataFrame:
    """For each ET session day, the close at clock+offset minutes (clock given in `tz`), using the LAST bar at or before
    that minute within 3 minutes (bars print only when trading). Returns a frame indexed by day with one column per offset
    and the contract at the clock. tz 'UTC' for Beijing/Tokyo/London clocks (converted by the caller), 'America/New_York'
    for ET clocks."""
    d = df.copy()
    if tz == "UTC":
        ts = d["et"].dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC")
        d["tkey"] = ts.dt.tz_localize(None)
        # the calendar day in UTC of the bar, the clock on that UTC day
        d["cday"] = d["tkey"].dt.normalize()
    else:
        d["tkey"] = d["et"]
        d["cday"] = d["et"].dt.normalize()
    d = d.dropna(subset=["tkey"])
    hh, mm = map(int, clock.split(":"))
    base = d["cday"] + pd.Timedelta(hours=hh, minutes=mm)
    d["off"] = ((d["tkey"] - base).dt.total_seconds() // 60).astype(int)
    out = {}
    for o in offsets_min:
        sel = d[(d["off"] <= o) & (d["off"] > o - 4)]
        last = sel.sort_values("tkey").groupby("cday").tail(1).set_index("cday")
        out[o] = last["close"]
        if o == 0:
            out["contract"] = last["contract"]
            out["day"] = last["day"]
    res = pd.DataFrame(out)
    return res


def clock_test(df: pd.DataFrame, clock: str, tz: str, pre: int, post: int, mult: float, cost: float,
               exclude_days=None, min_abs_x=None, label="") -> dict:
    offs = sorted({-pre, 0, post})
    P = clock_prices(df, clock, tz, offs)
    P = P.dropna()
    if exclude_days is not None:
        P = P[~P["day"].isin(set(exclude_days))]
    x = (P[0] - P[-pre]).to_numpy(); y = (P[post] - P[0]).to_numpy()
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]; days = P["day"].to_numpy()[ok]
    n = len(x)
    if n < 50:
        return dict(label=label, n=n)
    rho = np.corrcoef(x, y)[0, 1]
    side = -np.sign(x)
    g = side * y * mult
    if min_abs_x is not None:
        thr = np.quantile(np.abs(x), min_abs_x)
        m = np.abs(x) >= thr
    else:
        m = x != 0
    gm = g[m]; dm = days[m]
    # rotation null of the sign against the response
    rot = np.array([np.mean((side[m] * np.roll(y, k)[m]) * mult) for k in range(1, min(301, n))])
    yrs = pd.Series(gm, index=pd.to_datetime(dm).year).groupby(level=0).agg(["count", "mean", "sum"])
    top = int(np.argmax(gm))
    q = np.quantile(gm, [0.01, 0.99])
    return dict(label=label, n=int(m.sum()), n_all=n, rho=float(rho), rho_t=float(rho * np.sqrt(n - 2) / np.sqrt(1 - rho**2)),
                sd_y_usd=float(np.std(y) * mult), mean_abs_y_usd=float(np.mean(np.abs(y)) * mult),
                gross=float(gm.mean()), gross_t=float(gm.mean() / gm.std() * np.sqrt(len(gm))), median=float(np.median(gm)),
                net=float(gm.mean() - cost), cost=cost, win=float((gm > 0).mean()),
                trim_ex_top=float(gm[gm <= q[1]].mean()), trim_ex_bottom=float(gm[gm >= q[0]].mean()), trim_both=float(gm[(gm >= q[0]) & (gm <= q[1])].mean()),
                rot_p50=float(np.median(rot)), rot_p95=float(np.quantile(rot, 0.95)), rot_share_ge=float((rot >= gm.mean()).mean()),
                years={int(k): [int(v["count"]), round(float(v["mean"]), 2), round(float(v["sum"]), 0)] for k, v in yrs.iterrows()},
                top_trade=dict(day=str(dm[top]), gross=float(gm[top]), x=float(x[m][top])),
                long_mean=float(gm[side[m] > 0].mean()) if (side[m] > 0).any() else None,
                short_mean=float(gm[side[m] < 0].mean()) if (side[m] < 0).any() else None)


def fmt(r: dict) -> str:
    if "rho" not in r:
        return f"{r.get('label')}: n={r.get('n')} (too few)"
    return (f"{r['label']:38s} n={r['n']:5d} rho={r['rho']:+.3f} (t {r['rho_t']:+.1f}) sd_y=${r['sd_y_usd']:.1f} "
            f"gross=${r['gross']:+.2f} (t {r['gross_t']:+.1f}) med=${r['median']:+.2f} net=${r['net']:+.2f} win={r['win']:.2f} "
            f"rot p50/p95=${r['rot_p50']:+.2f}/${r['rot_p95']:+.2f} share>={r['rot_share_ge']:.2f} "
            f"L/S=${r['long_mean']:+.2f}/${r['short_mean']:+.2f} years={r['years']} top={r['top_trade']}")
