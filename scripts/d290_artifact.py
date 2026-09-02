"""Render D290's three ranked tables as a standalone HTML page.

    uv run python scripts/d290_artifact.py

GENERATED FROM `data/d290_stage1.json`, never transcribed. 51 candidates x 3
constructions is 153 rows of dense numerics; hand-copying them into a document
is how a results table acquires an error that nobody can trace back.

The page reports and gates nothing. It is the same content as
`data/d290_full_tables.txt`, laid out so the two decisions a reader actually
makes -- does it survive the nulls, does it clear its own cost -- are legible
without reading every column.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
D = json.loads((REPO / "data" / "d290_stage1.json").read_text())
OUT = REPO / "temp" / "d290_results.html"
AX, R = D["axes"], D["results"]

AXIS_NAME = {"A": "price", "B": "intrabar shape", "C": "volume structure",
             "D": "volume profile", "E": "range / volatility",
             "F": "overnight vs intraday", "G": "documented anomalies",
             "H": "harvested instruments"}

KEY = [
    ("ax", "Axis. A price · B intrabar shape · C volume structure · D volume "
     "profile · E range/vol · F overnight-vs-intraday · G documented anomalies · "
     "H harvested instruments."),
    ("N", "Names held per leg at the candidate's best cell. Swept 3, 5, 10, 25, 50."),
    ("k", "Holding horizon in bars at that cell. Swept 1 to 40."),
    ("bp", "Effect in basis points. Positive always means the construction MADE "
     "money — the short column is already sign-flipped, verified by an oracle "
     "book earning +746 / +646 / +1392."),
    ("t", "In-sample t at that cell. Its LEVEL is not readable — a max-order "
     "statistic over 60 cells. Present for shape, not evidence."),
    ("CV t", "The ranking key, and the honest number. Peak cell chosen on half "
     "the NAMES, scored on the other half, over 10 re-randomised splits. The "
     "holdout is a disjoint name set, so this is its free in-sample proxy."),
    ("±", "Spread of that CV t across the 10 splits. Large means the choice "
     "of split decides the answer."),
    ("rot", "z against the ROTATION null — per-symbol time shift. Preserves "
     "turnover and autocorrelation, destroys return alignment. Catches signals "
     "whose timing adds nothing."),
    ("perm", "z against the WITHIN-BAR PERMUTATION null — shuffle the score "
     "across names inside a bar. Preserves cross-sectional dispersion and market "
     "regime. Catches signals that are not cross-sectional at all."),
    ("tail", "z against the TAIL-RANDOMISED null — pool the 2N most extreme "
     "by the candidate's own score, assign sides at random. Matches the nuisance "
     "by construction. Catches factor tilts."),
    ("min z", "The binding constraint across the three, declared in advance so "
     "there is no shopping for the flattering null."),
    ("cost", "MEASURED round trip in bp — Corwin–Schultz on the names "
     "actually held at that N. Long: one round trip. Short: one round trip "
     "EXCLUDING BORROW, which this fixture cannot measure. Spread: both legs."),
    ("× bar", "Effect divided by cost. At or above 1.00 the candidate clears "
     "its own trading cost. Below, it does not — however good the t."),
]

CON = [("long", "Long-only", "The N lowest. Net long, so it carries beta."),
       ("short", "Short-only", "The N highest. Pays borrow on top of the round "
        "trip, and borrow is not in the cost column."),
       ("spread", "Spread", "Dollar-neutral. Removes the drift term that "
        "dominates the long book.")]


def rows(con):
    out = []
    for c in R:
        r = R[c]
        N, k, (bp, t, _) = r["observed"][con]
        cv, sd, _ = r["cv"][con]
        z = {n: r["z"][n][con] for n in ("rotation", "permutation", "tail")}
        cost = r.get("cost_bp_per_side") or {}
        lo, sh = cost.get("long"), cost.get("short")
        rt = (2 * lo if lo else None) if con == "long" else \
             (2 * sh if sh else None) if con == "short" else \
             (2 * lo + 2 * sh if (lo and sh) else None)
        out.append(dict(c=c, ax=AX[c], N=N, k=k, bp=bp, t=t, cv=cv, sd=sd,
                        zr=z["rotation"], zp=z["permutation"], zt=z["tail"],
                        mn=min(z.values()), rt=rt,
                        xb=(bp / rt) if rt else None))
    return sorted(out, key=lambda x: -x["cv"])


def num(v, dp=2, sign=True):
    if v is None:
        return '<span class="na">&mdash;</span>'
    s = f"{v:+.{dp}f}" if sign else f"{v:.{dp}f}"
    cls = "pos" if v > 0 else "neg" if v < 0 else "zero"
    return f'<span class="{cls}">{s}</span>'


def table(con, label, blurb):
    rs = rows(con)
    surv = sum(1 for r in rs if r["mn"] > 0)
    clears = sum(1 for r in rs if r["xb"] and r["xb"] >= 1)
    body = []
    for i, r in enumerate(rs, 1):
        f = []
        if r["mn"] > 0:
            f.append("surv")
        if r["xb"] and r["xb"] >= 1:
            f.append("clears")
        # BUILT AS SEPARATE CELLS ON PURPOSE. A first version put the cost cell
        # behind an inline conditional inside an implicit string concatenation;
        # Python binds the concatenation tighter than the ternary, so a missing
        # cost would have collapsed the WHOLE ROW to a single cell rather than
        # blanking one column. Every candidate happens to carry a cost, so it
        # never fired -- which is exactly the kind of latent trap worth removing
        # rather than leaving for a future fixture to find.
        cost_cell = (f'<td class="g">{r["rt"]:.1f}</td>' if r["rt"]
                     else '<td class="g"><span class="na">&mdash;</span></td>')
        if r["xb"] is None:
            xb_cell = '<td class="xb"><span class="na">&mdash;</span></td>'
        else:
            ok = " ok" if r["xb"] >= 1 else ""
            xb_cell = (f'<td class="xb"><span class="pill{ok}">'
                       f'{r["xb"]:.2f}&times;</span></td>')
        body.append(
            f'<tr class="{" ".join(f)}">'
            f'<td class="rank">{i}</td>'
            f'<td class="ax" title="{AXIS_NAME[r["ax"]]}">{r["ax"]}</td>'
            f'<td class="name">{r["c"]}</td>'
            f'<td class="g">{r["N"]}</td><td>{r["k"]}</td>'
            f'<td class="g">{num(r["bp"], 1)}</td><td>{num(r["t"])}</td>'
            f'<td class="g cv">{num(r["cv"])}</td>'
            f'<td class="sd">{r["sd"]:.2f}</td>'
            f'<td class="g">{num(r["zr"])}</td><td>{num(r["zp"])}</td>'
            f'<td>{num(r["zt"])}</td><td class="mz">{num(r["mn"])}</td>'
            + cost_cell + xb_cell + '</tr>')
    return f"""
<section class="block">
  <div class="bhead">
    <h2>{label}</h2>
    <p>{blurb}</p>
    <div class="counts">
      <span class="chip surv-chip">{surv} of {len(rs)} survive all three nulls</span>
      <span class="chip clear-chip">{clears} clear measured cost</span>
    </div>
  </div>
  <div class="scroll">
  <table>
    <thead>
      <tr>
        <th class="rank">#</th><th class="ax">ax</th><th class="name">candidate</th>
        <th class="g">N</th><th>k</th>
        <th class="g">bp</th><th>t</th>
        <th class="g">CV t</th><th>&plusmn;</th>
        <th class="g">rot</th><th>perm</th><th>tail</th><th>min z</th>
        <th class="g">cost</th><th>&times; bar</th>
      </tr>
    </thead>
    <tbody>{"".join(body)}</tbody>
  </table>
  </div>
</section>"""


HTML = f"""<title>D290 Signal Screen</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
:root {{
  --bg:#F4F6F7; --surface:#FFFFFF; --raised:#FAFBFB;
  --ink:#0F1619; --ink2:#5B6970; --ink3:#8A979E;
  --line:#DCE3E6; --line2:#EDF1F3;
  --accent:#0E7C86; --pos:#15693D; --neg:#9C3030; --amber:#8A6100;
  --stripe:#0E7C86;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg:#0D1215; --surface:#141B1F; --raised:#182126;
    --ink:#E7EEF1; --ink2:#98A7AF; --ink3:#6B7A82;
    --line:#243036; --line2:#1C262B;
    --accent:#3FB6AE; --pos:#4FB07A; --neg:#D97068; --amber:#C79A3A;
    --stripe:#3FB6AE;
  }}
}}
:root[data-theme="dark"] {{
  --bg:#0D1215; --surface:#141B1F; --raised:#182126;
  --ink:#E7EEF1; --ink2:#98A7AF; --ink3:#6B7A82;
  --line:#243036; --line2:#1C262B;
  --accent:#3FB6AE; --pos:#4FB07A; --neg:#D97068; --amber:#C79A3A;
  --stripe:#3FB6AE;
}}
* {{ box-sizing:border-box; }}
body {{
  background:var(--bg); color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,-apple-system,sans-serif;
  margin:0; padding:32px 24px 96px; line-height:1.5;
  font-variant-numeric:tabular-nums;
}}
.wrap {{ max-width:1180px; margin:0 auto; display:flex; flex-direction:column; gap:32px; }}
header h1 {{ font-size:28px; font-weight:600; margin:0 0 6px; letter-spacing:-0.01em; text-wrap:balance; }}
header .sub {{ color:var(--ink2); margin:0 0 14px; max-width:70ch; }}
.meta {{ display:flex; flex-wrap:wrap; gap:8px; }}
.meta span {{
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:12px;
  color:var(--ink2); background:var(--raised); border:1px solid var(--line);
  padding:3px 9px; border-radius:3px;
}}
.verdicts {{ display:grid; gap:8px; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); }}
.v {{ background:var(--surface); border:1px solid var(--line); border-left:3px solid var(--ink3);
     padding:10px 12px; border-radius:3px; }}
.v.ok {{ border-left-color:var(--pos); }}
.v.fail {{ border-left-color:var(--neg); }}
.v b {{ font-family:"IBM Plex Mono",monospace; font-size:12px; letter-spacing:.04em; }}
.v p {{ margin:3px 0 0; font-size:13px; color:var(--ink2); }}
details.key {{ background:var(--surface); border:1px solid var(--line); border-radius:3px; padding:14px 16px; }}
details.key summary {{ cursor:pointer; font-weight:600; font-size:14px; }}
.keygrid {{ display:grid; gap:10px 20px; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); margin-top:14px; }}
.keygrid div {{ font-size:13px; color:var(--ink2); }}
.keygrid code {{
  font-family:"IBM Plex Mono",monospace; color:var(--accent);
  font-weight:600; font-size:12.5px; margin-right:6px;
}}
.controls {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; }}
.controls button {{
  font:inherit; font-size:13px; cursor:pointer; color:var(--ink2);
  background:var(--surface); border:1px solid var(--line); padding:6px 12px; border-radius:3px;
}}
.controls button[aria-pressed="true"] {{ color:var(--surface); background:var(--accent); border-color:var(--accent); }}
.controls button:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
.block {{ background:var(--surface); border:1px solid var(--line); border-radius:4px; overflow:hidden; }}
.bhead {{ padding:16px 18px; border-bottom:1px solid var(--line); display:flex; flex-direction:column; gap:6px; }}
.bhead h2 {{ margin:0; font-size:17px; font-weight:600; }}
.bhead p {{ margin:0; font-size:13px; color:var(--ink2); max-width:75ch; }}
.counts {{ display:flex; gap:8px; flex-wrap:wrap; margin-top:2px; }}
.chip {{ font-family:"IBM Plex Mono",monospace; font-size:11.5px; padding:3px 8px;
        border-radius:3px; border:1px solid var(--line); color:var(--ink2); }}
.surv-chip {{ border-color:var(--accent); color:var(--accent); }}
.clear-chip {{ border-color:var(--pos); color:var(--pos); }}
.scroll {{ overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:12.5px; }}
thead th {{
  position:sticky; top:0; z-index:2; background:var(--raised); color:var(--ink2);
  font-weight:500; text-align:right; padding:8px 9px; white-space:nowrap;
  border-bottom:1px solid var(--line); font-size:11.5px; letter-spacing:.03em;
}}
td {{ padding:5px 9px; text-align:right; white-space:nowrap; border-bottom:1px solid var(--line2); }}
th.g, td.g {{ border-left:1px solid var(--line); }}
th.rank, td.rank {{ text-align:right; color:var(--ink3); width:34px; }}
th.ax, td.ax {{ text-align:center; color:var(--ink2); width:28px; }}
th.name, td.name {{ text-align:left; color:var(--ink); font-weight:500; }}
td.cv {{ font-weight:600; }}
td.sd {{ color:var(--ink3); }}
td.mz {{ font-weight:600; }}
tbody tr {{ border-left:3px solid transparent; }}
tbody tr.surv {{ border-left-color:var(--stripe); }}
tbody tr:hover {{ background:var(--raised); }}
.pos {{ color:var(--pos); }}
.neg {{ color:var(--neg); }}
.zero, .na {{ color:var(--ink3); }}
.pill {{ display:inline-block; padding:1px 6px; border-radius:3px; border:1px solid var(--line);
        color:var(--ink2); font-size:11.5px; }}
.pill.ok {{ border-color:var(--pos); color:var(--pos); font-weight:600; }}
footer {{ color:var(--ink3); font-size:12.5px; max-width:75ch; }}
@media (prefers-reduced-motion:reduce) {{ * {{ transition:none !important; }} }}
</style>

<div class="wrap">
<header>
  <h1>D290 &mdash; stage-1 signal screen</h1>
  <p class="sub">51 candidates, three constructions, three nulls. A ranking, not a
  gate: nothing is closed, nothing is promoted, and the holdout was not read.
  Ranked by name-split cross-validation, which is the honest column.</p>
  <div class="meta">
    <span>{D['base_cells']:,} warm live cells</span>
    <span>{D['draws']} null draws &times; 3</span>
    <span>{D['splits']} name splits</span>
    <span>N {', '.join(str(n) for n in D['n_levels'])}</span>
    <span>k 1&ndash;40</span>
    <span>{D['elapsed_s']/60:.0f} min</span>
  </div>
</header>

<div class="verdicts">
  <div class="v ok"><b>P1 CALIBRATION</b><p>hist_L spread t +2.858 against D286's
    published +2.86. Delta 0.002 &mdash; the screen reproduces a known quantity.</p></div>
  <div class="v"><b>P2 SHRINKAGE &ge;40%</b><p>Not confirmed: 31%. close_in_range
    generalises across names better than predicted.</p></div>
  <div class="v fail"><b>P3 NOTHING SHORT-ONLY</b><p>Falsified &mdash; 7 candidates
    positive with min z &gt; 0 and CV t &gt; 0. But 6 of 7 sit below cost, and the
    one that clears has CV t +0.29 &plusmn; 1.15.</p></div>
  <div class="v fail"><b>P4 RISK TERMS TILT</b><p>Falsified. ivol_21, beta_63,
    max_ret_21, rvol21 and atr_norm all show tail z &ge; rotation z &mdash; the
    opposite of the D283/D284 signature.</p></div>
  <div class="v ok"><b>P5 SOMETHING ON SPREAD</b><p>Confirmed. 24 of 51 survive all
    three nulls; 5 flagged on CV rank and null survival together.</p></div>
  <div class="v ok"><b>P6 close_in_range CV</b><p>Confirmed. Retains 69% of pooled t
    across the name split, against a 60% bar.</p></div>
</div>

<details class="key">
  <summary>Column key</summary>
  <div class="keygrid">
    {''.join(f'<div><code>{k}</code>{v}</div>' for k, v in KEY)}
  </div>
</details>

<div class="controls">
  <span style="font-size:13px;color:var(--ink2)">Show</span>
  <button data-f="all" aria-pressed="true">All 51</button>
  <button data-f="surv" aria-pressed="false">Survives all three nulls</button>
  <button data-f="clears" aria-pressed="false">Clears measured cost</button>
  <button data-f="both" aria-pressed="false">Both</button>
</div>

{''.join(table(c, l, b) for c, l, b in CON)}

<footer>Generated from <code>data/d290_stage1.json</code>. The left stripe marks a
candidate whose weakest null z is positive; the cost pill turns green at 1.00&times;.
Borrow is absent from the short cost bar because this fixture cannot measure it, so
every short number is optimistic by that amount.</footer>
</div>

<script>
const btns = document.querySelectorAll('.controls button');
btns.forEach(b => b.addEventListener('click', () => {{
  btns.forEach(o => o.setAttribute('aria-pressed', String(o === b)));
  const f = b.dataset.f;
  document.querySelectorAll('tbody tr').forEach(tr => {{
    const s = tr.classList.contains('surv'), c = tr.classList.contains('clears');
    const show = f === 'all' || (f === 'surv' && s) || (f === 'clears' && c)
              || (f === 'both' && s && c);
    tr.style.display = show ? '' : 'none';
  }});
}}));
</script>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(HTML, encoding="utf-8")
print(f"wrote {OUT.relative_to(REPO)}  {OUT.stat().st_size / 1024:.0f} KB")
