# D759 STAGE 0 RESULT — NO ROOM: quiet long-gamma days revert 39.3 % of the time, but a 10:30 fade on a quiet morning needs 45.1 %

*2026-10-02. Prop book.*
- *Pre-registration: [D759](D759-STAGE-0-PRE-REG-quiet-long-gamma-premise.md) (1c2de7e3).*
- *Runner: `scripts/stage0_d759_quiet_gamma_premise.py`, committed before its run (cbdd5542).*
- *Output: `data/stage0_d759_quiet_gamma_premise.json`. Wall 37 s.*
- *The known answers held: D757's G ∧ ¬I cells on all four roots, and its impulse-day p\* (0.29636).*

## 0. The reading

**The prize on non-impulse days** (ES, YM, RTY pooled), the 10:30 fade to 15:59 at one micro:

| | n | mean | t | median | win |
|---|---|---|---|---|---|
| reverting days | 1,443 | **+\$23.68** | 21.2 | +\$15.24 | 73.7 % |
| other days | 2,501 | −\$19.48 | −7.9 | −\$31.26 | 30.5 % |

- **Z holds:** mean \|net\| on RD days is \$33.05, against 3× cost.
- **p\* = 0.451.**
- **The seen precision** (POST HOC, D757) **is q = 0.393** (SE 0.013, n 1,360).

**NO ROOM:** q < p\*.

**Per root (q against p\*):**

| root | q | p\* | reading |
|---|---|---|---|
| ES | 0.375 | 0.434 | NO ROOM |
| NQ | 0.378 | 0.449 | NO ROOM |
| YM | **0.404** | **0.411** | NO ROOM, the nearest |
| RTY | 0.406 | 0.517 | NO ROOM |

## 1. What it shows

**The principal's turn of the idea holds as a description, but not as a trade.** Strong long-gamma mornings
without an impulse do revert more often than the base: 39 % against 33 %. But on a quiet morning the fade has
little to give back: +\$24 on a reverting day, against +\$65 on an impulse day (D757). A trend that starts after a
quiet morning still costs a full move (−\$19 a day). The break-even rises to 45 %, and the selector reaches 39 %.

**YM comes closest** (0.404 against 0.411). One root out of four within a point, after the fact, is not a lead.

**A deliberate omission, disclosed.** The pre-registration listed "p\* split by gamma state" as reported. Together
with q, that would reveal the fade's net on exactly the G ∧ ¬I days a held-slice test would read. It was not
computed. The JSON says so too.

## 2. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 | Z holds (P 0.7) | **held** (+\$23.68, t 21.2) |
| P2 | NO ROOM, with p\* between 0.45 and 0.55 (P 0.6) | **held** (p\* 0.451) |
| | P(ROOM) ≈ 0.15 | NO ROOM |

## 3. What follows

- **The line stops here** (§3 of the pre-registration). No held-slice test is warranted: even the in-sample
  precision, which flatters by construction, sits below the break-even.
- **The reverting-day line as a whole** (D756, D757, D759) is now measured:
  - the prize is real;
  - a small gap and quiet long gamma each lift the hit rate by 3–6 points;
  - no detector reaches the trade's break-even.

  **Closing it is the principal's call (R15).**
- **The intraday mean-reversion closure on the index micros stands for trading.**
