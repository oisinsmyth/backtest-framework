---
name: no-detached-backgrounding
enabled: true
event: bash
action: block
conditions:
  - field: command
    operator: regex_match
    pattern: \bnohup\b
---

🛑 **`nohup` detaches, so the wrapper exits immediately.**

The completion notification then fires on nothing, leaving you polling a log with
foreground `sleep`s — which is the failure this repo has already hit once.

**Do instead:** `run_in_background: true`, then stop and wait to be re-invoked on
real exit.

A `&` fan-out is fine **when it ends in `wait`** — `for i in ...; do cmd & done;
wait` does not return until its children do, and D288 ran eight build workers
that way. A bare trailing `&` has the same defect as `nohup`.

`CLAUDE.md`: *"Never `nohup`/`&` — they detach, so the wrapper exits at once and
the completion notice fires on nothing."*
