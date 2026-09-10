"""D419 -- the three exits through the PATH-VARIANT lens. Bar committed in 346c671 BEFORE this ran.

    uv run python scripts/run_d419_book.py --books                # every book, both lenses' bar order
    uv run python scripts/run_d419_book.py --controls [--workers 8]   # the 200-draw sampled_runs nulls

A slot-limited book on D413's event stream: N slots, entry at the touch-day close, each exit rule
laid over a five-bar time stop, freed slots refilled from TODAY'S touches. Scored in bp/bar on the
book and NEVER quoted beside D417's per-trade numbers (FINDINGS section 10).

THE BAR ORDER IS D295's AND IT IS THE CORRECTNESS ARGUMENT -- see `simulate`:
  1. MARK every position held during day d, once. An intrabar trigger (D417's fills, on day d's
     OHLC) marks the position to its fill and frees the slot at the close of d; otherwise the mark
     is close-to-close and a position reaching age 5 closes at C[d].
  2. drop anything delisted out from under us (no price at d)
  3. REFILL freed slots from touches on day d, entering at C[d] -- earning from d+1
  4. book return for d = sum of marks / N, idle slots earning zero
Each slot-day earns at most one mark. [RECON] holds the book to the trade ledger to 1e-9 relative
on every rule -- D295's assertion [5], the one that caught a bar credited to two positions.

THE CONTROL is D295's sampled_runs: each position exits at the close of the day its age reaches
a target drawn from the rule's OWN realised run distribution. It matches turnover, cost and refill
frequency and destroys only the rule's information. A control must share the treatment's nuisance.

THE REPLACEMENT PREMIUM (D304): for every intrabar exit, what the arriving trade earned over its
own life minus what the departing one would have earned from its fill to its scheduled exit,
split by whether a replacement was available at that close.

COSTS: every trade is charged its own name's neutral round trip at entry -- ADDENDUM 2's estimator.
net bp/bar = gross bp/bar - (costs charged) / N / days.
"""
import argparse
import importlib.util
import json
import multiprocessing as mp
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d417", REPO / "scripts" / "run_d417_exits.py")
X = importlib.util.module_from_spec(_s)
sys.modules["d417"] = X
_s.loader.exec_module(X)                      # the [SPLIT] holdout guard comes with it
C, M, Z4, D = X.C, X.M, X.Z4, X.D
CS = C.CS                                     # D285's Corwin-Schultz, imported through D413-combine

OUT = REPO / "data" / "d419_book.json"
OUT_CTRL = REPO / "data" / "d419_book_controls.json"
CACHE = REPO / "temp" / "d419_inputs.npz"
HOLD = 5
N_PRIMARY, NS = 50, (50, 25, 100)
N_CELL2 = 10
SEEDS = (419, 4190, 41900)
RULES = ("FIXED", "SL", "TS", "TP", "SLTP")
FAMILIES = ("SL", "TS", "TP")
PARAM = dict(SL=1.5, TS=1.5, TP=2.0, SLTP=(1.5, 2.0))
N_DRAW = 200
N_BOOT = 1000
IBKR = 0.0035


# ------------------------------------------------------------------ inputs
def build_inputs():
    """Everything the simulator reads, once, cached on the fixture's mtime."""
    key = int(D.FIX.stat().st_mtime_ns) % (1 << 40)
    f = CACHE.with_name(f"d419_inputs_{key}.npz")
    if f.exists():
        z = np.load(f, allow_pickle=False)
        return {k: z[k] for k in z.files}
    P = D.load_panel(verbose=False)
    atr = Z4.atr_of(P)
    A = Z4.run_arm(P, atr, "dep", M.THETA, M.LIFE, M.H, delta=M.DELTA)
    Z, g = A["Z"], A["good"]
    t = A["tt"][g]; i = Z["i"][g]; side = Z["side"][g]; r_base = A["r"][g]
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))
    tr5 = D.trailing_ret(lg, 5); eff = C.path_efficiency(lg); DV = D.X.roll_mean_T(P["CL"] * P["VOL"])
    rev = tr5[t, i] * side; ef = eff[t, i]; dv = DV[t, i]
    fin = np.isfinite(rev) & np.isfinite(ef) & np.isfinite(dv)
    cuts = (np.median(rev[fin]), np.median(ef[fin]), np.median(dv[fin]))
    c2 = fin & (rev <= cuts[0]) & (ef > cuts[1]) & (dv > cuts[2])
    T = P["CL"].shape[0]
    off = np.arange(1, HOLD + 1)
    rows = t[:, None] + off[None, :]; cols = np.repeat(i[:, None], HOLD, axis=1)
    gth = lambda A_: Z4.gather(A_, rows, cols, T)[0]
    OP, HI, LO, CL = gth(P["OP"]), gth(P["HI"]), gth(P["LO"]), gth(P["CL"])
    E = P["CL"][t, i]; ATR = atr[t, i]
    spread = CS.corwin_schultz(P["HI"].T, P["LO"].T, P["live"].T).T
    neutral = np.full_like(spread, np.nan)
    for tt in range(62, T):
        with np.errstate(invalid="ignore"):
            neutral[tt] = np.nanmedian(spread[tt - 62:tt - 2], axis=0)
    cost = neutral[t, i] + 2 * IBKR / E
    cost = np.where(np.isfinite(cost), cost, np.nanmedian(cost))
    out = dict(t=t, i=i, side=side, r_base=r_base, c2=c2, OP=OP, HI=HI, LO=LO, CL=CL, E=E, ATR=ATR,
               cost=cost, T=np.array([T]), dates=np.array(P["dates"]), symbols=np.array(P["symbols"]))
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(f, **out)
    return out


# ------------------------------------------------------------------ the simulator
def simulate(I, rule, n_slots, seed, pool_mask=None, run_targets=None, oracle=False):
    """One book. Returns per-day gross/net marks, the trade ledger, and the swap ledger.

    `run_targets` (an array of ages, one per event, or None) turns the rule into its sampled_runs
    control: exits at the close of the day the position's age reaches its target, no intrabar
    trigger. `oracle` exits at the best close over the window -- deliberate look-ahead, for [SIGN].
    """
    t, side, E, ATR, cost = I["t"], I["side"], I["E"], I["ATR"], I["cost"]
    OP, HI, LO, CL, c2 = I["OP"], I["HI"], I["LO"], I["CL"], I["c2"]
    T = int(I["T"][0])
    N = len(t)
    rng = np.random.default_rng(seed)
    order = np.lexsort((rng.random(N), ~c2))          # cell 2 first, then random
    by_day = {}
    for k in order:
        if pool_mask is None or pool_mask[k]:
            by_day.setdefault(int(t[k]), []).append(int(k))
    p = PARAM.get(rule)
    a_ = p if rule == "SL" else (p[0] if rule == "SLTP" else None)
    b_ = p if rule == "TS" else None
    c_ = p if rule == "TP" else (p[1] if rule == "SLTP" else None)
    lgE = np.log(E)
    lgCL = np.log(CL)
    if oracle:
        best_close = np.nanargmax(np.where(np.isfinite(lgCL), side[:, None] * lgCL, -np.inf), axis=1)

    held = {}                    # k -> [age, cum, best_signed]
    held_names = set()
    gross = np.zeros(T); costs = np.zeros(T); occ = np.zeros(T, np.int32)
    ent = np.zeros(T, np.int32); frees = np.zeros(T, np.int32); refilled = np.zeros(T, np.int32)
    early_frees = np.zeros(T, np.int32)
    trades = []                  # (k, pnl, age, early, exit_day, fill)
    swaps = []                   # (departing k, fill, exit_day, age, arriving k or -1)
    d0 = int(t.min()) + 1
    for d in range(d0, T):
        freed = []
        # 1. MARK, and decide, on day d
        for k in list(held):
            st = held[k]
            a = st[0]                                  # age index into the window, 0..4
            o, h, l, c = OP[k, a], HI[k, a], LO[k, a], CL[k, a]
            if not (np.isfinite(o) and np.isfinite(h) and np.isfinite(l) and np.isfinite(c)):
                # 2. delisted out from under us: no mark, position ends
                held.pop(k); held_names.discard(int(I["i"][k]))
                trades.append((k, st[1], a, False, d, np.nan)); frees[d] += 1; freed.append((k, np.nan, a, False))
                continue
            s = float(side[k]); e = s * E[k]
            prev = lgE[k] if a == 0 else lgCL[k, a - 1]
            os_, hs, ls = s * o, (s * h if s > 0 else s * l), (s * l if s > 0 else s * h)
            trig = False; fill = None
            if run_targets is not None:
                pass                                   # control: no intrabar trigger
            elif oracle:
                pass
            else:
                stop = None
                if a_ is not None: stop = e - a_ * ATR[k]
                if b_ is not None: stop = st[2] - b_ * ATR[k]
                if stop is not None and ls <= stop:
                    trig, fill = True, s * min(stop, os_)
                elif c_ is not None and hs >= e + c_ * ATR[k]:
                    trig, fill = True, s * max(e + c_ * ATR[k], os_)
            if trig:
                mark = s * (np.log(fill) - prev)
                gross[d] += mark; occ[d] += 1
                held.pop(k); held_names.discard(int(I["i"][k]))
                trades.append((k, st[1] + mark, a + 1, True, d, fill)); frees[d] += 1; freed.append((k, fill, a + 1, True))
                continue
            mark = s * (lgCL[k, a] - prev)
            gross[d] += mark; occ[d] += 1
            st[0] += 1; st[1] += mark; st[2] = max(st[2], hs)
            close_now = (st[0] >= HOLD) or (run_targets is not None and st[0] >= run_targets[k]) \
                or (oracle and a >= best_close[k])
            if close_now:
                held.pop(k); held_names.discard(int(I["i"][k]))
                trades.append((k, st[1], st[0], run_targets is not None or oracle, d, c)); frees[d] += 1
                if run_targets is not None or oracle:
                    freed.append((k, c, st[0], True))
        # 3. REFILL from touches on day d
        free = n_slots - len(held)
        arrivals = []
        if free > 0:
            for k in by_day.get(d, []):
                if free == 0:
                    break
                nm = int(I["i"][k])
                if nm in held_names or k in held:
                    continue
                if not np.isfinite(E[k]) or E[k] <= 0:
                    continue
                held[k] = [0, 0.0, side[k] * E[k]]; held_names.add(nm)
                costs[d] += cost[k]; ent[d] += 1; free -= 1; arrivals.append(k)
        # pair freed slots with arrivals, in order, for the replacement premium
        for j, (kd, fill, age, early) in enumerate(freed):
            if early:
                swaps.append((kd, fill, d, age, arrivals[j] if j < len(arrivals) else -1))
        # same-day refill is EARLY frees that found a touch at that close, over EARLY frees --
        # the first version divided by ALL frees, which read 0% on FIXED (whose frees are all
        # time stops) and understated every rule. The premium's avail/idle split is the same count.
        refilled[d] += min(len(freed), len(arrivals))
        early_frees[d] += len(freed)
    resid = sum(st[1] for st in held.values())
    return dict(gross=gross, costs=costs, occ=occ, ent=ent, frees=frees, refilled=refilled,
                early_frees=early_frees, trades=trades, swaps=swaps, resid=resid, d0=d0)


# ------------------------------------------------------------------ scoring
def score(I, R, n_slots):
    T = int(I["T"][0]); d0 = R["d0"]
    days = np.arange(d0, T)
    g = R["gross"][d0:] / n_slots; c = R["costs"][d0:] / n_slots
    net = g - c
    tr = R["trades"]
    pnl = np.array([x[1] for x in tr]); age = np.array([x[2] for x in tr]); early = np.array([x[3] for x in tr])
    win = pnl > 0
    total_book = float(R["gross"][d0:].sum()); total_pos = float(pnl.sum() + R["resid"])
    out = dict(days=int(days.size), gross_bp=float(1e4 * g.mean()), net_bp=float(1e4 * net.mean()),
               cost_bp=float(1e4 * c.mean()),
               trades=int(pnl.size), trade_mean_bp=float(1e4 * pnl.mean()) if pnl.size else None,
               trade_median_bp=float(1e4 * np.median(pnl)) if pnl.size else None,
               win_rate=float(win.mean()) if pnl.size else None,
               run=float(age.mean()) if age.size else None,
               run_win=float(age[win].mean()) if win.any() else None,
               run_lose=float(age[~win].mean()) if (~win).any() else None,
               early_share=float(early.mean()) if early.size else None,
               entries_per_day=float(R["ent"][d0:].mean()),
               turnover=float(R["ent"][d0:].mean() / n_slots),
               utilisation=float(R["occ"][d0:].mean() / n_slots),
               same_day_refill=float(R["refilled"][d0:].sum() / max(R["early_frees"][d0:].sum(), 1)),
               early_frees=int(R["early_frees"][d0:].sum()),
               recon_rel=float(abs(total_book - total_pos) / max(abs(total_pos), 1e-12)),
               gross_series=g, net_series=net, run_dist=age.astype(int))
    return out


def premium(I, R, T_):
    """D304's replacement premium on the swap ledger."""
    lgCL = np.log(I["CL"]); side = I["side"]
    pnl_of = {x[0]: x[1] for x in R["trades"]}
    rows = dict(avail=[], idle=[])
    for kd, fill, d, age, ka in R["swaps"]:
        if not np.isfinite(fill):
            continue
        # departing: from its fill to its scheduled exit at age 5
        rem = side[kd] * (lgCL[kd, HOLD - 1] - np.log(fill)) if np.isfinite(lgCL[kd, HOLD - 1]) else np.nan
        if not np.isfinite(rem):
            continue
        if ka >= 0 and ka in pnl_of:
            rows["avail"].append((pnl_of[ka] - rem, pnl_of[ka], rem))
        else:
            rows["idle"].append((-rem, 0.0, rem))
    out = {}
    for k, v in rows.items():
        if len(v) < 30:
            out[k] = dict(n=len(v)); continue
        v = np.array(v)
        out[k] = dict(n=int(v.shape[0]), premium_bp=float(1e4 * v[:, 0].mean()),
                      arriving_bp=float(1e4 * v[:, 1].mean()), forfeited_bp=float(1e4 * v[:, 2].mean()),
                      se_bp=float(1e4 * v[:, 0].std(ddof=1) / np.sqrt(v.shape[0])))
    return out


def block_boot(diff, dates, n_boot=N_BOOT, seed=7):
    """SE of the mean of a daily difference series by monthly block bootstrap."""
    mon = np.array([str(x)[:7] for x in dates])
    keys, inv = np.unique(mon, return_inverse=True)
    sums = np.bincount(inv, weights=diff); cnts = np.bincount(inv)
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, keys.size, keys.size)
        means[b] = sums[pick].sum() / cnts[pick].sum()
    return float(means.std(ddof=1)), float(diff.mean())


# ------------------------------------------------------------------ assertions
def assert_RECON(S, tag):
    assert S["recon_rel"] < 1e-9, f"[RECON] {tag}: book and ledger disagree by {S['recon_rel']:.2e} relative"


def assert_all(I):
    R0 = simulate(I, "FIXED", N_PRIMARY, SEEDS[0]); S0 = score(I, R0, N_PRIMARY)
    assert_RECON(S0, "FIXED")
    assert abs(S0["run"] - HOLD) < 0.05, f"[HOLD] the no-exit book holds {S0['run']:.3f} bars, not {HOLD}"
    Rt = simulate(I, "TP", N_PRIMARY, SEEDS[0]); St = score(I, Rt, N_PRIMARY); assert_RECON(St, "TP")
    assert St["run_win"] < St["run_lose"], f"[MECH] the target's winners run {St['run_win']:.2f} vs losers {St['run_lose']:.2f}"
    Ro = simulate(I, "FIXED", N_PRIMARY, SEEDS[0], oracle=True); So = score(I, Ro, N_PRIMARY); assert_RECON(So, "oracle")
    assert So["gross_bp"] > 3 * S0["gross_bp"] and So["gross_bp"] > 10, f"[SIGN] the oracle earns {So['gross_bp']:+.2f} bp/bar"
    for r in ("SL", "TS", "SLTP"):
        assert_RECON(score(I, simulate(I, r, N_PRIMARY, SEEDS[0]), N_PRIMARY), r)
    print(f"  [RECON] book == ledger to <1e-9 on FIXED, SL, TS, TP, SLTP and the oracle")
    print(f"  [HOLD]  the no-exit book holds {S0['run']:.3f} bars")
    print(f"  [MECH]  the target's winners run {St['run_win']:.2f} vs losers {St['run_lose']:.2f}")
    print(f"  [SIGN]  the oracle earns {So['gross_bp']:+.2f} bp/bar against FIXED's {S0['gross_bp']:+.2f}")


# ------------------------------------------------------------------ phases
def books():
    t0 = time.time()
    print("D419  the three exits through the PATH-VARIANT lens")
    print("      the bar was committed in 346c671 BEFORE this ran\n")
    I = build_inputs()
    N = len(I["t"])
    print(f"  P1  {N:,} D413 touches; cell 2 {int(I['c2'].sum()):,}; per-trade neutral round trip "
          f"median {1e4*np.median(I['cost']):.1f} bp")
    assert_all(I)
    dates = I["dates"]
    res = dict(books={}, bar={}, secondary={}, premium={})
    t1 = time.time()

    def one(rule, n_slots, seed, pool=None):
        R = simulate(I, rule, n_slots, seed, pool_mask=pool)
        S = score(I, R, n_slots); assert_RECON(S, f"{rule}/{n_slots}/{seed}")
        S["premium"] = premium(I, R, int(I["T"][0]))
        return S

    for n_slots in NS:
        for seed in SEEDS:
            for rule in RULES:
                res["books"][f"{rule}_N{n_slots}_s{seed}"] = one(rule, n_slots, seed)
    for seed in SEEDS:
        for rule in RULES:
            res["books"][f"{rule}_C2N{N_CELL2}_s{seed}"] = one(rule, N_CELL2, seed, pool=I["c2"])
    per_book = (time.time() - t1) / (len(NS) * len(SEEDS) * len(RULES) + len(SEEDS) * len(RULES))
    print(f"  {len(res['books'])} books in {time.time()-t1:.0f}s  ({per_book:.2f}s each)")

    def show(key, S):
        print(f"  {key:22s} gross {S['gross_bp']:+7.3f}  net {S['net_bp']:+7.3f}  cost {S['cost_bp']:6.3f} bp/bar   "
              f"trades {S['trades']:7,}  run {S['run']:.2f}  early {100*(S['early_share'] or 0):5.1f}%  "
              f"turn {100*S['turnover']:.2f}%/d  util {100*S['utilisation']:.1f}%  refill {100*S['same_day_refill']:.1f}%  "
              f"trade {S['trade_mean_bp']:+.2f} bp")

    print(f"\n  --- the 50-slot book, seed {SEEDS[0]} ---")
    for rule in RULES:
        show(rule, res["books"][f"{rule}_N{N_PRIMARY}_s{SEEDS[0]}"])
    print(f"\n  --- the cell-2 book, {N_CELL2} slots, seed {SEEDS[0]} ---")
    for rule in RULES:
        show(rule, res["books"][f"{rule}_C2N{N_CELL2}_s{SEEDS[0]}"])

    # ---- T1 per family, primary book, averaged over seeds with block-bootstrap SE per seed
    def t1_block(tag_fmt, n_slots, pool_label):
        out = {}
        base = {s: res["books"][tag_fmt.format(rule="FIXED", s=s)] for s in SEEDS}
        for fam in FAMILIES + ("SLTP",):
            ds = []; ses = []; dg = []
            for s in SEEDS:
                B = res["books"][tag_fmt.format(rule=fam, s=s)]
                diff = B["net_series"] - base[s]["net_series"]
                se, mean = block_boot(diff, dates[int(I["T"][0]) - base[s]["days"]:])
                ds.append(1e4 * mean); ses.append(1e4 * se); dg.append(1e4 * (B["gross_series"] - base[s]["gross_series"]).mean())
            out[fam] = dict(net_delta_bp=float(np.mean(ds)), net_delta_se_bp=float(np.mean(ses)),
                            net_delta_t=float(np.mean(ds) / np.mean(ses)), gross_delta_bp=float(np.mean(dg)),
                            seed_spread_bp=float(np.ptp(ds)), T1=bool(np.mean(ds) / np.mean(ses) > 2.0))
        return out
    res["bar"] = t1_block("{rule}_N50_s{s}", N_PRIMARY, "pooled")
    res["secondary"] = t1_block("{rule}_C2N10_s{s}", N_CELL2, "cell2")
    print(f"\n  --- T1: family NET minus FIXED NET, bp/bar, mean over seeds, monthly block-bootstrap SE ---")
    for lab, blk in (("50-slot pooled", res["bar"]), ("cell-2 10-slot (secondary)", res["secondary"])):
        for fam, q in blk.items():
            print(f"  {lab:28s} {fam:5s} gross {q['gross_delta_bp']:+7.3f}   NET {q['net_delta_bp']:+7.3f} +-{q['net_delta_se_bp']:.3f} "
                  f"({q['net_delta_t']:+5.1f} SE)   seed spread {q['seed_spread_bp']:.3f}   T1 {q['T1']}")
    print(f"\n  --- the replacement premium, 50-slot book seed {SEEDS[0]}, per family ---")
    for fam in FAMILIES + ("SLTP",):
        pr = res["books"][f"{fam}_N50_s{SEEDS[0]}"]["premium"]
        for k in ("avail", "idle"):
            q = pr.get(k, {})
            if "premium_bp" in q:
                print(f"  {fam:5s} {k:5s} n {q['n']:6,}   premium {q['premium_bp']:+8.2f} +-{q['se_bp']:.2f} bp   "
                      f"arriving {q['arriving_bp']:+8.2f}   forfeited {q['forfeited_bp']:+8.2f}")
            else:
                print(f"  {fam:5s} {k:5s} n {q.get('n', 0):6,}")
    # ---- run distributions for the controls
    res["run_dist"] = {fam: res["books"][f"{fam}_N50_s{SEEDS[0]}"]["run_dist"].tolist() for fam in FAMILIES}
    res["run_dist_c2"] = {fam: res["books"][f"{fam}_C2N10_s{SEEDS[0]}"]["run_dist"].tolist() for fam in FAMILIES}
    # P4: one slot-month is the trade ledger of the FIXED book restricted to a month
    R = simulate(I, "TP", N_PRIMARY, SEEDS[0])
    sy = I["symbols"]; dt = I["dates"]
    print(f"\n  P4  TP book, first twelve trades of the ledger:")
    for k, pnl, age, early, d, fill in R["trades"][:12]:
        print(f"      {sy[I['i'][k]]:6s} touch {dt[I['t'][k]]} side {I['side'][k]:+d}  exit {dt[d]} age {age}  "
              f"{'TARGET' if early else 'time'}  {1e4*pnl:+7.0f} bp")
    per_ctrl = per_book * 0.7
    proj = N_DRAW * len(FAMILIES) * 2 * per_ctrl
    print(f"\n  controls projected: {N_DRAW} draws x {len(FAMILIES)} families x 2 books at ~{per_ctrl:.2f}s = "
          f"{proj/60:.1f} min serial; run --controls with --workers to stride over draws")
    for k, S in res["books"].items():
        S.pop("gross_series"); S.pop("net_series"); S.pop("run_dist")
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")


def _ctrl_worker(args):
    fam, n_slots, pool_is_c2, draws, run_dist = args
    I = build_inputs()
    pool = I["c2"] if pool_is_c2 else None
    rd = np.array(run_dist)
    out = []
    for dr in draws:
        rng = np.random.default_rng(100000 + dr)
        targets = rng.choice(rd, size=len(I["t"]))
        R = simulate(I, fam, n_slots, SEEDS[0], pool_mask=pool, run_targets=targets)
        S = score(I, R, n_slots)
        assert S["recon_rel"] < 1e-9, "[RECON] control"
        out.append((dr, S["net_bp"], S["gross_bp"], S["run"], S["turnover"]))
    return fam, n_slots, pool_is_c2, out


def controls(workers):
    t0 = time.time()
    res = json.loads(OUT.read_text(encoding="utf-8"))
    jobs = []
    for fam in FAMILIES:
        for n_slots, pool_is_c2, rd in ((N_PRIMARY, False, res["run_dist"][fam]), (N_CELL2, True, res["run_dist_c2"][fam])):
            for w in range(workers):
                jobs.append((fam, n_slots, pool_is_c2, list(range(w, N_DRAW, workers)), rd))
    print(f"D419 controls: {len(jobs)} jobs over {workers} workers, {N_DRAW} draws per (family, book)")
    # prove chunk == whole: draw 0 in-process must equal draw 0 from a worker
    I = build_inputs()
    fam0 = FAMILIES[0]; rd0 = np.array(res["run_dist"][fam0])
    rng = np.random.default_rng(100000); tg = rng.choice(rd0, size=len(I["t"]))
    S_in = score(I, simulate(I, fam0, N_PRIMARY, SEEDS[0], run_targets=tg), N_PRIMARY)
    with mp.Pool(workers) as pool:
        results = pool.map(_ctrl_worker, jobs)
    got = [o for f, n, p, o in results if f == fam0 and n == N_PRIMARY and not p for o in o if o[0] == 0][0]
    assert abs(got[1] - S_in["net_bp"]) < 1e-12, f"[CHUNK] worker draw 0 {got[1]} != in-process {S_in['net_bp']}"
    print(f"  [CHUNK] worker draw 0 == in-process draw 0 to 1e-12")
    agg = {}
    for fam, n_slots, pool_is_c2, out in results:
        key = f"{fam}_{'C2N10' if pool_is_c2 else 'N50'}"
        agg.setdefault(key, []).extend(out)
    ctrl = {}
    for key, out in agg.items():
        out.sort(); net = np.array([o[1] for o in out]); gross = np.array([o[2] for o in out])
        run = np.array([o[3] for o in out]); turn = np.array([o[4] for o in out])
        fam = key.split("_")[0]; bk = "N50_s419" if key.endswith("N50") else "C2N10_s419"
        obs = res["books"][f"{fam}_{bk}"]
        p95 = float(np.quantile(net, .95)); se = float(net.std(ddof=1) / np.sqrt(net.size))
        edge = obs["net_bp"] - p95
        ctrl[key] = dict(n=int(net.size), net_p5=float(np.quantile(net, .05)), net_p50=float(np.median(net)),
                         net_p95=p95, net_se_p95=se, observed_net=obs["net_bp"],
                         gross_p95=float(np.quantile(gross, .95)), observed_gross=obs["gross_bp"],
                         ctrl_run=float(run.mean()), observed_run=obs["run"],
                         ctrl_turnover=float(turn.mean()), observed_turnover=obs["turnover"],
                         beats=bool(edge > 0), margin_se=float(edge / se) if se > 0 else float("inf"),
                         unresolved=bool(abs(edge) < 2 * se), T2=bool(edge > 0 and abs(edge) >= 2 * se))
        q = ctrl[key]
        print(f"  {key:10s} observed net {q['observed_net']:+7.3f}   ctrl p5 {q['net_p5']:+7.3f}  p50 {q['net_p50']:+7.3f}  "
              f"p95 {q['net_p95']:+7.3f} (+-{se:.3f})   margin {q['margin_se']:+5.1f} SE   T2 {q['T2']}"
              f"{'  UNRESOLVED' if q['unresolved'] else ''}   [run {q['observed_run']:.2f} vs ctrl {q['ctrl_run']:.2f}]")
        assert abs(q["ctrl_run"] - q["observed_run"]) < 0.15, f"[NUISANCE] {key}: control run {q['ctrl_run']:.2f} != rule run {q['observed_run']:.2f}"
    OUT_CTRL.write_text(json.dumps(ctrl, indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT_CTRL.relative_to(REPO)}  in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--books", action="store_true")
    ap.add_argument("--controls", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.books:
        books()
    elif a.controls:
        controls(a.workers)
    else:
        ap.error("pass --books or --controls")
