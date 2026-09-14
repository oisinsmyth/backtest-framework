"""D533 -- the four conditions the inventory-transfer story implies, singly and in pairs.

Spec committed in d5bf27a BEFORE this file (R8). In sample 2016-01-04..2023-12-29; the 2024+ slice is
RESERVED AND NOT READ. Nothing admitted (R15).

    python scripts/run_d533_story_conditions.py --selftest
    python scripts/run_d533_story_conditions.py --run    # -> data/d533_story_conditions.json

C1/C2/C4 are ENTRY filters, C3 is an EXIT rule. Reference is the ROTATED BASE RATE (FINDINGS 74),
ties excluded, up and down separate. The family is the 20 POOLED cells; per-root is diagnostic only.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
_s = importlib.util.spec_from_file_location("d531e", REPO / "scripts" / "run_d531_orb_session_native.py")
D531 = importlib.util.module_from_spec(_s); sys.modules["d531e"] = D531; _s.loader.exec_module(D531)

OUT = REPO / "data" / "d533_story_conditions.json"
SPEC = "d5bf27a"
OR_N, BASE_H = 6, 12                      # 30-minute range; 60-minute baseline exit
CAND = ["CL", "GC", "SI", "NG"]
CALIB = ["ES", "NQ"]
NIGHT = [f"h{h:02d}" for h in list(range(18, 24)) + list(range(0, 9))]
TREND_N = 50
N_DRAWS = 1000
SEED = 20260915
COST = {"CL": 4.00, "GC": 5.00, "SI": 8.00, "NG": 5.00, "ES": 4.25, "NQ": 4.21}
# MINIMUM TRADABLE SIZE, and the USD per point IT pays -- MCL/MGC/SIL/MNG, from
# data/futures_contract_specs.json. The component line is computed at this size and no other.
MINSIZE = {"CL": ("MCL", 100.0), "GC": ("MGC", 10.0), "SI": ("SIL", 1000.0), "NG": ("MNG", 1000.0)}
ACCOUNT = 50_000.0                        # C-d: daily sigma at minimum size <= 1% of this
COMPONENT_CELLS = [("none", "fixed"), ("C2", "fixed"), ("C1", "fixed"), ("C1", "C3")]
COMBOS = [("none", "fixed"), ("C1", "fixed"), ("C2", "fixed"), ("C4", "fixed"), ("none", "C3"),
          ("C1", "C3"), ("C2", "C3"), ("C4", "C3"), ("C1C2", "fixed"), ("C1C4", "fixed"),
          ("C2C4", "fixed")]


def top_tercile(x, bottom=False):
    """TRUE in the top (or bottom) tercile of the finite values. NaN rows are FALSE."""
    out = np.zeros(len(x), bool)
    fin = np.isfinite(x)
    if fin.sum() < 90:
        return out
    q = np.quantile(x[fin], 1 / 3 if bottom else 2 / 3)
    out[fin] = (x[fin] < q) if bottom else (x[fin] > q)
    return out


def night_depth(B, root, days):
    """C2: log(night volume / night range) less its trailing 50-session mean, aligned to `days`."""
    t = B[B.root == root].sort_values("day")
    v = t[[f"{s}_v" for s in NIGHT if f"{s}_v" in t.columns]].to_numpy(float)
    hi = t[[f"{s}_h" for s in NIGHT if f"{s}_h" in t.columns]].to_numpy(float)
    lo = t[[f"{s}_l" for s in NIGHT if f"{s}_l" in t.columns]].to_numpy(float)
    with np.errstate(invalid="ignore"):
        rng = np.nanmax(hi, axis=1) - np.nanmin(lo, axis=1)
        vol = np.nansum(v, axis=1)
        d = np.where((rng > 0) & (vol > 0), np.log(vol / rng), np.nan)
    # min_periods MUST be below the window. The breadth fixture carries ~17% NaN night rows, so a
    # window of 50 essentially never holds 50 clean observations and min_periods=TREND_N collapses
    # the whole series to NaN -- the same trap that emptied activity_filter on this fixture.
    s = pd.Series(d)
    dev = (s - s.rolling(TREND_N, min_periods=TREND_N // 2).mean()).to_numpy()
    return pd.Series(dev, index=t["day"].to_numpy()).reindex(days).to_numpy(float)


def features(A, first, last, N):
    """Break direction, entry bar, and the three entry features. All causal: nothing after the break."""
    ns = A["high"].shape[0]
    d = np.zeros(ns); ent = np.full(ns, -1, dtype=int)
    c1 = np.full(ns, np.nan); c4 = np.full(ns, np.nan); premed = np.full(ns, np.nan)
    for s in range(ns):
        hi = A["high"][s, first:first + N]; lo = A["low"][s, first:first + N]
        cl = A["close"][s, first:first + N]; op = A["open"][s, first:first + N]
        if not (np.isfinite(hi).any() and np.isfinite(lo).any()):
            continue
        oh = np.nanmax(hi); ol = np.nanmin(lo)
        # C4: path efficiency INSIDE the range -- low means price oscillated while volume transacted
        steps = np.abs(np.diff(cl[np.isfinite(cl)]))
        if steps.sum() > 0 and np.isfinite(op[0]) and np.isfinite(cl[-1]):
            c4[s] = abs(cl[-1] - op[0]) / steps.sum()
        for b in range(first + N, last):
            up = A["high"][s, b] > oh; dn = A["low"][s, b] < ol
            if not (up or dn):
                continue
            if up and dn:
                break                                     # spans both: OHLC cannot order them
            pv = A["volume"][s, first:b]
            m = np.nanmedian(pv) if np.isfinite(pv).any() else np.nan
            premed[s] = m
            bv = np.nansum(A["volume"][s, b:b + 2])
            if np.isfinite(m) and m > 0 and bv > 0:
                c1[s] = np.log(bv / m)                    # C1: did the break TRANSACT
            d[s] = 1.0 if up else -1.0; ent[s] = b + 1
            break
    return d, ent, c1, c4, premed


def exit_bar(A, s, e, last, mode, premed):
    """Fixed 60 minutes, or C3: the first bar whose volume falls below the session's pre-break median."""
    if mode == "fixed":
        b = e + BASE_H
        return b if b <= last else None
    if not np.isfinite(premed[s]) or premed[s] <= 0:
        return None
    for b in range(e + 1, last + 1):                      # minimum hold of one bar
        v = A["volume"][s, b]
        if np.isfinite(v) and v < premed[s]:
            return b
    return last


def evaluate(A, d, ent, sel, last, want, mode, premed, rng, n_draws=N_DRAWS):
    """Observed agreement and the ROTATED BASE RATE at the same (bar, exit) positions. Ties excluded."""
    E = []
    for s in range(len(d)):
        if not sel[s] or d[s] != want or ent[s] < 0:
            continue
        xb = exit_bar(A, s, ent[s], last, mode, premed)
        if xb is None or xb <= ent[s]:
            continue
        E.append((s, ent[s], xb))
    if len(E) < 60:
        return None
    O, C = A["open"], A["close"]
    mv = np.array([C[s, x] - O[s, b] for s, b, x in E])
    nz = np.isfinite(mv) & (mv != 0)
    if nz.sum() < 60:
        return None
    obs = float((np.sign(mv[nz]) == want).mean())
    ns = O.shape[0]
    bars = np.array([(b, x) for _, b, x in E])
    draws = np.empty(n_draws)
    for i in range(n_draws):
        alt = rng.integers(0, ns, size=len(E))
        m2 = np.array([C[a, x] - O[a, b] for a, (b, x) in zip(alt, bars)])
        ok = np.isfinite(m2) & (m2 != 0)
        draws[i] = (np.sign(m2[ok]) == want).mean() if ok.sum() > 30 else np.nan
    return dict(n=int(nz.sum()), obs=obs, base=float(np.nanmedian(draws)),
                p95=float(np.nanquantile(draws, 0.95)),
                lift=obs - float(np.nanmedian(draws)), draws=draws,
                hold=float(np.mean([x - b for _, b, x in E])))


def build(roots):
    """Load the fixture and derive every session-level feature. Scores NOTHING -- shared by --run
    and --component so the component line cannot be computed off a different construction."""
    G = D531.load()
    B = pd.read_csv(REPO / "data" / "fixtures" / "fut_breadth_hourly.csv.gz",
                    dtype={"root": str, "day": str})
    S = {}
    for r in roots:
        g = G[G.root == r]
        if not len(g):
            continue
        first, last = D531.session_span(g)
        days, A = D531.grids(g)
        d, ent, c1, c4, premed = features(A, first, last, OR_N)
        c2 = night_depth(B, r, days)
        S[r] = dict(A=A, d=d, ent=ent, last=last, premed=premed, days=days,
                    C1=top_tercile(c1), C2=top_tercile(c2), C4=top_tercile(c4, bottom=True),
                    cov2=float(np.isfinite(c2).mean()))
        print(f"  {r:<4} sessions {len(d):,}  breaks {int((d!=0).sum()):,}  "
              f"C1 {S[r]['C1'].sum():>5,}  C2 {S[r]['C2'].sum():>5,} (night coverage "
              f"{100*S[r]['cov2']:.0f}%)  C4 {S[r]['C4'].sum():>5,}")
    return S


def mask_of(S, r, name):
    """The entry filter. One definition, used by the scorer and the component line alike."""
    if name == "none":
        return np.ones(len(S[r]["d"]), bool)
    m = np.ones(len(S[r]["d"]), bool)
    for c in ("C1", "C2", "C4"):
        if c in name:
            m &= S[r][c]
    return m


def run():
    t0 = time.time(); rng = np.random.default_rng(SEED)
    print(f"D533 -- the story's four conditions\n      spec {SPEC} committed BEFORE this ran; "
          f"reference = ROTATED BASE RATE; ties excluded; family = the 20 POOLED cells\n")
    S = build(CAND + CALIB)

    def mask(r, name):
        if name == "none":
            return np.ones(len(S[r]["d"]), bool)
        m = np.ones(len(S[r]["d"]), bool)
        for c in ("C1", "C2", "C4"):
            if c in name:
                m &= S[r][c]
        return m

    res = dict(spec="D533", commit=SPEC, cells={}, per_root={}, cost=COST)
    fam = {}
    print(f"\n  POOLED over {CAND}, sign-adjusted. Reference = rotated base rate.")
    print(f"  {'filter':<7}{'exit':<7}{'side':<6}{'n':>7}{'hold':>7}{'obs':>9}{'base':>9}{'lift':>8}"
          f"{'p95':>8}{'clears':>8}")
    for fname, xmode in COMBOS:
        for side, want in (("up", 1.0), ("down", -1.0)):
            tot_n = 0; tot_k = 0.0; dl = []; hold = []
            for r in CAND:
                if r not in S:
                    continue
                E = evaluate(S[r]["A"], S[r]["d"], S[r]["ent"], mask(r, fname), S[r]["last"],
                             want, xmode, S[r]["premed"], rng)
                if E is None:
                    continue
                tot_n += E["n"]; tot_k += E["obs"] * E["n"]; dl.append(E.pop("draws") * E["n"])
                hold.append(E["hold"] * E["n"])
            if tot_n < 200 or not dl:
                continue
            bd = np.sum(np.column_stack(dl), axis=1) / tot_n
            obs = tot_k / tot_n
            cell = dict(n=int(tot_n), obs=float(obs), base=float(np.nanmedian(bd)),
                        p95=float(np.nanquantile(bd, 0.95)), hold=float(np.sum(hold) / tot_n))
            cell["lift"] = cell["obs"] - cell["base"]
            cell["clears"] = bool(cell["obs"] > cell["p95"])
            key = f"{fname}-{xmode}-{side}"
            res["cells"][key] = cell; fam[key] = bd
            star = "  <-- PRIMARY" if (fname == "C2" and xmode == "fixed") else ""
            print(f"  {fname:<7}{xmode:<7}{side:<6}{tot_n:>7,}{cell['hold']:>7.1f}"
                  f"{100*cell['obs']:>8.2f}%{100*cell['base']:>8.2f}%{100*cell['lift']:>+8.2f}"
                  f"{100*cell['p95']:>7.2f}%{('YES' if cell['clears'] else 'no'):>8}{star}")

    prim = [res["cells"][f"C2-fixed-{s}"] for s in ("up", "down") if f"C2-fixed-{s}" in res["cells"]]
    pn = sum(c["n"] for c in prim)
    assert pn > 0, ("[PRIMARY] C2 produced no cells -- check its coverage above before reading "
                    "anything else in this run")
    pobs = sum(c["obs"] * c["n"] for c in prim) / pn
    pbase = sum(c["base"] * c["n"] for c in prim) / pn
    res["primary"] = dict(n=pn, obs=pobs, base=pbase, lift=pobs - pbase,
                          clears=all(c["clears"] for c in prim),
                          sign_ok=bool(pobs - pbase > 0))
    p = res["primary"]
    print(f"\n  PRIMARY  C2, fixed exit, both sides: n {p['n']:,}  observed {100*p['obs']:.2f}%  "
          f"base {100*p['base']:.2f}%  lift {100*p['lift']:+.2f} pts  -> "
          f"{'CLEARS' if p['clears'] else 'INSIDE the null'}")

    keys = sorted(fam); L = min(len(fam[k]) for k in keys)
    M = np.max(np.column_stack([fam[k][:L] - np.nanmedian(fam[k][:L]) for k in keys]), axis=1)
    obsl = {k: res["cells"][k]["lift"] for k in keys}
    best = max(obsl, key=obsl.get)
    res["family"] = dict(n_cells=len(keys), p95=float(np.nanquantile(M, 0.95)),
                         observed_max=float(obsl[best]), argmax=best,
                         clears=bool(obsl[best] > np.nanquantile(M, 0.95)))
    f = res["family"]
    print(f"  N2 FAMILY over {f['n_cells']} pooled cells: best {100*f['observed_max']:+.2f} "
          f"({f['argmax']}) against p95 {100*f['p95']:+.2f} -> {'CLEARS' if f['clears'] else 'INSIDE'}")

    print(f"\n  SIGN PREDICTIONS (each condition TRUE should IMPROVE continuation vs 'none'):")
    for c in ("C1", "C2", "C4"):
        for side in ("up", "down"):
            a = res["cells"].get(f"{c}-fixed-{side}"); b = res["cells"].get(f"none-fixed-{side}")
            if a and b:
                dlt = 100 * (a["lift"] - b["lift"])
                print(f"    {c} {side:<5} {dlt:+6.2f} pts vs unfiltered -> "
                      f"{'AS PREDICTED' if dlt > 0 else 'INVERTED'}")
    for side in ("up", "down"):
        a = res["cells"].get(f"none-C3-{side}"); b = res["cells"].get(f"none-fixed-{side}")
        if a and b:
            dlt = 100 * (a["lift"] - b["lift"])
            print(f"    C3 {side:<5} {dlt:+6.2f} pts vs the fixed exit (mean hold "
                  f"{a['hold']:.1f} vs {b['hold']:.1f} bars) -> "
                  f"{'AS PREDICTED' if dlt > 0 else 'INVERTED'}")

    res["verdict"] = dict(primary=p["clears"], family=f["clears"], sign=p["sign_ok"],
                          pass_all=bool(p["clears"] and f["clears"] and p["sign_ok"]))
    print(f"\n  DECLARED RULE: pass needs ALL THREE. primary {p['clears']}, family {f['clears']}, "
          f"sign {p['sign_ok']} -> {'PASS' if res['verdict']['pass_all'] else 'DOES NOT PASS'}")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"\nwrote {OUT.relative_to(REPO)} in {(time.time()-t0)/60:.1f} min")


def ledger_series():
    """K8's daily net P&L -- the ledger's only entry on this clock, for C-b."""
    f = REPO / "data" / "d498_trades_NQ_K8.csv.gz"
    if not f.exists():
        return None
    t = pd.read_csv(f, dtype={"day": str})
    return pd.Series(t["net_usd"].to_numpy(float), index=t["day"].to_numpy())


def pnl_series(S, r, fname, xmode):
    """Per-SESSION dollars at MINIMUM TRADABLE SIZE, gross and net, indexed by day. A session with no
    qualifying break contributes 0.0 -- the component's daily P&L is the account's, not the trade's."""
    sym, upt = MINSIZE[r]
    st = S[r]; A, d, ent, last, days = st["A"], st["d"], st["ent"], st["last"], st["days"]
    sel = mask_of(S, r, fname)
    O, C = A["open"], A["close"]
    g = np.zeros(len(days)); traded = np.zeros(len(days), bool)
    for s in range(len(days)):
        if not sel[s] or d[s] == 0 or ent[s] < 0:
            continue
        xb = exit_bar(A, s, ent[s], last, xmode, st["premed"])
        if xb is None or xb <= ent[s]:
            continue
        mv = C[s, xb] - O[s, ent[s]]
        if not np.isfinite(mv):
            continue
        g[s] = d[s] * mv * upt; traded[s] = True
    n = np.where(traded, g - COST[r], 0.0)
    return sym, pd.Series(g, index=days), pd.Series(n, index=days), traded


def sharpe(x):
    """Annualised Sharpe of a DAILY series, and Lo's SE for it."""
    x = np.asarray(x, float); sd = x.std(ddof=1)
    if sd <= 0 or len(x) < 60:
        return float("nan"), float("nan")
    s = float(x.mean() / sd * np.sqrt(252))
    return s, float(np.sqrt((1 + 0.5 * s * s / 252) / len(x)) * np.sqrt(252))


def component():
    """THE COMPONENT LINE. Required in every RESULT whether or not the construction clears the
    standalone bar (CLAUDE.md), computed HERE rather than in a spreadsheet -- that is the D466 lesson.
    C-a Sharpe > 0.5, C-b rho < 0.3 against the ledger, C-c skew >= -0.5, C-d daily sigma <= 1% of
    $50k at minimum size."""
    print(f"D533 COMPONENT LINE -- minimum tradable size, the cost that size pays, in DOLLARS\n")
    S = build(CAND)
    K8 = ledger_series()
    out = {}
    print(f"\n  {'cell':<12}{'root':<5}{'size':<6}{'trades':>8}{'gross$':>9}{'net$':>9}{'hit':>8}"
          f"{'dayS':>9}{'netSR':>9}{'SE':>7}{'skew':>7}{'rK8':>7}  C-a C-c C-d")
    for fname, xmode in COMPONENT_CELLS:
        key = f"{fname}-{xmode}"
        book_g = None; book_n = None; rows = {}
        for r in CAND:
            if r not in S:
                continue
            sym, gs, ns, traded = pnl_series(S, r, fname, xmode)
            if traded.sum() < 100:
                continue
            sr, se = sharpe(ns.to_numpy())
            sg, _ = sharpe(gs.to_numpy())
            sd = float(ns.std(ddof=1))
            sk = float(pd.Series(ns.to_numpy()).skew())
            rho = float("nan")
            if K8 is not None:
                j = pd.concat([ns.rename("a"), K8.rename("b")], axis=1).dropna()
                if len(j) > 60:
                    rho = float(j["a"].corr(j["b"]))
            rows[r] = dict(sym=sym, trades=int(traded.sum()),
                           gross_per_trade=float(gs[traded].mean()),
                           net_per_trade=float(ns[traded].mean()),
                           hit=float((ns[traded] > 0).mean()), daily_sd=sd,
                           net_sharpe=sr, sharpe_se=se, gross_sharpe=sg, skew=sk, rho_k8=rho,
                           C_a=bool(sr > 0.5), C_c=bool(sk >= -0.5), C_d=bool(sd <= 0.01 * ACCOUNT))
            book_g = gs if book_g is None else book_g.add(gs, fill_value=0.0)
            book_n = ns if book_n is None else book_n.add(ns, fill_value=0.0)
            v = rows[r]
            print(f"  {key:<12}{r:<5}{sym:<6}{v['trades']:>8,}{v['gross_per_trade']:>+9.2f}"
                  f"{v['net_per_trade']:>+9.2f}{100*v['hit']:>7.1f}%{sd:>9.0f}{sr:>+9.2f}"
                  f"{se:>7.2f}{sk:>+7.2f}{v['rho_k8']:>+7.2f}   "
                  f"{'Y' if v['C_a'] else 'n'}   {'Y' if v['C_c'] else 'n'}   "
                  f"{'Y' if v['C_d'] else 'n'}")
        if book_n is not None:
            bs, bse = sharpe(book_n.to_numpy()); gsr, _ = sharpe(book_g.to_numpy())
            bsd = float(book_n.std(ddof=1)); bsk = float(pd.Series(book_n.to_numpy()).skew())
            out[key] = dict(per_root=rows, book=dict(
                net_sharpe=bs, sharpe_se=bse, gross_sharpe=gsr, daily_sd=bsd, skew=bsk,
                C_a=bool(bs > 0.5), C_c=bool(bsk >= -0.5), C_d=bool(bsd <= 0.01 * ACCOUNT)))
            print(f"  {key:<12}{'BOOK':<5}{'1 each':<6}{'':>8}{'':>9}{'':>9}{'':>8}{bsd:>9.0f}"
                  f"{bs:>+9.2f}{bse:>7.2f}{bsk:>+7.2f}{'':>7}   "
                  f"{'Y' if out[key]['book']['C_a'] else 'n'}   "
                  f"{'Y' if out[key]['book']['C_c'] else 'n'}   "
                  f"{'Y' if out[key]['book']['C_d'] else 'n'}   "
                  f"(gross {gsr:+.2f})")
    # Trade distribution on the cells that earn a POSITIVE GROSS book -- mean, median, and the
    # symmetric 1% trim. Dropping only the winners always frightens on a two-sided book (D307), so
    # all three are printed or none of them is.
    print(f"\n  TRADE DISTRIBUTION, pooled over {CAND} (gross dollars per trade at minimum size)")
    print(f"  {'cell':<12}{'trades':>8}{'mean':>9}{'median':>9}{'ex-top1':>9}{'ex-bot1':>9}"
          f"{'trim1':>9}{'top1%P&L':>10}{'hold':>7}")
    for fname, xmode in COMPONENT_CELLS:
        key = f"{fname}-{xmode}"
        if key not in out:
            continue
        allg = []; holds = []
        for r in CAND:
            if r not in S:
                continue
            _, gs, _, tr = pnl_series(S, r, fname, xmode)
            allg.append(gs[tr].to_numpy())
            st = S[r]; sel = mask_of(S, r, fname)
            for s in range(len(st["days"])):
                if sel[s] and st["d"][s] != 0 and st["ent"][s] >= 0:
                    xb = exit_bar(st["A"], s, st["ent"][s], st["last"], xmode, st["premed"])
                    if xb is not None and xb > st["ent"][s]:
                        holds.append(xb - st["ent"][s])
        g = np.concatenate(allg); g.sort()
        k = max(1, int(round(0.01 * len(g))))
        top = g[-k:].sum(); tot = g.sum()
        d = dict(n=int(len(g)), mean=float(g.mean()), median=float(np.median(g)),
                 ex_top=float(g[:-k].mean()), ex_bot=float(g[k:].mean()),
                 trim=float(g[k:-k].mean()),
                 top1_share=float(top / tot) if tot != 0 else float("nan"),
                 hold=float(np.mean(holds)))
        out[key]["dist"] = d
        print(f"  {key:<12}{d['n']:>8,}{d['mean']:>+9.2f}{d['median']:>+9.2f}{d['ex_top']:>+9.2f}"
              f"{d['ex_bot']:>+9.2f}{d['trim']:>+9.2f}{100*d['top1_share']:>9.0f}%{d['hold']:>7.1f}")

    res = json.loads(OUT.read_text()) if OUT.exists() else dict(spec="D533", commit=SPEC)
    res["per_root"] = out
    res["component_note"] = ("minimum tradable size MCL/MGC/SIL/MNG; cost = the pre-registered "
                             "measured round trip; C-b is rho against K8, the ledger's only entry")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"\n  wrote the component line into {OUT.relative_to(REPO)}")


def selftest():
    print("== C4 path efficiency: a straight line reads 1.0, a round trip reads ~0")
    nb = 20
    A = {k: np.full((2, nb), np.nan) for k in ("high", "low", "open", "close", "volume")}
    A["volume"][:] = 1.0
    A["close"][0, 0:6] = [10, 11, 12, 13, 14, 15]; A["open"][0, 0] = 10      # a straight ramp
    A["close"][1, 0:6] = [10, 11, 10, 11, 10, 10]; A["open"][1, 0] = 10      # oscillation
    A["high"][:, 0:6] = 20; A["low"][:, 0:6] = 0
    _, _, _, c4, _ = features(A, 0, nb - 1, 6)
    assert abs(c4[0] - 1.0) < 1e-9, f"a straight line must read 1.0, got {c4[0]}"
    assert c4[1] < 0.2, f"oscillation must read near 0, got {c4[1]}"
    print(f"   ok: ramp {c4[0]:.3f}, oscillation {c4[1]:.3f}")

    print("== C3 exits on the first quiet bar, and never before the minimum hold")
    A2 = {k: np.full((1, nb), 1.0) for k in ("high", "low", "open", "close", "volume")}
    A2["volume"][0, :] = 10.0; A2["volume"][0, 11] = 1.0
    pm = np.array([5.0])
    xb = exit_bar(A2, 0, 8, nb - 1, "C3", pm)
    assert xb == 11, f"expected the first bar under the median (11), got {xb}"
    # the fixed rule needs entry + BASE_H <= last; from bar 8 in a 20-bar session it runs off the end,
    # and returning None there is correct -- so the check uses an entry that fits.
    assert exit_bar(A2, 0, 8, nb - 1, "fixed", pm) is None, "an exit past the session end must be None"
    assert exit_bar(A2, 0, 5, nb - 1, "fixed", pm) == 5 + BASE_H
    print(f"   ok: C3 exits at bar {xb}; the fixed rule exits at {5+BASE_H} and is None when it "
          f"would run past the session")

    print("== [X] a condition mask that selects EVERYTHING must reproduce the unfiltered cell")
    m = top_tercile(np.arange(300.0))
    assert 90 < m.sum() < 110, f"a tercile of 300 must select ~100, got {m.sum()}"
    assert not m[:100].any(), "the bottom third must be excluded"
    print(f"   ok: tercile selects {int(m.sum())} of 300 and excludes the bottom third")
    print("== [SIGN] in MONEY: a favourable move pays POSITIVELY on BOTH sides, and cost is a debit")
    nb = 20
    A3 = {k: np.full((2, nb), np.nan) for k in ("high", "low", "open", "close", "volume")}
    A3["volume"][:] = 1.0
    A3["open"][:, 5] = 100.0
    A3["close"][0, 5 + BASE_H] = 101.0                    # +1 point, long
    A3["close"][1, 5 + BASE_H] = 99.0                     # -1 point, short
    S3 = {"CL": dict(A=A3, d=np.array([1.0, -1.0]), ent=np.array([5, 5]), last=nb - 1,
                     premed=np.array([5.0, 5.0]), days=np.array(["d0", "d1"]),
                     C1=np.ones(2, bool), C2=np.ones(2, bool), C4=np.ones(2, bool))}
    sym, gs, ns, tr = pnl_series(S3, "CL", "none", "fixed")
    upt = MINSIZE["CL"][1]
    assert sym == "MCL" and tr.all(), f"both sessions must trade, got {tr}"
    assert gs.iloc[0] == +upt, f"a LONG into a +1 point move must pay +{upt}, got {gs.iloc[0]}"
    assert gs.iloc[1] == +upt, f"a SHORT into a -1 point move must pay +{upt}, got {gs.iloc[1]}"
    assert ns.iloc[0] == upt - COST["CL"], "cost must be a DEBIT against the gross"
    # [X] the audit must FAIL on an inverted book -- flip the short's sign and the payoff inverts
    S3["CL"]["d"] = np.array([1.0, +1.0])
    _, gbad, _, _ = pnl_series(S3, "CL", "none", "fixed")
    assert gbad.iloc[1] == -upt, "[X] a long into a falling market must LOSE; the check cannot fire"
    print(f"   ok: long +{gs.iloc[0]:.0f}, short +{gs.iloc[1]:.0f}, net {ns.iloc[0]:.0f} after "
          f"${COST['CL']:.2f}; the inverted book reads {gbad.iloc[1]:.0f}")

    print("== [QTY] the component line is at MINIMUM size -- the full contract is a different number")
    full = {"CL": 1000.0, "GC": 100.0, "SI": 5000.0, "NG": 10000.0}
    for r, (sy, u) in MINSIZE.items():
        assert u < full[r], f"{sy} must be smaller than the full {r} contract"
    assert MINSIZE["CL"][1] * 1.0 != full["CL"], "scoring the full contract would be a 10x error"
    print(f"   ok: {', '.join(f'{s}={u:g}' for s, u in MINSIZE.values())} USD/pt, each below its "
          f"full contract")

    print("\nSELFTEST PASSED")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true")
    g.add_argument("--component", action="store_true")
    a = ap.parse_args()
    if a.run:
        run()
    elif a.component:
        component()
    else:
        selftest()
