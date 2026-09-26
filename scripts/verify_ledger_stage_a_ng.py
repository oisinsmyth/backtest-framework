"""Verify that the frozen NG Stage A of the settlement flow ledger has not moved (amendment A10; the principal,
2026-09-26: "freeze Stage A"). The freeze is `data/FROZEN_ledger_stage_a_ng.json`, written by `scripts/freeze.py`.

It hashes the same code (text, LF-pinned) and inputs (bytes) and raises on any change. A change to any of them
restarts Stage A under a NEW frozen file (ledger §13A.4). Run it before the joint vault run and before any Stage B
work that imports these files.

    uv run python scripts/verify_ledger_stage_a_ng.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FROZEN = "data/FROZEN_ledger_stage_a_ng.json"
PARAMS = "data/ledger_stage_a_ng_params.json"
CODE = [f"scripts/{n}.py" for n in (
    "build_predicted_flow_panel", "check_uscf_months_and_rolls", "gate_0b_ng_nav", "gate_0b_cl_nav",
    "build_ledger_calendar", "estimate_fut_share", "build_window_volume_panel", "build_ng_minute_bars",
    "build_signed_window_panel", "sierra_bulk_download", "run_h1a_stage_a", "ledger_power_h1a",
    "ledger_power_signed_h1", "ledger_power_h2_ng", "run_signed_h1_stage_a", "run_h2_ng_stage_a")] + [
    "src/backtest_framework/ledger/flows.py", "src/backtest_framework/data/panels.py",
    "src/backtest_framework/validation/component_series.py", "src/backtest_framework/validation/dsr.py"]
FIXTURES = [f"data/{n}" for n in (
    "ledger_predicted_flow_daily.csv.gz", "ledger_predicted_flow_contracts.csv.gz",
    "ledger_window_volume_daily.csv.gz", "ledger_calendar_flags.csv", "ledger_fut_share_daily_a6.csv.gz",
    "ng_minute_bars.csv.gz", "ledger_signed_window_daily.csv.gz", "sierra_ledger_download_record.json",
    "ledger_signed_h1_stage_a.json", "ledger_h2_ng_stage_a.json", "ledger_power_signed_h1.json",
    "ledger_power_h2_ng.json")]


def main() -> int:
    cmd = [sys.executable, str(REPO / "scripts" / "freeze.py"), "--verify", FROZEN, "--params", PARAMS,
           "--code", *CODE, "--fixtures", *FIXTURES]
    return subprocess.run(cmd, cwd=REPO, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
