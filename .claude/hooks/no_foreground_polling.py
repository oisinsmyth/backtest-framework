#!/usr/bin/env python
"""PreToolUse blocker: no foreground polling, no detached backgrounding.

Wired in `.claude/settings.json` against `Bash` and `PowerShell`. Reads the tool
call as JSON on stdin, exits 2 to BLOCK with the reason on stderr, exits 0 to
allow.

WHY IT EXISTS. A foreground `sleep` is not waiting, it is BLOCKING THE AGENT.
The work is already running in the background and the harness re-invokes on real
exit, so a `sleep 115; tail log` call buys nothing and costs the user the ability
to interject for the whole two minutes. It happened repeatedly in D288 -- a
26-minute gate A was correctly backgrounded and then polled in the foreground
anyway, which is a foreground task wearing a background task's clothes.

THREE RULES, all already in CLAUDE.md; this makes them fail loudly instead of
quietly.

  1. FOREGROUND `sleep` / `Start-Sleep`   -> blocked.
     Background it and wait for the notification, or use Monitor with an
     until-loop. Never poll.

  2. `nohup`                              -> blocked.
     It detaches, so the wrapper exits at once and the completion notice fires
     on nothing.

  3. Detached `&` with no `wait`          -> blocked.
     Same failure. `cmd & ... ; wait` is FINE and is not blocked -- that is a
     real process fan-out (D288 ran 8 workers that way) and it does not return
     until the children do.

ESCAPE HATCH, deliberately noisy. Append `# hook:allow-sleep <reason>` to the
command. It has to be typed, it names a reason, and it is visible to the user in
the command itself -- so the choice is deliberate rather than reflexive.
"""

from __future__ import annotations

import json
import re
import sys

TOOLS = {"Bash", "PowerShell"}
HATCH = re.compile(r"#\s*hook:allow-sleep\s+\S")

# a `sleep` in COMMAND POSITION: start of the string or after a separator.
SLEEP_SH = re.compile(r"(?:^|[\n;|&]|\bdo\b|\bthen\b)\s*sleep\s+[\d.]", re.M)
SLEEP_PS = re.compile(r"\bStart-Sleep\b", re.I)
NOHUP = re.compile(r"\bnohup\b")
# `&` that is job control: not `&&`, not `2>&1`, not `&>`.
DETACH = re.compile(r"(?<![&>\d])&(?![&>])")
WAIT = re.compile(r"(?:^|[\n;&|])\s*wait\b", re.M)
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")


def strip_heredocs(cmd: str) -> str:
    """Remove heredoc BODIES before matching. They are data, not commands.

    This hook blocked its own commit on the first run: the message described
    `nohup` in prose, inside a `<<'EOF'` body, and the matcher saw the literal
    string. Writing ABOUT the anti-pattern is not committing it, and a gate that
    fires on its own documentation trains you to disable it.
    """
    lines, out, i = cmd.split("\n"), [], 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = HEREDOC.search(line)
        i += 1
        if not m:
            continue
        delim = m.group(2)
        while i < len(lines) and lines[i].strip() != delim:
            i += 1                     # body dropped
        if i < len(lines):
            out.append(lines[i])       # keep the closing delimiter
            i += 1
    return "\n".join(out)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0                      # never break the session on a parse error

    if payload.get("tool_name") not in TOOLS:
        return 0
    ti = payload.get("tool_input") or {}
    cmd = ti.get("command") or ""
    if not isinstance(cmd, str) or not cmd.strip():
        return 0
    background = bool(ti.get("run_in_background"))
    cmd = strip_heredocs(cmd)

    if NOHUP.search(cmd):
        print(
            "BLOCKED: `nohup` detaches, so the wrapper exits immediately and the "
            "completion notification fires on nothing.\n"
            "Use `run_in_background: true` and wait to be re-invoked on real exit.",
            file=sys.stderr)
        return 2

    if DETACH.search(cmd) and not WAIT.search(cmd):
        print(
            "BLOCKED: a detached `&` with no `wait` exits before its children, so "
            "the completion notification fires on nothing.\n"
            "Either use `run_in_background: true`, or keep the fan-out and end it "
            "with `wait` (`for i in ...; do cmd & done; wait`).",
            file=sys.stderr)
        return 2

    if background:
        return 0                      # a wait-loop inside a background task is fine

    hit = SLEEP_SH.search(cmd) or SLEEP_PS.search(cmd)
    if hit and not HATCH.search(cmd):
        print(
            "BLOCKED: a foreground `sleep` does not wait, it BLOCKS THE AGENT and "
            "stops the user interjecting for its whole duration.\n"
            "The work is already running and the harness re-invokes you on real "
            "exit -- do not poll.\n"
            "  - long command      -> run_in_background: true, then stop and wait\n"
            "  - waiting on a cond -> Monitor with an until-loop\n"
            "  - genuinely needed  -> append `# hook:allow-sleep <reason>`",
            file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
