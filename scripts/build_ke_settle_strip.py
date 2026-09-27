"""KE (KC HRW wheat) settlements for the index-reweight model (D634 §2; IR-A8), in `fut_settle_strip`'s schema:
root, contract, ref, settle. Run with the SYSTEM python (databento).

Source: the free Databento pull `fetch_index_reweight_ke.py` (statistics GLBX-20260926-Y9WW9HBUST, definitions
GLBX-20260926-84RXQWTRMA). The conventions are the strip's (D526/D556):
- stat_type 3 is the settlement, price x 1e-9;
- UNDEF and exact zero are missing markers and are dropped;
- a settlement is labelled with ts_ref + 1 day in US/Eastern.
Ids are mapped WINDOWED (D520/D521): a record at time t takes the raw_symbol of the definition with the same
instrument_id whose [activation, expiration] contains t. An id with two live definitions at t raises.
Outright contracts only (KE + month letter + one year digit).

The vault cut (IR-A1): records with ts_ref on or after 2025-03-01 are dropped from the raw arrays before any
DataFrame is built, and the output is asserted to hold no ref on or after 2025-03-01. The 2026 file is never opened.

Known answer: the settlements equal Sierra Chart's daily Close for KEH20 and KEZ18 (IR-A13 showed that Close is the
exchange settlement), exactly on every common day. This raises otherwise.

    python scripts/build_ke_settle_strip.py
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
STATS = REPO / "data" / "raw" / "databento" / "GLBX-20260926-Y9WW9HBUST"
DEFS = REPO / "data" / "raw" / "databento" / "GLBX-20260926-84RXQWTRMA"
OUT = REPO / "data" / "index_reweight" / "ke_settle_strip.csv.gz"
SC_DATA = Path(r"C:\SierraChart\Data")
CUT = "2025-03-01"
YEARS = range(2014, 2026)  # the 2025 file is cut at CUT; 2026 is never opened
ST_SETTLE, PX = 3, 1e-9
UNDEF = np.iinfo(np.int64).max
RE_OUT = re.compile(r"^KE[FGHJKMNQUVXZ]\d$")
CUT_NS = int(pd.Timestamp(CUT, tz="US/Eastern").tz_convert("UTC").value) - 86_400 * 10**9  # ref = ts_ref + 1 day


def definitions() -> pd.DataFrame:
    import databento as db
    rows = []
    for y in YEARS:
        a = db.DBNStore.from_file(DEFS / f"glbx-mdp3-{y}0101-{y}1231.definition.dbn.zst").to_ndarray()
        sym = np.char.decode(a["raw_symbol"].astype("S"), "ascii")
        keep = np.array([bool(RE_OUT.match(s)) for s in sym])
        rows.append(pd.DataFrame({"id": a["instrument_id"][keep].astype(np.int64), "contract": sym[keep],
                                  "act": a["activation"][keep].astype(np.int64),
                                  "exp": a["expiration"][keep].astype(np.int64)}))
    d = pd.concat(rows).drop_duplicates()
    if d.groupby(["id", "act", "exp"])["contract"].nunique().max() > 1:
        raise RuntimeError("one (id, window) carries two contracts")
    return d.reset_index(drop=True)


def settlements(defs: pd.DataFrame) -> pd.DataFrame:
    import databento as db
    ids = set(defs["id"])
    out = []
    for y in YEARS:
        a = db.DBNStore.from_file(STATS / f"glbx-mdp3-{y}0101-{y}1231.statistics.dbn.zst").to_ndarray()
        a = a[(a["stat_type"] == ST_SETTLE) & np.isin(a["instrument_id"], list(ids))]
        ts = a["ts_ref"].astype(np.int64)
        px = a["price"].astype(np.int64)
        ok = (px != UNDEF) & (px != 0) & (ts < CUT_NS)  # the vault cut, before any frame is built
        out.append(pd.DataFrame({"id": a["instrument_id"][ok].astype(np.int64), "ts": ts[ok],
                                 "recv": a["ts_recv"][ok].astype(np.int64), "settle": px[ok] * PX}))
    s = pd.concat(out, ignore_index=True)
    m = s.merge(defs, on="id")
    day = 86_400 * 10**9
    m = m[(m["ts"] >= m["act"] - day) & (m["ts"] <= m["exp"] + day)]
    # an id re-published with a revised window maps twice to the SAME contract: harmless, deduplicated. Two
    # different contracts for one record raise.
    m = m.drop_duplicates(["id", "ts", "settle", "contract"])
    if m.groupby(["id", "ts"])["contract"].nunique().max() > 1:
        raise RuntimeError("a record maps to two different contracts")
    ref = pd.to_datetime(m["ts"], utc=True).dt.tz_convert("US/Eastern") + pd.Timedelta(days=1)
    # the last publication of a session's settlement is the final one: order by receipt time
    m = m.assign(root="KE", ref=ref.dt.strftime("%Y-%m-%d")).sort_values("recv", kind="stable")
    d = m[["root", "contract", "ref", "settle"]].drop_duplicates(["root", "contract", "ref"], keep="last")
    d = d[pd.to_datetime(d["ref"]).dt.dayofweek < 5].sort_values(["ref", "contract"]).reset_index(drop=True)
    if (d["ref"] >= CUT).any():
        raise RuntimeError("a KE settlement on or after the vault cut survived")
    return d


def known_answer(d: pd.DataFrame) -> dict[str, int]:
    res = {}
    for sym, con in (("KEH20-CBOT", "KEH0"), ("KEZ18-CBOT", "KEZ8")):
        p = SC_DATA / f"{sym}.dly"
        if not p.exists():
            raise RuntimeError(f"known answer needs {p}")
        s = pd.read_csv(p, skipinitialspace=True, encoding="utf-8")
        s.columns = [c.strip() for c in s.columns]
        s["ref"] = pd.to_datetime(s["Date"]).dt.strftime("%Y-%m-%d")
        m = s.merge(d[d["contract"] == con], on="ref")
        bad = int(((m["Close"] - m["settle"]).abs() > 1e-6).sum())
        if len(m) < 100 or bad:
            raise RuntimeError(f"known answer failed on {sym}: {len(m)} common days, {bad} differ")
        res[sym] = int(len(m))
    return res


def main() -> int:
    defs = definitions()
    d = settlements(defs)
    ka = known_answer(d)
    d.to_csv(OUT, index=False, encoding="utf-8", lineterminator="\n", compression={"method": "gzip", "mtime": 0})
    print(f"KE: {len(d)} settlements, {d['contract'].nunique()} contracts, {d['ref'].min()} -> {d['ref'].max()}; "
          f"known answer exact on {ka}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
