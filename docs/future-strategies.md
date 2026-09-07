# Future strategies — ideas, not results

**STATUS: NONE OF THIS HAS BEEN TESTED. NOTHING HERE IS VIABLE, OR SHOWN TO BE.**

Every entry below is an *idea*, reasoned from what the programme has already established
and written down so it is not lost. No entry has a pre-registration, a runner, a null, a
single measured number, or any evidence whatever that it works. **They are not candidates.
They are not in any queue with a date on it.** Read them as hypotheses that survived an
argument, which is a much weaker thing than a result.

Three constraints on anyone picking one up:

1. **Each one needs its premise measured before it is designed.** That rule cost this
   programme two studies to learn — D359 shorted a pool that turned out to rise, and D361
   gated on a state that turned out to forecast the opposite of what the era splits
   suggested. Every entry below carries the one number that would kill it, and that number
   is computed *first*, before a line of the construction is written.
2. **Each one needs a data source the programme does not currently use.** The principal has
   **deferred starting on auxiliary data sources** (2026-09-07). That deferral is the reason
   this file exists instead of a pre-registration.
3. **These ideas have cousins in the published literature.** The reasoning chains here are
   the programme's own and the constructions would be too, but none of the underlying
   phenomena is a discovery. Anyone writing one of these up should say so plainly rather
   than let the derivation read as invention.

**Date reasoned:** 2026-09-07, after D363/D364 closed out the gap-up fade's cost question.

---

## 0. Why these three, and not others — the constraint they were reasoned from

The fade (D361–D364) taught the programme something more general than a verdict on one
signal. **A reversal edge is compensation for supplying liquidity, so its gross is
denominated in the spread and cannot be captured by crossing it.** The evidence is the
arithmetic: on the widest two deciles of the fade's own trades the gross is +219.8 bp a
trade and the round trip is 216.6 — the edge *is* the toll, to the basis point. Selection,
timing, exits and sizing were all tried and moved the net by 4 to 19 bp against a 45 to 90
bp gap, because none of them changes what the payoff is denominated in.

That is a fact about the **payoff type**, not about that one signal. So a tradeable short
needs a payoff that is not liquidity compensation, and there are only two ways out:

- **(a) Somebody sells for a reason unrelated to price.** Then you are ahead of a known
  flow rather than absorbing risk, and you are not being paid the spread for the service.
- **(b) The move is large and slow relative to the spread.** Then the toll is a rounding
  error rather than the whole payoff. The fade tried to earn 61 bp in a name that costs 100
  to touch; inverting that ratio is a design choice, not a discovery.

All three ideas below come from asking one of those two questions. All three deliberately
**leave the price-and-volume tape**, because the record's short side is now exhausted on it:
levels fail (D352), loser rallies fail (D359), news gaps reverse (D360), and the one
construction that clears its nulls does not clear its costs (D361–D363).

---

## 1. The issuer as the marginal seller

**Route (a) — forced supply.**

**The reasoning.** Who is *guaranteed* to be price-insensitive? Not a fund: it can wait. The
company itself. A firm running an at-the-market equity program has a treasurer whose mandate
is to raise cash, not to time the tape, and the mechanical consequence is that the company
sells into every rally. That is a seller who appears precisely when the price rises and is
indifferent to value — the cleanest forced supply in equities. And it is disclosed: shelf
takedowns are filed as **424B5 prospectus supplements**, and equity supplements carry the
share counts and ATM mechanics explicitly.

**The construction, as far as it has been thought through.** Short a name with live shelf
capacity after a sharp rally — the condition under which the program is actually being drawn
— and hold weeks rather than days. Announced capacity and realised usage are separable and
both are free: the **filing** gives the capacity, and the **quarterly share count** (`dei`
cover-page facts in XBRL) gives the usage. A construction that uses only the first is
measuring an option the company may never exercise.

**Data.** SEC EDGAR, no key. `scripts/d331_edgar_deals.py` already pulls by form type at
8 req/s with a warm cache, so adding 424B5 and the S-3 shelf it draws on is a form-list
change rather than new machinery. Share counts come from the XBRL company-facts API (§2).

**The premise check that kills it.** Do names with live shelf capacity drift down at all
after a rally, on *this* floored universe? One conditional drift, measured before anything
is designed.

**The diagnostic that distinguishes it from everything already tried.** Its gross should be
**uncorrelated with the held names' spread**. If it correlates, it is another liquidity
premium wearing a costume and it will die exactly as the fade did. This test should be in
the pre-registration, not discovered afterwards.

**The honest risk.** ATM issuers skew small and cheap, so the `keep_v2` floor ($5 and the
dv28 window) may remove precisely the population the idea is about — the same way it removed
the falling losers in D359. Check the survivor count before anything else.

---

## 2. Runway, from the filings

**Route (b) — make the move large relative to the spread.**

**The reasoning.** This attacks the ratio rather than the mechanism. The fade tried to earn
61 bp in a name that costs 100 bp to touch. Invert it: earn twenty percent over two quarters
in a name that costs forty basis points, and the toll is two percent of the payoff instead
of all of it. So the design target is **slow and large**. What falls slowly, largely and
predictably? A company running out of money. Cash divided by quarterly burn is arithmetic,
not opinion, and a firm with under about four quarters of it must dilute, sell assets or
shrink — all three negative per share. The claim would be that the market underreacts
because the number has to be assembled from two statements and nobody is paid to do that for
small caps.

**The construction, as far as it has been thought through.** Rank the universe on runway
quarters at each filing date; short the bottom; hold to the next filing. A cross-sectional
rank on a quarterly clock, which is a different object from every event book in this record.

**Data, and why it fits this programme's standards unusually well.** The SEC's **XBRL
company-facts API** is free and needs no key, and **every individual fact carries its own
filing date**. That solves look-ahead exactly: rank on the value from the day it became
public, never the period it describes — which is R9's requirement satisfied by the data
itself rather than by a convention. A bulk archive exists for a universe this size.

**This would be the first non-price data the programme has ever used.** That is worth
something independent of whether the signal works, because every finding in `FINDINGS.md` is
currently a statement about one OHLCV panel.

**The premise check that kills it.** D359's lesson applied in advance: does the
bottom-runway decile actually drift down on the floored universe, or does the floor remove
the names that fall? One number, before any design.

**The honest risk.** The most crowded of the three among quantitative funds, and cash-burn
names sit at the floor's edge by construction. Also, a runway measure is a ratio of two
noisy XBRL fields across inconsistent taxonomies — the assembly is the work, and a
mis-assembled denominator would produce a beautiful and completely fictitious rank.

---

## 3. The arbitrageur's hedge

**Route (a) — forced supply, a different forced seller.**

**The reasoning.** Back to who must sell for a non-price reason. In a **stock-for-stock
merger**, every merger-arbitrage fund that buys the target must **short the acquirer** to
hedge the exchange ratio. That short is sized by the deal, dated by the deal calendar, and
entirely indifferent to whether the acquirer is cheap. It appears on announcement and
unwinds at closing. So there is a known quantity of mechanical selling, in a named stock,
over a known window — the three things every other short idea in this record lacked.

**The construction, as far as it has been thought through.** Short the acquirer from
announcement, hold to closing or to a fixed window, whichever the event count supports.

**Data — and the programme already owns it.** D331 pulled **1,719 deal filings** into
`data/fixtures/us_shorts_daily_raw_deals.json`, and the F0 filter currently **excludes both
sides**, because the record learned that targets are pinned. The acquirer of a stock-financed
deal is the unexplored half. It is identified by the **S-4** the acquirer files to register
the shares it will issue, alongside the 425 communications the puller already handles.
**This is the only one of the three ideas that needs no new data source at all** — which is
why it is the one to take first if any is taken.

**Why the cost problem is smallest here.** Acquirers are large. The spread is narrow, and
the `keep_v2` floor works *for* this population rather than against it — the only idea here
of which that is true.

**The premise check that kills it.** A count, not a return: how many stock-financed deals
with an identifiable acquirer sit in the fixture. **If it is under about a hundred, the
study is not worth writing**, and that should be said before anything is built.

**The honest risk.** Event count is the binding constraint, and stock-financed deals are a
minority of deals. Acquirer underperformance is also well documented, so the honest framing
is not "does the acquirer fall" but "does the *arb-flow window* add anything to a known
effect" — a harder and more specific question, and the pre-registration has to ask that one.

---

## What would have to be true before any of this becomes a record

1. The principal decides to open an auxiliary data source. Until then this file is a note.
2. The premise number named in the entry is computed and points the right way.
3. A pre-registration is committed before the runner exists (R8), with the entry's own
   distinguishing diagnostic in it — for §1 the spread-correlation test, for §3 the
   separation from the known acquirer effect.
4. The signal criterion is the principal's (R15): **a positive gross mean per trade above
   its nulls**, with cost reported beside it and tuned afterwards.

**Nothing in this file has cleared step 2.** No entry has been measured at all.
