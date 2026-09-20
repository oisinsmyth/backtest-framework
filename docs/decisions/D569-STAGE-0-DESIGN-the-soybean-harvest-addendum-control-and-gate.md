# D569 STAGE 0 DESIGN — the soybean harvest addendum: the **always-on control per positioned day**, the **per-month split**, the **placement rank**, a **real-time stocks-to-use rule** and the **COT through the window**, declared before any of them is read

**Stage 0 design. Diagnostic on 2011 → 2023; no pre-registration is produced by it; the 2024+
slice is not read on any source.** Committed before the runner exists, as D567's design was.
Nothing admitted (R15).

*2026-09-20. D567's Stage 0 found the soybean F/H spread widens over September → November in
11 of 13 harvests (t −2.3), most when stocks-to-use is tight, and re-derived the avatar after
the read: a pre-harvest inverse collapsing, the short-bought crusher and exporter as the
constrained party. D568 then showed what a per-window Stage 0 read cannot see — the same
construction held always-on earned more per day than corn's window, December lost 10 of 13, and
the seen stocks-to-use ordering did not survive one declared real-time cut. This addendum puts
those tests on the soybean thread before anything is pre-registered, so that a pre-registration
written "as seen" is at least written on the right object. If the harvest window does not beat
the always-on spread per positioned day, the thread is a drift sampled at harvest and the record
says so.*

**What has been seen, exactly.** From D567's Stage 0 json, for the F/H survival pair over
September → November: the thirteen per-year spread returns (2011 −0.59 %, 2012 **−2.89**, 2013
−0.11, 2014 +0.13, 2015 −0.09, 2016 −0.69, 2017 −0.23, 2018 +0.07, 2019 −0.26, 2020 −0.10, 2021
−0.35, 2022 −0.26, 2023 −1.18), the front's, the August stocks-to-use for each, the formation
basis in cents and its ratio to full carry, the COT commercial net short share at formation, and
the Spearman correlations of each state with each outcome (S/U → spread +0.65, p 0.02; COT net
short → spread −0.61, p 0.03; carry ratio → spread +0.29). The same for the two-month X/F
window. **Not seen:** the daily path; the per-month split; the always-on spread on any month;
the placement null; any real-time rule's composition; the COT's movement *through* the window;
the mean and hit without 2012; any dollar figure. From the seen table a reader can compute by
hand that the gate declared below opens in 2013, 2016, 2021, 2022 and 2023 and is flat in
2014–15 and 2017–20; that composition is therefore disclosed as derivable, and the gate's
*outcome* (its mean and hit on the daily book) is what the addendum reads.

---

## 1. The objects

Both built from the ZS settlement strip through 2023-12-29, D564's five-session formation read.

- **A — the rule-rolled first-nearby spread, always on.** At every month-end, T1 by the grains
  delivery rule (delivery ≥ *m*+2), T2 the next listed; the daily spread return `y = r1 − r2`
  on the pair held through the next month; **sign −1 (short T1, long T2)**. Over September →
  November this holds X/F in September and October and F/H in November. Under the harvest mask
  it is *the window cell*; unmasked it is *the control*. This is the object D568 scored on corn
  and the one a pre-registration would have to be written on, because it exists every month.
- **B — the survival pair, F/H, held September → November.** D567's Stage 0 object, rebuilt on
  the daily book: T1 the first delivery strictly after November (January), T2 March, formed at
  the last session before September and held to November's last session. Reported beside A for
  continuity; it has no always-on analogue and is not the control comparison.

## 2. The tests, with predictions

Predictions are in the runner's quantities. **T1 and T4 decide whether anything follows.**

| # | test | predicted | if it fails |
|---|---|---|---|
| **T1 control per day** | mean return per positioned day of A under the harvest mask, 2011–2023, against A always-on per day, and against A on the off-window months alone | the window **> 1.5 × the always-on** per day, **and** the off-window mean per day **≤ 0** (a short soybean spread earns nothing outside harvest) | the harvest widening is the curve's average; no pre-registration on the schedule |
| **T2 per month** | the 13 September, 13 October and 13 November returns of the window cell | each month pays the short in **≥ 8 of 13**; no single month is **> 60 %** of the window's total | the window is one month; that month is Stage 0 material, not a licence |
| **T3 calendar profile** | A always-on, mean bp a day by calendar month, 2011–2023 | September → November are the three most negative months (the short's best) | a stronger month elsewhere is recorded and not built on |
| **T4 placement rank** | D555's rotation of the harvest mask through 2011–2023, purged 252, enumerated, exact | window cell's rank **≥ 0.90** | the placement is not special; no pre-registration |
| **T5 real-time gate** | open (short) iff the August stocks-to-use (the last WASDE before formation, the new-crop `Proj.`) ≤ the median of every prior August's in the fixture (2010 on; ≥ 3 prior, so the first decision is 2013); one cut, fixed direction | over the eleven decidable windows 2013–2023: the gated windows' mean **more negative** than the ungated mean, **and** their hit (short pays) **≥** the ungated hit | the ordering is real and the cut does not select (corn's outcome); the gate is not carried into any pre-registration |
| **T6 the formation inverse** | Spearman of the August F/H basis (cents) with stocks-to-use; and of the basis with the window return | S/U → basis **> +0.5** (tight stocks, an inverted curve) and basis → window return **> +0.3** (an inverse at formation is what collapses) | the "pre-harvest inverse" avatar is not the mechanism; the widening has another cause |
| **T7 COT through the window** | commercial net short share of open interest at the last report before November's last session, against the last report before formation | **rises in ≥ 9 of 13** (the new crop is hedged into the window); Spearman(change, window return) **< −0.3** (more hedge selling, more widening) | the merchant's harvest selling is not what moves this spread |
| **T8 without 2012** | the window's mean and hit on the twelve years excluding 2012 | mean **≤ −0.25 %**, short pays **≥ 10 of 12** | 2012's drought inverse is the result |
| **T9 tail** | worst positioned month for the short, 2011–2023 | **> −1.5 %** | the spread is not tail-limited on the short side |

Reported beside them, diagnostic: the B object's per-year and per-month returns; the window
cell's gross Sharpe and Sortino on 2016–2023 and 2011–2023 with flat sessions as zeros; a
one-contract dollar line (one ZS a leg, $50 a point, $6 a round trip plus one tick a leg, four
sides a window) — σ per positioned day, net and gross Sharpe / Sortino, total — for information,
not a component line, because a Stage 0 is not a scored construction; the audits of D568 (pair
by a second path, survival, held-contract, lag, sign in money for a *short* spread, right
quantity, gate by a second path), each proven to raise.

## 3. What follows, declared now

- **T1, T4, T5 hold and T7 holds in the avatar's direction:** a pre-registration of A under the
  harvest mask, flat by default, written *as seen* (this addendum and D567's table disclosed),
  with the gate as a secondary cell and ZS's 2024+ slice as the only clean test. The
  pre-registration is the principal's call, not this record's.
- **T1 or T4 fails:** no pre-registration; the soybean harvest widening is recorded as a sampled
  drift and the thread returns to the principal with the numbers.
- **T1 and T4 hold, T5 fails:** the schedule may be pre-registered, ungated; the state variable
  is not carried.
- **T7 fails while T1 and T4 hold:** the schedule may be pre-registered with the avatar recorded
  as unsupported, as D565 was.

**Not licensed by this addendum:** any window other than September → November; any month found
in T3 outside it; any cut other than the one declared in T5; any netting of A and B.

## 4. What is read, and what is not

The ZS settlement strip 2010-06 → 2023-12-29; the breadth fixture for the calendar and the ZS
specification; `data/fixtures/wasde_grains_su.csv` filtered to releases before 2024-01-01
before any use (D568's correction); the COT legacy fixture, commercial category, through 2023.
**Not read: anything from 2024-01-01 onward, on any source.**
