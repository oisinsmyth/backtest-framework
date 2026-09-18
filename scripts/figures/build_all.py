"""Write every figure in `docs/figures/`, or fail if a committed one has drifted.

    python scripts/figures/build_all.py --build     # write them
    python scripts/figures/build_all.py --check     # exit 1, naming every stale file
    python scripts/figures/build_all.py --list      # what exists, and where each one comes from

WHOLE FILES, NOT MARKED REGIONS
-------------------------------
`build_readme_counts.py` compares a marked block after `.strip()`, because it lives inside a
hand-written document that has slack around it. A figure has none: the file is generated end to
end, so the comparison is byte equality and the renderer emits exactly one trailing newline.

WHY A REGISTRY RATHER THAN A GLOB
---------------------------------
Each builder is imported by name here. A figure that is not in this list is not built, not
checked, and -- because `tests/unit/test_figures_index_is_complete.py` reads this same list --
not indexed either. Discovering builders by globbing would make forgetting to register one
silent, which is the failure mode every completeness guard in this repository exists to remove.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import svgkit as k  # noqa: E402

BUILDERS = (
    "build_dsr_hurdle",
    "build_lookahead",
    "build_two_nulls",
    "build_cross_engine",
    "build_cost_waterfall",
    "build_ledger_diff",
)


def modules() -> list[ModuleType]:
    """Every registered builder, or a clear failure naming the one that is missing."""
    out = []
    for name in BUILDERS:
        try:
            out.append(importlib.import_module(name))
        except ModuleNotFoundError as exc:  # pragma: no cover - a half-finished round
            if exc.name != name:
                raise
            raise SystemExit(
                f"{name} is registered in build_all.BUILDERS but scripts/figures/{name}.py "
                "does not exist. Either write it or remove it from the list."
            ) from exc
    return out


def render_all() -> dict[Path, str]:
    out: dict[Path, str] = {}
    for module in modules():
        for path, content in module.files().items():
            if path in out:  # pragma: no cover - two builders claiming one slug
                raise SystemExit(f"two builders both write {path.name}")
            out[path] = content
    return out


def cmd_build() -> int:
    k.FIGURES.mkdir(parents=True, exist_ok=True)
    written = render_all()
    for path, content in written.items():
        path.write_text(content, encoding="utf-8", newline="\n")
    total = sum(len(c.encode("utf-8")) for c in written.values())
    print(f"wrote {len(written)} files to docs/figures/ ({total:,} bytes)")
    return 0


def cmd_check() -> int:
    # BYTES, not text. `--build` writes with `newline="\n"` -- a property it deliberately
    # controls, because these files are compared byte for byte and the module docstring says so.
    # Reading with `read_text(encoding="utf-8")` applies universal-newline translation, so a
    # figure rewritten with CRLF by an editor, a zip download or a checkout that bypassed
    # `.gitattributes` decoded back to `\n` and compared EQUAL. The check was blind to exactly
    # the thing the build controls, and would have reported "12 figure files are current" over
    # twelve files none of which matched what `--build` produces.
    #
    # `render_all()` is bound once: it re-imports and re-executes all six builder modules on
    # every call, and the success path used to do that twice -- once to compare, once for a
    # count it was already holding.
    rendered = render_all()
    stale = [
        path
        for path, want in rendered.items()
        if not path.exists() or path.read_bytes() != want.encode("utf-8")
    ]
    for path in stale:
        state = "MISSING" if not path.exists() else "STALE"
        print(
            f"{state}  {path.relative_to(k.REPO).as_posix()} — "
            "run `python scripts/figures/build_all.py --build`"
        )
    if not stale:
        print(f"{len(rendered)} figure files are current")
    return 1 if stale else 0


def cmd_list() -> int:
    for module in modules():
        print(f"{module.SLUG:<28} {module.SOURCE}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--list", action="store_true", dest="listing")
    args = ap.parse_args()
    if args.build:
        return cmd_build()
    if args.check:
        return cmd_check()
    if args.listing:
        return cmd_list()
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
