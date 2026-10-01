# D745 PRE-REGISTRATION — the abstention principle on the joint vault: where C1's, NQ F2's and D737's money falls by shock recency

*2026-10-01.*
- *The principal: "The whole point of this is not to find a particular construction … We are trying to find some
  underlying principle by witch a strategy abstains and then trades when its profitable"; then "Pre-register for the
  vault".*
- *Design choices, all the principal's:*
  - a shock is a top-5 % day;
  - D737 should show no ordering;
  - confirmation needs the direction AND the pooled test.
- *Numbered D745, the next free number (AITODO; the documentation-review session confirmed 745).*
- ***Committed alone, before its scorer exists. The scorer reads vault data and runs ONLY in the joint run, on the
  principal's word.***

## 0. The principle and why the test is in the vault

**The candidate principle** (POST HOC, from C1's mechanism, after an adversarial Fable 5.1 review):
- **A gate's value is to sit out the state in which the trade's payoff turns negative.** Done well, it keeps the
  dollars on fewer trades with a smaller drawdown. That is the principal's earn-when-it-trades standard.
- **For a cash-session continuation trade on NQ,** the state is shock recency:
  - **best** some weeks after a large move with quiet since ("OLD");
  - **worst** within a few sessions of one ("FRESH").
- **The state belongs to the payoff source.** A relative-value trade (NQ against the market) should not be sorted by
  it the same way.

**What the review established** (accepted; the memory `the-goal-is-an-abstention-principle`):
- **C1's two "conditions"** (ATR20 high; rv5/ATR20 low) **are one event:** a big day some weeks back and nothing since.
- **That event is mostly 2020 and 2022 in-sample,** so the in-sample data cannot separate the principle from those
  years (n_eff ≈ 5–10 episodes).
- **C1 earns the same dollars a year as every break** (\$1,025 vs \$1,086, D672). The gate bought drawdown, not
  dollars.
- **An in-sample test across books would re-open R15-closed lines** (D720/D721, D740/D742).

**So the clean test is data no one has read:** the joint vault, which scores C1, NQ F2 and D737 anyway. All three
trade one MNQ, so one NQ state series serves all three.

## 1. The state (one variable, three values; fixed now)

**The series** is NQ's RTH daily panel: D727's `panel_from_raw` over the rebuilt `fut_NQ_rth_1m`, the same panel D737
scores on.
- **The panel's own sessions are the clock:** the roll days it drops are absent, and the windows count panel sessions.
- **The load starts early enough** for 250 + 20 prior sessions before the first scored session.

**The definitions:**
- **A shock day:** the session's |ln(close₁₅:₅₉ / open₀₉:₃₀)| is at or above the 95th percentile of the previous 250
  panel sessions' values, strictly earlier.
- **The state of session t,** from sessions ≤ t − 1 only, so it is known at the open:
  - **FRESH:** a shock day among t − 5 … t − 1;
  - **OLD:** none among t − 5 … t − 1, and one among t − 20 … t − 6;
  - **NONE:** none among t − 20 … t − 1.

**In-sample frequencies** (counts only, no P&L, 2017–2023; `temp/principle/state_freq.py`):
- FRESH 22 %, OLD 26 %, NONE 52 %;
- 47 OLD episodes (median 11 sessions), about 7 a year.

**Expected in the vault:** about 18 OLD episodes over 2024-01 → 2026-09, about 10 over C1's 2025-03 → 2026-09.

## 2. The books (each exactly as its frozen vault step scores it)

| book | class | window | rebuilt through |
|---|---|---|---|
| **C1** (D680, slot 9) | cash-session continuation | 2025-03-01 → 2026-09-18 | D734's rebuild of the frozen D680 path |
| **NQ F2, book B** (D716, slot 7) | cash-session continuation (last hour) | D716's vault window | D734's rebuild of the frozen D716 path |
| **D737** (slot 1) | relative value (NQ against YM) | 2024-01-01 → 2026-09-18 | D737's frozen `cell` over its vault load |

**Before any state is joined**, the scorer must reproduce, trade for trade:
- `vault_d716_nq_f2_result.json` `parts.vault`;
- `vault_d680_vault.json` C1;
- `vault_d737_nq_leads_the_dow.json`.

It refuses if any differs or is missing.

**Units:**
- dollars at one MNQ net of each book's own frozen cost line;
- **y = net ÷ σ\$**, with σ\$ = the session's σ_oc × \$2 (D727's prior-20 RMS, known at the open). y puts F2's smaller
  moves and C1's larger ones on one scale.

## 3. The predictions (declared now)

**P1, the continuation books** (C1 and NQ F2, each on its own): **OLD has the highest mean net per trade and FRESH
the lowest,** i.e. mean y(OLD) > mean y(NONE) > mean y(FRESH). Dollars are reported beside y; y decides.

**P2, the pooled test:** C1's and F2's trades together, in y units.
- The statistic is Δ = mean y(OLD) − mean y(FRESH).
- The null is the **exact circular rotation of the state series** over the panel sessions of each book's window:
  - every offset;
  - each book's trades keep their sessions and P&L, and the state labels shift;
  - the rotation keeps the state's clustering.
- p = the share of offsets with Δ ≥ the observed value (offset 0 included).
- C1 and F2 are rotated by the same offset over their own windows. The windows differ, so the pooled statistic at
  offset k uses each book's own shift k.

**P3, the contrast:** D737's Δ (OLD − FRESH, in y) is **less than half** the pooled continuation Δ, or of the opposite
sign. The state should not sort a relative-value payoff the way it sorts continuation.

## 4. The readings

- **CONFIRMED:** P1 holds for C1 AND for F2, P3 holds, AND P2's p ≤ 0.05.
- **CONSISTENT:** P1 holds for both and P3 holds, but P2's p > 0.05. The direction is right and power is short.
- **REFUTED:** pooled Δ < 0 with the rotation's lower-tail p ≤ 0.05 (FRESH beats OLD); OR P1 fails in the opposite
  direction for both books (FRESH highest).
- **NOT CONFIRMED:** anything else.
- **A label beside the reading:** "GENERIC VOLATILITY, NOT PAYOFF-SPECIFIC" if P1 and P2 hold but P3 fails.

## 5. Reported, not in the rule

- **Per book, by state:** trades, mean, median, win rate, and total net in dollars and y; the number of OLD and FRESH
  episodes, and the P&L by episode.
- **The principal's standard view.** For each continuation book:
  - take-all, against the book that skips FRESH, against the book that trades only OLD;
  - total, \$ a year, net Sharpe and Sortino, max drawdown, and the share of sessions traded.
  - This answers "selectivity buys drawdown, not dollars" out of sample.
- **The in-sample column** (2017–2023 for F2 and D737; C1's 2018–2023), computed in the same run on the same code.
  It is labelled POST HOC context and is not evidence.
- **P2's null:** p50 and p95 beside Δ, and the number of offsets.

## 6. Assertions (the scorer's self-test must make each canary raise)

1. **Known answers:** the three vault outputs reproduced trade for trade (§2); the in-sample state frequencies of §1
   reproduced exactly on the in-sample panel.
2. **Lag:** the shock threshold uses only sessions strictly before t, and a loop re-implementation agrees on 40
   sampled sessions; the state of t reads only t − 1 back. A canary that lets the threshold include day t must
   disagree.
3. **The join:** state to trade by session string; a one-session shift must make the join audit raise.
4. **The rotation:** offset 0 equals the observed Δ; a planted state that labels the best trades OLD gives p < 0.01
   in the self-test.
5. **The seal:** it refuses without `--principals-word`, refuses a second opening, and reads nothing after
   2026-09-18.

## 7. The run, and what follows

**Order in the joint run:** after slot 7's `--vault`, slot 9's `--run-vault`, D734's `--vault` and D737's `--vault`.
- `uv run python scripts/vault_d745_abstention_principle.py --vault --principals-word "..."`.
- **Its freeze** hashes the scorer and the files it imports, before the joint run. `JOINT_RUN_CHECKLIST.md` gets the
  step, coordinated with the documentation-review session.

**The forward read:** the same scorer on the forward ledgers, a second, independent read on the principal's word. The
recorder now keeps the Globex inputs for C1 and F2 alongside D737's ledger. The read comes once each continuation book
has a year of forward trades (not before 2027-10).

**After the reading:**
- **CONFIRMED or CONSISTENT:** the principle ("sit out FRESH for cash-session continuation") becomes a candidate
  standing rule. Applying it to any book needs its own record.
- **REFUTED or NOT CONFIRMED:** recorded. The principle stays a C1 description, not a rule.

**Nothing changes a frozen vault rule.**

## 8. Predictions (Opus)

- **P(CONFIRMED) ≈ 0.15.**
- **P(CONSISTENT or better) ≈ 0.35.**
- **The likeliest failure:** F2 does not follow C1's ordering. F2 is a last-hour trade, and D720 found its weakest days
  were the forecast-big ones, which may sit in OLD as well as FRESH.

## WITHDRAWN before its freeze (2026-10-01)

*The principal: "Withdraw D745". It had been offered as the recommendation, after "Amend to a new state first" found
no state to amend to. **No freeze was written; the vault was not read and is not spent on this record.***

### Why: the declared state does not reproduce the in-sample pattern

**The scorer's rehearsal** (`data/rehearsal_d745_abstention_principle.json`, in-sample ≤ 2023-12-29, POST HOC) was
run on the exact declared definition:
- **The state counts** reproduce §1 exactly: FRESH 366, OLD 447, NONE 878.
- **The reading is NOT CONFIRMED.** P1 fails for C1 and for F2; P3 fails.
- **P2:** pooled OLD − FRESH = −0.022 in y, p_high 0.665 over 1,464 offsets (null p50 −0.000, p95 0.093).
- **By state,** mean y and mean \$ net:

  | book | OLD | NONE | FRESH |
  |---|---|---|---|
  | C1 | 0.012, \$8.4 | **0.096**, \$19.8 | 0.014, \$21.7 |
  | F2 | 0.053, \$19.8 | 0.021, \$5.3 | **0.059**, \$34.7 |

**What it shows.** C1 does best with no recent shock, and F2 right after one. The round-2 diagnostics §0 drew on
used other definitions: the largest move in absolute bp, the shock's direction, dollars. The "post-shock" edge was
mostly dollar scale. **The predictions were declared without computing the declared statistic in-sample first.**
That is my error; the memory `check-the-declared-state-reproduces-the-in-sample-finding` records it.

### No candidate state sorts both continuation books

**The search.** The principal's first choice was an amendment A1 to a state that does reproduce the pattern.
`scripts/d745_candidate_states.py` → `data/d745_candidate_states.json` (POST HOC) searched the open-known candidates on
the scorer's books, panel and units.

**The candidates:**
- **Shock recency and sessions since a shock are one split.** The JSON asserts it on every book; they sort C1 and F2
  oppositely.
- **Volatility level** (the walk-forward percentile of σ_oc / open) sorts F2 in y (low −0.025 → high 0.072) but not
  C1 (0.048 / 0.079 / 0.044). In dollars every book rises with it, which is scale.
- **Compression** (prior-5 against prior-20 open-to-close RMS) is the only one that orders C1 and F2 the same way.
  Low minus high tercile, in y, against the exact rotation of the tercile labels:

  | | Δ | p_high | null p50 / p95 | offsets | years positive |
  |---|---|---|---|---|---|
  | C1 | 0.139 | **0.022** | −0.002 / 0.108 | 1,464 | 3 of 6 (1–7 high-tercile trades a year) |
  | F2 | 0.020 | 0.383 | 0.002 / 0.093 | 1,379 | 2 of 6 |
  | D737 (contrast) | 0.023 | 0.340 | −0.001 / 0.094 | 1,941 | 5 of 7 |
  | C1 + F2 pooled | 0.065 | 0.069 | −0.001 / 0.071 | 1,464 | |

**What compression shows:**
- **Only C1 is sorted, and its own gate selects on the same quantity** (rv5 / ATR20 low). That is why its trades bunch
  in the low tercile (190 / 105 / 26).
- **F2 is not sorted,** and the contrast book is sorted as much as F2.
- **A C1-only amendment would confirm C1's construction, not a principle across books.** Per-book states would be
  per-book filters, and F2's filter lines are closed (R15; D738, D740).

### What this leaves (POST HOC, not evidence)

**On the in-sample books, no single open-known state sorts the continuation books' payoff the same way.** Each
abstention edge found so far stays with the construction it came from: C1's gate here; C1's skip days on D735's legs
in D743. **The "underlying principle" is therefore unsupported in-sample, and §0's candidate is not carried
forward.** A new candidate needs a new record. Its declared statistic must reproduce its in-sample pattern before it
is declared.

**The scorer** `scripts/vault_d745_abstention_principle.py`:
- is committed as evidence;
- its self-test passes;
- `--freeze` and `--vault` refuse with exit 3.

`JOINT_RUN_CHECKLIST.md` gets no D745 step. **Nothing changes a frozen vault rule.**
