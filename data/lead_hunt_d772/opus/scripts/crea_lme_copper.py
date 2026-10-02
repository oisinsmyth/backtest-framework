"""C17: the LME copper official price (2nd ring 12:30-12:35 London) and the LME closing price (kerb close ~17:00 London):
physical contracts and hedges price off them, so pressure into the window should revert after it (the AITODO's untried
'copper LME fix'). London clock converted to ET per date (zoneinfo), so DST-mismatch weeks are handled.
x = P(window end) - P(window end - 30 min); fade from window end + 1 min to +30/+60/+120 min. One MHG ($2500/pt, RT $4.25).
Placebo: the same construction at London 11:30 and 14:00 (no fix). fut_opening_globex_1m_ho_rb_bz_hg_pl, 2016-2023 (seal)."""
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo

FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures\fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz"
SEAL = "2024-01-01"
d = pd.read_csv(FX, usecols=["root", "session", "et", "close"])
d = d[(d.root == "HG") & (d.session >= "2016-01-01") & (d.session < SEAL)]
assert d.session.max() < SEAL
d["et"] = pd.to_datetime(d.et)
sess = pd.to_datetime(d.session)
d = d[(d.et >= sess - pd.Timedelta(hours=6)) & (d.et < sess + pd.Timedelta(hours=17))]
d["date"] = d.et.dt.date
s = d.set_index("et").close
s = s[~s.index.duplicated()]
LON, NY = ZoneInfo("Europe/London"), ZoneInfo("America/New_York")
days = sorted(set(d.date))
usd = 2500.0


def px(ts):
    # price at time ts = close of the bar starting ts-1min
    return s.get(ts - pd.Timedelta(minutes=1), np.nan)


for lab, hh, mm in [("LME 2nd ring end 12:35", 12, 35), ("LME close 17:00", 17, 0), ("placebo 11:30", 11, 30), ("placebo 14:00", 14, 0)]:
    rows = []
    for dd in days:
        if pd.Timestamp(dd).dayofweek > 4:
            continue
        t_end = pd.Timestamp(year=dd.year, month=dd.month, day=dd.day, hour=hh, minute=mm, tz=LON).tz_convert(NY).tz_localize(None)
        p0, p1 = px(t_end - pd.Timedelta(minutes=30)), px(t_end)
        pe = px(t_end + pd.Timedelta(minutes=1))
        r = {"day": str(dd), "x": p1 - p0}
        for k in (30, 60, 120):
            r[f"y{k}"] = px(t_end + pd.Timedelta(minutes=1 + k)) - pe
        rows.append(r)
    R = pd.DataFrame(rows).dropna()
    R = R[R.x != 0]
    thr = R.x.abs().shift(1).rolling(250, min_periods=120).quantile(0.8)
    out = []
    for k in (30, 60, 120):
        f = -np.sign(R.x) * R[f"y{k}"] * usd
        fb = f[R.x.abs() >= thr]
        rho = R[["x", f"y{k}"]].rank().corr().iloc[0, 1]
        out.append(f"+{k}m: rho {rho:+.3f} all ${f.mean():+.2f} | q80 n{len(fb)} ${fb.mean():+.2f} t {fb.mean() / fb.std() * np.sqrt(len(fb)):+.2f}")
    print(f"{lab:24s} n{len(R)} mean|x| ${R.x.abs().mean() * usd:.1f} :: " + " | ".join(out))
