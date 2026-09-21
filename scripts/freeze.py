"""D594 -- freeze a model, and verify that nothing has moved since.

    uv run python scripts/freeze.py --selftest
    uv run python scripts/freeze.py --name stageA --params p.json \
        --code scripts/run_x.py src/backtest_framework/validation/frozen.py \
        --fixtures data/fixtures/f.csv.gz --evaluation-days 200 \
        --spec 7085aac --instruction "the principal, 2026-09-21: '...'" --out results/
    uv run python scripts/freeze.py --verify results/FROZEN_stageA.json \
        --params p.json --code scripts/run_x.py ... --fixtures data/fixtures/f.csv.gz

The library is `backtest_framework.validation.frozen` (D594); this file is only its
command line, so that freezing a model does not require writing a runner first.

WHAT THIS DOES NOT DO. It chooses no seal date and reads no fixture except to hash
its bytes. The deposit documents seal 2025-03-01 -> 2026-09-18; this repository
reserves 2024-01-01 onward (`RESERVED_FROM`, `run_d555:43`); reconciling the two is
the principal's open decision, and nothing here has a default that could pre-empt
it. `--selftest` runs entirely on synthetic files in a temporary directory.

EXIT CODES. 0 success, 1 a raise the caller should read. 2 is `refuse_without_word`'s
refusal -- the D574 shape, a return code from the REAL entry point, so the self-test
can call the real function and assert the 2 rather than read the source. (argparse's
own usage error also exits 2; it prints a usage block, so the two are told apart by
what is on stderr.)
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.validation.frozen import (  # noqa: E402
    AlreadyOpenedError,
    FrozenDriftError,
    FrozenError,
    FrozenExistsError,
    SealedWindow,
    VaultGuardError,
    assert_evaluation_length,
    assert_frozen,
    freeze,
    load_frozen,
    open_once,
    refuse_without_word,
)

SPEC = "89feba9"  # the commit this file was written against, as a constant (run_d555:37)


def expect_raise(fn, what, exc=AssertionError, log=print) -> bool:
    """`scripts/stage0_d581_gamma_close.py:39`, widened to take the exception class.

    A self-test that cannot fail is worse than none, so every guard below is proved
    to RAISE on a deliberately broken input, and the break hits the scalar the guard
    actually compares.
    """
    try:
        fn()
    except exc as e:
        log(f"    RAISES on {what}: {type(e).__name__}: {str(e)[:96]}")
        return True
    raise AssertionError(f"the guard did not raise on {what}")


# --------------------------------------------------------------------------------------------
# the command line
# --------------------------------------------------------------------------------------------
def _read_params(path: str | None) -> dict:
    if path is None:
        return {}
    p = Path(path)
    if not p.is_file():
        raise FrozenError(f"--params file not found: {p}")
    with open(p, encoding="utf-8") as fh:
        obj = json.load(fh)
    if not isinstance(obj, dict):
        raise FrozenError(f"--params {p} must hold a JSON object, got {type(obj).__name__}")
    return obj


def do_freeze(args, log=print) -> int:
    rec = freeze(
        args.out,
        name=args.name,
        params=_read_params(args.params),
        code_paths=args.code,
        fixture_paths=args.fixtures,
        evaluation_days=args.evaluation_days,
        spec_commit=args.spec,
        instruction=args.instruction,
        live_git=args.live_git,
    )
    log(f"FROZE {rec.name}  ->  {rec.path}")
    log(f"  frozen_utc       {rec.frozen_utc}")
    log(f"  content_sha256   {rec.content_sha256}")
    log(f"  params_sha256    {rec.params_sha256}   {len(rec.params)} key(s)")
    log(f"  evaluation_days  {rec.evaluation_days}")
    for d in rec.code:
        log(f"  code     {d.sha256}  {d.name}    (text, LF-pinned)")
    for d in rec.fixtures:
        log(f"  fixture  {d.sha256}  {d.name}    (bytes on disk)")
    if rec.git_head:
        log(f"  git_head         {rec.git_head}")
    log("  a parameter, rule or code change restarts the count under a NEW frozen file "
        "(ledger 13A.4)")
    return 0


def do_verify(args, log=print) -> int:
    fp = Path(args.verify)
    rec = load_frozen(fp)
    assert_frozen(
        fp,
        params=_read_params(args.params),
        code_paths=args.code,
        fixture_paths=args.fixtures,
    )
    if args.evaluation_days is not None:
        assert_evaluation_length(fp, args.evaluation_days)
    log(f"VERIFIED {fp}")
    log(f"  frozen {rec.frozen_utc}   content_sha256 {rec.content_sha256}")
    log(f"  {len(rec.params)} param(s), {len(rec.code)} code file(s), "
        f"{len(rec.fixtures)} fixture(s), evaluation_days {rec.evaluation_days}")
    log("  nothing has moved since the freeze")
    return 0


# --------------------------------------------------------------------------------------------
# self-test: every raise, proved, on synthetic files only
# --------------------------------------------------------------------------------------------
def selftest(log=print) -> int:
    log("D594 SELF-TEST -- synthetic files only; no fixture read, no seal date chosen\n")
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        alpha, beta, fix = d / "alpha.py", d / "beta.py", d / "g.csv.gz"
        alpha.write_bytes(b"a\n")
        beta.write_bytes(b"b\r\n")
        fix.write_bytes(b"\x1f\x8b\x08\x00bytes")
        params = {"tau": "15:00", "k": 3}
        code, fixtures = [alpha, beta], [fix]
        out = d / "results"

        rec = freeze(out, name="stageA", params=params, code_paths=code,
                     fixture_paths=fixtures, evaluation_days=200, spec_commit=SPEC,
                     instruction="synthetic, 2001-01-01: 'freeze stage A'")
        fp = rec.path
        log(f"  [0] froze {fp.name}: content_sha256 {rec.content_sha256}")
        assert_frozen(fp, params=params, code_paths=code, fixture_paths=fixtures)
        assert_evaluation_length(fp, 200)
        log("      and the guards are SILENT while nothing has moved "
            "(a check that always fires is not a check)")

        log("\n  [1] freeze() refuses to overwrite an existing frozen file (ledger 13A.4)")
        expect_raise(
            lambda: freeze(out, name="stageA", params=params, code_paths=code,
                           fixture_paths=fixtures, evaluation_days=200),
            "a second freeze under the same name", FrozenExistsError, log)

        log("\n  [2] one byte of ONE code file drifts, and the message names THAT file "
            "(ledger unit test 34)")
        alpha.write_bytes(b"A\n")
        try:
            assert_frozen(fp, params=params, code_paths=code, fixture_paths=fixtures)
            raise AssertionError("the guard did not raise on a drifted code file")
        except FrozenDriftError as e:
            msg = str(e)
            if "alpha.py" not in msg or "beta.py" in msg:
                raise AssertionError(f"the message did not name alpha.py alone: {msg}")
            if rec.code[0].sha256 not in msg:
                raise AssertionError("the message did not carry the expected digest")
            log(f"    RAISES on a drifted code file: {msg[:110]}")
        alpha.write_bytes(b"a\n")

        log("\n      and a CRLF-only rewrite of a code file is NOT drift (D550/D551)")
        beta.write_bytes(b"b\n")
        assert_frozen(fp, params=params, code_paths=code, fixture_paths=fixtures)
        log("      SILENT: the text digest is a fact about content, not about the checkout")
        beta.write_bytes(b"b\r\n")

        log("\n  [3] one parameter drifts (ledger unit test 34)")
        expect_raise(
            lambda: assert_frozen(fp, params={"tau": "15:00", "k": 4},
                                  code_paths=code, fixture_paths=fixtures),
            "a drifted param", FrozenDriftError, log)

        log("\n  [4] the evaluation length changes after evaluation started "
            "(ledger unit test 60 / 13A.7(2))")
        expect_raise(lambda: assert_evaluation_length(fp, 260),
                     "an extended evaluation window", FrozenDriftError, log)

        log("\n  [5] a SECOND opening of the sealed window for the same model "
            "(ledger unit test 65, opening unit test 20)")
        window = SealedWindow("2001-03-01", "2002-09-18")   # synthetic; see the docstring
        logp = out / "openings.jsonl"
        first = open_once(logp, window=window, model="stageA",
                          instruction="synthetic, 2001-01-01: 'open it'",
                          frozen_path=fp, params=params, code_paths=code,
                          fixture_paths=fixtures)
        log(f"    first opening logged at {first.opened_utc} "
            f"({logp.name}, {len(logp.read_bytes())} bytes)")
        expect_raise(
            lambda: open_once(logp, window=window, model="stageA",
                              instruction="synthetic, 2001-01-02: 'again'",
                              frozen_path=fp),
            "a second opening for the same model", AlreadyOpenedError, log)
        if len(logp.read_text(encoding="utf-8").splitlines()) != 1:
            raise AssertionError("the refused opening was appended to the log anyway")
        log("    and the refused opening appended NOTHING")

        log("\n      opening with no frozen model at all (ledger unit test 64 / 18)")
        expect_raise(
            lambda: open_once(out / "other.jsonl", window=window, model="m2",
                              instruction="synthetic: 'open'",
                              frozen_path=out / "FROZEN_absent.json"),
            "an opening without a frozen model", VaultGuardError, log)

        log("\n  [6] an unsorted sealed window")
        expect_raise(lambda: SealedWindow("2002-09-18", "2001-03-01"),
                     "start after end", FrozenError, log)

        log("\n  [7] the refusal, from the REAL entry point (the D574 shape)")
        said: list[str] = []
        rc = refuse_without_word(False, "a reserved slice", log=said.append)
        if rc != 2:
            raise AssertionError(f"refuse_without_word returned {rc}, not 2")
        if not said or not said[0].startswith("REFUSED: --run reads a reserved slice;"):
            raise AssertionError(f"the refusal message was {said!r}")
        log(f"    returns {rc}: {said[0]}")
        if refuse_without_word(True, "a reserved slice", log=said.append) != 0:
            raise AssertionError("refuse_without_word did not return 0 on the word")
        log("    and returns 0 on the principal's word, silently")

        log("\n  [8] a hand-edited frozen file (the easiest way to unfreeze a model)")
        obj = json.loads(fp.read_text(encoding="utf-8"))
        obj["evaluation_days"] = 400
        with open(fp, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh)
        expect_raise(lambda: load_frozen(fp), "an edited frozen file",
                     FrozenDriftError, log)

    log("\n  every guard raised on its break, and was silent otherwise. 9 checks.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true", help="prove every raise; no I/O outside a temp dir")
    ap.add_argument("--verify", metavar="FROZEN.json", help="check a frozen record against what is on disk now")
    ap.add_argument("--name", help="the frozen model's name; the file is FROZEN_<name>.json")
    ap.add_argument("--params", metavar="p.json", help="a JSON object of the frozen parameters")
    ap.add_argument("--code", nargs="*", default=[], metavar="PY", help="code files (hashed as TEXT, LF-pinned)")
    ap.add_argument("--fixtures", nargs="*", default=[], metavar="F", help="fixtures (hashed as the BYTES on disk)")
    ap.add_argument("--evaluation-days", type=int, default=None, help="the pre-computed evaluation length (13A.7(2))")
    ap.add_argument("--spec", default=None, help="the committed commit this model was frozen at")
    ap.add_argument("--instruction", default=None, help="the principal's words, verbatim, with a date")
    ap.add_argument("--live-git", action="store_true", help="also record `git rev-parse HEAD`; never required")
    ap.add_argument("--out", metavar="DIR", help="where FROZEN_<name>.json is written")
    args = ap.parse_args(argv)

    try:
        if args.selftest:
            return selftest()
        if args.verify:
            return do_verify(args)
        missing = [f"--{k}" for k in ("name", "out") if getattr(args, k) is None]
        if missing:
            ap.error(f"freezing needs {' and '.join(missing)} (or use --verify / --selftest)")
        return do_freeze(args)
    except FrozenError as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
