"""D630 s.8's vault-input path for NG: the settlement ledger's Stage A (programme slot 3, `ledger H2`) and D649's
projected-profit line (slot 8) both score D630's trade on the vault, so both need D630's inputs built through
2026-09-18 "by the same code with the cut moved" (D630 s.8). Prepared 2026-09-30 (the principal: the joint run's
inputs before the Databento subscription lapses); the vault is never opened here.

    python scripts/build_ledger_vault_inputs.py --prove dbn             # SYSTEM python (databento), in-sample only
    uv run python scripts/build_ledger_vault_inputs.py --prove panels   # in-sample only; needs --prove dbn first
    uv run python scripts/build_ledger_vault_inputs.py --selftest       # synthetic only
    python scripts/build_ledger_vault_inputs.py --build-vault dbn --principals-word "..."            # joint run ONLY
    uv run python scripts/build_ledger_vault_inputs.py --build-vault panels --principals-word "..." \\
        --fut-share-anchor YYYY-MM-DD --swap-q-last YYYY-Qn                                           # joint run ONLY

THE PLAN (docs/internal/AITODO.md, "PARKED (the principal, 2026-09-28): D630 s.8's vault-input path"): load each
frozen builder UNCHANGED, move only its cut and its output paths, prove it first with the cut left at 2025-03-01 by
reproducing the frozen in-sample inputs byte for byte, and switch to the vault only at the joint run.

THE BUILDERS, in dependency order (every one is hashed by data/FROZEN_ledger_stage_a_ng.json; none is edited):
  1. build_window_volume_panel.py  -> ledger_window_volume_daily.csv.gz         (SYSTEM python, Databento ohlcv-1s)
  2. build_ng_minute_bars.py       -> ng_minute_bars.csv.gz                     (SYSTEM python; checks itself vs 1)
  3. estimate_fut_share.py --seal a6 -> ledger_fut_share_daily_a6.csv.gz (+ summary_a6.json, read by 5)
  4. build_ledger_calendar.py      -> ledger_calendar_flags.csv
  5. build_predicted_flow_panel.py -> ledger_predicted_flow_daily.csv.gz, ledger_predicted_flow_contracts.csv.gz
  6. D630's own run_h2_ng_stage_a.build + signed -> the trade table (day, traded, absI_usd, g) that D649 reads.
  (ledger_signed_window_daily.csv.gz is frozen too, but it is H1's Sierra panel, not an input of D630's trade.)

THE CUT IS NOT ONE CONSTANT (an audit of the chain, verified line by line): the flow panel and the calendar COPY
their CUT into two separate copies of gate_0b_ng_nav at import time (U.G and U.GCL.G), estimate_fut_share holds a
third copy and a tuple A6_CONSTANTS, run_h1a/run_h2 hold their own CUT, and the two Databento builders select their
files by a LITERAL (`year <= 2024` plus the Jan-Feb 2025 tail pull) inside `files()`. `cut_state()` reads every one
of them and `expect_cuts()` raises unless each holds the value this run means, before every builder call; all are
set AFTER every module is imported (an import re-copies the builder's own CUT). The vault's file selection replaces
`files()` (the one place that cut lives), with the main pull's year files and not the tail (the two overlap on
Jan-Feb 2025 and the window panel would sum them); `--prove dbn` checks, record against record on the timestamp
field alone past the cut, that the main pull's Jan-Feb 2025 equals the tail's, so that swap cannot move the prefix.

READ-TIME RESTRICTION. The catalogue panels (fund_nav_daily, fut_settle_strip, fund_holdings_quarterly) are read by
`load_panel`, which reads the WHOLE file before it filters; here each is first restricted AS TEXT on its own date
column into a staging root (panels.REPO and panels.MANIFEST held there for the call), so no row at or past the cut
is ever parsed. The Databento files the in-sample builders open all END by 2025-03-01T00:00Z (checked from their
headers first), so none holds a vault record. The vault's files must end by 2026-09-19T00:00Z (D626's seal on CL/NG
from 2026-09-19), checked the same way.

OUTPUTS: proofs -> temp/ledger_vault_inputs/ (deletable); the joint run -> data/joint_run/ng/.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import gzip
import hashlib
import importlib.util
import io
import json
import math
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

MAIN_DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")
CUT_IN, LAST_IN = "2025-03-01", "2025-02-28"
VAULT_FROM, VAULT_END, CUT_V = "2025-03-01", "2026-09-18", "2026-09-19"
A6_IN = ("2025-03-01", "2025-02-28", "2024-12-31", "2024-Q4")  # estimate_fut_share.A6_CONSTANTS, as frozen
TS_CUT_IN = "2025-03-01T00:00:00Z"   # every in-sample Databento file ends by here
TS_SEAL_V = "2026-09-19T00:00:00Z"   # D626: nothing for CL/NG/HO/RB dated 2026-09-19 or later
FROZEN = REPO / "data" / "FROZEN_ledger_stage_a_ng.json"
STAGE = REPO / "temp" / "ledger_vault_inputs"
JOINT = REPO / "data" / "joint_run" / "ng"
CATALOGUE = {"fund_nav_daily": "date", "fut_settle_strip": "ref", "fund_holdings_quarterly": "filed_date"}
NAMES = {"wp": "ledger_window_volume_daily.csv.gz", "wp_sum": "ledger_window_volume_summary.json",
         "mb": "ng_minute_bars.csv.gz", "mb_sum": "ng_minute_bars_summary.json",
         "fs": "ledger_fut_share_daily_a6.csv.gz", "fs_sum": "ledger_fut_share_summary_a6.json",
         "cal": "ledger_calendar_flags.csv", "fp_day": "ledger_predicted_flow_daily.csv.gz",
         "fp_con": "ledger_predicted_flow_contracts.csv.gz", "fp_sum": "ledger_predicted_flow_summary.json",
         "table": "d630_trade_table.csv"}
D630_KNOWN = {"n": 1028, "gate_mean": 66.0214007782101}  # data/ledger_h2_ng_stage_a.json NG.gate
REFUSED = 2


class VaultInputError(RuntimeError):
    pass


def _load(name: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def frozen_sha() -> dict[str, str]:
    return {Path(f["path"]).name: f["sha256"] for f in json.loads(FROZEN.read_text(encoding="utf-8"))["fixtures"]}


def same_sha(got: bytes, want: str, what: str) -> str:
    h = sha(got)
    if h != want:
        raise VaultInputError(f"{what}: sha256 {h} is not the frozen {want}")
    return h


def gz_like_main(text: str) -> bytes:
    """The window panel's and the fut-share estimator's own `main` wrapping (GzipFile, mtime 0)."""
    b = io.BytesIO()
    with gzip.GzipFile(fileobj=b, mode="wb", mtime=0) as z:
        z.write(text.encode("utf-8"))
    return b.getvalue()


@contextlib.contextmanager
def held(pairs: list[tuple[Any, str, Any]]) -> Iterator[None]:
    """Hold module globals for the body and put every old value back whatever happens."""
    old = [(m, n, getattr(m, n)) for m, n, _ in pairs]
    try:
        for m, n, v in pairs:
            setattr(m, n, v)
        yield
    finally:
        for m, n, v in reversed(old):
            setattr(m, n, v)


def expect_raise(fn: Callable[[], Any], what: str, fired: list[str]) -> None:
    try:
        fn()
    except (VaultInputError, AssertionError) as e:
        fired.append(what)
        print(f"  fires: {what} ({type(e).__name__})", flush=True)
        return
    raise AssertionError(f"the check did not fire: {what}")


# ================================================================================ the Databento step (system python)
def header_span(p: Path) -> tuple[str, str]:
    import databento as db
    m = db.DBNStore.from_file(str(p)).metadata
    return (pd.Timestamp(int(m.start), tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
            pd.Timestamp(int(m.end), tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ"))


def check_ends(files: list[Path], by: str, what: str) -> list[dict[str, str]]:
    out = []
    for f in files:
        s, e = header_span(f)
        if e > by:
            raise VaultInputError(f"{what}: {f.name} ends {e}, after {by}; it would decode records past the cut")
        out.append({"file": f.name, "start": s, "end": e})
    return out


def check_disjoint(spans: list[dict[str, str]], what: str) -> None:
    by_dir: dict[str, list[tuple[str, str]]] = {}
    for s in spans:
        by_dir.setdefault(s.get("job", ""), []).append((s["start"], s["end"]))
    for j, iv in by_dir.items():
        iv.sort()
        for (a0, a1), (b0, b1) in zip(iv, iv[1:]):
            if b0 < a1:
                raise VaultInputError(f"{what}: two files of job {j} overlap ({a0}..{a1} and {b0}..{b1}); a day would count twice")


def job_ids() -> dict[str, str]:
    rec = json.loads((REPO / "data" / "ledger_free_pull_jobs.json").read_text(encoding="utf-8"))
    ids = {j["label"]: j["job"]["id"] for j in rec["jobs"]}
    tail = json.loads((REPO / "data" / "ledger_a6_tail_pull_jobs.json").read_text(encoding="utf-8"))
    ids["a6-tail-ohlcv1s"] = next(j["job"]["id"] for j in tail["jobs"] if j["label"] == "a6-tail-ohlcv1s")
    return ids


def vault_files(labels: tuple[str, ...]) -> Callable[[], list[Path]]:
    """The vault's `files()`: every year file of the main free pull's jobs (2017 -> 2026-09-18), not the tail."""
    def files() -> list[Path]:
        ids, raw = job_ids(), MAIN_DATA / "raw" / "databento"
        out = [f for lb in labels for f in sorted((raw / ids[lb]).glob("*.ohlcv-1s.dbn.zst"))]
        if not out:
            raise VaultInputError("no vault input files")
        return out
    return files


def masked_records(p: Path, cut_ns: int) -> np.ndarray:
    """Every record of one file stamped before the cut. Past the cut only `ts_event` is read."""
    import databento as db
    parts = []
    for arr in db.DBNStore.from_file(str(p)).to_ndarray(count=2_000_000):
        k = arr["ts_event"] < np.uint64(cut_ns)
        if k.any():
            parts.append(arr[k].copy())
    return np.concatenate(parts) if parts else np.zeros(0)


def canonical(a: np.ndarray) -> np.ndarray:
    return a[np.lexsort((a["instrument_id"], a["ts_event"]))]


def tail_equals_main() -> dict[str, Any]:
    """The main pull's 2025 year files, before 2025-03-01, against the separate Jan-Feb 2025 tail pull, record for
    record (every field). Decides whether the vault build (main files, no tail) can keep the in-sample prefix."""
    ids, raw = job_ids(), MAIN_DATA / "raw" / "databento"
    cut_ns = int(pd.Timestamp(TS_CUT_IN).value)
    tail = [masked_records(f, cut_ns) for f in sorted((raw / ids["a6-tail-ohlcv1s"]).glob("*.ohlcv-1s.dbn.zst"))]
    main = [masked_records(f, cut_ns) for lb in ("ohlcv1s-CL", "ohlcv1s-NG", "ohlcv1s-TAS")
            for f in sorted((raw / ids[lb]).glob("*.ohlcv-1s.dbn.zst")) if f.name.split("-")[2].startswith("2025")]
    t, m = canonical(np.concatenate(tail)), canonical(np.concatenate(main))
    lo = int(pd.Timestamp("2025-01-01T00:00:00Z").value)
    m = m[m["ts_event"] >= np.uint64(lo)]
    same = len(t) == len(m) and all(np.array_equal(t[f], m[f]) for f in t.dtype.names if f != "publisher_id")
    return {"tail_records": int(len(t)), "main_2025_records_before_cut": int(len(m)), "identical_every_field": bool(same),
            "fields": list(t.dtype.names)}


def build_dbn(cut: str, files_fn: Callable[[], list[Path]] | None, mb_files_fn: Callable[[], list[Path]] | None,
              out_dir: Path, workers: int, ts_by: str) -> dict[str, Any]:
    WP = _load("build_window_volume_panel")
    MB = _load("build_ng_minute_bars")
    raw = MAIN_DATA / "raw" / "databento"
    wp_pairs = [(WP, "RAW", raw), (WP, "CUT", cut)] + ([(WP, "files", files_fn)] if files_fn else [])
    out_dir.mkdir(parents=True, exist_ok=True)
    rep: dict[str, Any] = {}
    with held(wp_pairs):
        fl = WP.files()
        rep["wp_files"] = check_ends(fl, ts_by, "window panel")
        for s, f in zip(rep["wp_files"], fl):
            s["job"] = f.parent.name
        if files_fn:
            check_disjoint(rep["wp_files"], "window panel")
        expect_cuts({"WP.CUT": cut}, {"WP.CUT": WP.CUT})
        t0 = time.time()
        text, summary = WP.build(workers)
        rep["wp_min"] = round((time.time() - t0) / 60, 2)
    wp_gz = gz_like_main(text)
    (out_dir / NAMES["wp"]).write_bytes(wp_gz)
    (out_dir / NAMES["wp_sum"]).write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    mb_pairs = [(MB, "RAW", raw), (MB, "CUT", cut), (MB, "PANEL", out_dir / NAMES["wp"])] + \
        ([(MB, "files", mb_files_fn)] if mb_files_fn else [])
    with held(mb_pairs):
        fl = MB.files()
        rep["mb_files"] = check_ends(fl, ts_by, "minute bars")
        expect_cuts({"MB.CUT": cut}, {"MB.CUT": MB.CUT})
        t0 = time.time()
        gz, summ = MB.build(workers)
        rep["mb_min"] = round((time.time() - t0) / 60, 2)
    (out_dir / NAMES["mb"]).write_bytes(gz)
    (out_dir / NAMES["mb_sum"]).write_text(summ, encoding="utf-8", newline="\n")
    rep["sha256"] = {NAMES["wp"]: sha(wp_gz), NAMES["mb"]: sha(gz)}
    return rep


def prove_dbn(workers: int) -> int:
    t0 = time.time()
    out = STAGE / "prove"
    fz = frozen_sha()
    rep = build_dbn(CUT_IN, None, None, out, workers, TS_CUT_IN)
    res: dict[str, Any] = {"proof": "the two Databento builders at the in-sample cut, against the Stage A freeze", **rep}
    res["window_panel_sha256"] = same_sha((out / NAMES["wp"]).read_bytes(), fz[NAMES["wp"]], NAMES["wp"])
    res["minute_bars_sha256"] = same_sha((out / NAMES["mb"]).read_bytes(), fz[NAMES["mb"]], NAMES["mb"])
    for k in ("wp_sum", "mb_sum"):
        if (out / NAMES[k]).read_text(encoding="utf-8") != (REPO / "data" / NAMES[k]).read_text(encoding="utf-8"):
            raise VaultInputError(f"{NAMES[k]} does not reproduce the committed summary")
    res["summaries_reproduce"] = True
    fired: list[str] = []
    bent = bytearray((out / NAMES["mb"]).read_bytes())
    bent[len(bent) // 2] ^= 1
    expect_raise(lambda: same_sha(bytes(bent), fz[NAMES["mb"]], "one bit flipped"), "sha: one bit of the minute bars flipped", fired)
    res["checks_fired"] = fired
    res["tail_vs_main_2025"] = tail_equals_main()
    res["runtime_min"] = round((time.time() - t0) / 60, 2)
    (STAGE / "prove_dbn.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(res, indent=1))
    return 0


# ================================================================================ the panel step (uv)
def restrict_by_column(src: Path, col: str, before: str) -> tuple[bytes, dict[str, Any]]:
    """Header + every row whose `col` (an ISO date, or a datetime starting with one) is before `before`, as TEXT: the
    csv module splits each line into strings to find the date field, and no field of a dropped row is converted."""
    opener = gzip.open if src.suffix == ".gz" else open
    out = io.StringIO()
    kept = dropped = 0
    last = ""
    with opener(src, "rt", encoding="utf-8", newline="") as f:
        header = f.readline()
        names = next(csv.reader([header]))
        if col not in names:
            raise VaultInputError(f"{src.name}: no column {col}")
        i = names.index(col)
        out.write(header)
        buf: list[str] = []
        quotes = 0
        for line in f:
            buf.append(line)
            quotes += line.count('"')
            if quotes % 2:  # a quoted field with a newline: keep reading until it closes
                continue
            rec = "".join(buf)
            buf, quotes = [], 0
            d = next(csv.reader([rec]))[i][:10]
            if len(d) != 10 or d[4] != "-" or d[7] != "-":
                raise VaultInputError(f"{src.name}: {col} is not an ISO date on a data row")
            if d < before:
                out.write(rec)
                kept += 1
                last = max(last, d)
            else:
                dropped += 1
    return gzip.compress(out.getvalue().encode("utf-8"), mtime=0), {"kept": kept, "dropped": dropped, "last_kept": last}


def stage_catalogue(stage: Path, before: str) -> dict[str, Any]:
    """A repo root holding the three catalogue panels restricted before `before`, and a manifest of their digests."""
    import backtest_framework.data.panel_catalogue as PC
    info, files = {}, []
    for name, col in CATALOGUE.items():
        spec = PC.spec_for(name)
        rel = spec.path
        if spec.date_col != col or spec.date_format != "iso_day":
            raise VaultInputError(f"{name}: the catalogue cuts on {spec.date_col} ({spec.date_format}), not {col}")
        gz, info[name] = restrict_by_column(MAIN_DATA.parent / rel, col, before)
        p = stage / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(gz)
        files.append({"path": rel, "sha256": sha(gz), "bytes": len(gz)})
    (stage / "data").mkdir(parents=True, exist_ok=True)
    (stage / "data" / "data_manifest.json").write_text(json.dumps({"files": files}, indent=1) + "\n", encoding="utf-8", newline="\n")
    return info


@contextlib.contextmanager
def staged_panels(stage: Path) -> Iterator[None]:
    import backtest_framework.data.panels as P
    clear = [P._manifest, P.panel_names, P._entries_by_name]
    for c in clear:
        c.cache_clear()
    try:
        with held([(P, "REPO", stage), (P, "MANIFEST", stage / "data" / "data_manifest.json")]):
            yield
    finally:
        for c in clear:
            c.cache_clear()


def modules() -> dict[str, Any]:
    """Every builder of the panel step, imported first (an import re-copies a builder's CUT into the gate copies)."""
    FS = _load("estimate_fut_share")
    CAL = _load("build_ledger_calendar")
    FP = _load("build_predicted_flow_panel")
    R = _load("run_h2_ng_stage_a")
    H = sys.modules["run_h1a_stage_a"]
    if CAL.U is not FP.U:
        raise VaultInputError("the calendar and the flow panel no longer share one check_uscf module")
    return {"FS": FS, "CAL": CAL, "FP": FP, "R": R, "H": H, "U": FP.U}


def cut_state(M: dict[str, Any]) -> dict[str, Any]:
    FP, CAL, FS, R, H, U = M["FP"], M["CAL"], M["FS"], M["R"], M["H"], M["U"]
    return {"FP.CUT": FP.CUT, "FP.LAST": FP.LAST, "U.G.RESERVED_FROM": U.G.RESERVED_FROM,
            "U.GCL.G.RESERVED_FROM": U.GCL.G.RESERVED_FROM, "CAL.CUT": CAL.CUT, "CAL.LAST": CAL.LAST,
            "FS.A6_CONSTANTS": tuple(FS.A6_CONSTANTS), "R.CUT": R.CUT, "H.CUT": H.CUT}


def expected_cuts(cut: str, last: str, a6: tuple[str, ...]) -> dict[str, Any]:
    return {"FP.CUT": cut, "FP.LAST": last, "U.G.RESERVED_FROM": cut, "U.GCL.G.RESERVED_FROM": cut, "CAL.CUT": cut,
            "CAL.LAST": last, "FS.A6_CONSTANTS": tuple(a6), "R.CUT": cut, "H.CUT": cut}


def expect_cuts(want: dict[str, Any], got: dict[str, Any]) -> None:
    bad = {k: (got.get(k), v) for k, v in want.items() if got.get(k) != v}
    if bad:
        raise VaultInputError(f"a cut constant does not hold the value this run means (got, want): {bad}")


def cut_pairs(M: dict[str, Any], cut: str, last: str, a6: tuple[str, ...]) -> list[tuple[Any, str, Any]]:
    FP, CAL, FS, R, H, U = M["FP"], M["CAL"], M["FS"], M["R"], M["H"], M["U"]
    return [(FP, "CUT", cut), (FP, "LAST", last), (U.G, "RESERVED_FROM", cut), (U.GCL.G, "RESERVED_FROM", cut),
            (CAL, "CUT", cut), (CAL, "LAST", last), (FS, "A6_CONSTANTS", tuple(a6)), (R, "CUT", cut), (H, "CUT", cut)]


def build_panels(M: dict[str, Any], cut: str, last: str, a6: tuple[str, ...], dbn_dir: Path, stage: Path,
                 out_dir: Path) -> dict[str, Any]:
    """Steps 3-6 with every cut held, reading the staged catalogue panels and the Databento step's outputs."""
    FS, CAL, FP, R, H, U = M["FS"], M["CAL"], M["FP"], M["R"], M["H"], M["U"]
    out_dir.mkdir(parents=True, exist_ok=True)
    rep: dict[str, Any] = {"staged": stage_catalogue(stage, cut)}
    for name in ("fund_nav_daily", "fut_settle_strip"):  # a short input would drop the last days silently
        if rep["staged"][name]["last_kept"] < last:
            raise VaultInputError(f"{name} ends {rep['staged'][name]['last_kept']}, short of {last}: rebuild it first")
    rawu = MAIN_DATA / "raw" / "uscf"
    paths = [(FS, "A6_OUT_ROWS", out_dir / NAMES["fs"]), (FS, "A6_OUT_SUM", out_dir / NAMES["fs_sum"]),
             (CAL, "ROLLCAL", rawu), (U, "ROLLCAL", rawu),
             (FP, "PANEL", dbn_dir / NAMES["wp"]), (FP, "FSHARE", out_dir / NAMES["fs"]), (FP, "FSUM", out_dir / NAMES["fs_sum"]),
             (H, "FLOW", out_dir / NAMES["fp_day"]), (H, "PANEL", dbn_dir / NAMES["wp"]), (H, "FSHARE", out_dir / NAMES["fs"]),
             (H, "CAL", out_dir / NAMES["cal"]),
             (R, "FLOW", out_dir / NAMES["fp_day"]), (R, "BARS", dbn_dir / NAMES["mb"]), (R, "PANEL", dbn_dir / NAMES["wp"]),
             (R, "CAL", out_dir / NAMES["cal"])]
    want = expected_cuts(cut, last, a6)
    fs_globals = ("RESERVED_FROM", "LAST", "LAST_ANCHOR", "SWAP_Q_LAST", "OUT_ROWS", "OUT_SUM")
    fs_before = {n: getattr(FS, n) for n in fs_globals}
    fs_g_before = FS.G.RESERVED_FROM
    try:
        with staged_panels(stage), held(cut_pairs(M, cut, last, a6) + paths):
            expect_cuts(want, cut_state(M))
            t0 = time.time()
            FS.main(["--seal", "a6"])  # sets its own four constants from A6_CONSTANTS and its gate copy's cut
            if (FS.RESERVED_FROM, FS.LAST, FS.LAST_ANCHOR, FS.SWAP_Q_LAST) != tuple(a6) or FS.G.RESERVED_FROM != cut:
                raise VaultInputError("estimate_fut_share did not run at the intended constants")
            rep["fs_min"] = round((time.time() - t0) / 60, 2)
            expect_cuts(want, cut_state(M))
            t0 = time.time()
            text = CAL.build()
            (out_dir / NAMES["cal"]).write_text(text, encoding="utf-8", newline="\n")
            rep["cal_min"] = round((time.time() - t0) / 60, 2)
            expect_cuts(want, cut_state(M))
            t0 = time.time()
            day_b, con_b, summ = FP.build()
            (out_dir / NAMES["fp_day"]).write_bytes(day_b)
            (out_dir / NAMES["fp_con"]).write_bytes(con_b)
            (out_dir / NAMES["fp_sum"]).write_text(summ, encoding="utf-8", newline="\n")
            rep["fp_min"] = round((time.time() - t0) / 60, 2)
            expect_cuts(want, cut_state(M))
            t0 = time.time()
            d = R.build(read_returns=True)["d"]
            g = R.signed(d)
            rep["d630_min"] = round((time.time() - t0) / 60, 2)
    finally:
        for n, v in fs_before.items():  # FS.main assigns its module globals; put them back
            setattr(FS, n, v)
        FS.G.RESERVED_FROM = fs_g_before
    tab = pd.DataFrame({"day": d["day"].to_numpy(), "traded": d["traded"].to_numpy() & np.isfinite(g),
                        "absI_usd": d["absI_usd"].to_numpy(float), "g": np.where(np.isfinite(g), g, 0.0)})
    tab.to_csv(out_dir / NAMES["table"], index=False, encoding="utf-8", lineterminator="\n", float_format="%.17g")
    rep["sha256"] = {NAMES[k]: sha((out_dir / NAMES[k]).read_bytes()) for k in ("fs", "cal", "fp_day", "fp_con", "table")}
    rep["table_rows"], rep["table_days"] = int(len(tab)), [str(tab["day"].min()), str(tab["day"].max())]
    return rep


def d630_answer(tab: pd.DataFrame) -> dict[str, Any]:
    g = tab.loc[tab["traded"], "g"].to_numpy(float)
    return {"n": int(len(g)), "gate_mean": float(g.mean())}


def check_d630(got: dict[str, Any]) -> None:
    if got["n"] != D630_KNOWN["n"] or abs(got["gate_mean"] - D630_KNOWN["gate_mean"]) > 1e-9:
        raise VaultInputError(f"D630's trade table: {got} against the frozen result's {D630_KNOWN}")


def d649_answer(tab: pd.DataFrame) -> dict[str, Any]:
    P = _load("ledger_vault_pp_ng")
    tr = tab["traded"].to_numpy(bool)
    take = P.select(np.array([]), np.array([]), tr, tab["absI_usd"].to_numpy(float), tab["g"].to_numpy(float))
    s = P.score(tab["g"].to_numpy(float), take)
    if s["trades"] != P.KNOWN["trades"] or not math.isclose(s["mng_net_per_trade"], P.KNOWN["mng_net_per_trade"], abs_tol=0.005):
        raise VaultInputError(f"D649's known answer: {s['trades']} trades, {s['mng_net_per_trade']:.4f} against {P.KNOWN}")
    return {k: s[k] for k in ("trades", "mng_gross_per_trade", "mng_net_per_trade", "t_gross")}


def prove_panels() -> int:
    t0 = time.time()
    fz = frozen_sha()
    dbn = STAGE / "prove"
    for k in ("wp", "mb"):
        same_sha((dbn / NAMES[k]).read_bytes(), fz[NAMES[k]], f"{NAMES[k]} from --prove dbn (run it first)")
    M = modules()
    expect_cuts(expected_cuts(CUT_IN, LAST_IN, A6_IN), cut_state(M))  # the frozen modules' own values
    rep = build_panels(M, CUT_IN, LAST_IN, A6_IN, dbn, STAGE / "repo_in", dbn)
    res: dict[str, Any] = {"proof": "steps 3-6 at the in-sample cut, against the Stage A freeze", **rep}
    for k in ("fs", "cal", "fp_day", "fp_con"):
        res[f"{k}_sha256"] = same_sha((dbn / NAMES[k]).read_bytes(), fz[NAMES[k]], NAMES[k])
    if (dbn / NAMES["fs_sum"]).read_text(encoding="utf-8") != (REPO / "data" / NAMES["fs_sum"]).read_text(encoding="utf-8"):
        raise VaultInputError("the fut-share A6 summary does not reproduce")
    a, b = (json.loads(p.read_text(encoding="utf-8")) for p in (dbn / NAMES["fp_sum"], REPO / "data" / NAMES["fp_sum"]))
    for s_ in (a, b):  # the staged catalogue panels carry their own digests; everything else must match
        for r in (s_.get("reads") or {}).values():
            if isinstance(r, dict):
                r.pop("sha256", None)
    if a != b:
        raise VaultInputError("the flow panel's summary differs beyond the staged panels' digests")
    res["summaries_reproduce"] = "fut-share A6 exact; flow panel exact but for the staged panels' own sha256"
    tab = pd.read_csv(dbn / NAMES["table"], encoding="utf-8", dtype={"day": str})
    res["d630"] = d630_answer(tab)
    check_d630(res["d630"])
    res["d649_known_answer"] = d649_answer(tab)
    if expected_cuts(CUT_IN, LAST_IN, A6_IN) != cut_state(M):
        raise VaultInputError("a cut was not restored")
    fired: list[str] = []
    expect_raise(lambda: check_d630({**res["d630"], "n": res["d630"]["n"] - 1}), "D630: one traded day missing", fired)
    expect_raise(lambda: check_d630({**res["d630"], "gate_mean": res["d630"]["gate_mean"] + 1e-8}), "D630: mean + $1e-8", fired)
    P = _load("ledger_vault_pp_ng")
    take = P.select(np.array([]), np.array([]), tab["traded"].to_numpy(bool), tab["absI_usd"].to_numpy(float),
                    tab["g"].to_numpy(float))
    t2 = tab.copy()
    t2.loc[t2.index[take][-1], "g"] += 500.0  # the last TAKEN day: its own decision cannot move, its MNG net does
    expect_raise(lambda: d649_answer(t2), "D649: the last taken day's g + $500", fired)
    expect_raise(lambda: expect_cuts(expected_cuts(CUT_IN, LAST_IN, A6_IN), {**cut_state(M), "U.GCL.G.RESERVED_FROM": "2024-01-01"}),
                 "cut audit: CL's gate copy left at 2024-01-01", fired)
    res["checks_fired"] = fired
    res["runtime_min"] = round((time.time() - t0) / 60, 2)
    (STAGE / "prove_panels.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(res, indent=1, default=str))
    return 0


# ================================================================================ the joint run
def refuse(word: str | None) -> bool:
    if not (word or "").strip():
        print("refused: the vault is read only in the joint run, on the principal's word (A10; D630 s.8)")
        return True
    return False


def build_vault(step: str, workers: int, word: str, anchor: str | None, swap_q: str | None) -> int:
    JOINT.mkdir(parents=True, exist_ok=True)
    if step == "dbn":
        if (JOINT / NAMES["mb"]).exists():
            raise VaultInputError("the vault Databento outputs exist; they are built once")
        rep = build_dbn(CUT_V, vault_files(("ohlcv1s-CL", "ohlcv1s-NG", "ohlcv1s-TAS")), vault_files(("ohlcv1s-NG",)),
                        JOINT, workers, TS_SEAL_V)
        # prefix stability: the in-sample rows of the vault build are the frozen rows
        fz = frozen_sha()
        for k, col in (("wp", 2), ("mb", 0)):
            new = gz_text_rows_before(JOINT / NAMES[k], col, CUT_IN)
            old = gz_text_rows_before(MAIN_DATA / NAMES[k], col, CUT_IN)
            rep[f"{k}_in_sample_prefix_identical"] = new == old
            if new != old:
                raise VaultInputError(f"{NAMES[k]}: the vault build's rows before 2025-03-01 differ from the frozen file")
        rep["frozen"] = {NAMES["wp"]: fz[NAMES["wp"]], NAMES["mb"]: fz[NAMES["mb"]]}
        (JOINT / "dbn_manifest.json").write_text(json.dumps({"principals_word": word, **rep}, indent=1) + "\n",
                                                 encoding="utf-8", newline="\n")
        print(json.dumps(rep, indent=1))
        return 0
    if not (anchor and swap_q):
        raise VaultInputError("--fut-share-anchor and --swap-q-last are the principal's choice for the vault; no default")
    if (JOINT / NAMES["table"]).exists():
        raise VaultInputError("the vault trade table exists; it is built once")
    M = modules()
    a6 = (CUT_V, VAULT_END, anchor, swap_q)
    stage = STAGE / "repo_vault"
    rep = build_panels(M, CUT_V, VAULT_END, a6, JOINT, stage, JOINT)
    tab =pd.read_csv(JOINT / NAMES["table"], encoding="utf-8", dtype={"day": str})
    v = tab[(tab["day"] >= VAULT_FROM) & (tab["day"] <= VAULT_END)]
    v.to_csv(JOINT / "d630_vault_trade_table.csv", index=False, encoding="utf-8", lineterminator="\n", float_format="%.17g")
    rep["vault_days"], rep["vault_traded"] = int(len(v)), int(v["traded"].sum())
    rep["vault_traded_with_g_exactly_zero"] = int((v["traded"] & (v["g"] == 0)).sum())  # a missing bar books 0 (audit)
    # the in-sample part may move only where A6's interpolation is not point-in-time (days after its last anchor)
    ins = tab[tab["day"] < VAULT_FROM].reset_index(drop=True)
    ref = pd.read_csv(STAGE / "prove" / NAMES["table"], encoding="utf-8", dtype={"day": str})
    j = ins.merge(ref, on="day", how="outer", suffixes=("", "_in"), indicator=True)
    moved = j[(j["_merge"] != "both") | (j["traded"] != j["traded_in"]) | (j["absI_usd"] != j["absI_usd_in"]) | (j["g"] != j["g_in"])]
    rep["in_sample_days_moved"] = {"n": int(len(moved)), "first": str(moved["day"].min()) if len(moved) else None}
    if len(moved) and moved["day"].min() <= A6_IN[2]:
        raise VaultInputError(f"the vault build moved an in-sample day on or before {A6_IN[2]}: {moved['day'].min()}")
    rep["d649_input"] = str(JOINT / "d630_vault_trade_table.csv")
    (JOINT / "panels_manifest.json").write_text(json.dumps({"principals_word": word, "a6_vault": a6, **rep}, indent=1,
                                                           default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(rep, indent=1, default=str))
    return 0


def gz_text_rows_before(p: Path, field: int, before: str) -> bytes:
    with gzip.open(p, "rt", encoding="utf-8", newline="") as f:
        out = [f.readline()]
        out += [ln for ln in f if ln.split(",", field + 1)[field] < before]
    return "".join(out).encode("utf-8")


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fired: list[str] = []
    for argv in (["--build-vault", "dbn"], ["--build-vault", "panels"], ["--build-vault", "panels", "--principals-word", " "]):
        if main(argv) != REFUSED:
            raise AssertionError(f"{argv} ran without the principal's word")
    class _A:
        CUT, LAST = CUT_IN, LAST_IN
    try:
        with held([(_A, "CUT", CUT_V), (_A, "LAST", VAULT_END)]):
            assert (_A.CUT, _A.LAST) == (CUT_V, VAULT_END)
            raise ValueError("inside")
    except ValueError:
        pass
    if (_A.CUT, _A.LAST) != (CUT_IN, LAST_IN):
        raise AssertionError("held() did not restore after a raise")
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        (t / "a.csv").write_text('date,fund,note\n2025-02-28,BOIL,"a, b"\n2025-03-03,BOIL,SECRET\n2024-12-31,KOLD,"x\ny"\n',
                                 encoding="utf-8", newline="\n")
        gz, inf = restrict_by_column(t / "a.csv", "date", CUT_IN)
        body = gzip.decompress(gz).decode("utf-8")
        assert body == 'date,fund,note\n2025-02-28,BOIL,"a, b"\n2024-12-31,KOLD,"x\ny"\n' and inf["dropped"] == 1, (body, inf)
        (t / "b.csv").write_text("date,fund\n20250228,BOIL\n", encoding="utf-8", newline="\n")
        expect_raise(lambda: restrict_by_column(t / "b.csv", "date", CUT_IN), "restrict: a non-ISO date", fired)
        expect_raise(lambda: restrict_by_column(t / "b.csv", "ref", CUT_IN), "restrict: a missing column", fired)
    want = expected_cuts(CUT_IN, LAST_IN, A6_IN)
    expect_cuts(want, dict(want))
    expect_raise(lambda: expect_cuts(want, {**want, "FS.A6_CONSTANTS": ("2025-03-01", "2025-02-28", "2024-12-31", "2025-Q1")}),
                 "cut audit: one A6 constant moved", fired)
    expect_raise(lambda: same_sha(b"abc", sha(b"abd"), "synthetic"), "same_sha: one byte", fired)
    expect_raise(lambda: check_disjoint([{"job": "J", "start": "2025-01-01", "end": "2025-03-01"},
                                         {"job": "J", "start": "2025-02-01", "end": "2025-12-31"}], "synthetic"),
                 "disjoint: two overlapping files of one job", fired)
    check_disjoint([{"job": "J", "start": "2025-01-01", "end": "2025-03-01"}, {"job": "K", "start": "2025-01-01", "end": "2025-12-31"}], "ok")
    expect_raise(lambda: check_d630({"n": 1027, "gate_mean": D630_KNOWN["gate_mean"]}), "D630 known answer: n - 1", fired)
    rec = np.zeros(4, dtype=[("ts_event", "<u8"), ("instrument_id", "<u4"), ("close", "<i8")])
    rec["ts_event"], rec["instrument_id"], rec["close"] = [3, 1, 2, 1], [1, 2, 1, 1], [30, 12, 20, 11]
    c = canonical(rec)
    assert c["close"].tolist() == [11, 12, 20, 30], c
    # the real modules import and carry the frozen in-sample cuts (no data is read)
    M = modules()
    expect_cuts(expected_cuts(CUT_IN, LAST_IN, A6_IN), cut_state(M))
    with held(cut_pairs(M, CUT_V, VAULT_END, (CUT_V, VAULT_END, "2026-06-30", "2026-Q2"))):
        expect_cuts(expected_cuts(CUT_V, VAULT_END, (CUT_V, VAULT_END, "2026-06-30", "2026-Q2")), cut_state(M))
    expect_cuts(expected_cuts(CUT_IN, LAST_IN, A6_IN), cut_state(M))
    print(f"selftest OK: vault modes refused without the word; held() restores on a raise; {len(fired)} checks fired: {fired}; "
          "the real modules carry the frozen cuts, the vault cuts hold and restore")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prove", choices=("dbn", "panels"))
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--build-vault", choices=("dbn", "panels"))
    ap.add_argument("--principals-word", default=None)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--fut-share-anchor", default=None, help="estimate_fut_share's LAST_ANCHOR for the vault (the principal's)")
    ap.add_argument("--swap-q-last", default=None, help="estimate_fut_share's SWAP_Q_LAST for the vault (the principal's)")
    a = ap.parse_args(argv)
    if a.build_vault:
        if refuse(a.principals_word):
            return REFUSED
        return build_vault(a.build_vault, a.workers, a.principals_word, a.fut_share_anchor, a.swap_q_last)
    if a.selftest:
        return selftest()
    if a.prove == "dbn":
        return prove_dbn(a.workers)
    if a.prove == "panels":
        return prove_panels()
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
