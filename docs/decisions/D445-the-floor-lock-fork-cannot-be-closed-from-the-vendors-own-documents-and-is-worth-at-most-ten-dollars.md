# D445 — the Rapid floor-lock fork cannot be closed from MFFU's own documents, and pricing it shows it is worth at most $10

**MEASUREMENT record. No hurdle is claimed, no candidate is scored, and no strategy is proposed.**
Closes **[D386](D386-the-prop-account-is-worth-its-buffer.md)'s open item 4**. **Runner:**
`scripts/d445_floor_lock.py`. **Evidence:** `data/d445_floor_lock_sources.md` (verbatim sources),
`data/d445_floor_lock.json` (96 cells).

---

## THE ANSWER

> **The documentation fork is REAL, IRREDUCIBLE FROM MFFU'S OWN PUBLICATIONS — and economically
> immaterial. D386's open item 4 is closed as MOOT rather than resolved.**

**The worst cell in the study is `−$10`, or `−10.5%` of a `$92` value. Half the cells are exactly
zero. Funded life does not move to two decimal places anywhere.**

## 1. The documentation — three sources, and the binding one is silent

| source | says |
|---|---|
| help centre, **Rapid 50k AND 25k** | *"Max Loss Lock at $100. **Once your trailing Max Loss reaches $100, it locks there.**"* → **AUTOMATIC** |
| **`/plans/rapid`** | *"once your balance is +$100 above your starting balance **after your first payout**, the floor locks and stops trailing upward permanently."* → **PURCHASED** |
| `/plans/pro` *(different product)* | *"**After your first approved payout**, the MLL locks permanently… and stops trailing entirely."* → **PURCHASED** |
| **Terms of Service** | **SILENT.** 47,569 visible characters, **zero** occurrences of "Max Loss", "Maximum Loss", "MLL". *"Drawdown: Loss thresholds for the Account, including daily or trailing limits"* is the only definition |

> **THE ONE CONTRACTUALLY BINDING DOCUMENT DOES NOT ADDRESS THE RULE THAT SETS THE ACCOUNT'S ENTIRE
> GEOMETRY.** It lives in support and marketing copy, and those two contradict each other for the
> same product.

**One observation that weakens the help centre's side, recorded because it cuts against the reading
I found first:** the 25k article uses **identical phrasing at both stages** — *"Once your trailing
Max Loss reaches $25,100, it locks there"* in the evaluation and *"reaches $100, it locks there"*
when funded. **A payout precondition is impossible in an evaluation**, so the funded sentence may be
a template inherited from the eval rule rather than a statement about the funded stage.

**Method:** raw `curl` with a browser User-Agent, text extracted locally, **no summariser anywhere in
the path**. All five fetches returned **HTTP 200 with matching titles and the expected terms present
in quantity** — the wrong-200 check. **Nothing was purchased, signed up for or clicked through.**

## 2. Pricing it — because an unresolvable question can still be bounded

Both readings are expressible in D386's existing `Plan` with **no change to the simulator**:

```
AUTOMATIC   lock_fund = dd + 100                      what D386 and D440 have both assumed
PURCHASED   lock_fund = None, post_payout_floor = 100  trails forever until a payout is taken
```

**PURCHASED minus AUTOMATIC, on D440's measured path, MFFU Rapid EOD 50K, best over the risk grid:**

| | static | voltgt |
|---|---:|---:|
| **SPY** | **−10 (−10.5%)** | −1 (−1.4%) |
| QQQ | −3 (−4.0%) | 0 |
| IWM | −2 (−2.8%) | −5 (−6.5%) |
| DIA | 0 | 0 |

**Funded life: unchanged to two decimals in all eight cells. `P(ever paid)` moves by at most 0.004.**

### And it is not small merely because the measured path kills survival

**That was my hypothesis and it was wrong.** Run under D386's own Gaussian — where `P(ever paid)` is
**0.238 against the measured path's 0.143**, and payouts per evaluation **1.29 against 0.33** — the
fork is still nothing:

| | SPY | QQQ | IWM | DIA |
|---|---:|---:|---:|---:|
| **d`V`** | **−24 (−3.1%)** | −20 (−2.7%) | +4 (+1.0%) | +5 (+1.0%) |

**Four times the payout rate, the same immateriality.**

## 3. Why it is narrow, which is what makes the result robust

**The fork can only bite between the moment the trailing level is reached and the moment the first
payout is taken.** Outside that window the two readings are identical: before it, neither has
locked; after it, both have.

**And MFFU's own rules make that window short.** A payout needs `safety_net + min_payout` =
**`$2,000 + $500`**, so the first withdrawal comes at a balance near **`$2,500`**, where the trailing
floor sits at **`$500`** against the locked floor's **`$100`**. **The gap is ~`$400` of buffer
against a `$2,000` drawdown, for a few sessions.**

> **The vendor's own minimum-payout and safety-net rules are what make its own ambiguity
> immaterial.** That is a structural reason rather than a numerical accident, which is why the
> result holds under both a Gaussian and a measured path.

## 4. What this settles, and what it does not

- **D386's open item 4 is CLOSED — as moot.** *"Everything post-lock rests on it"* was the reason it
  was ranked the cheapest open item on the prop track. **Post-lock behaviour does rest on it; almost
  nothing reaches post-lock, and the approach to the lock is worth `$400` of buffer for a few
  sessions.** **The item was correctly flagged and wrongly prioritised, and the prioritisation was
  mine.**
- **It does not resolve the documentation fork**, and nothing here should be read as a legal
  reading. **If a real account is ever funded, the operative rule is whatever MFFU applies, and the
  contract does not say.**
- **It does not touch D440 or D442.** Both assumed AUTOMATIC; the correction to PURCHASED costs at
  most `$10` on the primary cell, **which does not move `T1`, `T2`, `T3` or any `G` verdict.**
- **It is not a reason to trust the other terms less or more.** It is one sentence, checked.

## 5. The generalisation worth keeping

> **An open item's PRIORITY is a claim about magnitude, and a claim about magnitude can be measured
> before the item is investigated.** This one was ranked first on the prop track for a month on the
> strength of *"everything post-lock rests on it"* — true, and it took **seven seconds of simulation**
> to show that the quantity it gates is worth `$10`.

**The cheap move, available whenever a fork is expressible as two parameter settings: price the fork
BEFORE reading the documents.** Had that been done here, the fetch would have been unnecessary — and
the fetch is the part that cannot be automated or guaranteed to terminate.
