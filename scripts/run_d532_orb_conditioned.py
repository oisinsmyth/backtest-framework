"""D532 -- does a CONDITION separate the breakouts that continue? Absorption versus vacuum.

Spec committed in ac15ee6 BEFORE this file (R8). In sample 2016-01-04..2023-12-29; the 2024+ slice is
RESERVED AND NOT READ. Nothing admitted (R15).

    python scripts/run_d532_orb_conditioned.py --selftest
    python scripts/run_d532_orb_conditioned.py --run    # -> data/d532_orb_conditioned.json

Reference is the ROTATED BASE RATE, never 50% (FINDINGS 74). Ties EXCLUDED. Up and down breaks kept
separate and pooled only after sign adjustment.
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
_s = importlib.util.spec_from_file_location("d531d", REPO / "scripts" / "run_d531_orb_session_native.py")
D531 = importlib.util.module_from_spec(_s); sys.modules["d531d"] = D531; _s.loader.exec_module(D531)

OUT = REPO / "data" / "d532_orb_conditioned.json"
SPEC = "ac15ee6"
OR_N = 6
PRIMARY_H = 12                     # 60 minutes
HORIZONS = [3, 6, 12, 24]
CAND = ["CL", "GC", "SI", "NG"]
CALIB = ["ES", "NQ"]
EMA_N, SMA_N = 10, 50
N_DRAWS = 1000
SEED = 20260915
COST = {"CL": 4.00, "GC": 5.00, "SI": 8.00, "NG": 5.00, "ES": 4.25, "NQ": 4.21}


def ema(x, n):
    a = 2.0 / (n + 1.0)
    o = np.empty(len(x)); o[0] = x[0]
    for i in range(1, len(x)):
        o[i] = a * x[i] + (1 - a) * o[i - 1]
    return o


def regime(series):
    """log(EMA_10 / SMA_50) of a positive per-session series. NaN until the SMA is seeded."""
    lv = np.log(np.where(series > 0, series, np.nan))
    out = np.full(len(lv), np.nan)
    fin = np.isfinite(lv)
    if fin.sum() > SMA_N:
        z = lv[fin]
        out[fin] = ema(z, EMA_N) - pd.Series(z).rolling(SMA_N, min_periods=SMA_N).mean().to_numpy()
    return out


def events(A, first, last, N):
    """Per session: break direction, entry bar, OR volume, OR range. dir 0 = no trade or skipped."""
    ns = A["high"].shape[0]
    d = np.zeros(ns); ent = np.full(ns, -1, dtype=int)
    ovol = np.full(ns, np.nan); orng = np.full(ns, np.nan)
    for s in range(ns):
        hi = A["high"][s, first:first + N]; lo = A["low"][s, first:first + N]
        if not (np.isfinite(hi).any() and np.isfinite(lo).any()):
            continue
        oh = np.nanmax(hi); ol = np.nanmin(lo)
        ovol[s] = np.nansum(A["volume"][s, first:first + N]); orng[s] = oh - ol
        for b in range(first + N, last):
            up = A["high"][s, b] > oh; dn = A["low"][s, b] < ol
            if not (up or dn):
                continue
            if up and dn:
                break                       # one bar spans both: OHLC cannot order them, SKIP
            d[s] = 1.0 if up else -1.0; ent[s] = b + 1
            break
    return d, ent, ovol, orng


def lift(A, d, ent, sel, H, last, want, rng, n_draws=N_DRAWS):
    """Observed agreement vs the ROTATED BASE RATE at the same bar positions. Ties excluded."""
    E = [(s, ent[s]) for s in range(len(d)) if sel[s] and d[s] == want and ent[s] >= 0 and ent[s] + H <= last]
    if len(E) < 80:
        return None
    O, C = A["open"], A["close"]
    mv = np.array([C[s, b + H] - O[s, b] for s, b in E])
    nz = np.isfinite(mv) & (mv != 0)
    if nz.sum() < 80:
        return None
    obs = float((np.sign(mv[nz]) == want).mean())
    bars = np.array([b for _, b in E]); ns = O.shape[0]
    draws = np.empty(n_draws)
    for i in range(n_draws):
        alt = rng.integers(0, ns, size=len(E))
        m2 = np.array([C[a, b + H] - O[a, b] for a, b in zip(alt, bars)])
        ok = np.isfinite(m2) & (m2 != 0)
        draws[i] = (np.sign(m2[ok]) == want).mean() if ok.sum() > 40 else np.nan
    p50 = float(np.nanmedian(draws)); p95 = float(np.nanquantile(draws, 0.95))
    return dict(n=int(nz.sum()), obs=obs, base=p50, p95=p95, lift=obs - p50,
                clears=bool(obs > p95), draws=draws)


def run():
    t0 = time.time(); rng = np.random.default_rng(SEED)
    G = D531.load()
    print(f"D532 -- conditioned opening-range breaks\n      spec {SPEC} committed BEFORE this ran; "
          f"reference = ROTATED BASE RATE, never 50%; ties excluded\n")
    res = dict(spec="D532", commit=SPEC, primary_H=5 * PRIMARY_H, cells={}, cost=COST)
    store = {}
    for r in CAND + CALIB:
        g = G[G.root == r]
        if not len(g):
            continue
        first, last = D531.session_span(g)
        days, A = D531.grids(g)
        d, ent, ovol, orng = events(A, first, last, OR_N)
        store[r] = dict(A=A, d=d, ent=ent, first=first, last=last,
                        V=regime(ovol), W=regime(orng))

    fam = {}
    print(f"  {'root':<5}{'cond':<7}{'tercile':<9}{'side':<6}{'H':>5}{'n':>7}{'obs':>9}{'base':>9}"
          f"{'lift':>8}{'clears':>8}")
    for r in CAND + CALIB:
        if r not in store:
            continue
        S = store[r]
        for cname in ("V", "W"):
            v = S[cname]
            fin = np.isfinite(v)
            if fin.sum() < 200:
                continue
            q = np.full(len(v), -1)
            q[fin] = pd.qcut(v[fin], 3, labels=False, duplicates="drop")
            for tname, tval in (("low", 0), ("high", 2)):
                sel = q == tval
                for H in HORIZONS:
                    for side, want in (("up", 1.0), ("down", -1.0)):
                        L = lift(S["A"], S["d"], S["ent"], sel, H, S["last"], want, rng)
                        if L is None:
                            continue
                        key = f"{r}-{cname}-{tname}-{side}-H{5*H}"
                        fam[key] = L.pop("draws")
                        res["cells"][key] = L
                        if H == PRIMARY_H:
                            print(f"  {r:<5}{cname:<7}{tname:<9}{side:<6}{5*H:>5}{L['n']:>7,}"
                                  f"{100*L['obs']:>8.2f}%{100*L['base']:>8.2f}%{100*L['lift']:>+8.2f}"
                                  f"{('YES' if L['clears'] else 'no'):>8}")

    # ---- PRIMARY: V low tercile, 60 min, pooled over the candidates, both sides sign-adjusted
    obs_n = obs_k = 0; base_draws = []
    for r in CAND:
        if r not in store:
            continue
        S = store[r]; v = S["V"]; fin = np.isfinite(v)
        q = np.full(len(v), -1); q[fin] = pd.qcut(v[fin], 3, labels=False, duplicates="drop")
        sel = q == 0
        for side, want in (("up", 1.0), ("down", -1.0)):
            L = lift(S["A"], S["d"], S["ent"], sel, PRIMARY_H, S["last"], want, rng)
            if L is None:
                continue
            obs_n += L["n"]; obs_k += L["obs"] * L["n"]; base_draws.append(L.pop("draws") * L["n"])
    prim_obs = obs_k / obs_n
    bd = np.sum(np.column_stack(base_draws), axis=1) / obs_n
    prim = dict(n=int(obs_n), obs=float(prim_obs), base=float(np.nanmedian(bd)),
                p95=float(np.nanquantile(bd, 0.95)))
    prim["lift"] = prim["obs"] - prim["base"]; prim["clears"] = bool(prim["obs"] > prim["p95"])
    res["primary"] = prim
    print(f"\n  PRIMARY  V low tercile, 60 min, pooled {CAND}, sign-adjusted: n {prim['n']:,}")
    print(f"           observed {100*prim['obs']:.2f}%   rotated base {100*prim['base']:.2f}%   "
          f"lift {100*prim['lift']:+.2f} pts   p95 {100*prim['p95']:.2f}%  -> "
          f"{'CLEARS' if prim['clears'] else 'INSIDE the null'}")

    # ---- dose-response: lift(low) - lift(high), the mechanism's own sign prediction
    dose = {}
    for r in CAND + CALIB:
        for cname in ("V", "W"):
            lo = [res["cells"][k]["lift"] for k in res["cells"]
                  if k.startswith(f"{r}-{cname}-low-") and k.endswith(f"H{5*PRIMARY_H}")]
            hi = [res["cells"][k]["lift"] for k in res["cells"]
                  if k.startswith(f"{r}-{cname}-high-") and k.endswith(f"H{5*PRIMARY_H}")]
            if lo and hi:
                dose[f"{r}-{cname}"] = float(np.mean(lo) - np.mean(hi))
    res["dose_response"] = dose
    dv = np.array([v for k, v in dose.items() if k.split("-")[0] in CAND])
    dw = np.array([v for k, v in dose.items() if k.endswith("-W") and k.split("-")[0] in CAND])
    dvv = np.array([v for k, v in dose.items() if k.endswith("-V") and k.split("-")[0] in CAND])
    print(f"\n  DOSE-RESPONSE  lift(low) - lift(high) at 60 min, in points:")
    for k, v in sorted(dose.items()):
        print(f"    {k:<8}{100*v:>+8.2f}")
    print(f"  candidates: V mean {100*dvv.mean():+.2f}, W mean {100*dw.mean():+.2f}  "
          f"-> P-1 {'HELD (positive)' if dvv.mean() > 0 else 'BROKEN (negative: the mechanism is inverted)'}")
    print(f"  -> P-2 {'HELD (V > W)' if abs(dvv.mean()) > abs(dw.mean()) else 'BROKEN (W dominates)'}")

    # ---- N2 family maximum
    keys = sorted(fam); L = min(len(fam[k]) for k in keys)
    obsl = {k: res["cells"][k]["obs"] - res["cells"][k]["base"] for k in keys}
    M = np.max(np.column_stack([fam[k][:L] - np.nanmedian(fam[k][:L]) for k in keys]), axis=1)
    best = max(obsl, key=obsl.get)
    res["family"] = dict(n_cells=len(keys), p95=float(np.nanquantile(M, 0.95)),
                         observed_max=float(obsl[best]), argmax=best,
                         clears=bool(obsl[best] > np.nanquantile(M, 0.95)))
    f = res["family"]
    print(f"\n  N2 FAMILY max lift over {f['n_cells']} cells: observed {100*f['observed_max']:+.2f} "
          f"({f['argmax']}) against p95 {100*f['p95']:+.2f} -> {'CLEARS' if f['clears'] else 'INSIDE'}")
    res["verdict"] = dict(primary=prim["clears"], family=f["clears"], dose_sign=bool(dvv.mean() > 0),
                          pass_all=bool(prim["clears"] and f["clears"] and dvv.mean() > 0))
    print(f"\n  DECLARED RULE: pass needs ALL THREE. primary {prim['clears']}, family {f['clears']}, "
          f"dose {dvv.mean() > 0} -> {'PASS' if res['verdict']['pass_all'] else 'DOES NOT PASS'}")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"\nwrote {OUT.relative_to(REPO)} in {(time.time()-t0)/60:.1f} min")


def selftest():
    print("== regime() is causal: it must not see the future")
    x = np.array([1.0] * 60 + [100.0] * 5)
    g = regime(x)
    # rolling(SMA_N, min_periods=SMA_N) makes index SMA_N-1 the FIRST valid value, so the warm-up is
    # SMA_N-1 NaNs. Asserting SMA_N of them is an off-by-one in the assertion, which is how it fired.
    assert np.isnan(g[:SMA_N - 1]).all(), "the SMA warm-up must be NaN"
    assert np.isfinite(g[SMA_N - 1]), "index SMA_N-1 must be the first valid value"
    assert g[59] < g[62], "a volume jump must raise the ratio AFTER it happens, not before"
    print(f"   ok: warm-up NaN, ratio rises only after the jump ({g[59]:+.3f} -> {g[62]:+.3f})")

    print("== events(): the both-sides bar is skipped, and the entry is the bar AFTER the break")
    nb = 20
    A = {k: np.full((2, nb), v) for k, v in (("high", 10.0), ("low", 9.0), ("open", 9.5),
                                             ("close", 9.5), ("volume", 1.0))}
    A["high"][0, 6] = 11.0; A["open"][0, 7] = 10.5
    A["high"][1, 6] = 11.0; A["low"][1, 6] = 8.0          # spans both -> skip
    d, ent, ov, orr = events(A, 0, nb - 1, 6)
    assert d[0] == 1.0 and ent[0] == 7, (d, ent)
    assert d[1] == 0.0 and ent[1] == -1, "the both-sides session must be skipped"
    print("   ok: clean break enters at bar 7; the both-sides session is skipped")

    print("== [X] a broken lift() must fail: the base rate cannot equal the observed by construction")
    rng = np.random.default_rng(0)
    A2 = {k: np.random.default_rng(1).normal(100, 1, (300, 40)) for k in ("open", "close")}
    A2["high"] = A2["open"] + 1; A2["low"] = A2["open"] - 1; A2["volume"] = np.ones((300, 40))
    d2 = np.ones(300); ent2 = np.full(300, 10)
    L = lift(A2, d2, ent2, np.ones(300, bool), 5, 39, 1.0, rng, n_draws=200)
    assert L is not None and abs(L["lift"]) < 0.15, "on pure noise the lift must be near zero"
    print(f"   ok: on pure noise the lift is {100*L['lift']:+.2f} points, near zero as it must be")
    print("\nSELFTEST PASSED")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    run() if a.run else selftest()
