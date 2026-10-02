"""D776: D775's CPI and jobs-report fade on MNQ for the joint vault run. Spec:
docs/decisions/D776-PRE-REG-the-cpi-and-jobs-report-fade-for-the-joint-vault.md, committed before this file existed.

    uv run --no-sync python scripts/vault_d776_cpi_nfp_fade.py --selftest        # synthetic only
    uv run --no-sync python scripts/vault_d776_cpi_nfp_fade.py --rehearse        # in-sample (2016-2023), once
    uv run --no-sync python scripts/vault_d776_cpi_nfp_fade.py --power           # in-sample, once
    uv run --no-sync python scripts/vault_d776_cpi_nfp_fade.py --freeze          # once, after both
    uv run --no-sync python scripts/vault_d776_cpi_nfp_fade.py --vault --principals-word "..." [--accept-end D]
                                                                                 # the joint run ONLY, after slot 9's
                                                                                 # --build-vault fixture

The construction is D775's own functions, imported (stage0_d775_cpi_nfp_fade: sessions, classify, rotation,
release_days, trade_stats, book, _load_file, BARS, ROOTS). In every mode but --vault the bars come through D775's
loader, which keeps sessions before 2024-01-01 and raises on a later one. --vault reads the joint run's vault opening
fixture (data/joint_run/d680/fut_opening_globex_1m.csv.gz, D644's builder through 2026-09-18) and nothing after
2026-09-18.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d775_cpi_nfp_fade as S  # noqa: E402

RUNNER_REL = "scripts/vault_d776_cpi_nfp_fade.py"
SPEC_REL = "docs/decisions/D776-PRE-REG-the-cpi-and-jobs-report-fade-for-the-joint-vault.md"
D775_PRE_REL = "docs/decisions/D775-STAGE-0-PRE-REG-fade-the-cpi-and-jobs-report-impulse-on-mnq.md"
D775_RES_REL = "docs/decisions/D775-STAGE-0-RESULT-the-cpi-and-jobs-report-fade-passes-in-sample-on-mnq.md"
D775_JSON = REPO / "data" / "stage0_d775_cpi_nfp_fade.json"
REHEARSAL = REPO / "data" / "rehearsal_vault_d776.json"
POWER = REPO / "data" / "vault_d776_power.json"
FROZEN = REPO / "data" / "FROZEN_vault_d776_cpi_nfp_fade.json"
OUT = REPO / "data" / "vault_d776_cpi_nfp_fade.json"
JOINT_FIX = S.MAIN / "data" / "joint_run" / "d680" / "fut_opening_globex_1m.csv.gz"

ROOT = "NQ"
FIX_NAME, MULT, COST = S.ROOTS[ROOT]
IN_LO, IN_HI = "2016-01-01", "2023-12-31"
VAULT_FROM, VAULT_END = "2024-01-01", "2026-09-18"
KNOWN_TRADES, KNOWN_MEAN_2DP = 186, 34.88
MIN_TRADES, T_GATE = 40, 1.2816
POWER_N, POWER_DRAWS, POWER_FRACS, WIN_STEP = 64, 4000, (1.0, 0.75, 0.5, 0.25, 0.0), 8
SEED = 776
PROGRAMME_FAMILY = "CPI/jobs-report fade (NQ, D775)"
REGISTERED = "2026-10-02"
PAGE_DATE = "2026-09-21"                                     # the page's pinned render date
INSTRUCTION = 'the principal, 2026-10-02: "Put D775 in the next slot and freeze it"'
NOTE = ("Vault line: D775's fade of the 08:30 CPI/jobs-report impulse (08:29 -> 08:34 bar closes) to the 11:00 close, "
        "one MNQ, $4.07, release days 2024-01-01 -> 2026-09-18; PASS with >= 40 trades, mean net > 0 and one-sided t "
        ">= 1.2816, and mean gross above the vault-window exact rotation p95; FAIL if mean net <= 0; else UNRESOLVED")
REFUSED = 2


class VaultError(RuntimeError):
    pass


def P(*a: Any) -> None:
    print(*a, flush=True)


# ================================================================================ loading and the trades
def release_window(lo: str, hi: str) -> dict[str, str]:
    e = pd.read_csv(S.EVENTS, encoding="utf-8")
    e = e[e["event"].isin(["CPI", "EMPSIT"]) & (e["datetime_et"].str[11:16] == "08:30")]
    d = e["datetime_et"].str[:10]
    e = e[(d >= lo) & (d <= hi)]
    return dict(zip(e["datetime_et"].str[:10], e["event"]))


def in_sample_bars() -> pd.DataFrame:
    b = S._load_file((FIX_NAME, (ROOT,)))                    # D775's loader: sessions < 2024-01-01, asserted
    if (b["session"] > IN_HI).any():
        raise VaultError("seal: an in-sample load holds a session after 2023-12-31")
    return b


def read_vault(path: Path, lo: str, hi: str) -> pd.DataFrame:
    parts = []
    for ch in pd.read_csv(path, encoding="utf-8", chunksize=2_000_000,
                          usecols=["root", "session", "et", "hhmm", "contract", "close"]):
        ch = ch[(ch["root"] == ROOT) & (ch["session"] >= lo) & (ch["session"] <= hi) & ch["hhmm"].isin(S.BARS)]
        parts.append(ch[ch["et"].str[:10] == ch["session"]])
    b = pd.concat(parts, ignore_index=True)
    return window_rows(b, hi)


def window_rows(b: pd.DataFrame, hi: str) -> pd.DataFrame:
    if len(b) and b["session"].max() > hi:
        raise VaultError(f"seal: a row after {hi} survived the filter")
    return b


def trades(b: pd.DataFrame, rel: dict[str, str]) -> tuple[pd.DataFrame, dict[str, int]]:
    return S.classify(S.sessions(b, ROOT), rel)


def known(U: pd.DataFrame, hi: str = IN_HI) -> dict[str, Any]:
    R = U[U["is_rel"] & (U.index <= hi)]
    return {"trades": int(len(R)), "mean_gross": float(R["gross"].mean())}


def check_known(got: dict[str, Any], ref: dict[str, Any]) -> None:
    if got["trades"] != ref["trades"] or not math.isclose(got["mean_gross"], ref["mean_gross"], rel_tol=0, abs_tol=1e-9):
        raise VaultError(f"the in-sample known answer is not reproduced: {got} against {ref}")


# ================================================================================ the gate
def gate(n: int, mean_net: float, t: float, mean_gross: float, p95: float) -> dict[str, Any]:
    g0, g1, g2 = n >= MIN_TRADES, (mean_net > 0 and t >= T_GATE), mean_gross > p95
    verdict = "PASS" if (g0 and g1 and g2) else "FAIL" if mean_net <= 0 else "UNRESOLVED"
    return {"G0": bool(g0), "G1": bool(g1), "G2": bool(g2), "verdict": verdict}


def score(U: pd.DataFrame, lo: str, hi: str, workers: int = 4, full: bool = True) -> dict[str, Any]:
    W = U[(U.index >= lo) & (U.index <= hi)].copy()
    R = W[W["is_rel"]]
    n = len(R)
    if n < 3:
        return {"trades": n, "gate": gate(n, float("nan"), float("nan"), float("nan"), float("nan"))}
    net = R["gross"] - COST
    t = float(net.mean() / net.std(ddof=1) * math.sqrt(n))
    rot = S.rotation(W["gross"].to_numpy(), np.flatnonzero(W["is_rel"].to_numpy()), workers=workers)
    if abs(rot[0] - R["gross"].mean()) > 1e-9:
        raise VaultError("right quantity: rotation offset 0 must equal the observed")
    p95 = float(np.percentile(rot[1:], 95))
    out: dict[str, Any] = {"window": [lo, hi], "trades": n, "mean_gross": float(R["gross"].mean()),
                           "mean_net": float(net.mean()), "t_net": t, "rotation_p50": float(np.percentile(rot[1:], 50)),
                           "rotation_p95": p95, "rotation_rank": float((rot[1:] < rot[0]).mean()),
                           "gate": gate(n, float(net.mean()), t, float(R["gross"].mean()), p95)}
    if full:
        out["stats"] = S.trade_stats(R["gross"], COST)
        bk = S.book(W, COST)
        bk.pop("daily_net")
        out["book"] = bk
        sec = R["sec"].dropna()
        out["leg_0930_1101"] = {"mean": round(sec.mean(), 2), "t": round(float(sec.mean() / sec.std(ddof=1) * math.sqrt(len(sec))), 2),
                                "n": int(len(sec))} if len(sec) > 2 else None
        out["by_sign"] = {k: round(float(g["gross"].mean()), 2) for k, g in R.groupby(np.where(R["x"] > 0, "up", "down"))}
        out["by_event"] = {k: round(float(g["gross"].mean()), 2) for k, g in R.groupby("event")}
        out["by_year"] = {k: [int(len(g)), round(float(g["gross"].mean()), 2)] for k, g in R.groupby("year")}
        out["va_mean"] = round(float(R["va"].mean()), 3)
    return out


# ================================================================================ power
def power(U: pd.DataFrame) -> dict[str, Any]:
    R = U[U["is_rel"]]
    rng = np.random.default_rng(SEED)
    out: dict[str, Any] = {"n_vault": POWER_N, "draws": POWER_DRAWS, "g1": {}}
    for base, sel in (("all", R["year"] != ""), ("2016-19", R["year"] <= "2019"), ("2020-23", R["year"] >= "2020")):
        g = R.loc[sel, "gross"].to_numpy()
        mu = g.mean()
        row = {}
        for f in POWER_FRACS:
            gg = g - (1 - f) * mu
            hits = 0
            for _ in range(POWER_DRAWS):
                x = rng.choice(gg, POWER_N, replace=True) - COST
                sd = x.std(ddof=1)
                hits += int(x.mean() > 0 and sd > 0 and x.mean() / sd * math.sqrt(POWER_N) >= T_GATE)
            row[f"{int(f * 100)}%"] = round(hits / POWER_DRAWS, 3)
        out["g1"][base] = {"mean_gross": round(float(mu), 2), "pass_g1": row}
    days = list(R.index)
    wins = []
    for i in range(0, len(days) - POWER_N + 1, WIN_STEP):
        lo, hi = days[i], days[i + POWER_N - 1]
        s = score(U, lo, hi, workers=1, full=False)
        wins.append({"from": lo, "to": hi, "trades": s["trades"], "mean_net": round(s["mean_net"], 2),
                     "t_net": round(s["t_net"], 2), "rotation_p95": round(s["rotation_p95"], 2), **s["gate"]})
    out["full_gate_windows"] = wins
    out["full_gate_summary"] = {v: sum(w["verdict"] == v for w in wins) for v in ("PASS", "UNRESOLVED", "FAIL")}
    out["independent_windows"] = round(len(days) / POWER_N, 2)
    return out


# ================================================================================ freeze
_TOP = re.compile(r"^(?:import|from)[ \t]+([A-Za-z_]\w*)", re.M)
_BF = re.compile(r"^[ \t]*(?:from[ \t]+(backtest_framework[\w.]*)[ \t]+import|import[ \t]+(backtest_framework[\w.]*))", re.M)


def sha_text(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def discover(root: Path, starts: tuple[str, ...]) -> list[str]:
    """Repo modules imported at module level, recursively (static; never executed)."""
    seen: set[str] = set()
    stack = list(starts)
    while stack:
        rel = stack.pop()
        if rel in seen:
            continue
        seen.add(rel)
        text = (root / rel).read_text(encoding="utf-8")
        found = [f"scripts/{n}.py" for n in _TOP.findall(text)]
        for a, b in _BF.findall(text):
            parts = (a or b).split(".")
            for k in range(1, len(parts) + 1):
                base = root / "src" / Path(*parts[:k])
                for p in (base.with_suffix(".py"), base / "__init__.py"):
                    if p.exists():
                        found.append(p.relative_to(root).as_posix())
        stack += [f for f in found if (root / f).exists() and f not in seen]
    return sorted(seen - set(starts))


def params() -> dict[str, Any]:
    return {"root": ROOT, "fixture": FIX_NAME, "mult": MULT, "cost": COST, "bars": S.BARS,
            "in_sample": [IN_LO, IN_HI], "vault": [VAULT_FROM, VAULT_END], "joint_fixture": "data/joint_run/d680/" + FIX_NAME,
            "known_trades": KNOWN_TRADES,
            "gate": {"G0": f">= {MIN_TRADES} trades", "G1": f"mean net > 0 and one-sided t >= {T_GATE}",
                     "G2": "mean gross > the vault-window exact rotation p95", "FAIL": "mean net <= 0", "else": "UNRESOLVED"},
            "seed": SEED, "programme_family": PROGRAMME_FAMILY}


def manifest(root: Path) -> dict[str, Any]:
    imported = discover(root, (RUNNER_REL,))
    return {"runner": {"path": RUNNER_REL, "sha256": sha_text(root / RUNNER_REL)},
            "records": {p: sha_text(root / p) for p in (SPEC_REL, D775_PRE_REL, D775_RES_REL)},
            "imported_unchanged": {p: sha_text(root / p) for p in imported},
            "files": {p.relative_to(REPO).as_posix(): sha_text(root / p.relative_to(REPO))
                      for p in (D775_JSON, REHEARSAL, POWER)},
            "params": params()}


def check_freeze(doc: dict[str, Any], root: Path = REPO) -> None:
    now = manifest(root)
    bad = [k for k in ("runner", "records", "files", "params") if now[k] != doc.get(k)]
    fi, ni = doc.get("imported_unchanged", {}), now["imported_unchanged"]
    if set(fi) != set(ni):
        bad.append(f"the import set (added {sorted(set(ni) - set(fi))}, dropped {sorted(set(fi) - set(ni))})")
    bad += [f"imported {p}" for p in sorted(set(fi) & set(ni)) if fi[p] != ni[p]]
    if bad:
        raise VaultError(f"moved since the freeze: {bad}")


def write_once(path: Path, doc: dict[str, Any]) -> None:
    with open(path, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, default=str)
        fh.write("\n")


# ================================================================================ modes
def rehearse() -> int:
    if REHEARSAL.exists():
        raise VaultError(f"{REHEARSAL.name} exists: the rehearsal is run-once")
    t0 = time.time()
    b = in_sample_bars()
    U, counts = trades(b, S.release_days())
    ka = known(U)
    if ka["trades"] != KNOWN_TRADES or round(ka["mean_gross"], 2) != KNOWN_MEAN_2DP:
        raise VaultError(f"D775's answer is not reproduced: {ka}")
    d775 = json.loads(D775_JSON.read_text(encoding="utf-8"))["NQ"]["primary"]
    # the vault reader's path on the committed fixture's in-sample rows: the same trades, exactly
    bv = read_vault(S.FIX / FIX_NAME, IN_LO, IN_HI)
    Uv, _ = trades(bv, release_window(IN_LO, IN_HI))
    kv = known(Uv)
    check_known(kv, ka)
    res = score(U, IN_LO, IN_HI)
    doc = {"mode": "IN-SAMPLE REHEARSAL (2016-01-01 -> 2023-12-31): the vault scorer on the in-sample window",
           "spec": SPEC_REL, "known_answer": ka, "known_answer_d775_json_2dp": d775["mean_gross"], "counts": counts,
           "vault_reader_reproduces": kv, "score": res, "wall_s": round(time.time() - t0, 1)}
    write_once(REHEARSAL, doc)
    P(f"[D776] rehearsal: {ka}; vault reader {kv}; in-sample gate {res['gate']}; t {res['t_net']:.2f}; "
      f"rotation p95 {res['rotation_p95']:.2f}")
    return 0


def do_power() -> int:
    if POWER.exists():
        raise VaultError(f"{POWER.name} exists: the power run is run-once")
    t0 = time.time()
    U, _ = trades(in_sample_bars(), S.release_days())
    check_known(known(U), json.loads(REHEARSAL.read_text(encoding="utf-8"))["known_answer"])
    pw = power(U)
    pw["wall_s"] = round(time.time() - t0, 1)
    write_once(POWER, pw)
    P(f"[D776] power: {pw['g1']}; full-gate windows {pw['full_gate_summary']} (~{pw['independent_windows']} independent)")
    return 0


def freeze() -> int:
    if FROZEN.exists():
        raise VaultError(f"{FROZEN.name} exists: the freeze is written once")
    for p in (REHEARSAL, POWER):
        if not p.exists():
            raise VaultError(f"{p.name} is missing: run --rehearse and --power first")
    from backtest_framework.validation.programme import Registry
    reg = Registry()
    fam = reg.register(PROGRAMME_FAMILY, Path(SPEC_REL).name, registered_utc=REGISTERED, note=NOTE)
    reg.render_md(date=PAGE_DATE)
    ka = json.loads(REHEARSAL.read_text(encoding="utf-8"))["known_answer"]
    doc = {"name": "FROZEN_vault_d776_cpi_nfp_fade", "record": SPEC_REL, "instruction": INSTRUCTION,
           "programme_slot": fam.slot, "programme_family": fam.name, "alpha": fam.alpha, **manifest(REPO),
           "known_answer": ka}
    write_once(FROZEN, doc)
    P(f"[D776] FROZEN; programme slot {fam.slot} ({fam.name}); {len(doc['imported_unchanged'])} imported files hashed")
    return 0


def refuse(word: str | None) -> bool:
    return not (word and word.strip())


def vault(word: str | None, accept_end: str | None, fixture: Path = JOINT_FIX) -> int:
    if refuse(word):
        P("[D776] REFUSED: --vault needs --principals-word")
        return REFUSED
    if not FROZEN.exists():
        raise VaultError("no freeze: --vault runs only on a frozen line")
    doc = json.loads(FROZEN.read_text(encoding="utf-8"))
    check_freeze(doc)
    if OUT.exists():
        raise VaultError(f"{OUT.name} exists: the vault is opened once")
    if not fixture.exists():
        raise VaultError(f"{fixture} is missing: run slot 9's --build-vault fixture first")
    t0 = time.time()
    end = accept_end or VAULT_END
    if end > VAULT_END:
        raise VaultError(f"seal: the vault load may not pass {VAULT_END}")
    ref = doc["known_answer"]
    check_known(known(trades(in_sample_bars(), S.release_days())[0]), ref)       # the committed in-sample path
    bv = read_vault(fixture, IN_LO, end)
    last = bv["session"].max()
    if last < end:
        raise VaultError(f"the vault fixture ends {last}, before {end}: pass --accept-end (the principal's call)")
    Uv, counts = trades(bv, release_window(IN_LO, end))
    check_known(known(Uv), ref)                                                     # the vault file's own 2016-2023 rows
    res = score(Uv, VAULT_FROM, end)
    out = {"mode": "VAULT", "spec": SPEC_REL, "principals_word": word, "accept_end": accept_end, "end": end,
           "known_answer_reproduced_on_both_inputs": ref, "counts_2016_to_end": counts, "score": res,
           "verdict": res["gate"]["verdict"], "wall_s": round(time.time() - t0, 1)}
    write_once(OUT, out)
    P(f"[D776] VAULT: {res['gate']}; trades {res['trades']}; mean net {res['mean_net']:.2f}; t {res['t_net']:.2f}")
    return 0


# ================================================================================ self-test (synthetic only)
def _synthetic(days: list[str], rel: dict[str, str], effect: float, rng: np.random.Generator) -> pd.DataFrame:
    """Random-walk bars; on release days the 08:34 -> 11:00 move is -effect x the impulse (effect > 0 reverts)."""
    rows = []
    for d in days:
        p = 15000.0 + rng.normal(0, 5)
        closes = {}
        for h in S.BARS:
            p += rng.normal(0, 4)
            closes[h] = p
        if d in rel:
            x = closes[S.ENTRY] - closes[S.PRE]
            closes[S.EXIT] = closes[S.ENTRY] - effect * x + rng.normal(0, 2)
        for h in S.BARS:
            rows.append({"root": ROOT, "session": d, "et": f"{d} {h}", "hhmm": h, "contract": "NQZ5",
                         "close": round(closes[h], 2)})
    return pd.DataFrame(rows)


def selftest() -> int:
    fails: list[str] = []

    def expect(fn: Callable[[], Any], what: str, exc: type = VaultError) -> None:
        try:
            fn()
        except exc:
            return
        fails.append(f"did not raise: {what}")

    # 1) the gate's three readings
    if gate(64, 10.0, 2.0, 14.0, 9.0)["verdict"] != "PASS":
        fails.append("gate: a clear pass")
    if gate(64, -1.0, -0.5, 3.0, 9.0)["verdict"] != "FAIL":
        fails.append("gate: a loss must FAIL")
    if gate(64, 2.0, 0.6, 6.0, 9.0)["verdict"] != "UNRESOLVED":
        fails.append("gate: a weak gain is UNRESOLVED")
    if gate(30, 10.0, 2.0, 14.0, 9.0)["verdict"] != "UNRESOLVED":
        fails.append("gate: too few trades is UNRESOLVED")
    # 2) the window filter refuses a row past the end
    late = pd.DataFrame({"session": ["2026-09-17", "2026-09-21"]})
    expect(lambda: window_rows(late, VAULT_END), "a row after the vault end")
    # 3) --vault is refused without a word
    if vault(None, None) != REFUSED or vault("  ", None) != REFUSED:
        fails.append("--vault ran without the principal's word")
    # 4) a planted reversal passes, a planted continuation fails
    rng = np.random.default_rng(SEED)
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2024-01-02", "2026-09-18")]
    rel = {d: "CPI" for d in days[::11]}
    for eff, want in ((0.8, "PASS"), (-0.8, "FAIL")):
        U, _ = trades(_synthetic(days, rel, eff, rng), rel)
        got = score(U, VAULT_FROM, VAULT_END, workers=1, full=False)["gate"]["verdict"]
        if got != want:
            fails.append(f"planted effect {eff}: {got}, expected {want}")
    # 5) the vault reader filters by root, window and clock, and a file ending early is caught by vault()'s check
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "fx.csv.gz"
        syn = _synthetic(days[:40], {}, 0.0, rng)
        syn = pd.concat([syn, syn.assign(root="ES")], ignore_index=True)
        syn.to_csv(f, index=False, compression="gzip", encoding="utf-8")
        got = read_vault(f, days[5], days[30])
        if set(got["root"]) != {ROOT} or got["session"].min() < days[5] or got["session"].max() > days[30]:
            fails.append("read_vault: root or window filter")
    # 6) the freeze detects drift (once the rehearsal and power files exist)
    if REHEARSAL.exists() and POWER.exists():
        doc = manifest(REPO)
        check_freeze(doc)
        doc2 = json.loads(json.dumps(doc))
        doc2["params"]["cost"] = 9.99
        expect(lambda: check_freeze(doc2), "a moved parameter")
        doc3 = json.loads(json.dumps(doc))
        k = next(iter(doc3["imported_unchanged"]))
        doc3["imported_unchanged"][k] = "0" * 64
        expect(lambda: check_freeze(doc3), "a moved imported file")
    if fails:
        raise VaultError("; ".join(fails))
    P("[D776] selftest OK: the gate's readings, the window seal, the refusal without a word, a planted reversal "
      "passes and a continuation fails, the reader's filters"
      + ("; the freeze check fires on a moved parameter and a moved import" if REHEARSAL.exists() and POWER.exists()
         else " (the freeze-drift check runs once the rehearsal and power files exist)"))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for m in ("selftest", "rehearse", "power", "freeze", "vault"):
        g.add_argument(f"--{m}", action="store_true")
    ap.add_argument("--principals-word")
    ap.add_argument("--accept-end")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.rehearse:
        return rehearse()
    if a.power:
        return do_power()
    if a.freeze:
        return freeze()
    return vault(a.principals_word, a.accept_end)


if __name__ == "__main__":
    sys.exit(main())
