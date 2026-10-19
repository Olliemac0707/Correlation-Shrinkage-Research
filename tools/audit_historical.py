"""Full arithmetic/provenance audit of historical outputs using direct solves.

Codex audit only, not independent scientific validation or calibrated inference.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from numpy.testing import assert_allclose
from sklearn.covariance import ledoit_wolf


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reference_fit(x):
    sample = x.T @ x / len(x)
    sd = np.sqrt(np.diag(sample))
    fitted, intensity = ledoit_wolf(x / sd, assume_centered=True)
    return sample, fitted * sd[:, None] * sd[None, :], intensity


def audit(run, data):
    artifacts = json.loads((run / "artifact-manifest.json").read_text())
    for name, value in artifacts.items():
        assert sha(run / name) == value, name
    data_acceptance = json.loads((data / "DATA-ACCEPTANCE.json").read_text())
    assert data_acceptance["status"] == "accepted"
    for name, value in data_acceptance["hashes"].items():
        assert sha(data / name) == value, name
    manifest = json.loads((run / "run-manifest.json").read_text())
    assert sha(data / "DATA-ACCEPTANCE.json") == manifest["data_acceptance_sha256"]
    for name, value in manifest["source_hashes"].items():
        assert sha(run / "source" / name) == value
    panel = np.load(data / "prices.npz")
    prices, dates = panel["prices"], panel["dates"].tolist()
    returns = (prices[1:] - prices[:-1]) / prices[:-1]
    return_dates = dates[1:]
    expected = [i for i, day in enumerate(return_dates) if "2007-01-01" <= day <= "2025-12-31"]
    ledger = [json.loads(line) for line in (run / "paired-scores.jsonl").read_text().splitlines()]
    with np.load(run / "forecasts.npz") as compressed:
        forecasts = {key: compressed[key] for key in compressed.files}
    assert len(ledger) == len(expected) == 4780
    assert forecasts["matrices"].shape == (4780, 2, 8, 8)
    recomputed = []
    maximum_loss_error = 0.0
    maximum_condition = 0.0
    for index, (target, row) in enumerate(zip(expected, ledger, strict=True)):
        assert row["target_date"] == return_dates[target]
        assert row["origin_date"] == return_dates[target - 1]
        assert row["training_start_return_date"] == return_dates[target - 252]
        assert row["training_end_return_date"] == return_dates[target - 1]
        assert forecasts["target_dates"][index] == row["target_date"]
        sample, shrink, intensity = reference_fit(returns[target - 252 : target])
        assert_allclose(intensity, row["delta"], atol=3e-12, rtol=3e-12)
        assert_allclose(forecasts["target_returns"][index], returns[target], atol=3e-16, rtol=1e-10)
        losses = []
        for method, (name, matrix) in enumerate((("sample", sample), ("shrinkage", shrink))):
            assert_allclose(forecasts["matrices"][index, method], matrix, atol=1e-16, rtol=5e-10)
            sign, logdet = np.linalg.slogdet(matrix)
            assert sign == 1
            loss = logdet + returns[target] @ np.linalg.solve(matrix, returns[target])
            maximum_loss_error = max(maximum_loss_error, abs(loss - row[name + "_loss"]))
            assert_allclose(loss, row[name + "_loss"], atol=3e-9, rtol=1e-10)
            condition = np.linalg.cond(matrix)
            assert condition <= 1e12
            maximum_condition = max(maximum_condition, condition)
            losses.append(loss)
        assert_allclose(np.diag(sample), np.diag(shrink), atol=1e-16, rtol=5e-12)
        assert_allclose(losses[1] - losses[0], row["difference"], atol=3e-9, rtol=1e-8)
        recomputed.append(losses[1] - losses[0])
    differences = np.array(recomputed)
    summary = json.loads((run / "summary.json").read_text())
    assert_allclose(differences.mean(), summary["mean_difference"], atol=3e-10, rtol=1e-10)
    centered = differences - differences.mean()
    variance = centered @ centered / len(centered)
    for lag in range(1, 253):
        variance += 2 * (1 - lag / 253) * (centered[lag:] @ centered[:-lag]) / len(centered)
    se = np.sqrt(variance / len(centered))
    assert_allclose(se, summary["hac"]["se"], atol=3e-10, rtol=1e-10)
    assert_allclose(
        [differences.mean() - 1.959963984540054 * se, differences.mean() + 1.959963984540054 * se],
        [summary["hac"]["low"], summary["hac"]["high"]],
        atol=3e-10,
        rtol=1e-10,
    )
    monthly = [
        json.loads(line) for line in (run / "monthly-weights.jsonl").read_text().splitlines()
    ]
    expected_monthly = [
        i
        for i, day in enumerate(return_dates)
        if "2007-01-01" <= day <= "2025-12-31"
        and (i + 1 == len(return_dates) or day[:7] != return_dates[i + 1][:7])
    ]
    assert len(monthly) == len(expected_monthly) == 228
    valid_counts = {"sample": 0, "shrinkage": 0}
    for month, (origin, row) in enumerate(zip(expected_monthly, monthly, strict=True)):
        assert row["origin_date"] == return_dates[origin]
        assert row["training_start_return_date"] == return_dates[origin - 251]
        sample, shrink, _ = reference_fit(returns[origin - 251 : origin + 1])
        for name, matrix in (("sample", sample), ("shrinkage", shrink)):
            item = row["methods"][name]
            result = item["solver"]
            w = np.array(result["weights"])
            gradient = 2 * matrix @ w / np.trace(matrix)
            level = w @ gradient
            active = w > 1e-7
            active_error = np.max(np.abs(gradient[active] - level)) if active.any() else np.inf
            inactive_margin = np.min(gradient[~active] - level) if (~active).any() else np.inf
            valid = (
                result["solver_success"]
                and w.min() >= -1e-10
                and abs(w.sum() - 1) <= 1e-8
                and active_error <= 1e-7
                and inactive_margin >= -1e-7
            )
            assert bool(valid) == result["valid"]
            if valid:
                valid_counts[name] += 1
                assert_allclose(item["concentration"], w @ w, atol=1e-15)
            previous = monthly[month - 1]["methods"][name] if month else None
            adjacent_valid = bool(valid and previous and previous["solver"]["valid"])
            assert ("target_distance" in item) == adjacent_valid
            if adjacent_valid:
                assert_allclose(
                    item["target_distance"],
                    0.5 * np.abs(w - previous["solver"]["weights"]).sum(),
                    atol=1e-15,
                )
        inverse = 1 / np.sqrt(np.diag(sample))
        inverse /= inverse.sum()
        assert_allclose(row["methods"]["inverse_vol"]["weights"], inverse, atol=2e-13)
        assert_allclose(row["methods"]["equal"]["weights"], np.full(8, 1 / 8), atol=1e-15)
    for name, valid in valid_counts.items():
        assert 228 - valid == summary["portfolio_failures"][name]
    assert monthly[-1]["origin_date"] == "2025-12-31"
    primary_spans_zero = summary["hac"]["low"] <= 0 <= summary["hac"]["high"]
    sensitivity_spans_zero = summary["bootstrap"]["low"] <= 0 <= summary["bootstrap"]["high"]
    return {
        "status": "passed",
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_hashes_verified": len(artifacts),
        "input_hashes_verified": len(data_acceptance["hashes"]),
        "forecast_targets_recomputed": len(ledger),
        "monthly_origins_checked": len(monthly),
        "maximum_direct_loss_discrepancy": maximum_loss_error,
        "maximum_matrix_condition": maximum_condition,
        "valid_monthly_weights": valid_counts,
        "primary_interval_spans_zero": primary_spans_zero,
        "sensitivity_interval_spans_zero": sensitivity_spans_zero,
        "scope": "Codex arithmetic/provenance audit, not independent scientific review",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.run, args.data)
    result["audit_script_sha256"] = sha(Path(__file__))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result, indent=2))
