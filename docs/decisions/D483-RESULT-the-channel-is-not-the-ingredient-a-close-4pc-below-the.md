# RESULT D483 — the channel is not the ingredient: a close 4% below the 30-bar low earns the same with no lines at all

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D483-RESULT-the-channel-is-not-the-ingredient-a-close-4pc-below-the-30-bar-low-earns-the-same-with-no-lines-at-all.md`. The H1 above is the full title.*

*Runner `scripts/run_d478_grow_trades.py` (`--rule dip`, `--rule dip --dip-drawn`,
`--rule level --head 20`); numbers `data/d483_dip_all.json`, `data/d483_dip_drawn.json`,
`data/d483_level_hold20.json`; logs `temp/d483_*.log`; spec
[D483](D483-the-dip-control-and-the-hold-20-null-does-the-channel-floor.md).
In-sample, the mining panel, 1,573 names; no holdout read. This is the record on which the
daily channel line closes — see the closing record.*

## 0. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 dip-all long, hold 5, earns most of it | +25 to +45 gross, above its null p95 | **+47.4 ± 10.1**, null p95 +18.6 — above; 2 bp past the range's top: the dip earns *all* of it |
| P2 dip-drawn adds little | within ±10 of dip-all | +45.2 vs +47.4: **−2.2** — held |
| P3 the level rule beats the dip by < 15 | | +43.6 vs +45.2: **−1.6** — held |
| P4 hold-20 level null: score above p95 by > 2 SE; book above p95 on return | | +112.8 vs p95 +76.9 (SE 1.8): 20 SE above; book +31.1% vs p95 +20.1% — held |
| P5 dip short near zero | −10 to +15 | **+24.3 ± 8.8** — missed: the reversal runs both ways |

## 1. The three readings side by side, long, gross bp

| hold | level rule on the channel (D482) | dip, no lines | dip, only where the channel is drawn |
|---|---|---|---|
| 1 | +6.2 ± 3.3 (n 16,933) | −32.3 ± 7.1 (n 12,192) | −19.1 ± 15.4 (n 2,015) |
| 3 | +26.5 ± 4.6 | +18.7 ± 9.3 | +23.6 ± 22.2 |
| **5** | **+43.6 ± 5.6**, median +58, net −34 | **+47.4 ± 10.1**, median +89, net −80 | **+45.2 ± 25.7**, median +56, net −99 |
| 10 | +56.4 ± 7.8 | +5.7 ± 13.6 | +58.9 ± 31.9 |
| 20 | +112.8 ± 10.7, net +37 | +121.2 ± 16.6, net +16 | +191.3 ± 40.5, net +72 |

Nulls at hold 5 (within-name time rotation, 200 draws): level +43.6 against p95 +27.1; dip-all
+47.4 against p95 +18.6; dip-drawn +45.2 against p95 +31.8. All three above. Shorts at hold 5:
level +11.4, dip-all **+24.3** (above its p95 −3.4), dip-drawn +16.2 (unresolved).

At hold 20 (D482's rule, the null moved there): long +112.8 against p50 +61.1 / p95 +76.9; book
long +31.1% at Sharpe 0.67, exposure 0.074, against p95 +20.1% and a Sharpe p95 of 0.62 — above
on return, level on Sharpe; 72 names to half the P&L, 14 of 17 years profitable. The dip with
no lines at hold 20: +121.2, net +16, no null run there.

## 2. Reading it

- **The floor of the channel is not doing anything.** A close 4% below the previous 30 bars'
  low, with no channel anywhere, earns the same over five bars (+47 against +44), and is above
  its own null. Restricting the dip to bars inside a live channel changes nothing (+45), and a
  fall inside a live channel is rare — nine in ten such falls break the channel. The one place
  the channel differs is the first day: the dip's first day is −32, the channel's +6, which is
  the channel's floor selecting falls that have already stopped; by day three the two are the
  same.
- **What D482 found is short-horizon reversal after a sharp break of a trading range, in both
  directions**: long +47 after a 4% break below, short +24 after a 4% break above, per-bar gross
  of 5–9 bp that persists to twenty bars, net negative until roughly fifteen. It is real on this
  panel by the programme's criterion and it is not new, and it does not need lines.
- **The channel added a drawing, a labelled set and a scorecard, and no information.** Five
  direction cells sat below their rotation nulls; the one level cell above its null is
  reproduced without the channel.

## 3. Audits carried

Each run: [V] extractor equality on all real trades within 2e-12 bp; [XV]; [F] with future
prices deleted as well as future levels; [S]; [M] `assert_matches_scorer`; [N] above 100 a side
in every headline cell. Event counts against D482's 15,603: dip-all 11,086, dip-drawn 1,961
(the depth was not tuned to match; the mismatch is reported, not hidden). Split-guard rejections
627 / 1,051 / 627.
