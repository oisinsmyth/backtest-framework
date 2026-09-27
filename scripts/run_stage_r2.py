"""D636 Stage R2: does the January rebalance's price pressure reverse after the last hedge day?

Spec: docs/decisions/D636-PRE-REG-stages-r1-r2-r3-the-january-rebalance-trades.md s.5 (1315ecf; s.11 notes), after
D636's POWER (7ec7a21), which found R2 UNDERPOWERED (power 0.3-9% at its plausible effect): a miss is INCONCLUSIVE.

    uv run python -W error::RuntimeWarning scripts/run_stage_r2.py --selftest   # reads placebo holds (from BD16) only
    uv run python -W error::RuntimeWarning scripts/run_stage_r2.py --run        # refuses a second run; needs gate_c0.json
    uv run python -W error::RuntimeWarning scripts/run_stage_r2.py --check

Entry at the settlement of January BD9, OPPOSITE to each commodity's total predicted flow; exit at the settlement
h = 1, 3, 5 business days later. A: total-flow |I| >= 3 x cost and SNR >= 1.5. B: the s.3 basket on the total flow
share, reversed. H-R2: any of the 6 tests (3 holds x 2) with mean >= cost and Holm-adjusted wild-bootstrap p < 0.05.
Adoption: H-R2 AND the yearly sign test on the surviving hold (the move reversed).
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
OUT = IR / "stage_r2.json"
SPEC = REPO / "docs" / "decisions" / "D636-PRE-REG-stages-r1-r2-r3-the-january-rebalance-trades.md"
HOLDS = (1, 3, 5)
REQUIRED_OUTPUTS = ("verdict", "tests", "sign_test", "calibration_reported", "headline_only", "dose_response",
                    "groups", "component_line", "power", "deviations", "reads")


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
G = RD.G


class R2Error(RuntimeError):
    pass


def totals(b: Any, kappa: dict[str, Any], headline: bool = False) -> pd.DataFrame:
    """Per (year, commodity): the total predicted flow over BD5-9 and the gate inputs at BD9."""
    h = RD.r1_rows(b, kappa, "hedge", headline=headline)
    t = h.sort_values("day").groupby(["year", "comp"]).agg(
        Q=("Q", "sum"), sigma=("sigma", "last"), V=("V", "last"), P=("P", "last"), mult=("mult", "first"),
        cost_usd=("cost_usd", "first"), usable=("usable", "all"), root=("root", "first"), day9=("day", "last"),
        sym=("sym", "first")).reset_index()
    t["impact_usd"] = RD.Y_IMPACT * t["sigma"] * np.sqrt(np.abs(t["Q"]) / t["V"]) * t["P"] * t["mult"]
    return t


def moves(b: Any, t: pd.DataFrame, start_bd: int | None = None) -> pd.DataFrame:
    """The reversal move per hold: -sign(Q) x (settle[entry + h] - settle[entry]) x mult, entry = BD9 (or, for the
    selftest's placebo, January BD `start_bd`)."""
    out = t.copy()
    for h in HOLDS:
        col = []
        for r in t.itertuples():
            day = r.day9 if start_bd is None else next(iter(RD.january_days(b, r.year, start_bd, start_bd)), None)
            if day is None or not r.usable or r.Q == 0:
                col.append(np.nan)
                continue
            i = b.bdays.index(day)
            ym, _ = b.lead_sym(r.comp, r.year)
            p0, p1 = b.settle(r.comp, b.bdays[i], ym), b.settle(r.comp, b.bdays[i + h], ym)
            col.append(-np.sign(r.Q) * (p1 - p0) * r.mult if p0 is not None and p1 is not None else np.nan)
        out[f"move_h{h}"] = col
    return out


def gate(t: pd.DataFrame, snr_y: dict[int, float]) -> pd.Series:
    s = t["year"].map(snr_y).fillna(0.0)
    return t["usable"] & (t["impact_usd"] >= 3 * t["cost_usd"]) & (s >= 1.5)


def basket(t: pd.DataFrame, col: str, k: int = 3) -> pd.DataFrame:
    """B reversed: short the top k predicted buys, long the bottom k predicted sells, equal risk."""
    out = []
    for y, g in t.groupby("year"):
        g = g[g["usable"] & (g["Q"] != 0) & g[col].notna()].assign(share=lambda z: z["Q"] / z["V"])
        lo, sh = g[g["Q"] > 0].nlargest(k, "share"), g[g["Q"] < 0].nsmallest(k, "share")
        if lo.empty or sh.empty:
            continue
        legs = pd.concat([lo, sh]).copy()
        legs["w"] = 1.0 / (legs["sigma"] * legs["P"] * legs["mult"])
        legs.loc[legs["Q"] < 0, "w"] *= len(lo) / len(sh)
        risk = legs["w"] * legs["sigma"] * legs["P"] * legs["mult"]
        if abs(risk[legs["Q"] > 0].sum() / risk[legs["Q"] < 0].sum() - 1) > 0.01:
            raise R2Error("unit test 10: unequal risk")
        out.append({"year": y, "gross": float((legs["w"] * legs[col]).sum()), "comp": "basket", "root": "basket",
                    "cost_usd": float((legs["w"] * legs["cost_usd"]).sum())})
    return pd.DataFrame(out)


def six_tests(a: pd.DataFrame, t: pd.DataFrame) -> dict[str, Any]:
    res: dict[str, Any] = {}
    for h in HOLDS:
        col = f"move_h{h}"
        for lab, d, c in ((f"A_h{h}", a.dropna(subset=[col]), col), (f"B_h{h}", basket(t, col), "gross")):
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


def power_note(kappa: float) -> dict[str, Any]:
    p = json.loads((IR / "power_r.json").read_text(encoding="utf-8"))["R2"]
    k = min(p, key=lambda x: abs(float(x) - kappa))
    return {"grid_kappa": float(k), **{h: {"power": v.get("power"), "mde_usd": v.get("mde_usd_2.8se")} for h, v in p[k].items()}}


def build(kappa: dict[str, Any]) -> dict[str, Any]:
    b = RD.Base()
    snr_y = {y: RC.snr(kappa, G.AUM[y]) for y in RD.YEARS}
    t = moves(b, totals(b, kappa))
    t["traded"] = gate(t, snr_y)
    a = t[t["traded"]]
    tests = six_tests(a, t)
    passed = [k for k, v in tests.items() if v["pass"]]
    surv = min(passed, key=lambda k: tests[k]["p_holm"]) if passed else "A_h1"
    hcol = f"move_{surv.split('_')[1]}"
    # the reversed raw move: the raw price move is -move x sign(Q), reversed it is move x sign(Q); a reversal makes
    # it rise with the signed flow share
    sy = a.assign(share=a["Q"] / a["V"], rev=a[hcol] * np.sign(a["Q"])).dropna(subset=["rev"])
    sign = RC.sign_test(sy[["year", "comp", "share", "rev"]], "share", "rev")
    sign["hold"] = surv
    cal = {"realised_reversal_over_total_impact": float(a[hcol].sum() / a["impact_usd"].sum()) if len(a) else None}
    head = moves(b, totals(b, kappa, headline=True))
    head["traded"] = gate(head, snr_y)
    head_t = six_tests(head[head["traded"]], head)
    dose = {f"h{h}": float(stats.spearmanr(np.abs(a["Q"]) / a["V"], a[f"move_h{h}"], nan_policy="omit").statistic)
            for h in HOLDS} if len(a) > 3 else {}
    groups = {f"A_h{h}": RC.four_groups(a.dropna(subset=[f"move_h{h}"]), f"move_h{h}", "cost_usd", len(a) / 10)
              for h in HOLDS if len(a) > 5}
    comp_line = {f"A_h{h}": RC.component_line(a.dropna(subset=[f"move_h{h}"]), f"move_h{h}", len(a) / 10)
                 for h in HOLDS if len(a) > 5}
    h_r2 = bool(passed)
    adopt = RC.adoption(h_r2, sign["pass"], None)
    pw = power_note(abs(kappa["kappa"]))
    if adopt:
        verdict = f"ADOPTED ({surv})"
    elif h_r2:
        verdict = f"POOLED PASS ({surv}), NOT ADOPTED (driven by a few years)"
    else:
        verdict = "INCONCLUSIVE (underpowered; D636 s.8)"
    return {"spec": "D636 s.5 (1315ecf + s.11), POWER 7ec7a21", "kappa": kappa, "snr_by_year": snr_y,
            "verdict": {"verdict": verdict, "H_R2": h_r2, "passed": passed, "adoption": adopt, "c0": kappa["c0_verdict"]},
            "tests": tests, "sign_test": sign, "calibration_reported": cal, "headline_only": head_t,
            "dose_response": dose, "groups": groups, "component_line": comp_line, "power": pw,
            "traded_by_comp": a.groupby("comp").size().to_dict(),
            "deviations": [], "reads": {"spec_sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest(), **b.reads}}


def dump(doc: dict[str, Any]) -> str:
    return json.dumps(doc, indent=1, sort_keys=True, default=float) + "\n"


def selftest() -> int:
    """Placebo holds only (entry at January BD16): a synthetic reversal of 2 x the MDE must pass one test; the raw
    placebo must not; the money audit (a predicted buy whose price then falls books +) holds."""
    if not math.isclose(-np.sign(1.0) * (1.99 - 2.0) * 10_000, 100.0):
        raise R2Error("sign audit: a reversal after a predicted buy must book + when the price falls")
    b = RD.Base()
    kappa = {"separable": False, "kappa_C": 0.05, "kappa": 0.05, "se": 0.001, "kappa_B": 0.05, "kappa_G_per_bn": 0.0,
             "c0_verdict": "PASS", "c0_passed": True}
    snr_y = {y: RC.snr(kappa, G.AUM[y]) for y in RD.YEARS}
    t = moves(b, totals(b, kappa), start_bd=16)
    t["traded"] = gate(t, snr_y)
    a = t[t["traded"]]
    null = six_tests(a, t)
    if any(v["pass"] for v in null.values()):
        raise AssertionError("the raw placebo passed an R2 test")
    syn = t.copy()
    for h in HOLDS:
        syn[f"move_h{h}"] = syn[f"move_h{h}"] + 3000.0
    eff = six_tests(syn[syn["traded"]], syn)
    if not any(v["pass"] for v in eff.values()):
        raise AssertionError(f"a synthetic $3,000 reversal passed no R2 test: {eff}")
    print(f"selftest OK: the placebo passes none of the 6 tests; a synthetic $3,000 reversal passes "
          f"{sum(v['pass'] for v in eff.values())}; the money audit holds")
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
            raise SystemExit(f"{OUT.name} exists: Stage R2 runs once")
        doc = build(kappa)
        miss = [k for k in REQUIRED_OUTPUTS if k not in doc]
        if miss:
            raise R2Error(f"declared outputs missing: {miss}")
        OUT.write_text(dump(doc), encoding="utf-8", newline="\n")
        print(f"STAGE R2: {doc['verdict']['verdict']}")
        return 0
    if a.check:
        if dump(build(kappa)) != OUT.read_text(encoding="utf-8"):
            raise SystemExit("CHECK FAILED: the rebuild differs from stage_r2.json")
        print("check OK: byte for byte")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
