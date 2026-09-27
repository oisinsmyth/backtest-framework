"""D636 Stage R1: do the January rebalance flows move prices into the settlement window on the execution days?

Spec: docs/decisions/D636-PRE-REG-stages-r1-r2-r3-the-january-rebalance-trades.md (1315ecf; its s.11 notes), under
IR-A1..IR-A14, after D636's POWER (7ec7a21). This file comes after both and before its one run.

    uv run python -W error::RuntimeWarning scripts/run_stage_r1.py --selftest   # reads placebo days only
    uv run python -W error::RuntimeWarning scripts/run_stage_r1.py --run        # refuses a second run; needs gate_c0.json
    uv run python -W error::RuntimeWarning scripts/run_stage_r1.py --check

THE TEST (D636 s.4): on January BD5-BD9 of 2016-2025, each traded commodity enters at the close of bar t0+1
(t0 = W_start - 10 min) in the direction of its predicted flow Q, and exits at the last trade before W_end.
H-R1 per construction: mean gross >= mean cost AND the wild cluster bootstrap by year (Holm across A and B) p < 0.05.
Adoption: H-R1 AND the yearly sign test (>= 9 of 10) AND the calibration CI overlapping [0.5, 2], with C0 PASSED.
If C0 did not pass, R1 is descriptive only (R-D5). The date placebo or the label shuffle can kill it (deposit s.14).
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
OUT = IR / "stage_r1.json"
SPEC = REPO / "docs" / "decisions" / "D636-PRE-REG-stages-r1-r2-r3-the-january-rebalance-trades.md"
GRAINS = {"Corn", "Soybeans", "Soybean Meal", "Soybean Oil", "Wheat", "HRW Wheat"}
SHUFFLES, SEED = 1000, 636
KEY = ["year", "comp", "k"]
REQUIRED_OUTPUTS = ("verdict", "A", "B", "sign_test", "calibration", "placebo", "label_shuffle", "headline_only",
                    "dose_response", "robustness", "beside", "component_line", "audits", "deviations", "reads")
DEVIATIONS = [
    "D636 s.7's LE/HE/GC beside trades the NEXT contract with BCOM's roll buy plus the reweight on it; GSCI's legs on "
    "those three are not added.",
]


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


class R1Error(RuntimeError):
    pass


# ------------------------------------------------------------------ construction A
def gate_rows(rows: pd.DataFrame, snr_by_year: dict[int, float]) -> pd.Series:
    s = rows["year"].map(snr_by_year).fillna(0.0)
    return rows["usable"] & (rows["impact_usd"] >= 3 * rows["cost_usd"]) & (s >= 1.5) & rows["move_usd"].notna()


def gate_second(rows: pd.DataFrame, snr_by_year: dict[int, float]) -> np.ndarray:
    """The gate audit's second implementation: the impact rebuilt from its stored inputs, never calling r_design."""
    imp = 0.7 * rows["sigma"].astype(float) * np.sqrt(np.abs(rows["Q"].astype(float)) / rows["V"].astype(float)) \
        * rows["P"].astype(float) * rows["mult"].astype(float)
    ok = np.array([snr_by_year.get(int(y), 0.0) >= 1.5 for y in rows["year"]])
    return (imp.to_numpy() >= 3 * rows["cost_usd"].to_numpy()) & ok & rows["usable"].to_numpy() \
        & rows["move_usd"].notna().to_numpy()


# ------------------------------------------------------------------ construction B
def check_parity(legs: pd.DataFrame, qcol: str) -> None:
    """Unit test 10: the long and short books carry equal dollar risk, within 1%."""
    risk = legs["w"] * legs["sigma"] * legs["P"] * legs["mult"]
    rl, rs = risk[legs[qcol] > 0].sum(), risk[legs[qcol] < 0].sum()
    if abs(rl / rs - 1) > 0.01:
        raise R1Error(f"unit test 10: B's books carry unequal risk ({rl:.4g} vs {rs:.4g})")


def book_b(b: Any, rows: pd.DataFrame, qcol: str = "Q", k: int = 3, t0_min: int = 10) -> pd.DataFrame:
    """B (D636 s.3): per (year, day), long the top k predicted buys by Q/V, short the bottom k predicted sells;
    inverse dollar-vol weights, the short book scaled to the long book's risk; every leg enters at the close of bar
    t0c+1 with t0c = the earliest chosen W_start - t0_min, and exits at its own W_end (unit test 11)."""
    out = []
    for (y, dk), g in rows.groupby(["year", "k"]):
        g = g[g["usable"] & (g[qcol] != 0)].assign(share=lambda z: z[qcol] / z["V"])
        lo = g[g[qcol] > 0].nlargest(k, "share")
        sh = g[g[qcol] < 0].nsmallest(k, "share")
        if lo.empty or sh.empty:
            continue
        legs = pd.concat([lo, sh]).copy()
        legs["w"] = 1.0 / (legs["sigma"] * legs["P"] * legs["mult"])
        legs.loc[legs[qcol] < 0, "w"] *= len(lo) / len(sh)
        check_parity(legs, qcol)
        t0c = legs["ws"].min() - pd.Timedelta(minutes=t0_min)
        if not t0c < legs["ws"].min():
            raise R1Error("unit test 11: B's common entry does not precede the earliest window")
        mv, imp, ok = 0.0, 0.0, True
        floor = t0c - pd.Timedelta(hours=3)
        for r in legs.itertuples():
            f = b.before(r.sym, t0c + pd.Timedelta(minutes=2), floor)
            e = b.before(r.sym, r.we, floor)  # its own W_end
            if f is None or e is None:
                ok = False
                break
            mv += r.w * (e - f) * np.sign(getattr(r, qcol)) * r.mult
            imp += r.w * abs(r.impact_usd)
        if ok:
            out.append({"year": y, "k": dk, "gross": mv, "impact": imp, "legs": int(len(legs)), "comp": "basket",
                        "root": "basket", "cost_usd": float((legs["w"] * legs["cost_usd"]).sum())})
    return pd.DataFrame(out)


# ------------------------------------------------------------------ tests
def h_test(a: pd.DataFrame, bk: pd.DataFrame, gcol_a: str = "move_usd") -> dict[str, Any]:
    res: dict[str, Any] = {}
    for lab, d, col in (("A", a, gcol_a), ("B", bk, "gross")):
        if len(d) < 10 or d["year"].nunique() < 4:
            res[lab] = {"n": int(len(d)), "p": 1.0, "mean_gross": float(d[col].mean()) if len(d) else None,
                        "mean_cost": float(d["cost_usd"].mean()) if len(d) else None, "note": "too few trades"}
            continue
        wb = RC.wild_boot_p(d[col].to_numpy(float), d["year"].to_numpy())
        res[lab] = {"n": int(len(d)), "mean_gross": float(d[col].mean()), "mean_cost": float(d["cost_usd"].mean()), **wb}
    adj = RC.holm({k: v["p"] for k, v in res.items()})
    for k in res:
        res[k]["p_holm"] = adj[k]
        mg, mc = res[k].get("mean_gross"), res[k].get("mean_cost")
        res[k]["pass"] = bool(mg is not None and mc is not None and mg >= mc and adj[k] < RC.ALPHA)
    return res


def shuffle_null(b: Any, rows: pd.DataFrame, snr_y: dict[int, float], rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Label shuffle (D636 s.7): within each year Q is permuted across the commodities; each permutation's own gate,
    direction and B basket; the statistic is each construction's pooled mean move."""
    na, nb = [], []
    raw = rows["move_usd"] * np.sign(rows["Q"])  # exit - fill, in dollars, before the direction
    for _ in range(SHUFFLES):
        perm = rows.copy()
        for _y, g in rows.groupby("year"):
            comps = g["comp"].unique()
            mp = dict(zip(comps, rng.permutation(comps)))
            qmap = g.groupby("comp")["Q"].first().to_dict()
            perm.loc[g.index, "Q"] = g["comp"].map(lambda c: qmap[mp[c]]).to_numpy()
        perm["impact_usd"] = 0.7 * perm["sigma"] * np.sqrt(np.abs(perm["Q"]) / perm["V"]) * perm["P"] * perm["mult"]
        perm["move_usd"] = raw * np.sign(perm["Q"])
        tr = perm[gate_rows(perm, snr_y)]
        na.append(float(tr["move_usd"].mean()) if len(tr) else 0.0)
        bk = book_b(b, perm)
        nb.append(float(bk["gross"].mean()) if len(bk) else 0.0)
    return {"A": np.array(na), "B": np.array(nb)}


def summary(rows: pd.DataFrame, snr_y: dict[int, float]) -> dict[str, Any]:
    t = rows[gate_rows(rows, snr_y)]
    return {"n": int(len(t)), "mean_gross": float(t["move_usd"].mean()) if len(t) else None,
            "mean_net": float((t["move_usd"] - t["cost_usd"]).mean()) if len(t) else None}


def beside(b: Any, kappa: dict[str, Any], snr_y: dict[int, float]) -> dict[str, Any]:
    """D636 s.7 and s.11: LE, HE and GC with BCOM's roll buy added on the NEXT contract; and R1 with GSCI's January
    roll-in flow added on the energy leads."""
    extra = {(y, c): RD.bcom_roll_buy(b, c, y) for y in RD.YEARS for c in RD.BESIDE}
    roll3 = RD.r1_rows(b, kappa, "hedge", comps=RD.BESIDE, with_moves=True, next_contract=True, extra_dnb=extra)
    ext_g = {(y, c): RD.gsci_roll_in(b, c, y) for y in RD.YEARS for c in RD.UNIVERSE}
    groll = RD.r1_rows(b, kappa, "hedge", with_moves=True, extra_dng=ext_g)
    return {"LE_HE_GC_roll_plus_reweight_next_contract": summary(roll3, snr_y),
            "with_gsci_january_roll_in": {**summary(groll, snr_y),
                                         "comps_with_roll_in": sorted({c for (_, c), v in ext_g.items() if v})}}


# ------------------------------------------------------------------ build
def build(kappa: dict[str, Any]) -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    b = RD.Base()
    snr_y = {y: RC.snr(kappa, G.AUM[y]) for y in RD.YEARS}
    rows = RD.r1_rows(b, kappa, "hedge", with_moves=True)
    rows = rows.assign(traded=gate_rows(rows, snr_y))
    if not np.array_equal(rows["traded"].to_numpy(), gate_second(rows, snr_y)):
        raise R1Error("gate audit: the second implementation of construction A's traded set disagrees")
    a = rows[rows["traded"]]
    bk = book_b(b, rows)
    ht = h_test(a, bk)
    sy = a.assign(share=a["Q"] / a["V"], raw=a["move_usd"] * np.sign(a["Q"])).groupby(["year", "comp"]).agg(
        share=("share", "sum"), raw=("raw", "sum")).reset_index()
    sign = RC.sign_test(sy, "share", "raw")
    cal = RC.calibration(a["move_usd"].to_numpy(float), a["impact_usd"].to_numpy(float), a["year"].to_numpy())
    # the date placebo: BD12-16, hedge day k's traded set
    pla = RD.r1_rows(b, kappa, "placebo", with_moves=True)
    pm = rows[KEY + ["traded"]].merge(pla, on=KEY, how="left")
    pa = pm[pm["traded"] & pm["move_usd"].notna()]
    pt = h_test(pa, book_b(b, pla))
    kill_placebo = any(v.get("p_holm", 1) < RC.ALPHA and (v.get("mean_gross") or 0) > 0 for v in pt.values())
    both = a[KEY + ["move_usd"]].merge(pa[KEY + ["move_usd"]], on=KEY)
    if len(both) and np.allclose(both["move_usd_x"], both["move_usd_y"]):
        raise R1Error("right-quantity: the graded moves equal the placebo's")
    # the label shuffle
    nulls = shuffle_null(b, rows, snr_y, rng)
    shuf = {lab: RC.shuffle_verdict(float(ht[lab].get("mean_gross") or 0.0), nulls[lab]) for lab in ("A", "B")}
    kill_shuffle = any(v["verdict"] == "FAIL" for v in shuf.values())
    # headline-only, dose-response
    head = RD.r1_rows(b, kappa, "hedge", with_moves=True, headline=True)
    head_t = h_test(head[gate_rows(head, snr_y)], book_b(b, head))
    dose = float(stats.spearmanr(np.abs(a["Q"]) / a["V"], a["move_usd"]).statistic) if len(a) > 3 else None
    # robustness (reported)
    rob: dict[str, Any] = {
        "stress_fill": {"mean_gross": float(a["stress_move_usd"].mean()),
                        "mean_net": float((a["stress_move_usd"] - a["cost_usd"]).mean())},
        "cost_x2": {"mean_net": float((a["move_usd"] - 2 * a["cost_usd"]).mean())},
        "without_grains": summary(rows[~rows["comp"].isin(GRAINS)], snr_y)}
    kn = dict(kappa, separable=True, kappa_B=kappa["kappa_B"] if kappa["separable"] else kappa["kappa_C"], kappa_G_per_bn=0.0)
    rob["without_gsci_term"] = summary(RD.r1_rows(b, kn, "hedge", with_moves=True), snr_y)
    t20 = RD.r1_rows(b, kappa, "hedge", with_moves=True, t0_min=20)
    rob["t0_minus_20"] = summary(t20, snr_y)
    both20 = a[KEY + ["move_usd"]].merge(t20[KEY + ["move_usd"]], on=KEY)
    if len(both20) and np.allclose(both20["move_usd_x"], both20["move_usd_y"]):
        raise R1Error("right-quantity: the W_start - 20 variant's moves equal the primary's")
    for kk in (2, 4):
        bb = book_b(b, rows, k=kk)
        rob[f"B_k{kk}"] = {"n": int(len(bb)), "mean_gross": float(bb["gross"].mean()) if len(bb) else None}
    groups_a = RC.four_groups(a, "move_usd", "cost_usd", len(a) / 10) if len(a) > 5 else {}
    groups_b = RC.four_groups(bk.rename(columns={"gross": "g"}), "g", "cost_usd", len(bk) / 10) if len(bk) > 5 else {}
    comp_line = RC.component_line(a, "move_usd", len(a) / 10) if len(a) > 5 else {}
    # the verdict (D636 s.4, s.7; deposit s.14)
    pooled = {lab: bool(ht[lab]["pass"]) for lab in ("A", "B")}
    adopt = {lab: RC.adoption(pooled[lab], sign["pass"], cal["pass"]) for lab in ("A", "B")}
    # the date placebo and the label shuffle are specificity checks: they overturn a pooled pass; a miss stays a miss
    if not kappa["c0_passed"]:
        verdict = f"DESCRIPTIVE (C0 {kappa['c0_verdict']}; R-D5)"
    elif any(pooled.values()) and (kill_placebo or kill_shuffle):
        verdict = "KILLED (" + ", ".join(x for x, f in (("date placebo", kill_placebo), ("label shuffle", kill_shuffle)) if f) + ")"
    elif any(adopt.values()):
        verdict = "ADOPTED: " + ", ".join(k for k, v in adopt.items() if v)
    elif any(pooled.values()):
        verdict = "POOLED PASS, NOT ADOPTED (" + ("driven by a few years" if not sign["pass"] else "calibration") + ")"
    else:
        verdict = "FAIL"
    return {"spec": "D636 (1315ecf + s.11), POWER 7ec7a21", "kappa": kappa, "snr_by_year": snr_y,
            "verdict": {"verdict": verdict, "H_R1": pooled, "adoption": adopt, "sign_test": sign["pass"],
                        "calibration": cal["pass"], "placebo_kill": kill_placebo, "shuffle_kill": kill_shuffle},
            "A": {**ht["A"], "groups": groups_a, "traded_by_comp": a.groupby("comp").size().to_dict()},
            "B": {**ht["B"], "groups": groups_b}, "sign_test": sign, "calibration": cal,
            "placebo": pt, "label_shuffle": shuf, "headline_only": head_t, "dose_response": dose,
            "robustness": rob, "beside": beside(b, kappa, snr_y), "component_line": comp_line,
            "audits": {"gate_second_implementation": "agrees", "B_equal_risk": "within 1%",
                       "B_timing": "common entry before the earliest window; each leg exits at its own W_end",
                       "right_quantity": "graded moves differ from the placebo's and from the -20 variant's"},
            "deviations": DEVIATIONS,
            "reads": {"spec_sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest(), **b.reads}}


def dump(doc: dict[str, Any]) -> str:
    return json.dumps(doc, indent=1, sort_keys=True,
                      default=lambda o: o.isoformat() if hasattr(o, "isoformat") else float(o)) + "\n"


def audit_money() -> None:
    """A predicted buy (Q > 0) whose price rises books +; a predicted sell books the reverse."""
    for q, want in ((1.0, 100.0), (-1.0, -100.0)):
        if not math.isclose((2.01 - 2.0) * np.sign(q) * 10_000, want):
            raise R1Error("sign audit: the move does not pay the predicted way")


def selftest() -> int:
    """Reads PLACEBO days only (BD12-16). A synthetic effect (0.5 |I| added in the predicted direction) must pass
    H-R1 for A; the raw placebo must not; the gate audit and B's parity check raise on breaks."""
    print("  unit tests", RC.unit_tests())
    audit_money()
    b = RD.Base()
    kappa = {"separable": False, "kappa_C": 0.05, "kappa": 0.05, "se": 0.001, "kappa_B": 0.05, "kappa_G_per_bn": 0.0,
             "c0_verdict": "PASS", "c0_passed": True}
    snr_y = {y: RC.snr(kappa, G.AUM[y]) for y in RD.YEARS}
    pla = RD.r1_rows(b, kappa, "placebo", with_moves=True)
    null = h_test(pla[gate_rows(pla, snr_y)], book_b(b, pla))
    syn = pla.assign(move_usd=pla["move_usd"] + 0.5 * pla["impact_usd"])
    eff = h_test(syn[gate_rows(syn, snr_y)], book_b(b, pla))
    if not eff["A"]["pass"]:
        raise AssertionError(f"the synthetic effect did not pass H-R1 A: {eff['A']}")
    if null["A"]["pass"]:
        raise AssertionError(f"the raw placebo passed H-R1 A: {null['A']}")
    broken = pla.copy()
    broken["V"] = broken["V"] * 1e-6
    if np.array_equal(gate_rows(pla, snr_y).to_numpy(), gate_second(broken, snr_y)):
        raise AssertionError("the gate audit did not fire on broken inputs")
    legs = pd.DataFrame({"sigma": [1.0, 1.0], "P": [1.0, 1.0], "mult": [1.0, 1.0], "Q": [1.0, -1.0], "w": [1.0, 2.0]})
    try:
        check_parity(legs, "Q")
        raise AssertionError("the parity check did not fire")
    except R1Error:
        pass
    print(f"selftest OK: H-R1 A passes a synthetic 0.5|I| effect (p_holm {eff['A']['p_holm']:.4f}) and rejects the raw "
          f"placebo (p_holm {null['A']['p_holm']:.3f}); the gate audit and B's parity check fire; the money audit holds")
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
            raise SystemExit(f"{OUT.name} exists: Stage R1 runs once")
        doc = build(kappa)
        miss = [k for k in REQUIRED_OUTPUTS if k not in doc]
        if miss:
            raise R1Error(f"declared outputs missing: {miss}")
        OUT.write_text(dump(doc), encoding="utf-8", newline="\n")
        print(f"STAGE R1: {doc['verdict']['verdict']}")
        return 0
    if a.check:
        if dump(build(kappa)) != OUT.read_text(encoding="utf-8"):
            raise SystemExit("CHECK FAILED: the rebuild differs from stage_r1.json")
        print("check OK: byte for byte")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
