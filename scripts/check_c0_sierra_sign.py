"""D635 §7: is Sierra Chart's signing of settlement-window flow the exchange's, root by root? Run with the SYSTEM
python (databento).

For every post-vault session (from 2026-09-19) and every sign-check contract (`sierra_index_reweight_download.
signcheck_list()`), this compares the Sierra-signed net aggressor volume in the root's settlement window (AskVolume -
BidVolume) with Databento's exchange-flagged net (side B = buyer aggressor, +size; A = seller, -size; N = none, 0).
The window is `settlement_windows.window_for` (the current_only rows, served from 2026-09-21).

A root is kept for C0 when it has >= 10 sessions and r(net_sierra, net_exchange) >= 0.8 over its (contract, session)
pairs with >= 5 contracts of exchange window volume; below that it is VOID for C0. The result is merged per root into
data/index_reweight/c0_signcheck.json, which run_gate_c0.py requires.

CL, NG, HO and RB sessions from 2026-09-19 are D626's sample: `--group energy` refuses before 2026-10-11 (after its one
read on 2026-10-10).

    python scripts/check_c0_sierra_sign.py --group nonenergy
    python scripts/check_c0_sierra_sign.py --group energy          # from 2026-10-11 only
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import settlement_windows as SW  # noqa: E402
import sierra_index_reweight_download as D  # noqa: E402

OUT = REPO / "data" / "index_reweight" / "c0_signcheck.json"
RAW = REPO / "data" / "raw" / "databento"
FIRST = "2026-09-19"
ENERGY = ("CL", "NG", "HO", "RB")
ENERGY_FROM = dt.date(2026, 10, 11)
MIN_SESSIONS, R_BAR, MIN_VOL = 10, 0.8, 5
ORIGIN = pd.Timestamp("1899-12-30", tz="UTC")


def jobs() -> list[Path]:
    out = []
    for rec in sorted((REPO / "data" / "index_reweight").glob("signcheck_jobs_*.json")):
        for j in json.loads(rec.read_text(encoding="utf-8"))["jobs"]:
            out.extend(sorted((RAW / j["job"]["id"]).glob("*.trades.dbn.zst")))
    return out


def window_utc(root: str, day: str) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    try:
        w = SW.window_for(root, day)
    except (SW.UnmappedProduct, SW.UnsourcedDate):
        return None
    a = pd.Timestamp(f"{day} {w.start_ct}", tz="America/Chicago").tz_convert("UTC")
    b = pd.Timestamp(f"{day} {w.end_ct}", tz="America/Chicago").tz_convert("UTC")
    return a, b


def exchange(roots: set[str], syms: list[str]) -> pd.DataFrame:
    import databento as db  # type: ignore[import-not-found]
    to_sc = {s[:2] + s[2] + s[4]: s for s in syms}  # Databento CLX6 -> Sierra CLX26-NYMEX
    rows = []
    for f in jobs():
        df = db.DBNStore.from_file(f).to_df(map_symbols=True)
        df = df[df["symbol"].astype(str).isin(set(to_sc)) & df["symbol"].astype(str).str[:2].isin(roots)]
        if df.empty:
            continue
        ts = pd.DatetimeIndex(df["ts_recv"] if "ts_recv" in df.columns else df.index)
        size = df["size"].astype("int64").to_numpy()
        side = df["side"].astype(str).to_numpy()
        signed = np.where(side == "B", size, np.where(side == "A", -size, 0))
        sym = df["symbol"].astype(str).map(to_sc).to_numpy()
        day = ts.tz_convert("America/New_York").strftime("%Y-%m-%d").to_numpy()
        frame = pd.DataFrame({"sym": sym, "day": day, "ts": ts, "size": size, "signed": signed})
        for (s, d), g in frame.groupby(["sym", "day"]):
            if d < FIRST:
                continue
            w = window_utc(s[:2], d)
            if w is None:
                continue
            m = (g["ts"] >= w[0]) & (g["ts"] < w[1])
            rows.append((s, d, int(g.loc[m, "signed"].sum()), int(g.loc[m, "size"].sum())))
    return pd.DataFrame(rows, columns=["sym", "day", "ex_net", "ex_vol"])


def sierra(pairs: pd.DataFrame) -> pd.DataFrame:
    out = []
    for s, g in pairs.groupby("sym"):
        p = D.SC_DATA / f"{s}.scid"
        a = np.memmap(p, dtype=np.dtype([("t", "<i8"), ("o", "<f4"), ("h", "<f4"), ("l", "<f4"), ("c", "<f4"),
                                         ("n", "<u4"), ("v", "<u4"), ("bv", "<u4"), ("av", "<u4")]),
                      mode="r", offset=D.HDR)
        for d in g["day"]:
            w = window_utc(s[:2], d)
            assert w is not None
            i, j = np.searchsorted(a["t"], [int((w[0] - ORIGIN) / pd.Timedelta(microseconds=1)),
                                            int((w[1] - ORIGIN) / pd.Timedelta(microseconds=1))])
            net = int((a["av"][i:j].astype(np.int64) - a["bv"][i:j].astype(np.int64)).sum())
            out.append((s, d, net, int(a["v"][i:j].astype(np.int64).sum())))
    return pd.DataFrame(out, columns=["sym", "day", "sc_net", "sc_vol"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", choices=["nonenergy", "energy"], required=True)
    a = ap.parse_args()
    if a.group == "energy" and dt.date.today() < ENERGY_FROM:
        raise SystemExit(f"REFUSING: CL/NG/HO/RB post-vault sessions are D626's sample until {ENERGY_FROM}")
    roots = set(ENERGY) if a.group == "energy" else {D.ROOTS[c][0] for c in D.ROOTS} - set(ENERGY)
    syms = [s for s in D.signcheck_list() if s[:2] in roots]
    ex = exchange(roots, syms)
    ex = ex[ex["ex_vol"] >= MIN_VOL]
    sc = sierra(ex[["sym", "day"]])
    m = ex.merge(sc, on=["sym", "day"])
    rec: dict[str, Any] = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"roots": {}}
    for root in sorted(roots):
        g = m[m["sym"].str[:2] == root]
        n_sess = int(g["day"].nunique())
        r = float(np.corrcoef(g["sc_net"], g["ex_net"])[0, 1]) if len(g) >= 3 else float("nan")
        rec["roots"][root] = {
            "pairs": int(len(g)), "sessions": n_sess, "first": str(g["day"].min()) if len(g) else None,
            "last": str(g["day"].max()) if len(g) else None, "r_net": round(r, 4),
            "sign_agreement": round(float((np.sign(g["sc_net"]) == np.sign(g["ex_net"])).mean()), 4) if len(g) else None,
            "volume_ratio_median": round(float((g["sc_vol"] / g["ex_vol"]).median()), 4) if len(g) else None,
            "enough_sessions": n_sess >= MIN_SESSIONS,
            "pass": bool(n_sess >= MIN_SESSIONS and r >= R_BAR), "checked_utc": dt.datetime.now(dt.timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ")}
        print(root, rec["roots"][root], flush=True)
    rec["rule"] = f">= {MIN_SESSIONS} sessions and r >= {R_BAR} over (contract, session) pairs with >= {MIN_VOL} lots"
    OUT.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
