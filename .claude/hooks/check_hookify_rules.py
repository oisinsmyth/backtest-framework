"""Does the real hookify engine load our rules and actually deny?"""
import json
import subprocess
import sys

L = ".claude/hooks/hookify_pretooluse.py"
S = "sl" + "eep"
N = "noh" + "up"

CASES = [
    (True, "Bash", f"{S} 115; tail -5 log", "foreground poll"),
    (True, "Bash", f"{N} foo", "detaching launcher"),
    (False, "Bash", "git status", "ordinary command"),
    (False, "Bash", f"{S} 3 # hook:allow-sleep port settling", "escape hatch"),
]

bad = 0
for want_deny, tool, cmd, why in CASES:
    p = subprocess.run([sys.executable, L],
                       input=json.dumps({"tool_name": tool,
                                         "hook_event_name": "PreToolUse",
                                         "tool_input": {"command": cmd}}),
                       capture_output=True, text=True)
    out = p.stdout.strip()
    denied = '"permissionDecision": "deny"' in out or '"decision": "block"' in out
    ok = denied == want_deny
    bad += not ok
    print(f"  {'ok ' if ok else 'FAIL'} {'DENY ' if want_deny else 'allow'} "
          f"{why:22s} denied={denied}")
    if not ok or (p.stderr.strip() and "error" in p.stderr.lower()):
        print(f"        stdout: {out[:200]}")
        if p.stderr.strip():
            print(f"        stderr: {p.stderr.strip()[:200]}")

print(f"\n{'HOOKIFY ENGINE WORKS' if not bad else f'{bad} CASE(S) WRONG'}")
sys.exit(1 if bad else 0)
