"""C26 score, as declared to the conservative before any number was seen.
Per series (family, expiry E): OI by strike = last publication per option before E 09:00 ET (usable at E). U = underlying.
K* = argmax (call+put OI) over strikes within +-3% of U's last settlement before E. d = K* - settle_U.
Traded contract T = the fut_day1m front on E; must differ from U for monthly LO/ON; weeklies may trade U if E is > 10 calendar
days before U's monthly option expiry. x = P(14:30) - P(09:01) on T (closes of bars 14:29 and 09:00). toward = sign(x) == sign(d).
PRIMARY: fade x when toward, 14:35 -> 16:00 on E. SECONDARY: 18:05 E -> 14:30 E+1 (fut_opening_globex). Splits toward / away.
Null A (partner's): the same-clock unconditional fade of x on non-expiry days (all days not an expiry of any series of the root).
Null B: same series, same K*, business days E-5..E-2 (d recomputed from the prior settle), toward-only fade.
MCL $100/pt RT $5.03; MNG $1000/pt RT $4.00 (one-tick line). 2016-2023 (seal asserted)."""
import pickle
from pathlib import Path
import numpy as np, pandas as pd, pyarrow.parquet as pq

OUT = Path(__file__).resolve().parents[1] / "out"
FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"
oi = pickle.loads((OUT / "crea_pin_oi.pkl").read_bytes())
oi = oi[oi.expiry_date < SEAL]
oi["root"] = np.where(oi.family.str.startswith("LO"), "CL", "NG")
oi["monthly"] = oi.family.isin(["LO", "ON"])
oi["et"] = pd.to_datetime(oi.ts_event, utc=True).dt.tz_convert("US/Eastern").dt.tz_localize(None)
strip = pd.read_csv(f"{FXD}\\fut_settle_strip.csv.gz")
strip = strip[strip.root.isin(["CL", "NG"]) & (strip.ref < SEAL)]
sett = {k: g.set_index("ref").settle.sort_index() for k, g in strip.groupby("contract")}
USD = {"CL": (100.0, 5.03), "NG": (1000.0, 4.00)}
day = pq.read_table(f"{FXD}\\fut_day1m.parquet", filters=[("root", "in", ["CL", "NG"]), ("day", ">=", "2016-01-01"), ("day", "<", SEAL)],
                    columns=["root", "day", "bar", "close", "contract"]).to_pandas()
assert day.day.max() < SEAL
front = day.groupby(["root", "day"]).contract.first()
PX = {r: g.pivot_table(index="day", columns="bar", values="close", aggfunc="last").reindex(columns=range(420)).ffill(axis=1) for r, g in day.groupby("root")}
glob = pd.read_csv(f"{FXD}\\fut_opening_globex_1m_cl_ng_gc_si.csv.gz", usecols=["root", "session", "hhmm", "close"])
glob = glob[glob.root.isin(["CL", "NG"]) & (glob.session >= "2016-01-01") & (glob.session < SEAL) & glob.hhmm.isin(["18:04", "14:29"])]
G = {r: g.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last") for r, g in glob.groupby("root")}
bh = pd.read_csv(f"{FXD}\\fut_breadth_hourly.csv.gz", usecols=["root", "day", "same_front"])
bh = bh[bh.root.isin(["CL", "NG"]) & (bh.day < SEAL)]
roll_day = set(zip(bh.root[~bh.same_front.astype(bool)], bh.day[~bh.same_front.astype(bool)]))
monthly_exp = oi[oi.monthly].groupby("underlying").expiry_date.max().to_dict()
bar = lambda hm: int(hm[:2]) * 60 + int(hm[3:]) - 540
rows = []
for (fam, E, U), g in oi.groupby(["family", "expiry_date", "underlying"]):
    root = "CL" if fam.startswith("LO") else "NG"
    pre = g[g.et < pd.Timestamp(E + " 09:00")]
    if pre.empty or U not in sett:
        continue
    last = pre.sort_values("et").groupby("raw_symbol").tail(1)
    byK = last.groupby("strike").oi.sum()
    s_prev = sett[U][sett[U].index < E]
    if s_prev.empty:
        continue
    S0 = s_prev.iloc[-1]
    near = byK[(byK.index / S0 - 1).__abs__() <= 0.03]
    if near.empty or near.max() <= 0:
        continue
    K = near.idxmax(); d = K - S0
    if (root, E) not in front.index or E not in PX[root].index or (root, E) in roll_day:
        continue
    T = front[(root, E)]
    if fam in ("LO", "ON") and T == U:
        continue
    if fam not in ("LO", "ON") and T == U:
        me = monthly_exp.get(U)
        if me is None or (pd.Timestamp(me) - pd.Timestamp(E)).days <= 10:
            continue
    P = PX[root].loc[E]
    x = P[bar("14:29")] - P[bar("09:00")]
    y1 = P[bar("15:59")] - P[bar("14:34")]
    nxt = PX[root].index[PX[root].index > E]
    y2 = np.nan
    if len(nxt) and nxt[0] in G[root].index:
        gn = G[root].loc[nxt[0]]
        y2 = gn.get("14:29", np.nan) - gn.get("18:04", np.nan)
    usd = USD[root][0]
    rows.append(dict(root=root, fam=fam, monthly=fam in ("LO", "ON"), E=E, U=U, T=T, K=K, d=d, x=x,
                     toward=np.sign(x) == np.sign(d) and x != 0 and d != 0, f1=-np.sign(x) * y1 * usd, f2=-np.sign(x) * y2 * usd,
                     pinned=abs(sett[U].get(E, np.nan) - K) < abs(d), oiK=near.max()))
R = pd.DataFrame(rows)
print("series scored:", len(R), R.groupby(["root", "monthly"]).size().to_dict())
print("share where U settled closer to K* on E than the day before (pin check):", R.groupby(["root", "monthly"]).pinned.mean().round(3).to_dict())


def st(f, lab):
    f = f.dropna()
    if len(f) < 5:
        return f"{lab} n{len(f)}"
    yrs = f.groupby(f.index.str[:4]).mean() if hasattr(f.index, "str") else None
    return f"{lab} n{len(f)} ${f.mean():+.2f} med {f.median():+.2f} t {f.mean() / (f.std() + 1e-12) * np.sqrt(len(f)):+.2f}" + (f" yrs>0 {(yrs > 0).sum()}/{len(yrs)}" if yrs is not None else "")


R = R.set_index("E")
for (root, mon), g in R.groupby(["root", "monthly"]):
    lab = f"{root} {'monthly' if mon else 'weekly'} (RT ${USD[root][1]})"
    print(f"\n{lab}: PRIMARY toward 14:35->16:00 " + st(g.f1[g.toward], "") + " | away " + st(g.f1[~g.toward], "") +
          f"\n   SECONDARY toward 18:05->14:30 E+1 " + st(g.f2[g.toward], "") + " | away " + st(g.f2[~g.toward], ""))
# Null A: unconditional same-clock fade of x on non-expiry days
for root in ("CL", "NG"):
    usd = USD[root][0]; P = PX[root]
    exps = set(R[R.root == root].index)
    x = P[bar("14:29")] - P[bar("09:00")]; y = P[bar("15:59")] - P[bar("14:34")]
    f = (-np.sign(x) * y * usd)[~P.index.isin(list(exps)) & (x != 0)]
    print(f"Null A {root}: same-clock fade on non-expiry days " + st(f, ""))
