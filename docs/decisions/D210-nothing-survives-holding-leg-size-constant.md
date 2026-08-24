# D210 — nothing survives holding leg size constant

**Status:** Committed (H1–H4 and H6 confirmed; no component promoted)
**Date:** 2026-08-24
**Category:** Signals & strategy interface
**Source:** WP4 of `New Docs/STRUCTURE_MODEL.md` (D204), after D209's correction

## The result

**No component of the strategy predicts anything once leg size relative to ATR is held
constant.** Not the change of character, not the flipped level, not the golden ratio, not
the fair value gap, not RSI.

Three of them looked like candidates on the way there, and taking that back is the work.

## Step 1 — three features clear the promotion criteria

On the annotation population (every setup evaluated independently — 3,875 and 3,753 trades,
not the 275 the one-position-at-a-time book gives):

| feature | BTC rho / verdict | ETH rho / verdict |
|---|---|---|
| `fib_depth` | +0.183 / NO | +0.178 / NO |
| `gap_distance_atr` | −0.214 / **CANDIDATE** | −0.205 / **CANDIDATE** |
| `atr_to_golden` | −0.243 / **CANDIDATE** | −0.246 / **CANDIDATE** |
| `rsi` | −0.019 / NO | −0.022 / NO |
| `stop_atr` | −0.307 / **CANDIDATE** | −0.301 / **CANDIDATE** |
| `bars_waited` | −0.059 / NO | −0.043 / NO |

Three candidates, both symbols, same signs, under criteria this project committed to long
before this study existed. Read alone that is the strongest positive result the structure
programme has produced.

## Step 2 — they are one quantity under three names

Pairwise rank correlation between the candidates:

| | BTC | ETH |
|---|---:|---:|
| `atr_to_golden` ~ `stop_atr` | **+0.87** | **+0.88** |
| `gap_distance_atr` ~ `atr_to_golden` | +0.82 | +0.83 |
| `gap_distance_atr` ~ `stop_atr` | +0.79 | +0.80 |

`stop_atr` is leg size relative to ATR. `atr_to_golden` is a distance to a fixed *fraction*
of the same leg, in the same ATR units. `gap_distance_atr` is a distance to a level inside
it. They are the same measurement.

**And MFE is expressed in R, so `MFE_R = excursion / risk` correlates with leg size
arithmetically.** A trade whose risk is small relative to the volatility that drives its
excursions has a large MFE in R whether or not anything about it was predicted. All three
"candidates" are reporting that identity.

This matrix was not planned. It was added because three verdicts came back with
suspiciously similar signs and magnitudes, which is the same instinct that produced every
census in this programme.

## Step 3 — the control that settles it

Rank each feature inside **stop-width quintiles**, holding leg size roughly constant and
letting the feature vary:

| | largest \|rho\| in any bucket, any feature | signs agree across buckets |
|---|---:|---|
| `BTCUSDT` | **0.13** | none |
| `ETHUSDT` | **0.13** | none |

Against a promotion bar of 0.2. **Every feature collapses, depth included.** Not one holds
its sign across all five buckets.

Contrast with the depth control, which was the natural one after D208: there
`gap_distance_atr`, `atr_to_golden` and `stop_atr` all still cleared 0.2 with agreeing
signs. Depth was the wrong nuisance variable — or rather, it was *a* nuisance variable and
not *the* one. Leg size is the one, and it subsumes depth: `fib_depth` reaches 0.07 inside
stop-width buckets.

## The lattice agrees, and adds one thing

All 8 subsets of {C2, C3, C4}, frozen wrapper, identical setups:

- Median entry depth rises from **0.308 to 0.538** (BTC) as filters stack. That is the
  filters' only reliable effect, exactly as D206's census predicted.
- **At zero cost the fully-stacked arm earns −0.038R and −0.102R a trade against the base
  arm's +0.013R and +0.093R.** Stacking all four filters makes the strategy *worse* before
  costs are even considered.
- At 40 bps every arm loses. Median net R on the base arm is −1.38 and −1.19, with **44%
  and 32% of its trades untradeable outright** — the round trip costs at least their entire
  risk.

The zero-cost diagnostic is doing its D202 job: this is not "information the costs ate".
The base arm earns +0.013R a trade with no costs at all. There was nothing to eat.

## Two method notes, both of which changed a result

**MFE had to move into R units.** The first run expressed it as a fraction of the entry
price and `stop_atr` came back a CANDIDATE at rho +0.56 — an artifact of ranking a
scale-dependent quantity across a fixture running from \$3,000 to \$100,000 and two assets.
That is D187's lesson in a new costume. The R form is scale-invariant and is asserted so by
test.

**The annotation population had to allow overlap.** The one-position-at-a-time rule is
correct for a book and threw away 93% of the sample for a rank statistic — 3,875 setups
became 275 trades. A book and a sample are different objects and the code now says which it
is producing.

## Predictions, scored

- **H1** (CHoCH fails its null) — confirmed. Also fails to add anything conditionally.
- **H2** (0.618 no better than matched placebos) — confirmed by D208 and again here:
  `atr_to_golden` survives nothing.
- **H3** (FVG fails) — confirmed twice, by D208's depth-matched null and by the stop-width
  control here.
- **H4** (flipped level fails, consistent with D196) — confirmed.
- **H5** (stacked arm underpowered) — falsified by D206; 118 and 104 trades.
- **H6** (RSI at least as good as the structural components) — confirmed, and now moot:
  RSI reaches 0.07 inside stop-width buckets, which is the same nothing everything else
  reaches.
- **H7** (verdict stable across the grid) — WP6's question, not yet run.

## The stop condition applies

`STRUCTURE_MODEL.md` fixes it: *"no component clearing the promotion criteria ends the
programme here as a reportable negative; WP5 does not run."*

No component clears them under the control that matters. **WP5 does not run**, and the
remaining work is WP6's discretion audit and the final report.

That stop is worth honouring rather than arguing past. The temptation is real — three
features cleared the unconditional bar, and a costed backtest of them would produce a
number. D203 is the record of where that path goes: five refinements, each better than its
predecessor, none of them moving the null.
