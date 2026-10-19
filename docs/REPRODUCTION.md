# Reproduction and evidence boundaries

## Install and verify offline

From the repository root, using Python 3.12:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check src tests tools
.venv/bin/python tools/check_publication.py
.venv/bin/python -m covariance_research.demo --output results/demo
```

Tests and the demonstration use synthetic fixtures and do not fetch prices or rerun historical studies. The small two-asset demonstration is a software integration check, not evidence for the registered research hypothesis. Existing output directories are rejected rather than overwritten.

## Full registered synthetic experiment

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m covariance_research.run --output results/new-synthetic-run --workers 4
.venv/bin/python tools/audit_run.py results/new-synthetic-run --output audits/new-synthetic-audit.json
```

This runs all 18 cells with 500 training samples each, 400 adaptation paths and the frozen uncertainty diagnostics. It can take several minutes. Random streams depend on immutable cell/path identities, not worker order. [Published summaries](results/synthetic/summary.json) are the original recorded outcomes, not CI-generated demonstrations.

## Historical reproduction

Raw Yahoo responses, accepted price panels, detailed historical return/forecast ledgers and full local run directories are not distributed. Their redistribution rights have not been established. A fresh download can differ from the accepted snapshot, so historical numerical reproduction is conditional on source identity; do not describe a new snapshot as a pristine holdout.

Acquisition is an explicit separate command:

```bash
.venv/bin/python -m covariance_research.historical acquire --output data/new-acquisition
```

Review `validation.json`, the corporate-action evidence and any extreme-move flags against the [frozen input policy](../protocol/frozen/v1.0/PROTOCOL-DRAFT.md). Missing sessions, invalid identity or prices must be resolved before acceptance; no silent repair, fill, deletion or ticker substitution. Preserve rejected attempts. Write a nonempty `INPUT-REVIEW.md` inside the acquisition directory describing the checks and unresolved limits. An extreme move is a review flag, not permission to remove it.

After that review, record acceptance explicitly. This snippet does not perform the review for you:

```python
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

directory = Path("data/new-acquisition")
review = directory / "INPUT-REVIEW.md"
if not review.exists() or not review.read_text().strip():
    raise RuntimeError("Document the input review before accepting this snapshot")
validation = json.loads((directory / "validation.json").read_text())
if not validation["complete_calendar"]:
    raise RuntimeError("Calendar validation did not pass")
record = {
    "status": "accepted",
    "accepted_at_utc": datetime.now(timezone.utc).isoformat(),
    "outcome_knowledge": "Reproduction after the original results were published",
    "hashes": {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.iterdir()) if path.is_file()
    },
}
with (directory / "DATA-ACCEPTANCE.json").open("x") as handle:
    json.dump(record, handle, indent=2)
```

Then run and audit, preserving all outputs:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m covariance_research.historical run --data data/new-acquisition --output results/new-historical-run
.venv/bin/python tools/audit_historical.py --run results/new-historical-run --data data/new-acquisition --output audits/new-historical-audit.json
```

The current audit records whether intervals span zero without requiring a particular outcome. A changed-snapshot interval can legitimately differ; investigate and record that distinction rather than editing the published result to match. The original audit source remains preserved with its execution record.

## What the public evidence can establish

Selected run reports, aggregate numerical summaries, audit receipts, execution manifests and original-source archives are in `docs/results/`. Their bytes are preserved and checked by the publication verifier. Full local artifact manifests also list omitted files; an audit receipt is a record of checks performed against the complete local run, not proof that every check can be repeated using only this public subset.

The original source archives identify the exact execution code. Current entry points package the protocol locally, add the offline demonstration and remove stale synthetic-only status wording. No scientific method or recorded result is changed by those publication adjustments. Source archives are provenance records, not installed dependencies.

The figures show derived research summaries. No raw provider-price files, environments, credentials or unrelated research streams are included. Scientific and numerical limitations remain in the reports; neither CI success nor matching hashes certifies inference calibration or an economic claim.
