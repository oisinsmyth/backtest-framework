"""The opening agent-state model's Phase 1 bars: ES and NQ at one minute over each TRADING SESSION's whole Globex span
(the prior evening from 18:00 ET through 16:59 ET), on that session's front contract, from the CME ohlcv-1m archive
(OPENING_AGENT_STATE_PREREG.md s.3, Gate O0; OA-A1).

    python scripts/build_fut_opening_1m.py --selftest
    python scripts/build_fut_opening_1m.py --build [--workers 6] [--data-root DIR]     # SYSTEM interpreter (databento)

WHY A NEW FIXTURE. D462's `fut_{ES,NQ}_rth_1m` holds 09:30-15:59 only, and `fut_day1m` 09:00-15:59. The deposit needs
08:00-16:00 coverage (Gate O0), the overnight high and low (A1), 08:29 -> 09:25 (A5) and the prior RTH extremes.

CONVENTIONS.
- `ts_event` is the bar START, converted to US/Eastern with DST (as D462).
- **Session:** a bar at or after 18:00 ET on calendar date D belongs to the first D462 session day after D (so
  Sunday evening feeds Monday, and a Friday-evening bar cannot exist). A bar before 18:00 ET belongs to D when D is
  a D462 session day, and is dropped otherwise. 17:00-17:59 has no trading.
- **Contract:** every bar of a session is the session's FRONT contract as D462's `fut_index_sessions` names it
  (the highest full-day volume on that calendar day, D448). So the evening before a roll day already carries the new
  front, which trades then. No stitching, no adjustment.
- Contract labels come from D462's WINDOWED id table (`ids_of`, `label_rows`; D520), never a flat id map.
- **Sessions written:** 2015-09-01 -> 2025-02-28 (a warm-up for the 250-session standardisation and ATR20 before
  2016-01-04, then the in-sample). The vault (2025-03-01 onward) is not written (OA-A1); `--through` extends it for
  the joint vault run only.

INPUTS read from `--data-root` (default this checkout's `data/`; a worktree passes the main checkout's, where the
gitignored archive and D462's session table live): `raw/databento/*/*.ohlcv-1m.dbn.zst` and
`fixtures/fut_index_sessions.csv.gz`. OUTPUT (this checkout): `data/fixtures/fut_opening_globex_1m.csv.gz` and its
`.meta.json`.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures"
OUT = FIX / "fut_opening_globex_1m.csv.gz"
META = FIX / "fut_opening_globex_1m.meta.json"
ROOTS = ("ES", "NQ")
START, THROUGH = "2015-09-01", "2025-02-28"
EVENING = "18:00"
PX = 1e-9
CHUNK = 10_000_000

_s = importlib.util.spec_from_file_location("build_fut_index_1m", REPO / "scripts" / "build_fut_index_1m.py")
assert _s is not None and _s.loader is not None
D462 = importlib.util.module_from_spec(_s)
sys.modules["build_fut_index_1m"] = D462
_s.loader.exec_module(D462)


def session_of(day: np.ndarray, hhmm: np.ndarray, sessions: np.ndarray) -> np.ndarray:
    """Each bar's trading session ('' when it has none). `sessions` is sorted."""
    out = np.full(len(day), "", dtype=object)
    eve = hhmm >= EVENING
    if eve.any():
        i = np.searchsorted(sessions, day[eve], side="right")
        ok = i < len(sessions)
        v = np.full(int(eve.sum()), "", dtype=object)
        v[ok] = sessions[i[ok]]
        out[eve] = v
    day_part = ~eve
    if day_part.any():
        member = np.isin(day[day_part], sessions)
        v = np.where(member, day[day_part], "")
        out[day_part] = v
    return out


def process_chunk(arr: np.ndarray, w: pd.DataFrame | None, sessions: np.ndarray, front: pd.DataFrame,
                  roots: tuple[str, ...] = ROOTS) -> pd.DataFrame | None:
    if w is None or len(w) == 0:
        return None
    w = w[w["root"].isin(roots)]
    if len(w) == 0:
        return None
    j = D462.label_rows(arr, w).sort_values("_i")
    if len(j) == 0:
        return None
    a = arr[j["_i"].to_numpy()]
    ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern")
    day = np.asarray(ts.strftime("%Y-%m-%d"))
    hhmm = np.asarray(ts.strftime("%H:%M"))
    sess = session_of(day, hhmm, sessions)
    root, contract = j["root"].to_numpy(), j["contract"].to_numpy()
    k = pd.DataFrame({"root": root, "session": sess}).merge(front, on=["root", "session"], how="left")
    keep = (k["front"].to_numpy() == contract) & (sess != "")
    if not keep.any():
        return None
    return pd.DataFrame({"root": root[keep], "session": sess[keep], "et": np.asarray(ts.strftime("%Y-%m-%d %H:%M"))[keep],
                         "hhmm": hhmm[keep], "contract": contract[keep],
                         "open": a["open"][keep] * PX, "high": a["high"][keep] * PX, "low": a["low"][keep] * PX,
                         "close": a["close"][keep] * PX, "volume": a["volume"][keep].astype(np.int64)})


_CTX: dict = {}


def _init(sessions: np.ndarray, front: pd.DataFrame, roots: tuple[str, ...] = ROOTS, breadth: bool = False) -> None:
    _CTX["sessions"], _CTX["front"], _CTX["roots"], _CTX["breadth"] = sessions, front, roots, breadth
    if breadth:
        sys.path.insert(0, str(REPO / "scripts"))


def worker(path: str) -> dict:
    import databento as db
    t0 = time.time()
    store = db.DBNStore.from_file(path)
    if _CTX.get("breadth"):  # D674: non-index roots take the breadth builder's windowed id table (all 36 roots)
        import build_fut_breadth_hourly as BH
        w = BH.ids_of(store)
    else:
        w = D462.ids_of(store)
    parts, n_in = [], 0
    for arr in store.to_ndarray(count=CHUNK):
        n_in += len(arr)
        b = process_chunk(arr, w, _CTX["sessions"], _CTX["front"], _CTX.get("roots", ROOTS))
        if b is not None:
            parts.append(b)
    bars = pd.concat(parts, ignore_index=True) if parts else None
    return {"file": Path(path).name, "rows_in": n_in, "rows_kept": 0 if bars is None else len(bars),
            "secs": round(time.time() - t0, 1), "bars": bars}


def load_front(data_root: Path, through: str, roots: tuple[str, ...] = ROOTS, breadth: bool = False) -> tuple[np.ndarray, pd.DataFrame]:
    if breadth:  # D674: the breadth fixture's front (the election every later futures fixture inherits); its
        # placeholder rows (Sundays, holidays with no bars) are not sessions
        s = pd.read_csv(data_root / "fixtures" / "fut_breadth_hourly.csv.gz", encoding="utf-8", dtype={"day": str},
                        usecols=["root", "day", "contract", "bars"])
        s = s[s["root"].isin(roots) & (s["bars"].fillna(0) > 0) & (s["day"] >= START) & (s["day"] <= through)]
    else:
        s = pd.read_csv(data_root / "fixtures" / "fut_index_sessions.csv.gz", encoding="utf-8", dtype={"day": str})
        s = s[s["root"].isin(roots) & (s["day"] >= START) & (s["day"] <= through)]
    sessions = np.array(sorted(s["day"].unique()), dtype=object)
    front = s[["root", "day", "contract"]].rename(columns={"day": "session", "contract": "front"})
    if front.duplicated(["root", "session"]).any():
        raise SystemExit("two fronts for one (root, session)")
    return sessions, front.reset_index(drop=True)


def cmd_build(workers: int, data_root: Path, through: str, roots: tuple[str, ...] = ROOTS, breadth: bool = False) -> int:
    global OUT, META
    if roots != ROOTS:  # D673/D674: other roots go to their own fixture; ES/NQ's is untouched
        tag = "_".join(r.lower() for r in roots)
        OUT, META = FIX / f"fut_opening_globex_1m_{tag}.csv.gz", FIX / f"fut_opening_globex_1m_{tag}.meta.json"
    t0 = time.time()
    files = sorted((data_root / "raw" / "databento").glob("*/*.ohlcv-1m.dbn.zst"), key=lambda p: p.name)
    assert files, "no ohlcv-1m files"
    sessions, front = load_front(data_root, through, roots, breadth)
    print(f"{len(files)} ohlcv-1m files, {len(sessions)} sessions {sessions[0]} .. {sessions[-1]}, {workers} workers",
          flush=True)
    order = {f.name: i for i, f in enumerate(files)}
    from multiprocessing import Pool
    with Pool(workers, initializer=_init, initargs=(sessions, front, roots, breadth)) as pool:
        res = pool.map(worker, [str(f) for f in sorted(files, key=lambda p: -p.stat().st_size)], chunksize=1)
    res.sort(key=lambda r: order[r["file"]])
    sec = sum(r["secs"] for r in res)
    wall = time.time() - t0
    print(f"[SPEED] sum(item time)/wall = {sec / wall:.2f}x on {workers} workers ({100 * sec / wall / workers:.0f}%)",
          flush=True)
    bars = pd.concat([r["bars"] for r in res if r["bars"] is not None], ignore_index=True)
    n0 = len(bars)
    bars = bars.sort_values(["root", "session", "et"], kind="stable").drop_duplicates(["root", "session", "et"])
    if (bars["session"] > through).any():
        raise SystemExit("a session past the cut reached the fixture")
    FIX.mkdir(parents=True, exist_ok=True)
    # D676: %.2f rounded NG (tick 0.001) and SI (0.005); caught by D676's identity gate. Index fixtures keep %.2f.
    ffmt = "%.5f" if breadth else "%.2f"
    bars.to_csv(OUT, index=False, compression={"method": "gzip", "mtime": 0}, float_format=ffmt, encoding="utf-8",
                lineterminator="\n")
    meta = {"spec": "OPENING_AGENT_STATE_PREREG.md s.3 / Gate O0; OA-A1", "built_utc": time.strftime(
        "%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "sessions": [START, through], "roots": list(roots),
        "session_rule": "bar >= 18:00 ET -> next D462 session day; else its own day if a session day",
        "contract_rule": "the session's front per D462 fut_index_sessions (highest full-day volume)",
        "float_format": ffmt, "rows": int(len(bars)), "duplicates_dropped": int(n0 - len(bars)),
        "files": [{k: v for k, v in r.items() if k != "bars"} for r in res], "gates": None}
    META.write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    for r in roots:
        b = bars[bars["root"] == r]
        print(f"  {r}: {len(b):,} bars over {b['session'].nunique():,} sessions", flush=True)
    print(f"wrote {OUT.name} in {(time.time() - t0) / 60:.1f} min", flush=True)
    return 0


def selftest() -> int:
    s = np.array(["2019-03-08", "2019-03-11", "2019-03-12"], dtype=object)  # Fri, Mon, Tue (DST starts Sun 03-10)
    day = np.array(["2019-03-08", "2019-03-08", "2019-03-10", "2019-03-11", "2019-03-11", "2019-03-09"], dtype=object)
    hhmm = np.array(["09:30", "18:00", "18:00", "08:00", "18:01", "10:00"], dtype=object)
    got = session_of(day, hhmm, s).tolist()
    assert got == ["2019-03-08", "2019-03-11", "2019-03-11", "2019-03-11", "2019-03-12", ""], got
    ts = pd.to_datetime(["2019-03-11 13:30:00", "2019-03-08 14:30:00"], utc=True).tz_convert("US/Eastern")
    assert list(ts.strftime("%H:%M")) == ["09:30", "09:30"], "DST: 09:30 ET is 13:30 UTC in summer time, 14:30 in winter"
    print("selftest: session mapping (evening -> next session, weekend, non-session day) and DST pass")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    ap.add_argument("--through", default=THROUGH, help="last session written (the vault only in the joint run)")
    ap.add_argument("--roots", default=",".join(ROOTS), help="D673: YM,RTY (written to their own fixture)")
    ap.add_argument("--breadth", action="store_true",
                    help="D674: non-index roots (e.g. GC,SI): the breadth builder's id table and front election")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.build:
        return cmd_build(a.workers, a.data_root, a.through, tuple(a.roots.split(",")), a.breadth)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
