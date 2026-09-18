"""Splice ONE section into a results document without eating its neighbours (D542).

    from results_document import splice_section
    splice_section(RESULTS, marker, render(payload), anchor="---\\n\\n### Parking lot")

WHY THIS EXISTS
---------------
Eight runners write sections into `docs/results/STRUCTURE_RESULTS.md`, and each carried
the same eleven-line splice:

    head, _, rest = text.partition(marker)
    _, sep, tail = rest.partition(anchor)
    text = head + body + "\\n" + anchor + tail if sep else head + body

That replaces everything from the runner's own heading down to the parking lot at the
BOTTOM OF THE FILE. It was correct for each runner on the day it was written, because each
was then the last section. It stopped being correct the moment the next runner appended
below it, and nothing said so — the document simply got shorter.

Measured before the fix, per runner, on the live document:

    run_structure_components   61,508 chars, 8 sections   (incl. the FINAL REPORT)
    run_structure_marginal     48,420 chars, 7 sections
    run_structure_audit        45,069 chars, 6 sections
    run_structure_pnl          31,676 chars, 4 sections
    run_structure_selection    24,820 chars, 3 sections
    run_structure_terrain_gate 15,916 chars, 2 sections
    run_generic_reversal        9,353 chars, 1 section
    run_reversion_tail                 0 — it is still the last section

Seven of eight would destroy published results written by other runners, silently, on a
plain re-run. **Each of those sections prints `Reproduce: uv run python scripts/<its own
runner>` directly beneath its heading**, so a reader following the document's own
instructions was the mechanism.

Found during D542 by diffing the document after a re-run — not by reading the function.
The `else head + body` branch is the tell: a fallback whose behaviour is "keep the start
and discard the rest" is a truncation with a comma in front of it.

WHAT THIS DOES INSTEAD
----------------------
The replacement is bounded by the NEXT top-level heading, so a section can neither grow
into its neighbours nor outlive them, and it REFUSES rather than truncating when it has no
boundary to stop at. A missing section is still inserted above the anchor.
"""

from __future__ import annotations

from pathlib import Path

PARKING_LOT = "---\n\n### Parking lot"
"""The conventional bottom-of-document anchor these runners insert above."""


def splice_section(
    path: Path, marker: str, body: str, anchor: str = PARKING_LOT
) -> None:
    """Replace the section headed `marker` with `body`, or insert it above `anchor`.

    `marker` is the section's `## ` heading line, and `body` must begin with it.
    Everything from the NEXT `## ` heading onward is preserved exactly.
    """
    if not body.lstrip().startswith(marker):
        raise ValueError(
            f"the rendered body does not start with its own marker {marker!r}. Splicing "
            f"it would leave the document with a section that no rerun can find again, "
            f"and the next run would insert a second copy rather than replace this one."
        )
    text = path.read_text(encoding="utf-8")

    if marker not in text:
        head, sep, rest = text.partition(anchor)
        if not sep:
            raise SystemExit(
                f"{path.name}: neither the section {marker!r} nor the anchor {anchor!r} "
                f"is present, so there is nowhere to put this section."
            )
        path.write_text(head + body.rstrip("\n") + "\n\n" + anchor + rest, encoding="utf-8")
        return

    head, _, rest = text.partition(marker)
    next_heading = rest.find("\n## ")
    anchor_at = rest.find(anchor)
    boundaries = [x for x in (next_heading, anchor_at) if x >= 0]
    if not boundaries:
        raise SystemExit(
            f"{path.name}: the section {marker!r} has no following heading and no anchor "
            f"to stop at. Refusing to write, because the only other option is to truncate "
            f"{len(rest):,} characters of someone else's results."
        )
    tail = rest[min(boundaries) :]
    path.write_text(head + body.rstrip("\n") + "\n\n" + tail.lstrip("\n"), encoding="utf-8")
