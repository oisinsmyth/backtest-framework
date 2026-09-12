"""How many CME names are worth buying, measured on ETF proxies. NOT a study.

    uv run python scripts/project_futures_breadth.py
    uv run python scripts/project_futures_breadth.py --json

WHAT QUESTION THIS ANSWERS
--------------------------
Under a one-month Databento Standard subscription every additional symbol costs
NOTHING, so the buy list is no longer bounded by money. It is bounded by disk, by
download hours, and by whether an extra contract adds any independent information.
This measures the third one.

THE CEILING, AND IT IS THE WHOLE POINT
--------------------------------------
`docs/FINDINGS.md` §4: *"Effective independent instruments saturate at `1/rho`
regardless of `n`"*, with

    N_eff = N / (1 + (N-1) * rho_bar)

and it reports 57 ETFs at rho 0.47 -> 2.2, and 486 ETFs at rho 0.48 -> 2.1. **Going
from 57 to 486 instruments LOWERED effective breadth.** So "more names" is not a
strategy; lowering rho_bar is.

R16 AND THE TWO DISAGREEING PUBLISHED NUMBERS
---------------------------------------------
`docs/prop firm leads/01-prop-lead.md` §6.2 quotes **1.17** for four equity indices,
**3.00** for a 12-symbol futures complex and **2.35** for 55 ETFs. `FINDINGS.md` §4
quotes **2.2** for 57 ETFs on the same idea. Those are different builds and they do
not agree, so under [R16](../docs/RULES.md#r16) neither is inherited here. Everything
below is recomputed on one named fixture, and the 57-ETF cell is recomputed too so a
reader can see which published figure this build reproduces.

TWO MEASURES, REPORTED SEPARATELY, NEVER CONFLATED
--------------------------------------------------
  N_eff(rho)   N / (1 + (N-1)*rho_bar)   -- the variance-reduction measure FINDINGS
                                            uses; answers "how much does averaging
                                            these reduce variance"
  PR           (sum lambda)^2 / sum(lambda^2) on the correlation matrix -- the
                                            eigenvalue participation ratio D251 uses
                                            (3.61 raw -> 11.55 market-neutral)

They answer different questions and give different numbers on the same data. Both are
printed because quoting one as the other is exactly the error R16 exists to stop.

THE PROXY CAVEAT, STATED NOT BURIED
-----------------------------------
**These are ETFs, not futures.** An ETF tracks its index; the future carries basis,
roll and a 23-hour session. What transfers is the CROSS-ASSET CORRELATION STRUCTURE --
gold against bonds against crude -- which is a property of the underlying risk, not of
the wrapper. What does NOT transfer is anything about level, cost or path. This is an
acquisition-planning measurement for choosing a buy list, and it opens and closes
nothing.
"""

from __future__ import annotations

import argparse
import gzip
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "etf_wide_daily_raw.csv.gz"
OUT = REPO / "data" / "futures_breadth_projection.json"

# CME root -> the ETF that proxies its UNDERLYING RISK, with the family it sits in.
# Where no honest proxy exists the entry is None and the symbol is reported as
# unmeasurable rather than quietly dropped.
PROXY = {
    # equity index -- the venue's liquid contracts, and what C1/C2/C3 were screened on
    "ES": ("SPY", "equity index"), "NQ": ("QQQ", "equity index"),
    "RTY": ("IWM", "equity index"), "YM": ("DIA", "equity index"),
    "EMD": ("MDY", "equity index"),
    # micros -- SAME underlying as their e-mini. Bought for contract SIZE, never breadth.
    "MES": (None, "micro"), "MNQ": (None, "micro"),
    "M2K": (None, "micro"), "MYM": (None, "micro"),
    # energy
    "CL": ("USO", "energy"), "NG": ("UNG", "energy"), "RB": ("UGA", "energy"),
    "HO": (None, "energy"),
    # metals
    "GC": ("GLD", "metals"), "SI": ("SLV", "metals"), "PL": ("PPLT", "metals"),
    "PA": ("PALL", "metals"), "HG": ("DBB", "metals"),
    # rates
    "ZT": ("SHY", "rates"), "ZF": ("IEI", "rates"), "ZN": ("IEF", "rates"),
    "ZB": ("TLT", "rates"), "UB": ("EDV", "rates"),
    # FX
    "6E": ("FXE", "FX"), "6J": ("FXY", "FX"), "6B": ("FXB", "FX"),
    "6A": ("FXA", "FX"), "6C": ("FXC", "FX"), "6S": ("FXF", "FX"),
    # ags and softs
    "ZC": ("CORN", "ags"), "ZS": (None, "ags"), "ZW": (None, "ags"),
    "AGS_BASKET": ("DBA", "ags"),
    # livestock -- no surviving ETF proxy
    "LE": (None, "livestock"), "HE": (None, "livestock"),
    # international equity, which the prop lead's "diversified complex" includes
    "NKD": ("EWJ", "intl equity"), "FT5": ("FXI", "intl equity"),
    "MXEF": ("EEM", "intl equity"), "MFS": ("EFA", "intl equity"),
    # crypto -- CME contracts exist but no ETF proxy spans this fixture's window
    "BTC": (None, "crypto"), "MBT": (None, "crypto"),
}

# The order families are added in. Equity first because that is what the track
# already screened on, so every later row is a MARGINAL gain over the status quo.
FAMILY_ORDER = ["equity index", "rates", "metals", "energy", "FX", "intl equity", "ags"]

MIN_DAYS = 1500


def load_returns() -> tuple[dict[str, np.ndarray], list[str]]:
    """Daily log returns from the committed wide ETF fixture, on the common date grid."""
    by_sym: dict[str, dict[str, float]] = {}
    with gzip.open(FIXTURE, "rt") as fh:
        fh.readline()
        for line in fh:
            p = line.rstrip("\n").split(",")
            by_sym.setdefault(p[1], {})[p[0][:10]] = float(p[5])
    wanted = {p for p, _f in PROXY.values() if p}
    have = {s: v for s, v in by_sym.items() if s in wanted and len(v) >= MIN_DAYS}
    dates = sorted(set.intersection(*(set(v) for v in have.values())))
    out = {}
    for s, v in have.items():
        px = np.array([v[d] for d in dates])
        out[s] = np.diff(np.log(px))
    return out, dates


def n_eff_rho(R: np.ndarray) -> tuple[float, float]:
    """FINDINGS §4's measure: N / (1 + (N-1)*rho_bar), and rho_bar itself."""
    n = R.shape[0]
    if n == 1:
        return 1.0, float("nan")
    iu = np.triu_indices(n, 1)
    rho = float(np.mean(np.corrcoef(R)[iu]))
    return n / (1.0 + (n - 1) * rho), rho


def participation_ratio(R: np.ndarray) -> float:
    """D251's measure: (sum lambda)^2 / sum(lambda^2) on the correlation matrix."""
    if R.shape[0] == 1:
        return 1.0
    lam = np.linalg.eigvalsh(np.corrcoef(R))
    lam = np.clip(lam, 0, None)
    return float(lam.sum() ** 2 / (lam ** 2).sum())


def block(rets, syms):
    return np.vstack([rets[s] for s in syms])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    rets, dates = load_returns()
    print(f"fixture {FIXTURE.name}   {dates[0]}..{dates[-1]}   {len(dates)-1:,} common days   "
          f"{len(rets)} proxies resolved")

    measured = {r: (p, f) for r, (p, f) in PROXY.items() if p and p in rets}
    missing = {r: f for r, (p, f) in PROXY.items() if not p or p not in rets}
    print(f"\nUNMEASURABLE, reported not dropped: "
          + ", ".join(f"{r}({f})" for r, f in sorted(missing.items(), key=lambda x: x[1])))

    fams: dict[str, list[str]] = {}
    for root, (px, fam) in measured.items():
        fams.setdefault(fam, []).append(px)

    # 1. Redundancy INSIDE each family -- where a buy list wastes contracts.
    print(f"\n{'family':14}{'n':>3}{'rho_bar':>9}{'N_eff':>8}{'PR':>7}   proxies")
    within = {}
    for fam in FAMILY_ORDER:
        syms = sorted(set(fams.get(fam, [])))
        if len(syms) < 2:
            continue
        R = block(rets, syms)
        ne, rho = n_eff_rho(R)
        pr = participation_ratio(R)
        within[fam] = {"n": len(syms), "rho_bar": rho, "n_eff": ne, "pr": pr, "proxies": syms}
        print(f"  {fam:12}{len(syms):>3}{rho:>9.3f}{ne:>8.2f}{pr:>7.2f}   {' '.join(syms)}")

    # 2. Nested build-up: what each family ADDS over everything before it.
    print(f"\n{'complex':34}{'n':>3}{'rho_bar':>9}{'N_eff':>8}{'dN_eff':>8}{'PR':>7}")
    nested, acc, prev = {}, [], 1.0
    for fam in FAMILY_ORDER:
        syms = sorted(set(fams.get(fam, [])))
        if not syms:
            continue
        acc = sorted(set(acc) | set(syms))
        R = block(rets, acc)
        ne, rho = n_eff_rho(R)
        pr = participation_ratio(R)
        label = " + ".join(FAMILY_ORDER[:FAMILY_ORDER.index(fam) + 1])
        nested[fam] = {"through": fam, "n": len(acc), "rho_bar": rho, "n_eff": ne,
                       "delta_n_eff": ne - prev, "pr": pr, "proxies": acc}
        print(f"  {label[:32]:32}{len(acc):>3}{rho:>9.3f}{ne:>8.2f}{ne - prev:>8.2f}{pr:>7.2f}")
        prev = ne

    # 3. The saturation ceiling, which is what actually bounds the buy list.
    full = nested[[f for f in FAMILY_ORDER if f in nested][-1]]
    print(f"\n  ceiling 1/rho_bar on the full complex = {1/full['rho_bar']:.2f} "
          f"effective instruments, reached asymptotically no matter how many contracts are added")

    # 4. Recompute the published ETF cell on THIS build, per R16.
    etf_all = sorted(rets)
    R = block(rets, etf_all)
    ne_all, rho_all = n_eff_rho(R)
    print(f"\n  R16 check -- all {len(etf_all)} resolved ETF proxies on this build: "
          f"rho_bar {rho_all:.3f}, N_eff {ne_all:.2f}, PR {participation_ratio(R):.2f}")
    print("  FINDINGS §4 publishes 2.2 for 57 ETFs at rho 0.47; the prop lead publishes 2.35 "
          "for 55.\n  Those are different builds and neither is inherited.")

    # 5. One-in-one-out: the marginal value of each contract at the margin.
    print(f"\n  marginal cost of DROPPING one name from the full complex (N_eff falls by):")
    drops = {}
    for s in full["proxies"]:
        rest = [x for x in full["proxies"] if x != s]
        ne, _ = n_eff_rho(block(rets, rest))
        drops[s] = full["n_eff"] - ne
    for s, d in sorted(drops.items(), key=lambda x: -x[1])[:8]:
        print(f"    {s:6}{d:+7.3f}")
    print(f"    ...")
    for s, d in sorted(drops.items(), key=lambda x: -x[1])[-5:]:
        print(f"    {s:6}{d:+7.3f}")

    if a.json:
        OUT.write_text(json.dumps({
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "purpose": "acquisition planning: which CME names add independent information. Not a study; opens and closes nothing.",
            "fixture": FIXTURE.name, "window": [dates[0], dates[-1]], "n_days": len(dates) - 1,
            "proxy_map": {k: {"proxy": v[0], "family": v[1]} for k, v in PROXY.items()},
            "unmeasurable": missing,
            "measures": {"n_eff_rho": "N/(1+(N-1)*rho_bar), the FINDINGS §4 measure",
                         "pr": "(sum lambda)^2/sum(lambda^2), the D251 measure"},
            "within_family": within, "nested": nested,
            "ceiling_1_over_rho": 1 / full["rho_bar"],
            "all_proxies_this_build": {"n": len(etf_all), "rho_bar": rho_all, "n_eff": ne_all},
            "drop_one_delta_n_eff": drops,
        }, indent=1) + "\n", encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
