"""C22: the Shanghai-shut windows inside the Asian day. SHFE's day session breaks 11:30-13:30 Beijing (lunch) and closes
15:00 -> 21:00 Beijing (night open). COMEX metals keep trading while Shanghai is shut; does a move made in a Shanghai-shut
window revert once Shanghai reopens (Lead 1-3's family: shocks absorbed while the main venue is shut)?
W1 lunch: m = P(13:30 BJ) - P(11:30 BJ); fade from 13:35 BJ to 15:00 BJ and to 08:00 ET.
W2 afternoon gap: m = P(21:00 BJ) - P(15:00 BJ); fade from 21:05 BJ to 11:00 ET / 13:00 ET.
Placebo: the same clocks on China exchange holidays (CME open, Shanghai shut all day). GC/SI/HG, 2016-2023 (seal).
Prices: close of the bar before the clock, from fut_opening_globex_1m_* (et column, naive ET)."""
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
CAL = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674\data\calendar\china_exchange_holidays.csv"
SEAL = "2024-01-01"
hol = set(pd.read_csv(CAL).date)
BJ, NY = ZoneInfo("Asia/Shanghai"), ZoneInfo("America/New_York")
CASES = {"GC": ("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", 10.0, 5.93), "SI": ("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", 1000.0, 8.0),
         "HG": ("fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz", 2500.0, 4.25)}
cache = {}


def book(f, lab):
    f = f.dropna()
    if len(f) < 20:
        return f"{lab} n{len(f)}"
    yrs = f.groupby(f.index.str[:4]).mean()
    return f"{lab} n{len(f)} ${f.mean():+.2f} med {f.median():+.2f} t {f.mean() / f.std() * np.sqrt(len(f)):+.2f} yrs>0 {(yrs > 0).sum()}/{len(yrs)}"


for root, (fn, usd, rt) in CASES.items():
    if fn not in cache:
        d = pd.read_csv(f"{FXD}\\{fn}", usecols=["root", "session", "et", "close"])
        cache[fn] = d[(d.session >= "2016-01-01") & (d.session < SEAL)]
    d = cache[fn][cache[fn].root == root].copy()
    assert d.session.max() < SEAL
    d["et"] = pd.to_datetime(d.et)
    sess = pd.to_datetime(d.session)
    d = d[(d.et >= sess - pd.Timedelta(hours=6)) & (d.et < sess + pd.Timedelta(hours=17))]
    s = d.drop_duplicates("et").set_index("et").close.sort_index()

    def px(ts):
        i = s.index.searchsorted(ts) - 1  # last bar starting before ts
        return s.iloc[i] if i >= 0 and (ts - s.index[i]) <= pd.Timedelta(minutes=10) else np.nan
    rows = []
    for dd in sorted(set(d.session)):
        D = pd.Timestamp(dd)
        if D.dayofweek > 4:
            continue
        def bj(h, m, day=D):
            return pd.Timestamp(year=day.year, month=day.month, day=day.day, hour=h, minute=m, tz=BJ).tz_convert(NY).tz_localize(None)
        r = {"day": dd, "hol": dd in hol}
        a, b, e = px(bj(11, 30)), px(bj(13, 30)), px(bj(13, 35))
        r["m1"] = b - a
        r["y1a"] = px(bj(15, 0)) - e
        r["y1b"] = px(pd.Timestamp(dd + " 08:00")) - e
        a2, b2, e2 = px(bj(15, 0)), px(bj(21, 0)), px(bj(21, 5))
        r["m2"] = b2 - a2
        r["y2a"] = px(pd.Timestamp(dd + " 11:00")) - e2 if bj(21, 5).hour < 11 else np.nan
        r["y2b"] = px(pd.Timestamp(dd + " 13:00")) - e2
        rows.append(r)
    R = pd.DataFrame(rows).set_index("day")
    print(f"== {root} (RT ${rt}) days {len(R)}, China-holiday weekdays {int(R.hol.sum())}")
    for w, ys in [("m1 lunch", ["y1a", "y1b"]), ("m2 15:00->21:00 BJ", ["y2a", "y2b"])]:
        m = R[w.split()[0]]
        g = (m.abs() >= m.abs().shift(1).rolling(250, min_periods=120).quantile(0.8)) & (m != 0)
        for y in ys:
            f = -np.sign(m) * R[y] * usd
            print(f"   {w} {y}: " + book(f[g & ~R.hol], "SHFE days q80") + " | " + book(f[~R.hol & (m != 0)], "all") + " | " + book(f[R.hol & (m != 0)], "CN-holiday placebo all"))
