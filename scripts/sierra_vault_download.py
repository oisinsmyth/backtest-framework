"""Download Sierra Chart's 1-tick history for the NG contracts the BCOM index held during the VAULT,
2025-03-01 → 2026-09-18, while the trial is free (to 2026-10-17; the principal, 2026-09-26: "Start the vault-period
Sierra download"). Downloading is not reading. The vault is opened only in the joint run (amendment A10).

THE LIST: the lead and next contracts of `gate_0b_ng_nav.contracts_for` on every weekday of the vault: NGK25 … NGX26.

HOW: `sierra_bulk_download`'s own queue, wait and file-span functions, imported, not copied. That file is frozen with
Stage A (A10), so this separate script records the vault list's files to their own record. A file is read only for
its first and last timestamps. The two live contracts (NGX26, NGF26) hold sessions after 2026-09-18, which belong to
D626's unread sample: only their LAST timestamp is read, and no price, volume or side.

Queueing: after a 57081 cancel, opening a chart does not queue its download (see the memory note on Sierra Chart's
quirks), so each empty contract is opened and sent 57078 (Download Data From End of Chart), then its chart is closed.

    uv run python scripts/sierra_vault_download.py --queue     # queue the contracts whose file is empty
    uv run python scripts/sierra_vault_download.py --wait --record
"""
from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import sierra_bulk_download as S  # noqa: E402
import sierra_ui as U  # noqa: E402

OUT = REPO / "data" / "sierra_vault_download_record.json"
VAULT = ("2025-03-01", "2026-09-18")
LETTER = "FGHJKMNQUVXZ"


def vault_list() -> list[str]:
    import gate_0b_ng_nav as G
    out = set()
    for d in pd.bdate_range(*VAULT).strftime("%Y-%m-%d"):
        for y, m in G.contracts_for(d):
            out.add(f"NG{LETTER[m - 1]}{str(y)[2:]}")
    return sorted(out)


def queue(syms: list[str]) -> list[str]:
    todo = [x for x in syms if S.size(x) <= S.HDR]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for x in todo:
        s.sendto(f"{x}-NYMEX.scid".encode(), S.UDP)
        for _ in range(30):
            time.sleep(0.2)
            if any(t.startswith(f"{x}-NYMEX") for _h, t in U.mdi_charts()):
                break
        time.sleep(1.0)
        U.cmd_command(57078)
        time.sleep(1.5)
        U.cmd_close("^" + re.escape(x) + r"-NYMEX")
    print(f"queued {len(todo)}: {todo}", flush=True)
    return todo


def record(syms: list[str]) -> dict[str, Any]:
    today = pd.Timestamp.now().normalize()
    rec: dict[str, Any] = {"vault": VAULT, "contracts": {}}
    for x in syms:
        r = {"bytes": S.size(x), **S.file_span(x)}
        # a live contract has traded only to the last session before today
        exp = min(S.expected_last_day(x), today - pd.offsets.BDay())
        r["expected_last_day"] = str(exp.date())
        r["cut_short"] = bool(r.get("records", 0) > 0 and pd.Timestamp(r["last_utc"][:10])
                              < exp - S.CUT_TOL_BDAYS * pd.offsets.BDay())
        rec["contracts"][x] = r
    OUT.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return rec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", action="store_true")
    ap.add_argument("--wait", action="store_true")
    ap.add_argument("--record", action="store_true")
    a = ap.parse_args(argv)
    syms = vault_list()
    print(f"{len(syms)} vault contracts: {syms}", flush=True)
    if a.queue:
        queue(syms)
    if a.wait:
        S.wait_drained(syms)
    if a.record:
        rec = record(syms)
        miss = [x for x in syms if rec["contracts"][x].get("records", 0) == 0]
        cut = [x for x in syms if rec["contracts"][x]["cut_short"]]
        print(f"recorded {len(syms)}; without data: {miss}; cut short: {cut}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
