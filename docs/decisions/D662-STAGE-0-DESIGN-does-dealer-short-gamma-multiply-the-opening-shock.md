# D662 — STAGE 0 DESIGN: does dealer short gamma multiply the opening shock? The shock × gamma product at the opening-range break, on ES

*2026-09-28.*
- *The principal: "Yes, write the design", then "Continue with the original design, if we end up with the same
  results so be it".*
- *It follows D661, after the principal's question whether stacked flows could be super-additive.*
- *It is committed alone, before its runner (R8).*
- *Stage 0 is a premise check on the in-sample. It builds no book, and it spends no reserved sample.*

## 1. The question and the mechanism

**When dealers are short gamma, their hedging trades with the move.** A shock that moves the price makes them trade
further in the same direction. A shock Q then moves price by about λQ / (1 + λG), where G is dealer gamma (negative =
short) and λ the price impact per dollar. Neither the shock nor gamma need show alone. Their **product** can.

**At the open the mechanism is lagged hedging.** Dealers' delta drifts with the overnight move and with the stops run
early in the session. They rebalance in the cash session, so the rebalancing flow is −G × (the move being hedged):
- short-gamma dealers trade with that move;
- long-gamma dealers trade against it.

**The question:** does the follow-through of the opening-range break depend on the product of (a) dealer short gamma
and (b) a shock the break direction is exposed to? Each is tested alone as a control.

**What is new here, and what is not.** v1's agent A4 is already a product, P4 = −G × (open − prior close):
- D645 H-O6 found its linear coefficient on r(09:31 → 10:30), over all days, at **0.002 bp per z (t 0.00)**;
- D645 S-H found it added 0.02% to log loss;
- D652 found its liquidity scaling changed nothing.

This design differs in five ways:
1. The outcome is the **follow-through after the break**: entry at the break, 10:00–11:29. It is not the first hour
   on every day.
2. The product is written **multiplicatively**, with main effects and an interaction. Gamma enters in dollars
   relative to liquidity.
3. The model's **own size claim** is tested (β against the predicted push), as D640 did.
4. It adds a second shock never tested: the **stop run**.
5. It has a **midday placebo**, and tail and era reads.

The overlap with H-O6 is large, and the author expects the same null (§9).

## 2. The prize, on paper and before any outcome

`scripts/diag_opening_gamma_product_sizing.py` → `data/opening/gamma_product_sizing.json`. It reads inputs only: ES
gamma, the gap, the opening range against the prior day's levels, σ and volume. No return after 09:30 is read.

Setup:
- 2,227 in-sample sessions. Dealer gamma in dollars per 1% has median +$0.9bn, p5 −$8.3bn, p95 +$9.8bn. It is short
  on 42% of sessions.
- The implied rebalancing flow is Q = |G$| × |move| (%). The push is Y σ_d √(Q / V), from the prior 20 sessions' σ and
  day-session dollar volume.
- The bar (D661, mean-push terms): the push must clear the micro round trip plus the vault's 80%-power detectable
  effect, about **6.5 bp** on a daily 60-minute trade.

| shock | mean push, Y 1 / 0.5 | short-gamma days, Y 1 | days ≥ D661's 8.2 bp sd bar, Y 1 / 0.5 | verdict |
|---|---|---:|---|---|
| **gap** | **7.1 / 3.6 bp** | 10.1 bp | 27% / 8% | clears only at the best case |
| **stop run** | 4.4 / 2.2 bp | 5.9 bp | 17% / 5% | fails even at the best case |

**Both shocks are carried anyway, on the principal's instruction.** Under D661's method the stop run would stop here;
it is tested as the secondary. **The gap product's paper size can already be checked against H-O6.** A 7 bp mean push
on a 35–45 bp hour is a correlation of about 0.2. Over some 2,000 ES sessions that is a t of order 10, and H-O6's t
was 0.00. So the best case is contradicted on the first hour,
and this design asks whether anything survives at the break.

## 3. Data and seal

- **Sessions:** the ES usable sessions (D644 Gate O0), **2016-01-04 → 2025-02-28**, through the runners' sealed
  loader (`run_opening_v2.load_inputs`: `filter_before` and `assert_none_at_or_after` at 2025-03-01). Nothing in the
  vault (2025-03-01 → 2026-09-18) is read, and neither is D626's energy sample (not an ES root).
- **ES only.** NQ's option open interest is 2–5% of ES's, so its G is a thin book.
- **G:** A4's column in `data/opening/agents.csv` (`build_opening_agents.dealer_gamma`). It uses open interest at the
  prior close, Black-76 gamma at the prior settlement, and options alive after 09:30, so it is **known before 09:30**.
  The sign is the naive convention: dealers long calls, short puts.
- **G$ = G × $50 × F² × 0.01**, with F the prior day-session close: dollars of hedge per 1% move.
- **Already read on this window:** D645 (the first hour, all days), D652, D660, D661's size oracle (B3 by ex-post
  expansion) and D581 (the close). The break follow-through split by gamma has not been read.

## 4. Variables, per session

**The break (D645's B3, `run_opening_stages.b3_trade`):**
- the opening range is the 09:30–09:59 bars' high and low;
- D = +1 or −1 at the first bar starting 10:00–11:29 whose close lies beyond the range;
- entry is B3's own entry: the close of the bar starting one minute after the signal bar.
- Sessions without a break are not in the sample.

**Outcome F** (primary; no stop, so a stop cannot truncate an amplified move):
- F = D × ln(P₆₀ / P_entry) × 10⁴, with P₆₀ the close of the bar starting 60 minutes after the entry bar;
- if that bar is missing, the last close at or before it;
- **secondary:** B3's own gross, with its half-range stop.

**Gamma:** g = −G$ / V₂₀ × 100, dealer SHORT gamma as a percentage of the prior 20 sessions' mean day-session dollar
volume, per 1% move. g > 0 means short gamma.

**Shocks,** each signed by D so that positive means the shock ran in the break's direction:
- **s_gap** = D × (open / prior close − 1) × 100 (%);
- **s_stop** = D × (u − w), where u = max(0, range high / prior high − 1) × 100 and w = max(0, 1 − range low / prior
  low) × 100: how far the opening range ran the stops beyond the prior day's high and low.

**The predicted push** (for §5.3), with Q_k = |G$| × |shock_k| (%):
- I_k = sign(g × s_k) × σ_d √(Q_k / V₂₀), at Y = 1;
- σ_d is the prior 20 sessions' day-session close-to-close sd.

## 5. Statistics

1. **Primary, the interaction.** For each shock k, an OLS over the break sessions (sorted by session):
   F = a + b₁ g + b₂ s_k + **b₃ (g × s_k)** + e, with HAC standard errors (Newey–West, lag 5).
   The mechanism predicts b₃ > 0: a shock in the break's direction carries further when dealers are short gamma.
2. **Controls:**
   - each term alone: F on g, and F on s_k;
   - piecewise: the slope of F on s_k among short-gamma sessions (g > 0) against long-gamma sessions (g ≤ 0). The
     mechanism predicts it is steeper when short.
3. **The model's own size claim:** F = α + β I_k + e.
   - β = 1 means the square-root law's push is realised.
   - If β's 90% CI lies wholly below 0.5, the product is labelled **a powered null against its own claim** (D640's
     A7 label).
4. **Null:** an enumerated circular rotation of the per-session g series against the break sessions.
   - Every offset of T − 1 is used, **purged of offsets within ±10 sessions**, because gamma regimes last about a week
     (D581: autocorrelation 0.64).
   - Only the rank of b₃ is reported. It is exact, so there is no sampling SE.
5. **Placebo (D640's kill rule):**
   - the same rule at midday: range 12:00–12:29, breaks 12:30–13:59, F over 60 minutes;
   - the same g and s_k (prior-close gamma, the gap, the morning's stop run);
   - the lagged hedge should be done by midday.
6. **Tails and eras:** all read, none gating.
   - b₃ without 2020-02-01 → 2020-04-30;
   - without the top 1% of |F|;
   - leave-one-year-out;
   - by year;
   - before and after the 0DTE break (2022-05-16);
   - F's mean, median, trimmed means and ex-top/ex-bottom 1%.
7. **Power:** the MDE of b₃ at 80% (HAC SE × 2.80). The b₃ implied by the paper's best case is also given, so a null
   can be read as powered or not.

## 6. Verdict (per shock; Holm over the two, one-sided)

**SUPPORTED** needs all of:
- b₃ > 0 with Holm p < 0.05;
- b₃'s rank ≥ 0.95 in the purged rotation null;
- the midday placebo's b₃ with |t| < 2;
- the short-gamma slope steeper than the long.

Otherwise the verdict is **NOT SUPPORTED**, and it is stated whether the null is powered (§5.3 and §5.7).

## 7. Routing

- **Gap SUPPORTED:**
  - a pre-registration of a trade follows: the break traded only when the product predicts follow-through, with the
    principal's expected-profit filter (k = 2 × cost) and the four reporting groups;
  - its confirmation is the vault (the joint run, on the principal's word), after a power computation.
- **Stop run SUPPORTED alone:** the same routing. Its paper size already fails the confirmable bar (§2), so a pass
  here is read as a direction to size, not a trade.
- **Neither:** the shock × gamma product is closed at the opening range on the ES carried book. That is the fourth
  null for the gamma mechanism here: D581 at the close, H-O6 and S-H at the open, and this one. The opening line's
  closure (D658 H-O2, D652 without its vault look) is then recommended with it. The one untested measurement left is
  SPX/0DTE gamma (paid OPRA data). It is named, and not pursued without the principal's word and a quote.

## 8. The runner's assertions, each proved to fire in `--selftest` on a broken input

1. **Lag:** g, s_k and I_k are rebuilt by a second implementation from the raw bars and `agents.csv`, never calling
   the runner's feature functions. It must agree on every session.
   - Every input to g and s_k must be dated before the entry bar. Gamma comes from the prior close; the shocks from
     bars ending by 09:59.
   - A canary that reads the entry bar's own close must raise.
2. **Sign, in money:** an up-break followed by a rise gives F > 0, and a down-break followed by a fall gives F > 0.
   A flipped D must raise.
3. **Right quantity:**
   - F differs from the same return measured from 10:00 instead of the entry;
   - b₃ differs from the coefficient on the unsigned product (g × |s|).
4. **Reproduces B3:**
   - the break sessions and D equal `b3_trade`'s on every session;
   - F at 60 minutes with the stop equals B3's gross on every session where the stop did not fire.
5. **Null exactness:**
   - the rotation's b₃ at offset 0 equals the primary OLS's b₃ exactly;
   - the vectorised batch of OLS fits equals a loop over offsets on a tie-heavy probe.

**Speed, by design** (CLAUDE.md, 2026-09-28): the rotation null solves every offset's 4 × 4 normal equations in one
batched call, not a Python loop. It is proved equal to the loop in the selftest. The two shocks and the placebo run as
independent processes.

## 9. Predictions, written before the run

1. **Gap × gamma: NOT SUPPORTED.** A4's first-hour null (H-O6 t 0.00) covers most of what the break sees.
2. **Stop run × gamma: NOT SUPPORTED.** It is below the bar on paper.
3. **The gap product's β against its own claim** lies below 0.5 with its CI wholly below 0.5: a powered null.
4. **The short-gamma and long-gamma slopes do not differ** (|t| < 2).
5. **The midday placebo's b₃ is inside noise** (|t| < 2).
6. **Whatever b₃ there is sits in the tails:** removing February–April 2020 moves it by more than half.

## 10. Outputs

- `scripts/stage0_d662_gamma_product.py` (`--selftest`, `--dry-run` on synthetic bars, `--run` once);
- `data/stage0_d662_gamma_product.json`;
- a RESULT record.

No trials row is written, because Stage 0 is not a trial. The programme's trial counter is untouched.
