"""Bars for the LIVE page: the same twelve draws, full own-history OHLC per name so the
construction can run from bar 0 in the browser exactly as it does in Python.

    uv run python scripts/d399_emit_live_bars.py

Only bars, dates for the window, and the window start. No lines, no pivots, no parameters -- the
page computes all of that itself from whatever the principal sets. The draw is the declared one
(`d399_new_sample.draw_sample`, same seed), so the panels line up with every earlier twelve-name
page.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "temp" / "d399_live_bars.json"


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main() -> int:
    NS = _load("d399ns", "d399_new_sample.py")
    DR = _load("d399draw", "d399_draw_construction.py")
    RP = _load("rp", "ragged_panel.py")
    UF = _load("d339uf", "d339_universe_floor.py")
    panel, cleaned = RP.load_ragged(*DR.MINING, fee_bps=0.0, dividend_bound=True)
    draw, rej = NS.draw_sample(panel, cleaned, UF, NS.N_DRAW)
    names = []
    for s, st in draw:
        bars = cleaned[s]
        r = lambda a: [round(float(v), 4) for v in a]        # noqa: E731
        names.append(dict(
            symbol=s, start=int(st), n=NS.WIN, m=len(bars),
            dates=[str(b.timestamp)[:10] for b in bars[st:st + NS.WIN]],
            o=r([b.bar.open for b in bars]), h=r([b.bar.high for b in bars]),
            l=r([b.bar.low for b in bars]), c=r([b.bar.close for b in bars])))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dict(seed=NS.SEED, window=NS.WIN, delta=DR.DELTA, names=names),
                              separators=(",", ":")))
    tot = sum(x["m"] for x in names)
    print(f"  wrote {OUT.relative_to(REPO)}: {len(names)} names, {tot:,} bars, "
          f"{OUT.stat().st_size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
