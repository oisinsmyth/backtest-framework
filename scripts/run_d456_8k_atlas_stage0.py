"""D456 stage 0 -- the 8-K item atlas: every corporate-event item type on the dead-inclusive fixture, from the EDGAR submissions index.
NO forward return is read. Spec committed in 5f8899e BEFORE this file.

    uv run python -u scripts/run_d456_8k_atlas_stage0.py --build      # parse D331's cached submissions (re-fetch where missing) -> data/d456_8k_events.csv.gz
    uv run python -u scripts/run_d456_8k_atlas_stage0.py --run        # the stage-0 tables -> data/d456_stage0.json
    uv run python -u scripts/run_d456_8k_atlas_stage0.py --selftest

An event = one 8-K (or 8-K/A) filing on one name (issuer mapped by CIK inside D331's window); it enters the cell of every modern item
it carries except 9.01 and 7.01; 'pure' = a single item other than 9.01. Availability = the first fixture bar strictly after filingDate.
Filings after END are parsed and flagged unread (the confirmation slice for the stage-1 atlas).
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
DEALS = REPO / "data" / "fixtures" / "us_shorts_daily_raw_deals.json"; META = REPO / "data" / "fixtures" / "us_shorts_daily_raw.meta.json"
EVENTS = REPO / "data" / "d456_8k_events.csv.gz"; INFO = REPO / "data" / "d456_build_info.json"; OUT = REPO / "data" / "d456_stage0.json"
END = "2023-12-29"; SPAN_END = "2026-08-26"; YEARS = range(2010, 2024); MIN_CELL = 300; NOT_CELLS = ("9.01", "7.01")
CANDIDATE_ITEMS = ("1.01", "1.02", "1.03", "2.01", "2.02", "2.03", "2.04", "2.05", "2.06", "3.01", "3.02", "3.03", "4.01", "4.02", "5.01", "5.02", "5.03", "5.07", "5.08", "8.01")
A1_DEAD, A2_MIN_CELLS, A3_LAG = 0.50, 8, 6.0


# ------------------------------------------------------------------------------------------ parsing
def cik_windows():
    res = json.loads(DEALS.read_text())["resolution"]; meta = json.loads(META.read_text())["symbols"]; out = {}
    for s, r in res.items():
        for c in r.get("ciks") or []:
            out.setdefault(c["cik"].lstrip("0").zfill(10), []).append((s, c.get("from") or meta[s]["first_bar"], c.get("to") or meta[s]["last_bar"]))
    return out


def parse_items(s):
    """Modern item codes (d.dd) from the index string; legacy single-number codes are returned separately."""
    modern, legacy = [], []
    for tok in str(s or "").split(","):
        t = tok.strip()
        if not t:
            continue
        (modern if "." in t else legacy).append(t)
    return modern, legacy


def filings_of(F, D31, cik, lo, hi):
    """All 8-K / 8-K/A filings of one CIK with filingDate in [lo, hi], from the cached index (pages fetched where missing)."""
    j = F.get_json(D31.URL_SUBMISSIONS.format(name=f"CIK{cik}.json"), kind="submissions")
    if j is None:
        return None
    chunks = [j["filings"]["recent"]]
    for fl in j["filings"].get("files", []):
        if fl["filingTo"] >= lo and fl["filingFrom"] <= hi:
            pj = F.get_json(D31.URL_SUBMISSIONS.format(name=fl["name"]), kind="submissions")
            if pj is not None:
                chunks.append(pj)
    rows = []
    for ch in chunks:
        n = len(ch["form"]); items = ch.get("items") or [""] * n; rep = ch.get("reportDate") or [""] * n
        for i in range(n):
            if ch["form"][i] in ("8-K", "8-K/A") and lo <= ch["filingDate"][i] <= hi:
                rows.append(dict(cik=cik, form=ch["form"][i], filing=ch["filingDate"][i], report=rep[i] or "", items=items[i] or "", accession=ch["accessionNumber"][i]))
    return rows


def cmd_build():
    t0 = time.time(); D31 = _load("d331", "d331_edgar_deals.py"); F = D31.Fetcher(D31.CACHE_DIR, D31.MAX_RPS); cmap = cik_windows(); meta = json.loads(META.read_text())["symbols"]
    rows, missing, no8k = [], [], []
    for k, (cik, wins) in enumerate(sorted(cmap.items())):
        lo = min(w[1] for w in wins); hi = SPAN_END
        fl = filings_of(F, D31, cik, lo, hi)
        if fl is None:
            missing.append(cik); continue
        n0 = len(rows)
        for r in fl:
            for s, wlo, whi in wins:
                if wlo <= r["filing"] <= (SPAN_END if meta[s]["last_bar"] == SPAN_END else whi):
                    rows.append(dict(r, symbol=s)); break
        if len(rows) == n0:
            no8k.append(cik)
        if (k + 1) % 200 == 0:
            print(f"  {k+1}/{len(cmap)} CIKs  {len(rows):,} 8-K rows  (cached {F.n_cached}, fetched {F.n_fetched})  {(time.time()-t0)/60:.1f} min", flush=True)
    df = pd.DataFrame(rows).drop_duplicates(["symbol", "accession"]); df["unread"] = df["filing"] > END
    df = df.sort_values(["symbol", "filing", "accession"]).reset_index(drop=True); df.to_csv(EVENTS, index=False, compression="gzip")
    info = dict(n_ciks=len(cmap), n_missing_docs=len(missing), missing=missing[:50], n_no_8k=len(no8k), n_rows=int(len(df)), n_rows_unread=int(df["unread"].sum()), n_names=int(df["symbol"].nunique()), docs_cached=F.n_cached, docs_fetched=F.n_fetched, fetch_events=F.events[-20:])
    INFO.write_text(json.dumps(info, indent=1)); print(f"8-K rows {len(df):,} on {info['n_names']} names ({info['n_rows_unread']:,} after {END}, unread); CIK docs missing {len(missing)}; no 8-K {len(no8k)}; index docs cached {F.n_cached} / fetched {F.n_fetched}\nwrote {EVENTS.relative_to(REPO)} in {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ the tables
def stage0(P, df, meta, log=print):
    A92 = _load("d392", "run_d392_base_rate_atlas.py"); syms = list(P["symbols"]); sym_i = {s: i for i, s in enumerate(syms)}; dates = np.array([str(x)[:10] for x in P["dates"]]); T = P["T"]
    elig = np.asarray(P["elig"]).copy(); t_end = int(np.searchsorted(dates, END, side="right")); elig[t_end:] = False; live = np.asarray(P["live"]); fix = pd.to_datetime(dates); res = {}
    d = df[~df["unread"].astype(bool) & (df["filing"] >= "2010-01-01")].copy(); d["t_av"] = np.searchsorted(fix, pd.to_datetime(d["filing"]), side="right"); d = d[d["t_av"] < T]; d["j"] = d["symbol"].map(sym_i); d = d[d["j"].notna()]; d["j"] = d["j"].astype(int)
    d["live_at"] = [bool(live[j, t]) for j, t in zip(d["j"], d["t_av"])]; d["year"] = d["filing"].str[:4].astype(int); parsed = d["items"].map(parse_items); d["modern"] = [m for m, _ in parsed]; d["legacy"] = [l for _, l in parsed]
    d["pure"] = d["modern"].map(lambda m: [x for x in m if x != "9.01"]).map(lambda m: m[0] if len(m) == 1 else None)
    dl = d[d["live_at"]]
    # 1. coverage
    coh = {s: meta[s]["cohort"] for s in syms}; st = {s: meta[s]["status"] for s in syms}; conf = {s: r.get("confidence", "unresolved") for s, r in json.loads(DEALS.read_text())["resolution"].items()}; has = set(dl["symbol"]); cov = {}
    for lab, key in (("cohort", coh), ("status", st), ("cik", conf)):
        for g in sorted(set(key.values())):
            names = [s for s in syms if key[s] == g]; cov[f"{lab}:{g}"] = dict(n=len(names), share=float(np.mean([s in has for s in names])))
    cov["all"] = dict(n=len(syms), share=len(has) / len(syms)); per_ny = []
    for y in YEARS:
        idx = np.flatnonzero(np.array([x[:4] for x in dates]) == str(y)); alive = np.flatnonzero(live[:, idx].any(axis=1)); c = dl[dl["year"] == y].groupby("symbol").size()
        per_ny += [int(c.get(syms[j], 0)) for j in alive]
    per_ny = np.array(per_ny); res["coverage"] = dict(by_group=cov, per_name_year={"p10": float(np.quantile(per_ny, .1)), "p50": float(np.median(per_ny)), "p90": float(np.quantile(per_ny, .9)), "zero_share": float((per_ny == 0).mean())})
    log("1. COVERAGE (>= 1 8-K while live, 2010-2023)"); [log(f"  {k:16s} n {v['n']:5d}  {100*v['share']:5.1f}%") for k, v in cov.items()]; log(f"  8-Ks per live name-year: p10 {res['coverage']['per_name_year']['p10']:.0f} p50 {res['coverage']['per_name_year']['p50']:.0f} p90 {res['coverage']['per_name_year']['p90']:.0f}; zero on {100*res['coverage']['per_name_year']['zero_share']:.0f}%")
    # 2. counts
    ex = dl.explode("modern"); ex = ex[ex["modern"].notna()]; cnt = ex["modern"].value_counts(); cells = [it for it in CANDIDATE_ITEMS if cnt.get(it, 0) >= MIN_CELL]
    pure_cnt = dl["pure"].value_counts(); byy = {it: {str(y): int(((ex["modern"] == it) & (ex["year"] == y)).sum()) for y in YEARS} for it in CANDIDATE_ITEMS}
    legacy_n = int(dl["legacy"].map(len).gt(0).sum()); res["counts"] = dict(n_filings=int(len(dl)), items={it: int(cnt.get(it, 0)) for it in CANDIDATE_ITEMS + NOT_CELLS}, pure={it: int(pure_cnt.get(it, 0)) for it in CANDIDATE_ITEMS}, cells=cells, by_year=byy, legacy_filings=legacy_n,
                         share_2_02=float(cnt.get("2.02", 0) / len(dl)), share_5_02=float(cnt.get("5.02", 0) / len(dl)))
    log(f"\n2. COUNTS: {len(dl):,} 8-K filings while live; cells with >= {MIN_CELL}: {len(cells)} -> {cells}; legacy-coded filings {legacy_n}")
    log("  item: filings (pure)  " + "  ".join(f"{it}: {cnt.get(it,0):,} ({pure_cnt.get(it,0):,})" for it in CANDIDATE_ITEMS) + f"   9.01 {cnt.get('9.01',0):,}  7.01 {cnt.get('7.01',0):,}")
    # 3. timeliness (filing - reportDate, business days)
    ok = dl["report"].str.len() == 10; lag = pd.Series([int(np.busday_count(np.datetime64(a), np.datetime64(b))) for a, b in zip(dl.loc[ok, "report"], dl.loc[ok, "filing"])], index=dl.index[ok]); dl = dl.assign(lag=lag)
    exl = dl.explode("modern"); exl = exl[exl["modern"].notna() & exl["lag"].notna()]
    res["timeliness"] = {it: dict(n=int((exl["modern"] == it).sum()), p50=float(exl[exl["modern"] == it]["lag"].median()), p90=float(exl[exl["modern"] == it]["lag"].quantile(.9)), over_4=float((exl[exl["modern"] == it]["lag"] > 4).mean())) for it in cells}
    res["timeliness"]["all"] = dict(n=int(lag.notna().sum()), p50=float(lag.median()), p90=float(lag.quantile(.9)), over_4=float((lag > 4).mean()), no_report_date=float((~ok).mean()))
    log(f"\n3. TIMELINESS (business days, reportDate -> filingDate): all p50 {res['timeliness']['all']['p50']:.0f} p90 {res['timeliness']['all']['p90']:.0f} > 4 on {100*res['timeliness']['all']['over_4']:.1f}% (no report date on {100*res['timeliness']['all']['no_report_date']:.1f}%);  " + "  ".join(f"{it}: {v['p50']:.0f}/{v['p90']:.0f}/{100*v['over_4']:.0f}%" for it, v in res["timeliness"].items() if it != "all"))
    # 4. co-occurrence
    top = [it for it in cells] + ["9.01", "7.01"]; M = {}
    for a in top:
        ma = dl["modern"].map(lambda m, a=a: a in m); M[a] = {b: float((ma & dl["modern"].map(lambda m, b=b: b in m)).sum() / max(ma.sum(), 1)) for b in top}
    res["cooccurrence"] = M; with_202 = {it: M[it].get("2.02", 0.0) for it in cells}
    log("\n4. CO-OCCURRENCE (share of an item's filings also carrying the column item): " + "  ".join(f"{it}: with 2.02 {100*with_202[it]:.0f}%, 9.01 {100*M[it]['9.01']:.0f}%, 8.01 {100*M[it].get('8.01',0):.0f}%" for it in cells))
    # 5. what each item sits in
    tp = A92.tercile_pools(P, elig); C = np.asarray(P["CLOSE"], float); DV = np.asarray(P["DV"], float)
    with np.errstate(invalid="ignore", divide="ignore"):
        ret20 = np.log(C / np.vstack([np.full((20, C.shape[1]), np.nan), C[:-20]])); ldv = np.log(pd.DataFrame(DV).rolling(60, min_periods=30).mean().to_numpy())
    def terc_of(grid, t, j):
        col = elig[t] & np.isfinite(grid[t]); k = col.sum()
        if k < 30 or not np.isfinite(grid[t, j]):
            return -1
        return int(min(2, 3 * (grid[t, col] < grid[t, j]).mean()))
    prox = {}
    for it in cells:
        sub = ex[ex["modern"] == it]; out = {}
        for nm in ("price", "vol", "mom"):
            cnt3 = np.zeros(3); n = 0
            for t, j in zip(sub["t_av"], sub["j"]):
                tb = max(t - 1, 0)
                for k, band in enumerate(("lo", "mid", "hi")):
                    if tp[f"{nm}_{band}"][tb, j]:
                        cnt3[k] += 1; n += 1
            out[nm] = (cnt3 / max(n, 1)).round(3).tolist()
        for nm, grid in (("ret20", ret20), ("logdv", ldv)):
            cnt3 = np.zeros(3); n = 0
            for t, j in zip(sub["t_av"], sub["j"]):
                k = terc_of(grid, max(t - 1, 0), j)
                if k >= 0:
                    cnt3[k] += 1; n += 1
            out[nm] = (cnt3 / max(n, 1)).round(3).tolist()
        out["dead_share"] = float(np.mean([coh[s] == "dead" for s in sub["symbol"]])); out["n"] = int(len(sub)); prox[it] = out
    res["proxy"] = prox; base_dead = float(np.mean([coh[s] == "dead" for s in syms]))
    log(f"\n5. WHAT EACH ITEM SITS IN (lo/mid/hi tercile share at the bar before availability; base 33/33/33; dead share base {100*base_dead:.0f}%)")
    for it in cells:
        p = prox[it]; log(f"  {it}  n {p['n']:6,}  price {100*p['price'][0]:.0f}/{100*p['price'][1]:.0f}/{100*p['price'][2]:.0f}  mom {100*p['mom'][0]:.0f}/{100*p['mom'][1]:.0f}/{100*p['mom'][2]:.0f}  ret20 {100*p['ret20'][0]:.0f}/{100*p['ret20'][1]:.0f}/{100*p['ret20'][2]:.0f}  DV {100*p['logdv'][0]:.0f}/{100*p['logdv'][1]:.0f}/{100*p['logdv'][2]:.0f}  dead {100*p['dead_share']:.0f}%")
    # 6. tails
    most = dl.groupby("symbol").size().sort_values(ascending=False).head(10); m301 = ex[ex["modern"].isin(["3.01", "4.02"])].groupby(["symbol", "modern"]).size().sort_values(ascending=False).head(10)
    res["tails"] = dict(most_8k=[(s, int(n), st[s]) for s, n in most.items()], most_301_402=[(s, it, int(n), st[s]) for (s, it), n in m301.items()])
    log("\n6. TAILS: most 8-Ks " + ", ".join(f"{s} {n} ({stt})" for s, n, stt in res["tails"]["most_8k"]) + "\n   most 3.01 / 4.02: " + ", ".join(f"{s} {it} x{n} ({stt})" for s, it, n, stt in res["tails"]["most_301_402"]))
    # abandon + predictions
    dead_cov = cov["cohort:dead"]["share"]; lag202 = res["timeliness"].get("2.02", {}).get("p50", float("nan"))
    res["abandon"] = dict(A1=bool(dead_cov < A1_DEAD), A2=bool(len(cells) < A2_MIN_CELLS), A3=bool(not (lag202 <= A3_LAG)), dead_cov=dead_cov, n_cells=len(cells), lag_202=lag202)
    log(f"\nABANDON\n  A1 dead coverage < 50%  : {res['abandon']['A1']}  ({100*dead_cov:.0f}%)\n  A2 cells < 8            : {res['abandon']['A2']}  ({len(cells)})\n  A3 2.02 lag median > 6  : {res['abandon']['A3']}  ({lag202:.0f})")
    c = res["counts"]; tl = res["timeliness"]; pr = res["proxy"]; g = lambda it, k: pr.get(it, {}).get(k, [float("nan")] * 3)
    log("\nPREDICTIONS\n" + f"  X-a alive >= 95%, dead >= 85%; 8-Ks per name-year p50 6-10                     : alive {100*cov['cohort:alive']['share']:.0f}%  dead {100*dead_cov:.0f}%  p50 {res['coverage']['per_name_year']['p50']:.0f}\n"
        + f"  X-b cells 12-16; 2.02 30-40%, 5.02 12-20%; 4.02 < 250; 3.01 300-800; 2.06 300-600 : {len(cells)}; 2.02 {100*c['share_2_02']:.0f}%  5.02 {100*c['share_5_02']:.0f}%;  4.02 {c['items']['4.02']}  3.01 {c['items']['3.01']}  2.06 {c['items']['2.06']}\n"
        + f"  X-c lag p50 1-2, > 4 on < 10%, tightest on 2.02                                  : all {tl['all']['p50']:.0f} / {100*tl['all']['over_4']:.0f}%;  2.02 {tl.get('2.02',{}).get('p50',float('nan')):.0f} / {100*tl.get('2.02',{}).get('over_4',float('nan')):.0f}%\n"
        + f"  X-d 1.01 with 2.03 or 9.01 >= 60%; 5.02 pure >= 40%; 8.01 co-occurs broadly      : 1.01 w/ 9.01 {100*M.get('1.01',{}).get('9.01',0):.0f}% w/ 2.03 {100*M.get('1.01',{}).get('2.03',0):.0f}%;  5.02 pure {100*c['pure']['5.02']/max(c['items']['5.02'],1):.0f}%\n"
        + f"  X-e 3.01/4.02/2.04/2.05 bottom price & mom >= 55%, dead >= 60% (3.01 >= 75%); 2.02 flat : " + "  ".join(f"{it}: px-lo {100*g(it,'price')[0]:.0f}% mom-lo {100*g(it,'mom')[0]:.0f}% dead {100*pr.get(it,{}).get('dead_share',float('nan')):.0f}%" for it in ("3.01", "4.02", "2.04", "2.05", "2.02") if it in pr) + "\n"
        + f"  X-f most 8-Ks: acquirers/REITs; most 3.01: collapsed                             : {[s for s,_,_ in res['tails']['most_8k'][:5]]}; 3.01/4.02 {[(s,it,stt) for s,it,_,stt in res['tails']['most_301_402'][:5]]}")
    return res


def _prep():
    return _load("d348p", "d348_prep.py").prep(need_grids=True)


def cmd_run():
    t0 = time.time(); print("D456 STAGE 0 -- the 8-K item atlas: coverage, counts, timeliness, co-occurrence, proxy. NO forward return.\n      spec committed in 5f8899e before this file\n")
    P = _prep(); meta = json.loads(META.read_text())["symbols"]; df = pd.read_csv(EVENTS, dtype={"symbol": str, "cik": str, "filing": str, "report": str, "items": str, "accession": str, "form": str}); df["items"] = df["items"].fillna(""); df["report"] = df["report"].fillna("")
    res = stage0(P, df, meta); res["build"] = json.loads(INFO.read_text()); OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min   (no forward return read)")


def cmd_selftest():
    t0 = time.time(); print("== (a) item parsing, pure flag, legacy exclusion, business-day lag, unread flag")
    assert parse_items("1.01,2.03,9.01") == (["1.01", "2.03", "9.01"], []) and parse_items("7,9") == ([], ["7", "9"]) and parse_items("") == ([], []) and parse_items(None) == ([], [])
    d = pd.DataFrame(dict(items=["5.02,9.01", "2.02", "1.01,2.03", "9.01"])); m = d["items"].map(parse_items).map(lambda x: x[0]); pure = m.map(lambda mm: [x for x in mm if x != "9.01"]).map(lambda mm: mm[0] if len(mm) == 1 else None)
    assert list(pure[:2]) == ["5.02", "2.02"] and pd.isna(pure[2]) and pd.isna(pure[3]); assert int(np.busday_count(np.datetime64("2015-03-03"), np.datetime64("2015-03-09"))) == 4
    print("  ok")
    print("== (b) the real events file, if built: every row has a symbol and a filing date; unread == filing > END; no duplicate (symbol, accession)")
    if EVENTS.exists():
        df = pd.read_csv(EVENTS, dtype={"symbol": str, "filing": str, "accession": str}); assert df["symbol"].notna().all() and (df["unread"].astype(bool) == (df["filing"] > END)).all() and not df.duplicated(["symbol", "accession"]).any()
        print(f"  {len(df):,} rows, {int(df['unread'].sum()):,} unread")
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
