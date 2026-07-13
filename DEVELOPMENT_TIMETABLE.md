# Development Timetable

## Assumptions (the honest kind)

- **Budget: ~7 h/week.** Weekday mornings ~45 min × 5 = 3.75 h, plus one 3 h weekend block. If the morning habit doesn't hold, every date below slips 1:1 — the habit is the critical path, not the code.
- **Estimates include a 25% illness/life buffer.** Weeks like this one (sick, 2 h sleep) are the rule, not the exception. A slipped week is absorbed, not "caught up" — catching up is how streaks die.
- **A step is done when its VERIFICATION_SCHEME gate passes** (see that doc), not when code exists.
- **Scope cut already applied:** Step 10 (crypto + FX instruments) is deferred past the portfolio deadline. It's a strong framework feature but zero portfolio-narrative value vs. the pairs research. FX *plumbing* needed for base-currency NAV rides along in Step 7/9 minimally.

## Week 0 — now

No code. Recover from being ill; install the wind-down + morning routine and hold it for 7 consecutive days. Optional light task if a morning feels good: read Chan ch. 1–3. **Gate: 5 of 7 mornings happened.** If this gate fails twice, the problem is the routine design, not discipline — redesign it before touching the timetable.

## Phase A — Foundations (weeks 1–2, ~12 h)

- Step 1: TrialRegistry + stop-gap fix (D10) + calendar accrual fix (D33)
- Step 2: declarative config + factories (D35)
- Reading: Chan *Quantitative Trading* alongside.
- **Milestone: reproducibility loop closes** — a trial can be logged, reloaded, and re-run identically.

## Phase B — The whale (weeks 3–6, ~26 h, hard timebox per R2)

- Step 3: CostStack + Instrument + signal→target→order refactor
- Step 4: DataView guard, RiskMonitor, allocator stand-in
- **Slip rule:** if the refactor regression gate (Step 3's golden reproduction) isn't passing by end of week 5, split D27 (pipeline) out and land it in Phase D. Do not extend the whale.
- Reading: Carver *Systematic Trading* (directly informs D27).

## Phase C — First contact with reality (weeks 7–8, ~12 h)

- Step 5: IBKR commission, margin interest, sqrt impact bricks
- Step 6: cost-multiplier sweep → **run XLE/XOP walk-forward end-to-end**
- **Milestone (~week 8): THE FIRST REAL NUMBER.** Ugly is fine. This is the project's existence gate (R1). Log it, frame it, move on.

## Phase D — Trust hardening (weeks 9–11, ~19 h)

- Step 7: data snapshots, cleaner contract, sanity gate, raw prices + dividend flows
- Step 8: golden master, property invariants, cross-engine reconciliation
- **Milestone: the simulator is anchored to references you didn't write.**

## Phase E — Honest reporting (weeks 12–13, ~10 h)

- Step 9: sample-size gating, beta + rf benchmark, seeds, momentum labelling
- Step 11: options stub + docs/options_extension.md (cheap, high signalling value)

## Phase F — Validation science (weeks 14–17, ~22 h)

- Step 12: pair selection inside walk-forward + multiplicity, regime fitting rule, DSR (reproduce the paper's worked example), synthetic nulls
- Reading: López de Prado relevant chapters + Bailey/de Prado DSR paper; Gatev paper re-read.
- **Milestone: the framework can now say "no edge" and be believed.**

## Phase G — Research & portfolio (weeks 18–24, ~40 h)

This is the actual portfolio. The framework is frozen except for bug fixes.
- The study: Gatev distance → cointegration → Kalman (Anderson & Moore interleaved), pair selection in-window over a broad ETF universe, full cost sweep, DSR-adjusted results.
- Writeup: methodology, results (including negative ones), the "doesn't clear costs at retail scale, clears at £X AUM" analysis, scoping docs as appendices.
- **Parallel from week 18: reviewer access.** Finding senior quants to review it has lead time — QuantNet/Wilmott forums, LinkedIn, Manchester/Dublin meetups, cold emails with the writeup attached. This is a networking task and it starts before the writeup is polished.

## Summary line

Framework: weeks 1–17 (~100 h). Research + writeup: weeks 18–24. Portfolio lands ~month 6 — exactly on the original deadline, with zero slack beyond the built-in 25%. Anything added to framework scope now comes directly out of the research phase, i.e. out of the part reviewers actually judge.

## Kill criteria (pre-committed, so future-you can't negotiate)

- First real number (Phase C gate) not produced by **week 10** → cut Phase D to snapshots-only, drop cross-engine test to post-portfolio.
- Entering **week 20** without a started writeup → freeze all code permanently, write up whatever exists. An honest writeup of a modest study beats an unfinished ambitious one.
