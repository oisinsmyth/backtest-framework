"""The opening agent-state model's POWER, before any stage runs (OPENING_AGENT_STATE_PREREG.md s.10; ledger 9A.2: "before
each stage, record real n_eff, SE, MDE and a plausible-effect statement"). The principal, 2026-09-28: "Run the power
study".

    python scripts/power_opening.py      # -> data/opening/power.json + docs/results/OPENING_AGENT_STATE_POWER.md

WHAT IT READS (and nothing else):
- D644's labels (`data/opening/labels.csv`): how many classified days, and how often ES and NQ carry the same label on
  the same day. The label-to-feature relation is never read.
- the DISPERSION of the raw 60-minute move from the t0+1 close (s.6.3's entry, to its 60-minute time stop), per
  market, from the bar fixture: its standard deviation and the same-day ES/NQ correlation. Its mean is never
  computed, and no move is signed by d0, a label, a state or an agent.

WHAT IT GIVES (s.10's rows, on the walk-forward's out-of-sample days: s.11 trains on 252 sessions first):
- n per market and pooled; rho_same_day; n_eff = n / (1 + rho) for a pooled ES+NQ statistic (s.10);
- H-O1 (classification): SE ~ 1/sqrt(n_eff) (the deposit's formula) and the binomial SE of accuracy at the base rate;
- H-O2 (decision value, paired, all days): SE = sigma / sqrt(n_eff), in sigma and in bp;
- the policy's traded days (~35% confident, s.10): the same on 0.35 n_eff;
- H-O6 per agent: SE of a correlation, 1/sqrt(n_eff);
- MDE at t = 2, at 80% power (2.8 SE), at Holm across the two t0s with 80% power, and at the programme's
  alpha = 0.005 (12A.2) with 80% power;
- the plausible-effect floor for the book: the micro round trip (D508 + $3 + one tick; OA-A5) in bp.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from backtest_framework.validation.frozen import assert_none_at_or_after, filter_before  # noqa: E402
from backtest_framework.validation.power import mde, mde_80, power_class, se_correlation, se_mean  # noqa: E402

BARS = REPO / "data" / "fixtures" / "fut_opening_globex_1m.csv.gz"
LABELS = REPO / "data" / "opening" / "labels.csv"
OUT_JSON = REPO / "data" / "opening" / "power.json"
OUT_MD = REPO / "docs" / "results" / "OPENING_AGENT_STATE_POWER.md"
RESERVED_FROM = "2025-03-01"
TRAIN = 252
T0S = {"09:45": ("09:45", "10:45"), "10:00": ("10:00", "11:00")}  # t0 -> (entry bar, exit bar); closes at +1 min
USD_PER_POINT = {"ES": 5.0, "NQ": 2.0}  # MES, MNQ
COST_USD = {"ES": 3.0 + 1.1345 * 1.25 + 1.25, "NQ": 3.0 + 2.1342 * 0.5 + 0.5}  # D508 crossing + $3 + one tick
Z_HOLM2_80 = 2.2414 + 0.8416  # two-sided 0.05/2, 80% power
Z_PROG_80 = 2.8070 + 0.8416   # two-sided 0.005 (12A.2), 80% power
CONFIDENT = 0.35              # s.10's planned share of confident (traded) days


def moves(t0: str) -> pd.DataFrame:
    a, b = T0S[t0]
    x = pd.read_csv(BARS, encoding="utf-8", dtype={"session": str, "hhmm": str}, usecols=["root", "session", "hhmm",
                                                                                        "close"])
    x = filter_before(x, "session", RESERVED_FROM)
    assert_none_at_or_after(x, "session", RESERVED_FROM)
    x = x[x["hhmm"].isin([a, b])]
    p = x.pivot_table(index=["root", "session"], columns="hhmm", values="close", aggfunc="first")
    out = pd.DataFrame({"move_bp": (np.log(p[b] / p[a]) * 1e4), "entry": p[a]}).reset_index()
    return out


def label_rho(L: pd.DataFrame) -> float:
    """Same-day ES/NQ agreement: the class-share-weighted mean phi of the per-class indicators (REV merged)."""
    w = L.pivot_table(index="session", columns="root", values="label", aggfunc="first").dropna()
    w = w.replace({"REV": "RANGE"})
    phis, wts = [], []
    for c in ("CONT", "FADE", "RANGE"):
        a, b = (w["ES"] == c).astype(float), (w["NQ"] == c).astype(float)
        phis.append(float(np.corrcoef(a, b)[0, 1]))
        wts.append(float((a.mean() + b.mean()) / 2))
    return float(np.average(phis, weights=wts))


def main() -> int:
    L = pd.read_csv(LABELS, encoding="utf-8", dtype={"session": str})
    L = filter_before(L, "session", RESERVED_FROM)
    assert_none_at_or_after(L, "session", RESERVED_FROM)
    res: dict = {"spec": "s.10; ledger 9A.2; OA-A1..A7; D644", "train_sessions": TRAIN, "cost_usd": COST_USD,
                 "t0": {}}
    for t0 in T0S:
        Lt = L[(L["t0"] == t0) & L["label"].notna()].copy()
        sess = sorted(Lt["session"].unique())
        oos = set(sess[TRAIN:])
        Lo = Lt[Lt["session"].isin(oos)]
        n = {r: int((Lo["root"] == r).sum()) for r in ("ES", "NQ")}
        n_pool = n["ES"] + n["NQ"]
        rho_lab = label_rho(Lo)
        base = float(Lo["label"].replace({"REV": "RANGE"}).value_counts(normalize=True).max())
        neff_lab = n_pool / (1 + rho_lab)
        m = moves(t0)
        m = m[m["session"].isin(oos)]
        sig = {r: float(m.loc[m["root"] == r, "move_bp"].std(ddof=1)) for r in ("ES", "NQ")}
        w = m.pivot_table(index="session", columns="root", values="move_bp").dropna()
        rho_mv = float(np.corrcoef(w["ES"], w["NQ"])[0, 1])
        neff_mv = len(w) * 2 / (1 + rho_mv)
        cost_bp = {r: float((COST_USD[r] / USD_PER_POINT[r] / m.loc[m["root"] == r, "entry"]).mean() * 1e4)
                   for r in ("ES", "NQ")}
        sig_pool = float(np.sqrt((sig["ES"] ** 2 + sig["NQ"] ** 2) / 2))
        cost_pool = float((cost_bp["ES"] + cost_bp["NQ"]) / 2)
        se_cls = se_correlation(neff_lab)
        se_acc = math.sqrt(base * (1 - base) / neff_lab)
        se_dv = se_mean(1.0, neff_mv)  # in sigma
        se_tr = se_mean(1.0, CONFIDENT * neff_mv)

        def ladder(se: float, scale: float = 1.0) -> dict:
            return {"t2": mde(se) * scale, "power80": mde_80(se) * scale, "holm2_80": Z_HOLM2_80 * se * scale,
                    "programme_0005_80": Z_PROG_80 * se * scale}

        row = {
            "oos_sessions": len(oos), "n": n, "n_pooled": n_pool,
            "H_O1": {"rho_same_day_labels": rho_lab, "n_eff": neff_lab, "base_rate": base,
                     "se_deposit": se_cls, "se_binomial_accuracy": se_acc, "mde_accuracy_lift": ladder(se_acc),
                     "mde_deposit_formula": ladder(se_cls), "plan": {"n_eff": "2,700-2,900", "mde_t2": 0.04}},
            "H_O2": {"rho_same_day_moves": rho_mv, "n_eff": neff_mv, "sigma_60min_bp": sig, "sigma_pooled_bp": sig_pool,
                     "se_sigma": se_dv, "mde_sigma": ladder(se_dv), "mde_bp": ladder(se_dv, sig_pool),
                     "cost_bp": cost_bp, "cost_pooled_bp": cost_pool,
                     "cost_in_sigma": cost_pool / sig_pool,
                     "class_t2_vs_cost": power_class(mde(se_dv) * sig_pool, cost_pool),
                     "class_programme_vs_cost": power_class(Z_PROG_80 * se_dv * sig_pool, cost_pool),
                     "plan": {"n_eff": "2,700-2,900", "mde_t2_sigma": 0.04}},
            "traded_days": {"share": CONFIDENT, "n_eff": CONFIDENT * neff_mv, "mde_sigma": ladder(se_tr),
                            "mde_bp": ladder(se_tr, sig_pool),
                            "class_t2_vs_cost": power_class(mde(se_tr) * sig_pool, cost_pool),
                            "plan": {"n_eff": "950-1,000", "mde_t2_sigma": 0.065}},
            "H_O6_per_agent": {"n_eff": neff_lab, "se_correlation": se_cls, "mde": ladder(se_cls),
                               "plan": {"n_eff": "~2,700", "mde_t2": 0.04}},
            "track3_edge_needed_sigma": 0.115,
        }
        res["t0"][t0] = row
    OUT_JSON.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    OUT_MD.write_text(render(res), encoding="utf-8", newline="\n")
    print(json.dumps({t: {"n_eff_labels": round(v["H_O1"]["n_eff"]), "rho_labels": round(v["H_O1"]["rho_same_day_labels"], 3),
                          "n_eff_moves": round(v["H_O2"]["n_eff"]), "rho_moves": round(v["H_O2"]["rho_same_day_moves"], 3),
                          "sigma_bp": {k: round(x, 1) for k, x in v["H_O2"]["sigma_60min_bp"].items()},
                          "cost_bp": {k: round(x, 2) for k, x in v["H_O2"]["cost_bp"].items()},
                          "HO2_mde_bp_t2": round(v["H_O2"]["mde_bp"]["t2"], 2),
                          "HO2_mde_bp_prog": round(v["H_O2"]["mde_bp"]["programme_0005_80"], 2),
                          "traded_mde_bp_t2": round(v["traded_days"]["mde_bp"]["t2"], 2),
                          "HO1_mde_acc_t2": round(v["H_O1"]["mde_accuracy_lift"]["t2"], 4)}
                      for t, v in res["t0"].items()}, indent=1))
    return 0


def render(res: dict) -> str:
    r = res["t0"]["10:00"]
    q = res["t0"]["09:45"]
    f = lambda x, d=3: f"{x:.{d}f}"  # noqa: E731
    lines = [
        "# Opening agent-state model: POWER (before any stage runs)",
        "",
        "*`scripts/power_opening.py` → `data/opening/power.json`. OPENING_AGENT_STATE_PREREG.md §10 and ledger 9A.2, on",
        "the walk-forward's out-of-sample sessions (§11 trains on 252 first). It reads D644's labels and the DISPERSION",
        "of the raw 60-minute move from the t0+1 close. No mean return is computed, and no move is signed by any state,",
        "label or agent.*",
        "",
        "## The samples (t0 = 10:00; 09:45 in brackets)",
        "",
        f"- Out-of-sample sessions: {r['oos_sessions']:,} ({q['oos_sessions']:,}); classified days ES {r['n']['ES']:,}, NQ "
        f"{r['n']['NQ']:,}.",
        f"- **Same-day ES/NQ agreement of the labels:** ρ = {f(r['H_O1']['rho_same_day_labels'])} "
        f"({f(q['H_O1']['rho_same_day_labels'])}), so the pooled n_eff is **{r['H_O1']['n_eff']:,.0f}**"
        f" ({q['H_O1']['n_eff']:,.0f}). The plan assumed 2,700–2,900 on the full sample before the vault.",
        f"- **Same-day correlation of the 60-minute moves:** ρ = {f(r['H_O2']['rho_same_day_moves'])} "
        f"({f(q['H_O2']['rho_same_day_moves'])}); n_eff **{r['H_O2']['n_eff']:,.0f}** ({q['H_O2']['n_eff']:,.0f}).",
        f"- σ of the 60-minute move: ES {r['H_O2']['sigma_60min_bp']['ES']:.1f} bp, NQ "
        f"{r['H_O2']['sigma_60min_bp']['NQ']:.1f} bp. The micro round trip is ES {r['H_O2']['cost_bp']['ES']:.2f} bp, "
        f"NQ {r['H_O2']['cost_bp']['NQ']:.2f} bp ({f(r['H_O2']['cost_in_sigma'])} σ pooled).",
        "",
        "## Minimum detectable effects (t0 = 10:00)",
        "",
        "| test | n_eff | SE | MDE t = 2 | 80% power | Holm across 2 t0, 80% | programme α 0.005, 80% | plan (t = 2) |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]

    def row(name: str, ne: float, se: float, lad: dict, unit: str, plan: str) -> str:
        return (f"| {name} | {ne:,.0f} | {se:.4f} | {lad['t2']:.4f}{unit} | {lad['power80']:.4f}{unit} | "
                f"{lad['holm2_80']:.4f}{unit} | {lad['programme_0005_80']:.4f}{unit} | {plan} |")

    lines.append(row("H-O1 accuracy lift (binomial, base " + f"{r['H_O1']['base_rate']:.3f})", r["H_O1"]["n_eff"],
                     r["H_O1"]["se_binomial_accuracy"], r["H_O1"]["mde_accuracy_lift"], "", "—"))
    lines.append(row("H-O1, the deposit's 1/√n_eff", r["H_O1"]["n_eff"], r["H_O1"]["se_deposit"],
                     r["H_O1"]["mde_deposit_formula"], "", "0.04"))
    lines.append(row("H-O2 decision value, all days", r["H_O2"]["n_eff"], r["H_O2"]["se_sigma"], r["H_O2"]["mde_sigma"],
                     " σ", "0.04 σ"))
    lines.append(row("the policy's traded days (35%)", r["traded_days"]["n_eff"],
                     r["traded_days"]["mde_sigma"]["t2"] / 2, r["traded_days"]["mde_sigma"], " σ", "0.065 σ"))
    lines.append(row("H-O6, per agent (a correlation)", r["H_O6_per_agent"]["n_eff"],
                     r["H_O6_per_agent"]["se_correlation"], r["H_O6_per_agent"]["mde"], "", "0.04"))
    b = r["H_O2"]["mde_bp"]
    t = r["traded_days"]["mde_bp"]
    lines += [
        "",
        "## In basis points, against the cost",
        "",
        f"- **H-O2 (per day, all days):** MDE {b['t2']:.2f} bp at t = 2, {b['programme_0005_80']:.2f} bp at the "
        f"programme's α with 80% power, against a pooled micro round trip of {r['H_O2']['cost_pooled_bp']:.2f} bp. "
        f"Class at t = 2: **{r['H_O2']['class_t2_vs_cost']}**; at the programme's bar: "
        f"**{r['H_O2']['class_programme_vs_cost']}**.",
        f"- **Per traded day (35%):** MDE {t['t2']:.2f} bp at t = 2, {t['programme_0005_80']:.2f} bp at the programme's "
        f"bar. Class at t = 2 against the cost: **{r['traded_days']['class_t2_vs_cost']}**.",
        "",
        "## The plausible-effect statement (ledger 9A.2)",
        "",
        "- **H-O2 and the traded days.** The floor that matters is the cost. A state policy whose edge per traded day is",
        "  below one micro round trip cannot be net-positive, whatever its t. **The traded-days row is the one to read",
        "  against it**: H-O2's all-days statistic averages in the no-trade days (0 by §9), so its bp MDE is per calendar",
        "  day, not per trade.",
        "- **H-O1.** There is no in-repository prior for day-type classification lift at the open. The MDE is stated",
        f"  against the deposit's plan (0.04 at t = 2) and the {r['H_O1']['base_rate']:.1%} base rate (RANGE with REV merged,",
        "  O-D4, which also makes the base rate harder to beat). The prior reads (OA-A2) point to",
        "  small effects: D531 (the opening-range breakout loses to the base rate), D463 (intraday momentum is a third",
        "  of its published size), D581 (dealer gamma orders nothing at the close).",
        "- **H-O6.** One correlation per agent. The MDE applies to each agent's own signature.",
        f"- **Track 3 (§12):** the consistency route is likely unless the edge exceeds ~{r['track3_edge_needed_sigma']} σ",
        "  per trade. The Track 1 estimate decides which route after Phase 5.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
