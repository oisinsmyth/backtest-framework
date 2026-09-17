# D506 — stage 1: does a signal's directional accuracy survive the in-play filter, or does selection only dilute the fee?

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D506-stage-1-does-a-signals-accuracy-survive-the-in-play-filter-or-does-selection-only-dilute-the-fee.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
In-sample **2016-01-04 → 2023-12-29** on `data/fixtures/fut_sessions_hourly.csv.gz`, the eight roots
that pass D467's gates. **2024-01 onward is not read.**

## 0. Why, and what is already measured

Design and premise: `working/DRAFT-in-play-on-the-prop-book.md` (`bd7f92f`), from the principal's
direction of 2026-09-13 after the in-play concept was parsed in `docs/youtube-lessons.md` §6.

The premise was measured before this record (`working/inplay_premise_scratch.py`, outcome never
touched — only |move|, σ and volume). A causal in-play score predicts the size of the day move it
precedes at ρ 0.09–0.20 per root and persists at ρ 0.19–0.41. Top decile against bottom raises
E|M| by ×1.15 to ×1.94 and cuts the fee's share of the move: ES 3.3% → 1.8%, NQ 2.1% → 1.2%,
YM 4.4% → 2.3%, 6E 9.7% → 7.1%.

**That arithmetic is worth +0.05 to +0.30 of Sharpe and creates no edge**, because
`Sharpe ≈ √252/c · [(2p − 1) − fee/E|M|]` with `c = σ/E|M|` measured at 1.3–1.4, and selection moves
only the second term. **The whole value rests on the assumption that directional accuracy `p` is
unchanged on in-play sessions. This record tests that assumption and nothing else.** No new signal
is invented.

## 1. Definitions

- **Session set.** Same-front sessions, 2016-01-04 → 2023-12-29, per root. Day open `O = h09_o`,
  day close `C = h15_c`, **day move `M = (C − O) × multiplier`** in dollars at one minimum contract.
- **The overnight leg** is `h18 … h08`. Its **range** `NR` = (max high − min low) × multiplier and
  its **volume** `NV` = the sum of hourly volume over those segments.
- **The in-play score** `s_d = √( (NR_d / median₂₀(NR)) × (NV_d / median₂₀(NV)) )`, each median taken
  over the trailing 20 sessions **ending at d−1**. Known before 09:30.
- **In play** = `s_d ≥ Q90_d`, where `Q90_d` is the **trailing 250-session 90th percentile of `s`,
  ending at d−1** (causal, not a full-sample decile). The first 250 sessions are warm-up.
  "The rest" is every non-warm-up session that is not in play.
- **Realised day range** `DR_d` = (max high − min low over `h09 … h15`) × multiplier. Used only for
  the matched control and never as a conditioner in a traded cell.
- **Cost** is $3 a round trip on the micros and $6 on ZN/ZB, charged per trade, computed in the
  runner in dollars (the ledger's standard).

## 2. The two signals, both already owned by this programme

- **S1, the drift.** Always long the day session. `p` is then the share of sessions with `M > 0`.
- **S2, the log MACD** (D484 §3 B2, canonical 12/26/9, not tuned): `sign(macd_hist(log C))`
  evaluated on the **daily close series at d−1**, traded on the day session of `d`.
  `macd_hist(x) = m − EMA₉(m)` with `m = EMA₁₂(x) − EMA₂₆(x)`. **This is a declared daily-bar
  version of D484's signal, not a reproduction of D503's hourly MACD component**, and the record
  says so rather than borrowing that component's numbers.

Sessions where `M = 0` are excluded from `p` and reported.

## 3. The primary statistic, one (R14)

**`T = (2p − 1) − fee/E|M|`**, and the primary is **`Δ = T(in play) − T(the rest)` for S2 on YM.**

**YM is the declared primary root, not NQ**, for two stated reasons: it has the second-largest cost
improvement of any root (4.4% → 2.3%) with a daily σ of $184 that fits the account's budget, and its
2024+ slice is unread, whereas NQ's and ES's are spent (D503).

The raw quantities are reported beside `T` and are not the primary: gross and net mean per trade,
median, symmetric 1% trim, hit rate, skew, kurtosis, σ, and net Sharpe at one micro.
**If `Δ` and the raw mean disagree in sign, the record says so** — they can, because `(2p−1)E|M|` is
the edge only when winners and losers are the same size.

## 4. Controls

- **V, the control that decides it — realised-volatility matched.** Restrict to sessions in the
  **top decile of realised day range `DR`**, then split by the causal score: high (`s ≥ Q90`) against
  low (`s <` its causal median). `T(high) − T(low)` **within the same realised-size bucket**
  separates "the day was big" from "we knew in advance it would be big". If this difference is zero
  while the headline `Δ` is positive, the filter is a noisy proxy for realised size and its only
  tradeable content is its foreknowledge, which the premise put at ρ 0.09–0.20.
  Matched-count is not a control (D279) and a redrawn random subset is not a control for a
  persistent selector (D291).
- **W, wrong window.** The **previous** session's overnight score `s_{d−1}` in place of `s_d`. It
  must not reproduce the effect.
- **U, the untradeable upper bound.** The realised same-day range `DR_d` as the conditioner. It
  cannot be traded and exists to bound what perfect foreknowledge of the day's size would be worth.

## 5. Nulls

- **N1, exact enumerated common rotation.** The score series `s` (and with it the causal threshold
  and the in-play mask) is rotated by `k = 1 … T−1` sessions against the outcome pair `(M, signal)`,
  **enumerated**, ≈ 1,700 offsets after warm-up. A single market-level daily series per root, so the
  group is finite and the p95's sampling error is exactly zero. Per cell: p50, p95, and the share of
  offsets at or above the observed `Δ`.
- **N2, family maximum.** The **16 cells** (8 roots × 2 signals) share each offset `k`; the family
  bar is the p95 of the per-offset maximum of `Δ`. The primary must clear this, not only N1.

## 6. Decision rule (pre-registered)

**PROCEED** to a declared stage 2 (root selection) only if **all four** hold on the primary cell:

1. `Δ` clears the **N2 family p95**;
2. control **V** shows the same sign at a comparable size, so the effect is foreknowledge rather
   than realised size;
3. the in-play cell clears **C-a** (net Sharpe > 0.5 at one micro) on its own sessions;
4. **P3a**, recomputed per year rather than pooled, is **≤ 1.0 breaches a year** (R11's amendment of
   2026-09-13: P3 is a rate; P3b ≤ 33% life cost and P3c reported).

**PICK** if `Δ` clears N1 and V but not the family bar. **CLOSE** otherwise. The principal closes.

**On "recompute at 2026 price levels".** The 2024+ slice is the declared forward slice for the six
unspent roots and **is not read here**, so the runner cannot measure a 2026 σ directly. It instead
reports σ **per year in dollars** across 2016–2023 to expose the drift, and σ as a **percentage of
the index level**, from which σ at any stated level follows as `multiplier × level × σ%`. For NQ the
figure is already public on our own record without a re-read: D503 measured **$340** forward against
$180 in sample. Any 2026 check on the other roots requires the principal's word and is not performed.

## 7. Predictions (checkable in the runner's quantities)

- **X-a** `p` is **not** materially higher on in-play sessions for either signal: |Δp| < 1.5
  percentage points on the primary, and `Δ` is therefore driven almost entirely by the fee term,
  landing between **+0.005 and +0.020** (that is, +0.5 to +2.0 points of `(2p−1)`-equivalent).
- **X-b** `Δ` does **not** clear the N2 family p95, which lands between **+0.020 and +0.045**.
- **X-c** Control **V** is **near zero** (|T(high) − T(low)| < 0.010 within the top realised-range
  decile): within a fixed realised size, the causal score adds nothing, because its correlation with
  the move is only 0.09–0.20.
- **X-d** The untradeable bound **U** is **much larger** than the traded cells, at least +0.03 on the
  primary, confirming that the information is about size and that we have very little of it in
  advance.
- **X-e** S1's `p` on the day session is between **50% and 53%** on the index roots and S2's is
  between **50% and 52%**, so neither clears the 53.6% component bar in any decile, in play or not.
- **X-f** P3a on the in-play cell is **higher per traded session but lower per year** than the
  all-sessions cell, because the filter trades about a tenth of the days.
- **X-g** The verdict is **CLOSE**.

## 8. Files

This record · `scripts/run_d506_inplay_accuracy.py` (`--run`, `--selftest`) ·
`data/d506_inplay_accuracy.json` · a per-root cell table · RESULT (separate). Projected runtime
under three minutes: 8 roots × ~1,950 sessions, 16 cells, ≈ 1,700 enumerated offsets, vectorised
over offsets.
