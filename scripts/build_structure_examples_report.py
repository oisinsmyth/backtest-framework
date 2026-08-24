"""Assemble docs/results/structure_trade_examples.html.

The head — fonts and the whole stylesheet — is lifted verbatim from `final_report.html` so
the two reports are the same document rather than two that resemble each other; a test
asserts the stylesheet stays byte-identical. Only the chart rules are added on top.

Numbers are quoted from `data/structure_examples_summary.json` and pinned against it by
`tests/unit/test_structure_examples.py`, because hand-written prose around
machine-extracted numbers is exactly the arrangement that drifts (D176/D183/D186).

## Why the candles are hollow and filled rather than red and green

The report inherits a palette with one accent (brass) and a set of neutrals. Dropping a
red/green pair into it would introduce a second colour system fighting the first, and would
spend the reader's attention on which way each bar closed — which is not what any of these
charts is about. The Japanese hollow/filled convention carries the same information in the
ink the page already uses, and leaves the accent free to mean *this is the thing the trade
turned on*: the entry, the stop, the target, the gap.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GOLD = 0.618

SLOT, BODY = 8.0, 5.0
LEFT, RIGHT, TOP, BOTTOM, PLOT = 58.0, 10.0, 14.0, 24.0, 250.0


def _scale(lo: float, hi: float):
    pad = (hi - lo) * 0.04 or (hi * 0.001)
    lo, hi = lo - pad, hi + pad
    span = hi - lo or 1.0
    return (lambda price: TOP + PLOT * (hi - price) / span), lo, hi


def _fmt(price: float) -> str:
    return f"{price:,.2f}" if price < 100 else f"{price:,.0f}"


def candles(e: dict, chart_id: str) -> str:
    """One trade's chart, as inline SVG, themed through the page's own custom properties."""
    rows = e["chart"]["bars"]
    first = e["chart"]["first_index"]
    n = len(rows)
    width = LEFT + n * SLOT + RIGHT
    height = TOP + PLOT + BOTTOM

    leg, lv, en, rk, ex, ch = (
        e["leg"], e["levels"], e["entry"], e["risk"], e["exit"], e["choch"],
    )
    band = 0.5 * en["atr"]
    gold = lv["fib_618"]

    lo = min(b["low"] for b in rows)
    hi = max(b["high"] for b in rows)
    # Overlays must sit inside the frame too, or a stop falls off the bottom edge.
    for extra in (rk["stop_price"], gold + band, gold - band, en["price"], ex["price"]):
        lo, hi = min(lo, extra), max(hi, extra)
    if lv["gap_midpoint"] is not None:
        half = lv["gap_width"] / 2.0
        lo, hi = min(lo, lv["gap_midpoint"] - half), max(hi, lv["gap_midpoint"] + half)
    y, ylo, yhi = _scale(lo, hi)

    def x(index: int) -> float:
        return LEFT + (index - first) * SLOT + SLOT / 2.0

    out: list[str] = []
    add = out.append
    add(f'<svg viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" '
        f'height="{height:.0f}" role="img" xmlns="http://www.w3.org/2000/svg" '
        f'aria-labelledby="{chart_id}-t">')
    add(f'<title id="{chart_id}-t">{e["symbol"]} {e["side"]}: candlesticks with the change '
        f'of character, impulse leg, 61.8 percent touch band, fair value gap, entry, stop, '
        f'target and exit marked.</title>')

    for i in range(5):
        price = ylo + (yhi - ylo) * i / 4.0
        yy = y(price)
        add(f'<line x1="{LEFT:.0f}" y1="{yy:.1f}" x2="{width - RIGHT:.0f}" y2="{yy:.1f}" '
            f'stroke="var(--rule)" stroke-width="1"/>')
        add(f'<text x="{LEFT - 8:.0f}" y="{yy + 3.5:.1f}" text-anchor="end" font-size="9" '
            f'fill="var(--faint)">{_fmt(price)}</text>')

    # The 61.8% touch band — the width of this shaded strip is the report's finding 2.
    top, bot = y(gold + band), y(gold - band)
    add(f'<rect x="{LEFT:.0f}" y="{top:.1f}" width="{n * SLOT:.0f}" '
        f'height="{bot - top:.1f}" fill="var(--slate)" opacity="0.10"/>')
    add(f'<line x1="{LEFT:.0f}" y1="{y(gold):.1f}" x2="{width - RIGHT:.0f}" '
        f'y2="{y(gold):.1f}" stroke="var(--slate)" stroke-width="1" stroke-dasharray="1 3"/>')
    add(f'<text x="{LEFT + 4:.0f}" y="{max(top - 4, TOP + 8):.1f}" font-size="9" '
        f'letter-spacing="0.08em" fill="var(--slate)">61.8% &#177; 0.5 ATR</text>')

    if lv["gap_midpoint"] is not None:
        half = lv["gap_width"] / 2.0
        gt, gb = y(lv["gap_midpoint"] + half), y(lv["gap_midpoint"] - half)
        gx = x(leg["start_index"]) - SLOT / 2
        add(f'<rect x="{gx:.1f}" y="{gt:.1f}" width="{width - RIGHT - gx:.1f}" '
            f'height="{max(gb - gt, 1.2):.1f}" fill="var(--brass)" opacity="0.18"/>')

    for price, dash, label in ((rk["stop_price"], "4 3", "stop"),
                               (rk["target_price"], "1 4", "5R target")):
        if not (ylo <= price <= yhi):
            continue
        add(f'<line x1="{LEFT:.0f}" y1="{y(price):.1f}" x2="{width - RIGHT:.0f}" '
            f'y2="{y(price):.1f}" stroke="var(--brass)" stroke-width="1" '
            f'stroke-dasharray="{dash}"/>')
        add(f'<text x="{width - RIGHT - 3:.0f}" y="{y(price) - 4:.1f}" text-anchor="end" '
            f'font-size="9" letter-spacing="0.08em" fill="var(--brass)">{label}</text>')

    add(f'<line x1="{x(leg["start_index"]):.1f}" y1="{y(leg["start_price"]):.1f}" '
        f'x2="{x(leg["end_index"]):.1f}" y2="{y(leg["end_price"]):.1f}" '
        f'stroke="var(--slate)" stroke-width="1.6" opacity="0.8"/>')
    for idx, price in ((leg["start_index"], leg["start_price"]),
                       (leg["end_index"], leg["end_price"])):
        add(f'<circle cx="{x(idx):.1f}" cy="{y(price):.1f}" r="2.6" fill="var(--slate)"/>')

    for b in rows:
        cx = x(b["index"])
        up = b["close"] >= b["open"]
        add(f'<line x1="{cx:.1f}" y1="{y(b["high"]):.1f}" x2="{cx:.1f}" '
            f'y2="{y(b["low"]):.1f}" stroke="var(--muted)" stroke-width="1"/>')
        yt, yb = y(max(b["open"], b["close"])), y(min(b["open"], b["close"]))
        add(f'<rect x="{cx - BODY / 2:.1f}" y="{yt:.1f}" width="{BODY:.0f}" '
            f'height="{max(yb - yt, 1.0):.1f}" '
            f'fill="{"var(--paper)" if up else "var(--ink)"}" stroke="var(--ink)" '
            f'stroke-width="1"/>')

    for idx, label, colour in ((ch["index"], "CHoCH", "var(--slate)"),
                               (en["index"], "entry", "var(--brass)"),
                               (ex["index"], "exit", "var(--brass)")):
        cx = x(idx)
        add(f'<line x1="{cx:.1f}" y1="{TOP:.0f}" x2="{cx:.1f}" y2="{TOP + PLOT:.0f}" '
            f'stroke="{colour}" stroke-width="1" opacity="0.45"/>')
        add(f'<text x="{cx:.1f}" y="{TOP + PLOT + 13:.0f}" text-anchor="middle" '
            f'font-size="9" letter-spacing="0.06em" fill="{colour}">{label}</text>')

    add(f'<circle cx="{x(en["index"]):.1f}" cy="{y(en["price"]):.1f}" r="3.4" '
        f'fill="var(--brass)"/>')
    add(f'<circle cx="{x(ex["index"]):.1f}" cy="{y(ex["price"]):.1f}" r="3.4" fill="none" '
        f'stroke="var(--brass)" stroke-width="1.8"/>')
    add("</svg>")
    return "".join(out)


CHART_CSS = """
  /* ---------------------------------------------------------------- charts */

  .chart { margin: 0 0 0.4rem; }
  .chart svg { display: block; }
  .chart svg text { font-family: var(--cond); }
  .chart figcaption { margin-top: 0.45rem; }

  .legend {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem 1.1rem;
    font-family: var(--cond);
    font-size: 0.72rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--faint);
    margin: 0 0 1.75rem;
  }
  .legend span { display: inline-flex; align-items: center; gap: 0.4rem; }
  .sw { width: 0.72rem; height: 0.72rem; display: inline-block; flex: none; }
  .sw.hollow  { background: var(--paper); border: 1px solid var(--ink); }
  .sw.filled  { background: var(--ink); border: 1px solid var(--ink); }
  .sw.leg     { height: 0; border-top: 2px solid var(--slate); }
  .sw.bandsw  { background: var(--slate); opacity: 0.30; }
  .sw.gapsw   { background: var(--brass); opacity: 0.40; }
  .sw.brasssw { height: 0; border-top: 2px dashed var(--brass); }

  ul.findings.single li:first-child { border-top: 0; padding-top: 0.2rem; }
"""

LEGEND = (
    '<p class="legend">'
    '<span><i class="sw hollow"></i>closed up</span>'
    '<span><i class="sw filled"></i>closed down</span>'
    '<span><i class="sw leg"></i>impulse leg</span>'
    '<span><i class="sw bandsw"></i>61.8&percnt; &plusmn; 0.5&nbsp;ATR band</span>'
    '<span><i class="sw gapsw"></i>fair value gap</span>'
    '<span><i class="sw brasssw"></i>entry &middot; stop &middot; target &middot; exit</span>'
    "</p>"
)


def band_of(e: dict) -> tuple[float, float, float]:
    frac = 0.5 * e["entry"]["atr"] / abs(e["leg"]["span"])
    return frac, GOLD - frac, GOLD + frac


def block(tag: str, e: dict, chart_id: str, comment: str) -> str:
    """A chart and its comment — the findings pattern, with the evidence above it."""
    o, r, en, ex = e["outcome"], e["risk"], e["entry"], e["exit"]
    cap = (
        f'{e["symbol"]} &middot; {en["timestamp"][:16].replace("T", " ")} UTC &middot; '
        f'{e["side"]} &middot; {len(e["chart"]["bars"])} bars &middot; '
        f'entered at a {en["retracement"]:.1%} retracement, stop '
        f'{r["distance_atr"]:.2f}&nbsp;ATR away &middot; exited on the '
        f'{ex["reason"].replace("_", " ")} for {o["net_r"]:+.3f}R net'
    )
    return f"""  <div class="bleed">
    <figure class="chart">
      <div class="scroll">{candles(e, chart_id)}</div>
      <figcaption>{cap}</figcaption>
    </figure>
    <ul class="findings single">
      <li>
        <span class="rec">{tag}</span>
        <span>{comment}</span>
      </li>
    </ul>
  </div>
"""


def main() -> int:
    src = (REPO / "docs/results/final_report.html").read_text(encoding="utf-8")
    head = src[: src.index("</style>")]
    head = head.replace("<title>Nothing Worked</title>", "<title>Four Basis Points</title>", 1)
    head = head + CHART_CSS + "</style>"

    d = json.loads((REPO / "data/structure_examples_summary.json").read_text(encoding="utf-8"))
    B, E, LOW = d["per_symbol"]["BTCUSDT"], d["per_symbol"]["ETHUSDT"], d["lowest_cost"]
    bb, bm, bw = B["best"], B["median"], B["worst"]
    eb, em, ew = E["best"], E["median"], E["worst"]

    bb_frac, bb_lo, bb_hi = band_of(bb)
    ew_frac, _, ew_hi2 = band_of(ew)
    em_frac, _, em_hi = band_of(em)
    eb_frac, _, _ = band_of(eb)
    _, ew_lo, ew_hi = band_of(ew)
    gap_to_618 = abs(bb["entry"]["price"] - bb["levels"]["fib_618"])
    low_target_pct = LOW["risk"]["target_price"] / LOW["entry"]["price"] - 1.0

    def row(label: str, e: dict) -> str:
        o, r, en, ex = e["outcome"], e["risk"], e["entry"], e["exit"]
        return (
            f'      <tr><td class="name">{label}</td><td>{e["side"]}</td>'
            f'<td>{en["timestamp"][:10]}</td><td>{en["retracement"]:.3f}</td>'
            f'<td>{r["distance_atr"]:.2f}</td><td>{r["distance_pct"]:.3%}</td>'
            f'<td>{o["gross_r"]:+.2f}</td><td class="hi">{o["cost_r"]:.2f}</td>'
            f'<td>{o["net_r"]:+.2f}</td><td>{ex["reason"].replace("_", " ")}</td></tr>'
        )

    c_bb = (
        f'<strong>The strategy working exactly as advertised &mdash; and the golden ratio '
        f'is not really in it.</strong> A change of character, a 12-bar impulse down '
        f'{bb["leg"]["span_pct"]:.2%}, a pullback into a fair value gap '
        f'{bb["levels"]["gap_width_atr"]:.2f}&nbsp;ATR wide, a stop '
        f'{bb["risk"]["distance_atr"]:.2f}&nbsp;ATR away at the leg&rsquo;s origin, and a '
        f'clean 5R banked {bb["exit"]["bars_held"]} bars later for '
        f'<span class="num obs">{bb["outcome"]["net_r"]:+.3f}R</span> net. It is a good '
        f'trade. But it filled at a <strong>{bb["entry"]["retracement"]:.1%}</strong> '
        f'retracement, not 61.8&percnt;: the 0.618 level sat at '
        f'<code>{bb["levels"]["fib_618"]:,.2f}</code> and price closed '
        f'<code>{gap_to_618:,.2f}</code> below it. Look at the width of the shaded band on '
        f'the chart &mdash; half an ATR is <code>{0.5 * bb["entry"]["atr"]:,.2f}</code> on '
        f'a leg of <code>{abs(bb["leg"]["span"]):,.2f}</code>, or <strong>{bb_frac:.1%} of '
        f'the entire move</strong>. &ldquo;Price touched the golden ratio&rdquo; was true '
        f'anywhere between the {bb_lo:.0%} and {bb_hi:.0%} retracement.'
    )
    c_bm = (
        f'<strong>A textbook loss, correctly handled, and still half fee.</strong> Short at '
        f'{bm["entry"]["retracement"]:.1%} into the leg, stop '
        f'{bm["risk"]["distance_atr"]:.2f}&nbsp;ATR away, 5R target below the frame. Price '
        f'went {bm["outcome"]["mfe_r"]:+.2f}R in favour, turned, and paid the stop '
        f'{bm["exit"]["bars_held"]} bars later. Nothing went wrong: gross '
        f'<span class="num">{bm["outcome"]["gross_r"]:+.2f}R</span> is exactly one unit of '
        f'planned risk. What makes it a losing business is the line beneath &mdash; '
        f'<span class="num obs">{bm["outcome"]["cost_r"]:.3f}R</span> of fees on that 1R, '
        f'so the median trade hands back {bm["outcome"]["cost_r"]:.0%} of its risk before '
        f'the market is consulted.'
    )
    c_bw = (
        f'<strong>The worst trade in the book is not a bad prediction. It is a fee '
        f'bill.</strong> The chart is the argument: the whole impulse leg is '
        f'{bw["leg"]["span_pct"]:.2%} of price, and the entry sits so close to the leg&rsquo;s '
        f'origin that the stop line and the entry dot are almost the same pixel. Gross it '
        f'lost <span class="num">{bw["outcome"]["gross_r"]:+.2f}R</span> &mdash; an ordinary '
        f'stop-out, identical to the median above. The difference is that the entry filled '
        f'<code>{bw["risk"]["distance"]:,.2f}</code> from its stop on a '
        f'<code>{bw["entry"]["price"]:,.2f}</code> bitcoin: '
        f'<strong>{bw["risk"]["distance_pct"]:.3%} of price</strong>, '
        f'{bw["risk"]["distance_atr"]:.2f}&nbsp;ATR. An 80&nbsp;bp round trip against a '
        f'{bw["risk"]["distance_pct"] * 10000:.1f}&nbsp;bp stop is '
        f'<span class="num obs">{bw["outcome"]["cost_r"]:.3f}R</span>, and no position size '
        f'makes that tradeable. Every filter agreed: change of character, '
        f'{bw["entry"]["retracement"]:.1%} retracement, inside a fair value gap '
        f'{bw["levels"]["gap_width_atr"]:.2f}&nbsp;ATR wide. They agreed on a trade whose '
        f'entire risk was smaller than the spread. Its recorded '
        f'{bw["outcome"]["mfe_r"]:+.2f}R best excursion is the same tininess from the other '
        f'side &mdash; the excursion window includes the entry bar, whose own fifteen '
        f'minutes are nine times a six-dollar stop.'
    )
    c_eb = (
        f'<strong>The mirror of BTC&rsquo;s best, seven years later and the other way '
        f'up.</strong> A long at {eb["entry"]["retracement"]:.1%} into a 6-bar impulse, a '
        f'fair value gap {eb["levels"]["gap_width_atr"]:.2f}&nbsp;ATR wide &mdash; the '
        f'widest gap in this set, and visibly so &mdash; stop '
        f'{eb["risk"]["distance_atr"]:.2f}&nbsp;ATR below at the leg&rsquo;s origin, target '
        f'reached in {eb["exit"]["bars_held"]} bars for '
        f'<span class="num obs">{eb["outcome"]["net_r"]:+.3f}R</span>. This is also the '
        f'tightest the 61.8&percnt; band gets anywhere in the seven: half an ATR here is '
        f'only {eb_frac:.1%} of the leg, so the level meant something closer to what the '
        f'course claims it means. The fee still took '
        f'<span class="num">{eb["outcome"]["cost_r"]:.3f}R</span>. Fees are not why this '
        f'trade fails, because it does not fail. They are why the 103 around it do.'
    )
    c_em = (
        f'<strong>Deeper than the golden ratio, and it made no difference.</strong> Entered '
        f'at a <strong>{em["entry"]["retracement"]:.1%}</strong> retracement &mdash; well '
        f'past 61.8&percnt;, and still inside the band, which here reaches to {em_hi:.0%}. '
        f'Price never moved more than '
        f'<span class="num">{em["outcome"]["mfe_r"]:+.2f}R</span> in favour and stopped out '
        f'in {em["exit"]["bars_held"]} bars. The wrapper did nothing wrong and the entry '
        f'was simply not predictive. This is what the middle of 104 perfect-confluence '
        f'setups looks like.'
    )
    c_ew = (
        f'<strong>The same defect as BTC&rsquo;s worst, on a different asset in a different '
        f'year.</strong> A {ew["leg"]["span_pct"]:.2%} impulse leg &mdash; six dollars on a '
        f'<code>{ew["entry"]["price"]:,.2f}</code> ether &mdash; with the entry '
        f'<code>{ew["risk"]["distance"]:,.2f}</code> from its stop, '
        f'<strong>{ew["risk"]["distance_pct"]:.3%} of price</strong>. Cost '
        f'<span class="num obs">{ew["outcome"]["cost_r"]:.3f}R</span>. Note the price axis: '
        f'the entire chart spans about eight dollars. That the two worst trades in two '
        f'independent books are the same shape is the point &mdash; the leg&rsquo;s origin '
        f'can sit arbitrarily close to the pullback entry, and nothing anywhere in the rule '
        f'prevents it. There is no minimum stop, because the course never mentions one.'
    )
    c_low = (
        f'<strong>When the fees are as small as they ever get, the trade makes a sixth of '
        f'one unit of risk.</strong> A {LOW["leg"]["span_pct"]:.2%} impulse leg puts the '
        f'stop {LOW["risk"]["distance_atr"]:.2f}&nbsp;ATR away, so the round trip costs only '
        f'<span class="num obs">{LOW["outcome"]["cost_r"]:.3f}R</span> &mdash; the lowest of '
        f'all {d["pooled_n"]} stacked trades in both books. The 5R target is '
        f'{low_target_pct:.1%} above the entry and never appears on the chart at all. Price '
        f'drifted the right way and closed at the 60-bar cap for '
        f'<span class="num">{LOW["outcome"]["gross_r"]:+.3f}R</span> gross. Net '
        f'<span class="num">{LOW["outcome"]["net_r"]:+.3f}R</span>. This is the ceiling of '
        f'the friendly case.'
    )

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
    <h2>Reading the charts</h2>
    <p>Each chart runs from a few bars before the change of character to a few past the exit. Candles are hollow when the bar closed up and filled when it closed down &mdash; the report has one accent colour and it is reserved for the things the trade turned on, not spent on which way each bar went.</p>
    <p>The shaded horizontal strip is the <strong>61.8&percnt; touch band</strong>: the 0.618 level with the half-ATR tolerance the rule actually uses. Its height on each chart is the point of finding&nbsp;2 below &mdash; on several of these it covers most of the leg.</p>
  </section>

  <div class="bleed">{LEGEND}</div>

  <section>
    <h2>BTCUSDT</h2>
    <p class="kicker">118 trades &mdash; best, median, worst</p>
  </section>

{block("BEST", bb, "btc-best", c_bb)}
{block("MEDIAN", bm, "btc-med", c_bm)}
{block("WORST", bw, "btc-worst", c_bw)}

  <section>
    <h2>ETHUSDT</h2>
    <p class="kicker">104 trades &mdash; best, median, worst</p>
  </section>

{block("BEST", eb, "eth-best", c_eb)}
{block("MEDIAN", em, "eth-med", c_em)}
{block("WORST", ew, "eth-worst", c_ew)}

  <section>
    <h2>The cheapest trade the rule ever produced</h2>
    <p class="kicker">Everything about the cost structure going right</p>
  </section>

{block("LOW", LOW, "cheapest", c_low)}

  <section>
    <h2>Three things the examples show</h2>
    <p class="kicker">Each visible in the charts above, not inferred from them</p>
  </section>

  <div class="bleed">
    <ul class="findings">
      <li>
        <span class="rec">1</span>
        <span><strong>The stop can be arbitrarily tight and the rule does not care.</strong> Stop distance is the unretraced part of the leg, so a deep entry on a small leg leaves almost nothing between fill and stop. Across the two books that produces trades risking <span class="num">{bw["risk"]["distance_pct"]:.3%}</span> and <span class="num">{ew["risk"]["distance_pct"]:.3%}</span> of price, on which an 80&nbsp;bp round trip is twenty times the risk. <strong>67&percnt; of BTC&rsquo;s stacked trades and 50&percnt; of ETH&rsquo;s cost at least their entire risk to put on.</strong> A minimum-stop filter would fix it and would also be a new parameter the course never states.</span>
      </li>
      <li>
        <span class="rec">2</span>
        <span><strong>The 61.8&percnt; level is a band, and the band is up to a quarter of the leg on each side.</strong> The touch tolerance is half an ATR in price. On a 15-minute impulse leg that is {eb_frac:.1%} of the move at its tightest here and {ew_frac:.1%} at its loosest &mdash; so &ldquo;price reached the golden ratio&rdquo; can be satisfied anywhere from the {ew_lo:.0%} to the {ew_hi:.0%} retracement. It is why this filter admits roughly seven setups in ten, and why the best trade in the BTC book qualifies at a {bb["entry"]["retracement"]:.1%} retracement. The shaded strip on each chart is that band drawn to scale.</span>
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
    <p>Reproduce: <code>uv run python scripts/run_structure_examples.py</code> then <code>uv run python scripts/build_structure_examples_report.py</code> &middot; offline, deterministic, from the committed 15-minute Binance fixture. Every number on this page is quoted from <code>data/structure_examples_summary.json</code> and pinned against it by <code>tests/unit/test_structure_examples.py</code>.</p>
    <p>Full programme: <code>STRUCTURE_RESULTS.md</code>, decision records D204&ndash;D212, closed after 102 looks.</p>
  </footer>

</div>
"""

    out = REPO / "docs/results/structure_trade_examples.html"
    out.write_text(head + body, encoding="utf-8")
    print(f"wrote {out} ({len(head + body):,} bytes, 7 charts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
