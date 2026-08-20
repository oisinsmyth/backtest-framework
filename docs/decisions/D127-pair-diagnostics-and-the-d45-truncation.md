# D127 — Pair diagnostics are computed locally, and D45's truncation to ETH's inception is reported as the sample definition

**Status:** Committed
**Date:** 2026-08-18
**Category:** Analytics
**Source:** Crypto pairs study session

## Decision

Two small choices that both come down to the same thing — the pairs study does not get to
edit what already exists, so it states what it does instead.

**1. Trade diagnostics are computed in this study, not by extending
`research/trade_diagnostics.py`.**

D112 defines a trade as a **position episode**: flat → long → flat, on one instrument.
That definition is correct for the breakout study and does not describe a pairs book,
which is never "flat then long" on a single leg — it is simultaneously long one leg and
short the other, and it can flip from long-spread straight to short-spread without ever
passing through flat. `extract_episodes` is also a breakout artifact this study is not
permitted to modify.

So `crypto_pairs_study` computes only what a pairs book actually has, from the engine's
own fill stream, and defines each term where it is computed:

- **round trip** — a flat → in-position transition of the *pair*, read off leg A (the two
  legs open and close together by construction: `_targets_for_side` emits `+w` and `−w` in
  one call). A side **flip** never returns to flat, so sign changes are counted too — one
  close and one open on the same bar, which is what it costs.
- **exposure** — the fraction of OOS bars on which the book held a non-zero position.
- **annual turnover** — traded notional ÷ average NAV ÷ years.
- **cost attribution** — fees / borrow / margin, from `research.capacity`'s
  `recording_cost_stack` (D95), reused unmodified.

MFE/MAE, win rate, holding-period percentiles and whipsaw rate are **not** reported. They
are D112's statistics, they are defined against an entry price on one instrument, and
inventing pair analogues of them would be four more conventions to defend for numbers this
study's verdict does not turn on.

One consequence is written into the code rather than left to be discovered: the round-trip
and exposure reconstruction runs **per run segment**. Under chained stitching (D123) each
window is its own `run_backtest` with its own portfolio, so a position open at a window's
end simply *ceases* — there is no closing fill. Reconstructing across the seam from one
cumulative fill stream would carry a phantom position into the next window and undercount
round trips, hiding the very artifact the sensitivity row exists to expose.

**2. D45's inner-join truncation is the study's sample definition, and it is stated in the
report's header.**

Aligning BTC-USD and ETH-USD on exact timestamps (D45/D63) drops every date ETH does not
have, truncating the study at ETH's inception (2017-11-09) and discarding 1,043 BTC bars.
`aligned_series` does this once, and every downstream span — walk-forward windows,
warm-up prefixes, strategy runs, benchmarks — is derived from its output, so the strategy
and its benchmarks cannot disagree about what "the sample" is.

## Rationale

**On the diagnostics.** D112's own rationale is that "a trade is an interpretation" and
that the interpretation should be written down once, in one module, rather than assumed.
Extending that module to cover a second, incompatible interpretation would have made it
two modules wearing one name. Writing a parallel `pair_diagnostics.py` was the other
option and was rejected as premature: four numbers, used by one study, do not need a
package — and if a second pairs study ever wants them, *that* is when the shared module
earns its existence (R1's spirit).

**On the truncation.** This is stated rather than worked around because there is no
version of "working around it" that is honest: forward-filling ETH before it existed
fabricates prices that fills would execute against (D45's exact complaint), and running
BTC's extra history without a counterparty leg is not a pairs trade. The truncation is
*correct* — there is no spread on a day one leg does not exist.

What it costs is comparability, and that is the part worth recording. `BREAKOUT_RESULTS.md`
runs one single-instrument backtest per symbol and therefore keeps BTC's full 2015-onward
history; its own fixture metadata says so explicitly ("NOT inner-joined across symbols").
**The two studies do not cover the same span**, so no return in the pairs artifact is
directly comparable to a BTC-USD row in the breakout one — including through the shared
cost tiers, which are identical by construction (D124) but are being applied to different
samples. The report says this in its header rather than in a footnote, because the two
studies sit next to each other in the repo and a reader will otherwise assume the
comparison is available.
