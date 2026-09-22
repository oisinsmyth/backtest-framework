# D617 FIXTURE — the ES option signed flow census, from the `tbbo` year

*A census, not a signal: buy-initiated, sell-initiated and unsigned contracts per (session, option, ET
clock bucket). No return, no price outcome, no conditioner. The reserved window is read on the
principal's instruction and stays unspent for any return-bearing construction.*

## 1. Why it exists

[D614](D614-STAGE-0-RESULT-not-pinning-ten-sessions-carry-the-whole-pull.md) §7 named the missing
ingredient in its own closing: traded volume is **turnover with no side**, so it cannot say which way
dealers lean, and that is the whole mechanism of a pin. The aggressor side exists in exactly one place on
this disk — the `tbbo` schema — and no study here had ever read it. D511 declined it explicitly. This
builder reads it for the ES option families for the first time.

It answers three questions that had never been measured and that any future signed construction needs
answered before it is designed: whether the ES option tape carries a side at all, how much of its mass
arrives **unsigned**, and whether the flag agrees with the book the same message carries.

## 2. The window, and the authority for reading it

The `tbbo` pull spans **2025-09-11 → 2026-09-10**, 13 files, **37.30 GB**, which lies inside the 2024+
slice this repository holds back. Two things make the read admissible and both are recorded rather than
assumed:

1. the principal's instruction of **2026-09-22** asked for the six sharpenings with the aggressor
   improvement built as a **fixture only** — that is the authority for opening these files;
2. **D510 and D511 read this same window as a non-return census** and recorded it spent for that and
   still unspent for any return-bearing construction. This record makes the same declaration.

Nothing here is scored. A study that later scores a return on these sessions spends the slice then, on
the principal's word, and counts the looks from this census as **zero**, because none was taken: the
output carries contracts and trade counts and G4 asserts the written header is exactly that declared set,
so a return cannot arrive by accident.

Enforcement is at the **file** level, as in D613: `audit_window` raises before any read if a file whose
span falls outside 2025-09-11 → 2026-09-10 would be opened, and the self-test proves it raises on a
pre-window file, a post-window file and an unparseable span.

## 3. The premise, checked against the data rather than the pull spec

The plan asserted from the pull specification that ES options are in these files. That is the kind of
claim this repository requires be measured, so it was, from the file **header** alone before any decode:

| | one 10-day file, from the header alone | the whole year, after the decode |
|---|---|---|
| mapped symbols | **1,339,484**, of which **29,304** are ES-family options | 124,580 options traded |
| families present | 23 | **26** |
| trades decoded | 38,193,225 | **1,440,501,590** |
| ES option trades | 612,149 (**1.10 %** of the tape) | **22,706,840** |
| option contracts | — | **162,752,858** |
| **unsigned (`N`) share of option contracts** | 0.0003 | **0.000166** — against 7.4 % `N` on the whole tape |
| quotes usable on option trades | 0.9923 | **0.9908** |
| **D485 at-quote agreement** | 1.0000 | **0.999983** on 22,496,746 trades |

The unsigned share is the number the design was most worried about: a conditioner signed on 60 % of its
own mass would not be a signed conditioner. At **0.017 %** — 27,000 contracts of 162.8 million — it is a
non-issue for the ES option families. The ceiling is declared at 0.10 and G3 measures it per family and
per bucket, so a later era that starts routing blocks unsigned would trip it rather than pass silently.

**The agreement is 0.999983, not 1.000000, and the difference is the point.** 389 at-quote trades of
22,496,746 disagree with the flag. A check that came back exactly 1 on 22 million rows would be
suspicious — it would suggest the book snapshot is derived from the trade rather than independent of it,
in which case the check would be tautological and worth nothing. A handful of disagreements is what an
independent comparison looks like.

**What the agreement does and does not establish.** It confirms the flag's *direction* — `B` is a buyer
lifting the offer, `A` a seller hitting the bid, D485's convention — and the flipped mapping takes it to
0.0000, which is what makes the check real. It says nothing about **who** the aggressor is. Market makers
aggress to hedge, and a combo leg's side is the combo's. Signed flow is a proxy for customer direction
with an error rate this census does not measure, and the sharpened-ladder pre-registration that follows
carries that limit forward rather than treating the flag as having removed it.

## 4. What is in it

**1,044,886 rows over 124,580 options and 314 ET calendar dates, 2025-09-10 → 2026-09-10**, sha256
`848d4826d240dd2633721e430d07ba87a851f29c793f780f817aa81da10b30ad`; the gzip mtime is pinned, so two
builds hash identically.

Per (`raw_symbol`, `session`) — the ET calendar date of the trade, which is D581's and D613's convention,
so the three option panels join on the same key — twenty value columns: buy-initiated, sell-initiated and
unsigned **contracts**, plus **trade counts**, in each of D613's five ET clock buckets, reused verbatim:

```
[00:00, 12:00)  [12:00, 15:30)  [15:30, 16:00)  [16:00, 18:00)  [18:00, 24:00)
```

The 18:00–24:00 bucket is folded into nothing: the CME trading session for date D opens at 18:00 on D−1,
so those hours are filed under the prior date, and a study wanting session-aligned accumulation adds the
prior date's bucket explicitly. Neither convention is chosen silently.

**The ET date convention also moves the window's own edge, and the build found it rather than the design.**
The first build came back with sessions starting **2025-09-10**, one day before the pull's first UTC date,
and G1 failed. The cause is not a defect: a trade at 00:30 UTC on 2025-09-11 is 20:30 ET on 2025-09-10,
so the opening Globex evening of the window's first trading session carries the previous ET date. The
allowance is exactly **one evening**, it is now declared as `SESSION_FROM` with the reason attached, and
the self-test proves the boundary is tight — the opening evening passes, a second day earlier raises, and
a day past the pull's end raises. The file-level audit is untouched and still refuses to open anything
outside the pull window, which is where the reserved-slice guarantee actually lives. **314** ET calendar
dates rather than ~250 trading sessions is the same convention: Sunday and holiday Globex evenings are
their own dates.

## 5. The gates, each proven to raise on its own break

| gate | what it holds |
|---|---|
| **G1** | keys unique; every session inside the declared window; every symbol matching D581's option regex |
| **G2** | the three sides add to the row total in every bucket; no negative count; no volume without a trade behind it |
| **G3** | the **unsigned share** overall, per family and per bucket, under the declared ceiling of 0.10 |
| **G4** | the written header is **exactly** the declared census set — the guard that keeps a return out |
| **G5** | a **scalar second path** over the raw file reproduces three named (option, session) cells with **positive** 15:30–16:00 volume — the positivity is D613's correction, since a cell where both paths read zero is a check that cannot disagree |
| **G6** | D485's at-quote agreement above the declared floor of 0.95, with the flipped mapping taking it to zero |
| **G7** | the fixture's sha256 is the one the meta recorded |

The self-test proves thirteen breaks fire: the window audit on three kinds of out-of-window file, the
census guard on a return column arriving and on a declared column missing, G1 on a duplicate key and an
out-of-window session and a non-option symbol, G2 on a negative count and on volume with no trade, G3 on
an unsigned share over the ceiling, G6 on agreement below the floor and on there being no at-quote trade
to check against, and the flipped aggressor mapping taking agreement from 1.0 to 0.0. It also proves the
five ET buckets partition the clock at the declared edges — 720, 210, 30, 120 and 360 minutes — and that
15:29 and 15:30 and 15:59 and 16:00 land where they should.

## 6. Cost

Profiled before launching, as the speed discipline requires: the smallest file, 1.00 GB, decoded
**38,193,225 trades in 20.0 s** — 3.01 GB/min serial. Over 37.3 GB that is **12.4 min serial** and a
projection of 2.4 min on six workers at D613's measured 85 % of linear.

Measured: **6.5 min wall on two workers, `[SPEED]` 1.94× — 97 % of linear.** Two rather than six because
D616's fixture rebuild was holding 7.6 GB of the machine at the time and an out-of-memory kill would have
cost that rebuild; the choice was the memory, not the scaling, and the 97 % says the work parallelises
cleanly whenever more workers are free.

## 7. What this does not do

- It does not score anything, and it does not make the signed arm testable. ~250 sessions with the robust
  standard errors this panel produces puts D614's own effect size at **|t| ≈ 1**: a signed arm on this
  window is a pilot, not a test, and the study's pre-registration writes that arithmetic down so the
  census cannot be promoted later.
- It does not identify customers, for the reason in §3.
- It does not touch open interest, gamma or the close. The one number here that constrains a later design
  is the unsigned share, and it constrains it favourably.
