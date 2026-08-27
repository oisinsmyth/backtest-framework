# The assembled strategy — D224

**Produced:** 2026-08-27 · **Reproduce:** `uv run python scripts/run_assembled_strategy.py` (offline, deterministic, seed 0) ·
Record: [`D224`](docs/decisions/D224-the-assembled-strategy.md) ·
Artifact: `data/assembled_strategy_summary.json`

15m bars, Impulse acceleration `(136, 36)` (k=4, a 33-hour channel) · volume gate `EMA(200) > SMA(200)` on entry only · trailing ratchet at 2×ATR(56) · net of 10 bp per side.

## The factorial

| symbol | cell | gate | stop | net Sharpe | net total | gross Sharpe | RT/yr | hold | trades |
|---|---|:--:|:--:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | A_parent | - | - | -0.284 | -64.2% | +0.735 | 222 | 63 | 1,842 |
| BTCUSDT | B_gate | y | - | +0.205 | 75.6% | +0.882 | 112 | 67 | 927 |
| BTCUSDT | C_stop | - | y | -3.173 | -97.9% | -0.133 | 222 | 7 | 1,842 |
| BTCUSDT | D_gate_and_stop | y | y | -2.355 | -88.4% | -0.333 | 112 | 7 | 927 |
| ETHUSDT | A_parent | - | - | -0.006 | -2.9% | +0.813 | 228 | 60 | 1,891 |
| ETHUSDT | B_gate | y | - | +0.584 | 724.3% | +1.096 | 111 | 68 | 923 |
| ETHUSDT | C_stop | - | y | -2.019 | -96.3% | +0.303 | 228 | 7 | 1,891 |
| ETHUSDT | D_gate_and_stop | y | y | -0.984 | -70.7% | +0.498 | 111 | 8 | 923 |

## Hurdle H — the matched-count random null

Because the parent's average trade does not cover its fees, **removing trades at
random gains money**. A cell that improves net PnL without clearing this null has not
shown selectivity — it has traded less.

| symbol | cell | removed | net Sharpe | null p95 | pct in null (Sh / $) | **H** | beats parent |
|---|---|---:|---:|---:|---:|:--:|:--:|
| BTCUSDT | B_gate | 915 | +0.205 | +0.200 | 96 / 96 | PASS | yes |
| BTCUSDT | C_stop | 0 | -3.173 | +nan | nan / nan | FAIL | no |
| BTCUSDT | D_gate_and_stop | 915 | -2.355 | +0.200 | 0 / 0 | FAIL | no |
| ETHUSDT | B_gate | 968 | +0.584 | +0.404 | 100 / 100 | PASS | yes |
| ETHUSDT | C_stop | 0 | -2.019 | +nan | nan / nan | FAIL | no |
| ETHUSDT | D_gate_and_stop | 968 | -0.984 | +0.404 | 0 / 7 | FAIL | no |

## Hurdle G — the multiplicity floor

**`var_trials` is taken from the simulated null, not from this study's own cells.**
D219's amendment recorded that a sweep containing real effects inflates it; here that
is extreme — `C_stop`'s −3.17 is a genuine effect, and using the cells puts the floor
at **+4.9 annualised**, which is not a noise floor for anything. The matched-count
null IS the null distribution, so its variance is the right estimate.

| symbol | cell | net Sharpe | null sd | floor @ 10 (fresh) | floor @ 3,833 (verdict) | G |
|---|---|---:|---:|---:|---:|:--:|
| BTCUSDT | B_gate | +0.205 | 0.243 | +0.383 | +0.880 | FAIL |
| BTCUSDT | D_gate_and_stop | -2.355 | 0.243 | +0.383 | +0.880 | FAIL |
| ETHUSDT | B_gate | +0.584 | 0.255 | +0.401 | +0.923 | FAIL |
| ETHUSDT | D_gate_and_stop | -0.984 | 0.255 | +0.401 | +0.923 | FAIL |

## Interaction — is the stack worth more than its parts?

| symbol | best single component | full stack (D) | **interaction** |
|---|---:|---:|---:|
| BTCUSDT | +0.205 | -2.355 | **-2.561** |
| ETHUSDT | +0.584 | -0.984 | **-1.568** |

**Cells that clear selectivity and beat the parent, but not the multiplicity
floor: B_gate/BTCUSDT, B_gate/ETHUSDT.** That is D214's pattern — a
result publishable as a first study is not publishable as the n-th look.

**Survivors: 0.** Minimum detectable effect on this fixture is
**0.18 Sharpe** (D222); anything smaller is not a finding here.

