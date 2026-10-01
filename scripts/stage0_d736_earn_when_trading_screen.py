"""D736 Stage 0: a screen of the ES/NQ index-futures constructions already scored, under the principal's standard that a
strategy must earn when it trades (docs/decisions/D736-STAGE-0-PRE-REG-which-es-nq-constructions-earn-when-they-trade.md).

    uv run python scripts/stage0_d736_earn_when_trading_screen.py --selftest
    uv run python scripts/stage0_d736_earn_when_trading_screen.py --run        # once; writes the result JSON

It reads ONLY committed result JSONs (yearly net dollars at one micro, years <= 2023). It opens no fixture, no data
file and no vault output. Nothing here admits anything (D736 s.0).

Per block (D736 s.2): ex-2 = the net without the two best calendar years; G1 ex-2 > 0; G2 positive in at least
ceil(2/3 n_years) years; G3 ex-2 per year >= $209 (hurdle P's P4 account cost, data/prop_venues.json). Before any
gate: every year <= 2023 (a later year raises), the yearly nets reproduce the record's own total (else UNREADABLE),
and D732's F and C and D735's YM k1.0 reproduce their known answers (s.3).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Callable, Iterator

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
OUT = DATA / "stage0_d736_earn_when_trading_screen.json"
SPEC = "docs/decisions/D736-STAGE-0-PRE-REG-which-es-nq-constructions-earn-when-they-trade.md"
LAST_YEAR = 2023
G3_FLOOR = 209.0  # data/prop_venues.json mffu_rapid_50k fee; checked at run time
TOL_PER_YEAR = 0.01

KNOWN = {  # D736 s.3
    "D732/F": {"by_year": {"2018": -13, "2019": -29, "2020": 1220, "2021": 509, "2022": 3772, "2023": 169}, "ex2": 636.0},
    "D732/C": {"by_year": {"2018": 251, "2019": 152, "2020": 385, "2021": 1537, "2022": 1930, "2023": 700}, "ex2": 1488.2,
               "years_positive": 6},
    "D735/YM_k1.0_1s": {"trades": 1699, "ex2": 6933.0},
}

# status in each construction's own record (the inventory of 2026-10-01, re-read from the records cited there)
STATUS_D732 = {"A": "RETIRED (MACD arm, BOOK_PROP 2026-10-01)", "F": "QUEUED slot 7 (D716)", "C": "QUEUED slot 9 (D680)",
               "E": "PARKED, withdrawn from the vault (D716)", "T1": "DECLINED by the principal (D727 follow)",
               "T1.5": "DECLINED by the principal (D727 follow)"}
NAME_D732 = {"A": "MACD day-session arm", "F": "NQ F2 book B", "C": "NQ compression C1", "E": "ES F2",
             "T1": "NQ follow k1.0 (D727)", "T1.5": "NQ follow k1.5 (D727)"}


class ScreenError(RuntimeError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise ScreenError(msg)


def load(name: str) -> dict[str, Any]:
    return json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------------------------------------ the statistics
def ex2(by: dict[str, float]) -> tuple[float, list[str]]:
    """Net without the two best calendar years (ties: the earlier year counts as better, so the pick is deterministic)."""
    order = sorted(by, key=lambda y: (-by[y], y))
    best = order[:2]
    return float(sum(v for y, v in by.items() if y not in best)), sorted(best)


def stats(by: dict[str, float]) -> dict[str, Any]:
    n = len(by)
    need(n >= 3, "fewer than three years: ex-2 per year is undefined")
    tot = float(sum(by.values()))
    e2, best = ex2(by)
    pos = sum(1 for v in by.values() if v > 0)
    need_pos = math.ceil(2 * n / 3)
    g1, g2, g3 = e2 > 0, pos >= need_pos, e2 / (n - 2) >= G3_FLOOR
    label = ("EARNS" if g1 and g2 and g3 else "RESTS ON ITS BEST YEARS" if not g1 else "INTERMITTENT" if not g2
             else "BREAK-EVEN")
    return {"n_years": n, "years": [min(by), max(by)], "total_net": tot, "best_two": best, "ex2": e2,
            "ex2_per_year": e2 / (n - 2), "years_positive": pos, "years_needed": need_pos,
            "worst_year": min(by, key=lambda y: by[y]), "worst_net": min(by.values()),
            "best_two_share": (sum(by[y] for y in best) / tot) if tot else None,
            "G1": g1, "G2": g2, "G3": g3, "label": label}


def check_years(key: str, by: dict[str, float]) -> None:
    late = [y for y in by if int(y) > LAST_YEAR]
    need(not late, f"[SEAL] {key} holds a year after {LAST_YEAR}: {late}")


def check_sum(by: dict[str, float], total: float | None) -> bool | None:
    if total is None:
        return None
    return abs(sum(by.values()) - total) <= TOL_PER_YEAR * len(by)


# ------------------------------------------------------------------------------------------------ the universe (D736 s.1)
Row = dict[str, Any]


def _row(key: str, family: str, name: str, by: dict[str, float], total: float | None, trades: int | None,
         share: float | None, share_approx: bool, status: str, primary: bool, **rec: Any) -> Row:
    return {"key": key, "family": family, "name": name, "by_year": {y: float(v) for y, v in by.items()},
            "total_recorded": total, "trades": trades, "market_share": share, "share_approx": share_approx,
            "status": status, "primary": primary, "recorded": rec}


def _approx_share(trades: int, n_years: int) -> float:
    return trades / (252 * n_years)


def src_d732() -> Iterator[Row]:
    d = load("stage0_d732_year_robust_book")
    ses = d["calendar"]["sessions"]
    for s in ("A", "F", "C", "E", "T1", "T1.5"):
        x = d["series"][s]
        yield _row(f"D732/{s}", f"D732-{s}", NAME_D732[s], x["by_year"], x["total_net"], x["trade_days"],
                   x["trade_days"] / ses, False, STATUS_D732[s], s in ("A", "F", "C", "E"),
                   sharpe=x["net_sharpe"], sortino=x["net_sortino"], max_dd=x["max_dd"])


def src_d735() -> Iterator[Row]:
    d = load("stage0_d735_nq_breaks_from_the_market")
    for c, x in d["cells"].items():
        b = x["book"]
        leg = x["leg"]
        st = "QUEUED slot 1 (D737)" if c == "YM_k1.0_1s" else "DRIFT ONLY (D735)"
        yield _row(f"D735/{c}", f"D735-{leg}", f"NQ breaks from the market, leg {leg} k{x['k']} stop {x['stop']}",
                   b["net_by_year"], b["trades"] * b["mean_net_per_mnq"], b["trades"], b["trades"] / d["leg_days"][leg],
                   False, st, c == d["primary"], sharpe=b["net_sharpe"], sortino=b["net_sortino"], max_dd=b["max_dd"],
                   mean_net=b["mean_net_per_mnq"], rho_nq_f2=x.get("rho_nq_f2"))


def src_d727() -> Iterator[Row]:
    d = load("stage0_d727_trend_curve")
    for r, R in d["roots"].items():
        for kind in ("per_clock", "first_crossing"):
            for c, b in R["books"][kind].items():
                st = "DECLINED by the principal (D731 s.3.4)" if r == "NQ" else "NOT SUPPORTED (D727)"
                yield _row(f"D727/{r}/{kind}/{c}", f"D727-{r}", f"{r} trend follow, {kind} {c}", b["net_by_year"],
                           b["trades"] * b["mean_net"], b["trades"], b["trades"] / R["days"], False, st, False,
                           sharpe=b["net_sharpe"], sortino=b["net_sortino"], max_dd=b["max_dd"], mean_net=b["mean_net"])


def src_d728() -> Iterator[Row]:
    d = load("stage0_d728_cross_asset")
    for g, G in d["groups"].items():
        for k, B in G["S2_book"].items():
            b = B["full_book"]
            yield _row(f"D728/{g}/{k}", f"D728-{g}", f"NQ follow when {g} agrees, k{k}", b["net_by_year"],
                       b["trades"] * b["mean_net"], b["trades"], b["trades"] / d["nq_days"], False, "NOTHING (D728)",
                       False, sharpe=b["net_sharpe"], sortino=b["net_sortino"], max_dd=b["max_dd"], mean_net=b["mean_net"])


def src_d731() -> Iterator[Row]:
    d = load("stage0_d731_flat_u")
    for k, K in d["roots"]["NQ"]["S2"].items():
        if not (isinstance(K, dict) and "a_all" in K):  # S2 also holds rotation and rho summaries beside the k books
            continue
        b = K["a_all"]
        n = len(b["net_by_year"])
        yield _row(f"D731/NQ/{k}", "D731-NQ", f"NQ 13:30 entry, k{k}, every entry", b["net_by_year"],
                   b["trades"] * b["mean_net_per_mnq"], b["trades"], _approx_share(b["trades"], n), True,
                   "CLOSED (D731)", False, sharpe=b["net_sharpe"], sortino=b["net_sortino"], max_dd=b["max_dd"],
                   mean_net=b["mean_net_per_mnq"])


def src_d733() -> Iterator[Row]:
    d = load("stage0_d733_pullback_entry")
    for c, x in d["cells"].items():
        b = x["book"]
        yield _row(f"D733/{c}", "D733-NQ", f"NQ pullback entry {c}", b["net_by_year"],
                   b["trades"] * b["mean_net_per_mnq"], b["trades"], b["trades"] / d["days"], False, "CLOSED (D733)",
                   False, sharpe=b["net_sharpe"], sortino=b["net_sortino"], max_dd=b["max_dd"],
                   mean_net=b["mean_net_per_mnq"])


def src_d721() -> Iterator[Row]:
    d = load("diag_d721_quiet_day_f2")
    for r, R in d["roots"].items():
        for m in ("M0", "M1_reported"):
            if m not in R:
                continue
            b = R[m]["books"]["F2"]
            ses = R[m].get("sessions") or R["M0"].get("sessions")
            yield _row(f"D721/{r}/{m}", f"D721-{r}", f"{r} F2 on forecast-quiet days ({m})", b["net_by_year"], None,
                       b["trades"], b["trades"] / ses if ses else None, False, "CLOSED by the principal (D721)", False,
                       sharpe=b["net_sharpe"], sortino=b["net_sortino"], max_dd=b["max_dd"])


def src_d711() -> Iterator[Row]:
    """Its yearly block stores n and the MEAN net per trade; the yearly sum is n x mean, checked against the total."""
    d = load("stage1_d711_f2_mechanism")
    items = [(f"A1/{t}", "D711-ES", f"ES F2 at the {t} clock", b["book"]) for t, b in d["A1"]["clocks"].items()]
    items += [(f"A2/{r}", f"D711-{r}", f"{r} F2 (15:30)", R["line"]["book"]) for r, R in d["A2"]["roots"].items()]
    for k, fam, name, b in items:
        by = {y: v["n"] * v["net"] for y, v in b["by_year"].items()}
        yield _row(f"D711/{k}", fam, name, by, b["trades"] * b["mean_net"], b["trades"], b["trades_per_year"] / 252, True,
                   "SCORED, NOT ENTERED (D711)" if not k.endswith("15:30") else "= ES F2, PARKED (D716)", False,
                   sharpe=b.get("sharpe_daily"), sortino=b.get("sortino_daily"), max_dd=b.get("max_drawdown_usd"),
                   mean_net=b["mean_net"])


def src_d699() -> Iterator[Row]:
    d = load("d699_gamma_macd_long")
    for v, V in d["variants"].items():
        b = V["2_book"]
        yield _row(f"D699/{v}", "D699-ES", f"ES gamma-gated MACD long {v}", {y: x["net"] for y, x in b["by_year"].items()},
                   b["total_net"], b["trades"], b["trades_per_year"] / 252, True, "CLOSED by the principal (D699)",
                   v == "V1_HIST", sharpe=b["net_sharpe"], sortino=b["net_sortino"], max_dd=b["max_dd"],
                   mean_net=b["mean_net"])


def src_d689() -> Iterator[Row]:
    d = load("d689_short_gamma_continuation")
    for c, C in d["cells"].items():
        b = C["books"]["unfiltered_mes"]
        n = len(b["by_year_net_usd"])
        yield _row(f"D689/{c}", "D689-ES", f"ES short-gamma continuation {c} (1 MES)", b["by_year_net_usd"],
                   b["net"]["total_usd"], b["trades"], b["days_traded"] / (252 * n), True,
                   "IN-SAMPLE ONLY; D712 withdrawn", False, sharpe=b["net"]["sharpe_daily"],
                   sortino=b["net"]["sortino_daily"], max_dd=b["net"]["max_dd_usd"],
                   mean_net=b["net"]["mean_per_trade_usd"])


SOURCES: list[Callable[[], Iterator[Row]]] = [src_d732, src_d735, src_d727, src_d728, src_d731, src_d733, src_d721,
                                               src_d711, src_d699, src_d689]


# ------------------------------------------------------------------------------------------------ the screen
def known_answers(rows: dict[str, Row], ex2_fn: Callable[[dict[str, float]], tuple[float, list[str]]] = ex2) -> None:
    for k, ka in KNOWN.items():
        r = rows[k]
        if "by_year" in ka:
            need(all(abs(r["by_year"][y] - v) < 0.5 + 1e-9 for y, v in ka["by_year"].items()),
                 f"[KNOWN] {k} yearly nets differ from D736 s.3")
        e2 = ex2_fn(r["by_year"])[0]
        need(abs(e2 - ka["ex2"]) < 1.0, f"[KNOWN] {k} ex-2 {e2:.1f} != {ka['ex2']}")
        if "trades" in ka:
            need(r["trades"] == ka["trades"], f"[KNOWN] {k} trades {r['trades']} != {ka['trades']}")
        if "years_positive" in ka:
            need(stats(r["by_year"])["years_positive"] == ka["years_positive"], f"[KNOWN] {k} years positive")


def screen() -> dict[str, Any]:
    fee = json.loads((DATA / "prop_venues.json").read_text(encoding="utf-8"))
    need(G3_FLOOR in _numbers(fee), "[G3] $209 is not in data/prop_venues.json (the floor's anchor moved)")
    rows: dict[str, Row] = {}
    for src in SOURCES:
        for r in src():
            need(r["key"] not in rows, f"duplicate key {r['key']}")
            check_years(r["key"], r["by_year"])
            r["sum_check"] = check_sum(r["by_year"], r["total_recorded"])
            rows[r["key"]] = r
    known_answers(rows)
    for r in rows.values():
        if r["sum_check"] is False:
            r["label"] = "UNREADABLE"
            continue
        r.update(stats(r["by_year"]))
        sh = r["market_share"]
        r["ex2_per_market_session"] = r["ex2_per_year"] / (252 * sh) if sh else None
    earns = sorted((r for r in rows.values() if r.get("label") == "EARNS"),
                   key=lambda r: -(r["ex2_per_market_session"] or 0))
    fams: dict[str, list[str]] = {}
    for r in earns:
        fams.setdefault(r["family"], []).append(r["key"])
    labels: dict[str, int] = {}
    for r in rows.values():
        labels[r["label"]] = labels.get(r["label"], 0) + 1
    return {"spec": SPEC, "reads": "committed result JSONs only; years <= 2023", "g3_floor": G3_FLOOR,
            "n_blocks": len(rows), "labels": labels, "earns_families": fams, "n_earns_families": len(fams),
            "shortlist": [r["key"] for r in earns], "rows": rows}


def _numbers(o: Any) -> set[float]:
    if isinstance(o, dict):
        return set().union(*(_numbers(v) for v in o.values())) if o else set()
    if isinstance(o, list):
        return set().union(*(_numbers(v) for v in o)) if o else set()
    return {float(o)} if isinstance(o, (int, float)) and not isinstance(o, bool) else set()


# ------------------------------------------------------------------------------------------------ selftest
def selftest() -> int:
    fired = []

    def fires(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except ScreenError:
            fired.append(name)
            print(f"  fires: {name}")
            return
        raise SystemExit(f"SELFTEST FAILED: {name} did not raise")

    fires("a 2024 key", lambda: check_years("x", {"2022": 1.0, "2024": 2.0}))
    need(check_sum({"2020": 1.0, "2021": 2.0}, 3.0) is True, "the sum check fails a match")
    fires("a yearly sum that disagrees with its total",
          lambda: need(check_sum({"2020": 1.0, "2021": 2.0}, 3.5) is not False, "[SUM] yearly nets do not add up"))

    def worst_two(by: dict[str, float]) -> tuple[float, list[str]]:
        order = sorted(by, key=lambda y: by[y])[:2]
        return float(sum(v for y, v in by.items() if y not in order)), order

    rows = {r["key"]: r for s in SOURCES for r in s() if r["key"] in KNOWN}
    known_answers(rows)
    print("  known answers hold on the real ex-2")
    fires("ex-2 dropping the two WORST years", lambda: known_answers(rows, worst_two))
    s = stats({"2016": 100.0, "2017": -10.0, "2018": 500.0, "2019": 300.0, "2020": 50.0, "2021": 40.0})
    need(s["ex2"] == 180.0 and s["years_positive"] == 5 and s["years_needed"] == 4 and s["label"] == "BREAK-EVEN",
         f"synthetic stats wrong: {s}")
    s2 = stats({"2016": 1000.0, "2017": -10.0, "2018": 500.0, "2019": 300.0, "2020": 600.0, "2021": 400.0})
    need(s2["label"] == "EARNS" and s2["best_two"] == ["2016", "2020"], f"synthetic EARNS wrong: {s2}")
    s3 = stats({"2016": 1000.0, "2017": -10.0, "2018": -50.0, "2019": 300.0, "2020": 600.0, "2021": -40.0})
    need(s3["label"] == "INTERMITTENT", f"synthetic INTERMITTENT wrong: {s3}")
    print("  synthetic labels: BREAK-EVEN, EARNS, INTERMITTENT as constructed")
    print(f"SELFTEST PASS: {len(fired)} canaries raised")
    return 0


def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists; the screen is run once")
    res = screen()
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else run() if a.run else ap.print_help() or 2)
