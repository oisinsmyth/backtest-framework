"""The index-reweight R-stages' trials log, built from the frozen runners' own outputs (IR-A16; D636 s.7).

D636 promises that every configuration evaluated in Stages R1-R3 is logged, and that a surviving Sharpe carries a
Deflated Sharpe Ratio over the trial count. The frozen runners (`run_stage_r{1,2,3}.py`, IR-A10/A16) write no trials
file, and editing them would break the freeze. So this script, OUTSIDE the freeze, derives the log after each run
from each runner's JSON output (outputs are not hashed): every block that carries a trade count and a mean is one
configuration evaluated.

    uv run python scripts/log_index_reweight_trials.py              # after each R-stage run; rebuilds the whole log
    uv run python scripts/log_index_reweight_trials.py --selftest

-> data/index_reweight/trials.csv (D592's translation of D636's `results/index_reweight/trials.csv`).

A block is a CONFIGURATION if it carries `n` and at least one of `mean_gross`, `mean_net` or `mean`. Blocks under
`groups`, `component_line`, `audits`, `reads`, `kappa`, `power` and `snr_by_year` describe a configuration already
counted (its four groups, its component line) or are inputs, and are not counted again. The log is rebuilt from
scratch on every call, and a stage's rows are never dropped once its output exists: a stage file that disappears
raises.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
IR = REPO / "data" / "index_reweight"
STAGES = {"R1": IR / "stage_r1.json", "R2": IR / "stage_r2.json", "R3": IR / "stage_r3.json"}
OUT = IR / "trials.csv"
SKIP = {"groups", "component_line", "audits", "reads", "kappa", "power", "snr_by_year", "deviations"}
MEANS = ("mean_gross", "mean_net", "mean")
COLS = ["trial_id", "stage", "role", "path", "n", "mean_gross", "mean_cost", "mean_net", "mean", "p", "p_holm",
        "pass", "source", "source_sha256", "logged_utc"]


def configurations(doc: Any, path: tuple[str, ...] = ()) -> list[tuple[tuple[str, ...], dict]]:
    out: list[tuple[tuple[str, ...], dict]] = []
    if isinstance(doc, dict):
        if "n" in doc and any(k in doc for k in MEANS):
            out.append((path, doc))
        for k, v in doc.items():
            if k in SKIP:
                continue
            out += configurations(v, path + (str(k),))
    elif isinstance(doc, list):
        for i, v in enumerate(doc):
            out += configurations(v, path + (str(i),))
    return out


def rows_for(stage: str, p: Path, now: str) -> list[dict]:
    raw = p.read_bytes()
    doc = json.loads(raw.decode("utf-8"))
    sha = hashlib.sha256(raw).hexdigest()
    rows = []
    for path, d in configurations(doc):
        rows.append({"trial_id": f"{stage}:{'/'.join(path) or '.'}", "stage": stage, "role": path[0] if path else "",
                     "path": "/".join(path), "n": d.get("n"), "mean_gross": d.get("mean_gross"),
                     "mean_cost": d.get("mean_cost"), "mean_net": d.get("mean_net"), "mean": d.get("mean"),
                     "p": d.get("p"), "p_holm": d.get("p_holm"), "pass": d.get("pass"),
                     "source": str(p.relative_to(REPO)).replace("\\", "/"), "source_sha256": sha, "logged_utc": now})
    return rows


def build(stages: dict[str, Path] = STAGES, out: Path = OUT) -> int:
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    logged_before: set[str] = set()
    if out.exists():
        with out.open(encoding="utf-8", newline="") as f:
            logged_before = {r["stage"] for r in csv.DictReader(f)}
    rows: list[dict] = []
    present = set()
    for stage, p in stages.items():
        if p.exists():
            present.add(stage)
            rows += rows_for(stage, p, now)
    gone = logged_before - present
    if gone:
        raise SystemExit(f"REFUSING: stage(s) {sorted(gone)} were logged before and their output is now missing")
    ids = [r["trial_id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit("two configurations share a trial_id")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="\n") as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    per = {s: sum(1 for r in rows if r["stage"] == s) for s in sorted(present)}
    print(f"wrote {out.relative_to(REPO)}: {len(rows)} configurations {per}; total for the DSR = {len(rows)}")
    return 0


def selftest() -> int:
    import tempfile

    doc = {"verdict": {"verdict": "FAIL"}, "A": {"n": 40, "mean_gross": 12.0, "mean_cost": 20.0, "p": 0.3, "p_holm": 0.6,
                                                 "pass": False, "groups": {"n": 40, "mean_gross": 12.0}},
           "B": {"n": 9, "p": 1.0, "mean_gross": 3.0, "mean_cost": 20.0, "note": "too few trades"},
           "robustness": {"cost_x2": {"n": 40, "mean_net": -28.0}, "B_k2": {"n": 7, "mean_gross": 1.0}},
           "component_line": {"n": 40, "mean": 1.0}, "reads": {"x": {"n": 1, "mean": 1}}}
    with tempfile.TemporaryDirectory() as t:
        td = Path(t)
        p1 = td / "stage_r1.json"
        p1.write_text(json.dumps(doc), encoding="utf-8")
        out = td / "trials.csv"
        global REPO
        repo0, REPO = REPO, td
        try:
            build({"R1": p1, "R2": td / "absent.json"}, out)
            with out.open(encoding="utf-8") as f:
                ids = sorted(r["trial_id"] for r in csv.DictReader(f))
            assert ids == ["R1:A", "R1:B", "R1:robustness/B_k2", "R1:robustness/cost_x2"], ids
            p1.unlink()
            try:
                build({"R1": p1}, out)
                raise AssertionError("a logged stage whose output vanished must raise")
            except SystemExit as e:
                assert "REFUSING" in str(e)
        finally:
            REPO = repo0
    print("selftest: 3 checks fire as they must (configurations found, described blocks skipped, a vanished stage raises)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else build())
