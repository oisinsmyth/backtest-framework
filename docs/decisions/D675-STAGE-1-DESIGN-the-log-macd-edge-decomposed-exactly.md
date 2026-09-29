# D675 STAGE 1 DESIGN — D484's log MACD edge decomposed exactly: continuation or reversal, which clock, which moves, which state

*Drafted 2026-09-29 on the principal's word. Committed alone, before its runner exists (R8). **No decomposition has
been computed.** Before drafting I checked only mechanics that read no forward return: the kernel's shape, and the
identity of §2 on the real price chains. It is a diagnostic on data D484 already read, so it gives no verdict. TAIL
(lags ≥ 79) holds 0.69% of the kernel's absolute weight. Both books; it
measures only and admits nothing.*

## 0. Why, and what it can and cannot decide

The principal, 2026-09-29:

> "Lets re-examine the Log MACD. We have learnt a lot since then, we now require a deterministic explanation of the
> underlying mechanism. Not just testing random signals, we design a signal that fires on a mechanism of the market
> we can make money off."

Then: "Ok lets go start with stage 1".

**The programme has three stages.**
1. **Stage 1, this record:** locate exactly where D484's edge comes from.
2. **Stage 2:** design a signal that fires on the mechanism's own observable, not on the MACD. It gets its own
   pre-registration, per root, with a component line on both books.
3. **Stage 3:** confirm on a slice nothing has read. An inventory of every open seal comes first, then the slice's
   power.

**What D484 found.** On 8 roots, hourly, 2016-01-04 → 2023-12-29, the plain log MACD histogram (12/26/9, B2) has a
pooled gross edge of +0.00720 σ (+32.4 SE over the rotation null's p95). It fails only on micro cost. On a full NQ
contract it nets +2.24 ticks a trade.

**What is known since.**
- The admitted arm descends from it (D486 → D491 → D495 → D503), and D669, D670 and D673 found the arm has no portable
  mechanism.
- D484's edge itself has never been taken apart.

**The fact that makes the decomposition worth doing.** The histogram is a fixed linear filter of past returns, and
its weights **sum to zero**:
- positive on returns 0–13 bars ago (peak at 3);
- negative, in equal total, on returns 14 bars ago and older (trough at 23; 90% of the absolute weight lies within
  43 bars).

So `sign(hist) > 0` means "the last ~13 hours rose more than the previous one to three days did". The edge can come
from continuation of the recent move, from reversal of the older one, or from both. D484's own Part A points at
reversal: plain sign-momentum lost at −62 SE on the same data.

**What this can decide.** Which lags, clock hours, kinds of move and market states carry the edge, per root. It also
decides which of six candidate mechanisms (§4) has the fingerprint the decomposition shows.

**What it cannot decide.**
- **Nothing is admitted or confirmed.** The window is the one D484 read. A mechanism located here is a hypothesis for
  Stage 2, confirmed only in Stage 3.
- **Nothing from 2024 on is read.**

## 1. The object, frozen and imported

- **D484's B2 on D484's data.** The runner imports `scripts/d484_offdiagonal_and_macd.py` unchanged for:
  - `series_for` and its contract-purity mask (78 trailing bars on one contract);
  - `macd_hist`;
  - the forward return: `f_H[t] = log close[t+H] − log open[t+1]`, entry at the next bar's open;
  - the edge `E = mean(signal · f) / σ(f)` over bars where the signal is finite and non-zero.
- **Roots:** ES, NQ, YM, ZN, ZB, GC, CL, 6E (RTY is excluded, as in D484).
- **Holds:** H ∈ {1, 2, 3, 5} bars.
- **Window:** 2016-01-04 → 2023-12-29.
- **Fixture:** `fut_sessions_hourly.csv.gz`, read from `--data-root`, because the fixture is gitignored. Its 23
  segments are ET hours, h18 → h16.
- **B1, the impulse MACD, is not decomposed.** It is not linear: it has a no-trade band and uses highs and lows.
  D484 §7.4 left open whether B1 and B2 measure the same smoothed trend. The runner reports their sign agreement per
  root, and nothing more.

## 2. The exact identity

**The kernel.** Let `r_s` be the log close-to-close return along a root's chain of valid bars. A bar whose OHLC is
not all positive is dropped from the chain, exactly as the EMA skips it; that is 94–254 bars per root. Then
`hist_t = Σ_{k=0}^{t−1} w_k · r_{t−k}` exactly, where:
- `w_k` is the impulse response of the 12/26/9 histogram;
- the EMA initialisation is `s_0 = p_0`, so `r_0 = 0`.

Checked before drafting, on all 8 chains: the largest difference from `macd_hist` is 4.6e-17 to 3.4e-15 in log units,
or 1.4e-13 to 6.6e-12 of the histogram's standard deviation. The kernel is truncated at 2,000 lags, where the weight
is below 1e-60.

**Three versions of the signal at bar t:**

| | signal | role |
|---|---|---|
| **S** | `sign(hist_t)` | D484's traded signal. Its edge is reproduced exactly. |
| **L0** | `hist_t` | raw linear; reported only |
| **L1** | `hist_t / v_t` | **the version decomposed.** `v_t = sqrt(EMA_120(r²))` along the chain through t, so it is known at the close of t. 120 bars is about five sessions, declared and not tuned. |

L1 is rescaled by its RMS over the valid bars, so its edge is in the same units as S's. The rescaling is one constant
per root and hold, so it does not disturb the identity.

**Why L1, and the guard on it.** S is not linear, so it cannot be split across lags. L1 is linear, and its edge
splits exactly:

`E_L1 · N · σ(f) · rms = Σ_t Σ_k Σ_{j=1}^{H} w_k · r_{t−k} · g_{t+j} / v_t`

Here `g_{t+1}` is the entry bar's open-to-close return and `g_{t+j}` (for j ≥ 2) is the close-to-close return, so that
`f_H = Σ_j g_{t+j}`. Every term belongs to exactly one cell of each partition in §3, so **each partition's cells sum
to E_L1.** The runner asserts this to 1e-10 relative.

**The guard.** L1's lag split is read as S's only on a root where both of these hold:
- **G-S1:** L1 and S have the same sign (on the mean over the four holds);
- **G-S2:** across the 13 time-subset cells of §3 (5 target clocks and 8 years), the Pearson correlation between S's
  contributions and L1's is at least 0.5.

A root that fails either is reported with its lag split marked **NOT REPRESENTATIVE**.

## 3. The partitions

**Source side** (attributes of the lagged bar s = t − k, or of the pair):

| | cells |
|---|---|
| **Lag region** (by k) | **CONT** 0–13 (the positive weights); **REV1** 14–39; **REV2** 40–78; **TAIL** ≥ 79 (beyond the purity window, so it holds any roll gap). **REV** = REV1 + REV2 + TAIL. |
| **Source clock** (segment of s) | ASIA h18–h02 · EUROPE h03–h08 · US_OPEN h09–h10 · US_MID h11–h13 · US_CLOSE h14–h16 (9 + 6 + 2 + 3 + 3 = 23) |
| **Same session** | s in the same 18:00–16:59 session as t, or an earlier one |
| **Move size** | `|r_s| / v_{s−1}`: SMALL < 1, MID 1–2, LARGE ≥ 2 |
| **Source volume** | the bar's volume against the median of the same segment over the prior 20 sessions: HIGH ≥ 1.5×, NORMAL otherwise |
| **Source sign** | UP (r_s > 0), DOWN (r_s < 0) |

**Time side** (subsets of the signal time t):

| | cells |
|---|---|
| **Target clock** | the segment of the entry bar t+1, in the same five groups |
| **Year** | the year of t, 2016–2023 |
| **Vol state** | RISING when `sqrt(EMA_23(r²)) > sqrt(EMA_230(r²))` at t (about one session against about ten), FALLING otherwise |
| **Dealer gamma** | ES only: the sign of SqueezeMetrics GEX on the last row dated strictly before t's session day. SHORT when GEX < 0. |

**The components.** The runner computes a component series for:
- each lag region;
- each of CONT and REV crossed with source clock, same session, move size, source volume and source sign;
- S and the L1 total.

Each component is paired with the forward return restricted to each time subset. The cells reported are the
component × subset products. Mixed pairs not listed here are not reported.

**Intensity, for reading a bucket.** A raw contribution scales with how much of the signal a bucket holds.
`I_b = (C_b / C_region) / (V_b / V_region)`, where `V_b = Σ_t Σ_{k ∈ region} w_k² r_{t−k}² 1[b] / v_t²` is the
bucket's share of the component's variance. I_b > 1 means the bucket contributes more than its share of the signal.
For a time subset, intensity is the contribution per bar relative to the root's contribution per bar.

**Holds.** Every cell is reported per hold. The per-root figure is the mean over the four holds, as D484's P1 averages
cells.

## 4. The mechanisms and their fingerprints, declared before the run

Each fingerprint is read per root, on the mean over the holds, on L1. A mechanism **fits** a root when all its
fingerprints hold there. Several can fit one root. None is a verdict; Stage 2 designs from what fits.

| mechanism | the idea | fingerprints (all must hold) |
|---|---|---|
| **F1 Liquidity-provision reversal** (Grossman–Miller; Campbell–Grossman–Wang 1993) | Price moves forced by liquidity demand revert once intermediaries lay off their inventory, and high-volume moves revert more. | (a) REV > 0.5·E_L1 and REV above its null p95; (b) within REV, I_HIGH > 1; (c) within REV, I_LARGE > 1; (d) within REV, UP and DOWN both contribute positively |
| **F2 Metaorder splitting** (order-flow persistence, Lillo–Farmer) | Large orders worked over hours keep the flow one-signed, so the price continues while they execute. | (a) CONT > 0.5·E_L1 and CONT above its null p95; (b) within CONT, same-session intensity > cross-session intensity; (c) CONT's target-clock intensity is above 1 in the root's liquid hours: US_OPEN + US_MID + US_CLOSE, or for 6E EUROPE + US_OPEN + US_MID |
| **F3 Vol-target / deleveraging feedback** | Volatility-targeting and risk-parity money sells as volatility rises, which extends moves. | (a) CONT above its null p95; (b) CONT's RISING intensity > FALLING; (c) within CONT, I_DOWN > I_UP; (d) 2018, 2020 and 2022 together supply more than half of CONT (they hold 37.5% of the bars) |
| **F4 Overnight information carried into the US day** | News that lands abroad is absorbed by the US session over its first hours. | (a) CONT above its null p95; (b) CONT's cells with source clock ASIA or EUROPE and target clock US_* supply more than half of CONT |
| **F5 Dealer gamma** (ES only) | Short-gamma hedging chases moves; long-gamma hedging leans against them. | (a) CONT's SHORT intensity > LONG; (b) REV's LONG intensity > SHORT |
| **F6 Settlement or fix flow** | A benchmark window concentrates flow at one clock hour. | Target-clock intensity ≥ 2 in the root's window: US_CLOSE for ES, NQ, YM, ZN, ZB and CL (CL settles 14:30, in h14); US_MID for GC (13:30, in h13) and for 6E (the WM/R fix at 11:00 ET, in h11) |

**Signed order flow**, the direct measurement F2 needs, exists only for ES, NQ, YM and RTY (the Sierra ticks). If F2
fits, measuring it is Stage 1b, a separate record.

## 5. The null

**An exact session rotation, enumerated.** For each root, hold and cell, the forward return and its time subset are
rotated together against the component by 23·j bars (whole sessions). This keeps every bar's clock, and it keeps each
time subset attached to its own returns. Every offset from 5 sessions to n − 5 sessions is enumerated. The five-session
purge at each end (115 bars) holds the kernel's effective length away from the unrotated alignment: 99% of |w| lies
within 74 bars and 99.9% within 104. Enumeration makes the p95's SE exactly zero.

**Fixed constants.** The normalisers (the count N, σ(f) and L1's rms) stay at their observed values, so the null
varies only the numerator. The observed value is the null draw at offset 0, computed by the same function, so the two
cannot differ by a rounding path. `fast_null.py` does not apply: it rotates equity-panel books, not a
cross-moment. This record uses its principle instead.

**Reported:** each cell's value, the null's p50 and p95, and the value's percentile.

## 6. Predictions (mine, before the run)

1. **G0 reproduction:** all 32 B2 cells of `data/d484_offdiagonal_and_macd.json` reproduce bit for bit, and P1 pooled
   is +0.007203157478334437.
2. **The identity** closes to 1e-10 relative in every partition.
3. **L1 represents S** (G-S1 and G-S2) on at least 7 of 8 roots.
4. **REV supplies more than half of E_L1 on at least 5 of 8 roots.** The MACD is mostly a reversal signal.
5. **TAIL supplies under 10% of E_L1 on every root.**
6. **F1 fits at least 3 roots; F4 fits at most 2.**

## 7. What is reported

- **Per root and hold:** E_S (reproduced), E_L0 and E_L1, with the guard's two figures.
- **Every partition's cells**, with the null's p50, p95 and percentile, and intensities.
- **The fingerprint table:** mechanism × root, each fingerprint's number and whether it holds.
- **In ticks:** each root's gross ticks per trade for S (D484 §2's conversion), and the share of it from CONT and REV.
  This record is not a trade. The cost lines, micro and full size, come with Stage 2.
- **The forward-window roll:** D484's purity mask checks only the trailing 78 bars, so a forward window can cross a
  roll. The runner reports how many such bars there are and their contribution. The decomposition keeps D484's mask
  so that G0 holds.
- **SqueezeMetrics:** aggregates only (licence note, `docs/research/licences/squeezemetrics-dix-gex.md`). No per-date
  series is written.

**Output:** `data/d675_macd_kernel_decomposition.json`, from `scripts/d675_macd_kernel_decomposition.py`.
**Projected wall time:** about 3 minutes. Most of it is the null, run as a GEMM per offset over sliced views of a
doubled target array, so no array is rolled.

## 8. Runner assertions and self-test

1. **Lag audit:** the component at t is unchanged when every return after t is altered. The check is a second path
   that rebuilds z_t from the chain up to t alone, without calling the convolution.
2. **Sign audit, in money:** on a synthetic chain with a positive component and a positive forward return, the
   contribution is positive; flip the forward return and it is negative.
3. **Right quantity:** the forward return starts at the open of t+1, not the close of t. The runner asserts that the
   two differ on the real data and that it uses the first.
4. **Identity:** the cells of each partition sum to E_L1, and the L1 total equals the direct mean.
5. **Reproduction:** G0 as in prediction 1. Any mismatch stops the run.

**Each audit must be able to fail.** The self-test feeds each one a deliberately broken input (a look-ahead
component, an inverted sign, a close-of-t entry, a dropped cell) and asserts that it raises.
