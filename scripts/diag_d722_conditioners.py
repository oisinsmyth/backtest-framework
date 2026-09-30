"""D722 Phase 0b: the per-session conditioner panel of D722 s.3 (docs/decisions/D722-DIAG-PRE-REG-why-2022-scale-regime-or-one-bet.md,
f25e4726), for roots ES, NQ and HO, sessions 2016-01-04 -> 2023-12-29. Every variable is known BEFORE the session (lagged to the prior
session) unless the record says otherwise (X8, X9 and war are calendar flags of the session itself; X2's IV and X3's gamma are D691's and
D688's own prior-settlement quantities keyed on the session).

    uv run python scripts/diag_d722_conditioners.py --selftest     # clean pass on the real inputs, then every canary must RAISE
    uv run python scripts/diag_d722_conditioners.py --build        # builds (or refreshes) the cache, prints coverage and wall time

    from diag_d722_conditioners import load_conditioners
    P = load_conditioners()          # index (root, session "YYYY-MM-DD"); refuses a stale cache (refresh=True rebuilds)

THE SEAL. No value dated 2024-01-01 or later enters any computation: every loader filters each chunk on read and `seal()` asserts on
every input frame and on the panel. The vault (2025-03-01 ->) is never opened for use. SqueezeMetrics GEX (licensed) enters only X3; the
per-date panel lives in temp/d722/ (gitignored); data/diag_d722_conditioners_summary.json carries aggregates only.

DEFINITIONS (the record's s.3; sources in brackets). `prior(d)` = the source's last row dated strictly before session d.
  sig20  ES, NQ: D663's `sig20` EXACTLY (stage0_d663_per_root_gamma_break.root_frame): the front contract's last 09:30-15:59 bar close
         per session [fut_opening_globex_1m, the bars D663/D691 read], r = ln(c_t / c_{t-1}) x 1e4 over the fixture's sessions (the roll
         day's front-to-front return included, as D663 has it), sig20_bp(d) = r.shift(1).rolling(20, min_periods=15).std(ddof=1);
         `sig20` = sig20_bp / 1e4 (a log-return sd, not bp). Asserted equal to D663's own root_frame on the same bars.
         HO (and CL for X5): the DAILY SETTLEMENT convention (the brief's option): r_t = ln(S_t(c) / S_prev(c)), c = the session's front
         [fut_curve_front_next, the breadth front], S from fut_settle_strip, the SAME contract on both settlements (a roll day's return is
         the new front's own move, never the calendar spread; energy spreads reach 10 %+ in 2022), over the root's settling sessions;
         sd over the 20 settling sessions ending prior(d), >= 15 finite, ddof 1.
  X1     ln sig20.
  X2     D691's ivrv exactly: ln(IV / RV20), IV = D691's at-the-money IV from the prior settlement (temp/d691_iv_{es,nq}.csv, D691's own
         cache, its key re-derived and required to match; rows >= 2024-01-01 dropped on read), RV20 = sig20_bp / 1e4 x sqrt(252)
         (stage0_d691_iv_size.design). ES, NQ; NaN on HO.
  X3     1 if G_SUM < 0, G_SUM = G_SPX (SqueezeMetrics GEX, the last row dated strictly before d) + G_ES (the ES option book at the prior
         settlement), built by D688's own load_inputs / build_panel / _work (stage0_d688_gamma_close, CUTOFF 2024-01-01) exactly as
         D699's `panel` assembles it; D699's panel is reproduced (D688's beta_G to the bit) before the flag is kept. Defined on D688's
         session set (ES sessions with >= 380 RTH bars, from 2016-01-04); the same market-level flag on ES and NQ rows; NaN on HO.
  X4     ln sd of daily changes in ZT's front settlement [fut_curve_front_next], over the 20 ZT settling sessions ending prior(d), a change
         across a front-contract change (roll) excluded (NaN), >= 15 finite, ddof 1. Same value on every root's row.
  X5     ln sig20 of CL, the settlement convention above, market-level.
  X6     D487's S1 variance ratio VR = var(R_day, ddof 1) / (q x var(r_bucket, ddof 1)) (run_d487_continuation_stage0.vr: the horizon is
         the WHOLE session, q = the number of buckets; bucket returns are simple, (C / prev - 1) x 1e4, the first from the session open),
         on the record's 30-MINUTE RTH returns, over the 60 most recent FULL sessions strictly before d.
           ES, NQ: fut_{root}_rth_1m (D487's source), 09:30 open then closes of the bars labelled 09:59, 10:29 .. 15:59 (q = 13); a full
           session has all 390 bars (D487's rule).
           HO: its own day-session band 09:00 -> 14:29 ET (cme_session_calendar's modal session_open_et / session_close_et for HO,
           asserted), bars from fut_opening_globex_1m_ho_rb_bz_hg_pl: the 09:00 open then closes at 09:29, 09:59 .. 14:29 (q = 11); a
           full session has every one of those 12 anchor bars (HO's band holds all 330 minutes on only ~90 % of sessions, 80 % in 2022,
           because a thin contract prints no bar when it does not trade).
         X6_15m: the same on D487's own 15-minute buckets (ES/NQ q = 26, D487's ENDS; HO q = 22), carried beside X6 because D487's S1 was
         measured at 15 minutes; its per-year values reproduce D487's recorded S1 exactly (a known-answer gate).
  r60    the root's 60-session log return to the prior settlement: the sum of the 60 same-contract daily settlement log returns (above)
         ending prior(d), all 60 finite. Part B forms X7 = r60 x side.
  X8     1 if the session's ET calendar date carries FOMC, FOMC_UNSCHEDULED, CPI or EMPSIT (data/calendar/events.csv, the date of
         datetime_et); on HO also EIA_WPSR. Columns fomc (FOMC or FOMC_UNSCHEDULED), fomc_unscheduled, cpi, empsit, eia_wpsr.
  X9     1 inside the three Economic Impact Payment windows: the 35 sessions of the ROOT's own calendar starting at the first session on or
         after each round's first deposit date, the dates VERIFIED from IRS / Treasury (EIP_FIRST_DEPOSIT_VERIFIED, with URLs and quotes).
         X9_record: the same on the record's approximate dates (EIP_FIRST_DEPOSIT_RECORD), kept for the amendment.
  X10    ln(MES day volume / ES day volume) on prior(d) of the ES session calendar (NQ rows: MNQ / NQ) [fut_micro_day_volume,
         fut_index_sessions: both the front's volume over the CALENDAR ET day, front = the highest full-day volume, the same rule].
         NaN before the micros exist (MES / MNQ from 2019-05-05) and on HO.
  X11    SMH's 60-session log return minus QQQ's, to prior(d) of the ETF calendar [etf_wide_daily_raw, not adjusted: a day with
         |daily log return| > 0.30 is a corporate action and its return is excluded; the rolling sum needs >= 55 of 60]. ES, NQ; NaN HO.
  X12    HO only: (front settle - next settle) / front settle on HO's prior settling session [fut_curve_front_next].
  war    1 for sessions 2022-02-24 -> 2022-04-29 (Part C only).

ASSERTIONS (D722 s.7), each shown to RAISE in --selftest: the seal (a planted 2024 row in every input); the lag audit (a SECOND
implementation, plain loops over raw inputs strictly before the session, on >= 50 random sessions per root, every variable; exact for flags
and single-operation ratios, 1e-12 relative where the float order differs; each variable made same-day must raise); right-quantity (X4
differs from the roll-inclusive version, X6 from the unlagged one, HO/CL sig20 and r60 from the front-to-front version, X10 and X11 from the
same-day version); known answers (D663's root_frame, D487's per-year S1, D699's reproduction of D688's beta_G, D691's cache key).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import run_d487_continuation_stage0 as D487  # noqa: E402  (defines only)
import stage0_d663_per_root_gamma_break as D663  # noqa: E402  (defines only; imports stage0_d662, defines only)
import stage0_d688_gamma_close as D688  # noqa: E402  (defines only; D581 is loaded on call)

DATA = REPO / "data"
FIX = DATA / "fixtures"
TMP = REPO / "temp" / "d722"
CACHE = TMP / "conditioners.csv.gz"
CACHE_META = TMP / "conditioners.meta.json"
INPUTS_PKL = TMP / "conditioner_inputs.pkl"
SUMMARY = DATA / "diag_d722_conditioners_summary.json"

CUT = "2024-01-01"
FIRST, LAST = "2016-01-04", "2023-12-29"
WARM_RTH = "2015-06-01"          # ES/NQ rth_1m warm-up for X6's 60 full sessions
WARM_GLX = "2015-09-01"          # the opening fixtures start here (D663's own warm-up)
ROOTS = ("ES", "NQ", "HO")
SEED = 722
N_AUDIT = 60                     # random sessions per root in the lag audit (>= 50 required)
REL = 1e-12                      # the lag audit's tolerance where the float order differs
WAR = ("2022-02-24", "2022-04-29")
EIP_WINDOW = 35
CA_LIMIT = 0.30                  # X11: |daily log return| above this is a corporate action
SIG_N, SIG_MIN = 20, 15
R60_N = 60
VR_N = 60
ETF_N, ETF_MIN = 60, 55
MACRO = ("FOMC", "FOMC_UNSCHEDULED", "CPI", "EMPSIT")

# X9. The record: "about 2020-04-10, 2020-12-29 and 2021-03-12". Verified 2026-09-30 (UTC ~22:50-23:05) from irs.gov / treasury.gov:
EIP_FIRST_DEPOSIT_RECORD = {"EIP1": "2020-04-10", "EIP2": "2020-12-29", "EIP3": "2021-03-12"}
EIP_FIRST_DEPOSIT_VERIFIED = {"EIP1": "2020-04-10", "EIP2": "2020-12-29", "EIP3": "2021-03-13"}
EIP_SOURCES = {
    "EIP1": [{"url": "https://www.irs.gov/pub/foia/ig/wi/wi-21-0820-0867.pdf", "accessed_utc": "2026-09-30T23:00Z",
              "doc": "IRS Interim IRM Procedural Update WI-21-0820-0867 (Aug 2020)",
              "quote": "Economic Impact Payment direct deposits started April 10, 2020"},
             {"url": "https://home.treasury.gov/news/press-releases/sm975", "accessed_utc": "2026-09-30T22:55Z",
              "doc": "Treasury press release, 2020-04-13",
              "quote": "Millions of Americans are starting to see Economic Impact Payments deposited directly in their bank accounts."}],
    "EIP2": [{"url": "https://home.treasury.gov/news/press-releases/sm1224", "accessed_utc": "2026-09-30T22:57Z",
              "doc": "Treasury press release, 2020-12-29",
              "quote": "The initial direct deposit payments may begin arriving as early as tonight for some and will continue into next week."}],
    "EIP3": [{"url": "https://www.irs.gov/newsroom/irs-begins-delivering-third-round-of-economic-impact-payments-to-americans",
              "accessed_utc": "2026-09-30T23:02Z", "doc": "IRS IR-2021-54, 2021-03-12",
              "quote": "the first batch of payments will be sent by direct deposit, which some recipients will start receiving as early as "
                       "this weekend"},
             {"url": "https://www.irs.gov/newsroom/irs-begins-delivering-third-round-of-economic-impact-payments-to-americans",
              "accessed_utc": "2026-09-30T23:02Z", "doc": "IRS IR-2021-54, 2021-03-12",
              "quote": "before the official payment date of March 17"},
             {"url": "https://home.treasury.gov/news/press-releases/jy0063", "accessed_utc": "2026-09-30T22:58Z",
              "doc": "Treasury press release, 2021-03-17", "quote": "These payments began processing on Friday, March 12."}],
}
EIP_NOTE = ("EIP1 and EIP2 match the record. EIP3 DIFFERS: 2021-03-12 (a Friday) is the date the first batch began PROCESSING; the "
            "first deposits reached accounts 'as early as this weekend' (Sat 2021-03-13 / Sun 03-14), official payment date 2021-03-17. "
            "The first session on or after the first deposit is therefore 2021-03-15 (Monday), not 2021-03-12: an amendment before Part "
            "B/C run. X9 uses the verified dates; X9_record carries the record's. EIP1's 2020-04-10 was Good Friday (no session), so "
            "both start 2020-04-13. EIP2's deposits could arrive 'as early as tonight' (after the 2020-12-29 close); 2020-12-29 is kept.")

INPUT_FILES = [FIX / "fut_ES_rth_1m.csv.gz", FIX / "fut_NQ_rth_1m.csv.gz", FIX / "fut_opening_globex_1m.csv.gz",
               FIX / "fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz", FIX / "fut_settle_strip.csv.gz", FIX / "fut_curve_front_next.csv.gz",
               FIX / "fut_index_sessions.csv.gz", FIX / "fut_micro_day_volume.csv.gz", FIX / "etf_wide_daily_raw.csv.gz",
               FIX / "cme_session_calendar.csv.gz", FIX / "fut_es_options_eod.csv.gz", DATA / "calendar" / "events.csv",
               DATA / "letf" / "letf_aum_daily.csv.gz", DATA / "raw" / "squeezemetrics" / "DIX.csv", DATA / "d688_gamma_close.json",
               DATA / "d487_continuation_stage0.json", REPO / "temp" / "d691_iv_es.csv", REPO / "temp" / "d691_iv_es.key",
               REPO / "temp" / "d691_iv_nq.csv", REPO / "temp" / "d691_iv_nq.key"]
MODULES = [Path(__file__).resolve(), REPO / "scripts" / "run_d487_continuation_stage0.py",
           REPO / "scripts" / "stage0_d663_per_root_gamma_break.py", REPO / "scripts" / "stage0_d662_gamma_product.py",
           REPO / "scripts" / "stage0_d688_gamma_close.py", REPO / "scripts" / "stage0_d581_gamma_close.py",
           REPO / "scripts" / "stage0_d691_iv_size.py", REPO / "scripts" / "stage0_d699_gamma_macd_long.py"]

COLUMNS = ["sig20", "X1", "X2", "X3", "X4", "X5", "X6", "X6_15m", "r60", "X8", "fomc", "fomc_unscheduled", "cpi", "empsit",
           "eia_wpsr", "X9", "X9_record", "X10", "X11", "X12", "war"]
LAGGED = ("sig20", "X2", "X3", "X4", "X5", "X6", "X6_15m", "r60", "X10", "X11", "X12")
SAMEDAY = ("X8", "X9")


class D722Error(AssertionError):
    """A gate refused the input. Raising, never a warning."""


def P(*a, **k):
    print(*a, **k, flush=True)


# ================================================================================ the seal
def seal(dates, what: str) -> None:
    d = pd.Series(np.asarray(dates, dtype=object)).astype(str)
    if len(d) and (d >= CUT).any():
        raise D722Error(f"[SEAL] {what}: a row dated {d[d >= CUT].min()} survived the {CUT} cut")


def read_sealed(path: Path, usecols, dtype, datecol: str, keep: Callable[[pd.DataFrame], pd.Series] | None = None,
                lo: str | None = None, cut: str = CUT, chunksize: int = 2_000_000) -> pd.DataFrame:
    """Read `path` in chunks, dropping every row dated >= `cut` (and < lo) chunk by chunk, before anything is computed; then seal.
    `cut` exists only so the self-test can disable the filter and prove the seal fires."""
    parts = []
    for ch in pd.read_csv(path, usecols=usecols, dtype=dtype, chunksize=chunksize, encoding="utf-8"):
        dd = ch[datecol].astype(str).str[:10]
        m = dd < cut
        if lo is not None:
            m &= dd >= lo
        if keep is not None:
            m &= keep(ch)
        if m.any():
            parts.append(ch[m])
    out = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=usecols)
    seal(out[datecol].astype(str).str[:10], path.name)
    return out


# ================================================================================ cache keys
def file_key(paths) -> dict[str, list[int]]:
    out = {}
    for p in paths:
        st = Path(p).stat()
        out[str(Path(p).relative_to(REPO)).replace("\\", "/")] = [int(st.st_size), int(st.st_mtime_ns)]
    return out


def cache_key() -> dict[str, Any]:
    return {"inputs": file_key(INPUT_FILES), "modules": file_key(MODULES), "cut": CUT, "first": FIRST, "last": LAST}


def d691_key_ok(root: str) -> bool:
    """D691's own cache key (stage0_d691_iv_size.iv_cached), re-derived: the options fixture's, the strip's, the calendar's and D691's mtimes."""
    key = ";".join(f"{p.name}:{p.stat().st_mtime_ns}" for p in (FIX / f"fut_{root.lower()}_options_eod.csv.gz", FIX / "fut_settle_strip.csv.gz",
                                                                FIX / "fut_index_sessions.csv.gz", REPO / "scripts" / "stage0_d691_iv_size.py"))
    return (REPO / "temp" / f"d691_iv_{root.lower()}.key").read_text(encoding="utf-8") == key


# ================================================================================ loaders (each seals)
def load_glx_rth(root: str) -> pd.DataFrame:
    """D663's bars: the opening fixture's 09:30-15:59 rows of `root`, file order kept (D663's groupby().last() reads that order)."""
    x = read_sealed(FIX / "fut_opening_globex_1m.csv.gz", ["root", "session", "hhmm", "close", "volume"],
                    {"root": str, "session": str, "hhmm": str}, "session", lo=WARM_GLX,
                    keep=lambda c: (c["root"] == root) & (c["hhmm"] >= "09:30") & (c["hhmm"] <= "15:59"))
    return x.reset_index(drop=True)


def load_rth(root: str) -> pd.DataFrame:
    """D487's bars: fut_{root}_rth_1m (09:30-15:59, D462 front)."""
    return read_sealed(FIX / f"fut_{root}_rth_1m.csv.gz", ["day", "hhmm", "open", "close"], {"day": str, "hhmm": str}, "day", lo=WARM_RTH)


def load_ho_bars() -> pd.DataFrame:
    return read_sealed(FIX / "fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz", ["root", "session", "hhmm", "open", "close"],
                       {"root": str, "session": str, "hhmm": str}, "session", lo=WARM_GLX,
                       keep=lambda c: (c["root"] == "HO") & (c["hhmm"] >= "09:00") & (c["hhmm"] <= "14:29"))


def load_strip() -> pd.DataFrame:
    return read_sealed(FIX / "fut_settle_strip.csv.gz", ["root", "contract", "ref", "settle"], {"root": str, "contract": str, "ref": str},
                       "ref", lo="2015-01-01", keep=lambda c: c["root"].isin(["ES", "NQ", "HO", "CL"]))


def load_curve() -> pd.DataFrame:
    return read_sealed(FIX / "fut_curve_front_next.csv.gz", ["root", "ref", "front", "front_settle", "next", "next_settle", "root_settles"],
                       {"root": str, "ref": str, "front": str, "next": str}, "ref", lo="2015-01-01",
                       keep=lambda c: c["root"].isin(["ES", "NQ", "HO", "CL", "ZT"]))


def load_isess() -> pd.DataFrame:
    return read_sealed(FIX / "fut_index_sessions.csv.gz", ["root", "day", "bars", "day_volume"], {"root": str, "day": str}, "day",
                       lo="2015-01-01", keep=lambda c: c["root"].isin(["ES", "NQ"]))


def load_micro() -> pd.DataFrame:
    return read_sealed(FIX / "fut_micro_day_volume.csv.gz", ["root", "day", "day_volume"], {"root": str, "day": str}, "day")


def load_etf() -> pd.DataFrame:
    e = read_sealed(FIX / "etf_wide_daily_raw.csv.gz", ["timestamp", "symbol", "close"], {"timestamp": str, "symbol": str}, "timestamp",
                    lo="2015-01-01", keep=lambda c: c["symbol"].isin(["SMH", "QQQ"]))
    e["date"] = e["timestamp"].str[:10]
    return e[["symbol", "date", "close"]].sort_values(["symbol", "date"]).reset_index(drop=True)


def load_events() -> pd.DataFrame:
    e = read_sealed(DATA / "calendar" / "events.csv", ["datetime_et", "event"], {"datetime_et": str, "event": str}, "datetime_et")
    e["date"] = e["datetime_et"].str[:10]
    return e[["date", "event", "datetime_et"]]


def load_iv(root: str) -> pd.DataFrame:
    """D691's IV cache: its key must match (else D691 would rebuild it; we refuse rather than compute over 2024 rows); >= 2024 dropped."""
    if not d691_key_ok(root):
        raise D722Error(f"[D691] temp/d691_iv_{root.lower()}.csv is stale against D691's own key; D722 does not rebuild it")
    t = pd.read_csv(REPO / "temp" / f"d691_iv_{root.lower()}.csv", index_col=0, dtype={"expiry": str, "underlying": str, "reason": str},
                    encoding="utf-8")
    t.index = t.index.astype(str)
    t = t[t.index < CUT]
    seal(t.index, f"d691_iv_{root.lower()}")
    return t[["iv"]].copy()


def load_ho_band() -> dict[str, Any]:
    c = read_sealed(FIX / "cme_session_calendar.csv.gz", ["root", "day", "is_trading", "session_open_et", "session_close_et"],
                    {"root": str, "day": str, "session_open_et": str, "session_close_et": str}, "day", lo=FIRST,
                    keep=lambda c: c["root"] == "HO")
    c = c[c["is_trading"].astype(str) == "True"]
    o, cl = c["session_open_et"].mode().iloc[0], c["session_close_et"].mode().iloc[0]
    if (o, cl) != ("09:00", "14:29"):
        raise D722Error(f"[HO band] the calendar's modal HO session is {o}-{cl}, not 09:00-14:29")
    return {"open": o, "close": cl, "open_share": float((c["session_open_et"] == o).mean()), "close_share": float((c["session_close_et"] == cl).mean())}


# ================================================================================ D688 / D699: G_SUM
def build_gsum(sample_keep: list[str], log=P) -> dict[str, Any]:
    """D699's `panel` first half, verbatim in substance: D688's inputs, its ES-book rebuild over processes (sessions[i::N]), build_panel,
    G_SUM = G_SPX + G_ES; D699's finiteness filter and its beta_G reproduction (to the bit) BEFORE anything is kept."""
    t0 = time.time()
    m581 = D688.d581(FIX)
    I = D688.load_inputs(DATA, lambda *a: None)
    es581 = m581.load_es(lambda *a: None)
    strip_es = I["strip"]
    refs = np.array(sorted(strip_es["ref"].unique()))
    win = [d for d in I["days"] if d >= D688.IN_FROM]
    strides = [win[i::D688.N_WORKERS] for i in range(D688.N_WORKERS)]
    with ProcessPoolExecutor(max_workers=D688.N_WORKERS, initializer=D688._init,
                             initargs=(str(FIX), es581, strip_es, I["cal"], I["tcal"], refs)) as ex:
        futs = [ex.submit(D688._work, (s, sample_keep)) for s in strides]
        Dfull = D688.build_panel(I, lambda *a: None)
        outs = [f.result() for f in futs]
    busy = sum(o["s"] for o in outs)
    wall = time.time() - t0
    prior = pd.concat([o["prior"] for o in outs]).sort_index()
    D = Dfull.join(prior[["G_ES"]], how="left")
    D = D[D.index >= D688.IN_FROM]
    D["G_SUM"] = D["G_SPX"] + D["G_ES"]
    need = ["P1530", "P1600", "P1100", "P1130", "P1550", "S_prev", "sig", "V", "G_SPX", "G_ES", "A_L"] + ["P" + t.replace(":", "") for t in D688.CLOCK]
    ok = np.isfinite(D[need].to_numpy(float)).all(1)
    Dg = D[ok]
    D688.guard_window(D.index, "D722 G_SUM panel")
    r = 100 * np.log(Dg["P1530"].to_numpy(float) / Dg["S_prev"].to_numpy(float))
    R2 = 1e4 * np.log(Dg["P1600"].to_numpy(float) / Dg["P1530"].to_numpy(float))
    f688, _ = D688.gamma_regression(R2, Dg["G_SUM"].to_numpy(float), r, Dg["sig"].to_numpy(float), Dg["V"].to_numpy(float),
                                    Dg["A_L"].to_numpy(float), null=False)
    ref = json.loads((DATA / "d688_gamma_close.json").read_text(encoding="utf-8"))["gate1"]["G1"]["beta_G"]
    if f688["beta_G"] != ref:
        raise D722Error(f"[REPRO] beta_G {f688['beta_G']!r} vs D688's {ref!r}: the G_SUM panel is not D699's")
    g = pd.DataFrame({"G_SPX": D["G_SPX"], "G_ES": D["G_ES"], "G_SUM": D["G_SUM"],
                      "G_SPX_sameday": D["G_SPX_sameday"], "in_d699": ok}, index=D.index)
    kept = pd.concat([o["kept"] for o in outs], ignore_index=True)
    seal(g.index, "G_SUM panel")
    seal(kept["session"], "options kept for the lag audit")
    log(f"  G_SUM: {len(g)} sessions, {int(ok.sum())} in D699's panel; D688 beta_G reproduced to the bit "
        f"({f688['beta_G']!r}); ES book over {D688.N_WORKERS} processes, [SPEED] {busy / wall:.2f}x ({100 * busy / wall / D688.N_WORKERS:.0f}%); "
        f"{time.time() - t0:.0f} s")
    return {"g": g, "beta_G": f688["beta_G"], "n_d699": int(ok.sum()), "kept": kept,
            "I": {k: I[k] for k in ("bars", "strip", "dix", "tcal", "days")}, "speed": busy / wall}


# ================================================================================ inputs bundle
def gsum_audit_sample() -> list[str]:
    """X3's lag-audit sessions, fixed before the ES book is rebuilt (its rows are kept in the same pass)."""
    s = pd.read_csv(FIX / "fut_index_sessions.csv.gz", usecols=["root", "day", "bars"], dtype={"root": str, "day": str}, encoding="utf-8")
    s = s[(s["root"] == "ES") & (s["day"] >= "2016-02-16") & (s["day"] <= LAST) & (s["bars"] >= 390)]
    days = np.array(sorted(s["day"].unique()))
    seal(days, "X3 audit sample")
    rng = np.random.default_rng(SEED + 3)
    return sorted(rng.choice(days, size=75, replace=False).tolist())


def inputs_key() -> dict[str, Any]:
    """The inputs bundle's key: every input file and every OTHER module by size+mtime, and this module's loader code by source hash
    (so editing the panel's arithmetic does not force a three-minute reload, while editing a loader does)."""
    import inspect
    src = "".join(inspect.getsource(f) for f in (seal, read_sealed, load_glx_rth, load_rth, load_ho_bars, load_strip, load_curve,
                                                   load_isess, load_micro, load_etf, load_events, load_iv, load_ho_band, build_gsum,
                                                   gsum_audit_sample, load_inputs, d691_key_ok))
    k = cache_key()
    k["modules"] = {m: v for m, v in k["modules"].items() if not m.endswith("diag_d722_conditioners.py")}
    k["loader_sha256"] = hashlib.sha256(src.encode("utf-8")).hexdigest()
    k["constants"] = [CUT, WARM_RTH, WARM_GLX, SEED]
    return k


def load_inputs(refresh: bool = False, log=P) -> dict[str, Any]:
    key = inputs_key()
    if not refresh and INPUTS_PKL.exists():
        with open(INPUTS_PKL, "rb") as f:
            I = pickle.load(f)
        if I.get("key") == key:
            reseal_inputs(I)
            log(f"  inputs from {INPUTS_PKL.relative_to(REPO)} (key matches)")
            return I
        log("  inputs cache stale: rebuilding")
    t0 = time.time()
    x3s = gsum_audit_sample()
    jobs: dict[str, Callable[[], Any]] = {
        "glx_ES": lambda: load_glx_rth("ES"), "glx_NQ": lambda: load_glx_rth("NQ"), "rth_ES": lambda: load_rth("ES"),
        "rth_NQ": lambda: load_rth("NQ"), "hob": load_ho_bars, "strip": load_strip, "curve": load_curve, "isess": load_isess,
        "micro": load_micro, "etf": load_etf, "events": load_events, "iv_ES": lambda: load_iv("ES"), "iv_NQ": lambda: load_iv("NQ"),
        "ho_band": load_ho_band}
    I: dict[str, Any] = {}
    t_items: dict[str, float] = {}

    def timed(k):
        s = time.time()
        v = jobs[k]()
        t_items[k] = time.time() - s
        return k, v
    # the ES book rebuild (processes) is the long pole; the file loaders run beside it on threads (gzip and the C parser release the GIL)
    with ThreadPoolExecutor(max_workers=6) as tp:
        futs = [tp.submit(timed, k) for k in jobs]
        gs = build_gsum(x3s, log)
        for f in futs:
            k, v = f.result()
            I[k] = v
    wall = time.time() - t0
    log(f"  loaders: sum(item time) {sum(t_items.values()):.0f} s beside the ES book; inputs wall {wall:.0f} s")
    I.update(gsum=gs, x3_sample=x3s, key=key, load_wall_s=wall)
    reseal_inputs(I)
    TMP.mkdir(parents=True, exist_ok=True)
    with open(INPUTS_PKL, "wb") as f:
        pickle.dump(I, f, protocol=pickle.HIGHEST_PROTOCOL)
    return I


def input_frames(I: dict[str, Any]) -> list[tuple[str, pd.DataFrame, str]]:
    """(name, frame, date column or '__index__') for every input series the panel reads."""
    fr = [("glx_ES", I["glx_ES"], "session"), ("glx_NQ", I["glx_NQ"], "session"), ("rth_ES", I["rth_ES"], "day"),
          ("rth_NQ", I["rth_NQ"], "day"), ("hob", I["hob"], "session"), ("strip", I["strip"], "ref"), ("curve", I["curve"], "ref"),
          ("isess", I["isess"], "day"), ("micro", I["micro"], "day"), ("etf", I["etf"], "date"), ("events", I["events"], "date"),
          ("iv_ES", I["iv_ES"], "__index__"), ("iv_NQ", I["iv_NQ"], "__index__"), ("gsum", I["gsum"]["g"], "__index__"),
          ("d688_bars", I["gsum"]["I"]["bars"], "day"), ("d688_strip", I["gsum"]["I"]["strip"], "ref"),
          ("d688_dix", I["gsum"]["I"]["dix"], "date"), ("opts_kept", I["gsum"]["kept"], "session")]
    return fr


def reseal_inputs(I: dict[str, Any]) -> None:
    for name, df, col in input_frames(I):
        seal(df.index if col == "__index__" else df[col], f"input {name}")
    seal(I["gsum"]["I"]["days"], "input d688 days")


# ================================================================================ helpers
def prior_map(src: np.ndarray, vals: np.ndarray, targets: np.ndarray, same_day: bool = False) -> np.ndarray:
    """The value of the last source row dated strictly before each target (same_day=True: on or before -- the leak canary)."""
    src = np.asarray(src, dtype=object).astype(str)
    pos = np.searchsorted(src, np.asarray(targets).astype(str), side="right" if same_day else "left") - 1
    v = np.asarray(vals, float)
    return np.where(pos >= 0, v[np.clip(pos, 0, None)], np.nan)


def roll_std(x: np.ndarray, n: int, minp: int) -> np.ndarray:
    """sd (ddof 1) of the finite values in each window of n ending at i; NaN below minp finite. Vectorised (sliding windows)."""
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    W = np.lib.stride_tricks.sliding_window_view(x, n)
    f = np.isfinite(W)
    c = f.sum(1)
    Z = np.where(f, W, 0.0)
    m = Z.sum(1) / np.maximum(c, 1)
    v = (np.where(f, W - m[:, None], 0.0) ** 2).sum(1) / np.maximum(c - 1, 1)
    out[n - 1:] = np.where(c >= minp, np.sqrt(v), np.nan)
    return out


def roll_sum(x: np.ndarray, n: int, minp: int) -> np.ndarray:
    x = np.asarray(x, float)
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    W = np.lib.stride_tricks.sliding_window_view(x, n)
    f = np.isfinite(W)
    s = np.where(f, W, 0.0).sum(1)
    out[n - 1:] = np.where(f.sum(1) >= minp, s, np.nan)
    return out


def settling(curve: pd.DataFrame, root: str) -> pd.DataFrame:
    c = curve[(curve["root"] == root) & (curve["root_settles"].astype(str) == "True")].sort_values("ref").reset_index(drop=True)
    if c["ref"].duplicated().any():
        raise D722Error(f"[CURVE] {root}: duplicate settling refs")
    return c


def same_contract_returns(curve: pd.DataFrame, strip: pd.DataFrame, root: str, front_to_front: bool = False) -> pd.Series:
    """ln(S_t(front_t) / S_prev(front_t)) over the root's settling sessions (front_to_front=True: the WRONG quantity, S_prev(front_prev))."""
    c = settling(curve, root)
    refs = c["ref"].to_numpy(str)
    s = strip[strip["root"] == root].set_index(["ref", "contract"])["settle"]
    s = s[~s.index.duplicated()]
    front = c["front"].to_numpy(str)
    f_t = c["front_settle"].to_numpy(float)
    prev_contract = np.r_[[""], front[:-1]] if front_to_front else front
    prev_ref = np.r_[[""], refs[:-1]]
    f_p = s.reindex(list(zip(prev_ref, prev_contract))).to_numpy(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where((f_t > 0) & (f_p > 0), np.log(f_t / f_p), np.nan)
    r[0] = np.nan
    return pd.Series(r, index=refs)


def bucket_matrix(bars: pd.DataFrame, datecol: str, open_hhmm: str, ends: list[str], full_rule: str, n_full: int = 390):
    """Sessions x q simple bucket returns in bp (D487's (C / prev - 1) x 1e4, the first from the open). full_rule 'count' = exactly
    n_full bars (D487); 'anchors' = the open bar and every bucket-end bar present (HO)."""
    b = bars
    n = b.groupby(datecol).size()
    C = b.pivot(index=datecol, columns="hhmm", values="close").reindex(columns=ends)
    O = b[b["hhmm"] == open_hhmm].set_index(datecol)["open"].reindex(C.index)
    if full_rule == "count":
        full = n.reindex(C.index) == n_full
    else:
        full = np.isfinite(C.to_numpy(float)).all(1) & np.isfinite(O.to_numpy(float))
        full = pd.Series(full, index=C.index)
    C = C[full.to_numpy()]
    O = O[full.to_numpy()]
    Cm = C.to_numpy(float)
    prev = np.column_stack([O.to_numpy(float), Cm[:, :-1]])
    X = (Cm / prev - 1) * 1e4
    return np.asarray(C.index, dtype=object).astype(str), X


_BM: dict[tuple, tuple] = {}


def bucket_matrix_memo(bars: pd.DataFrame, datecol: str, open_hhmm: str, ends: list[str], full_rule: str):
    """Hoisted: the bucket matrix does not depend on a canary's leak or wrong quantity, so it is built once per bar frame."""
    k = (id(bars), len(bars), datecol, open_hhmm, tuple(ends), full_rule)
    if k not in _BM:
        _BM[k] = (bars, bucket_matrix(bars, datecol, open_hhmm, ends, full_rule))
    return _BM[k][1]


def vr_rolling(X: np.ndarray, n: int) -> np.ndarray:
    """D487's S1 over each window of n sessions ending at i: var(sum, ddof 1) / (q var(all bucket returns, ddof 1))."""
    out = np.full(len(X), np.nan)
    if len(X) < n:
        return out
    q = X.shape[1]
    R = X.sum(axis=1)
    vR = np.lib.stride_tricks.sliding_window_view(R, n).var(axis=1, ddof=1)
    WX = np.lib.stride_tricks.sliding_window_view(X, (n, q))[:, 0].reshape(len(X) - n + 1, n * q)
    out[n - 1:] = vR / (q * WX.var(axis=1, ddof=1))
    return out


ENDS30_ES = [f"{h:02d}:{m:02d}" for h in range(9, 16) for m in (29, 59) if (h, m) >= (9, 59)]            # 09:59 .. 15:59, 13
ENDS15_ES = list(D487.ENDS)                                                                                # 09:44 .. 15:59, 26
ENDS30_HO = [f"{h:02d}:{m:02d}" for h in range(9, 15) for m in (29, 59) if (h, m) <= (14, 29)]           # 09:29 .. 14:29, 11
ENDS15_HO = [f"{h:02d}:{m:02d}" for h in range(9, 15) for m in (14, 29, 44, 59) if (h, m) <= (14, 29)]   # 09:14 .. 14:29, 22
assert len(ENDS30_ES) == 13 and len(ENDS15_ES) == 26 and len(ENDS30_HO) == 11 and len(ENDS15_HO) == 22


def sessions_of(I: dict[str, Any], root: str) -> np.ndarray:
    if root in ("ES", "NQ"):
        s = I["isess"]
        d = s.loc[(s["root"] == root) & (s["day"] >= FIRST) & (s["day"] <= LAST), "day"].unique()
    else:
        h = I["hob"]
        d = h.loc[(h["session"] >= FIRST) & (h["session"] <= LAST), "session"].unique()
    return np.array(sorted(d), dtype=object).astype(str)


def eip_windows(sess: np.ndarray, dates: dict[str, str]) -> np.ndarray:
    flag = np.zeros(len(sess), dtype=bool)
    for k, d0 in dates.items():
        i = int(np.searchsorted(sess, d0, side="left"))
        flag[i:i + EIP_WINDOW] = True
    return flag


# ================================================================================ the panel (vectorised)
def compute(I: dict[str, Any], leak: str | None = None, wrong: str | None = None) -> tuple[pd.DataFrame, dict[str, Any]]:
    """The panel. `leak` = a variable computed SAME-DAY (the lag canary); `wrong` = a variable computed as the quantity we did NOT mean
    (the right-quantity canary: 'X4' roll changes included, 'sig20_HO'/'X5'/'r60' front-to-front, 'X6' unlagged)."""
    lk = lambda v: leak == v  # noqa: E731
    curve, strip = I["curve"], I["strip"]
    aux: dict[str, Any] = {}
    # market-level series, each on its own calendar, then mapped to prior(d)
    zt = settling(curve, "ZT")
    zf = zt["front"].to_numpy(str)
    chg = np.r_[np.nan, np.diff(zt["front_settle"].to_numpy(float))]
    if wrong != "X4":
        chg = np.where(np.r_[False, zf[1:] == zf[:-1]], chg, np.nan)
    zsd = roll_std(chg, SIG_N, SIG_MIN)
    cl_r = same_contract_returns(curve, strip, "CL", front_to_front=(wrong == "X5"))
    cl_sd = roll_std(cl_r.to_numpy(float), SIG_N, SIG_MIN)
    etf = I["etf"]
    etf_r = {}
    for sym in ("SMH", "QQQ"):
        e = etf[etf["symbol"] == sym]
        c = e["close"].to_numpy(float)
        r = np.r_[np.nan, np.log(c[1:] / c[:-1])]
        ca = np.abs(r) > CA_LIMIT
        aux[f"etf_ca_days_{sym}"] = e["date"].to_numpy(str)[ca].tolist()
        r = np.where(ca, np.nan, r)
        etf_r[sym] = pd.Series(roll_sum(r, ETF_N, ETF_MIN), index=e["date"].to_numpy(str))
    if not etf_r["SMH"].index.equals(etf_r["QQQ"].index):
        raise D722Error("[ETF] SMH and QQQ do not share one calendar")
    x11_src = etf_r["SMH"].index.to_numpy(str)
    x11_val = (etf_r["SMH"] - etf_r["QQQ"]).to_numpy(float)
    ev = I["events"]
    ev_by = {k: set(ev.loc[ev["event"] == k, "date"]) for k in ("FOMC", "FOMC_UNSCHEDULED", "CPI", "EMPSIT", "EIA_WPSR")}
    g = I["gsum"]["g"]
    gsum_col = g["G_SPX_sameday"] + g["G_ES"] if lk("X3") else g["G_SUM"]
    rows = []
    for root in ROOTS:
        sess = sessions_of(I, root)
        F = pd.DataFrame(index=pd.Index(sess, name="session"))
        # ---- sig20 / X1
        if root in ("ES", "NQ"):
            x = I[f"glx_{root}"]
            close = x.groupby("session")["close"].last()
            r_bp = np.log(close / close.shift(1)) * 1e4
            sig_ok = r_bp.shift(1).rolling(SIG_N, min_periods=SIG_MIN).std().reindex(sess).to_numpy(float)   # D663, verbatim
            sig_lk = r_bp.rolling(SIG_N, min_periods=SIG_MIN).std().reindex(sess).to_numpy(float)            # same-day (canary)
            F["sig20"] = (sig_lk if lk("sig20") else sig_ok) / 1e4
            sig_bp = sig_lk if lk("X2") else sig_ok
        else:
            rr = same_contract_returns(curve, strip, root, front_to_front=(wrong == "sig20_HO"))
            sd = roll_std(rr.to_numpy(float), SIG_N, SIG_MIN)
            F["sig20"] = prior_map(rr.index.to_numpy(str), sd, sess, same_day=lk("sig20"))
            sig_bp = F["sig20"].to_numpy(float) * 1e4
        with np.errstate(divide="ignore", invalid="ignore"):
            F["X1"] = np.log(F["sig20"].to_numpy(float))
        # ---- X2
        if root in ("ES", "NQ"):
            iv = I[f"iv_{root}"]["iv"].reindex(sess).to_numpy(float)
            rv = sig_bp / 1e4 * np.sqrt(252.0)
            with np.errstate(divide="ignore", invalid="ignore"):
                F["X2"] = np.log(iv / rv)
        else:
            F["X2"] = np.nan
        # ---- X3
        if root in ("ES", "NQ"):
            gs = gsum_col.reindex(sess).to_numpy(float)
            F["X3"] = np.where(np.isfinite(gs), (gs < 0).astype(float), np.nan)
            aux[f"G_SUM_{root}"] = pd.Series(gs, index=sess)
        else:
            F["X3"] = np.nan
        # ---- X4, X5 (market level)
        with np.errstate(divide="ignore", invalid="ignore"):
            F["X4"] = np.log(prior_map(zt["ref"].to_numpy(str), zsd, sess, same_day=lk("X4")))
            F["X5"] = np.log(prior_map(cl_r.index.to_numpy(str), cl_sd, sess, same_day=lk("X5")))
        # ---- X6 (30 min) and X6_15m
        for col, ends in (("X6", ENDS30_ES if root != "HO" else ENDS30_HO), ("X6_15m", ENDS15_ES if root != "HO" else ENDS15_HO)):
            if root in ("ES", "NQ"):
                dts, X = bucket_matrix_memo(I[f"rth_{root}"], "day", "09:30", ends, "count")
            else:
                dts, X = bucket_matrix_memo(I["hob"], "session", "09:00", ends, "anchors")
            v = vr_rolling(X, VR_N)
            F[col] = prior_map(dts, v, sess, same_day=lk(col) or (wrong == "X6" and col == "X6"))
        # ---- r60
        rr = same_contract_returns(curve, strip, root, front_to_front=(wrong == "r60"))
        F["r60"] = prior_map(rr.index.to_numpy(str), roll_sum(rr.to_numpy(float), R60_N, R60_N), sess, same_day=lk("r60"))
        # ---- X8 (the session's own calendar date; the canary keys it on the PRIOR session instead)
        key = np.r_[[""], sess[:-1]] if lk("X8") else sess
        for col, evs in (("fomc", ("FOMC", "FOMC_UNSCHEDULED")), ("fomc_unscheduled", ("FOMC_UNSCHEDULED",)), ("cpi", ("CPI",)),
                         ("empsit", ("EMPSIT",)), ("eia_wpsr", ("EIA_WPSR",))):
            F[col] = np.array([any(k in ev_by[e] for e in evs) for k in key], dtype=float)
        macro = (F["fomc"] + F["cpi"] + F["empsit"]) > 0
        F["X8"] = (macro | ((F["eia_wpsr"] > 0) & (root == "HO"))).astype(float)
        # ---- X9
        F["X9"] = eip_windows(sess if not lk("X9") else np.r_[sess[1:], ["9999-12-31"]], EIP_FIRST_DEPOSIT_VERIFIED).astype(float)
        F["X9_record"] = eip_windows(sess, EIP_FIRST_DEPOSIT_RECORD).astype(float)
        # ---- X10
        if root in ("ES", "NQ"):
            micro = {"ES": "MES", "NQ": "MNQ"}[root]
            s = I["isess"]
            big = s[s["root"] == root].set_index("day")["day_volume"].sort_index()
            mv = I["micro"]
            sm = mv[mv["root"] == micro].set_index("day")["day_volume"].reindex(big.index)
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = np.log(sm.to_numpy(float) / big.to_numpy(float))
            ratio = np.where(np.isfinite(ratio), ratio, np.nan)
            F["X10"] = prior_map(big.index.to_numpy(str), ratio, sess, same_day=lk("X10"))
        else:
            F["X10"] = np.nan
        # ---- X11
        F["X11"] = prior_map(x11_src, x11_val, sess, same_day=lk("X11")) if root in ("ES", "NQ") else np.nan
        # ---- X12
        if root == "HO":
            h = settling(curve, "HO")
            fs, ns = h["front_settle"].to_numpy(float), h["next_settle"].to_numpy(float)
            F["X12"] = prior_map(h["ref"].to_numpy(str), (fs - ns) / fs, sess, same_day=lk("X12"))
        else:
            F["X12"] = np.nan
        # ---- war
        F["war"] = ((F.index >= WAR[0]) & (F.index <= WAR[1])).astype(float)
        F.insert(0, "root", root)
        rows.append(F.reset_index())
    panel = pd.concat(rows, ignore_index=True).set_index(["root", "session"])[COLUMNS]
    seal(panel.index.get_level_values("session"), "panel")
    return panel, aux


# ================================================================================ the lag audit: a second implementation (plain loops)
class Raw:
    """Per-session dictionaries from the RAW input frames (never the vectorised panel's intermediates)."""

    def __init__(self, I: dict[str, Any]):
        self.I = I
        self.glx = {}
        for r in ("ES", "NQ"):
            d: dict[str, list] = {}
            for s, c in zip(I[f"glx_{r}"]["session"].to_numpy(str), I[f"glx_{r}"]["close"].to_numpy(float)):
                d.setdefault(s, []).append(c)
            self.glx[r] = d
        self.bars = {}
        for r, df, dc in (("ES", I["rth_ES"], "day"), ("NQ", I["rth_NQ"], "day"), ("HO", I["hob"], "session")):
            d2: dict[str, dict[str, tuple[float, float]]] = {}
            for s, hm, o, c in zip(df[dc].to_numpy(str), df["hhmm"].to_numpy(str), df["open"].to_numpy(float), df["close"].to_numpy(float)):
                d2.setdefault(s, {})[hm] = (o, c)
            self.bars[r] = d2
        self.curve: dict[str, list[tuple]] = {}
        for rec in I["curve"].itertuples(index=False):
            if str(rec.root_settles) == "True":
                self.curve.setdefault(rec.root, []).append((rec.ref, rec.front, float(rec.front_settle), rec.next, float(rec.next_settle)))
        for k in self.curve:
            self.curve[k].sort()
        st = I["strip"]
        self.settle = {(a, b, c): float(v) for a, b, c, v in zip(st["root"].to_numpy(str), st["ref"].to_numpy(str),
                                                                 st["contract"].to_numpy(str), st["settle"].to_numpy(float))}
        self.memo: dict[tuple, Any] = {}
        self.isess = {(rec.root, rec.day): float(rec.day_volume) for rec in I["isess"].itertuples(index=False)}
        self.micro = {(rec.root, rec.day): float(rec.day_volume) for rec in I["micro"].itertuples(index=False)}
        self.etf = {}
        for rec in I["etf"].itertuples(index=False):
            self.etf.setdefault(rec.symbol, []).append((rec.date, float(rec.close)))
        self.events = [(rec.date, rec.event) for rec in I["events"].itertuples(index=False)]

    def get(self, key: tuple, fn: Callable[[], Any]) -> Any:
        """Memoised: the second path is a pure function of (variable, root, session), so the canaries re-read it, never re-derive it."""
        if key not in self.memo:
            self.memo[key] = fn()
        return self.memo[key]

    @staticmethod
    def sd(vals: list[float], minp: int) -> float:
        v = [x for x in vals if math.isfinite(x)]
        if len(v) < minp:
            return float("nan")
        m = sum(v) / len(v)
        return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))

    def settle_returns_before(self, root: str, d: str, n: int) -> list[float]:
        rows = [x for x in self.curve[root] if x[0] < d][-(n + 1):]
        out = []
        for i in range(1, len(rows)):
            ref, front, f_t = rows[i][0], rows[i][1], rows[i][2]
            f_p = self.settle.get((root, rows[i - 1][0], front), float("nan"))
            out.append(math.log(f_t / f_p) if (f_t > 0 and f_p > 0) else float("nan"))
        return out

    def sig20(self, root: str, d: str) -> float:
        if root in ("ES", "NQ"):
            prev = sorted(s for s in self.glx[root] if s < d)[-(SIG_N + 1):]
            cl = [[c for c in self.glx[root][s] if math.isfinite(c)][-1] for s in prev]
            rets = [math.log(cl[i] / cl[i - 1]) * 1e4 for i in range(1, len(cl))]
            if len(prev) < SIG_N + 1:
                rets = rets  # the first fixture session has no return; the count rule below decides
            return self.sd(rets, SIG_MIN) / 1e4
        return self.sd(self.settle_returns_before(root, d, SIG_N), SIG_MIN)

    def x4(self, d: str) -> float:
        rows = [x for x in self.curve["ZT"] if x[0] < d][-(SIG_N + 1):]
        ch = [(rows[i][2] - rows[i - 1][2]) if rows[i][1] == rows[i - 1][1] else float("nan") for i in range(1, len(rows))]
        return math.log(self.sd(ch, SIG_MIN))

    def r60(self, root: str, d: str) -> float:
        r = self.settle_returns_before(root, d, R60_N)
        if len(r) < R60_N or not all(math.isfinite(x) for x in r):
            return float("nan")
        return math.fsum(r)

    def vr(self, root: str, d: str, ends: list[str]) -> float:
        bars = self.bars[root]
        op = "09:30" if root != "HO" else "09:00"
        got = []
        for s in sorted((s for s in bars if s < d), reverse=True):
            b = bars[s]
            if root != "HO":
                if len(b) != 390:
                    continue
            elif op not in b or any(e not in b for e in ends):
                continue
            px = [b[op][0]] + [b[e][1] for e in ends]
            got.append([(px[i] / px[i - 1] - 1) * 1e4 for i in range(1, len(px))])
            if len(got) == VR_N:
                break
        if len(got) < VR_N:
            return float("nan")
        q = len(ends)
        day = [sum(x) for x in got]
        flat = [v for x in got for v in x]

        def var(v):
            m = sum(v) / len(v)
            return sum((a - m) ** 2 for a in v) / (len(v) - 1)
        return var(day) / (q * var(flat))

    def x10(self, root: str, d: str) -> float:
        days = sorted(k[1] for k in self.isess if k[0] == root and k[1] < d)
        if not days:
            return float("nan")
        p = days[-1]
        m = self.micro.get(({"ES": "MES", "NQ": "MNQ"}[root], p))
        b = self.isess[(root, p)]
        return math.log(m / b) if (m is not None and m > 0 and b > 0) else float("nan")

    def x11(self, d: str) -> float:
        out = {}
        for sym in ("SMH", "QQQ"):
            rows = [x for x in self.etf[sym] if x[0] < d][-(ETF_N + 1):]
            rets = [math.log(rows[i][1] / rows[i - 1][1]) for i in range(1, len(rows))]
            rets = [r for r in rets if abs(r) <= CA_LIMIT]
            out[sym] = math.fsum(rets) if len(rets) >= ETF_MIN else float("nan")
        return out["SMH"] - out["QQQ"]

    def x12(self, d: str) -> float:
        rows = [x for x in self.curve["HO"] if x[0] < d]
        ref, front, fs, nxt, ns = rows[-1]
        return (fs - ns) / fs

    def flags(self, root: str, d: str) -> dict[str, float]:
        evs = {e for (dt, e) in self.events if dt == d}
        f = {"fomc": float(bool(evs & {"FOMC", "FOMC_UNSCHEDULED"})), "fomc_unscheduled": float("FOMC_UNSCHEDULED" in evs),
             "cpi": float("CPI" in evs), "empsit": float("EMPSIT" in evs), "eia_wpsr": float("EIA_WPSR" in evs)}
        f["X8"] = float(bool(evs & set(MACRO)) or (root == "HO" and "EIA_WPSR" in evs))
        f["war"] = float(WAR[0] <= d <= WAR[1])
        return f

    def x9(self, sess: list[str], d: str, dates: dict[str, str]) -> float:
        for d0 in dates.values():
            win = [s for s in sess if s >= d0][:EIP_WINDOW]
            if d in win:
                return 1.0
        return 0.0


def close_enough(a: float, b: float, exact: bool) -> bool:
    if not (math.isfinite(a) and math.isfinite(b)):
        return (not math.isfinite(a)) and (not math.isfinite(b))
    if exact:
        return a == b
    return abs(a - b) <= REL * max(1.0, abs(a), abs(b)) if abs(a) < 1 else abs(a - b) <= REL * max(abs(a), abs(b))


def audit_sample(I: dict[str, Any], root: str) -> list[str]:
    """>= 50 random sessions per root (seed 722), plus forced ones where a leak or a mis-keying must show: event days, the EIP window
    edges, roll sessions, the first X10 sessions."""
    sess = sessions_of(I, root)
    rng = np.random.default_rng(SEED + ROOTS.index(root))
    pick = set(rng.choice(sess[sess >= "2016-04-01"], size=N_AUDIT, replace=False).tolist())
    ev = I["events"]
    for e in ("FOMC", "CPI", "EMPSIT", "EIA_WPSR"):
        dd = [x for x in ev.loc[ev["event"] == e, "date"] if x in set(sess)]
        pick.update(dd[5:8])
    for d0 in list(EIP_FIRST_DEPOSIT_VERIFIED.values()) + list(EIP_FIRST_DEPOSIT_RECORD.values()):
        i = int(np.searchsorted(sess, d0))
        pick.update(sess[max(0, i - 1):i + 2].tolist() + sess[i + EIP_WINDOW - 1:i + EIP_WINDOW + 1].tolist())
    pick.update(["2019-05-07", "2019-05-08", "2022-03-01", "2020-03-18", "2021-06-15", "2021-07-15"])
    return sorted(p for p in pick if p in set(sess))


def lag_audit(panel: pd.DataFrame, I: dict[str, Any], aux: dict[str, Any], raw: Raw | None = None, log=P) -> dict[str, Any]:
    """Every variable, >= 50 sessions per root, from raw inputs strictly before the session, never calling compute()."""
    raw = raw or Raw(I)
    stats: dict[str, Any] = {}
    worst: dict[str, float] = {}

    def chk(var: str, root: str, d: str, got: float, want: float, exact: bool):
        if not close_enough(float(got), float(want), exact):
            raise D722Error(f"[LAG] {root} {d} {var}: panel {got!r} vs second path {want!r}")
        if math.isfinite(got) and math.isfinite(want) and not exact:
            worst[var] = max(worst.get(var, 0.0), abs(got - want) / max(1e-300, abs(want)))
    for root in ROOTS:
        sess = sessions_of(I, root).tolist()
        sample = audit_sample(I, root)
        if len(sample) < 50:
            raise D722Error(f"[LAG] {root}: only {len(sample)} audit sessions")
        pr = panel.loc[root]
        G = raw.get
        for d in sample:
            row = pr.loc[d]
            s = G(("sig20", root, d), lambda: raw.sig20(root, d))
            chk("sig20", root, d, row["sig20"], s, exact=False)
            if root in ("ES", "NQ"):
                iv = float(I[f"iv_{root}"]["iv"].get(d, np.nan))
                want = math.log(iv / (s * math.sqrt(252.0))) if (math.isfinite(iv) and math.isfinite(s)) else float("nan")
                chk("X2", root, d, row["X2"], want, exact=False)
                chk("X10", root, d, row["X10"], G(("X10", root, d), lambda: raw.x10(root, d)), exact=True)
                chk("X11", root, d, row["X11"], G(("X11", d), lambda: raw.x11(d)), exact=False)
            else:
                chk("X12", root, d, row["X12"], G(("X12", d), lambda: raw.x12(d)), exact=True)
            chk("X4", root, d, row["X4"], G(("X4", d), lambda: raw.x4(d)), exact=False)
            chk("X5", root, d, row["X5"], G(("X5", d), lambda: math.log(raw.sig20("CL", d))), exact=False)
            chk("r60", root, d, row["r60"], G(("r60", root, d), lambda: raw.r60(root, d)), exact=False)
            e30, e15 = (ENDS30_ES, ENDS15_ES) if root != "HO" else (ENDS30_HO, ENDS15_HO)
            chk("X6", root, d, row["X6"], G(("X6", root, d), lambda: raw.vr(root, d, e30)), exact=False)
            chk("X6_15m", root, d, row["X6_15m"], G(("X6_15m", root, d), lambda: raw.vr(root, d, e15)), exact=False)
            for k, v in raw.flags(root, d).items():
                chk(k, root, d, row[k], v, exact=True)
            chk("X9", root, d, row["X9"], G(("X9", root, d), lambda: raw.x9(sess, d, EIP_FIRST_DEPOSIT_VERIFIED)), exact=True)
            chk("X9_record", root, d, row["X9_record"], G(("X9r", root, d), lambda: raw.x9(sess, d, EIP_FIRST_DEPOSIT_RECORD)), exact=True)
        stats[root] = len(sample)
    # X3: D688's own second implementation (second_path: loops over the option rows, never build_panel / es_book_prior)
    gs = I["gsum"]
    m = D688.d581(FIX)
    kept = gs["kept"]
    n3 = 0
    for d in I["x3_sample"]:
        if not bool(gs["g"]["in_d699"].get(d, False)):
            continue
        sp = raw.get(("X3", d), lambda: D688.second_path(d, gs["I"], kept[kept["session"] == d], m))
        want = sp["G_SPX"] + sp["G_ES"]
        for root in ("ES", "NQ"):
            got = float(aux[f"G_SUM_{root}"].get(d, np.nan))
            if not math.isfinite(got) and d not in set(sessions_of(I, root)):
                continue
            if not np.isclose(got, want, rtol=1e-9, atol=1e-9):
                raise D722Error(f"[LAG] {root} {d} G_SUM: panel {got!r} vs D688's second path {want!r}")
            if float(panel.loc[(root, d), "X3"]) != float(want < 0):
                raise D722Error(f"[LAG] {root} {d} X3: panel {panel.loc[(root, d), 'X3']} vs second path {float(want < 0)}")
        n3 += 1
    if n3 < 50:
        raise D722Error(f"[LAG] X3: only {n3} audit sessions inside D699's panel")
    stats["X3_sessions"] = n3
    stats["worst_rel_diff"] = {k: float(v) for k, v in worst.items()}
    log(f"  lag audit: sessions per root {dict((r, stats[r]) for r in ROOTS)}, X3 {n3} (D688 second_path, rtol 1e-9); worst relative "
        f"difference where float order differs: " + ", ".join(f"{k} {v:.1e}" for k, v in sorted(worst.items())))
    return stats


# ================================================================================ right quantity and known answers
def right_quantity(a: pd.Series, b: pd.Series, what: str) -> int:
    x, y = a.to_numpy(float), b.to_numpy(float)
    both = np.isfinite(x) & np.isfinite(y)
    n = int((both & (np.abs(x - y) > 1e-12)).sum() + (np.isfinite(x) != np.isfinite(y)).sum())
    if n == 0:
        raise D722Error(f"[RIGHT QUANTITY] {what}: identical to the quantity we did not mean")
    return n


def right_quantity_gates(I: dict[str, Any], panel: pd.DataFrame, log=P) -> dict[str, int]:
    out = {}
    for w, col in (("X4", "X4"), ("X5", "X5"), ("sig20_HO", "sig20"), ("r60", "r60"), ("X6", "X6")):
        alt, _ = compute(I, wrong=w)
        out[f"{col}_vs_{w}_wrong"] = right_quantity(panel[col], alt[col], f"{col} vs {w}")
    for v in ("X10", "X11"):
        alt, _ = compute(I, leak=v)
        out[f"{v}_vs_sameday"] = right_quantity(panel[v], alt[v], f"{v} vs same-day")
    log("  right quantity: sessions differing from the quantity not meant: " + ", ".join(f"{k} {v}" for k, v in out.items()))
    return out


def known_answers(I: dict[str, Any], panel: pd.DataFrame, d487_ref: dict | None = None, log=P) -> dict[str, Any]:
    """D663's own root_frame on the same bars; D487's recorded per-year S1 from this module's bucket matrix; D699's beta_G (in build_gsum);
    D691's key (in load_iv); the two ES/NQ RTH-close sources agree."""
    out: dict[str, Any] = {}
    for root in ("ES", "NQ"):
        x = I[f"glx_{root}"]
        b = x.assign(root=root)
        sess = sessions_of(I, root)
        tab = pd.DataFrame({"usable": True, "hi_10:00": 1.0, "lo_10:00": 1.0, "prior_close": 1.0, "open": 1.0}, index=pd.Index(sess))
        d = D663.root_frame(b, tab, root)
        mine = panel.loc[root, "sig20"].reindex(d.index).to_numpy(float) * 1e4     # /1e4 then *1e4: at most one ulp from D663's bp
        ref = d["sig20"].to_numpy(float)
        rel = np.abs(mine - ref) / ref
        if len(d) < 1900 or not np.isfinite(mine).all() or float(rel.max()) > 4e-16:
            raise D722Error(f"[KNOWN] {root}: sig20 is not D663's root_frame (max rel {float(np.nanmax(rel)):.2e}, n {len(d)})")
        out[f"d663_sig20_{root}"] = {"sessions_compared": int(len(d)), "max_rel_diff": float(rel.max()),
                                     "bitwise_equal_share": float((mine == ref).mean())}
        # D487 per-year S1 (15 minutes, D487's ENDS and full-session rule) from bucket_matrix + D487's own vr
        dts, X = bucket_matrix(I[f"rth_{root}"], "day", "09:30", ENDS15_ES, "count")
        refj = d487_ref or json.loads((DATA / "d487_continuation_stage0.json").read_text(encoding="utf-8"))
        yrs = {}
        for y in [str(k) for k in range(2016, 2024)]:
            m = (dts >= f"{y}-01-01") & (dts <= f"{y}-12-31") & (dts >= D487.START) & (dts <= D487.END)
            v, want = D487.vr(X[m]), refj[root]["groups"][y]["S1_vr"]
            if int(m.sum()) != refj[root]["groups"][y]["n"] or abs(v - want) > 1e-12 * abs(want):
                raise D722Error(f"[KNOWN] {root} {y}: D487 S1 {want!r} (n {refj[root]['groups'][y]['n']}) vs {v!r} (n {int(m.sum())})")
            yrs[y] = [round(v, 6), int(m.sum())]
        out[f"d487_S1_{root}"] = yrs
        # the two RTH-close sources (D663's opening fixture, D487's rth_1m) agree on the last bar's close
        c1 = x.groupby("session")["close"].last()
        r = I[f"rth_{root}"]
        c2 = r.sort_values(["day", "hhmm"]).groupby("day")["close"].last()
        j = pd.concat([c1, c2], axis=1, join="inner").sort_index()
        j = j[(j.index >= FIRST) & (j.index <= LAST)]
        agree = float((j.iloc[:, 0] == j.iloc[:, 1]).mean())
        if agree < 0.999:
            raise D722Error(f"[KNOWN] {root}: the two RTH sources agree on only {agree:.4f} of last closes")
        out[f"rth_sources_agree_{root}"] = {"sessions": int(len(j)), "share_equal": agree}
    out["d699_beta_G"] = I["gsum"]["beta_G"]
    out["d699_panel_sessions"] = I["gsum"]["n_d699"]
    log(f"  known answers: D663 root_frame sig20 identical (ES {out['d663_sig20_ES']['sessions_compared']}, NQ "
        f"{out['d663_sig20_NQ']['sessions_compared']} sessions); D487 per-year S1 reproduced on ES and NQ (8 years each); D699/D688 "
        f"beta_G {out['d699_beta_G']!r}; RTH sources agree ES {out['rth_sources_agree_ES']['share_equal']:.4f}, "
        f"NQ {out['rth_sources_agree_NQ']['share_equal']:.4f}")
    return out


def chunk_equals_whole(I: dict[str, Any]) -> int:
    """D688's ES book is rebuilt over session strides; each session is independent. Proven on the kept sessions: the whole set in one call
    equals the concatenation of per-stride calls, bit for bit."""
    gs = I["gsum"]
    m = D688.d581(FIX)
    kept = gs["kept"]
    strip_es = gs["I"]["strip"]
    refs = np.array(sorted(strip_es["ref"].unique()))
    whole = D688.es_book_prior(kept, strip_es, gs["I"]["tcal"], refs, m)
    days = sorted(kept["session"].unique())
    parts = pd.concat([D688.es_book_prior(kept[kept["session"].isin(days[i::4])], strip_es, gs["I"]["tcal"], refs, m) for i in range(4)]).sort_index()
    if not whole.equals(parts):
        raise D722Error("[CHUNK] the ES book over strides is not the whole")
    if not np.array_equal(whole["G_ES"].to_numpy(), gs["g"]["G_ES"].reindex(whole.index).to_numpy()):
        raise D722Error("[CHUNK] the kept sessions' G_ES differs from the pooled build")
    return int(len(whole))


# ================================================================================ build, cache, summary
def build(refresh_inputs: bool = False, log=P) -> tuple[pd.DataFrame, dict[str, Any]]:
    t0 = time.time()
    I = load_inputs(refresh=refresh_inputs, log=log)
    t1 = time.time()
    panel, aux = compute(I)
    t2 = time.time()
    log(f"  panel: {len(panel)} rows ({', '.join(f'{r} {int((panel.index.get_level_values(0) == r).sum())}' for r in ROOTS)}); "
        f"compute {t2 - t1:.1f} s")
    gates: dict[str, Any] = {"seal": "every input frame and the panel carry no date >= 2024-01-01"}
    gates["known_answers"] = known_answers(I, panel, log=log)
    gates["chunk_equals_whole_sessions"] = chunk_equals_whole(I)
    gates["lag_audit"] = lag_audit(panel, I, aux, log=log)
    gates["right_quantity"] = right_quantity_gates(I, panel, log=log)
    gates["etf_corporate_action_days"] = {k.split("_")[-1]: v for k, v in aux.items() if k.startswith("etf_ca_days")}
    gates["ho_band"] = I["ho_band"]
    gates["gsum_speed"] = I["gsum"]["speed"]
    wall = time.time() - t0
    TMP.mkdir(parents=True, exist_ok=True)
    panel.reset_index().to_csv(CACHE, index=False, compression={"method": "gzip", "mtime": 0}, encoding="utf-8", float_format="%.17g")
    meta = {"key": cache_key(), "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "rows": int(len(panel)),
            "wall_s": round(wall, 1), "sha256": hashlib.sha256(CACHE.read_bytes()).hexdigest()}
    CACHE_META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    write_summary(panel, gates, wall, I)
    return panel, gates


def load_conditioners(refresh: bool = False) -> pd.DataFrame:
    """The panel, indexed by (root, session "YYYY-MM-DD"). Refuses a missing or stale cache (every input's and module's size and mtime is
    in the key) unless refresh=True, which rebuilds it (about three minutes, processes)."""
    if refresh:
        build()
    if not (CACHE.exists() and CACHE_META.exists()):
        raise D722Error(f"[CACHE] {CACHE.relative_to(REPO)} missing: run `uv run python scripts/diag_d722_conditioners.py --build`")
    meta = json.loads(CACHE_META.read_text(encoding="utf-8"))
    if meta.get("key") != cache_key():
        raise D722Error("[CACHE] stale: an input or module changed since the build; rebuild with --build or refresh=True")
    if hashlib.sha256(CACHE.read_bytes()).hexdigest() != meta.get("sha256"):
        raise D722Error("[CACHE] the cached panel's bytes do not match its meta")
    p = pd.read_csv(CACHE, dtype={"root": str, "session": str}, encoding="utf-8").set_index(["root", "session"])
    seal(p.index.get_level_values("session"), "cached panel")
    return p[COLUMNS]


def coverage(panel: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for root in ROOTS:
        p = panel.loc[root]
        yr = p.index.str[:4]
        out[root] = {"sessions_by_year": p.groupby(yr).size().astype(int).to_dict(),
                     "non_null_by_year": {c: p[c].notna().groupby(yr).sum().astype(int).to_dict() for c in COLUMNS}}
    return out


def per_year(panel: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for root in ROOTS:
        p = panel.loc[root]
        yr = p.index.str[:4]
        out[root] = {c: {"mean": {k: (None if not np.isfinite(v) else round(float(v), 6)) for k, v in p[c].groupby(yr).mean().items()},
                         "median": {k: (None if not np.isfinite(v) else round(float(v), 6)) for k, v in p[c].groupby(yr).median().items()}}
                     for c in COLUMNS}
    return out


DEFINITIONS = {c: "" for c in COLUMNS}
DEFINITIONS.update({
    "sig20": "ES/NQ: D663 sig20 exactly (front's last 09:30-15:59 close, opening fixture; 20 sessions to the prior, min 15, ddof 1; roll-day "
             "front-to-front return included as D663) / 1e4. HO: same-contract daily SETTLEMENT log returns (breadth front, fut_settle_strip), 20 "
             "settling sessions to prior(d), min 15.",
    "X1": "ln sig20", "X2": "D691 ivrv: ln(IV / (sig20_bp/1e4*sqrt(252))); IV from temp/d691_iv (prior settlement); ES/NQ",
    "X3": "1 if G_SUM = G_SPX(prior GEX row) + G_ES(prior-settlement ES book) < 0; D688/D699 panel; D688 days (>=380 RTH bars); ES/NQ",
    "X4": "ln sd of ZT front-settlement daily changes, 20 settling sessions to prior(d), roll changes excluded, min 15",
    "X5": "ln sig20 of CL, settlement convention (as HO)",
    "X6": "D487 S1 VR on 30-min RTH buckets (ES/NQ 09:30-16:00 q=13, 390-bar sessions; HO 09:00-14:30 q=11, 12 anchor bars), 60 full sessions before d",
    "X6_15m": "the same on 15-min buckets (ES/NQ D487's ENDS q=26; HO q=22)",
    "r60": "sum of 60 same-contract daily settlement log returns ending prior(d) (all finite); X7 = r60 * side",
    "X8": "session date carries FOMC, FOMC_UNSCHEDULED, CPI or EMPSIT (events.csv datetime_et date); HO also EIA_WPSR",
    "fomc": "FOMC or FOMC_UNSCHEDULED", "fomc_unscheduled": "FOMC_UNSCHEDULED", "cpi": "CPI", "empsit": "EMPSIT", "eia_wpsr": "EIA_WPSR",
    "X9": "35 root sessions from the first session on/after each verified first-deposit date (EIP_FIRST_DEPOSIT_VERIFIED)",
    "X9_record": "the same on the record's approximate dates",
    "X10": "ln(MES/ES) or ln(MNQ/NQ) front day volume (calendar ET day, same D462 rule) on the prior ES/NQ session day; ES/NQ",
    "X11": "SMH minus QQQ 60-ETF-session log return (|r|>0.30 excluded, >=55 of 60) to the prior ETF close; ES/NQ",
    "X12": "HO: (front - next)/front settlement on the prior HO settling session", "war": "2022-02-24 .. 2022-04-29"})


def write_summary(panel: pd.DataFrame, gates: dict[str, Any], wall: float, I: dict[str, Any]) -> None:
    doc = {"spec": "D722 s.3 (f25e4726), Phase 0b", "builder": "scripts/diag_d722_conditioners.py",
           "window": [FIRST, LAST], "seal": f"no input row dated >= {CUT}; the vault never read", "roots": list(ROOTS),
           "definitions": DEFINITIONS,
           "sources": {"sig20_ES_NQ": "data/fixtures/fut_opening_globex_1m.csv.gz", "X6_ES_NQ": "data/fixtures/fut_{ES,NQ}_rth_1m.csv.gz",
                       "HO_bars": "data/fixtures/fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz", "settlements": "data/fixtures/fut_settle_strip.csv.gz",
                       "fronts_ZT_HO_CL": "data/fixtures/fut_curve_front_next.csv.gz", "IV": "temp/d691_iv_{es,nq}.csv (D691's cache)",
                       "G_SUM": "stage0_d688_gamma_close (SqueezeMetrics GEX + fut_es_options_eod); per-date values in temp/d722 only",
                       "events": "data/calendar/events.csv", "volumes": "data/fixtures/fut_micro_day_volume.csv.gz, fut_index_sessions.csv.gz",
                       "ETF": "data/fixtures/etf_wide_daily_raw.csv.gz", "HO_band": "data/fixtures/cme_session_calendar.csv.gz"},
           "X9_verification": {"record_dates": EIP_FIRST_DEPOSIT_RECORD, "verified_dates": EIP_FIRST_DEPOSIT_VERIFIED,
                               "sources": EIP_SOURCES, "note": EIP_NOTE},
           "coverage": coverage(panel), "per_year": per_year(panel), "gates": gates, "wall_s": round(wall, 1),
           "credit": "SqueezeMetrics (squeezemetrics.com) for GEX; X3 appears here only as per-year shares of short-gamma sessions"}
    # the licence guard: no list or mapping in this file may be a per-date series
    def walk(o, path=""):
        if isinstance(o, dict):
            if sum(1 for k in o if isinstance(k, str) and len(k) == 10 and k[4] == "-" and k[7] == "-") > 3 and "X9" not in path:
                raise D722Error(f"[LICENCE] {path} looks like a per-date series")
            for k, v in o.items():
                walk(v, f"{path}/{k}")
        elif isinstance(o, list) and len(o) > 60:
            raise D722Error(f"[LICENCE] {path} has {len(o)} entries")
    walk(doc)
    SUMMARY.write_text(json.dumps(doc, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")


def print_coverage(panel: pd.DataFrame) -> None:
    for root in ROOTS:
        p = panel.loc[root]
        yr = p.index.str[:4]
        n = p.groupby(yr).size()
        P(f"\n  {root}: sessions by year " + " ".join(f"{y}:{v}" for y, v in n.items()))
        P(f"    {'column':<17}" + "".join(f"{y:>7}" for y in n.index) + "   median by year")
        for c in COLUMNS:
            nn = p[c].notna().groupby(yr).sum()
            md = p[c].groupby(yr).median()
            P(f"    {c:<17}" + "".join(f"{int(nn.get(y, 0)):>7}" for y in n.index) + "   "
              + " ".join("   nan" if not np.isfinite(md.get(y, np.nan)) else f"{md[y]:.4g}" for y in n.index))


# ================================================================================ self-test
def expect_raise(fn: Callable[[], Any], what: str) -> None:
    try:
        fn()
    except D722Error as e:
        P(f"    RAISES on {what}: {str(e)[:110]}")
        return
    raise SystemExit(f"SELFTEST FAILED: no raise on {what}")


def selftest() -> int:
    t0 = time.time()
    P("D722 conditioners --selftest: a clean pass on the real (sealed) inputs, then every gate must RAISE on a deliberate break")
    I = load_inputs()
    panel, aux = compute(I)
    raw = Raw(I)
    P("== clean pass")
    known_answers(I, panel)
    chunk_equals_whole(I)
    lag_audit(panel, I, aux, raw=raw)
    right_quantity_gates(I, panel)
    P("== 1. the seal: a planted 2024 row in every input frame, in the panel, and a loader with its filter disabled")
    for name, df, col in input_frames(I):
        if col == "__index__":
            bad = pd.concat([df, df.iloc[[0]].set_axis(["2024-01-02"])])
            expect_raise(lambda b=bad, n=name: seal(b.index, f"input {n}"), f"a 2024 row planted in {name}")
        else:
            row = df.iloc[[0]].copy()
            row[col] = "2024-01-02" if col != "datetime_et" else "2024-01-02T08:30:00-05:00"
            bad = pd.concat([df, row], ignore_index=True)
            expect_raise(lambda b=bad, c=col, n=name: seal(b[c].astype(str).str[:10], f"input {n}"), f"a 2024 row planted in {name}")
    bp = pd.concat([panel, panel.iloc[[0]].rename(index={panel.index[0][1]: "2024-01-02"}, level=1)])
    expect_raise(lambda: seal(bp.index.get_level_values("session"), "panel"), "a 2024 session planted in the panel")
    tmpcsv = TMP / "selftest_seal.csv"
    pd.DataFrame({"day": ["2023-12-29", "2024-01-02"], "v": [1.0, 2.0]}).to_csv(tmpcsv, index=False, encoding="utf-8")
    ok = read_sealed(tmpcsv, ["day", "v"], {"day": str}, "day")
    assert list(ok["day"]) == ["2023-12-29"], ok
    expect_raise(lambda: read_sealed(tmpcsv, ["day", "v"], {"day": str}, "day", cut="2099-01-01"), "a loader whose chunk filter is off")
    tmpcsv.unlink()
    P("== 2. the lag audit: each lagged variable made SAME-DAY, each same-day flag keyed on the prior session")
    for v in LAGGED + SAMEDAY:
        bad, bad_aux = compute(I, leak=v)
        expect_raise(lambda b=bad, a=bad_aux: lag_audit(b, I, a, raw=raw, log=lambda *x: None), f"{v} leaked")
    P("== 3. right quantity: each gate handed the quantity we did not mean")
    for w, col in (("X4", "X4"), ("X5", "X5"), ("sig20_HO", "sig20"), ("r60", "r60"), ("X6", "X6")):
        alt, _ = compute(I, wrong=w)
        expect_raise(lambda a=alt, c=col: right_quantity(a[c], a[c], c), f"{col} compared with itself (the wrong one passed as right)")
        expect_raise(lambda a=alt, c=col, w_=w: lag_audit(a, I, aux, raw=raw, log=lambda *x: None), f"the lag audit on the wrong {w}")
    P("== 4. known answers perturbed")
    refj = json.loads((DATA / "d487_continuation_stage0.json").read_text(encoding="utf-8"))
    refj["ES"]["groups"]["2022"]["S1_vr"] *= 1 + 1e-9
    expect_raise(lambda: known_answers(I, panel, d487_ref=refj, log=lambda *x: None), "D487's 2022 S1 perturbed by 1e-9")
    p2 = panel.copy()
    p2.loc[("ES", "2019-06-03"), "sig20"] *= 1 + 1e-12
    expect_raise(lambda: known_answers(I, p2, log=lambda *x: None), "one ES sig20 perturbed by 1e-12 (vs D663's root_frame)")
    g0 = I["gsum"]
    kb = g0["kept"].copy()
    s0 = sorted(kb["session"].unique())[10]
    kb.loc[kb["session"] == s0, "oi"] *= 2.0
    expect_raise(lambda: chunk_equals_whole(dict(I, gsum=dict(g0, kept=kb))), f"every option row's OI doubled on {s0} (the pooled build no longer matches)")
    gb = g0["g"].copy()
    gb.loc[s0, "G_ES"] = np.nextafter(gb.loc[s0, "G_ES"], np.inf)
    expect_raise(lambda: chunk_equals_whole(dict(I, gsum=dict(g0, g=gb))), f"the pooled G_ES of {s0} moved by one ulp")
    P("== 5. X11's corporate-action filter: a planted +0.5 log-return day is excluded, and with the filter off the audit raises")
    e = I["etf"].copy()
    e.loc[e.index[(e["symbol"] == "SMH") & (e["date"] > "2021-06-01")], "close"] *= math.exp(0.5)
    Ie = dict(I, etf=e)
    pe, ae = compute(Ie)
    if "2021-06-02" not in ae["etf_ca_days_SMH"]:
        raise SystemExit(f"SELFTEST FAILED: the planted corporate action was not flagged ({ae['etf_ca_days_SMH']})")
    re_ = Raw(Ie)
    re_.memo.update({k: v for k, v in raw.memo.items() if k[0] != "X11"})   # only X11 reads the ETF file
    lag_audit(pe, Ie, ae, raw=re_, log=lambda *x: None)
    P("    clean: the planted day is flagged and excluded on both paths")
    old = globals()["CA_LIMIT"]
    globals()["CA_LIMIT"] = 9.9   # the vectorised X11 keeps the jump; the (memoised, filter-on) second path does not
    try:
        pe2, _ = compute(Ie)
    finally:
        globals()["CA_LIMIT"] = old
    expect_raise(lambda: lag_audit(pe2, Ie, ae, raw=re_, log=lambda *x: None), "X11 built with the corporate-action filter off")
    P("== 6. the cache refuses a stale key")
    if CACHE_META.exists():
        meta = json.loads(CACHE_META.read_text(encoding="utf-8"))
        bad = dict(meta, key=dict(meta["key"], cut="1999-01-01"))
        CACHE_META.write_text(json.dumps(bad, indent=1) + "\n", encoding="utf-8", newline="\n")
        try:
            expect_raise(load_conditioners, "a stale cache key")
        finally:
            CACHE_META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
        load_conditioners()
    else:
        P("    (no cache yet: run --build, then --selftest proves the refusal)")
    P(f"SELFTEST PASSED in {time.time() - t0:.0f} s")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--build", action="store_true")
    ap.add_argument("--refresh-inputs", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    t0 = time.time()
    panel, _ = build(refresh_inputs=a.refresh_inputs)
    print_coverage(panel)
    P(f"\nwrote {CACHE.relative_to(REPO)}, {CACHE_META.relative_to(REPO)}, {SUMMARY.relative_to(REPO)}; wall {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
