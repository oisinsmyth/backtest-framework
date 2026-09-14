# D530 — Avenue 3 CLOSED by the principal: the leveraged-ETF reset flow is real and carries **no direction** — and **16 of 36 roots do not trade in the day5m fixture's closing hour**

*2026-09-14. Closed on the principal's word after the Stage 0 below. Nothing admitted (R15).
In sample 2016-01-04 → 2023-12-29; the 2024+ slice was not read.*

---

## The avenue, and why it was worth an afternoon

A leveraged ETF must reset exposure to a fixed multiple of **that day's closing NAV**. For leverage
`L` and assets `A`, after an index move `r` the forced rebalance is `A·L·(L−1)·r` — **positive for
L = +3 (6Ar) and also positive for L = −3 (12Ar)**, so the long *and* the inverse fund both buy after
an up day and sell after a down day. The participant is forced by its own prospectus, cannot
decline, cannot wait, and its size is a deterministic function of a number anyone can observe in real
time. The hedge lands in index futures.

It came out of the lead-scan census as a **genuine hole**: absent from all 43 briefs and all six
exclusion lists — never examined and never excluded.

## It was already half-dead, and the other half died here

**The tradeable expression was already scored.** D463 tested exactly this — *"market intraday
momentum, the last 30 minutes, sign of return-of-day, 15:30 open → 16:00 print"* — and found it *"a
third of its published size on ES… not distinguishable from zero."* The ledger carries it as
K2/K3/K4: **NQ −0.01, ES −0.29, YM −1.12 net Sharpe, gross +$0.66 / +$0.62 / +$0.08** against a
round trip now corrected to $4.21 (D527).

What D463 did **not** test is the mechanism's own two predictions, because it was built as a strategy
test rather than a mechanism test:

| | prediction | result |
|---|---|---|
| **P1** | flow is LINEAR in `r`, so continuation strengthens with &#124;return-of-day&#124; | quintile 1 → 5 reads 47.20 % → **50.63 %**, and Q5 sits at **z ≈ 0.49** |
| **P2** | the flow exists only where a leveraged-ETP complex trades that future | US equity index, 7,489 observations: hit **50.03 %**, **z = +0.1** |

**Nothing, in the one place the mechanism can work.** Per-root the signs do not even agree — NQ
+0.52z, RTY +0.65z, ES −0.45z, YM −0.54z. Reported in **hit rate** because
[D529](D529-the-payoff-ratio-is-exit-geometry-the-hit-rate-is-the-edge-and-my-reframe-was-backwards.md)
established this book is paid for accuracy.

**The flow itself is real and visible** — the equity roots trade **15.7 %–21.1 % of session volume in
the closing hour against an even share of 14.3 %**, a hump of 1.10× to 1.48×. The forced trade
arrives. It just does not predict direction.

## The part that outlives the avenue: my control group was measuring dead air

The first run showed a spectacular apparent effect *outside* the equity index — hit 46.3 %,
**z = −12.6** across 19 roots, i.e. strong reversion into the close. One number gave it away:
**livestock returned n = 20 against ~1,900 for the equity roots.**

That is not a thin root. That is a root whose **session ends before the window**.

**`fut_day5m`'s 09:00–15:59 ET band is a TEMPLATE, not a session.** Share of each root's session
volume that trades in 15:00–15:59:

| root | group | late-vol share | vs even (14.3 %) | sessions with data |
|---|---|---:|---:|---:|
| RTY / ES / NQ / YM | equity index | 21.1 / 20.4 / ~18 / 15.7 % | **1.48 / 1.43 / 1.26 / 1.10** | ~1,970 |
| UB, TN, NKD, BTC, ZF, ZT, SR3 | — | 9.8–14.4 % | 0.68–1.01 | full |
| the six FX (6A 6B 6C 6E 6J 6S) | — | 6.6–8.3 % | 0.46–0.58 | full |
| ZN, ZB | — | 11.0 / 11.6 % | 0.77 / 0.81 | full |
| GC, SI, NG, CL, HG | COMEX/NYMEX | 5.4 / 4.4 / 3.9 / 3.1 / **2.6 %** | 0.38 → **0.18** | full bars, dead volume |
| PL, HO, PA, RB, BZ | — | 2.7–3.4 % | 0.19–0.24 | full bars, dead volume |
| LE, HE | livestock | **0.02 %** | 0.00 | **18–19** |
| **ZC, ZS, ZW, ZL, ZM** | grains | **0.00 %** | 0.00 | **ZERO** |

**The five grains have literally no bars in that hour** — they close 14:20 ET. Livestock closes
14:05, COMEX metals 13:30, NYMEX energy 14:30. **A "close" measured in a root's illiquid tail bounces
on the spread, and bid-ask bounce is indistinguishable from reversion.** Twelve of 25 roots in my
ZERO group and four of seven in MED were outside their own session; the −12.6 z was my grouping, not
the market.

**16 of 36 roots have the day5m closing hour essentially outside their market.** `data-available.md`
warned that the ags are not on the Globex template; this quantifies it for every root, and the table
is now recorded there.

## What this changes beyond this avenue

**Every price-action statistic computed on a commodity root over the 09:00–15:59 band in this
programme has included hours that root barely trades.** That includes D515's day/night
decomposition, which read CL and GC on `day_window = 9–15`. It does not overturn D515's headline —
NQ's day edge is measured on NQ's own session and stands — but **the CL and GC rows in that record
were measured on the equity clock, and a session-native re-measurement is the obvious next step**
rather than a correction to assume either way.

---

Reproduced by [`working/avenue3_leveraged_etf_reset.py`](../../working/avenue3_leveraged_etf_reset.py)
(the mechanism test, groups declared in the docstring before the run) and
[`working/avenue3_window_check.py`](../../working/avenue3_window_check.py) (the window census).
