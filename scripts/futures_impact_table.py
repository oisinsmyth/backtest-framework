"""D604 -- the futures impact parameter table: `data/futures_impact_params.json`.

    python scripts/futures_impact_table.py --build      # rewrite the artefact from its sources
    python scripts/futures_impact_table.py --show       # print it
    python scripts/futures_impact_table.py --selftest   # re-derive it, compare the COMMITTED
                                                        # bytes by sha256, and prove each refusal

SYSTEM PYTHON. The `day1m_2016_2023` line reads `data/fixtures/fut_day1m.parquet`, and the venv
has no pyarrow (the same split as `scripts/build_fut_cleared_volume_cm.py` and databento). Run it
with `python`, not `uv run`. The library that CONSUMES the artefact
(`backtest_framework/costs/futures_impact.py`) reads only JSON and runs anywhere.

WHAT THE TABLE IS
-----------------
`SETTLEMENT_FLOW_LEDGER_PREREG.md` 5.3 needs two numbers per instrument: `V_d`, a daily volume in
contracts, and `sigma_d`, a daily return standard deviation as a FRACTION. Nothing in this
repository held either for futures in one place. Three committed sources hold pieces of them, on
two different windows, and this file puts all three side by side rather than picking one:

  d511              ADV and a session sigma in dollars, 9 roots, 2025-09-11..2026-09-10.
                    Its price level is not in that artefact; it is taken from the breadth meta's
                    last bar, which is inside the same window, and the provenance says so.
  breadth_meta      A day-session sigma and a notional, 36 roots, at the fixture's last price.
                    NO VOLUME AT ALL, so the line is stored with `adv_contracts` absent and the
                    brick refuses it at construction rather than at bar 3,000.
  day1m_2016_2023   ADV and sigma computed HERE from the minute panel, 36 roots, front-contract
                    sessions 2016-01-04..2023-12-29. This is the DEFAULT line, and the reason is
                    the holdout: the other two are measured on 2025-09..2026-09, which is inside
                    the deposit's sealed vault window and after this repository's 2024-01-01 cut.

Nothing here is typed. Every number is copied from a source key path or computed by
`day1m_line()` from the panel, and every entry carries the key path it came from.

DETERMINISM
-----------
No timestamp, no machine name, no wall time. The artefact is a pure function of its four inputs,
so `--selftest` can rebuild it and compare the committed bytes byte for byte -- which is the only
check that catches an artefact edited by hand after the fact.

THE MULTIPLIER DISAGREEMENT, RECORDED HERE IN D604 AND RESOLVED IN D609
-----------------------------------------------------------------------
A session move in points becomes a sigma in dollars through `usd_per_point`, and this repository
had two answers for seven of the 36 roots. `instruments/future.py:Future.from_specs` fell back to
`data/fut_specs_from_definition.json`'s `tick_usd`, the RAW formula
`mpi * display_factor * uom_qty` with a `/100` applied on `unit_of_measure == "USD"` alone; the
breadth fixture's builder decides the divide by the NOTIONAL test instead. They disagreed by
exactly 100x on ZC, ZS, ZW, ZL, LE and HE (the definition file high) and on SR3 (the definition
file low, because the percent-of-par divide fired on a `uom_qty` that is already dollars per
point). Every one of the seven had `known_tick_usd: null` -- nothing had ever verified them.

**This builder always used the BREADTH value**, which is why every measured number in the
artefact was right while `multiplier_disagreements` was seven rows long, and why regenerating it
under D609 moved that list to `[]` and moved nothing else. D609 put `tick_usd_full_contract` in
the spec file, decided by the same `decide_scaling` the breadth builder runs, and `from_specs`
reads it. The empty list is now a GATE, not a note: `tests/unit/test_futures_impact.py` asserts
both that it is empty and what the seven corrected `usd_per_point` values are, so it cannot pass
by the table losing the roots that used to populate it.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "futures_impact_params.json"
D511 = REPO / "data" / "d511_trade_count.json"
BREADTH_META = REPO / "data" / "fixtures" / "fut_breadth_hourly.meta.json"
DAY1M = REPO / "data" / "fixtures" / "fut_day1m.parquet"

DAY1M_WINDOW = ("2016-01-04", "2023-12-29")
"""The in-sample window. `2023-12-29` is the last session before this repository's 2024-01-01
holdout; `2016-01-04` is where `glbx-archive-lacks-index-futures-day-session-before-2016` says the
day session becomes usable."""

LEDGER_Y = 0.7
DEFAULT_LINE = "day1m_2016_2023"


class ImpactTableError(RuntimeError):
    """A source was missing, incomplete or self-inconsistent. Never a default."""


# ------------------------------------------------------------------ shared inputs


def _panels():
    """`backtest_framework.data.panels` (D609), with `src/` put on the path first.

    Unlike `_future_module` below this is a REAL package import, because `panels.py` uses
    relative imports (`..validation.frozen`) that `spec_from_file_location` cannot resolve. The
    system python this script runs under has no `backtest_framework` installed, so `src/` goes
    on `sys.path`; the chain it pulls in needs numpy and pandas only, both of which this script
    already requires.
    """
    src = str(REPO / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from backtest_framework.data import panels

    return panels


def _future_module():
    """`instruments/future.py` loaded by explicit path.

    By path rather than by import because `scripts/` is not a package and the system python has no
    `backtest_framework` installed; the module itself imports nothing from its own package, which
    is why this works and is checked here rather than assumed.
    """
    path = REPO / "src" / "backtest_framework" / "instruments" / "future.py"
    spec = importlib.util.spec_from_file_location("d604_future", path)
    if spec is None or spec.loader is None:
        raise ImpactTableError(f"[LOAD] cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["d604_future"] = module
    spec.loader.exec_module(module)
    return module


def breadth_specs() -> dict:
    meta = json.loads(BREADTH_META.read_text(encoding="utf-8"))
    specs = meta.get("specs")
    if not isinstance(specs, dict) or not specs:
        raise ImpactTableError(f"[SRC] {BREADTH_META.name} carries no specs block")
    return specs


def breadth_window() -> tuple[str, str]:
    """The breadth fixture's span, read from its own `files` list.

    The meta carries no `span` field -- its `segments` key is the hour labels, not dates -- so the
    window is taken from the raw archive segment NAMES it records
    (`glbx-mdp3-YYYYMMDD-YYYYMMDD.ohlcv-1m.dbn.zst`), which is a number copied from the source
    rather than one typed here. A meta whose files do not parse raises.
    """
    meta = json.loads(BREADTH_META.read_text(encoding="utf-8"))
    starts, ends = [], []
    for name in meta.get("files", []):
        parts = str(name).split("-")
        if len(parts) < 4 or not (parts[2].isdigit() and parts[3][:8].isdigit()):
            raise ImpactTableError(f"[SRC] breadth meta file name {name!r} does not carry dates")
        starts.append(parts[2])
        ends.append(parts[3][:8])
    if not starts:
        raise ImpactTableError(f"[SRC] {BREADTH_META.name} lists no source files")
    lo, hi = min(starts), max(ends)
    return f"{lo[:4]}-{lo[4:6]}-{lo[6:]}", f"{hi[:4]}-{hi[4:6]}-{hi[6:]}"


def multipliers(specs: dict) -> tuple[dict[str, float], list[dict]]:
    """Each root's dollars per quoted point, and every disagreement with `Future.from_specs`.

    The breadth value is `tick_usd_full_contract / tick_price_units` -- the scaled tick divided by
    the tick's own width in points, which is the definition of a multiplier and cannot be off by a
    quote convention the way an unscaled `uom_qty` can.
    """
    Future = _future_module().Future
    upp: dict[str, float] = {}
    clashes: list[dict] = []
    for root, spec in sorted(specs.items()):
        tick_pts = float(spec["tick_price_units"])
        if tick_pts <= 0:
            raise ImpactTableError(f"[SPEC] {root}: tick_price_units={tick_pts}")
        mine = float(spec["tick_usd_full_contract"]) / tick_pts
        upp[root] = mine
        theirs = float(Future.from_specs(root).usd_per_point)
        if abs(theirs - mine) > 1e-9 * max(mine, 1.0):
            clashes.append({
                "root": root, "breadth_meta_usd_per_point": mine,
                "future_from_specs_usd_per_point": theirs,
                "ratio": theirs / mine,
                "scaling_divisor": spec.get("scaling_divisor"),
                "scaling_reason": spec.get("scaling_reason"),
            })
    return upp, clashes


def size_block(root: str, spec: dict, upp: float) -> dict:
    """The root's minimum tradable size, where a micro exists.

    `impact_fraction` is dimensionless and identical at either size; what changes is the NOTIONAL
    the fraction is charged on, and the quantity's units. A caller sizing at MES and dividing by a
    full-size ES ADV would understate `|Q|/V_d` by 10, so the ratio is stated here rather than
    left to be rediscovered.
    """
    full = float(spec["tick_usd_full_contract"])
    sized = float(spec["tick_usd"])
    if sized <= 0 or full <= 0:
        raise ImpactTableError(f"[SPEC] {root}: non-positive tick ({full}, {sized})")
    ratio = full / sized
    return {
        "sized_as": str(spec["sized_as"]),
        "has_micro": bool(spec["has_micro"]),
        "tick_usd_full_contract": full,
        "tick_usd_sized": sized,
        "size_ratio_full_over_sized": ratio,
        "usd_per_point_full": upp,
        "usd_per_point_sized": upp / ratio,
        "provenance": [
            f"data/fixtures/fut_breadth_hourly.meta.json#specs.{root}.sized_as",
            f"data/fixtures/fut_breadth_hourly.meta.json#specs.{root}.tick_usd_full_contract",
            f"data/fixtures/fut_breadth_hourly.meta.json#specs.{root}.tick_usd",
        ],
    }


# ------------------------------------------------------------------ the three lines


def d511_line(specs: dict) -> dict[str, dict]:
    """ADV in contracts and a session sigma in dollars, from `data/d511_trade_count.json`.

    `v_bar` is the mean session volume of the front contract and `sigma_sess` the standard
    deviation of the session's close-minus-open in dollars on ONE FULL contract -- D511's own
    units. The price level is not in that file, so `notional_usd` is taken from the breadth meta's
    `notional_usd`, measured at 2026-09-09, INSIDE d511's own 2025-09-11..2026-09-10 window. It is
    an end-of-window level, not a window mean, and `sigma_fraction` inherits that.
    """
    src = json.loads(D511.read_text(encoding="utf-8"))
    window = (str(src["window"][0]), str(src["window"][1]))
    out = {}
    for row in src["table"]:
        root = str(row["root"])
        if root not in specs:
            raise ImpactTableError(f"[SRC] d511 carries {root}, which the breadth meta does not")
        notional = float(specs[root]["notional_usd"])
        sigma_usd = float(row["sigma_sess"])
        out[root] = {
            "window": list(window),
            "adv_contracts": float(row["v_bar"]),
            "sigma_usd_per_contract": sigma_usd,
            "notional_usd": notional,
            "sigma_fraction": sigma_usd / notional,
            "sessions": int(row["sessions"]),
            "provenance": [
                f"data/d511_trade_count.json#table[root={root}].v_bar",
                f"data/d511_trade_count.json#table[root={root}].sigma_sess",
                f"data/d511_trade_count.json#table[root={root}].sessions",
                f"data/fixtures/fut_breadth_hourly.meta.json#specs.{root}.notional_usd",
            ],
            "notes": "sigma_sess is per FULL contract; notional_usd is the breadth fixture's last "
                     "price (2026-09-09), inside d511's own window but an END-of-window level. "
                     "This window is inside the deposit's sealed vault period.",
        }
    return out


def breadth_line(specs: dict) -> dict[str, dict]:
    """A day-session sigma and a notional, and NO volume, from the breadth fixture's meta.

    `day_session_sigma_usd` is quoted at the root's `sized_as` size -- the micro where one exists,
    so ES's 157.06 is MES dollars, not ES dollars. It is converted to FULL-contract dollars by
    `tick_usd_full_contract / tick_usd`, which is 10 on the index micros and 1 on the 28 roots with
    no micro. `sigma_fraction` is invariant to that conversion, since `notional_usd` is already
    full-size; the conversion is done anyway so the stored dollar sigma means what its name says.
    """
    window = breadth_window()
    out = {}
    for root, spec in sorted(specs.items()):
        ratio = float(spec["tick_usd_full_contract"]) / float(spec["tick_usd"])
        sigma_sized = float(spec["day_session_sigma_usd"])
        sigma_full = sigma_sized * ratio
        notional = float(spec["notional_usd"])
        out[root] = {
            "window": list(window),
            "sigma_usd_per_contract": sigma_full,
            "sigma_usd_at_sized_size": sigma_sized,
            "size_ratio_full_over_sized": ratio,
            "notional_usd": notional,
            "sigma_fraction": sigma_full / notional,
            "n_sessions": int(spec["n_sessions"]),
            "provenance": [
                f"data/fixtures/fut_breadth_hourly.meta.json#specs.{root}.day_session_sigma_usd",
                f"data/fixtures/fut_breadth_hourly.meta.json#specs.{root}.tick_usd_full_contract",
                f"data/fixtures/fut_breadth_hourly.meta.json#specs.{root}.tick_usd",
                f"data/fixtures/fut_breadth_hourly.meta.json#specs.{root}.notional_usd",
                f"data/fixtures/fut_breadth_hourly.meta.json#specs.{root}.n_sessions",
            ],
            "notes": "NO VOLUME in this source, so adv_contracts is absent and this line cannot "
                     "build an impact brick. The sigma is a DAY-SESSION move, measured at the "
                     "sized_as size and converted here to full-contract dollars.",
        }
    return out


def day1m_line(upp: dict[str, float]) -> dict[str, dict]:
    """ADV and sigma computed from `data/fixtures/fut_day1m.parquet`, 2016-01-04..2023-12-29.

    One session = one (root, day) with `present` and `same_front` both true for every bar:
    `present=False` is the breadth fixture's holiday/half-day/thin flag and `same_front=False` is a
    roll, whose close-minus-open is a contract change and not a move (the panel's own meta says
    both).

      ADV            = mean over sessions of the session's summed `volume`, in contracts
      sigma_usd      = std, ddof=1, of (last close - first open) x usd_per_point
      sigma_fraction = sigma_usd / (mean last close x usd_per_point)

    ddof=1 because these are a sample of sessions, not the population of them, and the choice
    changes the eighth digit on 2,000 sessions -- which matters here only because every number in
    this artefact is reproduced with `==`.
    """
    import pyarrow.parquet as pq

    status = _panels().panel_status(DAY1M)
    if status != "present":
        # D609: this sentence used to be hand-copied from `tests/conftest.py` and said the same
        # thing whether or not the manifest listed the file -- which, for a renamed artefact or a
        # typo'd constant, is a false explanation attached to a real failure. `panel_status` is
        # the one implementation of that distinction, so the wrong-path case now says so.
        panels = _panels()
        reason = (
            panels.absent_reason(DAY1M.name)
            if status == "absent_listed"
            else panels.unlisted_message(DAY1M)
        )
        raise ImpactTableError(f"[SRC] {reason}")
    import pandas as pd

    cols = ["root", "day", "bar", "open", "close", "volume", "same_front", "present"]
    pf = pq.ParquetFile(DAY1M)
    # (root, day) -> [volume, bar_min, open_at_min, bar_max, close_at_max, ok]
    # The per-batch work is vectorised in pandas and only the MERGE across batch boundaries is
    # Python -- a session's 420 bars can straddle a record batch, and a per-batch groupby that
    # ignored that would take a mid-session bar's open as the session's.
    acc: dict[tuple[str, str], list] = {}
    for batch in pf.iter_batches(batch_size=2_000_000, columns=cols):
        d = batch.to_pandas()
        d = d[(d["day"] >= DAY1M_WINDOW[0]) & (d["day"] <= DAY1M_WINDOW[1])]
        if d.empty:
            continue
        d = d.sort_values(["root", "day", "bar"], kind="mergesort")
        g = d.groupby(["root", "day"], sort=False)
        part = pd.DataFrame({
            "vol": g["volume"].sum(), "bmin": g["bar"].min(), "bmax": g["bar"].max(),
            "o": g["open"].first(), "c": g["close"].last(),
            "ok": g["same_front"].all() & g["present"].all(),
        })
        for (root, day), row in part.iterrows():
            key = (root, day)
            rec = acc.get(key)
            if rec is None:
                acc[key] = [int(row.vol), int(row.bmin), float(row.o), int(row.bmax),
                            float(row.c), bool(row.ok)]
                continue
            rec[0] += int(row.vol)
            if int(row.bmin) < rec[1]:
                rec[1], rec[2] = int(row.bmin), float(row.o)
            if int(row.bmax) > rec[3]:
                rec[3], rec[4] = int(row.bmax), float(row.c)
            rec[5] = rec[5] and bool(row.ok)

    by_root: dict[str, list[tuple[float, float, float, str]]] = {}
    for (root, day), rec in acc.items():
        if not rec[5]:
            continue
        if not (math.isfinite(rec[2]) and math.isfinite(rec[4])):
            continue
        by_root.setdefault(root, []).append((day, float(rec[0]), float(rec[2]), float(rec[4])))

    out = {}
    for root in sorted(by_root):
        rows = sorted(by_root[root])
        n = len(rows)
        if n < 100:
            raise ImpactTableError(
                f"[DAY1M] {root}: only {n} clean sessions in {DAY1M_WINDOW[0]}..{DAY1M_WINDOW[1]}; "
                "a sigma on fewer than 100 is not a measurement"
            )
        mult = upp[root]
        adv = math.fsum(r[1] for r in rows) / n
        moves = [(r[3] - r[2]) * mult for r in rows]
        mean_move = math.fsum(moves) / n
        var = math.fsum((m - mean_move) ** 2 for m in moves) / (n - 1)
        sigma_usd = math.sqrt(var)
        mean_notional = (math.fsum(r[3] for r in rows) / n) * mult
        out[root] = {
            "window": list(DAY1M_WINDOW),
            "realised_span": [rows[0][0], rows[-1][0]],
            "adv_contracts": adv,
            "sigma_usd_per_contract": sigma_usd,
            "notional_usd": mean_notional,
            "sigma_fraction": sigma_usd / mean_notional,
            "sessions": n,
            "mean_move_usd": mean_move,
            "usd_per_point": mult,
            "provenance": [
                "scripts/futures_impact_table.py:day1m_line over "
                "data/fixtures/fut_day1m.parquet (columns root, day, bar, open, close, volume, "
                "same_front, present)",
                f"data/fixtures/fut_breadth_hourly.meta.json#specs.{root}.tick_usd_full_contract",
                f"data/fixtures/fut_breadth_hourly.meta.json#specs.{root}.tick_price_units",
            ],
            "notes": "sessions with present AND same_front true on every bar; ADV is the mean of "
                     "the session's summed volume; sigma is the ddof=1 std of (last close - first "
                     "open) x usd_per_point; sigma_fraction divides it by the mean last close's "
                     "notional. IN SAMPLE: ends 2023-12-29, before the 2024-01-01 holdout.",
        }
    return out


# ------------------------------------------------------------------ assemble


def table() -> dict:
    specs = breadth_specs()
    upp, clashes = multipliers(specs)
    lines = {
        "d511": d511_line(specs),
        "breadth_meta": breadth_line(specs),
        DEFAULT_LINE: day1m_line(upp),
    }
    roots: dict[str, dict] = {}
    for root in sorted(specs):
        entry_lines = {name: by_root[root] for name, by_root in lines.items() if root in by_root}
        if not entry_lines:
            raise ImpactTableError(f"[BUILD] {root} has no line at all")
        roots[root] = {"size": size_block(root, specs[root], upp[root]), "lines": entry_lines}

    ratio = {}
    for root, entry in roots.items():
        a = entry["lines"].get("d511", {}).get("adv_contracts")
        b = entry["lines"].get(DEFAULT_LINE, {}).get("adv_contracts")
        if a is not None and b is not None:
            ratio[root] = a / b

    out = {
        "record": "D604",
        "builder": "scripts/futures_impact_table.py",
        "purpose": "parameters for costs/futures_impact.py:FuturesSqrtImpact -- V_d and sigma_d "
                   "of SETTLEMENT_FLOW_LEDGER_PREREG.md 5.3",
        "formula": "I = Y * sigma_d * sqrt(|Q_rem| / V_d) * P * sign(Q_rem)   (price units, 5.3)",
        "coefficient_Y": LEDGER_Y,
        "default_line": DEFAULT_LINE,
        "why_default": "day1m_2016_2023 is the only line measured IN SAMPLE. d511 and "
                       "breadth_meta are measured on 2025-09..2026-09, inside the deposit's "
                       "sealed vault window (2025-03-01..2026-09-18) and after this "
                       "repository's 2024-01-01 holdout; a study reaching for one is making a "
                       "claim this table cannot make for it.",
        "lines": {
            "d511": "ADV in contracts and a session sigma in dollars per FULL contract, 9 roots, "
                    "2025-09-11..2026-09-10, from data/d511_trade_count.json; price level from "
                    "the breadth meta's last bar",
            "breadth_meta": "day-session sigma and notional, 36 roots, from "
                            "data/fixtures/fut_breadth_hourly.meta.json. NO VOLUME: the line "
                            "carries no adv_contracts and cannot build a brick",
            DEFAULT_LINE: "ADV and sigma computed from data/fixtures/fut_day1m.parquet over "
                          "front-contract sessions 2016-01-04..2023-12-29, 36 roots",
        },
        "complete_lines": sorted({name for root in roots for name, ln in roots[root]["lines"].items()
                                  if ln.get("adv_contracts") is not None and ln.get("sigma_fraction") is not None}),
        "multiplier_source": "data/fixtures/fut_breadth_hourly.meta.json: "
                             "tick_usd_full_contract / tick_price_units",
        "multiplier_disagreements": clashes,
        "why_multiplier_disagreements": "EMPTY SINCE D609, AND IT WAS SEVEN ROOTS LONG. "
                                        "instruments/future.py:Future.from_specs fell back to "
                                        "data/fut_specs_from_definition.json's tick_usd, the raw "
                                        "mpi*display_factor*uom_qty with a /100 applied on "
                                        "unit_of_measure == 'USD' alone -- 100x HIGH on ZC, ZS, "
                                        "ZW, ZL, LE, HE and 100x LOW on SR3, every one of them "
                                        "with known_tick_usd: null. D604 recorded the seven here "
                                        "and resolved none; D609 added tick_usd_full_contract to "
                                        "the spec file, decided by the same NOTIONAL test the "
                                        "breadth builder uses, and from_specs reads that. This "
                                        "list being empty is the fix, and the seven corrected "
                                        "usd_per_point values are pinned in "
                                        "tests/unit/test_futures_impact.py so it cannot empty "
                                        "itself by the table losing its roots.",
        "adv_ratio_d511_over_day1m": dict(sorted(ratio.items())),
        "roots": roots,
    }
    out["gates"] = gates(out)
    return out


def gates(t: dict) -> dict:
    roots = t["roots"]
    if len(roots) != 36:
        raise ImpactTableError(f"[T1] {len(roots)} roots, expected the 36 breadth roots")
    n511 = sum(1 for e in roots.values() if "d511" in e["lines"])
    if n511 != 9:
        raise ImpactTableError(f"[T2] the d511 line covers {n511} roots, expected 9")
    for root, entry in roots.items():
        for name, ln in entry["lines"].items():
            if "provenance" not in ln or not ln["provenance"]:
                raise ImpactTableError(f"[T3] {root}/{name} carries no provenance")
            for key in ("sigma_fraction", "notional_usd", "sigma_usd_per_contract"):
                v = ln.get(key)
                if v is None or not math.isfinite(v) or v <= 0:
                    raise ImpactTableError(f"[T4] {root}/{name}.{key} = {v!r}")
            adv = ln.get("adv_contracts")
            if name == "breadth_meta":
                if adv is not None:
                    raise ImpactTableError(f"[T5] breadth_meta carries an ADV for {root}; the "
                                           "source has no volume column at all")
            elif adv is None or not math.isfinite(adv) or adv <= 0:
                raise ImpactTableError(f"[T5] {root}/{name}.adv_contracts = {adv!r}")
            if not (1e-5 < ln["sigma_fraction"] < 0.5):
                raise ImpactTableError(
                    f"[T6] {root}/{name}.sigma_fraction = {ln['sigma_fraction']!r} is outside "
                    "(1e-5, 0.5); a daily return sigma outside that band is a units error"
                )
    if DEFAULT_LINE not in t["complete_lines"]:
        raise ImpactTableError(f"[T7] the default line {DEFAULT_LINE} is not complete")
    return {
        "T1": "all 36 breadth roots present",
        "T2": "the d511 line covers exactly its 9 roots",
        "T3": "every line of every root carries provenance",
        "T4": "sigma_fraction, notional_usd and sigma_usd_per_contract are finite and positive",
        "T5": "adv_contracts present and positive on d511 and day1m, ABSENT on breadth_meta",
        "T6": "every sigma_fraction lies in (1e-5, 0.5)",
        "T7": f"the default line {DEFAULT_LINE} is complete",
        "roots": len(roots),
        "d511_roots": n511,
    }


def serialise(t: dict) -> bytes:
    return (json.dumps(t, indent=1, sort_keys=False) + "\n").encode("utf-8")


# ------------------------------------------------------------------ entry points


def build() -> None:
    t0 = time.time()
    payload = serialise(table())
    OUT.write_bytes(payload)
    print(f"  wrote {OUT.relative_to(REPO)}: {len(payload):,} bytes, "
          f"sha256 {hashlib.sha256(payload).hexdigest()[:16]}... in {time.time() - t0:.0f} s")


def show() -> None:
    t = json.loads(OUT.read_text(encoding="utf-8"))
    print(f"default line: {t['default_line']}   Y = {t['coefficient_Y']}")
    print(f"{'root':5} {'sized':6} {'line':16} {'ADV':>12} {'sigma_usd':>11} {'sigma_frac':>11} "
          f"{'notional':>12}")
    for root, entry in t["roots"].items():
        for name, ln in entry["lines"].items():
            adv = ln.get("adv_contracts")
            print(f"{root:5} {entry['size']['sized_as']:6} {name:16} "
                  f"{('-' if adv is None else f'{adv:,.0f}'):>12} "
                  f"{ln['sigma_usd_per_contract']:>11,.2f} {ln['sigma_fraction']:>11.6f} "
                  f"{ln['notional_usd']:>12,.0f}")
    print("\nADV ratio d511 / day1m_2016_2023 (the vault window over the in-sample one):")
    for root, r in t["adv_ratio_d511_over_day1m"].items():
        print(f"  {root:5} {r:6.2f}")
    clashes = t["multiplier_disagreements"]
    print(f"\nmultiplier disagreements: {len(clashes)}"
          + ("  (D604 recorded seven; D609 corrected the spec file)" if not clashes else ""))
    for c in clashes:
        print(f"  {c['root']:5} breadth {c['breadth_meta_usd_per_point']:>10,.2f}  "
              f"Future.from_specs {c['future_from_specs_usd_per_point']:>12,.2f}  "
              f"ratio {c['ratio']:.0f}x")


def selftest() -> None:
    def expect(fn, what):
        try:
            fn()
        except (ImpactTableError, KeyError, ValueError) as e:
            print(f"    RAISES on {what}: {str(e)[:92]}")
            return
        raise AssertionError(f"no raise on {what}")

    if not OUT.exists():
        raise ImpactTableError(f"{OUT} is not built; run --build first")
    committed = OUT.read_bytes()
    print(f"  committed: {len(committed):,} bytes, sha256 {hashlib.sha256(committed).hexdigest()}")

    if DAY1M.exists():
        t0 = time.time()
        rebuilt = serialise(table())
        if rebuilt != committed:
            for i, (x, y) in enumerate(zip(rebuilt.split(b"\n"), committed.split(b"\n"))):
                if x != y:
                    raise ImpactTableError(f"[SHA] re-derived != committed at line {i + 1}:\n"
                                           f"  rebuilt   {x!r}\n  committed {y!r}")
            raise ImpactTableError(f"[SHA] re-derived {len(rebuilt)} bytes != committed "
                                   f"{len(committed)}")
        print(f"  re-derived from source: {hashlib.sha256(rebuilt).hexdigest()} == committed, "
              f"byte for byte ({time.time() - t0:.0f} s)")
    else:
        print(f"  {DAY1M.name} absent (D536 untracked it) -- the day1m line cannot be re-derived "
              "here; the JSON-sourced lines and every refusal below still run")

    t = json.loads(committed.decode("utf-8"))
    gates(t)
    print(f"  gates pass the committed artefact: {t['gates']['T1']}, {t['gates']['T2']}")

    def broken(mutate):
        import copy
        c = copy.deepcopy(t)
        mutate(c)
        return c

    expect(lambda: gates(broken(lambda c: c["roots"].pop("ES"))), "a missing root (T1)")
    expect(lambda: gates(broken(lambda c: c["roots"]["ES"]["lines"].pop("d511"))),
           "a d511 root dropped (T2)")
    expect(lambda: gates(broken(lambda c: c["roots"]["ES"]["lines"]["d511"].update(provenance=[]))),
           "an empty provenance (T3)")
    expect(lambda: gates(broken(
        lambda c: c["roots"]["ES"]["lines"]["d511"].update(sigma_fraction=0.0))),
        "a zero sigma_fraction (T4)")
    expect(lambda: gates(broken(
        lambda c: c["roots"]["ES"]["lines"]["breadth_meta"].update(adv_contracts=1.0))),
        "an ADV invented for the volume-less line (T5)")
    expect(lambda: gates(broken(
        lambda c: c["roots"]["ES"]["lines"]["d511"].update(sigma_fraction=5.0))),
        "a sigma_fraction of 500% a day (T6)")
    expect(lambda: gates(broken(lambda c: c.update(complete_lines=["d511"]))),
           "a default line that is not complete (T7)")

    specs = breadth_specs()
    expect(lambda: multipliers({"NOSUCH": specs["ES"]}), "a root with no contract specification")
    print("  every gate raises on a break that hits the value it reads")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.build:
        build()
    if args.show:
        show()
    if args.selftest:
        selftest()
    if not (args.build or args.show or args.selftest):
        ap.print_help()


if __name__ == "__main__":
    main()
