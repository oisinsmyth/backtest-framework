# D713 DIAG DESIGN — the MES oracle profile of E: which of the hourly short-gamma continuation's trades net a profit at one MES, and where they sit

*2026-09-30. Committed before its runner (`scripts/diag_d713_e_oracle_mes.py`).*
- **The principal:** "No go get me the oracle first … and when presenting those results recap E's design and
  construction".
- **What it is:** a hindsight, descriptive diagnostic. Nothing is fitted, filtered, traded or gated.
- **In-sample:** 2016-01-04 → 2023-12-29. Nothing dated 2024-01-01 or later is read.
- **What it is for:** it is the evidence the principal designs any cut of E from. Any cut chosen is a new
  pre-registration.

## Why

- **D708:** E's side choice is real. It earns +$3.09 a MES trade over the drift (t 3.17), on both legs.
- **But at the only size the account trades (one MES, $4.42 a round trip),** E grosses +$3.16 a trade and nets −$1.26
  (daily Sharpe −0.45).
- **D712's vault pre-registration was withdrawn** on the principal's word: "We can't afford to trade on ES so it
  doesn't matter if its profitable there".
- **The question now:** is there a part of E whose trades clear the MES round trip?

## The candidates (E, unchanged: D708's rule, through D712's rule path)

- **Sessions:** ES sessions with ≥ 380 one-minute bars and G_ES < 0: the ES options book's dealer gamma at the prior
  settlement (D688's construction, D706's worker). There are 859 in-sample.
- **Decisions:**
  - at 10:30, 11:30, 12:30, 13:30 and 14:30 on D689's 5-minute grid, the side is s = sign of the last 60 minutes' log
    move m (m = 0 is no trade);
  - A1: every grid price from the open to t must be finite.
- **The trade:** hold 60 minutes. Gross = s × (P(t+60) − P(t)) × $5; net = gross − $4.42. There are 4,245 trades.
- **Reproduction guard:** the rule path's in-sample T (+$3.0952, 4,245 trades) and its population hash equal D712's
  power output.

## The oracle labels

- **WIN:** net > 0.
- **BAR:** gross ≥ 2 × $4.42 = $8.84 (the expected-profit template's bar).
- **Also given:** the oracle's total (every WIN taken), and each bucket's share of it.

## The profile (every bucket)

**For each bucket:** trades and trades a year; the WIN and BAR rates with their lift; the mean gross with its
day-clustered t; the mean net; the timing term T (the side's move over the per-(year, clock) drift, D708); the mean net
of winners and of losers; and the bucket's share of the oracle's net.

**The buckets:**
1. the clock (five decision times);
2. the side (long, short), and clock × side;
3. **the size of the last hour's move:** |m| / σ_h terciles, where σ_h = the sd of the day-session open-to-close log
   return over the previous 20 sessions × √(60/390), prior-only;
4. today's realised variance to t (the 5-minute grid), terciles;
5. **alignment:** the last hour with or against the day's move from the open to t;
6. **the depth of short gamma:** G_ES quintiles within the population. The SPX GEX sign (G_SUM < 0 or ≥ 0) is a split,
   read from SqueezeMetrics' last row strictly before the day, statistics only;
7. the year; the ES price tercile;
8. clock × |m| tercile.

**Edges:** tercile and quintile edges are taken over all candidates. Hindsight is allowed here; a filter would need
prior-only edges. The runner counts its buckets and reports the expected largest |t| under no effect, so no best bucket
is read without its multiplicity.

## The hold-length profile (descriptive; a different construction, not E)

- **Why:** E pays $4.42 on each of up to five round trips a day. A longer hold spends it once.
- **What is measured:** for the same entries, the side's move held to +60 minutes (E itself), to +120 (capped at the
  16:00 close) and to the 16:00 close.
- **Also measured, one trade a day and not overlapping:** the 10:30 decision held to the close, and the 13:30 decision
  held to the close.
- **For each:** trades a year, mean gross and net at one MES with the day-clustered t, WIN and BAR rates, and the daily
  net Sharpe and Sortino.
- **The overlap with F2:** the to-close holds pass through 15:30 → 16:00, D707's F2 clock. They are descriptive lines
  here, not a trade.

## Output

`data/d713_e_oracle_mes.json`: statistics only, with no per-date GEX.
