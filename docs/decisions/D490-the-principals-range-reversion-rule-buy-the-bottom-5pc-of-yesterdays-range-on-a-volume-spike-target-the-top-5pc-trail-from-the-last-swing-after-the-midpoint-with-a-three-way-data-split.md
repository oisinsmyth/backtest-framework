# D490 — the principal's range-reversion rule: buy the bottom 5% of yesterday's range on a volume spike, target the top 5%, trail from the last swing once past the midpoint; short symmetric; a three-way data split so selectivity filters can be added later

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. The
construction is the principal's, stated on 2026-09-12 and fixed here verbatim in its mechanics;
the parameters it names (5%, the volume spike, the midpoint, the swing) are declared once and
not searched. D490 taken after `ls docs/decisions` and `git log --all` on both worktrees showed
D488–D489 used by the other session.

## 0. Why, and the data split the principal asked for

D487 measured the index tape as **mean-reverting intraday in 2016, 2017 and 2019** (variance
ratios 0.86–0.97) and reverting on NQ the day after large moves. A rule that buys the extreme of
yesterday's range and sells the other extreme is the natural construction for that, and it has
the prop shape: intraday, flat by the close, a high hit rate if the reversion is there.

**The principal wants to add selectivity filters later without mining the reserve.** So the data
is split three ways, declared now:

| slice | sessions | use |
|---|---|---|
| **development** 2016-02-01 → 2020-12-31 | ≈ 1,230 | this record; any filter the principal chooses later is chosen HERE, on the splits this record reports |
| **validation** 2021-01-04 → 2023-12-29 | ≈ 750 | touched ONCE per declared filter set, under its own record, with the filter fixed first |
| **final** 2024-01-02 → 2026-09-09 | ≈ 680 | unread; the principal's word; the promotion test |

The development slice starts 2016-02 because the volume normaliser needs 20 prior sessions.
Nothing after 2020-12-31 is read by this record's runner (a gate raises otherwise).

## 1. The construction (the principal's rule, fixed)

On the D462 one-minute regular-hours fixtures, ES (one MES, the candidate) and NQ (one MNQ, the
check root), full 390-bar sessions, single contract per day by construction.

- **Yesterday's range:** the previous full session's regular-hours high `H` and low `L`
  (09:30–16:00). Position of a price `p` in it: `P = (p − L) / (H − L)`.
- **Volume spike:** the one-minute volume at the trigger bar ≥ **2×** the median volume of the
  same minute-of-day over the previous 20 sessions (time-of-day normalised; the open's U-shape
  is not a spike).
- **Long entry:** the first bar of the day, from 09:35, whose close has `P ≤ 0.05` (below
  yesterday's low counts; the subset `P < 0` is reported separately) **and** whose volume
  spikes. Enter at the next bar's open plus one tick (a market order on the trigger).
- **Long exits, whichever comes first:** (i) **target** — the first bar whose high reaches
  `P = 0.95`, filled at that level; (ii) **trailing stop** — armed once a bar's close has
  `P ≥ 0.5` (the opposite half); from then on the stop sits at the **most recent confirmed swing
  low**, a bar whose low is the minimum of the five bars either side (confirmed five bars
  later), and moves only up; exit when a bar's low trades through it, filled at the stop less
  one tick; (iii) **the close** — the 15:59 bar's close.
- **Short:** the mirror image (`P ≥ 0.95` on a spike; target `P = 0.05`; trail from the most
  recent confirmed swing high once `P ≤ 0.5`).
- **One entry per side per day**, no re-entry after an exit; both sides may trigger on one day.
  **No initial stop** — the principal did not specify one; the MAE distribution and the
  one-micro P3 check are reported so that the case for one is made by the data, not assumed.
- **Cost:** $3 a round trip plus the modelled fills above (one tick on the entry, one tick on a
  trailing-stop exit, none on the target or the close).

**Ablation, reported and not a candidate:** the same rule **without the trailing stop** (target
or close only), because the other session's D473 §4 proved a stop/target bracket is neutral on a
driftless walk and the trail's contribution has to be measured, not assumed.

## 2. Statistics (the ledger's line, plus what a filter decision needs)

Per side and pooled: trades, mean and **median** gross and net $ per trade, hit rate, payoff,
holding minutes, exit mix (target / trail / close), MAE and MFE quantiles, skew, the ten largest
and smallest trades named, the symmetric 1%-trimmed mean; **the net Sharpe of the daily P&L on
the session calendar at one micro with its block-bootstrap SE** (C-a's quantity); by year; the
one-micro P3 check (days below −2% of $50k).

**Descriptive splits for the principal's later filter choice** (reported, not gated, not
searched): `P < 0` vs `0 ≤ P ≤ 0.05`; spike size 2–3× vs > 3×; trigger before vs after 11:00;
the day's open inside vs outside yesterday's range; realised-vol tercile (trailing 21 sessions,
causal).

## 3. Nulls (named by what they destroy and keep)

- **N1 — wrong-range control:** the identical rule with yesterday's range replaced by the range
  of the session **five days earlier** (keeps the rule's mechanics, the spike, the exits and
  the count; destroys the specific level). 20 draws over offsets 3–22 sessions; the statistic is
  the gross mean per trade. If reversion is about *yesterday's* extremes the real rule beats
  this; if the exits or the spike do the work, it does not.
- **N2 — random-time entries:** entries at random bars with the same count per day-side and
  the same time-of-day distribution, the same exit rules (target and trail defined on the same
  yesterday's range). Destroys the entry state; keeps the exit machinery. 2,000 draws; p50, p95
  with its bootstrap SE.
- **N3 — sign flip** of the daily P&L for the net Sharpe.

## 4. The bar (declared)

The rule is **worth a validation read** if, on ES in development, the pooled gross mean per
trade is above **both** N1 p95 and N2 p95 + 2 SE, and the net Sharpe at one MES is **> 0.3** on
the point estimate (the ledger's C-a is 0.5; a rule the principal intends to filter is given a
lower first bar, said plainly). NQ reported as the check. Otherwise the rule is recorded and
the principal decides whether a filter is worth designing on the splits.

## 5. Predictions

- **X-a** Triggers: long on **35–50%** of sessions, short on **25–40%** (the market closes
  near yesterday's extremes often; the spike condition halves that).
- **X-b** Long side gross mean **+3 to +10 bp** per trade (ES), hit **52–58%**, exit mix
  target 15–30%, trail 30–50%, close the rest; **short side +0 to +5 bp** (the index drifts up
  against it). Median below the mean on the long side (a right tail from the target).
- **X-c** The trailing stop **raises the hit rate and lowers the mean** against the ablation;
  Sharpe within ±0.1 of it (the other session's neutrality result).
- **X-d** N1 is the binding null: the wrong-range control's mean is **within 2 bp** of the real
  rule's (the exits and the spike, not the level, carry most of it). N2 p95 is cleared by the
  long side.
- **X-e** Net Sharpe at one MES **+0.1 to +0.4**; the bar (0.3) is **not** cleared with
  confidence; 2018 the worst year (trend days through the trail, D487).
- **X-f** `P < 0` entries (below yesterday's low) are **worse** than `0 ≤ P ≤ 0.05`, and
  after-11:00 triggers better than before — the two most likely filters, predicted so the
  splits are checkable.
- **X-g** Runtime under 5 min.

## 6. Files

This record · `scripts/run_d490_range_reversion.py` (`--dev`, `--selftest`; `--validate` and
`--final` exist and refuse without their flags) · `data/d490_range_reversion_dev.json` ·
`data/d490_trades_dev.csv.gz` · RESULT.
