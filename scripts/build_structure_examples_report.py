"""Assemble docs/results/structure_trade_examples.html.

The head — fonts and the whole stylesheet — is lifted verbatim from final_report.html so
the two reports are the same document, not two documents that resemble each other. Numbers
are quoted from data/structure_examples_summary.json and pinned by
tests/unit/test_structure_examples.py.
"""
from pathlib import Path
import json

REPO = Path(__file__).resolve().parents[1]
src = (REPO / "docs/results/final_report.html").read_text(encoding="utf-8")
head = src[: src.index("</style>") + len("</style>")]
head = head.replace("<title>Nothing Worked</title>", "<title>Four Basis Points</title>", 1)

d = json.load(open(REPO / "data/structure_examples_summary.json", encoding="utf-8"))
B = d["per_symbol"]["BTCUSDT"]
E = d["per_symbol"]["ETHUSDT"]
LOW = d["lowest_cost"]

GOLD = 0.618


def band(e):
    """0.5 ATR as a fraction of the leg, and the retracement range it covers."""
    frac = 0.5 * e["entry"]["atr"] / abs(e["leg"]["span"])
    return frac, GOLD - frac, GOLD + frac


def row(label, e):
    o, r, en, ex = e["outcome"], e["risk"], e["entry"], e["exit"]
    return (
        f'      <tr><td class="name">{label}</td>'
        f'<td>{e["side"]}</td>'
        f'<td>{en["timestamp"][:10]}</td>'
        f'<td>{en["retracement"]:.3f}</td>'
        f'<td>{r["distance_atr"]:.2f}</td>'
        f'<td>{r["distance_pct"]:.3%}</td>'
        f'<td>{o["gross_r"]:+.2f}</td>'
        f'<td class="hi">{o["cost_r"]:.2f}</td>'
        f'<td>{o["net_r"]:+.2f}</td>'
        f'<td>{ex["reason"]}</td></tr>'
    )


bb, bm, bw = B["best"], B["median"], B["worst"]
eb, em, ew = E["best"], E["median"], E["worst"]

bb_frac, bb_lo, bb_hi = band(bb)
bw_frac, bw_lo, bw_hi = band(bw)
ew_frac, ew_lo, ew_hi = band(ew)
em_frac, em_lo, em_hi = band(em)
eb_frac, eb_lo, eb_hi = band(eb)

gap_to_618 = abs(bb["entry"]["price"] - bb["levels"]["fib_618"])
low_target_pct = LOW["risk"]["target_price"] / LOW["entry"]["price"] - 1.0

body = f"""

<div class="page">

  <header class="masthead">
    <p class="eyebrow">Backtest Framework &middot; Structure Programme</p>
    <h1>Four basis points from the stop</h1>
    <p class="standfirst">Seven worked examples from the strategy exactly as taught &mdash; change of character, flipped level, 61.8&percnt; retracement, fair value gap, all four agreeing on one bar. Chosen by a rule fixed before any outcome was looked at. The worst trade in the book is not a bad prediction; it is a fee bill.</p>
    <p class="byline">
      <span>222 stacked trades</span>
      <span>D204 &ndash; D212</span>
      <span>24 Aug 2026</span>
    </p>
  </header>

  <section>
    <h2>What you are looking at</h2>
    <p class="kicker">The full confluence arm, 15-minute bars, eight years</p>
    <p class="lead">Every trade below comes from the arm the course actually teaches: a change of character, then a pullback where the flipped level, the 61.8&percnt; retracement and a fair value gap all hold <em class="term">at the same bar</em>. 118 such trades on <code>BTCUSDT</code> and 104 on <code>ETHUSDT</code> over eight years of 15-minute bars.</p>
    <p>The wrapper is identical in every one and never varies: stop at the origin of the impulse leg, target at 5R, a channel trail once 1R in profit, a 60-bar cap. Entry is a market order at the close of the signalling bar. Costs are 40&nbsp;bps <strong>per side</strong>, so a round trip pays 80.</p>
    <p>Two numbers set the frame. At the measured costs this arm needs a <span class="num obs">40.2&percnt;</span> hit rate on BTC and <span class="num obs">33.5&percnt;</span> on ETH just to break even at a 5R target. It achieves <span class="num">11.0&percnt;</span> and <span class="num">15.4&percnt;</span>.</p>
  </section>

  <section>
    <h2>How these seven were chosen</h2>
    <p class="kicker">The rule, written down before the outcomes were read</p>
    <p>Examples are the easiest thing in a study to cherry-pick, so the selection is mechanical and was fixed in the extraction script before anything was inspected: per symbol, the <strong>best</strong>, <strong>median</strong> and <strong>worst</strong> trade by net R; then, pooled across both symbols, the trades with the <strong>highest</strong> and <strong>lowest cost in R</strong>.</p>
    <p>That names eight slots and yields seven trades, because the highest-cost trade in either book <em class="term">is</em> BTC's worst. Which is itself the finding: on this rule the worst outcome and the most expensive one are the same event.</p>
  </section>

  <div class="bleed">
    <figure>
      <div class="scroll">
        <table>
          <caption>Seven trades, full confluence arm, 40&nbsp;bps per side</caption>
          <thead>
            <tr><th>Trade</th><th>Side</th><th>Date</th><th>Retrace</th><th>Stop (ATR)</th><th>Stop (&percnt; px)</th><th>Gross R</th><th>Cost R</th><th>Net R</th><th>Exit</th></tr>
          </thead>
          <tbody>
{row("BTC best", bb)}
{row("BTC median", bm)}
{row("BTC worst", bw)}
{row("ETH best", eb)}
{row("ETH median", em)}
{row("ETH worst", ew)}
{row("Cheapest", LOW)}
          </tbody>
        </table>
      </div>
      <figcaption>Cost in R is the 80&nbsp;bp round trip divided by the distance to the stop. Where it exceeds 1.00 the fee is larger than everything the trade was risking.</figcaption>
    </figure>
  </div>

  <section>
    <h2>BTCUSDT</h2>
    <p class="kicker">118 trades &mdash; best, median, worst</p>
  </section>

  <div class="bleed">
    <ul class="findings">
      <li>
        <span class="rec">BEST</span>
        <span><strong>The strategy working exactly as advertised &mdash; and the golden ratio is not really in it.</strong> A change of character, a 12-bar impulse down {bb["leg"]["span_pct"]:.2%}, a pullback into a fair value gap {bb["levels"]["gap_width_atr"]:.2f}&nbsp;ATR wide, a stop {bb["risk"]["distance_atr"]:.2f}&nbsp;ATR away at the leg&rsquo;s origin, and a clean 5R banked {bb["exit"]["bars_held"]} bars later for <span class="num obs">{bb["outcome"]["net_r"]:+.3f}R</span> net. It is a good trade. But it filled at a <strong>{bb["entry"]["retracement"]:.1%}</strong> retracement, not 61.8&percnt;: the 0.618 level sat at <code>{bb["levels"]["fib_618"]:,.2f}</code> and price closed <code>{gap_to_618:,.2f}</code> below it. The touch band is half an ATR &mdash; <code>{0.5*bb["entry"]["atr"]:,.2f}</code> on a leg of <code>{abs(bb["leg"]["span"]):,.2f}</code>, or <strong>{bb_frac:.1%} of the entire move</strong>. &ldquo;Price touched the golden ratio&rdquo; was true anywhere between the {bb_lo:.0%} and {bb_hi:.0%} retracement.</span>
      </li>
      <li>
        <span class="rec">MEDIAN</span>
        <span><strong>A textbook loss, correctly handled, and still half fee.</strong> Short at {bm["entry"]["retracement"]:.1%} into the leg, stop {bm["risk"]["distance_atr"]:.2f}&nbsp;ATR away, 5R target below. Price went {bm["outcome"]["mfe_r"]:+.2f}R in favour, turned, and paid the stop {bm["exit"]["bars_held"]} bars later. Nothing went wrong: gross <span class="num">{bm["outcome"]["gross_r"]:+.2f}R</span> is exactly one unit of planned risk. What makes it a losing business is the line beneath &mdash; <span class="num obs">{bm["outcome"]["cost_r"]:.3f}R</span> of fees on that 1R, so the median trade hands back {bm["outcome"]["cost_r"]/1.0:.0%} of its risk before the market is consulted.</span>
      </li>
      <li>
        <span class="rec">WORST</span>
        <span><strong>The worst trade in the book is not a bad prediction. It is a fee bill.</strong> Gross it lost <span class="num">{bw["outcome"]["gross_r"]:+.2f}R</span> &mdash; an ordinary stop-out, identical to the median. The difference is that the entry filled <code>{bw["risk"]["distance"]:,.2f}</code> from its stop on a <code>{bw["entry"]["price"]:,.2f}</code> bitcoin: <strong>{bw["risk"]["distance_pct"]:.3%} of price</strong>, {bw["risk"]["distance_atr"]:.2f}&nbsp;ATR. An 80&nbsp;bp round trip against a {bw["risk"]["distance_pct"]*10000:.1f}&nbsp;bp stop is <span class="num obs">{bw["outcome"]["cost_r"]:.3f}R</span>, and no position size makes that tradeable. The setup was textbook: change of character, {bw["entry"]["retracement"]:.1%} retracement, inside a fair value gap {bw["levels"]["gap_width_atr"]:.2f}&nbsp;ATR wide, all three filters agreeing. They agreed on a trade whose entire risk was smaller than the spread. Its recorded {bw["outcome"]["mfe_r"]:+.2f}R best excursion is the same tininess from the other side &mdash; the excursion window includes the entry bar, whose own fifteen minutes are nine times a six-dollar stop. At this scale every number in R is noise.</span>
      </li>
    </ul>
  </div>

  <section>
    <h2>ETHUSDT</h2>
    <p class="kicker">104 trades &mdash; best, median, worst</p>
  </section>

  <div class="bleed">
    <ul class="findings">
      <li>
        <span class="rec">BEST</span>
        <span><strong>The mirror of BTC&rsquo;s best, five years later and the other way up.</strong> A long at {eb["entry"]["retracement"]:.1%} into a 6-bar impulse, a fair value gap {eb["levels"]["gap_width_atr"]:.2f}&nbsp;ATR wide, stop {eb["risk"]["distance_atr"]:.2f}&nbsp;ATR below at the leg&rsquo;s origin, target reached in {eb["exit"]["bars_held"]} bars for <span class="num obs">{eb["outcome"]["net_r"]:+.3f}R</span>. A real 5R, and the tightest the 61.8&percnt; band gets in this set &mdash; half an ATR here is only {eb_frac:.1%} of the leg, so the level meant something closer to what the course claims. The fee still took <span class="num">{eb["outcome"]["cost_r"]:.3f}R</span>. Fees are not why this trade fails, because it does not fail. They are why the 103 around it do.</span>
      </li>
      <li>
        <span class="rec">MEDIAN</span>
        <span><strong>Deeper than the golden ratio, and it made no difference.</strong> Entered at a <strong>{em["entry"]["retracement"]:.1%}</strong> retracement &mdash; well past 61.8&percnt;, and still inside the band, which here reaches to {em_hi:.0%}. Price never moved more than <span class="num">{em["outcome"]["mfe_r"]:+.2f}R</span> in favour and stopped out in {em["exit"]["bars_held"]} bars. The wrapper did nothing wrong and the entry was simply not predictive. This is what the middle of 104 perfect-confluence setups looks like.</span>
      </li>
      <li>
        <span class="rec">WORST</span>
        <span><strong>The same defect as BTC&rsquo;s worst, on a different asset in a different year.</strong> A {ew["leg"]["span_pct"]:.2%} impulse leg &mdash; six dollars on a <code>{ew["entry"]["price"]:,.2f}</code> ether &mdash; with the entry <code>{ew["risk"]["distance"]:,.2f}</code> from its stop, <strong>{ew["risk"]["distance_pct"]:.3%} of price</strong>. Cost <span class="num obs">{ew["outcome"]["cost_r"]:.3f}R</span>. That the two worst trades in two independent books are the same shape is the point: the leg&rsquo;s origin can sit arbitrarily close to the pullback entry, and nothing anywhere in the rule prevents it. There is no minimum stop, because the course never mentions one.</span>
      </li>
    </ul>
  </div>

  <section>
    <h2>The cheapest trade the rule ever produced</h2>
    <p class="kicker">Everything about the cost structure going right</p>
  </section>

  <div class="bleed">
    <ul class="findings">
      <li>
        <span class="rec">LOW</span>
        <span><strong>When the fees are as small as they ever get, the trade makes a sixth of one unit of risk.</strong> A {LOW["leg"]["span_pct"]:.2%} impulse leg puts the stop {LOW["risk"]["distance_atr"]:.2f}&nbsp;ATR away, so the round trip costs only <span class="num obs">{LOW["outcome"]["cost_r"]:.3f}R</span> &mdash; the lowest of all {d["pooled_n"]} stacked trades in both books. Price drifted the right way, never came near the 5R target {low_target_pct:.1%} above, and closed at the 60-bar cap for <span class="num">{LOW["outcome"]["gross_r"]:+.3f}R</span> gross. Net <span class="num">{LOW["outcome"]["net_r"]:+.3f}R</span>. This is the ceiling of the friendly case.</span>
      </li>
    </ul>
  </div>

  <section>
    <h2>Three things the examples show</h2>
    <p class="kicker">Each visible in the numbers above, not inferred from them</p>
  </section>

  <div class="bleed">
    <ul class="findings">
      <li>
        <span class="rec">1</span>
        <span><strong>The stop can be arbitrarily tight and the rule does not care.</strong> Stop distance is the unretraced part of the leg, so a deep entry on a small leg leaves almost nothing between fill and stop. Across the two books that produces trades risking <span class="num">{bw["risk"]["distance_pct"]:.3%}</span> and <span class="num">{ew["risk"]["distance_pct"]:.3%}</span> of price, on which an 80&nbsp;bp round trip is twenty times the risk. <strong>67&percnt; of BTC&rsquo;s stacked trades and 50&percnt; of ETH&rsquo;s cost at least their entire risk to put on.</strong> A minimum-stop filter would fix it and would also be a new parameter the course never states.</span>
      </li>
      <li>
        <span class="rec">2</span>
        <span><strong>The 61.8&percnt; level is a band, and the band is up to a quarter of the leg on each side.</strong> The touch tolerance is half an ATR in price. On a 15-minute impulse leg that is {eb_frac:.1%} of the move at its tightest here and {ew_frac:.1%} at its loosest &mdash; so &ldquo;price reached the golden ratio&rdquo; can be satisfied anywhere from the {ew_lo:.0%} to the {ew_hi:.0%} retracement. It is why this filter admits roughly seven setups in ten, and why the best trade in the BTC book qualifies at a {bb["entry"]["retracement"]:.1%} retracement.</span>
      </li>
      <li>
        <span class="rec">3</span>
        <span><strong>The winners are real. There are not enough of them.</strong> Both best trades reached a clean, full 5R exactly as designed &mdash; this is not a strategy that never works. At the measured costs it needs <span class="num obs">40.2&percnt;</span> of trades to do that on BTC and <span class="num obs">33.5&percnt;</span> on ETH. It gets <span class="num">11.0&percnt;</span> and <span class="num">15.4&percnt;</span>. Over eight years the full confluence arm turns 10,000 into <span class="num">3,352</span> on BTC and <span class="num">4,321</span> on ETH, against buy-and-hold&rsquo;s <span class="num">56,000</span> and <span class="num">21,521</span>.</span>
      </li>
    </ul>
  </div>

  <section>
    <h2>What these examples do not show</h2>
    <p>Seven trades cannot carry a verdict and are not being asked to. The verdict came from 222 stacked trades, 3,875 setups, eight parameter cells and a set of matched-placebo controls, and it is that no component of this strategy predicts anything once leg size relative to ATR is held constant. These are illustrations of a conclusion reached elsewhere.</p>
    <p>Two of them flatter the strategy on purpose. The selection rule includes both best trades because a page that showed only losers would be answering a question nobody asked &mdash; and both of those are genuine 5R winners, correctly identified, correctly held to target.</p>
    <p>And none of this refutes the course as a human practises it. What was tested is the mechanised version, which is not the thing being taught. A discretionary trader would have skipped the six-dollar stop. That instinct is exactly what mechanising the rules removed, and its absence from the written rules is the finding.</p>
  </section>

  <hr class="rule">
  <footer>
    <p>Reproduce: <code>uv run python scripts/run_structure_examples.py</code> &middot; offline, deterministic, from the committed 15-minute Binance fixture. Every number on this page is quoted from <code>data/structure_examples_summary.json</code> and pinned against it by <code>tests/unit/test_structure_examples.py</code>.</p>
    <p>Full programme: <code>STRUCTURE_RESULTS.md</code>, decision records D204&ndash;D212, closed after 102 looks.</p>
  </footer>

</div>
"""

out = REPO / "docs/results/structure_trade_examples.html"
out.write_text(head + body, encoding="utf-8")
print(f"wrote {out} ({len(head + body):,} bytes)")
