"""Drive the local Sierra Chart GUI through the Win32 API (ctypes only; no extra packages).

Sierra Chart serves CME data to no external API (its DTC server excludes CME), and its UDP port only opens or
activates charts. This module fills the gaps from the outside, on the principal's own machine at their request
(2026-09-26):
  * list    -- every window of the Sierra Chart process: top-level windows, dialogs and MDI chart windows;
  * close   -- close MDI chart windows whose title matches a pattern (WM_CLOSE);
  * dialogs -- list open dialog boxes with their text and buttons;
  * press   -- press a named button in an open dialog;
  * menu    -- list the main menu tree with command IDs; `command ID` sends one.
It never touches order entry: `press` and `command` refuse any caption or menu text mentioning buy, sell, order,
trade, position, flatten or account.

    python scripts/sierra_ui.py list | close PATTERN | dialogs | press "Button text" | menu | command ID
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import re
import sys

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
WM_CLOSE, WM_COMMAND, BM_CLICK = 0x0010, 0x0111, 0x00F5
FORBIDDEN = re.compile(r"buy|sell|order|trade|position|flatten|account", re.I)
PROCESS_NAMES = ("sierrachart_64.exe", "sierrachart.exe", "sierrachart_arm64.exe")


def _text(h: int) -> str:
    n = user32.GetWindowTextLengthW(h)
    b = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(h, b, n + 1)
    return b.value


def _class(h: int) -> str:
    b = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(h, b, 256)
    return b.value


def _pid(h: int) -> int:
    p = wt.DWORD()
    user32.GetWindowThreadProcessId(h, ctypes.byref(p))
    return p.value


def _proc_name(pid: int) -> str:
    h = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return ""
    b = ctypes.create_unicode_buffer(1024)
    n = wt.DWORD(1024)
    kernel32.QueryFullProcessImageNameW(h, 0, b, ctypes.byref(n))
    kernel32.CloseHandle(h)
    return b.value.rsplit("\\", 1)[-1].lower()


def sierra_top() -> list[int]:
    out: list[int] = []

    def cb(h: int, _l: int) -> bool:
        if user32.IsWindowVisible(h) and _proc_name(_pid(h)) in PROCESS_NAMES:
            out.append(h)
        return True
    user32.EnumWindows(WNDENUMPROC(cb), 0)
    return out


def children(h: int) -> list[int]:
    out: list[int] = []

    def cb(c: int, _l: int) -> bool:
        out.append(c)
        return True
    user32.EnumChildWindows(h, WNDENUMPROC(cb), 0)
    return out


def mdi_charts() -> list[tuple[int, str]]:
    """Sierra Chart's chart windows: class SCDW_MDIChild, anywhere under its top-level windows."""
    res = []
    for top in sierra_top():
        for c in children(top):
            if _class(c) == "SCDW_MDIChild":
                res.append((c, _text(c)))
    return res


def dialogs() -> list[tuple[int, str, list[tuple[int, str]]]]:
    res = []
    for top in sierra_top():
        if _class(top) == "#32770":  # the standard dialog class
            items = [(c, _text(c)) for c in children(top) if _text(c)]
            res.append((top, _text(top), items))
    return res


def cmd_list() -> None:
    for top in sierra_top():
        print(f"TOP {top:#x} class={_class(top)!r} title={_text(top)!r}")
    for h, t in mdi_charts():
        print(f"  CHART {h:#x} {t!r}")
    for h, t, items in dialogs():
        print(f"  DIALOG {h:#x} {t!r}: " + " | ".join(x for _c, x in items)[:400])


REMOVE_PROMPT = re.compile(r"^Remove chart window for ")


def click(dlg: int, btn: int) -> None:
    """Send the dialog the button's command (WM_COMMAND with its control ID, BN_CLICKED = 0). BM_CLICK is
    unreliable from another process when the dialog is not the active window."""
    cid = user32.GetDlgCtrlID(btn)
    user32.PostMessageW(dlg, WM_COMMAND, cid & 0xFFFF, btn)


def confirm_remove(timeout_s: float = 10.0) -> bool:
    """Press Yes on Sierra Chart's 'Remove chart window for ...?' prompt, and on nothing else."""
    import time
    end = time.time() + timeout_s
    while time.time() < end:
        hit = False
        for h, _t, items in dialogs():
            if any(REMOVE_PROMPT.match(x) for _c, x in items):
                for c, x in items:
                    if _class(c) == "Button" and x.replace("&", "") == "Yes":
                        click(h, c)
                        hit = True
        if hit:
            return True
        time.sleep(0.1)
    return False


def cmd_close(pattern: str) -> None:
    """Post WM_CLOSE (never Send: the removal prompt is modal and would block) and confirm its prompt."""
    import time
    rx = re.compile(pattern, re.I)
    n = 0
    for h, t in mdi_charts():
        if rx.search(t):
            user32.PostMessageW(h, WM_CLOSE, 0, 0)
            ok = confirm_remove()
            deadline = time.time() + 5
            while user32.IsWindow(h) and time.time() < deadline:
                time.sleep(0.1)
            print(f"{'closed' if not user32.IsWindow(h) else 'STILL OPEN'} {t!r} (prompt confirmed: {ok})")
            n += 0 if user32.IsWindow(h) else 1
    print(f"{n} chart(s) closed")


def cmd_press(label: str) -> None:
    if FORBIDDEN.search(label):
        raise SystemExit(f"refused: {label!r} looks trade-related")
    for h, t, items in dialogs():
        if FORBIDDEN.search(t):
            print(f"skipping dialog {t!r}: trade-related")
            continue
        for c, x in items:
            if _class(c) == "Button" and x.replace("&", "").strip().lower() == label.lower():
                click(h, c)
                print(f"pressed {x!r} in {t!r}")
                return
    print(f"no button {label!r} found")


def _menu_walk(m: int, depth: int, path: str) -> None:
    for i in range(user32.GetMenuItemCount(m)):
        b = ctypes.create_unicode_buffer(256)
        user32.GetMenuStringW(m, i, b, 256, 0x400)  # MF_BYPOSITION
        sub = user32.GetSubMenu(m, i)
        name = b.value.replace("&", "")
        if sub:
            _menu_walk(sub, depth + 1, f"{path}{name} > ")
        elif name:
            print(f"{user32.GetMenuItemID(m, i):6d}  {path}{name}")


def cmd_menu() -> None:
    for top in sierra_top():
        m = user32.GetMenu(top)
        if m:
            _menu_walk(m, 0, "")


def main_window() -> int:
    for top in sierra_top():
        if _class(top) == "SierraChartWindowClass" and _text(top).startswith("Sierra Chart "):
            return top
    raise SystemExit("Sierra Chart's main window was not found")


def menu_text(cid: int) -> str:
    b = ctypes.create_unicode_buffer(256)
    user32.GetMenuStringW(user32.GetMenu(main_window()), cid, b, 256, 0)  # MF_BYCOMMAND
    return b.value.replace("&", "")


def cmd_command(cid: int) -> None:
    top = main_window()
    name = menu_text(cid)
    if FORBIDDEN.search(name):
        raise SystemExit(f"refused: menu command {cid} {name!r} looks trade-related")
    user32.PostMessageW(top, WM_COMMAND, cid, 0)
    print(f"sent WM_COMMAND {cid} ({name!r}) to the main window")


def read_log() -> str:
    """The Message Log's text, through its own Edit > Copy Log (51004) and the clipboard (overwrites it)."""
    import subprocess
    import time
    ml = [h for h in sierra_top() if _text(h) == "Message Log"]
    if not ml:
        raise SystemExit("the Message Log window is not open (Window > Message Log)")
    user32.PostMessageW(ml[0], WM_COMMAND, 51004, 0)
    time.sleep(1.0)
    out = subprocess.run(["powershell.exe", "-NoProfile", "-Command", "Get-Clipboard"], capture_output=True,
                         text=True, encoding="utf-8", errors="replace")
    return out.stdout


def main(argv: list[str]) -> int:
    if argv and argv[0] == "log":
        pat = re.compile(argv[1], re.I) if len(argv) > 1 else None
        lines = read_log().splitlines()
        n = int(argv[2]) if len(argv) > 2 else 40
        print("\n".join([ln for ln in lines if pat is None or pat.search(ln)][-n:]))
        return 0
    if not argv or argv[0] == "list":
        cmd_list()
    elif argv[0] == "close":
        cmd_close(argv[1])
    elif argv[0] == "dialogs":
        for h, t, items in dialogs():
            print(f"{h:#x} {t!r}: {[x for _c, x in items]}")
    elif argv[0] == "press":
        cmd_press(argv[1])
    elif argv[0] == "menu":
        cmd_menu()
    elif argv[0] == "command":
        cmd_command(int(argv[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
