# Intraday microstructure and the overnight/intraday split

[← signals index](00-index.md) · prev: [structural decay instruments](08-structural-decay-instruments.md) · next: [dead-lane register](10-dead-lanes.md)

**The one page in this tree where a research hypothesis was tested here and LOST.** That is the
outcome that makes the folder worth keeping.

---

## The prerequisite: is our overnight drift real? `[SETTLED — REPO]`

**`[EXT]` the challenge, `shorts/03` §1.** Lachance (2021, *J. Financial Markets*): positive order
imbalance at the open plus wider overnight spreads **artificially inflate ETF overnight returns by
2.54 bp/day = 6.61%/yr**, and correcting for microstructure **eliminates three quarters of the ETF
overnight/intraday gap**. Our gap is `8.59 − (−0.36) =` **8.95 points**; three quarters is **6.7**.

> *"Our headline finding may be predominantly a trade-price artifact."*

**`[REPO]` the answer, [FINDINGS §58](../../../FINDINGS.md) / D402.** The test was run *because the
prop-firm research folder demanded it of its own row and nobody had demanded it of ours.*

| | |
|---|---|
| reproduction of D280's committed gap IC | **to five decimals**, before any filter |
| bars carrying a contamination flag (S1–S4) | **17.58%** of 2,232,440 out-of-sample bars |
| open **bit-identical** to the prior close | **5.84%** — one bar in seventeen |
| corr(gap, intraday), contaminated vs clean | **−0.1564 vs +0.0082** |
| **the edge on CLEAN bars only** | **−0.01746, `t` −4.49 — 1.14× the committed value**, on 60% of the sample |
| **the discriminating gradient** | gap IC by dollar-volume quintile: **−0.0123 → −0.0219.** **1.8× STRONGER in the most liquid quintile** |

> **A print artefact must concentrate where prints are unreliable. This concentrates where they are
> most reliable.** Removing every contaminated bar makes the edge **larger.**

**Repo prevails.** Two residuals kept honestly: D402 tested stale and extreme opening **prints**;
Lachance's channel is quoted-spread **width** at the open, not tested identically — the liquidity
gradient is evidence against it, but it is inference. And **the contamination itself is real, common
and detectable — a reusable data-quality fact about this fixture, independent of D280.**

## The cost hurdle kills most of the intraday literature outright `[EXT]` `shorts/03` §0

At **1.85 bp/side**, an intraday round trip costs **3.70 bp**. The three best-documented market-level
intraday effects:

| effect | gross per round trip |
|---|---|
| Gao et al. (2018) intraday momentum | **2.65 bp** |
| Baltussen et al. (2021) intraday momentum | **2.72 bp** |
| Baltussen–Da–Soebhag (2025) end-of-day reversal | **3.78 bp** |

**All three at or below 3.70. Not marginal — arithmetically dead as standalone daily-traded
strategies at our cost level, and the papers' own authors say so.**

## Where the effects that DO clear the hurdle live `[EXT]`

**In the cross-section of individual stocks, not in a 57-name liquid-ETF panel.** The magnitudes that
beat 3.70 bp/trade — **−1.96%/mo intraday alpha on the high-past-overnight decile**
(Lou–Polk–Skouras), **−7.7 bp/day-per-unit-beta** day-time security market line
(Hendershott–Livdan–Rösch) — are driven by cross-sectional **dispersion** in beta, volatility and
retail attention **that 57 liquid ETFs simply do not have.**

> **This is a dispersion problem, not a mechanism problem: the mechanism replicates, the spread does
> not.**

**`[REPO]` and this is [FINDINGS §4](../../../FINDINGS.md) again** — breadth, in a different costume.

## The two candidates `shorts/03` singled out `[EXT]` §8

1. **A volatility-regime-conditioned cross-sectional day/night risk sort.**
2. **A lagged overnight/intraday-persistence name selector** — which adds **zero incremental
   turnover**, because it only decides *which* names go into a book already paying the round trip.

**Both are cross-sectional and computable from data already held.** Neither has been run here.
**Candidate 2's zero-turnover property is the rarest thing in the whole research tree** and is worth
reading in full before it is dismissed.

## `[REPO]` what the repo has measured on this axis

| | |
|---|---|
| [§21](../../../FINDINGS.md) | the fill convention **credited the overnight gap to every entry**, worth more than the spread |
| [§43](../../../FINDINGS.md) | the entry-day spread does not move the fade's cost; **charging each trade its own spread does** |
| [§44](../../../FINDINGS.md) | **the opening minute is 1.4% of the day and the closing minute 7.9%** — the fade's order is 2.5% of the auction it fills in |
| [§45](../../../FINDINGS.md) | **the cost problem is a turnover problem**: the same momentum signal loses 1.5%/yr refreshed daily and earns 6.5% behind a rank buffer |
| [§58](../../../FINDINGS.md) | above |

**§45 is the direct answer to the intraday literature's problem**, measured here rather than read:
**turnover, not the effect, is what fails.** Nothing external contradicts it.

## And the hard constraint on any close-decided book `[EXT]`

**NYSE MOC/LOC hard cut-off is 3:50 pm** (Nasdaq MOC 3:55, LOC 3:58, IO 4:00). **A signal computed
FROM the close cannot fill IN that close.** → [spread estimation](../cost/01-spread-estimation.md)

---

**Sources.** [`shorts/03`](../../shorts/03-intraday-microstructure.md) ·
[`the-forced-seller-and-the-cost-wall.md` §1.7](../../the-forced-seller-and-the-cost-wall.md) ·
repo: [FINDINGS §21, §43, §44, §45, §58](../../../FINDINGS.md), D247, D280, D402.
