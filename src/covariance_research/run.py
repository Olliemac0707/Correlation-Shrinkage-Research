"""Execute all frozen synthetic scenarios; preserve immutable run evidence."""

import argparse
import hashlib
import json
import platform
import shutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from threadpoolctl import threadpool_limits

from .report import render
from .simulation import adaptation_path, grid_cell, uncertainty_case, write_json

EXPECTED_PROTOCOL_HASH = "72a337fd2b8093952cfc3cd00d82f35bb03c7d0bd4a1aaa9b4e0c4d960fa53da"


def now():
    return datetime.now(timezone.utc).isoformat()


def initialize_worker():
    # Four CPUs are available; one BLAS thread per independent worker avoids oversubscription.
    global _thread_limit
    _thread_limit = threadpool_limits(limits=1)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(output: Path, workers: int):
    project = Path(__file__).resolve().parents[2]
    planning = project / "protocol"
    frozen = planning / "frozen/v1.0"
    if digest(frozen / "manifest.json") != EXPECTED_PROTOCOL_HASH:
        raise RuntimeError("Frozen protocol manifest identity changed")
    protocol = json.loads((frozen / "manifest.json").read_text())
    for item in protocol["files"]:
        if digest(frozen / item["path"]) != item["sha256"]:
            raise RuntimeError("Frozen planning document changed: " + item["path"])
    if output.exists():
        raise FileExistsError("Refusing to overwrite run directory")
    output.mkdir(parents=True)
    source = output / "source"
    files = sorted(
        [
            *project.glob("src/**/*.py"),
            *project.glob("tests/**/*.py"),
            project / "pyproject.toml",
            project / "requirements-lock.txt",
        ]
    )
    hashes = {}
    for path in files:
        relative = path.relative_to(project)
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        hashes[str(relative)] = digest(path)
    shutil.copytree(frozen, output / "protocol")
    shutil.copyfile(planning / "AMENDMENT-A1.md", output / "AMENDMENT-A1.md")
    manifest = {
        "started_at_utc": now(),
        "python": platform.python_version(),
        "protocol_id": "correlation-shrinkage-v1.0",
        "protocol_manifest_sha256": EXPECTED_PROTOCOL_HASH,
        "amendment_sha256": digest(planning / "AMENDMENT-A1.md"),
        "source_hashes": hashes,
        "source_identity_sha256": hashlib.sha256(
            json.dumps(hashes, sort_keys=True).encode()
        ).hexdigest(),
        "workers": workers,
        "blas_threads_per_worker": 1,
        "registered_counts": {
            "grid_cells": 18,
            "grid_replications_per_cell": 500,
            "adaptation_paths_per_distribution": 200,
            "adaptation_targets_per_path": 1260,
            "uncertainty_processes": 3,
            "hac_repetitions_per_process": 1000,
            "bootstrap_repetitions_per_process": 200,
            "bootstrap_resamples_per_diagnostic": 999,
        },
        "historical_status": "not_executed_by_synthetic_runner",
    }
    write_json(output / "run-manifest.json", manifest)
    grid_dir, adaptation_dir, uncertainty_dir = [
        output / item for item in ("grid", "adaptation", "uncertainty")
    ]
    for directory in (grid_dir, adaptation_dir, uncertainty_dir):
        directory.mkdir()
    grid, paths, uncertainty = [], [], []
    print(json.dumps({"event": "started", "output": str(output), "time": now()}), flush=True)
    try:
        with ProcessPoolExecutor(max_workers=workers, initializer=initialize_worker) as pool:
            futures = {}
            for structure in range(3):
                for distribution in range(2):
                    for p in (8, 32, 96):
                        future = pool.submit(grid_cell, (structure, distribution, p, str(grid_dir)))
                        futures[future] = "grid"
            for process in range(3):
                futures[pool.submit(uncertainty_case, (process, str(uncertainty_dir)))] = (
                    "uncertainty"
                )
            for distribution in range(2):
                for replication in range(200):
                    future = pool.submit(
                        adaptation_path, (distribution, replication, str(adaptation_dir))
                    )
                    futures[future] = "adaptation"
            for future in as_completed(futures):
                kind = futures[future]
                result = future.result()
                if kind == "grid":
                    grid.append(result)
                    print(
                        json.dumps(
                            {
                                "event": "grid_complete",
                                "cell": result["cell"],
                                "completed": len(grid),
                                "failure_replications": result["failure_replications"],
                            }
                        ),
                        flush=True,
                    )
                elif kind == "uncertainty":
                    uncertainty.append(result)
                    print(json.dumps({"event": "uncertainty_complete", **result}), flush=True)
                else:
                    paths.append(result)
                    if len(paths) % 20 == 0:
                        print(
                            json.dumps(
                                {
                                    "event": "adaptation_progress",
                                    "completed": len(paths),
                                    "expected": 400,
                                }
                            ),
                            flush=True,
                        )
        if (len(grid), len(paths), len(uncertainty)) != (18, 400, 3):
            raise RuntimeError("Registered counts incomplete")
        if any(digest(project / relative) != value for relative, value in hashes.items()):
            raise RuntimeError("Source modified during execution")
        render(output, grid, paths, uncertainty)
        artifacts = {
            str(path.relative_to(output)): digest(path)
            for path in sorted(output.rglob("*"))
            if path.is_file()
        }
        write_json(output / "artifact-manifest.json", artifacts)
        write_json(
            output / "completion.json",
            {
                "completed_at_utc": now(),
                "status": "complete",
                "grid_cells": len(grid),
                "adaptation_paths": len(paths),
                "uncertainty_processes": len(uncertainty),
                "artifact_count": len(artifacts),
            },
        )
        print(json.dumps({"event": "complete", "output": str(output), "time": now()}), flush=True)
    except BaseException as exc:
        write_json(output / "execution-failure.json", {"time": now(), "error": repr(exc)})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4, choices=(1, 2, 3, 4))
    args = parser.parse_args()
    run(args.output.resolve(), args.workers)


if __name__ == "__main__":
    main()
