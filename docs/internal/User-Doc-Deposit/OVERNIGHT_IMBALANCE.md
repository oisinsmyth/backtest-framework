# Overnight Imbalance and the Cash Open: Study Design

**Status:** study design and pre-registration draft
**Instrument focus:** ES/MES primarily; NQ/MNQ and RTY/M2K as replication universe
**Horizon:** intraday, flat by default, no overnight exposure
**Why this candidate:** the only strategy in the programme where the existing Databento
subscription is the *correct* tool rather than an expensive substitute for daily data — and the
only one whose breadth per unit time suits a prop evaluation.

**Companions:**
- `FEATURE_RESEARCH.md` — the harness, trial budget, CPCV
- `ALPHA_PROGRAMME.md` — mechanism filter, exclusion discipline, first-passage sizing
- `BASIS_MOMENTUM.md` — the other novel candidate; different horizon, different mechanism
- `DATA_EXPANSION_PLAN.md` — §2.1 on Databento backfill provenance, which constrains §7 below

---

## 1. The mechanism

### 1.1 What is actually constrained

**The overnight session is not unobservable.** ES trades nearly 24 hours on Globex and full book
data exists for it. What closes is the **cash equity market**.

So the constrained participants are those who *cannot act* until 09:30 ET:

| Participant | Constraint |
|---|---|
| Mutual funds | Price and transact at NAV / cash session |
| Retail | Broker access, market-on-open orders |
| Cash equity desks | No venue to trade the underlying |
| Index funds tracking cash indices | Rebalance against cash prices |
| Anyone with a MOO/LOO order | Executes only in the opening auction |

Futures price incoming information continuously through the night. **Cash-side demand
accumulates unexpressed.** The tradeable claim concerns what happens when that class of
participant can finally respond.

This passes the mechanism filter in `ALPHA_PROGRAMME.md` §2: a named group, unable to trade for
a structural reason, forced to express accumulated demand in a narrow, scheduled window.

### 1.2 The reframe that matters

The difficulty is **not measurement**. The data exists. The difficulty is that overnight price
moves come from two sources with **opposite implications**:

| Source | Impact | Prediction at the open |
|---|---|---|
| **Information** — overseas news, scheduled releases, earnings | Permanent | **Continuation** |
| **Liquidity pressure** — someone needed to trade in a thin book | Transitory | **Reversal** |

Naive implementations fail because they cannot separate these. The signal averages a
continuation effect and a reversal effect and lands near zero. **Everything in this study is
built around that separation.**

### 1.3 Why an edge should persist here

At millisecond horizons this is the most contested part of the market and there is nothing
available. At **minutes-to-hours** — the realistic operating range — the competition is not
optimising for this horizon, the capacity is small enough to be uninteresting to anyone with a
research budget, and the data work is tedious. Those are the three durable barriers identified
in `ALPHA_PROGRAMME.md`: capacity, ugly data, effort.

**Expect a small, capacity-constrained edge, not a large one.**

---

## 2. The central confound

**Signed order flow imbalance and overnight return are mechanically linked.** Flow moves price.

Measuring imbalance by signed trade flow and then predicting the return that the flow *caused*
is regressing return on return. It will produce an excellent in-sample relationship that does
not trade. This is the single most likely way this study fails, and it fails *convincingly*,
which is worse.

Two independent defences, both to be built:

### 2.1 Book-state measures, not trade-flow measures

Depth asymmetry at the touch, queue imbalance, resting size skew. These describe **unexpressed
intent** rather than executed flow.

A book heavily bid-skewed at 09:25 **with no corresponding price move** is genuinely different
information from the same skew *after* the price has already run. The first says demand is
waiting; the second says demand has been satisfied.

### 2.2 Explicit residualisation

```
r_overnight = α + β·I + ε

unpriced  = ε                      # return not explained by observed imbalance
absorbed  = residual of I on r     # imbalance that did NOT move price
```

**`absorbed` is the more interesting quantity.** Imbalance the book absorbed without repricing
means depth was present — which says something about who is waiting on the other side.

Both `unpriced` and `absorbed` are candidate features. They must be tested separately, and each
costs a trial.

---

## 3. Feature construction

### 3.1 Bucketed overnight aggregation

Partition the overnight session into buckets (30 minutes as the pre-registered default; see §9
on why this is not to be swept).

For each bucket `k`:

```
OFI_k = signed order-flow imbalance from book updates   (Cont–Kukanov–Stoikov)
V_k   = volume
D_k   = mean depth at touch
σ_k   = realised volatility

x_k   = OFI_k / (D_k · sqrt(V_k / V̄_k))
```

**Normalisation is not optional.** Overnight volume varies by an order of magnitude across quiet
nights, event nights, holidays, and session overlaps. Without conditioning on expected volume
for that **time-of-night and day-of-week**, the feature primarily measures the calendar.

Build `V̄_k` as a trailing expectation by (bucket, weekday), estimated strictly out of sample.

### 3.2 Time-decayed aggregation

Flow at 09:25 is far more informative than flow at 02:00 — it is closer to the release of the
constraint and less likely to have already been absorbed.

```
I = Σ_k w_k · x_k,      w_k = exp( −(T_open − t_k) / τ )
```

**Ensemble `τ` over a small set of values rather than selecting one** (`FEATURE_RESEARCH.md` §7
item 2). Candidate set fixed in advance: τ ∈ {1h, 3h, 8h}, equally weighted. Costs **zero**
selection trials. Do not sweep τ.

### 3.3 The state-space decomposition — primary method

The permanent/transitory split in §1.2 is a **latent state estimation problem**. The natural
tool is a Kalman filter, and it is the structurally correct method rather than a fashionable one.

```
p_t = m_t + s_t
m_t = m_{t−1} + η_t            # permanent: efficient price, random walk
s_t = φ · s_{t−1} + ε_t        # transitory: pricing error, mean-reverting
```

Observed price is the sum; neither component is directly observed. The filter estimates both.

> **`s_t` evaluated at the open is the signal** — the accumulated pricing error that should
> revert once the cash market supplies depth.

This is the Hasbrouck permanent/transitory decomposition in state-space form.

**Two advantages over the regression version (§2.2):**
1. It handles the **sequential** structure properly rather than collapsing the night to one number.
2. It returns an **uncertainty estimate** on the state, usable directly for position sizing —
   size proportional to `s_t / SE(s_t)` rather than to `s_t` alone.

**Extension worth building:** condition the process noise `Var(η_t)` on observed order flow, so
incoming imbalance updates the state rather than only the price. This is the piece that makes it
more than a smoother.

**Engineering-transfer note.** This is state estimation of an unmeasurable disturbance from a
noisy output, with the process-to-measurement noise ratio setting adaptation speed. The
control-systems intuition transfers directly and is worth stating explicitly in any writeup —
it is a genuine differentiator against candidates who know only how to fit.

### 3.4 Candidate feature set (complete, fixed in advance)

| ID | Feature | Rationale |
|---|---|---|
| F1 | `I` — time-decayed normalised OFI | Direct imbalance measure |
| F2 | `unpriced` — return residual on `I` | Move not explained by observed flow |
| F3 | `absorbed` — imbalance residual on return | Flow the book absorbed without repricing |
| F4 | `s_t` — Kalman transitory component at open | Primary method; pricing error to revert |
| F5 | Book-state skew at 09:25 (depth asymmetry, queue imbalance) | Unexpressed intent, §2.1 |
| F6 | Opening auction imbalance (if data available — §6.1) | **Direct observation** of the constrained flow |
| F7 | Net derived mechanical flow (§4.2) | Published rules + published AUM; conditioning variable, not a signal |

**Nothing outside this list is tested without a new pre-registration entry.**

### 3.5 What the model outputs, and in what sense it is directional

Worth stating plainly, because it is easy to mistake this for a strategy with no directional view.

**The trade is directional.** The position is long or short, decided before entry. What the model
does *not* do is forecast the price move independently of state — nobody can. The forecast has
the form:

```
predicted return  =  sign  x  |overnight move|  x  strength
```

The **sign** comes from the state estimate; the **strength** is what the IC measures. This is the
same structure as every mean-reversion and momentum strategy in existence — trend following also
does not forecast direction absolutely, it takes the sign of the past return.

**Three independently signed sources:**

| Source | Sign from | Nature |
|---|---|---|
| Kalman transitory state `s_t` (F4) | Price above/below estimated efficient price → short/long | Estimated, with an uncertainty attached |
| Mechanical flow (§4.2) | Leveraged funds same-sign as `r`; band rebalancers opposite-sign | **Derived** from published rules |
| Book-state asymmetry (F5) | Depth skew at 09:25 | Observed |

Direction is therefore the **primary output**, not a gap in the model.

**Where the uncertainty actually sits** is in the *strength* — how much reversion, over what
horizon — which is what the IC decay curve in §7 is for.

**And this is why the dispersion arm (§5) multiplies rather than competes.** Position size is
direction divided by expected volatility. The two arms occupy different places in the same
expression:

```
position = sign(s_t, MechFlow, book) x strength x vol_target / ExpVol_open
           \_________ directional arm _________/           \__ dispersion arm __/
```

Sharpening the denominator raises realised Sharpe more than pushing directional IC from 0.03 to
0.04 would, because the denominator is estimated an order of magnitude more accurately.

---

## 4. Conditioning variables that decide the sign

The two hypotheses in §1.2 predict **opposite** directions. The separator must be **exogenous to
returns**, or the whole exercise is circular. Two candidates, both exogenous.

### 4.1 Scheduled news — the binary split

**Calendar-known, therefore exogenous by construction:**

| Condition | Source | Predicted effect |
|---|---|---|
| Scheduled overseas macro release overnight | Central bank and statistical agency calendars | Continuation |
| US pre-market scheduled release (CPI, payrolls, claims) | BLS/BEA calendar | Continuation |
| Major index constituent earnings overnight | Earnings calendar | Continuation |
| No scheduled event, thin book | Absence of the above | **Reversal** |

This is mechanism-based conditioning per `ALPHA_PROGRAMME.md` §10 — the split variable is a
published calendar, not something derived from performance. **Two states maximum** (news / no
news) at this sample size; do not subdivide further.

**Pre-registered prediction:** reversal on no-news nights, continuation on news nights, with the
no-news effect the larger and more reliable of the two.

### 4.2 Derived mechanical flow — the continuous split

Better than the binary news split, because it is **continuous** and computed from published
data rather than from returns.

**The derivation.** Certain participants at the open are mechanically obliged to trade, and both
the obligation and its direction follow from published rules applied to the overnight move:

| Agent | Trigger | Direction given overnight move `r` | Derivable? |
|---|---|---|---|
| **Leveraged ETF** | Daily reset, mandatory | **Same sign as `r`** | Fully — `(L² − L) · NAV · r` |
| **Target-band rebalancer** | Band breach vs prospectus target | **Opposite sign to `r`** | Yes, given target and band |
| Index fund with net creations | Cash inflow | Independent of `r` | Partly — needs a flow estimate |
| MOO retail / discretionary | Nothing mechanical | Unknown | No |

The first two carry **opposite signs**. A large overnight rally makes leveraged funds buyers and
band-rebalancers sellers; the net depends on relative AUM, which is estimable from filings but
not precise.

```
MechFlow(r) = Σ_agents  AUM_a · f_a(r)        # f_a from published rules
```

**Why this is a conditioning variable and not a signal.** The structural difference from the
producer-hedging derivation (`HEDGING_FLOW_DERIVATION.md`) matters:

> A producer's constraint is a **threshold in price space** — covenant ratios, breakeven levels.
> Price is an input to a constraint stated in price terms, so the constraint yields a **signed**
> reaction function.
>
> The cash-open participant's constraint is in **time, not price**. They cannot trade *until
> 09:30*, and there is no price level at which that binds differently. The constraint gives
> **timing with near-certainty and direction with none.**

So `MechFlow` does not predict the open. It measures **how much of the open is forced versus
discretionary**, which sharpens the §1.2 separation:

**Pre-registered prediction:** the reversal effect is **stronger when |MechFlow| is small**,
because the open is then dominated by discretionary participants rather than by agents trading
for reasons unrelated to value.

**Sign-stability requirement — mandatory before use.** AUM-by-category estimates are imprecise.
Apply the test from `HEDGING_FLOW_DERIVATION.md` §9: Monte Carlo over plausible AUM ranges and
check whether the **sign** of `MechFlow` is stable across them. If the sign flips within the
plausible range, the variable is too noisy to condition on — **fall back to §4.1 and record
that**. Do not attempt to tighten the AUM estimate instead.

**Honest note on crowding.** Unlike the producer derivation, this one is **commoditised**. Every
equity desk models cash-open mechanical flow, and the pre-open imbalance feeds are published to
everyone simultaneously — their entire purpose is to let liquidity providers respond before the
auction. The derivation is not the edge here.

The edge, such as it is, comes from **having done it at all**: most people building an overnight
reversal signal will not have assembled a mechanical-flow estimate, and will therefore be
averaging forced and discretionary opens together. That is a difference in care, not in insight.

---

## 5. The dispersion arm

### 5.1 Why this exists as a separate arm

The asymmetry established in `ALPHA_PROGRAMME.md` §13 applies with unusual force here:

| Quantity | Typical forecast R² |
|---|---|
| Return (first moment) | ~0.003 |
| Volatility (second moment) | ~0.3–0.5 |

A participant model (§4.2) delivers **known mechanical flow**. Known flow implies **predictable
volume**, and predictable volume implies **predictable dispersion**. The chain from a derived
quantity to a forecastable one is far shorter for the second moment than for the first.

**This arm carries no directional information and is valuable anyway.** Its output is the
denominator in position sizing, and it is directly actionable under a trailing drawdown limit: a
model saying "tomorrow's open has unusually wide dispersion" means *reduce size today*.

### 5.2 What the participant model predicts

Four quantities, all more forecastable than the mean:

| # | Prediction | Reasoning |
|---|---|---|
| D1 | **Conditional dispersion** is wide when mechanical flows **align**, narrow when they **offset** | Aligned forced flow must be absorbed by fewer willing counterparties |
| D2 | **Conditional skew** follows the sign of net one-directional forced flow | Forced flow is price-insensitive; absorption is not symmetric |
| D3 | **Tail asymmetry** follows the side with thinner absorption | Book depth is observable pre-open |
| D4 | **Timing within the session** — dispersion concentrates where the flow lands | Auction, first 10 minutes, close |

Each has a derived sign or shape. None requires estimating an impact coefficient, which is what
makes this arm cheaper than the directional one.

### 5.3 Construction

```
ExpVol_open = g( |MechFlow| ,  flow_alignment ,  overnight_sigma ,  book_depth_0925 ,  event_flag )
```

where:
- `|MechFlow|` and `flow_alignment` from §4.2 — derived, no free parameters
- `overnight_sigma` realised over the §6.4 session window
- `book_depth_0925` from the pre-open book
- `event_flag` from the §4.1 calendar

Fit as a **linear model on log realised dispersion**, one global specification across ES/NQ/RTY.
Volatility models are well-behaved and this does not need to be clever — resist the temptation
to reach for anything with latent states.

**Baseline to beat:** a plain EWMA of recent open-window realised volatility, by weekday. The
participant model earns its place only by beating that out of sample. Report both.

### 5.4 The two uses, and why the first matters more

**Use 1 — position sizing (primary).**

```
position = forecast_direction x vol_target / ExpVol_open
```

The arithmetic worth internalising: at IC around 0.03 on direction, **improving the volatility
forecast raises realised Sharpe by more than improving directional IC to 0.04 would.** The
dispersion arm therefore improves the directional strategy despite carrying no directional
content. This is the concrete instance of "most realised Sharpe improvement comes from modelling
risk well, not return."

**Use 2 — standalone (limited, futures-only).**

A dispersion forecast is naturally expressed in options, which are unavailable here. The
futures-only expressions are weak: scaling participation in other intraday strategies, and
flattening ahead of forecast-wide sessions. **Treat this as risk management, not as a strategy.**

### 5.5 Validation — the multi-prediction advantage

This is the methodological payoff of a structural model over a reduced-form fit.

The participant model makes **five** predictions: volume, dispersion (D1), skew (D2), tail
asymmetry (D3), timing (D4) — plus direction, in the other arm. **Test all of them.**

A model that predicts volume and dispersion well but direction badly is **not a failure**. It is
the model reporting which part of the mechanism is real, which a reduced-form fit cannot do. That
distinction is worth writing up explicitly: it reads as understanding rather than curve-fitting,
and it is the strongest argument for having built the structural version at all.

**Discipline, non-negotiable:** every agent parameter comes from **outside the price data** —
AUM from filings, rules from prospectuses, calendars from exchanges. The moment an agent
parameter is calibrated to match observed price behaviour, this becomes a fitted complex model
rather than a derived structured one, and the entire sample-efficiency advantage is gone. It is
the difference between measuring the masses independently and fitting them to match the
trajectory.

### 5.6 Trial cost

**2 trials**: one for the dispersion model versus the EWMA baseline, one for the skew and tail
predictions taken together. D4 (timing) is diagnostic.

Not counted against the directional budget in §9 — different target variable, separate
pre-registration.

### 5.7 Where it connects to §3.3

The state-space model already takes a known exogenous input:

```
m_t = m_{t-1} + B*u_t + eta_t        u_t = derived mechanical flow
```

This is **feedforward compensation** — the disturbance is known in advance, so the filter need
not infer it from the output. The dispersion arm supplies the other half: `Var(eta_t)`
conditioned on `|MechFlow|` and alignment, rather than held constant.

Both halves come from the same participant model, which is the argument for building it once
properly rather than bolting on two separate estimators.

---

## 6. Data

### 6.1 The measurement that would change everything

**Opening auction imbalance feeds.** NYSE and Nasdaq publish pre-open imbalance data in the
minutes before 09:30 — a **direct measurement** of the constrained flow this study theorises
about, rather than a proxy for it.

**Action:** check whether the Databento subscription covers XNAS/XNYS imbalance messages. If it
does, F6 becomes the primary feature and the study moves from inference to observation. This is
the first thing to establish, before any modelling.

### 6.2 Required

| Data | Use | Status |
|---|---|---|
| ES/NQ/RTY MBP-10 or MBO, full overnight session | Book state, OFI, depth | Held (Databento GLBX.MDP3) |
| Cash session prices, 09:30 onward | Target returns | Held |
| Scheduled macro release calendar | §4 conditioning | Free — BLS, BEA, central banks |
| Earnings calendar for large index constituents | §4 conditioning | Free / cheap |
| NYSE/Nasdaq opening imbalance | F6 | **Verify availability** |
| Exchange holiday and half-day calendar | Session definition | Free |
| Leveraged ETF AUM and multipliers | §4.2 `MechFlow` | Free — issuer daily disclosures |
| Fund target allocations and tolerance bands | §4.2 `MechFlow` | Prospectuses; imprecise by category |
| ETF creation/redemption baskets | §4.2 `MechFlow` | Published daily by issuers |

### 6.3 Provenance constraint — the clean sample is shorter than it looks

Per `DATA_EXPANSION_PLAN.md` §2.1: MBP-10 is the deepest schema available before the MDP 3.0
launch in **May 2017**, and timestamps in the backfilled period derive from the feed's
SendingTime field rather than a capture timestamp, because CME holds no PCAPs from before then.

**For book-state work the reliable window is 2017 onward — roughly nine years.**

Do not pool silently across the May 2017 boundary. Either restrict to post-2017, or run both and
report the difference. State the choice in the writeup; this is exactly the kind of limitation
that is more impressive disclosed than hidden.

### 6.4 Session boundary definition — a pre-registered decision

"Overnight" is ambiguous and the choices differ in content:

| Definition | Window | Content |
|---|---|---|
| A | Cash close 16:00 → cash open 09:30 | Includes the post-close futures session |
| B | Globex reopen 18:00 → cash open 09:30 | Excludes the post-close hour |
| C | European open → cash open | Focuses on the overlap session |

**Pre-registered default: B.** Rationale: the 17:00–18:00 halt is a clean natural boundary, and
including the post-close hour mixes cash-session aftermath with genuinely overnight flow.

A and C are **separate hypotheses with their own trial cost**, not alternatives to try.

Half-days, holiday sessions, and the maintenance break must be handled explicitly — exclude
them, pre-registered, on structural grounds rather than performance.

---

## 7. Targets

| Target | Window | Purpose |
|---|---|---|
| R1 | 09:30 → 10:00 | Immediate reversion / continuation |
| R2 | 09:30 → 10:30 | Primary |
| R3 | 09:30 → 16:00 | Full session; tests persistence |
| R4 | Opening auction print → 10:00 | Isolates post-auction behaviour |

Expect the horizon to matter substantially. Report the **IC decay curve across all four**
(`FEATURE_RESEARCH.md` §5.4) and read the holding period off it rather than selecting one.

Returns computed on the **tradeable price** — if the intended fill is at the open plus a
latency allowance, the target starts there, not at the official print.

---

## 8. Cost — the first test, not the last

At micro-contract notionals **a single tick of slippage is a large fraction of any plausible
edge**. MES is $1.25 per tick on roughly $30k notional; a 1-tick round-trip cost is ~8bp. An
intraday signal must clear that several times over.

**Run the break-even cost calculation (`FEATURE_RESEARCH.md` §6.5) before building anything
else.** If the top-minus-bottom spread from a crude first pass is within 2–3× of realistic
all-in cost, stop — no amount of modelling will rescue it.

Cost model must include:
- Commission per side (micro contracts, actual broker rate)
- Half-spread at the open — **wider than the intraday average**, and this matters
- Slippage on market orders into the opening minutes
- Realistic fill assumptions: no fills at the touch price; model queue position or assume
  crossing the spread

**Model costs from the Databento book data**, not from a flat assumption. This is the one place
in the whole programme where tick data earns its subscription, and doing it properly is itself a
portfolio artefact.

---

## 9. Trial budget and discipline

**Pre-registered budget: 9 trials.**

| Item | Trials |
|---|---|
| F1–F6 evaluated as features | 6 |
| News/no-news conditioning (§4.1) | 1 |
| MechFlow conditioning (§4.2) | 1 |
| Combination of surviving features | 1 |

**Not to be swept:**
- Bucket granularity (fixed at 30 min)
- `τ` (ensembled over a fixed set)
- Session definition (B, pre-registered)
- Kalman `φ` and noise ratio — estimated by maximum likelihood on training folds, **not tuned to
  performance**

Anything outside the list requires a new pre-registration entry and increments the count. If the
budget is exceeded, record the true number and accept the harsher DSR discount
(`FEATURE_RESEARCH.md` §6.2).

**Validation:** CPCV on the signal frame, walk-forward on the book frame
(`FEATURE_RESEARCH.md` §8.4). With ~2,250 sessions post-2017, N=8 groups, k=2, embargo of 5
sessions is a reasonable starting configuration.

---

## 10. Kill criteria — set now, before any results

Stop and record a negative result if:

1. **Break-even cost < 3× modelled all-in cost** (§8). Terminal.
2. **`I` explains >70% of overnight return variance** — the §2 confound dominates and the
   residual features are noise.
3. **IC t-stat < 3.0 after overlap correction** on every feature at every horizon.
4. **News/no-news conditioning shows no sign difference** — the mechanism in §1.2 is not
   operating, and whatever is left is unexplained.
5. **Effect present only pre-2017** — likely a data artefact from the backfill (§6.3), not a
   signal.

6. **`MechFlow` sign is unstable across plausible AUM ranges** (§4.2) — drop F7 and the §4.2
   conditioning, keep §4.1, and record the reason.

Criterion 4 is the mechanism test. Failing it matters more than failing 3, because a signal
without the predicted sign structure has no reason to persist.

---

## 11. Why this fits the constraints better than anything else in the programme

| Constraint | Fit |
|---|---|
| Futures only | Yes — ES/NQ/RTY micros |
| Prop hedging rules | **One position per instrument, directional.** No paired trades, no spreads |
| Trailing drawdown | **Flat overnight — removes the main gap-breach mechanism** |
| Minimum activity | Trades most sessions by construction |
| Quick turnaround | Data already held; no vendor purchase required |
| Algorithmic | Fully — scheduled window, rules-based entry and exit. **Verify each firm's automation policy**: some restrict fully unattended trading or require the trader to be present |
| Sim execution | Funded accounts are predominantly simulated (`PROP_LIQUIDATION_CASCADES.md` §0). Market orders into the open will fill differently in a sim engine than in the real book. **Maintain two cost models** — sim engine for prop, real book for personal capital — and do not let a sim-favourable fill assumption inflate the prop-side edge |

**The breadth argument reverses in your favour.** The first-passage analysis
(`ALPHA_PROGRAMME.md` §12.1) showed slow signals give 1–4 independent bets per evaluation
window, making the outcome close to a coin flip regardless of edge quality. An intraday strategy
trading daily across three instruments gives **hundreds**.

That is the single largest available lever on P(pass), and it is why this ranks ahead of
basis-momentum for the prop route specifically — notwithstanding that basis-momentum is the
better long-horizon research programme.

---

## 12. Sequence

1. **Verify opening auction imbalance data availability** (§6.1). Changes the design if present.
2. **Build the session definition and data layer.** Session B, holidays excluded, post-2017.
3. **Crude first pass on F1 only**, purely to run the break-even cost calculation (§8).
   **Gate: if cost kills it, stop here.** This is deliberately before any sophisticated modelling.
4. Build F2, F3 (regression residualisation), F5 (book state).
5. Build F4 (Kalman) — primary method, most work, do it once the cheaper features have shown
   the effect exists at all.
6. News/no-news and MechFlow conditioning (§4).
7. Full harness evaluation, IC decay across R1–R4, CPCV.
8. **Dispersion arm (§5)** — build after the directional features, because it is the sizing
   denominator for whatever survives. Can proceed even if the directional arm fails.
9. Combination and first-passage sizing if anything survives.

Step 3 is the important one. **It is cheap, it is decisive, and it is placed before the
interesting work on purpose** — the failure mode for this kind of study is building an elegant
Kalman filter for a signal that was never going to clear its costs.

---

## 13. Open questions

1. Does the Databento subscription include NYSE/Nasdaq opening imbalance? (§6.1)
2. Is the correct target the opening auction print or the first post-auction trade? (R4 vs R1)
3. Should ES, NQ and RTY be pooled or modelled separately? Pooling gains power; separating
   respects that their overnight participant bases differ. **Pre-register before running.**
4. Does the effect survive on micros specifically, where spreads are wider than the full-size
   contracts the effect would be measured on?
5. Is there a same-mechanism effect at the **European open** and the **cash close**? Natural
   extensions, separate hypotheses, separate trials.
6. **Leveraged ETF close rebalancing as a standalone candidate.** Fully mechanical, at the
   *close* rather than the open, horizon of minutes-to-the-bell rather than microseconds. Well
   documented and crowded, but the timing suits this programme better than the open does. Its
   own derivation and its own trial budget — not part of this study.

---

## 14. Honest position

The mechanism is sound and the constrained participant group is named and real. The data exists
and is already held. The fit to the prop constraints is the best in the programme.

Against that: the permanent/transitory separation is genuinely hard and is the whole problem;
cost is likely to be the binding constraint at micro notionals; and the clean sample is nine
years rather than the longer history available elsewhere.

**The programme has two arms with different odds.** The directional arm (§3, §4) is the harder
one and may not clear its costs. The dispersion arm (§5) rests on forecasting a second moment
rather than a first, is therefore far more likely to work, and is useful on its own as a sizing
input for every other intraday strategy in the book. **Build the directional arm first, but do
not treat its failure as the end of the study** — the dispersion arm survives it and is the more
reliable deliverable.

**The realistic outcome is a small, capacity-limited intraday edge with high breadth** — which
is exactly what the first-passage arithmetic says is worth more than a higher-Sharpe slow signal
for the purpose of passing an evaluation.

If it fails, it should fail at step 3 for a stated reason, cheaply, and that result is worth
writing up.
