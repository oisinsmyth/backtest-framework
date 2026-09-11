"""D443 stage 0 -- net share issuance: coverage, shape, persistence, and what it is a proxy for. NO forward return is read.
Spec docs/decisions/D443-net-share-issuance-stage-0-...md, committed in 0fa0d5c BEFORE this file and before the pull.

    uv run python -u scripts/run_d443_issuance_stage0.py --build [--partial]     # panel from the raw cache -> data/d443_issuance_panel.csv.gz
    uv run python -u scripts/run_d443_issuance_stage0.py --run                   # the stage-0 tables -> data/d443_stage0.json
    uv run python -u scripts/run_d443_issuance_stage0.py --selftest

Conventions (spec section 2): NS_q = ln(SO_q / SO_{q-4}) on split-adjusted shares (the daily_adjusted cache's split coefficients put
every report on the final basis, for the splits the raw share series shows -- the vendor restates some names and not others);
NIY_q = sum_4Q net equity proceeds / (SO_q x raw close at the fiscal date) -- the spec's two gross-flow fields are "None" on this
vendor throughout, so the populated net field proceedsFromRepurchaseOfEquity (+ = cash in) is used and disclosed; a value is
usable from fiscalDateEnding + 90 calendar days; [S] a quarter with |ln(SO_adj_q / SO_adj_{q-1})| > ln 1.5 is flagged, kept, and
every table is printed with and without the flagged rows.
"""
from __future__ import annotations
import argparse, gzip, importlib.util, json, math, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
CACHE = REPO / "data" / "raw" / "alphavantage" / "fundamentals"; ADJ = REPO / "data" / "raw" / "alphavantage" / "daily_adjusted"
META = REPO / "data" / "fixtures" / "us_shorts_daily_raw.meta.json"
PANEL = REPO / "data" / "d443_issuance_panel.csv.gz"; PANEL_INFO = REPO / "data" / "d443_issuance_panel_info.json"; OUT = REPO / "data" / "d443_stage0.json"
LAG_DAYS = 90; Y_LO, Y_HI = 330, 400; Q_LO, Q_HI = 60, 125; JUMP = math.log(1.5); FRESH_DAYS = 200
YEARS = range(2011, 2024); AXES = ("mom12", "ret20", "logpx", "logmcap", "vol60", "logdv"); MIN_PAIRS = 30
A1_DEAD_COVER, A2_R2, A2_RHO, A3_PERSIST = 0.50, 0.50, 0.40, 0.10


# ------------------------------------------------------------------------------------------ raw -> per-name reports
def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


NET_EQUITY_FIELD = "proceedsFromRepurchaseOfEquity"      # the one equity-flow field the vendor populates (+ = cash in = net issuance);
DECLARED_FIELDS = ("proceedsFromIssuanceOfCommonStock", "paymentsForRepurchaseOfCommonStock")   # the spec's two fields are "None" throughout -- disclosed


def load_reports(sym, cache=CACHE):
    """[(fiscal_date, SO, net_equity_proceeds)] sorted by date, or None when either file is absent."""
    pb, pc = cache / f"{sym}_bs.json.gz", cache / f"{sym}_cf.json.gz"
    if not (pb.exists() and pc.exists()):
        return None
    bs = json.load(gzip.open(pb, "rt", encoding="utf-8")).get("quarterlyReports") or []; cf = json.load(gzip.open(pc, "rt", encoding="utf-8")).get("quarterlyReports") or []
    so = {r["fiscalDateEnding"]: _f(r.get("commonStockSharesOutstanding")) for r in bs}
    fl = {r["fiscalDateEnding"]: _f(r.get(NET_EQUITY_FIELD)) for r in cf}
    load_reports.declared_seen += sum(_f(r.get(k)) == _f(r.get(k)) for r in cf for k in DECLARED_FIELDS)     # finite count of the spec's fields
    return [(d, so.get(d, float("nan")), fl.get(d, float("nan"))) for d in sorted(set(so) | set(fl))]


load_reports.declared_seen = 0


def visible_splits(splits, ds, so_raw):
    """Keep only the split events the RAW share series shows. The vendor restates some names' shares for later splits and not
    others (AHT 2020 is visible, AGL 2019 is restated); adjusting a restated series double-counts. A split at d_s with coefficient c
    between reports q_prev (last fiscal <= d_s) and q_next (first fiscal > d_s) is visible when the raw ratio r = SO_next / SO_prev
    is closer in log to c than to 1. Splits with no bracketing pair are kept (they predate or postdate the reports)."""
    keep, dropped = [], []
    for d_s, c in splits:
        prev = [i for i in range(len(ds)) if ds[i] <= d_s and np.isfinite(so_raw[i]) and so_raw[i] > 0]; nxt = [i for i in range(len(ds)) if ds[i] > d_s and np.isfinite(so_raw[i]) and so_raw[i] > 0]
        if not prev or not nxt:
            keep.append((d_s, c)); continue
        r = math.log(so_raw[nxt[0]] / so_raw[prev[-1]])
        (keep if abs(r - math.log(c)) < abs(r) else dropped).append((d_s, c))
    return keep, dropped


def split_events(sym, adj=ADJ):
    """[(date, coefficient)] with coefficient != 1, ascending, from the daily_adjusted cache; [] when the name is not cached."""
    p = adj / f"{sym}.json.gz"
    if not p.exists():
        return []
    d = json.load(gzip.open(p, "rt", encoding="utf-8"))
    return sorted((k, float(v["8. split coefficient"])) for k, v in d.items() if float(v.get("8. split coefficient", 1.0)) != 1.0)


def adjust_factor(splits, date):
    """Product of split coefficients dated AFTER `date`: shares reported at `date` times this are on the final basis."""
    f = 1.0
    for d, c in splits:
        if d > date:
            f *= c
    return f


# ------------------------------------------------------------------------------------------ the panel
def name_panel(sym, reports, splits, dates, close_col, T):
    """Rows for one name. `dates` are the fixture's ISO dates (T,), close_col the name's split-adjusted close (T,): market cap is
    SO_adj x CLOSE, both on the final basis, which is right whether the vendor's shares were as-reported or restated (SO_raw x
    RAW_CLOSE is wrong on a restated series before its split)."""
    ds = np.array([r[0] for r in reports]); dt = pd.to_datetime(ds); rows = []
    so_raw = np.array([r[1] for r in reports]); splits, restated = visible_splits(splits, ds, so_raw); so_adj = np.array([so_raw[i] * adjust_factor(splits, ds[i]) for i in range(len(ds))])
    neq = np.array([r[2] for r in reports]); name_panel.restated += len(restated); name_panel.visible += len(splits)
    fix_dt = pd.to_datetime(dates)
    for q in range(len(ds)):
        if not (np.isfinite(so_raw[q]) and so_raw[q] > 0):
            continue
        back = dt[q] - dt; y = np.flatnonzero((back.days >= Y_LO) & (back.days <= Y_HI) & np.isfinite(so_adj) & (so_adj > 0))
        ns = float(math.log(so_adj[q] / so_adj[y[-1]])) if y.size else float("nan")
        prev = np.flatnonzero((back.days >= Q_LO) & (back.days <= Q_HI) & np.isfinite(so_adj) & (so_adj > 0))
        jump = float(math.log(so_adj[q] / so_adj[prev[-1]])) if prev.size else float("nan"); flag = bool(np.isfinite(jump) and abs(jump) > JUMP)
        w = np.flatnonzero((back.days >= 0) & (back.days < 366)); four = w.size >= 4
        neq4 = float(np.nansum(neq[w])) if four and np.isfinite(neq[w]).any() else float("nan")       # missing quarters count as 0 when at least one is reported
        t_fis = int(np.searchsorted(fix_dt, dt[q], side="right") - 1); px = float("nan")
        if t_fis >= 0 and (dt[q] - fix_dt[t_fis]).days <= 14:
            px = close_col[t_fis] if np.isfinite(close_col[t_fis]) else float("nan")
        mcap = so_adj[q] * px if np.isfinite(px) else float("nan")
        niy = neq4 / mcap if (np.isfinite(neq4) and np.isfinite(mcap) and mcap > 0) else float("nan")
        av = dt[q] + pd.Timedelta(days=LAG_DAYS); t_av = int(np.searchsorted(fix_dt, av, side="left")); t_av = t_av if t_av < T else -1
        rows.append(dict(symbol=sym, fiscal_date=str(ds[q]), avail_date=str(av.date()), t_av=t_av, so_raw=so_raw[q], so_adj=so_adj[q], split_factor=so_adj[q] / so_raw[q], NS=ns, q_jump=jump, flag=flag,
                         neq4=neq4, mcap_fiscal=mcap, NIY=niy))
    return rows


name_panel.restated = 0; name_panel.visible = 0
REUSE_DAYS = 400          # a dead name whose vendor reports run more than this past its last fixture bar is a re-used ticker (another company)


def window_reports(reports, first_bar, last_bar):
    lo = str((pd.Timestamp(first_bar) - pd.Timedelta(days=Y_HI + 10)).date()); hi = str((pd.Timestamp(last_bar) + pd.Timedelta(days=45)).date())
    return [r for r in reports if lo <= r[0] <= hi]


def build_panel(P, meta, partial=False, cache=CACHE, adj=ADJ, log=print):
    syms = list(P["symbols"]); dates = np.array([str(x)[:10] for x in P["dates"]]); T = P["T"]; RC = np.asarray(P["CLOSE"], float)     # split-adjusted close
    rows, missing, no_reports, reused, outside, no_data = [], [], [], [], [], []
    name_panel.restated = name_panel.visible = load_reports.declared_seen = 0
    man = json.loads((cache / "_manifest.json").read_text()) if (cache / "_manifest.json").exists() else {}
    for j, s in enumerate(syms):
        rep = load_reports(s, cache)
        if rep is None:
            st = {man.get(f"{s}_{k}", {}).get("status") for k in ("bs", "cf")}
            (no_data if st and st <= {"empty", "Error Message", "no quarterlyReports"} else missing).append(s); continue      # the vendor answered "no such symbol" vs never asked
        if not rep:
            no_reports.append(s); continue
        m = meta[s]
        if m.get("cohort") == "dead" and (pd.Timestamp(max(r[0] for r in rep)) - pd.Timestamp(m["last_bar"])).days > REUSE_DAYS:
            reused.append(s); continue                                            # [G2] the vendor serves another company under this ticker
        rep = window_reports(rep, m["first_bar"], m["last_bar"])
        if not rep:
            outside.append(s); continue                                           # every report predates or postdates the fixture's life for the name
        rows += name_panel(s, rep, split_events(s, adj), dates, RC[:, j], T)
    assert partial or not missing, f"[C] {len(missing)} names have no cached fundamentals (run the fetch, or pass --partial): {missing[:8]}"
    df = pd.DataFrame(rows); info = dict(n_missing=len(missing), n_vendor_no_data=len(no_data), vendor_no_data=no_data, n_no_reports=len(no_reports), n_reused_ticker=len(reused), reused=reused, n_outside_window=len(outside), outside=outside,
                                         splits_visible=name_panel.visible, splits_restated=name_panel.restated, declared_fields_finite=load_reports.declared_seen)
    log(f"panel: {len(df):,} name-quarters on {df['symbol'].nunique() if len(df) else 0} names; {len(missing)} not fetched; {len(no_data)} unknown to the vendor; {len(no_reports)} with no reports; {len(reused)} re-used tickers dropped [G2]; {len(outside)} with no report in the name's window; "
        f"splits visible in the raw shares {name_panel.visible}, restated by the vendor (not re-adjusted) {name_panel.restated}; the spec's two flow fields finite in {load_reports.declared_seen} report-fields")
    return df, info


# ------------------------------------------------------------------------------------------ statistics
def spearman(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float); m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 3:
        return float("nan")
    rx, ry = pd.Series(x[m]).rank().to_numpy(), pd.Series(y[m]).rank().to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1])


def rank_r2(y, X):
    """R^2 of rank(y) on ranks of the columns of X (with intercept), rows with every value finite."""
    y = np.asarray(y, float); X = np.asarray(X, float); m = np.isfinite(y) & np.isfinite(X).all(axis=1)
    if m.sum() < X.shape[1] + 5:
        return float("nan")
    ry = pd.Series(y[m]).rank().to_numpy(); RX = np.column_stack([np.ones(m.sum())] + [pd.Series(X[m, k]).rank().to_numpy() for k in range(X.shape[1])])
    beta, *_ = np.linalg.lstsq(RX, ry, rcond=None); res = ry - RX @ beta
    return float(1.0 - res.var() / ry.var())


def axes_at(P, t, j_idx):
    C = np.asarray(P["CLOSE"], float); RC = np.asarray(P["RAW_CLOSE"], float); DV = np.asarray(P["DV"], float)
    with np.errstate(invalid="ignore", divide="ignore"):
        mom12 = np.log(C[t - 21, j_idx] / C[t - 252, j_idx]); ret20 = np.log(C[t, j_idx] / C[t - 20, j_idx]); logpx = np.log(RC[t, j_idx])
        lr = np.diff(np.log(C[t - 60:t + 1, j_idx]), axis=0); vol60 = np.nanstd(lr, axis=0, ddof=1); logdv = np.log(np.nanmean(DV[t - 59:t + 1, j_idx], axis=0))
    return dict(mom12=mom12, ret20=ret20, logpx=logpx, vol60=vol60, logdv=logdv)


def fresh_rows(df, dates, t):
    """The latest usable row per name available at bar t (t_av <= t) whose fiscal date is within FRESH_DAYS of bar t."""
    d = pd.Timestamp(str(dates[t])); sub = df[(df["t_av"] >= 0) & (df["t_av"] <= t) & (pd.to_datetime(df["fiscal_date"]) >= d - pd.Timedelta(days=FRESH_DAYS))]
    return sub.sort_values(["symbol", "fiscal_date"]).groupby("symbol").tail(1)


def quarter_end_bars(dates):
    d = pd.to_datetime(dates); out = []
    for y in YEARS:
        for mth in (3, 6, 9, 12):
            idx = np.flatnonzero((d.year == y) & (d.month == mth))
            if idx.size:
                out.append(int(idx[-1]))
    return out


def stage0(P, df, meta, log=print):
    syms = list(P["symbols"]); sym_i = {s: i for i, s in enumerate(syms)}; dates = np.array([str(x)[:10] for x in P["dates"]]); T = P["T"]; elig = np.asarray(P["elig"])
    A35 = _load("d435", "run_d435_atlas_conditional.py"); st = A35.state_pools_unshifted(P, elig)
    res = {}
    coh = {s: meta[s].get("cohort") for s in syms}; status = {s: meta[s].get("status") for s in syms}
    usable = df[np.isfinite(df["NS"]) & (df["t_av"] >= 0) & (df["avail_date"].str[:4].astype(int) <= max(YEARS))]; have_any = set(df["symbol"]); have_ns = set(usable["symbol"])
    # 1. coverage
    cov = {}
    for lab, key in (("cohort", coh), ("status", status)):
        for g in sorted(set(key.values())):
            names = [s for s in syms if key[s] == g]; cov[f"{lab}:{g}"] = dict(n=len(names), any_report=sum(s in have_any for s in names) / len(names), usable_NS=sum(s in have_ns for s in names) / len(names))
    cov["all"] = dict(n=len(syms), any_report=len(have_any) / len(syms), usable_NS=len(have_ns) / len(syms))
    live = np.asarray(P["live"]); ny = {}
    for y in YEARS:
        idx = np.flatnonzero(np.array([d[:4] for d in dates]) == str(y)); t = int(idx[-1]); alive = np.flatnonzero(live[:, idx].any(axis=1)); fr = fresh_rows(usable, dates, t)
        has = set(fr["symbol"]); ny[str(y)] = dict(live=int(alive.size), with_fresh_NS=int(sum(syms[j] in has for j in alive)), share=float(np.mean([syms[j] in has for j in alive])))
    dead = [s for s in syms if coh[s] == "dead" and s in have_any]; gaps = []
    for s in dead:
        last_f = pd.Timestamp(df[df["symbol"] == s]["fiscal_date"].max()); lb = pd.Timestamp(meta[s]["last_bar"]); gaps.append((lb - last_f).days)
    res["coverage"] = dict(by_group=cov, name_years=ny, name_year_share_mean=float(np.mean([v["share"] for v in ny.values()])), dead_gap_days=dict(n=len(gaps), median=float(np.median(gaps)) if gaps else None, p90=float(np.quantile(gaps, .9)) if gaps else None, share_over_365=float(np.mean(np.array(gaps) > 365)) if gaps else None))
    log("1. COVERAGE"); [log(f"  {k:18s} n {v['n']:5d}  any report {100*v['any_report']:5.1f}%  usable NS {100*v['usable_NS']:5.1f}%") for k, v in cov.items()]
    log(f"  live name-years with a fresh NS at year end: mean {100*res['coverage']['name_year_share_mean']:.1f}%  " + " ".join(f"{y}:{100*v['share']:.0f}%" for y, v in ny.items()))
    log(f"  dead names: last filed quarter to last fixture bar, median {res['coverage']['dead_gap_days']['median']} days, p90 {res['coverage']['dead_gap_days']['p90']}, share > 365 d {100*(res['coverage']['dead_gap_days']['share_over_365'] or 0):.1f}%")
    # 2. shape
    def shape(sub):
        q = [.05, .1, .25, .5, .75, .9, .95]; ns = sub["NS"].to_numpy(); niy = sub["NIY"].to_numpy(); fn = np.isfinite(niy)
        return dict(n=int(ns.size), NS_q={str(p): float(np.quantile(ns, p)) for p in q}, NS_pos=float(np.mean(ns > 0)), NS_mean=float(ns.mean()),
                    NIY_n=int(fn.sum()), NIY_q={str(p): float(np.quantile(niy[fn], p)) for p in q} if fn.any() else None, NIY_pos=float(np.mean(niy[fn] > 0)) if fn.any() else None,
                    any_repurchase=float(np.mean(sub["neq4"].to_numpy() < 0)), any_issuance=float(np.mean(sub["neq4"].to_numpy() > 0)), neq4_reported=float(np.mean(np.isfinite(sub["neq4"].to_numpy()))))
    res["shape"] = dict(all=shape(usable), unflagged=shape(usable[~usable["flag"]]), flagged_share=float(usable["flag"].mean()),
                        by_year={str(y): shape(usable[usable["avail_date"].str[:4] == str(y)]) for y in YEARS if (usable["avail_date"].str[:4] == str(y)).any()})
    log("\n2. SHAPE (usable name-quarters)")
    for lab in ("all", "unflagged"):
        s_ = res["shape"][lab]; log(f"  {lab:9s} n {s_['n']:6,}  NS p5 {100*s_['NS_q']['0.05']:+.1f}  p10 {100*s_['NS_q']['0.1']:+.1f}  p25 {100*s_['NS_q']['0.25']:+.1f}  p50 {100*s_['NS_q']['0.5']:+.1f}  p75 {100*s_['NS_q']['0.75']:+.1f}  p90 {100*s_['NS_q']['0.9']:+.1f}  p95 {100*s_['NS_q']['0.95']:+.1f} %/yr;  NS>0 {100*s_['NS_pos']:.0f}%;  any repurchase {100*s_['any_repurchase']:.0f}%  any issuance {100*s_['any_issuance']:.0f}%"
                                 + (f";  NIY n {s_['NIY_n']:,} p10 {100*s_['NIY_q']['0.1']:+.1f} p50 {100*s_['NIY_q']['0.5']:+.1f} p90 {100*s_['NIY_q']['0.9']:+.1f} %  NIY>0 {100*s_['NIY_pos']:.0f}%" if s_["NIY_q"] else ""))
    log(f"  flagged [S] rows: {100*res['shape']['flagged_share']:.2f}%;  NS median by year: " + " ".join(f"{y}:{100*v['NS_q']['0.5']:+.1f}" for y, v in res["shape"]["by_year"].items()))
    # 3. persistence
    def persist(sub, lo, hi, col):
        a = sub[["symbol", "fiscal_date", col]].dropna(); a = a.assign(dt=pd.to_datetime(a["fiscal_date"])); rhos, top = [], []
        by = {s: g.sort_values("dt") for s, g in a.groupby("symbol")}; pairs = []
        for s, g in by.items():
            d, v = g["dt"].to_numpy(), g[col].to_numpy()
            for i in range(len(d)):
                fwd = (d - d[i]) / np.timedelta64(1, "D"); k = np.flatnonzero((fwd >= lo) & (fwd <= hi))
                if k.size:
                    pairs.append((pd.Timestamp(d[i]).to_period("Q"), v[i], v[k[0]]))
        pp = pd.DataFrame(pairs, columns=["q", "x", "y"])
        for q, g in pp.groupby("q"):
            if len(g) >= MIN_PAIRS:
                rhos.append(spearman(g["x"], g["y"])); dx = pd.qcut(g["x"].rank(method="first"), 10, labels=False); dy = pd.qcut(g["y"].rank(method="first"), 10, labels=False)
                top.append(float(np.mean(dy[dx == 9] >= 7)))
        return dict(n_quarters=len(rhos), n_pairs=int(len(pp)), rho_mean=float(np.mean(rhos)) if rhos else float("nan"), rho_se=float(np.std(rhos, ddof=1) / np.sqrt(len(rhos))) if len(rhos) > 1 else float("nan"), top_decile_stays_top3=float(np.mean(top)) if top else float("nan"))
    res["persistence"] = dict(NS_1y=persist(usable, Y_LO, Y_HI, "NS"), NS_1q=persist(usable, Q_LO, Q_HI, "NS"), NS_1y_unflagged=persist(usable[~usable["flag"]], Y_LO, Y_HI, "NS"), NIY_1y=persist(usable, Y_LO, Y_HI, "NIY"))
    log("\n3. PERSISTENCE (cross-sectional Spearman, averaged over fiscal quarters)")
    for k, v in res["persistence"].items():
        log(f"  {k:16s} rho {v['rho_mean']:+.3f} +- {v['rho_se']:.3f}  ({v['n_quarters']} quarters, {v['n_pairs']:,} pairs)  top decile still in top 3: {100*v['top_decile_stays_top3']:.0f}%")
    # 4. proxy check
    qb = quarter_end_bars(dates); per = {a: [] for a in AXES}; r2s = []; states = {k: [] for k in st}; n_used = []
    for t in qb:
        fr = fresh_rows(usable, dates, t); j = np.array([sym_i[s] for s in fr["symbol"]]); ok = elig[t, j] if j.size else np.zeros(0, bool)
        if ok.sum() < MIN_PAIRS:
            continue
        j = j[ok]; ns = fr["NS"].to_numpy()[ok]; ax = axes_at(P, t, j); C = np.asarray(P["CLOSE"], float)
        ax["logmcap"] = np.log(fr["so_adj"].to_numpy()[ok] * C[t, j]); n_used.append(int(j.size))
        for a in AXES:
            per[a].append(spearman(ns, ax[a]))
        r2s.append(rank_r2(ns, np.column_stack([ax[a] for a in AXES])))
        for k, m in st.items():
            sel = m[t, j]; states[k].append(float(ns[sel].mean()) if sel.sum() >= 10 else float("nan"))
    res["proxy"] = dict(n_quarters=len(r2s), names_per_quarter=float(np.mean(n_used)), spearman={a: dict(mean=float(np.nanmean(per[a])), se=float(np.nanstd(per[a], ddof=1) / np.sqrt(np.isfinite(per[a]).sum()))) for a in AXES},
                        rank_r2=dict(mean=float(np.nanmean(r2s)), se=float(np.nanstd(r2s, ddof=1) / np.sqrt(len(r2s)))), by_state={k: float(np.nanmean(v)) for k, v in states.items()})
    log(f"\n4. PROXY CHECK ({len(r2s)} quarter ends, {np.mean(n_used):.0f} names each): Spearman(NS, axis)")
    for a in AXES:
        v = res["proxy"]["spearman"][a]; log(f"  {a:8s} {v['mean']:+.3f} +- {v['se']:.3f}")
    log(f"  rank R^2 on all six: {res['proxy']['rank_r2']['mean']:.3f} +- {res['proxy']['rank_r2']['se']:.3f}")
    log("  NS mean by atlas state (%/yr): " + "  ".join(f"{k}:{100*v:+.1f}" for k, v in sorted(res["proxy"]["by_state"].items())))
    # 5. tails, named
    cols = ["symbol", "fiscal_date", "so_raw", "so_adj", "split_factor", "NS", "q_jump", "flag"]; top = usable.nlargest(10, "NS")[cols]; bot = usable.nsmallest(10, "NS")[cols]
    res["tails"] = dict(largest=json.loads(top.to_json(orient="records")), smallest=json.loads(bot.to_json(orient="records")))
    log("\n5. THE TAILS, NAMED"); log("  largest NS:"); [log(f"    {r.symbol:6s} {r.fiscal_date}  SO {r.so_raw:.3e} (adj {r.so_adj:.3e}, factor {r.split_factor:.2f})  NS {100*r.NS:+.0f}%  q-jump {100*r.q_jump if np.isfinite(r.q_jump) else float('nan'):+.0f}%  flag {r.flag}") for r in top.itertuples()]
    log("  smallest NS:"); [log(f"    {r.symbol:6s} {r.fiscal_date}  SO {r.so_raw:.3e} (adj {r.so_adj:.3e}, factor {r.split_factor:.2f})  NS {100*r.NS:+.0f}%  q-jump {100*r.q_jump if np.isfinite(r.q_jump) else float('nan'):+.0f}%  flag {r.flag}") for r in bot.itertuples()]
    # abandon conditions
    dead_cov = cov["cohort:dead"]["usable_NS"]; r2 = res["proxy"]["rank_r2"]["mean"]; rho_max = max(abs(v["mean"]) for v in res["proxy"]["spearman"].values()); pers = res["persistence"]["NS_1y"]["rho_mean"]
    res["abandon"] = dict(A1_dead_coverage_lt_50=bool(dead_cov < A1_DEAD_COVER), A2_proxy=bool(r2 > A2_R2 or rho_max > A2_RHO), A3_no_persistence=bool(pers < A3_PERSIST), dead_cov=dead_cov, r2=r2, rho_max=rho_max, persistence_1y=pers)
    log(f"\nABANDON CONDITIONS\n  A1 dead-cohort usable-NS coverage < 50%     : {res['abandon']['A1_dead_coverage_lt_50']}   ({100*dead_cov:.1f}%)\n  A2 rank R2 > 0.50 or max |rho| > 0.40      : {res['abandon']['A2_proxy']}   (R2 {r2:.3f}, max |rho| {rho_max:.3f})\n  A3 one-year persistence < 0.10              : {res['abandon']['A3_no_persistence']}   ({pers:+.3f})")
    sh = res["shape"]["all"]; pr = res["proxy"]["spearman"]; bs = res["proxy"]["by_state"]
    log("\nPREDICTIONS\n" + f"  X-a survived >= 95%, dead 60-85%, all >= 80%, name-years 70-85% : survived {100*cov['status:survived']['usable_NS']:.0f}%  dead {100*dead_cov:.0f}%  all {100*cov['all']['usable_NS']:.0f}%  name-years {100*res['coverage']['name_year_share_mean']:.0f}%\n"
        + f"  X-b NS median +1..+2, >0 60-70%, p10 ~-4, p90 ~+15, p95 > +25    : median {100*sh['NS_q']['0.5']:+.1f}  >0 {100*sh['NS_pos']:.0f}%  p10 {100*sh['NS_q']['0.1']:+.1f}  p90 {100*sh['NS_q']['0.9']:+.1f}  p95 {100*sh['NS_q']['0.95']:+.1f};  any repurchase {100*sh['any_repurchase']:.0f}% (35-50)\n"
        + f"  X-c persistence 1y 0.30-0.50, 1q 0.70-0.85                       : {res['persistence']['NS_1y']['rho_mean']:+.3f} / {res['persistence']['NS_1q']['rho_mean']:+.3f}\n"
        + f"  X-d mom12 +.05..+.15  mcap -.15..-.30  px -.10..-.25  vol +.15..+.30  ret20 +-.05  R2 .10-.25 : {pr['mom12']['mean']:+.3f}  {pr['logmcap']['mean']:+.3f}  {pr['logpx']['mean']:+.3f}  {pr['vol60']['mean']:+.3f}  {pr['ret20']['mean']:+.3f}  R2 {r2:.3f}\n"
        + f"  X-e flagged < 3%                                                 : {100*res['shape']['flagged_share']:.2f}%\n"
        + f"  X-f NS highest in vol_hi / price_lo, lowest in price_hi; mom_hi - mom_lo < 2 pts : vol_hi {100*bs.get('vol_hi', float('nan')):+.1f}  price_lo {100*bs.get('price_lo', float('nan')):+.1f}  price_hi {100*bs.get('price_hi', float('nan')):+.1f}  mom_hi-mom_lo {100*(bs.get('mom_hi', float('nan')) - bs.get('mom_lo', float('nan'))):+.1f}")
    return res


# ------------------------------------------------------------------------------------------ entry points
def _prep():
    PREP = _load("d348p", "d348_prep.py"); P = PREP.prep(need_grids=True); return P


def cmd_build(partial):
    t0 = time.time(); P = _prep(); meta = json.loads(META.read_text())["symbols"]; df, info = build_panel(P, meta, partial)
    assert (pd.to_datetime(df["avail_date"]) - pd.to_datetime(df["fiscal_date"])).dt.days.min() >= LAG_DAYS, "[L] a row available before fiscal + 90 days"
    df.to_csv(PANEL, index=False, compression="gzip"); PANEL_INFO.write_text(json.dumps(dict(info, partial=partial, n_rows=int(len(df)), n_names=int(df["symbol"].nunique())), indent=1))
    print(f"wrote {PANEL.relative_to(REPO)} ({len(df):,} rows) and {PANEL_INFO.name} in {(time.time()-t0)/60:.1f} min")


def cmd_run():
    t0 = time.time(); print("D443 STAGE 0 -- net share issuance: coverage, shape, persistence, proxy. NO forward return.\n      spec committed in 0fa0d5c before the pull and before this file\n")
    P = _prep(); meta = json.loads(META.read_text())["symbols"]; df = pd.read_csv(PANEL, dtype={"fiscal_date": str, "avail_date": str, "symbol": str})
    assert set(df["symbol"]) <= set(P["symbols"]), "[C] panel names outside the fixture"
    res = stage0(P, df, meta); res["n_rows"] = int(len(df)); res["n_names"] = int(df["symbol"].nunique()); res["build"] = json.loads(PANEL_INFO.read_text()) if PANEL_INFO.exists() else None
    assert not (res["build"] or {}).get("partial"), "[C] the panel on disk is partial; rebuild without --partial after the fetch"
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min   (no forward return read)")


def cmd_selftest():
    t0 = time.time(); print("== (a) split adjustment: a 2:1 split between quarters gives NS = 0 adjusted, ln 2 unadjusted with the [S] flag")
    dates = np.array([str(d.date()) for d in pd.bdate_range("2014-01-01", "2016-12-31")]); T = dates.size; rc = np.full(T, 5.0)      # the split-ADJUSTED close: 5 throughout (raw was 10 before the 2:1)
    reps = [(f"{y}-{m}-{dd}", so, 1e6) for (y, m, dd, so) in [("2014", "03", "31", 100.), ("2014", "06", "30", 100.), ("2014", "09", "30", 100.), ("2014", "12", "31", 100.), ("2015", "03", "31", 100.), ("2015", "06", "30", 200.), ("2015", "09", "30", 200.), ("2015", "12", "31", 200.), ("2016", "03", "31", 200.), ("2016", "06", "30", 200.)]]
    adj = name_panel("X", reps, [("2015-05-15", 2.0)], dates, rc, T); un = name_panel("X", reps, [], dates, rc, T)
    a = {r["fiscal_date"]: r for r in adj}; u = {r["fiscal_date"]: r for r in un}
    assert abs(a["2016-06-30"]["NS"]) < 1e-12 and abs(a["2015-06-30"]["NS"] - 0.0) < 1e-12 and not a["2015-06-30"]["flag"], a["2015-06-30"]
    assert abs(u["2016-03-31"]["NS"] - math.log(2)) < 1e-12 and u["2015-06-30"]["flag"] and abs(u["2015-06-30"]["q_jump"] - math.log(2)) < 1e-12, u["2015-06-30"]
    assert abs(a["2015-03-31"]["so_adj"] - 200.0) < 1e-12 and abs(a["2015-06-30"]["so_adj"] - 200.0) < 1e-12
    # NIY is split-invariant: raw shares x raw price both halve/double; net equity proceeds 1e6 a quarter -> 4e6 over the year on a 1000 market cap
    assert abs(a["2015-06-30"]["mcap_fiscal"] - 1000.0) < 1e-9 and abs(a["2015-03-31"]["mcap_fiscal"] - 1000.0) < 1e-9 and abs(a["2016-06-30"]["NIY"] - 4e6 / 1000.0) < 1e-9
    assert all(r["avail_date"] == str((pd.Timestamp(r["fiscal_date"]) + pd.Timedelta(days=90)).date()) for r in adj) and all(dates[r["t_av"]] >= r["avail_date"] for r in adj if r["t_av"] >= 0)
    # a RESTATED series (shares unchanged across the split) must not be adjusted: the split is judged invisible and dropped
    flat = [(d, 100.0, float("nan")) for d, *_ in reps]; kept, dropped = visible_splits([("2015-05-15", 2.0)], np.array([r[0] for r in flat]), np.array([100.0] * len(flat)))
    assert kept == [] and dropped == [("2015-05-15", 2.0)]; fr = {r["fiscal_date"]: r for r in name_panel("Y", flat, [("2015-05-15", 2.0)], dates, rc, T)}
    assert all(abs(r["NS"]) < 1e-12 for r in fr.values() if np.isfinite(r["NS"])) and not any(r["flag"] for r in fr.values()) and math.isnan(fr["2016-06-30"]["NIY"])
    k2, d2 = visible_splits([("2015-05-15", 2.0)], np.array([r[0] for r in reps]), np.array([r[1] for r in reps])); assert k2 == [("2015-05-15", 2.0)] and d2 == []
    # [G2] a dead name whose vendor reports outrun its last bar by more than REUSE_DAYS is a re-used ticker
    assert (pd.Timestamp("2016-06-30") - pd.Timestamp("2014-12-31")).days > REUSE_DAYS and len(window_reports(reps, "2014-06-01", "2015-12-31")) == 8
    print("  adjusted NS 0.000, unadjusted ln 2 flagged; a restated series is left alone; NIY split-invariant; availability = fiscal + 90 days; window and re-use guards")
    print("== (b) Spearman and rank R^2 on synthetic data")
    rng = np.random.default_rng(443); x = rng.normal(size=5000); z = rng.normal(size=5000); y = x + 0.5 * z
    rho = spearman(y, x); r2 = rank_r2(y, np.column_stack([x, z])); r2x = rank_r2(y, x[:, None]); r2n = rank_r2(y, rng.normal(size=(5000, 2)))
    assert 0.85 < rho < 0.92 and r2 > 0.95 and 0.75 < r2x < 0.85 and r2n < 0.01, (rho, r2, r2x, r2n)
    assert spearman([1, 2, 3, np.nan], [1, 2, 3, 4]) == 1.0 and math.isnan(spearman([1, 2], [1, 2]))
    print(f"  rho {rho:.3f} (analytic 0.894), R2 on both {r2:.3f}, on x alone {r2x:.3f}, on noise {r2n:.4f}")
    print("== (c) reports loader: 'None' is missing, the report order is by date; split factor multiplies only later splits")
    assert math.isnan(_f("None")) and _f("12.5") == 12.5 and adjust_factor([("2015-01-01", 2.0), ("2016-01-01", 3.0)], "2015-06-30") == 3.0 and adjust_factor([("2015-01-01", 2.0)], "2015-01-01") == 1.0
    print("== (d) the real panel, if built: no row available before fiscal + 90; SO_adj x CLOSE == SO_raw x RAW_CLOSE at the fiscal bar on the fixture's own factor")
    if PANEL.exists():
        P = _prep(); df = pd.read_csv(PANEL, dtype={"fiscal_date": str, "avail_date": str, "symbol": str}); dates = np.array([str(x)[:10] for x in P["dates"]]); fix = pd.to_datetime(dates)
        assert (pd.to_datetime(df["avail_date"]) - pd.to_datetime(df["fiscal_date"])).dt.days.min() >= LAG_DAYS
        sym_i = {s: i for i, s in enumerate(P["symbols"])}; C = np.asarray(P["CLOSE"], float); RC = np.asarray(P["RAW_CLOSE"], float)
        sub = df[np.isfinite(df["mcap_fiscal"])].sample(min(3000, int(np.isfinite(df["mcap_fiscal"]).sum())), random_state=0)
        t = np.searchsorted(fix, pd.to_datetime(sub["fiscal_date"]), side="right") - 1; j = np.array([sym_i[s] for s in sub["symbol"]])
        lhs = sub["so_adj"].to_numpy() * C[t, j]; rhs = sub["so_raw"].to_numpy() * RC[t, j]; d = np.abs(np.log(lhs / rhs)); ok = np.isfinite(d)
        assert np.allclose(sub["mcap_fiscal"].to_numpy(), lhs, rtol=1e-9), "[M] market cap is not SO_adj x CLOSE at the fiscal bar"
        print(f"  {ok.sum()} sampled rows: mcap == SO_adj x CLOSE; |ln(SO_adj x CLOSE / SO_raw x RAW_CLOSE)| > 1e-3 on {100*np.mean(d[ok] > 1e-3):.2f}% -- the rows whose shares the vendor restated for a later split (the two products agree only where the raw series shows the split)")
    else:
        print("  panel not built yet; skipped")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--build", action="store_true"); g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true"); ap.add_argument("--partial", action="store_true")
    a = ap.parse_args()
    if a.build:
        cmd_build(a.partial)
    elif a.run:
        cmd_run()
    else:
        cmd_selftest()
