"""Splice GME's bars alone into the blank drawing page.

Same sanitiser discipline as scripts/d399_splice_charts.py: a bare NaN token makes JSON.parse
throw and renders the page blank with no visible error, so every float is finite or None and the
emitted block is re-parsed strictly before the file is written.

ONE-SHOT, PARTLY RECOVERABLE -- read this before running it. It was written against a
throwaway git worktree (`.claude/worktrees/signal-hunt-part2`) and an agent scratchpad under
the OS temp directory, neither of which exists in any clone. Its DATA input survives in the
repo as data/d399_chart_data.json and is repointed below. Its HTML TEMPLATE does not survive
anywhere: it lived only in that scratchpad. The page it produced is kept as
data/d399_gme_blank_draw.html, so the RESULT is on the record. Retained for the record, and
runs only if you hand it a template. The later, self-contained version of this page is
scripts/d478_splice_draw_page.py, which carries its own HTML.

    uv run python scripts/d399_splice_draw_page.py <template.html> [out_dir]
"""
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data" / "d399_chart_data.json"            # was <worktree>/temp/, now tracked
RENDERED = REPO / "data" / "d399_gme_blank_draw.html"    # what this script produced, kept

# Fail fast and SAY WHY. Without this the script died on a FileNotFoundError naming a
# scratchpad directory on the author's machine -- a path no cloner can act on.
if len(sys.argv) < 2:
    raise SystemExit(
        "d399_splice_draw_page.py: the `__DATA__` template this one-shot spliced into lived in\n"
        "an agent scratchpad that no longer exists and was never tracked, so there is nothing to\n"
        "default to. The rendered output is kept at data/d399_gme_blank_draw.html, and\n"
        "scripts/d478_splice_draw_page.py is the later version that carries its own HTML.\n"
        f"Pass a template explicitly:  uv run python {Path(__file__).name} <template.html> [out_dir]"
    )
TPL_PATH = Path(sys.argv[1]).resolve()
OUT_DIR = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else REPO / "temp"
if not TPL_PATH.exists():
    raise SystemExit(f"d399_splice_draw_page.py: template not found: {TPL_PATH}")
OUT_DIR.mkdir(parents=True, exist_ok=True)

src = json.loads(DATA.read_text())
gme = [c for c in src["charts"] if c["symbol"] == "GME"]
assert len(gme) == 1, f"expected one GME chart, got {len(gme)}"
c = gme[0]

keep = {k: c[k] for k in ("symbol", "start", "n", "dates", "open", "high", "low", "close")}


def clean(x, p=5):
    if isinstance(x, float):
        return None if not math.isfinite(x) else round(x, p)
    if isinstance(x, list):
        return [clean(v, p) for v in x]
    if isinstance(x, dict):
        return {k: clean(v, p) for k, v in x.items()}
    return x


keep = clean(keep)
keep["dates"] = [str(x)[:10] for x in keep["dates"]]
d = {"note": "BLANK. The principal draws the lines; nothing is fitted here.", "charts": [keep]}

payload = json.dumps(d, separators=(",", ":"), allow_nan=False)
assert "NaN" not in payload and "Infinity" not in payload

tpl = TPL_PATH.read_text(encoding="utf-8")
assert "__DATA__" in tpl
out = tpl.replace("__DATA__", payload)


def _bare(t):
    raise ValueError(f"bare {t} in the payload -- the page would render blank")


block = out.split('type="application/json">', 1)[1].split("</script>", 1)[0]
json.loads(block, parse_constant=_bare)

(OUT_DIR / "gme_draw_final.html").write_text(out, encoding="utf-8")
print(f"wrote {OUT_DIR / 'gme_draw_final.html'}  {len(out)/1024:.0f} KB; "
      f"the kept rendering is {RENDERED}")
print(f"  GME bars {keep['start']}-{keep['start']+keep['n']}  "
      f"{keep['dates'][0]} -> {keep['dates'][-1]}  n={keep['n']}")
