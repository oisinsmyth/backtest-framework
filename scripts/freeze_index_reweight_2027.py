"""Freeze, and verify, the index-reweight model for the January 2027 forward event (IR-A10; deposit s.11 / R-D8).

The freeze is written by `scripts/freeze.py` to data/index_reweight/FROZEN_2027.json (IR-A16: this repository has no
root `results/`; the first freeze, written there, is kept as FROZEN_2027_superseded_4945c1f.json). It hashes the code (text,
LF-pinned), the inputs (bytes) and the parameters (`data/index_reweight/frozen_2027_params.json`). After it, a code
change is allowed only as a logged bug fix, versioned in INDEX_REWEIGHT_FLOW_AMENDMENTS.md, under a NEW frozen file.

    uv run python scripts/freeze_index_reweight_2027.py --verify
    uv run python scripts/freeze_index_reweight_2027.py --freeze --instruction "the principal, <date>: '<words>'"
    uv run python scripts/freeze_index_reweight_2027.py --dry-run DIR      # a freeze into DIR, then a verify

Outputs of runs made AFTER the freeze by the frozen code (gate_c0.json, c0_signcheck.json, stage_r*.json, Track 2)
are not hashed: they are what the frozen code produces.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = "data/index_reweight"
FROZEN = f"{OUT_DIR}/FROZEN_2027.json"
PARAMS = "data/index_reweight/frozen_2027_params.json"
CODE = [f"scripts/{n}.py" for n in (
    "run_gate_r0", "gate_0b_ng_nav", "build_fund_panel", "fill_strip_holes_2020_sierra", "build_ke_settle_strip",
    "fetch_westmetall_lme", "sierra_index_reweight_download", "sierra_ui", "settlement_windows",
    "verify_settlement_windows_vwap", "build_gsci_inputs", "build_index_window_flow_panel", "c0_design",
    "power_gate_c0", "run_gate_c0", "check_c0_sierra_sign", "r_design", "r_common", "power_r_stages", "run_stage_r1",
    "run_stage_r2", "run_stage_r3", "record_index_reweight_2027", "freeze_index_reweight_2027")] + [
    "src/backtest_framework/data/panels.py", "src/backtest_framework/data/recorder.py",
    "src/backtest_framework/instruments/future.py"]
IR = "data/index_reweight"
FIXTURES = ["data/fixtures/fut_settle_strip.csv.gz", "data/settlement_windows.csv",
            "data/settlement_windows_vwap_check.json", f"{IR}/methodology_facts.json"] + [
    f"{IR}/weights/{y}.csv" for y in range(2016, 2027)] + [f"{IR}/{n}" for n in (
    "gsci_rpdw.csv", "gsci_schedule.csv", "gsci_cpw.csv", "gate_r0.json", "gate_r0_rerun.json",
    "drift_tracker_daily_rerun.csv.gz", "ke_settle_strip.csv.gz", "lme_westmetall_daily.csv.gz",
    "lme_copper_westmetall_daily.csv.gz", "strip_holes_2020_sierra.csv", "window_flow_daily.csv.gz",
    "power_c0.json", "power_r.json", "sierra_download_record.json", "sierra_download_record_ice.json")]


def run(args: list[str]) -> int:
    return subprocess.run([sys.executable, str(REPO / "scripts" / "freeze.py"), *args], cwd=REPO, check=False).returncode


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--dry-run", metavar="DIR")
    ap.add_argument("--instruction")
    a = ap.parse_args()
    missing = [p for p in CODE + FIXTURES + [PARAMS] if not (REPO / p).exists()]
    if missing:
        raise SystemExit(f"missing inputs: {missing}")
    common = ["--params", PARAMS, "--code", *CODE, "--fixtures", *FIXTURES]
    if a.dry_run:
        rc = run(["--name", "2027", "--evaluation-days", "5", "--spec", "dry-run",
                  "--instruction", "dry run of the machinery; not the freeze", "--out", a.dry_run, *common])
        return rc or run(["--verify", str(Path(a.dry_run) / "FROZEN_2027.json"), *common])
    if a.freeze:
        if not a.instruction:
            raise SystemExit("--freeze needs --instruction: the principal's words, verbatim, with a date")
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True,
                              check=True).stdout.strip()
        (REPO / OUT_DIR).mkdir(parents=True, exist_ok=True)
        return run(["--name", "2027", "--evaluation-days", "5", "--spec", head, "--instruction", a.instruction,
                    "--out", OUT_DIR, *common])
    if a.verify:
        return run(["--verify", FROZEN, *common])
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
