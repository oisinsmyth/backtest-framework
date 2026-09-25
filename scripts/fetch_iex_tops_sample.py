"""The ETF-premium bias check's quote sample: IEX's free historical TOPS feed on ten days, streamed, filtered to the
six ledger ETFs, and never stored whole (settlement ledger, A8's C2 clause and AITODO G3).

The principal approved the download on 2026-09-25 ("Go for the IEX download"): ten TOPS 1.6 files, 0.47–5.0 GB
each and about 25 GB in all. They come from IEX's public archive, whose listing is
https://iextrading.com/api/1.0/hist?date=YYYYMMDD. The IEX Historical Data Terms
(https://www.iex.io/legal/hist-data-terms) restrict no research use. A redistributor must credit "Data provided for
free by IEX".

WHAT IS KEPT. For BOIL, KOLD, UCO, SCO, UNG and USO: every Quote Update ('Q', IEX's own best bid and offer) and
every Trade Report ('T'). The layouts are TOPS 1.6, little-endian:
  Q: type 1, flags 1, timestamp 8 (ns since the epoch, UTC), symbol 8, bid size 4, bid price 8, ask price 8,
     ask size 4                                          = 42 bytes
  T: type 1, sale-condition flags 1, timestamp 8, symbol 8, size 4, price 8, trade id 8 = 38 bytes
Prices are integers in 1/10,000 of a dollar. These are IEX's quotes only, not the national best: that is the
documented limit of this check.

INTEGRITY. Each IEX-TP segment declares its payload length and message count, and the parser asserts both on every
packet. The packet capture may be classic pcap or pcapng; both are parsed. Output per day goes to
`data/raw/iex/tops_filtered/<YYYY-MM-DD>.csv.gz` (a gitignored cache). The job record is
`data/ledger_iex_sample_pull.json`, with bytes streamed, packets, messages, kept rows per symbol and wall time.

    uv run python scripts/fetch_iex_tops_sample.py [--workers 5] [--date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import gzip
import io
import json
import struct
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, BinaryIO

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "data" / "raw" / "iex" / "tops_filtered"
RECORD = REPO / "data" / "ledger_iex_sample_pull.json"
LISTING = "https://iextrading.com/api/1.0/hist?date={d}"
DATES = ("2018-06-13", "2019-03-12", "2019-11-13", "2020-06-16", "2021-02-17", "2021-10-13",
         "2022-05-17", "2023-01-18", "2023-09-13", "2024-07-17")
SYMS = {s.ljust(8).encode(): s for s in ("BOIL", "KOLD", "UCO", "SCO", "UNG", "USO")}
UA = {"User-Agent": "Mozilla/5.0 (research; settlement-ledger quote check)"}


class IexError(RuntimeError):
    pass


def tops_url(day: str) -> tuple[str, int]:
    with urllib.request.urlopen(urllib.request.Request(LISTING.format(d=day.replace("-", "")), headers=UA),
                                timeout=60) as r:
        listing = json.loads(r.read().decode("utf-8"))
    rows = [x for x in listing if x.get("feed") == "TOPS" and x.get("protocol") == "IEXTP1"]
    if not rows:
        raise IexError(f"{day}: no TOPS file in the listing")
    x = sorted(rows, key=lambda y: str(y.get("version")))[-1]
    return str(x["link"]), int(x.get("size", 0))


def _read(f: BinaryIO, n: int) -> bytes:
    b = f.read(n)
    if len(b) < n:
        raise EOFError
    return b


def packets(f: BinaryIO):  # type: ignore[no-untyped-def]
    """Yield the raw link-layer frames of a classic pcap or a pcapng stream."""
    head = _read(f, 4)
    if head in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1"):  # classic pcap, little-endian
        _read(f, 20)
        while True:
            try:
                h = _read(f, 16)
            except EOFError:
                return
            incl = struct.unpack_from("<I", h, 8)[0]
            yield _read(f, incl)
    elif head == b"\x0a\x0d\x0d\x0a":  # pcapng: section header block first
        blen = struct.unpack("<I", _read(f, 4))[0]
        _read(f, blen - 8)
        while True:
            try:
                bh = _read(f, 8)
            except EOFError:
                return
            btype, blen = struct.unpack("<II", bh)
            body = _read(f, blen - 8)
            if btype == 6:  # enhanced packet block
                cap = struct.unpack_from("<I", body, 12)[0]
                yield body[20:20 + cap]
    else:
        raise IexError(f"unknown capture format {head!r}")


def udp_payload(frame: bytes) -> bytes | None:
    off = 12
    etype = struct.unpack_from(">H", frame, off)[0]
    while etype == 0x8100:  # VLAN tags
        off += 4
        etype = struct.unpack_from(">H", frame, off)[0]
    off += 2
    if etype != 0x0800:
        return None
    ihl = (frame[off] & 0x0F) * 4
    if frame[off + 9] != 17:  # not UDP
        return None
    return frame[off + ihl + 8:]


def process(day: str) -> dict[str, Any]:
    out = OUT_DIR / f"{day}.csv.gz"
    if out.exists():
        return {"day": day, "skipped": "already on disk"}
    url, size = tops_url(day)
    t0 = time.time()
    rows: list[str] = []
    n_pkt = n_msg = 0
    kept: dict[str, int] = {}
    counted = _Counter()
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as resp:
        src = _CountingReader(resp, counted)
        gz = gzip.GzipFile(fileobj=src)
        f = io.BufferedReader(gz, buffer_size=1 << 22)  # type: ignore[arg-type]
        for frame in packets(f):
            p = udp_payload(frame)
            if p is None or len(p) < 40:
                continue
            plen, mcount = struct.unpack_from("<HH", p, 12)
            if len(p) != 40 + plen:
                raise IexError(f"{day}: packet {n_pkt} payload {len(p) - 40} != declared {plen}")
            n_pkt += 1
            i, seen = 40, 0
            while i < len(p):
                mlen = struct.unpack_from("<H", p, i)[0]
                m = p[i + 2: i + 2 + mlen]
                i += 2 + mlen
                seen += 1
                t = m[0:1]
                if t in (b"Q", b"T") and m[10:18] in SYMS:
                    sym = SYMS[m[10:18]]
                    ts = struct.unpack_from("<q", m, 2)[0]
                    if t == b"Q":
                        bs, bp, ap, asz = struct.unpack_from("<IqqI", m, 18)
                        rows.append(f"{ts},{sym},Q,{m[1]},{bs},{bp},{ap},{asz}")
                    else:
                        sz, px = struct.unpack_from("<Iq", m, 18)
                        rows.append(f"{ts},{sym},T,{m[1]},{sz},{px},,")
                    kept[sym] = kept.get(sym, 0) + 1
            if seen != mcount:
                raise IexError(f"{day}: packet {n_pkt} parsed {seen} messages, declared {mcount}")
            n_msg += seen
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    body = "ts_ns,symbol,type,flags,a,b,c,d\n" + "\n".join(rows) + ("\n" if rows else "")
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as z:
        z.write(body.encode("utf-8"))
    out.write_bytes(buf.getvalue())
    return {"day": day, "url": url, "listed_bytes": size, "streamed_bytes": counted.n, "packets": n_pkt,
            "messages": n_msg, "kept_rows": kept, "columns": "Q: flags,bid_size,bid_px_e4,ask_px_e4,ask_size; "
            "T: flags,size,px_e4", "wall_s": round(time.time() - t0, 1)}


class _Counter:
    def __init__(self) -> None:
        self.n = 0


class _CountingReader(io.RawIOBase):
    def __init__(self, raw: Any, counter: _Counter) -> None:
        self.raw, self.counter = raw, counter

    def readable(self) -> bool:
        return True

    def readinto(self, b: Any) -> int:
        data = self.raw.read(len(b))
        n = len(data)
        b[:n] = data
        self.counter.n += n
        return n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--date", default=None)
    a = ap.parse_args(argv)
    days = [a.date] if a.date else list(DATES)
    rec: dict[str, Any] = json.loads(RECORD.read_text(encoding="utf-8")) if RECORD.exists() else {
        "approved": "principal, 2026-09-25: 'Go for the IEX download'",
        "terms": "https://www.iex.io/legal/hist-data-terms", "days": {}}
    with cf.ProcessPoolExecutor(max_workers=min(a.workers, len(days))) as ex:
        for res in ex.map(process, days):
            if "skipped" not in res:
                rec["days"][res["day"]] = res
            print(json.dumps(res), flush=True)
            RECORD.write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
