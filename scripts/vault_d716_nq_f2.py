"""D716: NQ F2 for the joint vault run, with a fixed-sequence takeover by the agreement book (NQ F2 only when ES F2
takes the same side). Spec: docs/decisions/D716-PRE-REG-nq-f2-for-the-joint-vault.md (3cb79b6b).

    uv run python scripts/vault_d716_nq_f2.py --selftest
    uv run python scripts/vault_d716_nq_f2.py --known-answer
    uv run python scripts/vault_d716_nq_f2.py --power          # also writes the in-sample known answers
    uv run python scripts/vault_d716_nq_f2.py --freeze         # once
    uv run python scripts/vault_d716_nq_f2.py --vault --principals-word "..."   # the joint run only

STEP 1 (the family's full slot alpha): NQ F2 PASS with >= 30 trades on 2024-01-01 -> 2026-09-18, mean net > 0 and
one-sided NW(5) t >= 1.2816. STEP 2, only if step 1 passes: the agreement book A replaces NQ F2 iff (ii) A's net t >=
2.576 on >= 30 trades and (iii) A beats count-matched random deletion of NQ F2's unseen trades on direction efficiency
(D714's INCREMENT rule, 20,000 draws, seed 716). The construction is D711's code at 15:30 on NQ and ES, unchanged.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Callable, Iterator

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import diag_d714_drawdown_null as DD  # noqa: E402
import stage1_d711_f2_mechanism as M  # noqa: E402
import stage1_d714_nq_when_es_agrees as S  # noqa: E402

V, E, D = M.V, M.E, M.D
SPEC = REPO / "docs" / "decisions" / "D716-PRE-REG-nq-f2-for-the-joint-vault.md"
FROZEN = REPO / "data" / "FROZEN_vault_d716_nq_f2.json"
POWER_OUT = REPO / "data" / "vault_d716_power.json"
VAULT_OUT = REPO / "data" / "vault_d716_nq_f2_result.json"
HASHED = ("stage1_d711_f2_mechanism.py", "stage1_d714_nq_when_es_agrees.py", "diag_d714_drawdown_null.py",
          "diag_d711_trims_and_overlap.py", "vault_d707_last_hour_f2.py", "stage1_d703_last_hour_ep_filter.py",
          "diag_d702_last_hour_oracle_mes.py", "stage0_d618_sharpened_ladder.py", "stage0_d671_break_construction.py",
          "stage0_d691_iv_size.py", "stage1_d694_coiled_break.py", "stage0_d668_break_predictor.py")
IN_END, UNSEEN_FROM, VAULT_FROM, VAULT_END, B_START = "2023-12-29", "2024-01-01", "2025-03-01", "2026-09-18", "2018-05-14"
T_TAKE, T_PROMO_TWO_SIDED = 2.576, 2.807
N_DRAW, SEED = 20000, 716
N_UNSEEN, WIN = 130, 640
KNOWN_NQ = {"trades": 274, "mean_net": 20.67010517126089}
KNOWN_B, KNOWN_A = 271, {"trades": 216, "mean_net": 25.57871222722195}


class D716Error(RuntimeError):
    pass


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


@contextlib.contextmanager
def raised_seal() -> Iterator[None]:
    """Move D711's module seal past the vault's end for the vault build only, and put it back whatever happens."""
    old = M.SEAL
    M.SEAL = "2026-09-19"
    try:
        yield
    finally:
        M.SEAL = old


# ================================================================================ the build
def build(end: str = IN_END, vault_open: bool = False) -> dict[str, Any]:
    if end > IN_END and not vault_open:
        raise D716Error(f"seal: a build through {end} was asked for outside --vault")
    with (raised_seal() if vault_open else contextlib.nullcontext()):
        Le, Ln = M.load_root("ES", end), M.load_root("NQ", end)
    Xe, Xn = M.clock_frame(Le, M.ANCHOR), M.clock_frame(Ln, M.ANCHOR)
    if not vault_open and (max(Xe.index.max(), Xn.index.max()) >= UNSEEN_FROM):
        raise D716Error("seal: a session on or after 2024-01-01 reached the build")
    Fe, Fn = M.f2_on(Xe), M.f2_on(Xn)
    V.audit_tiers(Xe, Fe)
    V.audit_tiers(Xn, Fn)
    es_take = pd.Series(Fe["take"] & Fe["window"], index=Xe.index)
    es_side = pd.Series(Xe["side"].to_numpy(float), index=Xe.index)
    agree = (es_take.reindex(Xn.index).fillna(False).to_numpy(bool)
             & (es_side.reindex(Xn.index).to_numpy() == Xn["side"].to_numpy(float)))
    return {"Xe": Xe, "Fe": Fe, "Xn": Xn, "Fn": Fn, "agree": agree, "sn": Xn.index.to_numpy(str),
            "net": Xn["gross"].to_numpy(float) - Xn.attrs["cost"]}


def masks(bd: dict[str, Any], lo: str, hi: str) -> tuple[np.ndarray, np.ndarray]:
    sn, Fn = bd["sn"], bd["Fn"]
    B = Fn["take"] & Fn["window"] & (sn >= lo) & (sn <= hi)
    return B, B & bd["agree"]


def in_sample_answers(bd: dict[str, Any]) -> dict[str, Any]:
    sn, net, Fn = bd["sn"], bd["net"], bd["Fn"]
    own = Fn["take"] & Fn["window"] & (sn <= IN_END)
    B, A = masks(bd, B_START, IN_END)
    return {"nq_own_window": {"trades": int(own.sum()), "mean_net": float(net[own].mean()),
                              "take_sessions_sha256": V.take_hash(sn[own])},
            "B": {"trades": int(B.sum()), "mean_net": float(net[B].mean())},
            "A": {"trades": int(A.sum()), "mean_net": float(net[A].mean()), "take_sessions_sha256": V.take_hash(sn[A])},
            "es_f2": V.in_sample_answer(bd["Xe"], bd["Fe"])}


def check_known(ka: dict[str, Any]) -> None:
    o, b, a = ka["nq_own_window"], ka["B"], ka["A"]
    if o["trades"] != KNOWN_NQ["trades"] or abs(o["mean_net"] - KNOWN_NQ["mean_net"]) > 1e-9:
        raise D716Error(f"D711's NQ book is not reproduced: {o}")
    if b["trades"] != KNOWN_B or a["trades"] != KNOWN_A["trades"] or abs(a["mean_net"] - KNOWN_A["mean_net"]) > 1e-9:
        raise D716Error(f"D714's books are not reproduced: B {b}, A {a}")
    fz = json.loads(V.FROZEN.read_text(encoding="utf-8"))["known_answer_in_sample_own_window"]
    if ka["es_f2"]["take_sessions_sha256"] != fz["take_sessions_sha256"] or abs(ka["es_f2"]["mean_net"] - fz["mean_net"]) > 1e-9:
        raise D716Error("D707's frozen ES F2 answer is not reproduced")


# ================================================================================ the test (s.4)
def primary(net_b: np.ndarray) -> dict[str, Any]:
    r = V.score(net_b)
    if "t_net_hac" in r:
        r["programme_promotion_two_sided_2807"] = bool(r["mean_net"] > 0 and r["t_net_hac"] >= T_PROMO_TWO_SIDED)
    return r


def takeover(step1: dict[str, Any], net_b: np.ndarray, in_a: np.ndarray, n_draw: int = N_DRAW, seed: int = SEED) -> dict[str, Any]:
    """Step 2. `in_a` flags B's trades that are agreement trades. Refuses unless step 1 passed (the fixed sequence)."""
    if step1.get("verdict") != "PASS":
        raise D716Error("the takeover is tested only if step 1 PASSES (the fixed sequence, s.4)")
    net_a = net_b[in_a]
    sec = V.score(net_a)
    ii = bool(sec.get("trades", 0) >= V.MIN_TRADES and sec.get("mean_net", -1) > 0 and sec.get("t_net_hac", -9) >= T_TAKE)
    ef, mu = S.null(net_b, int(in_a.sum()), n_draw, seed)
    p95, se = float(np.quantile(ef, 0.95)), S.p95_se(ef)
    v3 = S.verdict(S.efficiency(net_a), float(net_a.mean()), float(net_b.mean()), p95, se)
    return {"secondary": sec, "ii_t_at_least_2576": ii,
            "iii_beats_random_deletion": {"verdict": v3, "efficiency_A": S.efficiency(net_a), "efficiency_B": S.efficiency(net_b),
                                          "null_p50": float(np.median(ef)), "null_p95": p95, "p95_bootstrap_se": se,
                                          "rank": float((ef < S.efficiency(net_a)).mean()),
                                          "mean_net_rank_reported": float((mu < net_a.mean()).mean())},
            "takes_over": bool(ii and v3 == "INCREMENT")}


def family(net_b: np.ndarray, in_a: np.ndarray, n_draw: int = N_DRAW, seed: int = SEED) -> dict[str, Any]:
    s1 = primary(net_b)
    out: dict[str, Any] = {"step1_nq_f2": s1}
    if s1.get("verdict") == "PASS":
        out["step2_takeover"] = takeover(s1, net_b, in_a, n_draw, seed)
        out["result"] = "THE AGREEMENT BOOK" if out["step2_takeover"]["takes_over"] else "NQ F2"
    else:
        out["step2_takeover"] = None
        out["result"] = "UNRESOLVED" if str(s1.get("verdict", "")).startswith("UNRESOLVED") else s1["verdict"]
    return out


# ================================================================================ power (s.6)
def power(bd: dict[str, Any]) -> dict[str, Any]:
    sn, net, Fn = bd["sn"], bd["net"], bd["Fn"]
    B, A = masks(bd, B_START, IN_END)
    M_B = float(net[B].mean())
    rng = np.random.default_rng(7161)
    pool = net[B] - M_B
    draws = pool[rng.integers(0, len(pool), (20000, N_UNSEEN))]
    t = V.nw_t_rows(draws)
    for i in (0, 1, 19999):
        if not math.isclose(t[i], D.nw_t(draws[i])[0], rel_tol=1e-12, abs_tol=1e-12):
            raise D716Error("the vectorised NW t differs from nw_t")
    size = float(((draws.mean(axis=1) > 0) & (t >= V.T_PASS)).mean())
    wi = np.flatnonzero(Fn["window"] & (sn >= B_START) & (sn <= IN_END))
    starts = list(range(0, len(wi) - WIN + 1, 5))
    lines = {}
    for s_ in (1.0, 0.5, 0.25, 0.0):
        p1 = tk = 0
        nb, na = [], []
        for w, st in enumerate(starts):
            idx = wi[st:st + WIN]
            kb = idx[Fn["take"][idx]]
            x = net[kb] - (1 - s_) * M_B
            in_a = bd["agree"][kb]
            f = family(x, in_a, 1000, 71600 + w)
            nb.append(len(x))
            na.append(int(in_a.sum()))
            p1 += f["step1_nq_f2"].get("verdict") == "PASS"
            tk += f["result"] == "THE AGREEMENT BOOK"
        lines[f"{int(s_ * 100)}pct"] = {"primary_pass": p1 / len(starts), "takeover": tk / len(starts),
                                        "takeover_given_pass": (tk / p1) if p1 else None,
                                        "trades_B_median": float(np.median(nb)), "trades_A_median": float(np.median(na))}
    return {"effect_in_sample_mean_net_B": M_B, "size_check": {"draws": 20000, "trades_a_draw": N_UNSEEN,
                                                               "pass_rate_at_zero": size, "bar": 0.12, "ok": bool(size <= 0.12)},
            "windows": {"candidates_a_window": WIN, "step": 5, "count": len(starts),
                        "independent_approx": round(len(wi) / WIN, 2), "lines": lines,
                        "note": "every NQ trade is shifted by the same dollars, so A's increment over B is kept as observed"}}


# ================================================================================ reports
def report(bd: dict[str, Any], lo: str, hi: str, arm: pd.Series | None) -> dict[str, Any]:
    sn, net, Xn = bd["sn"], bd["net"], bd["Xn"]
    B, A = masks(bd, lo, hi)
    years = max((pd.Timestamp(hi) - pd.Timestamp(lo)).days / 365.25, 1e-9)
    span = bd["Fn"]["window"] & (sn >= lo) & (sn <= hi)
    s_T = float(Xn["gross"].to_numpy(float)[span].std(ddof=1))
    out = S.books(Xn["gross"].to_numpy(float), {"A_agreement": A, "B_nq_f2": B, "dropped": B & ~A}, sn,
                  Xn["side"].to_numpy(float), Xn.attrs["cost"], years, arm, s_T)
    se_ = bd["Xe"].index.to_numpy(str)
    es_m = bd["Fe"]["take"] & bd["Fe"]["window"] & (se_ >= lo) & (se_ <= hi)
    with M.cost_as(M.ES_COST):
        out["es_f2_reported_only"] = E.book(bd["Xe"]["gross"].to_numpy(float), es_m, se_, bd["Xe"]["side"].to_numpy(float), years, arm)
    x = net[B]
    ys = pd.Series(x, index=sn[B]).groupby(lambda s: s[:4]).sum()
    out["concentration_B"] = {"max_year_share": float(ys.max() / x.sum()) if x.sum() > 0 else None,
                              "max_year": str(ys.idxmax()) if len(ys) else None,
                              "positive_years": f"{int((ys > 0).sum())} of {len(ys)}"}
    if A.sum() > 5:
        d = DD.draws(net[B], int(A.sum()), 5000, SEED + 1)
        out["drawdown_A_vs_random"] = {"A": DD.max_dd(net[A]), "null_p50": float(np.median(d["dd"])),
                                       "share_of_draws_at_or_below": float((d["dd"] <= DD.max_dd(net[A])).mean())}
    return out


# ================================================================================ modes
def vault(word: str | None) -> int:
    if not (word or "").strip():
        print("refused: the vault is read only in the joint run, on the principal's word (A10; D716 s.8)")
        return 2
    if not FROZEN.exists():
        raise D716Error("the D716 freeze is missing")
    fz = json.loads(FROZEN.read_text(encoding="utf-8"))
    if fz.get("runner_sha256") != sha(Path(__file__).resolve()) or fz.get("prereg_sha256") != sha(SPEC):
        raise D716Error("this runner or D716 has moved since the freeze")
    for p, h in fz["imported_unchanged"].items():
        if sha(REPO / "scripts" / p) != h:
            raise D716Error(f"{p} has moved since the freeze")
    if VAULT_OUT.exists():
        raise D716Error("the unseen span has already been scored; a second opening is refused")
    E.sign_audit()
    bd = build(VAULT_END, vault_open=True)
    ka = in_sample_answers(bd)
    check_known(ka)  # prefix stability: the extended build's in-sample part is the frozen one
    for k in ("nq_own_window", "A"):
        if ka[k]["take_sessions_sha256"] != fz["known_answers"][k]["take_sessions_sha256"]:
            raise D716Error(f"prefix stability: {k}'s in-sample take sessions moved")
    B, A = masks(bd, UNSEEN_FROM, VAULT_END)
    net = bd["net"]
    fam = family(net[B], bd["agree"][B])
    arm = E.P694.arm_daily()
    parts = {}
    for nm, lo, hi in (("held_slice", UNSEEN_FROM, "2025-02-28"), ("vault", VAULT_FROM, VAULT_END)):
        b_, a_ = masks(bd, lo, hi)
        parts[nm] = {"B": V.score(net[b_]), "A": V.score(net[a_])}
    out = {"principals_word": word, "known_answers_reproduced": ka, "family": fam, "parts": parts,
           "report": report(bd, UNSEEN_FROM, VAULT_END, arm if len(arm) else None),
           "last_sessions": {"NQ": str(bd["sn"][-1]), "ES": str(bd["Xe"].index[-1])}}
    VAULT_OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"result": fam["result"], "step1": fam["step1_nq_f2"], "parts": parts}, indent=1, default=float))
    return 0


def freeze() -> int:
    if FROZEN.exists():
        raise D716Error(f"{FROZEN.name} exists; a freeze is written once (a change needs a new record)")
    pw = json.loads(POWER_OUT.read_text(encoding="utf-8"))
    if not pw["power"]["size_check"]["ok"]:
        raise D716Error("the size check failed (s.6): nothing is frozen; the principal is told")
    doc = {"spec": SPEC.name, "prereg_sha256": sha(SPEC), "runner": "scripts/vault_d716_nq_f2.py",
           "runner_sha256": sha(Path(__file__).resolve()), "imported_unchanged": {p: sha(REPO / "scripts" / p) for p in HASHED},
           "params": {"primary": "NQ F2, one MNQ, $4.07; PASS >= 30 trades, net > 0, NW(5) t >= 1.2816",
                      "takeover": "only if step 1 PASSES: A's net t >= 2.576 on >= 30 trades AND D714's INCREMENT rule on direction efficiency (20,000 draws, seed 716)",
                      "promotion": "flagged at one-sided 2.576 and at 2.807"},
           "known_answers": pw["known_answers"], "power": pw["power"], "unseen": [UNSEEN_FROM, VAULT_END],
           "programme_slot": 7, "frozen_date": "2026-09-30",
           "withdrawn": "ES F2 (D707) withdrawn before any look; slot 7 released from it; D707's --vault must never be run",
           "instruction": "the principal, 2026-09-30: \"Remove ES F2 from the vault run and keep NQ F2 and NQ F2 only when ES F2 agrees\"; \"Ok I agree with your recommendations, write it up please.\""}
    FROZEN.write_text(json.dumps(doc, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("prereg_sha256", "runner_sha256", "programme_slot")}, indent=1))
    return 0


def selftest() -> int:
    fired: list[str] = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except D716Error:
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")
    rng = np.random.default_rng(716)
    must_raise("a takeover asked for when step 1 did not pass",
               lambda: takeover({"verdict": "FAIL"}, rng.normal(0, 100, 130), np.ones(130, bool), 100, 1))
    must_raise("a build past 2023-12-29 outside --vault", lambda: build(VAULT_END))
    old = M.SEAL
    with contextlib.suppress(ValueError):
        with raised_seal():
            if M.SEAL != "2026-09-19":
                raise SystemExit("selftest: raised_seal did not move the seal")
            raise ValueError
    if M.SEAL != old:
        raise SystemExit("selftest: raised_seal did not restore the seal")
    if main(["--vault"]) != 2:
        raise SystemExit("selftest: --vault ran without the principal's word")
    # a planted label that drops the losers takes over when the primary passes
    x = rng.normal(22, 130, 400)
    lab = np.ones(400, bool)
    lab[np.argsort(x)[:80]] = False
    f = family(x, lab, 2000, 3)
    if f["result"] != "THE AGREEMENT BOOK":
        raise SystemExit(f"selftest: a loser-dropping label did not take over ({f['result']})")
    if family(x - 40, lab, 200, 3)["result"] != "FAIL":
        raise SystemExit("selftest: a losing primary did not FAIL")
    if family(x[:20], lab[:20], 200, 3)["result"] != "UNRESOLVED":
        raise SystemExit("selftest: fewer than 30 trades did not read UNRESOLVED")
    # a random label takes over rarely, given a strongly passing primary
    hits, worlds = 0, 100
    for _ in range(worlds):
        y = rng.normal(40, 130, 300)
        f = family(y, rng.random(300) < 0.8, 1000, int(rng.integers(1e9)))
        hits += f["result"] == "THE AGREEMENT BOOK"
    if hits / worlds > 0.10:
        raise SystemExit(f"selftest: a random label took over in {hits / worlds:.2f} of worlds")
    print(f"selftest OK: {len(fired)} canaries fired: {fired}; raised_seal moves and restores; --vault refused without the "
          f"word; a loser-dropping label takes over; a losing primary FAILs; < 30 reads UNRESOLVED; a random label took "
          f"over in {hits / worlds:.2f} of {worlds} worlds with a passing primary. The known answers run in --known-answer.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--known-answer", action="store_true")
    ap.add_argument("--power", action="store_true")
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--vault", action="store_true")
    ap.add_argument("--principals-word", default=None)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.vault:
        return vault(a.principals_word)
    if a.freeze:
        return freeze()
    if a.known_answer or a.power:
        t0 = time.time()
        E.sign_audit()
        bd = build(IN_END)
        ka = in_sample_answers(bd)
        check_known(ka)
        if a.known_answer:
            print(json.dumps(ka, indent=1, default=float))
            return 0
        arm = E.P694.arm_daily()
        arm = arm[arm.index <= IN_END]
        B, A = masks(bd, B_START, IN_END)
        res = {"known_answers": ka, "power": power(bd),
               "in_sample_family_reported": family(bd["net"][B], bd["agree"][B]),
               "in_sample_report": report(bd, B_START, IN_END, arm), "runtime_min": round((time.time() - t0) / 60, 2)}
        POWER_OUT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({"known": ka, "size_check": res["power"]["size_check"], "windows": res["power"]["windows"],
                          "in_sample_family": res["in_sample_family_reported"]["result"]}, indent=1, default=float))
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
