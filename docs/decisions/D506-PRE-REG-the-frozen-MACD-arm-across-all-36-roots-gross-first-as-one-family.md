# D506 — PRE-REG: the frozen MACD arm across **all 36 roots**, scored **gross first**, as one family

**2026-09-13.** Committed **before the runner exists** ([R8](../RULES.md#r8)) and on its own, to
claim the number.

The principal set both the target and the order:

> *"we need 4 more components, where do we start?"* … *"shouldn't we focus on testing signals then
> building a strategy around them?"*

**The order matters and my first proposal had it backwards.** I proposed an eligibility census
first. This programme's own criterion, recorded at D360, is *"a signal = positive GROSS mean per
trade above the nulls; costs and confluences later"* — and the cost filter has in any case stopped
discriminating, since the fee is now 1.3% of the average NQ move
([D504](D504-the-MACD-arm-across-every-year-the-fixture-holds.md) §4). **So: gross signal first,
cost and C-d afterwards as routing, not rejection.**

---

## 1. Why breadth, and why it has to be different underlyings

The book has one arm at net Sharpe +0.698
([BOOK_PROP](../BOOK_PROP.md), admitted 2026-09-13) and needs four more.
`S_book = S·√k/√(1+(k−1)ρ)`:

| k | ρ=0.0 | ρ=0.1 | ρ=0.2 | **ρ=0.3** |
|---:|---:|---:|---:|---:|
| 5 | 1.56 | 1.32 | 1.16 | 1.05 |
| 10 | 2.21 | 1.60 | 1.32 | **1.15** |
| ∞ | — | 2.21 | 1.56 | **1.27** |

**At ρ = 0.3 no number of arms exceeds 1.27**, and D505 showed the principal's "at most one
negative year in eleven" standard needs ≈ 1.34. **ρ is worth more than count**, and more rules on
NQ will not deliver it: ρ was 0.70 between K8 and the ungated NQ day session, and 0.85 between NQ
and ES on one construction. **Different underlyings is the only route.**

We own `ohlcv-1m` for every CME instrument over 16 years and had scored eight roots. The breadth
fixture (`data/fixtures/fut_breadth_hourly.csv.gz`,
36 roots, 170,643 sessions, `all_gates_pass: True`) is what makes this askable.

## 2. The construction — frozen, not re-tuned

**Imported unchanged** from [D484](D484-RESULT-the-log-MACD-is-a-real-signal-that-fails-only-on-cost-and-the-off-diagonal-ordering-is-confirmed.md)
(signal) and [D491](D491-RESULT-the-first-component-candidate-and-why-it-is-thinner-than-it-looks.md)
(state machine). Not one parameter is fitted here.

- Decide at the **close of each hour** from the root's first day-session hour; execute at the
  **next hour's open**.
- **Enter** when the log Impulse MACD (34/9) and the plain log MACD histogram (12/26/9) **agree in
  sign**; `md == 0` is a no-trade state.
- **Exit** when the signal turns, after a **minimum hold of M = 5 hours**.
- **Forced flat at the close of the root's last day-session hour.**

**The window is per root, from the fixture's derived presence** — h09–h15 for index, metals, rates,
FX and BTC; **h09–h14 for grains and livestock**, whose sessions end ~14:20 ET. A fixed h09→h15
window has 0.1% coverage on grains, so this is not cosmetic. Sessions are filtered on the
fixture's `present` column.

## 3. The primary statistic is GROSS, and the family is 36 cells

| | |
|---|---|
| **primary** | **gross mean per trade, in ticks**, and gross annualised Sharpe of the daily series, per root |
| **family** | the **36 roots** at the frozen spec (AGREE, M = 5). One family, one null. |
| **null** | **circular rotation of the signal**, 2,000 draws, per root — D484's null, which preserves the signal's own autocorrelation where a sign shuffle destroys it (lag-1 ρ = +0.886 on the MACD histogram, and the shuffle's p95 is 1.7× too narrow) |
| **bar** | a root's gross mean per trade must clear **its own** rotation p95, **and** the family maximum must clear the **family-max** null p95, which prices picking the best of 36 |
| reported beside it | net under a stated cost, trips/session, hit rate, median, skew, kurtosis, and the **symmetric 1% trim from both tails** with all three means ([D504](D504-the-MACD-arm-across-every-year-the-fixture-holds.md) §2: I have quoted the one-sided trim twice and it always frightens) |

**Secondary, reported and covered by their own separate family null so they cannot be smuggled
into the primary:** the B1 (impulse only) and B2 (plain only) arms at M = 5, and AGREE at
M ∈ {1, 2, 3}. That is 36 × 5 further cells and **none of them can promote anything** — they exist
to show whether a positive primary cell is a knife-edge or a plateau.

## 4. Cost, stated honestly rather than assumed away

**Commission is $3 a round trip.** **Crossing has been measured on exactly one root** — 1.009
ticks on ES (D471 §1) — and `bbo-1m` covers 41 roots for the trailing year but is not decoded.

So: **gross is the primary and needs no cost assumption.** Net is reported under **one crossed
tick plus $3**, and that figure is **flagged unmeasured for 35 of the 36 roots.** A net column
computed on an unmeasured spread is not evidence and this record will not treat it as such.

**Fourteen of the 22 C-d-passing roots have no micro** and trade at full contract size — the short
Treasury curve, SOFR, all six FX crosses, four grains. Their $3 is a far smaller share of a much
larger tick, which is exactly why gross must lead.

## 5. Window, and what stays unspent

- **In-sample: 2016-01-04 → 2023-12-29**, the ledger's standard window, on all 36 roots.
- **2024-01-02 → 2026-09-09 is NOT read.** It is spent for NQ (D503) and **unspent on the other
  35 roots**, which is where any winner's forward read comes from.
- **2010-06-07 → 2015-12-31 is NOT read.** The index roots' day session is 21–42% covered before
  2016 (D462) so it is unusable for them, but it is **complete for the non-index roots** and is
  therefore a second unspent era for them. Declared here so it cannot later be spent silently.

## 6. Predictions

| | prediction |
|---|---|
| **W-a** | **at least 8 of 36 roots** show a positive gross mean per trade — the signal is real in many places and dies on cost (D495: ES +0.66, GC +0.60, ZB +0.49, CL +1.09 gross, all net-negative) |
| **W-b** | **fewer than 6** clear their **own** rotation p95 on gross |
| **W-c** | the **family maximum does NOT clear** the family-max null p95 — the honest prior, since D468's 24-cell family and D499's 16-cell family both failed theirs |
| **W-d** | NQ's gross figure **reproduces D495's** to within 10%, on a different fixture built by a different builder — the cross-check that the whole breadth exercise rests on |
| **W-e** | the **grains and livestock** (ZC, ZS, ZW, ZL, ZM, LE, HE) are **not** systematically better than the index roots, i.e. the ρ advantage of a new underlying does not come with a free edge |
| **W-f** | among any roots clearing W-b, **pairwise ρ of the daily P&L is below 0.3 for at least one pair that is not two energy or two grain roots** — which is the only result that would actually advance the book |

**I expect W-c to hold, which means I expect this to find no admissible component.** It is worth
running because it is the cheapest possible test of a 36-root universe with a construction already
validated on one root, and because W-f is the question the book actually needs answered.

## 7. Checks the runner must carry

1. **NQ reproduces D495** — asserted, not eyeballed, to within 10% on gross mean per trade. A
   larger gap **raises**, because it would mean the breadth fixture and the committed fixture
   disagree about a root they should agree on.
2. **Per-root windows are taken from the fixture's meta**, and a root whose declared window is not
   populated on ≥ 250 present sessions **raises**.
3. **`net = gross − cost × trips`** asserted exactly, with the trip count identical either way.
4. **The rotation preserves the signal's duty cycle and lag-1 autocorrelation**, and a **shuffle is
   shown to destroy** the latter — the difference the null depends on.
5. **The family-max null covers every statistic the primary reports**, asserted by count.
6. **No session outside 2016-01-04 → 2023-12-29 reaches the P&L path** — a deliberately widened
   window must raise.
7. Every `[X]` break fires on the **scalar** the assertion compares.

## 8. What this cannot do

- **It admits nothing** ([R15](../RULES.md#r15)). A root that clears both nulls is a *candidate for
  a forward read on its own unspent slice*, not a component.
- **It is in-sample and it is a 36-cell search.** The family-max null prices that and nothing else
  does.
- **Net is not evidence here** — see §4. Any claim about tradability waits on `bbo-1m`.
- **It does not test C2 (mean reversion) or C3 (opening range)**, the two named candidates from
  D258 that have never been screened. Those are different signal families and a separate record.
