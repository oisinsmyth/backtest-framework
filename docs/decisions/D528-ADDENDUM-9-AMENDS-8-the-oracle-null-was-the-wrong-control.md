# D528 ADDENDUM 9 — AMENDS ADDENDUM 8: the oracle null was the wrong control

Date: 2026-09-14. Runner: `working/d528_oracle_correct_control.py`.

**This amends ADDENDUM 8 §2.1–§3 and withdraws its central conclusion.** Nothing admitted (R15).
Micro universe, in sample only; reserved slice UNREAD.

**The principal caught this**, and the objection was exactly right: *"a null's purpose is to ask, is
this construction better than a randomised version of the construction. I can't understand how a
null with perfect foresight could work."*

---

## 1. What ADDENDUM 8's oracle null actually did, and why it could not answer the question

It sign-shuffled the path and then **re-derived the oracle on the shuffled path**, so it compared

> foresight on the real market **vs** foresight on a random walk

and concluded that because the shuffled arm scored higher (+$28.16 against +$23.92), "the ceiling
on detection is inside the null, so a better causal detector cannot help."

**That conclusion is withdrawn.** Two defects:

1. **Foresight pays on ANY series.** Knowing that a random walk will traverse a band lets you trade
   that traversal. The null therefore sits near its own ceiling by construction — it is a
   *saturated* benchmark, not a demanding one, and being below it means very little.
2. **The null's selector adapts to whatever path it is handed.** It is not "the same selection,
   randomised"; it is "an equally powerful selection, applied to noise". This programme's own rule
   is to **randomise the partner, not the membership**, and that a control must share the
   treatment's nuisance. This one shared neither.

**Exactly one inference survives, and it is narrow:** a random walk has nothing causally detectable
yet scored Sharpe +6.11 under foresight, so **a high oracle score does not by itself prove any of
it is causally reachable.** That is all. It says nothing about whether detection is worth pursuing.

## 2. The control it should have had

Keep the real data; randomise only **which** candidates are taken, with the count matched — 400
draws from the same pool. This asks the principal's question directly: *does knowing which windows
traverse beat picking at random?*

Candidate pool: 717 trades, P(target) 11.2%, gross −$1.21, net −$5.93.

| arm | window read | n | P(target) | win% | gross $ | random-matched p5 / p50 / p95 | verdict |
|---|---|---:|---:|---:|---:|---|---|
| `causal` | `[t−H, t)` | 109 | 11.0% | 21.1% | +3.00 | −5.39 / −1.34 / **+3.40** | inside |
| `oracle_h` | `[t, t+10)` **overlaps** | 98 | **57.1%** | 64.3% | **+23.92** | −5.86 / −1.39 / +3.67 | **ABOVE p95** |
| `oracle_tau` | `[t, t+40)` **overlaps** | 220 | 31.8% | 39.5% | +10.85 | −3.90 / −1.43 / +1.53 | **ABOVE p95** |
| `oracle_after` | `[t+40, t+50)` **disjoint** | 39 | 17.9% | 20.5% | +0.93 | −8.59 / −1.30 / +6.77 | inside |

### 2.1 The oracle's profit was OUTCOME knowledge, not REGIME knowledge

Both oracles whose window overlaps the trade's horizon beat the control enormously. The oracle
whose window begins only **after the trade has closed** does not. Self-test 1 asserts the
non-overlap on the indices: the disjoint window starts at `t+40` and every trade closes by `t+40`.

**Selecting windows in which price traverses inside the trade's own horizon is very nearly
selecting winning trades.** That was the "outcome overlap" flagged when the arm was first reported,
and it is the whole of the +$19.23.

## 3. What now stands, and how strongly

| claim | status |
|---|---|
| "a random walk with foresight earns more, so a better detector cannot help" | **WITHDRAWN** — wrong control |
| "the oracle's +$19.23 bounds what causal detection is worth" | **WITHDRAWN** — it is outcome knowledge |
| "the causal detector adds nothing over random selection" | **stands**: +3.00 against a p95 of +3.40 — inside, but *closer* than the sign-shuffle null implied |
| "regime knowledge alone is not demonstrably worth anything" | **weakly supported only**: `oracle_after` is inside its control, but on **n = 39** with a band spanning −8.59 to +6.77, and its point estimate (+0.93 vs a median of −1.30) is directionally *positive* |

**The confident negative of ADDENDUM 8 §3 — "there is no point searching for a causal predictor of
forward traversal" — is not supported by this evidence.** What the corrected control gives is a low
ceiling measured at n = 39: suggestive, badly underpowered, and not a basis for closing anything.

## 4. Disposition

1. **ADDENDUM 8's §2.1 null and its §3 conclusion are superseded by this record.** Its §1 (the
   premise check: lift −0.0345 at t = −25.08 on 441,848 bars) is untouched and still stands — that
   measurement used no oracle and no shuffle.
2. **The question of whether a better causal detector could pay is REOPENED**, and the honest way to
   settle it is to power `oracle_after` properly. At n = 39 on this fixture it cannot be settled;
   the multi-year 5-minute fixture is where it could be.
3. **No component line, no promotion**, and the reserved slice remains UNREAD.
4. **The lesson, stated so it survives this session:** an oracle arm needs a control that shares
   its data and randomises its *selection* — not one that re-derives the oracle on shuffled data,
   which is a different and much easier benchmark. And an oracle whose window overlaps the trade
   measures the outcome, not the regime; only a disjoint window bounds what regime knowledge is
   worth.
