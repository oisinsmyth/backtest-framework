"""NG TAS imbalance per held TAS month and trade date: aggressor-signed trade-at-settlement volume from the session
open to each τ (settlement ledger deposit §P5, Stage D: TAS_imb[t, τ] = Σ aggressor-signed TAS volume from the
session open to τ, + = clients bought TAS).

It builds a panel and computes no statistic: no Q, no window flow, no price.

SPANS: from the session open (18:00 ET the evening before, dated to the next day) to 11:30, 13:50, 14:00, 14:10 and
14:30 ET. Per span: `v_to_HHMM` (outright TAS volume), `net_to_HHMM` (buyer-initiated − seller-initiated) and `n_to_HHMM`.

TWO SOURCES, one per era, both with the exchange's aggressor side:
  * trade dates ≤ 2020-02-10: Databento `trades` for NGT.FUT (bought 2026-09-26, job in
    `data/ledger_ngt_tas_gap_job.json`), outrights only, B − A; size cast to int64 (D624);
  * trade dates ≥ 2020-02-11: Sierra Chart's NGT files (`sierra_tas_download.py`), AskVolume − BidVolume. On the HO/RB
    siblings, Sierra's TAS net flow matches the exchange flag at r 0.9998–0.9999 (`check_sierra_tas_aggressor.py`).
    Sierra holds no NG TAS before 2020-02-10.
KNOWN ANSWER, the overlap day 2020-02-10: Sierra's file starts that morning, so from its first record to 14:30 the two
sources are compared per contract. They must agree exactly in volume and in net (raises otherwise).

THE VAULT IS NEVER DECODED: Sierra files are cut by binary search at 2025-02-28 18:00 ET, the open of the vault's
first session. Nothing from that record on is decoded, and a guard asserts that no trade date after 2025-02-28 survives.

Output: `data/ledger_tas_imbalance_daily.csv.gz` (gitignored by suffix) and `data/ledger_tas_imbalance_summary.json`.

    python scripts/build_tas_imbalance_panel.py [--check]      # SYSTEM interpreter (databento)
"""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import io
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))  # the system interpreter (databento) does not install the package
import build_signed_window_panel as B  # noqa: E402  (frozen: the record layout and the Sierra paths, imported)
import sierra_tas_download as T  # noqa: E402

GAP_JOB = REPO / "data" / "ledger_ngt_tas_gap_job.json"
RAW = REPO / "data" / "raw" / "databento"
OUT_ROWS = REPO / "data" / "ledger_tas_imbalance_daily.csv.gz"
OUT_SUM = REPO / "data" / "ledger_tas_imbalance_summary.json"
ET = "America/New_York"
FIRST, LAST = "2017-05-22", "2025-02-28"
SWITCH = "2020-02-11"  # the first trade date taken from Sierra Chart
TO = {"to_1130": "11:30:00", "to_1350": "13:50:00", "to_1400": "14:00:00", "to_1410": "14:10:00",
      "to_1430": "14:30:00"}
CUT_US = B._us(pd.Timestamp("2025-02-28 18:00", tz=ET).tz_convert("UTC"))


class TasPanelError(RuntimeError):
    pass


def _ym_loader() -> Any:
    spec = importlib.util.spec_from_file_location("bwv", REPO / "scripts" / "build_window_volume_panel.py")
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m._ym


def session_rows(et: pd.DatetimeIndex, v: np.ndarray, net: np.ndarray) -> pd.DataFrame:
    """Per trade date and span: the sums from the 18:00 open to each τ."""
    day = np.asarray((et + pd.Timedelta(hours=6)).strftime("%Y-%m-%d"))
    clock = np.asarray(et.strftime("%H:%M:%S"))
    evening = clock >= "18:00:00"
    frames = []
    for name, end in TO.items():
        m = evening | (clock < end)
        g = pd.DataFrame({"day": day[m], "v": v[m], "net": net[m], "n": 1}).groupby("day").sum()
        frames.append(g.add_suffix(f"_{name}"))
    return pd.concat(frames, axis=1).fillna(0).astype("int64")


def sierra_one(sym: str) -> pd.DataFrame:
    path = B.SC_DATA / f"{sym}-NYMEX.scid"
    if not path.exists() or path.stat().st_size <= 56:
        return pd.DataFrame()
    mm = np.memmap(path, dtype=B.REC, mode="r", offset=56)
    dt_all = mm["dt"]
    cut = int(np.searchsorted(dt_all, CUT_US, side="left"))
    dt = np.array(dt_all[:cut])
    if len(dt) and (dt.max() >= CUT_US or (np.diff(dt) < -1_000_000).any()):
        raise TasPanelError(f"{sym}: the decoded prefix reaches the cut or has an inversion of 1 s or more")
    if cut < len(dt_all) and int(np.min(dt_all[cut:cut + 100])) < CUT_US:
        raise TasPanelError(f"{sym}: a record after the cut index is before the cut")
    if not len(dt):
        return pd.DataFrame()
    sub = mm[:cut]
    et = (B.ORIGIN + pd.to_timedelta(dt, unit="us")).tz_convert(ET)
    av, bv = np.asarray(sub["av"], dtype=np.int64), np.asarray(sub["bv"], dtype=np.int64)
    rows = session_rows(pd.DatetimeIndex(et), np.asarray(sub["v"], dtype=np.int64), av - bv).reset_index()
    rows["symbol"], rows["first_et"] = sym, str(et[0])
    return rows


def databento_rows() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(rows per contract and trade date; the raw outright trades of 2020-02-10, for the known answer)."""
    import databento as db  # type: ignore[import-not-found]
    rec = json.loads(GAP_JOB.read_text(encoding="utf-8"))
    files = sorted((RAW / rec["job"]["id"]).glob("*.trades.dbn.zst"))
    df = pd.concat([db.DBNStore.from_file(f).to_df(map_symbols=True) for f in files])
    sym = df["symbol"].astype(str)
    df = df[~sym.str.contains("-")]  # outrights only: a spread's sign is not a single month's
    et = pd.DatetimeIndex(df.index).tz_convert(ET)
    size = df["size"].astype("int64").to_numpy()
    side = df["side"].astype(str).to_numpy()
    net = np.where(side == "B", size, np.where(side == "A", -size, 0))
    parts = []
    for s in sorted(df["symbol"].astype(str).unique()):
        m = (df["symbol"].astype(str) == s).to_numpy()
        r = session_rows(et[m], size[m], net[m]).reset_index()
        r["symbol"] = s
        parts.append(r)
    day = np.asarray((et + pd.Timedelta(hours=6)).strftime("%Y-%m-%d"))
    raw = pd.DataFrame({"symbol": df["symbol"].astype(str).to_numpy(), "et": et, "day": day, "size": size, "net": net})
    return pd.concat(parts, ignore_index=True), raw[raw["day"] == "2020-02-10"]


def build() -> tuple[bytes, str]:
    ym_of = _ym_loader()
    syms = T.ng_tas_list()
    sc = pd.concat([sierra_one(s) for s in syms], ignore_index=True)
    sc["source"] = "sierra"
    firsts = sc.groupby("symbol")["first_et"].first().to_dict()
    sc = sc.drop(columns="first_et")
    dbn, raw0210 = databento_rows()
    dbn["source"] = "databento"
    # the known answer on 2020-02-10: from each Sierra file's first record to 14:30, both sources, per contract
    ka: dict[str, Any] = {}
    for s in [x for x in syms if x in firsts and firsts[x][:10] <= "2020-02-10"]:
        start = pd.Timestamp(firsts[s])
        d_sym = s[:4] + s[-1]  # NGTH20 -> NGTH0
        r = raw0210[(raw0210["symbol"] == d_sym) & (raw0210["et"] >= start)
                    & (np.asarray(raw0210["et"].dt.strftime("%H:%M:%S")) < "14:30:00")]
        srow = sierra_one(s)
        srow = srow[srow["day"] == "2020-02-10"]
        mm = np.memmap(B.SC_DATA / f"{s}-NYMEX.scid", dtype=B.REC, mode="r", offset=56)
        et = (B.ORIGIN + pd.to_timedelta(np.asarray(mm["dt"]), unit="us")).tz_convert(ET)
        day = np.asarray((et + pd.Timedelta(hours=6)).strftime("%Y-%m-%d"))
        keep = (day == "2020-02-10") & (np.asarray(et.strftime("%H:%M:%S")) < "14:30:00")
        sv = int(np.asarray(mm["v"], dtype=np.int64)[keep].sum())
        sn = int((np.asarray(mm["av"], dtype=np.int64) - np.asarray(mm["bv"], dtype=np.int64))[keep].sum())
        ka[s] = {"sierra_first_et": firsts[s], "sierra_v": sv, "databento_v": int(r["size"].sum()),
                 "sierra_net": sn, "databento_net": int(r["net"].sum()), "sierra_rows_that_day": int(len(srow))}
    bad = {k: v for k, v in ka.items() if v["sierra_v"] != v["databento_v"] or v["sierra_net"] != v["databento_net"]}
    if not ka or bad:
        raise TasPanelError(f"the known answer on 2020-02-10 fails or is empty: {ka}")
    df = pd.concat([dbn[dbn["day"] < SWITCH], sc[sc["day"] >= SWITCH]], ignore_index=True)
    df = df[(df["day"] >= FIRST) & (df["day"] <= LAST)]
    if (df["day"] > LAST).any():
        raise TasPanelError("a trade date after 2025-02-28 survived")
    df["ym"] = [ym_of(s, d) for s, d in zip(df["symbol"], df["day"])]  # D526's rule, one- or two-digit years
    cols = ["day", "symbol", "ym", "source"] + [f"{k}_{s}" for s in TO for k in ("v", "net", "n")]
    df = df[cols].sort_values(["day", "ym"]).reset_index(drop=True)
    if df.duplicated(["day", "ym"]).any():
        raise TasPanelError("two rows for one (trade date, month)")
    buf = io.StringIO()
    df.to_csv(buf, index=False, lineterminator="\n", encoding="utf-8")
    summ = {"first": FIRST, "last": LAST, "switch_to_sierra": SWITCH, "spans_from_18:00_prior": TO,
            "rows": int(len(df)), "rows_by_source": {k: int(v) for k, v in df["source"].value_counts().items()},
            "trade_dates": int(df["day"].nunique()), "known_answer_2020_02_10": ka,
            "net_to_1430_sum_by_source": {k: int(g["net_to_1430"].sum()) for k, g in df.groupby("source")}}
    return gzip.compress(buf.getvalue().encode("utf-8"), mtime=0), json.dumps(summ, indent=1, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    gz, summ = build()
    if a.check:
        if OUT_ROWS.read_bytes() != gz or OUT_SUM.read_text(encoding="utf-8") != summ:
            raise TasPanelError("the panel does not reproduce")
        print("reproduces byte for byte")
        return 0
    OUT_ROWS.write_bytes(gz)
    OUT_SUM.write_text(summ, encoding="utf-8", newline="\n")
    s = json.loads(summ)
    print(json.dumps({k: s[k] for k in ("rows", "rows_by_source", "trade_dates", "known_answer_2020_02_10")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
