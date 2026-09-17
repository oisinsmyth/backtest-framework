# D449 RESULT — the untraded window was not the problem: the proxy understates MAE by ~5%, its breach rate is identical, and what it actually flatters is the ENTRY

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D449-RESULT-the-untraded-window-was-not-the-problem-the-proxy-understates-MAE-by-five-percent-and-flatters-the-ENTRY.md`. The H1 above is the full title.*

**MEASUREMENT record. No hurdle is claimed and no candidate is admitted.** Closes the *"re-run
D440 on ES"* item. **Runner:** `scripts/d449_es_holds.py`. **Fixture built:**
`data/fixtures/es_c1_holds.csv.gz` (2,068 holds). **Evidence:** `data/d449_es_lifecycle.json`,
`data/d449_es_holds.csv.gz`. **Two of four predictions hold; one failed by an order of magnitude
and one failed in SIGN, and the sign failure is the finding.**

---

## AMENDMENT 2, 2026-09-12 — **ON THE COMPLETE ACQUISITION THE SIGN INVERTS: THE PROXY OVERSTATES THE EXCURSION**

**Re-run through 2026-09-09 as
[D451](D451-RESULT-the-complete-acquisition-T1-is-testable-and-the-cash.md).**
**2,595 matched holds.**

| | ES | proxy | ratio |
|---|---:|---:|---:|
| mean MAE | 0.698% | 0.708% | **0.99** |
| **breach 1×** | **1.195%** | **1.387%** | **0.86** |
| breach 2× / 3× | 10.906% / 25.279% | 12.100% / 27.784% | 0.90 / 0.91 |

> **§8a's premise is WRONG IN SIGN.** This record said the proxy understates the excursion and every
> `V` is an upper bound. **On the complete sample ES's MAE is marginally SMALLER and its breach rate
> is 9–14% LOWER** — the proxy is **conservative**, not optimistic.
> **Candidate explanation, not measured: SPY's extended-hours bars are built from THIN prints, which
> widens their high-low range, and that exaggeration exceeds what the invisible window conceals.
> The proxy's problem was never the window it could not see; it is the prints it could.**

**The headline is unchanged and stronger still: the untraded window was not the problem.**

## AMENDMENT 1, 2026-09-12 — **§3 IS WITHDRAWN. A BUG IN THIS RUNNER'S PAIRING EXCLUDED EVERY FRIDAY HOLD.**

**Found by [D450](D450-RESULT-the-entry-print-is-not-stale-and-the-anomaly-it-was.md)**,
which was commissioned by §6 of this record to explain §3 and found that §3's anomaly did not exist.

**The bug.** `days = sorted(set(ev) & set(front))` lists only days carrying 18:00+ bars, and the
build paired **consecutive entries of that list**. **ES is shut on Friday evening, so a Friday never
enters `ev` — and every Thursday→Friday hold was silently dropped.** D259's rule excludes
Friday→**Monday**; it does not exclude Thursday→Friday. **2,068 holds → 3,067 after the fix.**

**What it cost, on an identical window:**

| | n | hold diff | p99 MAE ratio | breach 1× ratio |
|---|---:|---:|---:|---:|
| **as published below** | 1,362 | **−1.74%/yr** | 1.05 | 1.00 |
| **corrected** | 1,808 | **+1.13%/yr** | 0.98 | 0.96 |

**Four consequences:**

1. **§3 — "what it actually flatters is the ENTRY" — is WITHDRAWN.** The −1.74%/yr was the Friday
   exclusion. **D450 measured the entry step directly at +0.42%/yr, in the opposite direction to
   staleness, and found D259's fallback branch never fires.**
2. **`Z3` INVERTS.** Corrected, ES `V` is **167 / 99** against the proxy's **95 / 63** — **ES is
   worth more, not less.**
3. **`Z4` was RIGHT and the data was wrong.** The corrected difference is the carry `Z4` predicted.
4. **§1 and the headline STRENGTHEN.** MAE ratios move from 1.03–1.07 to **0.98–1.02** and the 1×
   breach ratio from 1.00 to **0.90.** **"The untraded window was not the problem" is more true
   after the fix, not less.**

**The tables below are left exactly as published.** The corrected figures are in
`data/d449_es_lifecycle.json` and `data/fixtures/es_c1_holds.csv.gz`, both regenerated, and **that
fixture now extends to 2024-08-28 because the acquisition landed a further chunk mid-study** —
D450 §6.

---

## THE ANSWER

> **D440 section 8a named the 20:00–04:00 window as its largest limitation and said every MAE was
> a lower bound. It is — by 3 to 7%. The breach rate at 1× is IDENTICAL to three decimals.**
>
> **What the proxy actually flatters is not the path. It is the ENTRY: ES's hold return is
> 1.74%/yr BELOW the proxy's, on the same dates, at 0.9987 correlation.**

**The median ES hold carries 1,317 one-minute bars, of which 479 fall in 20:00–04:00 — the window
the equity proxy compresses to a single observation.** Seeing all 479 of them moves the MAE
quantiles by 3–7%.

## 1. The path, on matched dates

**1,362 holds, 2011-02-08 → 2022-08-16.** ES covers 2010-06 → 2022-08 and the equity fixture covers
2010-01 → 2026-08, so **the proxy is re-scored on exactly the dates ES supplies** — any difference
is the instrument, not the sample.

| | ES | proxy | ratio |
|---|---:|---:|---:|
| mean MAE | 0.688% | 0.649% | **1.06** |
| p50 | 0.437% | 0.409% | 1.07 |
| p90 | 1.539% | 1.498% | 1.03 |
| p95 | 2.113% | 2.038% | 1.04 |
| **p99** | **3.612%** | **3.453%** | **1.05** |
| worst | 9.971% | 9.678% | 1.03 |
| **breach 1×** | **1.542%** | **1.542%** | **1.00** |
| breach 2× | 10.940% | 10.132% | 1.08 |
| breach 3× | 23.789% | 22.687% | 1.05 |

> **The breach rate at 1× — the notional P1 is written about — is the same to three decimal
> places.** D259 predicted this without being able to measure it: it found the untraded gap
> breaching 4% on **0.10% of holds** and called its caution *"correct in mechanism and small in
> magnitude."* **It was right, and this is the measurement that says so.**

## 2. The lifecycle

**MFFU Rapid EOD 50K, best over the risk grid, matched dates:**

| series | rule | `V` | frac | funded yr | `P(pass)` | `P(paid)` |
|---|---|---:|---:|---:|---:|---:|
| **ES** | static | **627** | 0.4% | 0.90 | 0.762 | 0.553 |
| proxy | static | 1,092 | 0.4% | 0.97 | 0.778 | 0.592 |
| **ES** | voltgt | **571** | 0.4% | 0.47 | 0.656 | 0.370 |
| proxy | voltgt | 745 | 0.4% | 0.53 | 0.682 | 0.392 |

**`V` falls 43% (static) and 23% (voltgt) on the real instrument, and funded life shortens.
D440's caveat pointed the right way.**

> **THESE ARE NOT D440's HEADLINE NUMBERS AND MUST NOT BE READ AS THEM.** D440 ran 3,266 holds over
> 2010–2026 and reported `V` = 78 on SPY voltgt. This window is **1,362 holds ending 2022-08**, and
> it **excludes the 2021–2026 era D440 measured at `V` = −135.** The earlier window is far more
> favourable, which is why the proxy reads 745 here and 78 there. **The ES-versus-proxy comparison
> is valid because both sides share the dates; neither side is comparable to D440's headline.**

## 3. The finding I did not predict, and it is the useful one

**ES's hold return is `−0.69 bp/day = −1.74%/yr` against the proxy's, at correlation 0.9987.**

**That is the OPPOSITE SIGN to [D448](D448-RESULT-the-direct-test-the-drift-is-in-the-T0-future-too-and.md)**,
which measured ES **above** SPY by **+1.49%/yr** on the 16:00→09:30 overnight window and identified
that as the carry term `q − r`. **The two windows differ in one thing: where the hold STARTS.**

- **D448 starts at SPY's 16:00 close** — the closing auction, the most liquid print of the day.
- **D449 starts at SPY's 18:00 POST-MARKET print** — thin, and D259 was already worried about it:
  it carries an `ENTRY_STALE_FLOOR` of 17:00 precisely so that *"a session with no evening print
  after this is dropped rather than entered at a stale 16:15 price."*

> **The leading explanation is that the proxy's entry print is stale or low relative to the real
> price, inflating its hold return — and that ES, entering at the liquid Globex reopen, does not
> get that.** Combined with the `q − r` carry that should make ES *higher*, the proxy's entry
> advantage is **on the order of 3%/yr**.
>
> **`[NOT MEASURED HERE.]`** The entry prices themselves were not compared; this is the candidate
> explanation the sign flip points at, and §6 carries it as the open item.

## 4. A bug I introduced, caught by its own assertion, and its size

**The first version of this runner computed the trailing drawdown as
`1 − min(low) / max(max(high), 1)` — the global trough against the global peak, WITHOUT REQUIRING
THE PEAK TO COME FIRST.** That is not a trailing drawdown; it is an upper bound on one. D259's
`walk` tracks a **running** peak in order, and this did not.

**What it cost, now printed by the runner on every run:**

| | ordered | unordered | overstatement |
|---|---:|---:|---:|
| mean trailing DD | 1.055% | 1.347% | **+28%** |
| **breach 1×** | **1.542%** | **2.129%** | **+38%** |

**The buggy version reported breach ratios of 1.38× / 1.71× / 1.64× against the proxy and would
have supported a conclusion — "ES is far more dangerous than the proxy" — that is false.** The
corrected ratios are **1.00 / 1.08 / 1.05**.

**Three checks now run on every invocation**, and the synthetic one **fired on its own arithmetic
first**, which is how it earned its place: trailing DD must be **≥ MAE** and **≤ the unordered
bound**, and a hand-built path that dips to 0.90 before rising to 1.20 must give **0.10 ordered
against 0.25 unordered.**

**MAE was never affected** — it is a minimum relative to entry and carries no ordering.

## 5. Predictions

| | prediction | outcome |
|---|---|---|
| **Z1** | ES MAE larger at every quantile | **CONFIRMED** — every ratio above 1.00 |
| **Z2** | p99 rises **15–60%** | **WRONG, by an order of magnitude** — it rises **5%** |
| **Z3** | `V` falls and funded life shortens on ES | **CONFIRMED** — −43% / −23%, life 0.97→0.90 and 0.53→0.47 |
| **Z4** | corr > 0.98 **and** the mean differs by about `q − r` ≈ **+1.49%/yr** | **HALF WRONG** — corr **0.9987**, but the mean differs by **−1.74%/yr**, opposite in sign. §3 |

**Z2 and Z4 fail in the same direction of understanding: I assumed the untraded window was where
the danger was.** It is not. **The 479 minutes nobody could see turn out to be quiet, and the one
print everybody could see turns out to be the problem.**

## 6. What this leaves

1. **Compare the entry prints directly** — SPY's 18:00 post-market print against its own 16:00
   close, and against ES's 18:00. **§3's explanation is a candidate, not a measurement**, and this
   is a small study on data already in hand.
2. **The T+1 era is still absent.** ES ends 2022-08-16; the acquisition's final chunk
   (2022-08-17 → 2026-09-11) is still `submitted`. **When it lands, both this and
   [D448](D448-RESULT-the-direct-test-the-drift-is-in-the-T0-future-too-and.md)
   should be re-run**, and only then does the ES series cover the era D440 found negative.
3. **Nothing here rescues C1.** Under the [R11 ruling](../RULES.md#r11) P4 is the account's life,
   and on the full window D440 measured **0.14 years against a 3-year bar**. This window's 0.90
   years is a more favourable era, **on a sample that stops before the one that killed it**.

## 7. Provenance

**No roll adjustment anywhere.** Entry, path and exit come from one contract; a hold whose front
month differs between its two days is dropped. Front month is the highest-volume contract that day,
measured rather than a calendar rule. **`databento` is in the system interpreter and is not a
project dependency, so `--build` runs under bare `python`; `pyproject.toml` was not touched.** The
raw DBN under `temp/` was read only, and the fixture is written to `data/fixtures/` so nothing
downstream depends on a deletable directory.
