"""Registered HAC and stationary-bootstrap uncertainty; no automatic tuning."""

import numpy as np
from scipy.fft import irfft, next_fast_len, rfft

from .core import NumericalFailure


def hac_interval(values: np.ndarray, lag: int = 252) -> dict:
    x = np.asarray(values, dtype=float)
    n = len(x)
    if n <= lag or not np.isfinite(x).all():
        raise NumericalFailure("Insufficient or nonfinite HAC series")
    mean = float(x.mean())
    u = x - mean
    size = next_fast_len(2 * n - 1)
    transform = rfft(u, size)
    gamma = irfft(transform * transform.conj(), size)[: lag + 1] / n
    weights = 1 - np.arange(1, lag + 1) / (lag + 1)
    variance = float(gamma[0] + 2 * weights @ gamma[1:])
    if not np.isfinite(variance) or variance <= 0:
        raise NumericalFailure("Invalid HAC long-run variance")
    se = float(np.sqrt(variance / n))
    width = 1.959963984540054 * se
    return {
        "mean": mean,
        "se": se,
        "low": mean - width,
        "high": mean + width,
        "long_run_variance": variance,
        "lag": lag,
        "n": n,
    }


def stationary_means(
    values: np.ndarray, rng: np.random.Generator, replications: int, expected_length: int = 252
) -> np.ndarray:
    """Geometric circular blocks: exact stationary-bootstrap law using block sums.

    Every resample starts uniformly. Geometric block lengths implement independent
    restart probability 1/L at every next index; prefix sums avoid materializing
    billions of individual indices. This resamples stored paired losses only.
    """
    x = np.asarray(values, dtype=float)
    n = len(x)
    if n == 0 or not np.isfinite(x).all() or replications < 1 or expected_length < 1:
        raise NumericalFailure("Invalid bootstrap input")
    prefix = np.r_[0.0, np.cumsum(np.tile(x, 2))]
    remaining = np.full(replications, n, dtype=int)
    sums = np.zeros(replications)
    while np.any(remaining):
        active = np.flatnonzero(remaining)
        starts = rng.integers(0, n, len(active))
        lengths = np.minimum(rng.geometric(1 / expected_length, len(active)), remaining[active])
        sums[active] += prefix[starts + lengths] - prefix[starts]
        remaining[active] -= lengths
    return sums / n


def bootstrap_interval(
    values: np.ndarray, rng: np.random.Generator, replications: int, expected_length: int = 252
) -> dict:
    means = stationary_means(values, rng, replications, expected_length)
    lower, upper = np.quantile(means, [0.025, 0.975], method="linear")
    mean = float(np.mean(values))
    return {
        "mean": mean,
        "low": float(2 * mean - upper),
        "high": float(2 * mean - lower),
        "replications": replications,
        "expected_length": expected_length,
    }
