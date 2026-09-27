"""D636 §8: POWER for Stages R1-R3, before their runners exist. Reads moves on PLACEBO dates only:
  R1: January BD12-BD16 (each day k carries hedge day k's Q); R2: the same holds entered at the BD16 settlement;
  R3: 1 November -> 1 December (BD1 to BD1), in the direction of the 1 December forecast.
Nothing is read on January BD5-BD9, after BD9, or over December -> det.

Declared for POWER only (not the runners): kappa is assumed (C0 has not run): the combined form with GSCI's assets
equal to BCOM's (kappa_C = kappa), on the grid 0.02 / 0.05 / 0.10; the SNR gate is taken as passed; B's legs each use
their own t0; R3's forecast is BCOM-only.

Per stage x construction x kappa: the traded count, the within-year correlation rho of the placebo statistic,
n_eff = n / (1 + (m - 1) rho), the year-clustered SE, the MDE (2.8 SE), and by a year-block bootstrap of the centred
placebo noise (4,000 draws, seed 636): the power at the plausible effect (R1: realised = 0.5 |I|; R2: 0.25 |I_total|;
R3: 0) and the size (effect 0), each against t_(9 df) at the stage's Holm-first level (R1, R3: alpha/2; R2: alpha/6)
AND mean >= cost; plus R1's yearly sign-test power (>= 9 of 10).

    uv run python -W error::RuntimeWarning scripts/power_r_stages.py    # -> data/index_reweight/power_r.json
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "index_reweight" / "power_r.json"
KAPPAS = (0.02, 0.05, 0.10)
DRAWS, SEED = 4000, 636
ALPHA = 0.05


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


RD = _load("r_design", "r_design.py")
G = RD.G


def icc(x: np.ndarray, g: np.ndarray) -> float:
    """One-way ANOVA intraclass correlation of x within groups g."""
    df = pd.DataFrame({"x": x, "g": g})
    k = df.groupby("g").size()
    n, a = len(df), len(k)
    if a < 2 or n <= a:
        return float("nan")
    m0 = (n - (k ** 2).sum() / n) / (a - 1)
    ms_b = (k * (df.groupby("g")["x"].mean() - df["x"].mean()) ** 2).sum() / (a - 1)
    ms_w = ((df["x"] - df.groupby("g")["x"].transform("mean")) ** 2).sum() / (n - a)
    return float((ms_b - ms_w) / (ms_b + (m0 - 1) * ms_w))


def cluster_t(y: np.ndarray, g: np.ndarray) -> tuple[float, float]:
    n = len(y)
    mu = float(y.mean())
    u = y - mu
    s = pd.Series(u).groupby(g).sum().to_numpy()
    G_ = len(s)
    se = math.sqrt((s ** 2).sum() * G_ / (G_ - 1)) / n
    return mu, (mu / se if se > 0 else 0.0)


def simulate(noise: np.ndarray, eff: np.ndarray, cost: np.ndarray, years: np.ndarray, tcrit: float,
             rng: np.random.Generator) -> dict[str, float]:
    """Year-block bootstrap of the centred noise; returns the power at `eff` and the size at 0."""
    x = noise - noise.mean()
    uy = np.unique(years)
    idx = {y: np.flatnonzero(years == y) for y in uy}
    out = {}
    for lab, e in (("power", eff), ("size", np.zeros_like(eff))):
        hits = 0
        for _ in range(DRAWS):
            pick = rng.choice(uy, size=len(uy), replace=True)
            ii = np.concatenate([idx[y] for y in pick])
            gg = np.concatenate([np.full(len(idx[y]), j) for j, y in enumerate(pick)])
            mu, t = cluster_t(e[ii] + x[ii], gg)
            hits += bool(t >= tcrit and mu >= cost[ii].mean())
        out[lab] = hits / DRAWS
    return out


def summarise(noise: np.ndarray, eff: np.ndarray, cost: np.ndarray, years: np.ndarray, tcrit: float,
              rng: np.random.Generator) -> dict[str, Any]:
    if len(noise) < 10 or len(np.unique(years)) < 4:
        return {"n": int(len(noise)), "note": "too few traded observations"}
    rho = icc(noise, years)
    m = len(noise) / len(np.unique(years))
    ym = pd.Series(noise).groupby(years).mean()
    se = float(ym.std(ddof=1) / math.sqrt(len(ym)))
    sim = simulate(noise, eff, cost, years, tcrit, rng)
    return {"n": int(len(noise)), "years": int(len(ym)), "rho_within_year": round(rho, 4),
            "n_eff": round(len(noise) / (1 + (m - 1) * rho), 1) if np.isfinite(rho) else None,
            "se_usd": round(se, 2), "mde_usd_2.8se": round(2.8 * se, 2), "mean_cost_usd": round(float(cost.mean()), 2),
            "plausible_effect_usd": round(float(eff.mean()), 2), "tcrit": round(tcrit, 3), **sim}


def basket(rows: pd.DataFrame, move_col: str, eff_col: str) -> pd.DataFrame:
    """B: per (year, k), long the top 3 Q/V (Q > 0), short the bottom 3 (Q < 0); inverse dollar-vol weights, the
    short book scaled to the long book's risk. Returns the day's book move, effect and cost."""
    out = []
    for (y, k), g in rows.groupby(["year", "k"]):
        g = g[g["usable"] & (g["Q"] != 0)].assign(share=lambda z: z["Q"] / z["V"])
        lo = g[g["Q"] > 0].nlargest(3, "share")
        sh = g[g["Q"] < 0].nsmallest(3, "share")
        if lo.empty or sh.empty:
            continue
        w = pd.concat([lo, sh]).assign(w=lambda z: 1.0 / (z["sigma"] * z["P"] * z["mult"]))
        w.loc[w["Q"] < 0, "w"] *= len(lo) / len(sh)
        out.append({"year": y, "k": k, "move": float((w["w"] * w[move_col]).sum()),
                    "eff": float((w["w"] * w[eff_col]).sum()), "cost": float((w["w"] * w["cost_usd"]).sum())})
    return pd.DataFrame(out)


def sign_test_power(rows: pd.DataFrame, rng: np.random.Generator) -> float:
    """R1's yearly sign test under the plausible effect: per year, Spearman across traded names of the signed flow
    share against the raw move (sign(Q) x (effect + centred placebo noise)), summed over the days; >= 9 of 10."""
    x = rows["move_usd"].to_numpy() - rows["move_usd"].mean()
    rows = rows.assign(x=x)
    passes = 0
    ys = sorted(rows["year"].unique())
    for _ in range(1000):
        pos = 0
        for y in ys:
            g = rows[rows["year"] == y]
            sh = g.groupby("comp").apply(lambda z: (z["Q"] / z["V"]).sum(), include_groups=False)
            noise = rng.permutation(g["x"].to_numpy())
            raw = (np.sign(g["Q"]) * (0.5 * g["impact_usd"] + noise)).groupby(g["comp"].to_numpy()).sum()
            if len(sh) >= 4 and stats.spearmanr(sh.loc[raw.index], raw).statistic > 0:
                pos += 1
        passes += pos >= 9
    return passes / 1000


def main() -> int:
    rng = np.random.default_rng(SEED)
    b = RD.Base()
    t_r1 = float(stats.t.ppf(1 - ALPHA / 2, 9))
    t_r2 = float(stats.t.ppf(1 - ALPHA / 6, 9))
    res: dict[str, Any] = {"declared": __doc__.split("Declared for POWER only")[1].split("Per stage")[0].strip(),
                           "draws": DRAWS, "seed": SEED, "R1": {}, "R2": {}, "R3": {}}
    for kappa in KAPPAS:
        kp = {"separable": False, "kappa_C": kappa}
        hedge = RD.r1_rows(b, kp, "hedge")
        pla = RD.r1_rows(b, kp, "placebo", with_moves=True)
        key = ["year", "comp", "k"]
        m = hedge.merge(pla[key + ["move_usd"]], on=key, how="left")
        m["traded"] = RD.gate_a(m, snr=9.9) & m["move_usd"].notna()
        a = m[m["traded"]]
        r1a = summarise(a["move_usd"].to_numpy(), 0.5 * a["impact_usd"].to_numpy(), a["cost_usd"].to_numpy(),
                        a["year"].to_numpy(), t_r1, rng)
        if a["year"].nunique() >= 4:
            r1a["sign_test_power"] = sign_test_power(a, rng)
        bk = basket(m.assign(eff=0.5 * m["impact_usd"])[m["move_usd"].notna()], "move_usd", "eff")
        r1b = summarise(bk["move"].to_numpy(), bk["eff"].to_numpy(), bk["cost"].to_numpy(), bk["year"].to_numpy(),
                        t_r1, rng) if len(bk) else {"n": 0}
        res["R1"][str(kappa)] = {"A": r1a, "B": r1b, "traded_by_comp": a.groupby("comp").size().to_dict()}
        # R2: entry at the BD16 settlement (placebo), holds 1/3/5, against the total flow
        r2: dict[str, Any] = {}
        tot = hedge.groupby(["year", "comp"]).agg(Q=("Q", "sum"), sigma=("sigma", "last"), V=("V", "last"),
                                                  P=("P", "last"), mult=("mult", "first"), cost=("cost_usd", "first"),
                                                  usable=("usable", "all")).reset_index()
        tot["I_tot"] = RD.Y_IMPACT * tot["sigma"] * np.sqrt(np.abs(tot["Q"]) / tot["V"]) * tot["P"] * tot["mult"]
        for h in (1, 3, 5):
            rows = []
            for r in tot.itertuples():
                if not r.usable or r.Q == 0 or not r.I_tot >= 3 * r.cost:
                    continue
                d16 = RD.january_days(b, r.year, 16, 16)
                if not d16:
                    continue
                i = b.bdays.index(d16[0])
                ym, _ = b.lead_sym(r.comp, r.year)
                p0, p1 = b.settle(r.comp, b.bdays[i], ym), b.settle(r.comp, b.bdays[i + h], ym)
                if p0 is None or p1 is None:
                    continue
                rows.append((r.year, -np.sign(r.Q) * (p1 - p0) * r.mult, 0.25 * r.I_tot, r.cost))
            z = pd.DataFrame(rows, columns=["year", "move", "eff", "cost"])
            r2[f"h{h}"] = summarise(z["move"].to_numpy(), z["eff"].to_numpy(), z["cost"].to_numpy(),
                                    z["year"].to_numpy(), t_r2, rng) if len(z) else {"n": 0}
        res["R2"][str(kappa)] = r2
        # R3: 1 Nov -> 1 Dec placebo, in the direction of the 1 Dec BCOM-only forecast
        rows3 = []
        for y in RD.YEARS:
            nov = [d for d in b.bdays if d[:7] == f"{y - 1}-11"]
            dec = [d for d in b.bdays if d[:7] == f"{y - 1}-12"]
            if not nov or not dec:
                continue
            e, x, dec1 = nov[0], dec[0], dec[0]
            prev = b.bdays[b.bdays.index(dec1) - 1]
            w = G.weights(b.cim[y - 1], b.H, prev)
            for comp in RD.UNIVERSE:
                row = G.lead_table()[G.COMP[comp][2]]
                L, _ = G.lead_next(row, y - 1, 12)
                p = b.settle(comp, prev, L)
                sig = b.sigma(comp, L, dec1)
                _, sym = b.lead_sym(comp, y)
                v = b.vol_d(f"{G.COMP[comp][1]}{RD.LETTER[L[1] - 1]}{L[0] % 100:02d}-{sym.split('-')[1]}", dec1)
                if p is None or sig is None or v is None:
                    continue
                dn = G.AUM[y][0] * 1e9 * (b.cip[y].get(comp, 0.0) - w.get(comp, 0.0)) / (p * G.mult(comp))
                q = kappa * dn
                i_tot = RD.Y_IMPACT * sig * math.sqrt(abs(q) / v) * p * G.mult(comp)
                if i_tot < 3 * b.cost(comp):
                    continue
                ret = float(np.prod([b.R[comp][d] or 1.0 for d in b.bdays if e < d <= x])) - 1
                rows3.append((y, np.sign(q) * ret * p * G.mult(comp), 0.0, b.cost(comp)))
        z3 = pd.DataFrame(rows3, columns=["year", "move", "eff", "cost"])
        res["R3"][str(kappa)] = summarise(z3["move"].to_numpy(), z3["eff"].to_numpy(), z3["cost"].to_numpy(),
                                          z3["year"].to_numpy(), t_r1, rng) if len(z3) else {"n": 0}
        print(f"kappa {kappa}: R1 A {res['R1'][str(kappa)]['A'].get('power')} (n {r1a.get('n')}), "
              f"R1 B {r1b.get('power')}, R2 {[r2[k].get('power') for k in r2]}, R3 size "
              f"{res['R3'][str(kappa)].get('size')}", flush=True)
    OUT.write_text(json.dumps(res, indent=1, sort_keys=True, default=float) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
