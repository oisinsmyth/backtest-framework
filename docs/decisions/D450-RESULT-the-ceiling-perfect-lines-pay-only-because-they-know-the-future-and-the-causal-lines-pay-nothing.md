# RESULT D450 — the ceiling: perfect lines pay only because they know the future, the causal lines pay nothing, and steeper trends are *worse* in real time

*Runner `scripts/run_d450_oracle_ceiling.py`; numbers `data/d450_oracle_ceiling.json`; the oracle
page the settings were chosen on is artifact 3216fed4 ("Perfect Hindsight"). Sequel to
[D434](D434-RESULT-the-channel-traded-is-worse-than-re-timing-its-own-trades.md). Nothing is
admitted; nothing is closed — only the principal closes an avenue.*

## 0. What was asked, and what was learned about the question itself

The principal asked for a full-information trendline generator and a study of "what perfect
knowledge would get us", with one constraint: the trading rule may see only the support and
resistance at the current and previous bars, never where a channel starts or ends. The rule:
**in while there is a trend, out when there is not**, a trend being both lines drawn, gradients
of the same sign, both steeper than a swept minimum. No target, no stop.

Two things were established before the run and stand regardless of its numbers:

1. **With perfect hindsight and a dozen dials, tight respected channels are still hard to find.**
   The principal's own settings — `split=greedy seed=5 slack=0 pk=1 tol=1.75 mt=3 basis=wick
   minlen=20 maxlen=1000 mw=0 maxw=24 maxoff=-1 mintd=35 tau=0.4` — give channels 14–16% wide with
   price within ~2% of the nearer line and touching it on about half of bars, covering **62% of
   bars at a median 23 bars long**. His verdict: "not perfect but the best I could do." That is
   evidence about the object, not the estimator.
2. **Withholding the boundaries does not remove the hindsight.** A channel drawn at bar t was
   selected by what happens after t; its *existence* at t leaks the future even when its end is
   never shown. "In while a trend" on oracle lines is therefore a hindsight bet by construction,
   and its numbers are a tautology's numbers. (Recorded as memory `oracle-lines-leak-through-
   their-existence`; the honest oracle trades only beyond the fit window, which this study does
   not do.) The rotation null was dropped for the same reason — asking whether hindsight beats
   random timing is empty — and because it cost more than the study.

So the oracle column below is **not a ceiling on what an estimator could earn**. It is the size
of the tautology. The causal column is the result.

## 1. The comparison, per trade, gross bp — same rule, two line sources, 1,573 names

Oracle: 109,910 channels, length median 23 / p90 34 / max 867, both lines drawn on **69% of
bars**. Causal (D399's `CELL_FINAL`): both lines drawn on **28%**.

Net = gross − the Corwin-Schultz round-trip spread of the names held in that cell (given per cell).
Trim = mean with 1% cut from both tails.

| gmin %/yr | side | ORACLE n | gross | net | spread | trim | median | win | hold | | CAUSAL n | gross | ±SE | net | spread | trim | median | win | hold |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | long | 42,154 | +780 | +718 | 62 | +763 | +613 | 84% | 24 | | 28,740 | **+16.8** | 5.5 | **−58** | 75 | +5 | −125 | 42% | 10 |
| 0 | short | 32,587 | +680 | +613 | 67 | +660 | +470 | 78% | 23 | | 23,866 | **−41.9** | 6.5 | **−126** | 84 | −56 | −222 | 37% | 9 |
| 10 | long | 41,383 | +794 | +731 | 63 | +777 | | | | | 28,740 | +16.8 | 5.5 | −58 | 75 | +5 | −125 | 42% | 10 |
| 10 | short | 31,894 | +696 | +628 | 68 | +675 | | | | | 23,866 | −41.9 | 6.5 | −126 | 84 | −56 | −222 | 37% | 9 |
| 25 | long | 39,107 | +830 | +767 | 64 | +814 | +670 | 86% | 24 | | 28,740 | +16.8 | 5.5 | −58 | 75 | +5 | −125 | 42% | 10 |
| 25 | short | 29,858 | +741 | +672 | 69 | +721 | +534 | 81% | 23 | | 23,866 | −41.9 | 6.5 | −126 | 84 | −56 | −222 | 37% | 9 |
| 50 | long | 34,128 | +909 | +844 | 65 | +893 | +756 | 88% | 24 | | 22,502 | +4.7 | 6.1 | −73 | 78 | −7 | −136 | 41% | 9 |
| 50 | short | 25,802 | +832 | +761 | 72 | +813 | | | | | 18,633 | −39.7 | | −128 | 88 | −55 | | | |
| 100 | long | 25,251 | +1,057 | +988 | 69 | +1,041 | +913 | 91% | 23 | | 13,779 | −9.1 | 8.0 | −94 | 84 | −23 | −145 | 40% | 8 |
| 100 | short | 19,239 | +1,008 | +933 | 76 | +989 | | | | | 11,468 | −31.9 | | −127 | 96 | −48 | | | |
| 200 | long | 15,464 | +1,272 | +1,198 | 75 | +1,258 | +1,142 | 93% | 22 | | 6,581 | −21.4 | 11.9 | −117 | 95 | −38 | −153 | 39% | 7 |
| 200 | short | 12,256 | +1,248 | +1,166 | 82 | +1,229 | +1,063 | 93% | 22 | | 5,751 | −29.1 | 14.4 | −137 | 108 | −47 | −222 | 38% | 6 |

(The causal rows at gmin 0/10/25 are identical because `CELL_FINAL`'s channels already carry a
gradient floor of δ = 1e-3/bar ≈ 29%/yr; the oracle channels do not, so the sweep bites on them.
The oracle's net is its gross less ~8%: at +700 to +1,200 bp a trade, a 60–80 bp spread is
immaterial — which is itself the tell that the number is not an execution result. The spread of
the names held rises with the gradient floor on both sources, 62 → 82 oracle, 75 → 108 causal:
steeper channels live on wider-spread names.)

**Books** (descriptive, no null): oracle long +3,173% / Sharpe 4.5 / exposure 0.27, oracle both
+24,659% / Sharpe 9.2 — the tautology, in money. Causal long **+19.2%, Sharpe 0.29**, exposure
0.115, maxDD −5.7%; causal short **−20.6%, Sharpe −0.62**, maxDD −22.5%; both −5.0%.

Spread of the names held: 74 bp long, 84 bp short round-trip (Corwin-Schultz).

## 2. Reading it

- **The causal long side is positive and small: +16.8 ± 5.5 bp gross (t = 3.1), median −125,
  net −58.** A real but tiny mean carried by a tail, nine times short of its own spread. The short
  side is negative at eight SE. Same shape as D434, with a simpler rule.
- **Steeper is worse, causally — and better, in hindsight.** The oracle's gross rises monotonically
  with the gradient floor (+780 → +1,272 bp) because in hindsight a steep channel *is* a big
  completed move. The causal gross falls monotonically (+16.8 → +4.7 → −9.1 → −21.4) because in
  real time a steep channel is one that has already run: by the time two confirmed pivots a side
  agree on a steep slope, the leg is late. This is the cleanest statement yet of why D434 sat
  below its own rotation null, and it answers the question this study was built for: **the
  value of the channel's direction is a property of hindsight, not of the object.**
- **Coverage is not the gap.** The oracle draws both lines on 69% of bars, the causal on 28%; but
  the causal trades that *do* fire earn nothing, so more of them would not help.
- Top oracle trade: CC 2016-08-10, long, bars 280→362, +8,714 bp — an 82-bar hindsight channel.
  587 trades rejected by the split guard.

## 3. What this does and does not license

It does not say the D399 lines carry no information — only that their *direction*, traded by
holding while the channel exists, carries none in real time on this panel, on two rules now
(D434 with a target and trail, D450 without). It does not close the avenue.

It does say that another exit overlay is the wrong next move, and it says the oracle-as-ceiling
design needs the fit window and the test window to be disjoint before it can bound anything.
The principal's sliding-window suggestion — the oracle's fitter applied to the trailing W bars,
read at the right edge — is now a mode on the oracle page; under the same filters it covers
4% of bars at W = 40 and 18% at W = 20 in runs of one or two bars, which is the estimator cost
made visible before a single trade.

## 4. Audits carried

`[F]` nine states on AA unchanged when every level after the bar is deleted — the rule reads no
boundary in advance. `[S]` the largest up-bar inside a short trade (+3,908 bp) contributes with
the right sign, and the inverted direction is asserted to fail. `[N]` 39,107 long / 29,858 short
oracle trades at the headline floor. Python–page parity of the oracle generator was checked on
three names under the principal's settings before the run (counts, lengths, width, offset and
touch rate identical). No null was run, by the principal's decision and for the reason in §0.
