"""Watchdog for the pre-lapse options downloaders (2026-09-28; the principal: "Make sure they catch whenever they hang").

    python -u scripts/watch_prelapse_downloads.py        # run under Monitor; every printed line is an event

`databento_download.py` already catches a stalled CONNECTION (a 120 s read timeout, then resume). This catches the rest:
a downloader PROCESS that stops making progress anywhere (a status call without a timeout, a frozen interpreter).

Every CHECK_S seconds it measures the bytes written to the jobs' per-file downloads and reads new lines of
`data/raw/databento/download_events.jsonl`, and prints a line when:
- a stall / error / abandoned / hash_mismatch / job_end event is logged;
- no byte has been written for HUNG_S while a downloader runs: it KILLS that set's downloader and RESTARTS it (the
  per-file resume keeps every byte already written), and says so;
- a set's downloader is not running: EXITED (finished, or died), with the job record's state;
- every job of both sets is recorded as downloaded: ALL DONE, and it exits.
Restarted downloaders run detached and log to `data/raw/databento/downloader_<set>.log`.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
EVENTS = RAW / "download_events.jsonl"
SETS = ("nq", "energy")
CHECK_S, HUNG_S = 60, 15 * 60
LOUD = {"stall", "error", "abandoned", "hash_mismatch", "job_end", "oversize", "rate_limited"}


def say(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def jobs(which: str) -> list[dict]:
    return json.loads((REPO / "data" / f"prelapse_options_pull_jobs_{which}.json").read_text(encoding="utf-8"))["jobs"]


def written_bytes() -> int:
    n = 0
    for s in SETS:
        for j in jobs(s):
            d = RAW / j["job"]["id"]
            if d.exists():
                n += sum(p.stat().st_size for p in d.glob("*.dbn.zst"))
    return n


def running() -> dict[str, list[int]]:
    out = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | "
                          "Where-Object { $_.CommandLine -match 'fetch_prelapse_options' } | "
                          "ForEach-Object { \"$($_.ProcessId) $($_.CommandLine)\" }"],
                         capture_output=True, text=True).stdout
    procs: dict[str, list[int]] = {s: [] for s in SETS}
    for line in out.splitlines():
        for s in SETS:
            if f"--set {s}" in line:
                procs[s].append(int(line.split()[0]))
    return procs


def start(which: str) -> None:
    log = (RAW / f"downloader_{which}.log").open("a", encoding="utf-8")
    subprocess.Popen([sys.executable, "-u", str(REPO / "scripts" / "fetch_prelapse_options.py"), "--set", which,
                      "--download", "--wait"], cwd=REPO, stdout=log, stderr=subprocess.STDOUT,
                     creationflags=getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))


def main() -> int:
    pos = EVENTS.stat().st_size if EVENTS.exists() else 0
    last_bytes, last_growth = written_bytes(), time.time()
    exited_said: set[str] = set()
    say(f"watching: {last_bytes / 1e9:.2f} GB written so far; hang = no byte for {HUNG_S // 60} min")
    while True:
        time.sleep(CHECK_S)
        if EVENTS.exists():
            with EVENTS.open(encoding="utf-8") as f:
                f.seek(pos)
                for line in f:
                    try:
                        e = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if e.get("event") in LOUD:
                        say(f"{e['event'].upper()} {e.get('job', '')} {e.get('file', '')} "
                            + " ".join(f"{k}={v}" for k, v in e.items() if k not in ("utc", "event", "job", "file")))
                pos = f.tell()
        b = written_bytes()
        if b > last_bytes:
            last_bytes, last_growth = b, time.time()
        procs = running()
        done = {s: all("downloaded_utc" in j for j in jobs(s)) for s in SETS}
        if all(done.values()):
            say(f"ALL DONE: every job of both sets downloaded and verified ({b / 1e9:.2f} GB)")
            return 0
        for s in SETS:
            if not procs[s] and not done[s] and s not in exited_said:
                say(f"EXITED: the {s} downloader is not running and its jobs are not all downloaded; restarting it")
                start(s)
                exited_said.add(s)
            elif procs[s]:
                exited_said.discard(s)
        if time.time() - last_growth > HUNG_S and any(procs.values()):
            say(f"HUNG: no byte written for {(time.time() - last_growth) / 60:.0f} min at {b / 1e9:.2f} GB; killing and restarting")
            for s in SETS:
                for pid in procs[s]:
                    subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"], capture_output=True)
                if not done[s]:
                    start(s)
            last_growth = time.time()


if __name__ == "__main__":
    sys.exit(main())
