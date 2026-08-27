# The scaling ladder — D222

**Produced:** 2026-08-27 · **Reproduce:** `uv run python scripts/run_scaling_ladder.py` (offline, deterministic) ·
Record: [`D222`](docs/decisions/D222-does-the-fine-bar-advantage-grow-with-the-window.md) ·
Artifact: `data/scaling_ladder_summary.json`

Is the fine-bar residual **structure or noise**? A residual that is noise has no
reason to order itself by `k`. **Every rung scores on one shared span**, set by the
largest warm-up in the ladder, so a growing gap cannot be the later period.

## Δ(k) — the shape under test

| symbol | rung | k | native | 15m matched | **Δ** | bootstrap p5..p95 | resolvable |
|---|---|---:|---:|---:|---:|---:|:--:|
| BTCUSDT | 1h | 4 | +0.574 | +0.728 | **+0.155** | -0.059 .. +0.368 | no |
| BTCUSDT | 8h | 32 | +0.682 | +0.558 | **-0.124** | -0.336 .. +0.166 | no |
| BTCUSDT | 1d | 96 | +0.560 | +0.572 | **+0.012** | -0.139 .. +0.224 | no |
| ETHUSDT | 1h | 4 | +0.607 | +0.756 | **+0.148** | -0.082 .. +0.332 | no |
| ETHUSDT | 8h | 32 | +0.324 | +0.237 | **-0.087** | -0.302 .. +0.131 | no |
| ETHUSDT | 1d | 96 | +0.787 | +0.667 | **-0.120** | -0.347 .. +0.075 | no |

## Verdict

| hurdle | | holds |
|---|---|:--:|
| **K** | Δ > 0 at every k | no |
| **L** | Δ(4) < Δ(32) < Δ(96) | no |
| **M** | the Δ(96)−Δ(4) gap exceeds its own CI width | no |

**L without M is a pattern in noise.** Per symbol:

| symbol | K | L | M |
|---|:--:|:--:|:--:|
| BTCUSDT | no | no | no |
| ETHUSDT | no | no | no |

## Trading rate — N5

| symbol | rung | native RT/yr | 15m matched RT/yr |
|---|---|---:|---:|
| BTCUSDT | 1h | 226.0 | 221.7 |
| BTCUSDT | 8h | 29.0 | 27.4 |
| BTCUSDT | 1d | 8.3 | 8.6 |
| ETHUSDT | 1h | 228.3 | 229.7 |
| ETHUSDT | 8h | 28.7 | 29.9 |
| ETHUSDT | 1d | 9.5 | 8.5 |

**No config is promoted by this study.** It asks how an estimator behaves, not
whether an arm is tradeable.

