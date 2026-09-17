"""Splice the chart data into the template.

GENERIC SANITISER, and it exists because a targeted one silently broke the page. `json.dumps`
writes bare `NaN` for a non-finite float; Python's `json.load` accepts that token, but
`JSON.parse` in the browser REJECTS it -- so one unsanitised field threw inside the page's script
and rendered NOTHING AT ALL, with no visible error. The previous version listed the fields to
round by name, and fields added later (`g_lo`, `g_hi`) were not on the list.

So: walk the whole structure, convert every non-finite float to None, and ASSERT that no NaN or
Infinity token survives into the HTML. A blank page must not be a possible outcome again.

ONE-SHOT, PARTLY RECOVERABLE -- read this before running it. It was written against a
throwaway git worktree (`.claude/worktrees/signal-hunt-part2`) and an agent scratchpad under
the OS temp directory, neither of which exists in any clone. Its DATA input survives in the
repo as data/d399_chart_data.json and is repointed below. Its HTML TEMPLATE does not survive
anywhere: it lived only in that scratchpad. The page this script produced is kept as
data/d399_ratchet_charts.html, so the RESULT is on the record even though the input template
is gone. The script is retained for the record, and runs only if you hand it a template.

    uv run python scripts/d399_splice_charts.py <template.html> [out_dir]
"""
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data" / "d399_chart_data.json"           # was <worktree>/temp/, now tracked
RENDERED = REPO / "data" / "d399_ratchet_charts.html"   # what this script produced, kept

# Fail fast and SAY WHY. Without this the script died on a FileNotFoundError naming a
# scratchpad directory on the author's machine -- a path no cloner can act on.
if len(sys.argv) < 2:
    raise SystemExit(
        "d399_splice_charts.py: the `__DATA__` template this one-shot spliced into lived in an\n"
        "agent scratchpad that no longer exists and was never tracked, so there is nothing to\n"
        "default to. The rendered output is kept at data/d399_ratchet_charts.html.\n"
        f"Pass a template explicitly:  uv run python {Path(__file__).name} <template.html> [out_dir]"
    )
TPL_PATH = Path(sys.argv[1]).resolve()
OUT_DIR = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else REPO / "temp"
if not TPL_PATH.exists():
    raise SystemExit(f"d399_splice_charts.py: template not found: {TPL_PATH}")
OUT_DIR.mkdir(parents=True, exist_ok=True)

d = json.loads(DATA.read_text())


def clean(x, p=5):
    """Every float finite or None; everything else passed through untouched."""
    if isinstance(x, float):
        return None if not math.isfinite(x) else round(x, p)
    if isinstance(x, list):
        return [clean(v, p) for v in x]
    if isinstance(x, dict):
        return {k: clean(v, p) for k, v in x.items()}
    return x


d = clean(d)
for c in d["charts"]:
    c["dates"] = [str(x)[:10] for x in c["dates"]]

payload = json.dumps(d, separators=(",", ":"), allow_nan=False)
assert "NaN" not in payload and "Infinity" not in payload, "a non-finite value survived the clean"

tpl = TPL_PATH.read_text(encoding="utf-8")
assert "__DATA__" in tpl, "marker missing"
out = tpl.replace("__DATA__", payload)


def _bare(c):
    raise ValueError(f"bare {c} in the payload -- JSON.parse would throw and the page would be blank")


block = out.split('type="application/json">', 1)[1].split("</script>", 1)[0]
json.loads(block, parse_constant=_bare)

(OUT_DIR / "ratchet_charts_final.html").write_text(out, encoding="utf-8")
print(f"wrote {OUT_DIR / 'ratchet_charts_final.html'}  {len(out) / 1024:.0f} KB  "
      f"({len(d['charts'])} charts); the kept rendering is {RENDERED}")
print(f"  {'sym':>5s} {'support':>12s} {'resistance':>12s} {'state on':>12s}")
for c in d["charts"]:
    n = c["n"]
    a = sum(1 for v in c["line_lo"] if v is not None)
    b = sum(1 for v in c["line_hi"] if v is not None)
    st = sum(1 for v in c["state"] if v != 0)
    print(f"  {c['symbol']:>5s} {a:>8d}/{n} {b:>8d}/{n} {st:>8d}/{n}")
