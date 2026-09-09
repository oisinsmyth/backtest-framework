# working/leads2/ — external-evidence briefs, ROUND 2

**Commissioned 2026-09-09**, after round 1 (`working/leads/`) returned eleven leads of which three
stand. Six agents, one territory each, researched in parallel.

**The same quarantine contract applies as in [`../leads/README.md`](../leads/README.md)** and is
not repeated here: a brief is evidence about the outside world and never a measurement on this
fixture; citing one in a decision record requires reading the source, because an agent's summary
of a paper is not a reading of the paper; and under [R15](../../docs/RULES.md#r15) they close
nothing and admit nothing. **All six were again commissioned with a deliberate bias toward the
negative.**

| file | territory | why it was chosen |
|---|---|---|
| `F1-index-reconstitution.md` | S&P / Russell membership changes and forced index flows | route (a) — a mandate-driven, date-known, price-insensitive participant, **in large liquid names** |
| `F2-insider-form4.md` | SEC Form 4 insider transactions | best fit between an untouched variable and machinery the programme **already owns** |
| `F3-earnings-dates.md` | earnings on **real announcement dates** — PEAD, the announcement premium | the programme's edge is **overnight**, and earnings print outside market hours |
| `F4-sizing-and-construction.md` | position sizing and portfolio construction | **the programme's own stated gap**, not a new idea — see below |
| `F5-execution-cost.md` | retail IBKR execution and cost reduction | **attacks the binding constraint** rather than adding a signal |
| `F6-corporate-supply-events.md` | lockups, buybacks, SEOs, spin-offs | route (a) — dated, mechanical changes to share supply |

---

## Why these six, and the reasoning is the point

**Two of them are not signal hunts at all, and that is deliberate.**

**F4 exists because the truth file says so, verbatim:** *"Every cross-sectional book is
equal-weighted and nothing has ever been run against it: sizing was never chosen."* Equal weight
is the incumbent **by default rather than by decision**. That is a gap the programme identified
about itself and never closed.

**F5 exists because cost, not signal, is what has actually killed studies here.** The record's own
numbers: a construction that beat its cost bar by 2.41× and died on an 11.36 bp/side breakeven; an
intraday cell where **commission alone was 1.92 bp/side against a 1.06 bp breakeven — it lost at a
zero spread**; and a strategy whose gross was +219.8 bp/trade against a 216.6 bp round trip.
**A basis point saved on execution is worth exactly as much as a basis point of alpha found, and
is very likely easier to get.** Nobody had ever researched it.

**The other four are all route (a)** from the programme's own framing — *somebody buys or sells
for a reason unrelated to price* — because that framing is the record's own answer to why reversal
payoffs keep dying in the spread. F1, F2, F3 and F6 are each a different mechanically-motivated,
calendar-dated participant.

## THE EXCLUSION LIST GIVEN TO EVERY AGENT — this is the durable part of this file

**Round 2 was told, in every prompt, not to re-tread any of:**

credit spreads / yield curve / defensive–cyclical rotation as a regime gate · calendar effects
(turn-of-month, day-of-week, pre-FOMC drift, the even-week FOMC cycle) · short interest,
days-to-cover, borrow fees, FINRA and FTD data · short-term reversal, industry-relative and
residual reversal, return clustering · closed-end fund discounts · lead–lag of every kind (size,
industry, customer–supplier, geographic) · signal combination, ML return prediction, factor-zoo
multiple testing · **options of any kind** · inferring order flow from price action ·
price-level / support-resistance / volume-profile maps · at-the-market shelf issuance ·
XBRL cash runway · merger-arbitrage acquirer shorting · CFTC COT positioning · momentum, wedge
breakouts, MACD, stops and targets.

**Three of those exclusions have specific reasons worth restating:**

1. **OPTIONS ARE ANOTHER SESSION'S TERRITORY.** A concurrent session on `master` is running an
   open-interest density screen (`run_d406_oi_density_screen.py`) and pulling historical options
   snapshots. **Every round-2 prompt forbids options entirely**, including implied volatility and
   earnings-volatility strategies, to avoid duplicating live work.
2. **ATM ISSUANCE, XBRL RUNWAY AND THE MERGER-ARB ACQUIRER** are excluded because
   [`docs/future-strategies.md`](../../docs/future-strategies.md) already reasons all three.
   Re-listing them would double-count the same thinking. They still owe their premise numbers.
3. **TAPE-IDENTIFIED NEWS GAPS ARE NOT EARNINGS DATES.** D360 ran a gap-on-abnormal-volume study
   and found the gapped name *bounces*; its own record says the earnings-date literature *"does
   not"* apply to that construction, because a tape gap is a proxy. **F3 was therefore scoped to
   real announcement dates, which the programme has never held**, and told explicitly not to
   re-analyse gap proxies.

## What round 1 taught that shaped round 2

- **The score did not predict the outcome.** C1 scored lowest of seven and now ranks first; K1 and
  N1 scored 17 and both fell hard. **The failing axis was `KILL`, and it was measuring my
  knowledge rather than the lead.** Round 2 therefore leans on *territories* with a clear premise
  number rather than on pre-scoring.
- **The most valuable returns were not leads.** Round 1's three best results were a hole in the
  programme's floor methodology, a fixture defect on three committed studies, and a withdrawn
  inference — none of them a strategy. **Two of round 2's six were commissioned as method and
  cost work for exactly that reason.**
- **An enthusiastic brief deserves more suspicion than a damning one.** Round 1's most confident
  brief was the one whose headline construction claims did not survive measurement.
