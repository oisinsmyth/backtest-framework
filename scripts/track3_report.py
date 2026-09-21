"""D605 TRACK 3 REPORT -- the shortfall table, the latency check, the 50-trade cost review and
the trial counter, read off a per-trade fill log.

    uv run python scripts/track3_report.py --selftest
    uv run python scripts/track3_report.py --log data/track3/<model>_trades.csv --root MNQ \
        --size micro --line d508_exec [--bar-seconds 60]

NOTHING HERE TRADES. No broker adapter, no scheduler, no order is sent, and **no real fill
exists yet**: `data/track3/` holds `SCHEMA.md` and no trade file, so the live path of this
script has never been run on a real log. `--selftest` writes a synthetic log to a temporary
directory, proves every guard in `validation/track3.py` RAISES on a real break, and deletes
it. Every number it prints is hand-typed.

The spec is `docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md` §13A.5, quoted
verbatim in `src/backtest_framework/validation/track3.py`'s docstring. This file is its
command line and holds no rule of its own.

DECLARED OUTPUTS. `REQUIRED_SECTIONS` names the four blocks a report must contain and the
report RAISES if one is missing -- a section promised in a docstring and skipped in code is
the failure `CLAUDE.md` calls "declared outputs need a guard, not prose".
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

# The library's docstrings quote the deposit VERBATIM, so they carry the section sign, the
# true minus and the ellipsis. A Windows console defaults to cp1252 and a print of any of
# them dies with UnicodeEncodeError -- which would turn a failing guard into a failing
# encoder and hide which one fired. Pinned here, at the one place this package prints.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="backslashreplace")  # type: ignore[union-attr]

from backtest_framework.costs.futures_bricks import FuturesRoundTrip  # noqa: E402
from backtest_framework.instruments.future import Future  # noqa: E402
from backtest_framework.validation.track3 import (  # noqa: E402
    FIELDS,
    COST_REVIEW_N,
    Track3Error,
    Track3LogError,
    TradeLog,
    TradeRow,
    TrialCounter,
    cost_assumption_ticks,
    cost_review,
    exit_shortfall_ticks,
    latency_report,
    shortfall_ticks,
    shortfall_usd,
)

REQUIRED_SECTIONS = ("SHORTFALL", "LATENCY", "COST REVIEW", "TRIAL COUNTER")
DEFAULT_BAR_SECONDS = 60.0
FIELD_QTY = FIELDS.index("qty")
"""Index of `qty` in the schema, used only to mangle one cell in the selftest."""


# --------------------------------------------------------------------------- the report


def report(
    log_path: Path,
    root: str,
    size: str | None,
    line: str | None,
    bar_seconds: float,
    counter: TrialCounter | None = None,
    log: Any = print,
) -> dict[str, Any]:
    """Print the four blocks and return them. Raises if a declared section is missing."""
    rows = TradeLog(log_path).read()
    if not rows:
        raise Track3Error(
            f"{log_path} has a header and no trades. Track 3 has recorded nothing; there is "
            "no shortfall, no latency distribution and no review to print."
        )
    trip = FuturesRoundTrip.from_table(root, size, line)
    fut = trip.instrument
    if fut is None:  # pragma: no cover - from_table always carries one
        raise Track3Error(f"the cost table gave no instrument for {root!r}")
    assumption = cost_assumption_ticks(root, size, line)

    emitted: list[str] = []
    out: dict[str, Any] = {}

    log(f"  SHORTFALL -- {len(rows)} trades on {fut.root} (tick {fut.tick_points}, "
        f"${fut.tick_usd}/tick)")
    emitted.append("SHORTFALL")
    log("    id            side   qty  model_fill      fill    ticks       usd  sim")
    table = []
    for r in rows:
        ticks = shortfall_ticks(r, fut)
        usd = shortfall_usd(r, fut)
        table.append({"trade_id": r.trade_id, "ticks": ticks, "usd": usd})
        log(f"    {r.trade_id:<12} {r.side:<6}{r.qty:>4}  {r.model_fill_px:>10}"
            f"{r.fill_px:>10}  {ticks:>7.4g}  {usd:>8.4g}  {'Y' if r.simulated else 'n'}")
    mean_ticks = sum(x["ticks"] for x in table) / len(table)
    total_usd = sum(x["usd"] for x in table)
    log(f"    mean {mean_ticks:.6g} ticks/fill; total {total_usd:.6g} usd. "
        "POSITIVE = the fill was worse for the strategy (d364's convention).")
    out["shortfall"] = {"rows": table, "mean_ticks": mean_ticks, "total_usd": total_usd}

    lat = latency_report(rows, bar_seconds)
    log(f"\n  LATENCY -- signal to fill, in bars of {bar_seconds:g} s")
    emitted.append("LATENCY")
    log(f"    min {lat['min']:.6g}  p50 {lat['p50']:.6g}  p95 {lat['p95']:.6g}  "
        f"max {lat['max']:.6g}   (nearest-rank quantiles)")
    log(f"    beyond t0+{lat['assumed_max']:g}: {lat['n_beyond']} of {lat['n']} = "
        f"{lat['share_beyond_t0_plus_5']:.6g}   (§13A.5's reported share)")
    out["latency"] = lat

    rev = cost_review(rows, fut, assumption)
    log(f"\n  COST REVIEW -- after {COST_REVIEW_N} trades (§13A.5)")
    emitted.append("COST REVIEW")
    log(f"    assumption {assumption:.10g} ticks/fill = crossing/2 + 1 adverse tick "
        f"({trip.line} line, {trip.size} size)")
    if rev.sufficient:
        log(f"    mean {rev.mean_shortfall_ticks:.10g}  ratio {rev.ratio:.10g}  "
            f"exceeds_by_50pct {rev.exceeds_by_50pct}")
    log(f"    action: {rev.action}")
    out["cost_review"] = rev.to_dict()

    log("\n  TRIAL COUNTER -- §13A.4")
    emitted.append("TRIAL COUNTER")
    if counter is None:
        log("    no counter supplied: the log carries fills, not net returns per trade. "
            "§13A.4's N is a count of SCORED trades and this script will not invent one.")
        out["counter"] = None
    else:
        state = counter.to_dict()
        log(f"    N {state['n']} / {state['target']}  looks {state['looks']}  "
            f"mean {state['mean']}  t {state['t']}")
        log(f"    futility {state['futility']}   efficacy {state['efficacy']}   "
            f"counts_as_efficacy {state['counts_as_efficacy']}")
        out["counter"] = state

    missing = [s for s in REQUIRED_SECTIONS if s not in emitted]
    if missing:
        raise Track3Error(f"the report declared {REQUIRED_SECTIONS} and did not emit {missing}")
    return out


# --------------------------------------------------------------------------- the selftest


def _expect_raise(fn: Any, exc: type[BaseException], what: str, log: Any = print) -> None:
    """A clean case is not a gate. Every guard below must also RAISE on a real break."""
    try:
        fn()
    except exc as e:
        log(f"    RAISES on {what}: {type(e).__name__}: {str(e)[:76]}")
        return
    raise AssertionError(f"guard did not raise on {what}")


MES = Future(root="MES", tick_points=0.25, usd_per_point=5.0, tick_usd=1.25)
D = dt.datetime(2026, 10, 1)


def _row(trade_id: str, side: str, qty: int, sig: int, sent: int, fill: int,
         model_px: float, fill_px: float, simulated: bool = False, **kw: Any) -> TradeRow:
    return TradeRow(
        trade_id=trade_id, model="selftest", stage="A", frozen_sha256="0" * 64,
        root="MES", size_label="micro", side=side, qty=qty,  # type: ignore[arg-type]
        signal_ts=D + dt.timedelta(seconds=sig),
        model_fill_px=model_px,
        order_sent_ts=D + dt.timedelta(seconds=sent),
        fill_ts=D + dt.timedelta(seconds=fill),
        fill_px=fill_px, simulated=simulated, venue="SYNTHETIC", **kw,
    )


def selftest(log: Any = print) -> int:
    """The good case first, then every raise. Returns 0, or raises."""
    log("  [1] the good case -- a synthetic six-trade log, written and read back")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "selftest_trades.csv"
        tl = TradeLog(path)
        long_hit = _row("S1", "long", 1, 0, 10, 60, 5000.00, 5000.50)
        short_hit = _row("S2", "short", 1, 120, 130, 180, 5020.00, 5019.50)
        tl.append(long_hit)
        tl.append(short_hit)
        tl.append(_row("S3", "long", 2, 300, 310, 660, 4990.00, 4989.75, simulated=True,
                       exit_signal_ts=D + dt.timedelta(seconds=900),
                       exit_fill_ts=D + dt.timedelta(seconds=960),
                       exit_fill_px=4995.00))
        back = tl.read()
        assert len(back) == 3, back
        assert back[0] == long_hit and back[1] == short_hit, "round trip changed a row"
        log(f"    wrote and read back {len(back)} rows; the round trip is exact")

        log("  [2] ledger 35 -- the sign, in money, on BOTH sides")
        lt = shortfall_ticks(long_hit, MES)
        st = shortfall_ticks(short_hit, MES)
        assert lt == 2.0, lt
        assert st == 2.0, st
        assert shortfall_usd(long_hit, MES) == 2.5, shortfall_usd(long_hit, MES)
        good = _row("S4", "long", 1, 0, 1, 2, 5000.00, 4999.75)
        assert shortfall_ticks(good, MES) == -1.0, "a favourable fill must be NEGATIVE"
        log("    long +2 above model = +2 ticks; short +2 below model = +2 ticks; "
            "a favourable long fill = -1")

        log("  [3] the exit sign inverts")
        closed = back[2]
        assert exit_shortfall_ticks(closed, MES, 4995.25) == 1.0
        assert exit_shortfall_ticks(closed, MES, 4994.75) == -1.0
        log("    a long selling a tick below the model exit = +1 (worse); above = -1")

        log("  [4] every guard raises")
        _expect_raise(lambda: tl.append(long_hit), Track3Error, "a duplicate trade_id", log)
        _expect_raise(
            lambda: tl.append(_row("S9", "long", 1, 100, 50, 200, 5000.0, 5000.0)),
            Track3Error, "order_sent_ts before signal_ts", log)
        _expect_raise(
            lambda: tl.append(_row("S9", "long", 1, 0, 100, 50, 5000.0, 5000.0)),
            Track3Error, "fill_ts before order_sent_ts", log)
        _expect_raise(lambda: _row("S9", "sell", 1, 0, 1, 2, 5000.0, 5000.0),
                      Track3Error, "a side that is not long or short", log)
        _expect_raise(lambda: _row("S9", "long", 0, 0, 1, 2, 5000.0, 5000.0),
                      Track3Error, "qty = 0", log)
        _expect_raise(lambda: _row("S9", "long", 1, 0, 1, 2, 5000.0, float("nan")),
                      Track3Error, "a non-finite fill price", log)
        _expect_raise(
            lambda: _row("S9", "long", 1, 0, 1, 2, 5000.0, 5000.0,
                         exit_fill_ts=D + dt.timedelta(seconds=99)),
            Track3Error, "a half-recorded exit", log)
        _expect_raise(
            lambda: _row("S9", "long", 1, 0, 1, 2, 5000.0, 5000.0,
                         exit_signal_ts=dt.datetime(2026, 10, 1, 1, tzinfo=dt.UTC),
                         exit_fill_ts=dt.datetime(2026, 10, 1, 2, tzinfo=dt.UTC),
                         exit_fill_px=5000.0),
            Track3Error, "aware and naive timestamps in one row", log)
        _expect_raise(lambda: exit_shortfall_ticks(long_hit, MES, 5000.0),
                      Track3Error, "the exit shortfall of an OPEN trade", log)
        _expect_raise(lambda: shortfall_ticks(long_hit, Future("ES", 0.25, 50.0, 12.5)),
                      Track3Error, "a Future whose root is not the row's", log)
        _expect_raise(lambda: latency_report([], 60.0),
                      Track3Error, "the latency distribution of an EMPTY log", log)
        _expect_raise(lambda: latency_report(back, 0.0),
                      Track3Error, "bar_seconds = 0", log)
        _expect_raise(lambda: cost_review(back, MES, 0.0),
                      Track3Error, "a zero cost assumption", log)
        _expect_raise(lambda: TradeLog(Path(tmp) / "absent.csv").read(),
                      Track3LogError, "a log that does not exist", log)

        bad = Path(tmp) / "bad.csv"
        bad.write_text("trade_id,nope\n", encoding="utf-8", newline="\n")
        _expect_raise(lambda: TradeLog(bad).read(), Track3LogError, "a wrong header", log)
        rowsrc = path.read_text(encoding="utf-8").splitlines()
        mangled = Path(tmp) / "mangled.csv"
        broken = rowsrc[1].split(",")
        broken[FIELD_QTY] = "two"
        mangled.write_text(
            "\n".join([rowsrc[0], ",".join(broken)]) + "\n", encoding="utf-8", newline="\n")
        _expect_raise(lambda: TradeLog(mangled).read(), Track3LogError,
                      "qty that is not a whole number (names the line and field)", log)

        log("  [5] the cost review never returns a verdict on too few trades")
        thin = cost_review(back, MES, 2.0, n=COST_REVIEW_N)
        assert thin.sufficient is False and thin.mean_shortfall_ticks is None
        assert thin.exceeds_by_50pct is None, thin
        log(f"    {thin.action}")
        full = cost_review(back, MES, 0.5, n=3)
        assert full.sufficient is True and full.exceeds_by_50pct is True
        log(f"    at n=3 and a 0.5-tick assumption: ratio {full.ratio:.6g}, exceeds True")

    log("  [6] the trial counter -- ledger 36 and the efficacy decision")
    c = TrialCounter("selftest", target=300, looks=(100, 200), counts_as_efficacy=True)
    _expect_raise(lambda: c.mean, Track3Error, "the mean of no trades", log)
    c.add(-6.3125)
    _expect_raise(lambda: c.t, Track3Error, "t at N = 1", log)
    c.extend([-0.0625] * 98)
    m99, t99 = c.mean, c.t
    assert c.n == 99 and m99 < 0 and t99 < -1
    assert c.futility() is False, "99 is not a look"
    c.add(-0.0625)
    assert c.n == 100 and c.mean == -0.125 and c.t == -2.0, (c.mean, c.t)
    assert c.futility() is True
    log(f"    N=99 mean {m99:.6g} t {t99:.6g} -> False (not a look); "
        f"N=100 mean {c.mean} t {c.t} -> True")
    flat = TrialCounter("flat")
    flat.extend([0.5] * 100)
    _expect_raise(lambda: flat.t, Track3Error, "t on a constant series (sd = 0)", log)
    _expect_raise(lambda: TrialCounter("x", counts_as_efficacy=False),
                  Track3Error, "counts_as_efficacy=False with no reason", log)
    _expect_raise(lambda: TrialCounter("x", target=300, looks=(100, 300)),
                  Track3Error, "a futility look at the target", log)
    _expect_raise(lambda: TrialCounter("x").check_frozen({}, []),
                  Track3Error, "check_frozen with no frozen_path", log)
    log("  [7] §13A.7(4) route, delegated to validation/power.track3_route")
    assert c.route(0.15).route == "efficacy_n300"
    assert c.route(0.08).route == "combined_evidence"
    log("    0.15 sigma -> efficacy_n300; 0.08 sigma -> combined_evidence")
    log("  OK -- every guard fired on its break. No order was sent and no real fill exists.")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--log", type=Path, help="the per-trade fill log")
    p.add_argument("--root", help="contract root or traded symbol, e.g. MNQ")
    p.add_argument("--size", default=None, help="micro | full (default: the entry's min size)")
    p.add_argument("--line", default=None, help="crossing line, e.g. d508_exec")
    p.add_argument("--bar-seconds", type=float, default=DEFAULT_BAR_SECONDS)
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.log is None or a.root is None:
        p.error("--log and --root are required unless --selftest is given")
    report(a.log, a.root, a.size, a.line, a.bar_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
