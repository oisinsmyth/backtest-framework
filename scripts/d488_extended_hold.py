"""D488 -- does the MACD edge keep growing with the holding period, and does it cross its cost?

    uv run python scripts/d488_extended_hold.py --self-test
    uv run python scripts/d488_extended_hold.py --run [--json]

Pre-registered in
`docs/decisions/D488-PRE-REG-does-the-MACD-edge-keep-growing-with-the-holding.md`,
committed before this file existed.

**THE SIGNAL CODE IS IMPORTED FROM D484, NOT REIMPLEMENTED.** `impulse_macd`, `macd_hist`,
`ema`, `smma`, `zlema`, `sma`, `edge_sigma`, `rotate` and `series_for` all come from
`d488`'s predecessor so the parameters and smoothers cannot drift between the two records --
which is the whole basis for calling this an extension of D484 rather than a new study.

TWO CONSTRAINTS FROM THE PRE-REG, ENFORCED IN CODE
--------------------------------------------------
* **P2**: a hold must be flat by 4pm ET, so the last usable exit is segment index 21 (h15).
  The maximum within-session hold is therefore 22 hours.
* **THE PRINCIPAL'S CLOSURE**: the index overnight leg at micro cost is closed for the prop
  book, any gate, window or size. So on ES/NQ/YM **every hold must lie wholly inside the day
  session** -- entry at or after h09 (index 15) and exit by index 21. Non-index roots are
  unaffected and run to H=22.

WHY A LONGER HOLD IS FAVOURED TWICE OVER, one of which needs no new edge
------------------------------------------------------------------------
Cost is FIXED per round trip while sigma grows as sqrt(H), so

    gross/cost  ~  edge_sigma(H) * sqrt(H)

rises as sqrt(H) **even if edge_sigma is completely flat**. D484 measured it rising. S2 below
measures which of the two is happening: a flat edge gives a growth exponent of 0.5.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from d484_offdiagonal_and_macd import (  # noqa: E402
    CROSS_TICKS, COMMISSION_RT, IN_SAMPLE, MICRO_OF, SEGMENTS, SPECS,
    edge_sigma, impulse_macd, macd_hist, rotate, series_for,
)

FIX = REPO / "data" / "fixtures" / "fut_sessions_hourly.csv.gz"
META = REPO / "data" / "fixtures" / "fut_sessions_hourly.meta.json"
OUT = REPO / "data" / "d488_extended_hold.json"

INDEX_ROOTS = ("ES", "NQ", "YM")                       # §2: day session only
NONINDEX_ROOTS = ("ZN", "ZB", "GC", "CL", "6E")        # §2: run to H=22
ROOTS = INDEX_ROOTS + NONINDEX_ROOTS
H_NONINDEX = (5, 8, 11, 16, 22)                        # §2
H_INDEX = (5, 7)                                       # §2
LAST_EXIT_IDX = 21                                     # §2: h15 ends 4pm ET (P2)
DAY_START_IDX = 15                                     # §2: h09
N_DRAWS = 2000                                         # §4
FLAT_EXPONENT = 0.5                                    # §5: what a flat edge_sigma gives
SEED = 488


class GateError(AssertionError):
    """A validation gate refused the input."""


def P(*a, **k):
    print(*a, **k, flush=True)


def eligible_entries(root: str, H: int, n_seg: int) -> np.ndarray:
    """Which segment indices may OPEN a hold of H hours, per §2.

    Non-index: exit index <= LAST_EXIT_IDX (P2's flatten cap).
    Index:     additionally entry >= DAY_START_IDX, so the hold never spans the overnight
               and stays outside the principal's closure.
    """
    lo = DAY_START_IDX if root in INDEX_ROOTS else 0
    hi = LAST_EXIT_IDX - H + 1          # entry a, exit a+H-1 <= LAST_EXIT_IDX
    if hi < lo:
        return np.array([], dtype=np.int64)
    return np.arange(lo, hi + 1, dtype=np.int64)


def growth_exponent(hs: np.ndarray, edges: np.ndarray) -> float:
    """§3 S2: slope of log(edge_sigma * sqrt(H)) on log(H).

    A FLAT edge_sigma gives exactly 0.5, because sqrt(H) alone contributes that. Above 0.5
    means the edge per sigma is itself rising with the hold.
    """
    ok = np.isfinite(edges) & (edges > 0) & (hs > 0)
    if ok.sum() < 3:
        return float("nan")
    y = np.log(edges[ok] * np.sqrt(hs[ok]))
    x = np.log(hs[ok].astype(float))
    return float(np.polyfit(x, y, 1)[0])


def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:66} {detail}")
        if not cond:
            fails.append(label)

    # --- THE GROWTH EXPONENT, which is the hypothesis. Its calibration must be exact.
    hs = np.array([5, 8, 11, 16, 22])
    chk("a FLAT edge_sigma gives an exponent of exactly 0.5",
        abs(growth_exponent(hs, np.full(5, 0.02)) - 0.5) < 1e-9,
        f"{growth_exponent(hs, np.full(5, 0.02)):.6f}")
    # an edge_sigma itself growing as H^0.25 must give 0.75
    chk("edge_sigma ~ H^0.25 gives an exponent of 0.75",
        abs(growth_exponent(hs, 0.02 * hs ** 0.25) - 0.75) < 1e-9,
        f"{growth_exponent(hs, 0.02*hs**0.25):.6f}")
    # a DECAYING edge_sigma must pull it BELOW 0.5 -- the W-b direction
    chk("a decaying edge_sigma pulls the exponent BELOW 0.5",
        growth_exponent(hs, 0.02 * hs ** -0.25) < 0.5,
        f"{growth_exponent(hs, 0.02*hs**-0.25):.4f}")
    chk("and edge_sigma ~ 1/sqrt(H) gives exactly 0.0 -- gross/cost then FLAT in H",
        abs(growth_exponent(hs, 0.02 * hs ** -0.5)) < 1e-9,
        f"{growth_exponent(hs, 0.02*hs**-0.5):.6f}")
    chk("too few points returns NaN rather than a number",
        bool(np.isnan(growth_exponent(np.array([5, 8]), np.array([.02, .02])))))

    # --- §2 eligibility: P2's cap and the closure, both enforced, both proven to bind
    for H in H_NONINDEX:
        e = eligible_entries("GC", H, len(SEGMENTS))
        chk(f"non-index H={H}: exits all land by index {LAST_EXIT_IDX}",
            len(e) > 0 and int(e.max() + H - 1) == LAST_EXIT_IDX,
            f"{len(e)} entries, last exit {int(e.max()+H-1)}")
    chk("non-index H=22 admits exactly ONE entry, at the 18:00 open",
        list(eligible_entries("GC", 22, 23)) == [0])
    for H in H_INDEX:
        e = eligible_entries("ES", H, len(SEGMENTS))
        chk(f"INDEX H={H}: every entry is in the day session (>= {DAY_START_IDX})",
            len(e) > 0 and int(e.min()) >= DAY_START_IDX,
            f"entries {int(e.min())}..{int(e.max())}, exits to {int(e.max()+H-1)}")
    chk("THE CLOSURE BINDS: an index root gets NO entry at a 22-hour hold",
        len(eligible_entries("ES", 22, 23)) == 0,
        "an ES 22h hold would span the overnight and is closed")
    chk("and the closure is what excludes it, not P2 -- a NON-index root does get one",
        len(eligible_entries("GC", 22, 23)) == 1)
    chk("index entries never start before h09, so no hold spans the overnight",
        all(int(eligible_entries(r, H, 23).min()) >= DAY_START_IDX
            for r in INDEX_ROOTS for H in H_INDEX))

    # --- the imported signal code must be the SAME code D484 ran
    rg = np.random.default_rng(2)
    walk = np.cumsum(rg.standard_normal(3000)) * 0.001 + np.log(100.0)
    h_, l_ = walk + 0.001, walk - 0.001
    hist, md = impulse_macd(h_, l_, walk)
    chk("imported impulse_macd returns a finite histogram and a zero state",
        bool(np.isfinite(hist[-1])) and bool((md[np.isfinite(md)] == 0).any()))
    chk("imported macd_hist is finite", bool(np.isfinite(macd_hist(walk)[-1])))
    s = np.sign(rg.standard_normal(20_000))
    f = rg.standard_normal(20_000)
    # THIS CHECK WAS A TAUTOLOGY on the first pass -- it ended in `or True` and could not
    # fail. Scale-freedom means the SAME signal and returns scaled by any constant give the
    # SAME number, which is a real comparison.
    chk("imported edge_sigma is scale-free (x1000 the returns, same answer)",
        abs(edge_sigma(s, f * 1000.0) - edge_sigma(s, f)) < 1e-9,
        f"{edge_sigma(s, f*1000.0):+.6f} vs {edge_sigma(s, f):+.6f}")
    chk("and it is NOT invariant to scaling only the numerator -- so the test has teeth",
        abs(edge_sigma(s * 2.0, f) - edge_sigma(s, f)) > 1e-6,
        "doubling the signal doubles the edge")
    # MEASURE THE INCREMENT, not the level. This draw carries a -0.015 spurious baseline
    # (~2 SE at n=20,000), so an absolute test reads 0.025 for a planted 0.04 and looks
    # broken when it is not. The increment isolates the planted effect from the draw.
    base = edge_sigma(s, f)
    chk("imported edge_sigma recovers a planted 0.04 edge (as an INCREMENT)",
        abs((edge_sigma(s, f + 0.04 * s) - base) - 0.04) < 0.004,
        f"{edge_sigma(s, f + 0.04*s) - base:+.5f} over a {base:+.5f} baseline")
    chk("imported rotate preserves the multiset",
        bool(np.array_equal(np.sort(rotate(f, 137)), np.sort(f))))

    # --- cost arithmetic: gross/cost grows as sqrt(H) at a FLAT edge, which is the premise
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    cost_mnq = COMMISSION_RT / spec["MNQ"]["tick_usd"] + CROSS_TICKS
    r5 = 0.55                                    # D484's measured NQ ratio at H=5
    chk("a flat edge takes NQ's 0.55 at H=5 to ~0.65 at H=7, not to 1.0",
        abs(r5 * np.sqrt(7 / 5) - 0.651) < 0.01,
        f"{r5*np.sqrt(7/5):.3f} -- W-c's arithmetic")
    chk("and reaching 1.0 on a flat edge would need H ~ 16.5 hours (CLOSED for index)",
        abs(5 * (1 / r5) ** 2 - 16.5) < 0.3, f"{5*(1/r5)**2:.1f} hours")
    chk("MNQ cost is still 7.009 ticks", abs(cost_mnq - 7.009) < 1e-3)

    if fails:
        P(f"\n  SELF-TEST FAILED: {fails}")
        return 1
    P("\n  SELF-TEST PASSED.")
    return 0


def do_run(as_json: bool) -> int:
    import pandas as pd

    meta = json.loads(META.read_text(encoding="utf-8"))
    spec = json.loads(SPECS.read_text(encoding="utf-8"))
    for root in ROOTS:
        g = meta["gates"].get(root)
        if g is None:
            raise GateError(f"[FIXTURE] no gate block for {root}")
        bad = [k for k, v in g.items() if isinstance(v, dict) and v.get("passes") is False]
        if bad:
            raise GateError(f"[FIXTURE] {root} fails gates {bad}")
    P("  RTY excluded (fails G2). Index roots confined to the DAY SESSION by the "
      "principal's closure.\n")

    d_all = pd.read_csv(FIX)
    nseg = len(SEGMENTS)
    rows, series = [], {}
    for root in ROOTS:
        s = series_for(root, d_all, meta)
        series[root] = s
        lo_, lc = s["log_open"], s["log_close"]
        lh, ll = s["log_high"], s["log_low"]
        n = len(lc)
        seg_idx = np.arange(n) % nseg                      # position within the session
        sig = {"B1": np.where(impulse_macd(lh, ll, lc)[1] == 0.0, 0.0,
                              np.sign(impulse_macd(lh, ll, lc)[0])),
               "B2": np.sign(macd_hist(lc))}
        Hs = H_INDEX if root in INDEX_ROOTS else H_NONINDEX
        for H in Hs:
            elig = set(eligible_entries(root, H, nseg).tolist())
            if not elig:
                continue
            # entry at the OPEN of t+1, exit at the CLOSE of t+H
            fwd = np.full(n, np.nan)
            j = np.arange(n)
            ok = (j + H) < n
            fwd[ok] = lc[j[ok] + H] - lo_[j[ok] + 1]
            # the ENTRY bar is t+1, so its segment index decides eligibility
            ent_seg = (seg_idx + 1) % nseg
            same_session = (j + H) // nseg == (j + 1) // nseg     # no session crossing
            mask = (s["pure"] & np.isin(ent_seg, list(elig)) & same_session)
            sig_ticks = float(np.nanstd(fwd[mask], ddof=1)) if mask.sum() > 10 else np.nan
            for fam in ("B1", "B2"):
                sg = np.where(mask, sig[fam], np.nan)
                e = edge_sigma(sg, fwd)
                nn = int((np.isfinite(sg) & np.isfinite(fwd) & (sg != 0)).sum())
                rows.append({"root": root, "family": fam, "H": H, "n": nn,
                             "edge_sigma": e, "sigma_log": sig_ticks,
                             "index_root": root in INDEX_ROOTS,
                             "entries_per_session": len(elig)})
        P(f"  {root:4} {s['n_sessions']:>5} sessions · {len(lc):>7,} bars · "
          f"H {list(Hs)} · entries/session "
          f"{[len(eligible_entries(root,H,nseg)) for H in Hs]}")

    # ALL holds in the header, not just the non-index ones -- the first version used
    # H_NONINDEX as the columns, so the index roots' H=7 cells existed in the data and
    # were invisible in the table.
    ALL_H = sorted(set(H_NONINDEX) | set(H_INDEX))
    P(f"\n  S1 -- the scale-free edge, by root and hold:")
    P(f"  {'root':>5}{'fam':>4}" + "".join(f"{f'H={h}':>10}" for h in ALL_H))
    for root in ROOTS:
        for fam in ("B1", "B2"):
            cells = {r["H"]: r for r in rows if r["root"] == root and r["family"] == fam}
            line = "".join(
                (f"{cells[h]['edge_sigma']:>+10.5f}" if h in cells else f"{'--':>10}")
                for h in ALL_H)
            P(f"  {root:>5}{fam:>4}{line}")

    # ---- S2: the growth exponent
    P(f"\n  S2 -- growth exponent of gross/cost in H "
      f"(flat edge = {FLAT_EXPONENT}; above means the edge per sigma is rising):")
    expo = {}
    for fam in ("B1", "B2"):
        per_root = {}
        for root in ROOTS:
            cells = sorted((r for r in rows if r["root"] == root and r["family"] == fam),
                           key=lambda z: z["H"])
            hs = np.array([c["H"] for c in cells], dtype=float)
            es = np.array([c["edge_sigma"] for c in cells], dtype=float)
            per_root[root] = growth_exponent(hs, es)
        pooled = float(np.nanmean([v for v in per_root.values() if np.isfinite(v)]))
        expo[fam] = {"per_root": per_root, "pooled": pooled}
        P(f"    {fam}: pooled {pooled:+.3f}  " +
          "  ".join(f"{r} {per_root[r]:+.2f}" for r in ROOTS
                    if np.isfinite(per_root[r])))

    # ---- §4 nulls, on the pooled exponent and on the longest-H edge
    rg = np.random.default_rng(SEED)
    P(f"\n  R1 rotation null, {N_DRAWS:,} draws ...")
    null_expo = {f: np.empty(N_DRAWS) for f in ("B1", "B2")}
    null_long = {f: np.empty(N_DRAWS) for f in ("B1", "B2")}
    cache = {}
    for root in ROOTS:
        s = series[root]
        lo_, lc = s["log_open"], s["log_close"]
        lh, ll = s["log_high"], s["log_low"]
        n = len(lc)
        seg_idx = np.arange(n) % nseg
        md = impulse_macd(lh, ll, lc)[1]
        sig = {"B1": np.where(md == 0.0, 0.0, np.sign(impulse_macd(lh, ll, lc)[0])),
               "B2": np.sign(macd_hist(lc))}
        Hs = H_INDEX if root in INDEX_ROOTS else H_NONINDEX
        fw, mk = {}, {}
        for H in Hs:
            elig = set(eligible_entries(root, H, nseg).tolist())
            fwd = np.full(n, np.nan)
            j = np.arange(n)
            ok = (j + H) < n
            fwd[ok] = lc[j[ok] + H] - lo_[j[ok] + 1]
            ent_seg = (seg_idx + 1) % nseg
            same = (j + H) // nseg == (j + 1) // nseg
            fw[H] = fwd
            mk[H] = s["pure"] & np.isin(ent_seg, list(elig)) & same
        cache[root] = (sig, fw, mk, Hs, n)

    for i in range(N_DRAWS):
        for fam in ("B1", "B2"):
            ex, lg = [], []
            for root in ROOTS:
                sig, fw, mk, Hs, n = cache[root]
                k = int(rg.integers(100, n - 100))
                rot = rotate(sig[fam], k)
                es, hs = [], []
                for H in Hs:
                    es.append(edge_sigma(np.where(mk[H], rot, np.nan), fw[H]))
                    hs.append(H)
                ex.append(growth_exponent(np.array(hs, float), np.array(es, float)))
                lg.append(es[-1])
            null_expo[fam][i] = float(np.nanmean(ex))
            null_long[fam][i] = float(np.nanmean(lg))

    def band(x):
        p50, p95 = float(np.quantile(x, .50)), float(np.quantile(x, .95))
        boot = np.array([np.quantile(rg.choice(x, len(x), replace=True), .95)
                         for _ in range(400)])
        return {"p50": p50, "p95": p95, "se_of_p95": float(boot.std(ddof=1))}

    P(f"\n  === VERDICTS ===")
    verdicts, nulls_out = {}, {}
    for fam in ("B1", "B2"):
        be, bl = band(null_expo[fam]), band(null_long[fam])
        obs_e = expo[fam]["pooled"]
        obs_l = float(np.nanmean([r["edge_sigma"] for r in rows
                                  if r["family"] == fam
                                  and r["H"] == max(H_NONINDEX if not r["index_root"]
                                                    else H_INDEX)]))
        # S2'S NULL IS UNDEFINED, AND THAT IS A FLAW IN THE PRE-REGISTERED STATISTIC, not
        # a coding slip. §3 defined S2 as the slope of log(edge_sigma * sqrt(H)) on log H.
        # Under a null centred on zero the edge goes NEGATIVE about half the time, and the
        # log of a negative number does not exist -- so growth_exponent returns NaN on most
        # null draws and the family mean is NaN. The statistic cannot be tested against its
        # own null. It is reported DESCRIPTIVELY and its bar is recorded as unmet-because-
        # ill-posed, never as passed. A slope of edge_sigma on log H (no log of the edge)
        # would be testable and needs its own pre-registration.
        s2_testable = bool(np.isfinite(be["p95"]) and np.isfinite(be["se_of_p95"]))
        me = ((obs_e - be["p95"]) / be["se_of_p95"]) if s2_testable else float("nan")
        ml = (obs_l - bl["p95"]) / bl["se_of_p95"]
        grows = bool(s2_testable and obs_e > FLAT_EXPONENT and me > 2)
        survives = bool(ml > 2)
        P(f"\n  {fam}:")
        if s2_testable:
            P(f"    S2 exponent {obs_e:+.3f}  vs flat {FLAT_EXPONENT}  and R1 p95 "
              f"{be['p95']:+.3f} (SE {be['se_of_p95']:.3f}) -> {me:+.1f} SE")
        else:
            P(f"    S2 exponent {obs_e:+.3f}  vs flat {FLAT_EXPONENT}  --  **R1 NULL IS "
              f"UNDEFINED**: log(edge) does not exist where a null edge is negative, so "
              f"the pre-registered statistic cannot be tested. DESCRIPTIVE ONLY.")
        P(f"    longest-H edge {obs_l:+.5f}  vs R1 p95 {bl['p95']:+.5f} "
          f"(SE {bl['se_of_p95']:.5f}) -> {ml:+.1f} SE")
        P(f"    **EDGE GROWS: {'YES' if grows else 'no'} · "
          f"EDGE SURVIVES: {'YES' if survives else 'no'}**")
        verdicts[fam] = {"edge_grows": grows, "edge_survives": survives,
                         "exponent": obs_e, "exponent_margin_se": me,
                         "S2_null_testable": s2_testable,
                         "S2_note": ("R1 null undefined: the pre-registered statistic takes "
                                     "log(edge_sigma), which does not exist where a null "
                                     "edge is negative. Descriptive only; the bar is "
                                     "unmet-because-ill-posed, never passed."),
                         "longest_edge": obs_l, "longest_margin_se": ml}
        nulls_out[fam] = {"R1_exponent": be, "R1_longest_edge": bl}

    # ---- S3: tradeability, ONLY where a verified micro spec exists (§3)
    P(f"\n  S3 -- tradeability. AVAILABLE ONLY for roots with a committed micro spec:")
    trade, blocked = [], []
    for root in ROOTS:
        micro = MICRO_OF.get(root)
        if micro is None or micro not in spec or root not in spec:
            blocked.append(root)
            continue
        cost = COMMISSION_RT / spec[micro]["tick_usd"] + CROSS_TICKS
        tickp = spec[root]["tick_points"]
        lvl = float(np.nanmedian(np.exp(series[root]["log_close"])))
        for r in [r for r in rows if r["root"] == root]:
            if not np.isfinite(r["sigma_log"]):
                continue
            sig_tk = r["sigma_log"] * lvl / tickp
            gross = r["edge_sigma"] * sig_tk
            trade.append({**{k: r[k] for k in ("root", "family", "H", "n")},
                          "micro": micro, "sigma_ticks": sig_tk, "cost_ticks": cost,
                          "gross_ticks": gross, "net_ticks": gross - cost,
                          "gross_over_cost": gross / cost})
    P(f"  {'root':>5}{'fam':>4}{'H':>4}{'sigma tk':>10}{'cost tk':>9}{'gross tk':>10}"
      f"{'net tk':>9}{'g/c':>7}")
    for t in sorted(trade, key=lambda z: -z["gross_over_cost"])[:12]:
        P(f"  {t['root']:>5}{t['family']:>4}{t['H']:>4}{t['sigma_ticks']:>10.1f}"
          f"{t['cost_ticks']:>9.3f}{t['gross_ticks']:>10.3f}{t['net_ticks']:>9.3f}"
          f"{t['gross_over_cost']:>7.2f}")
    n_pos = sum(1 for t in trade if t["net_ticks"] > 0)
    P(f"  net positive: {n_pos} of {len(trade)}")
    P(f"  **BLOCKED, no committed micro spec: {', '.join(blocked)}** -- MGC/MCL/M6E are "
      f"absent and no tick value is guessed (§3)")

    # ---- §6 predictions
    d484 = json.loads((REPO / "data" / "d484_offdiagonal_and_macd.json")
                      .read_text(encoding="utf-8"))
    nonidx_long = {r["root"]: r["edge_sigma"] for r in rows
                   if r["family"] == "B1" and r["H"] == max(H_NONINDEX)
                   and not r["index_root"]}
    best_long = max(nonidx_long, key=nonidx_long.get) if nonidx_long else None
    wa = verdicts["B1"]["edge_grows"]
    wb = verdicts["B1"]["exponent"] < 1.0      # H=1..5 on NQ implied roughly ~1.0
    wc = not any(t["net_ticks"] > 0 for t in trade if t["root"] in INDEX_ROOTS)
    wd = best_long in ("GC", "CL")
    P(f"\n  === PRE-REGISTERED PREDICTIONS (D488 §6) ===")
    P(f"    W-a B1 exponent > 0.5 and clears R1   {'HELD' if wa else 'BROKEN':>7}  "
      f"{verdicts['B1']['exponent']:+.3f}")
    P(f"    W-b the rise DECELERATES               {'HELD' if wb else 'BROKEN':>7}")
    P(f"    W-c no index root tradeable            {'HELD' if wc else 'BROKEN':>7}")
    P(f"    W-d GC or CL largest at the longest H  {'HELD' if wd else 'BROKEN':>7}  "
      f"best = {best_long}")

    res = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "pre_registration": "docs/decisions/D488-PRE-REG-does-the-MACD-edge-keep-growing-"
                               "with-the-holding-period-and-does-it-cross-its-cost.md",
           "purpose": "D488: does the D484 MACD edge keep growing with the hold, and does it "
                      "cross its cost? Signal code imported from D484 unchanged.",
           "constraints_enforced": {
               "P2_last_exit_segment_index": LAST_EXIT_IDX,
               "closure_index_roots_day_session_only": True,
               "index_roots": list(INDEX_ROOTS), "holds_index": list(H_INDEX),
               "holds_nonindex": list(H_NONINDEX)},
           "S1_cells": rows, "S2_growth_exponent": expo, "nulls": nulls_out,
           "verdicts": verdicts, "S3_tradeability": trade,
           "S3_blocked_no_micro_spec": blocked,
           "predictions": {"W-a": bool(wa), "W-b": bool(wb), "W-c": bool(wc),
                           "W-d": bool(wd)},
           "limitations": [
               "the volume-clock exit (D472, +10.4%) is NOT applied, so every figure "
               "understates by roughly that much",
               "the 1.009-tick crossing is an ES measurement assumed for other roots",
               "overlapping holds mean the effective sample is far smaller than the row "
               "count; only the rotation null's distribution is used for inference",
               "H=22 admits one entry per session, so ~2,000 independent observations",
               "in-sample only; 2024+ sealed",
               "eight roots are not eight independent draws (ZN/ZB rates, ES/NQ/YM index)",
               "GC, CL, ZN, ZB and 6E cannot be costed: MGC/MCL/M6E are absent from the "
               "committed specs and no tick value is guessed"]}
    if as_json:
        OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
        P(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.run:
        return do_run(a.json)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
