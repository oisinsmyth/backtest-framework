# Figures

**Six pictures, none of them of a strategy.** Each one is about the *instrument* — what the guards
caught, what the nulls said, what the ledger proves, what the registry knows. They are generated
from tracked artifacts and every number on them is pinned to its source by a test.

```bash
uv run python scripts/figures/build_all.py --check   # fails if any of the twelve has drifted
uv run python scripts/figures/build_all.py --build   # regenerate
```

`tests/unit/test_figures.py` asserts the mechanics every figure shares and
`tests/unit/test_figure_<name>.py` asserts what each one claims. A figure is a number in a
picture, and a number in a picture is quoted and never re-derived — so the gate treats it the way
this project treats every other headline number.

---

## The six

| | Figure | What it shows | Built from |
|---|---|---|---|
| 1 | [`dsr-hurdle-vs-look-count`](dsr-hurdle-vs-look-count.svg) | The noise floor a selected result must clear rises with the look count. The MACD ladder's best cell clears at 42 looks and fails at 45,783 — and stops being publishable at **1,086**, which nobody had noticed because nobody had drawn the curve | [`macd_ladder_summary.json`](../../data/macd_ladder_summary.json) + [`validation/dsr.py`](../../src/backtest_framework/validation/dsr.py) |
| 2 | [`lookahead-before-after`](lookahead-before-after.svg) | D279's look-ahead fix removing the edge it appeared to find: three selected cells fall by up to 3.01 Sharpe and cross zero, **eight unselected cells are bit-identical**, and two recorded survivors become none | [`d279_concentrated_summary.json`](../../data/d279_concentrated_summary.json) and its `WITHDRAWN_lookahead` twin |
| 3 | [`two-nulls-one-statistic`](two-nulls-one-statistic.svg) | One observed statistic, 22.0564, decisive against one null and UNRESOLVED against another — D373's rule that a margin inside 2 SE is not a pass, made visual | [`d393_aprime_null.json`](../../data/d393_aprime_null.json), [`d393_b_null.json`](../../data/d393_b_null.json) |
| 4 | [`cross-engine-agreement`](cross-engine-agreement.svg) | Agreement with vectorbt on two axes: divergence four decades above float noise and six below the tolerance, and — the part that matters — the **same 1,370 of 2,515 re-size decisions**, with an empty difference row | [`cross_engine_residuals.json`](../../data/cross_engine_residuals.json) |
| 5 | [`cost-waterfall`](cost-waterfall.svg) | Every dollar between the golden master's 100,000 and its 100,149.6537 final NAV — commission, spread, borrow, margin interest and a dividend debit, each hand-computed | [`test_the_golden_master.hand.json`](../../tests/golden/test_the_golden_master.hand.json) |
| 6 | [`golden-master-ledger-diff`](golden-master-ledger-diff.svg) | The hand ledger beside the engine's own, bar by bar, with a Δ column of real zeros — and a separated band for the five rows **the engine does not publish at all** | the hand ledger + [`golden_master_ledger.json`](../../data/golden_master_ledger.json) |

Figure 1 is the one in `README.md`. Figure 6 is the thesis but is a table, and a table is
unreadable at the width a README gives it.

---

## Three limits, stated rather than hidden

**The theme can be wrong, and nobody has solved it.** Each figure ships twice —
`<name>.svg` and `<name>.dark.svg` — and `README.md` chooses between them with
`<picture media="(prefers-color-scheme: dark)">`. That media query tracks the **operating
system**, not GitHub's own light/dark toggle. A reader on a dark OS with GitHub set to light gets
the dark figure on a light page. Every figure paints its own background first, so the failure is a
dark card on a light page rather than invisible text, but it is a real failure and this is where
it is written down.

**The fonts are not the ones asked for.** A standalone SVG gets no external resources, so
`IBM Plex Sans Condensed` is never what renders; `"Arial Narrow"` is absent on most Linux and
Android, and the substitute is *wider* than the condensed face the layout was designed in.
`tests/unit/test_figures.py::test_no_label_runs_off_the_edge` estimates every label at 0.62em per
character — deliberately above the widest realistic substitute — and fails a label that would
have only just fitted rather than one that runs off a reader's screen.

**On a phone they are small.** These are 880–900 units wide and scale to fit their container, so
at a 390px viewport everything renders at about 0.44× and 9-unit label text lands near 4px. The
shapes still read — a curve crossing a line, a column of flat controls beside three that collapse
— and the numbers do not. Tapping the image on GitHub opens it full size, which is the only
mitigation there is; the alternative is six figures designed for a phone and wasted on a desktop.
The `alt` text on the one embedded in `README.md` states its finding in words for exactly this
reason, rather than describing the picture.

---

## Adding one

1. Write `scripts/figures/build_<name>.py` on the pattern of
   [`build_dsr_hurdle.py`](../../scripts/figures/build_dsr_hurdle.py): `SLUG`, `SOURCE`,
   `GENERATOR`, a `facts()` that computes everything drawn, `render(theme)`, `files()`.
2. Register it in `build_all.BUILDERS`. The list is explicit rather than a glob, so that
   forgetting is loud.
3. Write `tests/unit/test_figure_<name>.py` asserting what the figure *claims*, not that it
   rendered. Recompute every derived quantity from the artifact; never trust a summary field.
4. Add a row above, and a row to this table only — `tests/unit/test_figures_index_is_complete.py`
   fails if a file here is unlisted or a listed file is missing.

Colours come from [`docs/results/final_report.html`](../results/final_report.html), parsed rather
than copied, and the drawing functions take token names rather than colours — so a hex literal
raises at build time instead of rendering one theme's ink on the other theme's ground.
