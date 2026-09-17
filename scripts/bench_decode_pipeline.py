"""Measure where the decode pipeline actually bottlenecks on THIS machine.

The chain for any study reading a Databento fixture is:

    disk (zstd-compressed DBN)  ->  zstd decompress  ->  DBN parse  ->  numpy

An external drive only needs to be fast enough to keep the SLOWEST downstream stage
busy. Buying past that point is wasted money, so this measures each stage.
"""
from __future__ import annotations

import gzip
import io
import os
import struct
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import zstandard as zstd

# Resolved from this file, not hardcoded: the literal absolute path this line used to
# hold was the author's own checkout, so the script could not run on any other machine.
REPO = Path(__file__).resolve().parents[1]
BARS = REPO / "data" / "fixtures" / "index_extended_15m_raw.csv.gz"
SCRATCH = Path(sys.argv[1] if len(sys.argv) > 1 else ".")


def build_dbn_ohlcv(target_mb: int = 512) -> bytes:
    """Real market bars packed into the exact 56-byte DBN OHLCV record layout,
    tiled up to `target_mb` so the timing is not dominated by cache effects."""
    rows = []
    with gzip.open(BARS, "rt") as fh:
        fh.readline()
        for line in fh:
            p = line.rstrip("\n").split(",")
            ts = datetime.fromisoformat(p[0]).replace(tzinfo=timezone.utc)
            rows.append((int(ts.timestamp() * 1e9), float(p[2]), float(p[3]),
                         float(p[4]), float(p[5]), int(float(p[6]))))
    buf = io.BytesIO()
    for ts, o, h, lo, c, v in rows:
        buf.write(struct.pack("<BBHIq", 14, 0x22, 1, 12345, ts))
        buf.write(struct.pack("<qqqq", *(int(round(x * 1e9)) for x in (o, h, lo, c))))
        buf.write(struct.pack("<Q", v))
    one = buf.getvalue()
    reps = max(1, (target_mb * 1024 * 1024) // len(one))
    return one * reps


def timed(fn, *a, **k):
    t0 = time.perf_counter()
    r = fn(*a, **k)
    return r, time.perf_counter() - t0


def main() -> None:
    print(f"cores: {os.cpu_count()} logical\n")
    raw = build_dbn_ohlcv(512)
    n_rec = len(raw) // 56
    print(f"test payload: {len(raw)/1e6:.0f} MB uncompressed, {n_rec:,} DBN OHLCV records\n")

    # ---- 1. zstd compress / decompress, single thread ----
    comp, t_c = timed(zstd.ZstdCompressor(level=3).compress, raw)
    ratio = len(raw) / len(comp)
    dec, t_d = timed(zstd.ZstdDecompressor().decompress, comp, max_output_size=len(raw) + 64)
    assert dec == raw
    print(f"zstd level 3   ratio {ratio:.2f}x")
    print(f"  compress     {len(raw)/1e6/t_c:8.0f} MB/s (uncompressed side)")
    print(f"  DECOMPRESS   {len(raw)/1e6/t_d:8.0f} MB/s uncompressed  "
          f"= {len(comp)/1e6/t_d:6.0f} MB/s of DISK READ to keep ONE core fed")
    dec_mb_s = len(raw) / 1e6 / t_d
    disk_per_core = len(comp) / 1e6 / t_d

    # ---- 2. DBN parse into numpy, the stage Python actually pays for ----
    dt = np.dtype([("hdr", "u1", 4), ("iid", "<u4"), ("ts", "<i8"),
                   ("o", "<i8"), ("h", "<i8"), ("l", "<i8"), ("c", "<i8"), ("v", "<u8")])
    assert dt.itemsize == 56, dt.itemsize

    def parse(buf):
        a = np.frombuffer(buf, dtype=dt)
        return (a["c"].astype(np.float64) * 1e-9).sum()

    _, t_p = timed(parse, raw)
    print(f"\nDBN -> numpy (frombuffer, zero-copy view + one float cast)")
    print(f"  PARSE        {len(raw)/1e6/t_p:8.0f} MB/s  = {n_rec/t_p/1e6:.1f} M records/s")
    parse_mb_s = len(raw) / 1e6 / t_p

    # ---- 3. the honest end-to-end: read compressed bytes -> usable float array ----
    def end_to_end(cbuf):
        d = zstd.ZstdDecompressor().decompress(cbuf, max_output_size=len(raw) + 64)
        return parse(d)

    _, t_e = timed(end_to_end, comp)
    e2e_unc = len(raw) / 1e6 / t_e
    e2e_disk = len(comp) / 1e6 / t_e
    print(f"\nEND TO END, one core: compressed bytes -> float array")
    print(f"  {e2e_unc:8.0f} MB/s uncompressed = {e2e_disk:6.0f} MB/s of DISK READ per core")

    # ---- 4. what that implies for a drive ----
    print(f"\n{'cores used':>12}{'disk read needed (MB/s)':>26}")
    for c in (1, 4, 8, 12, 16):
        print(f"{c:>12}{e2e_disk*c:>26,.0f}")

    # ---- 5. measure the INTERNAL NVMe as a baseline, on a real file ----
    p = SCRATCH / "_bench_blob.bin"
    p.parent.mkdir(parents=True, exist_ok=True)
    blob = comp * max(1, int(600e6 // len(comp)))
    _, t_w = timed(lambda: p.write_bytes(blob))
    # drop what we can of the cache by reading a different large region first
    _, t_r = timed(lambda: p.read_bytes())
    print(f"\ninternal NVMe on {SCRATCH.drive or SCRATCH}  ({len(blob)/1e6:.0f} MB file)")
    print(f"  write {len(blob)/1e6/t_w:7.0f} MB/s     read {len(blob)/1e6/t_r:7.0f} MB/s "
          f"(warm cache inflates read)")
    try:
        p.unlink()
    except OSError:
        pass

    print(f"\nSUMMARY")
    print(f"  zstd decompress alone   {dec_mb_s:,.0f} MB/s/core -> {disk_per_core:,.0f} MB/s disk/core")
    print(f"  numpy parse alone       {parse_mb_s:,.0f} MB/s/core")
    print(f"  end to end              {e2e_unc:,.0f} MB/s/core -> {e2e_disk:,.0f} MB/s disk/core")


if __name__ == "__main__":
    main()
