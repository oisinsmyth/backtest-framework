# D630 RESULT — H2 on NG PASSES: $66 a trade gross, $40 net, t 5.01. The move reverts after the settlement, it is concentrated in 2022, and it rises with fund size only up to a threshold

*Run once on 2026-09-26 (`scripts/run_h2_ng_stage_a.py --run`, committed `caaf42a` after the pre-registration
`96b34c2` and its amendment `a9f4a4b`). Output: `data/ledger_h2_ng_stage_a.json`, which `--check` reproduces byte
for byte. Sections 1–4 are the registered result. Section 5 is POST HOC (`scripts/explore_h2_ng_partner_control.py`
→ `data/ledger_h2_ng_posthoc.json`) and never replaces it.*

## 1. The verdict

| n trades | mean gross | t (NW) | mean net | placebo t | rotation p50 / p95 (± SE) | verdict |
|---|---|---|---|---|---|---|
| 1,028 | **$66.02** | **5.01** (4.55) | **$40.02** | −0.42 | −0.09 / 1.47 (± 0.05) | **PASS** |

- All four parts of §4 hold:
  1. t 5.01 ≥ 2.2414 (Holm, CL untested);
  2. the net mean is +$40 at $26 a trade;
  3. the 11:30 placebo is flat (−$6.51, t −0.42, 661 days);
  4. the observed t beats the rotation p95 by 3.54, 65 SEs.
- **Gate 1 is met on NG,** with its H1 half provisional until the CL/NG check of Sierra's sign after 2026-10-10
  (D629 §6). Under D630 §6, **the vault's one look now goes to the principal.**
- **Programme level:** the Holm-adjusted p is 1.1 × 10⁻⁶ (the 0.005 bar is met). The DSR is **0.87** over this
  record's 7 configurations, **below the programme's 0.95**. Promotion would need it. The vault comes first.
- No traded day lacked a fill or an exit price. The sign audit of the top trade is in §5.

## 2. Performance, net and gross (one full-size NG, $16 round trip + one tick of entry slippage)

| | gross | net |
|---|---|---|
| mean per trade | $66.02 | $40.02 |
| Sharpe (daily, all 1,936 days, √252) | 1.80 | **1.09** |
| Sortino | 3.02 | **1.75** |
| total, 2017-05 → 2025-02 | $67.9k | $41.1k |

- Exposure: a position on 53% of days, held from t0+1 to 14:29 (38 minutes on a 13:50 trade).
- Daily volatility $308 (net); maximum drawdown −$9,352.
- The mean move is 2.54 × the cost; the breakeven cost is $66 a round trip.

## 3. The trade distribution, and what the result depends on

**Distribution** (gross; net is $26 lower): median **+$40**; win rate 57.3% (net 53.0%); payoff 1.13; skew 0.33;
excess kurtosis 9.0. The trimmed means are all above the cost:

| ex-top 1% | ex-bottom 1% | trimmed both | full mean |
|---|---|---|---|
| $46.19 | $83.15 | $63.29 | $66.02 |

The median ($40) is below the mean ($66): the right tail adds, but without it the mean still clears the cost.

**What it depends on:**
- **Years:** 7 of 9 profitable. **2022 carries the most:** $207 a trade (205 trades, t 4.07). 2024 gives $41
  (t 3.16).
  - **Without 2022:** $31 (t 3.04), net +$5. It survives (§13A.8.5), barely above the cost.
  - **Without the best 1% of days:** $46 (t 3.91).
- **Concentration:** 22 trades make half the gross P&L. The top ten are 28.5% of it, and nine of them are in
  2022's price spike.
- **Price:** by NG price tercile, $23 / $28 / **$147**. Dollars per contract scale with the price.
- **t0:** 13:50 gives $70 (928 trades), 14:00 $30 (52), 14:10 $19 (48).
- **Fund size (D629's lesson):** by BOIL+KOLD AUM tercile, $19 (t 1.04) / **$151 (t 5.03)** / $28 (t 1.66). The
  largest-fund tercile is weak (§5).
- **H3 (dose-response),** all days by |I| quintile: −$3, −$4, −$4, +$34, +$137. Spearman ρ 0.7 with one inversion:
  **passes** the deposit's rule.
- **H6:** the yearly mean against the yearly AUM, r 0.27.

## 4. Controls and variants (reported beside, never gating)

- **D629's control:** the same rule on the 908 untraded days gives −$6 (t −1.08). Traded minus untraded is **+$72
  (Welch t 5.03)**.
- **Without the 247 estimated-f days:** $79 (t 4.83).

| variant | mean gross | t | mean net | Sharpe / Sortino net |
|---|---|---|---|---|
| fixed 14:10 (§7.1 secondary) | $44 | 4.19 | $18 | 0.62 / 0.96 |
| **stress fill** (worst close of bars t0+1…t0+5) | **$17** | **1.32** | **−$9** | −0.25 / −0.36 |
| 2× cost | — | — | $24 | 0.66 / 1.03 |
| one-bar delay (fill at t0+2) | $65 | 4.97 | $39 | 1.08 / 1.71 |
| without flagged days (354 trades) | $67 | 3.34 | $41 | 0.73 / 1.15 |
| **book frame** (§7.4: stop and early profit at 1 × \|I\|; mean hold 22 min) | $58 | **6.35** | $32 | **1.25 / 2.20** |

- **The edge is less than the fill risk.** The worst of five fills loses $49 against the primary fill, and the net
  becomes −$9. The trade needs a fill near the bar close of t0+1, and it has one minute of slack: a one-bar delay
  keeps 99% of the edge.
- **H4 (timing): passes.** 11% of the move to W_end is made by t0+5 (the deposit's bar is ≤ 50%). The mean signed
  move from t0 builds through the window: +$7 at +5 minutes, +$25 at +30, +$46 at +40.
- **§7.5, the post-window fade:** from the W_end close to +30 minutes, AGAINST the direction, **+$29 (t 3.98)**.
  About 44% of the move reverses within half an hour. That is the signature of temporary price pressure at the
  settlement, which is what the ledger claims.
- §7.4's flow-reversal exit is not built (D630 §7).

**The component line (minimum size: one MNG, $3 + $1 a round trip + $1 slippage):** gross $6.60 and net **$1.60** a
trade. Sharpe gross 1.80 and **net 0.44** (Sortino 3.02 / 0.67); hit rate 48%; skew +0.53. **It misses
`COMPONENTS_PROP.md`'s C-a (> 0.5).** At micro size the fixed cost is 76% of the gross. The correlation with the
ledger's entries is not computable: entries #2 and #3 have no daily P&L on disk.

## 5. POST HOC: the funds, or plain continuation on big-move days?

Traded days are big-|I| days, and |I| grows with the day's move as well as with fund size. §4's untraded control
compares against smaller moves. This section holds the move fixed.

- **The partner control:** within deciles of the standardised move |r(τ)| / σ_d, traded days beat untraded days by
  **$65 a trade (t 4.76, HC1, decile fixed effects)**. Untraded days show no continuation in any decile (−$38 to
  +$23), while traded days reach $124–137 in deciles 4 and 7. **At the same move, the days the funds are predicted to
  trade heavily continue; the others do not.** That is the ledger's mechanism, not momentum.
- **Fund scale within move deciles:** over all days, the log of the funds' contracts per unit return predicts the
  return (+$11.9 per log unit, t 2.68). **Among traded days, it does not** (−$3.7, t −0.22). With the fund-size
  terciles (§3), the effect looks like a THRESHOLD: once the predicted flow is large enough to trade, larger funds do
  not add more. D629 found the same shape in the flow.
- **The top trade:** 2022-05-09, NGN22, a sell at 13:51. NG was down 9.9% from the prior settlement by 13:50. The fill
  was 7.357 (the 13:51 bar's close) and the exit 7.100 (the 14:29 bar's close), +$2,570. The window traded 3,041
  contracts, and the 14:30 bar bounced to 7.125. The bars are consistent with the as-of prices in the volume panel.

## 6. What this means

- **As pre-registered, H2 passes on NG, and Stage A's Gate 1 is met on NG** (H1 provisional). The price moves into
  the settlement in the direction of the funds' predicted rebalance: $66 a contract on traded days, about 2.5 ×
  the cost. It reverts afterwards. It is specific to the traded days, to the settlement window (the placebo is
  flat), and to days whose predicted flow is large at a given move.
- **Caveats, in order of weight:**
  1. **Execution:** the stress fill loses money. The edge is real at the bar close and gone at the worst close of
     five minutes.
  2. **Concentration:** 2022 is the best year by far. Without it the net is +$5 a trade.
  3. **The DSR (0.87) is below the programme's 0.95.**
  4. **The micro line misses C-a** (net Sharpe 0.44). The full-size contract's $308 daily volatility fits the
     personal book, not a small prop account.
  5. **Fund size works as a threshold, not proportionally** (§5).
  6. **This is the fourth test on this in-sample** (D627–D630).
- **Next, for the principal:**
  1. **The vault's one look** (D630 §8): NG 2025-03-01 → 2026-09-18, about 200 trades. Pass: the same sign,
     one-sided p < 0.10, and a net mean > 0. POWER's vault pass rate at a quarter of the ledger's predicted move is
     0.82. It needs the vault inputs built and frozen first, and the look is spent whatever it shows.
  2. After 2026-10-10: the CL/NG check of Sierra's sign, which keeps or voids H1's half of Gate 1.
