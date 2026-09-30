"""The joint vault run's D680 line (programme slot 9, the NQ compression break): its vault INPUTS and the cut wrapper.
Prepared 2026-09-30 before the Databento CME subscription lapses; the vault is never opened here.

    python scripts/joint_d680_vault.py --prove fixture               # SYSTEM python (databento): D644 on in-sample DBN
    uv run python scripts/joint_d680_vault.py --prove inputs         # G0 + writer + the frozen book(), in-sample only
    uv run python scripts/joint_d680_vault.py --selftest             # synthetic only
    python scripts/joint_d680_vault.py --build-vault fixture --principals-word "..."        # the joint run ONLY
    uv run python scripts/joint_d680_vault.py --build-vault inputs --principals-word "..."  # the joint run ONLY
    uv run python scripts/joint_d680_vault.py --run-vault --principals-word "..."           # the joint run ONLY

WHY. D680's frozen `--vault` (scripts/vault_d680_nq_compression.py) needs two files nobody had built, and even fed them
it would score ZERO vault trades: its `book()` builds the frame with D663's `root_frame`, which keeps only sessions
before the module constant `stage0_d663_per_root_gamma_break.RESERVED_FROM` = 2025-03-01. The frozen files are not
edited. The principal's decision (2026-09-30, "go with your full recommendation"): a JOINT-RUN WRAPPER that holds
T.RESERVED_FROM at 2026-09-19 for the duration of the frozen runner's own call and restores it whatever happens (the
mechanism of D698's `raised_cut`). The audit of the frozen `--vault` path found that constant and no other: D668's,
run_opening_v2's, run_opening_stages' and G0's RESERVED_FROM are read only by the in-sample loaders, which `--vault`
does not call (it reads the two files below); `stage0_d671`/`stage0_d666` hold no cut of their own. The synthetic
rehearsal in `--selftest` (and again on the vault files' own layout in `--run-vault`, before the frozen call) proves
that nothing else in `book()` drops a session after 2025-03-01.

THE INPUT PATH (D680's prerequisite; AITODO): D644's fixture builder (`build_fut_opening_1m`: `load_front`,
`process_chunk`, D462's `ids_of`, all imported UNCHANGED) built through 2026-09-18 into a SEPARATE file, then G0's
loader (`opening_gate0.usable_sessions`, `.load_bars`, UNCHANGED) with its cut and its bar path moved, written out as
the `--vault-bars` CSV and the `--vault-use` JSON the frozen runner reads. Only the cut and the output paths move.
The orchestration around `process_chunk` mirrors D644's `cmd_build` line for line (file order, stable sort,
de-duplication, the same `to_csv`), because D644's own worker reads each DBN file whole: this one restricts every
record AT READ TIME on its `ts_event` field alone (every other field of a record at or past the cut is never read) and
skips any file whose header starts at or past the cut. Every other input is restricted as TEXT before a value is
parsed: `fut_index_sessions` (it carries prices and volumes) by its day field, SPY's daily file by its date KEYS only
(G0 reads nothing else from it), DIX by its date field. The session calendar carries no price and is copied.

THE SEALS. The vault (2025-03-01 -> 2026-09-18) for every root; and ES/NQ prices from 2024-01-01 are D716's unseen
span (NQ F2, slot 7). So the in-sample proofs here use ES/NQ sessions before 2024-01-01 ONLY, and D680's full known
answer (387 C1 trades, +6.93 / +7.56 bp; its window runs to 2025-02-28) cannot be reproduced before the joint run:
the frozen `--vault` re-proves it itself, on the built files' in-sample part, before it scores anything. What is
proved here instead: D644's rebuild reproduces the committed fixture's rows byte for byte on 2015-09-01 -> 2023-12-29;
G0 + the writer reproduce that text byte for byte and the frozen in-sample loader's frame exactly; the usable
sessions reproduce gate0.json exactly (2,285; SPY keys only); and the frozen `book()` on the written files reproduces
D672's committed per-year C1 answer for 2018-2023 exactly (the trades, and the gross and net means to 1e-9).

OUTPUTS at the joint run: data/joint_run/d680/ (fixture, bars, use, manifest). Proof scratch goes to temp/joint_d680/.
"""
from __future__ import annotations

import argparse
import contextlib
import gzip
import hashlib
import importlib.util
import io
import json
import math
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Iterator

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

MAIN_DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")  # the frozen runner's DATA
CUT, VAULT_END, RAISED = "2025-03-01", "2026-09-18", "2026-09-19"
ES_NQ_SEAL = "2024-01-01"  # D707/D716: ES/NQ prices from here are unseen until the joint run
PROVE_THROUGH = "2023-12-29"  # the last ES/NQ session before the D716 seal
JOINT = REPO / "data" / "joint_run" / "d680"
STAGE = REPO / "temp" / "joint_d680"
FIX_NAME = "fut_opening_globex_1m.csv.gz"
BARS_NAME, USE_NAME, MANIFEST_NAME = "d680_vault_bars.csv.gz", "d680_vault_use.json", "d680_inputs_manifest.json"
RUNNER = REPO / "scripts" / "vault_d680_nq_compression.py"
FROZEN = REPO / "data" / "FROZEN_vault_d680_nq_compression.json"
SPEC = REPO / "docs" / "decisions" / "D680-PRE-REG-the-nq-compression-break-for-the-joint-vault.md"
D672_JSON = REPO / "data" / "stage0_d672_compression_break.json"
GATE0_JSON = REPO / "data" / "opening" / "gate0.json"
PROVE_YEARS = ("2018", "2019", "2020", "2021", "2022", "2023")
ET = "US/Eastern"
REFUSED = 2
DATE = re.compile(r"\d{4}-\d{2}-\d{2}$")
SPY_KEY = re.compile(r'"(\d{4}-\d{2}-\d{2})"\s*:\s*\{')


class JointRunError(RuntimeError):
    pass


def _spec_load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


D644 = _spec_load("build_fut_opening_1m", "build_fut_opening_1m.py")  # loads D462 as `build_fut_index_1m`


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_text_file(p: Path) -> str:
    """The frozen runners' hash: text, LF-pinned."""
    return sha_bytes(p.read_bytes().replace(b"\r\n", b"\n"))


def gz_text_bytes(p: Path) -> bytes:
    with gzip.open(p, "rb") as f:
        return f.read()


def write_gz(p: Path, data: bytes) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as z:
        z.write(data)


@contextlib.contextmanager
def held(module: Any, name: str, value: Any) -> Iterator[None]:
    """Hold a module global at `value` for the body; put the old value back whatever happens (D698's raised_cut)."""
    old = getattr(module, name)
    setattr(module, name, value)
    try:
        yield
    finally:
        setattr(module, name, old)


def expect_raise(fn: Callable[[], Any], what: str, fired: list[str]) -> None:
    try:
        fn()
    except (JointRunError, AssertionError) as e:
        fired.append(what)
        print(f"  fires: {what} ({type(e).__name__})")
        return
    raise AssertionError(f"the check did not fire: {what}")


# ================================================================================ restriction at read time (text)
def restrict_csv(src: Path, field: int, keep: Callable[[str], bool]) -> tuple[bytes, dict[str, Any]]:
    """The header and every line whose comma field `field` (a YYYY-MM-DD date) passes `keep`, filtered as TEXT: no value
    on a dropped line is ever parsed. Raises on a line whose field is not a date (the filter would be meaningless)."""
    opener = gzip.open if src.suffix == ".gz" else open
    out = io.StringIO()
    kept = dropped = 0
    last = ""
    with opener(src, "rt", encoding="utf-8", newline="") as f:
        out.write(f.readline())
        for line in f:
            parts = line.split(",", field + 1)
            d = parts[field] if len(parts) > field else ""
            if not DATE.match(d):
                raise JointRunError(f"{src.name}: field {field} is not a date on a data line; nothing is filtered")
            if keep(d):
                out.write(line)
                kept += 1
                last = max(last, d)
            else:
                dropped += 1
    return out.getvalue().encode("utf-8"), {"kept": kept, "dropped": dropped, "last_kept": last}


def spy_keys(src: Path, before: str) -> list[str]:
    """SPY's daily file is {date: {five fields}}. Its date KEYS before `before`, found by a key pattern; no value is
    parsed. Raises unless every object in the file is one such date's (the structure G0 relies on)."""
    with gzip.open(src, "rt", encoding="utf-8") as f:
        t = f.read()
    keys = SPY_KEY.findall(t)
    if not t.lstrip().startswith("{") or t.count("{") != len(keys) + 1:
        raise JointRunError(f"{src}: not a flat {{date: {{...}}}} object; the key scan would not be the file's days")
    return sorted(k for k in keys if k < before)


def stage_root(data_root: Path, stage: Path, sessions_through: str, spy_before: str, spy_src: Path | None) -> dict:
    """A data root holding only what G0 and D644's `load_front` may read, restricted at read time."""
    info: dict[str, Any] = {}
    txt, info["fut_index_sessions"] = restrict_csv(data_root / "fixtures" / "fut_index_sessions.csv.gz", 1,
                                                   lambda d: d <= sessions_through)
    write_gz(stage / "fixtures" / "fut_index_sessions.csv.gz", txt)
    keys = spy_keys(spy_src or data_root / "raw" / "alphavantage" / "daily" / "SPY.json.gz", spy_before)
    write_gz(stage / "raw" / "alphavantage" / "daily" / "SPY.json.gz", json.dumps({k: {} for k in keys}).encode("utf-8"))
    info["spy_keys"] = {"kept": len(keys), "first": keys[0] if keys else None, "last": keys[-1] if keys else None}
    shutil.copyfile(data_root / "fixtures" / "cme_session_calendar.csv.gz", stage / "fixtures" / "cme_session_calendar.csv.gz")
    return info


# ================================================================================ D644's fixture, restricted per record
def ts_cut_ns(through: str) -> int:
    """18:00 ET on the last session day: every bar before it belongs to a session <= through (or none), every bar at or
    after it to a later session (D644's session rule)."""
    return int(pd.Timestamp(f"{through} 18:00", tz=ET).tz_convert("UTC").value)


def restrict_chunk(arr: np.ndarray, cut_ns: int) -> tuple[np.ndarray, int]:
    """Keep the records whose ts_event is before the cut; only that field of a record past the cut is read."""
    keep = arr["ts_event"] < np.uint64(cut_ns)
    n_past = int((~keep).sum())
    return (arr if n_past == 0 else arr[keep]), n_past


def dbn_headers(data_root: Path) -> list[dict[str, Any]]:
    import databento as db
    out = []
    for p in sorted((data_root / "raw" / "databento").glob("*/*.ohlcv-1m.dbn.zst"), key=lambda q: q.name):
        m = db.DBNStore.from_file(str(p)).metadata
        out.append({"path": str(p), "file": p.name, "bytes": p.stat().st_size, "start": int(m.start), "end": int(m.end),
                    "schema": str(m.schema), "dataset": str(m.dataset)})
    return out


def holes(spans: list[tuple[int, int]], lo: int, hi: int) -> list[tuple[int, int]]:
    """The parts of [lo, hi) that no [start, end) span covers."""
    out, at = [], lo
    for s, e in sorted(spans):
        if e <= at:
            continue
        if s > at:
            out.append((at, min(s, hi)))
        at = max(at, e)
        if at >= hi:
            break
    if at < hi:
        out.append((at, hi))
    return [(a, b) for a, b in out if a < b]


def iso(ns: int) -> str:
    return pd.Timestamp(ns, tz="UTC").strftime("%Y-%m-%dT%H:%MZ")


def fixture_worker(task: tuple[str, int, np.ndarray, pd.DataFrame]) -> dict[str, Any]:
    """D644's `worker` with the per-record restriction; `process_chunk` and `ids_of` are D644's/D462's, unchanged."""
    import databento as db
    path, cut_ns, sessions, front = task
    t0 = time.time()
    store = db.DBNStore.from_file(path)
    w = D644.D462.ids_of(store)
    parts, n_read, n_past = [], 0, 0
    for arr in store.to_ndarray(count=D644.CHUNK):
        n_read += len(arr)
        arr, k = restrict_chunk(arr, cut_ns)
        n_past += k
        b = D644.process_chunk(arr, w, sessions, front, D644.ROOTS)
        if b is not None:
            parts.append(b)
    bars = pd.concat(parts, ignore_index=True) if parts else None
    return {"file": Path(path).name, "rows_read": n_read, "rows_past_cut_dropped": n_past,
            "rows_kept": 0 if bars is None else len(bars), "secs": round(time.time() - t0, 1), "bars": bars}


def build_fixture(data_root: Path, stage: Path, through: str, out: Path, workers: int,
                  accept_holes: tuple[str, ...] = ()) -> dict[str, Any]:
    """D644's `cmd_build`, mirrored, over the files whose header starts before the cut; `load_front` reads the staged
    (text-restricted) session table."""
    t0 = time.time()
    cut_ns = ts_cut_ns(through)
    hdr = dbn_headers(data_root)
    lo = int(pd.Timestamp(f"{D644.START} 00:00", tz=ET).tz_convert("UTC").value) - 86_400 * 10**9
    gaps = holes([(h["start"], h["end"]) for h in hdr], lo, cut_ns)
    ok_days = {pd.Timestamp(d).strftime("%Y-%m-%d") for d in accept_holes}
    bad = [(a, b) for a, b in gaps if not all(x.strftime("%Y-%m-%d") in ok_days for x in
                                              pd.date_range(pd.Timestamp(a, tz="UTC").floor("D"), pd.Timestamp(b - 1, tz="UTC").floor("D"), freq="D"))]
    if bad:
        raise JointRunError("the ohlcv-1m archive has a hole before the cut: " + ", ".join(f"[{iso(a)}, {iso(b)})" for a, b in bad)
                            + " (fill it, or name each whole UTC day with --accept-hole on the principal's word)")
    files = [h for h in hdr if h["start"] < cut_ns]
    sessions, front = D644.load_front(stage, through)
    if len(sessions) == 0 or sessions[-1] > through:
        raise JointRunError("the staged session table is empty or runs past the cut")
    print(f"{len(files)} of {len(hdr)} ohlcv-1m files start before {iso(cut_ns)}; {len(sessions)} sessions "
          f"{sessions[0]} .. {sessions[-1]}; {workers} workers", flush=True)
    order = {h["file"]: i for i, h in enumerate(files)}
    tasks = [(h["path"], cut_ns, sessions, front) for h in sorted(files, key=lambda h: -h["bytes"])]
    from multiprocessing import Pool
    with Pool(workers) as pool:
        res = pool.map(fixture_worker, tasks, chunksize=1)
    res.sort(key=lambda r: order[r["file"]])
    sec, wall = sum(r["secs"] for r in res), time.time() - t0
    print(f"[SPEED] sum(item time)/wall = {sec / wall:.2f}x on {workers} workers ({100 * sec / wall / workers:.0f}%)", flush=True)
    bars = pd.concat([r["bars"] for r in res if r["bars"] is not None], ignore_index=True)
    n0 = len(bars)
    bars = bars.sort_values(["root", "session", "et"], kind="stable").drop_duplicates(["root", "session", "et"])
    if (bars["session"] > through).any():
        raise JointRunError("a session past the cut reached the fixture")
    out.parent.mkdir(parents=True, exist_ok=True)
    bars.to_csv(out, index=False, compression={"method": "gzip", "mtime": 0}, float_format="%.2f", encoding="utf-8",
                lineterminator="\n")
    meta = {"builder": "scripts/joint_d680_vault.py (D644's build_fut_opening_1m functions, unchanged; per-record cut)",
            "sessions": [D644.START, through], "ts_cut_utc": iso(cut_ns), "rows": int(len(bars)),
            "duplicates_dropped": int(n0 - len(bars)), "accepted_holes": sorted(ok_days),
            "holes_before_cut": [[iso(a), iso(b)] for a, b in gaps],
            "files": [{k: v for k, v in r.items() if k != "bars"} for r in res],
            "files_skipped_header_at_or_past_cut": [h["file"] for h in hdr if h["start"] >= cut_ns],
            "pandas": pd.__version__, "python": sys.version.split()[0], "wall_min": round((time.time() - t0) / 60, 2)}
    out.with_suffix("").with_suffix(".meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")
    return meta


def same_bytes(a: bytes, b: bytes, what: str) -> str:
    if a != b:
        i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
        raise JointRunError(f"{what}: differ at byte {i} of {len(a)} / {len(b)}")
    return sha_bytes(a)


def vault_coverage_report(hdr: list[dict[str, Any]]) -> list[list[str]]:
    lo = int(pd.Timestamp(f"{CUT} 00:00", tz=ET).tz_convert("UTC").value) - 86_400 * 10**9
    return [[iso(a), iso(b)] for a, b in holes([(h["start"], h["end"]) for h in hdr], lo, ts_cut_ns(VAULT_END))]


def prove_fixture(data_root: Path, workers: int) -> int:
    """D644's rebuild, restricted to sessions <= 2023-12-29 at read time, against the committed fixture's rows for the
    same sessions (filtered as text): byte for byte."""
    t0 = time.time()
    st = STAGE / "prove_fixture"
    if st.exists():
        shutil.rmtree(st)
    info = stage_root(data_root, st, PROVE_THROUGH, CUT, None)
    if info["fut_index_sessions"]["last_kept"] >= ES_NQ_SEAL:
        raise JointRunError("the staged session table reaches the D716 seal")
    built = st / "built" / FIX_NAME
    meta = build_fixture(data_root, st, PROVE_THROUGH, built, workers)
    ref, rinfo = restrict_csv(data_root / "fixtures" / FIX_NAME, 1, lambda d: d < ES_NQ_SEAL)
    got = gz_text_bytes(built)
    h = same_bytes(got, ref, "the rebuilt fixture against the committed fixture's sessions before 2024-01-01")
    fired: list[str] = []
    bent = bytearray(got)
    k = got.index(b"\n", len(got) // 2) - 1  # the last digit of a mid-file line
    bent[k] = ord("0") if bent[k] != ord("0") else ord("1")
    expect_raise(lambda: same_bytes(bytes(bent), ref, "one digit changed"), "the byte comparison, one digit changed", fired)
    hdr = dbn_headers(data_root)
    out = {"proof": "D644 rebuild == committed fut_opening_globex_1m on sessions 2015-09-01 -> 2023-12-29",
           "sha256_text": h, "rows": rinfo["kept"], "rows_of_committed_fixture_not_compared_sealed": rinfo["dropped"],
           "staged": info, "build": {k_: v for k_, v in meta.items() if k_ != "files"},
           "files_read": [f["file"] for f in meta["files"]], "checks_fired": fired,
           "vault_range_holes_in_ohlcv_1m_headers": vault_coverage_report(hdr),
           "runtime_min": round((time.time() - t0) / 60, 2)}
    (STAGE / "prove_fixture.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    return 0


# ================================================================================ G0's loader, cut moved, written out
def load_g0() -> Any:
    return _spec_load("joint_d680_opening_gate0", "opening_gate0.py")  # a private instance of G0, unchanged


def build_inputs(fixture: Path, stage: Path, cut: str, out_dir: Path) -> dict[str, Any]:
    from backtest_framework.validation.frozen import assert_none_at_or_after
    G0 = load_g0()
    with held(G0, "RESERVED_FROM", cut), held(G0, "BARS", fixture):
        use, info = G0.usable_sessions(stage)
        b = G0.load_bars()
    assert_none_at_or_after(b, "session", cut)
    if any(s >= cut for s in use):
        raise JointRunError("a usable session at or after the cut")
    out_dir.mkdir(parents=True, exist_ok=True)
    bars_p, use_p = out_dir / BARS_NAME, out_dir / USE_NAME
    b.to_csv(bars_p, index=False, compression={"method": "gzip", "mtime": 0}, float_format="%.2f", encoding="utf-8",
             lineterminator="\n")
    use_p.write_text(json.dumps(use) + "\n", encoding="utf-8", newline="\n")
    return {"cut": cut, "fixture": str(fixture), "fixture_sha256": sha_bytes(fixture.read_bytes()),
            "bars": str(bars_p), "bars_sha256": sha_bytes(bars_p.read_bytes()), "bars_rows": int(len(b)),
            "bars_sessions": [str(b["session"].min()), str(b["session"].max())], "bars_nq_sessions": int(b.loc[b["root"] == "NQ", "session"].nunique()),
            "use": str(use_p), "use_sha256": sha_bytes(use_p.read_bytes()), "use_n": len(use),
            "use_span": [use[0], use[-1]] if use else None, "g0_info": info, "pandas": pd.__version__}


def read_like_runner(bars_p: Path, use_p: Path) -> tuple[pd.DataFrame, Any]:
    """Exactly as the frozen `--vault` reads its two files."""
    bv = pd.read_csv(bars_p, encoding="utf-8", dtype={"session": str, "hhmm": str, "et": str})
    uv = json.loads(use_p.read_text(encoding="utf-8"))
    return bv, uv


def frozen_runner() -> Any:
    import vault_d680_nq_compression as V680
    return V680


def check_freeze(runner: Path = RUNNER, spec: Path = SPEC, frozen: Path = FROZEN) -> dict[str, str]:
    """The frozen runner's own check (its runner and D680's record against the freeze), plus the imported files the
    freeze lists as unchanged."""
    fz = json.loads(frozen.read_text(encoding="utf-8"))
    got = {"runner": sha_text_file(runner), "prereg": sha_text_file(spec)}
    if got["runner"] != fz["runner_sha256"] or got["prereg"] != fz["prereg_sha256"]:
        raise JointRunError("the D680 runner or its record has moved since the freeze")
    for p, h in fz["imported_unchanged"].items():
        if sha_text_file(runner.parent / p) != h:
            raise JointRunError(f"{p} has moved since the freeze")
        got[p] = h
    return got


def c1_by_year(tr: pd.DataFrame) -> dict[str, dict[str, float]]:
    win = np.isfinite(tr["t671"].to_numpy(float)) & np.isfinite(tr["ctier"].to_numpy(float))
    c1 = win & (tr["ctier"].to_numpy(float) < 1 / 3)
    yrs = tr["session"].str[:4].to_numpy()
    return {y: {"trades": int((c1 & (yrs == y)).sum()), "gross": float(tr.loc[c1 & (yrs == y), "gross_prereg"].mean()),
                "net": float(tr.loc[c1 & (yrs == y), "net_prereg"].mean())} for y in sorted(set(yrs[c1]))}


def check_years(got: dict[str, dict[str, float]], ref: dict[str, Any]) -> None:
    for y in PROVE_YEARS:
        r, g = ref[y]["C1"], got.get(y, {"trades": 0, "gross": math.nan, "net": math.nan})
        if g["trades"] != r["trades"] or abs(g["gross"] - r["gross"]) > 1e-9 or abs(g["net"] - r["net"]) > 1e-9:
            raise JointRunError(f"{y}: C1 {g} against D672's {r['trades']} trades, gross {r['gross']}, net {r['net']}")


def check_use(use: list[str], info: dict[str, Any], g0: dict[str, Any]) -> None:
    if len(use) != g0["usable_sessions"] or info != g0["calendar"] or use[-1] >= CUT:
        raise JointRunError(f"usable sessions: {len(use)}, {info.get('nyse_days')} NYSE days, against gate0.json's "
                            f"{g0['usable_sessions']} / {g0['calendar']['nyse_days']}")


def frames_equal(a: pd.DataFrame, b: pd.DataFrame, what: str) -> None:
    a, b = a.reset_index(drop=True), b.reset_index(drop=True)
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        raise JointRunError(f"{what}: columns or length differ")
    for c in a.columns:
        x, y = a[c].to_numpy(), b[c].to_numpy()
        if a[c].dtype != b[c].dtype:
            raise JointRunError(f"{what}: {c} dtype {a[c].dtype} != {b[c].dtype}")
        same = np.array_equal(x, y, equal_nan=True) if x.dtype.kind == "f" else bool((x == y).all())
        if not same:
            raise JointRunError(f"{what}: column {c} differs")


def prove_inputs(data_root: Path) -> int:
    t0 = time.time()
    fired: list[str] = []
    out: dict[str, Any] = {"proof": "the D680 input path on in-sample ES/NQ sessions before 2024-01-01 (D716's seal)"}
    out["freeze_check_before"] = check_freeze()
    st = STAGE / "prove_inputs"
    if st.exists():
        shutil.rmtree(st)
    out["staged"] = stage_root(data_root, st, PROVE_THROUGH, CUT, None)
    fx, fxi = restrict_csv(data_root / "fixtures" / FIX_NAME, 1, lambda d: d < ES_NQ_SEAL)
    write_gz(st / "fixtures" / FIX_NAME, fx)
    out["staged"]["fixture_before_2024"] = fxi
    dix, dixi = restrict_csv(data_root / "raw" / "squeezemetrics" / "DIX.csv", 0, lambda d: d < ES_NQ_SEAL)
    out["staged"]["dix_before_2024"] = dixi
    # 1. the builder at the in-sample cut: G0's loader, written out
    bi = build_inputs(st / "fixtures" / FIX_NAME, st, CUT, st / "out")
    out["inputs"] = bi
    bars_p, use_p = Path(bi["bars"]), Path(bi["use"])
    # 2. the bars file reproduces the fixture's text byte for byte (loader + writer are lossless)
    out["bars_text_sha256"] = same_bytes(gz_text_bytes(bars_p), fx, "the written bars against the staged fixture")
    # 3. the usable sessions reproduce gate0.json (SPY's keys before 2025-03-01, the calendar's half days)
    g0 = json.loads(GATE0_JSON.read_text(encoding="utf-8"))
    bv, uv = read_like_runner(bars_p, use_p)
    check_use(uv, bi["g0_info"], g0)
    out["use_check"] = {"usable_sessions": len(uv), "nyse_days": bi["g0_info"]["nyse_days"],
                        "half_days_removed": len(bi["g0_info"]["half_days_removed"]), "gate0_json": "equal"}
    # 4. the frozen in-sample loader (D668's load_bars) on the same staged root gives the same frame and sessions
    V680 = frozen_runner()
    b_f, use_f, _gd, R = V680.M.load_bars(st, False, ("ES", "NQ"))
    cols = list(b_f.columns)
    frames_equal(bv[cols], b_f, "the written bars (read as the frozen --vault reads them) against D668.load_bars")
    if list(use_f) != list(uv):
        raise JointRunError("the use list differs from D668.load_bars's")
    out["frozen_loader_check"] = {"columns": cols, "rows": int(len(b_f)), "equal": True}
    # 5. the frozen book() on the written files reproduces D672's per-year C1, 2018-2023, exactly
    gex = pd.read_csv(io.BytesIO(dix), encoding="utf-8", dtype={"date": str}).set_index("date")["gex"].astype(float).sort_index()
    tr_m, sess_m = V680.book(bv, V680.cut_use(uv, CUT), R, gex)
    tr_f, _ = V680.book(b_f, use_f, R, gex)
    frames_equal(tr_m, tr_f, "book() on the written files against book() on the frozen loader's frame")
    if tr_m["session"].max() >= ES_NQ_SEAL:
        raise JointRunError("a trade on or after 2024-01-01 in the proof")
    ref = json.loads(D672_JSON.read_text(encoding="utf-8"))["roots"]["NQ"]["by_year"]
    got = c1_by_year(tr_m)
    check_years(got, ref)
    out["d672_by_year_check"] = {y: {"trades": got[y]["trades"], "gross": got[y]["gross"], "net": got[y]["net"],
                                     "d672": [ref[y]["C1"]["trades"], ref[y]["C1"]["gross"], ref[y]["C1"]["net"]],
                                     "abs_diff": [abs(got[y]["gross"] - ref[y]["C1"]["gross"]), abs(got[y]["net"] - ref[y]["C1"]["net"])]}
                                 for y in PROVE_YEARS}
    out["c1_trades_2018_2023"] = int(sum(got[y]["trades"] for y in PROVE_YEARS))
    # 6. the raised cut changes nothing on in-sample input (prefix stability on real data)
    with held(V680.T, "RESERVED_FROM", RAISED):
        tr_r, _ = V680.book(bv, uv, R, gex)
    frames_equal(tr_r, tr_m, "book() under the raised cut against the default cut, in-sample input")
    if V680.T.RESERVED_FROM != CUT:
        raise JointRunError("the cut was not restored")
    out["raised_cut_in_sample"] = "identical trade table"
    # 7. every check fires on a deliberately broken input
    expect_raise(lambda: check_use(uv[:-1], bi["g0_info"], g0), "use: one session dropped", fired)
    bent = bv.copy()
    i = int(np.flatnonzero((bent["root"] == "NQ").to_numpy())[1000])
    bent.loc[i, "close"] += 0.25
    expect_raise(lambda: frames_equal(bent[cols], b_f, "one NQ close + one tick"), "frame: one NQ close + one tick", fired)
    worse = {y: dict(v) for y, v in got.items()}
    worse["2021"]["trades"] -= 1
    expect_raise(lambda: check_years(worse, ref), "per-year: one 2021 trade missing", fired)
    nudged = {y: dict(v) for y, v in got.items()}
    nudged["2019"]["net"] += 1e-8
    expect_raise(lambda: check_years(nudged, ref), "per-year: 2019 net + 1e-8 bp", fired)
    with tempfile.TemporaryDirectory() as td:
        tp = Path(td) / RUNNER.name
        tp.write_bytes(RUNNER.read_bytes() + b"# moved\n")
        for p in json.loads(FROZEN.read_text(encoding="utf-8"))["imported_unchanged"]:
            shutil.copyfile(RUNNER.parent / p, Path(td) / p)
        expect_raise(lambda: check_freeze(tp), "freeze: a runner with one line appended", fired)
    out["checks_fired"] = fired
    out["freeze_check_after"] = check_freeze()
    out["runtime_min"] = round((time.time() - t0) / 60, 2)
    (STAGE / "prove_inputs.json").write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1, default=str))
    return 0


# ================================================================================ the rehearsal (synthetic prices)
def rehearse(V680: Any, R: Any, layout: pd.DataFrame, use: list[str], seed: int = 680) -> dict[str, Any]:
    """The frozen book() on the given calendar and bar layout with every price and volume a synthetic walk (D668's
    `synth`): under the default cut no session from 2025-03-01 reaches the frame; under the held cut they do, C1 trades
    exist among them, and the pre-cut part of the trade table is unchanged."""
    cols = ["root", "session", "hhmm", "open", "high", "low", "close", "volume"]
    roots = sorted(set(layout["root"]))
    bs = V680.M.synth(layout[cols].copy(), {r: {"ES": 5000.0, "NQ": 18000.0}.get(r, 1000.0) for r in roots}, seed)
    tr0, f0 = V680.book(bs, use, R, None)
    with held(V680.T, "RESERVED_FROM", RAISED):
        tr1, f1 = V680.book(bs, use, R, None)
    if V680.T.RESERVED_FROM != CUT:
        raise JointRunError("the cut was not restored after the rehearsal")
    post0, post1 = int((f0 >= CUT).sum()), int((f1 >= CUT).sum())
    c1_post = int(((tr1["session"] >= CUT) & (tr1["ctier"].to_numpy(float) < 1 / 3)).sum())
    if post0 != 0:
        raise JointRunError("the default cut kept a session on or after 2025-03-01")
    if post1 == 0 or c1_post == 0:
        raise JointRunError(f"the held cut still dropped the vault ({post1} frame sessions, {c1_post} C1 trades after the cut)")
    frames_equal(tr1[tr1["session"] < CUT].reset_index(drop=True), tr0, "the pre-cut trade table under the held cut")
    return {"frame_sessions_after_cut_default": post0, "frame_sessions_after_cut_held": post1,
            "last_frame_session_held": str(f1.max()), "last_layout_session": str(layout["session"].max()),
            "c1_trades_after_cut_held": c1_post, "trades_before_cut_identical": True}


def synthetic_layout(first: str, last: str) -> tuple[pd.DataFrame, list[str]]:
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range(first, last)]
    rth = pd.date_range("2000-01-01 09:30", "2000-01-01 15:59", freq="min").strftime("%H:%M").tolist()
    hh = ["18:00", "20:00", "22:00", "02:00", "05:00", "08:00", "09:00"] + rth
    n = len(hh)
    b = pd.DataFrame({"root": "NQ", "session": np.repeat(days, n), "hhmm": np.tile(hh, len(days))})
    b["et"] = b["session"] + " " + b["hhmm"]
    for c in ("open", "high", "low", "close"):
        b[c] = 1.0
    b["volume"] = 1
    return b, days


# ================================================================================ the joint run
def refuse(word: str | None) -> bool:
    if not (word or "").strip():
        print("refused: the vault is read only in the joint run, on the principal's word (A10)")
        return True
    return False


def build_vault(step: str, data_root: Path, workers: int, spy: Path | None, accept: tuple[str, ...], word: str) -> int:
    st = STAGE / "vault"
    if step == "fixture":  # SYSTEM python
        if (JOINT / FIX_NAME).exists():
            raise JointRunError(f"{JOINT / FIX_NAME} exists; the vault fixture is built once")
        if st.exists():
            shutil.rmtree(st)
        info = stage_root(data_root, st, VAULT_END, RAISED, spy)
        if info["fut_index_sessions"]["last_kept"] < VAULT_END:
            raise JointRunError(f"fut_index_sessions ends {info['fut_index_sessions']['last_kept']}: rebuild D462 through "
                                f"{VAULT_END} first (scripts/build_fut_index_1m.py after the top-up)")
        meta = build_fixture(data_root, st, VAULT_END, JOINT / FIX_NAME, workers, accept)
        (JOINT / "d680_fixture_stage.json").write_text(json.dumps({"principals_word": word, "staged": info, "build": meta},
                                                                  indent=1) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({k: v for k, v in meta.items() if k != "files"}, indent=1))
        return 0
    # step == "inputs", uv
    if (JOINT / MANIFEST_NAME).exists():
        raise JointRunError("the vault inputs are built once; the manifest exists")
    if not (JOINT / FIX_NAME).exists():
        raise JointRunError("build the vault fixture first (--build-vault fixture, system python)")
    st = STAGE / "vault_inputs"
    if st.exists():
        shutil.rmtree(st)
    info = stage_root(data_root, st, VAULT_END, RAISED, spy)
    if (info["spy_keys"]["last"] or "") < VAULT_END:
        raise JointRunError(f"SPY's daily file ends {info['spy_keys']['last']}: refresh it (pass --spy) or the use list stops short")
    bi = build_inputs(JOINT / FIX_NAME, st, RAISED, JOINT)
    if bi["bars_sessions"][1] > VAULT_END:
        raise JointRunError("the vault bars run past 2026-09-18")
    doc = {"principals_word": word, "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **bi,
           "freeze_check": check_freeze()}
    (JOINT / MANIFEST_NAME).write_text(json.dumps(doc, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc, indent=1, default=str))
    return 0


def run_vault(word: str) -> int:
    check_freeze()
    man = json.loads((JOINT / MANIFEST_NAME).read_text(encoding="utf-8"))
    bars_p, use_p = JOINT / BARS_NAME, JOINT / USE_NAME
    if sha_bytes(bars_p.read_bytes()) != man["bars_sha256"] or sha_bytes(use_p.read_bytes()) != man["use_sha256"]:
        raise JointRunError("the vault input files moved after their manifest was written")
    V680 = frozen_runner()
    R = V680.M.S.load_v2().R
    bv, uv = read_like_runner(bars_p, use_p)
    print("rehearsal on the vault files' own calendar and layout, prices synthetic:", flush=True)
    print(json.dumps(rehearse(V680, R, bv[bv["root"] == "NQ"], uv), indent=1), flush=True)
    del bv
    with held(V680.T, "RESERVED_FROM", RAISED):
        rc = V680.main(["--vault-bars", str(bars_p), "--vault-use", str(use_p), "--principals-word", word])
    if V680.T.RESERVED_FROM != CUT:
        raise JointRunError("the cut was not restored after the frozen call")
    res = json.loads(V680.VAULT_OUT.read_text(encoding="utf-8")) if V680.VAULT_OUT.exists() else {}
    if int(res.get("reported_B0_every_break", {}).get("trades", 0)) == 0:
        raise JointRunError("the frozen runner scored no vault break: the cut did not reach it (the line is spent; report it)")
    return rc


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fired: list[str] = []
    # held(): holds, restores, and restores when the body raises
    class _M:
        RESERVED_FROM = CUT
    with held(_M, "RESERVED_FROM", RAISED):
        assert _M.RESERVED_FROM == RAISED
    assert _M.RESERVED_FROM == CUT
    try:
        with held(_M, "RESERVED_FROM", RAISED):
            raise ValueError("inside")
    except ValueError:
        pass
    if _M.RESERVED_FROM != CUT:
        raise AssertionError("held() did not restore after a raise")
    # refusals: every vault mode returns 2 without the principal's word, before touching anything
    for argv in (["--build-vault", "fixture"], ["--build-vault", "inputs"], ["--run-vault"],
                 ["--run-vault", "--principals-word", "  "]):
        if main(argv) != REFUSED:
            raise AssertionError(f"{argv} ran without the principal's word")
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        # restrict_csv: keeps before the cut, never parses a dropped line; a non-date field fires
        (t / "a.csv").write_text("root,day,x\nNQ,2024-12-31,1\nNQ,2025-03-01,SECRET\nNQ,2025-02-28,2\n", encoding="utf-8",
                                 newline="\n")
        txt, inf = restrict_csv(t / "a.csv", 1, lambda d: d < CUT)
        assert txt == b"root,day,x\nNQ,2024-12-31,1\nNQ,2025-02-28,2\n" and inf["dropped"] == 1, (txt, inf)
        (t / "b.csv").write_text("root,day,x\nNQ,20250301,1\n", encoding="utf-8", newline="\n")
        expect_raise(lambda: restrict_csv(t / "b.csv", 1, lambda d: d < CUT), "restrict_csv: a non-date field", fired)
        # spy_keys: keys only; a nested structure fires
        write_gz(t / "s.json.gz", json.dumps({"2025-03-03": {"1. open": "1"}, "2025-02-28": {"1. open": "2"}}).encode("utf-8"))
        assert spy_keys(t / "s.json.gz", CUT) == ["2025-02-28"]
        write_gz(t / "n.json.gz", json.dumps({"Meta": {"x": {"y": 1}}, "2025-02-28": {"1. open": "2"}}).encode("utf-8"))
        expect_raise(lambda: spy_keys(t / "n.json.gz", CUT), "spy_keys: a nested object", fired)
        # the freeze check passes on the real files and fires on a tampered copy of the runner or of an import
        check_freeze()
        imports = list(json.loads(FROZEN.read_text(encoding="utf-8"))["imported_unchanged"])
        for p in imports:
            shutil.copyfile(RUNNER.parent / p, t / p)
        tp = t / RUNNER.name
        tp.write_bytes(RUNNER.read_bytes())
        check_freeze(tp)  # an exact copy passes
        tp.write_bytes(RUNNER.read_bytes().replace(b"T_VAULT, MIN_VAULT_TRADES, N_VAULT_SESSIONS",
                                                   b"T_VAULT, MIN_VAULT_TRADES,  N_VAULT_SESSIONS"))
        expect_raise(lambda: check_freeze(tp), "check_freeze: one space added to the runner", fired)
        tp.write_bytes(RUNNER.read_bytes())
        (t / imports[-1]).write_bytes((RUNNER.parent / imports[-1]).read_bytes() + b"\n")
        expect_raise(lambda: check_freeze(tp), "check_freeze: an imported file moved", fired)
    # the per-record restriction
    rec = np.zeros(6, dtype=[("ts_event", "<u8"), ("close", "<i8")])
    rec["ts_event"] = [1, 5, 9, 10, 11, 3]
    rec["close"] = [1, 2, 3, 99, 99, 4]
    kept, past = restrict_chunk(rec, 10)
    assert past == 2 and kept["close"].tolist() == [1, 2, 3, 4], (past, kept)
    assert ts_cut_ns("2023-12-29") == pd.Timestamp("2023-12-29 23:00", tz="UTC").value  # EST: 18:00 ET = 23:00 UTC
    assert ts_cut_ns("2026-09-18") == pd.Timestamp("2026-09-18 22:00", tz="UTC").value  # EDT
    # the header coverage check finds a one-day hole and nothing else
    d = 86_400 * 10**9
    assert holes([(0, 10 * d), (11 * d, 20 * d)], 0, 20 * d) == [(10 * d, 11 * d)]
    assert holes([(0, 10 * d), (5 * d, 20 * d)], 0, 15 * d) == []
    assert holes([(0, 10 * d)], 0, 12 * d) == [(10 * d, 12 * d)]
    # the byte comparison fires on one byte
    expect_raise(lambda: same_bytes(b"a,1.25\n", b"a,1.50\n", "synthetic"), "same_bytes: one byte", fired)
    # the frozen book() on a synthetic NQ frame whose sessions run past 2025-03-01: dropped under the default cut,
    # kept under the held cut, C1 trades after the cut, and the pre-cut trade table unchanged
    V680 = frozen_runner()
    R = V680.M.S.load_v2().R
    layout, days = synthetic_layout("2022-01-03", VAULT_END)
    reh = rehearse(V680, R, layout, days)
    print("  synthetic rehearsal:", json.dumps(reh))
    # and the rehearsal's own check fires when the cut is NOT held (the wrapper's mechanism removed)
    def _no_hold() -> None:
        bs = V680.M.synth(layout[["root", "session", "hhmm", "open", "high", "low", "close", "volume"]].copy(), {"NQ": 18000.0}, 680)
        _tr, f = V680.book(bs, days, R, None)
        if int((f >= CUT).sum()) == 0:
            raise JointRunError("no session after the cut without the hold")
    expect_raise(_no_hold, "the frozen root_frame drops every post-cut session without the hold", fired)
    print(f"selftest OK: held() holds and restores (also on a raise); every vault mode refused without the word; "
          f"{len(fired)} checks fired: {fired}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prove", choices=("fixture", "inputs"))
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--build-vault", choices=("fixture", "inputs"))
    ap.add_argument("--run-vault", action="store_true")
    ap.add_argument("--principals-word", default=None)
    ap.add_argument("--data-root", type=Path, default=MAIN_DATA)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--spy", type=Path, default=None, help="a refreshed SPY daily file (G0's default ends 2026-08-26)")
    ap.add_argument("--accept-hole", action="append", default=[], help="a whole UTC day the principal accepts missing")
    a = ap.parse_args(argv)
    if a.build_vault or a.run_vault:
        if refuse(a.principals_word):
            return REFUSED
        if a.build_vault:
            return build_vault(a.build_vault, a.data_root, a.workers, a.spy, tuple(a.accept_hole), a.principals_word)
        return run_vault(a.principals_word)
    if a.selftest:
        return selftest()
    if a.prove == "fixture":
        return prove_fixture(a.data_root, a.workers)
    if a.prove == "inputs":
        return prove_inputs(a.data_root)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
