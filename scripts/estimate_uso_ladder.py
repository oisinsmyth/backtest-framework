"""USO's daily futures weights by contract month, 2017-05-22 → 2023-12-29, from its documented allocations (AITODO 1e).

SPEC -- written 2026-09-24, the principal's instruction ("Yes go for that in 1e"), before any
predicted weight was compared with a held one; frozen from then on.

THE DOCUMENTED HISTORY is `data/fund_facts/uso_allocation_notices.csv`, from USO's 8-Ks on its
library page. The daily weights follow it period by period. A weight is the share of USO's
FUTURES book, not of AUM; f_fut (`data/ledger_fut_share_daily.csv.gz`) scales it.
  1. `benchmark` (up to 2020-04-16): the pre-2020 rule. The near month, rolled into the next month
     over four trade closes starting at D0 = the near month's last trading day - 14 calendar
     days, 25% at each. The official USCF calendar matches this every month from 2020.
     Implemented as `check_uscf_months_and_rolls.roll_calendar`.
  2. `documented_apr2020` (2020-04-17 → 2020-04-29), each day's end-of-day holding as announced:
       04-17 → 04-20: 80% June, 20% July. The May contract was within two weeks of its expiry,
                      so per the 04-16 8-K "the second month contract and third month contract".
       04-21: 40% June, 55% July, 5% August.
       04-22 → 04-23: 20% June, 50% July, 20% August, 10% September.
       04-24: 20% June, 40% July, 20% August, 20% September.
       04-27, 04-28, 04-29: one third of the way per day from the 04-24 mix to the target 30% July,
                      15% August, 15% September, 15% October, 15% December, 10% June 2021.
  3. `transition_2020` (2020-04-30 → 2020-09-30): linear in trading days, contract by contract,
     between three anchors: the 04-29 target, the 2020-06-30 holdings and the 2020-09-30 holdings
     (D620 month weights). Flagged. The quarter-ends are inputs here, not tests.
  4. `ladder` (2020-10-01 → 2023-08-31): the stable ladder.
       * At a month-end m it holds contracts m+2 … m+7 with weights w_2 … w_7, plus one "annual"
         contract with weight w_A. The annual contract is the earliest June or December contract
         at least 8 months after m.
       * The weights are the mean of the quarter-end weights by offset over 2020-09-30 → 2023-06-30
         (twelve quarter-ends), renormalised to 1.
       * During month m+1's roll (Business Days 1-10, the official calendar), the book moves from
         the month-m ladder to the month-(m+1) ladder, 10% at each close: h = (1-φ) old + φ new,
         with φ = BD/10.
  5. `transition_2023` (2023-09-01 → 2023-12-29): the 2023-08-29 8-K says the book moves back to the
     benchmark over the rolls from September 2023 to January 2024, but not at what pace. Two
     scenarios are written, and the ledger reads both:
       weight     = the 2023-09-30 holdings (D620), shifted one month at each later roll;
       weight_alt = the benchmark rule (100% front / next), the end state.
     September's own roll goes from the August ladder to the 2023-09-30 holdings over BD1-10.
     2023-12-31 was filed in 2024 and is not read.

VALIDATION (the ladder, period 4). Each of the twelve quarter-ends is predicted from weights
averaged over the OTHER eleven (leave-one-out). The error is |predicted - held| per contract.
Reported: mean, p90 and max, and the band half-width h_w = p90, used as each ladder weight's
band. Also reported: whether each held quarter-end's contract SET equals the predicted set
(offsets 2-7 plus the annual contract).

WHAT THIS DOES NOT TOUCH: it reads the D620 holdings (cut on filed_date < 2024-01-01) and the CL
business-day calendar before 2024. It computes no return. It writes
`data/ledger_uso_weights_daily.csv.gz` (gitignored by suffix) and
`data/ledger_uso_weights_summary.json`.

    uv run python scripts/estimate_uso_ladder.py            # write both
    uv run python scripts/estimate_uso_ladder.py --check    # rebuild, compare byte for byte
"""
from __future__ import annotations

import argparse
import bisect
import gzip
import importlib.util
import io
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT_ROWS = REPO / "data" / "ledger_uso_weights_daily.csv.gz"
OUT_SUM = REPO / "data" / "ledger_uso_weights_summary.json"
FIRST, LAST = "2017-05-22", "2023-12-29"
Key = tuple[int, int]


class LadderError(RuntimeError):
    pass


def _load(name: str, rel: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


U = _load("check_uscf_months_and_rolls", "scripts/check_uscf_months_and_rolls.py")
G = U.G


def add(y: int, m: int) -> Key:
    return (y + (m - 1) // 12, (m - 1) % 12 + 1)


def ym(s: str) -> Key:
    return (int(s[:4]), int(s[5:7]))


def off(c: Key, m: Key) -> int:
    return (c[0] * 12 + c[1]) - (m[0] * 12 + m[1])


def annual_for(m: Key) -> Key:
    """The earliest June or December contract at least 8 months after month m."""
    c = add(m[0], m[1] + 8)
    while c[1] not in (6, 12):
        c = add(c[0], c[1] + 1)
    return c


def quarter_end_holdings() -> dict[str, dict[Key, float]]:
    h = G.load_panel("fund_holdings_quarterly", reserved_from=G.RESERVED_FROM).frame
    g = h[(h["fund"] == "USO") & (h["kind"] == "futures") & (h["period_end"].astype(str) >= "2020-03-31")]
    g = g.sort_values(["period_end", "filed_date"])
    out: dict[str, dict[Key, float]] = {}
    for pe, x in g.groupby("period_end"):
        x = x[x["source_accession"] == x["source_accession"].iloc[0]]
        w: dict[Key, float] = {}
        for cm, mw in zip(x["contract_month"].astype(str), x["month_weight"].astype(float)):
            w[ym(cm)] = w.get(ym(cm), 0.0) + mw
        tot = sum(w.values())
        out[str(pe)] = {k: v / tot for k, v in w.items()}
    return out


def ladder_weights(qe: dict[str, dict[Key, float]], use: list[str]) -> dict[str, float]:
    """Mean weight by offset ('2'..'7', 'A') over the quarter-ends in `use`, renormalised."""
    acc: dict[str, list[float]] = {}
    for pe in use:
        m = ym(pe)
        A = annual_for(m)
        row = {str(k): qe[pe].get(add(m[0], m[1] + k), 0.0) for k in range(2, 8)}
        row["A"] = qe[pe].get(A, 0.0)
        for k, v in row.items():
            acc.setdefault(k, []).append(v)
    mean = {k: float(np.mean(v)) for k, v in acc.items()}
    tot = sum(mean.values())
    return {k: v / tot for k, v in mean.items()}


def ladder_at(m: Key, w: dict[str, float]) -> dict[Key, float]:
    out = {add(m[0], m[1] + k): w[str(k)] for k in range(2, 8)}
    A = annual_for(m)
    out[A] = out.get(A, 0.0) + w["A"]
    return out


def mix(a: dict[Key, float], b: dict[Key, float], phi: float) -> dict[Key, float]:
    keys = set(a) | set(b)
    return {k: (1 - phi) * a.get(k, 0.0) + phi * b.get(k, 0.0) for k in keys if (1 - phi) * a.get(k, 0.0) + phi * b.get(k, 0.0) > 1e-12}


def shift(h: dict[Key, float], months: int) -> dict[Key, float]:
    return {add(c[0], c[1] + months): v for c, v in h.items()}


def build() -> tuple[str, dict[str, Any]]:
    _nav, st, _r = U.GCL.load()
    copies = set(G.copy_days(st))
    bdays = sorted(d for d in st if d not in copies)
    rolls = U.roll_calendar("CL", bdays)
    qe = quarter_end_holdings()
    stable_q = [pe for pe in sorted(qe) if "2020-09-30" <= pe <= "2023-06-30"]
    if len(stable_q) != 12:
        raise LadderError(f"expected 12 stable quarter-ends, found {len(stable_q)}: {stable_q}")

    # ---- validation: leave-one-out
    errs, set_match, loo = [], 0, []
    for pe in stable_q:
        w = ladder_weights(qe, [q for q in stable_q if q != pe])
        pred = ladder_at(ym(pe), w)
        held = qe[pe]
        e = [abs(pred.get(k, 0.0) - held.get(k, 0.0)) for k in set(pred) | set(held)]
        errs += e
        same = set(pred) == set(held)
        set_match += same
        loo.append({"quarter_end": pe, "max_abs_err": round(max(e), 4), "same_contract_set": same})
    hw = float(np.quantile(errs, 0.9))
    W = ladder_weights(qe, stable_q)

    # ---- the documented April 2020 days
    J, JL, AU, SE, OC, DE, J21 = (2020, 6), (2020, 7), (2020, 8), (2020, 9), (2020, 10), (2020, 12), (2021, 6)
    m0424 = {J: 0.2, JL: 0.4, AU: 0.2, SE: 0.2}
    target = {JL: 0.30, AU: 0.15, SE: 0.15, OC: 0.15, DE: 0.15, J21: 0.10}
    april = {"2020-04-17": {J: 0.8, JL: 0.2}, "2020-04-20": {J: 0.8, JL: 0.2}, "2020-04-21": {J: 0.40, JL: 0.55, AU: 0.05},
             "2020-04-22": {J: 0.2, JL: 0.5, AU: 0.2, SE: 0.1}, "2020-04-23": {J: 0.2, JL: 0.5, AU: 0.2, SE: 0.1},
             "2020-04-24": m0424, "2020-04-27": mix(m0424, target, 1 / 3), "2020-04-28": mix(m0424, target, 2 / 3),
             "2020-04-29": target}

    lines = ["date,contract_month,weight,weight_alt,band_lo,band_hi,method"]

    def emit(d: str, h: dict[Key, float], method: str, alt: dict[Key, float] | None = None, band: float = 0.0) -> None:
        tot = sum(h.values())
        if abs(tot - 1.0) > 1e-9:
            raise LadderError(f"{d}: weights sum to {tot}")
        keys = sorted(set(h) | set(alt or {}))
        for k in keys:
            v = h.get(k, 0.0)
            a = (alt or h).get(k, 0.0)
            lines.append(f"{d},{k[0]:04d}-{k[1]:02d},{v!r},{a!r},{max(0.0, v - band)!r},{min(1.0, v + band)!r},{method}")

    def bench(d: str) -> dict[Key, float]:
        i = bdays.index(d)
        for r in rolls:
            if d <= r["E"]:
                phi = min(max((i - r["i0"] + 1) / 4.0, 0.0), 1.0)
                return mix({r["near"]: 1.0}, {r["next"]: 1.0}, phi)
        # past the last computable expiry (the calendar ends at the cut): the benchmark is the next
        # contract, whose own roll cannot begin before the month before its delivery month
        nxt = rolls[-1]["next"]
        before = add(nxt[0], nxt[1] - 1)
        if d >= f"{before[0]:04d}-{before[1]:02d}-01":
            raise LadderError(f"no roll entry for {d}")
        return {nxt: 1.0}

    def bd_of(d: str) -> int:
        month = [x for x in bdays if x[:7] == d[:7]]
        return month.index(d) + 1

    anchors = [("2020-04-29", target), ("2020-06-30", qe["2020-06-30"]), ("2020-09-30", qe["2020-09-30"])]
    a_days = [a for a, _ in anchors]
    counts: dict[str, int] = {}
    for d in bdays:
        if not (FIRST <= d <= LAST):
            continue
        if d <= "2020-04-16":
            method, h, alt, band = "benchmark", bench(d), None, 0.0
        elif d in april:
            method, h, alt, band = "documented_apr2020", april[d], None, 0.0
        elif d <= "2020-09-30":
            j = bisect.bisect_left(a_days, d)
            (da, ha), (db, hb) = anchors[j - 1], anchors[j]
            ia, ib, idd = bdays.index(da), bdays.index(db), bdays.index(d)
            method, h, alt, band = "transition_2020", mix(ha, hb, (idd - ia) / (ib - ia)), None, hw
        elif d <= "2023-08-31":
            m = ym(d)
            prev = add(m[0], m[1] - 1)
            phi = min(bd_of(d) / 10.0, 1.0)
            method, h, alt, band = "ladder", mix(ladder_at(prev, W), ladder_at(m, W), phi), None, hw
        else:
            m = ym(d)
            b = bench(d)
            if d[:7] == "2023-09":
                phi = min(bd_of(d) / 10.0, 1.0)
                h = mix(ladder_at((2023, 8), W), qe["2023-09-30"], phi)
            else:
                months_after = off(m, (2023, 9))
                h = mix(shift(qe["2023-09-30"], months_after - 1), shift(qe["2023-09-30"], months_after), min(bd_of(d) / 10.0, 1.0))
            method, alt, band = "transition_2023", b, 1.0
        emit(d, h, method, alt, band)
        counts[method] = counts.get(method, 0) + 1
    summary = {
        "ladder_weights_by_offset": {k: round(v, 6) for k, v in W.items()},
        "loo_validation": {"quarter_ends": len(stable_q), "same_contract_set": set_match,
                           "mean_abs_err": round(float(np.mean(errs)), 5), "p90_abs_err": round(hw, 5),
                           "max_abs_err": round(float(np.max(errs)), 5), "per_quarter": loo},
        "band_half_width": round(hw, 5), "days_by_method": counts,
    }
    return "\n".join(lines) + "\n", summary


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    text, summary = build()
    stext = json.dumps(summary, indent=1, sort_keys=True) + "\n"
    if a.check:
        with gzip.open(OUT_ROWS, "rt", encoding="utf-8", newline="") as fh:
            if fh.read() != text:
                raise LadderError(f"{OUT_ROWS.name} does not reproduce")
        if OUT_SUM.read_text(encoding="utf-8") != stext:
            raise LadderError(f"{OUT_SUM.name} does not reproduce")
        print("[check] both outputs reproduce byte for byte")
        return 0
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        gz.write(text.encode("utf-8"))
    OUT_ROWS.write_bytes(buf.getvalue())
    OUT_SUM.write_text(stext, encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "loo_validation"}, indent=1))
    v = summary["loo_validation"]
    print(f"LOO: same contract set {v['same_contract_set']}/{v['quarter_ends']}; |err| mean {v['mean_abs_err']}, "
          f"p90 {v['p90_abs_err']}, max {v['max_abs_err']}")
    for q in v["per_quarter"]:
        print("  ", q)
    return 0


if __name__ == "__main__":
    sys.exit(main())
