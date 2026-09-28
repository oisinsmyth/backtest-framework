"""Sierra Chart 'Edit > Delete All Data And Download' for named market-statistics symbols, one at a time, with the target
chart made active and VERIFIED before the command is sent (the command acts on whichever chart is active, and other
work's charts may be open). On the principal's word (2026-09-28), after they raised 'Maximum Historical Intraday Days
to Download' to 4700: it replaces Sierra's local six-month file with the full history from about 2014.

    python scripts/sierra_redownload_stats.py TICK-NYSE UVOL-NYSE DVOL-NYSE

Refuses any symbol that is not a market-statistics symbol (TICK/UVOL/DVOL/ADV/DECL/TRIN -NYSE/-NASDAQ/-SP/-NQ).
The confirmation prompt is accepted only if its text names the symbol; any other prompt is cancelled.
"""
from __future__ import annotations

import ctypes
import re
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sierra_ui as U  # noqa: E402

UDP = ("127.0.0.1", 22903)
CMD = 57074  # Edit > Delete All Data And Download
ALLOWED = re.compile(r"^(TICK|UVOL|DVOL|ADV|DECL|TRIN)-(NYSE|NASDAQ|SP|NQ)$")
WM_MDIACTIVATE, WM_MDIGETACTIVE = 0x0222, 0x0229
user32 = U.user32
user32.SendMessageW.restype = ctypes.c_ssize_t


def chart_of(sym: str) -> int | None:
    for h, t in U.mdi_charts():
        if t.startswith(f"{sym}["):
            return h
    return None


def active_is(sym: str) -> bool:
    """Sierra Chart is not a standard MDI application: its main window title carries the ACTIVE chart in brackets,
    e.g. 'Sierra Chart 2957 ... [TICK-NYSE[M]  1 Min  #16 | NYSE TICK]'."""
    t = U._text(U.main_window())
    return f"[{sym}[" in t


def activate(sym: str, s: socket.socket, timeout_s: float = 8.0) -> bool:
    """The UDP port opens OR activates a chart; wait until the main title names it."""
    s.sendto(f"{sym}.scid".encode(), UDP)
    end = time.time() + timeout_s
    while time.time() < end:
        if active_is(sym):
            return True
        time.sleep(0.2)
    return False


def handle_prompt(sym: str, timeout_s: float = 10.0) -> str:
    end = time.time() + timeout_s
    while time.time() < end:
        for h, title, items in U.dialogs():
            text = " | ".join(x for _c, x in items)
            if U.FORBIDDEN.search(title) or U.FORBIDDEN.search(text):
                continue
            names = {x.replace("&", "").strip().lower(): c for c, x in items if U._class(c) == "Button"}
            # the prompt Sierra actually shows (2026-09-28): "Confirm Intraday data download for SYM starting at ..."
            if re.search(rf"(delete.*{re.escape(sym)}|Confirm Intraday data download for {re.escape(sym)} )", text, re.I):
                for ok in ("yes", "ok"):
                    if ok in names:
                        U.click(h, names[ok])
                        return f"accepted: {text[:200]}"
            for no in ("no", "cancel"):
                if no in names:
                    U.click(h, names[no])
                    return f"CANCELLED an unexpected prompt: {text[:200]}"
        time.sleep(0.1)
    return "no prompt seen"


def main(argv: list[str]) -> int:
    if U.menu_text(CMD) != "Delete All Data And Download":
        raise SystemExit(f"menu {CMD} is {U.menu_text(CMD)!r}, not 'Delete All Data And Download'")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for sym in argv:
        if not ALLOWED.match(sym):
            raise SystemExit(f"refused: {sym} is not a market-statistics symbol")
        s.sendto(f"{sym}.scid".encode(), UDP)
        h, end = None, time.time() + 15
        while h is None and time.time() < end:
            time.sleep(0.2)
            h = chart_of(sym)
        if h is None:
            print(f"{sym}: chart did not open; skipped")
            continue
        if not activate(sym, s):
            print(f"{sym}: could not verify the active chart (main title: {U._text(U.main_window())[-90:]!r}); skipped")
            continue
        if not active_is(sym):  # re-verify immediately before the command
            print(f"{sym}: the active chart changed; skipped")
            continue
        user32.PostMessageW(U.main_window(), U.WM_COMMAND, CMD, 0)
        print(f"{sym}: sent 'Delete All Data And Download' to the verified active chart {U._text(h)!r}")
        print(f"{sym}: {handle_prompt(sym)}")
        time.sleep(2)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
