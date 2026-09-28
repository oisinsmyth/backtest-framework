"""The NG projected-profit line for the joint vault run (the principal, 2026-09-28: "We need to add this to the vault
then - 'projected MNG >= 2 x $5'"). D649 registers it; this file computes it.

    uv run python scripts/ledger_vault_pp_ng.py --known-answer   # the rule on the spent in-sample (D630's trades)
    uv run python scripts/ledger_vault_pp_ng.py --power          # vault pass rates -> data/ledger_vault_pp_ng_power.json
    uv run python scripts/ledger_vault_pp_ng.py --selftest
    uv run python scripts/ledger_vault_pp_ng.py --vault TRADES.csv --principals-word "..."   # the joint run ONLY

THE RULE, on D630's primary trade (fill at the close of bar t0+1, exit at the close of 14:29, no stop or target):
    b_t   = sum(g_j x I_j) / sum(I_j^2) over every traded day j BEFORE t (the in-sample's 1,028 first, then the vault's
            own earlier traded days), OLS through the origin: the realized pass-through of the ledger's |I|;
    P_t   = b_t x |I_t| x MNG / NG   (projected gross dollars at one MNG; MNG / NG = 1 / 10);
    trade one MNG when D630's gate passes AND P_t >= 2 x $5, i.e. b_t x |I_t| >= $100 at full size.
    |I| is D630's (the square-root form, x_SR); the form is the principal's choice (D648 found x_GM on CL).
g is gross dollars per full contract; one MNG earns g / 10 and pays $5 ($3 + one $1 tick + $1 slippage).

THE VAULT INPUT is D630's own vault trade table (built at the joint run by D630 s.8's code with the cut moved): one
row per vault business day with columns day, traded (D630's gate), absI_usd (|I| x 10,000), g (gross dollars per
full contract, D630's primary). This file never builds or reads vault prices itself; --vault refuses without the
principal's word and without the D649 freeze verifying.
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

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
POWER_OUT = REPO / "data" / "ledger_vault_pp_ng_power.json"
VAULT_OUT = REPO / "data" / "ledger_vault_pp_ng_vault.json"
FROZEN = REPO / "data" / "FROZEN_ledger_vault_pp_ng.json"
SPEC = REPO / "docs" / "decisions" / "D649-PRE-REG-ng-projected-profit-line-for-the-joint-vault.md"
MNG_RATIO, MNG_COST, K = 0.1, 5.0, 2.0
THRESH_FULL = K * MNG_COST / MNG_RATIO  # $100 of projected gross at full size
T_VAULT, MIN_VAULT_TRADES = 1.2816, 15
KNOWN = {"trades": 270, "mng_net_per_trade": 15.43}
SEED = 649


class VaultRuleError(RuntimeError):
    pass


def select(prior_g: np.ndarray, prior_I: np.ndarray, traded: np.ndarray, I: np.ndarray, g: np.ndarray,
           min_prior: int = 100) -> np.ndarray:
    """Point-in-time: for each day in order, b from all EARLIER traded days (the prior sample first), then the
    decision; a traded day's (g, I) joins the estimate only after its own decision."""
    sgI, sII, n = float(np.sum(prior_g * prior_I)), float(np.sum(prior_I ** 2)), len(prior_g)
    take = np.zeros(len(g), bool)
    for t in range(len(g)):
        if not traded[t]:
            continue
        if n >= min_prior and sII > 0:
            take[t] = (sgI / sII) * I[t] >= THRESH_FULL
        sgI += g[t] * I[t]
        sII += I[t] ** 2
        n += 1
    return take


def score(g: np.ndarray, take: np.ndarray) -> dict[str, Any]:
    x = g[take] * MNG_RATIO
    n = int(take.sum())
    out: dict[str, Any] = {"trades": n}
    if n < 2:
        return {**out, "verdict": "UNRESOLVED (too few trades)"}
    se = float(x.std(ddof=1) / math.sqrt(n))
    # identical trades (e.g. every g zero) have no dispersion: the sign of the mean decides, a zero mean is t = 0
    t = float(x.mean() / se) if se > 0 else (0.0 if x.mean() == 0 else math.copysign(math.inf, float(x.mean())))
    out.update({"mng_gross_per_trade": float(x.mean()), "mng_net_per_trade": float(x.mean() - MNG_COST),
                "t_gross": t, "full_gross_per_trade": float(g[take].mean()),
                "full_net_per_trade": float(g[take].mean() - 26.0)})
    if n < MIN_VAULT_TRADES:
        out["verdict"] = "UNRESOLVED (too few trades)"
    elif x.mean() > 0 and t >= T_VAULT and x.mean() - MNG_COST > 0:
        out["verdict"] = "PASS"
    else:
        out["verdict"] = "FAIL"
    return out


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def in_sample() -> pd.DataFrame:
    """D630's in-sample trade table: day, traded, absI_usd, g (full-contract gross), from D630's own runner."""
    X = _load("explore_d630_exits_micro", "explore_d630_exits_micro.py")  # repoints D630's inputs in a worktree
    d = X.R.build(read_returns=True)["d"]
    g = X.R.signed(d)
    return pd.DataFrame({"day": d["day"], "traded": d["traded"].to_numpy() & np.isfinite(g),
                         "absI_usd": d["absI_usd"].to_numpy(float), "g": np.where(np.isfinite(g), g, 0.0)})


def known_answer(t: pd.DataFrame) -> dict[str, Any]:
    tr = t["traded"].to_numpy()
    take = select(np.array([]), np.array([]), tr, t["absI_usd"].to_numpy(), t["g"].to_numpy())
    s = score(t["g"].to_numpy(), take)
    if s["trades"] != KNOWN["trades"] or not math.isclose(s["mng_net_per_trade"], KNOWN["mng_net_per_trade"],
                                                          abs_tol=0.005):
        raise VaultRuleError(f"known answer: {s['trades']} trades, ${s['mng_net_per_trade']:.2f} against the "
                             f"post-hoc record's {KNOWN}")
    return s


def power(t: pd.DataFrame) -> dict[str, Any]:
    """Vault pass rates. The vault is modelled as n_vault days drawn in 20-day blocks from the in-sample trade table
    (its shape: traded share, |I|, g), with the vault's g shrunk toward zero by a factor s (s = 1: the in-sample
    edge; s = 0: none). b_t is warmed on the whole in-sample, as at the joint run."""
    rng = np.random.default_rng(SEED)
    tr, I, g = t["traded"].to_numpy(), t["absI_usd"].to_numpy(), t["g"].to_numpy()
    pI, pg = I[tr], g[tr]
    b_in = float(np.sum(pg * pI) / np.sum(pI ** 2))
    n_days = 390  # 2025-03-01 -> 2026-09-18 business days
    res: dict[str, Any] = {"b_in_sample": b_in, "n_vault_days": n_days, "reps": 2000}
    edge = b_in * I  # the in-sample's own expected move per day, removed then scaled back
    for s in (1.0, 0.5, 0.25, 0.0):
        ver, ntr = [], []
        for _ in range(2000):
            idx = np.concatenate([np.arange(k, k + 20) for k in rng.integers(0, len(t) - 20, n_days // 20 + 1)])[:n_days]
            gv = g[idx] - edge[idx] * (1 - s) * tr[idx]
            take = select(pg, pI, tr[idx], I[idx], gv)
            sc = score(gv, take)
            ver.append(sc["verdict"])
            ntr.append(sc["trades"])
        v = pd.Series(ver).value_counts(normalize=True).to_dict()
        res[f"edge_scale={s:g}"] = {"PASS": float(v.get("PASS", 0.0)), "FAIL": float(v.get("FAIL", 0.0)),
                                    "UNRESOLVED": float(v.get("UNRESOLVED (too few trades)", 0.0)),
                                    "trades_median": float(np.median(ntr)), "trades_p10_p90":
                                    [float(np.quantile(ntr, 0.1)), float(np.quantile(ntr, 0.9))]}
    return res


def selftest() -> int:
    rng = np.random.default_rng(1)
    n = 800
    I = rng.lognormal(4, 1, n)
    tr = rng.random(n) < 0.6
    g_edge = 0.4 * I + rng.standard_normal(n) * 150
    take = select(np.array([]), np.array([]), tr, I, g_edge)
    # point-in-time: the decision on day t must not change when day t's own g changes
    g2 = g_edge.copy()
    k = int(np.flatnonzero(take)[len(np.flatnonzero(take)) // 2])
    g2[k] = -1e6
    if select(np.array([]), np.array([]), tr, I, g2)[k] != take[k]:
        raise AssertionError("select is not point-in-time: a day's own outcome changed its decision")
    later = select(np.array([]), np.array([]), tr, I, g2)
    if np.array_equal(later[k + 1:], take[k + 1:]):
        raise AssertionError("select ignores prior outcomes: a changed past g moved no later decision")
    if score(g_edge, take)["verdict"] != "PASS":
        raise AssertionError("an injected edge did not PASS")
    g_null = rng.standard_normal(n) * 150
    if score(g_null, select(np.array([]), np.array([]), tr, I, g_null))["verdict"] == "PASS":
        raise AssertionError("noise passed")
    if score(g_edge, np.zeros(n, bool) | (np.arange(n) < 5) & tr)["verdict"] != "UNRESOLVED (too few trades)":
        raise AssertionError("fewer than 15 trades did not read UNRESOLVED")
    rc = main(["--vault", "x.csv"])
    if rc != 2:
        raise AssertionError("--vault ran without the principal's word")
    print("selftest OK: point-in-time selection (own outcome ignored, past outcomes used), PASS on an edge, not on "
          "noise, UNRESOLVED below 15 trades, --vault refused without the principal's word")
    return 0


def sha(p: Path) -> str:
    """Text hash, LF-pinned (as the Stage A freeze), so a checkout's line endings cannot fake a drift."""
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--known-answer", action="store_true")
    ap.add_argument("--power", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--vault", default=None)
    ap.add_argument("--principals-word", default=None)
    ap.add_argument("--freeze", action="store_true", help="write the D649 freeze (once)")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.vault is not None:
        if not (a.principals_word or "").strip():
            print("refused: the vault is read only in the joint run, on the principal's word (A10)")
            return 2
        if not FROZEN.exists():
            raise VaultRuleError("the D649 freeze is missing")
        frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
        if frozen.get("runner_sha256") != sha(Path(__file__).resolve()) or frozen.get("prereg_sha256") != sha(SPEC):
            raise VaultRuleError("this runner or D649 has moved since the freeze")
        if VAULT_OUT.exists():
            raise VaultRuleError("the vault line has already been scored; a second opening is refused")
        t = in_sample()
        v = pd.read_csv(a.vault, encoding="utf-8", dtype={"day": str}).sort_values("day")
        if not ((v["day"] >= "2025-03-01") & (v["day"] <= "2026-09-18")).all():
            raise VaultRuleError("the vault table holds a day outside 2025-03-01 -> 2026-09-18")
        tr = t["traded"].to_numpy()
        take = select(t["g"].to_numpy()[tr], t["absI_usd"].to_numpy()[tr], v["traded"].to_numpy(bool),
                      v["absI_usd"].to_numpy(float), v["g"].to_numpy(float))
        out = {"principals_word": a.principals_word, **score(v["g"].to_numpy(float), take)}
        VAULT_OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(out, indent=1))
        return 0
    if a.freeze:
        if FROZEN.exists():
            raise VaultRuleError(f"{FROZEN.name} exists; a freeze is written once (a change needs a new record)")
        doc = {"spec": SPEC.name, "prereg_sha256": sha(SPEC), "runner": "scripts/ledger_vault_pp_ng.py",
               "runner_sha256": sha(Path(__file__).resolve()), "params": {"k": K, "mng_cost": MNG_COST,
               "mng_ratio": MNG_RATIO, "threshold_full_usd": THRESH_FULL, "t_vault": T_VAULT,
               "min_vault_trades": MIN_VAULT_TRADES, "min_prior": 100, "form": "x_SR (D630's |I|)"},
               "vault": ["2025-03-01", "2026-09-18"], "programme_slot": 8, "frozen_date": "2026-09-28",
               "instruction": "the principal, 2026-09-28: \"We need to add this to the vault then - 'projected MNG >= 2 x $5'\""}
        FROZEN.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(doc, indent=1))
        return 0
    t = in_sample()
    if a.known_answer:
        print(json.dumps(known_answer(t), indent=1))
        return 0
    if a.power:
        ka = known_answer(t)
        res = {"known_answer_in_sample": ka, **power(t)}
        POWER_OUT.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(res, indent=1))
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
