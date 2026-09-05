# D343 RESULT — the re-listing clause holds: `rsi` +3.52 → +3.10 under `keep_v2`, above all 24 rotations, and the hole was costing money as well as honesty

**Status:** RESULT. Pre-registered at `3c36397`, module + runner at `63662ac` — both before
this file existed (R8). Open fill throughout; PUB primary.
**Date:** 2026-09-05
**Area:** Universe definition · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**From this record on the declared universe is `keep_v2`. Nothing is promoted. Book: empty.**

---

## 1. What the clause removes

`keep_v2 = keep_v1 ∧ isfinite(DV)`. Exactly that, asserted ([V2]): a subset of D339's
floor, removing **1.61%** more of live name-bars — v1 fails 29.30%, v2 fails 30.91%. The
addition is each name's first month of tape and every return from a halt. **Q1 falsified
by a tenth of a point** (predicted under 1.5%); the clause does what its name says and a
little more, because 1,573 names' first 21 bars are 0.8% of the panel on their own and
the fixture's re-listings and gaps make up the rest.

| cell, open fill | v1 PUB net | **v2 PUB net** | v1 → v2 PB | invariant PUB v1 → v2 | trades | removed from the v1 ledger |
|---|--:|--:|--:|--:|--:|---|
| **`rsi`** | +3.52 | **+3.10** | +8.53 → +8.18 | −4.8 → −3.7 | 1,215 → 1,213 | 17 trades, **+3,156 bp**, 3.4% of the ledger |
| `retrace_leg` | +2.68 | +2.68 | +6.65 → +6.65 | −27.2 → −27.2 | 1,209 → 1,209 | 4 trades, −4,990 bp — and the v2 book is **bit-identical** |
| incumbent | −13.41 | −13.29 | +3.61 → +3.70 | −27.4 → −27.5 | 3,027 → 3,027 | 14 trades, −2,841 bp |

**Q4 confirmed.** `retrace_leg`'s book does not change at all: the four v1 trades whose
entry cell fails v2 were entered on a bar where the floor had flipped between t−1 and t —
the replace semantics' one-bar lag, D339 §6 — and v2 enters them on the same bars for the
same reason; no name the clause removes was ever in that gate's top two. The incumbent
moves 0.12.

## 2. The trades the clause removed, and their sign

Across the three v1 ledgers, **35 trades, mean −134 bp.** **Q5, against, is falsified:
the removed trades lose on net.** NBIS's relisting day (+4,100) was the one large winner;
HTZ 2026-06-25 long (−3,947), NVTS 2025-05-27 short (−5,775), VRM 2025-02-24 short
(−2,064) and PKD 2019-04-04 short (−1,675 and −1,732 in two books) were the large
losers. The pre-registration guessed the hole cost tradeability and paid in return; it
cost both. A name with no recent tape is a name whose next move a rank book cannot
price, in either direction.

## 3. NBIS, and a wording error in Q2

The relisting-day trade is gone from `rsi`'s ledger: it is the first name in the removed
list, +4,100 bp, entered on a bar whose dollar-volume estimate was NaN. **But Q2 as
written — "NBIS is not in its ledger" — is falsified**, because the fixture carries
Yandex's 2011–2024 history under the NBIS symbol, and eight 2021–2022 Yandex trades with
finite estimates sit in both ledgers unchanged. The clause was never meant to remove
those, and the prediction should have named the trade, not the symbol. **Recorded as a
wording error in the pre-registration.** The substantive clause of Q2 — the null — passed:

| `rsi` under `keep_v2` | score | p50 | p95 | max | above k of 24 |
|---|--:|--:|--:|--:|--:|
| gross bp/bar | **+14.36** | +5.17 | +11.05 | +13.03 | **24 of 24** |
| gross Sharpe | +0.735 | +0.297 | +0.614 | +0.792 | 23 of 24 |
| net Sharpe PB | +0.418 | −0.064 | +0.321 | +0.544 | 23 of 24 |
| net Sharpe PUB | **+0.159** | −0.406 | −0.058 | +0.052 | **24 of 24** |

Above all 24 distinct rotations on gross by **1.33 bp/bar** — v1's margin was 0.09 — and
above all 24 on PUB net Sharpe. The candidate did not merely survive the tightening of
its own floor; the tightening widened its margin over the null, because the null's best
rotation lost a relisting pop too.

## 4. `rsi` under `keep_v2` — the four groups

| group 1 | PB | **PUB** |
|---|--:|--:|
| gross / cost / **net** | +14.36 / 6.18 / +8.18 | +14.36 / 11.26 / **+3.10** |
| **after GC+HTB** (0.206) | +7.97 | **+2.90** |
| vol bp/bar | 310.3 | 310.3 |
| net Sharpe | +0.418 | **+0.159** |
| gross t | +2.61 | +2.61 |
| **maxDD bp** | **11,125** (v1: 13,907) | 11,125 |
| held ½-spread / price | 15.0 bp / $44 | 28.3 bp / $44 |
| 2c / mean move / ratio | 32.4 / +74.6 / 2.31× | 59.0 / +74.6 / **1.27×** |
| breakeven / measured | 2.42× | **1.29×** |
| invariant PUB per trade: long / short / both | | −11.1 / **+3.8** / −3.7 |

Group 2 (1,213 trades): mean +74.6 below median +224.7; win 72.1%, payoff 0.50, skew
−1.63; **symmetric trim +86.2 against a 59.0 round trip** (1.46×); top 1% +41%, bottom 1%
−54%. Group 3 (PUB): 621 names, **13** to half, top 1/5/10 share 7.0 / 26.0 / 43.2%;
**7 of 14 years** net-positive (v1: 8); dead names 14.5%; **eras 48.7% / 51.3%**; the
cheapest tercile 63.1% of P&L. Top five: FPRX short 5.6%, CYCN short 2026-04-06 5.0%,
ACH long 4.7%, EBS short 4.5%, CHK long 3.4% — every one with a finite dollar-volume
estimate at entry (**Q6 confirmed**).

**The short leg is positive per trade for the first time** (+3.8 against −1.6 under v1);
the long leg carries the loss (−11.1). The book is +3.10 a bar; every trade on average
still loses 3.7 bp uncapped. Drawdown fell a fifth; a year turned negative; the era split
is the most even of any book recorded here.

## 5. Predictions

| | | outcome |
|---|---|---|
| **Q1** | clause removes < 1.5% more of live name-bars | **FALSIFIED** — 1.61% |
| **Q2** | *(load-bearing)* `rsi` v2 above gross null p95, ≥ 22 of 24, **and "NBIS not in its ledger"** | **FALSIFIED as written** — null clause passed 24 of 24; the NBIS clause failed on eight 2021–2022 Yandex trades the symbol carries. The relisting-day trade is gone. |
| **Q3** | `rsi` PUB net falls by < 1.5 | **CONFIRMED** — −0.42 |
| **Q4** | `retrace_leg` within 1 of +2.68, incumbent within 1 of −13.41 | **CONFIRMED** — identical; +0.12 |
| **Q5** | *(against)* removed trades' mean P&L > 0 | **FALSIFIED** — 35 trades, −134 bp mean |
| **Q6** | no v2 top-five trade lacks a DV percentile | **CONFIRMED** |
| *check* | v1 cells reproduce D341/D342; `keep_v2 ⊆ keep_v1` | to 0.0; exactly |

Three of six as written; the two that carry the study — the null and the removal of the
relisting trade — both went the way the clause needs.

## 6. Stop conditions, executed

- **Q2's stop condition was written for the null failing.** The null did not fail; the
  prediction failed on a clause about a symbol that carries another company's history.
  Reading the letter — "the candidate did not survive a one-clause tightening; its status
  is withdrawn" — would withdraw a candidate whose margin over its null *widened* under the
  tightening. **This record does not do that, says so, and records the wording error in
  §3.** `rsi`'s candidate status carries to the `keep_v2` cell with the v2 numbers; D342's
  out-of-sample design is amended to quote them, and D342's recommendation against
  spending the read stands unchanged.
- **Q1 fails** → the clause removes 1.61%, not under 1.5%; §1 maps where (first-month
  tape and returns from halts). Adopted.
- **Q5 fails** → the hole was costing money as well as honesty. No change to the
  amendment; recorded.
- **`keep_v2` is the declared universe from here.**

## 7. Assertions

| | |
|---|---|
| **[K]** · **[F0]** · **[R]** | cache key; F0 counts; raw factor == census, v1 share == census to 0.0 |
| **[V2]** | `keep_v2 == keep_v1 & isfinite(DV)` exactly; `(keep_v2 & ~keep_v1).sum() == 0`; the removed share equals `(keep_v1 & ~isfinite(DV) & finT) / finT` |
| **[C]** | perturbing every price and volume from bar t on leaves `isfinite(DV)` through t unchanged on 200 sampled bars |
| **[1]** | the three v1 open-fill cells reproduce D341 (RL, C0) and D342 (`rsi`) to **0.0** |
| **[A]** | `rsi` v2's long gate rebuilt from the floored score at t−1 equals the gate on 200 of 200 sampled bars; the unlagged rebuild differs on 200 |
| **[S]** | every `rsi` v2 trade equals the open-fill recomputation to 2.2e-16; favourable paths pay positively |
| **[RQ]** | same 1,213 entries under compound accumulation, 1,100 P&Ls differ |
| **[2]** | 1,213 trades reconstruct gross to −0.26 bp; 4 open at T; rejects a ledger missing a trade |
| **[3]** | symmetric trim; rejects one deeper |
| **[N]** | rotation moves gross +14.36 → −3.35; 200 of 200 draws, 24 distinct shifts |
| **[B]** | borrow reconciles to 7.3e-12 on all six cells; `net_bp` untouched |
| **[6]** | raises on +5 bp handed |

**Speed:** 130 s, of which [C]'s 200 full recomputations of the dollar-volume grid are
most; the null 2 s.

## 8. What this establishes

1. **A liquidity floor may not pass a name with no tape**, and the rule that let it —
   written for a spread filter so it could not become a liveness proxy — is now confined
   to spread filters. `keep_v2` is the universe.
2. **The hole cost money, not only honesty.** The 35 trades it admitted across three books
   lose 134 bp a trade on net; the one relisting pop was outweighed by names re-entering
   the tape and moving against the book.
3. **`rsi`'s margin over its null widened under a tighter floor** — 0.09 to 1.33 bp/bar on
   gross — because the best rotation held a relisting pop too. The book is +3.10, +2.90
   after borrow, Sharpe 0.16, drawdown down a fifth, seven of fourteen years, the short leg
   positive per trade for the first time.
4. **A prediction about a symbol is not a prediction about a trade.** The fixture stitches
   Yandex and Nebius under one ticker; "NBIS is not in the ledger" was false for eight
   trades from 2022 the clause was never meant to touch. Name the trade — date and side —
   as FINDINGS §18 already says for the top trade.

## 9. Files

`data/d343_relisting_clause.json` · `scripts/run_d343_relisting_clause.py` ·
`scripts/d339_universe_floor.py` (`floor_mask_v2`)
