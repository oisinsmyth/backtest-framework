# Review: State-Based Allocation (RL vs regime models)

*2026-10-01. A review of the principal's deposit
[`User-Doc-Deposit/STATE_BASED_ALLOCATION.md`](User-Doc-Deposit/STATE_BASED_ALLOCATION.md), saved unchanged. It is
read against what this repository has measured. Nothing here was run; this is a reading, and it binds nothing. The
principal: "Looking ahead a wee bit, I would like you to save this doc and analyse it for effectiveness and use".*

## 1. The verdict

**The document is sound, and most of it is already this repository's practice.**
- No RL.
- The inner loop before the outer loop.
- Filtered (not smoothed) HMM probabilities, two or three states, and a dumb baseline the HMM must beat.
- A small, calibrated probability model.
- **"Meta-labelling" is the formal name for what the principal already requires of every strategy:** an
  expected-profit filter, designed with the principal and held to its oracle.

**Three things in it need adjusting for this book,** and one of them changes what the allocator is for:
1. **The allocator's binding constraint is not a slot.** The three live NQ components can all hold at once; what binds
   is the drawdown barrier (§3).
2. **Its prior "exit modulation is the likeliest win" runs against the measured record here** (§4.1).
3. **State here has predicted SIZE, almost never WIN PROBABILITY** (§4.2). So the realistic use of a state model is
   risk and abstention, not edge.

## 2. What it gets right, with this repository's evidence

| the document says | this repository's evidence |
|---|---|
| RL's effective sample is the collision count, which is tiny | Agreed, and the book is smaller than it assumes: three NQ components, about 50 / 65 / 210 trades a year. An RL policy over that is a fit to one history |
| the "simulator" is a bootstrap of our own trades, so RL overfits | The same lesson as layers selected on spent names vanishing out of sample, and as a degenerate cell beating the rotation null |
| use filtered probabilities P(state_t \| data to t) only | Every runner here carries a lag audit with a canary for exactly this. A smoothed HMM would fail it |
| check that the state labels mean the same thing across refits | Agreed. Unchecked, label switching is a silent lookahead |
| test the HMM against realised-volatility percentile + trend strength | **Strongly supported.** D691: implied vol predicts size only relative to realised vol. D720: a day-size forecast is a vol forecast. D722: no variable explains 2022. The dumb baseline is likely to capture most of what an HMM finds |
| a small model, calibrated (reliability curve) | Agreed. On 50–210 trades a year, a handful of features is the ceiling |
| an integer contract makes the probability a take/skip gate plus a priority | Agreed. At one micro this is the only form. "Micro size is the only size" makes size scaling moot |
| the inner loop first; if (1) fails, the allocator has nothing to arbitrate | Agreed. It is the cascade rule, and the cheapest kill |
| count collisions before anything | Agreed, and done roughly below. It changes the question |

## 3. The collision count: the constraint is not a slot

**The live and queued components** (in-sample clocks):

| component | status | clock | trades a year (in-sample) |
|---|---|---|---:|
| NQ F2 (D716, slot 7) | frozen, PROVISIONAL #5 | 15:30 → 16:00 | about 48 |
| NQ compression break, C1 (D680, slot 9) | frozen | a break after 09:30 → trail or the close | about 65 |
| NQ leads the Dow (D737, slot 1) | frozen, PROVISIONAL #6 | about 10:00 → the close (96% enter in the 10:00 hour) | about 210 |

**What follows from this:**
- **All three trade the same contract in the same day session.** D737 is open on about 88% of sessions, so nearly
  every F2 trade and most C1 trades overlap a D737 position.
  - On the document's definition, collisions are therefore not rare: they are the normal state.
- **But nothing forces a choice between them.**
  - One account nets same-contract orders. Long one MNQ plus short one MNQ is flat, and the P&L of the net position
    is the sum of the components' P&Ls.
  - Netting only saves commission. No signal is lost.
  - `data/prop_venues.json` records no contract caps, and three MNQs are far below any 50k plan's micro limit.
    **That still needs verifying per venue.**
- **What binds is the drawdown barrier:** a $2,000 trailing (end-of-day) barrier on every 50k plan in
  `prop_venues.json`.
  - D737 alone drew down $2,690 in-sample at one MNQ.
  - D732's in-sample book drew down $4,920 before the MACD arm was retired.
- **So "allocation" here is risk budgeting under a barrier:** which components to run, and on which days, so the
  combined path does not touch $2,000. That is hurdle P's P3b (life cost) and P(pass) question, already in
  `hurdle_p.py`. It is not arbitration between signals competing for a slot.

**What this means for the document:** its sanity check comes out the opposite way from the case it anticipates.
Collisions are frequent, but they do not bind. **The allocator's job is the drawdown, and the state model's value
lies in (a) the component-level gate and (b) the barrier.**

## 4. Where it needs adjusting for this book

### 4.1 Exit modulation is the least likely win here, not the likeliest

The record:
- **D630:** exits cannot rescue a thin micro edge.
- **D733:** 1R, 2R, retest and 60-minute exits were all worse than holding; the stop was neutral.
- **D735:** a 60-minute exit kept about a third of the net; a 0.5σ stop was neutral; holding to the close was best.
- The memory note on matching the statistic to the object (entry against exit) says the same.

**On NQ the drift needs the whole day.** A state-modulated exit is the lowest-prior step, not the first.

### 4.2 State has predicted size, not win probability

| what was tried as a state or conditioner | result |
|---|---|
| dealer gamma (D665; direction uses D688–D713) | size t 8–12; every direction use failed at MES |
| day-size forecast (D691, D720) | knows the range (Spearman 0.51), not the trade's sign; sizing by it lowered both lines |
| aggressor flow (D695, D704, D715, D717) | nothing, or inverted, as a direction gate |
| volume profile (D730, D731) | finds big days, not continuing ones |
| cross-asset agreement (D728) | wrong way round: disagreement continues more, and became D735 |
| "2022 regime" (D722) | no pre-trade variable explains it |

**Implication:** a meta-label P(win | state) has a low prior on these components. What a state model can
realistically deliver is σ, i.e. size and risk. That makes it a tool for:
- the barrier (§3), by abstaining when forecast risk would threaten the trailing drawdown;
- the principal's own rule that abstaining beats trading without profit, through an expected-profit gate.

It is not a tool for sharpening edge.

### 4.3 A dollar threshold is a volatility gate

The document's "P × payoff − cost clears a threshold" is in dollars. **A dollar bar on a vol-scaled payoff selects
high-volatility days** (a $ bar turns a relative-size signal into a vol-regime gate; D713). Two consequences:
- **Its null must be the size-robust one:** Σg/Σ|g| efficiency, not mean P&L, because an input-rotation null is
  anti-conservative for a size-selecting filter (D711-A1).
- **Its oracle must come first:** what the gate earns if the state were known perfectly, so that a gate with no room
  is never fitted.

### 4.4 The data: the confirmation slices are spent

- **NQ's 2024 → 2026-09-18 is committed** to D716 (slot 7) and D737 (slot 1). D680 holds the opening's vault slice.
- **A state model fitted after the joint run is fitted on 2016–2023 again,** a sample every component was chosen on.
- **Its only clean confirmation is forward data:** sessions after 2026-09-18, live paper or a later Databento pull.
  That is a cost and a calendar decision, and it belongs in the plan before any fitting starts.

## 5. How to use it: the sequence for this repository

All of this comes **after the joint run.** It is only worth starting if at least two of D716, D680 and D737 confirm.
If one or none does, there is nothing to allocate between.

0. **The binding-constraint check** (cheap, in-sample, no model):
   - rebuild the three components' daily P&L on one calendar;
   - count same-day and same-minute overlaps;
   - run hurdle P on the assembled one-MNQ book (P2, P3a, P3b on the $50k terms);
   - verify each venue's contract limit.
   - **If P3b is fine at one MNQ each, there is no allocation problem to solve.**
1. **Component gates, oracle first, with the principal** (the existing filter rule):
   - **the oracle:** the best abstention rule if the state were known, scored on Σg/Σ|g| and on P3b;
   - **the dumb baseline:** a realised-volatility percentile plus a trend-strength measure (§2), in walk-forward;
   - **the HMM:** 2–3 states, filtered probabilities, refit stability checked. Only if it beats the baseline
     out of fold;
   - **the target:** expected net per trade or day-risk, not P(win), because of §4.2.
2. **The book's risk rule.** Only if (0) shows the barrier binds and (1) produced calibrated per-component forecasts:
   - rank or skip by expected net per unit of forecast day-risk against the remaining barrier;
   - test it against the fixed pre-registered rule ("run all three, one MNQ each") on P(pass) and P3b in walk-forward
     Monte Carlo (`hurdle_p`);
   - **if the gain is inside noise, keep the fixed rule.**
3. **Confirmation on forward sessions only** (§4.4), pre-registered like any vault line.

**What to drop from the document's plan:**
- exit modulation as step 1;
- P(win) as the label;
- the slot-arbitration framing of the allocator.

**What to keep:** everything else.
