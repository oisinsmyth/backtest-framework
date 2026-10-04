"""The forward ledger for D776 (D775's CPI and jobs-report fade on MNQ, frozen in programme slot 2), D785.

    python scripts/forward_d776_ledger.py --selftest
    python scripts/forward_d776_ledger.py --prove      # in-sample only: the reader and the Sierra source
    python scripts/forward_d776_ledger.py --ledger     # every CPI/EMPSIT release from 2026-09-21 on

The trades are D775's own functions, imported unchanged, called exactly as D776's frozen vault scorer calls them:
`classify(sessions(bars, "NQ"), release_days)`. Each trade needs only its own morning (the 08:29, 08:34 and 11:00
bar closes), so unlike L4, F2 and C1 this ledger needs no history and runs now.

The input is the forward recorder's NQ Globex sessions (data/raw/forward/fut_NQ_fwd_globex_1m.csv.gz, sessions from
2026-09-21), read with D776's reader's filters (root, D775's bars, same-day stamps), Sierra contract names normalised.
The release days are D585's calendar (`data/calendar/events.csv`), CPI and EMPSIT at 08:30, from 2026-09-21.

THE SEALS. No session before 2026-09-21 is read in --ledger (it raises); --prove reads only 2016-2023 (D775's loader)
and Sierra's 2023-04 -> 2023-12 files (the recorder's validation window). NQ 2024-01-01 -> 2026-09-18 (D776's vault)
is never read.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d775_cpi_nfp_fade as S  # noqa: E402

ROOT = "NQ"
FIX_NAME, MULT, COST = S.ROOTS[ROOT]
FORWARD_FROM = "2026-09-21"
FORWARD = S.MAIN / "data" / "raw" / "forward" / "fut_NQ_fwd_globex_1m.csv.gz"
LEDGER = REPO / "data" / "forward" / "d776_forward.csv"
REVISIONS = REPO / "data" / "forward" / "d776_forward_revisions.csv"
PROOF = REPO / "data" / "forward" / "d776_ledger_proof.json"
# D794 (the principal, 2026-10-04: "Yes add it to the ledgers"): the cost measured at this line's own fills, reported
# BESIDE the frozen net, never instead of it. The mean of data/diag_d794_fill_cost.json's MNQ cost line, asserted below.
COST_MEASURED = 4.196759
D794_JSON = REPO / "data" / "diag_d794_fill_cost.json"
COLS = ["day", "event", "contract", "x_pts", "side", "entry", "exit", "gross_usd", "net_usd", "net_measured_cost_usd", "status"]
SIERRA_NAME = re.compile(r"^([A-Z]+)([FGHJKMNQUVXZ])(\d{2})-[A-Z]+$")


class LedgerError(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise LedgerError(msg)


# ================================================================================ input
def normalise_contract(k: str) -> str:
    m = SIERRA_NAME.match(str(k))
    return f"{m.group(1)}{m.group(2)}{m.group(3)[-1]}" if m else str(k)


def read_bars(path: Path, lo: str, hi: str) -> pd.DataFrame:
    """D776's reader's filters on any opening-layout file: NQ, D775's bars, the bar stamped on its own session day."""
    parts = []
    for ch in pd.read_csv(path, encoding="utf-8", chunksize=2_000_000, dtype={"session": str, "et": str, "hhmm": str,
                                                                               "contract": str},
                          usecols=["root", "session", "et", "hhmm", "contract", "close"]):
        ch = ch[(ch["root"] == ROOT) & (ch["session"] >= lo) & (ch["session"] <= hi) & ch["hhmm"].isin(S.BARS)]
        parts.append(ch[ch["et"].str[:10] == ch["session"]])
    b = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["root", "session", "et", "hhmm", "contract", "close"])
    b["contract"] = b["contract"].map(normalise_contract)
    return b


def release_days(lo: str, hi: str) -> dict[str, str]:
    e = pd.read_csv(S.EVENTS, encoding="utf-8")
    e = e[e["event"].isin(["CPI", "EMPSIT"]) & (e["datetime_et"].str[11:16] == "08:30")]
    d = e["datetime_et"].str[:10]
    e = e[(d >= lo) & (d <= hi)]
    return dict(zip(e["datetime_et"].str[:10], e["event"]))


# ================================================================================ the ledger
def ledger_rows(b: pd.DataFrame, rel: dict[str, str]) -> pd.DataFrame:
    """One row per release day: D775's classify over D775's sessions, with the reason a day was not traded."""
    Sx = S.sessions(b, ROOT)
    U, _ = S.classify(Sx, rel)
    K = b.groupby("session")["contract"].first()
    rows = []
    for d in sorted(rel):
        base = {"day": d, "event": rel[d], "contract": K.get(d, "")}
        if d in U.index and bool(U.at[d, "is_rel"]):
            r = U.loc[d]
            rows.append({**base, "x_pts": round(float(r["x"]), 2), "side": int(r["side"]), "entry": float(r[S.ENTRY]),
                         "exit": float(r[S.EXIT]), "gross_usd": round(float(r["gross"]), 2),
                         "net_usd": round(float(r["gross"]) - COST, 2),
                         "net_measured_cost_usd": round(float(r["gross"]) - COST_MEASURED, 2), "status": "trade"})
            continue
        if d not in Sx.index:
            status = "pending or missing (no bars recorded for the session)"
        else:
            r = Sx.loc[d]
            status = ("two contracts" if r["nk"] != 1 else
                      "missing bar" if pd.isna(r[S.PRE]) or pd.isna(r[S.ENTRY]) or pd.isna(r[S.EXIT]) else
                      "zero impulse" if r["x"] == 0 else "not traded")
        rows.append({**base, "x_pts": "", "side": 0, "entry": "", "exit": "", "gross_usd": "", "net_usd": "",
                     "net_measured_cost_usd": "", "status": status})
    return pd.DataFrame(rows, columns=COLS)


def write_ledger(new: pd.DataFrame) -> int:
    revised = 0
    out = new.astype(str)
    if LEDGER.exists():
        old = pd.read_csv(LEDGER, dtype=str, keep_default_na=False, encoding="utf-8")
        cmp_cols = [c for c in COLS[1:] if c in old.columns]        # a column added later (D794) is not a revision
        old = old.reindex(columns=COLS, fill_value="")
        mm = old.merge(out, on="day", how="inner", suffixes=("_old", "_new"))
        ch = []
        for _, r in mm.iterrows():
            diff = [c for c in cmp_cols if r[f"{c}_old"] != r[f"{c}_new"]]
            if diff and not r["status_old"].startswith("pending"):
                ch.append({"day": r["day"], "changed": ";".join(diff),
                           "recorded_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                           "old": json.dumps({c: r[f"{c}_old"] for c in diff}), "new": json.dumps({c: r[f"{c}_new"] for c in diff})})
        if ch:
            revised = len(ch)
            pd.DataFrame(ch).to_csv(REVISIONS, mode="a", header=not REVISIONS.exists(), index=False, encoding="utf-8")
        lost = old[~old["day"].isin(out["day"])]
        out = pd.concat([out, lost], ignore_index=True).sort_values("day")
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(LEDGER, index=False, encoding="utf-8", lineterminator="\n")
    return revised


def ledger() -> int:
    need(FORWARD.exists(), f"{FORWARD} is missing")
    today = dt.date.today().isoformat()
    b = read_bars(FORWARD, FORWARD_FROM, today)
    need(len(b) > 0 and bool((b["session"] >= FORWARD_FROM).all()), "seal: no forward bars, or a session before 2026-09-21")
    rel = release_days(FORWARD_FROM, today)
    L = ledger_rows(b, rel)
    revised = write_ledger(L)
    tr = L[L["status"] == "trade"]
    net = pd.to_numeric(tr["net_usd"], errors="coerce")
    net_m = pd.to_numeric(tr["net_measured_cost_usd"], errors="coerce")
    print(f"[D776 ledger] release days {len(L)} from {FORWARD_FROM} (bars to {b['session'].max()}); trades {len(tr)}, "
          f"net ${net.sum():.2f} at the frozen ${COST:.2f} (${net_m.sum():.2f} at D794's measured ${COST_MEASURED:.2f}); "
          f"revisions {revised} -> {LEDGER.relative_to(REPO)}")
    for _, r in L.iterrows():
        print(f"  {r['day']} {r['event']:6s} {r['status']}" + (f": side {r['side']}, net ${r['net_usd']} "
                                                              f"(measured cost ${r['net_measured_cost_usd']})" if r["status"] == "trade" else ""))
    return 0


# ================================================================================ the in-sample proofs
def prove() -> int:
    t0 = time.time()
    out: dict[str, Any] = {"tool": "scripts/forward_d776_ledger.py --prove", "in_sample_only": True}
    full = S._load_file((FIX_NAME, (ROOT,)))                       # D775's loader: sessions < 2024-01-01, asserted
    rel_all = S.release_days()
    # (a) the reader: the whole in-sample written in the recorder's layout with Sierra contract names and read back;
    #     the ledger must give D775's known answer (186 trades, +$34.879...) exactly
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "fwd.csv.gz"
        x = full.copy()
        x["contract"] = x["contract"].map(lambda k: f"{k[:-2]}{k[-2]}2{k[-1]}-CME")
        for c in ("open", "high", "low"):
            x[c] = x["close"]
        x["volume"] = 1
        x[["root", "session", "et", "hhmm", "contract", "open", "high", "low", "close", "volume"]].to_csv(
            p, index=False, encoding="utf-8")
        rb = read_bars(p, S.START, "2023-12-31")
    L = ledger_rows(rb, rel_all)
    T = L[L["status"] == "trade"]
    g = pd.to_numeric(T["gross_usd"])
    U, _ = S.classify(S.sessions(full, ROOT), rel_all)
    R = U[U["is_rel"]]
    need(len(T) == 186 and list(T["day"]) == list(R.index), f"reader: {len(T)} trades, not D775's 186 on the same days")
    need(bool((g.to_numpy() == R["gross"].round(2).to_numpy()).all()), "reader: the gross differs from D775's")
    out["reader"] = {"trades": int(len(T)), "mean_gross": round(float(R["gross"].mean()), 6), "equal_to_d775": True,
                     "non_trade_statuses": L.loc[L["status"] != "trade", "status"].value_counts().to_dict()}
    # (b) the Sierra source: the recorder's own builder over Sierra's 2023 NQ files, on Databento's contract per session
    import record_forward_nq_lines as REC
    fx = full[(full["session"] > REC.VAL_LO) & (full["session"] <= REC.VAL_HI)]
    con = fx.groupby("session")["contract"].agg(lambda s: s.value_counts().index[0])
    sb = REC.build_globex(ROOT, {d: REC.sierra_name(ROOT, con[d], d) for d in con.index}, REC.VAL_LO, REC.VAL_CUT)
    need(len(sb) > 0 and sb["session"].max() <= REC.VAL_HI, "the Sierra build is empty or runs past the validation window")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "sierra.csv.gz"
        sb.to_csv(p, index=False, encoding="utf-8")
        sf = read_bars(p, "2000-01-01", "2099-12-31")
    lo, hi = sf["session"].min(), sf["session"].max()
    rel = {d: e for d, e in rel_all.items() if lo <= d <= hi}
    Ls = ledger_rows(sf, rel)
    Ld = ledger_rows(full[(full["session"] >= lo) & (full["session"] <= hi)], rel)
    m = Ls.merge(Ld, on="day", suffixes=("_s", "_d"))
    both = m[(m["status_s"] == "trade") & (m["status_d"] == "trade")]
    gs, gd = pd.to_numeric(both["gross_usd_s"]), pd.to_numeric(both["gross_usd_d"])
    out["sierra_2023"] = {"from": lo, "to": hi, "release_days": int(len(m)),
                          "status_agree": float((m["status_s"] == m["status_d"]).mean()),
                          "trades_sierra": int((m["status_s"] == "trade").sum()), "trades_databento": int((m["status_d"] == "trade").sum()),
                          "side_agree": float((both["side_s"] == both["side_d"]).mean()) if len(both) else None,
                          "gross_abs_diff_max": float((gs - gd).abs().max()) if len(both) else None,
                          "net_sum_sierra": round(float((gs - COST).sum()), 2), "net_sum_databento": round(float((gd - COST).sum()), 2)}
    out["wall_s"] = round(time.time() - t0, 1)
    PROOF.parent.mkdir(parents=True, exist_ok=True)
    PROOF.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    return 0


# ================================================================================ self-test
def _bars(day: str, closes: dict[str, float], k: str = "NQZ26-CME") -> list[dict]:
    return [{"root": ROOT, "session": day, "et": f"{day} {h}", "hhmm": h, "contract": k, "close": v} for h, v in closes.items()]


def selftest() -> int:
    need(normalise_contract("NQZ26-CME") == "NQZ6" and normalise_contract("NQZ6") == "NQZ6", "normalise_contract")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "x.csv"
        rows = (_bars("2026-10-02", {"08:29": 100.0, "08:34": 110.0, "11:00": 104.0})
                + [{"root": ROOT, "session": "2026-10-02", "et": "2026-10-01 18:00", "hhmm": "18:00", "contract": "NQZ26-CME", "close": 1.0},
                   {"root": "ES", "session": "2026-10-02", "et": "2026-10-02 08:29", "hhmm": "08:29", "contract": "ESZ26-CME", "close": 1.0}])
        pd.DataFrame(rows).to_csv(p, index=False, encoding="utf-8")
        b = read_bars(p, FORWARD_FROM, "2099-12-31")
        need(set(b["hhmm"]) == {"08:29", "08:34", "11:00"} and set(b["contract"]) == {"NQZ6"},
             "read_bars keeps NQ's same-day D775 bars and normalises the name")
    # an up-impulse (+10) that falls back by 6 pays the short fade: (110 - 104) x $2 = +$12
    L = ledger_rows(b, {"2026-10-02": "EMPSIT", "2026-10-14": "CPI"})
    t = L[L["day"] == "2026-10-02"].iloc[0]
    need(t["status"] == "trade" and t["side"] == -1 and abs(t["gross_usd"] - 12.0) < 1e-9, f"the fade in money: {t.to_dict()}")
    need(abs(t["net_measured_cost_usd"] - round(12.0 - COST_MEASURED, 2)) < 1e-9 and abs(t["net_usd"] - round(12.0 - COST, 2)) < 1e-9,
         "the measured-cost net sits beside the frozen net")
    d794 = json.loads(D794_JSON.read_text(encoding="utf-8"))["lines"]["D776"]["micro"]["cost_line"]["measured_cost_usd"]
    need(round(d794, 6) == COST_MEASURED, f"COST_MEASURED {COST_MEASURED} is not D794's {d794}")
    with tempfile.TemporaryDirectory() as td2:                      # an old file without the D794 column: no revision
        global LEDGER, REVISIONS
        keep = (LEDGER, REVISIONS)
        LEDGER, REVISIONS = Path(td2) / "l.csv", Path(td2) / "r.csv"
        try:
            L.drop(columns=["net_measured_cost_usd"]).astype(str).to_csv(LEDGER, index=False, encoding="utf-8")
            need(write_ledger(L) == 0 and not REVISIONS.exists(), "adding the D794 column must not log a revision")
            need("net_measured_cost_usd" in pd.read_csv(LEDGER, dtype=str, encoding="utf-8").columns, "the rewritten ledger carries the D794 column")
        finally:
            LEDGER, REVISIONS = keep
    need(L[L["day"] == "2026-10-14"].iloc[0]["status"].startswith("pending"), "a release with no bars yet is pending")
    b2 = pd.DataFrame(_bars("2026-10-02", {"08:29": 100.0, "08:34": 110.0}))
    need(ledger_rows(b2, {"2026-10-02": "EMPSIT"}).iloc[0]["status"] == "missing bar", "a missing 11:00 bar is named")
    print("selftest OK: contract names normalise; the reader keeps NQ's same-day D775 bars; the fade pays a reversal in "
          "money (+$12); an unrecorded release is pending; a missing bar is named")
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
