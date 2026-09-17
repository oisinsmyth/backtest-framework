# D470 RESULT — stage 0: the drift follows DOWN nights, not up ones — a reversal sign on all eight cells that clears the single nulls on three, not the family bar, and lives in 2020–2022

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D470-RESULT-stage-0-the-drift-follows-DOWN-nights-not-up-ones-a-consistent-reversal-sign-on-all-eight-cells-that-clears-the-single-nulls-and-not-the-family-bar-and-lives-in-2020-2022.md`. The H1 above is the full title.*

**Result of the pre-registered stage-0 premise check in D470.** Runner `scripts/run_d470_gate_stage0.py`
(`--selftest` passes; `--run` 5.4 min), artefact `data/d470_gate_stage0.json`. ES and NQ, 2016-01-04
to 2023-12-29, same-front nights, state read at the previous session's 16:00 print; **2024-01
onward unread; no holdout spent.** Nothing enters the ledger (stage 0 cannot).

**Under [R15](../RULES.md#r15) this record closes nothing.**

---

## 0. The headline

**No cell meets the declared stage-1 criterion** (net Sharpe > 0.5, above N1 p95, above N2 p95 + 2 SE,
above the family-maximum p95). **But the principal's two conditions came out with the sign
reversed and the reversal is on every cell:** the drift is concentrated on nights that follow a
**down** session or a **down** overnight leg, on both roots and both windows, 8 of 8 in sign.

| cell (one micro, $3) | nights | p | gross $/night | other side | diff (SE) | net Sharpe of the gated component | N1 rotation p95 | N2 run-length p95 (+2 SE) | family p95 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **ES-W2 after a down overnight leg (G-B down)** | 904 | 45% | **+10.66** | −1.37 | **+12.0 (4.9)** | **+0.70 ± 0.26** | 8.37 ✓ | 8.76 ✓ | 13.45 ✗ |
| **NQ-W2 G-B down** | 887 | 44% | **+13.32** | −1.57 | **+14.9 (7.2)** | **+0.62 ± 0.25** | 11.27 ✓ | 11.64 ✓ | 19.52 ✗ |
| NQ-W1 after a down session (G-A down) | 813 | 44% | +24.92 | −1.16 | +26.1 (14.0) | +0.71 ± 0.29 | 23.41 ✓ | 23.17 ✓ | 29.08 ✗ |
| ES-W1 G-A down | 835 | 46% | +13.74 | +4.87 | +8.9 (8.9) | +0.52 ± 0.32 | 16.51 ✗ | 17.20 ✗ | 19.94 ✗ |
| ES-W1 below the 200-average (G-C below) | 361 | 21% | +24.53 | +4.86 | +19.7 (17.4) | +0.44 ± 0.32 | 19.23 ✓ | 22.65 ✓ | **19.94 ✓** (0.2% of offsets) |
| NQ-W1 G-C below | 339 | 19% | +5.79 | +12.23 | −6.4 (27.0) | +0.04 | | | |
| G-D (vol tercile), all four | | | high tercile worse on W1, mixed on W2 | | ≤ 1 SE | ≤ +0.21 | | | |

Ungated base rates reproduce D468 to the cent (ES-W1 $7.69 / 187; NQ-W1 $10.13 / 294).

## 1. What the reversal is, and what it is not

**The cleanest cell is the overnight leg after a negative overnight leg (W2, G-B down):** ES
+10.66 against −1.37 on the other side, a 2.5-SE difference; NQ +13.32 against −1.57, 2.1 SE;
both clear the exact rotation and the run-length null; the two are one construction (ρ(ES-W2,
NQ-W2) = 0.92, D468). The medians sit beside the means (+11.25 / +13.50) and the symmetric
1%-trimmed means are +9.86 / +12.21, so the left tail is not doing the work; the top 1% of nights
carries 51–55% of the P&L (2020-03-13, 2020-11-09, 2022-11-10, 2022-01-26 lead both lists),
which is the shape of every overnight series here.

**Where it lives — looked at, not inferred.** By year, gated mean against the other side:

| ES-W2 G-B down | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| after a down leg | −0.8 | +4.5 | +5.4 | +14.7 | **+39.2** | **+21.1** | +0.8 | +4.3 |
| after an up leg | +1.8 | +5.4 | +4.7 | +9.1 | +0.7 | −12.9 | **−20.4** | −3.5 |

In 2016–2019 the two sides are the same within noise (four years, gap ≤ $6 either way); the whole
difference is **2020 (the March crash and the November vaccine rally), 2021 and 2022** — the
high-volatility years, where index short-term reversal is a documented regime feature. NQ has
the same profile (2020: +37.5 vs +15.6; 2021: +25.6 vs −11.3; 2022: +6.0 vs −38.3; 2016–2019
mixed). **YM, read here as the third root outside the pre-registered family:** W2 G-B down +6.63
vs +1.08 (same sign, 5 of 8 years); W1 G-A down +6.94 vs +6.51 (**no concentration**, 4 of 8).

So: **a reversal with a consistent sign whose size is a regime property**, present in three of
eight years, absent in four, and the family null — which prices exactly this (the best of eight
cells drawn from a series whose variance is concentrated in those same years) — refuses it on
both roots. The stage-1 criterion was written for this case and it did its job.

**The 200-average cell on ES is a pick.** It clears every null including the family bar (only
0.2% of common offsets produce a $24.53 cell), and 6 of 6 years show it — but its 361 nights are
56% 2022 and 17% 2020, its 2022 "other side" is 13 nights at −$107, **NQ shows the opposite
sign** (+5.79 below vs +12.23 above), and its gated net Sharpe is +0.44, below the bar. One root
against the other on the same construction is not a concentration; it is the ES-only path of
2022.

**Vol terciles concentrate nothing** (high-σ nights are worse on W1 on both roots), which is
the arithmetic §0 of the spec predicted: σ rises with the mean.

## 2. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a base rates reproduce D468 | | exact | right |
| X-b G-A / G-B sides differ by < 1 SE (no concentration) | | ES G-B on W2 **2.5 SE**, NQ 2.1 SE; W1 1.0 / 1.9 SE | **wrong**, and in the sign opposite to the principal's continuation hypothesis |
| X-c below-average: 1.3–2.0× mean, 1.4–1.7× σ, gated Sharpe < 0.5; G-D high same | | ES **3.2×** / 1.7× / +0.44; NQ **0.57×** / 1.6× / +0.04; G-D high 0.5× and −0.03× | Sharpe right; the size wrong on ES and the sign wrong on NQ |
| X-d no cell clears all three; ES-W1 family p95 $11–14 | | none clears; family p95 **$19.94** | verdict right; the family null is wider than I set because the small-p cells (G-C, G-D) carry σ 270–320 |
| X-e W2 ratios closer on the below / high-vol side | | 5.7% vs 7.6%; 4.5% vs 1.5% | half right |
| X-f under 2 min | | 5.4 min | wrong: 32 cells × (rotation + 2,000 run-length draws) in pure Python; the family loop is the cost |

## 3. What this leaves standing, and what a stage 1 could and could not do

- **The overnight leg after a negative overnight leg is a declared pick with a consistent sign**
  (8 of 8 cells across ES, NQ, YM and two windows), an in-sample gated net Sharpe of 0.6–0.7 at
  micro cost, and a size that comes from 2020–2022. It is not a component: it failed the family
  bar this record set for it, and it was selected here.
- **An in-sample stage 1 would prove nothing** — it would re-report these numbers under a
  narrower declaration. **The only test that can promote it is the unread 2024-01 → 2026-09
  slice, and that slice is underpowered for a single cell:** ≈ 430 W2 nights, ≈ 190 after a down
  leg, SE of the gated mean ≈ $7.8 against an expected +$10.7 — about 1.4 SE if the effect is
  its in-sample size, and nothing if 2024–2026 is a 2016–2019-type regime. Reading it costs the
  slice for this construction. **Not read; the principal's call.**
- **Continuation is the wrong sign on every cell.** The prior-close-above-average condition is
  the wrong sign on ES (below is better) and inconsistent on NQ.
- The arithmetic in the spec stands: a gate that trades 45% of nights must lift the per-night
  ratio 1.5× to stand still; the down-leg gate lifts it 2.3× (ES-W2 9.2% vs 4.0%) and that is why
  its gated Sharpe clears 0.5 in-sample. It is the one condition tested here that beats the
  √p penalty, and it beats it in three years out of eight.

## 4. Files

Runner · `data/d470_gate_stage0.json` · this record · the ledger's *Scored and NOT entered*
row.
