"""Fixed registered simulation cells, paths and uncertainty stress diagnostics."""

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
from scipy.signal import lfilter

from .core import NumericalFailure, accept, estimate, estimate_at, minimum_variance
from .inference import bootstrap_interval, hac_interval

STRUCTURES = ("diagonal", "common", "mixed_factor")
DISTRIBUTIONS = ("gaussian", "t8")


def clean(value):
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def write_json(path: Path, value):
    with path.open("x") as handle:
        json.dump(clean(value), handle, indent=2, allow_nan=False)
        handle.write("\n")


def rng_for(family, structure, distribution, dimension, replication):
    return np.random.Generator(
        np.random.PCG64(
            np.random.SeedSequence(
                41001, spawn_key=(family, structure, distribution, dimension, replication)
            )
        )
    )


def covariance(p: int, structure: int) -> np.ndarray:
    sd = np.resize(np.array([0.06, 0.12, 0.24]), p) / np.sqrt(252)
    if structure == 0:
        correlation = np.eye(p)
    elif structure == 1:
        correlation = 0.4 * np.eye(p) + 0.6 * np.ones((p, p))
    elif structure == 2:
        b = np.resize(np.array([[0.75, 0.10], [0.65, 0.25], [-0.30, 0.70], [-0.40, 0.55]]), (p, 2))
        correlation = b @ b.T + np.diag(1 - np.sum(b * b, axis=1))
    else:
        raise ValueError("Unregistered covariance structure")
    return sd[:, None] * correlation * sd[None, :]


def draw_returns(rng, n, factor, distribution):
    x = rng.standard_normal((n, len(factor))) @ factor.T
    if distribution == 1:
        x *= np.sqrt(6 / rng.chisquare(8, n))[:, None]
    elif distribution != 0:
        raise ValueError("Unregistered return distribution")
    return x


def describe(values) -> dict:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if not len(x):
        return {"n": 0}
    return {
        "n": len(x),
        "mean": float(x.mean()),
        "mcse": float(x.std(ddof=1) / np.sqrt(len(x))) if len(x) > 1 else None,
        "median": float(np.median(x)),
        "q05": float(np.quantile(x, 0.05)),
        "q95": float(np.quantile(x, 0.95)),
    }


def grid_cell(args):
    structure, distribution, p, destination = args
    destination = Path(destination)
    name = f"grid-s{structure}-d{distribution}-p{p}"
    truth = accept(covariance(p, structure))
    oracle = minimum_variance(truth.matrix)
    oracle_risk = float(oracle.weights @ truth.matrix @ oracle.weights) if oracle.valid else None
    records = []
    with (destination / f"{name}.jsonl").open("x") as handle:
        for rep in range(500):
            row = {
                "replication": rep,
                "structure": structure,
                "distribution": distribution,
                "p": p,
                "failures": [],
            }
            x = draw_returns(
                rng_for(0, structure, distribution, p, rep), 252, truth.chol, distribution
            )
            try:
                fitted = estimate(x)
                row["delta"] = fitted.intensity
                row["cancellation_clamped"] = fitted.cancellation_clamped
            except NumericalFailure as exc:
                row["failures"].append({"stage": "estimator", "error": str(exc)})
                records.append(row)
                handle.write(json.dumps(clean(row), allow_nan=False) + "\n")
                continue
            for method, matrix in (("sample", fitted.sample), ("shrinkage", fitted.shrinkage)):
                try:
                    accepted = accept(matrix)
                    portfolio = minimum_variance(matrix)
                    item = {
                        "condition": accepted.condition,
                        "frobenius": float(
                            np.sum((matrix - truth.matrix) ** 2) / np.sum(truth.matrix**2)
                        ),
                        "regret": accepted.expected_regret(truth),
                        "portfolio": asdict(portfolio),
                    }
                    if portfolio.valid:
                        risk = float(portfolio.weights @ truth.matrix @ portfolio.weights)
                        item.update(true_variance=risk, **portfolio.diagnostics())
                        if oracle_risk is not None:
                            ratio = risk / oracle_risk
                            if ratio < 1 - 1e-7:
                                row["failures"].append(
                                    {"stage": method + "_oracle_ratio", "ratio": ratio}
                                )
                            else:
                                item["risk_ratio"] = ratio
                    else:
                        row["failures"].append(
                            {"stage": method + "_optimizer", "message": portfolio.message}
                        )
                    row[method] = item
                except NumericalFailure as exc:
                    row["failures"].append({"stage": method + "_matrix", "error": str(exc)})
            equal = np.full(p, 1 / p)
            inverse = 1 / np.sqrt(np.diag(fitted.sample))
            inverse /= inverse.sum()
            row["references"] = {
                "equal_true_variance": float(equal @ truth.matrix @ equal),
                "inverse_vol_true_variance": float(inverse @ truth.matrix @ inverse),
            }
            records.append(row)
            handle.write(json.dumps(clean(row), allow_nan=False) + "\n")
    summary = {
        "cell": name,
        "structure": STRUCTURES[structure],
        "distribution": DISTRIBUTIONS[distribution],
        "p": p,
        "replications": 500,
        "failure_replications": sum(bool(row["failures"]) for row in records),
        "oracle": {**asdict(oracle), "true_variance": oracle_risk},
        "metrics": {},
    }
    for metric in (
        "frobenius",
        "regret",
        "true_variance",
        "risk_ratio",
        "concentration",
        "maximum_weight",
        "effective_number",
    ):
        pairs = [
            (row["sample"][metric], row["shrinkage"][metric])
            for row in records
            if metric in row.get("sample", {}) and metric in row.get("shrinkage", {})
        ]
        differences = [b - a for a, b in pairs]
        wins = sum(value < 0 for value in differences)
        summary["metrics"][metric] = {
            "sample": describe([a for a, _ in pairs]),
            "shrinkage": describe([b for _, b in pairs]),
            "paired_difference": describe(differences),
            "complete_pairs": len(pairs),
            "total_replications": 500,
            "negative_difference_fraction_total": wins / 500,
            "fraction_mcse": np.sqrt((wins / 500) * (1 - wins / 500) / 500),
        }
    summary["delta"] = describe([row["delta"] for row in records if "delta" in row])
    write_json(destination / f"{name}-summary.json", summary)
    return clean(summary)


def adaptation_path(args):
    distribution, replication, destination = args
    destination = Path(destination)
    first = accept(covariance(8, 1))
    second = accept(2.25 * covariance(8, 2))
    truths = (first, second)
    oracles = [minimum_variance(truth.matrix) for truth in truths]
    oracle_risks = [
        float(w.weights @ a.matrix @ w.weights) if w.valid else np.nan
        for w, a in zip(oracles, truths, strict=True)
    ]
    rng = rng_for(1, 3, distribution, 8, replication)
    g = rng.standard_normal((1512, 8))
    returns = np.empty_like(g)
    returns[:882] = g[:882] @ first.chol.T
    returns[882:] = g[882:] @ second.chol.T
    if distribution == 1:
        returns *= np.sqrt(6 / rng.chisquare(8, 1512))[:, None]
    arrays = {
        "scores": np.full((1260, 2), np.nan),
        "regrets": np.full((1260, 2), np.nan),
        "true_variances": np.full((1260, 2), np.nan),
        "risk_ratios": np.full((1260, 2), np.nan),
        "weights": np.full((1260, 2, 8), np.nan),
        "concentration": np.full((1260, 2), np.nan),
        "maximum_weight": np.full((1260, 2), np.nan),
        "conditions": np.full((1260, 2), np.nan),
        "delta": np.full(1260, np.nan),
        "reference_true_variances": np.full((1260, 2), np.nan),
        "oracle_true_variances": np.r_[
            np.full(630, oracle_risks[0]), np.full(630, oracle_risks[1])
        ],
    }
    failures = []
    for index in range(1260):
        origin = 252 + index
        truth = truths[int(index >= 630)]
        try:
            fitted = estimate_at(returns, origin)
            arrays["delta"][index] = fitted.intensity
        except NumericalFailure as exc:
            failures.append({"target": index, "stage": "estimator", "error": str(exc)})
            continue
        equal = np.full(8, 1 / 8)
        inverse = 1 / np.sqrt(np.diag(fitted.sample))
        inverse /= inverse.sum()
        arrays["reference_true_variances"][index] = [
            equal @ truth.matrix @ equal,
            inverse @ truth.matrix @ inverse,
        ]
        for method, matrix in enumerate((fitted.sample, fitted.shrinkage)):
            try:
                accepted = accept(matrix)
                arrays["conditions"][index, method] = accepted.condition
                arrays["scores"][index, method] = accepted.loss(returns[origin])
                arrays["regrets"][index, method] = accepted.expected_regret(truth)
            except NumericalFailure as exc:
                failures.append(
                    {"target": index, "method": method, "stage": "matrix", "error": str(exc)}
                )
                continue
            portfolio = minimum_variance(matrix)
            arrays["weights"][index, method] = portfolio.weights
            if not portfolio.valid:
                failures.append(
                    {
                        "target": index,
                        "method": method,
                        "stage": "optimizer",
                        "diagnostics": asdict(portfolio),
                    }
                )
                continue
            risk = float(portfolio.weights @ truth.matrix @ portfolio.weights)
            arrays["true_variances"][index, method] = risk
            arrays["concentration"][index, method] = portfolio.weights @ portfolio.weights
            arrays["maximum_weight"][index, method] = portfolio.weights.max()
            oracle_risk = oracle_risks[int(index >= 630)]
            if np.isfinite(oracle_risk):
                ratio = risk / oracle_risk
                if ratio < 1 - 1e-7:
                    failures.append(
                        {"target": index, "method": method, "stage": "oracle_ratio", "ratio": ratio}
                    )
                else:
                    arrays["risk_ratios"][index, method] = ratio
    stem = f"adaptation-d{distribution}-r{replication:03}"
    with (destination / f"{stem}.npz").open("xb") as handle:
        np.savez_compressed(handle, **arrays, returns=returns)
    result = {
        "distribution": distribution,
        "replication": replication,
        "failure_count": len(failures),
        "failures": failures,
        "oracle_valid": [oracle.valid for oracle in oracles],
        "segments": {},
    }
    for name, selection in (
        ("before", slice(0, 630)),
        ("after", slice(630, 1260)),
        ("transition", slice(630, 882)),
    ):
        segment = {}
        for metric in (
            "scores",
            "regrets",
            "true_variances",
            "risk_ratios",
            "concentration",
            "maximum_weight",
        ):
            x = arrays[metric][selection]
            complete = np.isfinite(x).all(axis=1)
            segment[metric] = {
                "targets": len(x),
                "complete_targets": int(complete.sum()),
                "sample_mean": float(x[complete, 0].mean()) if complete.any() else None,
                "shrinkage_mean": float(x[complete, 1].mean()) if complete.any() else None,
                "paired_mean": float((x[complete, 1] - x[complete, 0]).mean())
                if complete.any()
                else None,
            }
        result["segments"][name] = segment
    write_json(destination / f"{stem}.json", result)
    return clean(result)


def uncertainty_case(args):
    process, destination = args
    destination = Path(destination)
    records = []
    with (destination / f"uncertainty-{process}.jsonl").open("x") as handle:
        for rep in range(1000):
            rng = np.random.Generator(
                np.random.PCG64(np.random.SeedSequence(41003, spawn_key=(process, rep, 0)))
            )
            if process == 0:
                x = rng.standard_normal(5040)
            elif process == 1:
                initial = rng.standard_normal()
                innovations = rng.standard_normal(5039) * np.sqrt(0.75)
                tail, _ = lfilter([1], [1, -0.5], innovations, zi=[0.5 * initial])
                x = np.r_[initial, tail]
            else:
                eps = rng.standard_normal(5040 + 252)
                prefix = np.r_[0, np.cumsum(eps)]
                x = (prefix[253:] - prefix[:-253]) / np.sqrt(253)
            row = {"replication": rep, "process": process}
            try:
                row["hac"] = hac_interval(x)
            except NumericalFailure as exc:
                row["hac_failure"] = str(exc)
            if rep < 200:
                bootstrap_rng = np.random.Generator(
                    np.random.PCG64(np.random.SeedSequence(41003, spawn_key=(process, rep, 1)))
                )
                try:
                    row["bootstrap"] = bootstrap_interval(x, bootstrap_rng, 999)
                except NumericalFailure as exc:
                    row["bootstrap_failure"] = str(exc)
            records.append(row)
            handle.write(json.dumps(clean(row), allow_nan=False) + "\n")
    summary = {"process": ("iid", "ar1", "ma252")[process], "procedures": {}}
    for method, expected in (("hac", 1000), ("bootstrap", 200)):
        valid = [row[method] for row in records if method in row]
        covered = sum(ci["low"] <= 0 <= ci["high"] for ci in valid)
        rate = covered / expected
        summary["procedures"][method] = {
            "expected": expected,
            "valid": len(valid),
            "covered": covered,
            "coverage": rate,
            "coverage_mcse": float(np.sqrt(rate * (1 - rate) / expected)),
            "positive_rejections": sum(ci["low"] > 0 for ci in valid),
            "negative_rejections": sum(ci["high"] < 0 for ci in valid),
        }
    write_json(destination / f"uncertainty-{process}-summary.json", summary)
    return summary
