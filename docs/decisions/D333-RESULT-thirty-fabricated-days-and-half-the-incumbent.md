# D333 RESULT — thirty fabricated days: half the incumbent's book, a quarter of the concentration premium, and five bp/bar off every reversal signal

**Status:** RESULT. Pre-registered at `7e10066`, fix and runner at `3849274` —
both before this file existed (R8).
**Date:** 2026-09-05
**Area:** Data integrity · **every study since the ragged panel (D285+)**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. Every net number since D285 is re-read.**

---

## 1. Thirty dividends dropped, and all thirty are corporate actions

The bound dropped **30 of 35,713** applied dividends (0.08%), on 27 names.
Every one is a day where the events file says the name paid 10% to 352% of
its price and the tape says the price did not fall:

| symbol | date | "dividend" / close | ratio | price move | implied | what it is |
|---|---|--:|--:|--:|--:|---|
| PNK | 2016-04-29 | 38.86 / 11.04 | 3.52× | +0.9% | −77.9% | Pinnacle/GLPI consideration |
| GCI | 2015-06-29 | 18.58 / 14.13 | 1.31× | −5.2% | −56.8% | Gannett/TEGNA spin-off |
| GOCOQ | 2026-07-21 | 0.38 / 0.34 | 1.14× | +8.7% | −53.2% | bankruptcy distribution |
| CLH, MMP | 2011, 2012 | = close | 1.00× | −3.0%, +0.6% | −50.0% | 2-for-1 splits booked as dividends |
| TMUS | 2013-05-01 | 8.10 / 16.52 | 0.49× | **+39.5%** | −32.9% | MetroPCS reverse merger |
| MSGS | 2020-04-20 | 68.06 / 182.44 | 0.37× | +7.8% | −27.2% | MSG Entertainment spin-off |
| BHI | 2017-07-03 **and** 07-05 | 17.50 / 57.68 | 0.30× | +5.8%, 0.0% | −23.3% | GE/Baker Hughes consideration, booked twice |
| RTX | 2020-04-03 | 13.28 / 49.93 | 0.27× | −7.8% | −21.0% | Carrier/Otis spin-offs |
| KHC | 2015-07-06 | 16.50 / 72.96 | 0.23× | *(first bar)* | −18.4% | Kraft special on a stitched series |
| FMC, FWONA, TFCFA, LYB, MFGP, NYRT, TK, TDS, VGR, JILL, CEQP, VSH, NG, AFSI ×2, HOMB, VIAV | | | 0.10–0.75× | flat to −7% | −9% to −43% | spin-offs, returns of value, stitched series |

**Q1 (fewer than 15) is falsified**, and the pre-registered stop condition
for that — *re-examine the ½ tolerance before repricing, and say which cases*
— is answered here: **one case is borderline.** IDT 2013-08-01 fell 48% of
its implied move against a 50% rule; it is a 0.17× event on one bar and may be
a real special dividend partly offset by a rally. Every other drop fell less
than a third of the implied move, most less than a tenth. **The rule stands
as declared**, IDT is named, and the repricing below includes it.

The census (`d333_dividend_census.txt`) had found 62 dividends over 25% of
price and only five inconsistent; the other 25 drops sit between 10% and 25%,
where the census did not look name by name. **Assertion `[D]` checked every
applied dividend at or above 10% against the rule — 105 of them — and all
pass.** HLSS, PENN, BAX and the other real distributions are untouched.

## 2. What the thirty days were worth

`[Z]` proves exactly 30 return cells changed, each by `−log1p(ratio)`.
`[L]` proves the incumbent's *entries* are unchanged (2 of 4,921 differ, via
the volatility-target exit). **Everything below is the same trades, with
thirty bars' returns corrected.**

| cell | PB old → **new** | Sharpe old → new | PUB old → **new** | per trade PB old → new |
|---|--:|--:|--:|--:|
| **incumbent C0, N=2/target, k=5** | +14.57 → **+7.15** | +0.334 → +0.187 | −5.16 → **−12.68** | +9.92 → +0.45 |
| incumbent N=19 | −15.02 → −15.79 | | −37.09 → −37.85 | |
| incumbent N=2 + dv28 | +18.37 → +10.82 | +0.507 → +0.370 | −1.61 → −9.25 | |
| **`retrace_leg` k=20** | +20.91 → **+18.78** | +0.625 → +0.568 | +16.06 → **+13.76** | +48.28 → +36.85 |
| `skew_63` k=20 | +12.60 → +7.02 | +0.421 → +0.314 | +4.97 → −0.58 | +44.83 → +20.05 |
| `dist_lvn` k=20 | +14.96 → +9.55 | +0.379 → +0.280 | +5.47 → +0.04 | +12.46 → −2.36 |
| `rev_21` k=20 | −9.31 → −14.34 | | | +25.99 → +7.48 |
| `rev_5` k=20 | −7.46 → −12.13 | | | |
| `hist_L` k=20 (book) | −3.97 → −4.09 | | | −0.89 → −17.59 |
| `hist_L` **long leg**, per trade | | | | **+97.0 → +63.9** |
| leg-wise LW k=20 | +17.49 → +17.46 | +0.434 → +0.434 | | +63.26 → +44.05 |

**Three things the thirty days were doing:**

1. **Half the incumbent's book.** +14.57 → +7.15 bp/bar, −7.42; under the
   published spread convention −5.16 → −12.68. Its top-1 trade share barely
   moved (14.1% → 14.0%) because VSA — a real mania day — took PNK's place;
   its top-5 share fell 39.8% → 33.2%. **Q2 confirmed.** Its long leg is what
   carried them: `hist_L`'s long leg loses **33 bp per trade**. **Q4
   confirmed.**
2. **A quarter of the concentration premium.** N=2 minus N=19 on the
   incumbent: **+29.59 → +22.93.** A +356% day in a two-name book is +178% on
   the bar; in a nineteen-name book it is +19%. **Q7 falsified** — and STACK
   Axis B's "+21 bp, basis-immune" was partly this. Concentration still wins
   by 23; the *reason* it looked like 30 was fabricated.
3. **Five bp/bar off every reversal-type signal.** `skew_63` −5.6, `dist_lvn`
   −5.4, `rev_21` −5.0, `rev_5` −4.7. **Q6 confirmed, against my own
   mechanism**: I predicted the price-momentum family would hold the jump
   days; it was the *reversal* family. The scores never saw the fake bars —
   they rank on raw closes — but a book that is long a name on a day the
   panel pays +356% collects it whatever the signal.

**Q3 falsified**: `retrace_leg` moves −2.1 / −2.3 bp/bar, not under 1. It was
carrying some of the same days. **It remains the best symmetric book in the
programme** — +18.78 PB, +13.76 PUB — and the only one above +10 under the
published convention; the runner-up on both conventions is now `price_log`,
the known-bad control. **Q5 falsified** for exactly that reason.

## 3. What this establishes

1. **The fixture carried thirty fabricated return days**, +9% to +356%, from
   corporate actions booked as cash dividends with the price left at its
   post-transaction level, and the panel applied them without a bound. Fixed
   in `load_ragged`; every runner inherits it; the derived-array cache is
   keyed on it.
2. **The incumbent's headline since D318 was half data defect.** STACK §0 is
   rewritten a third time.
3. **Concentration's premium was a quarter data defect** and still stands at
   +23 bp/bar.
4. **A concentration report is not finished until the top trade is named and
   its bar is looked at.** D322 reported "six names of 718 make half the
   P&L" and "top-1% of trades = 96.3% of P&L" — rule 3 was followed — and
   the question *which name, which day, is that bar real* was never asked.
   PNK was in that six. **This is now a rule** (FINDINGS §18).
5. **The score cache is stale for three signals.** `beta_63`, `ivol_21` and
   `signed_vol` read `total_log_returns`, and `d290_build_cache.cache_key`
   does not include `ragged_panel.py`. None is in scope here. Owed.

## 4. Predictions

| | | outcome |
|---|---|---|
| **Q1** | fewer than 15 dropped | **FALSIFIED** — 30. §1 re-examines the tolerance as the stop condition requires: one borderline case (IDT), the rule stands |
| **Q2** | incumbent falls ≥ 2 bp/bar; top-1 share < 14.1% *(load-bearing)* | **CONFIRMED** — −7.42; 14.0% (VSA replaces PNK) |
| **Q3** | `retrace_leg` moves < 1 bp/bar | **FALSIFIED** — −2.1 / −2.3 |
| **Q4** | `hist_L` long leg falls ≥ 20 bp/trade *(load-bearing)* | **CONFIRMED** — −33 |
| **Q5** | D323 top-2 unchanged | **FALSIFIED** — `price_log` is now second on both conventions |
| **Q6** | some signal moves > 3 bp/bar *(against)* | **CONFIRMED** — four do, and not the family I named |
| **Q7** | concentration moves < 3 bp/bar | **FALSIFIED** — −6.66 |

Three of seven; both load-bearing confirmed.

## 5. Assertions

All seven pass; all properties of the code, the data, or a prior record.

| | |
|---|---|
| **[C]** | the derived-array cache rebuilt under the bounded panel, bit-identical to a fresh build |
| **[D]** | the dropped set is exactly the inconsistent set; PNK, GCI, CLH, MMP, GOCOQ in it; HLSS, PENN, BAX kept; all 105 applied dividends at ≥ 10% satisfy the rule |
| **[Z]** | exactly 30 return cells changed, one per drop, each by −log1p(ratio); nothing below 10% moved |
| **[S]** | SIGN AUDIT, in money: on the PNK bar a long was paid +356% and a short −356%; now both get +0.9% |
| **[1]** | under the unbounded panel the incumbent and two singles reproduce D332 to 0.0e+00 |
| **[L]** | 4,921 entries old and new, 2 differ |
| **[6]** | raises on a panel handed a free dividend |

**Speed:** 116 s including a 22 s cache rebuild.

## 6. Files

`data/d333_dividend_bound.json` · `scripts/run_d333_dividend_bound.py` ·
`scripts/ragged_panel.py` (the fix) · `scripts/run_d303_reference.py` (the key)
· `scripts/d333_dividend_census.py`, `data/d333_dividend_census.txt`
