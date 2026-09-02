"""D280 part 5 -- how much of the overnight edge is just ex-dividend drops?

    uv run python scripts/d280_dividend_check.py

NOTHING HERE SCORES A CELL. Measurement, same standing as parts 1-4.

THE CONFOUND, and it is the first thing that should have been checked
=====================================================================
Part 4 found the entire edge lives in the overnight gap: cross-sectional IC of
the lagged `hist_L` against `open(t+1)/close(t) - 1` is **-0.01531, t -4.71**
over all names, against +0.00168 for the intraday session.

**`gap` is built from RAW OHLC, and an ex-dividend drop is an overnight drop.**
The fixture's prices are split-adjusted but NOT dividend-adjusted -- `load_ragged`
carries dividends separately, in `total_log_returns`, precisely because the raw
series does not contain them.

**A short OWES the dividend.** So a price gap caused by going ex is not profit;
it is a payment the short leg makes. If `hist_L` tilts at all toward dividend
payers -- and it plausibly does, since dividend payers are mature, larger, and
have different momentum characteristics -- then some of that -0.0153 is an
accounting artefact and not an edge.

THREE MEASUREMENTS, and the second is the one that matters
-----------------------------------------------------------
  RAW        gap = open(t+1)/close(t) - 1                  what part 4 measured
  ADJUSTED   gap = (open(t+1) + div(t+1))/close(t) - 1     the ECONOMIC overnight
                                                           return, which is what
                                                           a short actually pays
  EX-DATES   the raw gap, restricted to bars where t+1 IS an ex-date, and
             separately EXCLUDED -- so the effect is localised rather than
             merely netted away

WHAT WOULD KILL THE OVERNIGHT FINDING, declared before the numbers are read:
if the ADJUSTED gap IC collapses toward zero, part 4's result is a dividend
artefact and D282 should not be run at all. If it survives close to -0.015, the
overnight edge is real and the study is worth its compute.

Reported alongside: the share of bars that are ex-dates, and whether the score
actually tilts toward dividend payers -- because if it does not, the confound
cannot bite regardless of how large individual dividends are.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


B = _load("d256", "run_book_single_names.py")
C = _load("d279", "run_concentrated_short.py")
P1 = _load("d280p1", "d280_forecast_precheck.py")
P3 = _load("d280p3", "d280_score_extrapolation.py")
RP = B.RP

OUT = REPO / "data" / "d280_dividend_check.json"
SPLIT_DATE = P3.SPLIT_DATE
ic_series = P3.ic_series


def ic(score, target, mask):
    ics = ic_series(score, target, mask)
    if ics.size < 30:
        return None
    mu = ics.mean()
    return {"mean_ic": float(mu),
            "t": float(mu / (ics.std(ddof=1) / np.sqrt(ics.size))),
            "bars": int(ics.size)}


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=C.FEE)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    live = panel.live
    g = P1.build_grids(panel, cleaned)
    O, Cl, H, L = g["open"], g["close"], g["high"], g["low"]
    dates = np.array(panel.dates)
    pos_of = {d: i for i, d in enumerate(panel.dates)}
    oos = live & (dates >= SPLIT_DATE)[None, :]
    print(f"loaded {time.time() - t0:.0f}s", flush=True)

    # ---- the dividend grid, parsed exactly as load_ragged parses it ----
    div = np.zeros_like(Cl)
    ev = json.loads(Path(B.EVENTS).read_text(encoding="utf-8"))
    payload = ev.get("dividends", ev) if isinstance(ev, dict) else ev
    idx_of = {s: i for i, s in enumerate(panel.symbols)}
    applied = 0
    for s, items in (payload.items() if isinstance(payload, dict) else []):
        i = idx_of.get(s)
        if i is None:
            continue
        for it in items:
            if isinstance(it, (list, tuple)):
                d, amt = str(it[0])[:10], float(it[1])
            else:
                d = str(it.get("date") or it.get("ex_date") or "")[:10]
                amt = float(it.get("amount", it.get("dividend", 0.0)) or 0.0)
            t = pos_of.get(d)
            if t is None or amt <= 0.0 or not live[i, t]:
                continue
            div[i, t] = amt
            applied += 1
    print(f"  dividends placed on the grid: {applied:,}\n", flush=True)

    def nxt(x):
        out = np.full_like(x, np.nan)
        ok = live[:, 1:] & live[:, :-1]
        out[:, :-1] = np.where(ok, x[:, 1:], np.nan)
        return out

    gap_raw = nxt(O) / Cl - 1.0
    gap_adj = (nxt(O) + nxt(div)) / Cl - 1.0      # the short's ECONOMIC overnight
    is_ex = nxt(div) > 0.0

    m = oos & np.isfinite(gap_raw)
    ex_share = float((is_ex & m).sum() / m.sum())
    print(f"  bars whose NEXT session is an ex-date: {ex_share:.3%}")
    if (is_ex & m).sum():
        dy = (nxt(div) / Cl)[is_ex & m]
        print(f"  median dividend yield on those bars: {np.median(dy):.4%}")
        print(f"  median |raw gap| overall            : "
              f"{np.median(np.abs(gap_raw[m])):.4%}\n", flush=True)

    h = C.lag1(hs)
    rng_l = C.lag1((H - L) / Cl)
    safe = np.where(np.isfinite(rng_l) & (rng_l > 0), rng_l, np.nan)

    okm = ~(np.isnan(md) | np.isnan(hs)) & warm
    qual = oos & (-B.hold_book((hs < 0) & (md >= 0) & okm, warm) != 0.0)

    rows = {"ex_date_share": ex_share, "dividends_applied": applied}
    print("  THE COMPARISON. Negative IC = tradeable for a short.\n")
    print(f"  {'universe':>9s} {'score':>20s} {'target':>26s} {'mean IC':>9s} {'t':>7s}")
    for uname, mask in (("ALL", oos), ("QUAL", qual)):
        for sname, s in (("h", h), ("h / lagged range", h / safe)):
            for tname, tgt, sub in (
                    ("gap RAW (part 4)", gap_raw, None),
                    ("gap DIVIDEND-ADJUSTED", gap_adj, None),
                    ("gap RAW, ex-dates EXCLUDED", gap_raw, ~is_ex),
                    ("gap RAW, ex-dates ONLY", gap_raw, is_ex)):
                mm = mask if sub is None else (mask & sub)
                r = ic(s, tgt, mm)
                if r is None:
                    print(f"  {uname:>9s} {sname:>20s} {tname:>26s}   too few bars")
                    continue
                rows[f"{uname}|{sname}|{tname}"] = r
                print(f"  {uname:>9s} {sname:>20s} {tname:>26s} "
                      f"{r['mean_ic']:+9.5f} {r['t']:+7.2f}", flush=True)
        print()

    # ---- does the score tilt toward dividend payers at all? ----
    pays = (div > 0).sum(axis=1) > 0
    mm = oos & np.isfinite(h)
    tilt = []
    for t in range(h.shape[1]):
        col = mm[:, t]
        if col.sum() < P3.MIN_NAMES or pays[col].sum() < 5 or (~pays[col]).sum() < 5:
            continue
        v = h[col, t]
        sd = v.std()
        if sd > 0:
            z = (v - v.mean()) / sd
            tilt.append(float(z[pays[col]].mean() - z[~pays[col]].mean()))
    if tilt:
        tl = np.array(tilt)
        tt = tl.mean() / (tl.std(ddof=1) / np.sqrt(tl.size))
        rows["score_tilt_toward_payers_z"] = {"mean": float(tl.mean()),
                                              "t": float(tt), "bars": int(tl.size)}
        print(f"  SCORE TILT. Mean z of `hist_L` for dividend payers minus "
              f"non-payers:\n     {tl.mean():+.4f} (t {tt:+.2f}, {tl.size:,} bars). "
              f"Positive = payers score HIGHER,\n     so the short ranking ASCENDING "
              f"under-selects them and the confound cannot bite hard.\n")

    json.dump({"purpose": ("measures how much of D280 part 4's overnight gap IC "
                           "is an ex-dividend artefact; scores no cell"),
               "split_date": SPLIT_DATE, "results": rows,
               "elapsed_s": round(time.time() - t0, 1)}, open(OUT, "w"), indent=1)
    print(f"wrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
