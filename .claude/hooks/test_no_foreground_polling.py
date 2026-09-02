"""Prove the polling blocker BOTH fires and stays quiet. A gate that cannot fail
is worse than none, and a gate that fires on everything is worse than that."""
import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(".claude/hooks/no_foreground_polling.py").resolve()
S = "sl" + "eep"                      # kept out of literal form so this driver
N = "noh" + "up"                      # does not trip the very hook it tests
PS = "Start-" + "Sleep"

CASES = [
    (2, "Bash", f"{S} 115; tail -5 log", None, "foreground poll"),
    (2, "Bash", f"cd x && {S} 60; cat f", None, f"{S} after &&"),
    (2, "Bash", f"for i in 1 2; do {S} 5; done", None, f"{S} inside a do-loop"),
    (2, "PowerShell", f"{PS} -Seconds 30", None, "PowerShell sleep"),
    (2, "Bash", f"{N} foo", None, "detach via nohup"),
    (2, "Bash", "python a.py & python b.py &", None, "detached, no wait"),
    (0, "Bash", f"{S} 115; tail log", True, "background wait-loop is fine"),
    (0, "Bash", "for i in 0 1; do w $i & done; wait", None, "fan-out ending in wait"),
    (0, "Bash", "uv run p.py > l 2>&1", None, "2>&1 is not job control"),
    (0, "Bash", "git commit -m x && git log", None, "&& is not job control"),
    (0, "Bash", f"{S} 3 # hook:allow-sleep port settling", None, "escape hatch"),
    (0, "Read", f"{S} 99", None, "not a shell tool"),
    # writing ABOUT the anti-pattern is not committing it. The hook blocked its
    # own commit message on the first run, which is how this case exists.
    (0, "Bash", f"git commit -F - <<'EOF'\nfix: never use {N} here\nand never {S} 5\nEOF",
     None, "prose inside a heredoc body"),
    (2, "Bash", f"cat <<'EOF' > f\nharmless text\nEOF\n{S} 30; tail f",
     None, "a real poll AFTER a heredoc still blocks"),
    # an ampersand inside a quoted argument is not job control. This blocked a
    # real sed whose replacement contained numpy's bitwise-and.
    (0, "Bash", "sed -i 's/v=m&np.isfinite(d)/v=m\\&np.isfinite(d)\\&(y!=2020)/' f.py",
     None, "bitwise-and inside a sed argument"),
    (0, "Bash", "python -c \"print(a&b)\"", None, "bitwise-and in python -c"),
    (2, "Bash", "python long.py &", None, "trailing job-control ampersand"),
]

bad = 0
for want, tool, cmd, bg, why in CASES:
    ti = {"command": cmd}
    if bg:
        ti["run_in_background"] = True
    p = subprocess.run([sys.executable, str(HOOK)],
                       input=json.dumps({"tool_name": tool, "tool_input": ti}),
                       capture_output=True, text=True)
    ok = p.returncode == want
    bad += not ok
    tag = "BLOCK" if want == 2 else "allow"
    print(f"  {'ok ' if ok else 'FAIL'} {tag:5s} {why:34s} exit={p.returncode}")

print(f"\n{f'ALL {len(CASES)} CASES CORRECT' if not bad else f'{bad} CASE(S) WRONG'}")
sys.exit(1 if bad else 0)
