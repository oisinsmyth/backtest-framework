"""Prove, quarter by quarter, which quarters BOIL and KOLD held NO swaps — from their audited filings.

Extended 2026-09-24: SCO (AITODO 1d) and the two USCF funds UNG and USO (AITODO 1e, `uscf_statement`).
USCF prints the swap lines only when the fund held swaps. An absent line counts as zero ONLY when
the statement never mentions a swap; otherwise the period is unparsed. UNG's 2024-Q2 10-Q wrote
"on close OTC commodity swap contracts", and the nine-months check caught the silent zero that
would otherwise have followed. The USCF parse also records each quarter's futures P&L
(`futures_pl_usd`), which sizes a quarter whose swaps opened and closed inside it.

The settlement ledger's P1 term needs each fund's daily futures share `f_fut`. No free daily source
exists (AITODO item 1). But a quarter can be proven futures-only exactly, without daily data:

    a fund held no swap agreement on any day of a quarter  ⇐  its statement of operations shows
    no realized and no unrealized swap gain or loss for that quarter, AND its schedule of
    investments shows no swap line at either bounding quarter-end.

A swap held for even one day accrues a non-zero gain or loss on the index move, so zero on both
lines, with nothing open at either end, leaves no day on which one was held.

Sources, all already recorded by D620 under `data/raw/recorder/sec_fund_filings/`:
  * Q1–Q3: each 10-Q's three-month column;
  * Q4: the 10-K's full-year column minus the Q3 10-Q's nine-month column (exact integer
    arithmetic; the dollar figures are whole);
  * quarter-end swap lines: `data/fixtures/fund_holdings_quarterly.csv.gz` (D620).

A period whose statement cannot be parsed is UNPROVEN — never assumed zero.

Controls, each able to fire:
  * BOIL 2023-Q1..Q3 held swaps at quarter-end (D620) and MUST show non-zero swap P&L;
  * UCO held swaps at every quarter-end and MUST show non-zero swap P&L in every quarter read;
  * every Q3 10-Q's nine-month figure MUST equal the sum of its three quarters.

    uv run python scripts/prove_swap_free_quarters.py            # build and write the JSON
    uv run python scripts/prove_swap_free_quarters.py --check    # rebuild and compare byte for byte
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
FILES = REPO / "data" / "raw" / "recorder" / "sec_fund_filings"
HOLDINGS = REPO / "data" / "fixtures" / "fund_holdings_quarterly.csv.gz"
OUT = REPO / "data" / "ledger_swap_free_quarters.json"
FUNDS = ("BOIL", "KOLD", "SCO", "UCO")  # UCO is the positive control; SCO added 2026-09-24 (AITODO 1d)
FIRST, LAST = "2016-12-31", "2025-06-30"


class ProofError(RuntimeError):
    pass


def _b620():
    spec = importlib.util.spec_from_file_location("b620", REPO / "scripts" / "build_fund_holdings_quarterly.py")
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ProofError("cannot load scripts/build_fund_holdings_quarterly.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["b620"] = mod
    spec.loader.exec_module(mod)
    return mod


B = _b620()
from backtest_framework.data.recorder import Recorder  # noqa: E402

_SOO = re.compile(r"(?P<name>PROSHARES [A-Z0-9&,\.'\-/ ]{3,70}?) STATEMENTS? OF OPERATIONS")
_REAL = re.compile(r"Net realized gain \(loss\) on (?P<blk>.*?) Net realized gain \(loss\) ")
_UNREAL = re.compile(
    r"Change in net unrealized appreciation\s*(?:/|\()\s*depreciation\)?\s+on\s+(?P<blk>.*?)\s+"
    r"Change in net unrealized appreciation"
)
_NUM = re.compile(r"\(\s*[\d,]+\s*\)|[\d,]*\d|[—–\-�]")


def _value(tok: str) -> int:
    tok = tok.strip()
    if tok in ("—", "–", "-", "�"):
        return 0
    neg = tok.startswith("(")
    v = int(re.sub(r"[^\d]", "", tok))
    return -v if neg else v


def _swap_line(block: str, ncols: int) -> list[int] | None:
    """The swap-agreements values across the statement's columns; [0]*ncols when the line is absent."""
    at = block.find("Swap agreements")
    if at < 0:
        return [0] * ncols
    rest = block[at + len("Swap agreements"):]
    toks: list[str] = []
    pos = 0
    for m in _NUM.finditer(rest):
        if re.search(r"[A-Za-z]", rest[pos: m.start()]):  # the next line item has begun
            break
        toks.append(m.group(0))
        pos = m.end()
        if len(toks) == ncols:
            break
    return [_value(t) for t in toks] if len(toks) == ncols else None


def statement(text: str, fund: str) -> tuple[list[int], dict[str, list[int] | None]] | None:
    """(column years, {'realized': [...], 'unrealized': [...]}) for `fund`'s statement of operations."""
    for m in _SOO.finditer(text):
        if B._proshares_fund(m.group("name")) != fund:
            continue
        body = text[m.end(): m.end() + 6000]
        end = body.find("See accompanying notes")
        body = body[: end if end > 0 else len(body)]
        head = body[: body.find("Investment Income")] if "Investment Income" in body else body[:300]
        years = [int(y) for y in re.findall(r"\b(20\d\d)\b", head)]
        if not years:
            continue
        r, u = _REAL.search(body), _UNREAL.search(body)
        out = {
            "realized": _swap_line(r.group("blk"), len(years)) if r else None,
            "unrealized": _swap_line(u.group("blk"), len(years)) if u else None,
        }
        return years, out
    return None


#: USCF funds (added 2026-09-24, AITODO 1e): issuer id in D620's index, and the fund's name in its filings.
USCF = {"UNG": ("ung", "United States Natural Gas Fund"), "USO": ("uso", "United States Oil Fund")}
_U_REAL = re.compile(r"Realized gain \(loss\) on (?:closed? )?(?:OTC )?(?:commodity )?swap contracts")  # 'close' is UNG 2024-Q2's typo
_U_UNREAL = re.compile(r"Change in unrealized gain \(loss\) on open (?:OTC )?(?:commodity )?swap contracts")
_U_FREAL = re.compile(r"Realized gain \(loss\) on closed? (?:commodity )?futures contracts")
_U_FUNREAL = re.compile(r"Change in unrealized gain \(loss\) on open (?:commodity )?futures contracts")
_U_COLS = re.compile(r"\b(?:Three|Six|Nine) months ended|\bYear ended")


def _values_after(block: str, at: int, ncols: int) -> list[int] | None:
    rest = block[at:]
    toks: list[str] = []
    pos = 0
    for m in _NUM.finditer(rest):
        if re.search(r"[A-Za-z]", rest[pos: m.start()]):
            break
        toks.append(m.group(0))
        pos = m.end()
        if len(toks) == ncols:
            break
    return [_value(t) for t in toks] if len(toks) == ncols else None


def uscf_statement(text: str, name: str) -> tuple[list[int], dict[str, list[int] | None]] | None:
    """USCF's statement of operations: '<name>, LP (Condensed) Statements of Operations', whose income
    block carries 'Realized gain (loss) on swap contracts' and 'Change in unrealized gain (loss) on
    open OTC commodity swap contracts' only when the fund held swaps; absent lines are zero."""
    for m in re.finditer(re.escape(name) + r", LP (?:Condensed )?Statements of Operations", text):
        body = text[m.end(): m.end() + 5000]
        end = re.search(r"Total [Ii]ncome", body)
        if end is None or "Realized gain (loss) on closed" not in body[: end.start()]:
            continue  # a table-of-contents mention, not the statement
        block = body[: end.start()]
        head = block[: block.find("Income")]
        ncols = len(_U_COLS.findall(head))
        years = [int(y) for y in re.findall(r"\b(20\d\d)\b", head)]
        if ncols == 0 or not years:
            continue
        out: dict[str, list[int] | None] = {}
        mentions_swap = "swap" in block.lower()
        for key, rx in (("realized", _U_REAL), ("unrealized", _U_UNREAL)):
            hit = rx.search(block)
            if hit is None:
                # absent is zero ONLY when the statement never mentions a swap; a wording variant
                # must fail loudly as unparsed, never read as zero (UNG 2024-Q2 wrote 'close')
                out[key] = None if mentions_swap else [0] * ncols
            else:
                out[key] = _values_after(block, hit.end(), ncols)
        # the futures lines too (optional): they size a quarter whose swaps opened and closed inside it
        for key, rx in (("fut_realized", _U_FREAL), ("fut_unrealized", _U_FUNREAL)):
            hit = rx.search(block)
            vals = None if hit is None else _values_after(block, hit.end(), ncols)
            if vals is not None:
                out[key] = vals
        return [years[0]] + [0] * (ncols - 1), out
    return None


def quarter_of(period_end: str) -> str:
    y, mth = period_end[:4], int(period_end[5:7])
    return f"{y}-Q{(mth - 1) // 3 + 1}"


def build() -> dict[str, object]:
    import pandas as pd

    rec = Recorder(B.ROOT)
    every = [r for r in B._index(rec) if r["form"] in ("10-Q", "10-K") and FIRST[:4] <= r["period_end"][:4] <= LAST[:4]]
    idx = [r for r in every if r["issuer"] == "proshares_trust_ii"]
    jobs: list[tuple[str, list[dict[str, str]], Any]] = [
        (f, idx, (lambda text, f=f: statement(text, f))) for f in FUNDS]
    for f, (issuer, name) in USCF.items():
        jobs.append((f, [r for r in every if r["issuer"] == issuer], (lambda text, name=name: uscf_statement(text, name))))
    texts: dict[str, str] = {}
    for r in [r for _f, filings, _p in jobs for r in filings]:
        if r["accession"] in texts:
            continue
        hits = sorted(FILES.glob(f"{r['accession']}__*.htm"))
        if not hits:
            raise ProofError(f"filing {r['accession']} ({r['form']} {r['period_end']}) is in the index but not on disk")
        texts[r["accession"]] = B.flatten(hits[-1].read_bytes())

    h = pd.read_csv(HOLDINGS, encoding="utf-8", dtype=str)
    h["n_swap"] = pd.to_numeric(h["n_swap_lines"], errors="coerce")
    swap_at_end = {(f, q): bool((g["n_swap"].fillna(0) > 0).any()) for (f, q), g in h.groupby(["fund", "period_end"])}

    result: dict[str, object] = {}
    for fund, filings, parse in jobs:
        q3m: dict[str, dict[str, int]] = {}   # quarter -> three-month values
        ytd: dict[str, dict[str, int]] = {}   # period_end -> year-to-date values (Q2, Q3 10-Q; 10-K)
        src: dict[str, str] = {}
        unparsed: list[str] = []
        for r in sorted(filings, key=lambda x: (x["period_end"], x["filed"])):
            st = parse(texts[r["accession"]])
            if st is None:
                unparsed.append(f"{r['form']} {r['period_end']} {r['accession']}: no statement of operations for {fund}")
                continue
            years, lines = st
            if years[0] != int(r["period_end"][:4]):
                unparsed.append(f"{r['form']} {r['period_end']}: first column year {years[0]}")
                continue
            if lines["realized"] is None or lines["unrealized"] is None:
                unparsed.append(f"{r['form']} {r['period_end']} {r['accession']}: swap line present but not parsed")
                continue
            q = quarter_of(r["period_end"])
            got = {k: v for k, v in lines.items() if v is not None}
            if r["form"] == "10-Q":
                q3m[q] = {k: v[0] for k, v in got.items()}
                src[q] = r["accession"]
                if len(years) == 4:  # [3m cur, 3m prior, ytd cur, ytd prior]
                    ytd[r["period_end"]] = {k: v[2] for k, v in got.items()}
            else:  # 10-K: [year, year-1, (year-2)]
                ytd[r["period_end"]] = {k: v[0] for k, v in got.items()}
                src[q] = r["accession"]

        # Q4 = full year minus nine months; Q3's nine months must equal Q1+Q2+Q3.
        checks: list[str] = []
        for pe, full in sorted(ytd.items()):
            y = pe[:4]
            if pe.endswith("-09-30"):
                parts = [q3m.get(f"{y}-Q{i}") for i in (1, 2, 3)]
                if all(parts):
                    common = [k for k in full if all(k in p for p in parts if p is not None)]
                    for k in common:
                        s = sum(p[k] for p in parts if p is not None)
                        if s != full[k]:
                            raise ProofError(f"{fund} {y}: nine-month {k} {full[k]} != Q1+Q2+Q3 {s}")
                    checks.append(f"{y} nine months == Q1+Q2+Q3")
            if pe.endswith("-12-31"):
                nine = ytd.get(f"{y}-09-30")
                if nine is not None:
                    q3m[f"{y}-Q4"] = {k: full[k] - nine[k] for k in full if k in nine}
                    src[f"{y}-Q4"] = f"{src[f'{y}-Q4']} minus {src.get(f'{y}-Q3', '?')} (nine months)"

        rows = {}
        quarters = sorted({quarter_of(r["period_end"]) for r in filings})
        for q in quarters:
            yq, n = int(q[:4]), int(q[-1])
            end_pe = {1: f"{yq}-03-31", 2: f"{yq}-06-30", 3: f"{yq}-09-30", 4: f"{yq}-12-31"}[n]
            start_pe = {1: f"{yq - 1}-12-31", 2: f"{yq}-03-31", 3: f"{yq}-06-30", 4: f"{yq}-09-30"}[n]
            pl = q3m.get(q)
            s_start, s_end = swap_at_end.get((fund, start_pe)), swap_at_end.get((fund, end_pe))
            if pl is None or s_start is None or s_end is None:
                verdict = "UNPROVEN"
            elif pl["realized"] == 0 and pl["unrealized"] == 0 and not s_start and not s_end:
                verdict = "FUTURES_ONLY_PROVEN"
            else:
                verdict = "SWAPS_HELD"
            rows[q] = {
                "verdict": verdict,
                "swap_realized_usd": None if pl is None else pl["realized"],
                "swap_unrealized_change_usd": None if pl is None else pl["unrealized"],
                **({"futures_pl_usd": pl["fut_realized"] + pl["fut_unrealized"]}
                   if pl is not None and "fut_realized" in pl and "fut_unrealized" in pl else {}),
                "swap_line_at_start": s_start,
                "swap_line_at_end": s_end,
                "source": src.get(q),
            }
        result[fund] = {"quarters": rows, "unparsed": unparsed, "checks": checks}

    # Controls that must fire.
    boil = result["BOIL"]["quarters"]  # type: ignore[index]
    for q in ("2023-Q1", "2023-Q2", "2023-Q3"):
        if boil.get(q, {}).get("verdict") != "SWAPS_HELD":
            raise ProofError(f"control failed: BOIL {q} held swaps at quarter-end (D620) but reads {boil.get(q)}")
    uco = result["UCO"]["quarters"]  # type: ignore[index]
    uco_bad = [q for q, v in uco.items() if v["verdict"] == "FUTURES_ONLY_PROVEN"]
    if uco_bad:
        raise ProofError(f"control failed: UCO proven futures-only in {uco_bad}, but it held swaps at every quarter-end")
    # USCF controls (2026-09-24): quarters with a swap line at quarter-end must read SWAPS_HELD.
    for fund, qs in (("UNG", ("2023-Q1", "2023-Q2", "2023-Q3")),
                     ("USO", ("2022-Q2", "2022-Q3", "2022-Q4", "2023-Q1", "2023-Q2", "2023-Q3"))):
        got = result[fund]["quarters"]  # type: ignore[index]
        for q in qs:
            if got.get(q, {}).get("verdict") != "SWAPS_HELD":
                raise ProofError(f"control failed: {fund} {q} held swaps at quarter-end (D620) but reads {got.get(q)}")
    return {
        "spec": "settlement-ledger AITODO item 1: swap-free quarters proven from audited statements of operations",
        "rule": (
            "FUTURES_ONLY_PROVEN when the quarter's swap realized gain/loss and change in unrealized are both zero "
            "(line absent or dash) AND no swap line at either bounding quarter-end; SWAPS_HELD otherwise; "
            "UNPROVEN when a statement or a quarter-end is missing or unparsed. Q4 = 10-K year minus Q3 10-Q nine months."
        ),
        "sources": {"filings": str(FILES.relative_to(REPO)).replace("\\", "/"), "holdings": str(HOLDINGS.relative_to(REPO)).replace("\\", "/")},
        "controls": [
            "BOIL 2023-Q1..Q3 read SWAPS_HELD (they held swaps at quarter-end)",
            "UCO never reads FUTURES_ONLY_PROVEN (it held swaps at every quarter-end)",
            "UNG 2023-Q1..Q3 and USO 2022-Q2..2023-Q3 read SWAPS_HELD (swap lines at quarter-end)",
            "every Q3 nine-month figure equals Q1+Q2+Q3, realized and unrealized",
        ],
        "funds": result,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    doc = build()
    text = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if a.check:
        if OUT.read_text(encoding="utf-8") != text:
            raise ProofError(f"{OUT.name} does not reproduce from the filings")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    OUT.write_text(text, encoding="utf-8", newline="\n")
    for fund in doc["funds"]:  # type: ignore[attr-defined]
        rows = doc["funds"][fund]["quarters"]  # type: ignore[index]
        line = " ".join(f"{q[2:]}:{'F' if v['verdict'] == 'FUTURES_ONLY_PROVEN' else ('S' if v['verdict'] == 'SWAPS_HELD' else '?')}" for q, v in rows.items())
        print(f"{fund:5s} {line}")
        for u in doc["funds"][fund]["unparsed"]:  # type: ignore[index]
            print(f"      unparsed: {u}")
    print(f"wrote {OUT.relative_to(REPO)}; controls passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
