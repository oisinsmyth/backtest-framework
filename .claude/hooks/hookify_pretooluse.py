#!/usr/bin/env python
"""Run hookify's PreToolUse hook WITHOUT installing it as a plugin.

There is no `claude` CLI on this machine -- this is the desktop/remote app -- so
`claude --plugin-dir .../hookify`, the documented install, cannot run here at
all. Hookify's hook is only a script, though, so it can be wired straight into
`.claude/settings.json`. This launcher supplies the two things the plugin loader
would normally provide:

  1. `CLAUDE_PLUGIN_ROOT`, which `hooks/pretooluse.py` reads to put the plugin's
     PARENT on `sys.path` -- it imports `hookify.core.*`, so the directory must
     be named `hookify` and its parent must be importable. The sparse clone
     gives exactly that shape: `<src>/plugins/hookify`.
  2. `python` rather than `python3`. `hooks/hooks.json` hardcodes `python3`,
     which is not on PATH on Windows.

Rules live in `.claude/hookify.*.local.md` and are found by `glob` RELATIVE TO
THE WORKING DIRECTORY, so this hook only sees them when the session's cwd is the
project root. That is the normal case and is asserted below rather than assumed
-- a rule file that is silently never loaded is a gate that cannot fire, which
this repo holds to be worse than no gate at all.

Hookify maps `Bash` -> bash and `Edit`/`Write`/`MultiEdit` -> file. It does NOT
map the `PowerShell` tool, which is why the native blocker still covers that.
"""

from __future__ import annotations

import json
import os
import runpy
import sys
from pathlib import Path

# Resolved, never hardcoded. Until this change `ROOT` was an absolute path under the
# AUTHOR'S home directory, and the miss branch in `main()` PRINTED it -- so every cloner
# who enabled this hook got a stranger's home directory echoed into their own session.
# The candidates below are in precedence order; the first whose `hooks/pretooluse.py`
# exists wins. `HOOKIFY_ROOT` is the explicit override, `CLAUDE_PROJECT_DIR` covers a
# checkout vendored beside the project, and `Path.home()` covers a per-user install.
_REL = Path("hookify-src") / "plugins" / "hookify"


def _candidates() -> list[Path]:
    out: list[Path] = []
    env = os.environ.get("HOOKIFY_ROOT")
    if env:
        out.append(Path(env))
    proj = os.environ.get("CLAUDE_PROJECT_DIR")
    if proj:
        out.append(Path(proj) / ".claude" / _REL)
    out.append(Path.home() / ".claude" / _REL)
    return out


def _find_root() -> Path | None:
    for c in _candidates():
        if (c / "hooks" / "pretooluse.py").exists():
            return c
    return None


def main() -> int:
    root = _find_root()
    if root is None:
        # Fail OPEN, loudly. A missing checkout must not wedge every tool call.
        # The message names the ENV VARS and the relative shape, never an absolute
        # path: this branch runs on a stranger's machine and has no business
        # reciting a directory from the machine the hook was written on.
        print(json.dumps({"systemMessage":
                          "hookify checkout not found (looked at $HOOKIFY_ROOT, "
                          "$CLAUDE_PROJECT_DIR/.claude/hookify-src/plugins/hookify, "
                          "and ~/.claude/hookify-src/plugins/hookify); "
                          "rules are NOT enforced"}))
        return 0

    os.environ["CLAUDE_PLUGIN_ROOT"] = str(root)
    runpy.run_path(str(root / "hooks" / "pretooluse.py"), run_name="__main__")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:                                   # never wedge a session
        print(json.dumps({"systemMessage": f"hookify launcher error: {e}"}))
        sys.exit(0)
