"""D454 stage 0 -- insider open-market purchases on the dead-inclusive fixture: coverage, shape, timeliness, routine share, and what the
buys sit in. NO forward return is read. Spec committed in 4ce4b86 BEFORE the fetcher and this file.

    uv run python -u scripts/run_d454_insider_stage0.py --build      # parse the cached quarterly zips -> data/d454_insider_events.csv.gz
    uv run python -u scripts/run_d454_insider_stage0.py --run        # the stage-0 tables -> data/d454_stage0.json
    uv run python -u scripts/run_d454_insider_stage0.py --selftest

Event (spec section 2): a Form 4 (4 or 4/A) submission with >= 1 non-derivative transaction TRANS_CODE P / ACQUIRED, shares > 0, price > 0,
on a common security (title rule), issuer mapped by CIK through D331's resolution inside the CIK's window; aggregated per (name, filing
date); availability = the first fixture bar strictly after FILING_DATE. Sales (S / DISPOSED) built the same way for comparison only.
Only filings dated <= END enter any table; later quarters are cached and unread.
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys, time, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
CACHE = REPO / "data" / "raw" / "edgar" / "form345"; DEALS = REPO / "data" / "fixtures" / "us_shorts_daily_raw_deals.json"; META = REPO / "data" / "fixtures" / "us_shorts_daily_raw.meta.json"
EVENTS = REPO / "data" / "d454_insider_events.csv.gz"; OWNERS = REPO / "data" / "d454_insider_owner_rows.csv.gz"; INFO = REPO / "data" / "d454_build_info.json"; OUT = REPO / "data" / "d454_stage0.json"
END = "2023-12-29"; YEARS = range(2010, 2024); CLUSTER_BARS = 5; A1_DEAD, A2_MIN_EVENTS, A3_LAG = 0.50, 2000, 5.0
KEEP_WORDS = ("common", "ordinary", "class a", "class b", "class c"); DROP_WORDS = ("preferred", "warrant", "option", "note", "debenture", "right")
ROLES = ("Director", "Officer", "TenPercentOwner", "Other"); VALUE_CAP = 2e9        # no single insider open-market filing exceeds $2B; above it the field is mis-scaled


# ------------------------------------------------------------------------------------------ parsing
def common_title(t):
    t = str(t).lower()
    if "common unit" in t:
        return True
    return any(k in t for k in KEEP_WORDS) and not any(d in t for d in DROP_WORDS)


def cik_windows():
    """CIK -> [(symbol, from, to)] from D331's resolution."""
    res = json.loads(DEALS.read_text())["resolution"]; meta = json.loads(META.read_text())["symbols"]; out = {}
    for s, r in res.items():
        for c in r.get("ciks") or []:
            out.setdefault(c["cik"].lstrip("0").zfill(10), []).append((s, c.get("from") or meta[s]["first_bar"], c.get("to") or meta[s]["last_bar"]))
    return out


def _date(s):
    return pd.to_datetime(s, format="%d-%b-%Y", errors="coerce")


def parse_quarter(zp, cmap, symbols_set, end=END):
    """Purchase / sale transactions on mapped issuers from one quarterly zip -> (transactions DataFrame, owner rows, counters)."""
    with zipfile.ZipFile(zp) as z:
        sub = pd.read_csv(z.open("SUBMISSION.tsv"), sep="\t", dtype=str, usecols=["ACCESSION_NUMBER", "FILING_DATE", "DOCUMENT_TYPE", "ISSUERCIK", "ISSUERTRADINGSYMBOL"], low_memory=False)
        nd = pd.read_csv(z.open("NONDERIV_TRANS.tsv"), sep="\t", dtype=str, usecols=["ACCESSION_NUMBER", "TRANS_DATE", "TRANS_FORM_TYPE", "TRANS_CODE", "TRANS_SHARES", "TRANS_PRICEPERSHARE", "TRANS_ACQUIRED_DISP_CD", "SECURITY_TITLE", "DIRECT_INDIRECT_OWNERSHIP"], low_memory=False)
        ro = pd.read_csv(z.open("REPORTINGOWNER.tsv"), sep="\t", dtype=str, usecols=["ACCESSION_NUMBER", "RPTOWNERCIK", "RPTOWNER_RELATIONSHIP"], low_memory=False)
    sub = sub[sub["DOCUMENT_TYPE"].isin(["4", "4/A"])].copy(); sub["filing"] = _date(sub["FILING_DATE"]); sub = sub[sub["filing"].notna()]
    sub["cik10"] = sub["ISSUERCIK"].fillna("").str.strip().str.lstrip("0").str.zfill(10)
    fdate = sub["filing"].dt.strftime("%Y-%m-%d"); sub["fdate"] = fdate
    win = pd.DataFrame([(cik, s, lo, hi) for cik, wins in cmap.items() for s, lo, hi in wins], columns=["cik10", "sym", "lo", "hi"])
    j = sub[["ACCESSION_NUMBER", "cik10", "fdate"]].merge(win, on="cik10"); j = j[(j["fdate"] >= j["lo"]) & (j["fdate"] <= j["hi"])].drop_duplicates("ACCESSION_NUMBER")   # first window wins, as before
    sub = sub.merge(j[["ACCESSION_NUMBER", "sym"]], on="ACCESSION_NUMBER", how="left").rename(columns={"sym": "symbol"})
    ticker_only = int((sub["symbol"].isna() & sub["ISSUERTRADINGSYMBOL"].fillna("").str.upper().isin(symbols_set)).sum())
    n_after_end = int((sub["fdate"] > end).sum()); sub = sub[sub["symbol"].notna() & (sub["fdate"] <= end)]        # the merge re-indexed sub: use its own column
    nd = nd[nd["ACCESSION_NUMBER"].isin(sub["ACCESSION_NUMBER"]) & (nd["TRANS_FORM_TYPE"] == "4")].copy()
    nd["shares"] = pd.to_numeric(nd["TRANS_SHARES"], errors="coerce"); nd["price"] = pd.to_numeric(nd["TRANS_PRICEPERSHARE"], errors="coerce"); nd["trans"] = _date(nd["TRANS_DATE"])
    buy = (nd["TRANS_CODE"] == "P") & (nd["TRANS_ACQUIRED_DISP_CD"] == "A"); sell = (nd["TRANS_CODE"] == "S") & (nd["TRANS_ACQUIRED_DISP_CD"] == "D")
    nd = nd[(buy | sell) & (nd["shares"] > 0) & (nd["price"] > 0) & nd["trans"].notna() & nd["SECURITY_TITLE"].map(common_title)].copy(); nd["kind"] = np.where(nd["TRANS_CODE"] == "P", "P", "S")
    nd = nd.merge(sub[["ACCESSION_NUMBER", "symbol", "cik10", "filing"]], on="ACCESSION_NUMBER"); nd["value"] = nd["shares"] * nd["price"]; nd["direct"] = (nd["DIRECT_INDIRECT_OWNERSHIP"].fillna("D").str.upper() == "D")
    misdated = int((nd["trans"] > nd["filing"]).sum()); nd = nd[nd["trans"] <= nd["filing"]]                      # a transaction dated after its own filing is a filer error (D444 had 44 of these)
    outlier = int((nd["value"] > VALUE_CAP).sum()); nd = nd[nd["value"] <= VALUE_CAP]                             # shares x price above VALUE_CAP is a mis-scaled field (PKY 2012: $4e14), not a trade
    ro = ro[ro["ACCESSION_NUMBER"].isin(nd["ACCESSION_NUMBER"])].copy(); ro["rel"] = ro["RPTOWNER_RELATIONSHIP"].fillna("Other")
    return nd, ro, dict(ticker_only=ticker_only, after_end=n_after_end, form4_submissions=int(len(sub)), misdated=misdated, value_outlier=outlier)


def aggregate(nd, ro):
    """Per (symbol, filing date, kind): value, shares, transactions, distinct owners, roles, direct share, earliest transaction date; plus owner rows."""
    own = nd[["ACCESSION_NUMBER", "symbol", "cik10", "filing", "kind", "trans", "value"]].merge(ro[["ACCESSION_NUMBER", "RPTOWNERCIK", "rel"]], on="ACCESSION_NUMBER", how="left")
    own["RPTOWNERCIK"] = own["RPTOWNERCIK"].fillna("unknown")
    for r in ROLES:
        own[r] = own["rel"].str.contains(r, na=False)
    own["Other"] = own["Other"] | ~(own["Director"] | own["Officer"] | own["TenPercentOwner"])
    g = nd.groupby(["symbol", "filing", "kind"]); ev = g.agg(cik=("cik10", "first"), value=("value", "sum"), shares=("shares", "sum"), n_tx=("value", "size"), trans_min=("trans", "min"), trans_max=("trans", "max"), n_acc=("ACCESSION_NUMBER", "nunique")).reset_index()
    dv = nd.assign(dv=nd["value"] * nd["direct"]).groupby(["symbol", "filing", "kind"])["dv"].sum().reset_index(); ev = ev.merge(dv, on=["symbol", "filing", "kind"]); ev["direct_share"] = ev["dv"] / ev["value"]; ev = ev.drop(columns="dv")
    og = own.groupby(["symbol", "filing", "kind"]); roles = og[list(ROLES)].any().reset_index(); owners = og["RPTOWNERCIK"].nunique().reset_index().rename(columns={"RPTOWNERCIK": "owners"})
    ev = ev.merge(owners, on=["symbol", "filing", "kind"]).merge(roles, on=["symbol", "filing", "kind"])
    ev["lag_bdays"] = [int(np.busday_count(np.datetime64(a, "D"), np.datetime64(b, "D"))) for a, b in zip(ev["trans_min"].dt.date, ev["filing"].dt.date)]
    orow = own.groupby(["symbol", "RPTOWNERCIK", "kind", "filing"]).agg(value=("value", "sum"), trans=("trans", "min")).reset_index()
    return ev, orow


def routine_flags(orow):
    """Cohen-Malloy-Pomorski: a purchase by owner o in name s in calendar month m of year y is routine when o bought s in month m in y-1 AND y-2."""
    p = orow[orow["kind"] == "P"].copy(); p["y"] = p["trans"].dt.year; p["m"] = p["trans"].dt.month
    key = set(zip(p["symbol"], p["RPTOWNERCIK"], p["y"], p["m"]))
    p["routine"] = [((s, o, y - 1, m) in key) and ((s, o, y - 2, m) in key) for s, o, y, m in zip(p["symbol"], p["RPTOWNERCIK"], p["y"], p["m"])]
    return p


def cmd_build():
    t0 = time.time(); cmap = cik_windows(); meta = json.loads(META.read_text())["symbols"]; symbols_set = set(meta); zips = sorted(CACHE.glob("*_form345.zip"))
    assert zips, "no cached quarters: run scripts/fetch_sec_form345.py"
    nds, ros, counters = [], [], dict(ticker_only=0, after_end=0, form4_submissions=0, misdated=0, value_outlier=0, quarters=0, quarters_unread=[])
    for zp in zips:
        q = zp.name[:6]
        if q > "2023q4":
            counters["quarters_unread"].append(q); continue
        nd, ro, c = parse_quarter(zp, cmap, symbols_set); nds.append(nd); ros.append(ro); counters["quarters"] += 1
        for k in ("ticker_only", "after_end", "form4_submissions", "misdated", "value_outlier"):
            counters[k] += c[k]
        counters.setdefault("ticker_only_by_year", {}); counters["ticker_only_by_year"][q[:4]] = counters["ticker_only_by_year"].get(q[:4], 0) + c["ticker_only"]     # 2006-2008 sit outside every CIK window by construction
        print(f"  {q}: {len(nd):6,} P/S transactions on mapped issuers  ({(time.time()-t0)/60:.1f} min)", flush=True)
    nd = pd.concat(nds, ignore_index=True); ro = pd.concat(ros, ignore_index=True); ev, orow = aggregate(nd, ro); p = routine_flags(orow)
    rk = p.groupby(["symbol", "filing"])["routine"].agg(["any", "all"]).reset_index().rename(columns={"any": "routine_any", "all": "routine_all"}); ev = ev.merge(rk, on=["symbol", "filing"], how="left")
    ev["routine_any"] = ev["routine_any"].fillna(False); ev["routine_all"] = ev["routine_all"].fillna(False)
    ev["filing"] = ev["filing"].dt.strftime("%Y-%m-%d"); ev["trans_min"] = ev["trans_min"].dt.strftime("%Y-%m-%d"); ev["trans_max"] = ev["trans_max"].dt.strftime("%Y-%m-%d")
    assert (ev["filing"] <= END).all() and (ev["trans_min"] <= ev["filing"]).all(), "[L] a filing after END or a transaction after its filing"
    ev.to_csv(EVENTS, index=False, compression="gzip"); orow.assign(filing=orow["filing"].dt.strftime("%Y-%m-%d"), trans=orow["trans"].dt.strftime("%Y-%m-%d")).to_csv(OWNERS, index=False, compression="gzip")
    counters.update(n_events=int(len(ev)), n_purchase_filings=int((ev["kind"] == "P").sum()), n_sale_filings=int((ev["kind"] == "S").sum()), n_names=int(ev["symbol"].nunique())); INFO.write_text(json.dumps(counters, indent=1))
    print(f"events: {counters['n_purchase_filings']:,} purchase filings, {counters['n_sale_filings']:,} sale filings on {counters['n_names']} names from {counters['quarters']} quarters; ticker-only issuers {counters['ticker_only']:,}; quarters unread {counters['quarters_unread']}\nwrote {EVENTS.relative_to(REPO)} in {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ the tables
def stage0(P, ev, meta, log=print):
    A92 = _load("d392", "run_d392_base_rate_atlas.py"); R46 = _load("d446", "run_d446_issuance_book.py")
    syms = list(P["symbols"]); sym_i = {s: i for i, s in enumerate(syms)}; dates = np.array([str(x)[:10] for x in P["dates"]]); T = P["T"]; elig = np.asarray(P["elig"]).copy(); t_end = int(np.searchsorted(dates, END, side="right")); elig[t_end:] = False
    live = np.asarray(P["live"]); fix = pd.to_datetime(dates); res = {}
    ev = ev.copy(); ev["t_av"] = np.searchsorted(fix, pd.to_datetime(ev["filing"]), side="right"); ev = ev[ev["t_av"] < T]; ev["j"] = ev["symbol"].map(sym_i)
    ev["live_at"] = [bool(live[j, t]) for j, t in zip(ev["j"], ev["t_av"])]; ev["year"] = ev["filing"].str[:4].astype(int)
    P_ = ev[(ev["kind"] == "P") & (ev["year"] >= 2010)]; S_ = ev[(ev["kind"] == "S") & (ev["year"] >= 2010)]; Pl = P_[P_["live_at"]]
    # 1. coverage
    coh = {s: meta[s]["cohort"] for s in syms}; st = {s: meta[s]["status"] for s in syms}; conf = {s: r.get("confidence", "unresolved") for s, r in json.loads(DEALS.read_text())["resolution"].items()}
    hasP = set(Pl["symbol"]); hasS = set(S_[S_["live_at"]]["symbol"])
    cov = {}
    for lab, key in (("cohort", coh), ("status", st), ("cik", conf)):
        for g in sorted(set(key.values())):
            names = [s for s in syms if key[s] == g]; cov[f"{lab}:{g}"] = dict(n=len(names), purchase=float(np.mean([s in hasP for s in names])), sale=float(np.mean([s in hasS for s in names])))
    cov["all"] = dict(n=len(syms), purchase=len(hasP) / len(syms), sale=len(hasS) / len(syms))
    dead = [s for s in syms if coh[s] == "dead"]; dy = {}
    for s in dead:
        dy.setdefault(meta[s]["last_bar"][:4], []).append(s in hasP)
    ny = {}
    for y in YEARS:
        idx = np.flatnonzero(np.array([d[:4] for d in dates]) == str(y)); alive = np.flatnonzero(live[:, idx].any(axis=1)); has = set(Pl[Pl["year"] == y]["symbol"])
        ny[str(y)] = dict(live=int(alive.size), with_purchase=int(sum(syms[j] in has for j in alive)), share=float(np.mean([syms[j] in has for j in alive])))
    res["coverage"] = dict(by_group=cov, dead_by_delist_year={y: dict(n=len(v), share=float(np.mean(v))) for y, v in sorted(dy.items())}, name_years=ny, name_year_share=float(np.mean([v["share"] for v in ny.values()])))
    log("1. COVERAGE (>= 1 purchase filing while live, 2010-2023)"); [log(f"  {k:16s} n {v['n']:5d}  purchase {100*v['purchase']:5.1f}%  sale {100*v['sale']:5.1f}%") for k, v in cov.items()]
    log("  dead by delisting year: " + " ".join(f"{y}:{100*v['share']:.0f}%({v['n']})" for y, v in res["coverage"]["dead_by_delist_year"].items())); log(f"  live name-years with a purchase: {100*res['coverage']['name_year_share']:.0f}%  " + " ".join(f"{y}:{100*v['share']:.0f}%" for y, v in ny.items()))
    # 2. shape
    q = [.1, .5, .9]; byy = {}
    for y in YEARS:
        p, s = Pl[Pl["year"] == y], S_[(S_["year"] == y) & S_["live_at"]]; byy[str(y)] = dict(purchases=int(len(p)), sales=int(len(s)), ratio=float(len(s) / max(len(p), 1)), value_p50=float(p["value"].median()) if len(p) else None)
    # clusters: DISTINCT reporting owners buying the same name within +-CLUSTER_BARS bars of the event, from the owner rows
    orow = pd.read_csv(OWNERS, dtype={"symbol": str, "RPTOWNERCIK": str, "kind": str, "filing": str}); orow = orow[(orow["kind"] == "P") & (orow["filing"] <= END)]; orow["t_av"] = np.searchsorted(fix, pd.to_datetime(orow["filing"]), side="right")
    by_sym = {s: (g["t_av"].to_numpy(), g["RPTOWNERCIK"].to_numpy()) for s, g in orow.groupby("symbol")}; own_in_cluster = np.zeros(len(Pl), int)
    for i, (s, t) in enumerate(zip(Pl["symbol"], Pl["t_av"])):
        tt, oo = by_sym.get(s, (np.zeros(0), np.zeros(0))); own_in_cluster[i] = len(set(oo[np.abs(tt - t) <= CLUSTER_BARS]))
    Pl = Pl.assign(cluster=own_in_cluster >= 2, cluster_owners=own_in_cluster); cl = Pl["cluster"].to_numpy()
    roles = {r: float(Pl[r].mean()) for r in ROLES}
    res["shape"] = dict(n_purchases=int(len(Pl)), n_sales=int(S_["live_at"].sum()), value_q={str(p): float(Pl["value"].quantile(p)) for p in q}, owners_median=float(Pl["owners"].median()), owners_ge2=float((Pl["owners"] >= 2).mean()),
                        cluster_share=float(cl.mean()), roles=roles, direct_share_mean=float(Pl["direct_share"].mean()), by_year=byy, sale_to_purchase=float(S_["live_at"].sum() / max(len(Pl), 1)))
    log(f"\n2. SHAPE: {len(Pl):,} purchase filings, {int(S_['live_at'].sum()):,} sale filings (ratio {res['shape']['sale_to_purchase']:.1f}); value p10 ${res['shape']['value_q']['0.1']:,.0f} p50 ${res['shape']['value_q']['0.5']:,.0f} p90 ${res['shape']['value_q']['0.9']:,.0f}; owners median {res['shape']['owners_median']:.0f}, >= 2 on {100*res['shape']['owners_ge2']:.0f}%; clusters (>= 2 owners within {CLUSTER_BARS} bars) {100*res['shape']['cluster_share']:.0f}%")
    log("  roles: " + "  ".join(f"{r} {100*v:.0f}%" for r, v in roles.items()) + f";  direct {100*res['shape']['direct_share_mean']:.0f}%"); log("  by year P/S: " + " ".join(f"{y}:{v['purchases']}/{v['sales']}" for y, v in byy.items()))
    # 3. timeliness
    lag = Pl["lag_bdays"]; res["timeliness"] = dict(p50=float(lag.median()), p90=float(lag.quantile(.9)), over_2=float((lag > 2).mean()), by_year={str(y): float(Pl[Pl["year"] == y]["lag_bdays"].median()) for y in YEARS})
    log(f"\n3. TIMELINESS (business days, earliest transaction -> filing): p50 {res['timeliness']['p50']:.0f}  p90 {res['timeliness']['p90']:.0f}  > 2 days {100*res['timeliness']['over_2']:.1f}%;  median by year " + " ".join(f"{y}:{v:.0f}" for y, v in res["timeliness"]["by_year"].items()))
    # 4. routine
    res["routine"] = dict(any=float(Pl["routine_any"].mean()), all=float(Pl["routine_all"].mean()), by_role={r: float(Pl[Pl[r]]["routine_any"].mean()) for r in ROLES})
    log(f"\n4. ROUTINE (same owner, same name, same month in each of the two prior years): {100*res['routine']['any']:.1f}% of purchase filings (all owners routine {100*res['routine']['all']:.1f}%); by role " + " ".join(f"{r} {100*v:.0f}%" for r, v in res["routine"]["by_role"].items()))
    # 5. proxy: terciles at the availability bar
    tp = A92.tercile_pools(P, elig); C = np.asarray(P["CLOSE"], float); DV = np.asarray(P["DV"], float)
    def terc_of(grid, t, j):
        col = elig[t] & np.isfinite(grid[t]); k = col.sum()
        if k < 30 or not np.isfinite(grid[t, j]):
            return -1
        return int(min(2, 3 * (grid[t, col] < grid[t, j]).mean()))
    with np.errstate(invalid="ignore", divide="ignore"):
        ret20 = np.log(C / np.vstack([np.full((20, C.shape[1]), np.nan), C[:-20]])); ldv = np.log(pd.DataFrame(DV).rolling(60, min_periods=30).mean().to_numpy())
    df44 = pd.read_csv(R46.PANEL, dtype={"fiscal_date": str, "avail_date": str, "symbol": str, "cik": str}); NS = R46.latest_ns_panel(df44, syms, dates, T); S = R46.percentile_panel(NS, elig)
    def dist(sub):
        out = {}
        for nm in ("price", "vol", "mom"):
            cnt = np.zeros(3); n = 0
            for t, j in zip(sub["t_av"], sub["j"]):
                for k, band in enumerate(("lo", "mid", "hi")):
                    if tp[f"{nm}_{band}"][t, j]:
                        cnt[k] += 1; n += 1
            out[nm] = (cnt / max(n, 1)).tolist() + [int(n)]
        for nm, grid in (("ret20", ret20), ("logdv", ldv)):
            cnt = np.zeros(3); n = 0
            for t, j in zip(sub["t_av"], sub["j"]):
                k = terc_of(grid, t, j)
                if k >= 0:
                    cnt[k] += 1; n += 1
            out[nm] = (cnt / max(n, 1)).tolist() + [int(n)]
        dec = np.array([int(min(9, S[t, j] // 10)) if np.isfinite(S[t, j]) else -1 for t, j in zip(sub["t_av"], sub["j"])]); ok = dec >= 0
        out["issuance_decile"] = dict(n=int(ok.sum()), top=float((dec[ok] == 9).mean()) if ok.any() else None, bottom=float((dec[ok] == 0).mean()) if ok.any() else None)
        return out
    res["proxy"] = dict(purchases=dist(Pl), sales=dist(S_[S_["live_at"]]))
    log("\n5. WHAT THE BUYS SIT IN (share in lo / mid / hi tercile at the availability bar; base rate 1/3 each)")
    for kind in ("purchases", "sales"):
        d = res["proxy"][kind]; log(f"  {kind:9s} " + "  ".join(f"{nm}: {100*v[0]:.0f}/{100*v[1]:.0f}/{100*v[2]:.0f}" for nm, v in d.items() if nm != "issuance_decile") + f"   issuance top decile {100*(d['issuance_decile']['top'] or 0):.0f}%  bottom {100*(d['issuance_decile']['bottom'] or 0):.0f}% (n {d['issuance_decile']['n']:,}; base 10/10)")
    # 6. tails
    top = Pl.nlargest(10, "value")[["symbol", "filing", "value", "owners", "Director", "Officer", "TenPercentOwner"]]; clus = Pl.nlargest(10, "cluster_owners")[["symbol", "filing", "cluster_owners", "value"]]
    res["tails"] = dict(largest=json.loads(top.to_json(orient="records")), clusters=json.loads(clus.to_json(orient="records")))
    log("\n6. TAILS: largest purchases " + "; ".join(f"{r.symbol} {r.filing} ${r.value/1e6:.0f}M {'10%' if r.TenPercentOwner else 'officer/dir'}" for r in top.itertuples()) + "\n   largest clusters " + "; ".join(f"{r.symbol} {r.filing} {r.cluster_owners} owners" for r in clus.itertuples()))
    # abandon + predictions
    dead_cov = cov["cohort:dead"]["purchase"]; res["abandon"] = dict(A1=bool(dead_cov < A1_DEAD), A2=bool(len(Pl) < A2_MIN_EVENTS), A3=bool(res["timeliness"]["p50"] > A3_LAG), dead_cov=dead_cov, n_purchases=int(len(Pl)), lag_p50=res["timeliness"]["p50"])
    log(f"\nABANDON\n  A1 dead coverage < 50%     : {res['abandon']['A1']}  ({100*dead_cov:.0f}%)\n  A2 purchases < 2,000       : {res['abandon']['A2']}  ({len(Pl):,})\n  A3 lag median > 5 bdays    : {res['abandon']['A3']}  ({res['timeliness']['p50']:.0f})")
    pp = res["proxy"]["purchases"]; sh = res["shape"]; rt = res["timeliness"]
    log("\nPREDICTIONS\n" + f"  X-a alive >= 85%, dead >= 60%, all >= 75%; name-years 45-60%; ticker-only < 5%  : alive {100*cov['cohort:alive']['purchase']:.0f}%  dead {100*dead_cov:.0f}%  all {100*cov['all']['purchase']:.0f}%  name-years {100*res['coverage']['name_year_share']:.0f}%\n"
        + f"  X-b 12,000-35,000 purchases; p50 $25-60k, p90 $0.5-1.5M; clusters 12-25%; officer+director >= 85%; S:P 3-6  : {len(Pl):,}; p50 ${sh['value_q']['0.5']:,.0f} p90 ${sh['value_q']['0.9']:,.0f}; clusters {100*sh['cluster_share']:.0f}%; officer|director {100*float((Pl['Officer']|Pl['Director']).mean()):.0f}%; S:P {sh['sale_to_purchase']:.1f}  (2020 {byy['2020']['ratio']:.1f}, 2022 {byy['2022']['ratio']:.1f})\n"
        + f"  X-c lag p50 1-2, > 2 on 10-20%                                       : p50 {rt['p50']:.0f}  > 2 {100*rt['over_2']:.0f}%\n"
        + f"  X-d routine 8-20%, officers > directors                              : {100*res['routine']['any']:.0f}%; officers {100*res['routine']['by_role']['Officer']:.0f}% directors {100*res['routine']['by_role']['Director']:.0f}%\n"
        + f"  X-e ret20 bottom >= 45%, mom bottom >= 40%, small/cheap >= 40%; issuance top 8-15 / bottom 12-20 : ret20 lo {100*pp['ret20'][0]:.0f}%  mom lo {100*pp['mom'][0]:.0f}%  price lo {100*pp['price'][0]:.0f}%  DV lo {100*pp['logdv'][0]:.0f}%;  issuance top {100*(pp['issuance_decile']['top'] or 0):.0f}% bottom {100*(pp['issuance_decile']['bottom'] or 0):.0f}%\n"
        + f"  X-f largest by value are 10% owners; largest clusters 2008-09 / 2020-03 : 10%-owner share of top ten {sum(r['TenPercentOwner'] for r in res['tails']['largest'])}/10; cluster dates {[r['filing'][:7] for r in res['tails']['clusters'][:5]]}")
    return res


def _prep():
    return _load("d348p", "d348_prep.py").prep(need_grids=True)


def cmd_run():
    t0 = time.time(); print("D454 STAGE 0 -- insider open-market purchases: coverage, shape, timeliness, routine, proxy. NO forward return.\n      spec committed in 4ce4b86 before the fetch and before this file\n")
    P = _prep(); meta = json.loads(META.read_text())["symbols"]; ev = pd.read_csv(EVENTS, dtype={"symbol": str, "filing": str, "trans_min": str, "trans_max": str, "cik": str, "kind": str})
    res = stage0(P, ev, meta); res["build"] = json.loads(INFO.read_text()); OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min   (no forward return read)")


def cmd_selftest():
    t0 = time.time(); print("== (a) title rule, aggregation, lag in business days, roles, routine flags")
    assert common_title("Common Stock") and common_title("Class A Common Stock") and common_title("Common Units") and not common_title("Series A Preferred Stock") and not common_title("Common Stock Warrant") and not common_title("Ordinary Shares Option")
    sub = pd.DataFrame(dict(ACCESSION_NUMBER=["a1", "a2", "a3"], symbol=["X", "X", "Y"], cik10=["0000000001"] * 2 + ["0000000002"], filing=pd.to_datetime(["2015-03-05", "2015-03-05", "2015-03-09"])))
    nd = pd.DataFrame(dict(ACCESSION_NUMBER=["a1", "a1", "a2", "a3"], trans=pd.to_datetime(["2015-03-03", "2015-03-04", "2015-03-03", "2015-03-02"]), shares=[100.0, 50.0, 10.0, 1000.0], price=[10.0, 10.0, 12.0, 5.0], kind=["P", "P", "P", "S"], direct=[True, False, True, True]))
    nd = nd.merge(sub, on="ACCESSION_NUMBER"); nd["value"] = nd["shares"] * nd["price"]
    ro = pd.DataFrame(dict(ACCESSION_NUMBER=["a1", "a2", "a2", "a3"], RPTOWNERCIK=["o1", "o1", "o2", "o3"], rel=["Officer", "Officer", "Director,TenPercentOwner", "Other"]))
    ev, orow = aggregate(nd, ro); x = ev[(ev["symbol"] == "X") & (ev["kind"] == "P")].iloc[0]
    assert x["value"] == 1620.0 and x["n_tx"] == 3 and x["owners"] == 2 and x["Officer"] and x["Director"] and x["TenPercentOwner"] and not x["Other"] and abs(x["direct_share"] - (1000 + 120) / 1620) < 1e-12 and x["lag_bdays"] == 2 and x["n_acc"] == 2
    y = ev[ev["symbol"] == "Y"].iloc[0]; assert y["kind"] == "S" and y["lag_bdays"] == 5 and y["Other"]
    o = orow.copy(); rows = [dict(symbol="X", RPTOWNERCIK="o1", kind="P", filing=pd.Timestamp(f"{yy}-03-05"), value=1.0, trans=pd.Timestamp(f"{yy}-03-03")) for yy in (2013, 2014)]; o = pd.concat([o, pd.DataFrame(rows)], ignore_index=True)
    p = routine_flags(o); r15 = p[(p["symbol"] == "X") & (p["RPTOWNERCIK"] == "o1") & (p["trans"].dt.year == 2015)]["routine"].iloc[0]; r14 = p[(p["symbol"] == "X") & (p["RPTOWNERCIK"] == "o1") & (p["trans"].dt.year == 2014)]["routine"].iloc[0]
    assert r15 and not r14 and not p[p["RPTOWNERCIK"] == "o2"]["routine"].iloc[0]
    print("  ok: X 2015-03-05 P: value 1620, 3 tx, 2 owners, roles Officer+Director+10%, direct 69%, lag 2 bdays; Y S lag 5 bdays; o1's 2015 buy routine (2013 and 2014 March buys), 2014 not")
    print("== (b) availability strictly after the filing date, on the real events file if built")
    if EVENTS.exists():
        ev = pd.read_csv(EVENTS, dtype={"filing": str, "trans_min": str}); assert (ev["filing"] <= END).all() and (ev["trans_min"] <= ev["filing"]).all(); print(f"  {len(ev):,} rows; every transaction precedes its filing; no filing after {END}")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--build", action="store_true"); g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.build:
        cmd_build()
    elif a.run:
        cmd_run()
    else:
        cmd_selftest()
