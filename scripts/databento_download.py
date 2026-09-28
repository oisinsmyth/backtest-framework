"""A hang-proof, resumable downloader for finished Databento batch jobs, shared by `fetch_prelapse_options.py` and
`fetch_prelapse_topup.py` (2026-09-28, after two stalls lost every byte of a whole-job zip: the client's own download
calls `requests.get` with NO timeout, so a stalled connection waits forever).

- Each job is downloaded FILE BY FILE from its manifest (`batch.list_files`), never as one whole-job zip, so an
  interruption costs at most the current file's unwritten tail.
- Every request has a connect timeout (30 s) and a READ timeout (120 s): two minutes without a byte raises, and the
  file RESUMES from its last written byte with an HTTP Range request.
- Retries back off (5 s doubling to 5 min). A file is abandoned only after STALL_LIMIT consecutive attempts that added
  no bytes; the job continues with its other files and the abandoned one is reported.
- Each finished file's SHA-256 is checked against the manifest. A mismatch is logged and the file is re-fetched once
  (the corrupt copy is renamed `.bad`, not deleted).
- Every event (start, stall, retry, resume, done, hash) is appended to `data/raw/databento/download_events.jsonl`
  with a UTC stamp, and printed. The key is never printed or logged.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

CONNECT_TIMEOUT, READ_TIMEOUT = 30, 120
STALL_LIMIT = 5
CHUNK = 1024 * 1024  # a stall loses at most one unwritten chunk
EVENTS = Path(__file__).resolve().parents[1] / "data" / "raw" / "databento" / "download_events.jsonl"


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def event(kind: str, **kw: Any) -> None:
    row = {"utc": now(), "event": kind, **kw}
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(row) + "\n")
    print(f"  [{row['utc']}] {kind} " + " ".join(f"{k}={v}" for k, v in kw.items()), flush=True)


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open(mode="rb") as f:
        while b := f.read(32 * 1024 * 1024):
            h.update(b)
    return h.hexdigest()


def fetch_file(key: str, job_id: str, name: str, url: str, size: int, digest: str, out: Path) -> dict[str, Any]:
    """One manifest file, resumable and timeout-guarded. Returns what happened."""
    stalls = attempts = 0
    backoff = 5.0
    ok_marker = out.with_name(out.name + ".sha256ok")
    if ok_marker.exists() and out.exists() and out.stat().st_size == size:
        return {"file": name, "status": "already verified", "bytes": size}
    refetched = False
    while True:
        have = out.stat().st_size if out.exists() else 0
        if have > size:
            bad = out.with_name(out.name + ".bad")
            out.rename(bad)
            event("oversize", job=job_id, file=name, have=have, size=size, moved_to=bad.name)
            have = 0
        if have < size:
            attempts += 1
            headers = {"Range": f"bytes={have}-{size - 1}"} if have else {}
            before = have
            try:
                if have:
                    event("resume", job=job_id, file=name, from_bytes=have, of=size, attempt=attempts)
                with requests.get(url, headers=headers, auth=HTTPBasicAuth(key, ""), stream=True, allow_redirects=True,
                                  timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)) as r:
                    if r.status_code == 429:
                        wait = int(r.headers.get("Retry-After", "30"))
                        event("rate_limited", job=job_id, file=name, wait_s=wait)
                        time.sleep(wait)
                        continue
                    r.raise_for_status()
                    if have and r.status_code != 206:
                        raise RuntimeError(f"server ignored the Range request (HTTP {r.status_code})")
                    with out.open(mode="ab") as f:  # have == 0 means empty or absent: append == write
                        for chunk in r.iter_content(chunk_size=CHUNK):
                            f.write(chunk)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError,
                    requests.exceptions.ChunkedEncodingError, requests.exceptions.HTTPError, RuntimeError) as e:
                got = (out.stat().st_size if out.exists() else 0) - before
                stalls = 0 if got > 0 else stalls + 1
                # a read timeout mid-stream surfaces as a ConnectionError wrapping urllib3's ReadTimeoutError
                kind = "stall" if isinstance(e, requests.exceptions.Timeout) or "timed out" in str(e).lower() else "error"
                event(kind, job=job_id, file=name, error=type(e).__name__, added_bytes=got, no_progress_in_a_row=stalls,
                      retry_in_s=int(backoff))
                if stalls >= STALL_LIMIT:
                    event("abandoned", job=job_id, file=name, have=out.stat().st_size if out.exists() else 0, size=size)
                    return {"file": name, "status": "abandoned", "bytes": out.stat().st_size if out.exists() else 0}
                time.sleep(backoff)
                backoff = min(backoff * 2, 300.0) if got == 0 else 5.0
                continue
            continue  # loop back: re-check the size
        algo, _, hexd = digest.partition(":")
        if algo != "sha256":
            event("hash_skipped", job=job_id, file=name, algo=algo)
            return {"file": name, "status": "done (hash not sha256)", "bytes": size}
        got_hex = sha256_of(out)
        if got_hex == hexd:
            ok_marker.write_text(hexd + "\n", encoding="utf-8", newline="\n")
            event("done", job=job_id, file=name, bytes=size, sha256="ok", attempts=attempts)
            return {"file": name, "status": "verified", "bytes": size, "attempts": attempts}
        bad = out.with_name(out.name + ".bad")
        out.rename(bad)
        event("hash_mismatch", job=job_id, file=name, moved_to=bad.name, refetch=not refetched)
        if refetched:
            return {"file": name, "status": "hash mismatch twice", "bytes": size}
        refetched = True


def download_job(client: Any, key: str, job_id: str, raw: Path) -> dict[str, Any]:
    """Every file of a finished job into raw/<job_id>/. Returns a summary for the job record."""
    manifest = client.batch.list_files(job_id)
    out_dir = raw / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    event("job_start", job=job_id, files=len(manifest), bytes=sum(int(m["size"]) for m in manifest))
    results = []
    for m in sorted(manifest, key=lambda z: str(z["filename"])):
        results.append(fetch_file(key, job_id, str(m["filename"]), m["urls"]["https"], int(m["size"]),
                                  str(m["hash"]), out_dir / str(m["filename"])))
    done = [r for r in results if r["status"] in ("verified", "already verified", "done (hash not sha256)")]
    summary = {"files": len(manifest), "verified": len(done), "bytes": int(sum(r["bytes"] for r in done)),
               "incomplete": [r for r in results if r not in done], "finished_utc": now()}
    event("job_end", job=job_id, verified=f"{len(done)}/{len(manifest)}", gb=round(summary["bytes"] / 1e9, 2))
    return summary
