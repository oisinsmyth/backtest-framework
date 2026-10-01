"""D734: the assembled book NQ F2 + the NQ compression break, one MNQ each, as pre-registered in
docs/decisions/D734-PRE-REG-the-nq-f2-and-compression-book-for-the-joint-vault.md (09b7e2a0).

    uv run python scripts/vault_d734_nq_book.py --selftest
    uv run python scripts/vault_d734_nq_book.py --rehearse     # in-sample 2018-05-14 -> 2023-12-29 (D734 s.3.4), under D734-A1

THIS COMMIT HOLDS THE IN-SAMPLE REHEARSAL ONLY. The vault mode (rebuilding both parts' vault trades through their frozen
functions after D716's --vault and D680's joint-wrapper --run-vault, reproducing their recorded results exactly) is
built, rehearsed and frozen before the joint run (AITODO); there is no --vault here, so nothing can open the vault.

The rehearsal runs the book's gates on the in-sample span through the same code paths the vault mode will use:
F from D716's `build` + `masks` (book B), C from D680's frozen `in_sample` + `known_answer`. It must reproduce D732's
F and C daily totals. Gates: G1 each part's own criterion (D716 `primary`, D680 `score`) on the span; G2 book net > 0;
G3 net > 0 in each half of the sessions; G4 hurdle P on $50k at the topstep_50k / mffu_rapid_50k intersection.
Writes data/rehearsal_d734_nq_book.json (aggregates only).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
from backtest_framework.validation import hurdle_p as H  # noqa: E402

LO, HI, SEAL = "2018-05-14", "2023-12-29", "2024-01-01"
OUT_REHEARSAL_V1 = REPO / "data" / "rehearsal_d734_nq_book.json"      # the first rehearsal (before D734-A1), kept
OUT_REHEARSAL = REPO / "data" / "rehearsal_d734_nq_book_a1.json"     # the re-run under D734-A1
P3_CAP_FRACTION, P3B_BAR = 0.02, 0.33
VENUES = ("topstep_50k", "mffu_rapid_50k")
ACCOUNT, TRAIL = 50_000.0, 2_000.0
P4_COST_VENUE = "mffu_rapid_50k"        # topstep_50k's plan (fees) is not recorded in data/prop_venues.json
EXIT_ET = "16:00"                       # both parts are flat at the close at the latest (D716 s.1; D680 E4)
NQ_USD_PP = 2.0
D732_F_TOTAL = 5628.310180              # D732's F (load_lines L2) total on the span, to the cent
TOL = 1e-6


class D734Error(AssertionError):
    pass


def need(c: bool, msg: str) -> None:
    if not c:
        raise D734Error(msg)


def seal(days, what: str) -> None:
    d = np.asarray(days, dtype=str)
    need(not (d >= SEAL).any(), f"[SEAL] {what}: a session dated >= {SEAL}")


# ------------------------------------------------------------------------------------------------ the parts
def part_f() -> tuple[pd.DataFrame, dict]:
    """F through D716's own build + masks on the span (book B), exactly the path its vault run takes."""
    import vault_d716_nq_f2 as F
    bd = F.build()                                   # IN_END, vault closed
    B, _A = F.masks(bd, LO, HI)
    sess = np.asarray(bd["sn"], dtype=str)[B]
    net = np.asarray(bd["net"], dtype=float)[B]
    seal(sess, "F")
    crit = F.primary(net)
    return pd.DataFrame({"session": sess, "net": net}), crit


def part_c() -> tuple[pd.DataFrame, dict, dict]:
    """C through D680's frozen in-sample function, C1 mask, single-count net to dollars at one MNQ; cut to the span."""
    import vault_d680_nq_compression as V
    tr, _s, R = V.in_sample()
    ka = V.known_answer(tr)
    win = np.isfinite(tr["t671"].to_numpy(float)) & np.isfinite(tr["ctier"].to_numpy(float))
    c1 = win & (tr["ctier"].to_numpy(float) < 1 / 3)
    need(int(c1.sum()) == ka["trades"], "[C] the C1 mask differs from D680's known answer")
    x = tr[c1]
    x = x[x["session"].astype(str) <= HI]
    seal(x["session"].astype(str), "C")
    crit = V.score(x["gross"].to_numpy(float), x["net"].to_numpy(float), R)
    usd = x["net"].to_numpy(float) / 1e4 * x["entry"].to_numpy(float) * NQ_USD_PP
    return pd.DataFrame({"session": x["session"].astype(str).to_numpy(), "net": usd}), crit, ka


def calendar() -> np.ndarray:
    import diag_d722_conditioners as DC
    p = DC.load_conditioners().reset_index()
    s = np.sort(p.loc[p["root"] == "NQ", "session"].to_numpy(str))
    return s[(s >= LO) & (s <= HI)]


def daily(t: pd.DataFrame, cal: np.ndarray, name: str) -> pd.Series:
    t = t[(t["session"] >= LO) & (t["session"] <= HI)]
    need(not t["session"].duplicated().any(), f"[DAILY] {name}: two trades on one session")
    need(t["session"].isin(set(cal)).all(), f"[DAILY] {name}: a trade off the calendar")
    d = t.groupby("session")["net"].sum().reindex(cal).fillna(0.0)
    need(abs(float(d.sum()) - float(t["net"].sum())) <= 1e-9 * max(1.0, float(t["net"].abs().sum())),
         f"[DAILY] {name}: the daily sum differs from the trade total")
    return d


# ------------------------------------------------------------------------------------------------ the gates
def sharpe(x: np.ndarray) -> float:
    sd = float(np.std(x, ddof=1))
    return float(np.mean(x) / sd * math.sqrt(252)) if sd > 0 else float("nan")


def sortino(x: np.ndarray) -> float:
    dd = math.sqrt(float(np.mean(np.minimum(x, 0.0) ** 2)))
    return float(np.mean(x) / dd * math.sqrt(252)) if dd > 0 else float("nan")


def halves(x: np.ndarray) -> tuple[float, float]:
    h = len(x) // 2
    return float(x[:h].sum()), float(x[h:].sum())


def p5_largest_day_share(d: pd.Series) -> dict:
    """The largest single day's share of its calendar year's net (R11 P5's quantity; 30 % is the operative haircut)."""
    yrs = d.index.str[:4]
    out = {}
    for y in sorted(set(yrs)):
        x = d[yrs == y].to_numpy()
        tot = float(x.sum())
        out[y] = float(x.max() / tot) if tot > 0 else None
    vals = [v for v in out.values() if v is not None]
    return {"by_year": out, "max": max(vals) if vals else None, "operative_haircut": 0.30}


def lives_censored(d: np.ndarray, trail: float, p3_cap: float, with_p3: bool, censor: bool = True) -> list[int]:
    """D734-A1: the module's walkers (a death is the trailing drawdown reaching `trail`, or, with_p3, a day <= -p3_cap;
    the account restarts flat), with the final UNFINISHED spell kept as a life censored at the window's end."""
    lives, eq, peak, start = [], 0.0, 0.0, 0
    for i, x in enumerate(d):
        eq += x
        peak = max(peak, eq)
        if peak - eq >= trail or (with_p3 and x <= -p3_cap):
            lives.append(i - start + 1)
            eq, peak, start = 0.0, 0.0, i + 1
    if censor and start < len(d):
        lives.append(len(d) - start)
    return lives


def p3b_a1(d: np.ndarray, module_p3: dict, account: float = ACCOUNT, censor: bool = True) -> dict:
    """D734-A1's P3b: the module's value where it is finite (the account dies under the drawdown walker); otherwise the
    censored value. A NaN never passes."""
    trail, cap = TRAIL, P3_CAP_FRACTION * account
    a = lives_censored(d, trail, cap, False, censor)
    b = lives_censored(d, trail, cap, True, censor)
    cens = (1.0 - float(np.mean(b)) / float(np.mean(a))) if (a and b and np.mean(a) > 0) else float("nan")
    mod = module_p3["p3b_life_cost"]
    read = mod if math.isfinite(mod) else cens
    return {"module_p3b": mod, "censored_p3b": cens, "read_p3b": read, "read_from": "module" if math.isfinite(mod) else "censored (A1)",
            "lives_dd": len(a), "lives_either": len(b), "pass": bool(math.isfinite(read) and read <= P3B_BAR)}


def gates(f_crit: dict, c_crit: dict, book: pd.Series) -> dict:
    x = book.to_numpy(float)
    g1 = {"F": f_crit.get("verdict"), "C": c_crit.get("verdict"),
          "holds": f_crit.get("verdict") == "PASS" and c_crit.get("verdict") == "PASS"}
    g2 = {"net": float(x.sum()), "holds": bool(x.sum() > 0)}
    a, b = halves(x)
    g3 = {"first_half_net": a, "second_half_net": b, "holds": bool(a > 0 and b > 0)}
    p2 = {v: H.p2_flatten([EXIT_ET], v) for v in VENUES}
    p3 = H.p3(x, ACCOUNT)
    p3b = p3b_a1(x, p3)
    sd = float(np.std(x, ddof=1))
    plan = H.load_venue(P4_COST_VENUE)
    cost = float(plan.fee_eval + plan.fee_activation)
    prof, life = H.expected_profit_before_breach_usd(sharpe(x), sd, ACCOUNT, TRAIL)
    p1 = H.p1_size(x, TRAIL)
    g4 = {"P2": p2, "P2_pass": all(p2.values()),
          "P3": {k: p3[k] for k in ("p3a_breaches", "p3a_breaches_per_year", "p3a_pass", "p3b_life_cost", "p3b_pass",
                                     "p3c_worst_day_usd", "p3c_share_of_loss_budget", "daily_sigma_usd", "life_dd_only_sessions")},
          "P3b_A1": p3b,
          "P3_pass": bool(p3["p3a_pass"] and p3b["pass"]),
          "P4": {"expected_profit_before_breach_usd": prof, "expected_life_days": life, "account_cost_usd": cost,
                 "cost_venue": P4_COST_VENUE},
          "P4_pass": bool(math.isfinite(prof) and prof > cost),
          "P1_reported": p1, "P5_reported": None, "P6": {v: bool(H.venue_record(v)["automation_permitted_funded"]) for v in VENUES}}
    g4["holds"] = bool(g4["P2_pass"] and g4["P3_pass"] and g4["P4_pass"] and all(g4["P6"].values()))
    return {"G1": g1, "G2": g2, "G3": g3, "G4": g4,
            "reading": "ADMITTED" if all(g["holds"] for g in (g1, g2, g3, g4)) else "NOT ADMITTED"}


# ------------------------------------------------------------------------------------------------ rehearsal
def rehearse() -> int:
    need(not OUT_REHEARSAL.exists(), f"[RUN] {OUT_REHEARSAL.name} exists: the rehearsal is run-once")
    t0 = time.time()
    cal = calendar()
    f, f_crit = part_f()
    c, c_crit, ka = part_c()
    F, C = daily(f, cal, "F"), daily(c, cal, "C")
    need(abs(float(F.sum()) - D732_F_TOTAL) < 1e-3, f"[D732] F total {F.sum():.6f} != D732's {D732_F_TOTAL}")
    import diag_d722_lines as DL
    l2 = DL.load_lines().query("line == 'L2'")
    need(np.allclose(F.to_numpy(), l2.groupby("session")["net_usd"].sum().reindex(cal).fillna(0.0).to_numpy(), atol=TOL),
         "[D732] F's daily series differs from D722's L2 (the series D732 used)")
    book = F + C
    need(np.allclose((F + C).to_numpy(), book.to_numpy()), "[BOOK] identity")
    G = gates(f_crit, c_crit, book)
    G["G4"]["P5_reported"] = p5_largest_day_share(book)
    x = book.to_numpy(float)
    yrs = book.index.str[:4]
    res = {"spec": "docs/decisions/D734-PRE-REG-the-nq-f2-and-compression-book-for-the-joint-vault.md (09b7e2a0), with D734-A1 (be558fb8)",
           "mode": "IN-SAMPLE REHEARSAL (not the vault)", "span": [LO, HI], "sessions": int(len(cal)),
           "parts": {"F": {"trades": int(len(f)), "net": float(F.sum()), "sharpe": sharpe(F.to_numpy()), "criterion": f_crit},
                     "C": {"trades": int(len(c)), "net": float(C.sum()), "sharpe": sharpe(C.to_numpy()), "criterion": c_crit,
                           "d680_known_answer": ka}},
           "book": {"net": float(x.sum()), "net_per_year": float(x.sum() / (len(x) / 252)), "sharpe": sharpe(x),
                    "sortino": sortino(x),
                    "by_year": {y: float(x[yrs == y].sum()) for y in sorted(set(yrs))},
                    "trade_days": int((x != 0).sum())},
           "gates": G, "wall_s": None}
    c_ = np.cumsum(x)
    res["book"]["max_dd_closed_usd"] = float(np.max(np.maximum.accumulate(np.r_[0.0, c_])[1:] - c_))
    res["wall_s"] = round(time.time() - t0, 1)
    with open(OUT_REHEARSAL, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1, default=lambda o: None if isinstance(o, float) and not math.isfinite(o) else str(o))
        fh.write("\n")
    print(json.dumps({"parts": {k: {kk: v[kk] for kk in ("trades", "net", "sharpe")} | {"verdict": v["criterion"].get("verdict")}
                                for k, v in res["parts"].items()},
                      "book": res["book"], "gates": G}, indent=1, default=str))
    print(f"wrote {OUT_REHEARSAL.relative_to(REPO)} in {res['wall_s']} s")
    return 0


def selftest() -> int:
    fired = []

    def expect(fn, what):
        try:
            fn()
        except D734Error as e:
            print(f"  RAISES  {what}: {str(e)[:110]}")
            fired.append(what)
            return
        raise SystemExit(f"SELFTEST FAILED: did not raise: {what}")

    cal = pd.bdate_range("2019-01-02", periods=300).strftime("%Y-%m-%d").to_numpy()
    rng = np.random.default_rng(734)
    good = pd.Series(rng.normal(25, 60, len(cal)), index=cal)          # draws down sometimes, earns in both halves
    G = gates({"verdict": "PASS"}, {"verdict": "PASS"}, good)
    need(G["G2"]["holds"] and G["G3"]["holds"] and G["G1"]["holds"], "[GATES] a clean book fails G1-G3")
    print(f"  PASS    a clean synthetic book passes G1-G3 (reading {G['reading']})")
    expect(lambda: need(gates({"verdict": "PASS"}, {"verdict": "FAIL"}, good)["G1"]["holds"], "[G1] one FAIL still holds"),
           "G1: one component failing")
    half_bad = good.copy()
    half_bad.iloc[len(half_bad) // 2:] = -20.0
    expect(lambda: need(gates({"verdict": "PASS"}, {"verdict": "PASS"}, half_bad)["G3"]["holds"], "[G3] a losing half holds"),
           "G3: a losing second half")
    expect(lambda: need(gates({"verdict": "PASS"}, {"verdict": "PASS"}, -good)["G2"]["holds"], "[G2] a losing book holds"),
           "G2: a losing book")
    expect(lambda: seal(["2023-12-29", "2024-01-02"], "x"), "seal: a planted 2024 session")
    t = pd.DataFrame({"session": [cal[0], cal[0]], "net": [1.0, 2.0]})
    expect(lambda: daily(t, cal, "x"), "daily: two trades on one session")
    need(not H.p2_flatten(["16:20"], "topstep_50k"), "[P2] 16:20 passes a 16:10 flatten")
    print("  PASS    P2 refuses an exit after the venue's flatten time")
    # D734-A1: P3b with the unfinished life censored
    calm = np.tile([30.0, -20.0, 25.0, -10.0], 100)                  # never dies, never a 2 % day
    m = H.p3(calm, ACCOUNT)
    r = p3b_a1(calm, m)
    need(not math.isfinite(m["p3b_life_cost"]) and r["read_p3b"] == 0.0 and r["pass"],
         "[A1] a never-dying, breach-free book must read P3b = 0 and pass")
    print(f"  PASS    A1: never dies, no 2 % day -> module P3b {m['p3b_life_cost']}, censored {r['read_p3b']} (pass)")
    one_bad = calm.copy()
    one_bad[200] = -1_100.0                                          # one 2 % day, still no trailing death
    r1 = p3b_a1(one_bad, H.p3(one_bad, ACCOUNT))
    need(r1["read_from"].startswith("censored") and r1["read_p3b"] > 0, "[A1] a 2 % day must shorten the censored life")
    print(f"  PASS    A1: one 2 % day, no death -> censored P3b {r1['read_p3b']:.3f}")
    dying = np.r_[np.full(50, 20.0), np.full(30, -80.0), np.full(300, 15.0)]
    md = H.p3(dying, ACCOUNT)
    need(math.isfinite(md["p3b_life_cost"]) and p3b_a1(dying, md)["read_from"] == "module",
         "[A1] the module's finite value must be the one read")
    print("  PASS    A1: an account that dies reads the module's own P3b")
    expect(lambda: need(p3b_a1(calm, m, censor=False)["pass"], "[A1] without censoring the 0/0 case must not pass"),
           "A1: the uncensored 0/0 case does not pass")
    print(f"SELFTEST PASS: {len(fired)} canaries raised")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--rehearse", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else rehearse()


if __name__ == "__main__":
    sys.exit(main())
