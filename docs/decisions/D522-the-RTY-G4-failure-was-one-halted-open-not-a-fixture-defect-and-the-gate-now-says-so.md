# D522 — RTY's G4 failure was **one halted open**, not a fixture defect; the gate now says so, and RTY joins the committed fixtures

*2026-09-13, on the principal's instruction to fix the RTY G4 failure carried forward from
[D521](D521-the-three-remaining-flat-id-builders-are-ported-and-the-open-interest-fixture-was-carrying-a-phantom-CL-contract.md).
Data layer only: no study, no signal, nothing admitted to any book or ledger (R15).*

---

## The one-line answer

**One session — 2020-03-16 — carried the entire failure, and both fixtures are right about it.**
Dropping that single day takes RTY's open-to-close correlation with IWM from **0.989854 to
0.999339**. The gate was comparing a **limit-locked futures print** against a **cleared equity
price**, because the futures and the equity market did not open over the same interval that
morning. The fixture is not wrong; the gate's implicit assumption was.

| RTY G4, corr(futures open→close, IWM open→close) | |
|---|---|
| as gated before | **0.989854** on 2,277 days — FAIL against a 0.99 bar |
| drop the single worst day | **0.999339** |
| drop the worst 5 | 0.999741 |
| **as gated now** (sessions with a continuous open) | **0.999554** on 2,272 days — PASS |

**All four roots now pass every gate**, and `fut_RTY_rth_1m.csv.gz` is committed for the first time.

---

Every figure below is recomputed by
[`scripts/d522_rty_g4_diagnosis.py`](../../scripts/d522_rty_g4_diagnosis.py) into
[`data/d522_rty_g4_diagnosis.json`](../../data/d522_rty_g4_diagnosis.json) from committed fixtures
only — no archive, no databento, either interpreter, 18 s. It asserts the gate's own 0.98985 before
it explains it.

---

## 1. It is one day, and I looked at it

Ranking the 2,277 matched sessions by the disagreement between the two legs. The distribution is not heavy — it is **one point**:

    day          futures 09:30 -> 15:59      IWM 09:30 -> 15:45        disagreement
    2020-03-16   1,109.40 ->   999.60   -9.90%   105.47 -> 103.30  -2.06%   -7.84 pts
    2020-03-12   1,178.90 -> 1,114.30   -5.48%   116.77 -> 111.72  -4.33%   -1.16 pts
    2020-03-13   1,175.90 -> 1,201.70   +2.19%   118.31 -> 119.70  +1.18%   +1.02 pts

The second-worst day is **6.8× smaller** than the worst. Ten of the worst fifteen are March 2020.

## 2. The futures side is not wrong — and the independent builder does better than agree

`fut_sessions_hourly` reads the same archive through different code (hourly bars, a different
front-month rule, a different `ids_of` call site). Its close leg is the same object — `h15_c` equals
`p1600` **exactly on all 2,277 shared days** — but its open leg is **not**: `h09_o` is the 09:00
hour's open, which on a normal RTY session sits **1.8 points** away from the 09:30 open (p90 5.5),
and matches it exactly on only **43 days in nine years**.

**2020-03-16 is one of those 43.** `h09_o` = `p0930` = **1109.4**, and the 09:00 hour carries just
**16 minute-bars against a median of 60**. So the independent builder is not merely confirming the
number — it is saying the contract **did not move between 09:00 and 09:30** on a morning the index
fell 14 %, and barely traded. That is the signature of a limit lock, arrived at from the other side.

The equity side is not flagged either: the equity fixture ships a `suspect` column, and **0 of the
2,277 days are flagged**, so that was not the answer.

## 3. What actually happened: the market was halted at the open, and the futures were limit-locked

On 2020-03-16 **all four index roots print exactly once at
09:30 and then nothing until 09:45**:

    RTY  09:30   1109.4 / 1109.4 / 1109.4 / 1109.4    115 lots   <- one price, the limit
         09:45   1091.2 / 1094.7 / 1047.1 / 1050.7  1,034 lots   <- the market reopens and gaps
    ES   09:30   2501.50 (single price, 831 lots) then 09:45 2445.50 -> 2367.00

All four sessions carry **376 bars: exactly the 14 minutes 09:31–09:44 are missing.** On the equity
side the 09:30 fifteen-minute bars barely traded — as a fraction of each ETF's own trailing median
opening volume: **QQQ 0.004, SPY 0.261, IWM 0.368, DIA 0.477.**

So the two legs measure different things. The futures' 09:30 print is **pinned at the price limit**
(a single trade at a single price); the ETF's 09:30 bar is the **true gap-down** after the
circuit-breaker halt. The disagreement is not error — it is the distance between a locked price and
a cleared one, and it is market-wide, hitting all four roots at once:

| root | futures 09:30→close | ETF 09:30→close | disagreement |
|---|---|---|---|
| ES | −4.97 % | −0.73 % | −4.23 pts |
| NQ | −6.06 % | −2.63 % | −3.43 pts |
| YM | −6.01 % | −1.97 % | −4.04 pts |
| **RTY** | **−9.90 %** | **−2.06 %** | **−7.84 pts** |

**RTY fails and the others do not because small caps moved furthest between the lock and the
reopen**, not because its fixture is worse. ES, NQ and YM carry the same defect in the same
statistic; they simply had enough margin to absorb it.

**A halt LATER in the session does not do this.** 2020-03-09, 03-12 and 03-18 were also halted, and
their disagreements are −0.33, −1.16 and −0.17 points — ordinary. Both markets still opened at 09:30
and closed at 16:00; only a halt *at the open* separates the two legs' start points.

## 4. The amendment, and why it is not a thumb on the scale

**The rule:** exclude sessions whose minute bars are **not contiguous over 09:30–09:44**.

Three properties make this a statement about the gate's assumption rather than a fitted exclusion:

1. **The window is not a free parameter.** G4's open-side reference *is* the ETF's 09:30
   **fifteen-minute** bar. 09:30–09:44 is that bar's own span. The requirement is simply that the
   futures traded throughout the interval the equity leg is measured over.
2. **It is decided from the futures bars alone** — it never sees the disagreement it is used to
   judge. (`a-check-must-be-able-to-fire-and-a-control-must-not-overlap-the-outcome`.)
3. **It is extremely narrow, and it was measured before it was adopted.** It flags 4, 6, 14 and 6
   sessions on ES, NQ, YM and RTY (0.11 %–0.39 %), and of those the ones that actually reach G4 —
   i.e. that have both legs — are **3, 3, 3 and 5**:

   | root | flagged | **excluded from G4** | the rest are |
   |---|---|---|---|
   | ES | 4 | **3** — 2020-03-09, 03-12, 03-16 | 2011-05-30 (Memorial Day) |
   | NQ | 6 | **3** — the same three | two holidays and 2013-09-20 |
   | YM | 14 | **3** — the same three | ten holidays and 2020-02-28 |
   | RTY | 6 | **5** — those three plus 2017-07-10 (its first session) and 2017-07-31 | 2019-07-04 |

   Everything flagged but not excluded is a **US market holiday with no ETF bar**, so it was never in
   the matched set to begin with. The three days common to all four roots are exactly the three
   Level-1 circuit-breaker sessions of March 2020.

   And the rule is visibly **not** fitted to the harmful day: of RTY's five exclusions, 2017-07-10
   and 2017-07-31 disagree by **0.07 and 0.01 points** — they are harmless, and they are excluded
   anyway because the rule is mechanical.

**And it cannot hide a defect.** `corr_open_to_close` keeps its old meaning and its old value and is
still written to the meta — it is now *reported* rather than gated. The gated statistic is the new
`corr_open_to_close_continuous_open`; every excluded session is **named in the meta with both legs'
returns and their disagreement**; and the gate additionally fails if more than `G4_MAX_EXCLUDED = 10`
sessions are excluded, so the exclusion cannot silently grow into a place to put inconvenient days.

| root | all days (reported) | continuous-open (gated) | excluded |
|---|---|---|---|
| ES | 0.9957 | **0.9997** on 3,490 | 3 |
| NQ | 0.9974 | **0.9991** on 3,490 | 3 |
| YM | 0.9955 | **0.9995** on 3,488 | 3 |
| RTY | 0.9899 | **0.9996** on 2,272 | 5 |

The self-test gained a check that can fail: the detector must flag a 09:30-then-nothing session and
a session with no open, must **not** flag a full open, a 13:00 halt or an early close, must catch a
single missing minute inside the window, and must return the empty set on a clean session.

## 5. What was NOT done, and why

**The threshold was not lowered.** RTY's bar is already the loosest of the four (0.99 against 0.995)
and it missed by 0.00015. Moving a bar to clear a number it was written to test is how a gate stops
being one.

**The statistic was not made robust.** A rank correlation or a trimmed mean would have passed too,
and would also have hidden *a handful of badly-wrong days* — which is exactly the signature the
D520/D521 id defect produces. The gate keeps its sensitivity to that; it loses only the assumption
that both markets open at the same moment.

## 6. Consequence for a study

**Anything reading the 09:30 open of an index future must drop 2020-03-09, 2020-03-12 and
2020-03-16, or read the open at 09:45 on those sessions.** The prints on those days are real, and
they are not tradeable opens. This is now recorded in `docs/data-available.md` beside the fixture.
