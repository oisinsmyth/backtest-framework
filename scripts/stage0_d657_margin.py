"""D657 Stage 0 -- margin-driven deleveraging: forced exit (M1), reversion of the forced-window move (M2), and
realised variance beyond a pre-notice forecast (M3).

    python scripts/stage0_d657_margin.py --selftest
    python scripts/stage0_d657_margin.py --extract-oi [--workers 8]   # system interpreter (databento) -> temp/
    python scripts/stage0_d657_margin.py --run                        # -> data/stage0_d657_margin.json

DESIGN: docs/decisions/D657-STAGE-0-DESIGN-margin-hikes-forced-exit-and-reversion.md (65d7682, amended by A1 ed24889),
committed before this file existed. Events: data/d657_margin_changes.csv from scripts/build_cme_margin_events.py.

NOTHING AT OR AFTER 2024-01-01 IS READ: the strip and the hourly fixture are filtered at the loader and asserted after,
the open-interest extraction opens only the 2010-2023 statistics files, and every event has E <= 2023-12-15.
Contract codes are resolved per ROW (D655). No window holds a contract within ten sessions of its delivery guard
(first notice for metals, Treasuries, grains and LE; the last trading day elsewhere), asserted per event.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import build_fut_oi_expiry as d654  # noqa: E402
import run_d655_metals_roll as m655  # noqa: E402
from backtest_framework.validation.frozen import assert_none_at_or_after, filter_before  # noqa: E402

MAIN = d654._main_checkout(REPO)
RAW_STATS = d654.RAW
STRIP = m655.STRIP
HOURLY = (REPO if (REPO / "data/fixtures/fut_breadth_hourly.csv.gz").exists() else MAIN) / \
    "data" / "fixtures" / "fut_breadth_hourly.csv.gz"
CHANGES = REPO / "data" / "d657_margin_changes.csv"
COVERAGE = REPO / "data" / "d657_margin_coverage.csv"
NOTICES = REPO / "data" / "d657_margin_notices.csv"
SPECS = REPO / "data" / "fut_specs_from_definition.json"
D651 = REPO / "data" / "d651_liquidity_map.json"
OI_CACHE = REPO / "temp" / "d657_oi_root_daily.csv"
OUT = REPO / "data" / "stage0_d657_margin.json"

RESERVED_FROM, LAST, E_LAST = "2024-01-01", "2023-12-29", "2023-12-15"
ROOTS = ("ES", "NQ", "YM", "NKD", "CL", "NG", "RB", "HO", "GC", "SI", "PL", "HG", "ZN", "ZB", "ZF", "ZT", "UB", "TN",
         "SR3", "6E", "6J", "6B", "6A", "6C", "6S", "ZC", "ZS", "ZW", "ZL", "ZM", "LE", "HE", "BTC")
FND_ROOTS = {"GC", "SI", "PL", "HG", "ZN", "ZB", "ZF", "ZT", "UB", "TN", "ZC", "ZS", "ZW", "ZL", "ZM", "LE"}
MIN_PCT, MERGE, CTRL_GAP, VOLWIN = 0.05, 10, 20, 20
W_AFTER, Y_LEN, OI_AFTER, RV_LEN = 2, 5, 5, 10
NO_DELIVERY = 10
DRAWS, SEED, BOOT = 2000, 657, 1000
COST_MULT = 3.0
# D651 bucket holding each root's settlement (ET): grains 14:14-14:15, energy 14:28-14:30, metals 13:30 (gold) and
# 13:25 (copper), rates / FX / NKD / SR3 15:00, index and BTC 16:00, livestock 14:05
SETTLE_BUCKET = {**{r: "14:00" for r in ("ZC", "ZS", "ZW", "ZL", "ZM", "LE", "HE")},
                 **{r: "14:15" for r in ("CL", "NG", "RB", "HO")},
                 **{r: "13:15" for r in ("GC", "SI", "PL", "HG")},
                 **{r: "14:45" for r in ("ZN", "ZB", "ZF", "ZT", "UB", "TN", "SR3", "6E", "6J", "6B", "6A", "6C", "6S",
                                         "NKD")},
                 **{r: "15:45" for r in ("ES", "NQ", "YM", "BTC")}}
MICRO = {"ES": "MES", "NQ": "MNQ", "YM": "MYM", "BTC": "MBT"}
GUARD_SOURCE: dict[str, int] = {}
COMMISSION_RT = 6.0            # D591, declared, per contract


def P(*a, **k):
    print(*a, **k, flush=True)


class GateError(AssertionError):
    pass


def load_expiries() -> dict[str, list[pd.Timestamp]]:
    """D654's expiry map for THIS study's 33 roots (d654.load_expiries keeps only D654's 26, which would silently
    drop ES, NQ, YM, NKD, LE, HE, SR3 and BTC)."""
    e = json.loads(d654.EXPIRIES.read_text(encoding="utf-8"))["expiries"]
    missing = [r for r in ROOTS if r not in e]
    if missing:
        raise GateError(f"[EXPIRIES] no definition expiries for {missing}")
    return {code: sorted(pd.Timestamp(int(x), tz="UTC").tz_convert("US/Eastern").tz_localize(None).normalize()
                         for x in ns) for r in ROOTS for code, ns in e[r].items()}


# ================================================================== open interest (system interpreter)
def _stat_files() -> list[Path]:
    fs = sorted(RAW_STATS.glob("glbx-mdp3-*.statistics.dbn.zst"))
    keep = [f for f in fs if "2010" <= f.name[10:14] <= "2023"]
    if any(f.name[10:14] >= RESERVED_FROM[:4] for f in keep):
        raise GateError("[HOLDOUT] a statistics file from 2024 on was selected")
    if len(keep) != 14:
        raise GateError(f"[FILES] expected 14 yearly files 2010-2023, found {[f.name for f in keep]}")
    return keep


def oi_worker(path: str) -> tuple[pd.DataFrame, dict]:
    """Open interest (stat 9, in `quantity`) per (contract, reference trade date), last publication kept."""
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
        a = arr[np.isin(arr["instrument_id"], keys) & (arr["stat_type"] == d654.ST_OI)]
        if not a.size:
            continue
        j = d654.label(a, w)
        if not len(j):
            continue
        k = j["_i"].to_numpy()
        ts_ref = a["ts_ref"][k].astype("int64")
        ev = a["ts_event"][k].astype("int64")
        parts.append(pd.DataFrame({"root": j["root"].to_numpy(), "contract": j["contract"].to_numpy(),
                                   "ts_event": ev,
                                   # the 2010-2015 files carry no ts_ref (0): the session is assigned from the
                                   # publication date later, so it is left empty here rather than dated 1970
                                   "ref": np.where((ts_ref > 0) & (ts_ref != d654.UNDEF), d654.ref_date(ts_ref), ""),
                                   "pub": pd.to_datetime(ev, utc=True).tz_convert("US/Eastern").strftime("%Y-%m-%d"),
                                   "pub_hour": pd.to_datetime(ev, utc=True).tz_convert("US/Eastern").hour,
                                   "oi": a["quantity"][k].astype("int64")}))
    d = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    if len(d):
        d = d[(d["oi"] != d654.UNDEF) & (d["oi"] >= 0)]
        d = d.sort_values("ts_event").groupby(["root", "contract", "ref", "pub"], as_index=False).last()
    return d, {"file": Path(path).name, "rows_in": n_in, "rows_kept": int(len(d)), "secs": round(time.time() - t0, 1)}


def extract_oi(workers: int) -> None:
    files = _stat_files()
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(oi_worker, [str(f) for f in files]))
    d = pd.concat([r[0] for r in res], ignore_index=True)
    # From 2016 CME publishes each session's open interest twice: the morning after (09:00-16:00 ET) and again at
    # the next session's evening open (20:00-23:00 ET), keyed there to the NEXT session. The 2010-2015 files carry
    # only the morning publication and no ts_ref. So, uniformly for all fourteen years: morning publications only,
    # each describing the root's last session strictly before its publication date. Checked against ts_ref
    # wherever the files carry it (2016-2023: 99.6 % on a 2020 probe; the misses are 09:00 publications of a
    # same-day record).
    d = d[d["pub_hour"] < 17].copy()
    d["ref_given"] = d["ref"]
    d["ref"] = ""
    s = pd.read_csv(STRIP, usecols=["root", "ref"], encoding="utf-8")
    s = filter_before(s[s["root"].isin(ROOTS)], "ref", RESERVED_FROM).drop_duplicates()
    assigned = []
    check = {}
    for root, g in d.groupby("root"):
        cal_r = np.sort(pd.to_datetime(s.loc[s["root"] == root, "ref"]).to_numpy("datetime64[ns]"))
        pub = pd.to_datetime(g["pub"]).to_numpy("datetime64[ns]")
        k = np.searchsorted(cal_r, pub, side="left") - 1
        prev = np.where(k >= 0, pd.DatetimeIndex(cal_r[np.clip(k, 0, len(cal_r) - 1)]).strftime("%Y-%m-%d"), "")
        g = g.copy()
        given = (g["ref_given"] != "").to_numpy()
        check[root] = float((prev[given] == g["ref_given"].to_numpy()[given]).mean()) if given.any() else None
        g["ref"] = prev
        assigned.append(g[g["ref"] != ""])
    d = pd.concat(assigned, ignore_index=True)
    d = d.sort_values("ts_event").groupby(["root", "contract", "ref"], as_index=False).last()
    agree = [v for v in check.values() if v is not None]
    P(f"publication-date rule vs ts_ref where both exist: median agreement {np.median(agree):.4f}, "
      f"min {min(agree):.4f} ({min(check, key=lambda r: check[r] if check[r] is not None else 9)})")
    d = filter_before(d, "ref", RESERVED_FROM)
    assert_none_at_or_after(d, "ref", RESERVED_FROM)
    exp = load_expiries()
    d["ref_ts"] = pd.to_datetime(d["ref"])
    keep = []
    for root, g in d.groupby("root"):
        g = g.copy()
        g["dlv"] = infer_dlv(g)      # from the code and the session: the definitions map lacks whole contract-years
        keep.append(g[g["dlv"].notna()])
    d = pd.concat(keep, ignore_index=True)
    # A contract's morning publication is missing on some sessions (holiday-adjacent days especially); a plain sum
    # then collapses to whatever deferred months did publish (ZT on 2018-12-31: 23 contracts). Each contract's
    # INTERNAL gaps (between its own first and last records, up to FILL sessions) carry its last value; it is
    # never carried past its last record. The filled share is reported.
    FILL = 5
    tots, filled_share = [], {}
    for root, g in d.groupby("root"):
        cal_r = pd.DatetimeIndex(np.sort(pd.to_datetime(s.loc[s["root"] == root, "ref"]).unique()))
        m = g.pivot_table(index="ref_ts", columns=["contract", "dlv"], values="oi", aggfunc="last").reindex(cal_r)
        have = m.notna()
        first, last = have.idxmax(), have[::-1].idxmax()
        inside = pd.DataFrame({c: (cal_r >= first[c]) & (cal_r <= last[c]) for c in m.columns}, index=cal_r)
        f = m.ffill(limit=FILL).where(inside)
        filled_share[root] = float((f.notna() & ~have).to_numpy().sum() / max(f.notna().to_numpy().sum(), 1))
        t = pd.DataFrame({"root": root, "ref": cal_r.strftime("%Y-%m-%d"), "oi_total": f.sum(axis=1, min_count=1),
                          "n_contracts": f.notna().sum(axis=1)})
        tots.append(t[t["oi_total"].notna()])
    tot = pd.concat(tots, ignore_index=True)
    P(f"internal gaps filled (share of contract-days): median {np.median(list(filled_share.values())):.4f}, "
      f"max {max(filled_share.values()):.4f} ({max(filled_share, key=filled_share.get)})")
    OI_CACHE.parent.mkdir(exist_ok=True)
    tot.to_csv(OI_CACHE, index=False, encoding="utf-8", lineterminator="\n")
    P(f"open interest: {len(d):,} contract-days -> {len(tot):,} root-days, {tot['root'].nunique()} roots, "
      f"{(time.time() - t0) / 60:.1f} min; per file {[(r[1]['file'][10:14], r[1]['secs']) for r in res]}")


# ================================================================== loaders
MONTH_OF = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}
LAG_MONTHS = 3      # a SOFR code names the START of its reference quarter and trades to its end


def infer_dlv(g: pd.DataFrame) -> pd.Series:
    """year*12+month of each row's contract, from the code and the row's own session, WITHOUT the definitions
    expiry map (which lacks a quarter of Treasury contract-years, ~9 % of FX from 2017, 7-22 % of SI and PL and
    most of BTC, so a row it cannot resolve would vanish). A two-digit year is read directly; a one-digit year
    is the first year ending in that digit whose delivery month is no more than LAG_MONTHS before the session."""
    out = pd.Series(np.nan, index=g.index)
    for code, idx in g.groupby("contract").groups.items():
        m = d654.RE_C.match(code)
        if not m:
            continue
        mon, yy = MONTH_OF[m.group(2)], m.group(3)
        refs = g.loc[idx, "ref_ts"]
        ry, rm = refs.dt.year.to_numpy(), refs.dt.month.to_numpy()
        if len(yy) == 2:
            y = np.full(len(idx), 2000 + int(yy))
        else:
            y = ry - ry % 10 + int(yy)
            y = np.where(y * 12 + mon < ry * 12 + rm - LAG_MONTHS, y + 10, y)
            y = np.where(y * 12 + mon >= (ry + 10) * 12 + rm - LAG_MONTHS, y - 10, y)
        out.loc[idx] = y * 12 + mon
    return out


def load_prices(exp) -> tuple[dict, dict, dict]:
    """Per root: settlements pivoted (session x delivery), the session calendar, and each delivery's guard."""
    s = pd.read_csv(STRIP, usecols=["root", "contract", "ref", "settle"], encoding="utf-8")
    s = s[s["root"].isin(ROOTS)]
    s = filter_before(s, "ref", RESERVED_FROM)
    assert_none_at_or_after(s, "ref", RESERVED_FROM)
    s["ref_ts"] = pd.to_datetime(s["ref"])
    px, cal, guard = {}, {}, {}
    for root, g in s.groupby("root"):
        g = g.copy()
        g["dlv"] = infer_dlv(g)
        g = g[g["dlv"].notna() & (g["settle"] > 0)]
        g["dlv"] = g["dlv"].astype(int)
        if g.duplicated(["dlv", "ref_ts"]).any():
            dup = g[g.duplicated(["dlv", "ref_ts"], keep=False)].head(4)[["contract", "ref", "dlv"]].to_dict("records")
            raise GateError(f"[RESOLVE] {root}: two settlements for one (contract, session): {dup}")
        p = g.pivot_table(index="ref_ts", columns="dlv", values="settle", aggfunc="last").sort_index()
        sessions = p.index.to_numpy("datetime64[ns]")
        code_of = g.groupby("dlv")["contract"].first().to_dict()
        last_settle = g.groupby("dlv")["ref_ts"].max().to_dict()
        gd = {}
        for dlv in p.columns:
            y, m = divmod(int(dlv) - 1, 12)
            m += 1
            if root in FND_ROOTS:
                py, pm = (y, m - 1) if m > 1 else (y - 1, 12)
                lo, hi = np.datetime64(pd.Timestamp(py, pm, 1)), np.datetime64(pd.Timestamp(y, m, 1))
                inside = sessions[(sessions >= lo) & (sessions < hi)]
                gd[int(dlv)] = pd.Timestamp(inside[-1]) if len(inside) else \
                    pd.bdate_range(pd.Timestamp(lo), pd.Timestamp(hi) - pd.Timedelta(days=1))[-1]
                continue
            # the last trading day: the listed expiry within [delivery - 2 months, delivery + 4 months] when the
            # definitions carry it; else the contract's last settlement if that came before the window's end;
            # else (still trading on the last in-sample session, expiry unlisted) beyond the window
            lo, hi = pd.Timestamp(y, m, 1) - pd.DateOffset(months=2), pd.Timestamp(y, m, 1) + pd.DateOffset(months=4)
            listed = [e for e in exp.get(code_of[int(dlv)], []) if lo <= e < hi]
            if listed:
                gd[int(dlv)] = listed[0]
                GUARD_SOURCE["listed"] = GUARD_SOURCE.get("listed", 0) + 1
            elif last_settle[int(dlv)] < p.index[-1]:
                gd[int(dlv)] = last_settle[int(dlv)]
                GUARD_SOURCE["last_settlement"] = GUARD_SOURCE.get("last_settlement", 0) + 1
            else:
                gd[int(dlv)] = pd.Timestamp("2099-12-31")
                GUARD_SOURCE["beyond_window"] = GUARD_SOURCE.get("beyond_window", 0) + 1
        px[root], cal[root], guard[root] = p, p.index, gd
    return px, cal, guard


def guard_index(cal: pd.DatetimeIndex, gd: dict) -> tuple[np.ndarray, np.ndarray]:
    """(deliveries sorted, each guard as a session index; a guard beyond the calendar counts sessions on bdays)."""
    dl = np.array(sorted(gd), dtype=int)
    gi = np.searchsorted(cal.to_numpy("datetime64[ns]"), np.array([np.datetime64(gd[d]) for d in dl]), side="right") - 1
    beyond = np.array([gd[d] > cal[-1] for d in dl])
    extra = np.array([len(pd.bdate_range(cal[-1], gd[d])) - 1 if b else 0 for d, b in zip(dl, beyond)])
    return dl, gi + extra


def pick_contract(p: np.ndarray, dl: np.ndarray, gi: np.ndarray, need: list[int], end: int):
    """The nearest delivery whose guard is >= end + NO_DELIVERY sessions and that settles at every needed session."""
    for k in np.nonzero(gi >= end + NO_DELIVERY)[0]:
        col = p[:, k]
        if all(0 <= i < len(col) and np.isfinite(col[i]) for i in need):
            return k
    return None


def daily_returns(px: pd.DataFrame, dl: np.ndarray, gi: np.ndarray) -> np.ndarray:
    """r[s] = log settle(s) / settle(s-1) on the nearest contract clear of its guard through s (NaN if absent)."""
    p = px[dl].to_numpy(float)
    r = np.full(len(p), np.nan)
    for s in range(1, len(p)):
        k = pick_contract(p, dl, gi, [s - 1, s], s)
        if k is not None:
            r[s] = np.log(p[s, k] / p[s - 1, k])
    return r


def rolling_state(r: np.ndarray, win: int = VOLWIN) -> tuple[np.ndarray, np.ndarray]:
    """Trailing volatility and trailing return over the last `win` daily returns ending at s (>= 15 valid)."""
    s = pd.Series(r)
    vol = s.rolling(win, min_periods=15).std().to_numpy()
    tr = s.rolling(win, min_periods=15).sum().to_numpy()
    return vol, tr


def realised_variance(cal: dict) -> dict[str, np.ndarray]:
    """Daily realised variance: the sum of squared hourly log returns between consecutive hourly closes of the
    root's front contract in `fut_breadth_hourly` (Sunday placeholder rows carry no close and drop out)."""
    cols = None
    out = {}
    for chunk in pd.read_csv(HOURLY, chunksize=50_000, encoding="utf-8"):
        chunk = chunk[chunk["root"].isin(ROOTS)]
        chunk = filter_before(chunk, "day", RESERVED_FROM)
        assert_none_at_or_after(chunk, "day", RESERVED_FROM)
        if cols is None:
            cols = [c for c in chunk.columns if c.endswith("_c") and c.startswith("h")]
        for root, g in chunk.groupby("root"):
            c = g[cols].to_numpy(float)
            with np.errstate(invalid="ignore", divide="ignore"):
                rv = np.array([np.nansum(np.diff(np.log(row[np.isfinite(row) & (row > 0)])) ** 2)
                               if np.sum(np.isfinite(row) & (row > 0)) >= 3 else np.nan for row in c])
            out.setdefault(root, []).append(pd.Series(rv, index=pd.to_datetime(g["day"])))
    res = {}
    for root, parts in out.items():
        s = pd.concat(parts)
        s = s[~s.index.duplicated(keep="last")]
        res[root] = s.reindex(cal[root]).to_numpy(float) if root in cal else None
    return res


def load_oi(cal: dict) -> dict[str, np.ndarray]:
    if not OI_CACHE.exists():
        raise SystemExit(f"{OI_CACHE} missing: run --extract-oi under the system interpreter first")
    d = pd.read_csv(OI_CACHE, encoding="utf-8")
    d = filter_before(d, "ref", RESERVED_FROM)
    assert_none_at_or_after(d, "ref", RESERVED_FROM)
    out = {}
    for root, g in d.groupby("root"):
        s = pd.Series(g["oi_total"].to_numpy(float), index=pd.to_datetime(g["ref"]))
        out[root] = s.reindex(cal[root]).to_numpy(float) if root in cal else None
    return out


# ================================================================== events
def merge_events(dates_idx: list[int], gap: int = MERGE) -> list[int]:
    """Increases within `gap` sessions of the last KEPT one are the same episode, dated by its first."""
    kept: list[int] = []
    for i in sorted(dates_idx):
        if not kept or i - kept[-1] > gap:
            kept.append(i)
    return kept


def load_events(cal: dict) -> tuple[pd.DataFrame, dict, dict]:
    ch = pd.read_csv(CHANGES, encoding="utf-8")
    cov = pd.read_csv(COVERAGE, encoding="utf-8")
    notices = pd.read_csv(NOTICES, encoding="utf-8") if NOTICES.exists() else None
    ev, change_idx, covered = [], {}, {}
    for root in ROOTS:
        if root not in cal:
            continue
        c = cal[root]
        cn = c.to_numpy("datetime64[ns]")
        g = ch[ch["root"] == root]
        idx_all = np.searchsorted(cn, pd.to_datetime(g["date"]).to_numpy("datetime64[ns]"), side="left")
        change_idx[root] = np.unique(idx_all[idx_all < len(c)])
        mask = np.zeros(len(c), bool)
        for _, r in cov[cov["root"] == root].iterrows():
            mask |= (c >= pd.Timestamp(r["from"])) & (c <= pd.Timestamp(r["to"]))
        covered[root] = mask
        inc = g[(g["pct"] >= MIN_PCT) & (g["date"] <= E_LAST)]
        ii = np.searchsorted(cn, pd.to_datetime(inc["date"]).to_numpy("datetime64[ns]"), side="left")
        pct = dict(zip(ii, inc["pct"]))
        for e in merge_events([int(i) for i in ii if i < len(c)]):
            n_idx, n_src = e - 1, "E-1"
            if notices is not None:
                # an advisory may take effect after a WEEKEND close (10-117: "Saturday, March 20, 2010"); it is
                # matched to the first session on or after its effective date
                eff_idx = np.searchsorted(cn, pd.to_datetime(notices["effective"]).to_numpy("datetime64[ns]"), side="left")
                m = notices[eff_idx == e]
                if len(m):
                    nd = pd.Timestamp(m["notice"].min())
                    k = int(np.searchsorted(cn, np.datetime64(nd), side="left"))
                    if k < e:
                        n_idx, n_src = k, "advisory"
            ev.append({"root": root, "E": c[e], "e": e, "n": n_idx, "N": c[n_idx], "n_source": n_src,
                       "pct": float(pct[e])})
    return pd.DataFrame(ev), change_idx, covered


def control_pool(root_len: int, change_idx: np.ndarray, covered: np.ndarray, volq: np.ndarray,
                 trend: np.ndarray, a: int, span: int) -> np.ndarray:
    """Candidate start sessions for one event's control: same volatility quintile and trend sign as the event's
    start `a`, at least CTRL_GAP sessions from every margin change on the root, covered by the margin history
    (so "no change" is known), and with its whole window inside the calendar."""
    s = np.arange(root_len)
    ok = (s + span < root_len) & covered & np.isfinite(volq) & (volq == volq[a]) & \
        (np.sign(trend) == np.sign(trend[a]))
    if len(change_idx):
        d = np.abs(s[:, None] - change_idx[None, :]).min(axis=1)
        ok &= d >= CTRL_GAP
    # the control window itself must be covered end to end
    ok &= np.array([covered[i: i + span + 1].all() if i + span < root_len else False for i in s])
    return s[ok]


# ================================================================== statistics
def cluster_mean_t(x: np.ndarray, cl: np.ndarray) -> tuple[float, float]:
    x = np.asarray(x, float)
    m = x.mean()
    g = pd.Series(x - m).groupby(cl).sum().to_numpy()
    n, G = len(x), len(g)
    se = np.sqrt(G / (G - 1) * np.sum(g ** 2)) / n if G > 1 else np.nan
    return float(m), float(m / se) if se > 0 else float("nan")


def cluster_ols(y: np.ndarray, x: np.ndarray, cl: np.ndarray) -> tuple[float, float]:
    """Slope of y on [1, x] and its cluster-robust t (CR1)."""
    X = np.column_stack([np.ones_like(x), x])
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ y
    u = y - X @ b
    meat = np.zeros((2, 2))
    groups = pd.Series(np.arange(len(y))).groupby(cl).indices
    for idx in groups.values():
        sg = X[idx].T @ u[idx]
        meat += np.outer(sg, sg)
    G, n = len(groups), len(y)
    V = XtX_inv @ meat @ XtX_inv * (G / (G - 1)) * ((n - 1) / (n - 2))
    return float(b[1]), float(b[1] / np.sqrt(V[1, 1]))


def slope(y: np.ndarray, x: np.ndarray) -> float:
    xm = x - x.mean()
    return float(np.dot(xm, y - y.mean()) / np.dot(xm, xm))


def qdist(draws: np.ndarray, rng, q: float) -> dict:
    boot = np.array([np.quantile(rng.choice(draws, len(draws)), q) for _ in range(BOOT)])
    return {"p05": float(np.quantile(draws, 0.05)), "p50": float(np.quantile(draws, 0.50)),
            "p95": float(np.quantile(draws, 0.95)), "q": q, "q_value": float(np.quantile(draws, q)),
            "q_boot_se": float(boot.std(ddof=1)), "draws": int(len(draws))}


def har_residuals(rv: np.ndarray, k0: int) -> np.ndarray:
    """u[t] = log mean RV(t+k0 .. t+k0+RV_LEN-1) less a HAR forecast made at t from coefficients fitted, per
    calendar quarter, ONLY on rows whose target window ended before the quarter began (>= 250 rows)."""
    n = len(rv)
    lr = np.log(np.where(rv > 0, rv, np.nan))
    s = pd.Series(rv)
    xd = lr
    xw = np.log(s.rolling(5, min_periods=4).mean().to_numpy())
    xm = np.log(s.rolling(22, min_periods=18).mean().to_numpy())
    fut = s[::-1].rolling(RV_LEN, min_periods=RV_LEN - 2).mean()[::-1].to_numpy()   # mean of rv[t .. t+RV_LEN-1]
    y = np.full(n, np.nan)
    y[: n - k0] = np.log(fut[k0:]) if k0 else np.log(fut)
    return xd, xw, xm, y


def har_forecast_u(rv: np.ndarray, cal: pd.DatetimeIndex, k0: int) -> np.ndarray:
    xd, xw, xm, y = har_residuals(rv, k0)
    n = len(rv)
    u = np.full(n, np.nan)
    q = pd.PeriodIndex(cal, freq="Q")
    ok_x = np.isfinite(xd) & np.isfinite(xw) & np.isfinite(xm)
    for per in np.unique(q):
        rows = np.nonzero(q == per)[0]
        start = rows[0]
        fit = np.nonzero(ok_x & np.isfinite(y) & (np.arange(n) + k0 + RV_LEN - 1 < start))[0]
        if len(fit) < 250:
            continue
        X = np.column_stack([np.ones(len(fit)), xd[fit], xw[fit], xm[fit]])
        b = np.linalg.lstsq(X, y[fit], rcond=None)[0]
        r = rows[ok_x[rows]]
        f = b[0] + b[1] * xd[r] + b[2] * xw[r] + b[3] * xm[r]
        u[r] = y[r] - f
    return u


# ================================================================== cost
def cost_bp(root: str, price: float, specs: dict, d651: dict, micro: bool = False) -> float | None:
    sym = MICRO.get(root) if micro else root
    if sym is None or sym not in d651 or sym not in specs:
        return None
    pr = d651[sym]
    prof = pr["profile"].get(SETTLE_BUCKET[root])
    if prof is None or prof.get("S_mean") is None:
        return None
    rt_usd = prof["S_mean"] * pr["tick_usd"] + COMMISSION_RT
    e = specs[sym]
    pv = e["unit_of_measure_qty"] / e["scaling_divisor"]
    return rt_usd / (price * pv) * 1e4


# ================================================================== run
def run() -> int:
    t0 = time.time()
    exp = load_expiries()
    px, cal, guard = load_prices(exp)
    lost = sorted(set(ROOTS) - set(px))
    if lost:
        raise GateError(f"[ROOTS] prices missing for {lost}")
    P(f"prices: {len(px)} roots, sessions to {max(c[-1] for c in cal.values()).date()}")
    oi = load_oi(cal)
    rvs = realised_variance(cal)
    ev, change_idx, covered = load_events(cal)
    P(f"events after merging: {len(ev)}; notice dates from advisories: {(ev['n_source'] == 'advisory').sum()}")
    specs = json.loads(SPECS.read_text(encoding="utf-8"))["specs"]
    d651 = json.loads(D651.read_text(encoding="utf-8"))["per_root"]

    per_root = {}
    for root in ev["root"].unique():
        dl, gi = guard_index(cal[root], guard[root])
        p = px[root][dl].to_numpy(float)
        r = daily_returns(px[root], dl, gi)
        vol, tr = rolling_state(r)
        ok = np.isfinite(vol)
        volq = np.full(len(vol), np.nan)
        volq[ok] = pd.qcut(vol[ok], 5, labels=False, duplicates="drop")
        per_root[root] = {"dl": dl, "gi": gi, "p": p, "vol": vol, "tr": tr, "volq": volq}

    rng = np.random.default_rng(SEED)
    rows = []
    for _, e in ev.iterrows():
        root, a, ie = e["root"], int(e["n"]) - 1, int(e["e"])
        R = per_root[root]
        if a < VOLWIN or not np.isfinite(R["vol"][a]):
            continue
        lW = ie + W_AFTER - a
        end = ie + W_AFTER + Y_LEN
        L_oi = ie + OI_AFTER - a
        if end >= len(R["p"]):
            continue
        k = pick_contract(R["p"], R["dl"], R["gi"], [a, a + lW, end], end)
        if k is None:
            continue
        if R["gi"][k] < end + NO_DELIVERY:
            raise GateError(f"[DELIVERY] {root} {e['E'].date()}: window ends within {NO_DELIVERY} sessions of the guard")
        W = np.log(R["p"][a + lW, k] / R["p"][a, k])
        Y = np.log(R["p"][end, k] / R["p"][a + lW, k])
        o = oi.get(root)
        dOI = np.log(o[a + L_oi] / o[a]) if o is not None and o[a] > 0 and np.isfinite(o[a + L_oi]) and o[a + L_oi] > 0 \
            else np.nan
        span = max(end, a + L_oi) - a
        pool = control_pool(len(R["p"]), change_idx[root], covered[root], R["volq"], R["tr"], a, span)
        rows.append({"root": root, "E": e["E"], "N": e["N"], "n_source": e["n_source"], "pct": e["pct"], "a": a,
                     "lW": lW, "L_oi": L_oi, "k0": ie + 1 - a, "W": W, "Y": Y, "sigma": R["vol"][a], "dOI": dOI,
                     "price": R["p"][a, k], "pool": pool, "year": e["E"].year,
                     "cost_bp": cost_bp(root, R["p"][a, k], specs, d651),
                     "cost_bp_micro": cost_bp(root, R["p"][a, k], specs, d651, micro=True)})
    E = pd.DataFrame(rows)
    E = E[E["pool"].map(len) >= 20].reset_index(drop=True)
    P(f"events scored: {len(E)} on {E['root'].nunique()} roots; distinct notice dates {E['N'].nunique()}")

    # ---------------- control draws: one control start per event per draw
    draws = np.stack([rng.choice(pl, DRAWS) for pl in E["pool"]])          # events x DRAWS

    def at(root, arr_name, idx):
        return per_root[root][arr_name][idx]

    # M1 -- open interest
    m1 = E[np.isfinite(E["dOI"])].index.to_numpy()
    c_dOI = np.full((len(E), DRAWS), np.nan)
    for i in m1:
        root, L = E.at[i, "root"], int(E.at[i, "L_oi"])
        o = oi[root]
        s = draws[i]
        with np.errstate(divide="ignore", invalid="ignore"):
            c_dOI[i] = np.log(o[s + L] / o[s])
    abn = E.loc[m1, "dOI"].to_numpy() - np.nanmean(c_dOI[m1], axis=1)
    cl = E.loc[m1, "N"].dt.strftime("%Y-%m-%d").to_numpy()
    m1_mean, m1_t = cluster_mean_t(abn, cl)
    ev_mean = float(E.loc[m1, "dOI"].mean())
    null_m1 = np.nanmean(c_dOI[m1], axis=0)
    m1_null = qdist(null_m1, rng, 0.05)
    loyo_m1 = {int(y): float(abn[E.loc[m1, "year"].to_numpy() != y].mean()) for y in sorted(E.loc[m1, "year"].unique())}
    M1 = {"events": int(len(m1)), "mean_dOI": ev_mean, "mean_abnormal_dOI": m1_mean, "t_cluster": m1_t,
          "null_of_event_mean": m1_null, "loyo_abnormal": loyo_m1,
          "B1": m1_mean < 0 and m1_t <= -2.0, "B2": ev_mean < m1_null["p05"],
          "B2_within_2se": abs(ev_mean - m1_null["p05"]) <= 2 * m1_null["q_boot_se"],
          "B3": all(v < 0 for v in loyo_m1.values())}
    M1["pass"] = bool(M1["B1"] and M1["B2"] and M1["B3"])

    # M2 -- the forced-window move reverts
    x = (E["W"] / E["sigma"]).to_numpy()
    y = E["Y"].to_numpy()
    cl2 = E["N"].dt.strftime("%Y-%m-%d").to_numpy()
    b2, t2 = cluster_ols(y, x, cl2)
    bstd, _ = cluster_ols(y / E["sigma"].to_numpy(), x, cl2)
    null_b = np.empty(DRAWS)
    for d in range(DRAWS):
        cx, cy = np.empty(len(E)), np.empty(len(E))
        for i in range(len(E)):
            root, lW = E.at[i, "root"], int(E.at[i, "lW"])
            R = per_root[root]
            s = draws[i, d]
            end = s + lW + Y_LEN
            k = pick_contract(R["p"], R["dl"], R["gi"], [s, s + lW, end], end)
            if k is None or not np.isfinite(R["vol"][s]):
                cx[i] = cy[i] = np.nan
                continue
            cx[i] = np.log(R["p"][s + lW, k] / R["p"][s, k]) / R["vol"][s]
            cy[i] = np.log(R["p"][end, k] / R["p"][s + lW, k])
        m = np.isfinite(cx) & np.isfinite(cy)
        null_b[d] = slope(cy[m], cx[m])
        if d % 250 == 0:
            P(f"  M2 control draw {d}/{DRAWS} ({(time.time() - t0) / 60:.1f} min)")
    m2_null = qdist(null_b, rng, 0.05)
    loyo_m2 = {int(yr): slope(y[E["year"].to_numpy() != yr], x[E["year"].to_numpy() != yr])
               for yr in sorted(E["year"].unique())}
    med_absx = float(np.median(np.abs(x)))
    move_bp = abs(b2) * med_absx * 1e4
    move_bp_std = abs(bstd) * med_absx * float(E["sigma"].median()) * 1e4
    cb = E["cost_bp"].dropna()
    cbm = E["cost_bp_micro"].dropna()
    M2 = {"events": int(len(E)), "beta": b2, "t_cluster": t2, "null_beta": m2_null, "loyo_beta": loyo_m2,
          "median_abs_W_over_sigma": med_absx, "median_sigma": float(E["sigma"].median()),
          "expected_move_bp": move_bp, "beta_standardised": bstd, "expected_move_bp_standardised": move_bp_std,
          "cost_bp_full_median": float(cb.median()) if len(cb) else None, "cost_events_full": int(len(cb)),
          "cost_bp_micro_median": float(cbm.median()) if len(cbm) else None, "cost_events_micro": int(len(cbm)),
          "B1": b2 < 0 and t2 <= -2.0, "B2": b2 < m2_null["p05"],
          "B2_within_2se": abs(b2 - m2_null["p05"]) <= 2 * m2_null["q_boot_se"],
          "B3": all(v < 0 for v in loyo_m2.values()),
          "B4": bool(len(cb)) and move_bp >= COST_MULT * float(cb.median()),
          "B5": M1["pass"]}
    M2["pass"] = bool(M2["B1"] and M2["B2"] and M2["B3"] and M2["B4"] and M2["B5"])

    # M3 -- realised variance beyond a pre-notice HAR forecast
    u_cache = {}
    ue = np.full(len(E), np.nan)
    cu = np.full((len(E), DRAWS), np.nan)
    for i in range(len(E)):
        root, k0 = E.at[i, "root"], int(E.at[i, "k0"])
        if rvs.get(root) is None:
            continue
        if (root, k0) not in u_cache:
            u_cache[(root, k0)] = har_forecast_u(rvs[root], cal[root], k0)
        u = u_cache[(root, k0)]
        ue[i] = u[int(E.at[i, "a"])]
        cu[i] = u[draws[i]]
    m3 = np.nonzero(np.isfinite(ue))[0]
    m3_mean, m3_t = cluster_mean_t(ue[m3], cl2[m3])
    null_m3 = np.nanmean(cu[m3], axis=0)
    m3_null = qdist(null_m3, rng, 0.95)
    loyo_m3 = {int(yr): float(ue[m3][E["year"].to_numpy()[m3] != yr].mean()) for yr in sorted(E["year"].iloc[m3].unique())}
    M3 = {"events": int(len(m3)), "mean_u": m3_mean, "t_cluster": m3_t, "null_mean_u": m3_null, "loyo_mean_u": loyo_m3,
          "B1": m3_mean > 0 and m3_t >= 2.0, "B2": m3_mean > m3_null["p95"],
          "B2_within_2se": abs(m3_mean - m3_null["p95"]) <= 2 * m3_null["q_boot_se"],
          "B3": all(v > 0 for v in loyo_m3.values())}
    M3["pass"] = bool(M3["B1"] and M3["B2"] and M3["B3"])

    # diagnostics, not bars (disclosed): where M1 and M3 come from. FX and index open interest carries a real,
    # mechanical drop at each quarterly expiry that the volatility-matched control does not align on.
    CLASS = {**{r: "index" for r in ("ES", "NQ", "YM", "NKD")}, **{r: "energy" for r in ("CL", "NG", "RB", "HO")},
             **{r: "metals" for r in ("GC", "SI", "PL", "HG")},
             **{r: "rates" for r in ("ZN", "ZB", "ZF", "ZT", "UB", "TN", "SR3")},
             **{r: "fx" for r in ("6E", "6J", "6B", "6A", "6C", "6S")},
             **{r: "grains" for r in ("ZC", "ZS", "ZW", "ZL", "ZM")}, "LE": "livestock", "HE": "livestock", "BTC": "crypto"}
    cls1 = E.loc[m1, "root"].map(CLASS).to_numpy()
    cls3 = E["root"].map(CLASS).to_numpy()[m3]
    era1 = np.where(E.loc[m1, "year"].to_numpy() <= 2017, "2010-2017", "2019-2023")
    era3 = np.where(E["year"].to_numpy()[m3] <= 2017, "2010-2017", "2019-2023")
    diag = {"M1_abnormal_by_class": {c: [round(float(abn[cls1 == c].mean()), 5), int((cls1 == c).sum())]
                                     for c in sorted(set(cls1))},
            "M1_abnormal_by_era": {e: [round(float(abn[era1 == e].mean()), 5), int((era1 == e).sum())] for e in sorted(set(era1))},
            "M1_abnormal_median": float(np.median(abn)),
            "M3_u_by_class": {c: [round(float(ue[m3][cls3 == c].mean()), 4), int((cls3 == c).sum())] for c in sorted(set(cls3))},
            "M3_u_by_era": {e: [round(float(ue[m3][era3 == e].mean()), 4), int((era3 == e).sum())] for e in sorted(set(era3))},
            "M3_rv_ratio_exp_u": float(np.exp(m3_mean)),
            "note": "diagnostics, not bars"}
    by_year = E.groupby("year").size().to_dict()
    out = {
        "decision_record": "docs/decisions/D657-STAGE-0-DESIGN-margin-hikes-forced-exit-and-reversion.md",
        "last_session_read": LAST, "events_merged": int(len(ev)), "events_scored": int(len(E)),
        "roots_scored": sorted(E["root"].unique().tolist()), "distinct_notice_dates": int(E["N"].nunique()),
        "notice_from_advisory": int((E["n_source"] == "advisory").sum()),
        "events_per_year": {int(k): int(v) for k, v in by_year.items()},
        "events_per_root": {k: int(v) for k, v in E.groupby("root").size().items()},
        "share_2020_2022": float(E["year"].isin([2020, 2022]).mean()),
        "control_pool_median": int(E["pool"].map(len).median()),
        "M1": M1, "M2": M2, "M3": M3, "diagnostics": diag,
        "guard_source_counts": GUARD_SOURCE,
        "wall_min": round((time.time() - t0) / 60, 1),
    }
    OUT.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8", newline="\n")
    P(json.dumps({k: out[k] for k in ("events_scored", "distinct_notice_dates", "events_per_year", "share_2020_2022")}))
    for name in ("M1", "M2", "M3"):
        P(name, {k: v for k, v in out[name].items() if not isinstance(v, dict)})
    return 0


# ================================================================== selftest
def selftest() -> int:
    bad = []

    def check(label, cond):
        print(("  ok   " if cond else "  FAIL ") + label)
        if not cond:
            bad.append(label)

    check("merging joins increases within 10 sessions and not beyond",
          merge_events([100, 105, 110, 121, 140, 150]) == [100, 121, 140] and merge_events([5, 16]) == [5, 16])
    # delivery guard: the nearest contract whose guard clears end + 10 is picked, a nearer one is refused
    p = np.array([[1.0, 2.0], [1.1, 2.1], [1.2, 2.2], [1.3, 2.3]] * 10)
    dl, gi = np.array([1, 2]), np.array([15, 60])
    check("pick_contract refuses a contract whose guard is within 10 sessions of the window end",
          pick_contract(p, dl, gi, [0, 3, 8], 8) == 1 and pick_contract(p, dl, gi, [0, 1, 4], 4) == 0)
    # control pool: excludes sessions within 20 of a change, matches the quintile and trend sign, covered only
    n = 400
    volq = np.tile(np.arange(5), n // 5).astype(float)
    tr = np.where(np.arange(n) % 2 == 0, 1.0, -1.0)
    cov = np.ones(n, bool)
    cov[300:] = False
    pool = control_pool(n, np.array([100]), cov, volq, tr, a=50, span=7)
    check("control pool: >= 20 sessions from a change, same quintile and sign, window covered",
          len(pool) > 0 and np.all(np.abs(pool - 100) >= 20) and np.all(volq[pool] == volq[50])
          and np.all(np.sign(tr[pool]) == np.sign(tr[50])) and np.all(pool + 7 < 300))
    # HAR forecast uses nothing on or after the quarter it forecasts (a planted future spike leaves it unchanged)
    rng = np.random.default_rng(1)
    cal = pd.bdate_range("2012-01-02", periods=900)
    rv = np.exp(rng.normal(-9, 0.5, 900))
    u1 = har_forecast_u(rv, cal, 3)
    rv2 = rv.copy()
    t = 700
    rv2[t + 1:] *= 50.0
    u2 = har_forecast_u(rv2, cal, 3)
    q = pd.PeriodIndex(cal, freq="Q")
    same_q = np.nonzero(q == q[t])[0]
    ok_rows = same_q[(same_q + 3 + RV_LEN - 1) <= t]           # rows whose target window ends by t
    check("HAR: a spike after t leaves every forecast made from coefficients fitted before t's quarter unchanged",
          np.allclose(u1[ok_rows], u2[ok_rows], equal_nan=True) and len(ok_rows) > 0)
    # the M2 regression recovers a planted beta and returns ~0 on a random walk
    xw = rng.normal(0, 1, 4000)
    yy = -0.3 * xw + rng.normal(0, 1, 4000)
    cl = np.repeat(np.arange(400), 10)
    b, tt = cluster_ols(yy, xw, cl)
    b0, _ = cluster_ols(rng.normal(0, 1, 4000), xw, cl)
    check("cluster_ols recovers a planted beta of -0.3 and ~0 on noise", abs(b + 0.3) < 0.05 and abs(b0) < 0.05 and tt < -10)
    # W and Y do not overlap and share the contract
    a, ie = 10, 12
    lW = ie + W_AFTER - a
    check("W ends where Y begins, on one contract", a + lW == ie + W_AFTER and ie + W_AFTER + Y_LEN > a + lW)
    # contract decades come from the code and the session, never from the (incomplete) definitions map
    probe = pd.DataFrame({"contract": ["SR3U2", "SR3U32", "ZFZ1", "CLF3", "GCG1", "GCG1", "ZBH0", "SR3U2"],
                          "ref_ts": pd.to_datetime(["2022-12-21", "2022-12-21", "2021-09-01", "2022-12-15",
                                                    "2011-01-10", "2021-01-10", "2020-03-25", "2012-06-01"])})
    want = [2022 * 12 + 9, 2032 * 12 + 9, 2021 * 12 + 12, 2023 * 12 + 1, 2011 * 12 + 2, 2021 * 12 + 2, 2020 * 12 + 3,
            2012 * 12 + 9]
    got = infer_dlv(probe).astype(int).tolist()
    check(f"infer_dlv: SOFR final settlement, a two-digit year, a recycled code and energy's early expiry {got}",
          got == want)
    # every root has definition expiries (D654's loader keeps 26 roots and would drop eight of these silently)
    exp = load_expiries()
    check("the expiry map covers all 33 roots",
          all(any(c.startswith(r) and d654.RE_C.match(c) and d654.RE_C.match(c).group(1) == r for c in exp) for r in ROOTS))
    # holdout guard
    try:
        assert_none_at_or_after(pd.DataFrame({"ref": ["2023-12-29", "2024-01-02"]}), "ref", RESERVED_FROM)
        check("the holdout guard raises on a 2024 settlement", False)
    except Exception:
        check("the holdout guard raises on a 2024 settlement", True)
    print("SELFTEST", "PASSED" if not bad else f"FAILED: {bad}")
    return 0 if not bad else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--extract-oi", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.extract_oi:
        extract_oi(a.workers)
        return 0
    if a.run:
        return run()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
