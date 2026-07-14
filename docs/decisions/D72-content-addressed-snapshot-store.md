# D72 — Content-addressed SnapshotStore; quarantine semantics; meta refreshes on re-freeze

**Status:** Committed
**Date:** 2026-07-14
**Category:** Data layer
**Source:** Implementation session (Step 7)

## Decision

`data.snapshot_store.SnapshotStore` (D24): `snapshot_id = sha256(bars.csv bytes +
events.json bytes)` — content-addressed. Same data re-frozen → same id (idempotent;
this is what makes a results doc's snapshot_id reproducible from a committed
fixture); a yfinance history restatement → new id, with no version counter to
maintain. `load()` re-hashes and refuses on mismatch (byte-identical or nothing) and
raises `QuarantinedSnapshotError` for snapshots whose validation had hard violations
— quarantined data cannot reach the engine by any default path (D26, Pillar 1);
`allow_quarantined=True` exists for inspection only.

**Meta is provenance, not identity**: `meta.json` (cleaning report, validation
outcome, fetch metadata) is not hashed, and re-freezing identical content refreshes
it. Learned the hard way in this very session: the first v2 freeze was quarantined by
a validator bug (see D74); after the fix, an identity-included-meta or
never-refresh-meta design would have left the correct data permanently locked behind
a stale quarantine flag. The validator version recorded in meta says what judged the
data; the payload hash says what the data is. Those are different facts.

## Rationale

Content addressing makes D24's whole requirement list fall out of one mechanism —
immutability (any byte change is a new identity), the checksum gate, restatement
detection, and reproducibility — instead of maintaining a registry of version
numbers that could drift from the bytes they describe. Storage reuses the existing
`csv_fixture` format and `data/snapshots/` has been gitignored since the day-one
.gitignore: snapshots are local artifacts; committed fixtures are how data enters
the repo.
