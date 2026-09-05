# D341 RESULT — honestly scored, `retrace_leg` is +2.7 bp/bar: the two conventions overlapped by 13, the ordering survives, and the book is a rounding error above zero

**Status:** RESULT. Pre-registered at `7413deb`, runner at `db004b3` — both before this
file existed (R8). D333 panel, D334 cache, F0 on the structure books, D339's floor
(replace), D340's open fill, PUB primary.
**Date:** 2026-09-05
**Area:** Cost model · universe · strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. Book: empty.**

---

## 1. The four squares

PUB net bp/bar, PB in brackets. The three known corners reproduce D338, D333, D339 and
D340 to **0.0** on 70 published numbers ([1]); the fourth is new.

| | none / close | floor / close | none / open | **FLOOR / OPEN** | Δfloor | Δfill | additive | **interaction** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| **`retrace_leg`** | +18.93 [+23.43] | +3.14 [+7.40] | +5.14 [+9.97] | **+2.68 [+6.65]** | −15.79 | −13.78 | −10.65 | **+13.33** |
| incumbent C0 | −12.68 [+7.15] | −13.02 [+4.89] | −15.90 [+2.29] | **−13.41 [+3.61]** | −0.34 | −3.21 | −16.23 | +2.82 |
| `rsi` | −2.55 [+6.18] | +4.05 [+10.59] | −3.85 [+3.58] | **+3.52 [+8.53]** | +6.60 | −1.30 | +2.75 | +0.77 |
| `hist_L` | −26.79 [−12.33] | −11.56 [+1.22] | −14.88 [+2.89] | **−10.28 [+1.00]** | +15.22 | +11.91 | +0.35 | −10.63 |

Invariant lens, PUB net per trade, same layout:

| | none / close | floor / close | none / open | floor / open |
|---|--:|--:|--:|--:|
| `retrace_leg` | +10.0 | −24.5 | −18.3 | **−27.2** |
| incumbent | −34.5 | −23.8 | −43.3 | −27.4 |
| `rsi` | +11.0 | −8.5 | +9.7 | **−4.8** |
| `hist_L` | −59.2 | −6.6 | −52.5 | −23.9 |

**Q1, the load-bearing prediction, is falsified: +2.68, not ≤ 0.** I predicted the two
corrections would add. They overlap by 13 bp/bar, because the overnight gap the fill
credited lived in the names the floor removes.

## 2. The overlap, and where it is not

| implementation-lag premium per entry, bp | long, unfloored → floored | short, unfloored → floored |
|---|--:|--:|
| `retrace_leg` | **+44.8 → +11.2** (t 1.35) | +27.2 → **+29.2** (t 1.55) |
| incumbent | +20.6 → +12.2 (t 2.07) | −15.8 → −2.0 |
| `rsi` | +18.5 → **+0.7** (t 0.08) | −43.1 → −7.7 |
| `hist_L` | +91.8 → +45.9 (t 2.89) | +19.4 → −20.6 |

**Q2 and Q3 confirmed.** The long-leg gap on `retrace_leg` was three-quarters the
floor's names: +44.8 falls to +11.2 once the sub-$5, bottom-decile-volume names are
gone. **The short-leg gap is not the floor's** — +27.2 becomes +29.2 — so the liquid
names `retrace_leg` shorts still gap down at the next open, and that is a real cost the
floored book pays under the open fill. `rsi`'s premiums go to zero under the floor on
both legs: its floored book has no gap dependence at all.

**Q4 falsified**: the incumbent's corrections are not additive within 2 bp/bar either;
its interaction is +2.82, from the long-leg premium halving under the floor.

**The `hist_L` square is the caution.** The open fill *improves* its unfloored book by
+11.9 bp/bar although its long leg was credited +91.8 bp per entry under the close fill.
D340 §3 explained the mechanism: the target exit reads the accumulated excess, the
entry bar's excess differs, exits fire on different days, and only a fraction of trades
recur — the two fills are different books. **Δfill is not the premium times the entry
rate**; for a book with a target exit it can have the opposite sign. The premium table
says what the convention credited per entry; only the square says what it did to the
book.

## 3. The honest number: `retrace_leg` under floor and open fill

| group 1 | PB | **PUB** |
|---|--:|--:|
| gross / cost / **net** bp/bar | +13.87 / 7.22 / +6.65 | +13.87 / 11.19 / **+2.68** |
| **after GC+HTB borrow** (0.216) | +6.44 | **+2.46** |
| after house 300 | +5.47 | +1.50 |
| vol bp/bar | 300.1 | 300.1 |
| gross / net Sharpe | +0.734 / +0.352 | +0.734 / **+0.142** |
| gross t | +2.61 | +2.61 |
| maxDD bp | 11,059 | 11,059 |
| exposure / fill | 76.1% / 100% | 76.1% / 100% |
| held ½-spread / price / $vol | 17.9 bp / $46 / $46.8M | 28.3 bp / $46 / $46.8M |
| 2c / mean move / ratio | 37.9 / +73.1 / 1.93× | 58.8 / +73.1 / **1.24×** |
| breakeven ½-spread | 35.4 = 1.98× | 35.4 = **1.25×** |
| invariant per trade: long / short / both | | **−23.1 / −31.8 / −27.2** |

Group 2 (1,209 trades): mean +73.1 **below** median +217.1; win rate 71.4%, payoff 0.52;
skew −0.03, kurtosis 19.9; ex-top-1% +39.5, ex-bottom-1% +110.6, **symmetric trim +77.0
against a round trip of 58.8** (1.31×); top 1% +47% of P&L, bottom 1% **−50%**.

Group 3 (PUB): 594 names, **9** to half the P&L, top 1/5/10 share 15.9 / 36.5 / 55.8%;
**8 of 14 years** net-positive (12 gross); both era halves positive (+16.2 / +12.4 a
trade); the cheapest tercile is 52% of P&L at +30 net on its own cost; **dead names are
44.4% of P&L**.

| top five | side | entry | hold | P&L bp | share | entry bar r1 / oc | raw price | DV pct |
|---|---|---|--:|--:|--:|---|--:|--:|
| **CHK** | short | 2020-06-09 | 16 | +8,758 | **9.9%** | −66.0% / +23.7% | $69.92 | 0.69 |
| KALA | short | 2022-12-30 | 13 | +5,684 | 6.4% | +53.6% / +12.6% | $24.84 | 0.54 |
| CHK | long | 2020-04-22 | 2 | +4,597 | 5.2% | +13.6% / +10.4% | $17.77 | 0.55 |
| RAPT | long | 2024-02-21 | 1 | +3,683 | 4.2% | +48.2% / +37.0% | $6.87 | 0.36 |
| KODK | short | 2018-01-16 | 16 | +3,167 | 3.6% | −7.6% / −4.0% | $9.20 | 0.59 |

Every top trade passes the floor. **Q8 falsified** on share: CHK's bankruptcy week is
9.9% of the ledger — under the open fill the short is held sixteen bars, not one, and
earns the collapse after the entry-day squeeze rather than the gap. Two of the five
largest trades are Chesapeake in 2020; CHK and KODK are both dead names, and 44% of the
book's P&L comes from names that later delisted.

**The null, resolution stated** — 200 draws, **24 of 24 distinct shifts drawn**:

| statistic | score | p50 | p95 | max | above k of 24 |
|---|--:|--:|--:|--:|--:|
| gross bp/bar | **+13.87** | +4.09 | +8.48 | +12.28 | **24 of 24** |
| gross Sharpe | +0.734 | +0.237 | +0.489 | +0.795 | 23 of 24 |
| net Sharpe PB | +0.352 | −0.131 | +0.201 | +0.422 | 23 of 24 |
| net Sharpe PUB | +0.142 | −0.528 | −0.211 | +0.031 | 24 of 24 |

**Q7 confirmed.** The gross null has teeth and the ordering is above all 24 rotations of
the liquid gate. The matched-cost net null under PUB is negative at p95 and at its
maximum: a random four-name book from the same gate loses 11 bp/bar of cost, and the
signal pays it back with 2.7 to spare. That is what "survives every convention" means
here — an ordering that clears its own cost by a margin smaller than the borrow
uncertainty.

## 4. `rsi` gains from honest scoring

| `rsi` floor/open (PUB) | |
|---|--:|
| gross / net bp/bar | +14.72 / **+3.52** |
| net Sharpe / maxDD | +0.181 / 13,907 |
| held ½-spread / price | 28.1 bp / $44 |
| trades / names / names to half | 1,215 / 627 / **14** |
| symmetric trim vs 2c | **+88.3** vs ~58 |
| top 1% / bottom 1% share | +40% / −54% |
| years net-positive | 8 of 14 |
| dead names' share | 12.1% |
| invariant PUB per trade | −4.8 |
| top trade | FPRX short 2020-11-13, **5.5%** |

**Q5, against, confirmed.** `rsi`'s book was negative on the unfloored universe; under
the floor it is positive, and the open fill barely touches it because its floored legs
have no gap premium (+0.7 / −7.7). It is a broader book than `retrace_leg`'s — 14 names to
half, 12% from dead names, top trade 5.5% — with a higher trimmed mean and a higher
Sharpe. The stop condition executes: **`rsi` under the floor and the open fill gets its
own candidate record next**, four groups and the top trade first.

## 5. Predictions

| | | outcome |
|---|---|---|
| **Q1** | *(load-bearing)* RL floor/open PUB net ≤ 0 | **FALSIFIED** — +2.68; +2.46 after GC+HTB |
| **Q2** | floored long-leg premium < +22.4 | **CONFIRMED** — +11.2 |
| **Q3** | RL interaction > +5 | **CONFIRMED** — +13.33 |
| **Q4** | incumbent additive within 2 | **FALSIFIED** — +2.82 |
| **Q5** | *(against)* `rsi` floor/open > 0 | **CONFIRMED** — +3.52 |
| **Q6** | `hist_L` floor/open < −10 | **CONFIRMED** — −10.28 |
| **Q7** | RL floor/open gross above its null p95, teeth | **CONFIRMED** — 24 of 24 |
| **Q8** | top trade < 7%, liquid | **FALSIFIED** on share — CHK 9.9%, liquid |
| *check* | three known corners reproduce | 70 numbers to 0.0 |

Five of eight. The one that mattered was wrong because I treated two corrections with a
common cause as if they added.

## 6. Stop conditions, executed

- **Q1 fails** → by the record's letter `retrace_leg` under floor and open fill is **the
  first cell that survives every convention this programme owns**, and D339 §7's
  out-of-sample design **becomes live**. Live is not run. **This record recommends
  against spending the holdout on it**: +2.68 bp/bar is a 0.14 Sharpe on a book with 47%
  annualised volatility, negative per trade on both legs, 44% of its P&L in names that
  later died and a tenth in one bankruptcy. An out-of-sample read would not be able to
  distinguish it from zero, and the holdout has one read.
- **Q5 holds** → `rsi` under the floor and the open fill is pre-registered as a
  candidate record next. It is the better liquid book on every group-2 and group-3
  statistic, and it is the first book here to *gain* from honest scoring.
- **Q3 holds** → the floor and the fill are not two costs to charge in full against
  every future book; a floored book pays the fill only on the gap that survives the
  floor. The short-side gap does.
- **Q7 holds** → D338's "the signal is real" stands in its narrowest form: an ordering
  of the liquid gate, above all 24 rotations on gross, worth about 3 bp/bar after
  everything.

## 7. Assertions

| | |
|---|---|
| **[K]** | cache key with `ragged_panel.py`; npz newer than the builder |
| **[F0]** | 1,719 filings applied, 2.54% |
| **[R]** | module raw factor == census factor on the full grid; floor fails 29.2962% == census |
| **[F]** | 0 of 4,137,239 priced cells lack a usable open |
| **[1]** | **70 published numbers reproduced to 0.0** — D338 (RL none/close), D333 (C0), D339 (all eight close-fill cells), D340 (RL and C0 none/open), on net, Sharpe and invariant per trade under both conventions |
| **[E]** | in all 8 squares the two fills read one gate; entries never diverge before the exit sets do |
| **[A]** | RL floor gate rebuilt from the floored score at t−1 equals the gate on 200 of 200 sampled bars; the unlagged rebuild differs on 200 |
| **[S]** | every RL floor/open trade equals the open-fill recomputation to 2.2e-16; favourable excess paths pay positively on every long and short |
| **[RQ]** | same 1,209 entries under compound accumulation, 1,122 P&Ls differ; group 1 scores the summed ledger |
| **[2]** | 1,209 trades reconstruct gross to −0.40 bp via `contributions_fill`; 4 open at T, no hole; rejects a ledger missing a trade |
| **[3]** | symmetric trim, k=12; rejects one deeper |
| **[N]** | rotation moves open-fill gross +13.87 → −2.86; 200 of 200 draws valid, 24 distinct shifts |
| **[B]** | borrow reconciles to 1.1e-11 on all 16 cells; `net_bp` untouched |
| **[6]** | raises on +5 bp handed |

**Speed:** 74 s including the null (2 s: 24 simulations, one per distinct shift).

## 8. What this establishes

1. **The honest number exists and it is +2.68 bp/bar PUB, +2.46 after borrow**, for the
   best book the programme has found, after the deal filter, the dividend bound, the
   published spread, the universe floor and a next-open fill. Sharpe 0.14. The stack's
   headline since D318 was +14.57.
2. **Corrections with a common cause do not add.** The gap the fill removed was in the
   names the floor removed; the two overlapped by 13 bp/bar on `retrace_leg`. A
   prediction written as a sum of marginal effects will be wrong whenever the effects
   share a mechanism, and this one was.
3. **The fill's effect on a book is not the premium.** `hist_L`'s unfloored book
   *improved* under the open fill by 12 bp/bar while its long leg had been credited +92
   bp a trade. With a target exit the fill changes the book, not just the entry bar.
4. **`rsi` is the better liquid book**, +3.52 with no gap dependence, 14 names to half,
   a 5.5% top trade, and the first here to gain from honest scoring. It gets the next
   record.
5. **Dead names are 44% of `retrace_leg`'s honest P&L.** A dead-inclusive fixture exists
   to include them; that the surviving edge is nearly half in names that later delisted
   is a fact about where structure breakdowns pay, and a risk statement for anyone who
   would trade it.
6. **The rotation null has 24 values and this record says so on every line.** Above 24
   of 24 is the strongest statement the family's null can make, and it is what the
   ordering achieves; it is also the ceiling.

## 9. Files

`data/d341_floor_and_open_fill.json` · `scripts/run_d341_floor_and_open_fill.py` ·
reuses `scripts/d339_universe_floor.py`, `scripts/d340_fill.py`
