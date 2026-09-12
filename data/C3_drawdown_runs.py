"""C3 lane measurement: drawdown shape of a LONG-ONLY characteristic tilt vs the market
and vs the long-short spread, on Ken French monthly data.

Controls required by the campaign contract:
  - sentinel census: count of -99.99 / -999 in every block actually used (must be 0 after slice)
  - block proof: print the header line and line-range of the block read
  - negative control: RF cumulative series must have max drawdown exactly 0.0
  - positive control: reproduce a published table figure (Fama-French 2015 Table 1 means)
"""
import io, os, sys, math
import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
FR = os.path.join(D, "C3_french")

SENT = (-99.99, -999.0, -99.99e0)


def read_blocks(path):
    """Return list of (header_text, header_line_no, colnames, dates[list of str], data[np 2d])."""
    with open(path, "r", encoding="latin-1") as f:
        lines = f.read().split("\n")
    blocks = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        # a column-header line starts with ',' and the line above (skipping blanks) is a title
        if ln.startswith(",") and len(ln.split(",")) > 2:
            # find title: nearest preceding non-blank line
            j = i - 1
            while j >= 0 and lines[j].strip() == "":
                j -= 1
            title = lines[j].strip() if j >= 0 else "<none>"
            cols = [c.strip() for c in ln.split(",")[1:]]
            dates, rows = [], []
            k = i + 1
            while k < len(lines):
                s = lines[k].strip()
                if s == "":
                    break
                parts = s.split(",")
                if not parts[0].strip().isdigit():
                    break
                dates.append(parts[0].strip())
                rows.append([float(x) for x in parts[1:]])
                k += 1
            if rows:
                blocks.append(dict(title=title, hdr_line=i + 1, first_data_line=i + 2,
                                   last_data_line=k, cols=cols, dates=dates,
                                   data=np.array(rows, dtype=float)))
            i = k
        else:
            i += 1
    return blocks


def pick(blocks, title_substr, freq="monthly"):
    """Pick the block whose title contains title_substr; freq monthly=YYYYMM dates, annual=YYYY."""
    cands = []
    for b in blocks:
        if title_substr.lower() in b["title"].lower():
            dl = len(b["dates"][0])
            if (freq == "monthly" and dl == 6) or (freq == "annual" and dl == 4):
                cands.append(b)
    if len(cands) != 1:
        raise SystemExit(f"block pick ambiguous/absent for {title_substr!r} {freq}: {len(cands)}")
    return cands[0]


def sentinel_census(b, cols=None):
    d = b["data"]
    n99 = int(np.sum(np.isclose(d, -99.99)))
    n999 = int(np.sum(np.isclose(d, -999.0)))
    return n99, n999


def to_series(b, colname):
    j = b["cols"].index(colname)
    return np.array(b["dates"]), b["data"][:, j]


def align(dates_list, series_list):
    common = set(dates_list[0])
    for d in dates_list[1:]:
        common &= set(d)
    common = np.array(sorted(common))
    out = []
    for d, s in zip(dates_list, series_list):
        idx = {k: i for i, k in enumerate(d)}
        out.append(np.array([s[idx[c]] for c in common]))
    return common, out


# ---------- drawdown machinery ----------

def nav_from_pct(r_pct):
    """r_pct monthly returns in PERCENT -> NAV starting at 1.0, length n+1 (t=0 is 1.0)."""
    return np.concatenate([[1.0], np.cumprod(1.0 + r_pct / 100.0)])


def drawdown_series(nav):
    peak = np.maximum.accumulate(nav)
    return nav / peak - 1.0


def episodes(nav, dates):
    """Distinct drawdown episodes. dates: array of YYYYMM aligned to nav[1:].
    Returns list of dicts: peak_date, trough_date, recovery_date(or None), depth,
    months_peak_to_trough, months_trough_to_recovery, months_underwater."""
    n = len(nav)
    peak = np.maximum.accumulate(nav)
    eps = []
    i = 1
    dt = ["t0"] + list(dates)
    while i < n:
        if nav[i] < peak[i] - 1e-15:
            start = i - 1  # last index at the peak
            # walk to recovery
            j = i
            trough = i
            while j < n and nav[j] < nav[start] - 1e-15:
                if nav[j] < nav[trough]:
                    trough = j
                j += 1
            rec = j if j < n else None
            eps.append(dict(
                peak_i=start, trough_i=trough, rec_i=rec,
                peak_date=dt[start], trough_date=dt[trough],
                rec_date=(dt[rec] if rec is not None else None),
                depth=nav[trough] / nav[start] - 1.0,
                m_to_trough=trough - start,
                m_to_recover=(rec - trough) if rec is not None else None,
                m_underwater=(rec - start) if rec is not None else (n - 1 - start),
                ongoing=(rec is None),
            ))
            i = j if rec is not None else n
        else:
            i += 1
    return eps


def dd_report(name, r_pct, dates, topn=5):
    nav = nav_from_pct(r_pct)
    eps = sorted(episodes(nav, dates), key=lambda e: e["depth"])
    mx = eps[0] if eps else None
    longest = max(eps, key=lambda e: e["m_underwater"]) if eps else None
    n = len(r_pct)
    ann = (nav[-1]) ** (12.0 / n) - 1.0
    vol = np.std(r_pct, ddof=1) * math.sqrt(12) / 100.0
    return dict(name=name, n=n, first=dates[0], last=dates[-1],
                cagr=ann, vol=vol, maxdd=(mx["depth"] if mx else 0.0),
                mx=mx, longest=longest, eps=eps[:topn], nav=nav)


def fmt_ep(e):
    if e is None:
        return "none"
    rec = e["rec_date"] if e["rec_date"] else "NOT RECOVERED"
    mr = e["m_to_recover"] if e["m_to_recover"] is not None else "-"
    return (f"{e['depth']*100:7.2f}%  peak {e['peak_date']} -> trough {e['trough_date']}"
            f" ({e['m_to_trough']:3d}m) -> recover {rec} ({mr}m)  underwater {e['m_underwater']:4d}m")
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from C3_dd import *

FR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C3_french")

print("=" * 100)
print("STEP 1 - BLOCK PROOF: every block in every file, with its line range")
print("=" * 100)
files = {
    "OP": "Portfolios_Formed_on_OP.csv",
    "BEME": "Portfolios_Formed_on_BE-ME.csv",
    "FF3": "F-F_Research_Data_Factors.csv",
    "FF5": "F-F_Research_Data_5_Factors_2x3.csv",
    "ME_OP_25": "25_Portfolios_ME_OP_5x5.csv",
    "ME_OP_6": "6_Portfolios_ME_OP_2x3.csv",
}
B = {}
for k, fn in files.items():
    p = os.path.join(FR, fn)
    B[k] = read_blocks(p)
    print(f"\n--- {k}: {fn}")
    for b in B[k]:
        n99, n999 = sentinel_census(b)
        print(f"    lines {b['first_data_line']:5d}-{b['last_data_line']:5d}  "
              f"rows {len(b['dates']):5d}  {b['dates'][0]}..{b['dates'][-1]}  "
              f"sent(-99.99)={n99:5d} sent(-999)={n999:5d}  ncols={len(b['cols'])}  "
              f"TITLE={b['title']!r}")
import os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from C3_dd import *

FR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C3_french")
OP = read_blocks(os.path.join(FR, "Portfolios_Formed_on_OP.csv"))
BM = read_blocks(os.path.join(FR, "Portfolios_Formed_on_BE-ME.csv"))
F3 = read_blocks(os.path.join(FR, "F-F_Research_Data_Factors.csv"))
F5 = read_blocks(os.path.join(FR, "F-F_Research_Data_5_Factors_2x3.csv"))
P25 = read_blocks(os.path.join(FR, "25_Portfolios_ME_OP_5x5.csv"))

op_vw = OP[0]; op_ew = OP[1]; op_vw_ann = OP[2]
bm_vw = BM[0]; bm_ew = BM[1]
ff3m = F3[0]; ff5m = F5[0]
p25_ew = P25[1]; p25_vw = P25[0]

print("COLS ff3m:", ff3m["cols"], " ff5m:", ff5m["cols"])
print("COLS op_vw:", op_vw["cols"])
print("COLS p25_ew:", p25_ew["cols"][:6], "...")

print("\n" + "=" * 100)
print("CONTROL A (POSITIVE, internal): compound my monthly VW decile-10 returns by calendar year")
print("  and compare to FRENCH'S OWN annual VW block. If I read the wrong block or the wrong units,")
print("  this fails.")
print("=" * 100)
d_m, hi_m = to_series(op_vw, "Hi 10")
d_a, hi_a = to_series(op_vw_ann, "Hi 10")
years = {}
for dt, r in zip(d_m, hi_m):
    years.setdefault(dt[:4], []).append(r)
worst = 0.0; nchk = 0
for y, ra in zip(d_a, hi_a):
    if y in years and len(years[y]) == 12:
        comp = (np.prod(1 + np.array(years[y]) / 100.0) - 1) * 100
        worst = max(worst, abs(comp - ra)); nchk += 1
print(f"  years checked: {nchk}   max |compounded_monthly - French_annual| = {worst:.4f} pp")
assert nchk > 55 and worst < 0.06, "POSITIVE CONTROL FAILED"
print("  PASS (agreement to rounding)")

print("\n" + "=" * 100)
print("CONTROL B (NEGATIVE): a series whose drawdown MUST be exactly zero -> cumulative RF")
print("=" * 100)
d_rf, rf = to_series(ff3m, "RF")
print(f"  RF months {len(rf)} {d_rf[0]}..{d_rf[-1]}  min monthly RF = {rf.min():.4f}%")
nav_rf = nav_from_pct(rf)
eps_rf = episodes(nav_rf, d_rf)
print(f"  max drawdown of cumulative RF = {drawdown_series(nav_rf).min()*100:.10f}%   "
      f"n episodes = {len(eps_rf)}")
if abs(drawdown_series(nav_rf).min()) < 1e-12 and len(eps_rf) == 0:
    print("  PASS (exactly zero, as it must be)")
else:
    neg = [(a, b) for a, b in zip(d_rf, rf) if b < 0]
    print("  *** CONTROL FIRED, AND IT CAUGHT A REAL DATA PROPERTY, NOT A BUG ***")
    print(f"  French's RF series has {len(neg)} NEGATIVE monthly values, all pre-war: {neg}")
    print("  So cumulative RF is NOT monotone over 1926-2026 and its drawdown is not zero.")
    print("  The control is therefore re-stated on the OP sample window (196307-202607), where")
    print("  RF is never negative and the drawdown must be - and is - exactly 0 (see C3_run3.py).")
    # the control as it must hold: strip the pre-war window
    m = np.array([x >= "196307" for x in d_rf])
    nav2 = nav_from_pct(rf[m])
    print(f"  restated: maxDD of cumulative RF on 196307-202607 = {drawdown_series(nav2).min()*100:.12f}%"
          f"  episodes={len(episodes(nav2, d_rf[m]))}")
    assert abs(drawdown_series(nav2).min()) == 0.0 and len(episodes(nav2, d_rf[m])) == 0

print("\n" + "=" * 100)
print("CONTROL C (SENTINEL CENSUS) on every slice actually used")
print("=" * 100)
for nm, b in [("OP VW monthly", op_vw), ("OP EW monthly", op_ew),
              ("BE-ME VW monthly", bm_vw), ("BE-ME EW monthly", bm_ew),
              ("FF3 monthly", ff3m), ("FF5 monthly", ff5m),
              ("25 ME_OP EW monthly", p25_ew), ("25 ME_OP VW monthly", p25_vw)]:
    n99, n999 = sentinel_census(b)
    print(f"  {nm:24s} -99.99 x{n99:4d}   -999 x{n999:4d}")
# where the BE-ME sentinels live
d = bm_vw["data"]
rr, cc = np.where(np.isclose(d, -99.99))
if len(rr):
    print(f"  BE-ME VW sentinel rows: {sorted(set(bm_vw['dates'][i] for i in rr))}")
    print(f"  BE-ME VW sentinel cols: {sorted(set(bm_vw['cols'][j] for j in cc))}")
import os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from C3_dd import *

FR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C3_french")
OP = read_blocks(os.path.join(FR, "Portfolios_Formed_on_OP.csv"))
BM = read_blocks(os.path.join(FR, "Portfolios_Formed_on_BE-ME.csv"))
F3 = read_blocks(os.path.join(FR, "F-F_Research_Data_Factors.csv"))
F5 = read_blocks(os.path.join(FR, "F-F_Research_Data_5_Factors_2x3.csv"))
P25 = read_blocks(os.path.join(FR, "25_Portfolios_ME_OP_5x5.csv"))
op_vw, op_ew, _, _, op_nf = OP[0], OP[1], OP[2], OP[3], OP[4]
bm_vw, bm_ew = BM[0], BM[1]
ff3m, ff5m = F3[0], F5[0]
p25_vw, p25_ew = P25[0], P25[1]

DEC = ['Lo 10', '2-Dec', '3-Dec', '4-Dec', '5-Dec', '6-Dec', '7-Dec', '8-Dec', '9-Dec', 'Hi 10']

# ---- build the common monthly grid on the OP sample 196307..202607
dates = np.array(op_vw["dates"])
assert list(dates) == list(op_ew["dates"]) == list(ff5m["dates"]) == list(p25_vw["dates"])
idx3 = {d: i for i, d in enumerate(ff3m["dates"])}
sel3 = np.array([idx3[d] for d in dates])
idxb = {d: i for i, d in enumerate(bm_vw["dates"])}
selb = np.array([idxb[d] for d in dates])

col = lambda b, c: b["data"][:, b["cols"].index(c)]
rf = col(ff3m, "RF")[sel3]
mktrf = col(ff3m, "Mkt-RF")[sel3]
MKT = mktrf + rf                      # value-weighted total market, total return %
RMW = col(ff5m, "RMW")
HML = col(ff5m, "HML")
SMB = col(ff5m, "SMB")

# EW universe from the Number-of-Firms block (true equal-weight across all names)
nf = np.array([col(op_nf, c) for c in DEC]).T           # 757 x 10
rw = np.array([col(op_ew, c) for c in DEC]).T
rv = np.array([col(op_vw, c) for c in DEC]).T
assert (nf > 0).all()
EWUNI = (nf * rw).sum(axis=1) / nf.sum(axis=1)

HI_VW, LO_VW = col(op_vw, "Hi 10"), col(op_vw, "Lo 10")
HI_EW, LO_EW = col(op_ew, "Hi 10"), col(op_ew, "Lo 10")
HI20_VW, LO20_VW = col(op_vw, "Hi 20"), col(op_vw, "Lo 20")
HI30_VW, HI30_EW = col(op_vw, "Hi 30"), col(op_ew, "Hi 30")
SPREAD_VW = HI_VW - LO_VW
SPREAD_EW = HI_EW - LO_EW
SMALLHI_EW = col(p25_ew, "SMALL HiOP")
SMALLHI_VW = col(p25_vw, "SMALL HiOP")
BIGHI_VW = col(p25_vw, "BIG HiOP")
VAL_VW = col(bm_vw, "Hi 10")[selb]     # value decile (high BE/ME)
VAL_EW = col(bm_ew, "Hi 10")[selb]
assert not np.isclose(VAL_VW, -99.99).any() and not np.isclose(VAL_EW, -99.99).any()

# NEGATIVE CONTROL on this window: RF drawdown must be exactly 0 here
nav_rf = nav_from_pct(rf)
print(f"[NEG CTRL] cumulative RF max drawdown on 196307-202607 = "
      f"{drawdown_series(nav_rf).min()*100:.12f}%  episodes={len(episodes(nav_rf,dates))}  "
      f"min monthly RF={rf.min():.4f}%")
assert abs(drawdown_series(nav_rf).min()) == 0.0 and len(episodes(nav_rf, dates)) == 0

SERIES = [
    ("MKT  value-weighted market (total ret)", MKT),
    ("EWUNI equal-wtd all-name universe", EWUNI),
    ("OP d10 VW  (long-only tilt, VW)", HI_VW),
    ("OP d10 EW  (long-only tilt, EW)", HI_EW),
    ("OP top30% VW", HI30_VW),
    ("OP top30% EW", HI30_EW),
    ("OP d1 VW (short leg, held long)", LO_VW),
    ("OP d1 EW (short leg, held long)", LO_EW),
    ("SMALL HiOP EW (small+profitable)", SMALLHI_EW),
    ("SMALL HiOP VW", SMALLHI_VW),
    ("BIG HiOP VW", BIGHI_VW),
    ("SPREAD d10-d1 VW (long-short)", SPREAD_VW),
    ("SPREAD d10-d1 EW (long-short)", SPREAD_EW),
    ("RMW factor (FF 2x3)", RMW),
    ("HML factor", HML),
    ("VALUE d10 VW (high BE/ME)", VAL_VW),
    ("VALUE d10 EW (high BE/ME)", VAL_EW),
]


def table(series, dates, label):
    print("\n" + "=" * 118)
    print(label + f"   [{dates[0]}..{dates[-1]}, n={len(dates)}]")
    print("=" * 118)
    print(f"{'series':40s} {'CAGR':>7s} {'vol':>6s} {'maxDD':>8s} {'peak':>7s} {'trough':>7s} "
          f"{'recov':>7s} {'p->t':>5s} {'t->r':>6s} {'UW':>5s} {'#DD>20%':>7s}")
    out = {}
    for nm, s in series:
        r = dd_report(nm, s, dates)
        e = r["mx"]
        all_eps = episodes(nav_from_pct(s), dates)
        n20 = sum(1 for x in all_eps if x["depth"] <= -0.20)
        print(f"{nm:40s} {r['cagr']*100:6.2f}% {r['vol']*100:5.1f}% {e['depth']*100:7.2f}% "
              f"{e['peak_date']:>7s} {e['trough_date']:>7s} "
              f"{(e['rec_date'] or 'NEVER'):>7s} {e['m_to_trough']:5d} "
              f"{(e['m_to_recover'] if e['m_to_recover'] is not None else -1):6d} "
              f"{e['m_underwater']:5d} {n20:7d}")
        out[nm] = r
    return out


rep = table(SERIES, dates, "TABLE 1 - FULL SAMPLE drawdown of long-only tilts vs market vs spread")

print("\n" + "=" * 118)
print("TABLE 2 - the FIVE WORST episodes of each key series (depth-ranked, distinct episodes)")
print("=" * 118)
for nm in ["MKT  value-weighted market (total ret)", "EWUNI equal-wtd all-name universe",
           "OP d10 VW  (long-only tilt, VW)", "OP d10 EW  (long-only tilt, EW)",
           "SMALL HiOP EW (small+profitable)",
           "SPREAD d10-d1 VW (long-short)", "RMW factor (FF 2x3)",
           "HML factor", "VALUE d10 VW (high BE/ME)"]:
    print(f"\n  {nm}")
    for e in rep[nm]["eps"]:
        print("    " + fmt_ep(e))
    print("    LONGEST UNDERWATER: " + fmt_ep(rep[nm]["longest"]))
import os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from C3_dd import *
np.set_printoptions(suppress=True)

FR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C3_french")
OP = read_blocks(os.path.join(FR, "Portfolios_Formed_on_OP.csv"))
BM = read_blocks(os.path.join(FR, "Portfolios_Formed_on_BE-ME.csv"))
F3 = read_blocks(os.path.join(FR, "F-F_Research_Data_Factors.csv"))
F5 = read_blocks(os.path.join(FR, "F-F_Research_Data_5_Factors_2x3.csv"))
P25 = read_blocks(os.path.join(FR, "25_Portfolios_ME_OP_5x5.csv"))
op_vw, op_ew, op_nf = OP[0], OP[1], OP[4]
bm_vw = BM[0]; ff3m, ff5m = F3[0], F5[0]; p25_vw, p25_ew = P25[0], P25[1]
DEC = ['Lo 10','2-Dec','3-Dec','4-Dec','5-Dec','6-Dec','7-Dec','8-Dec','9-Dec','Hi 10']
col = lambda b, c: b["data"][:, b["cols"].index(c)]
dates = np.array(op_vw["dates"])
idx3 = {d:i for i,d in enumerate(ff3m["dates"])}; sel3 = np.array([idx3[d] for d in dates])
idxb = {d:i for i,d in enumerate(bm_vw["dates"])}; selb = np.array([idxb[d] for d in dates])
rf = col(ff3m,"RF")[sel3]; MKT = col(ff3m,"Mkt-RF")[sel3] + rf
nf = np.array([col(op_nf,c) for c in DEC]).T; rw = np.array([col(op_ew,c) for c in DEC]).T
EWUNI = (nf*rw).sum(1)/nf.sum(1)
HI_VW, LO_VW = col(op_vw,"Hi 10"), col(op_vw,"Lo 10")
HI_EW, LO_EW = col(op_ew,"Hi 10"), col(op_ew,"Lo 10")
RMW, HML = col(ff5m,"RMW"), col(ff5m,"HML")
SPREAD_VW, SPREAD_EW = HI_VW-LO_VW, HI_EW-LO_EW
SMALLHI_EW = col(p25_ew,"SMALL HiOP")
VAL_VW = col(bm_vw,"Hi 10")[selb]

KEY = [("MKT(VW mkt)", MKT), ("EWUNI", EWUNI), ("OPd10_VW", HI_VW), ("OPd10_EW", HI_EW),
       ("SMALLHiOP_EW", SMALLHI_EW), ("SPREAD_VW", SPREAD_VW), ("SPREAD_EW", SPREAD_EW),
       ("RMW", RMW), ("HML", HML), ("VALUEd10_VW", VAL_VW)]

print("="*118)
print("TABLE 3 - DRAWDOWN TIME, not just depth: mean drawdown, % of months underwater, % in >20% hole")
print("   'mean drawdown' = time-average of the drawdown series, the same statistic CFM's A6 reports")
print("="*118)
print(f"{'series':14s} {'maxDD':>8s} {'meanDD':>8s} {'medDD':>7s} {'%UW':>6s} {'%DD>10%':>8s} {'%DD>20%':>8s} {'%DD>30%':>8s} {'worstUW(m)':>10s}")
for nm, s in KEY:
    nav = nav_from_pct(s); dd = drawdown_series(nav)[1:]
    eps = episodes(nav, dates)
    worstuw = max(e["m_underwater"] for e in eps) if eps else 0
    print(f"{nm:14s} {dd.min()*100:7.2f}% {dd.mean()*100:7.2f}% {np.median(dd)*100:6.2f}% "
          f"{(dd< -1e-12).mean()*100:5.1f}% {(dd<=-0.10).mean()*100:7.1f}% {(dd<=-0.20).mean()*100:7.1f}% "
          f"{(dd<=-0.30).mean()*100:7.1f}% {worstuw:10d}")

print("\n" + "="*118)
print("TABLE 4 - IS THE TILT'S DRAWDOWN THE MARKET'S? drawdown-path overlap and the RELATIVE drawdown")
print("="*118)
ddm = drawdown_series(nav_from_pct(MKT))[1:]
dde = drawdown_series(nav_from_pct(EWUNI))[1:]
for nm, s, bench, bn in [("OPd10_VW", HI_VW, MKT, "MKT"), ("OPd10_EW", HI_EW, EWUNI, "EWUNI"),
                         ("OPd10_EW", HI_EW, MKT, "MKT"), ("SMALLHiOP_EW", SMALLHI_EW, EWUNI, "EWUNI"),
                         ("SPREAD_VW", SPREAD_VW, MKT, "MKT"), ("RMW", RMW, MKT, "MKT")]:
    dd = drawdown_series(nav_from_pct(s))[1:]
    ddb = drawdown_series(nav_from_pct(bench))[1:]
    # relative NAV: tilt cumulative / benchmark cumulative -> its own drawdown = underperformance hole
    relnav = nav_from_pct(s)/nav_from_pct(bench)
    reldd = drawdown_series(relnav)[1:]
    releps = sorted(episodes(relnav, dates), key=lambda e: e["depth"])
    r = np.corrcoef(dd, ddb)[0,1]
    # fraction of the tilt's own max drawdown that the benchmark was also in
    i = int(np.argmin(dd))
    print(f"\n  {nm} vs {bn}: corr(drawdown paths) = {r:.3f}")
    print(f"    at the tilt's trough ({dates[i]}): tilt DD {dd[i]*100:6.2f}%   {bn} DD {ddb[i]*100:6.2f}%"
          f"   -> tilt-specific excess hole {(dd[i]-ddb[i])*100:6.2f}pp")
    print(f"    RELATIVE drawdown (cumulative {nm} / cumulative {bn}) worst = {reldd.min()*100:6.2f}%")
    for e in releps[:3]:
        print("      rel: " + fmt_ep(e))

print("\n" + "="*118)
print("TABLE 5 - STRESS CORRELATION: does the tilt's diversification survive the month it is needed?")
print("   buckets defined on the VW market's own monthly total return")
print("="*118)
ord_m = np.argsort(MKT)
buckets = [("all months", np.ones(len(MKT), bool)),
           ("market DOWN months", MKT < 0),
           ("worst decile of mkt months", np.isin(np.arange(len(MKT)), ord_m[:len(MKT)//10])),
           ("worst 5% of mkt months", np.isin(np.arange(len(MKT)), ord_m[:len(MKT)//20])),
           ("worst 20 mkt months", np.isin(np.arange(len(MKT)), ord_m[:20])),
           ("best decile of mkt months", np.isin(np.arange(len(MKT)), ord_m[-(len(MKT)//10):]))]
print(f"{'bucket':28s} {'n':>4s} {'mktRet':>7s} | " + " | ".join(f"{n:>22s}" for n in ["OPd10_VW","OPd10_EW","SPREAD_VW","RMW"]))
print(f"{'':28s} {'':>4s} {'':>7s} | " + " | ".join(f"{'corr   beta   mean':>22s}" for _ in range(4)))
for bn, m in buckets:
    row = f"{bn:28s} {m.sum():4d} {MKT[m].mean():6.2f}% | "
    cells = []
    for nm, s in [("OPd10_VW",HI_VW),("OPd10_EW",HI_EW),("SPREAD_VW",SPREAD_VW),("RMW",RMW)]:
        c = np.corrcoef(s[m], MKT[m])[0,1]
        b = np.cov(s[m], MKT[m])[0,1]/np.var(MKT[m], ddof=1)
        cells.append(f"{c:6.3f} {b:6.2f} {s[m].mean():6.2f}%")
    print(row + " | ".join(f"{c:>22s}" for c in cells))

print("\n  And the statistic that actually matters for a tilt: EXCESS over the market in each bucket")
for bn, m in buckets:
    print(f"    {bn:28s} OPd10_VW-MKT {np.mean(HI_VW[m]-MKT[m]):6.2f}%   "
          f"OPd10_EW-EWUNI {np.mean(HI_EW[m]-EWUNI[m]):6.2f}%   RMW {RMW[m].mean():6.2f}%")

print("\n" + "="*118)
print("TABLE 6 - HOW LONG MUST YOU HOLD? fraction of OVERLAPPING rolling windows that are positive,")
print("   and the fraction that beat the benchmark. (overlapping windows -> not independent; count only)")
print("="*118)
def roll_frac(s, k):
    nav = nav_from_pct(s); n = len(s)
    if n <= k: return None
    g = nav[k:]/nav[:-k] - 1.0
    return g
def roll_sum(s, k):
    c = np.concatenate([[0.0], np.cumsum(s)])
    return c[k:] - c[:-k]
hdr = ["1y(12m)","3y(36m)","5y(60m)","10y(120m)","15y(180m)","20y(240m)","30y(360m)"]
ks = [12,36,60,120,180,240,360]
print(f"{'series / question':46s} " + " ".join(f"{h:>10s}" for h in hdr))
for nm, s in [("MKT total return > 0", MKT), ("EWUNI total return > 0", EWUNI),
              ("OPd10_VW total return > 0", HI_VW), ("OPd10_EW total return > 0", HI_EW),
              ("SMALLHiOP_EW total return > 0", SMALLHI_EW)]:
    print(f"{nm:46s} " + " ".join(f"{(roll_frac(s,k)>0).mean()*100:9.1f}%" for k in ks))
for nm, s in [("MKT beats cash (RF)", MKT), ("OPd10_VW beats cash (RF)", HI_VW),
              ("OPd10_EW beats cash (RF)", HI_EW)]:
    print(f"{nm:46s} " + " ".join(f"{(roll_frac(s,k)>roll_frac(rf,k)).mean()*100:9.1f}%" for k in ks))
print(f"{'OPd10_VW beats MKT':46s} " + " ".join(f"{(roll_frac(HI_VW,k)>roll_frac(MKT,k)).mean()*100:9.1f}%" for k in ks))
print(f"{'OPd10_EW beats EWUNI':46s} " + " ".join(f"{(roll_frac(HI_EW,k)>roll_frac(EWUNI,k)).mean()*100:9.1f}%" for k in ks))
print(f"{'OPd10_EW beats MKT':46s} " + " ".join(f"{(roll_frac(HI_EW,k)>roll_frac(MKT,k)).mean()*100:9.1f}%" for k in ks))
for nm, s in [("SPREAD_VW cumulative > 0 (additive)", SPREAD_VW), ("SPREAD_EW cumulative > 0", SPREAD_EW),
              ("RMW cumulative > 0 (additive)", RMW), ("HML cumulative > 0 (additive)", HML)]:
    print(f"{nm:46s} " + " ".join(f"{(roll_sum(s,k)>0).mean()*100:9.1f}%" for k in ks))
import os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from C3_dd import *

FR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C3_french")
OP = read_blocks(os.path.join(FR, "Portfolios_Formed_on_OP.csv"))
BM = read_blocks(os.path.join(FR, "Portfolios_Formed_on_BE-ME.csv"))
F3 = read_blocks(os.path.join(FR, "F-F_Research_Data_Factors.csv"))
F5 = read_blocks(os.path.join(FR, "F-F_Research_Data_5_Factors_2x3.csv"))
P25 = read_blocks(os.path.join(FR, "25_Portfolios_ME_OP_5x5.csv"))
op_vw, op_ew, op_nf = OP[0], OP[1], OP[4]
bm_vw = BM[0]; ff3m, ff5m = F3[0], F5[0]; p25_vw, p25_ew = P25[0], P25[1]
DEC = ['Lo 10','2-Dec','3-Dec','4-Dec','5-Dec','6-Dec','7-Dec','8-Dec','9-Dec','Hi 10']
col = lambda b,c: b["data"][:, b["cols"].index(c)]
dates = np.array(op_vw["dates"])
idx3 = {d:i for i,d in enumerate(ff3m["dates"])}; sel3=np.array([idx3[d] for d in dates])
idxb = {d:i for i,d in enumerate(bm_vw["dates"])}; selb=np.array([idxb[d] for d in dates])
rf = col(ff3m,"RF")[sel3]; MKT = col(ff3m,"Mkt-RF")[sel3]+rf
nf = np.array([col(op_nf,c) for c in DEC]).T; rw = np.array([col(op_ew,c) for c in DEC]).T
EWUNI = (nf*rw).sum(1)/nf.sum(1)
HI_VW, LO_VW = col(op_vw,"Hi 10"), col(op_vw,"Lo 10")
HI_EW, LO_EW = col(op_ew,"Hi 10"), col(op_ew,"Lo 10")
RMW, HML = col(ff5m,"RMW"), col(ff5m,"HML")
SPREAD_VW, SPREAD_EW = HI_VW-LO_VW, HI_EW-LO_EW
SMALLHI_EW = col(p25_ew,"SMALL HiOP"); VAL_VW = col(bm_vw,"Hi 10")[selb]

ALL = [("MKT",MKT),("EWUNI",EWUNI),("OPd10_VW",HI_VW),("OPd10_EW",HI_EW),
       ("SMALLHiOP_EW",SMALLHI_EW),("SPREAD_VW",SPREAD_VW),("SPREAD_EW",SPREAD_EW),
       ("RMW",RMW),("HML",HML),("VALUEd10_VW",VAL_VW)]

print("="*115)
print("TABLE 7 - THE LIVE DRAWDOWN as at the data end (202607). What the investor is sitting in NOW.")
print("="*115)
for nm, s in ALL:
    nav = nav_from_pct(s); dd = drawdown_series(nav)
    eps = episodes(nav, dates)
    ong = [e for e in eps if e["ongoing"]]
    cur = dd[-1]*100
    if ong:
        e = ong[0]
        print(f"  {nm:14s} current DD {cur:7.2f}%  (ONGOING from peak {e['peak_date']}, "
              f"trough so far {e['trough_date']} {e['depth']*100:.2f}%, {e['m_underwater']}m underwater)")
    else:
        print(f"  {nm:14s} current DD {cur:7.2f}%  (at/near a high)")

print("\n" + "="*115)
print("TABLE 8 - PROGRAMME-ERA SUBSAMPLE 201001..202607 (the window the programme's own fixture spans)")
print("="*115)
m = np.array([d >= "201001" for d in dates])
dsub = dates[m]
print(f"{'series':14s} {'CAGR':>7s} {'vol':>6s} {'maxDD':>8s} {'peak':>7s} {'trough':>7s} {'recov':>7s} "
      f"{'UW(m)':>6s} {'meanDD':>8s} {'%UW':>6s}")
for nm, s in ALL:
    ss = s[m]; nav = nav_from_pct(ss); dd = drawdown_series(nav)[1:]
    eps = sorted(episodes(nav, dsub), key=lambda e: e["depth"])
    e = eps[0]
    cagr = nav[-1]**(12/len(ss))-1
    print(f"  {nm:12s} {cagr*100:6.2f}% {np.std(ss,ddof=1)*math.sqrt(12):5.1f}% {e['depth']*100:7.2f}% "
          f"{e['peak_date']:>7s} {e['trough_date']:>7s} {(e['rec_date'] or 'NEVER'):>7s} "
          f"{e['m_underwater']:6d} {dd.mean()*100:7.2f}% {(dd<-1e-12).mean()*100:5.1f}%")

print("\n" + "="*115)
print("TABLE 9 - SUB-Q2: are PROFITABILITY's worst episodes the SAME episodes as VALUE's?")
print("="*115)
ddR = drawdown_series(nav_from_pct(RMW))[1:]
ddH = drawdown_series(nav_from_pct(HML))[1:]
ddS = drawdown_series(nav_from_pct(SPREAD_VW))[1:]
ddV = drawdown_series(nav_from_pct(VAL_VW))[1:]
ddT = drawdown_series(nav_from_pct(HI_VW))[1:]
ddM = drawdown_series(nav_from_pct(MKT))[1:]
import itertools
names = {"RMW":ddR,"HML":ddH,"SPREAD_VW":ddS,"VALUEd10":ddV,"OPd10_VW":ddT,"MKT":ddM}
print("  correlation of DRAWDOWN PATHS")
ks = list(names)
print("       " + " ".join(f"{k:>10s}" for k in ks))
for a in ks:
    print(f"  {a:9s}" + " ".join(f"{np.corrcoef(names[a],names[b])[0,1]:10.3f}" for b in ks))
print("\n  correlation of MONTHLY RETURNS: RMW vs HML = %.3f   SPREAD_VW vs HML = %.3f" %
      (np.corrcoef(RMW,HML)[0,1], np.corrcoef(SPREAD_VW,HML)[0,1]))
print("\n  What each factor did inside the OTHER's worst drawdown window:")
def win(d0,d1):
    return np.array([(d>=d0) and (d<=d1) for d in dates])
wins = [("RMW worst 199809-200002", "199809","200002"),
        ("HML worst 200701-202009", "200701","202009"),
        ("dot-com 199901-200002", "199901","200002"),
        ("GFC 200711-200902", "200711","200902"),
        ("junk rally 200903-201002", "200903","201002"),
        ("COVID 202002-202003", "202002","202003"),
        ("meme/rates 202011-202103", "202011","202103"),
        ("recent 202311-202607", "202311","202607")]
print(f"  {'window':28s} {'n':>3s} " + " ".join(f"{k:>11s}" for k in ["MKT","EWUNI","OPd10_VW","OPd10_EW","SPREAD_VW","RMW","HML","VALUEd10"]))
for lab,d0,d1 in wins:
    mm = win(d0,d1)
    cells=[]
    for nm,s in [("MKT",MKT),("EWUNI",EWUNI),("OPd10_VW",HI_VW),("OPd10_EW",HI_EW),
                 ("SPREAD_VW",SPREAD_VW),("RMW",RMW),("HML",HML),("VALUEd10",VAL_VW)]:
        if nm in ("SPREAD_VW","RMW","HML"):
            tot = s[mm].sum()          # additive for a self-financing spread
        else:
            tot = (np.prod(1+s[mm]/100)-1)*100
        cells.append(f"{tot:10.1f}%")
    print(f"  {lab:28s} {mm.sum():3d} " + " ".join(cells))

print("\n" + "="*115)
print("TABLE 10 - GOING PAST THE SUB-QUESTIONS: is the observed maxDD informative, or is it just")
print("   what ANY series with this mean and vol produces? Bootstrap null of max drawdown.")
print("   iid resample (destroys autocorrelation) and a 24-month stationary block bootstrap.")
print("="*115)
rng = np.random.default_rng(20260910)
def maxdd_of(r):
    nav = np.cumprod(1+r/100.0)
    return (nav/np.maximum.accumulate(nav)-1).min()
def boot_iid(s, B=5000):
    n=len(s); out=np.empty(B)
    for b in range(B):
        out[b]=maxdd_of(s[rng.integers(0,n,n)])
    return out
def boot_block(s, L=24, B=5000):
    n=len(s); out=np.empty(B)
    for b in range(B):
        idx=[]
        while len(idx)<n:
            st=rng.integers(0,n)
            idx.extend(((st+np.arange(L))%n).tolist())
        out[b]=maxdd_of(s[np.array(idx[:n])])
    return out
print(f"{'series':14s} {'observed':>9s} | {'iid p5':>8s} {'iid p50':>8s} {'iid p95':>8s} {'pct(obs)':>9s} | "
      f"{'blk p5':>8s} {'blk p50':>8s} {'blk p95':>8s} {'pct(obs)':>9s}")
for nm,s in [("MKT",MKT),("EWUNI",EWUNI),("OPd10_VW",HI_VW),("OPd10_EW",HI_EW),
             ("SMALLHiOP_EW",SMALLHI_EW),("SPREAD_VW",SPREAD_VW),("RMW",RMW)]:
    obs=maxdd_of(s)
    bi=boot_iid(s); bb=boot_block(s)
    pi=(bi<=obs).mean()*100; pb=(bb<=obs).mean()*100
    print(f"{nm:14s} {obs*100:8.2f}% | {np.percentile(bi,5)*100:7.2f}% {np.percentile(bi,50)*100:7.2f}% "
          f"{np.percentile(bi,95)*100:7.2f}% {pi:8.1f}% | {np.percentile(bb,5)*100:7.2f}% "
          f"{np.percentile(bb,50)*100:7.2f}% {np.percentile(bb,95)*100:7.2f}% {pb:8.1f}%")
print("  pct(obs) = fraction of bootstrap draws with a DEEPER maxDD than observed; a low number means")
print("  the realised drawdown was MILD for this mean/vol, a high number means it was extreme.")
import os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from C3_dd import *
FR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C3_french")
OP = read_blocks(os.path.join(FR,"Portfolios_Formed_on_OP.csv"))
F3 = read_blocks(os.path.join(FR,"F-F_Research_Data_Factors.csv"))
F5 = read_blocks(os.path.join(FR,"F-F_Research_Data_5_Factors_2x3.csv"))
P25= read_blocks(os.path.join(FR,"25_Portfolios_ME_OP_5x5.csv"))
op_vw,op_ew,op_nf = OP[0],OP[1],OP[4]; ff3m,ff5m = F3[0],F5[0]; p25_ew=P25[1]
DEC=['Lo 10','2-Dec','3-Dec','4-Dec','5-Dec','6-Dec','7-Dec','8-Dec','9-Dec','Hi 10']
col=lambda b,c: b["data"][:,b["cols"].index(c)]
dates=np.array(op_vw["dates"]); idx3={d:i for i,d in enumerate(ff3m["dates"])}
sel3=np.array([idx3[d] for d in dates]); rf=col(ff3m,"RF")[sel3]
MKT=col(ff3m,"Mkt-RF")[sel3]+rf
nf=np.array([col(op_nf,c) for c in DEC]).T; rw=np.array([col(op_ew,c) for c in DEC]).T
EWUNI=(nf*rw).sum(1)/nf.sum(1)
HI_VW,HI_EW=col(op_vw,"Hi 10"),col(op_ew,"Hi 10")
SPREAD_VW=HI_VW-col(op_vw,"Lo 10"); RMW=col(ff5m,"RMW"); SMALLHI=col(p25_ew,"SMALL HiOP")

print("BOOTSTRAP SANITY: does any block draw reproduce the original series exactly?")
rng=np.random.default_rng(1)
def maxdd_of(r):
    nav=np.cumprod(1+r/100.0); return (nav/np.maximum.accumulate(nav)-1).min()
n=len(MKT); obs=maxdd_of(MKT); exact=0; vals=[]
for b in range(3000):
    idx=[]
    while len(idx)<n:
        st=rng.integers(0,n); idx.extend(((st+np.arange(24))%n).tolist())
    r=MKT[np.array(idx[:n])]
    if np.array_equal(r,MKT): exact+=1
    vals.append(maxdd_of(r))
vals=np.array(vals)
print(f"  exact reproductions of the original ordering: {exact} / 3000 (must be ~0)")
print(f"  observed {obs:.8f}  block p50 {np.percentile(vals,50):.8f}  (equality at 2dp was coincidence)")
print(f"  n distinct bootstrap maxDD values: {len(np.unique(np.round(vals,10)))}")

print("\n" + "="*112)
print("TABLE 11 - TIME TO RECOVERY, the statistic most often omitted: the distribution across ALL")
print("   drawdown episodes deeper than 10%, and deeper than 20%")
print("="*112)
print(f"{'series':14s} {'thr':>4s} {'n eps':>5s} {'median t->r':>12s} {'mean t->r':>10s} {'max t->r':>9s} "
      f"{'median UW':>10s} {'max UW':>7s} {'n unrecovered':>13s}")
for nm,s in [("MKT",MKT),("EWUNI",EWUNI),("OPd10_VW",HI_VW),("OPd10_EW",HI_EW),
             ("SMALLHiOP_EW",SMALLHI),("SPREAD_VW",SPREAD_VW),("RMW",RMW)]:
    eps=episodes(nav_from_pct(s),dates)
    for thr in (0.10,0.20):
        e=[x for x in eps if x["depth"]<=-thr]
        rec=[x["m_to_recover"] for x in e if x["m_to_recover"] is not None]
        uw=[x["m_underwater"] for x in e]
        nun=sum(1 for x in e if x["m_to_recover"] is None)
        if not e: continue
        print(f"{nm:14s} {int(thr*100):3d}% {len(e):5d} {np.median(rec) if rec else -1:12.1f} "
              f"{np.mean(rec) if rec else -1:10.1f} {max(rec) if rec else -1:9d} "
              f"{np.median(uw):10.1f} {max(uw):7d} {nun:13d}")

print("\n" + "="*112)
print("TABLE 12 - how often is the TILT's hole DEEPER than the MARKET's at the same moment?")
print("="*112)
ddM=drawdown_series(nav_from_pct(MKT))[1:]; ddE=drawdown_series(nav_from_pct(EWUNI))[1:]
for nm,s,bn,bdd in [("OPd10_VW",HI_VW,"MKT",ddM),("OPd10_EW",HI_EW,"MKT",ddM),
                    ("OPd10_EW",HI_EW,"EWUNI",ddE),("SMALLHiOP_EW",SMALLHI,"EWUNI",ddE),
                    ("SMALLHiOP_EW",SMALLHI,"MKT",ddM)]:
    dd=drawdown_series(nav_from_pct(s))[1:]
    deeper=(dd<bdd-1e-12)
    stress=bdd<=-0.20
    print(f"  {nm:13s} vs {bn:6s}: tilt hole deeper than benchmark's in {deeper.mean()*100:5.1f}% of all months, "
          f"{deeper[stress].mean()*100:5.1f}% of months when {bn} was >20% down "
          f"(n={stress.sum()}); mean gap {np.mean(dd-bdd)*100:6.2f}pp, worst gap {np.min(dd-bdd)*100:6.2f}pp")
import os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from C3_dd import *
FR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C3_french")

OPD = read_blocks(os.path.join(FR, "Portfolios_Formed_on_OP_Daily.csv"))
F3D = read_blocks(os.path.join(FR, "F-F_Research_Data_Factors_daily.csv"))
print("DAILY BLOCK PROOF (titles, line ranges, sentinel census):")
for k, bl in [("OP daily", OPD), ("FF3 daily", F3D)]:
    for b in bl:
        n99, n999 = sentinel_census(b)
        print(f"  {k:10s} lines {b['first_data_line']:6d}-{b['last_data_line']:6d} rows {len(b['dates']):6d} "
              f"{b['dates'][0]}..{b['dates'][-1]} sent99={n99} sent999={n999} ncols={len(b['cols'])} "
              f"TITLE={b['title'][:60]!r}")
opd_vw, opd_ew = OPD[0], OPD[1]
ffd = F3D[0]
col = lambda b, c: b["data"][:, b["cols"].index(c)]
dD = np.array(opd_vw["dates"])
idx = {d: i for i, d in enumerate(ffd["dates"])}
sel = np.array([idx[d] for d in dD])
rfD = col(ffd, "RF")[sel]
MKTD = col(ffd, "Mkt-RF")[sel] + rfD
HI_VWD, HI_EWD = col(opd_vw, "Hi 10"), col(opd_ew, "Hi 10")
LO_VWD = col(opd_vw, "Lo 10")
SPD = HI_VWD - LO_VWD
print(f"\n  daily grid: {len(dD)} days {dD[0]}..{dD[-1]}")

# NEG CTRL: RF drawdown must be 0 on the daily grid too
print(f"  [NEG CTRL] cumulative daily RF maxDD = {drawdown_series(nav_from_pct(rfD)).min()*100:.12f}%"
      f"  min daily RF = {rfD.min():.6f}%")

# POS CTRL: compound daily to monthly and compare to the monthly file
OPM = read_blocks(os.path.join(FR, "Portfolios_Formed_on_OP.csv"))
opm_vw = OPM[0]
dM, hiM = to_series(opm_vw, "Hi 10")
monthly_from_daily = {}
for d, r in zip(dD, HI_VWD):
    monthly_from_daily.setdefault(d[:6], []).append(r)
worst, nchk = 0.0, 0
for d, r in zip(dM, hiM):
    if d in monthly_from_daily:
        c = (np.prod(1 + np.array(monthly_from_daily[d]) / 100.0) - 1) * 100
        worst = max(worst, abs(c - r)); nchk += 1
print(f"  [POS CTRL] compounded DAILY -> monthly vs French's MONTHLY file: {nchk} months, "
      f"max abs diff {worst:.4f} pp")

print("\n" + "="*112)
print("TABLE 13 - HOW MUCH DOES MONTHLY SAMPLING HIDE? the same drawdowns at DAILY frequency")
print("   (the programme trades daily bars; every figure in the literature above is monthly)")
print("="*112)
print(f"{'series':22s} {'freq':>7s} {'maxDD':>8s} {'peak':>9s} {'trough':>9s} {'recov':>9s} "
      f"{'p->t':>6s} {'t->r':>6s} {'UW':>6s} {'meanDD':>8s}")
pairs = [("MKT", MKTD, None), ("OP d10 VW", HI_VWD, None), ("OP d10 EW", HI_EWD, None),
         ("SPREAD d10-d1 VW", SPD, None)]
res = {}
for nm, s, _ in pairs:
    nav = nav_from_pct(s); dd = drawdown_series(nav)[1:]
    eps = sorted(episodes(nav, dD), key=lambda e: e["depth"])
    e = eps[0]
    print(f"{nm:22s} {'daily':>7s} {e['depth']*100:7.2f}% {e['peak_date']:>9s} {e['trough_date']:>9s} "
          f"{(e['rec_date'] or 'NEVER'):>9s} {e['m_to_trough']:6d} "
          f"{(e['m_to_recover'] if e['m_to_recover'] is not None else -1):6d} {e['m_underwater']:6d} "
          f"{dd.mean()*100:7.2f}%   (p->t/t->r/UW in TRADING DAYS)")
    res[nm] = e["depth"]
    for x in eps[:4]:
        print("      " + fmt_ep(x))

# monthly counterparts on the SAME start date for apples-to-apples
m0 = dD[0][:6]
OPMvw, OPMew = OPM[0], OPM[1]
dMM = np.array(OPMvw["dates"])
mm = np.array([d >= m0 for d in dMM])
F3M = read_blocks(os.path.join(FR, "F-F_Research_Data_Factors.csv"))[0]
i3 = {d: i for i, d in enumerate(F3M["dates"])}
s3 = np.array([i3[d] for d in dMM[mm]])
MKTM = col(F3M, "Mkt-RF")[s3] + col(F3M, "RF")[s3]
print("\n  MONTHLY counterparts over the SAME span:")
for nm, s in [("MKT", MKTM), ("OP d10 VW", col(OPMvw, "Hi 10")[mm]), ("OP d10 EW", col(OPMew, "Hi 10")[mm]),
              ("SPREAD d10-d1 VW", (col(OPMvw, "Hi 10") - col(OPMvw, "Lo 10"))[mm])]:
    nav = nav_from_pct(s); dd = drawdown_series(nav)[1:]
    print(f"    {nm:22s} monthly maxDD {dd.min()*100:7.2f}%  meanDD {dd.mean()*100:6.2f}%   "
          f"-> DAILY is {abs(res[nm])*100 - abs(dd.min())*100:+6.2f}pp deeper")
import os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from C3_dd import *
FR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C3_french")
OP = read_blocks(os.path.join(FR, "Portfolios_Formed_on_OP.csv"))
F3 = read_blocks(os.path.join(FR, "F-F_Research_Data_Factors.csv"))
F5 = read_blocks(os.path.join(FR, "F-F_Research_Data_5_Factors_2x3.csv"))
P25 = read_blocks(os.path.join(FR, "25_Portfolios_ME_OP_5x5.csv"))
BM = read_blocks(os.path.join(FR, "Portfolios_Formed_on_BE-ME.csv"))
op_vw, op_ew, op_nf = OP[0], OP[1], OP[4]; ff3m, ff5m = F3[0], F5[0]; p25_ew = P25[1]; bm_vw = BM[0]
DEC = ['Lo 10','2-Dec','3-Dec','4-Dec','5-Dec','6-Dec','7-Dec','8-Dec','9-Dec','Hi 10']
col = lambda b,c: b["data"][:, b["cols"].index(c)]
dates = np.array(op_vw["dates"])
i3 = {d:i for i,d in enumerate(ff3m["dates"])}; s3 = np.array([i3[d] for d in dates])
ib = {d:i for i,d in enumerate(bm_vw["dates"])}; sb = np.array([ib[d] for d in dates])
rf = col(ff3m,"RF")[s3]; MKT = col(ff3m,"Mkt-RF")[s3] + rf
nf = np.array([col(op_nf,c) for c in DEC]).T; rw = np.array([col(op_ew,c) for c in DEC]).T
EWUNI = (nf*rw).sum(1)/nf.sum(1)
HI_VW, HI_EW = col(op_vw,"Hi 10"), col(op_ew,"Hi 10")
SPREAD_VW = HI_VW - col(op_vw,"Lo 10")
RMW, HML = col(ff5m,"RMW"), col(ff5m,"HML")
SMALLHI = col(p25_ew,"SMALL HiOP"); VAL = col(bm_vw,"Hi 10")[sb]

print("="*114)
print("TABLE 14 - BETA AND EXCESS RETURN *INSIDE* THE MARKET'S OWN WORST DRAWDOWN EPISODES")
print("   (the episode, not scattered worst months: this is 'the moment the diversification is needed')")
print("="*114)
epsM = sorted(episodes(nav_from_pct(MKT), dates), key=lambda e: e["depth"])[:6]
print(f"{'market episode (peak->trough)':34s} {'n':>3s} {'MKT':>8s} | "
      + " | ".join(f"{k:>26s}" for k in ["OPd10_VW","OPd10_EW","SMALLHiOP_EW","RMW"]))
print(f"{'':34s} {'':>3s} {'':>8s} | " + " | ".join(f"{'tot%   beta   excess':>26s}" for _ in range(4)))
for e in epsM:
    i0, i1 = e["peak_i"], e["trough_i"]           # nav indices; returns index = nav index - 1
    sl = slice(i0, i1)                            # returns from peak+1..trough
    n = i1 - i0
    cells = []
    for nm, s in [("a",HI_VW),("b",HI_EW),("c",SMALLHI),("d",RMW)]:
        tot = (np.prod(1+s[sl]/100)-1)*100 if nm != "d" else s[sl].sum()
        b = np.cov(s[sl], MKT[sl])[0,1]/np.var(MKT[sl], ddof=1)
        exc = tot - ((np.prod(1+MKT[sl]/100)-1)*100)
        cells.append(f"{tot:7.1f} {b:6.2f} {exc:7.1f}")
    print(f"{e['peak_date']+'->'+e['trough_date']:34s} {n:3d} "
          f"{(np.prod(1+MKT[sl]/100)-1)*100:7.1f}% | " + " | ".join(f"{c:>26s}" for c in cells))

print("\n" + "="*114)
print("TABLE 15 - MEAN DRAWDOWN IS A SHARPE STATISTIC, NOT A LEG STATISTIC")
print("   (this is the mechanism behind CFM's LH -8.2% vs LS -3.9% and my own opposite ordering)")
print("="*114)
rows = [("MKT",MKT),("EWUNI",EWUNI),("OPd10_VW",HI_VW),("OPd10_EW",HI_EW),("SMALLHiOP_EW",SMALLHI),
        ("VALUEd10_VW",VAL),("SPREAD_VW",SPREAD_VW),("RMW",RMW),("HML",HML)]
print(f"{'series':14s} {'ann.ret':>8s} {'ann.vol':>8s} {'Sharpe*':>8s} {'meanDD':>8s} {'maxDD':>8s} {'%UW':>6s}")
xs, ys = [], []
for nm, s in rows:
    nav = nav_from_pct(s); dd = drawdown_series(nav)[1:]
    ar = nav[-1]**(12/len(s))-1
    av = np.std(s, ddof=1)*math.sqrt(12)/100
    # Sharpe* = total-return / vol for a funded book; for a self-financing spread the excess IS the return
    sh = (ar - (nav_from_pct(rf)[-1]**(12/len(s))-1))/av if nm in ("MKT","EWUNI","OPd10_VW","OPd10_EW","SMALLHiOP_EW","VALUEd10_VW") else ar/av
    print(f"{nm:14s} {ar*100:7.2f}% {av*100:7.2f}% {sh:8.2f} {dd.mean()*100:7.2f}% {dd.min()*100:7.2f}% {(dd<-1e-12).mean()*100:5.1f}%")
    xs.append(sh); ys.append(dd.mean()*100)
xs, ys = np.array(xs), np.array(ys)
print(f"\n  corr(Sharpe*, meanDD) across these 9 series = {np.corrcoef(xs,ys)[0,1]:.3f}")
print(f"  OLS: meanDD(%) = {np.polyfit(xs,ys,1)[1]:.2f} + {np.polyfit(xs,ys,1)[0]:.2f} x Sharpe*")
print("  *Sharpe is excess-of-cash for the funded books, raw for the self-financing spreads.")

print("\n" + "="*114)
print("TABLE 16 - TIME TO t=2: the closed-form horizon, computed from the MEASURED numbers")
print("   years = (2/IR)^2 where IR is the annualised information ratio of the stated object")
print("="*114)
def ir_years(y, x=None, label=""):
    if x is None:
        m = np.mean(y); sd = np.std(y, ddof=1)
    else:
        d = y - x; m = np.mean(d); sd = np.std(d, ddof=1)
    ir = (m/sd)*math.sqrt(12)
    t = ir*math.sqrt(len(y)/12.0)
    yrs = (2.0/ir)**2 if ir > 0 else float('inf')
    print(f"  {label:44s} mean {m:6.3f}%/mo  IR {ir:6.3f}  t(realised,{len(y)/12:.0f}y) {t:6.2f}  "
          f"years to t=2: {yrs:8.1f}")
ir_years(HI_VW-rf, None, "OP d10 VW excess of cash (total Sharpe)")
ir_years(HI_EW-rf, None, "OP d10 EW excess of cash (total Sharpe)")
ir_years(HI_VW, MKT, "OP d10 VW MINUS the VW market")
ir_years(HI_EW, EWUNI, "OP d10 EW MINUS the EW universe")
ir_years(HI_EW, MKT, "OP d10 EW MINUS the VW market")
ir_years(SMALLHI, EWUNI, "SMALL HiOP EW MINUS the EW universe")
ir_years(SPREAD_VW, None, "OP d10-d1 VW spread")
ir_years(RMW, None, "RMW factor")
import os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from C3_dd import *
FR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C3_french")
OP = read_blocks(os.path.join(FR, "Portfolios_Formed_on_OP.csv"))
F3 = read_blocks(os.path.join(FR, "F-F_Research_Data_Factors.csv"))
P25 = read_blocks(os.path.join(FR, "25_Portfolios_ME_OP_5x5.csv"))
op_vw, op_ew, op_nf = OP[0], OP[1], OP[4]; ff3m = F3[0]; p25_ew = P25[1]
col = lambda b, c: b["data"][:, b["cols"].index(c)]
dates = np.array(op_vw["dates"])
i3 = {d: i for i, d in enumerate(ff3m["dates"])}; s3 = np.array([i3[d] for d in dates])
rf = col(ff3m, "RF")[s3]; MKT = col(ff3m, "Mkt-RF")[s3] + rf
DEC = ['Lo 10','2-Dec','3-Dec','4-Dec','5-Dec','6-Dec','7-Dec','8-Dec','9-Dec','Hi 10']
nf = np.array([col(op_nf, c) for c in DEC]).T; rw = np.array([col(op_ew, c) for c in DEC]).T
EWUNI = (nf*rw).sum(1)/nf.sum(1)

print("="*112)
print("EXTERNAL POSITIVE CONTROL 1 - reproduce a PUBLISHED exhibit")
print("  Van Hemert, Ganz, Harvey, Rattray, Sanchez Martin & Yawitch, 'Drawdowns', JPM 46(8) 2020,")
print("  pp.34-50, Exhibit 1 baseline: normal iid monthly returns, 10-year window, 10% annualised")
print("  volatility, 0.5 annualised Sharpe. Published P(maxDD <= -1s/-2s/-3s/-4s) = 97.1/43.0/9.9/1.5%.")
print("  Read in full from the published PDF on the author's own page (people.duke.edu/~charvey).")
print("="*112)
rng = np.random.default_rng(7)
N, T = 200000, 120
r = rng.normal(0.5*0.10/12, 0.10/math.sqrt(12), size=(N, T))
nav = np.cumprod(1+r, axis=1)
dd = (nav/np.maximum.accumulate(nav, axis=1) - 1).min(axis=1)
pub = [97.1, 43.0, 9.9, 1.5]
for k in (1, 2, 3, 4):
    print(f"  P(maxDD <= -{k}sigma = {-k*10}%) mine {(dd<=-k*0.10).mean()*100:6.2f}%   published {pub[k-1]:5.1f}%")

print("\n" + "="*112)
print("EXTERNAL POSITIVE CONTROL 2 - reproduce THREE published numbers at once")
print("  Arnott, Harvey, Kalesnik & Linnainmaa, 'Reports of Value's Death May Be Greatly Exaggerated',")
print("  FAJ 77(1) 2021, 44-67 (read in full, published PDF from Harvey's own Duke page):")
print("   (a) HML drawdown from the 2006/12 peak to 2020/06 = -54.8%")
print("   (b) their block bootstrap (6-month blocks, pre-2007 HML, 57-year samples, 1e6 draws):")
print("       median simulated maxDD -32.7%, and P(deeper than -54.8%) = 2.3%")
print("="*112)
d3 = np.array(ff3m["dates"]); hml = col(ff3m, "HML")
m = d3 >= "196307"; d3, hml = d3[m], hml[m]
nv = nav_from_pct(hml); ddh = drawdown_series(nv)
i = list(d3).index("202006")
print(f"  (a) mine: HML drawdown at 202006 from the running peak (200612) = {ddh[i+1]*100:6.2f}%"
      f"   published -54.8%")
pool = hml[d3 <= "200612"]; n = len(pool)
rng2 = np.random.default_rng(11); B, L, TT = 100000, 6, 684
out = np.empty(B)
for b in range(B):
    st = rng2.integers(0, n, size=TT//L + 1)
    idx = (st[:, None] + np.arange(L)[None, :]) % n
    rr = pool[idx.ravel()[:TT]]
    v = np.cumprod(1 + rr/100.0)
    out[b] = (v/np.maximum.accumulate(v) - 1).min()
print(f"  (b) mine: resample pool {n} months 196307..200612; B={B}, 6-month blocks, 684-month samples")
print(f"      median simulated maxDD {np.median(out)*100:6.2f}%   published -32.7%")
print(f"      P(maxDD deeper than -54.8%) {(out<=-0.548).mean()*100:5.2f}%   published 2.3%")

print("\n" + "="*112)
print("TABLE 17 - PAST THE SUB-QUESTIONS (a): does CONCENTRATING the tilt change the drawdown?")
print("   top 10% vs top 20% vs top 30% of the OP sort, both weightings, 196307-202607")
print("="*112)
print(f"{'portfolio':28s} {'CAGR':>7s} {'vol':>7s} {'maxDD':>8s} {'meanDD':>8s} {'%UW':>6s} "
      f"{'worstUW(m)':>10s} {'excess vs bench':>16s}")
for lab, b, bench, bn in [("OP Hi 10%  VW", op_vw, MKT, "VW mkt"), ("OP Hi 20%  VW", op_vw, MKT, "VW mkt"),
                          ("OP Hi 30%  VW", op_vw, MKT, "VW mkt"),
                          ("OP Hi 10%  EW", op_ew, EWUNI, "EW uni"), ("OP Hi 20%  EW", op_ew, EWUNI, "EW uni"),
                          ("OP Hi 30%  EW", op_ew, EWUNI, "EW uni")]:
    cn = {"10": "Hi 10", "20": "Hi 20", "30": "Hi 30"}[lab.split("Hi ")[1][:2]]
    s = col(b, cn)
    nav = nav_from_pct(s); dd = drawdown_series(nav)[1:]
    eps = episodes(nav, dates)
    print(f"{lab:28s} {(nav[-1]**(12/len(s))-1)*100:6.2f}% {np.std(s,ddof=1)*math.sqrt(12):6.2f}% "
          f"{dd.min()*100:7.2f}% {dd.mean()*100:7.2f}% {(dd<-1e-12).mean()*100:5.1f}% "
          f"{max(e['m_underwater'] for e in eps):10d} {np.mean(s-bench):8.3f}%/mo vs {bn}")

print("\n" + "="*112)
print("TABLE 18 - PAST THE SUB-QUESTIONS (b): what a COST DRAG does to the drawdown of a")
print("   cash-funded long-only tilt. Costs charged as a flat annual drag on the monthly series.")
print("   (Novy-Marx's own estimate for quality strategies: ~0.5%/yr large cap, ~1.5%/yr small cap.)")
print("="*112)
SMALLHI = col(p25_ew, "SMALL HiOP")
print(f"{'series':22s} {'drag/yr':>8s} {'CAGR':>7s} {'maxDD':>8s} {'meanDD':>8s} {'worstUW(m)':>10s} "
      f"{'vs bench %/mo':>13s}")
for nm, s, bench in [("OP d10 VW", col(op_vw, "Hi 10"), MKT), ("OP d10 EW", col(op_ew, "Hi 10"), EWUNI),
                     ("SMALL HiOP EW", SMALLHI, EWUNI)]:
    for drag in (0.0, 0.5, 1.5, 3.0):
        sc = s - drag/12.0
        nav = nav_from_pct(sc); dd = drawdown_series(nav)[1:]
        eps = episodes(nav, dates)
        print(f"{nm:22s} {drag:7.1f}% {(nav[-1]**(12/len(sc))-1)*100:6.2f}% {dd.min()*100:7.2f}% "
              f"{dd.mean()*100:7.2f}% {max(e['m_underwater'] for e in eps):10d} {np.mean(sc-bench):12.3f}%")
import os, sys, math, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from C3_dd import *
FR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "C3_french")
OP = read_blocks(os.path.join(FR, "Portfolios_Formed_on_OP.csv"))
F3 = read_blocks(os.path.join(FR, "F-F_Research_Data_Factors.csv"))
op_vw, op_ew, op_nf = OP[0], OP[1], OP[4]; ff3m = F3[0]
col = lambda b, c: b["data"][:, b["cols"].index(c)]
dates = np.array(op_vw["dates"])
i3 = {d: i for i, d in enumerate(ff3m["dates"])}; s3 = np.array([i3[d] for d in dates])
rf = col(ff3m, "RF")[s3]; MKT = col(ff3m, "Mkt-RF")[s3] + rf
DEC = ['Lo 10','2-Dec','3-Dec','4-Dec','5-Dec','6-Dec','7-Dec','8-Dec','9-Dec','Hi 10']
nf = np.array([col(op_nf, c) for c in DEC]).T
rwE = np.array([col(op_ew, c) for c in DEC]).T
EWUNI = (nf * rwE).sum(1) / nf.sum(1)
print("=" * 108)
print("TABLE 19 - DOES THE CHARACTERISTIC MOVE THE DRAWDOWN AT ALL? all ten OP deciles, 196307-202607")
print("  French's OP = (sales - COGS - SG&A - interest expense) / book equity, lagged to the prior")
print("  fiscal year end, portfolios formed end-June. This is Fama-French OP, NOT Novy-Marx GP.")
print("=" * 108)
for lab, b, bench, bn in [("VALUE-WEIGHTED", op_vw, MKT, "VW mkt"),
                          ("EQUAL-WEIGHTED", op_ew, EWUNI, "EW uni")]:
    ddb = drawdown_series(nav_from_pct(bench))[1:]
    print(f"\n  {lab}   (benchmark = {bn}: maxDD {ddb.min()*100:.2f}%, meanDD {ddb.mean()*100:.2f}%)")
    print(f"    {'decile':8s} {'CAGR':>7s} {'vol':>7s} {'beta':>6s} {'maxDD':>8s} {'meanDD':>8s} "
          f"{'worstUW':>8s} {'vs bench':>10s} {'DDcorr':>7s}")
    for j, c in enumerate(DEC):
        s = col(b, c); nav = nav_from_pct(s); dd = drawdown_series(nav)[1:]
        eps = episodes(nav, dates)
        beta = np.cov(s, MKT)[0, 1] / np.var(MKT, ddof=1)
        print(f"    d{j+1:<7d} {(nav[-1]**(12/len(s))-1)*100:6.2f}% {np.std(s,ddof=1)*math.sqrt(12):6.2f}% "
              f"{beta:6.2f} {dd.min()*100:7.2f}% {dd.mean()*100:7.2f}% "
              f"{max(e['m_underwater'] for e in eps):7d}m {np.mean(s-bench):9.3f}% "
              f"{np.corrcoef(dd,ddb)[0,1]:7.3f}")
