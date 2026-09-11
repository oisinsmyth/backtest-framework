"""D441 -- quoted spreads on the names B trades: is the modelled half-spread a quote or a range, and what does B net at the quote.
Spec docs/decisions/D441-quoted-spreads-on-the-names-B-trades-...md, committed in a92710a BEFORE this file. In-sample; no holdout.
D336's instrument (scripts/d336_ibkr_quoted_spreads.py) is imported, not altered: its pull(), TokenBucket, quoted_half, ohlc_estimates
and assertions [W] [N] [G] [U]; the raw cache data/raw/ibkr/ is SHARED (a name D336 pulled is not pulled again).

    uv run python -u scripts/run_d441_b_quotes.py --plan                       # data/d441_sample.json, before any quote (no network)
    uv run --group ibkr python scripts/run_d441_b_quotes.py --pull --host 127.0.0.1 --port <PORT> --client-id 441   # the principal
    uv run python -u scripts/run_d441_b_quotes.py --compare                    # ratio by tercile; B re-costed at the quote; the bar
    uv run python -u scripts/run_d441_b_quotes.py --selftest                   # plan == disk; mocked pull; [K2]; broken inputs raise

One deviation from D336's compare, disclosed: a name that fails [N] or [G] is EXCLUDED AND LISTED (D336 aborts on the first). With
272 names one acquired-since or re-listed name must not stop the comparison; the RESULT reports every exclusion by tag.
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys, tempfile, time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
D36 = _load("d336q", "d336_ibkr_quoted_spreads.py")                     # light: numpy/pandas; estimators loaded lazily by D36
SAMPLE = REPO / "data" / "d441_sample.json"; OUT = REPO / "data" / "d441_comparison.json"; RAW_DIR = D36.RAW_DIR
MIN_TRADES = 10; TAIL_BARS = 21; MIN_DISTINCT_CLOSES = 5; LAST_BAR = "2026-08-26"; WINDOW_BARS = 252
CAPS = (20, 40); SIDE = 1; SEED = 441; N_BOOT = 1000
CAPTURE, CHASE_BP = 0.66, 9.0                                            # D439 / D440's passive line, applied at the quote
TERC = {0: "narrow", 1: "mid", 2: "wide"}


def tercile_of(h, cuts):
    h = np.asarray(h, float)
    return np.where(~np.isfinite(h), -1, np.where(h <= cuts[0], 0, np.where(h <= cuts[1], 1, 2)))


# ------------------------------------------------------------------------------------------ the book (D440's, re-simulated)
def load_book():
    """P, the kernel, D436's B events, the PUB grid and D438's cuts. Heavy (the d348 cache); loaded once per process."""
    A34 = _load("d434", "run_d434_atlas_volume.py"); A35 = _load("d435", "run_d435_atlas_conditional.py"); A92 = _load("d392", "run_d392_base_rate_atlas.py")
    R38 = _load("d438", "run_d438_cost_axes.py"); PREP = _load("d348p", "d348_prep.py"); V59 = _load("d359r", "run_d359_loser_rally_short.py")
    P = PREP.prep(need_grids=True); T, N = P["T"], P["n"]; elig = np.asarray(P["elig"]); dates = np.array([str(x)[:10] for x in P["dates"]])
    SC = np.full((T, N), 50.0); R38.SC = SC; idx = A92.eligible_index(elig)
    mk = A92.draw_mask(np.random.default_rng(A92.SEED), idx, (T, N), 2_000); r1 = V59.run_mirror(P, mk, SC, "cap", 20); m1, c1 = A92.score_once(V59, P, mk, 20, "long", SC)
    assert abs(m1 - float(V59.V47.pnl_bp(r1).mean())) < 1e-12 and c1 == len(r1["trades"]), "[K]"
    st = A35.state_pools_unshifted(P, elig); vp, F = A34.volume_pools_unshifted(P, elig)
    ev = A35.shift(st["price_hi"] & vp["rv_x3"], elig); assert int(ev.sum()) == 12597, "[F] not D436's B"
    HS = np.asarray(P["HALF"]["PUB"], float); hs_prev = np.full_like(HS, np.nan); hs_prev[1:] = HS[:-1]
    CLOSE = np.asarray(P["CLOSE"], float); VOL = np.asarray(P["VOL"], float)
    assert HS.shape == CLOSE.shape == VOL.shape == (T, N), "[S] grids are not (T, N)"
    cuts = json.load(open(REPO / "data" / "d438_cost_axes.json"))["cuts"]["B"]
    d40 = json.load(open(REPO / "data" / "d440_stage2_B.json"))
    print("  [K] kernel probe;  [F] events == D436's B (12,597);  D438's spread cuts attached")
    return dict(P=P, V59=V59, R38=R38, ev=ev, HS=HS, hs_prev=hs_prev, CLOSE=CLOSE, VOL=VOL, cuts=cuts, dates=dates, T=T, N=N, elig=elig, SC=SC,
                symbols=list(P["symbols"]), d440=d40, PER_SHARE=float(V59.PER_SHARE))


def simulate(B, cap):
    return B["V59"].simulate(B["P"], B["ev"], B["SC"], "cap", cap, SIDE)


def trade_arrays(B, r):
    """Per-trade arrays in the order of r["trades"]: name row, entry bar, hs at entry (the kernel's cost basis), hs known at t-1 (D438's
    tercile basis), price, commission round trip (bp), 2c PUB (bp), borrow (bp), pnl (bp)."""
    tr = r["trades"]; row = np.array([t[0] for t in tr]); e0 = np.array([t[1] for t in tr])
    hs = B["HS"][e0, row]; hsp = B["hs_prev"][e0, row]; px = B["CLOSE"][e0, row]
    comm = 2.0 * B["PER_SHARE"] / px * 1e4; c_pub = 2.0 * hs + comm
    borrow = np.asarray(B["V59"].V49.borrow_of(B["P"], tr)[0], float); pnl = np.asarray(B["V59"].V47.pnl_bp(r), float)
    assert np.isfinite(hs).all() and np.isfinite(px).all() and (px > 0).all(), "[S] a trade without a half-spread or price at entry"
    return dict(row=row, e0=e0, hs=hs, hsp=hsp, px=px, comm=comm, c_pub=c_pub, borrow=borrow, pnl=pnl, terc=tercile_of(hsp, B["cuts"]))


# ------------------------------------------------------------------------------------------ --plan
def plan(B, meta, r20):
    ta = trade_arrays(B, r20); syms = B["symbols"]; T = B["T"]
    rows = []
    for j in np.unique(ta["row"]):
        m = ta["row"] == j; s = syms[j]; mi = meta.get(s, {})
        vol_tail = B["VOL"][T - TAIL_BARS:, j]; cl_tail = B["CLOSE"][T - TAIL_BARS:, j]
        padded = bool(np.nan_to_num(vol_tail).max() <= 0 or np.unique(cl_tail[np.isfinite(cl_tail)]).size < MIN_DISTINCT_CLOSES)
        hs252 = B["HS"][T - WINDOW_BARS:, j]; hsp_tr = ta["hsp"][m]
        med_hsp = float(np.nanmedian(hsp_tr)) if np.isfinite(hsp_tr).any() else float("nan")
        rows.append(dict(symbol=s, exchange=mi.get("exchange"), cohort=mi.get("cohort"), last_bar=mi.get("last_bar"), n_splits=int(mi.get("n_splits") or 0), padded=padded,
                         n_trades=int(m.sum()), n_wide=int((ta["terc"][m] == 2).sum()), n_mid=int((ta["terc"][m] == 1).sum()), n_narrow=int((ta["terc"][m] == 0).sum()), n_no_spread=int((ta["terc"][m] == -1).sum()),
                         hs_pub_at_trades=med_hsp, tercile=int(tercile_of([med_hsp], B["cuts"])[0]),
                         hs_pub_last252=float(np.nanmedian(hs252)) if np.isfinite(hs252).any() else float("nan"), pnl_sum=float(ta["pnl"][m].sum())))
    n_all = len(rows); tot_tr = int(ta["pnl"].size); tot_wide = int((ta["terc"] == 2).sum())
    alive = [x for x in rows if x["cohort"] == "alive" and x["last_bar"] == LAST_BAR]; unpadded = [x for x in alive if not x["padded"]]
    chosen = [x for x in unpadded if x["n_trades"] >= MIN_TRADES]
    for x in chosen:
        ex = x["exchange"]; assert ex in D36.EXCH_MAP, f"{x['symbol']}: exchange {ex!r} has no primaryExchange mapping"; x["primaryExchange"] = D36.EXCH_MAP[ex]
    chosen.sort(key=lambda x: (-x["n_wide"], -x["n_trades"], x["symbol"]))
    assert all(x["tercile"] in (0, 1, 2) for x in chosen), "[T] a sampled name has no tercile"
    d336 = {r["symbol"] for r in json.load(open(D36.SAMPLE_OUT))["rows"]} if D36.SAMPLE_OUT.exists() else set()
    return dict(record="D441", written_before_any_quote_was_seen=True, rule=f"B cap-20 names, alive, last bar {LAST_BAR}, unpadded (volume > 0 and >= {MIN_DISTINCT_CLOSES} distinct closes in the last {TAIL_BARS} bars), >= {MIN_TRADES} trades; splits not excluded",
                cuts_d438=B["cuts"], n_names_traded=n_all, n_trades_cap20=tot_tr, n_wide_trades_cap20=tot_wide,
                n_alive=len(alive), n_alive_unpadded=len(unpadded), padded_alive=[x["symbol"] for x in alive if x["padded"]],
                n_sampled=len(chosen), trades_covered=int(sum(x["n_trades"] for x in chosen)), wide_trades_covered=int(sum(x["n_wide"] for x in chosen)),
                pnl_share_covered=float(sum(x["pnl_sum"] for x in chosen) / ta["pnl"].sum()), n_in_d336_sample=len(d336 & {x["symbol"] for x in chosen}),
                by_tercile={TERC[k]: int(sum(x["tercile"] == k for x in chosen)) for k in TERC},
                hs_pub_last252_median=float(np.nanmedian([x["hs_pub_last252"] for x in chosen])), hs_pub_at_trades_median=float(np.nanmedian([x["hs_pub_at_trades"] for x in chosen])),
                pull_order="wide-tercile trade count descending", rows=chosen)


def cmd_plan():
    t0 = time.time(); B = load_book(); meta = json.load(open(D36.META))["symbols"]; r20 = simulate(B, 20)
    s = plan(B, meta, r20); D36._dump(s, SAMPLE)
    print(f"names traded at cap 20 {s['n_names_traded']}  trades {s['n_trades_cap20']:,}  wide trades {s['n_wide_trades_cap20']:,}")
    print(f"  alive & last bar {LAST_BAR}: {s['n_alive']};  unpadded: {s['n_alive_unpadded']}  (padded: {s['padded_alive']})")
    print(f"  >= {MIN_TRADES} trades: {s['n_sampled']} names, {s['trades_covered']:,} trades ({100*s['trades_covered']/s['n_trades_cap20']:.0f}%), {s['wide_trades_covered']:,} wide ({100*s['wide_trades_covered']/s['n_wide_trades_cap20']:.0f}%), P&L share {100*s['pnl_share_covered']:.0f}%; in D336's sample {s['n_in_d336_sample']}")
    print(f"  by tercile {s['by_tercile']};  modelled PUB half: last 252 bars median {s['hs_pub_last252_median']:.1f}, at the B trades {s['hs_pub_at_trades_median']:.1f}")
    print(f"  spec section 1 said 272 names / 6,883 trades / 1,982 wide / 33 in D336 -- any difference is disclosed in the RESULT")
    print(f"wrote {SAMPLE.relative_to(REPO)} ({len(s['rows'])} names) in {time.time()-t0:.0f}s")


# ------------------------------------------------------------------------------------------ --pull (the principal's session)
def cmd_pull(host, port, client_id):
    import ib_async
    from ib_async import IB, Stock
    from datetime import datetime, timezone
    sample = json.loads(SAMPLE.read_text()); ib = IB(); pace = None; client = getattr(ib, "client", None)
    for name in ("setConnectOptions", "setConnectionOptions"):
        if hasattr(client, name):
            getattr(client, name)("+PACEAPI"); pace = f"client.{name}('+PACEAPI')"; break
    else:
        if hasattr(client, "connectOptions"):
            client.connectOptions = b"+PACEAPI"; pace = "client.connectOptions = b'+PACEAPI'"
    print(f"connecting {host}:{port} clientId={client_id}; pacing option: {pace or 'not available'}", flush=True)
    ib.connect(host, port, clientId=client_id, readonly=True); accounts = list(ib.managedAccounts())
    meta_base = {"d441_provider": "Interactive Brokers TWS API via ib_async", "d441_ib_async_version": getattr(ib_async, "__version__", "?"),
                 "d441_fetched_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "d441_accounts": accounts, "d441_account_type": D36._account_type(accounts),
                 "d441_sample_file": str(SAMPLE.relative_to(REPO)), "d441_pacing": pace, "d441_n_sample": len(sample["rows"])}
    bucket = D36.TokenBucket()
    try:
        res = D36.pull(ib, sample["rows"], RAW_DIR, lambda s, pe: Stock(s, "SMART", "USD", primaryExchange=pe), bucket, meta_base)
    finally:
        ib.disconnect()
    m = res["meta"]; print(f"done: ok {len(m['symbols_ok'])}, unresolved {len(m['symbols_unresolved'])}, error {len(m['symbols_error'])}; bucket waited {bucket.n_waits} times")


# ------------------------------------------------------------------------------------------ --compare
def quotes_by_name(sample, fx, raw_dir):
    """Per sampled name with a CSV: the quoted half (median over days), PB / PUB / AR on the fixture over exactly the quoted dates, the
    ratios. [W] [U] raise (they are code errors); [N] and [G] exclude and list (data)."""
    raw_dir = Path(raw_dir); groups = {s: g.sort_values("date") for s, g in fx.groupby("symbol")}
    rows, missing, excluded = [], [], []
    for r in sample["rows"]:
        sym = r["symbol"]; p = raw_dir / f"{sym}.csv"
        if not p.exists():
            missing.append(sym); continue
        ib = pd.read_csv(p, dtype={"date": str}).sort_values("date"); ok, half = D36.quoted_half(ib["open"].to_numpy(), ib["close"].to_numpy())
        q = ib[ok]; qdates = q["date"].to_numpy(dtype=str)
        try:
            D36.assert_N(sym, len(qdates))
        except AssertionError as e:
            excluded.append(dict(symbol=sym, tag="N", msg=str(e))); continue
        g = groups.get(sym); assert g is not None, f"[W] {sym}: not in the fixture"
        j = g[g["date"].isin(qdates)]; D36.assert_W(sym, qdates, j["date"].to_numpy(dtype=str))
        H, L, C = (j[k].to_numpy(dtype=float) for k in ("high", "low", "close")); est = D36.ohlc_estimates(H, L, C)
        ib_mid_last = float((q["open"].iloc[-1] + q["close"].iloc[-1]) / 2.0)
        try:
            D36.assert_G(sym, ib_mid_last, float(C[-1]))
        except AssertionError as e:
            excluded.append(dict(symbol=sym, tag="G", msg=str(e))); continue
        quoted = float(np.median(half[ok])); D36.assert_U(sym, quoted, est)
        rows.append(dict(symbol=sym, tercile=r["tercile"], n_trades=r["n_trades"], n_wide=r["n_wide"], n_quoted_days=int(len(qdates)), first_date=str(qdates[0]), last_date=str(qdates[-1]),
                         quoted_half_bp=quoted * 1e4, PB_bp=est["PB"] * 1e4, PUB_bp=est["PUB"] * 1e4, AR_bp=est["AR"] * 1e4, zero_rate=est["zero_rate"],
                         ratio_PUB=quoted / est["PUB"] if est["PUB"] > 0 else float("inf"), ratio_PB=quoted / est["PB"] if est["PB"] > 0 else float("inf"),
                         hs_pub_at_trades=r["hs_pub_at_trades"], ib_mid_last=ib_mid_last, fixture_close_last=float(C[-1]), g_abs_log=abs(math.log(ib_mid_last / float(C[-1])))))
    return rows, missing, excluded


def boot_median(x, rng, n=N_BOOT):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if x.size < 2:
        return float("nan")
    return float(np.std([np.median(rng.choice(x, x.size)) for _ in range(n)], ddof=1))


def rho_table(qrows, rng):
    """Median ratio quoted/PUB (and /PB) by the name's D438 tercile, with a name-bootstrap SE; the imputation table for unsampled names."""
    out = {}
    for k, nm in TERC.items():
        v = np.array([r["ratio_PUB"] for r in qrows if r["tercile"] == k]); vb = np.array([r["ratio_PB"] for r in qrows if r["tercile"] == k])
        out[nm] = dict(n=int(v.size), median_ratio_PUB=float(np.median(v)) if v.size else float("nan"), se=boot_median(v, rng), median_ratio_PB=float(np.median(vb)) if vb.size else float("nan"),
                       median_quoted_bp=float(np.median([r["quoted_half_bp"] for r in qrows if r["tercile"] == k])) if v.size else float("nan"))
    allv = np.array([r["ratio_PUB"] for r in qrows]); out["all"] = dict(n=int(allv.size), median_ratio_PUB=float(np.median(allv)), se=boot_median(allv, rng),
                                                                          median_ratio_PB=float(np.median([r["ratio_PB"] for r in qrows])), median_quoted_bp=float(np.median([r["quoted_half_bp"] for r in qrows])))
    return out


def rho_per_name(B, qrows, sample, tab):
    """rho for every name row in the panel: measured where quoted, else the tercile median of the measured names; names with no
    tercile (no spread at any trade) get the all-names median. Returns (rho array (N,), measured mask (N,))."""
    N = B["N"]; sym_i = {s: i for i, s in enumerate(B["symbols"])}; rho = np.full(N, np.nan); measured = np.zeros(N, bool)
    for r in qrows:
        rho[sym_i[r["symbol"]]] = r["ratio_PUB"]; measured[sym_i[r["symbol"]]] = True
    return rho, measured


def impute(B, rho, measured, ta, tab):
    """Per-trade rho: the name's measured value, else the tercile median (the trade's D438 tercile), else the all-names median."""
    rj = rho[ta["row"]].copy(); miss = ~measured[ta["row"]]; fallback = tab["all"]["median_ratio_PUB"]
    for k, nm in TERC.items():
        v = tab[nm]["median_ratio_PUB"]; sel = miss & (ta["terc"] == k); rj[sel] = v if np.isfinite(v) else fallback     # an empty tercile falls back to all names
    sel = miss & (ta["terc"] == -1); rj[sel] = fallback
    assert np.isfinite(rj).all(), "[I] a trade has no rho after imputation"
    return rj, ~miss


def recost(B, cap, rj, meas, ta, r, dates, rho_override=None):
    """Per-trade and per-bar lines at the quote. rho_override (selftest [K2]) replaces every trade's rho."""
    R37 = sys.modules.get("d437") or _load("d437", "run_d437_stage1.py"); R38 = B["R38"]; T = B["T"]
    rj = np.full_like(rj, rho_override) if rho_override is not None else rj
    c_q = 2.0 * ta["hs"] * rj + ta["comm"]; p_q = c_q * (1 - CAPTURE) + CHASE_BP
    net_pub = ta["pnl"] - ta["c_pub"] - ta["borrow"]; net_q = ta["pnl"] - c_q - ta["borrow"]; net_pq = ta["pnl"] - p_q - ta["borrow"]
    def line(m):
        n = int(m.sum()); se = float(ta["pnl"][m].std(ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
        return dict(trades=n, gross=float(ta["pnl"][m].mean()), se=se, c_pub=float(ta["c_pub"][m].mean()), c_quote=float(c_q[m].mean()), passive_quote=float(p_q[m].mean()), borrow=float(ta["borrow"][m].mean()),
                    net_pub=float(net_pub[m].mean()), net_quote=float(net_q[m].mean()), net_passive_quote=float(net_pq[m].mean()), median_gross=float(np.median(ta["pnl"][m])))
    per_trade = dict(all_imputed=line(np.ones(ta["pnl"].size, bool)), measured_only=line(meas))
    per_trade["by_tercile_all"] = {TERC[k]: line(ta["terc"] == k) for k in TERC if (ta["terc"] == k).any()}
    per_trade["by_tercile_measured"] = {TERC[k]: line(meas & (ta["terc"] == k)) for k in TERC if (meas & (ta["terc"] == k)).any()}
    # the book: D440's per-bar crossed constant scaled by the trade-mean cost ratio (rho == 1 reproduces D440 exactly, [K2])
    tb = B["V59"].trade_block(B["P"], r, B["elig"], SIDE, False); db = B["V59"].deployed_block(r, B["P"]); borrow_mean = tb.get("borrow", {}).get("mean_bp", 0.0)
    turn = db["PUB"]["hedged"]["turnover"]; dep_cost2 = db["PUB"]["hedged_2x"]["cost_bp"]; crossed_d440 = dep_cost2 + borrow_mean * turn
    scale = (c_q.mean() + ta["borrow"].mean()) / (ta["c_pub"].mean() + ta["borrow"].mean()); crossed_q = crossed_d440 * scale
    passive_q = turn * (p_q.mean() + ta["borrow"].mean()); trade_mean_line = turn * (ta["c_pub"].mean() + ta["borrow"].mean())
    g = np.nan_to_num(np.asarray(r["book_dep_x"], float)) * 1e4; d0 = int(ta["e0"].min()); gs = g[d0:]; ds = dates[d0:]
    se_g, mg = R37.block_boot(gs, ds); nq = gs - crossed_q; half = d0 + (T - d0) // 2; era2 = np.arange(d0, T) >= half
    se2, m2 = R37.block_boot(nq[era2], ds[era2]); se1, m1 = R37.block_boot(nq[~era2], ds[~era2]); ys = np.array([int(d[:4]) for d in ds])
    book = dict(gross=mg, gross_se=se_g, turnover=turn, dep_cost2=dep_cost2, cost_crossed_d440=crossed_d440, cost_crossed_trade_mean_pub=trade_mean_line, cost_scale=float(scale), cost_crossed_quote=float(crossed_q), cost_passive_quote=float(passive_q),
                net_crossed_d440=float(mg - crossed_d440), net_crossed_quote=float(mg - crossed_q), net_passive_quote=float(mg - passive_q), net_se=se_g,
                sharpe_crossed_quote=float(nq.mean() / nq.std(ddof=1) * np.sqrt(252)), era1_quote=m1, era1_se=se1, era2_quote=m2, era2_se=se2, era2_start=str(dates[half]),
                by_year_quote={str(y): float(nq[ys == y].mean()) for y in np.unique(ys)})
    return dict(cap=cap, per_trade=per_trade, book=book, rho_mean_trade=float(rj.mean()), rho_measured_share=float(meas.mean()))


def compare(sample, fx, raw_dir, B, out_path, log=print, rho_override=None):
    rng = np.random.default_rng(SEED); qrows, missing, excluded = quotes_by_name(sample, fx, raw_dir)
    assert qrows, "no sampled name has a usable quote"
    tab = rho_table(qrows, rng); rho, measured = rho_per_name(B, qrows, sample, tab)
    res = dict(record="D441", n_sampled=len(sample["rows"]), n_quoted=len(qrows), n_missing_csv=len(missing), missing_csv=missing, excluded=excluded, ratio_by_tercile=tab,
               median_quoted_half_bp=tab["all"]["median_quoted_bp"], median_est_bp={k: float(np.median([r[f"{k}_bp"] for r in qrows])) for k in ("PB", "PUB", "AR")}, cap={}, rho_override=rho_override)
    log(f"quoted {len(qrows)} of {len(sample['rows'])} names ({len(missing)} without a CSV, {len(excluded)} excluded: {[(e['symbol'], e['tag']) for e in excluded]})")
    log(f"  median quoted half {res['median_quoted_half_bp']:.1f} bp/side;  modelled on the same dates: PB {res['median_est_bp']['PB']:.1f}  PUB {res['median_est_bp']['PUB']:.1f}  AR {res['median_est_bp']['AR']:.1f}")
    for nm in ("narrow", "mid", "wide", "all"):
        t = tab[nm]; log(f"  {nm:7s} n {t['n']:3d}  quoted {t['median_quoted_bp']:5.1f}  rho quoted/PUB {t['median_ratio_PUB']:.3f} ± {t['se']:.3f}   quoted/PB {t['median_ratio_PB']:.3f}")
    for cap in CAPS:
        r = simulate(B, cap); ta = trade_arrays(B, r); rj, meas = impute(B, rho, measured, ta, tab); c = recost(B, cap, rj, meas, ta, r, B["dates"], rho_override); res["cap"][str(cap)] = c
        if cap == 20 and rho_override is None:
            assert abs(c["per_trade"]["all_imputed"]["gross"] - B["d440"]["cap"]["20"]["per_trade"]["gross"]) < 1e-9, "[P2] cap-20 gross != D440's"
        pt, bk = c["per_trade"], c["book"]
        log(f"\nCAP {cap}  (rho measured on {100*c['rho_measured_share']:.0f}% of trades; trade-mean rho {c['rho_mean_trade']:.3f})")
        for lab in ("all_imputed", "measured_only"):
            x = pt[lab]; log(f"  per trade {lab:13s} n {x['trades']:5,}  gross {x['gross']:+6.2f} ± {x['se']:.1f}  2c PUB {x['c_pub']:5.1f} -> net {x['net_pub']:+6.2f}   2c QUOTE {x['c_quote']:5.1f} -> net {x['net_quote']:+6.2f}   passive@quote {x['passive_quote']:4.1f} -> net {x['net_passive_quote']:+6.2f}")
        for nm, x in pt["by_tercile_all"].items():
            log(f"    tercile {nm:6s} n {x['trades']:5,}  gross {x['gross']:+6.1f}  2c PUB {x['c_pub']:5.1f}  2c QUOTE {x['c_quote']:5.1f}  net PUB {x['net_pub']:+6.1f}  net QUOTE {x['net_quote']:+6.1f}")
        log(f"  book: gross {bk['gross']:+.3f} ± {bk['net_se']:.3f}/bar  crossed D440 {bk['cost_crossed_d440']:.3f} (trade-mean PUB line {bk['cost_crossed_trade_mean_pub']:.3f}) -> net {bk['net_crossed_d440']:+.3f}   crossed@QUOTE {bk['cost_crossed_quote']:.3f} (x{bk['cost_scale']:.3f}) -> net {bk['net_crossed_quote']:+.3f} ({bk['net_crossed_quote']/bk['net_se']:+.1f} SE)  Sharpe {bk['sharpe_crossed_quote']:+.2f}   passive@QUOTE {bk['cost_passive_quote']:.3f} -> net {bk['net_passive_quote']:+.3f}")
        log(f"        era1 {bk['era1_quote']:+.3f} ± {bk['era1_se']:.3f}   era2 (from {bk['era2_start']}) {bk['era2_quote']:+.3f} ± {bk['era2_se']:.3f} ({bk['era2_quote']/bk['era2_se']:+.1f} SE)")
    w = tab["wide"]; b20 = res["cap"]["20"]["book"]; m20 = res["cap"]["20"]["per_trade"]["measured_only"]
    T1q = bool(np.isfinite(w["se"]) and (1.0 - w["median_ratio_PUB"]) > 2 * w["se"]); T2q = bool(m20["net_quote"] > 0 and m20["net_quote"] / m20["se"] >= 2)
    T3q = bool(b20["net_crossed_quote"] > 0 and b20["net_crossed_quote"] / b20["net_se"] >= 2); T4q = bool(b20["era2_quote"] > 0 and b20["era2_quote"] / b20["era2_se"] >= 2)
    res["bar"] = dict(T1q=T1q, T2q=T2q, T3q=T3q, T4q=T4q, candidate=bool(T3q and T4q))
    log(f"\nTHE BAR (cap 20)\n  T1q wide-tercile median rho < 1 by 2 SE           : {T1q}   ({w['median_ratio_PUB']:.3f} ± {w['se']:.3f})\n  T2q measured-only per-trade net@quote > 0 by 2 SE  : {T2q}   ({m20['net_quote']:+.2f} ± {m20['se']:.2f})")
    log(f"  T3q book net crossed@quote > 0 by 2 SE          : {T3q}   ({b20['net_crossed_quote']:+.3f} ± {b20['net_se']:.3f}, {b20['net_crossed_quote']/b20['net_se']:+.1f} SE)\n  T4q era-2 net crossed@quote > 0 by 2 SE          : {T4q}   ({b20['era2_quote']:+.3f} ± {b20['era2_se']:.3f})")
    log(f"  CANDIDATE for the holdouts (T3q & T4q, crossed line): {res['bar']['candidate']}")
    a = tab["all"]; n_, wd = tab["narrow"], tab["wide"]; wt = res["cap"]["20"]["per_trade"]["by_tercile_all"].get("wide", {})
    log("\nPREDICTIONS\n" + f"  X-a median quoted half 5-15 bp/side                 : {a['median_quoted_bp']:.1f}\n  X-b median rho 0.15-0.40; rho vs PB ~1.4x higher     : {a['median_ratio_PUB']:.3f}; vs PB {a['median_ratio_PB']:.3f} ({a['median_ratio_PB']/a['median_ratio_PUB']:.2f}x)\n"
        + f"  X-c wide rho >= 1.3 x narrow rho                     : wide {wd['median_ratio_PUB']:.3f} vs narrow {n_['median_ratio_PUB']:.3f} ({wd['median_ratio_PUB']/n_['median_ratio_PUB'] if n_['median_ratio_PUB'] else float('nan'):.2f}x)\n"
        + f"  X-d measured-only per trade net@quote +15..+25       : {m20['net_quote']:+.2f} (gross {m20['gross']:+.1f}, 2c@quote {m20['c_quote']:.1f}, borrow {m20['borrow']:.1f})\n"
        + f"  X-e book cap 20 net@quote +1.0..+1.4, T3q fails      : {b20['net_crossed_quote']:+.3f} ± {b20['net_se']:.3f}; cap 40 {res['cap']['40']['book']['net_crossed_quote']:+.3f} ± {res['cap']['40']['book']['net_se']:.3f}\n"
        + f"  X-f wide tercile net@quote +60..+80 per trade        : {wt.get('net_quote', float('nan')):+.1f}")
    res["qrows"] = qrows; D36._dump(res, Path(out_path)); log(f"wrote {out_path}")
    return res


def cmd_compare():
    t0 = time.time(); sample = json.loads(SAMPLE.read_text()); B = load_book()
    fx = D36.load_fixture([r["symbol"] for r in sample["rows"]]); compare(sample, fx, RAW_DIR, B, OUT); print(f"{(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ --selftest
def _expect_raise(label, fn):
    try:
        fn()
    except (AssertionError, SystemExit) as e:
        print(f"    [6] {label:40s} raised: {str(e)[:100]}"); return
    raise AssertionError(f"[6] {label}: did not raise on a broken input")


def cmd_selftest():
    t0 = time.time(); print("== (a) plan reproduces the sample on disk"); B = load_book(); meta = json.load(open(D36.META))["symbols"]; r20 = simulate(B, 20)
    s = plan(B, meta, r20); assert SAMPLE.exists(), "run --plan first"; on_disk = json.loads(SAMPLE.read_text()); assert json.loads(json.dumps(s, default=D36._jsonable)) == on_disk, "[S] plan differs from disk"
    print(f"  identical: {len(s['rows'])} names")
    print("== (b) mocked pull into a temp dir on 8 sample names; quoted half injected at 20 bp")
    rows = s["rows"][:8]; syms = [r["symbol"] for r in rows]; fx = D36.load_fixture(syms); dates = np.sort(fx["date"].unique())[-WINDOW_BARS:]
    sub = fx[fx["date"].isin(dates)]; win = {k: g.sort_values("date")[["date", "close"]] for k, g in sub.groupby("symbol")}
    clk = SimpleNamespace(t=0.0); mini = dict(s, rows=rows)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td); mock = D36.MockIB(win, half=0.0020, unresolved=[syms[-1]]); tb = D36.TokenBucket(clock=lambda: clk.t, sleep=lambda x: setattr(clk, "t", clk.t + x))
        res = D36.pull(mock, rows, td / "raw", lambda a, pe: SimpleNamespace(symbol=a, primaryExchange=pe), tb, {"provider": "mock"}, log=lambda *a: None)
        assert res["n_new"] == 7 and mock.n_details == 8, res["meta"]
        qrows, missing, excluded = quotes_by_name(mini, fx, td / "raw"); assert len(qrows) == 7 and missing == [syms[-1]] and not excluded
        qs = np.array([r["quoted_half_bp"] for r in qrows]); assert np.all(np.abs(qs - 20.0) < 2.5), qs
        assert all(abs(r["ratio_PUB"] - r["quoted_half_bp"] / r["PUB_bp"]) < 1e-12 for r in qrows); print(f"  quoted {qs.round(1)} bp; ratios {[round(r['ratio_PUB'], 3) for r in qrows]}")
        print("== (c) compare on the mocked cache; [K2] rho == 1 reproduces D440's crossed line")
        out = compare(mini, fx, td / "raw", B, td / "cmp.json", log=lambda *a: None)
        d40 = B["d440"]["cap"]["20"]; b = out["cap"]["20"]["book"]
        assert abs(b["cost_crossed_d440"] - d40["book"]["cost_crossed"]) < 1e-9 and abs(b["gross"] - d40["book"]["gross"]) < 1e-9, "[K2] the re-simulated book is not D440's"
        out1 = compare(mini, fx, td / "raw", B, td / "cmp1.json", log=lambda *a: None, rho_override=1.0); b1 = out1["cap"]["20"]["book"]
        assert abs(b1["cost_crossed_quote"] - d40["book"]["cost_crossed"]) < 1e-9 and abs(b1["net_crossed_quote"] - d40["book"]["net_crossed"]) < 1e-9, "[K2] rho == 1 != D440"
        p1 = out1["cap"]["20"]["per_trade"]["all_imputed"]; assert abs(p1["c_quote"] - p1["c_pub"]) < 1e-12 and abs(p1["net_quote"] - p1["net_pub"]) < 1e-12
        out5 = compare(mini, fx, td / "raw", B, td / "cmp5.json", log=lambda *a: None, rho_override=0.5); p5 = out5["cap"]["20"]["per_trade"]["all_imputed"]
        assert abs(p5["c_quote"] - ((p1["c_pub"] - np.mean(trade_arrays(B, r20)["comm"])) * 0.5 + np.mean(trade_arrays(B, r20)["comm"]))) < 1e-9, "[K2] rho == 0.5 does not halve the spread half of 2c"
        print(f"  D440 crossed {d40['book']['cost_crossed']:.4f} == re-simulated {b['cost_crossed_d440']:.4f}; rho=1 net {b1['net_crossed_quote']:+.4f} == D440 {d40['book']['net_crossed']:+.4f}; rho=0.5 halves the spread term")
        print(f"  measured share of trades at cap 20 with 7 names: {100*out['cap']['20']['rho_measured_share']:.1f}%; imputation covers the rest")
        print("== (d) broken inputs raise")
        ib = pd.read_csv(td / "raw" / f"{syms[0]}.csv", dtype={"date": str})
        def shifted():
            bad = ib.copy(); d = pd.to_datetime(bad["date"]) + pd.Timedelta(days=1); bad["date"] = d.dt.strftime("%Y-%m-%d"); (td / "bad").mkdir(exist_ok=True); bad.to_csv(td / "bad" / f"{syms[0]}.csv", index=False)
            quotes_by_name(dict(mini, rows=rows[:1]), fx, td / "bad")
        _expect_raise("[W] quoted dates shifted a day", shifted)
        def ahead():
            bad = ib.copy(); bad.loc[bad.index[-1], "date"] = "2026-09-01"; (td / "bad2").mkdir(exist_ok=True); bad.to_csv(td / "bad2" / f"{syms[0]}.csv", index=False)
            fx2 = pd.concat([fx, fx[fx["symbol"] == syms[0]].tail(1).assign(date="2026-09-01", timestamp="2026-09-01")]); quotes_by_name(dict(mini, rows=rows[:1]), fx2, td / "bad2")
        _expect_raise("[W] a quoted date past the window end", ahead)
        bad = ib.copy(); bad[["open", "close"]] *= 1.2; (td / "bad3").mkdir(exist_ok=True); bad.to_csv(td / "bad3" / f"{syms[0]}.csv", index=False)
        q, m, e = quotes_by_name(dict(mini, rows=rows[:1]), fx, td / "bad3"); assert not q and len(e) == 1 and e[0]["tag"] == "G", (q, e)
        print(f"    [6] [G] mid 20% off the fixture              excluded and listed: {e[0]['msg'][:80]}")
        bad = ib.head(100); (td / "bad4").mkdir(exist_ok=True); bad.to_csv(td / "bad4" / f"{syms[0]}.csv", index=False)
        q, m, e = quotes_by_name(dict(mini, rows=rows[:1]), fx, td / "bad4"); assert not q and len(e) == 1 and e[0]["tag"] == "N", (q, e)
        print(f"    [6] [N] 100 quoted days                      excluded and listed: {e[0]['msg'][:80]}")
        def bad_terc():
            ta = trade_arrays(B, r20); ta2 = dict(ta, terc=np.full_like(ta["terc"], -1)); rho = np.full(B["N"], np.nan); impute(B, rho, np.zeros(B["N"], bool), ta2, {"all": {"median_ratio_PUB": float("nan")}, **{n: {"median_ratio_PUB": 0.3} for n in TERC.values()}})
        _expect_raise("[I] a trade left without rho", bad_terc)
        _expect_raise("[T] a sampled name without a tercile", lambda: plan(dict(B, hs_prev=np.full_like(B["hs_prev"], np.nan)), meta, r20))   # no spread at any trade -> tercile -1
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--plan", action="store_true"); g.add_argument("--pull", action="store_true"); g.add_argument("--compare", action="store_true"); g.add_argument("--selftest", action="store_true")
    ap.add_argument("--host", default=None); ap.add_argument("--port", type=int, default=None); ap.add_argument("--client-id", type=int, default=None)
    a = ap.parse_args()
    if a.plan:
        cmd_plan()
    elif a.pull:
        if a.host is None or a.port is None or a.client_id is None:
            ap.error("--pull needs --host, --port and --client-id (no defaults)")
        if not SAMPLE.exists():
            ap.error(f"{SAMPLE} missing: run --plan first")
        cmd_pull(a.host, a.port, a.client_id)
    elif a.compare:
        cmd_compare()
    else:
        cmd_selftest()
