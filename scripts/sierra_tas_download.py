"""Download Sierra Chart's 1-tick TAS (trade-at-settlement) history for Stage D of the settlement ledger (deposit §P5;
the principal, 2026-09-26: "Sierra Chart"): the NG TAS month of every held NG contract, in-sample and vault; and
the HO/RB TAS months of the sibling year, for the known-answer check against the exchange's aggressor flag
(`check_sierra_tas_aggressor.py`).

THE LISTS:
  * NG: NGT + the month of every contract in `sierra_bulk_download.contract_list()` (the in-sample holdings) and in
    `sierra_vault_download.vault_list()` (the vault's). Vault files are downloaded and never read (amendment A10).
  * Siblings: HOTX25 … HOTV26 and RBTX25 … RBTV26, the twelve outright TAS months traded 2025-09-25 → 2026-09-18 in
    Databento's free sibling pull.
A file is read only for its first and last timestamps. Files that run past 2026-09-18 (HOTV26, RBTV26, NGTX26) hold
sessions from D626's unread sample. Only their last timestamp is read.

    uv run python scripts/sierra_tas_download.py --queue
    uv run python scripts/sierra_tas_download.py --wait --record
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import sierra_bulk_download as S  # noqa: E402  (frozen with Stage A: imported, never edited)
import sierra_vault_download as V  # noqa: E402

OUT = REPO / "data" / "sierra_tas_download_record.json"
SIBLING_MONTHS = ["X25", "Z25", "F26", "G26", "H26", "J26", "K26", "M26", "N26", "Q26", "U26", "V26"]


def ng_tas_list() -> list[str]:
    held = set(x for x in S.contract_list() if x.startswith("NG")) | set(V.vault_list())
    return sorted(f"NGT{x[2:]}" for x in held)


def sibling_list() -> list[str]:
    return [f"{r}T{m}" for r in ("HO", "RB") for m in SIBLING_MONTHS]


def record(syms: list[str]) -> dict[str, Any]:
    rec: dict[str, Any] = {"contracts": {x: {"bytes": S.size(x), **S.file_span(x)} for x in syms}}
    OUT.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return rec


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", action="store_true")
    ap.add_argument("--wait", action="store_true")
    ap.add_argument("--record", action="store_true")
    a = ap.parse_args(argv)
    syms = ng_tas_list() + sibling_list()
    print(f"{len(syms)} TAS contracts", flush=True)
    if a.queue:
        V.queue(syms)
    if a.wait:
        S.wait_drained(syms, quiet_s=180)
    if a.record:
        rec = record(syms)
        miss = [x for x in syms if rec["contracts"][x].get("records", 0) == 0]
        print(f"recorded {len(syms)}; without data: {miss}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
