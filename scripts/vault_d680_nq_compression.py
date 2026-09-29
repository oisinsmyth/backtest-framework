"""D680: the NQ compression break for the joint vault run (the principal, 2026-09-29: "happy for the NQ compression to
stay in queue for the big vault run"; "Freeze the ones that where queued today"). D680 registers it; this file
computes it.

    uv run python scripts/vault_d680_nq_compression.py --known-answer   # D672's C1 on the spent in-sample, both frictions
    uv run python scripts/vault_d680_nq_compression.py --power          # vault pass rates -> data/vault_d680_power.json
    uv run python scripts/vault_d680_nq_compression.py --selftest
    uv run python scripts/vault_d680_nq_compression.py --vault-bars B.csv.gz --vault-use U.json --principals-word "..."
                                                                         # the joint run ONLY

THE RULE is D672's C1, unchanged: D666's plain break of yesterday's NQ RTH range +/- 0.25 ATR20 from 09:30 with E4
(initial stop at the level, trail 0.25 A, flat at the close), traded only when the compression tier < 1/3 (comp = mean
of the walk-forward percentiles of rv5 and the overnight two-way range; comp's own walk-forward percentile; D671's
functions). One MNQ. Friction counted ONCE (D668-A2): the trade at the level (no fill tick), charged $3 + the measured
d508_exec crossing.

THE PIPELINE (`book`) is cut-agnostic: the seal lives in the loaders. The known answer feeds it the in-sample bars from
D668's loader; the joint run feeds it bars built by the vault-input path (D644's fixture builder and G0's loader with
the cut moved to 2026-09-19 -- NOT YET BUILT, a prerequisite like D630 s.8), and `--vault` first re-proves the known
answer on those bars' in-sample part before scoring the vault. The vault is never read here before the joint run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d671_break_construction as C  # noqa: E402

M, X, T = C.M, C.X, C.T
DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")
POWER_OUT = REPO / "data" / "vault_d680_power.json"
VAULT_OUT = REPO / "data" / "vault_d680_vault.json"
FROZEN = REPO / "data" / "FROZEN_vault_d680_nq_compression.json"
SPEC = REPO / "docs" / "decisions" / "D680-PRE-REG-the-nq-compression-break-for-the-joint-vault.md"
CUT, VAULT_END = "2025-03-01", "2026-09-18"
T_VAULT, MIN_VAULT_TRADES, N_VAULT_SESSIONS, BLOCK, REPS, SEED = 1.2816, 30, 390, 20, 2000, 680
PROGRAMME_ALPHA_SLOT = 0.005
KNOWN_JSON = REPO / "data" / "diag_d677_single_count_index.json"  # D672-A1's single-count C1 (reproduced D672 to 1e-9)


class VaultRuleError(RuntimeError):
    pass


def cost_lines() -> dict[str, float]:
    c = M.micro_costs()["NQ"]
    single = 3.0 + c["crossing_ticks"] * c["tick_usd"]
    if abs(c["cost_usd"] - (single + c["tick_usd"])) > 1e-12:
        raise VaultRuleError("the cost file's NQ line is not $3 + crossing + one tick")
    return {"usd_per_point": c["usd_per_point"], "tick": M.TICK_PTS["NQ"], "cost_prereg_usd": c["cost_usd"],
            "cost_single_usd": single, "crossing_ticks": c["crossing_ticks"]}


def book(b: pd.DataFrame, use: Any, R: Any, gex: pd.Series | None) -> tuple[pd.DataFrame, pd.Index]:
    """Every NQ plain break with its tier, at the level and (for the reproduction) with D672's fill ticks. `gex` is
    needed only for the in-sample window (D671's size forecast defined D672's evaluation start)."""
    cl = cost_lines()
    T.MULT.update(M.MULT)
    C._R = R
    tabs = R.session_table(b, use, roots=("NQ",))
    bars = R.bar_arrays(b[b["root"] == "NQ"])
    d = T.root_frame(b, tabs["NQ"], "NQ")
    d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
    d["gd_spx"] = T.gex_prior(gex, d.index) if gex is not None else np.nan
    cal = pd.read_csv(DATA / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
    on = C.overnight(b, "NQ")
    C.overnight_audit(on)
    S_ = C.session_features(d, on, cal[cal["root"] == "NQ"].set_index("day"))
    sess = S_.index.to_numpy()
    p_rv, p_on = C.tiers(S_["rv5"].to_numpy(float)), C.tiers(S_["on_range"].to_numpy(float))
    comp = (p_rv + p_on) / 2
    ctier = C.tiers(comp)
    C.tier_audit(ctier, comp, list(range(0, len(comp), max(1, len(comp) // 12))))
    t671 = np.full(len(sess), np.nan)
    if gex is not None:
        f671, _ = C.size_forecast(S_[list(C.SIZE_FEATS)].to_numpy(float), S_["y"].to_numpy(float))
        t671 = C.tiers(f671)
    rows = []
    for s, rec in d.iterrows():
        bb = bars.get(("NQ", s))
        if bb is None:
            continue
        Lh, Ll, A = float(rec["prior_high"]), float(rec["prior_low"]), float(rec["atr20"])
        X.TICK = cl["tick"]
        p = X.plain_break(bb, Lh, Ll, A)
        if p is None:
            continue
        px, _ = X.exit_trade(bb, p["i"], p["D"], p["entry"], p["L"], A, 0.0, "E4")
        X.TICK = 0.0
        p0 = X.plain_break(bb, Lh, Ll, A)
        if p0 is None or p0["i"] != p["i"] or p0["D"] != p["D"]:
            raise VaultRuleError(f"{s}: the break moved when the fill tick was removed")
        px0, _ = X.exit_trade(bb, p0["i"], p0["D"], p0["entry"], p0["L"], A, 0.0, "E4")
        rows.append({"session": s, "D": p["D"], "entry": p["entry"], "level": p0["entry"],
                     "gross_prereg": p["D"] * (px / p["entry"] - 1) * 1e4, "gross": p0["D"] * (px0 / p0["entry"] - 1) * 1e4})
    X.TICK = cl["tick"]
    tr = pd.DataFrame(rows).sort_values("session").reset_index(drop=True)
    tr["net_prereg"] = tr["gross_prereg"] - cl["cost_prereg_usd"] / cl["usd_per_point"] / tr["entry"] * 1e4
    tr["cost"] = cl["cost_single_usd"] / cl["usd_per_point"] / tr["level"] * 1e4
    tr["net"] = tr["gross"] - tr["cost"]
    for nm, v in (("ctier", ctier), ("t671", t671)):
        tr[nm] = pd.Series(v, index=sess).reindex(tr["session"]).to_numpy()
    return tr, d.index


def known_answer(tr: pd.DataFrame) -> dict[str, Any]:
    j = json.loads(KNOWN_JSON.read_text(encoding="utf-8"))["roots"]["NQ"]["D672_C1"]
    win = np.isfinite(tr["t671"].to_numpy(float)) & np.isfinite(tr["ctier"].to_numpy(float))
    c1 = win & (tr["ctier"].to_numpy(float) < 1 / 3)
    got = {"trades": int(c1.sum()), "net_prereg": float(tr.loc[c1, "net_prereg"].mean()), "net_single": float(tr.loc[c1, "net"].mean()),
           "gross_level": float(tr.loc[c1, "gross"].mean()), "window": [str(tr.loc[win, "session"].min()), str(tr.loc[win, "session"].max())]}
    if got["trades"] != j["trades"] or abs(got["net_prereg"] - j["D672_net"][0]) > 1e-9 or abs(got["net_single"] - j["single_count_net"][0]) > 1e-9:
        raise VaultRuleError(f"known answer: {got} against D672 / D672-A1's {j}")
    return got


def score(g: np.ndarray, net: np.ndarray, R: Any) -> dict[str, Any]:
    n = len(g)
    out: dict[str, Any] = {"trades": n}
    if n < 3:
        return {**out, "verdict": "UNRESOLVED (too few trades)"}
    t, se = R.nw_t(np.asarray(g, float))
    t = float(t)
    out.update({"gross_bp": float(np.mean(g)), "t_gross_hac": t, "net_bp": float(np.mean(net)),
                "p_one_sided": float(stats.norm.sf(t)), "programme_promotion_p_le_0.005": bool(stats.norm.sf(t) <= PROGRAMME_ALPHA_SLOT)})
    if n < MIN_VAULT_TRADES:
        out["verdict"] = "UNRESOLVED (too few trades)"
    elif np.mean(g) > 0 and t >= T_VAULT and np.mean(net) > 0:
        out["verdict"] = "PASS"
    else:
        out["verdict"] = "FAIL"
    return out


def session_table(tr: pd.DataFrame, sessions: pd.Index) -> pd.DataFrame:
    """One row per in-sample session of D672's window: whether C1 traded, its gross and net (0 when not)."""
    win = np.isfinite(tr["t671"].to_numpy(float)) & np.isfinite(tr["ctier"].to_numpy(float))
    c1 = tr[win & (tr["ctier"].to_numpy(float) < 1 / 3)].set_index("session")
    lo = tr.loc[win, "session"].min()
    s = pd.Index([x for x in sessions if lo <= x < CUT])
    return pd.DataFrame({"c1": s.isin(c1.index), "gross": c1["gross"].reindex(s).fillna(0.0).to_numpy(),
                         "cost": c1["cost"].reindex(s).fillna(0.0).to_numpy()}, index=s)


def power(st: pd.DataFrame, R: Any) -> dict[str, Any]:
    """The vault as 390 sessions drawn in 20-session blocks from D672's in-sample window, C1's gross shifted so its mean
    is s x the in-sample's (s = 1: the in-sample edge; s = 0: none)."""
    rng = np.random.default_rng(SEED)
    c1, g, cost = st["c1"].to_numpy(), st["gross"].to_numpy(), st["cost"].to_numpy()
    mu = float(g[c1].mean())
    res: dict[str, Any] = {"in_sample_c1_gross_mean": mu, "in_sample_c1_rate_per_session": float(c1.mean()),
                           "n_vault_sessions": N_VAULT_SESSIONS, "block": BLOCK, "reps": REPS}
    for s_ in (1.0, 0.5, 0.25, 0.0):
        ver, ntr, prom = [], [], []
        for _ in range(REPS):
            idx = np.concatenate([np.arange(k, k + BLOCK) for k in rng.integers(0, len(st) - BLOCK, N_VAULT_SESSIONS // BLOCK + 1)])[:N_VAULT_SESSIONS]
            m = c1[idx]
            gv = g[idx][m] - (1 - s_) * mu
            sc = score(gv, gv - cost[idx][m], R)
            ver.append(sc["verdict"])
            ntr.append(sc["trades"])
            prom.append(bool(sc.get("programme_promotion_p_le_0.005", False)))
        v = pd.Series(ver).value_counts(normalize=True).to_dict()
        res[f"edge_scale={s_:g}"] = {"PASS": float(v.get("PASS", 0.0)), "FAIL": float(v.get("FAIL", 0.0)),
                                     "UNRESOLVED": float(v.get("UNRESOLVED (too few trades)", 0.0)),
                                     "programme_promotion_rate": float(np.mean(prom)),
                                     "trades_median": float(np.median(ntr)), "trades_p10_p90": [float(np.quantile(ntr, 0.1)), float(np.quantile(ntr, 0.9))]}
    return res


def in_sample() -> tuple[pd.DataFrame, pd.Index, Any]:
    b, use, _gd, R = M.load_bars(DATA, False, ("ES", "NQ"))
    dix = pd.read_csv(DATA / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
    gex = dix[dix["date"] < CUT].set_index("date")["gex"].astype(float).sort_index()
    tr, sessions = book(b, use, R, gex)
    return tr, sessions, R


def cut_use(use: Any, cut: str) -> Any:
    if isinstance(use, dict):
        return {k: cut_use(v, cut) for k, v in use.items()}
    if isinstance(use, (list, tuple, set)):
        return type(use)(x for x in use if not isinstance(x, str) or x < cut)
    return use


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def selftest() -> int:
    class _R:
        @staticmethod
        def nw_t(x: np.ndarray) -> tuple[float, float]:
            se = float(np.std(x, ddof=1) / math.sqrt(len(x)))
            return float(np.mean(x) / se), se
    rng = np.random.default_rng(1)
    g = rng.normal(12.0, 45.0, 90)
    if score(g, g - 3.0, _R)["verdict"] != "PASS":
        raise AssertionError("an injected edge did not PASS")
    passes = sum(score(x, x - 3.0, _R)["verdict"] == "PASS" for x in rng.normal(0.0, 45.0, (400, 90)))
    if passes / 400 > 0.15:
        raise AssertionError(f"noise passed {passes / 400:.2f} of the time (bar 0.10 by construction)")
    if score(g[:20], g[:20] - 3.0, _R)["verdict"] != "UNRESOLVED (too few trades)":
        raise AssertionError("fewer than 30 trades did not read UNRESOLVED")
    if score(g, g - 1e3, _R)["verdict"] != "FAIL":
        raise AssertionError("a positive gross with a negative net did not FAIL")
    if main(["--vault-bars", "x.csv", "--vault-use", "u.json"]) != 2:
        raise AssertionError("--vault ran without the principal's word")
    v = rng.normal(size=600)
    try:
        C.tier_audit(C.tiers(v, leak=True), v, [300, 450, 599])
    except C.D671Error:
        pass
    else:
        raise AssertionError("the tier's lag canary did not fire")
    if cut_use({"NQ": ["2025-02-28", "2025-03-03"]}, CUT) != {"NQ": ["2025-02-28"]}:
        raise AssertionError("cut_use")
    print(f"selftest OK: PASS on an edge; noise passed {passes / 400:.3f} (<= 0.15); UNRESOLVED below {MIN_VAULT_TRADES}; FAIL on "
          "a negative net; --vault refused without the principal's word; the tier's lag canary fires")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--known-answer", action="store_true")
    ap.add_argument("--power", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--freeze", action="store_true", help="write the D680 freeze (once)")
    ap.add_argument("--vault-bars", default=None)
    ap.add_argument("--vault-use", default=None)
    ap.add_argument("--principals-word", default=None)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.vault_bars is not None:
        if not (a.principals_word or "").strip():
            print("refused: the vault is read only in the joint run, on the principal's word (A10)")
            return 2
        if not FROZEN.exists():
            raise VaultRuleError("the D680 freeze is missing")
        fz = json.loads(FROZEN.read_text(encoding="utf-8"))
        if fz.get("runner_sha256") != sha(Path(__file__).resolve()) or fz.get("prereg_sha256") != sha(SPEC):
            raise VaultRuleError("this runner or D680 has moved since the freeze")
        if VAULT_OUT.exists():
            raise VaultRuleError("the vault line has already been scored; a second opening is refused")
        R = M.S.load_v2().R
        bv = pd.read_csv(a.vault_bars, encoding="utf-8", dtype={"session": str, "hhmm": str, "et": str})
        uv = json.loads(Path(a.vault_use).read_text(encoding="utf-8"))
        if (bv["session"] > VAULT_END).any():
            raise VaultRuleError("the vault bars hold a session after 2026-09-18")
        dix = pd.read_csv(DATA / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
        gex = dix[dix["date"] < CUT].set_index("date")["gex"].astype(float).sort_index()
        # proof first: the vault-input path's in-sample part reproduces the known answer exactly
        tr_in, _ = book(bv[bv["session"] < CUT].copy(), cut_use(uv, CUT), R, gex)
        ka = known_answer(tr_in)
        tr, _ = book(bv, uv, R, None)
        v = tr[(tr["session"] >= CUT) & (tr["session"] <= VAULT_END)]
        c1 = v["ctier"].to_numpy(float) < 1 / 3
        out = {"principals_word": a.principals_word, "known_answer_reproduced": ka,
               "C1": score(v.loc[c1, "gross"].to_numpy(float), v.loc[c1, "net"].to_numpy(float), R),
               "reported_B0_every_break": score(v["gross"].to_numpy(float), v["net"].to_numpy(float), R),
               "reported_C1_minus_rest_gross": float(v.loc[c1, "gross"].mean() - v.loc[~c1, "gross"].mean()) if c1.any() and (~c1).any() else None}
        VAULT_OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(out, indent=1, default=float))
        return 0
    if a.freeze:
        if FROZEN.exists():
            raise VaultRuleError(f"{FROZEN.name} exists; a freeze is written once (a change needs a new record)")
        ka = json.loads(POWER_OUT.read_text(encoding="utf-8"))["known_answer_in_sample"]
        doc = {"spec": SPEC.name, "prereg_sha256": sha(SPEC), "runner": "scripts/vault_d680_nq_compression.py",
               "runner_sha256": sha(Path(__file__).resolve()),
               "imported_unchanged": {p: sha(REPO / "scripts" / p) for p in ("stage0_d671_break_construction.py", "stage0_d668_break_predictor.py",
                                                                             "stage0_d666_rebreak.py", "stage0_d663_per_root_gamma_break.py")},
               "params": {"t_vault": T_VAULT, "min_vault_trades": MIN_VAULT_TRADES, "tier": "C1 = ctier < 1/3 (D672)",
                          "friction": "at the level, $3 + d508_exec crossing, once (D668-A2)", "cost_lines": cost_lines(),
                          "size": "one MNQ"},
               "known_answer": ka, "vault": [CUT, VAULT_END], "programme_slot": 9, "frozen_date": "2026-09-29",
               "prerequisite_before_the_joint_run": "the vault-input path: D644's fixture built through 2026-09-18 and G0's loader with the cut moved, proved by --vault's own known-answer check",
               "instruction": "the principal, 2026-09-29: \"happy for the NQ compression to stay in queue for the big vault run\"; \"Freeze the ones that where queued today\""}
        FROZEN.write_text(json.dumps(doc, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(doc, indent=1, default=float))
        return 0
    if a.known_answer or a.power:
        t0 = time.time()
        tr, sessions, R = in_sample()
        ka = known_answer(tr)
        if a.known_answer:
            print(json.dumps(ka, indent=1))
            return 0
        res = {"known_answer_in_sample": ka, **power(session_table(tr, sessions), R), "runtime_min": round((time.time() - t0) / 60, 2)}
        POWER_OUT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(res, indent=1, default=float))
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
