"""The settlement strip through the vault's end, for the joint run's NG input path (slots 3 and 8). The principal,
2026-09-30, approved extending the strip for the vault. The committed fixture (`data/fixtures/fut_settle_strip.csv.gz`,
D556) ends at session 2026-09-10 because `build_fut_settle_strip.py` reads ONE job dir (`RAW`); the pre-lapse
top-up (2026-10-09) adds the statistics from 2026-09-11 in a second job dir. This wrapper runs the builder's own
`cmd_extract` UNCHANGED over both dirs, with a read-time cut, into a SEPARATE file.

    python scripts/build_strip_vault.py --discover                 # headers only: the job dirs and every file's span
    python scripts/build_strip_vault.py --prove [--workers 8]      # SYSTEM python; the cut at the committed strip's end
    python scripts/build_strip_vault.py --selftest                 # synthetic; no DBN record is decoded
    python scripts/build_strip_vault.py --build-vault --principals-word "..." [--workers 8]   # joint run ONLY

WHY A SEPARATE SCRIPT, not a mode of build_ledger_vault_inputs.py: it is a SYSTEM-python Databento step with a
process pool (Windows spawns, so every worker re-imports the main module), like that file's `--prove dbn`; it is the
strip's own data layer, not a D630 builder; and the panel step only needs its output and manifest, which it checks.

THE JOB DIRS are discovered from their job RECORDS, never from a directory listing alone:
  * the original: the one `statistics` / `41 roots` / `downloaded` item of `data/futures_acquisition_manifest.json`
    (GLBX-20260911-SDNLQ6M99S), which must also be `build_fut_settle_strip.RAW`;
  * the top-up: the `statistics 41 roots` job of `data/prelapse_topup_jobs.json`, once it has `downloaded_utc`.
    If the dir carries Databento's `metadata.json`, its query must be statistics / parent / every root's `.FUT`.
Every other GLBX dir holding statistics files (the options pulls, KE, CLT/NGT) is listed by `--discover` and ignored.

THE CUT, precisely. A file is decoded only if its DBN header END is at or before the cut, and a file whose header
START is at or after the cut is never decoded (its header is the only thing read). A file that STRADDLES the cut is
refused: the builder's worker decodes whole files and is not edited, so a straddling file cannot be cut at read time
here. The header window is the batch query's, on the index timestamp `ts_recv` (and `ts_event` <= `ts_recv`), so
every decoded record has both stamps before the cut. The vault's cut is 2026-09-19T00:00:00Z, i.e. 2026-09-18 20:00
EDT: after the last vault session's close (17:00 ET) and after every CME settlement window of 2026-09-18, before any
instant dated 2026-09-19 in ET or UTC. It is the same instant as the NG Databento step's seal (`TS_SEAL_V`), and it
falls on a boundary of the top-up's daily files (`split_duration="day"`), so no file straddles it. Nothing for any
root, CL/NG/HO/RB included, stamped 2026-09-19 or later is decoded (D626's sample, sealed until its read on 10-10).
MEASURED COST OF A WALL-CLOCK CUT (in-sample, the 2024 year file, 239,627 strip rows): the record that wins a strip
row (`keep="last"`) usually arrives after the next UTC midnight (37% of rows; every Friday row arrives the weekend
after), but with a cut at the next UTC midnight after each session 0 rows change value and 401 rows (0.17%; NG 2,
CL 12) have no earlier record and would be absent. At the vault's end only the last few sessions are so exposed.

THE PROOF (`--prove`): the same discovery and selection with the cut at the committed strip's reach,
2026-09-11T00:00:00Z (the header end of its last file). The selected files must be exactly the committed build's
17; the output (temp/strip_vault/prove/fut_settle_strip.csv.gz) must equal the committed fixture: the CSV text
identical, and the gzip bytes identical once the header's 4-byte MTIME (the build time, which pandas writes and the
builder does not pin) is set to the committed file's; the meta's counts, drops and per-root spans identical.

OUTPUTS (the joint run): data/joint_run/ng/fut_settle_strip_vault.csv.gz, its .meta.json (the builder's), and
fut_settle_strip_vault_manifest.json (the principal's word, the cut, every file and span, the builders' hashes, the
output's sha256, the in-sample prefix check). The committed fixture, its meta and data/data_manifest.json are never
written; `build_ledger_vault_inputs.py --build-vault panels` reads the vault strip through its own staged manifest.
"""
from __future__ import annotations

import argparse
import contextlib
import gzip
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Iterator

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import build_fut_settle_strip as S  # noqa: E402  (the builder, loaded unchanged)

MAIN_DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")  # the gitignored raw cache and fixtures
PATTERN = "*.statistics.dbn.zst"
PROVE_CUT = "2026-09-11T00:00:00Z"   # the committed strip's reach: the header end of its last file
VAULT_CUT = "2026-09-19T00:00:00Z"   # 2026-09-18 20:00 EDT; D626: nothing stamped 2026-09-19 or later
VAULT_END, CUT_IN = "2026-09-18", "2025-03-01"
ORIGINAL_JOB = "GLBX-20260911-SDNLQ6M99S"
TOPUP_LABEL = "statistics 41 roots"
MUST_REACH = ("NG", "CL")            # the roots D630's chain reads from the strip (gate_0b_ng_nav, gate_0b_cl_nav)
# LF-normalised sha256 of the builder and the two modules its worker imports, as proved by --prove (2026-10-01)
BUILDERS = {"scripts/build_fut_settle_strip.py": "8fc2690011c65a3c6ec44dd11967e93b501261f671cb3b93874d8955f26b6c22",
            "scripts/build_fut_open_interest.py": "e83fa9c7c975c3c10cf97d36f29d7e2b79490838bb84841b71808f9cf9a8fe2b",
            "scripts/build_fut_breadth_hourly.py": "8ea76301239f231c33d3d3e144dc072a587fb4ab24bd595e0b640b5e192d51c8"}
PROVE_DIR = REPO / "temp" / "strip_vault" / "prove"
JOINT = REPO / "data" / "joint_run" / "ng"
OUT_V = JOINT / "fut_settle_strip_vault.csv.gz"
META_V = JOINT / "fut_settle_strip_vault.meta.json"
MANIFEST_V = JOINT / "fut_settle_strip_vault_manifest.json"
META_SAME = ("rows", "rows_raw", "dropped_exact_zero", "dropped_exact_zero_by_root", "dropped_weekend_refs",
             "dropped_negative_non_CL", "roots", "per_root", "spec", "source", "session_label")
REFUSED = 2


class StripError(RuntimeError):
    pass


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def lf_sha(p: Path) -> str:
    return sha(p.read_bytes().replace(b"\r\n", b"\n"))


def check_builders(pins: dict[str, str] | None = None) -> dict[str, str]:
    got = {rel: lf_sha(REPO / rel) for rel in (pins or BUILDERS)}
    bad = {k: v for k, v in got.items() if v != (pins or BUILDERS)[k]}
    if bad:
        raise StripError(f"the strip builder changed since --prove certified it: {sorted(bad)}")
    return got


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


# ================================================================================ discovery (records, headers)
def header_span(p: Path) -> tuple[str, str]:
    import databento as db
    import pandas as pd
    m = db.DBNStore.from_file(str(p)).metadata
    return (pd.Timestamp(int(m.start), tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
            pd.Timestamp(int(m.end), tz="UTC").strftime("%Y-%m-%dT%H:%M:%SZ"))


def job_dirs(data: Path, need_topup: bool) -> list[dict[str, Any]]:
    """The statistics job dirs, each from its job record. The original first, then the top-up."""
    acq = json.loads((data / "futures_acquisition_manifest.json").read_text(encoding="utf-8"))
    orig = [j for j in acq["items"] if j.get("schema") == "statistics" and j.get("scope") == "41 roots"
            and j.get("state") == "downloaded"]
    if len(orig) != 1 or orig[0]["job_id"] != ORIGINAL_JOB or S.RAW.name != ORIGINAL_JOB:
        raise StripError(f"the original statistics job is not the one record and builder RAW name: {[j.get('job_id') for j in orig]}, "
                         f"RAW {S.RAW.name}")
    out = [{"job": ORIGINAL_JOB, "record": "data/futures_acquisition_manifest.json", "window": orig[0]["window"]}]
    rec_p = data / "prelapse_topup_jobs.json"
    top: list[dict[str, Any]] = []
    if rec_p.exists():
        rec = json.loads(rec_p.read_text(encoding="utf-8"))
        for j in rec.get("jobs", []):
            if j.get("label") != TOPUP_LABEL:
                continue
            if "job" not in j or j.get("schema") != "statistics":
                raise StripError(f"the top-up's statistics job was not submitted: {j}")
            if "downloaded_utc" not in j:
                raise StripError(f"the top-up's statistics job {j['job'].get('id')} is not fully downloaded")
            top.append({"job": j["job"]["id"], "record": "data/prelapse_topup_jobs.json",
                        "window": [rec.get("start"), rec.get("end")]})
    if len(top) > 1:
        raise StripError(f"{len(top)} top-up statistics jobs in the record; expected one")
    if need_topup and not top:
        raise StripError("no downloaded top-up statistics job in data/prelapse_topup_jobs.json; the strip would end 2026-09-10")
    for d in out + top:
        root = data / "raw" / "databento" / d["job"]
        if not root.is_dir() or not sorted(root.glob(PATTERN)):
            raise StripError(f"{root} holds no statistics files")
        mp = root / "metadata.json"
        if mp.exists():
            q = json.loads(mp.read_text(encoding="utf-8"))
            q = q.get("query", q)
            want = {f"{r}.FUT" for r in S.ROOTS}
            syms = set(q.get("symbols") or [])
            if q.get("schema") != "statistics" or q.get("stype_in") != "parent" or not want <= syms:
                raise StripError(f"{d['job']}/metadata.json is not a statistics pull of every root's .FUT parent")
            d["metadata_json_checked"] = True
    return out + top


def other_statistics_dirs(data: Path, known: set[str]) -> list[dict[str, Any]]:
    rows = []
    for d in sorted((data / "raw" / "databento").glob("GLBX-*")):
        if d.name in known or not any(d.glob(PATTERN)):
            continue
        mp = d / "metadata.json"
        q = json.loads(mp.read_text(encoding="utf-8")).get("query", {}) if mp.exists() else {}
        syms = q.get("symbols") or []
        rows.append({"dir": d.name, "files": len(list(d.glob(PATTERN))), "stype_in": q.get("stype_in"),
                     "symbols": syms[:4] + (["..."] if len(syms) > 4 else [])})
    return rows


def select(dirs: list[dict[str, Any]], data: Path, cut: str,
           span: Callable[[Path], tuple[str, str]] = header_span) -> dict[str, Any]:
    """The files decoded at this cut: header end <= cut. A header start >= cut is never decoded; a straddle raises."""
    keep: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    for d in dirs:
        for f in sorted((data / "raw" / "databento" / d["job"]).glob(PATTERN)):
            s, e = span(f)
            row = {"job": d["job"], "file": f.name, "start": s, "end": e, "path": str(f)}
            if e <= cut:
                keep.append(row)
            elif s >= cut:
                excluded.append({k: v for k, v in row.items() if k != "path"})
            else:
                raise StripError(f"{d['job']}/{f.name} spans {s}..{e} across the cut {cut}; the unchanged worker decodes "
                                 "whole files, so it cannot be cut at read time here")
    if not keep:
        raise StripError("no statistics file ends by the cut")
    chrono = sorted(keep, key=lambda r: (r["start"], r["end"]))
    for a, b in zip(chrono, chrono[1:]):
        if b["start"] < a["end"]:
            raise StripError(f"{a['job']}/{a['file']} and {b['job']}/{b['file']} overlap; a settlement would be read twice")
    if [Path(r["path"]) for r in chrono] != sorted(Path(r["path"]) for r in keep):
        raise StripError("the builder sorts files by path, and path order is not time order; keep='last' would not be the latest")
    return {"files": chrono, "excluded": excluded, "reach": max(r["end"] for r in keep)}


# ================================================================================ the extraction (the builder, unchanged)
class _Raw:
    """Stands in for build_fut_settle_strip.RAW, of which cmd_extract calls only `.glob(PATTERN)`."""

    def __init__(self, files: list[Path]) -> None:
        self.files = list(files)
        self.name = "+".join(sorted({f.parent.name for f in files}))

    def glob(self, pattern: str) -> list[Path]:
        if pattern != PATTERN:
            raise StripError(f"cmd_extract asked for {pattern}")
        return list(self.files)


def extract(files: list[dict[str, str]], out: Path, meta: Path, workers: int) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with held([(S, "RAW", _Raw([Path(r["path"]) for r in files])), (S, "STRIP", out), (S, "STRIP_META", meta)]):
        S.cmd_extract(workers)


# ================================================================================ comparisons
def gunzip(b: bytes) -> bytes:
    return gzip.decompress(b)


def with_mtime_of(b: bytes, ref: bytes) -> bytes:
    """`b` with its gzip header MTIME (bytes 4..8) taken from `ref`; both must be single-member gzip, method 8."""
    if b[:3] != b"\x1f\x8b\x08" or ref[:3] != b"\x1f\x8b\x08" or b[3] != ref[3]:
        raise StripError("not two gzip files with the same header flags")
    return b[:4] + ref[4:8] + b[8:]


def same_strip(mine: bytes, committed: bytes) -> dict[str, Any]:
    a, b = gunzip(mine), gunzip(committed)
    if sha(a) != sha(b):
        raise StripError(f"the CSV text differs: {sha(a)} against the committed {sha(b)}")
    norm = with_mtime_of(mine, committed)
    if norm != committed:
        raise StripError("the CSV text is identical but the gzip bytes differ beyond the header MTIME")
    return {"csv_text_sha256": sha(a), "csv_bytes": len(a), "gzip_sha256_raw": sha(mine),
            "gzip_sha256_with_committed_mtime": sha(norm), "committed_sha256": sha(committed),
            "raw_bytes_identical": mine == committed, "only_difference": None if mine == committed else "gzip header MTIME"}


def same_meta(mine: dict[str, Any], committed: dict[str, Any]) -> None:
    bad = [k for k in META_SAME if mine.get(k) != committed.get(k)]
    fm = [(f["file"], f["rows_in"], f["rows_kept"]) for f in mine["files"]]
    fc = [(f["file"], f["rows_in"], f["rows_kept"]) for f in committed["files"]]
    if fm != fc:
        bad.append("files (name, rows_in, rows_kept)")
    if bad:
        raise StripError(f"the meta differs from the committed on {bad}")


def rows_before(gz: bytes, before: str) -> bytes:
    """Header + every row whose `ref` (field 2 of root,contract,ref,settle) is before `before`, as text."""
    lines = gunzip(gz).decode("utf-8").splitlines(keepends=True)
    if not lines or lines[0].strip() != "root,contract,ref,settle":
        raise StripError("not the strip's header")
    return "".join([lines[0]] + [ln for ln in lines[1:] if ln.split(",", 3)[2] < before]).encode("utf-8")


def check_reach(meta: dict[str, Any], end: str, roots: tuple[str, ...] = MUST_REACH) -> dict[str, str]:
    last = {r: meta["per_root"].get(r, {}).get("last", "") for r in meta["roots"]}
    over = {r: v for r, v in last.items() if v > end}
    if over:
        raise StripError(f"rows past the vault's end {end}: {over}")
    short = {r: last[r] for r in roots if last.get(r, "") < end}
    if short:
        raise StripError(f"the strip ends before {end} on {short}")
    return last


# ================================================================================ modes
def discover(data: Path) -> int:
    dirs = job_dirs(data, need_topup=False)
    rep: dict[str, Any] = {"dirs": dirs}
    for cut in (PROVE_CUT, VAULT_CUT):
        sel = select(dirs, data, cut)
        rep[cut] = {"decoded": [f"{r['job']}/{r['file']} {r['start']}..{r['end']}" for r in sel["files"]],
                    "never_decoded": [f"{r['job']}/{r['file']} {r['start']}..{r['end']}" for r in sel["excluded"]],
                    "reach": sel["reach"]}
    rep["ignored_statistics_dirs"] = other_statistics_dirs(data, {d["job"] for d in dirs})
    print(json.dumps(rep, indent=1))
    return 0


def prove(data: Path, workers: int) -> int:
    import time
    t0 = time.time()
    pins = check_builders()
    dirs = job_dirs(data, need_topup=False)
    sel = select(dirs, data, PROVE_CUT)
    orig_reach = max(r["end"] for r in sel["files"] if r["job"] == ORIGINAL_JOB)
    if orig_reach != PROVE_CUT:
        raise StripError(f"the original job's files reach {orig_reach}, not {PROVE_CUT}")
    committed_meta = json.loads((data / "fixtures" / "fut_settle_strip.meta.json").read_text(encoding="utf-8"))
    if [r["file"] for r in sel["files"]] != [f["file"] for f in committed_meta["files"]]:
        raise StripError("the files selected at the proof's cut are not the committed build's")
    out, meta = PROVE_DIR / "fut_settle_strip.csv.gz", PROVE_DIR / "fut_settle_strip.meta.json"
    extract(sel["files"], out, meta, workers)
    committed = (data / "fixtures" / "fut_settle_strip.csv.gz").read_bytes()
    mine = out.read_bytes()
    res: dict[str, Any] = {"proof": "the wrapper at the committed strip's reach reproduces data/fixtures/fut_settle_strip.csv.gz",
                           "cut": PROVE_CUT, "dirs": dirs, "decoded_files": len(sel["files"]),
                           "never_decoded": sel["excluded"], "builders_lf_sha256": pins, **same_strip(mine, committed)}
    mm = json.loads(meta.read_text(encoding="utf-8"))
    same_meta(mm, committed_meta)
    res["meta_same"] = list(META_SAME) + ["files (name, rows_in, rows_kept)"]
    res["rows"] = mm["rows"]
    manifest = json.loads((data / "data_manifest.json").read_text(encoding="utf-8"))
    ent = [e for e in manifest["files"] if e["path"] == "data/fixtures/fut_settle_strip.csv.gz"]
    if len(ent) != 1 or ent[0]["sha256"] != res["gzip_sha256_with_committed_mtime"] or committed_meta["sha256"] != ent[0]["sha256"]:
        raise StripError("the committed strip, its meta and data_manifest.json do not agree on one sha256")
    res["data_manifest_sha256"] = ent[0]["sha256"]
    fired: list[str] = []
    bent = bytearray(gunzip(mine))
    bent[len(bent) // 2] ^= 1
    expect_raise(lambda: same_strip(gzip.compress(bytes(bent), mtime=0), committed), "one bit of the CSV flipped", fired)
    expect_raise(lambda: same_meta({**mm, "rows": mm["rows"] - 1}, committed_meta), "the meta's row count - 1", fired)
    expect_raise(lambda: same_meta({**mm, "files": mm["files"][:-1]}, committed_meta), "one file dropped from the meta", fired)
    res["checks_fired"] = fired
    res["wall_min"] = round((time.time() - t0) / 60, 2)
    (PROVE_DIR.parent / "prove.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(res, indent=1))
    return 0


def build_vault(data: Path, workers: int, word: str) -> int:
    pins = check_builders()
    for p in (OUT_V, META_V, MANIFEST_V):
        if p.exists():
            raise StripError(f"{p.name} exists; the vault strip is built once")
    dirs = job_dirs(data, need_topup=True)
    sel = select(dirs, data, VAULT_CUT)
    if sel["reach"] != VAULT_CUT:
        raise StripError(f"the decoded files reach {sel['reach']}, short of {VAULT_CUT}: the top-up's statistics are missing")
    extract(sel["files"], OUT_V, META_V, workers)
    meta = json.loads(META_V.read_text(encoding="utf-8"))
    last = check_reach(meta, VAULT_END)
    gz = OUT_V.read_bytes()
    committed = (data / "fixtures" / "fut_settle_strip.csv.gz").read_bytes()
    prefix_same = rows_before(gz, CUT_IN) == rows_before(committed, CUT_IN)
    if not prefix_same:
        raise StripError(f"the vault strip's rows before {CUT_IN} differ from the committed strip's")
    rep = {"principals_word": word, "principal_approval": "the principal, 2026-09-30: extend the settlement strip for the vault",
           "cut": VAULT_CUT, "vault_end": VAULT_END, "dirs": dirs, "decoded": [{k: v for k, v in r.items() if k != "path"}
                                                                             for r in sel["files"]],
           "never_decoded": sel["excluded"], "builders_lf_sha256": pins, "out": str(OUT_V.relative_to(REPO)).replace("\\", "/"),
           "sha256": sha(gz), "rows": meta["rows"], "last_ref_per_root": last,
           "roots_short_of_vault_end": {r: v for r, v in last.items() if v < VAULT_END},
           "in_sample_prefix_identical": prefix_same}
    MANIFEST_V.write_text(json.dumps(rep, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in rep.items() if k not in ("decoded", "never_decoded")}, indent=1))
    return 0


# ================================================================================ self-test (synthetic only)
def expect_raise(fn: Callable[[], Any], what: str, fired: list[str]) -> None:
    try:
        fn()
    except (StripError, AssertionError) as e:
        fired.append(what)
        print(f"  fires: {what} ({type(e).__name__})", flush=True)
        return
    raise AssertionError(f"the check did not fire: {what}")


def selftest() -> int:
    fired: list[str] = []
    for argv in (["--build-vault"], ["--build-vault", "--principals-word", " "]):
        if main(argv) != REFUSED:
            raise AssertionError(f"{argv} ran without the principal's word")
    check_builders()
    expect_raise(lambda: check_builders({**BUILDERS, "scripts/build_fut_settle_strip.py": "0" * 64}), "a changed builder", fired)
    with tempfile.TemporaryDirectory() as td:
        data = Path(td)
        raw = data / "raw" / "databento"
        spans: dict[str, tuple[str, str]] = {}

        def mk(job: str, name: str, s: str, e: str) -> None:
            (raw / job).mkdir(parents=True, exist_ok=True)
            (raw / job / name).write_bytes(b"")
            spans[f"{job}/{name}"] = (s, e)

        def span(p: Path) -> tuple[str, str]:
            return spans[f"{p.parent.name}/{p.name}"]

        mk(ORIGINAL_JOB, "glbx-mdp3-20250101-20251231.statistics.dbn.zst", "2025-01-01T00:00:00Z", "2026-01-01T00:00:00Z")
        mk(ORIGINAL_JOB, "glbx-mdp3-20260101-20260910.statistics.dbn.zst", "2026-01-01T00:00:00Z", PROVE_CUT)
        top = "GLBX-20261009-TESTTOPUP1"
        for d in ("20260911", "20260918", "20260919", "20260921"):
            iso = f"{d[:4]}-{d[4:6]}-{d[6:]}"
            nxt = {"20260911": "2026-09-12", "20260918": "2026-09-19", "20260919": "2026-09-20", "20260921": "2026-09-22"}[d]
            mk(top, f"glbx-mdp3-{d}.statistics.dbn.zst", f"{iso}T00:00:00Z", f"{nxt}T00:00:00Z")
        acq = {"items": [{"schema": "statistics", "scope": "41 roots", "state": "downloaded", "job_id": ORIGINAL_JOB,
                          "window": ["2010-06-06", "2026-09-11"]},
                         {"schema": "definition", "scope": "41 roots", "state": "downloaded", "job_id": "X"}]}
        (data / "futures_acquisition_manifest.json").write_text(json.dumps(acq), encoding="utf-8")
        # before the top-up: one dir; the vault refuses
        d1 = job_dirs(data, need_topup=False)
        assert [d["job"] for d in d1] == [ORIGINAL_JOB], d1
        expect_raise(lambda: job_dirs(data, need_topup=True), "discovery: no top-up record", fired)
        rec = {"start": "2026-09-11", "end": "2026-10-09", "jobs": [
            {"label": "ohlcv-1m all symbols", "schema": "ohlcv-1m", "job": {"id": "OTHER"}, "downloaded_utc": "x"},
            {"label": TOPUP_LABEL, "schema": "statistics", "job": {"id": top}}]}
        (data / "prelapse_topup_jobs.json").write_text(json.dumps(rec), encoding="utf-8")
        expect_raise(lambda: job_dirs(data, need_topup=True), "discovery: top-up not downloaded", fired)
        rec["jobs"][1]["downloaded_utc"] = "2026-10-09T12:00:00Z"
        (data / "prelapse_topup_jobs.json").write_text(json.dumps(rec), encoding="utf-8")
        dirs = job_dirs(data, need_topup=True)
        assert [d["job"] for d in dirs] == [ORIGINAL_JOB, top], dirs
        (raw / top / "metadata.json").write_text(json.dumps({"query": {"schema": "statistics", "stype_in": "parent",
                                                                       "symbols": ["ES.FUT"]}}), encoding="utf-8")
        expect_raise(lambda: job_dirs(data, need_topup=True), "discovery: metadata.json lacks the roots", fired)
        (raw / top / "metadata.json").write_text(json.dumps({"query": {"schema": "statistics", "stype_in": "parent",
                                                                       "symbols": [f"{r}.FUT" for r in S.ROOTS] + ["MES.FUT"]}}),
                                                 encoding="utf-8")
        dirs = job_dirs(data, need_topup=True)
        # the cuts
        sp = select(dirs, data, PROVE_CUT, span)
        assert [r["file"][10:18] for r in sp["files"]] == ["20250101", "20260101"] and len(sp["excluded"]) == 4, sp
        sv = select(dirs, data, VAULT_CUT, span)
        assert [r["file"][10:18] for r in sv["files"]] == ["20250101", "20260101", "20260911", "20260918"], sv
        assert [r["file"][10:18] for r in sv["excluded"]] == ["20260919", "20260921"] and sv["reach"] == VAULT_CUT, sv
        expect_raise(lambda: select(dirs, data, "2026-09-18T12:00:00Z", span), "cut: a file straddles the cut", fired)
        mk(top, "glbx-mdp3-20260910.statistics.dbn.zst", "2026-09-10T00:00:00Z", "2026-09-11T00:00:00Z")
        expect_raise(lambda: select(dirs, data, VAULT_CUT, span), "cut: two files overlap across the dirs", fired)
        (raw / top / "glbx-mdp3-20260910.statistics.dbn.zst").unlink()
        early = "GLBX-20200101-EARLYDIR01"
        spans2 = dict(spans)
        spans.clear()
        spans.update({k.replace(top, early): v for k, v in spans2.items()})
        (raw / top).rename(raw / early)
        dirs_bad = [dirs[0], {**dirs[1], "job": early}]
        expect_raise(lambda: select(dirs_bad, data, VAULT_CUT, span), "cut: path order is not time order", fired)
        # the _Raw stand-in and held()
        rw = _Raw([Path("a/x.statistics.dbn.zst")])
        assert rw.glob(PATTERN) == [Path("a/x.statistics.dbn.zst")]
        expect_raise(lambda: rw.glob("*.ohlcv-1m.dbn.zst"), "stand-in: another pattern", fired)
        old = S.RAW
        try:
            with held([(S, "RAW", rw)]):
                assert S.RAW is rw
                raise ValueError("inside")
        except ValueError:
            pass
        assert S.RAW is old, "held() did not restore RAW"
    # the comparisons
    text = b"root,contract,ref,settle\nCL,CLF5,2025-02-28,70.1\nCL,CLG5,2025-03-03,71.2\nNG,NGF5,2024-12-31,3.4\n"
    a, b = gzip.compress(text, mtime=1), gzip.compress(text, mtime=2)
    assert same_strip(a, b)["only_difference"] == "gzip header MTIME"
    expect_raise(lambda: same_strip(gzip.compress(text.replace(b"70.1", b"70.2"), mtime=2), b), "compare: one settlement", fired)
    assert rows_before(a, CUT_IN) == b"root,contract,ref,settle\nCL,CLF5,2025-02-28,70.1\nNG,NGF5,2024-12-31,3.4\n"
    expect_raise(lambda: rows_before(gzip.compress(b"root,ref\n"), CUT_IN), "prefix: not the strip's header", fired)
    meta = {"roots": ["CL", "NG", "ES"], "per_root": {"CL": {"last": "2026-09-18"}, "NG": {"last": "2026-09-18"},
                                                     "ES": {"last": "2026-09-17"}}}
    assert check_reach(meta, VAULT_END)["ES"] == "2026-09-17"
    expect_raise(lambda: check_reach({**meta, "per_root": {**meta["per_root"], "NG": {"last": "2026-09-10"}}}, VAULT_END),
                 "reach: NG ends 2026-09-10", fired)
    expect_raise(lambda: check_reach({**meta, "per_root": {**meta["per_root"], "ES": {"last": "2026-09-21"}}}, VAULT_END),
                 "reach: a row dated 2026-09-21", fired)
    print(f"selftest OK: vault mode refused without the word; {len(fired)} checks fired: {fired}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--discover", action="store_true")
    ap.add_argument("--prove", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--build-vault", action="store_true")
    ap.add_argument("--principals-word", default=None)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--data-root", type=Path, default=MAIN_DATA, help="the data dir holding raw/, fixtures/ and the job records")
    a = ap.parse_args(argv)
    if a.build_vault:
        if not (a.principals_word or "").strip():
            print("refused: the vault strip is built only in the joint run, on the principal's word (A10)")
            return REFUSED
        return build_vault(a.data_root, a.workers, a.principals_word)
    if a.selftest:
        return selftest()
    if a.discover:
        return discover(a.data_root)
    if a.prove:
        return prove(a.data_root, a.workers)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
