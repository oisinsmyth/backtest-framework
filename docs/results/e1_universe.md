# E1 on 62 coins it was never fitted on

**Produced:** 2026-08-21 ·
**Snapshot:** `75e1bbbfb10d70b64cb87a9ada00937e4bc00817340e9e671fc554237b847b5f` ·
**Reproduce:** `uv run python scripts/run_e1_universe.py` (offline, deterministic)

## What this is

`FailedBreakoutExit(k)` — E1 — exits when the close falls back INSIDE the channel the
entry broke, within k bars. It has cleared the every-symbol bar five times: the long book
at both k (D177), the short book at both k (D178), and the combined ensemble with both
bootstrap intervals excluding zero (D179).

**All five are BTC-USD and ETH-USD.** Correlated passes on two instruments are not
independent evidence, which is why D178 and D179 both named this test rather than another
sweep.

Two configurations per book — baseline, and baseline plus E1 at **k=3** — fixed
before they met this universe (D141), run unchanged across the D140 cross-section: a
mechanically-screened universe built to contain the coins that **failed**, not the ones
that survived to be worth studying. Reference tier `taker_40bp`; the short book
pays borrow at 10%/yr.

**Ties are counted as ties.** E1 is an added brick rather than a swapped one, so on a
symbol where it never fires the two runs are identical and the delta is exactly zero. Win
rates below are over the symbols where E1 actually fired, and both denominators are shown.

---

## The LONG book

| Status | Symbols | E1 fired | Wins | Losses | Win rate | Mean Δ Sharpe | Median Δ Sharpe |
|---|---|---|---|---|---|---|---|
| ALL | 62 | 62 | 24 | 38 | 39% | -0.065 | -0.050 |
| collapsed | 41 | 41 | 14 | 27 | 34% | -0.081 | -0.063 |
| delisted | 2 | 2 | 0 | 2 | 0% | -0.144 | -0.144 |
| survived | 19 | 19 | 10 | 9 | 53% | -0.022 | +0.018 |

**The claim does not survive on the long book.** E1 wins on only 24 of 62 firing symbols (39%), mean Δ Sharpe -0.065. Five passes on two instruments is then most simply explained as two instruments.

**Trade count:** E1 raises the total across the 62 symbols it fires on (1,329 -> 1,732), up on 61 symbols and down on 0. D177 read the long book's rise on BTC/ETH as re-entry; D178 falsified that attribution on the short book, concluding E1's benefit is not sitting in a failed trade. This is the cross-section's read on the same question.

**Absolute P&L — is either arm worth running?**

The win rate above is a RELATIVE statistic. It says whether E1 is the better of two
configurations; it says nothing about whether either makes money. This says that.

| Arm | Median total return | Mean, ex blow-ups | Mean Sharpe | Mean max DD | Profitable symbols |
|---|---|---|---|---|---|
| `baseline` | +152.4% | +338.1% | +0.411 | 49.1% | 52 / 62 |
| `+ E1` | +97.6% | +317.2% | +0.346 | 47.0% | 50 / 62 |

**The median is the headline and the mean is not** — a cross-section of alts has a return
distribution with a tail that eats any average. No symbol drove total return past -100% in this book.

**Sample symbols — the 5 largest gains and 5 largest losses**, by Sharpe
delta, shown in total return so the size of the effect is legible:

| Symbol | Status | Baseline return | + E1 return | Δ return | Δ Sharpe |
|---|---|---|---|---|---|
| `ADA-USD` | survived | +509.2% | +904.7% | +395.4 pp | +0.235 |
| `REP-USD` | collapsed | -38.3% | -2.5% | +35.8 pp | +0.180 |
| `ETH-USD` | survived | +552.2% | +906.1% | +353.9 pp | +0.177 |
| `KSM-USD` | collapsed | +148.3% | +224.4% | +76.2 pp | +0.142 |
| `VET-USD` | collapsed | +308.9% | +452.5% | +143.5 pp | +0.130 |
| … | | | | | |
| `XMR-USD` | survived | +132.5% | +18.8% | -113.7 pp | -0.302 |
| `FIL-USD` | collapsed | +313.4% | +65.5% | -247.9 pp | -0.309 |
| `XEM-USD` | collapsed | +51.4% | -25.0% | -76.3 pp | -0.388 |
| `ICX-USD` | collapsed | +479.1% | +91.0% | -388.0 pp | -0.412 |
| `ZRX-USD` | collapsed | +200.2% | -23.1% | -223.3 pp | -0.591 |

<details><summary>Every symbol (long)</summary>

| Symbol | Status | Baseline Sharpe | +E1 Sharpe | Δ | Trades |
|---|---|---|---|---|---|
| `ADA-USD` | survived | +0.80 | +1.03 | **+0.235** | 24 -> 27 |
| `REP-USD` | collapsed | -0.18 | -0.00 | **+0.180** | 22 -> 26 |
| `ETH-USD` | survived | +0.78 | +0.95 | **+0.177** | 28 -> 30 |
| `KSM-USD` | collapsed | +0.50 | +0.64 | **+0.142** | 14 -> 19 |
| `VET-USD` | collapsed | +0.65 | +0.78 | **+0.130** | 22 -> 22 |
| `XLM-USD` | survived | +0.29 | +0.41 | **+0.114** | 28 -> 33 |
| `BSV-USD` | collapsed | -0.29 | -0.18 | **+0.106** | 20 -> 24 |
| `XRP-USD` | survived | +0.36 | +0.46 | **+0.101** | 27 -> 34 |
| `BTC-USD` | survived | +1.20 | +1.30 | **+0.101** | 38 -> 44 |
| `WAVES-USD` | collapsed | +0.35 | +0.45 | **+0.100** | 24 -> 30 |
| `YFI-USD` | collapsed | -0.13 | -0.04 | **+0.097** | 16 -> 18 |
| `FTT-USD` | collapsed | +0.54 | +0.63 | **+0.093** | 20 -> 22 |
| `BCH-USD` | survived | +0.24 | +0.32 | **+0.080** | 30 -> 38 |
| `LINK-USD` | survived | +0.22 | +0.28 | **+0.065** | 35 -> 45 |
| `SRM-USD` | collapsed | -0.87 | -0.82 | **+0.048** | 13 -> 15 |
| `AVAX-USD` | collapsed | +0.83 | +0.87 | **+0.043** | 15 -> 17 |
| `SC-USD` | collapsed | +0.45 | +0.49 | **+0.039** | 19 -> 25 |
| `OMG-USD` | collapsed | +0.45 | +0.49 | **+0.039** | 21 -> 30 |
| `SUSHI-USD` | collapsed | +0.23 | +0.26 | **+0.033** | 16 -> 20 |
| `BNB-USD` | survived | +0.78 | +0.81 | **+0.027** | 30 -> 36 |
| `DOGE-USD` | survived | +0.55 | +0.57 | **+0.020** | 25 -> 27 |
| `DASH-USD` | collapsed | +0.29 | +0.31 | **+0.020** | 27 -> 34 |
| `SOL-USD` | survived | +0.86 | +0.87 | **+0.018** | 22 -> 25 |
| `HT-USD` | collapsed | +0.58 | +0.59 | **+0.011** | 19 -> 22 |
| `CRV-USD` | collapsed | -0.00 | -0.01 | **-0.010** | 18 -> 27 |
| `EGLD-USD` | collapsed | +0.33 | +0.31 | **-0.015** | 9 -> 12 |
| `MKR-USD` | survived | +0.09 | +0.07 | **-0.021** | 31 -> 41 |
| `EOS-USD` | collapsed | -0.01 | -0.05 | **-0.038** | 23 -> 29 |
| `SNX-USD` | collapsed | +0.80 | +0.76 | **-0.042** | 21 -> 31 |
| `CRO-USD` | survived | +1.17 | +1.13 | **-0.045** | 18 -> 21 |
| `NEO-USD` | collapsed | +0.32 | +0.27 | **-0.049** | 23 -> 27 |
| `BTG-USD` | collapsed | +0.29 | +0.24 | **-0.051** | 21 -> 26 |
| `ATOM-USD` | collapsed | +0.31 | +0.24 | **-0.063** | 20 -> 27 |
| `ETC-USD` | collapsed | +0.43 | +0.36 | **-0.066** | 24 -> 28 |
| `LUNA1-USD` | delisted | +1.88 | +1.81 | **-0.066** | 10 -> 12 |
| `QTUM-USD` | collapsed | +0.24 | +0.17 | **-0.070** | 26 -> 35 |
| `SAND-USD` | collapsed | +0.79 | +0.72 | **-0.074** | 12 -> 14 |
| `ALGO-USD` | collapsed | +0.56 | +0.47 | **-0.083** | 19 -> 26 |
| `STEEM-USD` | collapsed | -0.04 | -0.17 | **-0.127** | 20 -> 25 |
| `HBAR-USD` | survived | +1.03 | +0.89 | **-0.141** | 13 -> 18 |
| `SNT-USD` | collapsed | +0.15 | +0.01 | **-0.142** | 20 -> 28 |
| `USTC-USD` | collapsed | -1.19 | -1.34 | **-0.144** | 10 -> 11 |
| `LTC-USD` | survived | +0.45 | +0.31 | **-0.144** | 42 -> 54 |
| `OKB-USD` | survived | +0.56 | +0.41 | **-0.154** | 25 -> 30 |
| `DOT-USD` | collapsed | +0.20 | +0.04 | **-0.158** | 13 -> 19 |
| `MANA-USD` | collapsed | +0.60 | +0.44 | **-0.162** | 24 -> 31 |
| `LUNC-USD` | collapsed | +0.97 | +0.81 | **-0.162** | 18 -> 24 |
| `BAT-USD` | survived | +0.32 | +0.16 | **-0.164** | 27 -> 40 |
| `TRX-USD` | survived | +0.31 | +0.13 | **-0.177** | 30 -> 40 |
| `AXS-USD` | collapsed | -0.30 | -0.49 | **-0.195** | 12 -> 15 |
| `ONT-USD` | collapsed | -0.27 | -0.47 | **-0.202** | 25 -> 38 |
| `XTZ-USD` | collapsed | +0.47 | +0.27 | **-0.204** | 23 -> 35 |
| `THETA-USD` | collapsed | +0.80 | +0.60 | **-0.206** | 23 -> 34 |
| `ZEC-USD` | survived | +0.76 | +0.55 | **-0.210** | 25 -> 37 |
| `NEAR-USD` | collapsed | +0.74 | +0.52 | **-0.218** | 15 -> 22 |
| `LSK-USD` | collapsed | +0.25 | +0.03 | **-0.221** | 17 -> 25 |
| `MATIC-USD` | delisted | +0.66 | +0.44 | **-0.221** | 19 -> 30 |
| `XMR-USD` | survived | +0.40 | +0.09 | **-0.302** | 23 -> 34 |
| `FIL-USD` | collapsed | +0.56 | +0.25 | **-0.309** | 17 -> 29 |
| `XEM-USD` | collapsed | +0.21 | -0.17 | **-0.388** | 19 -> 30 |
| `ICX-USD` | collapsed | +0.72 | +0.31 | **-0.412** | 17 -> 31 |
| `ZRX-USD` | collapsed | +0.46 | -0.13 | **-0.591** | 22 -> 33 |

</details>

---

## The SHORT book

| Status | Symbols | E1 fired | Wins | Losses | Win rate | Mean Δ Sharpe | Median Δ Sharpe |
|---|---|---|---|---|---|---|---|
| ALL | 62 | 62 | 30 | 32 | 48% | -0.010 | -0.001 |
| collapsed | 41 | 41 | 22 | 19 | 54% | -0.003 | +0.011 |
| delisted | 2 | 2 | 1 | 1 | 50% | -0.046 | -0.046 |
| survived | 19 | 19 | 7 | 12 | 37% | -0.021 | -0.005 |

**The claim does not survive on the short book.** E1 wins on only 30 of 62 firing symbols (48%), mean Δ Sharpe -0.010. Five passes on two instruments is then most simply explained as two instruments.

**Trade count:** E1 raises the total across the 62 symbols it fires on (2,327 -> 2,760), up on 60 symbols and down on 0. D177 read the long book's rise on BTC/ETH as re-entry; D178 falsified that attribution on the short book, concluding E1's benefit is not sitting in a failed trade. This is the cross-section's read on the same question.

**Absolute P&L — is either arm worth running?**

The win rate above is a RELATIVE statistic. It says whether E1 is the better of two
configurations; it says nothing about whether either makes money. This says that.

| Arm | Median total return | Mean, ex blow-ups | Mean Sharpe | Mean max DD | Profitable symbols |
|---|---|---|---|---|---|
| `baseline` | -55.9% | -45.2% | -0.388 | 70.1% | 7 / 62 |
| `+ E1` | -49.5% | -42.3% | -0.398 | 67.9% | 7 / 62 |

**The median is the headline and the mean is not** — a cross-section of alts has a return
distribution with a tail that eats any average. 2 symbol(s) lost more than the entire account (`LUNA1-USD`, `LUNC-USD`), so the mean column excludes them. The engine models no margin call, liquidation or borrow recall (D175) — a real venue would have closed those positions.

**Sample symbols — the 5 largest gains and 5 largest losses**, by Sharpe
delta, shown in total return so the size of the effect is legible:

| Symbol | Status | Baseline return | + E1 return | Δ return | Δ Sharpe |
|---|---|---|---|---|---|
| `SNT-USD` | collapsed | -58.1% | -17.3% | +40.8 pp | +0.282 |
| `BNB-USD` | survived | -58.1% | -29.6% | +28.5 pp | +0.243 |
| `NEAR-USD` | collapsed | -51.6% | -32.7% | +19.0 pp | +0.201 |
| `SOL-USD` | survived | -34.0% | -16.1% | +17.9 pp | +0.161 |
| `ALGO-USD` | collapsed | -57.6% | -47.2% | +10.5 pp | +0.144 |
| … | | | | | |
| `SAND-USD` | collapsed | +9.4% | -9.6% | -19.0 pp | -0.166 |
| `XLM-USD` | survived | -42.4% | -56.5% | -14.1 pp | -0.178 |
| `KSM-USD` | collapsed | -13.2% | -28.7% | -15.5 pp | -0.185 |
| `MANA-USD` | collapsed | -74.5% | -78.1% | -3.7 pp | -0.238 |
| `DOGE-USD` | survived | -61.2% | -70.9% | -9.7 pp | -0.285 |

<details><summary>Every symbol (short)</summary>

| Symbol | Status | Baseline Sharpe | +E1 Sharpe | Δ | Trades |
|---|---|---|---|---|---|
| `SNT-USD` | collapsed | -0.34 | -0.06 | **+0.282** | 48 -> 51 |
| `BNB-USD` | survived | -0.49 | -0.24 | **+0.243** | 32 -> 35 |
| `NEAR-USD` | collapsed | -0.70 | -0.50 | **+0.201** | 32 -> 37 |
| `SOL-USD` | survived | -0.35 | -0.18 | **+0.161** | 23 -> 25 |
| `ALGO-USD` | collapsed | -0.76 | -0.62 | **+0.144** | 33 -> 38 |
| `STEEM-USD` | collapsed | -0.40 | -0.27 | **+0.136** | 48 -> 55 |
| `DASH-USD` | collapsed | -0.45 | -0.33 | **+0.126** | 52 -> 58 |
| `CRV-USD` | collapsed | -0.93 | -0.81 | **+0.113** | 33 -> 39 |
| `SC-USD` | collapsed | -0.24 | -0.13 | **+0.106** | 45 -> 57 |
| `ETH-USD` | survived | +0.14 | +0.24 | **+0.101** | 27 -> 28 |
| `DOT-USD` | collapsed | -0.73 | -0.63 | **+0.096** | 35 -> 37 |
| `OMG-USD` | collapsed | -0.01 | +0.09 | **+0.094** | 46 -> 49 |
| `ICX-USD` | collapsed | -0.05 | +0.03 | **+0.088** | 47 -> 55 |
| `ETC-USD` | collapsed | -0.87 | -0.79 | **+0.084** | 50 -> 58 |
| `NEO-USD` | collapsed | -0.29 | -0.22 | **+0.078** | 46 -> 52 |
| `ONT-USD` | collapsed | -0.34 | -0.26 | **+0.076** | 48 -> 53 |
| `LTC-USD` | survived | -0.93 | -0.85 | **+0.071** | 54 -> 60 |
| `BTC-USD` | survived | -0.62 | -0.56 | **+0.061** | 35 -> 39 |
| `CRO-USD` | survived | +0.02 | +0.07 | **+0.043** | 30 -> 40 |
| `BSV-USD` | collapsed | -0.85 | -0.82 | **+0.038** | 44 -> 51 |
| `LUNA1-USD` | delisted | -0.04 | -0.01 | **+0.031** | 7 -> 7 |
| `ZRX-USD` | collapsed | -0.54 | -0.51 | **+0.029** | 49 -> 58 |
| `ATOM-USD` | collapsed | -0.35 | -0.32 | **+0.029** | 31 -> 35 |
| `SRM-USD` | collapsed | -0.41 | -0.38 | **+0.027** | 30 -> 39 |
| `ADA-USD` | survived | -0.41 | -0.39 | **+0.023** | 42 -> 51 |
| `LUNC-USD` | collapsed | +0.05 | +0.07 | **+0.019** | 52 -> 52 |
| `SNX-USD` | collapsed | -0.45 | -0.43 | **+0.016** | 36 -> 46 |
| `QTUM-USD` | collapsed | -0.22 | -0.20 | **+0.013** | 46 -> 54 |
| `WAVES-USD` | collapsed | +0.11 | +0.12 | **+0.011** | 40 -> 49 |
| `THETA-USD` | collapsed | -0.66 | -0.66 | **+0.006** | 42 -> 52 |
| `XRP-USD` | survived | -0.84 | -0.84 | **-0.001** | 44 -> 50 |
| `HBAR-USD` | survived | -0.11 | -0.11 | **-0.001** | 27 -> 30 |
| `TRX-USD` | survived | -0.46 | -0.47 | **-0.005** | 25 -> 27 |
| `XEM-USD` | collapsed | +0.09 | +0.08 | **-0.017** | 39 -> 47 |
| `BCH-USD` | survived | -0.49 | -0.51 | **-0.021** | 40 -> 48 |
| `FIL-USD` | collapsed | -0.60 | -0.63 | **-0.021** | 39 -> 46 |
| `LINK-USD` | survived | -0.77 | -0.80 | **-0.025** | 35 -> 42 |
| `AXS-USD` | collapsed | -0.10 | -0.13 | **-0.029** | 31 -> 33 |
| `EOS-USD` | collapsed | -0.60 | -0.64 | **-0.046** | 52 -> 61 |
| `LSK-USD` | collapsed | -0.46 | -0.51 | **-0.047** | 50 -> 61 |
| `AVAX-USD` | collapsed | +0.28 | +0.22 | **-0.056** | 21 -> 24 |
| `SUSHI-USD` | collapsed | -0.40 | -0.46 | **-0.062** | 32 -> 39 |
| `FTT-USD` | collapsed | -0.22 | -0.29 | **-0.063** | 29 -> 38 |
| `ZEC-USD` | survived | -0.64 | -0.71 | **-0.067** | 49 -> 65 |
| `BTG-USD` | collapsed | -0.48 | -0.56 | **-0.074** | 43 -> 52 |
| `XMR-USD` | survived | -0.47 | -0.57 | **-0.103** | 31 -> 38 |
| `USTC-USD` | collapsed | +0.44 | +0.33 | **-0.104** | 21 -> 24 |
| `EGLD-USD` | collapsed | -0.49 | -0.59 | **-0.105** | 33 -> 40 |
| `MKR-USD` | survived | -0.75 | -0.86 | **-0.111** | 37 -> 48 |
| `MATIC-USD` | delisted | -0.13 | -0.25 | **-0.123** | 27 -> 33 |
| `VET-USD` | collapsed | -0.68 | -0.82 | **-0.132** | 42 -> 53 |
| `YFI-USD` | collapsed | -0.56 | -0.70 | **-0.137** | 33 -> 42 |
| `OKB-USD` | survived | -0.59 | -0.73 | **-0.142** | 20 -> 23 |
| `XTZ-USD` | collapsed | -0.48 | -0.63 | **-0.149** | 48 -> 61 |
| `BAT-USD` | survived | -0.67 | -0.82 | **-0.154** | 44 -> 59 |
| `REP-USD` | collapsed | -0.10 | -0.25 | **-0.154** | 33 -> 43 |
| `HT-USD` | collapsed | -0.11 | -0.28 | **-0.165** | 31 -> 40 |
| `SAND-USD` | collapsed | +0.07 | -0.10 | **-0.166** | 27 -> 32 |
| `XLM-USD` | survived | -0.28 | -0.46 | **-0.178** | 40 -> 50 |
| `KSM-USD` | collapsed | -0.13 | -0.32 | **-0.185** | 34 -> 41 |
| `MANA-USD` | collapsed | -0.63 | -0.87 | **-0.238** | 46 -> 58 |
| `DOGE-USD` | survived | -0.55 | -0.84 | **-0.285** | 41 -> 52 |

</details>

---

## Both books together

**E1 does not transfer on either book.** Five every-symbol passes on BTC and ETH, and neither survives a cross-section that includes the coins that died.

Win rates among firing symbols: long 39% of 62, short 48% of 62.

Whatever the sign, this does not make either book worth running. It answers one question
— whether E1's effect is a property of the rule or of two instruments — and nothing about
whether a breakout book has an edge. The long book's deflated Sharpe is near 1.0 on a flat
plateau and the short book's is 0.04-0.54; neither number moves because of anything here.


## Standing caveats

1. **This tests one rule, not a strategy.** Neither book has a demonstrated edge — the
   long book's DSR sits near 1.0 only because its plateau is flat, and the short book's is
   0.04-0.54. A rule that improves a losing book makes it lose less.
2. **The universe is screened, not curated.** `UniversePolicy` admits on tradability and
   data adequacy only — no return, Sharpe, drawdown or trade count enters it (D140).
3. **The cross-section is not independent.** These coins move together, so 62 symbols is
   far fewer than 62 independent tests and every win rate's effective sample is smaller
   than it looks.
4. **No margin call, no liquidation, no borrow recall (D175).** Short accounts in this
   universe have gone past -100% and kept trading. Until that is modelled, no short number
   here describes a loss a trader could actually have taken.
5. **One configuration each, no per-symbol tuning, one k** (D141). That is what makes this
   an out-of-sample test rather than a second search.
