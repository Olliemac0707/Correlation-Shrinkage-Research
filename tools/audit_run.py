"""Recompute selected scientific outputs independently of the implementation.

Run after completion. This is a Codex arithmetic/provenance audit, not an
independent scientific review. No experiment settings or artifacts are changed.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from numpy.testing import assert_allclose
from sklearn.covariance import ledoit_wolf


def true_covariance(p, structure):
    scales = np.array(([0.06, 0.12, 0.24] * (p // 3 + 1))[:p]) / np.sqrt(252)
    if structure == 0:
        corr = np.eye(p)
    elif structure == 1:
        corr = np.full((p, p), 0.6)
        np.fill_diagonal(corr, 1)
    else:
        loadings = np.array(
            ([(0.75, 0.1), (0.65, 0.25), (-0.3, 0.7), (-0.4, 0.55)] * (p // 4 + 1))[:p]
        )
        corr = loadings @ loadings.T
        np.fill_diagonal(corr, 1)
    return np.diag(scales) @ corr @ np.diag(scales)


def pair(x):
    sample = x.T @ x / len(x)
    sd = np.sqrt(np.diag(sample))
    standardized, intensity = ledoit_wolf(x / sd, assume_centered=True)
    return sample, sd[:, None] * standardized * sd[None, :], intensity


def audit(run: Path):
    completion = json.loads((run / "completion.json").read_text())
    assert completion["status"] == "complete"
    artifacts = json.loads((run / "artifact-manifest.json").read_text())
    for relative, expected in artifacts.items():
        assert hashlib.sha256((run / relative).read_bytes()).hexdigest() == expected, relative
    cells = sorted((run / "grid").glob("*.jsonl"))
    assert len(cells) == 18
    matrix_pairs = 0
    selected_rows = 0
    valid_portfolio_pairs = 0
    for path in cells:
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        assert len(rows) == 500
        assert [row["replication"] for row in rows] == list(range(500))
        matrix_pairs += sum(
            "regret" in row.get("sample", {}) and "regret" in row.get("shrinkage", {})
            for row in rows
        )
        valid_portfolio_pairs += sum(
            "risk_ratio" in row.get("sample", {}) and "risk_ratio" in row.get("shrinkage", {})
            for row in rows
        )
        for row in (rows[0], rows[-1]):
            p, structure, distribution, rep = [
                row[key] for key in ("p", "structure", "distribution", "replication")
            ]
            truth = true_covariance(p, structure)
            rng = np.random.Generator(
                np.random.PCG64(
                    np.random.SeedSequence(41001, spawn_key=(0, structure, distribution, p, rep))
                )
            )
            x = rng.normal(size=(252, p)) @ np.linalg.cholesky(truth).T
            if distribution:
                x *= np.sqrt(6 / rng.chisquare(8, 252))[:, None]
            sample, shrink, delta = pair(x)
            assert_allclose(delta, row["delta"], atol=2e-12, rtol=2e-12)
            truth_logdet = np.linalg.slogdet(truth)[1]
            for name, estimated in (("sample", sample), ("shrinkage", shrink)):
                item = row[name]
                regret = (
                    np.linalg.slogdet(estimated)[1]
                    - truth_logdet
                    + np.trace(np.linalg.solve(estimated, truth))
                    - p
                )
                assert_allclose(regret, item["regret"], atol=2e-10, rtol=2e-10)
                error = np.linalg.norm(estimated - truth) ** 2 / np.linalg.norm(truth) ** 2
                assert_allclose(error, item["frobenius"], atol=2e-12, rtol=2e-12)
                weights = np.array(item["portfolio"]["weights"])
                if item["portfolio"]["valid"]:
                    assert_allclose(weights @ truth @ weights, item["true_variance"], rtol=1e-12)
            selected_rows += 1
    path_files = sorted((run / "adaptation").glob("*.npz"))
    assert len(path_files) == 400
    complete_scores = 0
    checked_forecasts = 0
    true_first = true_covariance(8, 1)
    true_second = 2.25 * true_covariance(8, 2)
    for path in path_files:
        with np.load(path) as data:
            assert data["returns"].shape == (1512, 8)
            assert data["scores"].shape == (1260, 2)
            complete_scores += int(np.isfinite(data["scores"]).all(axis=1).sum())
            for target in (0, 630, 881, 1259):
                training = data["returns"][target : target + 252]
                next_return = data["returns"][target + 252]
                sample, shrink, delta = pair(training)
                assert_allclose(delta, data["delta"][target], atol=2e-12, rtol=2e-12)
                for method, matrix in enumerate((sample, shrink)):
                    direct = np.linalg.slogdet(matrix)[1] + next_return @ np.linalg.solve(
                        matrix, next_return
                    )
                    assert_allclose(direct, data["scores"][target, method], atol=2e-9, rtol=2e-10)
                checked_forecasts += 1
            weights = data["weights"]
            risks = np.empty((1260, 2))
            risks[:630] = np.einsum("tmi,ij,tmj->tm", weights[:630], true_first, weights[:630])
            risks[630:] = np.einsum("tmi,ij,tmj->tm", weights[630:], true_second, weights[630:])
            mask = np.isfinite(data["true_variances"])
            assert_allclose(risks[mask], data["true_variances"][mask], atol=1e-16, rtol=1e-12)
    uncertainty = sorted((run / "uncertainty").glob("*.jsonl"))
    assert len(uncertainty) == 3
    uncertainty_counts = []
    for path in uncertainty:
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        assert len(rows) == 1000
        assert sum("bootstrap" in row for row in rows) == 200
        process = rows[0]["process"]
        rng = np.random.Generator(
            np.random.PCG64(np.random.SeedSequence(41003, spawn_key=(process, 0, 0)))
        )
        if process == 0:
            values = rng.normal(size=5040)
        elif process == 1:
            values = np.empty(5040)
            values[0] = rng.normal()
            eps = rng.normal(size=5039) * np.sqrt(0.75)
            for index in range(1, 5040):
                values[index] = 0.5 * values[index - 1] + eps[index - 1]
        else:
            eps = rng.normal(size=5292)
            values = np.convolve(eps, np.ones(253) / np.sqrt(253), mode="valid")
        residuals = values - values.mean()
        variance = residuals @ residuals / 5040
        for lag in range(1, 253):
            variance += 2 * (1 - lag / 253) * (residuals[lag:] @ residuals[:-lag]) / 5040
        assert_allclose(variance, rows[0]["hac"]["long_run_variance"], rtol=2e-12)
        uncertainty_counts.append({"process": process, "hac": 1000, "bootstrap": 200})
    return {
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed",
        "artifact_hashes_verified": len(artifacts),
        "grid_samples": 9000,
        "complete_grid_matrix_pairs": matrix_pairs,
        "complete_grid_portfolio_risk_pairs": valid_portfolio_pairs,
        "independently_recomputed_grid_samples": selected_rows,
        "adaptation_paths": 400,
        "complete_adaptation_score_pairs": complete_scores,
        "expected_adaptation_score_pairs": 504000,
        "independently_recomputed_adaptation_forecasts": checked_forecasts,
        "uncertainty_registered_counts": uncertainty_counts,
        "scope": "Codex arithmetic/provenance audit, not independent scientific review",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.run)
    result["audit_script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result, indent=2))
