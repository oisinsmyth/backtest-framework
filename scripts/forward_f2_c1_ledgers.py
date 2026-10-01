"""The forward ledgers of NQ F2 (D716, programme slot 7) and C1 (D680, slot 9): each line's FROZEN code over its
Databento history followed by the forward recorder's Sierra bars (the principal, 2026-10-01: "yes start on the F2 and
C1 forward-log step").

    uv run python scripts/forward_f2_c1_ledgers.py --selftest
    uv run python scripts/forward_f2_c1_ledgers.py --prove        # in-sample: the splice against all-Databento, 2023
    uv run python scripts/forward_f2_c1_ledgers.py --ledgers [--spy P]   # AFTER the joint run only (refuses before)

WHY HERE AND NOT IN THE RECORDER. Both lines rank each session among the previous 250 three times over (D671's
`tiers`), so the first forward session's tier reads 2024-01 -> 2026-09-18: NQ/ES 2024+ is D716's unseen span and
2025-03 on is the joint vault. The recorder (scripts/record_forward_nq_lines.py) therefore keeps only the bars; this
file turns them into trades once the joint run has opened that history.

THE SPLICE. History and forward bars are concatenated and handed to the lines' own functions, unchanged:
  F2: D711's `clock_frame` at 15:30 and D707's `f2` on NQ (and ES, for D716's agreement book), over a frame built by
      `L_from_bars`, a copy of D711's `load_root` after its read (proved equal to `load_root` on the in-sample files).
  C1: D680's frozen `book()` on G0-layout bars (root, session, et, hhmm, contract, OHLCV) and G0's usable sessions,
      with D663's RESERVED_FROM held past the forward sessions for the call (joint_d680_vault.py's mechanism).
Sierra's contract names (NQZ26-CME) become Databento's codes (NQZ6), so the splice is never read as a roll.

THE PROOF (--prove). History = Databento before 2023-07-01; forward = Sierra bars 2023-07-03 -> 2023-12-29, built by
the recorder's own functions (the front by volume; the Globex session on the day session's front). Every session from
2023-07-01 is compared with the same line run on Databento alone. Every Databento file is restricted AS TEXT to rows
before 2024-01-01 before a value is parsed (NQ/ES 2024+ is D716's and D737's unseen span), and Sierra is read only in
[2023-07-01, 2024-01-01).

--ledgers (after the joint run): history = the rebuilt fut_{NQ,ES}_rth_1m (F2) and the joint run's
data/joint_run/d680/ bars and usable sessions (C1), all through 2026-09-18; forward = data/raw/forward/ from
2026-09-21. It refuses until both lines' vault results exist. The forward usable sessions follow G0's rule (SPY's
trading dates less ES's half days), so SPY's daily file (--spy for a refreshed one) must reach the last forward
session. The half days come from ES's own day-session bars (last bar before 15:30), because the CME calendar is built
from the Databento archive and cannot be extended after the lapse. Writes data/forward/f2_forward.csv and
data/forward/c1_forward.csv (one row a forward session; tracked).

THE PROOF'S RESULT (2026-10-01, data/forward/f2_c1_splice_proof.json): `L_from_bars` equals D711's `load_root`
exactly. F2: all 129 sessions of 2023-07 -> 12 take the same status, the same 32 trades on the same side, entry and
tier; 7 exits differ by <= 1.25 points (the 15:59 bar's last trade), net $29.35 against $30.85. C1: all 129 the same,
the same 27 trades on the same side and tier; levels differ by fractions of a point (ATR20 from the day's high and
low), net $11.20 against $11.89. The half-day rule equals the calendar on Sierra's 2023-H2 (5 of 5) and on Databento
2016-2023 except three NYSE closures with no ES day session (2018-12-05, 2021-04-02, 2023-04-07), which SPY's dates
exclude anyway: forward_use equals G0's usable sessions on 2023-H2 (124 of 124).
"""
from __future__ import annotations

import argparse
import contextlib
import gzip
import io
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import record_forward_nq_lines as REC  # noqa: E402  (defines only; its body runs nothing)

MAIN_DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")
SEAL = "2024-01-01"                     # NQ/ES 2024+ is unseen until the joint run (D716, D737)
SPLICE, PROVE_END = "2023-07-01", "2023-12-29"
FORWARD_FROM = REC.FORWARD_FROM         # 2026-09-21
HIST_CUT = "2026-09-19"                 # the history's end (the vault's last session is 2026-09-18)
FAR = "2099-01-01"                      # D663's RESERVED_FROM, held for the forward call
STAGE = REPO / "temp" / "forward_f2_c1"
OUT = REPO / "data" / "forward"
PROOF = OUT / "f2_c1_splice_proof.json"
F2_LEDGER, C1_LEDGER = OUT / "f2_forward.csv", OUT / "c1_forward.csv"
VAULT_RESULTS = (REPO / "data" / "vault_d716_nq_f2_result.json", REPO / "data" / "vault_d680_vault.json")
JOINT_D680 = REPO / "data" / "joint_run" / "d680"
DATE = re.compile(r"\d{4}-\d{2}-\d{2}$")
RTH_COLS = ["day", "hhmm", "contract", "open", "high", "low", "close", "volume"]
G0_COLS = ["root", "session", "et", "hhmm", "contract", "open", "high", "low", "close", "volume"]
F2_COLS = ["session", "contract", "status", "tc", "side", "entry", "exit", "gross_usd", "net_usd", "es_agrees"]
C1_COLS = ["session", "contract", "usable", "status", "ctier", "side", "level", "gross_bp", "net_bp", "gross_usd",
           "net_usd"]


class ForwardError(RuntimeError):
    pass


@contextlib.contextmanager
def held(module: Any, name: str, value: Any) -> Iterator[None]:
    """Hold a module global for the body and put the old value back whatever happens."""
    old = getattr(module, name)
    setattr(module, name, value)
    try:
        yield
    finally:
        setattr(module, name, old)


def restrict_text(src: Path, field: int, before: str) -> bytes:
    """The header and every line whose comma field `field` is a date before `before`, filtered as TEXT: no value on a
    dropped line is parsed. Raises on a data line whose field is not a date."""
    out = io.StringIO()
    with gzip.open(src, "rt", encoding="utf-8", newline="") as f:
        out.write(f.readline())
        for line in f:
            parts = line.split(",", field + 1)
            d = parts[field] if len(parts) > field else ""
            if not DATE.match(d):
                raise ForwardError(f"{src.name}: field {field} is not a date on a data line")
            if d < before:
                out.write(line)
    return out.getvalue().encode("utf-8")


def write_gz(p: Path, data: bytes) -> Path:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as z:
        z.write(data)
    return p


def databento_code(sierra: str) -> str:
    """Sierra's file name to Databento's contract code: NQZ26-CME -> NQZ6, YMH27-CBOT -> YMH7."""
    m = re.fullmatch(r"([A-Z]+)([FGHJKMNQUVXZ])(\d{2})-[A-Z]+", sierra)
    if m is None:
        raise ForwardError(f"not a Sierra futures name: {sierra}")
    return f"{m.group(1)}{m.group(2)}{int(m.group(3)) % 10}"


def rth_raw(root: str, before: str) -> bytes:
    return restrict_text(MAIN_DATA / "fixtures" / f"fut_{root}_rth_1m.csv.gz", 0, before)


def rth_history(raw: bytes) -> pd.DataFrame:
    """As D711's `load_root` reads its fixture."""
    return pd.read_csv(io.BytesIO(raw), dtype={"day": str, "hhmm": str, "contract": str}, encoding="utf-8")


def as_databento(b: pd.DataFrame) -> pd.DataFrame:
    return b.assign(contract=b["contract"].map(databento_code))


# ================================================================================ F2 (D716)
def f2_modules() -> tuple[Any, Any]:
    import vault_d716_nq_f2 as VD
    return VD, VD.M


def L_from_bars(M: Any, root: str, b: pd.DataFrame) -> dict[str, Any]:
    """D711's `load_root` after its read (b already restricted to its span): the same pivots, bar floor and roll flag."""
    b = b[b["day"] >= M.IN_FROM]
    nb = b.groupby("day").size()
    close = b.pivot(index="day", columns="hhmm", values="close")
    open_ = b.pivot(index="day", columns="hhmm", values="open")
    keep = nb.reindex(close.index) >= M.MIN_BARS
    close, open_ = close[keep], open_[keep]
    contract = b.groupby("day")["contract"].agg(lambda s: s.value_counts().index[0]).reindex(close.index)
    roll = contract != contract.shift(1)
    return {"root": root, "raw": b, "close": close, "open": open_, "roll": roll}


def f2_rows(Ln: dict[str, Any], Le: dict[str, Any], from_: str) -> pd.DataFrame:
    """One row a NQ session from `from_`: D716's B book (NQ F2), and whether its agreement book A would also take it."""
    VD, M = f2_modules()
    Xn, Xe = M.clock_frame(Ln, M.ANCHOR), M.clock_frame(Le, M.ANCHOR)
    Fn, Fe = M.f2_on(Xn), M.f2_on(Xe)
    VD.V.audit_tiers(Xn, Fn)
    VD.V.audit_tiers(Xe, Fe)
    es_take = pd.Series(Fe["take"] & Fe["window"], index=Xe.index)
    es_side = pd.Series(Xe["side"].to_numpy(float), index=Xe.index)
    agree = (es_take.reindex(Xn.index).fillna(False).to_numpy(bool)
             & (es_side.reindex(Xn.index).to_numpy() == Xn["side"].to_numpy(float)))
    cost = float(Xn.attrs["cost"])
    pos = {s: i for i, s in enumerate(Xn.index)}
    con = Ln["raw"].groupby("day")["contract"].first()
    rows = []
    for s in [d for d in con.index if d >= from_]:
        r: dict[str, Any] = {"session": s, "contract": con[s]}
        i = pos.get(s)
        if i is None:
            r["status"] = "excluded (roll day, fewer than 380 bars, or no move into 15:30)"
        elif not Fn["window"][i]:
            r["status"] = "burn-in (tier window not yet defined)"
        else:
            take = bool(Fn["take"][i])
            r.update({"status": "trade" if take else "no take", "tc": float(Fn["tc"][i]), "side": int(Xn["side"].iloc[i]),
                      "entry": float(Xn["P_entry"].iloc[i]), "exit": float(Xn["P_exit"].iloc[i]),
                      "es_agrees": bool(agree[i])})
            if take:
                g = float(Xn["gross"].iloc[i])
                r.update({"gross_usd": g, "net_usd": g - cost})
        rows.append(r)
    return pd.DataFrame(rows).reindex(columns=F2_COLS)


# ================================================================================ C1 (D680)
def c1_modules() -> tuple[Any, Any]:
    import vault_d680_nq_compression as V680
    return V680, V680.M.S.load_v2().R


def g0_module() -> Any:
    import opening_gate0 as G0
    return G0


def c1_rows(b: pd.DataFrame, use: list[str], from_: str) -> pd.DataFrame:
    """One row a NQ session from `from_`: D680's frozen book() on the bars, C1 = ctier < 1/3, one MNQ at the level."""
    V680, R = c1_modules()
    with held(V680.T, "RESERVED_FROM", FAR):
        tr, sess = V680.book(b, use, R, None)
    upp = V680.cost_lines()["usd_per_point"]
    brk = tr.set_index("session")
    sess, use_s = set(sess), set(use)
    nq = b[b["root"] == "NQ"]
    con = nq.groupby("session")["contract"].first()
    rows = []
    for s in [x for x in con.index if x >= from_]:
        r: dict[str, Any] = {"session": s, "contract": con[s], "usable": s in use_s}
        if s not in sess:
            r["status"] = "excluded (not usable, or a prior-session statistic undefined)"
        elif s not in brk.index:
            r["status"] = "no break"
        else:
            t = brk.loc[s]
            ct, lvl = float(t["ctier"]), float(t["level"])
            r.update({"ctier": ct, "side": int(t["D"]), "level": lvl, "gross_bp": float(t["gross"]), "net_bp": float(t["net"])})
            if not np.isfinite(ct):
                r["status"] = "break, tier undefined (burn-in)"
            elif ct < 1 / 3:
                r.update({"status": "trade", "gross_usd": float(t["gross"]) * lvl / 1e4 * upp,
                          "net_usd": float(t["net"]) * lvl / 1e4 * upp})
            else:
                r["status"] = "break, tier >= 1/3 (no trade)"
        rows.append(r)
    return pd.DataFrame(rows).reindex(columns=C1_COLS)


def g0_bars(fixture: Path, before: str) -> pd.DataFrame:
    """G0's own loader on a copy of the Globex fixture restricted as text to sessions before `before`."""
    G0 = g0_module()
    p = write_gz(STAGE / f"globex_before_{before}.csv.gz", restrict_text(fixture, 1, before))
    with held(G0, "BARS", p), held(G0, "RESERVED_FROM", before):
        return G0.load_bars()


def g0_use(data_root: Path, before: str) -> list[str]:
    G0 = g0_module()
    with held(G0, "RESERVED_FROM", before):
        use, _ = G0.usable_sessions(data_root)
    return use


EARLY_LAST = "15:30"  # an ES day session whose last bar starts before this is an exchange early close


def half_days_from_bars(es_rth: pd.DataFrame) -> set[str]:
    """ES early closes from the bars themselves: the day session's last bar starts before 15:30 (an early close ends
    at 13:15 ET). Stands in for the CME calendar, which is built from the Databento archive and cannot be extended
    after the lapse; proved equal to the calendar's ES half days by --prove."""
    last = es_rth.groupby("day")["hhmm"].max()
    return set(last.index[last < EARLY_LAST])


def calendar_half_days(lo: str, hi: str) -> set[str]:
    cal = pd.read_csv(MAIN_DATA / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
    es = cal[(cal["root"] == "ES") & (cal["day"] >= lo) & (cal["day"] <= hi)]
    return set(es.loc[es["is_early_close"].astype(bool), "day"])


def forward_use(sessions: list[str], spy: Path, es_rth: pd.DataFrame) -> list[str]:
    """G0's rule on the forward sessions: SPY's trading dates (keys only) less ES's half days (from the bars). SPY's
    file must reach the last session, or the list would silently stop short."""
    keys = set(json.load(gzip.open(spy, "rt", encoding="utf-8")).keys())
    last = max(sessions)
    if max(keys) < last:
        raise ForwardError(f"SPY's daily file ends {max(keys)}, before the last forward session {last}: refresh it")
    half = half_days_from_bars(es_rth)
    return sorted(s for s in sessions if s in keys and s not in half)


def sierra_forward(lo: str, hi: str, cut: str) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    """The recorder's own build over [lo, hi]: day-session bars (front by volume) and Globex sessions on that front."""
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range(lo, hi)]
    rth, glx = {}, {}
    for root in ("NQ", "ES"):
        b = REC.build_bars(root, days, lo, cut)
        g = REC.build_globex(root, b.groupby("day")["contract"].first().to_dict(), lo, cut)
        rth[root], glx[root] = as_databento(b)[RTH_COLS], as_databento(g)[G0_COLS]
    return rth, glx


# ================================================================================ the proof (in-sample)
def compare(a: pd.DataFrame, b: pd.DataFrame, num: list[str]) -> dict[str, Any]:
    m = a.merge(b, on="session", how="outer", suffixes=("_spl", "_ref"), indicator=True)
    both = m[m["_merge"] == "both"]
    tr_s, tr_r = set(a.loc[a["status"] == "trade", "session"]), set(b.loc[b["status"] == "trade", "session"])
    tt = both[(both["status_spl"] == "trade") & (both["status_ref"] == "trade")]
    out: dict[str, Any] = {"sessions_spliced": int(len(a)), "sessions_reference": int(len(b)),
                           "sessions_only_one_side": sorted(m.loc[m["_merge"] != "both", "session"].tolist()),
                           "status_agree": float((both["status_spl"] == both["status_ref"]).mean()),
                           "status_disagree": both.loc[both["status_spl"] != both["status_ref"],
                                                       ["session", "status_spl", "status_ref"]].to_dict("records"),
                           "trades_spliced": len(tr_s), "trades_reference": len(tr_r), "trades_in_both": len(tr_s & tr_r),
                           "same_side": float((tt["side_spl"] == tt["side_ref"]).mean()) if len(tt) else None,
                           "net_usd_sum_spliced": float(a.loc[a["status"] == "trade", "net_usd"].sum()),
                           "net_usd_sum_reference": float(b.loc[b["status"] == "trade", "net_usd"].sum())}
    for c in num:
        d = (tt[f"{c}_spl"].astype(float) - tt[f"{c}_ref"].astype(float)).abs()
        out[f"{c}_abs_diff"] = {"equal_share": float((d == 0).mean()) if len(d) else None,
                                "median": float(d.median()) if len(d) else None, "max": float(d.max()) if len(d) else None}
    return out


def prove() -> int:
    t0 = time.time()
    VD, M = f2_modules()
    res: dict[str, Any] = {"splice": SPLICE, "forward_span": [SPLICE, PROVE_END], "databento_restricted_before": SEAL}
    rth_s, glx_s = sierra_forward(SPLICE, PROVE_END, SEAL)
    # F2: L_from_bars equals D711's load_root on the restricted files; then the splice against Databento alone
    raw = {r: rth_raw(r, SEAL) for r in ("NQ", "ES")}
    hist = {r: rth_history(raw[r]) for r in ("NQ", "ES")}
    STAGE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=STAGE) as td:
        for r in ("NQ", "ES"):
            write_gz(Path(td) / f"fut_{r}_rth_1m.csv.gz", raw[r])
        with held(M, "FIX", Path(td)):
            ref = {r: M.load_root(r) for r in ("NQ", "ES")}
    for r in ("NQ", "ES"):
        mine = L_from_bars(M, r, hist[r][hist[r]["day"] <= M.IN_END])
        for k in ("close", "open"):
            if not mine[k].equals(ref[r][k]):
                raise ForwardError(f"L_from_bars: {r} {k} differs from D711's load_root")
        if not mine["roll"].equals(ref[r]["roll"]):
            raise ForwardError(f"L_from_bars: {r} roll differs from D711's load_root")
    res["L_from_bars_equals_load_root"] = True
    # the forward half-day rule against the CME calendar: Databento's ES 2016 -> 2023, and Sierra's ES 2023-H2;
    # then G0's usable sessions against forward_use's on the Sierra half-year
    es_db = hist["ES"][hist["ES"]["day"] >= "2016-01-04"]
    hd_db, cal_db = half_days_from_bars(es_db), calendar_half_days("2016-01-04", PROVE_END)
    hd_si, cal_si = half_days_from_bars(rth_s["ES"]), calendar_half_days(SPLICE, PROVE_END)
    g0u = [s for s in g0_use(MAIN_DATA, SEAL) if s >= SPLICE]
    fu = forward_use(sorted(rth_s["NQ"]["day"].unique()), MAIN_DATA / "raw" / "alphavantage" / "daily" / "SPY.json.gz",
                     rth_s["ES"])
    res["half_days"] = {"databento_2016_2023": {"rule": sorted(hd_db), "calendar": sorted(cal_db), "equal": hd_db == cal_db},
                        "sierra_2023_h2": {"rule": sorted(hd_si), "calendar": sorted(cal_si), "equal": hd_si == cal_si},
                        "forward_use_equals_g0_use_2023_h2": fu == g0u, "use_n": [len(fu), len(g0u)],
                        "use_only_one_side": sorted(set(fu) ^ set(g0u))}
    print(json.dumps({"half_days": {k: (v if not isinstance(v, dict) else {"equal": v["equal"], "n": len(v["rule"])})
                                    for k, v in res["half_days"].items()}}, indent=1), flush=True)
    spl = {r: L_from_bars(M, r, pd.concat([hist[r][hist[r]["day"] < SPLICE][RTH_COLS], rth_s[r]], ignore_index=True))
           for r in ("NQ", "ES")}
    f2_ref, f2_spl = f2_rows(ref["NQ"], ref["ES"], SPLICE), f2_rows(spl["NQ"], spl["ES"], SPLICE)
    res["F2"] = compare(f2_spl, f2_ref, ["entry", "exit", "gross_usd", "tc"])
    j = f2_spl.merge(f2_ref, on="session", suffixes=("_spl", "_ref"))
    j = j[(j["status_spl"] == "trade") & (j["status_ref"] == "trade")]
    res["F2"]["es_agrees_equal_on_common_trades"] = float((j["es_agrees_spl"] == j["es_agrees_ref"]).mean()) if len(j) else None
    print(json.dumps({"F2": res["F2"]}, indent=1, default=str), flush=True)
    # C1: G0's loader on the restricted fixture; the splice against Databento alone
    b_ref = g0_bars(MAIN_DATA / "fixtures" / "fut_opening_globex_1m.csv.gz", SEAL)
    use = g0_use(MAIN_DATA, SEAL)
    c1_ref = c1_rows(b_ref, use, SPLICE)
    b_spl = pd.concat([b_ref[b_ref["session"] < SPLICE], *glx_s.values()], ignore_index=True)
    c1_spl = c1_rows(b_spl, use, SPLICE)
    res["C1"] = compare(c1_spl, c1_ref, ["level", "gross_bp", "ctier"])
    res["runtime_min"] = round((time.time() - t0) / 60, 2)
    OUT.mkdir(parents=True, exist_ok=True)
    PROOF.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"C1": res["C1"], "runtime_min": res["runtime_min"]}, indent=1, default=str))
    return 0


# ================================================================================ the ledgers (after the joint run)
def ledgers(spy: Path | None) -> int:
    missing = [p.name for p in VAULT_RESULTS if not p.exists()]
    if missing:
        raise ForwardError(f"refused: the joint run has not scored {missing}; the history these ledgers read is the vault")
    VD, M = f2_modules()
    fw = REPO / "data" / "raw" / "forward"
    rth_f = {r: as_databento(pd.read_csv(fw / f"fut_{r}_fwd_1m.csv.gz", encoding="utf-8",
                                         dtype={"day": str, "hhmm": str, "contract": str}))[RTH_COLS] for r in ("NQ", "ES")}
    glx_f = {r: as_databento(pd.read_csv(fw / f"fut_{r}_fwd_globex_1m.csv.gz", encoding="utf-8",
                                         dtype={"session": str, "et": str, "hhmm": str, "contract": str}))[G0_COLS]
             for r in ("NQ", "ES")}
    for r in ("NQ", "ES"):
        if rth_f[r]["day"].min() < FORWARD_FROM or glx_f[r]["et"].min() < FORWARD_FROM:
            raise ForwardError("a forward bar before 2026-09-21")
    L = {r: L_from_bars(M, r, pd.concat([rth_history(rth_raw(r, HIST_CUT))[RTH_COLS], rth_f[r]], ignore_index=True))
         for r in ("NQ", "ES")}
    f2 = f2_rows(L["NQ"], L["ES"], FORWARD_FROM)
    bv = pd.read_csv(JOINT_D680 / "d680_vault_bars.csv.gz", encoding="utf-8", dtype={"session": str, "hhmm": str, "et": str})
    uv = json.loads((JOINT_D680 / "d680_vault_use.json").read_text(encoding="utf-8"))
    if bv["session"].max() > "2026-09-18":
        raise ForwardError("the joint run's D680 bars reach past the vault")
    sessions = sorted(glx_f["NQ"]["session"].unique())
    use = uv + forward_use(sessions, spy or REPO / "data" / "raw" / "alphavantage" / "daily" / "SPY.json.gz", rth_f["ES"])
    c1 = c1_rows(pd.concat([bv, *glx_f.values()], ignore_index=True), use, FORWARD_FROM)
    OUT.mkdir(parents=True, exist_ok=True)
    f2.to_csv(F2_LEDGER, index=False, encoding="utf-8", lineterminator="\n")
    c1.to_csv(C1_LEDGER, index=False, encoding="utf-8", lineterminator="\n")
    for nm, x in (("F2", f2), ("C1", c1)):
        t = x[x["status"] == "trade"]
        print(f"[{nm}] forward sessions {len(x)}; trades {len(t)}, net ${t['net_usd'].astype(float).sum():.2f}")
    return 0


# ================================================================================ self-test (synthetic and the refusal)
def selftest() -> int:
    fails: list[str] = []
    if databento_code("NQZ26-CME") != "NQZ6" or databento_code("YMH27-CBOT") != "YMH7" or databento_code("ESU23-CME") != "ESU3":
        fails.append("databento_code")
    try:
        databento_code("NQZ6")
        fails.append("databento_code accepted a Databento code")
    except ForwardError:
        pass
    STAGE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=STAGE) as td:
        p = write_gz(Path(td) / "x.csv.gz", b"root,session,v\nNQ,2023-12-29,1\nNQ,2024-01-02,2\nNQ,2023-06-30,3\n")
        if restrict_text(p, 1, SEAL) != b"root,session,v\nNQ,2023-12-29,1\nNQ,2023-06-30,3\n":
            fails.append("restrict_text keeps the wrong lines")
        q = write_gz(Path(td) / "y.csv.gz", b"root,session,v\nNQ,notadate,1\n")
        try:
            restrict_text(q, 1, SEAL)
            fails.append("restrict_text accepted a non-date field")
        except ForwardError:
            pass
    import types
    mod = types.SimpleNamespace(X=1)
    try:
        with held(mod, "X", 2):
            raise KeyError
    except KeyError:
        pass
    if mod.X != 1:
        fails.append("held did not restore after an exception")
    if not all(p.exists() for p in VAULT_RESULTS):
        try:
            ledgers(None)
            fails.append("--ledgers did not refuse before the joint run")
        except ForwardError:
            pass
    if fails:
        print("SELFTEST FAILED:", fails)
        return 1
    print("SELFTEST OK: Sierra-to-Databento contract codes (and a refusal); the text restriction keeps only earlier dates "
          "and raises on a non-date; held restores after an exception; --ledgers refuses before the joint run")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--prove", action="store_true")
    ap.add_argument("--ledgers", action="store_true")
    ap.add_argument("--spy", type=Path, default=None)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.prove:
        return prove()
    if a.ledgers:
        return ledgers(a.spy)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
