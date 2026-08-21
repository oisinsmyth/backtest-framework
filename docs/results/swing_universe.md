# swing_k2 vs trail_10 on coins this study did not choose

**Produced:** 2026-08-21 ·
**Snapshot:** `75e1bbbfb10d70b64cb87a9ada00937e4bc00817340e9e671fc554237b847b5f` ·
**Reproduce:** `uv run python scripts/run_swing_universe.py` (offline, deterministic)

## What this is, and what it deliberately is not

`swing_k2` was found on BTC/ETH as the **25th of 25 configurations** (D173). It beat
`trail_10` on both symbols — a real result, and also exactly what searching 25
configurations produces by chance often enough to be worth nothing on its own. That book's
deflated Sharpe is 0.04–0.54: no demonstrated edge.

So this is **not** another sweep. Two configurations, fixed before they met this universe
(D141), differing only in the stop, run unchanged across the D140 cross-section — a
mechanically-screened universe built to contain the coins that **failed**, not the ones
that survived to be worth studying. The only question asked is whether the challenger
beats the incumbent, and whether that holds among the coins that collapsed as well as the
ones that lived.

Short book throughout: SMA200 regime gate, inverse-vol sizing capped at 1.0, and borrow
charged at 10%/yr. Reference tier `taker_40bp`.

## The result, by cohort

| Status | Symbols | `swing_k2` wins | Win rate | Mean Δ Sharpe | Median Δ Sharpe |
|---|---|---|---|---|---|
| ALL | 62 | 43 | 69% | +0.035 | +0.049 |
| collapsed | 41 | 29 | 71% | +0.033 | +0.049 |
| delisted | 2 | 2 | 100% | +0.103 | +0.103 |
| survived | 19 | 12 | 63% | +0.033 | +0.061 |

**The claim survives contact with coins it was not fitted on.** `swing_k2` beats `trail_10` on 43 of 62 symbols (69%), mean Δ Sharpe +0.035, and the win rate is above half in **every** cohort — including the coins that collapsed or delisted, which are the ones a BTC/ETH study never sees. That is the first evidence in this project that the effect is a property of the stop rather than of the two instruments it was found on. It is evidence, not proof: the cross-section is not independent (these coins move together), so the effective sample is smaller than the symbol count suggests.

## And now the number that matters more

A win rate is a RELATIVE statistic. It says `swing_k2` is the better stop; it says nothing
about whether either is worth running. The absolute P&L says that, and it is brutal.

| Stop | Median total return | Mean, excluding blow-ups | Mean Sharpe | Profitable symbols |
|---|---|---|---|---|
| `trail_10` | -56.1% | -45.8% | -0.395 | 6 / 62 |
| `swing_k2` | -50.5% | -40.6% | -0.360 | 5 / 62 |

**The median is the headline and the mean is not.** The unadjusted mean return is dominated by 3 symbol(s) that lost more than the entire account, so the column above excludes them and the next section names them.

**The median coin loses roughly half the account.** `swing_k2` is consistently the better
of two stops on a book that is profitable on a handful of coins out of sixty-two — and it
posts *fewer* profitable symbols than `trail_10` while beating it on average, which is the
shape of a rule that trims the middle of the distribution rather than finding winners.

Read the two sections together and the honest summary is: **the stop is real, the strategy
is not.** Nothing here rescues a book whose deflated Sharpe on BTC/ETH is 0.04–0.54.

## 3 coins destroyed the account, and the engine let them

| Symbol | Status | `trail_10` return | `swing_k2` return | `swing_k2` max DD |
|---|---|---|---|---|
| `USTC-USD` | collapsed | -1,105.7% | -1,105.7% | 321.3% |
| `LUNC-USD` | collapsed | -165.8% | -167.1% | 125.3% |
| `LUNA1-USD` | delisted | -148.5% | -149.5% | 119.4% |

These are Terra. Shorting a collapsed, near-zero-priced coin that then rallies multiples
loses many times the notional, and the worst here is **-1,106%** — the book
lost eleven times the account it started with.

**The stops were active and did not prevent it, which is the point.** An intrabar stop
(D170) exits the moment price touches the level; it cannot help when the instrument opens
five times higher, and it cannot help at all once repeated losses have taken NAV negative
and the book is still trading.

**The engine models no margin call, no liquidation and no borrow recall (D175).** A real
venue would have closed these positions — probably at a terrible price, but it would have
closed them — and a real borrow desk would have recalled the shares long before. Every
short number in this project is optimistic for that reason, and the optimism is largest
exactly where the instrument is most violent, which is exactly where a short book looks
most attractive.

This is the single most important thing the universe test found, and it was not what the
test was looking for.

## Every symbol

| Symbol | Status | `trail_10` Sharpe | `swing_k2` Sharpe | Δ | Trades |
|---|---|---|---|---|---|
| `MATIC-USD` | delisted | -0.16 | +0.04 | **+0.197** | 27 |
| `STEEM-USD` | collapsed | -0.40 | -0.24 | **+0.160** | 51 |
| `ETC-USD` | collapsed | -0.76 | -0.61 | **+0.157** | 50 |
| `ZEC-USD` | survived | -0.74 | -0.58 | **+0.154** | 51 |
| `SUSHI-USD` | collapsed | -0.40 | -0.25 | **+0.148** | 32 |
| `NEAR-USD` | collapsed | -0.64 | -0.50 | **+0.137** | 33 |
| `BSV-USD` | collapsed | -0.73 | -0.59 | **+0.136** | 45 |
| `EGLD-USD` | collapsed | -0.53 | -0.40 | **+0.134** | 34 |
| `YFI-USD` | collapsed | -0.43 | -0.30 | **+0.130** | 34 |
| `FTT-USD` | collapsed | -0.20 | -0.08 | **+0.122** | 32 |
| `ONT-USD` | collapsed | -0.32 | -0.20 | **+0.119** | 50 |
| `XRP-USD` | survived | -0.73 | -0.62 | **+0.115** | 44 |
| `SOL-USD` | survived | -0.29 | -0.18 | **+0.113** | 23 |
| `LTC-USD` | survived | -0.83 | -0.71 | **+0.113** | 55 |
| `BTC-USD` | survived | -0.47 | -0.38 | **+0.100** | 35 |
| `NEO-USD` | collapsed | -0.25 | -0.16 | **+0.098** | 49 |
| `SNX-USD` | collapsed | -0.39 | -0.29 | **+0.096** | 38 |
| `FIL-USD` | collapsed | -0.59 | -0.49 | **+0.095** | 40 |
| `VET-USD` | collapsed | -0.64 | -0.55 | **+0.093** | 43 |
| `ETH-USD` | survived | +0.21 | +0.30 | **+0.093** | 28 |
| `XMR-USD` | survived | -0.46 | -0.37 | **+0.091** | 32 |
| `ZRX-USD` | collapsed | -0.49 | -0.40 | **+0.085** | 50 |
| `BCH-USD` | survived | -0.44 | -0.36 | **+0.081** | 41 |
| `SNT-USD` | collapsed | -0.42 | -0.35 | **+0.073** | 51 |
| `BNB-USD` | survived | -0.51 | -0.44 | **+0.072** | 34 |
| `AXS-USD` | collapsed | -0.00 | +0.06 | **+0.064** | 32 |
| `MKR-USD` | survived | -0.70 | -0.64 | **+0.061** | 38 |
| `QTUM-USD` | collapsed | -0.33 | -0.27 | **+0.058** | 52 |
| `MANA-USD` | collapsed | -0.68 | -0.63 | **+0.055** | 50 |
| `SAND-USD` | collapsed | -0.26 | -0.21 | **+0.052** | 31 |
| `CRV-USD` | collapsed | -0.96 | -0.91 | **+0.049** | 36 |
| `ADA-USD` | survived | -0.49 | -0.44 | **+0.049** | 46 |
| `ICX-USD` | collapsed | -0.11 | -0.06 | **+0.049** | 50 |
| `HT-USD` | collapsed | -0.18 | -0.13 | **+0.044** | 34 |
| `OMG-USD` | collapsed | -0.18 | -0.14 | **+0.044** | 51 |
| `LSK-USD` | collapsed | -0.39 | -0.35 | **+0.038** | 54 |
| `THETA-USD` | collapsed | -0.65 | -0.62 | **+0.025** | 46 |
| `SC-USD` | collapsed | -0.23 | -0.21 | **+0.024** | 51 |
| `LINK-USD` | survived | -0.72 | -0.71 | **+0.013** | 37 |
| `LUNA1-USD` | delisted | -0.03 | -0.02 | **+0.009** | 6 |
| `DASH-USD` | collapsed | -0.36 | -0.35 | **+0.006** | 55 |
| `LUNC-USD` | collapsed | +0.05 | +0.06 | **+0.006** | 44 |
| `BTG-USD` | collapsed | -0.39 | -0.39 | **+0.004** | 47 |
| `USTC-USD` | collapsed | -0.25 | -0.25 | **+0.000** | 54 |
| `DOT-USD` | collapsed | -0.75 | -0.76 | **-0.007** | 38 |
| `EOS-USD` | collapsed | -0.41 | -0.42 | **-0.010** | 56 |
| `HBAR-USD` | survived | -0.09 | -0.13 | **-0.036** | 29 |
| `ALGO-USD` | collapsed | -0.88 | -0.92 | **-0.040** | 37 |
| `OKB-USD` | survived | -0.76 | -0.80 | **-0.041** | 23 |
| `TRX-USD` | survived | -0.42 | -0.47 | **-0.044** | 27 |
| `CRO-USD` | survived | +0.02 | -0.04 | **-0.059** | 35 |
| `BAT-USD` | survived | -0.75 | -0.81 | **-0.062** | 51 |
| `AVAX-USD` | collapsed | +0.36 | +0.29 | **-0.071** | 23 |
| `DOGE-USD` | survived | -0.48 | -0.55 | **-0.072** | 45 |
| `XTZ-USD` | collapsed | -0.54 | -0.62 | **-0.077** | 55 |
| `XEM-USD` | collapsed | +0.20 | +0.12 | **-0.077** | 45 |
| `SRM-USD` | collapsed | -0.23 | -0.31 | **-0.080** | 36 |
| `XLM-USD` | survived | -0.38 | -0.50 | **-0.114** | 47 |
| `WAVES-USD` | collapsed | +0.09 | -0.03 | **-0.117** | 47 |
| `KSM-USD` | collapsed | -0.43 | -0.56 | **-0.126** | 39 |
| `ATOM-USD` | collapsed | -0.28 | -0.42 | **-0.140** | 33 |
| `REP-USD` | collapsed | -0.28 | -0.47 | **-0.194** | 46 |

## Standing caveats

1. **This tests one claim, not the strategy.** The short book has no demonstrated edge on
   BTC/ETH and nothing here changes that. A stop that improves a losing book makes it lose
   less; it does not make it win.
2. **The universe is screened, not curated.** `UniversePolicy` admits on tradability and
   data adequacy only — no return, Sharpe, drawdown or trade count enters it (D140). But
   it is still a universe someone assembled, and the coins in it are the ones a provider
   still serves bars for.
3. **Borrow at a flat 10%/yr is generous here.** Borrowing a
   small-cap altcoin to short it, in the size and at the moment you would most want to,
   is frequently impossible at any rate. Every short number in this document is optimistic
   for that reason and the effect is largest exactly in the collapsed cohort.
4. **One configuration each, no per-symbol tuning** (D141). That is what makes this an
   out-of-sample test rather than a second search.
5. **No margin call, no liquidation, no borrow recall (D175).** Three accounts in this
   run went past −100% and kept trading. A real venue would have closed them. Until that
   is modelled, no short result in this project describes a loss a trader could actually
   have taken.
6. **The cross-section is not independent.** These coins move together, so 62 symbols is
   far fewer than 62 independent tests and the win rate's effective sample is smaller
   than it looks.
