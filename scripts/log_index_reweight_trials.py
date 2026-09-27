"""The index-reweight R-stages' trials log, built from the frozen runners' own outputs (IR-A16; D636 s.7).

D636 promises that every configuration evaluated in Stages R1-R3 is logged, and that a surviving Sharpe carries a
Deflated Sharpe Ratio over the trial count. The frozen runners (`run_stage_r{1,2,3}.py`, IR-A10/A16) write no trials
file, and editing them would break the freeze. So this script, OUTSIDE the freeze, derives the log after each run
from each runner's JSON output (outputs are not hashed): every block that carries a trade count and a mean is one
configuration evaluated.

    uv run python scripts/log_index_reweight_trials.py              # after each R-stage run
    uv run python scripts/log_index_reweight_trials.py --selftest

-> data/index_reweight/trials.csv, in D592's union schema through `validation.programme.TrialsCsv` (append-only; the
programme counter pools it with every other document's). `doc` = INDEX_REWEIGHT_FLOW_PREREG.md; `family` = the
registered family of the stage (R1 -> "index H-R1", R2 -> "index H-R2", R3 -> "index H-R3(b)"). Columns used: stage,
construction (the block's path in the output), n_obs, mean_gross, mean_net, p_boot (the block's p), notes (Holm p,
pass, mean cost or mean, and the output file's sha256). **When rows are first appended, amend
`tests/unit/test_programme.py`'s TRIALS_CSV_FILES in the same commit.**

A block is a CONFIGURATION if it carries `n` and at least one of `mean_gross`, `mean_net` or `mean`. Blocks under
`groups`, `component_line`, `audits`, `reads`, `kappa`, `power`, `snr_by_year` and `deviations` describe a
configuration already counted or are inputs, and are not counted again. Only configurations not yet logged are
appended; a stage already logged whose output has since vanished raises.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from backtest_framework.validation.programme import TrialsCsv

REPO = Path(__file__).resolve().parents[1]
IR = REPO / "data" / "index_reweight"
STAGES = {"R1": IR / "stage_r1.json", "R2": IR / "stage_r2.json", "R3": IR / "stage_r3.json"}
FAMILY = {"R1": "index H-R1", "R2": "index H-R2", "R3": "index H-R3(b)"}
DOC = "INDEX_REWEIGHT_FLOW_PREREG.md"
OUT = IR / "trials.csv"
SKIP = {"groups", "component_line", "audits", "reads", "kappa", "power", "snr_by_year", "deviations"}
MEANS = ("mean_gross", "mean_net", "mean")


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


def rows_for(stage: str, p: Path) -> list[dict]:
    raw = p.read_bytes()
    doc = json.loads(raw.decode("utf-8"))
    sha = hashlib.sha256(raw).hexdigest()
    out = []
    for path, d in configurations(doc):
        extra = {k: d.get(k) for k in ("p_holm", "pass", "mean_cost", "mean") if d.get(k) is not None}
        out.append({"trial_id": f"index:{stage}:{'/'.join(path) or '.'}", "doc": DOC, "family": FAMILY[stage],
                    "stage": stage, "construction": "/".join(path), "n_obs": d.get("n"),
                    "mean_gross": d.get("mean_gross"), "mean_net": d.get("mean_net"), "p_boot": d.get("p"),
                    "notes": "; ".join(f"{k}={v}" for k, v in extra.items()) + f"; source_sha256={sha}"})
    return out


def build(stages: dict[str, Path] = STAGES, out: Path = OUT) -> int:
    log = TrialsCsv(out)
    logged = log.rows()
    logged_stages = {r["stage"] for r in logged}
    gone = sorted(s for s in logged_stages if not stages[s].exists())
    if gone:
        raise SystemExit(f"REFUSING: stage(s) {gone} were logged before and their output is now missing")
    have = {r["trial_id"] for r in logged}
    added = 0
    for stage, p in stages.items():
        if not p.exists():
            continue
        rows = rows_for(stage, p)
        ids = [r["trial_id"] for r in rows]
        if len(ids) != len(set(ids)):
            raise SystemExit(f"{stage}: two configurations share a trial_id")
        for r in rows:
            if r["trial_id"] not in have:
                log.append(r)
                added += 1
    total = log.count() if out.exists() else 0
    print(f"{out.name}: {added} configurations appended, {total} logged in all (the DSR's count for this document)")
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
        st = {"R1": p1, "R2": td / "absent.json", "R3": td / "absent3.json"}
        build(st, out)
        ids = sorted(r["trial_id"] for r in TrialsCsv(out).rows())
        assert ids == ["index:R1:A", "index:R1:B", "index:R1:robustness/B_k2", "index:R1:robustness/cost_x2"], ids
        build(st, out)
        assert TrialsCsv(out).count() == 4, "a second call must append nothing"
        p1.unlink()
        try:
            build(st, out)
            raise AssertionError("a logged stage whose output vanished must raise")
        except SystemExit as e:
            assert "REFUSING" in str(e)
    print("selftest: 4 checks fire as they must (found, described blocks skipped, idempotent, a vanished stage raises)")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else build())
