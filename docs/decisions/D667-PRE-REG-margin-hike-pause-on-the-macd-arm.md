# D667 PRE-REGISTRATION — pausing the admitted MACD arm for ten sessions after an NQ margin increase: does it improve the arm beyond what a volatility filter does? A disclosed measurement, which cannot admit anything

*Drafted 2026-09-29 on the principal's word. Committed alone, before its runner exists (R8). **The arm's P&L on any
hike window has not been looked at.** Prop book, measurement only.*

## 0. Why this runs against a closed line, and what it can and cannot decide

**The principal closed conditioning the admitted MACD day-session arm on 2026-09-13** (`BOOK_PROP.md`, after D508, D509
and D512): "any daily-clock conditioner as a ranker of its sessions". A pause after a margin increase is such a
conditioner. The book states why the line was closed: **the arm's 2024+ slice was spent by D503, so no conditioner
found on it can ever be confirmed.** Before this record was written the principal was told this, and ruled:

> "Run it as an overlay anyway, I think the MACD arm has a high chance of being overfitted."

**So this record reopens the line for this one overlay, as a disclosed measurement.**
- **It cannot admit anything.** A pass changes nothing in `BOOK_PROP.md` or `COMPONENTS_PROP.md`. At most it becomes a
  proposal to write the hike pause into a new component's pre-registration, where an unread slice could confirm it.
- **Nothing from 2024 on is read.** The window is 2016-01-04 → 2023-12-29, D508's.
- **What it can inform, given the principal's concern.** Margin increases are dated by CME, not by anything in the
  arm's construction. They are exogenous, high-variance windows (D657: realised variance 1.29 × a pre-notice
  forecast). How the arm behaves in them, against equally volatile windows chosen by its own market's state, is a
  small, independent look at whether its edge depends on the regime it was fitted in. That look is reported as a
  diagnostic (§5), never as a verdict on overfitting.

## 1. The arm, frozen and imported

The admitted arm exactly as `BOOK_PROP.md` specifies it: NQ front month by volume, one MNQ, the day session; decide
at each hour's close from h09 and execute at the next open; enter when the log Impulse MACD (34/9) and the log MACD
histogram (12/26/9) agree in sign; exit when the signal turns after a 5-hour minimum hold; forced flat at h15; cost
$3.50 a round trip. **It is imported, not rebuilt,** through `scripts/run_d508_stretch_ranker.py`'s `load_arm()` (D504's
build, D491's simulator), which scores only 2016-01-04 → 2023-12-29. **The runner first asserts the reproduction D508
recorded: 1,876 sessions and $15,423 net.** Each session starts and ends flat, so pausing a session (setting its P&L to
zero) is clean.

## 2. The overlay

- **Events:** every NQ front-month maintenance increase of at least 5 % in `data/d657_margin_changes.csv` (D657's
  builder, commit `6e9418d`), mapped to the first arm session on or after its date E, merged when within 10 arm sessions
  of the last kept (dated by the first). 12 increases fall in the window before merging.
- **The pause:** no trade on sessions **E+1 … E+10**. The new margin binds from E+1, and CME announces at least
  24 trading hours ahead, so the rule is causal.
- **Coverage:** the margin history covers 2016-01-04 → 2017-11-07 and 2020-06-30 → 2023-12-29 for NQ. In the gap no
  increase is known, so the overlay never acts there. **The nulls place pauses only inside covered sessions**, so both
  sides of every comparison can act in the same sessions.

## 3. The statistics

**Primary: Δ = net annualised Sharpe of the paused arm − net annualised Sharpe of the base arm**, over all 1,876
sessions (a paused session counts as a zero-P&L session). Beside it, for base and paused: net and gross Sharpe and
Sortino, total net P&L, maximum drawdown on the cumulative dollar curve, the worst day, trade count, and P3a
(breaches a year) and P3b (life cost) from `backtest_framework.validation.hurdle_p.p3`. Also the net P&L removed by
the pause (the sum over paused sessions: negative means pausing helped).

**N1, the exact rotation null.** The pause mask, restricted to covered sessions, is shifted cyclically by every
offset k = 1 … n−1 over the covered-session sequence and Δ is recomputed at each. It is enumerated, so it carries no
sampling error. Rank, p50 and p95 are reported. It keeps the pause's block structure (runs of ten) and asks whether
hike-dated pauses beat pauses at arbitrary dates.

**N2, the volatility-matched null.** For each event, candidate start sessions on NQ in the same within-window quintile
of trailing 20-session realised volatility (from NQ's daily closes, `load_arm()`'s `level_all`, reading only closes up
to and including the candidate) and with the same sign of the trailing 20-session return, at least 20 sessions from
any NQ margin change, and with their ten-session pause inside covered sessions. 2,000 draws of one start per event,
seed 667; Δ per draw. p50, p95 and the p95's bootstrap SE are reported. It asks whether the hike adds anything to
"pause when NQ is this volatile".

| bar | declared |
|---|---|
| **B1** | Δ > 0 |
| **B2** | Δ > N1's p95 (exact) |
| **B3** | Δ > N2's p95 by more than 2 of its bootstrap SE (within 2 SE is UNRESOLVED) |
| **B4** | the paused arm's P3a (breaches a year) is no higher than the base arm's |

**All four → "the hike pause improves the arm beyond a volatility filter, in sample"**, recorded as a measurement and
at most proposed for a new component's pre-registration. Otherwise, the overlay is not supported on this arm.

**Power, stated before the run.** About 12 events before merging, so about 100–120 paused sessions of 1,876 (≈ 6 %).
The spread of N1 sets the smallest Δ this can tell from chance, and the runner prints it before Δ.

## 4. Predictions

1. |Δ| < 0.10 Sharpe.
2. **B2 fails**: Δ sits inside N1's range.
3. **B3 fails**: the volatility-matched null does as well as the hike pause.
4. The arm's net P&L standard deviation on paused sessions is at least 1.2 × its standard deviation elsewhere (D657's
   variance increase).
5. The arm's mean net P&L on paused sessions is not distinguishable from its mean elsewhere (|t| < 2).

## 5. Diagnostics (not bars)

The arm's mean net P&L, standard deviation, hit rate and trade count on paused sessions, on N2's matched windows
(pooled over draws) and elsewhere; Δ year by year; the largest single paused session named with its date and P&L
(one session can carry a small sample).

## 6. Files

`scripts/run_d667_hike_pause_overlay.py` (`--selftest`, `--run`) → `data/d667_hike_pause_overlay.json`. The selftest
must show:
- the arm reproduces D508's 1,876 sessions and $15,423 net, and no session after 2023-12-29 is scored;
- the pause covers exactly E+1 … E+10 and merging joins increases within 10 sessions and not beyond;
- a paused session contributes zero P&L, and every other session is untouched;
- N1 enumerates every offset except zero and never places a pause outside covered sessions;
- N2's pool excludes sessions within 20 of any margin change, matches the volatility quintile and trend sign, and
  reads no close after the candidate session;
- the primary can fire: a planted mask pausing the arm's 100 worst sessions gives Δ > 0 above N1's p95, and a planted
  random mask sits near N1's median.
