# D681 — DIAG of D666: the retest selects the failed breaks, which is why the re-break loses; the thread is NQ's plain break with a trailing stop (+4.29 bp gross, HAC t 3.57, 8 of 10 years), found post hoc and unpromotable as it stands

*Renumbered from D667 on 2026-09-29, at this branch's merge into main: main holds D667 (the margin-hike pause on the MACD arm). Commits before the merge, recorded run outputs and the frozen D680 cite the old number.*

*2026-09-29.*
- *The principal: "B, I would like a diagnostic on this, a statistical analysis of the results, trades by year etc..
  I would like you to find a thread we can pull on", then "Is it the gap that make the retest not work?"*
- *Two scripts, both in-sample only (2016-01-04 → 2025-02-28) through D666's own sealed functions, and both reproduce
  D666's committed means exactly before reporting anything:*
  - *`scripts/diag_d666.py` → `data/diag_d666.json` (`f93a23cb`);*
  - *`scripts/diag_d666_gap.py` → `data/diag_d666_gap.json` (`f84a6c92`).*
- *Statistics only, licence-guarded. **Dealer gamma (GEX): SqueezeMetrics.***
- *No verdict changes. D666 stays NOT SUPPORTED on both roots.*

## 1. Mechanics: why the retest hurts

**Fills (A2):**

| construction | trades | gap through the stop at the fill | fill beyond the stop | median entry | median wait after the touch |
|---|---:|---:|---:|---|---:|
| ES plain | 1,432 | 29.6% | 12.1 bp | 09:50 | — |
| NQ plain | 1,435 | 28.6% | 13.7 bp | 09:46 | — |
| ES re-break | 652 | 0.2% | 0.8 bp | 10:56 | 24 min |
| NQ re-break | 700 | 0.0% | 0.3 bp | 10:33 | 24 min |

- About 29% of plain breaks fill at the 09:30 open, which gapped through the stop. The model fills them at that bar's
  open plus a tick. **The open is where real slippage is worst, and the plain break's net margin (below) is smaller
  than one extra tick.**
- The re-break is an hour later and almost never gaps.

**Excursions (A3), the mean favourable minus adverse move after entry, bp:**

| | to 60 min | to the close |
|---|---:|---:|
| ES plain | −2.95 | −4.05 |
| NQ plain | −1.45 | −3.78 |
| ES re-break | −5.05 | −6.31 |
| NQ re-break | −1.92 | −5.62 |

Adverse beats favourable everywhere, and more so after a retest. The trailing stop earns anyway by cutting losers
early: NQ plain E4's 1,241 stop exits average −4.0 bp, and the 194 trades held to the close average +57.5.

## 2. Is it the gap? No: it is the retest itself (`diag_d666_gap.py`)

Each session was classed by its 09:30 open against yesterday's level L, on the side of the day's first break:
- **no gap** (opened inside the range): 44–46% of breaks;
- **gap inside** (beyond L, inside the stop): 25–27%;
- **gap through** (beyond the stop, fills at the open): 29–30%.

**The plain break by open class, E4 gross per trade (share of the P&L):**

| | ES | NQ |
|---|---|---|
| no gap | +0.94 (t 0.68) | **+4.86 (t 2.82), 52%** |
| gap inside | −2.05 (t −1.12) | +4.93 (t 1.90), 29% |
| gap through | **+4.55 (t 2.15)** | +2.80 (t 0.96), 19% |

- **NQ's plain break does not live on the gap.** The first report to the principal said it was "largely gap
  continuation". That was wrong, and is corrected here. ES's small +1.20 does sit in its gap-through opens.

**The re-break by open class, E4:** after a gap-through open the re-break is the worst (ES −4.64, t −2.17; NQ E2
−14.0, t −2.14). The gap failed, price filled back to L, and the re-break followed the failure. But these are 11% of
re-breaks. Without them, NQ E4's re-break is +2.43 (t 1.14), still below the plain break.

**The retest is the selection.**
- 40–55% of breaks come back to L after the entry, in every open class (gap-through 40–42%, gap-inside 55%).
- Those are the plain break's losing days: E4 −16.6 bp (ES) and −18.9 (NQ).
- The breaks that never come back earn +17.5 (ES) and +25.2 (NQ). A re-break cannot take them, because it needs the
  pullback.
- **Paired, on the sessions with both trades on one side** (ES 639, NQ 683), the re-break beats the plain break: E4
  +3.44 (t 3.98) and +3.67 (t 4.27). It avoids the first, failed break.
- But on those days a second break is roughly a coin flip (NQ E4 +1.17 bp), so beating a losing trade is not enough.
- **Caveat:** the came-back/did-not split reads the future. For E2 it simply is the stop. It is a decomposition that
  explains the loss, not a signal.

**Economics this implies for the plain break:** with E4, expected gross ≈ 44 × P(hold) − 19 bp, where P(hold) is the
chance that the break does not come back to L. The unconditional P(hold) is about 0.53 (NQ).

## 3. Statistics: by year (E4 gross, bp; net at 1 micro in brackets)

| year | ES plain | NQ plain | ES re-break | NQ re-break |
|---|---:|---:|---:|---:|
| 2016 | +0.32 (−5.2) | +5.83 (+0.8) | −0.62 | +3.64 |
| 2017 | −0.37 (−5.0) | +1.94 (−2.1) | −1.37 | +1.10 |
| 2018 | +0.92 (−3.2) | +5.27 (+2.0) | +0.47 | +11.90 |
| 2019 | +1.92 (−2.0) | +4.67 (+1.7) | −0.73 | −0.83 |
| 2020 | −3.39 (−6.9) | −3.65 (−5.9) | −13.93 | −10.38 |
| 2021 | +6.77 (+4.1) | +7.41 (+5.8) | +4.42 | +0.37 |
| 2022 | +4.61 (+1.8) | +7.37 (+5.6) | +4.85 | +2.62 |
| 2023 | +1.87 (−0.8) | +1.44 (−0.2) | −1.75 | −0.23 |
| 2024 | −0.19 (−2.3) | +10.15 (+8.9) | −0.81 | +3.02 |
| 2025 (to Feb) | −7.54 (−9.4) | −5.11 (−6.2) | −7.29 | −4.75 |

**The plain break's own numbers:**

| cell | n | gross (HAC t) | median | win | net | years positive (gross) |
|---|---:|---|---:|---:|---:|---|
| ES E1 / E2 / E3 / E4 | 1,432 | −0.63 / −0.51 / −0.44 / +1.20 (1.31) | −6.9 (E4) | 40% | −2.31 (E4) | 6 / 6 / 4 / 6 of 10 |
| **NQ E1 / E2 / E3 / E4** | 1,435 | +3.46 (2.02) / +3.55 (2.03) / −0.48 / **+4.29 (3.57)** | −7.1 (E4) | 42% | **+1.69 (E4)** | 8 / 8 / 5 / **8** of 10 |

- NQ E4's net is positive in 6 of 10 years. It loses in 2020 (−5.9) and in the part of 2025 before the vault
  (−6.2).
- Its mean sits far above its median (+4.29 against −7.09): the right tail pays, as a trailing stop should.
- **The component line is not computed here.** CLAUDE.md forbids a component number from outside a runner. Any
  successor's runner computes it, with ρ against the ledger.

## 4. Splits, and the thread scan with its multiplicity

**NQ plain E4 gross (n; t):**
- side: long +5.71 (818; 3.94), short +2.40 (617; 1.31);
- era: before 2022-05-16 +3.72 (993; 2.84), after +5.56 (442; 2.18) — **it holds in the 0DTE era**;
- gap aligned with the trade +5.31 (1,015; 3.43), against +1.82 (420; 0.88);
- short gamma +6.37 (554; 2.82), long gamma +2.98 (881; 2.04);
- TICK aligned +6.21 (441; 2.63), not +3.44 (994; 2.37);
- A7 aligned +2.78 (535; 1.44), **not aligned +5.18** (900; 3.10): large-lot flow points the wrong way;
- aligned-confluence count 0 / 1 / 2 / 3: +3.41 / +3.20 / +6.85 / +4.47 — no dose-response;
- the fade veto removes 48 trades (+2.65), leaving +4.35.

**ES plain E4:** long +2.95 (t 2.68), short −0.97. Its other splits are inside noise.

**None of NQ's with-versus-without differences is individually significant:** gap ≈ t 1.4, gamma ≈ 1.3, side ≈ 1.4.

**The scan (D):** 472 subsets (both constructions, both roots, 11 dimensions, 4 exits, n ≥ 60).
- By chance, about 21.5 of them would be expected past |t| 2.
- 23 were past +2 and 17 past −2: **the subset scan as a whole is indistinguishable from chance.**
- The thread therefore is not chosen as the scan's top subset. It is **the whole NQ plain-break construction with the
  trailing stop**, which was D666's pre-registered control and needs no subsetting.

## 5. The oracle (C)

The favourable excursion available after entry, to the close:
- plain: ES 48.6 bp, NQ 64.5;
- re-break: ES 46.5, NQ 62.1.

That is 13–25 times the cost, so the room exists. **Capture is the problem, not the size of the move:** adverse beats
favourable on average (§1).

## 6. The thread, with its caveats

**NQ's plain break (a stop at yesterday's high or low ± 0.25 ATR, live from 09:30, first fill of the day) with the
0.25-ATR trailing stop:**
- +4.29 bp gross, HAC t 3.57, 8 of 10 years positive;
- +1.69 bp net at 1 micro;
- holds before and after 0DTE.

**The caveats:**
1. **Post hoc.** It was a control, read after the hypothesis failed, and the exit was one of four. Nothing here can
   promote it. It needs its own pre-registration, and a confirmation sample it was not found on.
2. **The net margin is below one extra tick** (1.2–2.5 bp a round trip on MNQ over the sample). 29% of its fills are
   at the open, where the one-tick slippage model is most optimistic.
3. **The drift is not controlled.** The long side is where most of it lives, and D666 never compared the break with
   the same-side, same-clock trade on any session. A random-entry control drawn on every session is needed.
4. **The confluences have shown no incremental value.**
   - Each with-versus-without difference is at t ≈ 1.3–1.4.
   - A7 points the wrong way.
   - The count has no dose-response.
   - A filter built on them would add variance before it adds edge.
5. **Power:** the vault's NQ sample (about 245 trades) has roughly 30–37% power at +4.3 bp. Confirmation needs
   roots that have not seen this construction; YM and RTY are the candidates.

**Where the prize is (§2):** the plain break's gross is 44 × P(hold) − 19. A predictor that sorts the breaks which
will not return to yesterday's level lifts the selected trades by about 2 bp for every 5 points of hold rate. **That
is the successor question:** the plain break sets the direction, and an expected-profit predictor built from the
confluences decides whether to take the trade and how big. It is for the principal to commission.
