"""On-disk premise proxy for L5-IMB: does KNOWN large closing-auction demand lift Lead 4's capture? Nights whose close carries
predictably huge MOC volume (month-end, quarter-end, quad witching / index rebalance Fridays; cme_session_calendar flags) vs
ordinary nights. Capture = fade P&L / |c|, c = P(16:00)-P(15:50); fade 18:05 -> 10:00 next session. q80 gate on |c| AND all
nights. Also capture by |c| quintile (does a bigger push revert proportionally more?). NQ/ES/RTY/YM 2016-2023 (seal)."""
import numpy as np, pandas as pd

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"
cal = pd.read_csv(f"{FXD}\\cme_session_calendar.csv.gz", usecols=["root", "day", "month_end", "quarter_end", "quad_witching"])
CASES = {"NQ": ("fut_opening_globex_1m.csv.gz", 2.0), "ES": ("fut_opening_globex_1m.csv.gz", 5.0),
         "RTY": ("fut_opening_globex_1m_ym_rty.csv.gz", 5.0), "YM": ("fut_opening_globex_1m_ym_rty.csv.gz", 0.5)}
cache = {}
for root, (fn, usd) in CASES.items():
    if fn not in cache:
        d = pd.read_csv(f"{FXD}\\{fn}", usecols=["root", "session", "hhmm", "close"])
        cache[fn] = d[(d.session >= "2016-01-01") & (d.session < SEAL) & d.hhmm.isin({"15:49", "15:59", "18:04", "09:59"})]
    d = cache[fn][cache[fn].root == root]
    assert d.session.max() < SEAL
    P = d.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    N = P.shift(-1)
    ok = (pd.to_datetime(pd.Series(P.index).shift(-1)) - pd.to_datetime(pd.Series(P.index))).dt.days.values <= 4
    c = (P["15:59"] - P["15:49"]) * usd
    y = ((N["09:59"] - N["18:04"]) * usd).where(ok)
    f = -np.sign(c) * y
    cr = cal[cal.root == ("ES" if root in ("ES", "NQ", "YM", "RTY") else root)].set_index("day").reindex(P.index)
    big = (cr.month_end.fillna(False).astype(bool) | cr.quarter_end.fillna(False).astype(bool) | cr.quad_witching.fillna(False).astype(bool))
    g80 = c.abs() >= c.abs().shift(1).rolling(250, min_periods=120).quantile(0.8)
    D = pd.DataFrame({"f": f, "ac": c.abs(), "big": big, "g": g80}).dropna()
    D = D[(D.index >= "2017-01-01") & (D.ac > 0)]
    def cap(S):
        return f"n{len(S)} ${S.f.mean():+.2f} capture {S.f.sum() / S.ac.sum():+.3f} t {S.f.mean() / S.f.std() * np.sqrt(len(S)):+.2f}"
    q = pd.qcut(D.ac.rank(method="first"), 5, labels=False)
    print(f"{root}: big-MOC nights {cap(D[D.big])} | ordinary {cap(D[~D.big])} || q80 & big {cap(D[D.g & D.big])} | q80 & ordinary {cap(D[D.g & ~D.big])}")
    print("   capture by |c| quintile: " + " ".join(f"Q{k}:{D[q == k].f.sum() / D[q == k].ac.sum():+.3f}" for k in range(5)))
