"""D654 Stage 0 -- when does open interest leave the expiring contract, and could anyone trade it without holding it?

    python scripts/build_fut_oi_expiry.py --selftest
    python scripts/build_fut_oi_expiry.py --build [--workers 8]     # system interpreter (databento)
    python scripts/build_fut_oi_expiry.py --report                  # fixture -> data/stage0_d654_oi_expiry.json

DESIGN: docs/decisions/D654-STAGE-0-DESIGN-when-open-interest-leaves-the-expiring-month.md (c651f6b), committed before
this file existed.

OPEN INTEREST AND CLEARED VOLUME ONLY. No price is read: the extractor keeps `stat_type` 9 and 6, whose value is in
`quantity`. Reference sessions 2016-01-04 -> 2023-12-29 only: the yearly files from 2024 on are never opened
(`_files` raises if one is selected), and the table is filtered and asserted before it is written.

The mapping from instrument id to contract is the breadth builder's WINDOWED one (D520/D521), imported, not retyped.
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
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))


def _main_checkout(repo: Path) -> Path:
    p = repo
    while p.parent != p:
        if p.name == "worktrees" and p.parent.name == ".claude":
            return p.parent.parent
        p = p.parent
    return repo


MAIN = _main_checkout(REPO)
RAW = MAIN / "data" / "raw" / "databento" / "GLBX-20260911-SDNLQ6M99S"
EXPIRIES = REPO / "data" / "fut_expiries_from_definition.json"
FLAGS = REPO / "data" / "ledger_calendar_flags.csv"
METHOD = REPO / "data" / "index_reweight" / "methodology_facts.json"
GSCI = REPO / "data" / "index_reweight" / "gsci_schedule.csv"
D497 = MAIN / "data" / "fixtures" / "fut_open_interest_daily.csv.gz"
FIX = REPO / "data" / "fixtures" / "fut_oi_expiry_cycles.csv.gz"
META = REPO / "data" / "fixtures" / "fut_oi_expiry_cycles.meta.json"
OUT = REPO / "data" / "stage0_d654_oi_expiry.json"

SPAN = ("2016-01-04", "2023-12-29")
RESERVED_FROM = "2024-01-01"
ST_OI, ST_CV = 9, 6
UNDEF = np.iinfo(np.int64).max
GROUPS = {"energy": ("CL", "HO", "RB", "NG"), "fx": ("6E", "6J", "6B", "6A", "6C", "6S"),
          "metals": ("GC", "SI", "HG", "PL", "PA"), "treasuries": ("ZN", "ZB", "ZF", "ZT", "UB", "TN"),
          "grains": ("ZC", "ZS", "ZW", "ZL", "ZM")}
ROOTS = tuple(r for g in GROUPS.values() for r in g)
LTD_ROOTS = set(GROUPS["energy"] + GROUPS["fx"])
FND_ROOTS = set(GROUPS["metals"] + GROUPS["treasuries"] + GROUPS["grains"])
MONTH = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}
RE_C = re.compile(r"^([A-Z0-9]{2,3}?)([FGHJKMNQUVXZ])(\d{1,2})$")
D_LO, D_RECV = -30, -20
D_CARRY = D_LO      # the cycle counts if the expiring month is the root's largest here (as run: d = -30; see the result)
INDEX_BD = range(4, 12)                     # BD4..BD11: the padded superset of BD5-9
Q1, Q2, Q3, Q4, Q5, MIN_QUALIFY = 0.5, 3, 0.5, 0.10, 0.05, 3
GFND_SHARE, GFND_LEFT = 0.90, 0.25


def P(*a, **k):
    print(*a, **k, flush=True)


class GateError(AssertionError):
    pass


# ------------------------------------------------------------------ extraction (system interpreter)
def _files() -> list[Path]:
    fs = sorted(RAW.glob("glbx-mdp3-*.statistics.dbn.zst"))
    keep = [f for f in fs if SPAN[0][:4] <= f.name[10:14] <= SPAN[1][:4]]
    bad = [f.name for f in keep if f.name[10:14] >= RESERVED_FROM[:4]]
    if bad:
        raise GateError(f"[HOLDOUT] a file from {RESERVED_FROM[:4]} on was selected: {bad}")
    if len(keep) != 8:
        raise GateError(f"[FILES] expected the eight yearly files 2016-2023, found {[f.name for f in keep]}")
    return keep


def ref_date(ts_ref_ns: np.ndarray) -> np.ndarray:
    """ts_ref is the session START (the evening before the trade date it describes): +12 h lands on the trade date."""
    t = pd.to_datetime(ts_ref_ns, utc=True).tz_convert("US/Eastern") + pd.Timedelta(hours=12)
    return t.strftime("%Y-%m-%d").to_numpy()


def label(a, w):
    """(root, contract) from the mapping window containing each record's ts_event; a record claimed twice raises."""
    raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "ts": a["ts_event"].astype(np.uint64),
                        "_i": np.arange(len(a), dtype=np.int64)})
    j = raw.merge(w, on="iid", how="inner")
    j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
    if j["_i"].duplicated().any():
        raise GateError(f"[IDS] {int(j['_i'].duplicated().sum())} records claimed by more than one mapping window")
    return j


def worker(path: str) -> tuple[pd.DataFrame, dict]:
    import databento as db
    from build_fut_breadth_hourly import ids_of

    t0 = time.time()
    store = db.DBNStore.from_file(path)
    w = ids_of(store)
    w = w[w["root"].isin(ROOTS)].reset_index(drop=True)
    keys = w["iid"].to_numpy(np.uint32)
    parts, n_in = [], 0
    for arr in store.to_ndarray(count=5_000_000):
        n_in += len(arr)
        a = arr[np.isin(arr["instrument_id"], keys) & np.isin(arr["stat_type"], (ST_OI, ST_CV))]
        if not a.size:
            continue
        j = label(a, w)
        if not len(j):
            continue
        k = j["_i"].to_numpy()
        parts.append(pd.DataFrame({"root": j["root"].to_numpy(), "contract": j["contract"].to_numpy(),
                                   "stat": a["stat_type"][k].astype(np.int16),
                                   "ts_event": a["ts_event"][k].astype("int64"),
                                   "ref": ref_date(a["ts_ref"][k].astype("int64")),
                                   "value": a["quantity"][k].astype("int64")}))
    d = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    if len(d):
        d = d[(d["value"] != UNDEF) & (d["value"] >= 0)]
    return d, {"file": Path(path).name, "rows_in": n_in, "rows_kept": int(len(d)), "secs": round(time.time() - t0, 1)}


def build(workers: int) -> int:
    from backtest_framework.validation.frozen import assert_none_at_or_after, filter_before

    files = _files()
    P(f"D654 build -- {len(files)} statistics files, {sum(f.stat().st_size for f in files) / 2**30:.2f} GiB, "
      f"{len(ROOTS)} roots, {workers} processes")
    t0 = time.time()
    parts, stats = [], []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for d, st in ex.map(worker, [str(f) for f in files]):
            parts.append(d)
            stats.append(st)
            P(f"  {st['file']}: {st['rows_in']:,} in, {st['rows_kept']:,} kept ({st['secs']}s)")
    wall = time.time() - t0
    busy = sum(s["secs"] for s in stats)
    P(f"[SPEED] sum(item time)/wall = {busy / wall:.2f}x on {workers} processes ({100 * busy / wall / workers:.0f}%)")
    d = pd.concat(parts, ignore_index=True)
    d = d[(d["ref"] >= SPAN[0])]
    d = filter_before(d, "ref", RESERVED_FROM)
    assert_none_at_or_after(d, "ref", RESERVED_FROM)
    wd = pd.to_datetime(d["ref"]).dt.dayofweek
    if (wd >= 5).any():
        raise GateError(f"[REF] {int((wd >= 5).sum())} reference dates fall on a weekend")
    # the last publication for each (contract, stat, reference date) is the figure
    d = (d.sort_values("ts_event").groupby(["root", "contract", "stat", "ref"], as_index=False).last())
    t = d.pivot_table(index=["root", "contract", "ref"], columns="stat", values="value", aggfunc="last").reset_index()
    t = t.rename(columns={ST_OI: "oi", ST_CV: "cv"})
    t = t[["root", "contract", "ref", "oi", "cv"]].sort_values(["root", "contract", "ref"], kind="mergesort")
    FIX.parent.mkdir(parents=True, exist_ok=True)
    t.to_csv(FIX, index=False, compression="gzip", encoding="utf-8")
    meta = {"decision": "D654", "built_by": "python scripts/build_fut_oi_expiry.py --build", "reads_no_price": True,
            "span": list(SPAN), "roots": list(ROOTS), "rows": int(len(t)), "files": stats,
            "wall_min": round(wall / 60, 2), "speed_ratio": round(busy / wall, 2),
            "conventions": "stat 9 open interest and 6 cleared volume from `quantity`; reference date = ts_ref (session "
                           "start, ET) + 12 h; the last publication per (contract, stat, reference date); windowed ids"}
    META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    P(f"wrote {FIX.name}: {len(t):,} rows in {(time.time() - t0) / 60:.1f} min")
    return 0


# ------------------------------------------------------------------ cycles and measurements
def load_expiries() -> dict[str, list[pd.Timestamp]]:
    e = json.loads(EXPIRIES.read_text(encoding="utf-8"))["expiries"]
    return {code: sorted(pd.Timestamp(int(x), tz="UTC").tz_convert("US/Eastern").tz_localize(None).normalize()
                         for x in ns) for r in ROOTS for code, ns in e[r].items()}


def resolve(code: str, ref: pd.Timestamp, exp: dict):
    """(expiry, delivery as year*12+month): the code's first expiry on or after the session; the delivery is the first
    (year, letter-month) at or after the expiry's month (energy expires the month before delivery, the rest inside it)."""
    m = RE_C.match(code)
    if not m or code not in exp:
        return None
    mon = MONTH[m.group(2)]
    for e in exp[code]:
        if e >= ref:
            y = e.year if mon >= e.month else e.year + 1
            return e, y * 12 + mon
    return None


def first_notice(dlv: int, sessions: np.ndarray) -> pd.Timestamp | None:
    """The last of the root's sessions in the month before the delivery month."""
    y, m = divmod(dlv - 1, 12)
    m += 1
    py, pm = (y, m - 1) if m > 1 else (y - 1, 12)
    lo, hi = pd.Timestamp(py, pm, 1), pd.Timestamp(y, m, 1)
    s = sessions[(sessions >= lo) & (sessions < hi)]
    return s[-1] if len(s) else None


def bd_of_month(sessions: np.ndarray) -> dict:
    s = pd.Series(sessions)
    return dict(zip(sessions, s.groupby([s.dt.year, s.dt.month]).cumcount() + 1))


def index_roots() -> set[str]:
    m = json.loads(METHOD.read_text(encoding="utf-8"))
    bb = {"CL": "CL", "HO": "HO", "XB": "RB", "NG": "NG", "GC": "GC", "SI": "SI", "HG": "HG", "C": "ZC", "S": "ZS",
          "W": "ZW", "BO": "ZL", "SM": "ZM", "PL": "PL", "PA": "PA"}
    out = set()
    for comps in m["component_list_by_year"]["by_target_year"].values():
        for c in comps:
            if c.get("bloomberg_ticker") in bb:
                out.add(bb[c["bloomberg_ticker"]])
    g = pd.read_csv(GSCI, encoding="utf-8")
    out |= set(g["cme_root"].dropna()) & set(ROOTS)
    return out


def cycles(t: pd.DataFrame, root: str, exp: dict, use_ltd: bool, fund_days: set, in_index: bool) -> pd.DataFrame:
    g = t[t["root"] == root].copy()
    g["ref_ts"] = pd.to_datetime(g["ref"])
    sessions = np.array(sorted(g["ref_ts"].unique()))
    pos = {s: i for i, s in enumerate(sessions)}
    bd = bd_of_month(sessions)
    res = {}
    for c in g["contract"].unique():
        r = resolve(c, g.loc[g["contract"] == c, "ref_ts"].iloc[0], exp)
        if r:
            res[c] = r
    g = g[g["contract"].isin(res)]
    g["dlv"] = g["contract"].map(lambda c: res[c][1])
    g["expiry"] = g["contract"].map(lambda c: res[c][0])
    oi = g.pivot_table(index="ref_ts", columns="dlv", values="oi", aggfunc="last").reindex(sessions)
    cv = g.pivot_table(index="ref_ts", columns="dlv", values="cv", aggfunc="last").reindex(sessions)
    expiry_of = g.groupby("dlv")["expiry"].first()
    rows = []
    for dlv in sorted(oi.columns):
        if use_ltd:
            D = expiry_of[dlv]
            if D not in pos:
                prior = sessions[sessions <= D]
                D = prior[-1] if len(prior) else None
        else:
            D = first_notice(dlv, sessions)
        if D is None or D > pd.Timestamp(SPAN[1]):
            continue
        i = pos[D]
        if i + D_LO < 0 or i + 1 >= len(sessions):
            continue
        idx = sessions[i + D_LO:i + 2]                        # d = -30 .. +1
        e = oi.loc[idx, dlv].to_numpy(float)
        if not np.isfinite(e[0]) or e[0] <= 0:
            continue
        row30 = oi.loc[sessions[i + D_CARRY]]
        if row30.idxmax() != dlv:                             # the cycle counts only if the expiring month carried the root
            continue
        at20 = oi.loc[sessions[i + D_RECV]]
        later = at20[[k for k in at20.index if k > dlv]].dropna()
        if later.empty:
            continue
        recv = int(later.idxmax())
        later2 = at20[[k for k in at20.index if k > recv]].dropna()
        hedge = int(later2.idxmax()) if not later2.empty else None
        e_fill = pd.Series(e).ffill().fillna(0).to_numpy()
        base = e_fill[0]
        dd = np.arange(D_LO, 2)
        half = next((int(d) for d, v in zip(dd, e_fill) if d <= 0 and v <= 0.5 * base), 1)
        x = e_fill[:-1]                                       # d = -30 .. 0
        drain = np.clip(x[:-1] - x[1:], 0, None)              # the decreases on d = -29 .. 0
        days = idx[1:-1]
        inside = np.array([(in_index and bd[s] in INDEX_BD) or (s in fund_days) for s in days])
        tot = drain.sum()
        outside = float(drain[~inside].sum() / tot) if tot > 0 else np.nan
        r_oi = oi.loc[idx, recv].ffill().fillna(0).to_numpy(float)
        net_exp = e_fill[0] - e_fill[-2]
        roll = float((r_oi[-2] - r_oi[0]) / net_exp) if net_exp > 0 else np.nan
        r_cv = cv.loc[days, recv].fillna(0).to_numpy(float)
        od = np.where(inside, 0.0, drain)
        best, best_cv = 0.0, np.nan
        for k in range(0, len(od) - 4):
            s5 = od[k:k + 5].sum()
            if s5 > best:
                best, best_cv = s5, r_cv[k:k + 5].sum()
        m5 = float(best * max(roll, 0) / best_cv) if best > 0 and best_cv and best_cv > 0 else np.nan
        early = sessions[i + D_LO:i - 9]                     # d = -30 .. -10
        m6 = np.nan
        if hedge is not None:
            hr = cv.loc[early, hedge].median()
            rr = cv.loc[early, recv].median()
            m6 = float(hr / rr) if rr and rr > 0 and np.isfinite(hr) else np.nan
        rows.append({"root": root, "dlv": dlv, "deadline": str(D.date()), "year": D.year, "oi_d30": base,
                     "left_d1": float(e_fill[-1] / base), "half_day": half, "outside": outside, "roll": roll,
                     "m5": m5, "m6": m6, "recv": recv, "hedge": hedge,
                     "profile": [round(float(v / base), 4) for v in e_fill[:-1]],
                     "best5_outside_drain": float(best)})
    return pd.DataFrame(rows)


def summarise(cy: pd.DataFrame) -> dict:
    hd = cy["half_day"].to_numpy(float)
    q25, q75 = np.percentile(hd, [25, 75])
    prof = np.median(np.vstack(cy["profile"].to_numpy()), axis=0)
    by_year = cy.groupby("year").agg(half_day=("half_day", "median"), outside=("outside", "median"),
                                     roll=("roll", "median"), m5=("m5", "median"), m6=("m6", "median"),
                                     n=("dlv", "size"))
    out = {"cycles": int(len(cy)), "half_day_median": float(np.median(hd)), "half_day_iqr": float(q75 - q25),
           "outside_median": float(cy["outside"].median()), "roll_median": float(cy["roll"].median()),
           "m5_median": float(cy["m5"].median()), "m6_median": float(cy["m6"].median()),
           "left_after_deadline_median": float(cy["left_d1"].median()),
           "profile_median": {int(d): round(float(v), 4) for d, v in zip(range(D_LO, 1), prof)},
           "by_year": {int(y): {k: (None if pd.isna(v) else round(float(v), 4)) for k, v in r.items()}
                       for y, r in by_year.iterrows()}}
    out["qualify"] = {"Q1_outside": out["outside_median"] >= Q1, "Q2_iqr": out["half_day_iqr"] <= Q2,
                      "Q3_roll": out["roll_median"] >= Q3, "Q4_size": out["m5_median"] >= Q4,
                      "Q5_hedge": out["m6_median"] >= Q5}
    out["qualifies"] = bool(all(out["qualify"].values()))
    return out


def report() -> int:
    t = pd.read_csv(FIX, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    if t["ref"].max() >= RESERVED_FROM:
        raise GateError("[HOLDOUT] the fixture carries a 2024 session")
    exp = load_expiries()
    idx_roots = index_roots()
    fl = pd.read_csv(FLAGS, encoding="utf-8")
    fund = {r: set(pd.to_datetime(fl[(fl["root"] == r) & (fl["fund_roll"] == 1)]["date"])) for r in ("CL", "NG")}
    flags_from = pd.Timestamp(fl["date"].min())
    out = {"decision_record": "D654", "stage": "0", "reads_no_price": True, "span": list(SPAN),
           "index_roots": sorted(idx_roots), "roots": {}}
    for root in ROOTS:
        use_ltd = root in LTD_ROOTS
        fd = fund.get(root, set())
        cy = cycles(t, root, exp, use_ltd, fd, root in idx_roots)
        rec = {"deadline_rule": "last trading day" if use_ltd else "first notice day", "in_index": root in idx_roots}
        if not use_ltd and len(cy):
            share = float((cy["left_d1"] < GFND_LEFT).mean())
            rec["G_FND"] = {"share_mostly_gone": share, "passes": share >= GFND_SHARE}
            if share < GFND_SHARE:
                cy = cycles(t, root, exp, True, fd, root in idx_roots)
                rec["deadline_rule"] = "last trading day (G-FND failed)"
        if root in fund and len(cy):
            cy = cy[pd.to_datetime(cy["deadline"]) >= flags_from + pd.Timedelta(days=45)]
            rec["note"] = f"cycles from {flags_from.date()} + 45 days only, where the fund-roll flags exist"
        if len(cy) < 8:
            rec["summary"] = None
            rec["note"] = rec.get("note", "") + f"; {len(cy)} cycles, too few"
        else:
            rec["summary"] = summarise(cy)
            top = cy.sort_values("best5_outside_drain", ascending=False).head(5)
            rec["largest_outside_drains"] = [{"deadline": r.deadline, "delivery": f"{(r.dlv - 1) // 12}-{(r.dlv - 1) % 12 + 1:02d}",
                                              "contracts": int(r.best5_outside_drain)} for r in top.itertuples()]
        out["roots"][root] = rec
    q = sorted(r for r, v in out["roots"].items() if v["summary"] and v["summary"]["qualifies"])
    out["qualifying_roots"] = q
    out["route"] = ("three or more roots qualify: draft a no-expiring-leg pre-registration for the principal"
                    if len(q) >= MIN_QUALIFY else "fewer than three roots qualify: recommend closing the delivery line")
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    P(f"index roots: {sorted(idx_roots)}")
    P(f"{'root':<5}{'rule':<34}{'cyc':>4}{'half':>6}{'iqr':>5}{'out':>7}{'roll':>7}{'m5':>8}{'m6':>8}  Q1-5  G-FND")
    for r, v in out["roots"].items():
        s = v["summary"]
        if not s:
            P(f"{r:<5}{v['deadline_rule']:<34}  -- {v.get('note')}")
            continue
        qs = "".join("Y" if x else "." for x in s["qualify"].values())
        gf = v.get("G_FND", {})
        P(f"{r:<5}{v['deadline_rule']:<34}{s['cycles']:>4}{s['half_day_median']:>6.0f}{s['half_day_iqr']:>5.1f}"
          f"{s['outside_median']:>7.2f}{s['roll_median']:>7.2f}{s['m5_median']:>8.3f}{s['m6_median']:>8.3f}  {qs}"
          f"  {gf.get('share_mostly_gone', float('nan')):.2f}")
    P(f"qualifying: {q} -> {out['route']}")
    return 0


# ------------------------------------------------------------------ selftest
def selftest() -> int:
    n = 0

    def check(label_, cond):
        nonlocal n
        if not cond:
            raise AssertionError(f"FAILED: {label_}")
        n += 1
        P(f"  ok  {label_}")

    def must_raise(label_, fn):
        nonlocal n
        try:
            fn()
        except (GateError, AssertionError):
            n += 1
            P(f"  ok  raises: {label_}")
            return
        raise AssertionError(f"did NOT raise: {label_}")

    w = pd.DataFrame({"iid": np.array([7, 7], np.uint32), "root": ["CL", "6A"], "contract": ["CLN9", "6AF4"],
                      "w0": np.array([0, 100], np.uint64), "w1": np.array([100, 200], np.uint64)})
    a = np.zeros(2, dtype=[("instrument_id", "u4"), ("ts_event", "u8")])
    a["instrument_id"] = 7
    a["ts_event"] = [50, 150]
    j = label(a, w)
    check("a reissued id takes the label of the window containing each record", list(j.sort_values("_i")["contract"]) == ["CLN9", "6AF4"])
    w2 = w.copy()
    w2.loc[1, "w0"] = 40
    must_raise("overlapping windows for one record", lambda: label(a, w2))

    def et(s):
        return np.array([pd.Timestamp(s, tz="US/Eastern").value], dtype=np.int64)
    check("a Sunday 18:00 session start labels Monday", ref_date(et("2019-06-09 18:00"))[0] == "2019-06-10")
    check("a Tuesday 17:00 session start labels Wednesday", ref_date(et("2019-06-11 17:00"))[0] == "2019-06-12")

    from backtest_framework.validation.frozen import assert_none_at_or_after
    must_raise("a 2024 reference session past extraction",
               lambda: assert_none_at_or_after(pd.DataFrame({"ref": ["2024-01-02"]}), "ref", RESERVED_FROM))

    exp = load_expiries()
    e, d = resolve("GCZ3", pd.Timestamp("2023-10-02"), exp)
    check(f"GCZ3 is December 2023 (expiry {e.date()}, inside the month)", d == 2023 * 12 + 12)
    e, d = resolve("CLF4", pd.Timestamp("2023-10-02"), exp)
    check(f"CLF4 is January 2024 (expiry {e.date()}, the month before)", d == 2024 * 12 + 1)
    e, d = resolve("ZNH3", pd.Timestamp("2022-12-01"), exp)
    check(f"ZNH3 is March 2023 (expiry {e.date()})", d == 2023 * 12 + 3)

    sess = np.array(pd.bdate_range("2019-11-01", "2019-12-31").drop(pd.Timestamp("2019-11-29")))
    check("first notice for a December delivery skips a month-end holiday (2019-11-29 missing -> 11-28)",
          first_notice(2019 * 12 + 12, sess) == pd.Timestamp("2019-11-28"))

    bd = bd_of_month(np.array(pd.bdate_range("2019-06-01", "2019-06-30")))
    check("BD5 is inside the padded window and BD12 outside",
          bd[pd.Timestamp("2019-06-07")] == 5 and 5 in INDEX_BD and bd[pd.Timestamp("2019-06-18")] == 12 and 12 not in INDEX_BD)

    # a synthetic root: the expiring month drains into the next; receiving and hedge are chosen at d = -20
    days = pd.bdate_range("2019-04-01", "2019-07-31")
    rows = []
    for i, s in enumerate(days):
        left = max(0.0, 1.0 - max(0, i - 30) / 12)          # drains over twelve sessions before late May
        rows += [("GC", "GCM9", s, 100000 * left, 5000), ("GC", "GCQ9", s, 20000 + 100000 * (1 - left), 40000),
                 ("GC", "GCZ9", s, 8000, 4000)]
    t = pd.DataFrame(rows, columns=["root", "contract", "ref", "oi", "cv"])
    t["ref"] = t["ref"].dt.strftime("%Y-%m-%d")
    cy = cycles(t, "GC", exp, False, set(), True)
    c = cy[cy["dlv"] == 2019 * 12 + 6].iloc[0]
    check(f"receiving is Aug (Q9), hedge Dec (Z9), never the expiring June (roll {c.roll:.2f})",
          c.recv == 2019 * 12 + 8 and c.hedge == 2019 * 12 + 12 and abs(c.roll - 1.0) < 0.01)
    check("the half-drain day falls before the deadline", c.half_day < 0)
    P(f"selftest: {n} checks")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--build", action="store_true")
    g.add_argument("--report", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    return selftest() if a.selftest else (build(a.workers) if a.build else report())


if __name__ == "__main__":
    sys.exit(main())
