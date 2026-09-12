# Structural decay instruments — shorting something with negative expected drift

[← signals index](00-index.md) · prev: [short-side cross-section](07-short-side-cross-sectional.md) · next: [intraday and overnight](09-intraday-and-overnight.md)

**The premise this stream was sent with:** our shorts keep dying because they fight **+8.59%/yr of
overnight equity drift**, so find an instrument whose expected drift is *mathematically* negative and
short that instead.

**Result: one genuinely negative-drift class, one partial, and the trade the brief singled out is
worse than "priced away" — it is identically zero.**

---

## The leveraged pair short is ZERO, not a fee-eroded positive `[EXT]` — the killing result

**Hold matched notional short in TQQQ and short SQQQ. The daily P&L is identically zero before
frictions.**

> **The "decay harvest" that appears in unrebalanced backtests is not decay at all — it is a
> disguised bet on negative serial correlation in the underlying index.**

**This kills the idea outright, independently of borrow cost.** `shorts/02` §2.2. **The brief
corrected its own commissioning premise**, which is the same shape as
[`D4` in the equity campaign](05-arrival-and-drawdown.md).

## Where decay IS large, borrow has not priced it away — and that is not good news `[EXT]`

| | |
|---|---|
| VXX / UVXY roll decay | **≈ 50%/yr** |
| real IBKR borrow, 2026-08-28 | **3.05% (VXX), 3.34% (UVXY)** |

**The arbitrage argument fails — but not because there is free money.** **The binding constraint is
margin and tail risk**, i.e. exactly the `gross = exposure × edge` constraint this programme keeps
hitting. `shorts/02` §3.

## The finding that generalises to the whole stream `[EXT]` §6

> **Every structural decay found is a risk premium paid for bearing crash risk. Shorting it is
> long-equity-beta in disguise.**
> A short VXX position is not a hedge against our long book — **it is a levered doubling-down on it.**
> We would be **selling crash insurance.** That does not diversify a long book; **it concentrates
> it.**

**This is the strategic finding, and it applies to every candidate in the document** — contango
commodity ETFs (USO, UNG) included.

## The verdict `[EXT]` §7

**Do not pursue any of these as a short strategy.** The one candidate with a defensible net edge —
**short VXX** — is:

1. a well-known **crowded** short-vol trade,
2. sizeable at only **~5% of book**, yielding **~2.4%/yr gross of the tail**, and
3. **positively correlated with existing long exposure** — so it fails the diversification test that
   motivated the shorts programme in the first place.

## The data-integrity warning attached to this stream `[OPEN]` — undischarged

> `[EXT]` *"the +733% single bar in our USO/UNG fixture is almost certainly a reverse-split artifact,
> not a market move."* USO executed a **1-for-8 effective 2020-04-29** (an unadjusted +700% bar); UNG
> has had multiple 1-for-4s. **"If our fixture shows a +733% bar, the series is not split-adjusted,
> and every result our framework has ever produced touching USO or UNG is contaminated."**
> *"This should be verified before anything else in this document is acted on."*

**`[REPO]` No record mentions USO or UNG.** The class is repo truth three times over — thirty
fabricated dividend days ([§18](../../../FINDINGS.md)), the 15m-versus-daily adjustment split, and the
closed-end-fund composition of `etf_wide_daily_raw` ([§60](../../../FINDINGS.md)).
**The specific claim has never been checked, and it is a one-line check.**
[vs repo R12](../conflicts/02-versus-repo-measurements.md).

---

**Sources.** [`shorts/02`](../../shorts/02-structural-decay-instruments.md) — §1 the mathematics of
LETF decay, §2 the pair short, §3 volatility ETPs, §4 commodity contango, §5 other candidates, §6 the
generalisable finding, §7 the ranking, §9 its own caveats.
