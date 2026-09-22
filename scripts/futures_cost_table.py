"""D591 -- build `data/futures_costs.json`, the reconciled futures cost table.

    uv run python scripts/futures_cost_table.py --build
    uv run python scripts/futures_cost_table.py --selftest
    uv run python scripts/futures_cost_table.py --show ES

WHAT THIS IS, AND WHAT IT IS NOT
--------------------------------
It is a COPYING machine. Every numeric value it writes is either

  (a) read out of a committed JSON artefact at a named key path, or
  (b) read out of a named source literal in a runner, through `ast`, never through a regex
      and never retyped here, or
  (c) arithmetic on (a) and (b) whose derivation is written into the record beside it.

and the builder REFUSES TO WRITE a value it cannot find that way. There is no fallback, no
default and no "approximately". A cost number that is merely plausible still produces a
Sharpe, which is why this is stricter than it looks.

It computes NO strategy return and reads NO bar. It reconciles ten cost literals read out of
six runners against seven committed measurement artefacts, and reconciling them found FIVE
disagreements (printed by `--selftest`, recorded in `disagreements`, discussed in D591).

DETERMINISM, AND WHY THERE IS NO TIMESTAMP
------------------------------------------
The output carries no build time. A timestamp would make every rebuild a diff and would make
`--selftest`'s byte-for-byte comparison impossible, which is the check that the committed
file IS what this builder produces from today's artefacts. The fingerprint is the sha256 of
every input instead -- which is the thing a timestamp only gestures at.

The file is written with LF newlines explicitly (D550: the author's OS is not the runner's).
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "futures_costs.json"


class BuildError(RuntimeError):
    """The builder could not find a value in a source, so it refuses to write one."""


def P(*a: object, **k: Any) -> None:
    print(*a, **k, flush=True)


# ------------------------------------------------------------------------------- sources

#: Committed JSON artefacts, by the short name this module cites them under.
ARTEFACTS = {
    "d465": "data/d465_es_spread_and_mae_bias.json",
    "d469": "data/d469_scalping_feasibility.json",
    "d507": "data/d507_spread_all_roots.json",
    "d508": "data/d508_micro_crossing_tbbo.json",
    "d510": "data/d510_spread_census.json",
    "d527": "data/d527_arm_crossing_cost.json",
    "d556": "data/d556_carry_timing.json",
    "cme_specs": "data/futures_contract_specs.json",
    "definition_specs": "data/fut_specs_from_definition.json",
}

#: Runner source files whose module-level literals are the DECLARED half of the table.
SCRIPTS = {
    "d469": "scripts/d469_scalping_feasibility.py",
    "d531": "scripts/run_d531_orb_session_native.py",
    "d532": "scripts/run_d532_orb_conditioned.py",
    "d533": "scripts/run_d533_story_conditions.py",
    "d535": "scripts/run_d535_illiq_ranked.py",
    "d555": "scripts/run_d555_tsmom_replication.py",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


class Sources:
    """Every input, loaded once, with its digest, and a `cite` that raises on a missing key."""

    def __init__(self) -> None:
        self.json: dict[str, Any] = {}
        self.digest: dict[str, str] = {}
        self.rel: dict[str, str] = {}
        for name, rel in ARTEFACTS.items():
            path = REPO / rel
            if not path.exists():
                raise BuildError(f"artefact {rel} is missing; the table cannot be built without it")
            self.json[name] = json.loads(path.read_text(encoding="utf-8"))
            self.digest[name] = sha256(path)
            self.rel[name] = rel
        self.script_digest: dict[str, str] = {}
        self.script_tree: dict[str, ast.Module] = {}
        for name, rel in SCRIPTS.items():
            path = REPO / rel
            if not path.exists():
                raise BuildError(f"source {rel} is missing; a declared literal cannot be cited")
            text = path.read_text(encoding="utf-8")
            self.script_digest[name] = sha256(path)
            self.script_tree[name] = ast.parse(text)

    # -- (a) artefact key paths ------------------------------------------------------

    def at(self, artefact: str, keypath: str) -> Any:
        """The value at a dotted key path, raising with the path that failed."""
        node: Any = self.json[artefact]
        walked: list[str] = []
        for part in keypath.split("."):
            walked.append(part)
            if isinstance(node, list):
                try:
                    node = node[int(part)]
                except (ValueError, IndexError) as exc:
                    raise BuildError(
                        f"{self.rel[artefact]}: no element at {'.'.join(walked)}"
                    ) from exc
                continue
            if not isinstance(node, dict) or part not in node:
                raise BuildError(
                    f"{self.rel[artefact]}: no key {'.'.join(walked)!r} "
                    f"(have: {', '.join(sorted(node)[:12]) if isinstance(node, dict) else type(node).__name__})"
                )
            node = node[part]
        return node

    def cite(
        self,
        artefact: str,
        keypath: str,
        decision: str,
        *,
        window: list[str] | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        """A measured value with its provenance. Refuses anything that is not a finite number."""
        value = self.at(artefact, keypath)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise BuildError(
                f"{self.rel[artefact]}:{keypath} is {type(value).__name__}, not a number"
            )
        value = float(value)
        if value != value or value in (float("inf"), float("-inf")):
            raise BuildError(f"{self.rel[artefact]}:{keypath} is not finite")
        out: dict[str, Any] = {
            "value": value,
            "measured": True,
            "provenance": {
                "artefact": self.rel[artefact],
                "key": keypath,
                "decision": decision,
            },
        }
        if window is not None:
            out["window"] = window
        if note is not None:
            out["note"] = note
        return out

    # -- (b) source literals ---------------------------------------------------------

    def literal(self, script: str, name: str) -> Any:
        """A module-level literal assignment, by `ast`.

        Handles a plain literal, and the one composed shape that occurs here:
        `dict(OTHER.NAME, k=v, **{...})` (run_d535's COST). A name it cannot evaluate
        RAISES -- the alternative is guessing what a runner charges.
        """
        for node in self.script_tree[script].body:
            if not isinstance(node, ast.Assign):
                continue
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if name not in targets:
                continue
            return self._eval(node.value, script, name)
        raise BuildError(f"{SCRIPTS[script]} has no module-level assignment to {name!r}")

    def _eval(self, node: ast.expr, script: str, name: str) -> Any:
        try:
            return ast.literal_eval(node)
        except ValueError:
            pass
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":
            out: dict[str, Any] = {}
            for arg in node.args:
                if isinstance(arg, ast.Attribute) and isinstance(arg.value, ast.Name):
                    # `dict(D533.COST, ...)` -- resolve through the module alias, which the
                    # importing script spells as the record number it imports from.
                    alias = arg.value.id.lower()
                    if alias not in self.script_tree:
                        raise BuildError(
                            f"{SCRIPTS[script]}: {name} composes from {arg.value.id}.{arg.attr}, "
                            f"and {alias!r} is not a source this builder reads"
                        )
                    out.update(self.literal(alias, arg.attr))
                else:
                    raise BuildError(f"{SCRIPTS[script]}: cannot evaluate {name}'s positional arg")
            for kw in node.keywords:
                if kw.arg is None:
                    out.update(ast.literal_eval(kw.value))
                else:
                    out[kw.arg] = ast.literal_eval(kw.value)
            return out
        raise BuildError(f"{SCRIPTS[script]}: {name} is not a literal this builder can evaluate")

    def declared(
        self, script: str, name: str, key: str | None, decision: str, why: str
    ) -> dict[str, Any]:
        """A DECLARED value: read from a runner literal, flagged `measured: false`."""
        literal = self.literal(script, name)
        if key is not None:
            if not isinstance(literal, dict) or key not in literal:
                raise BuildError(f"{SCRIPTS[script]}: {name} has no key {key!r}")
            value = literal[key]
        else:
            value = literal
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise BuildError(f"{SCRIPTS[script]}: {name}[{key!r}] is not a number")
        return {
            "value": float(value),
            "measured": False,
            "provenance": {
                "source": SCRIPTS[script],
                "literal": name if key is None else f"{name}[{key!r}]",
                "decision": decision,
                "why": why,
            },
        }


def derived(value: float, derivation: str, inputs: dict[str, Any], decision: str) -> dict[str, Any]:
    """Arithmetic on cited values. The derivation is written out, never implied."""
    return {
        "value": float(value),
        "measured": False,
        "provenance": {"derivation": derivation, "inputs": inputs, "decision": decision},
    }


# ------------------------------------------------------------------------------- the lines

#: Every crossing line the table can carry, and what statistic it is. Two DIFFERENT
#: statistics live here -- a QUOTED spread (a floor on the cost: D507, D510) and an EFFECTIVE
#: crossing (what an aggressor actually paid: D465, D508). The table never averages them and
#: the default never mixes them.
LINES: dict[str, dict[str, Any]] = {
    "d465": {
        "statistic": "effective, from the half-spread at trade instants, converted to ticks at "
        "D469's median price",
        "kind": "effective",
        "decision": "D465 / D469",
        "roots": "ES and MES only",
    },
    "d508_exec": {
        "statistic": "2*|price - mid| / tick at the instant of a trade, doubled for a round "
        "trip, over execution hours 10-15 ET",
        "kind": "effective",
        "decision": "D508",
        "roots": "the 8 micros and 8 parents D508 measured",
    },
    "d508_all": {
        "statistic": "the same effective statistic over the whole session",
        "kind": "effective",
        "decision": "D508",
        "roots": "the 8 micros and 8 parents D508 measured",
    },
    "d510": {
        "statistic": "time-weighted quoted spread in ticks, whole session (a FLOOR on the cost)",
        "kind": "quoted",
        "decision": "D510",
        "roots": "9 roots",
    },
    "d507_all": {
        "statistic": "time-weighted quoted spread in ticks on bbo-1m, whole session (a FLOOR)",
        "kind": "quoted",
        "decision": "D507",
        "roots": "41 symbols",
    },
    "d507_exec": {
        "statistic": "the same quoted spread conditioned on the execution instants (a FLOOR)",
        "kind": "quoted",
        "decision": "D507",
        "roots": "41 symbols",
    },
    "d556_one_tick": {
        "statistic": "CONVENTION, not a measurement: D555/D556 charge 0.5 tick a side, so one "
        "full tick a round trip",
        "kind": "convention",
        "decision": "D468 / D555 / D556",
        "roots": "every root",
    },
}

DEFAULT_LINE_RULE = (
    "d508_exec where D508 measured the contract -- it is an EFFECTIVE crossing (what an "
    "aggressor paid), trade-weighted, and conditioned on the hours a study actually executes "
    "in. Everywhere else the D556 one-tick convention, NOT D507: D507 is a QUOTED spread and "
    "therefore a floor, so falling back to it would serve two different statistics under one "
    "name and would silently make an unmeasured root look cheaper than a measured one. The "
    "one-tick rule is also what the seen ledger charges, so a construction scored on the "
    "default reproduces the ledger's cost line rather than improving on it."
)


# ------------------------------------------------------------------------------- build


def spec_for(src: Sources, symbol: str) -> dict[str, Any]:
    """tick_points / usd_per_point / tick_usd for one traded symbol, from the exchange files.

    CME's own specification service first (`Future.from_specs`'s primary), the Databento GLBX
    definition snapshot second. Unknown -> raise; a guessed multiplier prices every fill wrong.
    """
    cme = src.json["cme_specs"]
    if isinstance(cme.get(symbol), dict) and "usd_per_point" in cme[symbol]:
        tick_points = float(src.at("cme_specs", f"{symbol}.tick_points"))
        usd_per_point = float(src.at("cme_specs", f"{symbol}.usd_per_point"))
        tick_usd = float(src.at("cme_specs", f"{symbol}.tick_usd"))
        out = {
            "tick_points": tick_points,
            "usd_per_point": usd_per_point,
            "tick_usd": tick_usd,
            "specs_provenance": {
                "artefact": src.rel["cme_specs"],
                "key": f"{symbol}.(tick_points, usd_per_point, tick_usd)",
                "source": "CME contract-specification service, read 2026-09-10",
            },
            "tick_usd_verified": True,
        }
    else:
        entry = src.json["definition_specs"]["specs"].get(symbol)
        if not isinstance(entry, dict) or not entry.get("present"):
            raise BuildError(
                f"no contract specification for {symbol!r} in either "
                f"{src.rel['cme_specs']} or {src.rel['definition_specs']}"
            )
        tick_points = float(src.at("definition_specs", f"specs.{symbol}.tick_price_units"))
        # `tick_usd_full_contract`, NOT `tick_usd` -- D609. The snapshot's own `tick_usd`
        # divides by 100 on `unit_of_measure == "USD"` alone; the corrected field is decided by
        # the NOTIONAL test and reproduces CME on all 17 roots where CME's value is on file.
        tick_usd = float(src.at("definition_specs", f"specs.{symbol}.tick_usd_full_contract"))
        out = {
            "tick_points": tick_points,
            "usd_per_point": tick_usd / tick_points,
            "tick_usd": tick_usd,
            "specs_provenance": {
                "artefact": src.rel["definition_specs"],
                "key": f"specs.{symbol}.(tick_price_units, tick_usd_full_contract)",
                "source": "Databento GLBX definition snapshot, NOTIONAL-scaled (D609); "
                "usd_per_point = tick_usd_full_contract / tick",
            },
            "tick_usd_verified": entry.get("known_tick_usd") is not None,
            "quote_uom": entry.get("uom"),
            "percent_of_par": bool(entry.get("percent_of_par")),
            "scaling_divisor": float(
                src.at("definition_specs", f"specs.{symbol}.scaling_divisor")
            ),
            "scaling_reason": src.at("definition_specs", f"specs.{symbol}.scaling_reason"),
            "tick_usd_raw_formula": float(
                src.at("definition_specs", f"specs.{symbol}.tick_usd_raw_formula")
            ),
        }
    implied = out["usd_per_point"] * out["tick_points"]
    if abs(implied - out["tick_usd"]) > 1e-9 * out["tick_usd"]:
        raise BuildError(
            f"{symbol}: usd_per_point * tick_points = {implied!r} but tick_usd = {out['tick_usd']!r}"
        )
    return out


#: Price units that are CENTS at CME, so the definition file's raw formula
#: `tick_price_units * unit_of_measure_qty` is a hundredfold of the dollar value.
#:
#: **D609 CORRECTED THIS AND THE COMMENT THAT USED TO SIT HERE WAS THE DEFECT.** It said the
#: table "FLAGS the affected rows and writes the artefact's own figure unchanged", because
#: "inventing a corrected number would be typing a value no source carries". That was right
#: about the rule and wrong about the facts: a source DID carry the corrected number --
#: `fut_breadth_hourly.meta.json` has decided the scaling by the notional test since D519 --
#: and the builder was reading the wrong field of the wrong file. The definition table now
#: carries `tick_usd_full_contract` beside its raw formula, so nothing here is typed and
#: nothing here is written unchanged that is known to be wrong. `HG` is the root that proves
#: the divide is not inferable from `unit_of_measure`: it is "LBS" like ZL and is NOT divided.
CENT_QUOTED_UOM = {"BU", "LBS"}


def crossing_lines(src: Sources, symbol: str) -> dict[str, Any]:
    """Every crossing line measured on one traded symbol, in ticks per round trip."""
    out: dict[str, Any] = {}

    d508 = src.json["d508"]["per_root"]
    if symbol in d508:
        window = list(src.at("d508", "window"))
        out["d508_exec"] = src.cite(
            "d508",
            f"per_root.{symbol}.execution_hours.effective_mean_ticks",
            "D508",
            window=window,
            note="execution hours 10-15 ET",
        )
        out["d508_all"] = src.cite(
            "d508", f"per_root.{symbol}.all_session.effective_mean_ticks", "D508", window=window
        )

    d507 = src.json["d507"]["per_root"]
    if symbol in d507:
        window = list(src.at("d507", "window"))
        out["d507_all"] = src.cite(
            "d507",
            f"per_root.{symbol}.all_session.mean_spread_ticks",
            "D507",
            window=window,
            note="QUOTED spread -- a floor on the cost, not what an aggressor paid",
        )
        out["d507_exec"] = src.cite(
            "d507",
            f"per_root.{symbol}.execution_instants.mean_spread_ticks",
            "D507",
            window=window,
            note="QUOTED spread at the execution instants -- a floor",
        )

    for i, row in enumerate(src.json["d510"]["table"]):
        if row.get("root") == symbol:
            out["d510"] = src.cite(
                "d510",
                f"table.{i}.mean_spread_ticks",
                "D510",
                window=list(src.at("d510", "window")),
                note="QUOTED spread, time-weighted -- a floor",
            )
            break

    if symbol in ("ES", "MES"):
        out["d465"] = src.cite(
            "d469",
            f"cost_bars.{symbol}.crossing_ticks",
            "D465 / D469",
            window=["2025-09-11", "2026-09-11"],
            note=(
                "D465's 0.18219682151764224 bp a side, doubled and converted at D469's median "
                "price 6919.5. ES and MES differ in the last ULP because the same dollar figure "
                "is divided by a different tick_usd"
            ),
        )

    out["d556_one_tick"] = derived(
        1.0,
        "D555/D556 charge 0.5 * tick_usd a side (run_d555:dollar_book), so one full tick a "
        "round trip. A convention, not a measurement -- no window.",
        {"rule": "cost_per_side = comm_rt/2 + 0.5 * tick_usd"},
        "D468 / D555 / D556",
    )
    return out


def build(src: Sources) -> dict[str, Any]:
    min_size = src.at("d556", "dollar_book.min_size")
    micro_of = src.literal("d555", "MICRO_OF")

    # [XCHK] The artefact's min_size map and the runner's MICRO_OF literal are two records of
    # one fact. They must agree, or the table would be citing a size no runner traded.
    for root, sized in min_size.items():
        expected = micro_of.get(root, root)
        if sized != expected:
            raise BuildError(
                f"[XCHK] {root}: d556 min_size is {sized!r} but run_d555's MICRO_OF says "
                f"{expected!r}; the two records of the minimum tradable size disagree"
            )
    for root in micro_of:
        if root not in min_size:
            raise BuildError(f"[XCHK] run_d555's MICRO_OF carries {root!r}, which d556 does not size")

    # The runner lines, read as literals rather than retyped.
    d531_cost = src.literal("d531", "COST_USD")
    d531_roots = tuple(src.literal("d531", "CAND")) + tuple(src.literal("d531", "CALIB"))
    d533_cost = src.literal("d533", "COST")
    d532_cost = src.literal("d532", "COST")
    if d532_cost != d533_cost:
        raise BuildError("[XCHK] run_d532's COST and run_d533's COST were taken to be identical")
    d535_cost = src.literal("d535", "COST")
    d533_minsize = src.literal("d533", "MINSIZE")

    roots: dict[str, Any] = {}
    by_symbol: dict[str, list[str]] = {}
    flags: list[dict[str, Any]] = []

    for root in sorted(min_size):
        entry: dict[str, Any] = {}
        sizes = [("full", root)]
        if root in micro_of:
            sizes.append(("micro", micro_of[root]))

        for size, symbol in sizes:
            spec = spec_for(src, symbol)
            kind = "micro" if size == "micro" else "full"
            commission = src.declared(
                "d555",
                "COMMISSION_RT",
                kind,
                "D468",
                "DECLARED brokerage cost, never measured here. run_d555:56 calls it "
                "\"D468's convention\"; D466 declares the same $3 on the index micros and $6 "
                "full-size.",
            )
            crossing = crossing_lines(src, symbol)
            default_line = "d508_exec" if "d508_exec" in crossing else "d556_one_tick"

            runner_lines: dict[str, Any] = {}
            if min_size[root] == symbol:
                rt = commission["value"] + spec["tick_usd"]
                runner_lines["d556_min_size"] = derived(
                    rt,
                    "comm_rt + tick_usd -- two sides of (comm_rt/2 + 0.5*tick_usd)",
                    {
                        "comm_rt": commission["value"],
                        "tick_usd": spec["tick_usd"],
                        "min_size": symbol,
                        "min_size_key": f"dollar_book.min_size.{root}",
                    },
                    "D555 / D556",
                )
            if size == "micro" and root in d531_roots:
                runner_lines["d531"] = src.declared(
                    "d531",
                    "COST_USD",
                    None,
                    "D531",
                    "one FLAT round trip charged on all six of D531's roots at micro size; its "
                    "comment names it \"D527-corrected round trip at one micro\"",
                )
            if size == "micro" and root in d533_cost:
                line = src.declared("d533", "COST", root, "D532 / D533", _d533_why(root, d533_minsize))
                runner_lines["d533"] = line
            if size == "micro" and root in d535_cost and root not in d533_cost:
                runner_lines["d535"] = src.declared(
                    "d535", "COST", root, "D535", "D533's dict extended to the confirmation set"
                )
            if size == "full" and root in d535_cost and root not in d533_cost:
                runner_lines["d535_full"] = src.declared(
                    "d535",
                    "COST",
                    root,
                    "D535",
                    "D535 charges this at the size named in its own UPT map, which is the micro "
                    "where one exists; recorded on the full entry only for the roots with no micro",
                )
            if symbol in ("ES", "MES"):
                runner_lines["d469"] = _d469_line(src, symbol)
            if symbol == "MNQ":
                runner_lines["d527"] = _d527_line(src)

            if not spec.get("tick_usd_verified", False):
                flag = {
                    "symbol": symbol,
                    "tick_usd": spec["tick_usd"],
                    "uom": spec.get("quote_uom"),
                    "percent_of_par": spec.get("percent_of_par"),
                    "why": "tick_usd comes from the definition snapshot's formula and CME's own "
                    "value is not on file for this symbol (known_tick_usd is null)",
                }
                divisor = spec.get("scaling_divisor")
                if divisor is not None:
                    flag["scaling_divisor"] = divisor
                    flag["scaling_reason"] = spec.get("scaling_reason")
                    flag["tick_usd_raw_formula"] = spec.get("tick_usd_raw_formula")
                if spec.get("quote_uom") in CENT_QUOTED_UOM and divisor == 100.0:
                    flag["unit"] = (
                        "CORRECTED (D609), divisor 100: this root is quoted in CENTS per unit, "
                        f"so the definition snapshot's raw formula gives "
                        f"{spec['tick_usd_raw_formula']} cents and the dollar tick is "
                        f"${spec['tick_usd']:.2f}. The divisor is the NOTIONAL test's, not a "
                        "unit_of_measure rule: HG is 'LBS' too and is NOT divided."
                    )
                if spec.get("percent_of_par"):
                    flag["percent_of_par_note"] = (
                        "the definition snapshot's own `tick_usd` divides by 100 for "
                        "percent-of-par products; that is right where unit_of_measure_qty is "
                        "the par notional (ZN, ZB, ZF all reproduce CME) and wrong where it is "
                        "already dollars per index point (SR3: 0.0625 against CME's $6.25). "
                        f"D609 reads tick_usd_full_contract instead, so this table charges "
                        f"${spec['tick_usd']} at divisor {divisor:g}."
                    )
                flags.append(flag)

            entry[size] = {
                "symbol": symbol,
                **{k: v for k, v in spec.items() if k != "specs_provenance"},
                "specs_provenance": spec["specs_provenance"],
                "commission_rt_usd": commission,
                "crossing_ticks_rt": crossing,
                "default_line": default_line,
                "runner_lines": runner_lines,
            }
            by_symbol[symbol] = [root, size]

        entry["min_size"] = "micro" if root in micro_of else "full"
        if root not in micro_of:
            entry["no_micro_because"] = (
                "CME lists no micro for this root in data/futures_contract_specs.json, and "
                "run_d555's MICRO_OF does not name one; D556 sizes it at one full contract."
            )
        roots[root] = entry

    return {
        "_provenance": {
            "decision": "D591",
            "built_by": "uv run python scripts/futures_cost_table.py --build",
            "digests_live_here_only": "a provenance block names its artefact and key path; "
            "the sha256 of every input is recorded once, below, rather than repeated beside "
            "each of the 289 cited values",
            "rule": "every value is copied from a committed artefact at a named key path, or "
            "from a named source literal read through ast, or derived from those two with the "
            "derivation recorded. The builder refuses to write a value it cannot find.",
            "no_timestamp_because": "a build time would make every rebuild a diff and would "
            "make --selftest's byte-for-byte check impossible; the input digests are the "
            "fingerprint instead",
            "computes_no_return": True,
            "artefacts": {
                ARTEFACTS[name]: {"sha256": src.digest[name]} for name in sorted(ARTEFACTS)
            },
            "sources": {
                SCRIPTS[name]: {"sha256": src.script_digest[name]} for name in sorted(SCRIPTS)
            },
        },
        "conventions": {
            "crossing_unit": "TICKS per ROUND TRIP. Half is charged on each of the two fills.",
            "commission_unit": "USD per ROUND TRIP per CONTRACT, DECLARED. Half per fill.",
            "round_trip_usd": "commission_rt_usd + crossing_ticks_rt * tick_usd",
            "default_line_rule": DEFAULT_LINE_RULE,
            "window_caveat": "every crossing census on disk was measured on 2025-09..2026-09 "
            "and is applied by its callers to 2016-2023. A tick is fixed in price terms, so a "
            "recent spread on an older, cheaper window is OPTIMISTIC (D507, D508 say so "
            "themselves). Each line carries its window for that reason.",
            "two_statistics": "QUOTED spread (D507, D510) is a FLOOR; EFFECTIVE crossing "
            "(D465, D508) is what an aggressor paid. They are never averaged and the default "
            "never falls back from one to the other.",
        },
        "lines": LINES,
        "by_symbol": by_symbol,
        "roots": roots,
        "spec_flags": flags,
        "disagreements": _disagreements(src, d533_cost, d533_minsize),
    }


def _d533_why(root: str, minsize: dict[str, Any]) -> str:
    sized = minsize.get(root, ("its micro",))[0]
    return (
        f"charged at minimum tradable size ({sized}); D532's pre-registration line 97 says the "
        "four non-index values come \"from the measured median spreads\". Whether each one is "
        "reproducible from a line in this table is recorded in `disagreements`."
    )


def _d469_line(src: Sources, symbol: str) -> dict[str, Any]:
    return {
        "commission_rt_usd": src.declared(
            "d469",
            "COMMISSION_RT",
            symbol,
            "D258 (ES) / D466 (MES)",
            "D469's own declared commission. NOT run_d555's $6 full-size line -- see "
            "`disagreements`.",
        ),
        "crossing_usd_rt": src.cite("d469", f"cost_bars.{symbol}.crossing_usd", "D469"),
        "total_usd_rt": src.cite("d469", f"cost_bars.{symbol}.total_usd", "D469"),
        "breakeven_ticks": src.cite("d469", f"cost_bars.{symbol}.breakeven_ticks", "D469"),
        "at_price": src.cite("d469", "median_price", "D469"),
    }


def _d527_line(src: Sources) -> dict[str, Any]:
    return {
        "crossing_ticks_rt": src.cite(
            "d527",
            "reprice.round_trip_crossing_ticks",
            "D527",
            window=list(src.at("d527", "reprice.window")),
            note="STRATEGY-SPECIFIC: measured at the D484 MACD arm's own fill timestamps, which "
            "are concentrated in the 10:00 ET hour where the spread is 3.66 ticks. NOT the root "
            "default. reprice.scored.measured.cross_ticks carries the same number one ULP lower.",
        ),
        "commission_rt_usd": src.declared(
            "d555", "COMMISSION_RT", "micro", "D468", "one MNQ at the micro line"
        ),
        "rt_usd": src.cite("d527", "reprice.scored.measured.rt_usd", "D527"),
        "assumed_rt_usd": src.cite("d527", "reprice.scored.assumed.rt_usd", "D527"),
    }


def _disagreements(src: Sources, d533_cost: dict, d533_minsize: dict) -> list[dict[str, Any]]:
    """Every place two committed records give different numbers for the same thing."""
    out: list[dict[str, Any]] = []

    d469_comm = src.literal("d469", "COMMISSION_RT")
    d555_comm = src.literal("d555", "COMMISSION_RT")
    if d469_comm["ES"] != d555_comm["full"]:
        out.append(
            {
                "what": "full-size commission per round trip",
                "values": {
                    f"{SCRIPTS['d469']}:COMMISSION_RT['ES']": d469_comm["ES"],
                    f"{SCRIPTS['d555']}:COMMISSION_RT['full']": d555_comm["full"],
                },
                "resolution": "the table's `full` entries carry $6.00, the later and broader "
                "convention and the one the seen ledger charges; D469's $4.00 survives verbatim "
                "in ES's runner_lines.d469 so its published breakeven bar stays reproducible.",
                "measured": False,
            }
        )

    # D533's four non-index values against the one-tick rule they are closest to.
    for root, charged in sorted(d533_cost.items()):
        sized = d533_minsize.get(root, (None,))[0]
        if sized is None:
            continue
        spec = spec_for(src, sized)
        rule = d555_comm["micro"] + spec["tick_usd"]
        if charged != rule:
            out.append(
                {
                    "what": f"D533's charged round trip on {root} ({sized})",
                    "values": {
                        f"{SCRIPTS['d533']}:COST[{root!r}]": charged,
                        "D556 one-tick rule (comm 3.00 + tick_usd)": rule,
                    },
                    "resolution": "recorded as charged, NOT derived: no line in this table "
                    "produces it. Both are conservative against the rule.",
                    "measured": False,
                }
            )

    d527_a = src.at("d527", "reprice.round_trip_crossing_ticks")
    d527_b = src.at("d527", "reprice.scored.measured.cross_ticks")
    if d527_a != d527_b:
        out.append(
            {
                "what": "D527's round-trip crossing in ticks, carried twice",
                "values": {
                    "reprice.round_trip_crossing_ticks": d527_a,
                    "reprice.scored.measured.cross_ticks": d527_b,
                },
                "resolution": "one ULP apart; both give rt_usd 4.205511636799441 exactly on "
                "MNQ's $0.50 tick. The table carries the first, the artefact's headline. On a "
                "$31.25 tick the same gap would not be immaterial.",
                "measured": True,
            }
        )

    es = src.at("d469", "cost_bars.ES.crossing_ticks")
    mes = src.at("d469", "cost_bars.MES.crossing_ticks")
    if es != mes:
        out.append(
            {
                "what": "D465's round-trip crossing in ticks, on ES and on MES",
                "values": {"cost_bars.ES.crossing_ticks": es, "cost_bars.MES.crossing_ticks": mes},
                "resolution": "one ULP apart -- the same bp figure divided by $12.50 and by "
                "$1.25. Each size entry carries its own contract's number so that D469's "
                "published bars reproduce exactly on both rows.",
                "measured": True,
            }
        )
    return out


# ------------------------------------------------------------------------------- selftest


def expect_raise(fn: Any, what: str) -> None:
    """The D48/D399 idiom: a guard that cannot fire is worse than no guard."""
    try:
        fn()
    except (BuildError, ValueError, TypeError, KeyError) as exc:
        P(f"    RAISES on {what}: {str(exc)[:88]}")
        return
    raise AssertionError(f"guard did not raise on {what}")


def selftest(src: Sources, table: dict[str, Any]) -> int:
    """Reproduce every published number the table claims, and prove the refusals fire."""
    failures: list[str] = []

    def check(label: str, got: Any, want: Any) -> None:
        ok = got == want
        P(f"  [{'ok ' if ok else 'FAIL'}] {label}: {got!r}" + ("" if ok else f" != {want!r}"))
        if not ok:
            failures.append(f"{label}: got {got!r}, want {want!r}")

    P("[1] the committed file is what this builder produces")
    if OUT.exists():
        # The DIGEST, not the bytes: the comparison is byte-for-byte either way, and a failure
        # that dumps 250 KB of JSON into the log is a failure nobody reads.
        want = hashlib.sha256(_render(table).encode("utf-8")).hexdigest()
        check("sha256 of data/futures_costs.json", sha256(OUT), want)
    else:
        P("  [--  ] not written yet; run --build")

    P("[2] published round trips, reproduced from the table's own fields")
    roots = table["roots"]

    def rt(root: str, size: str, line: str) -> float:
        e = roots[root][size]
        return e["commission_rt_usd"]["value"] + e["crossing_ticks_rt"][line]["value"] * e["tick_usd"]

    mnq = roots["NQ"]["micro"]
    d527_rt = 3.0 + mnq["runner_lines"]["d527"]["crossing_ticks_rt"]["value"] * mnq["tick_usd"]
    check("MNQ on the D527 line", d527_rt, src.at("d527", "reprice.scored.measured.rt_usd"))
    check("...and D531's rounded form", round(d527_rt, 2), src.literal("d531", "COST_USD"))

    for root, want in [("NQ", 3.50), ("ES", 4.25), ("CL", 4.00), ("SI", 8.00), ("ZN", 21.625),
                       ("ZB", 37.25), ("ZF", 13.8125)]:
        size = roots[root]["min_size"]
        check(f"D556 min-size round trip, {root}", rt(root, size, "d556_one_tick"), want)
        check(
            f"...and its recorded runner line, {root}",
            roots[root][size]["runner_lines"]["d556_min_size"]["value"],
            want,
        )

    P("[3] D469's breakeven bars, from the d465 line")
    for root, size, symbol in [("ES", "full", "ES"), ("ES", "micro", "MES")]:
        e = roots[root][size]
        total = e["runner_lines"]["d469"]["commission_rt_usd"]["value"] + (
            e["crossing_ticks_rt"]["d465"]["value"] * e["tick_usd"]
        )
        check(f"{symbol} total_usd", total, src.at("d469", f"cost_bars.{symbol}.total_usd"))
        check(
            f"{symbol} breakeven_ticks",
            total / e["tick_usd"],
            src.at("d469", f"cost_bars.{symbol}.breakeven_ticks"),
        )

    P("[4] the refusals fire")
    expect_raise(lambda: src.at("d508", "per_root.NOPE.execution_hours.effective_mean_ticks"),
                 "a key path that is not in the artefact")
    expect_raise(lambda: src.literal("d555", "NO_SUCH_LITERAL"), "a literal that is not in the runner")
    expect_raise(lambda: src.cite("d508", "purpose", "D508"), "a cited value that is not a number")
    expect_raise(lambda: spec_for(src, "NOPE"), "a symbol in neither specification file")

    P("[5] structure")
    check("roots", len(table["roots"]), 36)
    check("symbols indexed", len(table["by_symbol"]), 47)
    for root, entry in table["roots"].items():
        for size in ("micro", "full"):
            if size not in entry:
                continue
            e = entry[size]
            if e["default_line"] not in e["crossing_ticks_rt"]:
                failures.append(f"{root}.{size}: default_line names a line it does not carry")
            for name in e["crossing_ticks_rt"]:
                if name not in table["lines"]:
                    failures.append(f"{root}.{size}: undeclared line {name}")
    check("every default_line is carried, every line declared", failures, [])

    P("")
    P(f"[6] disagreements recorded: {len(table['disagreements'])}")
    for d in table["disagreements"]:
        P(f"    - {d['what']}: {d['values']}")
    P(f"[7] spec rows flagged (tick_usd not verified against CME): {len(table['spec_flags'])}")
    for f in table["spec_flags"]:
        P(f"    - {f['symbol']}: tick_usd {f['tick_usd']}" + (f" -- {f['unit'][:60]}" if "unit" in f else ""))

    P("")
    if failures:
        P(f"SELFTEST FAILED: {len(failures)}")
        for f in failures:
            P(f"  {f}")
        return 1
    P("SELFTEST PASSED")
    return 0


def _render(table: dict[str, Any]) -> str:
    """The table's bytes, pinned.

    `json.dumps` escapes non-ASCII by default and that default is LEFT ALONE deliberately: it
    is the invariant `tests/unit/test_encoding_is_declared.py` gates, and it is why a reader
    opening this file through a platform default encoding still gets the right bytes. (That
    test greps the source for the argument's name, so this note does not spell it.) The write
    side pins `encoding="utf-8"` and `newline="\\n"` too (D550), so the file is identical on
    any OS and `--selftest` can compare it byte for byte.
    """
    return json.dumps(table, indent=1) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build", action="store_true", help="write data/futures_costs.json")
    ap.add_argument("--selftest", action="store_true", help="reproduce every published number")
    ap.add_argument("--show", metavar="ROOT", help="print one root's entry")
    args = ap.parse_args(argv)
    if not (args.build or args.selftest or args.show):
        ap.print_help()
        return 2

    src = Sources()
    table = build(src)

    if args.build:
        OUT.write_text(_render(table), encoding="utf-8", newline="\n")
        P(f"wrote {OUT.relative_to(REPO)} -- {len(table['roots'])} roots, "
          f"{len(table['by_symbol'])} traded symbols, {len(table['lines'])} crossing lines")

    if args.show:
        root = args.show.upper()
        if root in table["roots"]:
            P(json.dumps({root: table["roots"][root]}, indent=1))
        elif root in table["by_symbol"]:
            parent, size = table["by_symbol"][root]
            P(json.dumps({f"{parent}.{size}": table["roots"][parent][size]}, indent=1))
        else:
            P(f"no entry for {root!r}; roots: {', '.join(sorted(table['roots']))}")
            return 1

    if args.selftest:
        return selftest(src, table)
    return 0


if __name__ == "__main__":
    sys.exit(main())
