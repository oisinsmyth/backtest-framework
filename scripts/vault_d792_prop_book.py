"""D792: the assembled prop book -- the five live components, one micro each, the members that PASS their own frozen
vault lines -- as pre-registered in docs/decisions/D792-PRE-REG-the-assembled-prop-book-for-the-joint-vault.md
(a90f49da), committed before this file existed.

    uv run --no-sync python scripts/vault_d792_prop_book.py --selftest            # synthetic only
    uv run --no-sync python scripts/vault_d792_prop_book.py --rehearse            # in-sample (<= 2023-12-29), once
    uv run --no-sync python scripts/vault_d792_prop_book.py --freeze              # once, after --rehearse
    uv run --no-sync python scripts/vault_d792_prop_book.py --vault --principals-word "..."     # the joint run ONLY,
                                                                                  # after all five members' --vault and D734's
    uv run --no-sync python scripts/vault_d792_prop_book.py --forward --principals-word "..."   # on/after 2027-09-30

The members (D792 s.1), each rebuilt through its own frozen runner's functions, imported unchanged:
  F  NQ F2 (D716, slot 7)                 vault_d716_nq_f2: build / masks; book B, or A if step 2 takes over
  D  NQ leads the Dow (D737, slot 1)      vault_d737_nq_leads_the_dow: in_sample / vault_load / window
  R  the CPI/jobs-report fade (D776, 2)   vault_d776_cpi_nfp_fade: in_sample_bars / read_vault / trades
  C  the NQ compression break C1 (D680)   vault_d680_nq_compression + joint_d680_vault (as D734 reads it)
  L  base L4 on M2K (D781, slot 10)       vault_d781_l4_auction_fade: in_sample_bars / read_vault / frame
D734's book machinery (daily, Sharpe/Sortino, A1's censored P3b, P5, the F and C parts) is imported from
vault_d734_nq_book, unchanged.

The book (s.2): each member's daily net is the sum of its trades booked on the venue trading day of their EXIT (L's
18:05 -> 10:00 trade on S+1), 0 otherwise, on the union of the members' own session frames; the book is the sum. C
counts only from 2025-03-01 (its in-sample runs to 2025-02-28). Gates (s.3): G1 >= 2 members PASS; G2 book net > 0;
G3 net > 0 in each half of the sessions; G4 hurdle P on $50k at the topstep_50k / mffu_rapid_50k intersection.

Speed: the in-sample rehearsal is ~80 s serial (the members' own rehearsals: 31 + 8 + 14 + 25 s) and every mode is
run-once, so the members are built in sequence (CLAUDE.md: a run-once job under the optimisation's cost launches as
it stands).

Outputs (aggregates only): data/rehearsal_d792_prop_book.json, data/FROZEN_vault_d792_prop_book.json,
data/vault_d792_prop_book.json, data/forward_d792_prop_book.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import vault_d734_nq_book as K  # noqa: E402
from backtest_framework.validation import hurdle_p as H  # noqa: E402

SPEC_REL = "docs/decisions/D792-PRE-REG-the-assembled-prop-book-for-the-joint-vault.md"
SPEC = REPO / SPEC_REL
REHEARSAL = REPO / "data" / "rehearsal_d792_prop_book.json"
FROZEN = REPO / "data" / "FROZEN_vault_d792_prop_book.json"
VAULT_OUT = REPO / "data" / "vault_d792_prop_book.json"
FORWARD_OUT = REPO / "data" / "forward_d792_prop_book.json"
FWD = REPO / "data" / "forward"

IN_LO, IN_HI = "2018-05-14", "2023-12-29"            # the rehearsal: the span every member holds in-sample (s.4)
VAULT_FROM, VAULT_END = "2024-01-01", "2026-09-18"   # the book's window (the principal's choice)
C_FROM = "2025-03-01"                                # C's unseen window starts here (D680)
SUB_FROM = "2025-03-01"                              # reported beside: the span every member has unseen
FORWARD_FROM, FORWARD_TO = "2026-09-21", "2027-09-30"
MEMBERS = ("F", "D", "R", "C", "L")
NAMES = {"F": "NQ F2 (D716, slot 7)", "D": "NQ leads the Dow (D737, slot 1)", "R": "the CPI/jobs-report fade (D776, slot 2)",
         "C": "the NQ compression break C1 (D680, slot 9)", "L": "base L4, the M2K closing-auction fade (D781, slot 10)"}
EXITS = {"F": "16:00", "D": "16:00", "R": "11:00", "C": "16:00", "L": "10:00"}   # each member's latest exit, ET
HASHED = ("scripts/vault_d734_nq_book.py", "scripts/vault_d716_nq_f2.py", "scripts/vault_d680_nq_compression.py",
          "scripts/joint_d680_vault.py", "scripts/vault_d737_nq_leads_the_dow.py", "scripts/vault_d776_cpi_nfp_fade.py",
          "scripts/vault_d781_l4_auction_fade.py", "src/backtest_framework/validation/hurdle_p.py", "data/prop_venues.json")
# The forward ledgers' writers: hashed at the freeze and REPORTED at the forward read, never gating (the recorder is a
# live daily task and may need repairs within the year; a moved writer is named in the forward output).
FORWARD_WRITERS = ("scripts/record_forward_nq_lines.py", "scripts/forward_d776_ledger.py", "scripts/forward_f2_c1_ledgers.py",
                   "scripts/forward_l4_ledger.py")
LEDGERS = {"F": "f2_forward.csv", "D": "d737_forward.csv", "R": "d776_forward.csv", "C": "c1_forward.csv", "L": "l4_forward.csv"}
TRIM = 0.01
REFUSED = 2


class D792Error(AssertionError):
    pass


def need(c: bool, msg: str) -> None:
    if not c:
        raise D792Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def day_str(x: Any) -> np.ndarray:
    return np.array([str(v)[:10] for v in np.asarray(x)], dtype=str)


def tframe(session: Any, net: Any, gross: Any) -> pd.DataFrame:
    return pd.DataFrame({"session": day_str(session), "net": np.asarray(net, float), "gross": np.asarray(gross, float)})


def jdump(path: Path, doc: dict) -> None:
    with open(path, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, default=lambda o: None if isinstance(o, float) and not math.isfinite(o) else
                  (o.item() if isinstance(o, np.generic) else str(o)))
        fh.write("\n")


# ================================================================================ the members, in-sample
def in_F() -> tuple[pd.DataFrame, np.ndarray]:
    import vault_d716_nq_f2 as F
    bd = F.build()                                                         # IN_END, vault closed
    K.seal(bd["sn"], IN_HI, "F frame")
    Bm, _ = F.masks(bd, IN_LO, IN_HI)
    t = tframe(bd["sn"][Bm], bd["net"][Bm], bd["Xn"]["gross"].to_numpy(float)[Bm])
    need(len(t) == F.KNOWN_B and abs(float(t["net"].sum()) - K.D732_F_TOTAL) < 1e-3,
         f"[KNOWN F] {len(t)} trades, ${t['net'].sum():.6f} against D716's {F.KNOWN_B} and D732's ${K.D732_F_TOTAL}")
    return t, day_str(bd["sn"])


def in_D() -> tuple[pd.DataFrame, np.ndarray]:
    import vault_d737_nq_leads_the_dow as Dw
    cst = Dw.cost()
    c = Dw.in_sample(REPO / "data")                                        # D727's load_root: sealed at 2023-12-29
    Dw.check_known(c, cst)                                                 # 1,699 trades, D735's mean net to 1e-9
    days = day_str(c["days"])
    K.seal(days, IN_HI, "D frame")
    return tframe(days[c["d"]], c["g"] - cst, c["g"]), days


def in_R() -> tuple[pd.DataFrame, np.ndarray]:
    import vault_d776_cpi_nfp_fade as Rv
    U, _ = Rv.trades(Rv.in_sample_bars(), Rv.S.release_days())
    Rv.check_known(Rv.known(U), json.loads(Rv.FROZEN.read_text(encoding="utf-8"))["known_answer"])   # 186, to 1e-9
    R = U[U["is_rel"]]
    days = day_str(U.index)
    K.seal(days, "2023-12-31", "R frame")
    return tframe(R.index, R["gross"] - Rv.COST, R["gross"]), days


def in_C() -> tuple[pd.DataFrame, np.ndarray]:
    """D734's in-sample C, unchanged: D680's in_sample(), C1, cut at 2023-12-29; one MNQ at the level."""
    import vault_d680_nq_compression as V680
    tr, sessions, _R = V680.in_sample()
    ka = V680.known_answer(tr)
    win = np.isfinite(tr["t671"].to_numpy(float)) & np.isfinite(tr["ctier"].to_numpy(float))
    c1 = win & (tr["ctier"].to_numpy(float) < 1 / 3)
    need(int(c1.sum()) == ka["trades"], "[KNOWN C] the C1 mask differs from D680's known answer")
    inwin = (tr["session"].astype(str) <= IN_HI).to_numpy()
    return c_trades(tr, c1 & inwin), day_str(np.asarray(sessions, str)[np.asarray(sessions, str) <= IN_HI])


def c_trades(tr: pd.DataFrame, mask: np.ndarray) -> pd.DataFrame:
    x = tr[mask]
    net = K.c_part(tr, mask)["net"].to_numpy(float)
    gross = x["gross"].to_numpy(float) / 1e4 * x["entry"].to_numpy(float) * K.NQ_USD_PP
    return tframe(x["session"].astype(str).to_numpy(), net, gross)


def in_L() -> tuple[pd.DataFrame, np.ndarray]:
    import vault_d781_l4_auction_fade as Lv
    D = Lv.frame(Lv.in_sample_bars())
    Lv.check_known(Lv.known(D), json.loads(Lv.FROZEN.read_text(encoding="utf-8"))["known_answer"])   # 280, to 1e-9
    return l_trades(D, Lv.COST, "2016-01-01", "2023-12-31")


def l_trades(D: pd.DataFrame, cost: float, lo: str, hi: str) -> tuple[pd.DataFrame, np.ndarray]:
    """D781's score() selection, booked on the EXIT session s1 (D792 s.2)."""
    W = D[D["cvalid"] & (D.index >= lo) & (D["s1"] <= hi)]
    B = W[W["base"]]
    s1 = day_str(B["s1"])
    need(not pd.Series(s1).duplicated().any(), "[L] two trades exit on one session")
    return tframe(s1, B["gross"] - cost, B["gross"]), day_str(W["s1"])


IN_BUILDERS: dict[str, Callable[[], tuple[pd.DataFrame, np.ndarray]]] = {
    "F": in_F, "D": in_D, "R": in_R, "C": in_C, "L": in_L}
COSTS_NOTE = {"F": "D716's cost line, $4.067121", "D": "D711 cost_line('NQ')", "R": "D775's NQ line, $4.07",
              "C": "D680's single-count cost line (bp at the level)", "L": "D777's RTY line, $3.76"}


# ================================================================================ the book
def calendar(frames: dict[str, np.ndarray], lo: str, hi: str, starts: dict[str, str]) -> np.ndarray:
    cal: set[str] = set()
    for k, s in frames.items():
        s = np.asarray(s, str)
        cal |= set(s[(s >= max(lo, starts.get(k, lo))) & (s <= hi)])
    return np.array(sorted(cal))


def member_daily(t: pd.DataFrame, cal: np.ndarray, k: str, lo: str, hi: str, start: str) -> tuple[pd.Series, pd.Series, pd.DataFrame]:
    w = t[(t["session"] >= max(lo, start)) & (t["session"] <= hi)]
    dn = K.daily(w[["session", "net"]], cal, k)
    dg = K.daily(w[["session", "gross"]].rename(columns={"gross": "net"}), cal, k + " gross")
    return dn, dg, w


def dist(x: np.ndarray) -> dict[str, Any]:
    """CLAUDE.md group 2, on a set of P&L values: with the symmetric 1% trim and both one-sided trims."""
    x = np.sort(np.asarray(x, float))
    n = len(x)
    if n < 3:
        return {"n": n}
    k = int(math.floor(TRIM * n))
    sd = float(np.std(x, ddof=1))
    win, loss = x[x > 0], x[x < 0]
    return {"n": n, "mean": float(x.mean()), "median": float(np.median(x)), "win_rate": float((x > 0).mean()),
            "payoff": float(win.mean() / -loss.mean()) if len(win) and len(loss) else None,
            "skew": float(np.mean(((x - x.mean()) / sd) ** 3)) if sd > 0 else None,
            "kurtosis_excess": float(np.mean(((x - x.mean()) / sd) ** 4) - 3) if sd > 0 else None,
            "trim_k_each_tail": k, "mean_ex_top": float(x[:n - k].mean()) if k else float(x.mean()),
            "mean_ex_bottom": float(x[k:].mean()) if k else float(x.mean()),
            "mean_trimmed": float(x[k:n - k].mean()) if k and n > 2 * k else float(x.mean()),
            "mean_below_median": bool(x.mean() < np.median(x))}


def score_book(trades: dict[str, pd.DataFrame], frames: dict[str, np.ndarray], keys: list[str], lo: str, hi: str,
               starts: dict[str, str]) -> dict[str, Any]:
    """The book of `keys` on [lo, hi]: the union calendar, each member's daily net/gross, the sum, and the report."""
    need(len(keys) >= 1, "[BOOK] a book needs a member")
    cal = calendar({k: frames[k] for k in keys}, lo, hi, starts)
    need(len(cal) > 1, f"[BOOK] no calendar in {lo} -> {hi}")
    net, gross, parts, pooled = {}, {}, {}, []
    for k in keys:
        dn, dg, w = member_daily(trades[k], cal, k, lo, hi, starts.get(k, lo))
        net[k], gross[k] = dn, dg
        pooled.append(w["net"].to_numpy(float))
        parts[k] = {"name": NAMES.get(k, k), "trades": int(len(w)), "net": float(dn.sum()), "gross": float(dg.sum()),
                    "mean_net": float(w["net"].mean()) if len(w) else None, "mean_gross": float(w["gross"].mean()) if len(w) else None,
                    "sharpe": K.sharpe(dn.to_numpy()), "sortino": K.sortino(dn.to_numpy()), "from": max(lo, starts.get(k, lo))}
    N, G = pd.DataFrame(net), pd.DataFrame(gross)
    book, bg = N.sum(axis=1), G.sum(axis=1)
    x, xg = book.to_numpy(float), bg.to_numpy(float)
    c_ = np.cumsum(x)
    yrs = book.index.str[:4]
    tot = float(x.sum())
    top = book.sort_values(ascending=False)
    rho = N.corr().round(4) if len(keys) > 1 else None
    return {"window": [lo, hi], "members": list(keys), "calendar_sessions": int(len(cal)), "parts": parts,
            "book": {"net": tot, "gross": float(xg.sum()), "net_per_year": float(tot / (len(x) / 252)),
                     "sharpe_net": K.sharpe(x), "sortino_net": K.sortino(x), "sharpe_gross": K.sharpe(xg), "sortino_gross": K.sortino(xg),
                     "daily_sd_usd": float(np.std(x, ddof=1)), "exposure_trade_day_share": float((x != 0).mean()),
                     "max_dd_closed_usd": float(np.max(np.maximum.accumulate(np.r_[0.0, c_])[1:] - c_)),
                     "trade_days": int((x != 0).sum()), "by_year": {y: float(x[yrs == y].sum()) for y in sorted(set(yrs))},
                     "by_member_share": {k: (parts[k]["net"] / tot if tot else None) for k in keys},
                     "largest_days": [[d, float(v)] for d, v in top.head(5).items()],
                     "worst_days": [[d, float(v)] for d, v in top.tail(5).items()],
                     "top5_days_share": float(top.head(5).sum() / tot) if tot > 0 else None,
                     "max_concurrent_mnq_days": int(((N[[k for k in keys if k != "L"]] != 0).sum(axis=1)).max())},
            "rho_daily": rho.to_dict() if rho is not None else None,
            "trades_pooled": dist(np.concatenate(pooled)), "trade_days_dist": dist(x[x != 0]),
            "_book": book}


def g4(book: pd.Series, keys: list[str]) -> dict[str, Any]:
    """D734's G4, with each member's own latest exit time for P2."""
    x = book.to_numpy(float)
    exits = sorted({EXITS[k] for k in keys})
    p2 = {v: H.p2_flatten(exits, v) for v in K.VENUES}
    p3 = H.p3(x, K.ACCOUNT)
    p3b = K.p3b_a1(x, p3)
    sd = float(np.std(x, ddof=1))
    plan = H.load_venue(K.P4_COST_VENUE)
    cost = float(plan.fee_eval + plan.fee_activation)
    prof, life = H.expected_profit_before_breach_usd(K.sharpe(x), sd, K.ACCOUNT, K.TRAIL)
    try:
        p1: Any = H.p1_size(x, K.TRAIL)
    except ValueError as e:                                  # a book that never draws down has no P1 answer (D48)
        p1 = {"no_answer": str(e)}
    out = {"exits_et": exits, "P2": p2, "P2_pass": all(p2.values()),
           "P3": {k: p3[k] for k in ("p3a_breaches", "p3a_breaches_per_year", "p3a_pass", "p3c_worst_day_usd",
                                      "p3c_share_of_loss_budget", "daily_sigma_usd", "life_dd_only_sessions")},
           "P3b_A1": p3b, "P3_pass": bool(p3["p3a_pass"] and p3b["pass"]),
           "P4": {"expected_profit_before_breach_usd": prof, "expected_life_days": life, "account_cost_usd": cost,
                  "cost_venue": K.P4_COST_VENUE},
           "P4_pass": bool(math.isfinite(prof) and prof > cost),
           "P1_reported": p1, "P5_reported": K.p5_largest_day_share(book),
           "P6": {v: bool(H.venue_record(v)["automation_permitted_funded"]) for v in K.VENUES}}
    out["holds"] = bool(out["P2_pass"] and out["P3_pass"] and out["P4_pass"] and all(out["P6"].values()))
    return out


def gates(verdicts: dict[str, str], book: dict[str, Any] | None, g1_needed: bool = True) -> dict[str, Any]:
    """D792 s.3. `book` is the passes-only book's score (None when fewer than one member passes)."""
    passing = [k for k in MEMBERS if verdicts.get(k) == "PASS"]
    g1 = {"verdicts": verdicts, "passing": passing, "holds": len(passing) >= 2}
    if book is None:
        return {"G1": g1, "reading": "NOT ADMITTED", "failing": ["G1"]}
    x = book["_book"].to_numpy(float)
    a, b = K.halves(x)
    g2 = {"net": float(x.sum()), "holds": bool(x.sum() > 0)}
    g3 = {"first_half_net": a, "second_half_net": b, "holds": bool(a > 0 and b > 0)}
    g4_ = g4(book["_book"], book["members"])
    out = {"G1": g1, "G2": g2, "G3": g3, "G4": g4_}
    if not g1_needed:
        out.pop("G1")
    failing = [k for k, g in out.items() if not g["holds"]]
    if g1_needed and len(passing) == 1:
        reading = "ONE MEMBER"
    else:
        reading = "ADMITTED" if not failing else "NOT ADMITTED"
    out.update({"failing": failing, "reading": reading})
    return out


def strip(r: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in r.items() if not k.startswith("_")}


def show(tag: str, r: dict[str, Any]) -> None:
    b = r["book"]
    print(f"[{tag}] window {r['window']}  members {r['members']}  calendar {r['calendar_sessions']}")
    for k, p in r["parts"].items():
        print(f"    {k}: {p['trades']:5d} trades  net ${p['net']:>11,.2f}  gross ${p['gross']:>11,.2f}  Sharpe {p['sharpe']:+.2f}  from {p['from']}")
    print(f"    BOOK net ${b['net']:,.2f} (gross ${b['gross']:,.2f}); Sharpe {b['sharpe_net']:+.2f} / Sortino {b['sortino_net']:+.2f} "
          f"(gross {b['sharpe_gross']:+.2f} / {b['sortino_gross']:+.2f}); max DD ${b['max_dd_closed_usd']:,.0f}; "
          f"trade days {b['trade_days']}; most MNQ members on one day {b['max_concurrent_mnq_days']}")
    print("    by year:", {y: round(v) for y, v in b["by_year"].items()})


# ================================================================================ rehearsal (in-sample, once)
def rehearse() -> int:
    need(not REHEARSAL.exists(), f"[RUN] {REHEARSAL.name} exists: the rehearsal is run-once")
    t0 = time.time()
    trades, frames, walls = {}, {}, {}
    for k in MEMBERS:
        t1 = time.time()
        trades[k], frames[k] = IN_BUILDERS[k]()
        K.seal(trades[k]["session"], "2023-12-31", f"{k} trades")
        walls[k] = round(time.time() - t1, 1)
        print(f"  {k}: {len(trades[k])} in-sample trades (known answer reproduced) in {walls[k]} s", flush=True)
    keys = list(MEMBERS)
    r = score_book(trades, frames, keys, IN_LO, IN_HI, {})
    # D734's in-sample F and C on the same span, exactly: the shared machinery is the frozen one
    need(abs(r["parts"]["F"]["net"] - K.D732_F_TOTAL) < 1e-3 and r["parts"]["F"]["trades"] == 271, "[D734] F differs from D734's")
    d734 = json.loads(K.OUT_REHEARSAL.read_text(encoding="utf-8"))["parts"]
    need(r["parts"]["C"]["trades"] == d734["C"]["trades"] and abs(r["parts"]["C"]["net"] - d734["C"]["net"]) < 1e-6,
         f"[D734] C differs from D734's rehearsal: {r['parts']['C']['trades']} / {r['parts']['C']['net']}")
    gt = gates({k: "PASS" for k in keys}, r)
    doc = {"mode": "IN-SAMPLE REHEARSAL (2018-05-14 -> 2023-12-29), all five members in: the gates' machinery proved, "
                   "not evidence (D792 s.4)", "spec": SPEC_REL, "runner_sha256": sha(Path(__file__).resolve()),
           "prereg_sha256": sha(SPEC), "known_answers": "every member's reproduced exactly before scoring",
           "member_walls_s": walls, "costs": COSTS_NOTE, "score": strip(r), "gates": gt,
           "wall_s": round(time.time() - t0, 1)}
    jdump(REHEARSAL, doc)
    show("REHEARSAL", r)
    print(f"  gates: G2 {gt['G2']['holds']}  G3 {gt['G3']['holds']}  G4 {gt['G4']['holds']}  -> {gt['reading']}")
    print(f"wrote {REHEARSAL.relative_to(REPO)} in {doc['wall_s']} s")
    return 0


# ================================================================================ freeze
def member_freezes() -> dict[str, str]:
    return {"D716": "data/FROZEN_vault_d716_nq_f2.json", "D680": "data/FROZEN_vault_d680_nq_compression.json",
            "D737": "data/FROZEN_vault_d737_nq_leads_the_dow.json", "D776": "data/FROZEN_vault_d776_cpi_nfp_fade.json",
            "D781": "data/FROZEN_vault_d781_l4_auction_fade.json", "D734": "data/FROZEN_vault_d734_nq_book.json"}


def freeze() -> int:
    need(not FROZEN.exists(), f"[FREEZE] {FROZEN.name} exists: the freeze is written once")
    need(REHEARSAL.exists(), "[FREEZE] run --rehearse first")
    reh = json.loads(REHEARSAL.read_text(encoding="utf-8"))
    me = sha(Path(__file__).resolve())
    need(reh["runner_sha256"] == me and reh["prereg_sha256"] == sha(SPEC),
         "[FREEZE] the rehearsal was run on a different runner or record")
    for p in member_freezes().values():
        need((REPO / p).exists(), f"[FREEZE] {p} is missing: every member is frozen before the book")
    b = reh["score"]["book"]
    doc = {"record": SPEC_REL, "runner": "scripts/vault_d792_prop_book.py", "runner_sha256": me, "prereg_sha256": sha(SPEC),
           "hashed_unchanged": {p: sha(REPO / p) for p in HASHED},
           "member_freezes": {k: {"path": p, "sha256": sha(REPO / p)} for k, p in member_freezes().items()},
           "forward_writers_reported": {p: sha(REPO / p) for p in FORWARD_WRITERS},
           "rehearsal_sha256": sha(REHEARSAL),
           "known_answer_in_sample": {"window": reh["score"]["window"], "calendar_sessions": reh["score"]["calendar_sessions"],
                                      "book_net": b["net"], "book_sharpe": b["sharpe_net"],
                                      "parts": {k: [p["trades"], p["net"]] for k, p in reh["score"]["parts"].items()},
                                      "reading": reh["gates"]["reading"]},
           "programme_slot": None, "slot_note": "no slot: alpha stays with the members' lines (slots 1, 2, 7, 9, 10); D792 s.0",
           "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    jdump(FROZEN, doc)
    print(json.dumps({k: doc[k] for k in ("runner_sha256", "prereg_sha256", "known_answer_in_sample")}, indent=1))
    return 0


def check_freeze() -> dict[str, Any]:
    need(FROZEN.exists(), "[FREEZE] D792 is not frozen")
    fz = json.loads(FROZEN.read_text(encoding="utf-8"))
    need(fz["runner_sha256"] == sha(Path(__file__).resolve()) and fz["prereg_sha256"] == sha(SPEC),
         "[FREEZE] this runner or D792 has moved since the freeze")
    for p, h in fz["hashed_unchanged"].items():
        need(sha(REPO / p) == h, f"[FREEZE] {p} has moved since the freeze")
    for k, m in fz["member_freezes"].items():
        need(sha(REPO / m["path"]) == m["sha256"], f"[FREEZE] {k}'s freeze file has moved since D792's freeze")
    return fz


# ================================================================================ the vault (the joint run, once)
def v_F(end: str) -> tuple[pd.DataFrame, np.ndarray, str, dict]:
    import vault_d716_nq_f2 as F
    K.check_d716_freeze(F)
    need(F.VAULT_OUT.exists(), "[ORDER] D716's --vault has not run")
    r716 = json.loads(F.VAULT_OUT.read_text(encoding="utf-8"))
    result = r716["family"]["result"]
    key = K.F_LINES.get(result, "B")
    bd = F.build(F.VAULT_END, vault_open=True)
    net = np.asarray(bd["net"], float)
    rep = {}
    for part, lo, hi in (("held_slice", F.UNSEEN_FROM, "2025-02-28"), ("vault", F.VAULT_FROM, F.VAULT_END)):
        Bm, Am = F.masks(bd, lo, hi)
        got = F.V.score(net[Am if key == "A" else Bm])
        rec = r716["parts"][part][key]
        need(got["trades"] == rec["trades"] and got.get("mean_net") == rec.get("mean_net"),
             f"[REPRODUCE] D716 {part} {key}: {got.get('trades')}/{got.get('mean_net')} != {rec.get('trades')}/{rec.get('mean_net')}")
        rep[part] = got
    Bm, Am = F.masks(bd, VAULT_FROM, end)
    m = Am if key == "A" else Bm
    t = tframe(bd["sn"][m], net[m], bd["Xn"]["gross"].to_numpy(float)[m])
    return t, day_str(bd["sn"]), ("PASS" if result in K.F_LINES else "FAIL or UNRESOLVED"), {
        "family_result": result, "line": key, "reproduced": rep}


def v_C(end: str) -> tuple[pd.DataFrame, np.ndarray, str, dict]:
    """D734's vault C, unchanged: the joint wrapper's checked files, the frozen book() under the held cut."""
    import joint_d680_vault as J
    J.check_freeze()
    V680 = J.frozen_runner()
    need(V680.VAULT_OUT.exists(), "[ORDER] D680's joint-wrapper --run-vault has not run")
    r680 = json.loads(V680.VAULT_OUT.read_text(encoding="utf-8"))
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
    v = ((sess >= C_FROM) & (sess <= K.VAULT_END)).to_numpy()
    c1 = v & (tr["ctier"].to_numpy(float) < 1 / 3)
    got = V680.score(tr.loc[c1, "gross"].to_numpy(float), tr.loc[c1, "net"].to_numpy(float), R)
    rc = r680["C1"]
    need(got["trades"] == rc["trades"] and got.get("gross_bp") == rc.get("gross_bp") and got.get("net_bp") == rc.get("net_bp"),
         f"[REPRODUCE] D680 vault C1: {got} != recorded {rc}")
    keep = c1 & (sess <= end).to_numpy()
    return c_trades(tr, keep), day_str(np.asarray(sessions, str)), str(rc.get("verdict")), {"reproduced": got}


def v_D(end: str) -> tuple[pd.DataFrame, np.ndarray, str, dict]:
    import vault_d737_nq_leads_the_dow as Dw
    Dw.check_freeze(json.loads(Dw.FROZEN.read_text(encoding="utf-8")))
    need(Dw.OUT.exists(), "[ORDER] D737's --vault has not run")
    out = json.loads(Dw.OUT.read_text(encoding="utf-8"))
    cst = Dw.cost()
    c_in = Dw.in_sample(REPO / "data")
    Dw.check_known(c_in, cst)
    cv = Dw.vault_load(REPO / "data", out["end"])
    Dw.overlap_check(c_in, cv)
    w = Dw.window(cv, Dw.VAULT_FROM, out["end"])
    net = w["g"] - cst
    need(len(net) == out["score"]["trades"] and float(net.mean()) == out["score"]["mean_net"],
         f"[REPRODUCE] D737 vault: {len(net)}/{float(net.mean())} != {out['score']['trades']}/{out['score']['mean_net']}")
    days = day_str(w["days"])
    t = tframe(days[w["d"]], net, w["g"])
    return t[t["session"] <= end], days, str(out["verdict"]), {"reproduced": [int(len(net)), float(net.mean())], "end": out["end"]}


def v_R(end: str) -> tuple[pd.DataFrame, np.ndarray, str, dict]:
    import vault_d776_cpi_nfp_fade as Rv
    Rv.check_freeze(json.loads(Rv.FROZEN.read_text(encoding="utf-8")))
    need(Rv.OUT.exists(), "[ORDER] D776's --vault has not run")
    out = json.loads(Rv.OUT.read_text(encoding="utf-8"))
    bv = Rv.read_vault(Rv.JOINT_FIX, Rv.IN_LO, out["end"])
    Uv, _ = Rv.trades(bv, Rv.release_window(Rv.IN_LO, out["end"]))
    Rv.check_known(Rv.known(Uv), out["known_answer_reproduced_on_both_inputs"])
    W = Uv[(Uv.index >= Rv.VAULT_FROM) & (Uv.index <= out["end"])]
    R = W[W["is_rel"]]
    net = R["gross"] - Rv.COST
    need(len(R) == out["score"]["trades"] and float(net.mean()) == out["score"]["mean_net"],
         f"[REPRODUCE] D776 vault: {len(R)}/{float(net.mean())} != {out['score']['trades']}/{out['score']['mean_net']}")
    t = tframe(R.index, net, R["gross"])
    return t[t["session"] <= end], day_str(Uv.index), str(out["verdict"]), {"reproduced": [int(len(R)), float(net.mean())], "end": out["end"]}


def v_L(end: str) -> tuple[pd.DataFrame, np.ndarray, str, dict]:
    import vault_d781_l4_auction_fade as Lv
    Lv.check_freeze(json.loads(Lv.FROZEN.read_text(encoding="utf-8")))
    need(Lv.OUT.exists(), "[ORDER] D781's --vault has not run")
    out = json.loads(Lv.OUT.read_text(encoding="utf-8"))
    Dv = Lv.frame(Lv.read_vault(Lv.JOINT_FIX, Lv.D7.START, out["end"]))
    Lv.check_known(Lv.known(Dv, Lv.IN_HI), out["known_answer_reproduced_on_both_inputs"])
    t, frame_s1 = l_trades(Dv, Lv.COST, Lv.VAULT_FROM, out["end"])
    W = Dv[Dv["cvalid"] & (Dv.index >= Lv.VAULT_FROM) & (Dv["s1"] <= out["end"])]       # D781's score(), its expression
    m781 = float((W[W["base"]]["gross"] - Lv.COST).mean())
    need(len(t) == out["score"]["trades"] and m781 == out["score"]["mean_net"],
         f"[REPRODUCE] D781 vault: {len(t)}/{m781} != {out['score']['trades']}/{out['score']['mean_net']}")
    return t[t["session"] <= end], frame_s1, str(out["verdict"]), {"reproduced": [int(len(t)), float(t["net"].mean())], "end": out["end"]}


V_BUILDERS = {"F": v_F, "D": v_D, "R": v_R, "C": v_C, "L": v_L}


def refuse(word: str | None) -> bool:
    return not (word or "").strip()


def assemble(trades: dict[str, pd.DataFrame], frames: dict[str, np.ndarray], verdicts: dict[str, str],
             lo: str, hi: str) -> dict[str, Any]:
    """The passes-only book (primary), the fixed five (beside), and the sub-window (beside)."""
    starts = {"C": C_FROM}
    passing = [k for k in MEMBERS if verdicts[k] == "PASS"]
    prim = score_book(trades, frames, passing, lo, hi, starts) if passing else None
    gt = gates(verdicts, prim)
    fixed = score_book(trades, frames, list(MEMBERS), lo, hi, starts)
    sub = score_book(trades, frames, passing, SUB_FROM, hi, starts) if passing else None
    return {"reading": gt["reading"], "gates": gt, "book": strip(prim) if prim else None,
            "beside_fixed_five": {"score": strip(fixed), "gates_g2_g4": gates({}, fixed, g1_needed=False)},
            "beside_sub_window": strip(sub) if sub else None, "_prim": prim}


def vault(word: str | None) -> int:
    if refuse(word):
        print("refused: the book is scored only in the joint run, on the principal's word (D792 s.4)")
        return REFUSED
    check_freeze()
    need(not VAULT_OUT.exists(), "[VAULT] the book has already been scored; a second opening is refused")
    need(K.VAULT_OUT.exists(), "[ORDER] D734's --vault has not run")
    t0 = time.time()
    import vault_d737_nq_leads_the_dow as Dw
    import vault_d776_cpi_nfp_fade as Rv
    import vault_d781_l4_auction_fade as Lv
    ends = {}
    trades, frames, verdicts, info = {}, {}, {}, {}
    for k, mod in (("D", Dw), ("R", Rv), ("L", Lv)):   # the members with a recorded end (an --accept-end is the principal's)
        need(mod.OUT.exists(), f"[ORDER] {NAMES[k]}: its --vault has not run")
        ends[k] = json.loads(mod.OUT.read_text(encoding="utf-8"))["end"]
    hi = min([VAULT_END] + list(ends.values()))
    for k in MEMBERS:
        trades[k], frames[k], verdicts[k], info[k] = V_BUILDERS[k](hi)
        print(f"  {k}: verdict {verdicts[k]}; {len(trades[k])} trades in the window (recorded result reproduced)", flush=True)
    res = assemble(trades, frames, verdicts, VAULT_FROM, hi)
    prim = res.pop("_prim")
    d734 = json.loads(K.VAULT_OUT.read_text(encoding="utf-8"))
    res.update({"mode": "THE VAULT (the joint run)", "spec": SPEC_REL, "principals_word": word, "window": [VAULT_FROM, hi],
                "member_ends": ends, "members": info, "verdicts": verdicts,
                "d734_reported": {"reading": d734["gates"]["reading"], "book_net": d734["book"]["net"]},
                "candidate_rule": "D792 s.3: when both read ADMITTED, D792's book is the candidate; when one does, that one's; "
                                  "the entry is on the principal's word", "wall_s": round(time.time() - t0, 1)})
    jdump(VAULT_OUT, res)
    if prim:
        show("VAULT passes-only", prim)
    print(f"  READING: {res['reading']}  (passing {res['gates']['G1']['passing']}; failing gates {res['gates'].get('failing')})")
    return 0


# ================================================================================ the forward read (once, >= 2027-09-30)
def ledger(k: str, path: Path, line: str | None) -> tuple[pd.DataFrame, np.ndarray]:
    x = pd.read_csv(path, encoding="utf-8", dtype=str)
    dcol = "day" if "day" in x.columns else "session"
    if k == "L":
        frame_ = day_str(x.loc[x["s1"].fillna("").str.len() > 0, "s1"])
        tr = x[x["status"] == "trade"]
        book_day = tr["s1"]
    else:
        frame_ = day_str(x[dcol])
        tr = x[x["status"] == "trade"]
        if k == "F" and line == "A":
            tr = tr[tr["es_agrees"].astype(str).str.lower() == "true"]
        book_day = tr[dcol]
    t = tframe(book_day, pd.to_numeric(tr["net_usd"]), pd.to_numeric(tr["gross_usd"]))
    return t, frame_


def forward(word: str | None, today: str | None = None, fwd_dir: Path = FWD) -> int:
    if refuse(word):
        print("refused: the forward read runs once, on the principal's word (D792 s.5)")
        return REFUSED
    today = today or dt.date.today().isoformat()
    need(today >= FORWARD_TO, f"[FORWARD] the read is on or after {FORWARD_TO}; today is {today}")
    fz = check_freeze()
    need(VAULT_OUT.exists(), "[ORDER] D792's vault read has not run")
    need(not FORWARD_OUT.exists(), "[FORWARD] the forward read has already run; a second is refused")
    v = json.loads(VAULT_OUT.read_text(encoding="utf-8"))
    passing = v["gates"]["G1"]["passing"]
    line = v["members"]["F"]["line"]
    trades, frames = {}, {}
    for k in MEMBERS:
        p = fwd_dir / LEDGERS[k]
        need(p.exists(), f"[FORWARD] {p.name} is missing")
        trades[k], frames[k] = ledger(k, p, line)
        need(not (trades[k]["session"] < FORWARD_FROM).any(), f"[FORWARD] {k}: a trade before {FORWARD_FROM}")
    starts: dict[str, str] = {}
    out: dict[str, Any] = {"mode": "THE FORWARD READ", "spec": SPEC_REL, "principals_word": word, "today": today,
                           "window": [FORWARD_FROM, FORWARD_TO], "vault_reading": v["reading"], "members": passing,
                           "forward_writers_moved": [p for p, h in fz["forward_writers_reported"].items() if sha(REPO / p) != h]}
    fixed = score_book(trades, frames, list(MEMBERS), FORWARD_FROM, FORWARD_TO, starts)
    out["beside_fixed_five"] = {"score": strip(fixed), "gates_g2_g4": gates({}, fixed, g1_needed=False)}
    if len(passing) >= 1:
        b = score_book(trades, frames, passing, FORWARD_FROM, FORWARD_TO, starts)
        g = gates({}, b, g1_needed=False)
        holds = not g["failing"]
        out.update({"book": strip(b), "gates": g})
        if v["reading"] == "ADMITTED":
            out["outcome"] = "CONFIRMED" if holds else "RETIRE (on the principal's word)"
        elif len(passing) >= 2:
            out["outcome"] = "REPORTED (vault NOT ADMITTED): evidence for a later record"
        else:
            out["outcome"] = "NOT SCORED AS A BOOK (fewer than two members passed); the member's forward line is reported"
    else:
        out["outcome"] = "NOT SCORED AS A BOOK (no member passed)"
    jdump(FORWARD_OUT, out)
    print(f"[FORWARD] {out['outcome']}")
    return 0


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fired: list[str] = []

    def expect(fn: Callable[[], Any], what: str) -> None:
        try:
            fn()
        except (D792Error, K.D734Error) as e:
            print(f"  RAISES  {what}: {str(e)[:100]}")
            fired.append(what)
            return
        raise SystemExit(f"SELFTEST FAILED: did not raise: {what}")

    rng = np.random.default_rng(792)
    cal = pd.bdate_range("2024-01-02", "2026-09-18").strftime("%Y-%m-%d").to_numpy()
    def synth(step: int, off: int, mu: float, sd: float) -> pd.DataFrame:
        s = cal[off::step]
        g = rng.normal(mu + 4, sd, len(s))
        return tframe(s, g - 4.0, g)
    trades = {"F": synth(5, 0, 20, 40), "D": synth(2, 1, 12, 90), "R": synth(21, 3, 30, 120), "C": synth(4, 2, 15, 50),
              "L": synth(6, 4, 12, 60)}
    frames = {k: cal for k in MEMBERS}
    v_all = {k: "PASS" for k in MEMBERS}

    # 1. the book is the sum of its members; C counts only from 2025-03-01
    a = assemble(trades, frames, v_all, VAULT_FROM, VAULT_END)
    c_in = trades["C"][trades["C"]["session"] >= C_FROM]["net"].sum()
    want = sum(trades[k]["net"].sum() for k in MEMBERS if k != "C") + c_in
    need(abs(a["book"]["book"]["net"] - want) < 1e-6, "[BOOK] the book is not the members' sum with C from 2025-03-01")
    need(a["book"]["parts"]["C"]["from"] == C_FROM and a["book"]["parts"]["C"]["trades"] == int((trades["C"]["session"] >= C_FROM).sum()),
         "[BOOK] C was not cut at 2025-03-01")
    print(f"  PASS    the book is the members' sum; C counts from {C_FROM} ({a['reading']}, calendar {a['book']['calendar_sessions']})")
    # 2. passes only: a FAIL and an UNRESOLVED member are out of the primary book and in the fixed five
    v2 = dict(v_all, D="FAIL", L="UNRESOLVED")
    b = assemble(trades, frames, v2, VAULT_FROM, VAULT_END)
    need(b["book"]["members"] == ["F", "R", "C"] and b["beside_fixed_five"]["score"]["members"] == list(MEMBERS),
         "[G1] passes-only membership is wrong")
    print("  PASS    passes only: FAIL and UNRESOLVED members are out; the fixed five is reported beside")
    # 3. G1: one PASS reads ONE MEMBER; none reads NOT ADMITTED with no book
    one = assemble(trades, frames, {k: ("PASS" if k == "R" else "FAIL") for k in MEMBERS}, VAULT_FROM, VAULT_END)
    need(one["reading"] == "ONE MEMBER" and not one["gates"]["G1"]["holds"], "[G1] one PASS must read ONE MEMBER")
    none = assemble(trades, frames, {k: "FAIL" for k in MEMBERS}, VAULT_FROM, VAULT_END)
    need(none["reading"] == "NOT ADMITTED" and none["book"] is None, "[G1] no PASS must read NOT ADMITTED with no book")
    print("  PASS    G1: one PASS reads ONE MEMBER; no PASS reads NOT ADMITTED")
    expect(lambda: need(gates({"F": "PASS", "R": "FAIL"}, score_book(trades, frames, ["F"], VAULT_FROM, VAULT_END, {}))["G1"]["holds"],
                        "[G1] one PASS holds G1"), "G1 with one PASS")
    # 4. G3: a losing second half fails
    bad = {k: v.copy() for k, v in trades.items()}
    bad["F"].loc[bad["F"]["session"] > "2025-06-01", "net"] = -500.0
    expect(lambda: need(gates(v_all, score_book(bad, frames, list(MEMBERS), VAULT_FROM, VAULT_END, {"C": C_FROM}))["G3"]["holds"],
                        "[G3] a losing half holds"), "G3: a losing second half")
    # 5. daily: two trades on one session, a trade off the calendar, a session past the seal
    expect(lambda: K.daily(pd.DataFrame({"session": [cal[0], cal[0]], "net": [1.0, 2.0]}), cal, "x"), "daily: two trades on a session")
    expect(lambda: K.daily(pd.DataFrame({"session": ["2030-01-02"], "net": [1.0]}), cal, "x"), "daily: a trade off the calendar")
    expect(lambda: K.seal(["2023-12-29", "2024-01-02"], IN_HI, "x"), "seal: a session after the in-sample window")
    # 6. L books on its exit session s1, and two exits on one session raise
    D = pd.DataFrame({"cvalid": [True, True, True], "base": [True, False, True], "s1": ["2024-01-03", "2024-01-04", "2024-01-05"],
                      "gross": [10.0, 5.0, -3.0]}, index=["2024-01-02", "2024-01-03", "2024-01-04"])
    lt, lf = l_trades(D, 3.76, "2024-01-01", "2024-12-31")
    need(list(lt["session"]) == ["2024-01-03", "2024-01-05"] and list(lf) == ["2024-01-03", "2024-01-04", "2024-01-05"]
         and abs(lt["net"].sum() - (7.0 - 2 * 3.76)) < 1e-12, "[L] the trade is not booked on its exit session")
    D2 = D.copy()
    D2["s1"] = ["2024-01-03", "2024-01-03", "2024-01-03"]
    expect(lambda: l_trades(D2, 3.76, "2024-01-01", "2024-12-31"), "L: two trades exiting on one session")
    print("  PASS    L books on its exit session s1")
    # 7. P2: every member's exit passes the 16:10 flatten; an exit after it fails
    need(g4(a["_prim"]["_book"], list(MEMBERS))["P2_pass"], "[P2] the members' exits fail the 16:10 flatten")
    expect(lambda: need(H.p2_flatten(["10:00", "16:20"], "topstep_50k"), "[P2] 16:20 passes"), "P2: an exit after 16:10")
    # 8. refusals: no word (exit 2) for --vault and --forward; the forward read before its date
    need(vault("") == REFUSED and vault(None) == REFUSED and forward("") == REFUSED, "[REFUSE] an empty word must exit 2")
    print("  PASS    --vault and --forward refuse without the principal's word (exit 2), before reading anything")
    expect(lambda: forward("yes", today="2027-09-29"), "forward: before 2027-09-30")
    # 9. the forward ledgers' readers on synthetic files: status, es_agrees (line A), L on s1
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        pd.DataFrame({"session": ["2026-09-22", "2026-09-23", "2026-09-24"], "status": ["trade", "trade", "no take"],
                      "es_agrees": ["True", "False", ""], "gross_usd": ["10", "20", ""], "net_usd": ["6", "16", ""]}
                     ).to_csv(d / "f.csv", index=False, encoding="utf-8")
        tA, _ = ledger("F", d / "f.csv", "A")
        tB, fB = ledger("F", d / "f.csv", "B")
        need(list(tA["session"]) == ["2026-09-22"] and list(tB["session"]) == ["2026-09-22", "2026-09-23"] and len(fB) == 3,
             "[LEDGER] F's line A / B selection is wrong")
        pd.DataFrame({"session": ["2026-09-21", "2026-09-22"], "s1": ["2026-09-22", "2026-09-23"], "status": ["trade", "no trade"],
                      "gross_usd": ["9", ""], "net_usd": ["5.24", ""]}).to_csv(d / "l.csv", index=False, encoding="utf-8")
        tL, fL = ledger("L", d / "l.csv", None)
        need(list(tL["session"]) == ["2026-09-22"] and list(fL) == ["2026-09-22", "2026-09-23"], "[LEDGER] L is not booked on s1")
    print("  PASS    the forward readers: F's line A takes only ES-agreeing trades; L books on s1")
    # 10. the report's trims: a symmetric 1% trim on a fat two-sided sample
    x = np.r_[np.full(98, 1.0), 100.0, -100.0]
    dd = dist(x)
    need(dd["trim_k_each_tail"] == 1 and dd["mean_trimmed"] == 1.0 and dd["mean_ex_top"] < dd["mean_trimmed"] < dd["mean_ex_bottom"],
         "[DIST] the symmetric trim is wrong")
    print("  PASS    the trade distribution's three trimmed means")
    print(f"SELFTEST PASS: {len(fired)} canaries raised")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    for m in ("selftest", "rehearse", "freeze", "vault", "forward"):
        g.add_argument(f"--{m}", action="store_true")
    ap.add_argument("--principals-word", default=None)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.rehearse:
        return rehearse()
    if a.freeze:
        return freeze()
    if a.vault:
        return vault(a.principals_word)
    return forward(a.principals_word)


if __name__ == "__main__":
    sys.exit(main())
