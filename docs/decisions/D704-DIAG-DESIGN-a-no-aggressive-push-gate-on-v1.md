# D704 DIAG DESIGN — a volume gate on V1: did the price rise without a matching aggressive-buy imbalance? Ranked against V1's oracle before any threshold

*2026-09-30. Committed before the runner exists. The runner will be `scripts/diag_d704_no_push_gate_on_v1.py`,
committed separately before its one run.*
- **What it is:** a diagnostic of a filter on D699's V1, on its in-sample window (2016-01-05 → 2023-12-29,
  short-gamma days). Nothing dated 2024-01-01 or later is read.
- **What it is not:** it fits no threshold and admits nothing. A threshold follows only if the ranking carries
  information, as its own design.

## Why

The principal wants better signals: "in my head the signal need to be a conformation of sorts", then "the MACD
again plus some sort of volume type gate".

The mechanism's false positives were reviewed first. The one that has cost most is **the burst**: a move made by
aggressive one-off orders, which overshoots and fades before any hedging arrives.
- D697: fast rises lose −$3.46 in the next 15 minutes.
- D695: aggressively bought hours continue *less*. The Spearman of the last hour's (buy − sell) / volume against the
  outcome was −0.031 on D692's hourly grid.

Dealer re-hedging is hypothesised to be worked patiently, sliced rather than pushed through the book, so a hedging
move should rise without a matching aggressive-buy imbalance.

**The principal's choices (2026-09-30):**
- **Gate:** "B: no aggressive push".
- **Window:** "Last hour".
- **Scoring:** "Continuous ranking first".

## The objects

- **V1:** D699's 572 trades, through D699's functions unchanged. The guard: a mean net of +$10.47477440436403,
  exactly.
- **The flow:** the Sierra fixture `fut_ES_signed_1m`, per minute: volume, and buy and sell aggressor volume.
  - D695 validated it. The runner reads its validation flag and VOIDS the study if the flag is false.
  - It covers 2016-01-04 → 2023-12-29.
- **The window:** the 60 minutes labelled jd − 60 … jd − 1, where jd is V1's deciding close. This is D695's
  convention: the last hour's bars, ending at the close that decides.
  - **Early entries:** a third of V1's entries decide at 09:45, 10:00 or 10:15, when the last hour would reach into
    the overnight session. The flow fixture and D699's splice both exclude it.
  - **The rule for them:** the window is TRUNCATED to the session, from 09:30 to jd − 1, with length L = min(60, jd)
    minutes. The move is measured from the session's open.

## The score (higher = more confirmation, declared)

- **The imbalance share:** I = (buy − sell) / volume over the window.
- **The standardised move:** z = log(P_jd / P_jd−L) / (σ̂₆₀ √(L/60)).
  - σ̂₆₀ is the sd of the within-session 60-minute log moves over the 20 sessions before d, prior-only.
  - The 60-minute moves are measured at the 15-minute closes 10:30 … 16:00.
- **The expected imbalance for a move:** Î(z) = a + b·z. It is fitted by OLS over EVERY window of the in-sample:
  - the 15-minute closes 09:45 … 15:45 on every day, both gamma classes, with the same truncation rule;
  - no outcome is used;
  - it is the market's normal ratio of aggressive flow to price move.
- **PRIMARY:** S_B = −(I − Î(z)). A trade scores high when its last hour rose with LESS aggressive buying than a
  typical hour with that move.
- **SECONDARY (D695's A1, sign reversed):** S_A1 = −I. It is reported because it is the measure D695 already read,
  on a different set of trades.

## Declared measurements

1. **The oracle first:** V1's oracle as D699 §1 published it (50.5% winners, +$110.07 their mean net). It is shown
   again, not recomputed differently.
2. **The accuracy assessment** (`filter_oracle`), for S_B and S_A1 against V1's net:
   - the Spearman of the score against net and against the drift excess (D699's control);
   - the AUC against the oracle label (net > 0);
   - the realised mean net by score quintile, and the calibration slope of net on the score's rank. The slope's sign
     is the question: a positive slope means a higher score, more profit.
   - **Capture**, for the illustrative take "the upper half by score": its net against the oracle's and against
     taking everything.
3. **The null:** the enumerated rotation of the score across V1's trades in date order (k = 10 … n − 10, SE 0), for the
   Spearman against net. Reported with p05, p50, p95 and the percentile.
4. **The mechanism check (reported, not a gate):** the same S_B Spearman on V1's trades on LONG-gamma days, where the
   hedging story says the gate should carry less.
5. **The known false positives, against S_B:**
   - its Spearman with the window's |z| (does it just pick small moves?);
   - with the entry hour;
   - its Spearman against net by year, including without 2022.
6. **The upper half's book, descriptive:** trades, mean net, net Sharpe and Sortino (daily, as D699), and the edge per
   unit of noise (mean drift excess / its sd), against V1's own.

## Declared reading

- **INFORMATIVE:** S_B's Spearman against net is above the rotation null's p95, and the quintile calibration slope is
  positive.
- **WORTH A THRESHOLD DESIGN:** INFORMATIVE, and the upper half's edge per unit of noise is at least 1.7 × V1's. That
  is the lift a half-sized book needs to take V1's drift-excess t from 1.64 to 2.
- **NO INFORMATION:** anything else.

**The detection limit:** on 572 trades a Spearman's SE is about 0.042. A real gate below about 0.08 cannot be told
from nothing here, and that is said with the number.

No score, window or cut is tuned after the run.
