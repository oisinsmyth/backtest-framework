"""The 2020 settlement-strip holes (2020-02-27 and 2020-06-30), filled from Sierra Chart's daily settlements for the
15 CME components of BCOM (the principal, 2026-09-27: "fill the holes and rerun R0"; D634-RESULT §5 ruling 1,
amendment IR-A14).

For each component and hole date, the contracts Gate R0 needs are the month's lead and next (Table 9a). Their Sierra
daily files are downloaded, and a settlement is filled ONLY where the strip (or KE's strip) has none for that
(root, contract, date). Sierra's daily Close is the exchange settlement (IR-A13).

Known answer (raises): on the strip days on either side of each hole (2020-02-26, 02-28, 06-29, 07-01), every
needed contract's Sierra Close equals the strip's settlement exactly, where both exist.

    uv run python scripts/fill_strip_holes_2020_sierra.py --queue     # Sierra daily files for the needed contracts
    uv run python scripts/fill_strip_holes_2020_sierra.py --build     # -> data/index_reweight/strip_holes_2020_sierra.csv
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "index_reweight" / "strip_holes_2020_sierra.csv"
HOLES = ("2020-02-27", "2020-06-30")
NEIGHBOURS = ("2020-02-26", "2020-02-28", "2020-06-29", "2020-07-01")
LETTER = "FGHJKMNQUVXZ"


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def needed() -> list[dict[str, Any]]:
    G = _load("run_gate_r0", "run_gate_r0.py")
    D = _load("sierra_index_reweight_download", "sierra_index_reweight_download.py")
    table = G.lead_table()
    ex = {code: exch for code, exch in D.ROOTS.values()}
    out = []
    for comp in G.CME_COMPS:
        root = G.COMP[comp][1]
        for d in HOLES:
            L, N = G.lead_next(table[G.COMP[comp][2]], int(d[:4]), int(d[5:7]))
            # both holes fall after BD10, when the index holds only the next contract (b = 1): the next is required;
            # a lead that still trades is filled too, but its absence (an expired lead) is not an error
            for (y, m), req in {L: L == N, N: True}.items():
                out.append({"comp": comp, "root": root, "hole": d, "ym": (y, m), "required": req,
                            "sierra": f"{root}{LETTER[m - 1]}{str(y)[2:]}-{ex[root]}",
                            "strip": f"{root}{LETTER[m - 1]}{y % 10}"})
    return out


def queue() -> None:
    D = _load("sierra_index_reweight_download", "sierra_index_reweight_download.py")
    syms = sorted({n["sierra"] for n in needed()})
    D.queue(syms, "dly")
    print(f"{len(syms)} daily files requested")


def build() -> pd.DataFrame:
    G = _load("run_gate_r0", "run_gate_r0.py")
    st = G.load_panel("fut_settle_strip", reserved_from=G.CUT, usecols=["root", "contract", "ref", "settle"]).frame
    ke = pd.read_csv(G.KE_STRIP, encoding="utf-8", dtype={"root": str, "contract": str, "ref": str})
    strip = pd.concat([st, ke], ignore_index=True)
    strip = strip[strip["ref"].isin(HOLES + NEIGHBOURS)]
    have = {(r, c, d): float(s) for r, c, d, s in zip(strip["root"], strip["contract"], strip["ref"], strip["settle"])}
    rows, checked = [], 0
    for n in needed():
        p = G.SC_DATA / f"{n['sierra']}.dly"
        if not p.exists():
            raise RuntimeError(f"{p.name} is missing: run --queue first")
        s = pd.read_csv(p, skipinitialspace=True, encoding="utf-8")
        s.columns = [c.strip() for c in s.columns]
        close = dict(zip(pd.to_datetime(s["Date"]).dt.strftime("%Y-%m-%d"), s["Close"].astype(float)))
        for d in NEIGHBOURS:
            k = (n["root"], n["strip"], d)
            if k in have and d in close:
                checked += 1
                if abs(have[k] - close[d]) > 1e-6:
                    raise RuntimeError(f"known answer failed: {n['sierra']} {d} Sierra {close[d]} vs strip {have[k]}")
        k = (n["root"], n["strip"], n["hole"])
        if k not in have:
            if n["hole"] not in close:
                if n["required"]:
                    raise RuntimeError(f"{n['sierra']} has no settlement on {n['hole']}")
                continue
            rows.append({"root": n["root"], "contract": n["strip"], "ref": n["hole"], "settle": close[n["hole"]],
                         "source": f"Sierra Chart daily {n['sierra']}"})
    if checked < 50:
        raise RuntimeError(f"known answer covered only {checked} neighbour cells")
    df = pd.DataFrame(rows).drop_duplicates(["root", "contract", "ref"]).sort_values(["ref", "root", "contract"])
    df.to_csv(OUT, index=False, encoding="utf-8", lineterminator="\n")
    print(f"filled {len(df)} settlements ({df['root'].nunique()} roots); known answer exact on {checked} "
          f"neighbour cells")
    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", action="store_true")
    ap.add_argument("--build", action="store_true")
    a = ap.parse_args()
    if a.queue:
        queue()
    if a.build:
        build()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
