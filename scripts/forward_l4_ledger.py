"""The forward ledger for base L4 (D781's frozen line: D778's base book, the M2K closing-auction fade), D784.

    python scripts/forward_l4_ledger.py --selftest
    python scripts/forward_l4_ledger.py --prove      # in-sample only: the splice and the Sierra source
    python scripts/forward_l4_ledger.py --ledger     # AFTER the joint run only (refuses before D781's vault output exists)

The construction is D778's `frame`, imported unchanged; nothing about the trade is re-implemented here. What this adds
is the input path:
- HISTORY: the joint run's rebuilt YM/RTY fixture (data/joint_run/d781/fut_opening_globex_1m_ym_rty.csv.gz, through
  2026-09-18). Its q80 gate needs 250 prior sessions (at least 120), and the 200-session warm-up needs 200, so the
  forward sessions cannot be scored on forward history alone until about mid-2027.
- FORWARD: the forward recorder's RTY Globex sessions (data/raw/forward/fut_RTY_fwd_globex_1m.csv.gz, sessions from
  2026-09-21; Sierra contract names such as RTYZ26-CME are normalised to Databento's RTYZ6).

Both are read with D778's loader's filters (root, the bars D778 reads, a 0-4 day stamp lag), concatenated, and passed to
D778's frame. A session S is scored when S is a forward session; its exit day S+1 must also be recorded.

THE SEALS. --ledger reads the vault-window history only once D781's vault output exists (the joint run has scored it),
and refuses otherwise. Forward rows before 2026-09-21 raise. --prove reads only 2016-2023 (D778's loader) and Sierra's
2023-04 -> 2023-12 files (the recorder's own validation window).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d777_post_close_fade as D7  # noqa: E402
import stage0_d778_auction_fade_trend_filter as D8  # noqa: E402

ROOT = "RTY"
_, MULT, COST = D7.ROOTS[ROOT]
FORWARD_FROM, VAULT_END = "2026-09-21", "2026-09-18"
MAIN = D7.MAIN
HISTORY = MAIN / "data" / "joint_run" / "d781" / "fut_opening_globex_1m_ym_rty.csv.gz"
D781_OUT = MAIN / "data" / "vault_d781_l4_auction_fade.json"
FORWARD = MAIN / "data" / "raw" / "forward" / "fut_RTY_fwd_globex_1m.csv.gz"
LEDGER = REPO / "data" / "forward" / "l4_forward.csv"
REVISIONS = REPO / "data" / "forward" / "l4_forward_revisions.csv"
PROOF = REPO / "data" / "forward" / "l4_ledger_proof.json"
# D794 (the principal, 2026-10-04: "Yes add it to the ledgers"): the cost measured at this line's own fills, reported
# BESIDE the frozen net, never instead of it. The mean of data/diag_d794_fill_cost.json's M2K cost line, asserted below.
COST_MEASURED = 4.991972
D794_JSON = REPO / "data" / "diag_d794_fill_cost.json"
COLS = ["session", "s1", "contract", "c_pts", "thr_pts", "gated", "side", "entry", "exit", "gross_usd", "net_usd",
        "net_measured_cost_usd", "status"]
SPLICE_AT = "2022-12-30"                                  # the in-sample splice proof's last history session
SIERRA_NAME = re.compile(r"^([A-Z]+)([FGHJKMNQUVXZ])(\d{2})-[A-Z]+$")


class LedgerError(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise LedgerError(msg)


# ================================================================================ input
def normalise_contract(k: str) -> str:
    """Sierra's RTYZ26-CME -> Databento's RTYZ6 (root, month code, last digit of the year); others unchanged."""
    m = SIERRA_NAME.match(str(k))
    return f"{m.group(1)}{m.group(2)}{m.group(3)[-1]}" if m else str(k)


def read_bars(path: Path, lo: str, hi: str) -> pd.DataFrame:
    """D778's loader's filters on any opening-layout file, sessions in [lo, hi]."""
    parts = []
    for ch in pd.read_csv(path, encoding="utf-8", chunksize=2_000_000, dtype={"session": str, "et": str, "hhmm": str,
                                                                               "contract": str},
                          usecols=["root", "session", "et", "hhmm", "contract", "close"]):
        ch = ch[(ch["root"] == ROOT) & (ch["session"] >= lo) & (ch["session"] <= hi) & ch["hhmm"].isin(D8.BARS)]
        lag = (pd.to_datetime(ch["session"]) - pd.to_datetime(ch["et"].str[:10])).dt.days
        parts.append(ch[(lag >= 0) & (lag <= D7.MAX_GAP)])
    b = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["root", "session", "et", "hhmm", "contract", "close"])
    b["contract"] = b["contract"].map(normalise_contract)
    return b


def splice(hist: pd.DataFrame, fwd: pd.DataFrame) -> pd.DataFrame:
    need(len(hist) > 0 and len(fwd) > 0, "an empty history or forward input")
    h_last, f_first = hist["session"].max(), fwd["session"].min()
    need(h_last < f_first, f"history ({h_last}) and forward ({f_first}) overlap")
    gap = (pd.Timestamp(f_first) - pd.Timestamp(h_last)).days
    need(gap <= D7.MAX_GAP, f"history ends {h_last}, {gap} days before the first forward session {f_first}: the q80 "
                            "threshold and the warm-up would run over a hole (the ledger is owed after the joint run)")
    return pd.concat([hist, fwd], ignore_index=True)


# ================================================================================ the ledger
def ledger_rows(b: pd.DataFrame, first_scored: str) -> pd.DataFrame:
    """D778's frame over the spliced bars; one row per scored session S >= first_scored."""
    D = D8.frame(b, ROOT)
    K = b.groupby("session")["contract"].first()
    rows = []
    for s in D.index[D.index >= first_scored]:
        r = D.loc[s]
        c, thr = r["c"], r["cthr"]
        if pd.isna(c) or c == 0 or pd.isna(thr) or not bool(r["has_trend"]):
            status = "invalid (no closing move, threshold or warm-up)"
        elif pd.isna(r["y"]):
            status = "pending (the exit day is not recorded yet)"
        elif bool(r["base"]):
            status = "trade"
        else:
            status = "no trade (below the q80 gate)"
        trade = status == "trade"
        rows.append({"session": s, "s1": r["s1"] if isinstance(r["s1"], str) else "", "contract": K.get(s, ""),
                     "c_pts": round(float(c), 2) if pd.notna(c) else "", "thr_pts": round(float(thr), 4) if pd.notna(thr) else "",
                     "gated": bool(pd.notna(c) and pd.notna(thr) and c != 0 and abs(c) >= thr),
                     "side": int(r["side"]) if trade else 0, "entry": float(r["ent"]) if trade else "",
                     "exit": float(r["ex"]) if trade else "", "gross_usd": round(float(r["gross"]), 2) if trade else "",
                     "net_usd": round(float(r["gross"]) - COST, 2) if trade else "",
                     "net_measured_cost_usd": round(float(r["gross"]) - COST_MEASURED, 2) if trade else "", "status": status})
    return pd.DataFrame(rows, columns=COLS)


def write_ledger(new: pd.DataFrame) -> int:
    """A recorded row that later changes is never overwritten silently: the old values go to the revisions file."""
    revised = 0
    out = new.astype(str)
    if LEDGER.exists():
        old = pd.read_csv(LEDGER, dtype=str, keep_default_na=False, encoding="utf-8")
        cmp_cols = [c for c in COLS[1:] if c in old.columns]        # a column added later (D794) is not a revision
        old = old.reindex(columns=COLS, fill_value="")
        mm = old.merge(out, on="session", how="inner", suffixes=("_old", "_new"))
        ch = []
        for _, r in mm.iterrows():
            diff = [c for c in cmp_cols if r[f"{c}_old"] != r[f"{c}_new"]]
            if diff and not r["status_old"].startswith("pending"):
                ch.append({"session": r["session"], "changed": ";".join(diff),
                           "recorded_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                           "old": json.dumps({c: r[f"{c}_old"] for c in diff}), "new": json.dumps({c: r[f"{c}_new"] for c in diff})})
        if ch:
            revised = len(ch)
            pd.DataFrame(ch).to_csv(REVISIONS, mode="a", header=not REVISIONS.exists(), index=False, encoding="utf-8")
        lost = old[~old["session"].isin(out["session"])]
        out = pd.concat([out, lost], ignore_index=True).sort_values("session")
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(LEDGER, index=False, encoding="utf-8", lineterminator="\n")
    return revised


def ledger() -> int:
    if not D781_OUT.exists():
        print(f"[L4 ledger] OWED: {D781_OUT.name} does not exist, so the joint run has not scored D781's vault and its "
              f"history ({HISTORY.name}, through {VAULT_END}) may not be read. Nothing was read.")
        return 2
    need(HISTORY.exists(), f"{HISTORY} is missing")
    need(FORWARD.exists(), f"{FORWARD} is missing: the recorder has no RTY Globex sessions yet")
    hist = read_bars(HISTORY, D7.START, VAULT_END)
    fwd = read_bars(FORWARD, FORWARD_FROM, "2099-12-31")
    need(bool((fwd["session"] >= FORWARD_FROM).all()), "seal: a forward session before 2026-09-21")
    b = splice(hist, fwd)
    L = ledger_rows(b, fwd["session"].min())
    revised = write_ledger(L)
    tr = L[L["status"] == "trade"]
    net = pd.to_numeric(tr["net_usd"], errors="coerce")
    net_m = pd.to_numeric(tr["net_measured_cost_usd"], errors="coerce")
    print(f"[L4 ledger] sessions {len(L)} from {L['session'].min()}; trades {len(tr)}, net ${net.sum():.2f}"
          f" (mean {net.mean() if len(tr) else float('nan'):.2f}) at the frozen ${COST:.2f}; ${net_m.sum():.2f} at D794's "
          f"measured ${COST_MEASURED:.2f}; pending {int(L['status'].str.startswith('pending').sum())};"
          f" revisions {revised} -> {LEDGER.relative_to(REPO)}")
    return 0


# ================================================================================ the in-sample proofs
def to_recorder_layout(b: pd.DataFrame, path: Path, sierra_names: bool) -> None:
    """Write bars as the recorder writes its Globex file (columns, `to_csv(index=False)`), optionally with Sierra's
    contract names, so the proof reads exactly what the forward ledger will read."""
    x = b.copy()
    if sierra_names:
        x["contract"] = x["contract"].map(lambda k: f"{k[:-2]}{k[-2]}2{k[-1]}-CME")     # RTYZ3 -> RTYZ23-CME
    for c in ("open", "high", "low", "volume"):
        if c not in x.columns:
            x[c] = x["close"] if c != "volume" else 1
    x[["root", "session", "et", "hhmm", "contract", "open", "high", "low", "close", "volume"]].to_csv(
        path, index=False, encoding="utf-8")


def compare(a: pd.DataFrame, b: pd.DataFrame) -> dict[str, Any]:
    m = a.merge(b, on="session", suffixes=("_a", "_b"))
    ta, tb = m["status_a"] == "trade", m["status_b"] == "trade"
    both = m[ta & tb]
    ga = pd.to_numeric(both["gross_usd_a"], errors="coerce")
    gb = pd.to_numeric(both["gross_usd_b"], errors="coerce")
    return {"sessions": int(len(m)), "status_agree": float((m["status_a"] == m["status_b"]).mean()),
            "trades_a": int(ta.sum()), "trades_b": int(tb.sum()), "trades_both": int(len(both)),
            "side_agree": float((both["side_a"] == both["side_b"]).mean()) if len(both) else None,
            "gross_abs_diff_max": float((ga - gb).abs().max()) if len(both) else None,
            "gross_equal_share": float(((ga - gb).abs() < 1e-9).mean()) if len(both) else None,
            "net_sum_a": round(float(pd.to_numeric(m.loc[ta, "net_usd_a"]).sum()), 2),
            "net_sum_b": round(float(pd.to_numeric(m.loc[tb, "net_usd_b"]).sum()), 2)}


def prove() -> int:
    t0 = time.time()
    out: dict[str, Any] = {"tool": "scripts/forward_l4_ledger.py --prove", "in_sample_only": True}
    full = D8._load_file((D7.ROOTS[ROOT][0], (ROOT,)))           # D778's loader: sessions < 2024-01-01, asserted
    full = full.assign(contract=full["contract"].map(normalise_contract))
    # (a) the splice and the read path: Databento split at SPLICE_AT, the later part written in the recorder's layout
    #     with Sierra contract names and read back; the ledger must equal D778's base book over the later sessions
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "fwd.csv.gz"
        to_recorder_layout(full[full["session"] > SPLICE_AT], p, sierra_names=True)
        fwd = read_bars(p, "2000-01-01", "2099-12-31")
    hist = full[full["session"] <= SPLICE_AT]
    first = fwd["session"].min()
    L = ledger_rows(splice(hist, fwd), first)
    R = ledger_rows(full, first)                                  # the unspliced reference, same code
    D = D8.frame(full, ROOT)
    B = D[D["base"] & (D.index >= first)]
    T = L[L["status"] == "trade"].set_index("session")
    need(list(T.index) == list(B.index), f"splice: the ledger's trade sessions differ from D778's base book ({len(T)} vs {len(B)})")
    need(bool(np.allclose(pd.to_numeric(T["gross_usd"]).to_numpy(), B["gross"].round(2).to_numpy(), atol=1e-9)),
         "splice: the ledger's gross differs from D778's base book")
    need(L.equals(R), "splice: the spliced ledger differs from the unspliced one")
    out["splice"] = {"history_through": SPLICE_AT, "first_scored": first, "sessions": int(len(L)), "trades": int(len(T)),
                     "equal_to_d778_base_book": True, "equal_to_unspliced_ledger": True,
                     "net_sum": round(float(pd.to_numeric(T["net_usd"]).sum()), 2)}
    # (b) the Sierra source: the recorder's own builder over Sierra's 2023 RTY files, on Databento's contract per session
    import record_forward_nq_lines as REC
    fx = D8._load_file((D7.ROOTS[ROOT][0], (ROOT,)))
    fx = fx[(fx["session"] > REC.VAL_LO) & (fx["session"] <= REC.VAL_HI)]
    con = fx.groupby("session")["contract"].agg(lambda s: s.value_counts().index[0])
    sb = REC.build_globex(ROOT, {d: REC.sierra_name(ROOT, con[d], d) for d in con.index}, REC.VAL_LO, REC.VAL_CUT)
    need(len(sb) > 0 and sb["session"].max() <= REC.VAL_HI, "the Sierra build is empty or runs past the validation window")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "sierra.csv.gz"
        sb.to_csv(p, index=False, encoding="utf-8")
        sf = read_bars(p, "2000-01-01", "2099-12-31")
    first_s = sf["session"].min()
    Ls = ledger_rows(splice(full[full["session"] < first_s], sf), first_s)
    Ld = ledger_rows(full[full["session"] <= sf["session"].max()], first_s)
    out["sierra_2023"] = {"first_scored": first_s, "last_session": sf["session"].max(), **compare(Ls, Ld)}
    out["wall_s"] = round(time.time() - t0, 1)
    PROOF.parent.mkdir(parents=True, exist_ok=True)
    PROOF.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    return 0


# ================================================================================ self-test
def selftest() -> int:
    need(normalise_contract("RTYZ26-CME") == "RTYZ6" and normalise_contract("RTYH27-CME") == "RTYH7"
         and normalise_contract("RTYZ6") == "RTYZ6", "normalise_contract")
    h = pd.DataFrame({"root": "RTY", "session": ["2026-09-17", "2026-09-18"], "et": ["2026-09-17 15:59"] * 2,
                      "hhmm": "15:59", "contract": "RTYZ6", "close": [1.0, 2.0]})
    f = pd.DataFrame({"root": "RTY", "session": ["2026-09-22"], "et": ["2026-09-22 15:59"], "hhmm": "15:59",
                      "contract": "RTYZ6", "close": [3.0]})
    need(len(splice(h, f)) == 3, "splice")
    for bad, what in ((h.assign(session=["2026-09-17", "2026-09-22"]), "an overlap"),
                      (h.assign(session=["2026-09-01", "2026-09-02"]), "a hole before the forward sessions")):
        try:
            splice(bad, f)
        except LedgerError:
            continue
        raise LedgerError(f"splice did not raise on {what}")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "x.csv"
        rows = [{"root": r, "session": "2026-09-22", "et": e, "hhmm": hm, "contract": "RTYZ26-CME", "open": 1, "high": 1,
                 "low": 1, "close": 1, "volume": 1} for r, e, hm in (("RTY", "2026-09-21 18:04", "18:04"),
                                                                       ("RTY", "2026-09-22 12:00", "12:00"),
                                                                       ("YM", "2026-09-22 15:59", "15:59"),
                                                                       ("RTY", "2026-09-10 15:59", "15:59"))]
        pd.DataFrame(rows).to_csv(p, index=False, encoding="utf-8")
        got = read_bars(p, "2026-09-21", "2099-12-31")
        need(list(got["hhmm"]) == ["18:04"] and list(got["contract"]) == ["RTYZ6"],
             f"read_bars keeps RTY rows of D778's bars within the stamp lag and normalises the name: {got.to_dict('records')}")
    # D794: the measured cost is D794's, and adding its column to an old ledger is not a revision
    d794 = json.loads(D794_JSON.read_text(encoding="utf-8"))["lines"]["L4"]["micro"]["cost_line"]["measured_cost_usd"]
    need(round(d794, 6) == COST_MEASURED, f"COST_MEASURED {COST_MEASURED} is not D794's {d794}")
    L = pd.DataFrame([{"session": "2026-09-22", "s1": "2026-09-23", "contract": "RTYZ6", "c_pts": 3.1, "thr_pts": 2.0, "gated": True,
                       "side": -1, "entry": 2500.0, "exit": 2498.0, "gross_usd": 10.0, "net_usd": round(10.0 - COST, 2),
                       "net_measured_cost_usd": round(10.0 - COST_MEASURED, 2), "status": "trade"}], columns=COLS)
    with tempfile.TemporaryDirectory() as td2:
        global LEDGER, REVISIONS
        keep = (LEDGER, REVISIONS)
        LEDGER, REVISIONS = Path(td2) / "l.csv", Path(td2) / "r.csv"
        try:
            L.drop(columns=["net_measured_cost_usd"]).astype(str).to_csv(LEDGER, index=False, encoding="utf-8")
            need(write_ledger(L) == 0 and not REVISIONS.exists(), "adding the D794 column must not log a revision")
            need("net_measured_cost_usd" in pd.read_csv(LEDGER, dtype=str).columns, "the rewritten ledger carries the D794 column")
            L2 = L.copy()
            L2["net_usd"] = 99.0
            need(write_ledger(L2) == 1 and REVISIONS.exists(), "a changed recorded value must still log a revision")
        finally:
            LEDGER, REVISIONS = keep
    print("selftest OK: contract names normalise; the splice joins, and raises on an overlap and on a hole; the reader "
          "keeps only RTY rows of D778's bars within the stamp lag; D794's measured cost sits beside the frozen net and "
          "its column is not a revision")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--prove", action="store_true")
    g.add_argument("--ledger", action="store_true")
    a = ap.parse_args(argv)
    return selftest() if a.selftest else prove() if a.prove else ledger()


if __name__ == "__main__":
    sys.exit(main())
