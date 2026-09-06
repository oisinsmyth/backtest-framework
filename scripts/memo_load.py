"""memo_load -- execute each script in the `_load` chain ONCE per process.

    import memo_load; memo_load.install()      # before the first _load(...)

Every runner since D290 imports its predecessor with the same four lines:

    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    spec.loader.exec_module(m)

Nothing in that pattern memoises, so a D349 process executed `d285_spread_estimate.py`
151 times, `d290_build_cache.py` and `run_mine_neutral.py` 54 times each, and paid
164 s of import alone (460 s with six processes competing) and ~5 GB of resident
memory before a single array of its own was built (D348 prep, 2026-09-06).

`install()` wraps `importlib.util.spec_from_file_location` and `module_from_spec` so
that a second request for the SAME FILE (resolved, case-normalised path under
`scripts/`) returns the module object already executed, and its `exec_module` is a
no-op. Aliases differ (`d335`, `d335r`, ...) and all now bind the same object -- which
is what a normal `import` would have given. Module-level state such as
`run_d306_width_exits.BASE_HOLD` is therefore SHARED across every alias in the
process; that is the intended semantics (a runner sets `W.BASE_HOLD = k` once and
every function reading it sees it) and the reason this must be guarded by identity
checks against numbers produced without it (D348 [ID] to 0.0 against D346/D343;
`d348_prep.py --verify` against a cache built without memoisation).

Only files under `<repo>/scripts` are memoised; everything else is untouched.
`stats()` reports how many executions were skipped.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

_MEMO: dict[str, object] = {}
_SKIPPED: dict[str, int] = {}
_INSTALLED = False
_SCRIPTS = os.path.normcase(str((Path(__file__).resolve().parent)))


def _key(origin):
    if not origin:
        return None
    p = os.path.normcase(os.path.abspath(str(origin)))
    return p if p.startswith(_SCRIPTS + os.sep) else None


class _MemoLoader:
    """Delegates to the real loader the first time a file is executed; no-op after."""

    def __init__(self, inner, key):
        self._inner, self._key = inner, key

    def create_module(self, spec):
        return self._inner.create_module(spec)

    def exec_module(self, module):
        if self._key in _MEMO:
            if _MEMO[self._key] is not module:
                raise RuntimeError(f"memo_load: exec_module on a second module object for {self._key}")
            _SKIPPED[self._key] = _SKIPPED.get(self._key, 0) + 1
            return
        self._inner.exec_module(module)
        _MEMO[self._key] = module

    def __getattr__(self, item):                      # get_source, get_code, is_package, ...
        return getattr(self._inner, item)


def install():
    global _INSTALLED
    if _INSTALLED:
        return
    orig_sfl = importlib.util.spec_from_file_location
    orig_mfs = importlib.util.module_from_spec

    def spec_from_file_location(name, location=None, *args, **kwargs):
        spec = orig_sfl(name, location, *args, **kwargs)
        k = _key(getattr(spec, "origin", None)) if spec is not None else None
        if k is not None and spec.loader is not None and not isinstance(spec.loader, _MemoLoader):
            spec.loader = _MemoLoader(spec.loader, k)
        return spec

    def module_from_spec(spec):
        k = _key(getattr(spec, "origin", None))
        if k is not None and k in _MEMO:
            return _MEMO[k]
        return orig_mfs(spec)

    importlib.util.spec_from_file_location = spec_from_file_location
    importlib.util.module_from_spec = module_from_spec
    _INSTALLED = True


def stats():
    return {"executed": len(_MEMO), "skipped": int(sum(_SKIPPED.values())),
            "most_skipped": sorted(((v, os.path.basename(k)) for k, v in _SKIPPED.items()), reverse=True)[:5]}
