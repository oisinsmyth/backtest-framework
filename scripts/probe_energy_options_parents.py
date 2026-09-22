"""D619 — what every candidate CL/NG OPTION parent and every candidate TAS symbol resolves to on
Databento GLBX.MDP3. **Metadata calls only. No batch job, nothing downloaded, zero spend.**

    python scripts/probe_energy_options_parents.py          # SYSTEM interpreter (databento 0.86)

writes `data/tas_symbology_probe.json` (the TAS half, deposit Q3) and
`data/energy_options_parents_probe.json` (the options half, which feeds
`scripts/quote_energy_options_pull.py`).

WHY A PROBE AT ALL — D581's LESSON, RESTATED
--------------------------------------------
`ES.OPT` resolved to the QUARTERLY family ALONE: 54,250 options over 2016-2026 and not one
weekly, because the end-of-month, Friday-weekly and Monday-Thursday daily families are their own
parents (`scripts/quote_es_options_pull.py`, its `WEEKLY_FAMILIES`). A parent symbol is not a
product family; it is whatever the venue happens to hang under that root. **Each candidate is
therefore resolved and COUNTED before any size is quoted**, and a candidate that resolves to
nothing is recorded as resolving to nothing rather than quietly dropped.

WHAT THIS REPLACES. The tracker says NG and CL options open interest is "◐ (statistics schema
held, not built)". That is wrong and this record corrects it: BOTH Databento pulls on disk
(`run_futures_acquisition.py:176,183-188`) used `{root}.FUT` parents, and a full decode of the
2026 definition file — 9,138,836 records — shows `security_type {FUT: 9,138,835, OOF: 1}`. There
is no CL or NG option open interest on this disk at all.

TAS — DEPOSIT Q3, AND WHAT IS ALREADY KNOWN
-------------------------------------------
CME publishes Trade-at-Settlement as its own Globex products: **`CLT` for WTI crude and `NGT`
for Henry Hub natural gas**, adopted under NYMEX/COMEX rules effective 14 September 2009 and
priced at the settlement or within ten ticks of it
(`https://www.cmegroup.com/tools-information/lookups/advisories/market-regulation/NYMEX_COMEX_RA0909-4.html`,
read 2026-09-22). Full scans of the 2026 and 2020 definition files on disk for `raw_symbol`
containing `TAS`, starting `CLT`/`NGT`, or `asset in {CLT, NGT}` found **0 hits in 20.0 M
records** — so if TAS is reachable at all it is reachable only through a pull this repository has
not made, and this probe is what says which.

THE PRINCIPAL'S DECISION OF 2026-09-22: **quote only. No batch job is submitted and nothing is
downloaded from Databento in this round, even at a $0.00 quote.** This file calls
`symbology.resolve` and nothing else.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KEY_FILE = Path.home() / ".config" / "databento" / "key"
DATASET = "GLBX.MDP3"

#: Two windows, a decade apart: the earliest date the GLBX archive carries the index and energy
#: DAY session (D-memory: "usable from 2016-01-04"), and a recent week.
WINDOWS = (("2016-01-04", "2016-01-08"), ("2026-09-01", "2026-09-10"))

#: CL option families. `LO` is the American-style WTI option; `LO1`-`LO5` are the Friday weeklies;
#: `WA` is the WTI average-price (Asian) option and `CL` is included so that "does the FUTURES
#: root carry options under it" is answered rather than assumed.
CL_OPTION_PARENTS = ["LO", "LO1", "LO2", "LO3", "LO4", "LO5", "WA", "CL"]
#: NG option families. `LN` and `ON` are the two spellings CME has used for the Henry Hub option;
#: `ON1`-`ON5` and `LN1`-`LN5` are the weekly candidates; `NG` answers the same question as `CL`.
NG_OPTION_PARENTS = ["LN", "ON", "ON1", "ON2", "ON3", "ON4", "ON5", "LN1", "LN2", "LN3", "NG"]

#: Every shape a TAS instrument could carry. `.FUT`/`.OPT` are Databento parent suffixes; the bare
#: symbols are tried as `raw_symbol` in case TAS is an outright rather than a parent family.
TAS_CANDIDATES = [
    ("CLT.FUT", "parent"), ("NGT.FUT", "parent"),
    ("CLT.OPT", "parent"), ("NGT.OPT", "parent"),
    ("CL.TAS", "parent"), ("NG.TAS", "parent"),
    ("CLT", "raw_symbol"), ("NGT", "raw_symbol"),
    ("CLTV6", "raw_symbol"), ("NGTX6", "raw_symbol"),
    ("CLTF7", "raw_symbol"), ("NGTF7", "raw_symbol"),
]

OUT_TAS = REPO / "data" / "tas_symbology_probe.json"
OUT_OPT = REPO / "data" / "energy_options_parents_probe.json"


def P(*a: object) -> None:
    print(*a, flush=True)


def api_key() -> str:
    """The principal's key, from the environment or `~/.config/databento/key`. Never printed,
    never logged, never placed in a URL (`run_futures_acquisition.py:42`)."""
    k = os.environ.get("DATABENTO_API_KEY")
    if k:
        return k.strip()
    if KEY_FILE.exists():
        return KEY_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(f"no key: set DATABENTO_API_KEY or write {KEY_FILE}")


def resolve(client, symbol: str, stype_in: str, start: str, end: str) -> dict:
    """One `symbology.resolve` call, summarised. An exception is DATA, not a failure: a symbol
    the venue does not know is exactly what this probe is measuring, so the class and message are
    recorded and the probe carries on."""
    try:
        r = client.symbology.resolve(
            dataset=DATASET, symbols=[symbol], stype_in=stype_in,
            stype_out="instrument_id", start_date=start, end_date=end,
        )
    except Exception as exc:  # noqa: BLE001 — the exception IS the observation
        return {"ok": False, "error": type(exc).__name__, "detail": str(exc)[:300],
                "n_resolved": 0, "n_partial": 0, "n_not_found": 0}
    mappings = r.get("result", {}) if isinstance(r, dict) else {}
    ids: set[str] = set()
    for _sym, entries in mappings.items():
        for e in entries:
            if e.get("s"):
                ids.add(str(e["s"]))
    return {
        "ok": True,
        "n_resolved": len(mappings),
        "n_instruments": len(ids),
        "n_partial": len(r.get("partial", []) or []),
        "n_not_found": len(r.get("not_found", []) or []),
        "sample_raw_symbols": sorted(mappings)[:5],
        "sample_instrument_ids": sorted(ids)[:5],
    }


#: The two API errors that are ANSWERS rather than silence: the venue is positively saying that
#: this symbol does not exist in this symbology, not that it could not be reached.
_INVALID = ("symbology_invalid_symbol", "symbology_invalid_request")


def conclude(per_window: dict[str, dict]) -> tuple[str, str]:
    """`present | absent | invalid_symbol | unresolved`, with the reason. Always filled.

    `present`        at least one window resolved at least one instrument id.
    `absent`         every window answered cleanly and resolved zero — the venue knows the call
                     and has nothing under that symbol.
    `invalid_symbol` every window was refused with `symbology_invalid_symbol` (400: the shape is
                     not a symbol in this symbology) or `symbology_invalid_request` (422: the
                     smart symbol could not be resolved). That IS the answer: no such family.
    `unresolved`     anything else raised. The question is not answered and must not be recorded
                     as an answer; a transport error is silence, not a negative.
    """
    oks = [w for w in per_window.values() if w["ok"]]
    n = sum(w.get("n_instruments", 0) for w in oks)
    if n > 0:
        return "present", f"{n} instrument id(s) across {len(oks)} window(s) that answered"
    if oks:
        return "absent", f"{len(oks)} window(s) answered and resolved 0 instruments"
    bad = list(per_window.values())
    if all(any(tag in (w.get("detail") or "") for tag in _INVALID) for w in bad):
        codes = sorted({t for w in bad for t in _INVALID if t in (w.get("detail") or "")})
        return "invalid_symbol", f"every window refused with {codes}: no such family in this symbology"
    errs = sorted({w["error"] for w in bad})
    return "unresolved", f"every window raised {errs}; a transport error is silence, not a negative"


def probe(client, candidates: list[tuple[str, str]]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for symbol, stype in candidates:
        per = {f"{a}..{b}": resolve(client, symbol, stype, a, b) for a, b in WINDOWS}
        verdict, why = conclude(per)
        out[symbol] = {"stype_in": stype, "windows": per, "conclusion": verdict, "reason": why}
        P(f"  {symbol:<10} {stype:<10} {verdict:<10} {why}")
    return out


def main() -> int:
    import databento as db

    c = db.Historical(api_key())
    t0 = time.time()
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    head = {"dataset": DATASET, "windows": [list(w) for w in WINDOWS], "probed_utc": stamp,
            "record": "D619", "calls": "symbology.resolve only; no batch job, nothing downloaded"}

    P("TAS candidates (deposit Q3):")
    tas = probe(c, TAS_CANDIDATES)
    verdicts = {v["conclusion"] for v in tas.values()}
    overall = ("present" if "present" in verdicts
               else "unresolved" if "unresolved" in verdicts
               else "absent")
    OUT_TAS.write_text(json.dumps({
        **head,
        "question": "Deposit Q3: Databento TAS symbology and history coverage for NG and CL",
        "cme_product_codes": {"WTI crude TAS": "CLT", "Henry Hub natural gas TAS": "NGT",
                              "source": "https://www.cmegroup.com/tools-information/lookups/advisories/market-regulation/NYMEX_COMEX_RA0909-4.html",
                              "read_utc": stamp},
        "definition_archive_on_disk": {
            "scanned": "the 2026 and 2020 GLBX definition files, 20.0 M records",
            "raw_symbol contains TAS": 0, "raw_symbol starts CLT or NGT": 0,
            "asset in {CLT, NGT}": 0},
        "candidates": tas,
        "conclusion": overall,
    }, indent=1) + "\n", encoding="utf-8")

    P("\nCL option parents:")
    cl = probe(c, [(f"{s}.OPT", "parent") for s in CL_OPTION_PARENTS])
    P("\nNG option parents:")
    ng = probe(c, [(f"{s}.OPT", "parent") for s in NG_OPTION_PARENTS])
    OUT_OPT.write_text(json.dumps({
        **head,
        "note": "D581: ES.OPT resolved to the quarterlies alone. Each parent is probed, never assumed.",
        "CL": cl, "NG": ng,
        "resolved_parents": sorted([s for s, v in {**cl, **ng}.items() if v["conclusion"] == "present"]),
    }, indent=1) + "\n", encoding="utf-8")

    P(f"\n  TAS conclusion: {overall}")
    P(f"  wrote {OUT_TAS.relative_to(REPO)} and {OUT_OPT.relative_to(REPO)} in {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
