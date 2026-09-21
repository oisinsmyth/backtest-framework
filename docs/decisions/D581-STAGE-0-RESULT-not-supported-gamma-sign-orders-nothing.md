# D581 STAGE 0 RESULT — **NOT SUPPORTED.** The sign of carried dealer net gamma does not decide whether the last half-hour continues or reverts the hour before it: the interaction is **−0.023 (NW t −0.66), rank 0.32 in its enumerated day-shift null** (p05 −0.078, p95 +0.078) on 1,990 sessions; it is +0.0005 in 2016–2021 and −0.076 (rank 0.08) in 2022–2023, nothing in 2023 alone, and what little there is sits on the sessions **without** a same-day expiry. The close continues the prior hour in every regime (b +0.10, t 2.9), which is D463's market intraday momentum, not this mechanism. Terminal by the deposit's kill 2; the convention is neither confirmed nor refuted; nothing follows.

*2026-09-21. Design committed in `3d7db80` before the pulls, the fixture builder and the runner
(R8). **Data:** two zero-cost Databento batch pulls on the principal's word — `ES.OPT` (the
quarterly family alone, 47.7 GB billable) and the 24 weekly and daily families as their own
parents (336.2 GB billable), ~67 GB compressed under `data/raw/databento/GLBX-20260920-*`, job
records `data/es_options_pull_jobs*.json`. **Fixture** `fut_es_options_eod.csv.gz` by
`scripts/build_fut_es_options_eod.py`: 19,225,749 rows over 2,658 sessions 2016-01-04 →
2026-09-09, 25 families, six gates green (OI ≥ 0 and settlement > 0 on every row; every OI row
published before its session's 10:00 ET; a same-day expiry on 100 % of Fridays and 99 % of
sessions from 2022-05; median 348 strikes with OI a session; the family OI sums recomputed by a
second path equal on 10 of 10 seeded sessions; near-the-money settlement vol inverts on 100 % of
6,818 rows). **Runner** `scripts/stage0_d581_gamma_close.py`, artifact
`data/stage0_d581_gamma_close.json`, 372 s; every audit passed its clean case and raised on its
break inside the run (the Black-76 closed form and two implementations; the vol inversion's round
trip; the sign in money, c −0.30 on the synthetic panel and +0.30 negated; the OI keying on
12,594,319 rows; F1 by a scalar second path on four seeded sessions to 1e-9; F1 and F1b distinct;
the declared-outputs guard). **Read:** ES regular-hours minutes 2016-01-04 → 2023-12-29 (1,993
sessions), the options fixture and the option minute bars to 2023-12-29. **Not read:** any
session, option row or quote from 2024-01-01; the `tbbo` year; no cost, no book.*

---

## 1. Four data facts found on the way, before any statistic

1. **`ES.OPT` is the quarterly family alone.** The first pull, its build and its gates all ran
   before the definition decode said `{'ES': 54250}` with no weekly in it; the end-of-month,
   Friday, Monday, Tuesday, Wednesday and Thursday families are their own parents and were
   pulled second. The quote script now probes families before it quotes.
2. **Single-digit year codes recycle.** `ESZ6 C2200` is December 2016 and December 2026; one
   expiry per raw symbol across years was wrong for one of them. Every publication now takes the
   definition of its instrument id in force at the publication time (D520's windowed rule), with
   each (id, symbol)'s first and last definition times kept, because a definition record is
   republished every session.
3. **An expired option's final open interest is published on its last evening** and is usable
   the next session: 1.49 million contracts of expired ESM2 options sat in 2022-06-21 until the
   gate's second path applied the same expiry rule as the fixture.
4. **The quarterly expires at 09:30 ET** (AM settlement) and carries no gamma at 15:30 on its
   expiry day; every other family expires at 16:00.

## 2. The premise's persistence, read first

Carried net gamma was negative on 41 % of sessions (by year: 32, 21, 50, 38, 33, 29, **74**, 48 %
for 2016–2023). The regime's day-to-day autocorrelation is +0.64 with 343 switches over eight
years, 43 a year: regimes last about a week, so n_eff is in sessions, not years. The median
|F1| by year, in millions of dollars of dealer hedge per 1 % move: 3,544 · 4,371 · 4,389 · 3,486 ·
2,144 · 3,690 · 4,309 · **6,415**. **The same-day expiry's share of carried |gamma × OI| is 0 %
in 2016, 4–5 % in 2017–2019 and 7–8.5 % in 2020–2023** — the carried book sees a twelfth of the
0DTE gamma at most, exactly as the deposit's premise correction said it would. The median
session used 5,082 options; 31 near-the-money rows a session failed to invert.

## 3. The tests

| | c (interaction) | NW t | day-shift rank (bar ≤ 0.05) | n | slopes neg / pos |
|---|---:|---:|---:|---:|---|
| **T1, pooled** | **−0.0228** | −0.66 | **0.323** (p05 −0.078, p50 +0.001, p95 +0.078) | 1,990 | +0.126 / +0.080, ordered |
| F5-shift null | | | 0.17 | | |
| T3 2016–2021 | +0.0005 | +0.01 | 0.52 | 1,492 | |
| T3 2022–2023 | −0.076 | −1.49 | 0.08 | 498 | |
| T3 2023 alone (bar ≤ 0.10) | −0.003 | −0.05 | 0.46 | 248 | |
| T4 sessions with a same-day expiry | +0.004 | +0.07 | 0.52 | 1,271 | |
| T4 sessions without | −0.081 | −1.42 | 0.18 | 719 | |
| T5 far from the flip (|F3| above the median 1.08 ATR) | −0.100 | −2.10 | 0.054 | 959 | |
| T5 near the flip | −0.016 | −0.37 | 0.37 | 967 | |
| T6 the 0DTE volume build, F1b alone | −0.081 | −1.17 | | 1,263 | sign agreement with F1 0.65 |

The week-block bootstrap SE of c is 0.044. By year c (rank): 2016 +0.048 (0.72), 2017 −0.053
(0.27), **2018 −0.148 (0.10)**, 2019 +0.064 (0.75), 2020 +0.080 (0.73), 2021 +0.003 (0.50), **2022
−0.107 (0.06)**, 2023 −0.003 (0.46). **T2:** c by |F1| tercile +0.031, −0.066, −0.035; Spearman of
|F1| with the signed conformity +0.009. **The unconditional slope b is +0.103 at t 2.9:** the
15:30–16:00 return continues the 14:30–15:30 move in both regimes, and the regime moves that
slope by a fifth of its own standard error.

**Beside.** The 2 × 2 of mean R2 in bp (MES ticks at 0.77 bp): negative gamma, up hour **+2.3**
(+3.0 ticks, n 386); negative, down **−4.5** (−5.8, 412); positive, up +0.6 (+0.8, 659);
positive, down −1.0 (−1.2, 490). Continuation in all four cells, larger when gamma is negative
— and the ten largest |R2| sessions are all in February–March 2020, all in the negative regime
(2020-03-13 +458 bp on a +129 bp hour; 2020-03-17 +272 on −191; 2020-03-25 −263 on +2). The
signed conformity's mean is +0.93 bp, its 1 % trimmed mean +0.72, ex-top −0.57, ex-bottom +2.22:
what sign there is comes from the tails. R1 (to 15:50) c −0.025 (t −0.8), R3 (from 15:45) −0.019
(t −0.6). With D463's `rROD` in place of F5, b −0.019 and c +0.019.

## 4. Verdict, declared rule applied

T1's c is negative but inside its null at rank 0.32, against a bar of 0.05, and not above p95
either: **NOT SUPPORTED**, the deposit's kill 2 — the regime flag carries no information about
which of continuation and reversion the close shows. The dealer convention is neither confirmed
nor refuted (kill 3 does not fire; the sign is not wrong, it is absent). The declared era and
0DTE tests are moot but are read for the record: the 2022–2023 direction is right and inside its
null; 2023 alone is nothing; and the sessions carrying the little there is are the ones
**without** a same-day expiry, the opposite of the mechanism. The two subsets that reach t −2
(far from the flip level; 2018 and 2022 by year) are post-hoc cuts of a pooled null result and
are unpromotable — they are named so that nobody reads them as a finding later.

**What the data say.** The ES close continues its prior hour by about a tenth of the move, the
market-intraday-momentum effect D463 scored at a third of its published size, and it does so
whether carried dealer gamma is long or short. Carried open interest sees at most 8.5 % of the
same-day gamma even in 2023, so the regime it labels is the 1DTE-and-longer book, and that book's
sign does not touch the close. Whether the intraday 0DTE build would (the deposit's F1b proper,
which needs signed option flow) is not tested here; the unsigned volume build gives c −0.08 at
t −1.2 on 1,263 sessions and agrees with the carried sign on 65 % of them, which is a hint of the
same size as everything else here and is left as one.

**Spent:** nothing reserved. **Seen:** the ES last half-hour 2016–2023 by this line (it was
already seen by D463/D466). The reserved slice 2024-01 → 2026-09 at one minute is unread. The
options fixture stays, gated, for any later line that needs ES option open interest or the
0DTE volume by strike; and the parent-symbol, year-code and expired-OI traps are in
`docs/data-available.md`.
