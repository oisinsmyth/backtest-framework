"""Known-answer check: does Sierra Chart's TAS (trade-at-settlement) tick data carry the exchange's aggressor side?
(2026-09-26; Stage D's input, deposit §P5: TAS_imb = aggressor-signed TAS volume from the session open to τ.)

THE TRUTH: Databento `trades` for HO and RB TAS (HOT.FUT, RBT.FUT; the free sibling pull
`data/ledger_sibling_tas_pull_jobs.json`, label siblings-tas-trades), with the side flag: B = buyer aggressor,
A = seller, N = none. Outrights only; size cast to int64 (D624). The sibling year is SEEN data and serves only as a
data-quality reference, as in `check_sierra_aggressor.py`. No NG or CL byte is read.

SIERRA: `C:\\SierraChart\\Data\\{HOT,RBT}<M><YY>-NYMEX.scid` (`sierra_tas_download.py`), read with
`check_sierra_aggressor.read_scid`: AskVolume is buyer-initiated and BidVolume seller-initiated.

PER (contract, trade date), for two spans of the CME session, from 18:00 ET the evening before:
    to 13:50 ET (the earliest decision time), and to 14:30 ET (W_end);
    net_sierra = Σ AskVolume − Σ BidVolume;   net_truth = Σ size[B] − Σ size[A]   (Databento on ts_recv)
REPORTED: the sessions compared (at least 20 contracts gross); Pearson r of the nets; sign agreement; the share of
sessions whose nets match exactly; the median ratio of Sierra's total volume to the truth's.
THE BAR (the principal's, 2026-09-24, as in the futures check): r ≥ 0.8 makes the signed TAS usable. r ≥ 0.99 with
sign agreement ≥ 0.98 is reported as "the exchange flag". It was declared before the first run.
D626's sessions (trade dates after 2026-09-18) are dropped before anything is summed, and a guard raises if one
survives.

    python scripts/check_sierra_tas_aggressor.py      # SYSTEM interpreter (databento)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import check_sierra_aggressor as K  # noqa: E402  (read_scid and the paths)

JOBS = REPO / "data" / "ledger_sibling_tas_pull_jobs.json"
OUT = REPO / "data" / "sierra_tas_aggressor_check.json"
ET = "America/New_York"
LAST_TRADE_DATE = "2026-09-18"
SPANS = {"to_1350": "13:50:00", "to_1430": "14:30:00"}
MIN_GROSS = 20
MONTHS = ["X25", "Z25", "F26", "G26", "H26", "J26", "K26", "M26", "N26", "Q26", "U26", "V26"]


def trade_date_and_clock(et: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
    """The CME session runs 18:00 ET the evening before → 17:00 ET, dated to the next day."""
    shifted = et + pd.Timedelta(hours=6)
    return np.asarray(shifted.strftime("%Y-%m-%d")), np.asarray(et.strftime("%H:%M:%S"))


def spans(day: np.ndarray, clock: np.ndarray, evening: np.ndarray) -> dict[str, np.ndarray]:
    return {name: evening | (clock < end) for name, end in SPANS.items()}


def sierra(contracts: list[str]) -> pd.DataFrame:
    rows = []
    for c in contracts:
        p = K.SC_DATA / f"{c}-NYMEX.scid"
        if not p.exists() or p.stat().st_size <= 56:
            continue
        df = K.read_scid(p)
        et = pd.DatetimeIndex(df["et"])
        day, clock = trade_date_and_clock(et)
        keep = day <= LAST_TRADE_DATE
        df, day, clock = df[keep], day[keep], clock[keep]
        if (day > LAST_TRADE_DATE).any():
            raise RuntimeError("a TAS row after 2026-09-18 survived the guard")
        evening = clock >= "18:00:00"
        for name, m in spans(day, clock, evening).items():
            g = pd.DataFrame({"day": day[m], "v": df["v"].to_numpy()[m],
                              "net": (df["av"] - df["bv"]).to_numpy()[m]}).groupby("day").sum()
            for d, x in g.iterrows():
                rows.append({"contract": c, "day": d, "span": name, "sc_total": int(x["v"]), "sc_net": int(x["net"])})
    return pd.DataFrame(rows)


def truth(contracts: list[str]) -> pd.DataFrame:
    import databento as db  # type: ignore[import-not-found]
    rec = json.loads(JOBS.read_text(encoding="utf-8"))
    job = next(j for j in rec["jobs"] if j["label"] == "siblings-tas-trades")
    files = sorted((K.RAW / job["job"]["id"]).glob("*.dbn.zst"))
    to_sc = {c[:4] + c[-1]: c for c in contracts}  # Databento HOTZ5 -> Sierra HOTZ25
    parts = []
    for f in files:
        df = db.DBNStore.from_file(f).to_df(map_symbols=True)
        df = df[df["symbol"].astype(str).isin(set(to_sc))]
        ts = df["ts_recv"] if "ts_recv" in df.columns else df.index.to_series()  # to_df indexes on ts_recv
        et = pd.DatetimeIndex(ts).tz_convert(ET)
        day, clock = trade_date_and_clock(et)
        keep = day <= LAST_TRADE_DATE
        df, day, clock = df[keep], day[keep], clock[keep]
        size = df["size"].astype("int64").to_numpy()
        side = df["side"].astype(str).to_numpy()
        signed = np.where(side == "B", size, np.where(side == "A", -size, 0))
        evening = clock >= "18:00:00"
        for name, m in spans(day, clock, evening).items():
            parts.append(pd.DataFrame({"contract": df["symbol"].astype(str).map(to_sc).to_numpy()[m], "day": day[m],
                                       "span": name, "size": size[m], "signed": signed[m], "none": (side == "N")[m] * size[m]}))
    t = pd.concat(parts)
    return t.groupby(["contract", "day", "span"]).agg(tr_total=("size", "sum"), tr_net=("signed", "sum"),
                                                        tr_none=("none", "sum")).reset_index()


def compare(sc: pd.DataFrame, tr: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    m_all = sc.merge(tr, on=["contract", "day", "span"], how="inner")
    for (span, root), m in m_all.groupby(["span", m_all["contract"].str[:2]]):
        m = m[m["tr_total"] >= MIN_GROSS]
        r = float(np.corrcoef(m["sc_net"], m["tr_net"])[0, 1])
        sign = float((np.sign(m["sc_net"]) == np.sign(m["tr_net"])).mean())
        out[f"{root}_{span}"] = {
            "sessions": int(len(m)), "r_net": round(r, 4), "sign_agreement": round(sign, 4),
            "exact_net_share": round(float((m["sc_net"] == m["tr_net"]).mean()), 4),
            "total_ratio_median": round(float((m["sc_total"] / m["tr_total"]).median()), 4),
            "no_aggressor_share_of_truth_volume": round(float(m["tr_none"].sum() / m["tr_total"].sum()), 5),
            "usable_r_ge_0.8": bool(len(m) >= 50 and r >= 0.8),
            "exchange_flag_r_ge_0.99": bool(len(m) >= 50 and r >= 0.99 and sign >= 0.98)}
    return out


def main() -> int:
    contracts = [f"{r}T{m}" for r in ("HO", "RB") for m in MONTHS]
    sc, tr = sierra(contracts), truth(contracts)
    res = {"contracts": contracts, "spans_et_from_18:00_prior": SPANS, "min_gross": MIN_GROSS,
           "last_trade_date": LAST_TRADE_DATE, "sierra_contracts_with_data": sorted(sc["contract"].unique().tolist()),
           "comparison": compare(sc, tr)}
    OUT.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(res["comparison"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
