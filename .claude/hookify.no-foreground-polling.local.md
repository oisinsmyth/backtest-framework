---
name: no-foreground-polling
enabled: true
event: bash
action: block
conditions:
  - field: command
    operator: regex_match
    pattern: (?:^|[\n;|&]|\bdo\b|\bthen\b)\s*sleep\s+[\d.]
  - field: command
    operator: not_contains
    pattern: "hook:allow-sleep"
---

BLOCKED. A foreground `sleep` does not wait, it BLOCKS THE AGENT.

The work is already running and the harness re-invokes you on real exit. Polling
buys nothing and costs the user the ability to interject for the whole duration.

This happened repeatedly in D288: a 26-minute gate A was correctly backgrounded
and then polled with a foreground wait-and-tail anyway, which is a foreground
task wearing a background task's clothes.

Do instead:
  - long command      -> run_in_background: true, then STOP and wait for the
                         notification
  - waiting on a cond -> Monitor with an until-loop
  - genuinely needed  -> append `# hook:allow-sleep <reason>`

CLAUDE.md: ">~2 min -> run_in_background: true. Never poll; you are re-invoked
on real exit."

NOTE: this file must stay pure ASCII. hookify's config_loader opens rule files
with `open(path, 'r')` and no encoding, so on Windows a UTF-8 em-dash or emoji
is decoded as cp1252 and arrives as mojibake.
