# The equal-weighted rebalancing bias

[← cost index](00-index.md) · prev: [the price floor](03-price-floor-and-screens.md) · next: [borrow and financing](05-borrow-and-financing.md)

**Why this matters here and not in the papers it comes from: every cross-sectional book in this
programme is equal-weighted** ([FINDINGS §51](../../../FINDINGS.md) — *"sizing was never chosen"*).
The Blume–Stambaugh daily-rebalancing bias is therefore **a property of our own construction**, not
of a reference series we happen to read about.

---

## The measurement `[BRIEF]` `J3` — on public files, over our own window

```
microcap decile        : +6.79 %/yr
every decile above it  : +0.30 % to +1.28 %/yr
```

**A factor of ~11 across the floor, one-sided — 92% of months positive — and a pure construction
artefact.** Published simulation shows **name count does not attenuate it**: 7.12% at 100 names,
7.18% at 900.

**`J3` ran a negative control and proved it can fire:** the value-weighted columns, which carry no
compounding bias in theory, return **+0.0002%/month against equal-weighted's +0.5487%**; a sentinel
census returns **0 over our window but 67,250 over the full file.**

## The mechanism, and the correction that makes it survivable `[EXT]` `K5`

**The bias is paid PER REBALANCE, not per bar.** It comes from a noisy **denominator reset**, and the
generalised estimator's bias term is **exactly zero for every bar after the first of a hold** when
noise is serially uncorrelated. So:

```
bias per bar  ~  (1/H) * sigma^2 * (1 - rho)
```

> **THE CHECK THAT SETTLES IT HERE, AND IT IS ONE PROPERTY OF THE CODE: does the weight array get
> recomputed from the current bar's close for names already held, or only at entry?** `[OPEN]` —
> item 18 of [`../../README.md`](../../README.md) §"What is open". **It decides whether a multi-bar-hold
> book carries the large version of the bias or ~`1/H` of it.**

## The cross-validation, and it is the best in the tree `[EXT]` → `[REPO]`

Inverting the verified closed form on `J3`'s **+0.30%/yr** implies **34.5 bp/side**, against this
programme's measured **33.8**. **Agreement to 2%, and the mechanism is bid-ask bounce** — nothing in
common with a range-based spread estimator. Two briefs, one cross-validation, neither commissioned to
check the other. See [agreement A2](../conflicts/03-agreements.md).

## Four further results `[EXT]` `K5`

1. **The bias lives almost entirely in GROSS** — a factor of ~300 against a cost already charged.
2. **The floor's leverage is quadratic, `∝ 1/P²`** — sharper than this repo's existing note that cost
   scales inversely with price. Feeds [the price floor](03-price-floor-and-screens.md).
3. **In a RANKED book the bias is the DIFFERENCE of the legs' noise variances** — 0.09%/mo for a
   book-to-market sort but **0.61%/mo for a share-price sort, which kills that premium outright** —
   **and that risk does not shrink with holding period**, because it comes from the selector
   covarying with spread.
4. **A Corwin–Schultz σ is a lower bound on total price noise**, so `K5`'s own reassuring arithmetic
   is lower-bound reassurance.

## The unresolved numbers `[CONFLICT C14, C15, C16]`

| | readings |
|---|---|
| **months positive** | Canina et al. **99.2%** · `J3` **92%** |
| **magnitude** | ABK implied **36.4 bp/month** · FWW measured **12.67 bp/month** — different universes and eras |
| **two coefficient signs** | **Canina et al. report two signs coming out BACKWARDS versus Roll (1983) and versus Blume & Stambaugh (1983)** — stated in their own paper |

**All stand.** And the canonical 1983 paper **could not be obtained**: the host returned **HTTP 200,
`text/html`, 1,651 bytes, `<title>404Handler</title>`** — the failure is committed as evidence at
`data/k5_rotman_blume_stambaugh_404_at_http200.html`. `K5` derived the bid-ask form itself rather than
trust a summariser, **and caught that summariser's worked number wrong — 0.3% claimed, 0.2506%
computed.**

## The internal measurement nobody has run `[OPEN]`

**The fixture's own compounded-daily-minus-buy-and-hold equal-weighted gap.** Needs **no external
series**, and `J3` supplies a pre-registrable band:

> **0.3–1.3%/yr if the floor binds, ~6–7%/yr if it does not.**

Item 17 of [`../../README.md`](../../README.md) §"What is open".

## A premise corrected, and it was hiding a break

**No Ken French file header declares a survivorship-free database** — `J3` censused `surviv` across
four daily files and the landing page and found **zero hits in all five.** The commissioner had
promoted an inference into a declaration. **And the error was hiding a break: the only documented
statement about names leaving a French portfolio describes a convention that CHANGED IN MAY 2015,
inside this window.**

---

**Sources.** [`the-selection-round.md` §1.11](../../the-selection-round.md) ·
[`the-reversal-round.md` §1.4](../../the-reversal-round.md) ·
[`the-timestamp-round.md` §1.5](../../the-timestamp-round.md) ·
repo: [FINDINGS §51](../../../FINDINGS.md).
