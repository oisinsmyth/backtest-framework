# D415 RESULT — the candle is worse than the clock, and the filter drops the winners

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D415-RESULT-the-candle-is-worse-than-the-clock-and-the-filter-drops-the-winners.md`. The H1 above is the full title.*

**FAILS THE BAR on all three gates.** Pre-registration `dfb9c39` predates the runner and this file
(R8). **The ledger does not move. Nothing was admitted. No holdout was read. 2024+ was not read.**
Same 3,023 events as D414, reproduced from its committed artifact — one population read twice.

Cost: one second.

---

## 1. Stage 0 — the rules fire, and they fire late enough to mean something

```
R1 up-bar      fires 96.0%   lag p10/50/90  1/2/4 bars   trivial (last bar) 1.3%   k = 2
R2 higher low  fires 95.5%   lag           1/1/4         trivial 0.8%              k = 1
R3 re-cross    fires 72.0%   lag           1/1/7         trivial 1.7%              k = 1
```

X-a held: R1 fires on 96% with a median lag of two bars, and only 1.3% of its confirmations are the
trivial last-bar one. The rules are real intraday entries, not the close in disguise. Fire rates
inside cell 2 match outside (R1: 96.8% vs 95.7%), so the selection trap does not announce itself in
the *fire rate* — it announces itself in what the fired events are worth (§3).

---

## 2. The bar

```
                                            n      mean       +-     SE
R1 delta   confirmed entry vs daily close   2,903   -4.62 bp  3.61   -1.3      T1 FAIL
R1 ctrl    unconditional entry at j+2       2,890   -1.60     3.91   -0.4
R1 info    = delta - ctrl                   2,890   -3.04     1.48   -2.1      T2 FAIL
R1 daily-close return, KEPT events          2,903  -17.54    13.00   -1.3
R1 daily-close return, DROPPED events         120 +172.20    63.05   +2.7
R1 dropped - kept                                  +189.74    64.38   +2.9      T3 FAIL
```

| | condition | outcome |
|---|---|---|
| **G1** | R1 fires ≥ 30% | PASS — 96.0% |
| **T1** | confirmed entry beats the daily close | **FAIL** — −4.62 bp, −1.3 SE |
| **T2** | beats the time-matched control | **FAIL — and significantly NEGATIVE**, −3.04 bp, −2.1 SE |
| **T3** | the dropped trades are not better than the kept | **FAIL** — the dropped trades are **+190 bp better**, +2.9 SE |

**D415 FAILS.** Each gate fails for a different reason, and each reason is the study's finding.

---

## 3. THE THREE FINDINGS, one per gate

### 3a. T1 — confirmation does not beat the close, pooled

D414's first touch was −1.60 pooled; the first up-bar after it is −4.62. **No intraday entry on
this construction beats the daily close, pooled.** Nothing has changed since D414 on that point.

### 3b. T2 — THE CANDLE IS WORSE THAN THE CLOCK

This is the gate the design was built around. The time-matched control enters two bars after the
touch **unconditionally, on the same events**. The up-bar rule enters at the first bar that closes
above its open. **The rule is 3.04 bp worse than the clock, at 2.1 SE.**

**The mechanism is definitional.** A bar that closes above its open closed *higher* than the bars
before it — the confirmation *is* a worse price. You pay for the pattern. R3 makes the same point
with a megaphone: a re-cross above the zone's upper edge is by construction the highest entry of
the three, and it loses **35.44 bp to its own clock at −9.8 SE**, with **zero of 2,176 events**
where the pattern beat the unconditional entry.

**And the control's +29.99 bp on R3's confirmed events is not a tradeable number** — it is what
entering one bar after the touch pays *on events selected for having bounced*. That is precisely
the selection §2 of the pre-registration warned would flatter any rule, measured.

### 3c. T3 — THE FILTER DROPS THE WINNERS

R1 declines 120 events (4.0%) — the sessions in which **not one 15-minute bar closed above its
open after the touch**. The daily-close strategy made **+172.20 bp on them** against **−17.54 bp
on everything R1 kept.** The difference is **+189.74 ± 64.38, +2.9 SE.**

**A confirmation rule cannot see the trade that pays because the trade that pays is the one that
never confirms.** This is the selection trap running the other way from how §2 described it: the
rule does not merely flatter its own entries, it *removes the book's best trades* — and it would
have done so silently in a design that reported confirmed events only.

I drafted this section, before looking, as "those are the capitulation days." §4 says what they
actually are, and it is more specific than that.

---

## 4. The dropped trades, looked at — and the mechanism is the clock, not the candle

```
n 120   mean +172.2   median +30.0   trimmed (top 2 and bottom 2 off) +152.2 bp
positive 53%    > +100 bp: 49    < -100 bp: 37    top 5 events = 59% of the P&L
median touch bar of a dropped event: 25 -- THE LAST BAR OF THE SESSION
by year   2018: 34   2019: 15   2020: 23   2021: 15   2022: 23   2023: 10
top 6     C 2020-03-13 +2934 (x2)   GM 2020-03-02 +2410   F 2020-03-02 +1991
          MUR 2022-05-04 +1835      INTC 2020-03-13 +1720
```

**The median dropped event was touched on the last bar of the day.** "No up-bar after the touch"
is, for most of these, **"no bars left after the touch."** These are sessions where price fell all
day and reached the zone only at the close — and the daily-close entry, by construction, buys
them at the session's low. R1 cannot fire on them **mechanically**, because there is nothing left
to scan, not because they lacked a reversal in some long tail.

**It is not two squeeze days.** The trimmed mean is +152 against a raw +172; 49 of the 120 are
above +100 bp; every year from 2018 to 2023 contributes, with 2018 the largest by count. The top of
the list is a March-2020 cluster — four of the six largest are 2020-03-02 and 2020-03-13 — and the
bottom holds three events below −1,100 bp, so the set is violently dispersed and the mean carries
a fat right tail. But the median is +30, the trimmed mean is +152, and the sign holds without the
crash.

**So the finding sharpens rather than softens:** the touch's *time of day* is itself a conditioner
the two execution studies have now measured from both ends. D414 found the **open** touches — the
gap-throughs, 41.9% of events — are the −57 bp in cell 2. D415 finds the **last-bar** touches are
the +172 bp. **A confirmation rule structurally excludes the late-session touch, which is the best
entry there is, because it needs bars after the touch in which to confirm.** That is what
"confirmation" costs on this construction, and no choice of pattern recovers it.

Recorded as an observation about the two studies read together, not as a finding: the time-of-day
split was not declared in advance in either.

---

## 5. THE CELL-2 SECONDARY — nothing intraday fixes it

```
                        delta       ctrl        info          (cell 2, R1 confirms 871 of 900)
D414 first touch      -35.08 (-4.9 SE)
R1 up-bar             -31.98 (-4.8)   -27.10 (-3.9)   -4.98 (-2.2 SE)
R2 higher low         -29.69 (-4.3)   -32.62 (-4.7)   +2.93 (+1.4 SE)
R3 re-cross           -45.88 (-4.8)    -2.91 (-0.3)  -42.97 (-6.2 SE)
```

**Every intraday entry in cell 2 is −30 to −46 bp against the daily close.** First touch −35, first
up-bar −32, two bars later regardless −27, higher low −30, re-cross −46. **The continuation is a
whole-session phenomenon; there is no intraday moment inside it that is a good entry.** The one
positive information number in the study, R2's +2.93, is +1.4 SE and cannot be read.

**X-c was wrong on the word that mattered:** I predicted cell-2 confirmation would be *materially*
better than −35. It is three basis points better, inside the noise.

The secondary's T3 "passes" on 29 dropped events at +1.3 SE — **on lack of power, not on
evidence**; the point estimate (+142 bp) is the pooled finding's shape at a fifth of its size.

---

## 6. Predictions

| | prediction | outcome |
|---|---|---|
| X-a | R1 fires > 80%, median lag ≤ 3 | correct — 96.0%, lag 2 |
| X-b | pooled T1 fails | correct — −1.3 SE |
| **X-c** | cell-2 R1 **materially** better than −35, not positive | **wrong on "materially"** — −31.98, three basis points |
| X-d | T2 fails for R1 | correct, **and stronger than predicted** — significantly negative, not merely null |
| **X-e** | R3 fires < 40%, best delta, worst dropped-trade profile | **wrong in every clause** — 72%, the *worst* delta, and a *milder* dropped-trade gap than R1 |

Three of five. X-e was wrong three ways: the re-cross fires often, enters worst, and — because it
declines 847 events rather than 120 — its declined set is diluted toward the average.

---

## 7. What this leaves for a plan

1. **On this construction, "daily decision, 15-minute execution" has no timing content.** D414
   showed the first touch is worth nothing pooled and −35 in cell 2; D415 shows every confirmation
   pattern tried is worse than a clock, and every clock is worse than the close. **The only
   intraday value found in two studies is the ~6 bp half-spread a resting limit saves** (D414 §2),
   and that is the optimistic fill.
2. **A confirmation filter removes the book's best trades** — the capitulation days that never
   print an up-bar. Any intraday rule that requires a sign of reversal before entering excludes
   them by construction. This is not specific to R1; it is what "confirmation" means.
3. **For cell 2 the honest entry is the daily close or later, and "later" is the untested
   question** — a delayed-entry sweep on the full daily universe, where the signal is actually
   visible, is the next path-invariant step. It is a daily-bar study and does not need the 15m
   fixtures at all.
4. **The signal itself is still unconfirmed** and these 32 names cannot confirm it. `holdout2`
   remains unspent; **2024+ on the 15m fixtures remains reserved.**

**Disposition is the principal's.**

---

## 8. R13

Fifteenth look by object; second on execution; no new data spent.

**Evidence:** `data/d415_15m_confirmation.json` — stage 0, every arm pooled and in cell 2, the bar,
and the per-event table with each rule's confirming bar. Runner
`scripts/run_d415_15m_confirmation.py`, reading D414's committed events and 15m loader rather than
rebuilding either.
