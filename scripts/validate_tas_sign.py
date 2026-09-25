"""D626: a TAS premium goes with net SELLING in the settlement window. The confirmation, on data no one has read.

The spec is `docs/decisions/D626-PRE-REG-a-TAS-premium-goes-with-selling-in-the-window.md`, committed alone in
`9ee8142` before this file existed. D625's runner supplies the session builder (the traded contract, the matching
TAS month, T1/T2, the truth) and Cohen's kappa. D624's runner supplies the loaders and K1.

    python -W error::RuntimeWarning scripts/validate_tas_sign.py --gate    # once, after the 2026-10-10 top-up
    python scripts/validate_tas_sign.py --check | --selftest

It uses the SYSTEM interpreter (databento).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "ledger_tas_sign_validation.json"
BAR, NEAR_MISS, MIN_POOLED, CTRL = 0.20, 0.10, 45, 0.20
SEED = 626
SIBLING_YEAR_END = "2026-09-18"
#: Changes made after the first run. None yet.
DEVIATIONS: list[str] = []


def _load(name: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


T = _load("validate_tas_premium")
V = T.V


class D626Error(RuntimeError):
    pass


def unseen_guard(df: pd.DataFrame, roots: tuple[str, ...]) -> None:
    """§3: no HO/RB row from D625's sibling year (to 2026-09-18) may be read."""
    hit = df[df["symbol"].str[:2].isin(roots) & (df["day"] <= SIBLING_YEAR_END)]
    if len(hit):
        raise D626Error(f"{len(hit)} {roots} rows dated on or before {SIBLING_YEAR_END} (D625's SEEN year) are in memory")


def frames() -> dict[str, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
    """(outright trades, outright bars, TAS trades, TAS bars) for the CL/NG and HO/RB groups."""
    if not V.TOPUP_JOBS.exists():
        raise D626Error(f"{V.TOPUP_JOBS.name} is absent: D626 is read once, after the top-up")
    cl_tr = V._files(V.FREE_JOBS, "trades-post-vault") + V._files(V.TOPUP_JOBS, "topup-trades")
    cl_bar = V._files(V.TOPUP_JOBS, "topup-ohlcv1s")
    sib_tr = V._files(V.TOPUP_JOBS, "topup-sib-trades")
    sib_bar = V._files(V.TOPUP_JOBS, "topup-sib-ohlcv1s")
    out = {}
    for group, (tr, bar) in {"CL/NG": (cl_tr, cl_bar), "HO/RB": (sib_tr, sib_bar)}.items():
        ot = T.cached_load(tr, V.RE_OUT, V.PRE_FROM, V.W1)
        ob = T.cached_load(bar, V.RE_OUT, V.W0, V.W1)
        tt, tb = T.tas_span(tr, V.W1), T.tas_span(bar, V.W1)
        out[group] = (ot, ob, tt, tb)
    for df in out["CL/NG"][:2]:
        V.vault_guard(df, ("CL", "NG"))
    for df in out["CL/NG"][2:]:
        V.vault_guard(df.assign(symbol=df["symbol"].str[:2]), ("CL", "NG"))
    for df in out["HO/RB"][:2]:
        unseen_guard(df, ("HO", "RB"))
    for df in out["HO/RB"][2:]:
        unseen_guard(df.assign(symbol=df["symbol"].str[:2]), ("HO", "RB"))
    return out


def verdict(pooled: dict[str, Any], per: dict[str, dict[str, Any]]) -> str:
    k, n = pooled["kappa"], pooled["n"]
    if k is None or n < MIN_POOLED:
        return f"UNRESOLVED (fewer than {MIN_POOLED} pooled sessions)"
    cl_ng_ok = all(per[r]["kappa"] is not None and per[r]["kappa"] > 0 for r in ("CL", "NG"))
    if k >= BAR:
        return "PASS" if cl_ng_ok else "UNRESOLVED (pooled passes, but CL or NG has kappa <= 0)"
    return "UNRESOLVED (near miss)" if k >= NEAR_MISS else "FAIL"


def gate() -> dict[str, Any]:
    fr = frames()
    out: dict[str, Any] = {"k1": {}, "roots": {}}
    per_df: dict[str, pd.DataFrame] = {}
    for group, (ot, ob, tt, tb) in fr.items():
        out["k1"][group] = {"outright_window": V.k1(ob, ot), "tas": T.k1_tas(tb, tt)}
        roots = ("CL", "NG") if group == "CL/NG" else ("HO", "RB")
        for root in roots:
            df = T.sessions(ob, ot, tb, tt, root, "rule" if group == "CL/NG" else "most_active")
            if "excluded" not in df.columns:
                df["excluded"] = None
            per_df[root] = df
    usable = {r: T._usable(df).reset_index(drop=True) for r, df in per_df.items()}
    per = {}
    for r, u in usable.items():
        m = -u["W_T1"]
        rr = float(np.corrcoef(m, u["truth_W"])[0, 1]) if len(u) >= 4 and m.std() > 0 and u["truth_W"].std() > 0 else None
        per[r] = {**T.kappa(m, u["truth_W"]), "pearson_r": None if rr is None else round(rr, 4),
                  "kappa_d625_sign": T.kappa(u["W_T1"], u["truth_W"])["kappa"],
                  "kappa_T2_reversed": T.kappa(-u["W_T2"], u["truth_W"])["kappa"],
                  "excluded": per_df[r][per_df[r]["excluded"].notna()][["day", "excluded"]].to_dict("records")}
    allu = pd.concat(usable.values(), ignore_index=True)
    pooled = T.kappa(-allu["W_T1"], allu["truth_W"])
    # controls, pooled: the day shift within each root, and random signs
    sh_m = pd.concat([-u["W_T1"].iloc[:-1] for u in usable.values()], ignore_index=True)
    sh_t = pd.concat([u["truth_W"].iloc[1:] for u in usable.values()], ignore_index=True)
    c1 = T.kappa(sh_m, sh_t)
    rng = np.random.default_rng(SEED)
    c2 = T.kappa(pd.Series(rng.choice([-1.0, 1.0], size=len(allu))), allu["truth_W"])
    for name, c in (("C1 day shift", c1), ("C2 random signs", c2)):
        if c["kappa"] is None or abs(c["kappa"]) >= CTRL:
            raise D626Error(f"{name} failed: pooled kappa {c['kappa']}")
    out.update({"pooled": pooled, "per_root": per, "verdict": verdict(pooled, per),
                "controls": {"c1_day_shift": c1, "c2_random_sign": c2},
                "sessions": {r: df.to_dict("records") for r, df in per_df.items()}})
    return out


def selftest() -> None:
    k = T.kappa(pd.Series([1.0, -1.0, 1.0, -1.0]), pd.Series([1.0, -1.0, 1.0, -1.0]))
    if k["kappa"] != 1.0:
        raise D626Error(f"selftest: perfect agreement gave kappa {k}")
    try:
        unseen_guard(pd.DataFrame({"symbol": ["HOX6"], "day": ["2026-09-18"]}), ("HO", "RB"))
    except D626Error:
        pass
    else:
        raise D626Error("selftest: the unseen guard did not fire on a sibling-year row")
    unseen_guard(pd.DataFrame({"symbol": ["HOX6"], "day": ["2026-09-21"]}), ("HO", "RB"))
    pooled = {"kappa": 0.25, "n": 60}
    if verdict(pooled, {"CL": {"kappa": 0.1}, "NG": {"kappa": -0.05}}) != "UNRESOLVED (pooled passes, but CL or NG has kappa <= 0)":
        raise D626Error("selftest: CL/NG > 0 condition not enforced")
    if verdict({"kappa": 0.25, "n": 40}, {"CL": {"kappa": 0.3}, "NG": {"kappa": 0.3}}).startswith("PASS"):
        raise D626Error("selftest: the pooled-session floor not enforced")
    print("[selftest] kappa known answer; the unseen guard fires; the CL/NG and floor rules hold")


def _dump(doc: dict[str, Any]) -> str:
    return json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    for f in ("--gate", "--check", "--selftest"):
        ap.add_argument(f, action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        selftest()
        return 0
    head = {"spec": "D626; docs/decisions/D626-PRE-REG-a-TAS-premium-goes-with-selling-in-the-window.md (9ee8142)"}
    if a.check:
        doc = json.loads(OUT.read_text(encoding="utf-8"))
        if _dump({**head, "deviations": DEVIATIONS, "gate": gate()}) != OUT.read_text(encoding="utf-8"):
            raise D626Error(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte ({doc['gate']['verdict']})")
        return 0
    if not a.gate:
        ap.print_help()
        return 2
    if OUT.exists():
        raise D626Error(f"{OUT.name} exists: D626's gate is read ONCE. Use --check to reproduce it.")
    doc = {**head, "deviations": DEVIATIONS, "gate": gate()}
    OUT.write_text(_dump(doc), encoding="utf-8", newline="\n")
    g = doc["gate"]
    print("pooled", g["pooled"], "->", g["verdict"])
    for r, x in g["per_root"].items():
        print(f"  {r}: kappa {x['kappa']} n {x['n']} agreement {x['agreement']} chance {x['chance']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
