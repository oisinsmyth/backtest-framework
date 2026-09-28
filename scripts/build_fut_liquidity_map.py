"""D651 -- the time-of-day liquidity map on bbo-1m, and the session-handoff study's kill 1.

    python scripts/build_fut_liquidity_map.py --selftest
    python scripts/build_fut_liquidity_map.py --profile        # one file, timed, before the full build
    python scripts/build_fut_liquidity_map.py --build [--workers 6]
    python scripts/build_fut_liquidity_map.py --report         # fixture -> data/d651_liquidity_map.json + page

PRE-REGISTRATION: docs/decisions/D651-PRE-REG-the-time-of-day-liquidity-map-and-the-handoff-kill-1.md

NO RETURN IS COMPUTED. The fixture carries the quoted spread in ticks and the touch sizes and order counts; no price
level, no mid, nothing signed. The only arithmetic on a price is `ask - bid`, divided by the tick and asserted a whole
number. `_assert_columns` refuses any other column, and --selftest proves it refuses a price column.

EVERY BYTE READ IS INSIDE THE PROGRAMME VAULT (2025-03-01 -> 2026-09-18), the quotes-only class of read D507, D510,
D604 and D623 made of the same year. D626's sealed sample (CL NG HO RB, 2026-09-21 -> 25) is after the bbo-1m span;
`_assert_no_sealed_day` RAISES if a session at or after 2026-09-11 reaches the output.

Run under the system interpreter (databento). The raw cache lives in the MAIN checkout; from a worktree it is read
there, and the breadth fixture (the front-contract rule) is read from this checkout if present, else from main's.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]


def _main_checkout(repo: Path) -> Path:
    """This builder may run in a worktree; the gitignored raw pulls and fixtures live in the MAIN checkout."""
    p = repo
    while p.parent != p:
        if p.name == "worktrees" and p.parent.name == ".claude":
            return p.parent.parent
        p = p.parent
    return repo


MAIN = _main_checkout(REPO)


def _resolve(rel: str) -> Path:
    """This checkout's copy if it exists, else the main checkout's."""
    p = REPO / rel
    return p if p.exists() else MAIN / rel


RAW = MAIN / "data" / "raw" / "databento"
BREADTH = _resolve("data/fixtures/fut_breadth_hourly.csv.gz")
SPECS_DEF = REPO / "data" / "fut_specs_from_definition.json"
COSTS = REPO / "data" / "futures_costs.json"
FIX = REPO / "data" / "fixtures" / "fut_liquidity_15m.csv.gz"
META = REPO / "data" / "fixtures" / "fut_liquidity_15m.meta.json"
OUT = REPO / "data" / "d651_liquidity_map.json"
PAGE = REPO / "docs" / "results" / "LIQUIDITY_MAP.md"

ROOTS = ("ES", "NQ", "RTY", "YM", "MES", "MNQ", "M2K", "MYM",
         "CL", "NG", "GC", "SI", "HG", "ZN", "ZB", "ZF",
         "SR3", "ZT", "UB", "TN", "RB", "HO", "BZ", "PL", "PA",
         "6E", "6J", "6B", "6A", "6C", "6S",
         "ZC", "ZS", "ZW", "ZL", "ZM", "LE", "HE", "NKD", "BTC", "MBT")
PARENT_OF = {"MES": "ES", "MNQ": "NQ", "M2K": "RTY", "MYM": "YM", "MBT": "BTC"}
SYM = re.compile(r"^([A-Z0-9]{1,4})([FGHJKMNQUVXZ])([0-9]{1,2})$")
PX = 1e-9
UNDEF_PRICE = 2**63 - 1
DAY0, DAY1 = "2025-09-11", "2026-09-10"
FIRST_SEALED = "2026-09-11"          # D626's sample starts 2026-09-21; nothing after the bbo span may enter
COLS = ["root", "day", "bucket", "spread_ticks", "n", "q_lots", "q_orders"]
KEY = ["root", "day", "bucket", "spread_ticks"]

# ---------------------------------------------------------------- the windows, D651 s.3 (minutes of the ET day)
def _span(a: str, b: str) -> tuple[int, ...]:
    h0, m0 = map(int, a.split(":"))
    h1, m1 = map(int, b.split(":"))
    return tuple(range(h0 * 60 + m0, h1 * 60 + m1, 15))


WINDOWS = {
    "W1": {"window": _span("02:00", "03:30"), "before": _span("01:00", "02:00"), "after": _span("03:30", "04:30")},
    "W2": {"window": _span("07:30", "08:30"), "before": _span("06:30", "07:30"), "after": _span("08:30", "09:30")},
    "W3": {"window": _span("16:00", "17:00") + _span("18:00", "19:00"),
           "before": _span("15:00", "16:00"), "after": _span("19:00", "20:00")},
}
CORE = _span("10:00", "15:00")
COVERAGE_MIN = 0.90
MIN_SESSIONS = 100
BLOCK, DRAWS, SEED = 5, 2000, 651
H0_PASS, H0_FLOOR = 2.0, 1.0


def P(*a, **k):
    print(*a, **k, flush=True)


class GateError(AssertionError):
    pass


# ---------------------------------------------------------------- guards
def _assert_columns(df: pd.DataFrame) -> None:
    """The no-return guard: exactly the seven declared columns, nothing that could carry a price."""
    if list(df.columns) != COLS:
        raise GateError(f"[NO-RETURN] fixture columns {list(df.columns)} != declared {COLS}")


def _assert_no_sealed_day(days) -> None:
    bad = sorted({d for d in days if str(d) >= FIRST_SEALED})
    if bad:
        raise GateError(f"[SEAL] sessions at or after {FIRST_SEALED} reached the output: {bad[:5]}")


def _assert_whole_ticks(spread_t: np.ndarray, where: str) -> np.ndarray:
    if len(spread_t):
        frac = np.abs(spread_t - np.round(spread_t))
        if frac.max() > 1e-6:
            raise GateError(f"[TICK] spread not a whole number of ticks in {where}: "
                            f"{spread_t[int(np.argmax(frac))]:.9f}")
    return np.round(spread_t).astype(np.int64)


# ---------------------------------------------------------------- the pieces the build is made of
def valid_quotes(bid_raw: np.ndarray, ask_raw: np.ndarray) -> np.ndarray:
    """Two-sided, defined and uncrossed. INT64_MAX passes a `> 0` test, so it is removed by name (D507)."""
    undef = (bid_raw == UNDEF_PRICE) | (ask_raw == UNDEF_PRICE)
    return (bid_raw > 0) & (ask_raw > 0) & ~undef & (ask_raw > bid_raw)


def clock(ts_ns: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """ts_recv (UTC ns) -> (CME session day 'YYYY-MM-DD', minute of the ET day of the 15-minute bucket start)."""
    ts = pd.to_datetime(ts_ns, utc=True).tz_convert("US/Eastern")
    hh = ts.hour.to_numpy()
    mod = hh * 60 + ts.minute.to_numpy()
    cal = ts.normalize().tz_localize(None)
    sess = np.where(hh >= 18, (cal + pd.Timedelta(days=1)).strftime("%Y-%m-%d"), cal.strftime("%Y-%m-%d"))
    return sess, (mod // 15) * 15


def bucket_label(minute: int) -> str:
    return f"{minute // 60:02d}:{minute % 60:02d}"


def aggregate(d: pd.DataFrame) -> pd.DataFrame:
    """Integer sums only, so any partition of the rows aggregates to the same table (checked in --selftest)."""
    return (d.groupby(KEY, as_index=False, sort=True)
            .agg(n=("n", "sum"), q_lots=("q_lots", "sum"), q_orders=("q_orders", "sum")))


def specs() -> dict:
    sd = json.loads(SPECS_DEF.read_text(encoding="utf-8"))["specs"]
    out = {}
    for r in ROOTS:
        d = sd.get(r)
        if not d or not d.get("present"):
            raise GateError(f"[SPEC] {r} absent from {SPECS_DEF.name}")
        out[r] = float(d["tick_price_units"])
    return out


def front_table() -> pd.DataFrame:
    """(root, day, contract): the breadth fixture's volume rule; a micro inherits its parent's expiry (D507)."""
    t = pd.read_csv(BREADTH, usecols=["root", "day", "contract"], encoding="utf-8")
    t = t[t["day"].between(DAY0, DAY1) & t["contract"].notna()].drop_duplicates(["root", "day"])
    rows = [t]
    for micro, parent in PARENT_OF.items():
        p = t[t["root"] == parent].copy()
        p["contract"] = [micro + c[len(parent):] for c in p["contract"]]
        p["root"] = micro
        rows.append(p)
    return pd.concat(rows, ignore_index=True)[["root", "day", "contract"]]


def process_file(path: str, tickp: dict, fronts: pd.DataFrame, chunk: int = 4_000_000) -> tuple[pd.DataFrame, dict]:
    import databento as db

    store = db.DBNStore.from_file(path)
    id_root, id_sym = {}, {}
    for sym, ivs in store.metadata.mappings.items():
        m = SYM.match(str(sym))
        if not m or m.group(1) not in tickp:
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if sid:
                id_root[int(sid)] = m.group(1)
                id_sym[int(sid)] = str(sym)
    ids = np.array(sorted(id_root), dtype=np.int64)
    roots_of = np.array([id_root[i] for i in ids])
    syms_of = np.array([id_sym[i] for i in ids])
    tick_of = np.array([tickp[r] for r in roots_of])
    stats = {"file": Path(path).name, "rows": 0, "kept_ids": 0, "invalid": 0, "front_minutes": 0}
    parts = []
    if not len(ids):
        return pd.DataFrame(columns=COLS), stats
    for a in store.to_ndarray(count=chunk):
        stats["rows"] += len(a)
        iid = a["instrument_id"].astype(np.int64)
        pos = np.minimum(np.searchsorted(ids, iid), len(ids) - 1)
        hit = ids[pos] == iid
        a, pos = a[hit], pos[hit]
        stats["kept_ids"] += len(a)
        ok = valid_quotes(a["bid_px_00"], a["ask_px_00"])
        stats["invalid"] += int((~ok).sum())
        a, pos = a[ok], pos[ok]
        if not len(a):
            continue
        sess, minute = clock(a["ts_recv"].astype(np.int64))
        spread = (a["ask_px_00"].astype(np.float64) - a["bid_px_00"].astype(np.float64)) * PX / tick_of[pos]
        d = pd.DataFrame({"root": roots_of[pos], "contract": syms_of[pos], "day": sess, "minute": minute,
                          "spread_ticks": spread,
                          "n": np.ones(len(a), np.int64),
                          "q_lots": a["bid_sz_00"].astype(np.int64) + a["ask_sz_00"].astype(np.int64),
                          "q_orders": a["bid_ct_00"].astype(np.int64) + a["ask_ct_00"].astype(np.int64)})
        d = d[d["day"].between(DAY0, DAY1)]
        d = d.merge(fronts, on=["root", "day", "contract"], how="inner")
        # THE TICK MUST DIVIDE THE FRONT CONTRACT'S SPREAD (D507's gate, on the front only: a deferred SR3 or grain
        # month can quote on a coarser tick than the root's front-month increment)
        if len(d):
            frac = np.abs(d["spread_ticks"].to_numpy() - np.round(d["spread_ticks"].to_numpy()))
            if frac.max() > 1e-6:
                b = d.iloc[int(np.argmax(frac))]
                raise GateError(f"[TICK] {b['root']} {b['contract']} {b['day']}: spread {b['spread_ticks']:.9f} ticks "
                                f"in {Path(path).name}")
            d["spread_ticks"] = _assert_whole_ticks(d["spread_ticks"].to_numpy(), Path(path).name)
        stats["front_minutes"] += len(d)
        d["bucket"] = d["minute"]
        parts.append(aggregate(d[["root", "day", "bucket", "spread_ticks", "n", "q_lots", "q_orders"]]))
    out = aggregate(pd.concat(parts, ignore_index=True)) if parts else pd.DataFrame(columns=COLS)
    return out, stats


def _worker(args):
    paths, tickp, fronts = args
    res = []
    for p in paths:
        t0 = time.time()
        g, st = process_file(p, tickp, fronts)
        st["seconds"] = round(time.time() - t0, 1)
        res.append((g, st))
    return res


def bbo_files() -> list[Path]:
    files = sorted(RAW.glob("*/*.bbo-1m.dbn.zst"))
    if not files:
        raise GateError(f"[FILES] no bbo-1m files under {RAW}")
    return files


def finish(g: pd.DataFrame) -> pd.DataFrame:
    g = aggregate(g)
    g = g.sort_values(KEY, kind="mergesort").reset_index(drop=True)
    g["bucket"] = [bucket_label(int(m)) for m in g["bucket"]]
    g = g[COLS]
    _assert_columns(g)
    _assert_no_sealed_day(g["day"].unique())
    return g


def build(workers: int) -> int:
    tickp, fronts = specs(), front_table()
    files = bbo_files()
    P(f"D651 build -- {len(files)} bbo-1m files, {sum(f.stat().st_size for f in files) / 2**30:.2f} GiB, "
      f"{len(ROOTS)} roots, {workers} processes over files[i::{workers}]")
    t0 = time.time()
    # stride, don't slice: the files differ ~4x in size
    jobs = [([str(f) for f in files[i::workers]], tickp, fronts) for i in range(workers)]
    parts, stats = [], []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for res in ex.map(_worker, jobs):
            for g, st in res:
                parts.append(g)
                stats.append(st)
                P(f"  {st['file'][-34:]:<34} {st['rows']:>11,} rows  {st['front_minutes']:>10,} front minutes  "
                  f"{st['invalid']:>8,} invalid  ({st['seconds']}s)")
    wall = time.time() - t0
    busy = sum(s["seconds"] for s in stats)
    P(f"[SPEED] sum(item time)/wall = {busy / wall:.2f}x on {workers} processes "
      f"({100 * busy / wall / workers:.0f}% of the pool){'  <-- BELOW 70%' if busy / wall / workers < 0.7 else ''}")
    g = finish(pd.concat(parts, ignore_index=True))
    FIX.parent.mkdir(parents=True, exist_ok=True)
    g.to_csv(FIX, index=False, compression="gzip", encoding="utf-8")
    meta = {"decision": "D651", "built_by": "python scripts/build_fut_liquidity_map.py --build",
            "computes_no_return": True, "columns": COLS, "session_days": [DAY0, DAY1],
            "inside_programme_vault": ["2025-03-01", "2026-09-18"],
            "rows": int(len(g)), "roots": int(g["root"].nunique()), "sessions": int(g["day"].nunique()),
            "quoted_minutes": int(g["n"].sum()),
            "files": [{k: v for k, v in s.items() if k != "seconds"} for s in sorted(stats, key=lambda s: s["file"])],
            "clock": "ts_recv -> US/Eastern; session day rolls at 18:00 ET; bucket = 15-minute start, HH:MM",
            "front_rule": "fut_breadth_hourly volume rule; micros inherit the parent's expiry (D507)"}
    META.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8", newline="\n")
    P(f"wrote {FIX.name}: {len(g):,} rows, {meta['roots']} roots, {meta['sessions']} sessions, "
      f"{meta['quoted_minutes']:,} quoted minutes in {(time.time() - t0) / 60:.1f} min")
    return 0


def profile() -> int:
    tickp, fronts = specs(), front_table()
    f = max(bbo_files(), key=lambda p: p.stat().st_size)
    t0 = time.time()
    g, st = process_file(str(f), tickp, fronts)
    P(f"profile: {f.name} {f.stat().st_size / 2**30:.2f} GiB -> {st} in {time.time() - t0:.1f}s; {len(g):,} cells")
    return 0


# ---------------------------------------------------------------- the report, D651 s.4-s.6
def spans_by_date(fx: pd.DataFrame) -> pd.DataFrame:
    """Per (root, ET calendar date, bucket-minute): n, q_lots, spread-minutes. The calendar date is the session day,
    less one for buckets at or after 18:00 -- so W3's 18:00-19:00 reopen pairs with the same evening's 16:00 close."""
    m = fx["bucket"].str.slice(0, 2).astype(int) * 60 + fx["bucket"].str.slice(3, 5).astype(int)
    day = pd.to_datetime(fx["day"])
    cal = np.where(m >= 18 * 60, day - pd.Timedelta(days=1), day)
    t = pd.DataFrame({"root": fx["root"].to_numpy(), "cal": pd.to_datetime(cal), "minute": m.to_numpy(),
                      "n": fx["n"].to_numpy(), "q_lots": fx["q_lots"].to_numpy(),
                      "s_min": (fx["spread_ticks"] * fx["n"]).to_numpy()})
    return t.groupby(["root", "cal", "minute"], as_index=False)[["n", "q_lots", "s_min"]].sum()


def span_stats(t: pd.DataFrame, minutes: tuple[int, ...]) -> pd.DataFrame:
    """Per (root, cal): minutes, coverage, mean depth D, mean spread S over one span."""
    s = t[t["minute"].isin(minutes)].groupby(["root", "cal"])[["n", "q_lots", "s_min"]].sum()
    s["cov"] = s["n"] / (15 * len(minutes))
    s["D"] = s["q_lots"] / s["n"]
    s["S"] = s["s_min"] / s["n"]
    return s


def block_bootstrap_median(x: np.ndarray, block: int = BLOCK, draws: int = DRAWS, seed: int = SEED):
    n = len(x)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(draws, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(draws, -1)[:, :n]
    meds = np.median(x[idx], axis=1)
    return float(np.median(x)), float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))


def trough_verdict(lo: float, hi: float) -> str:
    return "TROUGH" if hi < 0 else ("NOT A TROUGH" if lo > 0 else "UNRESOLVED")


def h0_verdict(r: float) -> str:
    return "PASS" if r >= H0_PASS else ("MARGINAL" if r >= H0_FLOOR else "FAIL")


def cost_of(root: str, costs: dict) -> tuple[float, float]:
    parent, size = costs["by_symbol"][root]
    e = costs["roots"][parent][size]
    return float(e["tick_usd"]), float(e["commission_rt_usd"]["value"])


def score(fx: pd.DataFrame) -> dict:
    costs = json.loads(COSTS.read_text(encoding="utf-8"))
    t = spans_by_date(fx)
    core = span_stats(t, CORE)
    core_ok = core[core["cov"] >= COVERAGE_MIN]
    out = {}
    for root in ROOTS:
        tick_usd, comm_rt = cost_of(root, costs)
        side = comm_rt / 2
        tr = t[t["root"] == root]
        c = core_ok.loc[root] if root in core_ok.index.get_level_values(0) else None
        rec = {"tick_usd": tick_usd, "commission_rt_usd": comm_rt, "windows": {}}
        if c is not None and len(c):
            s_core = float(c["s_min"].sum() / c["n"].sum())
            rec["core"] = {"sessions": int(len(c)), "S_mean": s_core, "D_median": float(c["D"].median()),
                           "R": s_core * tick_usd / 2 / side, "H0": h0_verdict(s_core * tick_usd / 2 / side)}
        else:
            rec["core"] = None
        for w, sp in WINDOWS.items():
            a = {k: span_stats(tr, sp[k]) for k in ("window", "before", "after")}
            j = a["window"].join(a["before"], rsuffix="_b", how="inner").join(a["after"], rsuffix="_a", how="inner")
            j = j[(j["cov"] >= COVERAGE_MIN) & (j["cov_b"] >= COVERAGE_MIN) & (j["cov_a"] >= COVERAGE_MIN)]
            j = j.sort_index()
            if len(j) < MIN_SESSIONS:
                rec["windows"][w] = {"sessions": int(len(j)), "verdict": "NOT IN SESSION"}
                continue
            x = (np.log(j["D"]) - np.log(np.minimum(j["D_b"], j["D_a"]))).to_numpy()
            y = (j["S"] - np.maximum(j["S_b"], j["S_a"])).to_numpy()
            med, lo, hi = block_bootstrap_median(x)
            s_bar = float(j["s_min"].sum() / j["n"].sum())
            r = s_bar * tick_usd / 2 / side
            rec["windows"][w] = {
                "sessions": int(len(j)), "x_median": med, "x_ci95": [lo, hi], "verdict": trough_verdict(lo, hi),
                "share_x_below_0": float((x < 0).mean()),
                "y_median_ticks": float(np.median(y)), "y_mean_ticks": float(y.mean()),
                "D_median": float(j["D"].median()), "S_mean": s_bar,
                "D_vs_core": (float(j["D"].median()) / rec["core"]["D_median"]) if rec["core"] else None,
                "S_vs_core": (s_bar / rec["core"]["S_mean"]) if rec["core"] else None,
                "coverage_mean": float(j["cov"].mean()),
                "half_spread_usd": s_bar * tick_usd / 2, "commission_side_usd": side, "R": r, "H0": h0_verdict(r)}
        prof = t[t["root"] == root].copy()
        prof["D"] = prof["q_lots"] / prof["n"]
        prof["S"] = prof["s_min"] / prof["n"]
        # dates_quoted, not a coverage share: a share over all calendar dates is diluted by the Sunday-evening-only
        # dates and read 0.82 in every daytime bucket; the per-window gating uses per-date coverage and is unaffected
        pg = prof.groupby("minute")
        rec["profile"] = {bucket_label(int(m)): {"D_median": round(float(g["D"].median()), 3),
                                                 "S_mean": round(float(g["s_min"].sum() / g["n"].sum()), 4),
                                                 "dates_quoted": int(g["cal"].nunique())}
                          for m, g in pg}
        out[root] = rec
    return out


def decide(per_root: dict) -> dict:
    cells = [(r, w, c) for r, rec in per_root.items() for w, c in rec["windows"].items() if "R" in c]
    fires = not any(c["R"] >= H0_FLOOR for _, _, c in cells)
    cand = sorted({r for r, w, c in cells if c["verdict"] == "TROUGH" and c["H0"] == "PASS"})
    branch = "a" if fires else ("b" if cand else "c")
    return {"kill_1_fires": fires, "candidate_set": cand, "branch": branch,
            "candidate_cells": [f"{r} {w}" for r, w, c in cells if c["verdict"] == "TROUGH" and c["H0"] == "PASS"],
            "reading": {"a": "SESSION_HANDOFF_LIQUIDITY closes at its own kill 1; nothing is quoted.",
                        "b": "Quote a pre-vault tbbo + bbo-1m pull (2017-05-22 -> 2025-02-28) for the candidate set; "
                             "put it to the principal before 2026-10-09; submit nothing without the word.",
                        "c": "No affordable trough: recommend no pull; the principal decides."}[branch]}


def predictions(pr: dict) -> list[dict]:
    def v(r, w):
        return pr[r]["windows"][w].get("verdict")

    def h(r, w):
        return pr[r]["windows"][w].get("H0")
    out = []
    p1 = (not decide(pr)["kill_1_fires"]) and h("ES", "W3") == "PASS" and h("MES", "W3") == "FAIL"
    out.append({"id": 1, "text": "kill 1 does not fire; ES PASS, MES FAIL (read on W3)", "held": bool(p1)})
    out.append({"id": 2, "text": "W3 TROUGH on ES NQ ZN CL",
                "held": all(v(r, "W3") == "TROUGH" for r in ("ES", "NQ", "ZN", "CL")),
                "detail": {r: v(r, "W3") for r in ("ES", "NQ", "ZN", "CL")}})
    out.append({"id": 3, "text": "W2 TROUGH on ZN ZB ES",
                "held": all(v(r, "W2") == "TROUGH" for r in ("ZN", "ZB", "ES")),
                "detail": {r: v(r, "W2") for r in ("ZN", "ZB", "ES")}})
    idx = ("ES", "NQ", "RTY", "YM")
    out.append({"id": 4, "text": "W1 TROUGH on 6E 6B; not a TROUGH on the index roots",
                "held": all(v(r, "W1") == "TROUGH" for r in ("6E", "6B"))
                and all(v(r, "W1") != "TROUGH" for r in idx),
                "detail": {r: v(r, "W1") for r in ("6E", "6B") + idx}})
    d5 = {r: {w: pr[r]["windows"][w].get("D_vs_core") for w in WINDOWS} for r in idx}
    out.append({"id": 5, "text": "median D_W / median D_core < 0.5 on the index roots, every window",
                "held": all(x is not None and x < 0.5 for r in idx for x in d5[r].values()), "detail": d5})
    return out


def render(res: dict) -> str:
    L = ["# LIQUIDITY MAP", "",
         f"**Rendered from [`data/d651_liquidity_map.json`](../../data/d651_liquidity_map.json) by "
         f"`scripts/build_fut_liquidity_map.py --report` ([D651](../decisions/D651-PRE-REG-the-time-of-day-liquidity-map"
         f"-and-the-handoff-kill-1.md)).** The JSON is the truth; editing this page by hand is a change the next "
         f"render throws away.", "",
         f"Front-contract `bbo-1m`, session days {DAY0} → {DAY1} (inside the programme vault; quotes only, no return). "
         f"Spread is QUOTED spread in ticks, a floor on what an aggressor pays. Depth is bid + ask size at the touch, "
         f"contracts. Windows in ET: W1 02:00–03:30, W2 07:30–08:30, W3 16:00–17:00 + 18:00–19:00; core 10:00–15:00.", "",
         "## The decision", "",
         f"- kill 1 fires: **{res['decision']['kill_1_fires']}**",
         f"- candidate set (TROUGH and H0 PASS): **{', '.join(res['decision']['candidate_set']) or 'none'}**",
         f"- branch **({res['decision']['branch']})**: {res['decision']['reading']}", "",
         "## Predictions", ""]
    for p in res["predictions"]:
        L.append(f"- P{p['id']} {p['text']}: **{'HELD' if p['held'] else 'FAILED'}**"
                 + (f" — {p['detail']}" if "detail" in p and p["id"] != 5 else ""))
    L += ["", "## Per root and window", "",
          "`x` = median ln(depth in window / thinner neighbour), 95% block-bootstrap interval; R = half quoted spread "
          "in $ / declared commission per side.", "",
          "| root | core S | core R | W1 x [95%] | W1 R | W2 x [95%] | W2 R | W3 x [95%] | W3 R |",
          "|---|---:|---:|---|---:|---|---:|---|---:|"]
    for r, rec in res["per_root"].items():
        core = rec["core"]
        row = [r, f"{core['S_mean']:.2f}" if core else "—", f"{core['R']:.2f}" if core else "—"]
        for w in WINDOWS:
            c = rec["windows"][w]
            if "R" not in c:
                row += [f"not in session ({c['sessions']})", "—"]
            else:
                tag = {"TROUGH": "**T**", "NOT A TROUGH": "N", "UNRESOLVED": "U"}[c["verdict"]]
                row += [f"{tag} {c['x_median']:+.2f} [{c['x_ci95'][0]:+.2f}, {c['x_ci95'][1]:+.2f}]",
                        f"{c['R']:.2f} {c['H0'][0]}"]
        L.append("| " + " | ".join(row) + " |")
    L += ["", "T = TROUGH, N = NOT A TROUGH, U = UNRESOLVED; H0: P PASS (R ≥ 2), M MARGINAL, F FAIL (R < 1).", ""]
    return "\n".join(L)


def report() -> int:
    fx = pd.read_csv(FIX, dtype={"day": str, "bucket": str}, encoding="utf-8")
    _assert_columns(fx)
    _assert_no_sealed_day(fx["day"].unique())
    per_root = score(fx)
    res = {"decision_record": "D651", "computes_no_return": True, "session_days": [DAY0, DAY1],
           "windows_et": {w: {k: [bucket_label(v[0]), bucket_label(v[-1] + 15)] for k, v in sp.items()}
                          for w, sp in WINDOWS.items()},
           "pairing": "ET calendar date (the session day less one for buckets >= 18:00), so W3's reopen pairs with "
                      "the same evening's close; a Friday close has no same-evening reopen and drops out",
           "coverage_min": COVERAGE_MIN, "min_sessions": MIN_SESSIONS,
           "bootstrap": {"block_sessions": BLOCK, "draws": DRAWS, "seed": SEED},
           "per_root": per_root}
    res["decision"] = decide(per_root)
    res["predictions"] = predictions(per_root)
    OUT.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
    PAGE.write_text(render(res) + "\n", encoding="utf-8", newline="\n")
    P(render(res))
    return 0


# ---------------------------------------------------------------- selftest: every guard must be able to fire
def selftest() -> int:
    n_ok = 0

    def must_raise(label, fn):
        nonlocal n_ok
        try:
            fn()
        except GateError:
            n_ok += 1
            P(f"  ok  raises: {label}")
            return
        raise AssertionError(f"did NOT raise: {label}")

    def check(label, cond):
        nonlocal n_ok
        if not cond:
            raise AssertionError(f"FAILED: {label}")
        n_ok += 1
        P(f"  ok  {label}")

    good = pd.DataFrame({c: [1] for c in COLS})
    good["day"] = "2026-01-05"
    _assert_columns(good)
    must_raise("a price column in the fixture", lambda: _assert_columns(good.assign(mid=100.0)))
    must_raise("a session after the bbo span (D626's seal side)", lambda: _assert_no_sealed_day(["2026-09-11"]))
    check("the last in-span session passes the seal guard", _assert_no_sealed_day(["2026-09-10"]) is None)
    must_raise("a wrong tick (half a tick of spread)",
               lambda: _assert_whole_ticks(np.array([1.0, 1.5]), "synthetic"))

    bid = np.array([100, UNDEF_PRICE, 100, 0, 101], dtype=np.int64)
    ask = np.array([101, 101, UNDEF_PRICE, 101, 101], dtype=np.int64)
    check("INT64_MAX and zero and crossed quotes are removed; the good one kept",
          valid_quotes(bid, ask).tolist() == [True, False, False, False, False])

    def ns(s):
        return np.array([pd.Timestamp(s).value], dtype=np.int64)
    s, m = clock(ns("2026-01-05 22:59:00+00:00"))            # 17:59 ET, EST
    check("17:59 ET is the same session day, bucket 17:45", s[0] == "2026-01-05" and m[0] == 17 * 60 + 45)
    s, m = clock(ns("2026-01-05 23:00:00+00:00"))            # 18:00 ET
    check("18:00 ET rolls to the next session day", s[0] == "2026-01-06" and m[0] == 18 * 60)
    s, m = clock(ns("2026-03-09 11:30:00+00:00"))            # EDT after 2026-03-08: 07:30 ET
    check("DST spring week: 11:30 UTC is 07:30 ET (W2 start)", m[0] == 7 * 60 + 30)
    s, m = clock(ns("2025-11-03 12:30:00+00:00"))            # EST after 2025-11-02: 07:30 ET
    check("DST autumn week: 12:30 UTC is 07:30 ET (W2 start)", m[0] == 7 * 60 + 30)

    rng = np.random.default_rng(0)
    raw = pd.DataFrame({"root": rng.choice(["ES", "ZN"], 5000), "day": rng.choice(["2026-01-05", "2026-01-06"], 5000),
                        "bucket": rng.choice([0, 15, 30], 5000), "spread_ticks": rng.integers(1, 3, 5000),
                        "n": 1, "q_lots": rng.integers(1, 900, 5000), "q_orders": rng.integers(1, 90, 5000)})
    whole = aggregate(raw)
    chunks = aggregate(pd.concat([aggregate(raw.iloc[i::3]) for i in range(3)], ignore_index=True))
    check("strided chunks aggregate bit-identically to the whole", whole.equals(chunks))

    # the trough statistic on synthetic sessions, and a W3 pairing across the halt
    def synth(dip):
        rows = []
        for k, day in enumerate(pd.bdate_range("2025-10-01", periods=150)):
            sday = day.strftime("%Y-%m-%d")
            nday = (day + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            for mnt in range(0, 24 * 60, 15):
                if 17 * 60 <= mnt < 18 * 60:
                    continue
                depth = 100.0
                if mnt in WINDOWS["W3"]["window"]:
                    depth = 100.0 * dip
                sess = nday if mnt >= 18 * 60 else sday
                rows.append(("ES", sess, bucket_label(mnt), 1, 15, int(depth * 15 * (1 + 0.05 * ((k * 7 + mnt) % 5))), 30))
        return pd.DataFrame(rows, columns=COLS)

    def w3(dip):
        t = spans_by_date(synth(dip))
        sp = WINDOWS["W3"]
        a = {k: span_stats(t, sp[k]) for k in ("window", "before", "after")}
        j = a["window"].join(a["before"], rsuffix="_b").join(a["after"], rsuffix="_a")
        j = j[(j["cov"] >= COVERAGE_MIN) & (j["cov_b"] >= COVERAGE_MIN) & (j["cov_a"] >= COVERAGE_MIN)]
        x = (np.log(j["D"]) - np.log(np.minimum(j["D_b"], j["D_a"]))).to_numpy()
        return trough_verdict(*block_bootstrap_median(x)[1:]), len(j)
    v, nj = w3(0.5)
    check(f"a halved W3 reads TROUGH, paired across the halt by calendar date ({nj} evenings)", v == "TROUGH" and nj > 100)
    check("a doubled W3 reads NOT A TROUGH", w3(2.0)[0] == "NOT A TROUGH")
    check("a flat W3 is not read as a TROUGH", w3(1.0)[0] != "TROUGH")
    check("bootstrap is deterministic", block_bootstrap_median(np.arange(50.0)) == block_bootstrap_median(np.arange(50.0)))

    costs = json.loads(COSTS.read_text(encoding="utf-8"))
    tu, cr = cost_of("ES", costs)
    check("H0 arithmetic: ES at one tick R = 12.5/2 / 3 = 2.0833", abs(1 * tu / 2 / (cr / 2) - 2.0833333) < 1e-6)
    tu, cr = cost_of("MES", costs)
    check("H0 arithmetic: MES at one tick R = 0.4167 (FAIL)", h0_verdict(1 * tu / 2 / (cr / 2)) == "FAIL")
    check("kill 1 fires only when no cell reaches R >= 1",
          decide({"X": {"windows": {"W1": {"R": 0.9, "verdict": "TROUGH", "H0": "FAIL"}}}})["kill_1_fires"]
          and not decide({"X": {"windows": {"W1": {"R": 1.0, "verdict": "TROUGH", "H0": "MARGINAL"}}}})["kill_1_fires"])
    P(f"selftest: {n_ok} checks, every guard fires")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")        # the page carries arrows; a cp1252 console cannot print them
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--profile", action="store_true")
    g.add_argument("--build", action="store_true")
    g.add_argument("--report", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.profile:
        return profile()
    if a.build:
        return build(a.workers)
    return report()


if __name__ == "__main__":
    sys.exit(main())
