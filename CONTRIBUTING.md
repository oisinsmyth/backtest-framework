# Contributing

Thanks for taking an interest. Bug reports, questions and pull requests are all welcome.

## Setup

You need Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/oisinsmyth/backtest-framework.git
cd backtest-framework
uv sync
```

## Checks

CI runs these on every pull request, and a pull request needs all of them to pass:

```bash
uv run ruff check src tests examples scripts
uv run mypy
uv run pytest -q
```

It also runs the three scripts in `examples/`.

## Tests

- Every behaviour change comes with a test.
- Anything that moves money (a cost brick, a fill rule, carry, dividends, splits) belongs in
  `tests/golden/`. Work the expected numbers out by hand first, without importing this package,
  and record the arithmetic in the matching `.hand.txt` file next to the test. If the code and
  the hand ledger disagree, fix the code.
- A test that checks an argument is passed through should also check that the argument changes
  the result in its scenario. Otherwise it passes whether or not the argument is used.
- The default test run is offline. Tests that call a network data source are marked
  `live_fetch` and run with `uv run pytest -m live_fetch`.

## Pull requests

- Branch from `main` and keep each pull request to one change.
- Write commit messages as short imperative subjects ("Add borrow fee brick"), with a body only
  when the reason is not obvious from the diff.
- `main` is protected: changes go in through a pull request once CI passes.

## Style

- `ruff` and `mypy` settings are in `pyproject.toml`.
- Docstrings start with a one-line summary. Include units, sign conventions and when a function
  raises; leave out history.
- Raise on missing or invalid inputs rather than falling back to a default. A cost model that
  quietly returns zero produces a result that looks valid.

## Reporting a problem

Use the issue templates. For a wrong number, include the smallest input that reproduces it and
the value you expected. For a security issue, see [`SECURITY.md`](SECURITY.md).
