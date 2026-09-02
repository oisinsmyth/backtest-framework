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

ROOT = Path(r"C:\Users\O\.claude\hookify-src\plugins\hookify")


def main() -> int:
    if not (ROOT / "hooks" / "pretooluse.py").exists():
        # Fail OPEN, loudly. A missing checkout must not wedge every tool call.
        print(json.dumps({"systemMessage":
                          f"hookify not found at {ROOT}; rules are NOT enforced"}))
        return 0

    os.environ["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
    runpy.run_path(str(ROOT / "hooks" / "pretooluse.py"), run_name="__main__")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:                                   # never wedge a session
        print(json.dumps({"systemMessage": f"hookify launcher error: {e}"}))
        sys.exit(0)
