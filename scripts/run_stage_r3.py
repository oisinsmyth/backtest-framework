"""D636 Stage R3: is the January rebalance flow priced in beforehand (pre-positioning)?

Spec: docs/decisions/D636-PRE-REG-stages-r1-r2-r3-the-january-rebalance-trades.md s.6 (1315ecf; s.11 notes), after
D636's POWER (7ec7a21): R3's MDE is about $1,870 a contract; an R3 miss excludes only effects above it.

    uv run python -W error::RuntimeWarning scripts/run_stage_r3.py --selftest   # reads the Nov placebo window only
    uv run python -W error::RuntimeWarning scripts/run_stage_r3.py --run        # refuses a second run; needs gate_c0.json
    uv run python -W error::RuntimeWarning scripts/run_stage_r3.py --check

(b) Trading: enter at the settlement of December's first business day (y-1), in the direction of the forecast total
flow (weights and settlements to the prior business day; the year-y BCOM targets and GSCI CPWs, both announced by
then); exit at the settlement of det(y). The move is the BCOM sub-index return times the entry price times mult.
A: forecast |I_total| >= 3 x cost and SNR >= 1.5. B: the s.3 basket on the forecast share. H-R3(b): mean >= cost and
the Holm (A, B) wild-bootstrap p < 0.05. Adoption: H-R3(b) AND the yearly sign test. The label shuffle can kill it.
(a) Descriptive: residual sub-index returns (minus the equal-weighted mean of the 12) over announcement -> 1 Dec,
1 Dec -> 31 Dec and 1 Jan -> det, Spearman-correlated across commodities with the forecast share at each start.
"""
from __future__ import annotations

import argparse
import hashlib
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
IR = REPO / "data" / "index_reweight"
OUT = IR / "stage_r3.json"
SPEC = REPO / "docs" / "decisions" / "D636-PRE-REG-stages-r1-r2-r3-the-january-rebalance-trades.md"
SHUFFLES, SEED = 1000, 636
REQUIRED_OUTPUTS = ("verdict", "A", "B", "sign_test", "label_shuffle", "descriptive", "headline_only",
                    "dose_response", "groups", "component_line", "power", "deviations", "reads")


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
RC = _load("r_common", "r_common.py")
R2 = _load("run_stage_r2", "run_stage_r2.py")
G = RD.G


class R3Error(RuntimeError):
    pass


def first_bday(b: Any, ym: str) -> str | None:
    return next((d for d in b.bdays if d[:7] == ym), None)


def forecast(b: Any, kappa: dict[str, Any], y: int, day: str, headline: bool = False) -> pd.DataFrame:
    """The forecast total flow for target year y, as known at `day` (settlements and weights to the prior business
    day). Separable: kB dN_B + kG dN_G; combined: kC (dN_B + AUM dN_G)."""
    prev = b.bdays[b.bdays.index(day) - 1]
    w = G.weights(b.cim[y - 1], b.H, prev)
    gf = b.gsci_jan_flow(y, day=prev)["dN_G_per_bn"]
    aum = G.AUM[y][0]
    rows = []
    for comp in RD.UNIVERSE:
        L = G.lead_of(G.lead_table()[G.COMP[comp][2]], int(day[:4]), int(day[5:7]))
        p = b.settle(comp, prev, L)
        sig = b.sigma(comp, L, day)
        root, ex = RD.SD.ROOTS[G.COMP[comp][2]]
        v = b.vol_d(f"{root}{RD.LETTER[L[1] - 1]}{L[0] % 100:02d}-{ex}", day)
        if p is None or sig is None or v is None:
            continue
        tgt_prev = b.cip[y - 1].get(comp, 0.0)
        gap = (b.cip[y].get(comp, 0.0) - tgt_prev) if headline else (b.cip[y].get(comp, 0.0) - w.get(comp, 0.0))
        dnb = aum * 1e9 * gap / (p * G.mult(comp))
        q = (kappa["kappa_B"] * dnb + kappa["kappa_G_per_bn"] * gf.get(comp, 0.0)) if kappa["separable"] \
            else kappa["kappa_C"] * (dnb + aum * gf.get(comp, 0.0))
        rows.append({"year": y, "comp": comp, "root": root, "day": day, "Q": q, "sigma": sig, "V": v, "P": p,
                     "mult": G.mult(comp), "cost_usd": b.cost(comp), "usable": True,
                     "impact_usd": RD.Y_IMPACT * sig * math.sqrt(abs(q) / v) * p * G.mult(comp)})
    return pd.DataFrame(rows)


def sub_return(b: Any, comp: str, start: str, end: str) -> float:
    return float(np.prod([b.R[comp][d] or 1.0 for d in b.bdays if start < d <= end])) - 1


def trades(b: Any, kappa: dict[str, Any], window: str = "dec", headline: bool = False) -> pd.DataFrame:
    """window 'dec': Dec BD1 (y-1) -> det(y) (the test). 'nov': Nov BD1 -> Dec BD1 (the selftest's placebo)."""
    out = []
    for y in RD.YEARS:
        dec1 = first_bday(b, f"{y - 1}-12")
        if dec1 is None:
            continue
        f = forecast(b, kappa, y, dec1, headline)
        start, end = (dec1, b.det[y]) if window == "dec" else (first_bday(b, f"{y - 1}-11"), dec1)
        f["move_usd"] = [np.sign(r.Q) * sub_return(b, r.comp, start, end) * r.P * r.mult for r in f.itertuples()]
        out.append(f)
    return pd.concat(out, ignore_index=True)


def gate(t: pd.DataFrame, snr_y: dict[int, float]) -> pd.Series:
    return (t["impact_usd"] >= 3 * t["cost_usd"]) & (t["year"].map(snr_y).fillna(0.0) >= 1.5)


def basket(t: pd.DataFrame) -> pd.DataFrame:
    """B: long the top 3 forecast buys, short the bottom 3 forecast sells, equal risk (move already signed)."""
    out = []
    for y, g in t.groupby("year"):
        g = g[g["Q"] != 0].assign(share=lambda z: z["Q"] / z["V"])
        lo, sh = g[g["Q"] > 0].nlargest(3, "share"), g[g["Q"] < 0].nsmallest(3, "share")
        if lo.empty or sh.empty:
            continue
        legs = pd.concat([lo, sh]).copy()
        legs["w"] = 1.0 / (legs["sigma"] * legs["P"] * legs["mult"])
        legs.loc[legs["Q"] < 0, "w"] *= len(lo) / len(sh)
        out.append({"year": y, "gross": float((legs["w"] * legs["move_usd"]).sum()), "comp": "basket",
                    "root": "basket", "cost_usd": float((legs["w"] * legs["cost_usd"]).sum())})
    return pd.DataFrame(out)


def two_tests(a: pd.DataFrame, t: pd.DataFrame) -> dict[str, Any]:
    res: dict[str, Any] = {}
    for lab, d, c in (("A", a, "move_usd"), ("B", basket(t), "gross")):
        if len(d) < 10 or d["year"].nunique() < 4:
            res[lab] = {"n": int(len(d)), "p": 1.0, "note": "too few trades",
                        "mean_gross": float(d[c].mean()) if len(d) else None}
            continue
        res[lab] = {"n": int(len(d)), "mean_gross": float(d[c].mean()), "mean_cost": float(d["cost_usd"].mean()),
                    **RC.wild_boot_p(d[c].to_numpy(float), d["year"].to_numpy())}
    adj = RC.holm({k: v["p"] for k, v in res.items()})
    for k in res:
        res[k]["p_holm"] = adj[k]
        mg, mc = res[k].get("mean_gross"), res[k].get("mean_cost")
        res[k]["pass"] = bool(mg is not None and mc is not None and mg >= mc and adj[k] < RC.ALPHA)
    return res


def shuffle(t: pd.DataFrame, snr_y: dict[int, float], rng: np.random.Generator) -> dict[str, np.ndarray]:
    raw = t["move_usd"] * np.sign(t["Q"])
    na, nb = [], []
    for _ in range(SHUFFLES):
        p = t.copy()
        for _y, g in t.groupby("year"):
            p.loc[g.index, "Q"] = rng.permutation(g["Q"].to_numpy())
        p["impact_usd"] = RD.Y_IMPACT * p["sigma"] * np.sqrt(np.abs(p["Q"]) / p["V"]) * p["P"] * p["mult"]
        p["move_usd"] = raw * np.sign(p["Q"])
        tr = p[gate(p, snr_y)]
        na.append(float(tr["move_usd"].mean()) if len(tr) else 0.0)
        bk = basket(p)
        nb.append(float(bk["gross"].mean()) if len(bk) else 0.0)
    return {"A": np.array(na), "B": np.array(nb)}


def descriptive(b: Any, kappa: dict[str, Any]) -> dict[str, Any]:
    """(a): per year and period, the Spearman across the 12 of the residual sub-index return with the forecast share
    at the period's start. A year whose announcement falls after 1 December has an empty first period."""
    out: dict[str, Any] = {}
    for y in RD.YEARS:
        ann = pd.read_csv(IR / "weights" / f"{y}.csv", encoding="utf-8")["announcement_date"].iloc[0]
        dec1, jan1 = first_bday(b, f"{y - 1}-12"), first_bday(b, f"{y}-01")
        ann_d = next((d for d in b.bdays if d >= ann), None)
        dec_last = [d for d in b.bdays if d[:7] == f"{y - 1}-12"][-1]
        periods = {"announcement_to_dec1": (ann_d, dec1), "dec": (dec1, dec_last), "jan_to_det": (jan1, b.det[y])}
        res = {}
        for name, (s, e) in periods.items():
            if s is None or e is None or s >= e:
                res[name] = None
                continue
            f = forecast(b, kappa, y, s)
            rets = {c: sub_return(b, c, s, e) for c in f["comp"]}
            mean = float(np.mean(list(rets.values())))
            f["resid"] = f["comp"].map(lambda c: rets[c] - mean)
            res[name] = round(float(stats.spearmanr(f["Q"] / f["V"], f["resid"]).statistic), 4) if len(f) >= 4 else None
        out[str(y)] = res
    summary = {name: {"positive": sum(1 for v in out.values() if v.get(name) is not None and v[name] > 0),
                      "cast": sum(1 for v in out.values() if v.get(name) is not None)}
               for name in ("announcement_to_dec1", "dec", "jan_to_det")}
    return {"by_year": out, "summary": summary}


def build(kappa: dict[str, Any]) -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    b = RD.Base()
    snr_y = {y: RC.snr(kappa, G.AUM[y]) for y in RD.YEARS}
    t = trades(b, kappa)
    a = t[gate(t, snr_y)]
    tests = two_tests(a, t)
    sy = a.assign(share=a["Q"] / a["V"], raw=a["move_usd"] * np.sign(a["Q"]))[["year", "comp", "share", "raw"]]
    sign = RC.sign_test(sy, "share", "raw")
    nulls = shuffle(t, snr_y, rng)
    shuf = {lab: RC.shuffle_verdict(float(tests[lab].get("mean_gross") or 0.0), nulls[lab]) for lab in ("A", "B")}
    kill = any(v["verdict"] == "FAIL" for v in shuf.values())
    head = trades(b, kappa, headline=True)
    head_t = two_tests(head[gate(head, snr_y)], head)
    dose = float(stats.spearmanr(np.abs(a["Q"]) / a["V"], a["move_usd"]).statistic) if len(a) > 3 else None
    pw = json.loads((IR / "power_r.json").read_text(encoding="utf-8"))["R3"]
    k = min(pw, key=lambda x: abs(float(x) - abs(kappa["kappa"])))
    h_r3 = any(v["pass"] for v in tests.values())
    adopt = RC.adoption(h_r3, sign["pass"], None)
    # the shuffle is a specificity check: it overturns a pooled pass, it does not relabel a miss (deposit s.14)
    if h_r3 and kill:
        verdict = "KILLED (label shuffle)"
    elif adopt:
        verdict = "ADOPTED: " + ", ".join(x for x, v in tests.items() if v["pass"])
    elif h_r3:
        verdict = "POOLED PASS, NOT ADOPTED (driven by a few years)"
    else:
        verdict = f"NOT DETECTED (effects above the MDE ~${pw[k].get('mde_usd_2.8se')} excluded; D636 s.8)"
    return {"spec": "D636 s.6 (1315ecf + s.11), POWER 7ec7a21", "kappa": kappa, "snr_by_year": snr_y,
            "verdict": {"verdict": verdict, "H_R3b": h_r3, "adoption": adopt, "shuffle_kill": kill,
                        "c0": kappa["c0_verdict"]},
            "A": tests["A"], "B": tests["B"], "sign_test": sign, "label_shuffle": shuf,
            "descriptive": descriptive(b, kappa), "headline_only": head_t, "dose_response": dose,
            "groups": RC.four_groups(a, "move_usd", "cost_usd", len(a) / 10) if len(a) > 5 else {},
            "component_line": RC.component_line(a, "move_usd", len(a) / 10) if len(a) > 5 else {},
            "power": {"grid_kappa": float(k), **pw[k]}, "traded_by_comp": a.groupby("comp").size().to_dict(),
            "deviations": ["R3's B has no intraday timing: every leg enters and exits at settlement, so s.3's common "
                           "entry does not arise."],
            "reads": {"spec_sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest(), **b.reads}}


def dump(doc: dict[str, Any]) -> str:
    return json.dumps(doc, indent=1, sort_keys=True, default=float) + "\n"


def selftest() -> int:
    """The November placebo window only: the raw placebo passes no test; a synthetic $5,000 effect passes; the
    forecast uses nothing at or after its day (lag audit)."""
    b = RD.Base()
    kappa = {"separable": False, "kappa_C": 0.05, "kappa": 0.05, "se": 0.001, "kappa_B": 0.05, "kappa_G_per_bn": 0.0,
             "c0_verdict": "PASS", "c0_passed": True}
    snr_y = {y: RC.snr(kappa, G.AUM[y]) for y in RD.YEARS}
    t = trades(b, kappa, window="nov")
    null = two_tests(t[gate(t, snr_y)], t)
    if any(v["pass"] for v in null.values()):
        raise AssertionError("the raw November placebo passed an R3 test")
    syn = t.assign(move_usd=t["move_usd"] + 5000.0)
    eff = two_tests(syn[gate(syn, snr_y)], syn)
    if not eff["A"]["pass"]:
        raise AssertionError(f"a synthetic $5,000 effect did not pass R3 A: {eff['A']}")
    # lag audit: every forecast day's inputs are strictly before it
    for r in t.itertuples():
        prev = b.bdays[b.bdays.index(r.day) - 1]
        if not prev < r.day:
            raise R3Error("lag audit: the forecast read its own day")
    print(f"selftest OK: the November placebo passes no test; a synthetic $5,000 effect passes A "
          f"(p_holm {eff['A']['p_holm']:.4f}); the lag audit holds")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    kappa = RC.kappa_from_c0()
    if a.run:
        if OUT.exists():
            raise SystemExit(f"{OUT.name} exists: Stage R3 runs once")
        doc = build(kappa)
        miss = [k for k in REQUIRED_OUTPUTS if k not in doc]
        if miss:
            raise R3Error(f"declared outputs missing: {miss}")
        OUT.write_text(dump(doc), encoding="utf-8", newline="\n")
        print(f"STAGE R3: {doc['verdict']['verdict']}")
        return 0
    if a.check:
        if dump(build(kappa)) != OUT.read_text(encoding="utf-8"):
            raise SystemExit("CHECK FAILED: the rebuild differs from stage_r3.json")
        print("check OK: byte for byte")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
