"""An offline software demonstration, not another registered research result."""

import argparse
from pathlib import Path

import numpy as np
from numpy.testing import assert_allclose

from .core import accept, estimate, minimum_variance
from .simulation import write_json


def run(output: Path):
    # Orthogonal two-asset fixture, with an analytical diagonal GMV solution.
    x = np.array([[1.0, 0.0], [-1.0, 0.0], [0.0, 2.0], [0.0, -2.0]]) / 100
    fitted = estimate(x)
    sample, shrinkage = accept(fitted.sample), accept(fitted.shrinkage)
    portfolio = minimum_variance(fitted.shrinkage)
    if not portfolio.valid:
        raise RuntimeError("Analytical demonstration portfolio failed acceptance")
    assert_allclose(fitted.sample, np.diag([0.00005, 0.0002]), atol=1e-16)
    assert_allclose(portfolio.weights, [0.8, 0.2], atol=2e-7)
    assert_allclose(shrinkage.expected_regret(sample), 0, atol=1e-12)
    output.mkdir(parents=True, exist_ok=False)
    write_json(
        output / "demo.json",
        {
            "purpose": "offline integration check, not empirical or registered simulation evidence",
            "training_rows": len(x),
            "assets": 2,
            "sample": fitted.sample,
            "shrinkage": fitted.shrinkage,
            "delta": fitted.intensity,
            "accepted_weights": portfolio.weights,
            "portfolio_valid": portfolio.valid,
        },
    )
    print("Verified estimator, positive-definite scoring and analytical GMV weights [0.8, 0.2].")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)
