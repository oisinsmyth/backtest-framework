"""Splice the comparison payload into the side-by-side page. Same sanitiser discipline.

ONE-SHOT, PARTLY RECOVERABLE -- read this before running it. It was written against a
throwaway git worktree (`.claude/worktrees/signal-hunt-part2`) and an agent scratchpad under
the OS temp directory, neither of which exists in any clone. Its DATA input survives in the
repo as data/d399_compare_data.json and is repointed below. Its HTML TEMPLATE does not
survive anywhere: it lived only in that scratchpad. The page it produced is kept as
data/d399_drawn_vs_fitted.html, so the RESULT is on the record. Retained for the record, and
runs only if you hand it a template.

    uv run python scripts/d399_splice_compare_page.py <template.html> [out_dir]
"""
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data" / "d399_compare_data.json"          # was <worktree>/temp/, now tracked
RENDERED = REPO / "data" / "d399_drawn_vs_fitted.html"   # what this script produced, kept

# Fail fast and SAY WHY. Without this the script died on a FileNotFoundError naming a
# scratchpad directory on the author's machine -- a path no cloner can act on.
if len(sys.argv) < 2:
    raise SystemExit(
        "d399_splice_compare_page.py: the `__DATA__` template this one-shot spliced into lived\n"
        "in an agent scratchpad that no longer exists and was never tracked, so there is nothing\n"
        "to default to. The rendered output is kept at data/d399_drawn_vs_fitted.html.\n"
        f"Pass a template explicitly:  uv run python {Path(__file__).name} <template.html> [out_dir]"
    )
TPL_PATH = Path(sys.argv[1]).resolve()
OUT_DIR = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else REPO / "temp"
if not TPL_PATH.exists():
    raise SystemExit(f"d399_splice_compare_page.py: template not found: {TPL_PATH}")
OUT_DIR.mkdir(parents=True, exist_ok=True)

d = json.loads(DATA.read_text())


def clean(x, p=5):
    if isinstance(x, float):
        return None if not math.isfinite(x) else round(x, p)
    if isinstance(x, list):
        return [clean(v, p) for v in x]
    if isinstance(x, dict):
        return {k: clean(v, p) for k, v in x.items()}
    return x


payload = json.dumps(clean(d), separators=(",", ":"), allow_nan=False)
assert "NaN" not in payload and "Infinity" not in payload

tpl = TPL_PATH.read_text(encoding="utf-8")
assert "__DATA__" in tpl
out = tpl.replace("__DATA__", payload)


def _bare(t):
    raise ValueError(f"bare {t} in the payload -- the page would render blank")


block = out.split('type="application/json">', 1)[1].split("</script>", 1)[0]
json.loads(block, parse_constant=_bare)

(OUT_DIR / "compare_final.html").write_text(out, encoding="utf-8")
print(f"wrote {OUT_DIR / 'compare_final.html'}  {len(out)/1024:.0f} KB; "
      f"the kept rendering is {RENDERED}")
for s in ("support", "resistance"):
    r = d["ribbon"][s]
    print(f"  {s:>10s}: drawn {r['human_bars']:>3d}  fitted {r['machine_bars']:>3d}  "
          f"both {r['both']:>3d}  recall {100*r['both']/r['human_bars']:.0f}%  "
          f"precision {100*r['both']/r['machine_bars']:.0f}%")
