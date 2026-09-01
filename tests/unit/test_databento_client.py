"""Gates on the Databento client.

**Entirely offline. No key, no network, not even a mock server.** Everything
tested here is either pure arithmetic or the shape of the constants block, which
is deliberate: the value of this module before a purchase is that it CANNOT
spend and that its assumptions are visible.

The live surface is checked by `fetch_databento.py --verify`, which is free.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def mod():
    path = REPO / "scripts" / "fetch_databento.py"
    spec = importlib.util.spec_from_file_location("fetch_databento", path)
    m = importlib.util.module_from_spec(spec)
    sys.modules["fetch_databento"] = m
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------- the costing arithmetic


def test_the_plan_reproduces_the_proposals_symbol_years(mod):
    """§5 of the proposal commits to 26 symbols and 358 symbol-years. If this
    drifts, the proposal and the code disagree about what is being bought."""
    rows = mod.symbol_years()
    assert sum(len(s) for _g, s, _y, _sy in rows) == 26
    assert sum(sy for *_r, sy in rows) == pytest.approx(358.0)


def test_the_per_symbol_year_rate_is_derived_not_typed(mod):
    """56 bytes/bar x 347,760 bars/symbol-year at $28.00/GiB. The proposal quotes
    $0.51 and $182.58; the exact figures are $0.5079 and $181.81, because $0.51
    was a rounded intermediate. The code carries the exact one."""
    per_sy = (mod.BARS_PER_SYMBOL_YEAR * mod.OHLCV_MSG_BYTES / 2**30
              * mod.DERIVED_USD_PER_GIB)
    assert per_sy == pytest.approx(0.5079, abs=1e-4)
    total = per_sy * sum(sy for *_r, sy in mod.symbol_years())
    assert total == pytest.approx(181.81, abs=0.02)
    # And it must still fit the story: over the credit, but not by much.
    assert total > mod.FREE_CREDIT_USD
    assert total - mod.FREE_CREDIT_USD < 100


def test_the_rate_itself_is_the_one_inferred_number(mod):
    """Databento's own worked example: 99,219,648 bytes billed at
    $2.587353944778. That is EXACTLY $28.00/GiB, and it is the only place the
    whole costing touches a number we did not compute ourselves."""
    assert 2.587353944778 / (99_219_648 / 2**30) == pytest.approx(28.00, abs=1e-6)
    assert mod.DERIVED_USD_PER_GIB == 28.00


# ------------------------------------------------------------- the API surface


def test_endpoint_paths_use_dots_not_slashes(mod):
    """`/v0/metadata.list_datasets`, not `/v0/metadata/list_datasets`. Verified
    against two client sources and the official curl examples."""
    for name, (method, path) in mod.ENDPOINTS.items():
        assert "." in path, name
        assert "/" not in path, name
        assert method in ("GET", "POST"), name
    assert mod.BASE == "https://hist.databento.com/v0"


def test_the_money_endpoints_are_post(mod):
    """Both official clients POST get_cost and submit_job; the docs show GET for
    get_cost. The conflict is recorded in the module docstring and resolved in
    favour of what ships in production."""
    assert mod.ENDPOINTS["submit_job"][0] == "POST"
    assert mod.ENDPOINTS["get_cost"][0] == "POST"
    assert mod.ENDPOINTS["list_unit_prices"][0] == "GET"


def test_unit_price_accepts_the_array_shape_which_is_the_real_one(mod):
    """CORRECTED ASSUMPTION. The response is a JSON ARRAY of {mode, unit_prices},
    not a dict keyed by mode. This project believed the dict shape for long
    enough to reach a costed proposal, so both are accepted -- a client that
    dies on the shape it expected teaches nothing."""
    real = [
        {"mode": "historical", "unit_prices": {"ohlcv-1m": 28.0, "trades": 28.0}},
        {"mode": "live", "unit_prices": {"ohlcv-1m": 99.0}},
    ]
    assert mod.unit_price(real, "ohlcv-1m") == 28.0
    assert mod.unit_price(real, "ohlcv-1m", mode="live") == 99.0
    # The shape we WRONGLY assumed still parses, rather than crashing.
    legacy = {"historical": {"ohlcv-1m": 28.0}}
    assert mod.unit_price(legacy, "ohlcv-1m") == 28.0


def test_symbols_are_comma_joined_not_repeated(mod):
    """`symbols` is a single comma-separated string. Sending repeated params
    would silently request only one symbol on some stacks."""
    joined = ",".join(mod.continuous(s) for s in ["ES", "NQ", "YM"])
    assert joined == "ES.v.0,NQ.v.0,YM.v.0"


def test_encoding_and_compression_are_explicit(mod):
    """The raw HTTP API defaults to csv/none where the official clients send
    dbn/zstd. Omitting them means being billed for something other than what was
    expected."""
    assert mod.ENCODING == "dbn"
    assert mod.COMPRESSION == "zstd"


# ------------------------------------------------------------- the roll rule


def test_the_default_roll_rule_is_volume_not_calendar(mod):
    """THE CORRECTION THAT MATTERS. §11 of the proposal wrote `ES.c.0`, and `c`
    is almost certainly CALENDAR -- rolling at expiry, which is exactly the
    failure measured in Yahoo's ES=F, where the last 4-5 days of each quarter
    track the dying contract and contaminate 7-8% of the sample. §12 requires
    rolling on volume/open-interest crossover, so the default is `v`."""
    assert mod.ROLL_RULE == "v"
    assert mod.ROLL_RULES[mod.ROLL_RULE] == "volume"
    assert mod.continuous("ES") == "ES.v.0"
    assert mod.continuous("ES") != "ES.c.0"
    # The calendar rule must still be nameable, so --verify can resolve all three.
    assert mod.ROLL_RULES["c"] == "calendar"
    assert mod.ROLL_RULES["n"] == "open_interest"


def test_stype_in_is_continuous_never_parent(mod):
    """`parent` resolves to every outright PLUS every calendar spread -- wrong
    data and far more of it."""
    assert mod.STYPE_IN == "continuous"


# --------------------------------------------------------- it cannot spend


def test_submit_refuses_without_a_verify_stamp(mod, monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "VERIFY_STAMP", tmp_path / "absent.json")
    with pytest.raises(SystemExit) as exc:
        mod.do_submit(181.81)
    assert "verify" in str(exc.value).lower()


def test_submit_refuses_without_an_accepted_cost(mod, monkeypatch, tmp_path):
    stamp = tmp_path / "verify.json"
    stamp.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(mod, "VERIFY_STAMP", stamp)
    with pytest.raises(SystemExit) as exc:
        mod.do_submit(None)
    assert "REFUSING TO SPEND" in str(exc.value)


def test_submit_is_not_wired_up_even_when_fully_authorised(mod, monkeypatch,
                                                           tmp_path):
    """A spending path that exists is a spending path that can be run by
    accident. It gets wired up in the same commit as the purchase decision."""
    stamp = tmp_path / "verify.json"
    stamp.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(mod, "VERIFY_STAMP", stamp)
    with pytest.raises(SystemExit) as exc:
        mod.do_submit(181.81)
    assert "not wired up" in str(exc.value)


def test_plan_needs_no_key_and_no_network(mod, monkeypatch, capsys):
    """--plan must work on a machine that has never seen a Databento key."""
    monkeypatch.delenv("DATABENTO_API_KEY", raising=False)
    monkeypatch.setattr(mod, "KEY_FILE", Path("/nonexistent/key"))

    def _boom(*_a, **_k):  # pragma: no cover - the point is that it is unreached
        raise AssertionError("--plan touched the network")

    monkeypatch.setattr(mod, "call", _boom)
    assert mod.do_plan() == 0
    out = capsys.readouterr().out
    assert "358.0" in out
    assert "ES.v.0" in out


def test_the_key_never_enters_a_url(mod):
    """The key is transmitted as a Basic auth header, so nothing this module
    prints -- including an error containing a URL -- can leak it."""
    src = (REPO / "scripts" / "fetch_databento.py").read_text(encoding="utf-8")
    assert "key=" not in src.replace("api_key=", "")
    assert 'f"{BASE}/{path}"' in src
    assert "base64.b64encode" in src


def test_dataset_start_is_the_real_floor(mod):
    """GLBX.MDP3 begins 2010-06-06. Anything earlier does not exist to buy, so a
    span request reaching further back is a silent no-op, not an error."""
    assert mod.DATASET_START == "2010-06-06"
    assert mod.DATASET == "GLBX.MDP3"
