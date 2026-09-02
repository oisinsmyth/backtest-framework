"""Render D290's unified ranking as a standalone page.

    uv run python scripts/d290_rank_page.py

GENERATED FROM `data/d290_unified_rank.json`, never transcribed. Three
constructions x 51 candidates is 153 rows; hand-copying them is how a results
table acquires an error nobody can trace.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
U = json.loads((REPO / "data" / "d290_unified_rank.json").read_text())
OUT = REPO / "temp" / "d290_unified.html"

CON = [
    ("spread", "Spread",
     "Dollar-neutral. Removes the drift term that dominates the long book."),
    ("short", "Short-only",
     "Pays borrow <em>on top of</em> the round trip &mdash; and borrow is not in "
     "the cost column, so every number here is optimistic."),
    ("long", "Long-only",
     "Net long, so it carries market beta. The nulls are brutal here for exactly "
     "that reason."),
]

KEY = [
    ("real", "<b>min z &gt; 0</b> on all three nulls &mdash; rotation "
     "(turnover-matched), within-bar permutation (regime-matched) and "
     "tail-randomised (nuisance-matched by construction)."),
    ("generalises", "<b>CV t &gt; 0</b>. Peak cell picked on half the names, "
     "scored on the other half, 10 splits. Necessary and <b>not sufficient</b> "
     "&mdash; an entry artifact generalises across names perfectly well."),
    ("capturable", "<b>open t &ge; 2</b>. Enter at open[t] instead of the "
     "close[t&minus;1] that generated the signal. The question the skip test "
     "could <em>not</em> answer, because skipping a bar removes a real fast "
     "signal and an entry artifact alike."),
    ("kept", "open-entry effect &divide; close-entry effect. Below ~50% the edge "
     "was largely the print you traded on."),
    ("on%", "share of the k=1 return earned between the close and the next open "
     "&mdash; the segment you cannot trade into. Computed at k=1 for every "
     "candidate, so it is <b>not</b> a decomposition of a k=40 peak."),
    ("&times; bar", "effect &divide; the <b>measured</b> Corwin&ndash;Schultz "
     "round trip on names actually held. Reported, never ranked on &mdash; D289 "
     "defers magnitude to stage 2."),
    ("tier", "<b>1</b> real + generalises + capturable &middot; <b>2</b> real + "
     "generalises, not capturable &middot; <b>3</b> fails a null or the split."),
]


def fmt(v, d=1):
    return f"{v:+.{d}f}" if v is not None else "&mdash;"


def pct(v):
    return f"{v:+.0%}" if v is not None else "&mdash;"


def body(rows):
    out, shown3 = [], 0
    for r in rows:
        if r["tier"] == 3:
            shown3 += 1
            if shown3 > 6:
                continue
        xb = r["xbar"]
        pill = ('<span class="na">&mdash;</span>' if xb is None else
                f'<span class="pill{" ok" if xb >= 1 else ""}">{xb:.2f}&times;</span>')
        out.append(
            f'<tr class="tier{r["tier"]}"><td class="ax">{r["ax"]}</td>'
            f'<td class="name">{r["c"]}</td>'
            f'<td class="g">{r["N"]}</td><td>{r["k"]}</td>'
            f'<td class="g">{fmt(r["bp"])}</td><td>{fmt(r["cv"], 2)}</td>'
            f'<td>{fmt(r["mn"], 2)}</td>'
            f'<td class="g strong">{fmt(r["oe_t"], 2)}</td>'
            f'<td>{fmt(r["oe_bp"])}</td><td>{pct(r["kept"])}</td>'
            f'<td class="g">{pct(r["on_share"])}</td><td class="g">{pill}</td>'
            f'<td class="tier"><span class="t{r["tier"]}">{r["tier"]}</span></td></tr>')
    return "".join(out)


def section(con, label, blurb):
    rows = U["rows"][con]
    t1 = sum(1 for r in rows if r["tier"] == 1)
    t2 = sum(1 for r in rows if r["tier"] == 2)
    cost = sum(1 for r in rows if r["xbar"] and r["xbar"] >= 1)
    return f"""<section class="block"><div class="bhead">
<h2>{label}</h2><p>{blurb}</p>
<div class="counts"><span class="chip c1">{t1} tier 1</span>
<span class="chip c2">{t2} tier 2</span>
<span class="chip">{len(rows) - t1 - t2} tier 3</span>
<span class="chip c1">{cost} clear cost</span></div></div>
<div class="scroll"><table><thead><tr>
<th class="ax">ax</th><th class="name">candidate</th><th class="g">N</th><th>k</th>
<th class="g">bp</th><th>CV t</th><th>min z</th>
<th class="g">open t</th><th>open bp</th><th>kept</th>
<th class="g">on%</th><th class="g">&times; bar</th><th class="tier">tier</th>
</tr></thead><tbody>{body(rows)}</tbody></table></div>
<p class="note">Tier 3 truncated to six rows. All 51 per construction are in
<code>data/d290_unified_rank.json</code>.</p></section>"""


CSS = """
:root{--bg:#F4F6F7;--surface:#fff;--raised:#FAFBFB;--ink:#0F1619;--ink2:#5B6970;
--ink3:#8A979E;--line:#DCE3E6;--line2:#EDF1F3;--accent:#0E7C86;--pos:#15693D;
--neg:#9C3030;--amber:#8A6100;}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0D1215;
--surface:#141B1F;--raised:#182126;--ink:#E7EEF1;--ink2:#98A7AF;--ink3:#6B7A82;
--line:#243036;--line2:#1C262B;--accent:#3FB6AE;--pos:#4FB07A;--neg:#D97068;
--amber:#C79A3A;}}
:root[data-theme="dark"]{--bg:#0D1215;--surface:#141B1F;--raised:#182126;
--ink:#E7EEF1;--ink2:#98A7AF;--ink3:#6B7A82;--line:#243036;--line2:#1C262B;
--accent:#3FB6AE;--pos:#4FB07A;--neg:#D97068;--amber:#C79A3A;}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans",system-ui,sans-serif;
margin:0;padding:32px 24px 80px;line-height:1.5;font-variant-numeric:tabular-nums}
.wrap{max-width:1120px;margin:0 auto;display:flex;flex-direction:column;gap:26px}
h1{font-size:27px;font-weight:600;margin:0 0 6px;letter-spacing:-.01em}
.sub{color:var(--ink2);margin:0;max-width:74ch}
.ladder{display:grid;gap:8px;grid-template-columns:repeat(auto-fit,minmax(210px,1fr))}
.step{background:var(--surface);border:1px solid var(--line);
border-left:3px solid var(--accent);padding:10px 12px;border-radius:3px}
.step b{font-family:"IBM Plex Mono",monospace;font-size:11.5px;letter-spacing:.05em;
color:var(--accent)}
.step p{margin:3px 0 0;font-size:13px;color:var(--ink2)}
details.key{background:var(--surface);border:1px solid var(--line);border-radius:3px;
padding:14px 16px}
summary{cursor:pointer;font-weight:600;font-size:14px}
summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.kg{display:grid;gap:10px 20px;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));
margin-top:14px}
.kg div{font-size:13px;color:var(--ink2)}
.kg code{font-family:"IBM Plex Mono",monospace;color:var(--accent);font-weight:600;
font-size:12.5px;margin-right:6px}
.block{background:var(--surface);border:1px solid var(--line);border-radius:4px;overflow:hidden}
.bhead{padding:15px 18px;border-bottom:1px solid var(--line);display:flex;
flex-direction:column;gap:5px}
.bhead h2{margin:0;font-size:17px;font-weight:600}
.bhead p{margin:0;font-size:13px;color:var(--ink2);max-width:78ch}
.counts{display:flex;gap:7px;flex-wrap:wrap;margin-top:3px}
.chip{font-family:"IBM Plex Mono",monospace;font-size:11.5px;padding:3px 8px;
border-radius:3px;border:1px solid var(--line);color:var(--ink2)}
.c1{border-color:var(--pos);color:var(--pos)}
.c2{border-color:var(--amber);color:var(--amber)}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-family:"IBM Plex Mono",monospace;
font-size:12.5px}
thead th{position:sticky;top:0;background:var(--raised);color:var(--ink2);
font-weight:500;text-align:right;padding:8px 9px;border-bottom:1px solid var(--line);
font-size:11.5px;white-space:nowrap}
td{padding:5px 9px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--line2)}
th.g,td.g{border-left:1px solid var(--line)}
th.ax,td.ax{text-align:center;color:var(--ink2);width:26px}
th.name,td.name{text-align:left;font-weight:500}
td.strong{font-weight:600}
tr.tier1{border-left:3px solid var(--pos)}
tr.tier2{border-left:3px solid var(--amber)}
tr.tier3{border-left:3px solid transparent;opacity:.7}
tr:hover{background:var(--raised)}
.tier span{display:inline-block;width:18px;font-size:11px;font-weight:600}
.t1{color:var(--pos)}.t2{color:var(--amber)}.t3{color:var(--ink3)}
.pill{display:inline-block;padding:1px 6px;border-radius:3px;border:1px solid var(--line);
color:var(--ink2);font-size:11.5px}
.pill.ok{border-color:var(--pos);color:var(--pos);font-weight:600}
.na{color:var(--ink3)}
.note{margin:0;padding:9px 18px;font-size:12px;color:var(--ink3);
border-top:1px solid var(--line2)}
footer{color:var(--ink3);font-size:12.5px;max-width:78ch}
"""

LADDER = [
    ("1 &middot; IS IT REAL", "min z &gt; 0 across three nulls"),
    ("2 &middot; DOES IT GENERALISE",
     "CV t &gt; 0 on unseen names &mdash; and <em>not sufficient</em>"),
    ("3 &middot; CAN YOU CATCH IT", "open-entry t &ge; 2, entering a bar late"),
    ("4 &middot; DOES IT PAY", "vs measured cost &mdash; reported, never ranked on"),
]

HTML = f"""<title>D290 Unified Ranking</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{CSS}</style>
<div class="wrap">
<header><h1>D290 &mdash; unified ranking</h1>
<p class="sub">51 candidates, every diagnostic the study produced, ranked
separately for each construction. Nothing is closed or promoted, and the holdout
was not read.</p></header>
<div class="ladder">
{"".join(f'<div class="step"><b>{a}</b><p>{b}</p></div>' for a, b in LADDER)}
</div>
<details class="key"><summary>Column key</summary><div class="kg">
{"".join(f'<div><code>{k}</code>{v}</div>' for k, v in KEY)}</div></details>
{"".join(section(*c) for c in CON)}
<footer>Generated from <code>data/d290_unified_rank.json</code>. Green edge = tier 1,
amber = tier 2; the cost pill turns green at 1.00&times;.
<b>Borrow is absent from every short-only cost bar</b> because this fixture cannot
measure it, so those numbers are optimistic by that amount.</footer>
</div>"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(HTML, encoding="utf-8")
print(f"wrote {OUT.relative_to(REPO)}  {OUT.stat().st_size / 1024:.0f} KB")
