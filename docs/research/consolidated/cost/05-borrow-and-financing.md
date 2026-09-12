# Borrow, financing and what a short leg costs to own

[← cost index](00-index.md) · prev: [equal-weight bias](04-equal-weight-bias.md) · related: [short-side signals](../signals/07-short-side-cross-sectional.md)

**Scope warning.** This page is built almost entirely on the **57-liquid-ETF** research stream, whose
cost bar is **1.85 bp/side**. The equity campaign's bar is **33.8 bp/side** on 1,573 dead-inclusive
names. **Do not carry a figure across** — see [vs repo R11](../conflicts/02-versus-repo-measurements.md).

---

## Borrow is cheap; the financing gradient is not `[EXT]` `shorts/04`

| | |
|---|---|
| real IBKR borrow on core ETF names | **0.25%–0.65%/yr** — a rounding error |
| interest paid on the **first $100,000** of short proceeds | **zero** |
| next tranche | benchmark **− 1.25%** (2.38% against a 3.63% benchmark) |
| **structural carry cost of the short leg** | **≈ 4.0%/yr of capital at $100k, ≈ 2.0%/yr at $700k** |

> **That gradient — not borrow fees — is the binding size constraint.**

**Minimum viable capital for a dollar-neutral book at IBKR: `$250k` as a hard floor, `~$500k` before
the financing structure stops actively working against you.** And **clearing that floor fixes the
financing, not the breadth problem.**

## The arithmetic does not close at our breadth `[EXT]`

Adding a short leg **doubles gross notional and therefore doubles the turnover bill.** A dollar-neutral
book at $700k rebalancing monthly carries a **≈ 2.9%/yr structural hurdle before any alpha.**
Clearing a >10%/yr net target at an effective breadth near **2.2** needs an information coefficient of
**0.25–0.42**, against a realistic ceiling near **0.05** for a good equity signal.

**For scale: AQR's flagship Equity Market Neutral fund — thousands of names, institutional
financing — has returned 7.30%/yr since Oct 2014.**

> **Verdict `[EXT]`:** for a $100k–$700k book in 57 co-moving liquid ETFs, **the short leg is not
> additive. It is a hedge we would pay roughly 2–4%/yr of capital to own**, in order to cancel a
> measured +8.59%/yr overnight drift.

**`[REPO]` agrees by a different route.** [FINDINGS §19](../../../FINDINGS.md): *"The short side of
this programme is a cost failure, and neither sizing nor borrow changes the verdict"* — and D337
measured constant-shares at **+46 bp**, which **does not rescue the short leg**. See
[agreement A8](../conflicts/03-agreements.md) and [A7](../conflicts/03-agreements.md) on breadth.

## Where the borrow-fee literature actually lands `[EXT]`

Across **162 anomalies**: long/short is **+0.14%/month gross, entirely from the short leg, −0.01%/month
after borrow fees** — and **not profitable even before fees once the high-fee 12% of stock-dates are
excluded.**

> **We are not "paying away" the short-leg alpha. We are trading in the part of the market where it
> was never measured to exist.**

## Crowding, squeezes and the tail

`shorts/04` §3 carries the crowding and squeeze material; `shorts/02` §3 carries the volatility-ETP
tail. **The one structural fact that generalises** (`shorts/02` §6):

> **Every structural decay found is a risk premium paid for bearing crash risk, so shorting it is
> long-equity-beta in disguise.** A short VXX position is not a hedge against a long book — **it
> concentrates it.**

See [structural decay instruments](../signals/08-structural-decay-instruments.md).

## Two rule-level facts worth keeping

- **The `$25,000` pattern-day-trader rule was struck on 2026-06-04** `[EXT]`
  ([plumbing §1.9](../../the-plumbing-round.md)). Not verified here; it changes what a small account
  may do intraday.
- **Selecting for lendability selects for negative alpha.** The commissioner's premise — *"lending
  revenue is arithmetically identical to alpha"* — is **right arithmetically and inverted
  economically.** Recorded as one of the wrong premises in [`../../README.md`](../../README.md).

---

**Sources.** [`shorts/04`](../../shorts/04-short-book-construction.md) ·
[`shorts/02` §6](../../shorts/02-structural-decay-instruments.md) ·
[`the-plumbing-round.md` §1.9, `G5`](../../the-plumbing-round.md) ·
repo: [FINDINGS §1, §19, §30](../../../FINDINGS.md), D337.
