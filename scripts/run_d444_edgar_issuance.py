"""D444 -- point-in-time shares outstanding from EDGAR XBRL companyfacts, D443's panel schema and D443's stage-0 tables re-run
unchanged on it, plus filing lag, restatement share and the EDGAR-vs-vendor overlap. NO forward return is read.
Spec docs/decisions/D444-the-EDGAR-acquisition-...md, committed in f0d97af BEFORE the fetcher and this file.

    uv run python -u scripts/run_d444_edgar_issuance.py --build [--partial]     # -> data/d444_issuance_panel.csv.gz (+ _info.json)
    uv run python -u scripts/run_d444_edgar_issuance.py --run                   # -> data/d444_stage0.json
    uv run python -u scripts/run_d444_edgar_issuance.py --selftest

Point in time: for each (tag, end) the FIRST-filed value; availability = the first fixture bar strictly AFTER `filed`. Share count:
dei:EntityCommonStockSharesOutstanding (cover page) when a name has >= 4 first-filed rows in its window, else the balance-sheet
instant us-gaap:CommonStockSharesOutstanding. Splits: D443's visible_splits rule on the daily_adjusted coefficients.
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
R43 = _load("d443", "run_d443_issuance_stage0.py")
CACHE = REPO / "data" / "raw" / "edgar" / "companyfacts"; DEALS = REPO / "data" / "fixtures" / "us_shorts_daily_raw_deals.json"
PANEL = REPO / "data" / "d444_issuance_panel.csv.gz"; PANEL_INFO = REPO / "data" / "d444_issuance_panel_info.json"; OUT = REPO / "data" / "d444_stage0.json"
SHARE_TAGS = (("dei", "EntityCommonStockSharesOutstanding"), ("us-gaap", "CommonStockSharesOutstanding"))
FLOW_TAGS = {"rep": ("us-gaap", "PaymentsForRepurchaseOfCommonStock"), "iss": ("us-gaap", "ProceedsFromIssuanceOfCommonStock")}
FORMS = {"10-K", "10-Q", "10-K405", "10-KSB", "10-QSB", "20-F", "40-F", "8-K", "10-K/A", "10-Q/A", "20-F/A", "40-F/A"}
MIN_DEI_ROWS = 4; RESTATE_TOL = 0.001; WIN_BACK, WIN_FWD = R43.Y_HI + 10, 45


def facts_of(cik, cache=CACHE):
    p = cache / f"CIK{cik}.json.gz"
    if not p.exists():
        return None
    try:
        return json.load(gzip.open(p, "rt", encoding="utf-8"))
    except (EOFError, OSError, json.JSONDecodeError):
        return None                                   # a file still being written (or truncated) is not a document


def first_filed(rows, lo, hi):
    """rows -> {end: (val, filed, form, n_later, restated)} using the earliest `filed` per end, ends inside [lo, hi], periodic forms only."""
    by = {}
    for r in rows:
        if r.get("form") not in FORMS or not (lo <= r["end"] <= hi) or r.get("val") is None:
            continue
        by.setdefault(r["end"], []).append((r["filed"], float(r["val"]), r["form"]))
    out = {}
    for end, lst in by.items():
        lst.sort(); f0, v0, form0 = lst[0]; later = [v for _, v, _ in lst[1:]]
        restated = bool(v0 > 0 and any(v > 0 and abs(math.log(v / v0)) > RESTATE_TOL for v in later))
        out[end] = dict(val=v0, filed=f0, form=form0, n_later=len(later), restated=restated)
    return out


def extract(cf, lo, hi):
    """Share series (tag chosen per the docstring), the balance-sheet instant series (for the vendor overlap), annual flows."""
    facts = cf.get("facts", {}); series = {}
    for tx, tg in SHARE_TAGS:
        rows = facts.get(tx, {}).get(tg, {}).get("units", {}).get("shares", []); series[tg] = first_filed(rows, lo, hi)
    dei, bs = series["EntityCommonStockSharesOutstanding"], series["CommonStockSharesOutstanding"]
    use, tag = (dei, "dei") if len(dei) >= MIN_DEI_ROWS else (bs, "us-gaap")
    flows = {}
    for k, (tx, tg) in FLOW_TAGS.items():
        rows = [r for r in facts.get(tx, {}).get(tg, {}).get("units", {}).get("USD", []) if r.get("fp") == "FY" and str(r.get("frame") or "").startswith("CY") and "Q" not in str(r.get("frame") or "")]
        flows[k] = first_filed(rows, lo, hi)
    return use, tag, bs, flows


def rows_for(sym, cik, use, tag, flows, splits, dates, fix_dt, close_col, T):
    misdated = [e for e in use if use[e]["filed"] < e]; rows_for.misdated += len(misdated); use = {e: v for e, v in use.items() if e not in misdated}    # a period end after its own filing date is a filer tagging error
    ends = sorted(use); dt = pd.to_datetime(ends); so_raw = np.array([use[e]["val"] for e in ends]); ds = np.array(ends)
    if not ends:
        return []
    vis, restated_splits = R43.visible_splits(splits, ds, so_raw); so_adj = np.array([so_raw[i] * R43.adjust_factor(vis, ds[i]) for i in range(len(ds))])
    rows_for.visible += len(vis); rows_for.restated_splits += len(restated_splits); rows = []
    fy_ends = sorted(set(flows["rep"]) | set(flows["iss"])); fy_dt = pd.to_datetime(fy_ends) if fy_ends else None
    for q in range(len(ds)):
        if not (np.isfinite(so_raw[q]) and so_raw[q] > 0):
            continue
        back = dt[q] - dt; y = np.flatnonzero((back.days >= R43.Y_LO) & (back.days <= R43.Y_HI) & (so_adj > 0))
        ns = float(math.log(so_adj[q] / so_adj[y[-1]])) if y.size else float("nan")
        prev = np.flatnonzero((back.days >= R43.Q_LO) & (back.days <= R43.Q_HI) & (so_adj > 0))
        jump = float(math.log(so_adj[q] / so_adj[prev[-1]])) if prev.size else float("nan"); flag = bool(np.isfinite(jump) and abs(jump) > R43.JUMP)
        t_fis = int(np.searchsorted(fix_dt, dt[q], side="right") - 1); px = float("nan")
        if t_fis >= 0 and (dt[q] - fix_dt[t_fis]).days <= 14:
            px = close_col[t_fis] if np.isfinite(close_col[t_fis]) else float("nan")
        mcap = so_adj[q] * px if np.isfinite(px) else float("nan")
        neq4 = float("nan")
        if fy_dt is not None:
            k = np.flatnonzero(((dt[q] - fy_dt).days >= 0) & ((dt[q] - fy_dt).days < 366))
            if k.size:
                e = fy_ends[k[-1]]; iss = flows["iss"].get(e, {}).get("val"); rep = flows["rep"].get(e, {}).get("val")
                if iss is not None or rep is not None:
                    neq4 = float((iss or 0.0) - (rep or 0.0))
        niy = neq4 / mcap if (np.isfinite(neq4) and np.isfinite(mcap) and mcap > 0) else float("nan")
        filed = use[ends[q]]["filed"]; t_av = int(np.searchsorted(fix_dt, pd.Timestamp(filed), side="right")); t_av = t_av if t_av < T else -1
        rows.append(dict(symbol=sym, cik=cik, tag=tag, form=use[ends[q]]["form"], fiscal_date=ends[q], avail_date=filed, lag_days=int((pd.Timestamp(filed) - dt[q]).days), t_av=t_av,
                         restated=use[ends[q]]["restated"], n_later=use[ends[q]]["n_later"], so_raw=so_raw[q], so_adj=so_adj[q], split_factor=so_adj[q] / so_raw[q], NS=ns, q_jump=jump, flag=flag,
                         neq4=neq4, mcap_fiscal=mcap, NIY=niy))
    return rows


rows_for.visible = 0; rows_for.restated_splits = 0; rows_for.misdated = 0


def build_panel(P, meta, partial=False, cache=CACHE, log=print):
    res = json.loads(DEALS.read_text())["resolution"]; syms = list(P["symbols"]); dates = np.array([str(x)[:10] for x in P["dates"]]); fix_dt = pd.to_datetime(dates); T = P["T"]; C = np.asarray(P["CLOSE"], float)
    rows_for.visible = rows_for.restated_splits = rows_for.misdated = 0; rows, bs_rows, missing, unresolved, no_facts, no_shares = [], [], [], [], [], []; tag_used = {}
    man = json.loads((cache / "_manifest.json").read_text()) if (cache / "_manifest.json").exists() else {}
    for j, s in enumerate(syms):
        r = res.get(s, {}); ciks = r.get("ciks") or ([{"cik": r["cik"], "from": meta[s]["first_bar"], "to": meta[s]["last_bar"]}] if r.get("cik") else [])
        if not ciks:
            unresolved.append(s); continue
        got = False; splits = R43.split_events(s)
        for c in ciks:
            cf = facts_of(c["cik"], cache)
            if cf is None:
                st = man.get(c["cik"], {}).get("status")
                (no_facts if (st == "404" or partial) else missing).append(f"{s}:{c['cik']}"); continue        # 404 = the SEC holds no XBRL facts for that CIK
            lo = str((pd.Timestamp(c.get("from") or meta[s]["first_bar"]) - pd.Timedelta(days=WIN_BACK)).date()); hi = str((pd.Timestamp(c.get("to") or meta[s]["last_bar"]) + pd.Timedelta(days=WIN_FWD)).date())
            use, tag, bs, flows = extract(cf, lo, hi)
            for e, v in bs.items():
                if v["filed"] >= e:
                    bs_rows.append(dict(symbol=s, fiscal_date=e, filed=v["filed"], form=v["form"], so_bs=v["val"], lag_days=int((pd.Timestamp(v["filed"]) - pd.Timestamp(e)).days)))
            if not use:
                continue
            got = True; tag_used[tag] = tag_used.get(tag, 0) + 1
            rows += rows_for(s, c["cik"], use, tag, flows, splits, dates, fix_dt, C[:, j], T)
        if not got and not any(x.startswith(s + ":") for x in missing + no_facts):
            no_shares.append(s)                                                   # every CIK document present, none with a usable share series
    assert partial or not missing, f"[C] {len(missing)} CIK documents not cached (run the fetch, or pass --partial): {missing[:6]}"
    df = pd.DataFrame(rows); bs_df = pd.DataFrame(bs_rows)
    info = dict(n_unresolved=len(unresolved), unresolved=unresolved, n_missing=len(missing), n_no_facts_404=len(no_facts), no_facts_404=no_facts, n_no_share_facts=len(no_shares), no_share_facts=no_shares, tag_used=tag_used,
                splits_visible=rows_for.visible, splits_restated=rows_for.restated_splits, n_misdated_dropped=rows_for.misdated, n_rows=int(len(df)), n_names=int(df["symbol"].nunique()) if len(df) else 0, partial=partial)
    log(f"panel: {len(df):,} rows on {info['n_names']} names; unresolved {len(unresolved)}; no share facts {len(no_shares)}; tag used {tag_used}; splits visible {rows_for.visible} / judged restated {rows_for.restated_splits}; mis-dated rows dropped {rows_for.misdated}")
    return df, bs_df, info


def extras(P, df, bs_df, meta, log=print):
    res = json.loads(DEALS.read_text())["resolution"]; syms = list(P["symbols"]); usable = df[np.isfinite(df["NS"]) & (df["t_av"] >= 0) & (df["avail_date"].str[:4].astype(int) <= max(R43.YEARS))]
    have = set(usable["symbol"]); out = {}
    conf = {s: res.get(s, {}).get("confidence", "unresolved") for s in syms}
    out["coverage_by_confidence"] = {c: dict(n=sum(conf[s] == c for s in syms), usable_NS=float(np.mean([s in have for s in syms if conf[s] == c])) if any(conf[s] == c for s in syms) else None) for c in ("high", "low", "unresolved")}
    dead = [s for s in syms if meta[s]["cohort"] == "dead"]; dy = {}
    for s in dead:
        y = meta[s]["last_bar"][:4]; dy.setdefault(y, []).append(s in have)
    out["dead_coverage_by_delist_year"] = {y: dict(n=len(v), usable=float(np.mean(v))) for y, v in sorted(dy.items())}
    # the filing lag proper: PERIOD END -> filed, on the balance-sheet instants (the cover-page count is dated at the cover, days before filing)
    lag = bs_df[bs_df["fiscal_date"] >= "2010-01-01"]; q = [.1, .5, .9]
    out["filing_lag"] = dict(basis="us-gaap:CommonStockSharesOutstanding period end -> filed", n=int(len(lag)), all={str(p): float(lag["lag_days"].quantile(p)) for p in q}, over_90=float((lag["lag_days"] > 90).mean()),
                             by_form={f: {str(p): float(g["lag_days"].quantile(p)) for p in q} for f, g in lag.groupby("form") if len(g) >= 200},
                             by_year={y: float(g["lag_days"].median()) for y, g in lag.groupby(lag["fiscal_date"].str[:4]) if len(g) >= 200},
                             cover_to_filed_p50=float(df[(df["t_av"] >= 0) & (df["tag"] == "dei")]["lag_days"].median()))
    rs = df[df["n_later"] > 0]; out["restatement"] = dict(rows_with_later_filing=float((df["n_later"] > 0).mean()), restated_share=float(df["restated"].mean()), restated_given_later=float(rs["restated"].mean()) if len(rs) else None)
    # EDGAR balance-sheet instant vs the vendor at the same period end
    v = pd.read_csv(R43.PANEL, dtype={"fiscal_date": str, "symbol": str})[["symbol", "fiscal_date", "so_raw"]] if R43.PANEL.exists() else None
    if v is not None and len(bs_df):
        j = bs_df.merge(v, on=["symbol", "fiscal_date"]); j = j[(j["so_bs"] > 0) & (j["so_raw"] > 0)]; d = np.abs(np.log(j["so_bs"] / j["so_raw"]))
        out["vs_vendor"] = dict(n_overlap=int(len(j)), median_abs_log=float(d.median()), within_1pct=float((d < 0.01).mean()), within_10pct=float((d < 0.10).mean()))
    else:
        out["vs_vendor"] = None
    log("\n6. D444 EXTRAS")
    log("  coverage by CIK confidence: " + "  ".join(f"{c}: n {v['n']} usable {100*(v['usable_NS'] or 0):.0f}%" for c, v in out["coverage_by_confidence"].items()))
    log("  dead coverage by delisting year: " + " ".join(f"{y}:{100*v['usable']:.0f}%({v['n']})" for y, v in out["dead_coverage_by_delist_year"].items()))
    fl = out["filing_lag"]; log(f"  filing lag, period end -> filed ({fl['n']:,} balance-sheet instants): p10 {fl['all']['0.1']:.0f} p50 {fl['all']['0.5']:.0f} p90 {fl['all']['0.9']:.0f} d; > 90 d {100*fl['over_90']:.1f}%; by form " + " ".join(f"{f}:{v['0.5']:.0f}" for f, v in fl["by_form"].items()) + "; median by year " + " ".join(f"{y}:{m:.0f}" for y, m in fl["by_year"].items()) + f";  cover date -> filed p50 {fl['cover_to_filed_p50']:.0f} d")
    r = out["restatement"]; log(f"  restatement: {100*r['rows_with_later_filing']:.1f}% of values are filed again later; {100*r['restated_share']:.1f}% changed by > 0.1% ({100*(r['restated_given_later'] or 0):.0f}% of those refiled)")
    if out["vs_vendor"]:
        vv = out["vs_vendor"]; log(f"  EDGAR balance-sheet count vs vendor at the same period end: {vv['n_overlap']:,} name-quarters; median |log ratio| {100*vv['median_abs_log']:.2f}%; within 1% {100*vv['within_1pct']:.0f}%; within 10% {100*vv['within_10pct']:.0f}%")
    return out


def _prep():
    PREP = _load("d348p", "d348_prep.py"); return PREP.prep(need_grids=True)


def cmd_build(partial):
    t0 = time.time(); P = _prep(); meta = json.loads(R43.META.read_text())["symbols"]; df, bs_df, info = build_panel(P, meta, partial)
    assert (pd.to_datetime(df["avail_date"]) >= pd.to_datetime(df["fiscal_date"])).all(), "[L] a value filed before its period end"
    assert all(str(P["dates"][t])[:10] > a for t, a in zip(df["t_av"], df["avail_date"]) if t >= 0), "[L] availability not strictly after the filing date"
    df.to_csv(PANEL, index=False, compression="gzip"); bs_df.to_csv(REPO / "data" / "d444_bs_instants.csv.gz", index=False, compression="gzip"); PANEL_INFO.write_text(json.dumps(info, indent=1))
    print(f"wrote {PANEL.relative_to(REPO)} ({len(df):,} rows) in {(time.time()-t0)/60:.1f} min")


def cmd_run():
    t0 = time.time(); print("D444 -- EDGAR point-in-time issuance: D443's stage-0 tables on the EDGAR panel, plus lag, restatement, overlap. NO forward return.\n      spec committed in f0d97af before the fetcher and this file\n")
    P = _prep(); meta = json.loads(R43.META.read_text())["symbols"]; df = pd.read_csv(PANEL, dtype={"fiscal_date": str, "avail_date": str, "symbol": str, "cik": str}); bs_df = pd.read_csv(REPO / "data" / "d444_bs_instants.csv.gz", dtype={"fiscal_date": str, "symbol": str})
    info = json.loads(PANEL_INFO.read_text()); assert not info.get("partial"), "[C] the panel on disk is partial"
    res = R43.stage0(P, df, meta); res["extras"] = extras(P, df, bs_df, meta); res["build"] = info
    a = res["abandon"]; cov = res["coverage"]["by_group"]; sh = res["shape"]["all"]; pr = res["proxy"]; ex = res["extras"]
    print("\nD444 PREDICTIONS\n" + f"  X-a alive >= 92%, dead 65-85%, all >= 85%; A1 does not fire          : alive {100*cov['cohort:alive']['usable_NS']:.0f}%  dead {100*cov['cohort:dead']['usable_NS']:.0f}%  all {100*cov['all']['usable_NS']:.0f}%;  A1 {a['A1_dead_coverage_lt_50']}\n"
          + f"  X-b lag median 38-48, p90 ~80, > 90 d < 5%                            : p50 {ex['filing_lag']['all']['0.5']:.0f}  p90 {ex['filing_lag']['all']['0.9']:.0f}  > 90 d {100*ex['filing_lag']['over_90']:.1f}%\n"
          + f"  X-c restated 5-15%                                                    : {100*ex['restatement']['restated_share']:.1f}%\n"
          + f"  X-d NS median +0.5..+1.5, > 0 on 60-68%, repurchase 45-55%            : median {100*sh['NS_q']['0.5']:+.1f}  > 0 {100*sh['NS_pos']:.0f}%  repurchase {100*sh['any_repurchase']:.0f}% (NIY reported on {100*sh['neq4_reported']:.0f}% of rows)\n"
          + f"  X-e persistence 0.35-0.50; R2 0.08-0.20; max |rho| < 0.30; |rho mom| < 0.10 : {res['persistence']['NS_1y']['rho_mean']:+.3f}; R2 {pr['rank_r2']['mean']:.3f}; max {a['rho_max']:.3f}; mom {pr['spearman']['mom12']['mean']:+.3f}\n"
          + (f"  X-f vs vendor within 1% on >= 85%; splits visible >= 90%                : {100*ex['vs_vendor']['within_1pct']:.0f}% of {ex['vs_vendor']['n_overlap']:,}; visible {info['splits_visible']} / restated {info['splits_restated']} ({100*info['splits_visible']/max(1, info['splits_visible']+info['splits_restated']):.0f}%)" if ex["vs_vendor"] else "  X-f no vendor overlap available"))
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min   (no forward return read)")


def cmd_selftest():
    t0 = time.time(); print("== (a) first-filed extraction: the original value wins, later filings count as restatements, S-1 counts are dropped, window respected")
    rows = [dict(end="2015-03-31", val=100, filed="2015-05-10", form="10-Q"), dict(end="2015-03-31", val=103, filed="2016-03-01", form="10-K"), dict(end="2015-03-31", val=100.05, filed="2016-06-01", form="10-Q"),
            dict(end="2015-06-30", val=110, filed="2015-08-09", form="10-Q"), dict(end="2015-06-30", val=110, filed="2015-08-01", form="S-1"), dict(end="2014-01-31", val=5, filed="2014-03-01", form="10-Q"), dict(end="2015-09-30", val=None, filed="2015-11-01", form="10-Q")]
    ff = first_filed(rows, "2015-01-01", "2015-12-31")
    assert set(ff) == {"2015-03-31", "2015-06-30"} and ff["2015-03-31"] == dict(val=100.0, filed="2015-05-10", form="10-Q", n_later=2, restated=True) and ff["2015-06-30"]["n_later"] == 0 and not ff["2015-06-30"]["restated"], ff
    ff2 = first_filed([dict(end="2015-03-31", val=100, filed="2015-05-10", form="10-Q"), dict(end="2015-03-31", val=100.05, filed="2016-03-01", form="10-K")], "2015-01-01", "2015-12-31"); assert not ff2["2015-03-31"]["restated"]
    print("  ok: 2015-03-31 first-filed 100 (restated by 103 later), 0.05% change is not a restatement, S-1 and null and out-of-window rows dropped")
    print("== (b) tag choice and the annual-flow filter")
    cf = {"facts": {"dei": {"EntityCommonStockSharesOutstanding": {"units": {"shares": [dict(end=f"2015-0{m}-15", val=100 + m, filed=f"2015-0{m}-20", form="10-Q") for m in (3, 6, 9)]}}},
                    "us-gaap": {"CommonStockSharesOutstanding": {"units": {"shares": [dict(end="2015-03-31", val=99, filed="2015-05-10", form="10-Q")]}},
                                "PaymentsForRepurchaseOfCommonStock": {"units": {"USD": [dict(end="2015-12-31", val=7, filed="2016-02-20", form="10-K", fp="FY", frame="CY2015"), dict(end="2015-06-30", val=3, filed="2015-08-01", form="10-Q", fp="Q2", frame="CY2015Q2")]}}}}}
    use, tag, bs, flows = extract(cf, "2015-01-01", "2016-12-31"); assert tag == "us-gaap" and list(use) == ["2015-03-31"] and list(flows["rep"]) == ["2015-12-31"] and flows["iss"] == {}, (tag, use, flows)
    cf["facts"]["dei"]["EntityCommonStockSharesOutstanding"]["units"]["shares"].append(dict(end="2015-12-15", val=112, filed="2016-02-20", form="10-K")); use, tag, *_ = extract(cf, "2015-01-01", "2016-12-31"); assert tag == "dei" and len(use) == 4
    print("  ok: 3 cover rows -> balance-sheet series; 4 -> cover series; only the FY frame of the flow survives")
    print("== (c) rows: availability strictly after the filing date, NS on the adjusted series, [S] flag, NIY from the annual flow")
    dates = np.array([str(d.date()) for d in pd.bdate_range("2014-01-01", "2016-12-31")]); fix_dt = pd.to_datetime(dates); T = dates.size; close = np.full(T, 5.0)
    use = {f"{y}-{m}-{d}": dict(val=v, filed=f, form="10-Q", n_later=0, restated=False) for (y, m, d, v, f) in [("2014", "03", "31", 100, "2014-05-09"), ("2014", "06", "30", 100, "2014-08-08"), ("2014", "09", "30", 100, "2014-11-07"), ("2014", "12", "31", 100, "2015-02-27"),
                                                                                                            ("2015", "03", "31", 100, "2015-05-08"), ("2015", "06", "30", 200, "2015-08-07"), ("2015", "09", "30", 200, "2015-11-06"), ("2015", "12", "31", 200, "2016-02-26"), ("2016", "03", "31", 200, "2016-05-06"), ("2016", "06", "30", 200, "2016-08-05")]}
    flows = {"rep": {"2015-12-31": dict(val=250.0)}, "iss": {"2015-12-31": dict(val=1250.0)}}; rows_for.visible = rows_for.restated_splits = 0
    rs = {r["fiscal_date"]: r for r in rows_for("X", "0000000001", use, "dei", flows, [("2015-05-15", 2.0)], dates, fix_dt, close, T)}
    assert all(dates[r["t_av"]] > r["avail_date"] for r in rs.values() if r["t_av"] >= 0) and rs["2015-03-31"]["lag_days"] == 38
    assert abs(rs["2016-06-30"]["NS"]) < 1e-12 and not rs["2015-06-30"]["flag"] and abs(rs["2015-03-31"]["so_adj"] - 200) < 1e-12 and rows_for.visible == 1
    assert abs(rs["2016-06-30"]["NIY"] - 1000.0 / (200 * 5.0)) < 1e-12 and math.isnan(rs["2015-09-30"]["NIY"])
    ru = {r["fiscal_date"]: r for r in rows_for("X", "0000000001", use, "dei", flows, [], dates, fix_dt, close, T)}; assert abs(ru["2016-03-31"]["NS"] - math.log(2)) < 1e-12 and ru["2015-06-30"]["flag"]
    flat = {e: dict(v, val=100) for e, v in use.items()}; rows_for.visible = rows_for.restated_splits = 0; rows_for("Y", "0000000002", flat, "dei", {"rep": {}, "iss": {}}, [("2015-05-15", 2.0)], dates, fix_dt, close, T); assert rows_for.restated_splits == 1 and rows_for.visible == 0
    print("  ok: t_av after filed (lag 38 d); split adjusted NS 0 / unadjusted ln 2 flagged; a flat series judges the split restated; NIY = (1250 - 250) / (200 x 5)")
    print("== (d) the real panel, if built: filing dates precede availability; every value's period end precedes its filing date")
    if PANEL.exists():
        df = pd.read_csv(PANEL, dtype={"fiscal_date": str, "avail_date": str, "symbol": str, "cik": str}); assert (pd.to_datetime(df["avail_date"]) >= pd.to_datetime(df["fiscal_date"])).all()
        print(f"  {len(df):,} rows; lag min {df['lag_days'].min()} d; forms {df['form'].value_counts().head(4).to_dict()}")
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
