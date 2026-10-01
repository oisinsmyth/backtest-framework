"""D734: the assembled book NQ F2 + the NQ compression break, one MNQ each, as pre-registered in
docs/decisions/D734-PRE-REG-the-nq-f2-and-compression-book-for-the-joint-vault.md (09b7e2a0) with D734-A1 (be558fb8:
P3b with censored lives) and D734-A2 (b4169512: the calendar; the vault mode's mechanics).

    uv run python scripts/vault_d734_nq_book.py --selftest
    uv run python scripts/vault_d734_nq_book.py --rehearse                     # in-sample, the final code (run-once)
    uv run python scripts/vault_d734_nq_book.py --freeze                       # once, after --rehearse
    uv run python scripts/vault_d734_nq_book.py --vault --principals-word "..."   # the joint run ONLY, after D716's
                                                                                  # --vault and D680's --run-vault

The book's daily net is F + C on the union of the two parts' own session frames (A2). Gates: G1 each part's own
verdict; G2 book net > 0; G3 net > 0 in each half of the sessions; G4 hurdle P on $50k at the topstep_50k /
mffu_rapid_50k intersection (P2, P3 with A1's P3b, P4 must pass; P1 and P5 reported; P6 the venues' fact).
Outputs (aggregates only): data/rehearsal_d734_nq_book_frozen.json, data/FROZEN_vault_d734_nq_book.json,
data/vault_d734_nq_book.json.
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

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
from backtest_framework.validation import hurdle_p as H  # noqa: E402

SPEC = REPO / "docs" / "decisions" / "D734-PRE-REG-the-nq-f2-and-compression-book-for-the-joint-vault.md"
OUT_REHEARSAL_V1 = REPO / "data" / "rehearsal_d734_nq_book.json"          # before A1, kept
OUT_REHEARSAL_A1 = REPO / "data" / "rehearsal_d734_nq_book_a1.json"       # A1, the D722 panel calendar, kept
OUT_REHEARSAL = REPO / "data" / "rehearsal_d734_nq_book_frozen.json"      # A2, the final code: the freeze's known answer
FROZEN = REPO / "data" / "FROZEN_vault_d734_nq_book.json"
VAULT_OUT = REPO / "data" / "vault_d734_nq_book.json"
HASHED = ("scripts/vault_d716_nq_f2.py", "scripts/vault_d680_nq_compression.py", "scripts/joint_d680_vault.py",
          "src/backtest_framework/validation/hurdle_p.py", "data/prop_venues.json")
IN_LO, IN_HI, SEAL_IN = "2018-05-14", "2023-12-29", "2024-01-01"
VAULT_FROM, VAULT_END = "2025-03-01", "2026-09-18"
VENUES = ("topstep_50k", "mffu_rapid_50k")
ACCOUNT, TRAIL = 50_000.0, 2_000.0
P3_CAP_FRACTION, P3B_BAR = 0.02, 0.33
P4_COST_VENUE = "mffu_rapid_50k"        # topstep_50k's fees are not recorded in data/prop_venues.json
EXIT_ET = "16:00"                       # both parts are flat at the close at the latest (D716 s.1; D680 E4)
NQ_USD_PP = 2.0
D732_F_TOTAL = 5628.310180              # D732's F on the in-sample span
F_LINES = {"NQ F2": "B", "THE AGREEMENT BOOK": "A"}


class D734Error(AssertionError):
    pass


def need(c: bool, msg: str) -> None:
    if not c:
        raise D734Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def seal(days, hi: str, what: str) -> None:
    d = np.asarray(days, dtype=str)
    need(not (d > hi).any(), f"[SEAL] {what}: a session after {hi}")


# ------------------------------------------------------------------------------------------------ the book (both modes)
def daily(t: pd.DataFrame, cal: np.ndarray, name: str) -> pd.Series:
    need(not t["session"].duplicated().any(), f"[DAILY] {name}: two trades on one session")
    need(t["session"].isin(set(cal)).all(), f"[DAILY] {name}: a trade off the calendar")
    d = t.groupby("session")["net"].sum().reindex(cal).fillna(0.0)
    need(abs(float(d.sum()) - float(t["net"].sum())) <= 1e-9 * max(1.0, float(t["net"].abs().sum())),
         f"[DAILY] {name}: the daily sum differs from the trade total")
    return d


def sharpe(x: np.ndarray) -> float:
    sd = float(np.std(x, ddof=1))
    return float(np.mean(x) / sd * math.sqrt(252)) if sd > 0 else float("nan")


def sortino(x: np.ndarray) -> float:
    dd = math.sqrt(float(np.mean(np.minimum(x, 0.0) ** 2)))
    return float(np.mean(x) / dd * math.sqrt(252)) if dd > 0 else float("nan")


def halves(x: np.ndarray) -> tuple[float, float]:
    h = len(x) // 2
    return float(x[:h].sum()), float(x[h:].sum())


def lives_censored(d: np.ndarray, trail: float, p3_cap: float, with_p3: bool, censor: bool = True) -> list[int]:
    """D734-A1: the module's walkers, with the final UNFINISHED spell kept as a life censored at the window's end."""
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
    """D734-A1: the module's P3b where finite, else the censored value; a NaN never passes."""
    a = lives_censored(d, TRAIL, P3_CAP_FRACTION * account, False, censor)
    b = lives_censored(d, TRAIL, P3_CAP_FRACTION * account, True, censor)
    cens = (1.0 - float(np.mean(b)) / float(np.mean(a))) if (a and b and np.mean(a) > 0) else float("nan")
    mod = module_p3["p3b_life_cost"]
    read = mod if math.isfinite(mod) else cens
    return {"module_p3b": mod, "censored_p3b": cens, "read_p3b": read, "read_from": "module" if math.isfinite(mod) else "censored (A1)",
            "lives_dd": len(a), "lives_either": len(b), "pass": bool(math.isfinite(read) and read <= P3B_BAR)}


def p5_largest_day_share(d: pd.Series) -> dict:
    yrs = d.index.str[:4]
    out = {}
    for y in sorted(set(yrs)):
        x = d[yrs == y].to_numpy()
        tot = float(x.sum())
        out[y] = float(x.max() / tot) if tot > 0 else None
    vals = [v for v in out.values() if v is not None]
    return {"by_year": out, "max": max(vals) if vals else None, "operative_haircut": 0.30}


def gates(f_verdict_ok: bool, c_verdict_ok: bool, f_label: str, c_label: str, book: pd.Series) -> dict:
    x = book.to_numpy(float)
    g1 = {"F": f_label, "C": c_label, "holds": bool(f_verdict_ok and c_verdict_ok)}
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
    try:
        p1 = H.p1_size(x, TRAIL)
    except ValueError as e:                     # a book that never draws down has no P1 answer (D48); reported as such
        p1 = {"no_answer": str(e)}
    g4 = {"P2": p2, "P2_pass": all(p2.values()),
          "P3": {k: p3[k] for k in ("p3a_breaches", "p3a_breaches_per_year", "p3a_pass", "p3c_worst_day_usd",
                                     "p3c_share_of_loss_budget", "daily_sigma_usd", "life_dd_only_sessions")},
          "P3b_A1": p3b, "P3_pass": bool(p3["p3a_pass"] and p3b["pass"]),
          "P4": {"expected_profit_before_breach_usd": prof, "expected_life_days": life, "account_cost_usd": cost,
                 "cost_venue": P4_COST_VENUE},
          "P4_pass": bool(math.isfinite(prof) and prof > cost),
          "P1_reported": p1, "P5_reported": p5_largest_day_share(book),
          "P6": {v: bool(H.venue_record(v)["automation_permitted_funded"]) for v in VENUES}}
    g4["holds"] = bool(g4["P2_pass"] and g4["P3_pass"] and g4["P4_pass"] and all(g4["P6"].values()))
    return {"G1": g1, "G2": g2, "G3": g3, "G4": g4,
            "reading": "ADMITTED" if all(g["holds"] for g in (g1, g2, g3, g4)) else "NOT ADMITTED"}


def score_book(f_tr: pd.DataFrame, f_sess: np.ndarray, c_tr: pd.DataFrame, c_sess: np.ndarray, lo: str, hi: str,
               f_ok: bool, c_ok: bool, f_label: str, c_label: str) -> dict:
    cal = np.array(sorted(set(np.asarray(f_sess, str)) | set(np.asarray(c_sess, str))))
    cal = cal[(cal >= lo) & (cal <= hi)]
    F = daily(f_tr[(f_tr["session"] >= lo) & (f_tr["session"] <= hi)], cal, "F")
    C = daily(c_tr[(c_tr["session"] >= lo) & (c_tr["session"] <= hi)], cal, "C")
    book = F + C
    x = book.to_numpy(float)
    yrs = book.index.str[:4]
    c_ = np.cumsum(x)
    return {"window": [lo, hi], "calendar_sessions": int(len(cal)),
            "parts": {"F": {"trades": int((F != 0).sum()), "net": float(F.sum()), "sharpe": sharpe(F.to_numpy()), "label": f_label},
                      "C": {"trades": int((C != 0).sum()), "net": float(C.sum()), "sharpe": sharpe(C.to_numpy()), "label": c_label}},
            "book": {"net": float(x.sum()), "net_per_year": float(x.sum() / (len(x) / 252)), "sharpe": sharpe(x),
                     "sortino": sortino(x), "max_dd_closed_usd": float(np.max(np.maximum.accumulate(np.r_[0.0, c_])[1:] - c_)),
                     "trade_days": int((x != 0).sum()), "by_year": {y: float(x[yrs == y].sum()) for y in sorted(set(yrs))}},
            "gates": gates(f_ok, c_ok, f_label, c_label, book)}


# ------------------------------------------------------------------------------------------------ the parts
def f_part(bd: dict, mask: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({"session": np.asarray(bd["sn"], dtype=str)[mask], "net": np.asarray(bd["net"], dtype=float)[mask]})


def c_part(tr: pd.DataFrame, mask: np.ndarray) -> pd.DataFrame:
    x = tr[mask]
    usd = x["net"].to_numpy(float) / 1e4 * x["entry"].to_numpy(float) * NQ_USD_PP     # single-count bp -> $ at one MNQ
    return pd.DataFrame({"session": x["session"].astype(str).to_numpy(), "net": usd})


# ------------------------------------------------------------------------------------------------ rehearsal (in-sample)
def rehearse() -> int:
    need(not OUT_REHEARSAL.exists(), f"[RUN] {OUT_REHEARSAL.name} exists: the rehearsal is run-once")
    t0 = time.time()
    import vault_d680_nq_compression as V680
    import vault_d716_nq_f2 as F
    bd = F.build()                                                         # IN_END, vault closed
    Bm, _Am = F.masks(bd, IN_LO, IN_HI)
    f_crit = F.primary(np.asarray(bd["net"], float)[Bm])
    f_tr = f_part(bd, Bm)
    seal(bd["sn"], IN_HI, "F frame")
    need(abs(float(f_tr["net"].sum()) - D732_F_TOTAL) < 1e-3, f"[D732] F total {f_tr['net'].sum():.6f} != {D732_F_TOTAL}")
    tr, sessions, R = V680.in_sample()
    ka = V680.known_answer(tr)
    win = np.isfinite(tr["t671"].to_numpy(float)) & np.isfinite(tr["ctier"].to_numpy(float))
    c1 = win & (tr["ctier"].to_numpy(float) < 1 / 3)
    need(int(c1.sum()) == ka["trades"], "[C] the C1 mask differs from D680's known answer")
    inwin = (tr["session"].astype(str) <= IN_HI).to_numpy()
    c_crit = V680.score(tr.loc[c1 & inwin, "gross"].to_numpy(float), tr.loc[c1 & inwin, "net"].to_numpy(float), R)
    c_tr = c_part(tr, c1 & inwin)
    c_sess = np.asarray(sessions, dtype=str)
    c_sess = c_sess[c_sess <= IN_HI]
    res = score_book(f_tr, bd["sn"], c_tr, c_sess, IN_LO, IN_HI, f_crit.get("verdict") == "PASS", c_crit.get("verdict") == "PASS",
                     f"NQ F2 (in-sample primary: {f_crit.get('verdict')})", f"C1 (in-sample score: {c_crit.get('verdict')})")
    res.update({"mode": "IN-SAMPLE REHEARSAL on the final code (D734-A2): the freeze's known answer",
                "runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC), "d680_known_answer": ka,
                "f_criterion": f_crit, "c_criterion": c_crit, "wall_s": round(time.time() - t0, 1)})
    with open(OUT_REHEARSAL, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1, default=lambda o: None if isinstance(o, float) and not math.isfinite(o) else str(o))
        fh.write("\n")
    show(res)
    print(f"wrote {OUT_REHEARSAL.relative_to(REPO)} in {res['wall_s']} s")
    return 0


def show(res: dict) -> None:
    b, g = res["book"], res["gates"]
    print(f"window {res['window']}  calendar {res['calendar_sessions']} sessions")
    for k, p in res["parts"].items():
        print(f"  {k}: {p['trades']} trades, net ${p['net']:,.2f}, Sharpe {p['sharpe']:+.2f}  [{p['label']}]")
    print(f"  BOOK: net ${b['net']:,.2f} (${b['net_per_year']:,.0f}/yr), Sharpe {b['sharpe']:+.2f}, Sortino {b['sortino']:+.2f}, "
          f"max DD ${b['max_dd_closed_usd']:,.0f}, trade days {b['trade_days']}")
    print("  by year:", {y: round(v) for y, v in b["by_year"].items()})
    g4 = g["G4"]
    print(f"  G1 {g['G1']['holds']}  G2 {g['G2']['holds']}  G3 {g['G3']['holds']} ({g['G3']['first_half_net']:+,.0f} / "
          f"{g['G3']['second_half_net']:+,.0f})  G4 {g4['holds']} (P2 {g4['P2_pass']}, P3a {g4['P3']['p3a_pass']}, "
          f"P3b {g4['P3b_A1']['read_p3b']} via {g4['P3b_A1']['read_from']}, P4 {g4['P4_pass']}, P6 {all(g4['P6'].values())})")
    print(f"  READING: {g['reading']}")


# ------------------------------------------------------------------------------------------------ freeze
def freeze() -> int:
    need(not FROZEN.exists(), f"[FREEZE] {FROZEN.name} exists: the freeze is written once")
    need(OUT_REHEARSAL.exists(), "[FREEZE] run --rehearse on the final code first")
    reh = json.loads(OUT_REHEARSAL.read_text(encoding="utf-8"))
    me = sha(Path(__file__).resolve())
    need(reh["runner_sha256"] == me and reh["prereg_sha256"] == sha(SPEC),
         "[FREEZE] the rehearsal was run on a different runner or record: re-run it on this code")
    doc = {"record": "D734 (09b7e2a0; A1 be558fb8; A2 b4169512)", "runner": "scripts/vault_d734_nq_book.py",
           "runner_sha256": me, "prereg_sha256": sha(SPEC),
           "hashed_unchanged": {p: sha(REPO / p) for p in HASHED},
           "components_frozen": {"D716": "data/FROZEN_vault_d716_nq_f2.json", "D680": "data/FROZEN_vault_d680_nq_compression.json"},
           "known_answer_in_sample": {"window": reh["window"], "calendar_sessions": reh["calendar_sessions"],
                                      "book_net": reh["book"]["net"], "book_sharpe": reh["book"]["sharpe"],
                                      "F_trades": reh["parts"]["F"]["trades"], "F_net": reh["parts"]["F"]["net"],
                                      "C_trades": reh["parts"]["C"]["trades"], "C_net": reh["parts"]["C"]["net"],
                                      "reading": reh["gates"]["reading"]},
           "programme_slot": None, "slot_note": "no slot: alpha stays with the components (slots 7 and 9); D734 s.0",
           "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    with open(FROZEN, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1)
        fh.write("\n")
    print(json.dumps({k: doc[k] for k in ("runner_sha256", "prereg_sha256", "hashed_unchanged", "known_answer_in_sample")}, indent=1))
    return 0


def check_freeze() -> dict:
    need(FROZEN.exists(), "[FREEZE] D734 is not frozen")
    fz = json.loads(FROZEN.read_text(encoding="utf-8"))
    need(fz["runner_sha256"] == sha(Path(__file__).resolve()) and fz["prereg_sha256"] == sha(SPEC),
         "[FREEZE] this runner or D734 has moved since the freeze")
    for p, h in fz["hashed_unchanged"].items():
        need(sha(REPO / p) == h, f"[FREEZE] {p} has moved since the freeze")
    return fz


def check_d716_freeze(F: Any) -> None:
    fz = json.loads(F.FROZEN.read_text(encoding="utf-8"))
    need(fz.get("runner_sha256") == F.sha(Path(F.__file__).resolve()) and fz.get("prereg_sha256") == F.sha(F.SPEC),
         "[D716] its runner or record has moved since its freeze")
    for p, h in fz["imported_unchanged"].items():
        need(F.sha(REPO / "scripts" / p) == h, f"[D716] {p} has moved since its freeze")


# ------------------------------------------------------------------------------------------------ the vault (joint run)
def vault(word: str | None) -> int:
    if not (word or "").strip():
        print("refused: the book is scored only in the joint run, on the principal's word (D734 s.3)")
        return 2
    check_freeze()
    need(not VAULT_OUT.exists(), "[VAULT] the book has already been scored; a second opening is refused")
    import joint_d680_vault as J
    import vault_d716_nq_f2 as F
    check_d716_freeze(F)
    J.check_freeze()
    need(F.VAULT_OUT.exists(), "[ORDER] D716's --vault has not run")
    V680 = J.frozen_runner()
    need(V680.VAULT_OUT.exists(), "[ORDER] D680's joint-wrapper --run-vault has not run")
    r716 = json.loads(F.VAULT_OUT.read_text(encoding="utf-8"))
    r680 = json.loads(V680.VAULT_OUT.read_text(encoding="utf-8"))
    # F: D716's own build and masks, the line its recorded family result names, reproduced exactly
    bd = F.build(VAULT_END, vault_open=True)
    Bm, Am = F.masks(bd, VAULT_FROM, VAULT_END)
    result = r716["family"]["result"]
    key = F_LINES.get(result, "B")
    mask = Am if key == "A" else Bm
    got = F.V.score(np.asarray(bd["net"], float)[mask])
    rec = r716["parts"]["vault"][key]
    need(got["trades"] == rec["trades"] and got.get("mean_net") == rec.get("mean_net"),
         f"[REPRODUCE] D716 vault {key}: {got.get('trades')}/{got.get('mean_net')} != recorded {rec.get('trades')}/{rec.get('mean_net')}")
    f_tr = f_part(bd, mask)
    # C: the wrapper's checked files, the frozen book() under the held cut, C1 inside the vault, reproduced exactly
    man = json.loads((J.JOINT / J.MANIFEST_NAME).read_text(encoding="utf-8"))
    bars_p, use_p = J.JOINT / J.BARS_NAME, J.JOINT / J.USE_NAME
    need(J.sha_bytes(bars_p.read_bytes()) == man["bars_sha256"] and J.sha_bytes(use_p.read_bytes()) == man["use_sha256"],
         "[C] the vault input files moved after their manifest")
    R = V680.M.S.load_v2().R
    bv, uv = J.read_like_runner(bars_p, use_p)
    with J.held(V680.T, "RESERVED_FROM", J.RAISED):
        tr, sessions = V680.book(bv, uv, R, None)
    need(V680.T.RESERVED_FROM == J.CUT, "[C] the cut was not restored")
    sess = tr["session"].astype(str)
    v = ((sess >= VAULT_FROM) & (sess <= VAULT_END)).to_numpy()
    c1 = v & (tr["ctier"].to_numpy(float) < 1 / 3)
    got_c = V680.score(tr.loc[c1, "gross"].to_numpy(float), tr.loc[c1, "net"].to_numpy(float), R)
    rc = r680["C1"]
    need(got_c["trades"] == rc["trades"] and got_c.get("gross_bp") == rc.get("gross_bp") and got_c.get("net_bp") == rc.get("net_bp"),
         f"[REPRODUCE] D680 vault C1: {got_c} != recorded {rc}")
    c_tr = c_part(tr, c1)
    f_ok = result in F_LINES
    c_ok = rc.get("verdict") == "PASS"
    res = score_book(f_tr, bd["sn"], c_tr, np.asarray(sessions, str), VAULT_FROM, VAULT_END, f_ok, c_ok,
                     f"D716 family: {result} (line {key})", f"D680 C1: {rc.get('verdict')}")
    res.update({"principals_word": word, "mode": "THE VAULT (the joint run)", "d716_reproduced": got, "d680_reproduced": got_c})
    with open(VAULT_OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1, default=lambda o: None if isinstance(o, float) and not math.isfinite(o) else str(o))
        fh.write("\n")
    show(res)
    return 0


# ------------------------------------------------------------------------------------------------ selftest
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
    f_tr = pd.DataFrame({"session": cal[::5], "net": rng.normal(20, 40, len(cal[::5]))})
    c_tr = pd.DataFrame({"session": cal[2::7], "net": rng.normal(15, 30, len(cal[2::7]))})
    r = score_book(f_tr, cal, c_tr, cal, cal[0], cal[-1], True, True, "f", "c")
    need(abs(r["book"]["net"] - (f_tr["net"].sum() + c_tr["net"].sum())) < 1e-9, "[BOOK] the book is not F + C")
    print(f"  PASS    score_book on a synthetic pair (reading {r['gates']['reading']}, calendar {r['calendar_sessions']})")
    expect(lambda: need(score_book(f_tr, cal, c_tr, cal, cal[0], cal[-1], True, False, "f", "c")["gates"]["G1"]["holds"],
                        "[G1] one component failing still holds"), "G1: one component failing")
    half_bad = c_tr.copy()
    half_bad.loc[half_bad["session"] > cal[150], "net"] = -200.0
    expect(lambda: need(score_book(f_tr, cal, half_bad, cal, cal[0], cal[-1], True, True, "f", "c")["gates"]["G3"]["holds"],
                        "[G3] a losing half holds"), "G3: a losing second half")
    expect(lambda: daily(pd.DataFrame({"session": [cal[0], cal[0]], "net": [1.0, 2.0]}), cal, "x"), "daily: two trades on a session")
    expect(lambda: daily(pd.DataFrame({"session": ["2030-01-02"], "net": [1.0]}), cal, "x"), "daily: a trade off the calendar")
    expect(lambda: seal(["2023-12-29", "2024-01-02"], IN_HI, "x"), "seal: a session after the window")
    calm = np.tile([30.0, -20.0, 25.0, -10.0], 100)
    m = H.p3(calm, ACCOUNT)
    need(p3b_a1(calm, m)["read_p3b"] == 0.0 and p3b_a1(calm, m)["pass"], "[A1] never-dying book must read 0 and pass")
    expect(lambda: need(p3b_a1(calm, m, censor=False)["pass"], "[A1] the uncensored 0/0 must not pass"), "A1: uncensored 0/0")
    print("  PASS    A1: a never-dying book reads P3b 0 and passes")
    need(vault("") == 2 and vault(None) == 2, "[VAULT] an empty word must be refused with exit 2")
    print("  PASS    --vault refuses without the principal's word (exit 2), before reading anything")
    need(not H.p2_flatten(["16:20"], "topstep_50k"), "[P2] 16:20 passes a 16:10 flatten")
    print("  PASS    P2 refuses an exit after the venue's flatten time")
    print(f"SELFTEST PASS: {len(fired)} canaries raised")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--rehearse", action="store_true")
    g.add_argument("--freeze", action="store_true")
    g.add_argument("--vault", action="store_true")
    ap.add_argument("--principals-word", default=None)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.rehearse:
        return rehearse()
    if a.freeze:
        return freeze()
    return vault(a.principals_word)


if __name__ == "__main__":
    sys.exit(main())
