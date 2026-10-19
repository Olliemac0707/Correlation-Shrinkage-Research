import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal
from sklearn.covariance import ledoit_wolf

from covariance_research.core import (
    NumericalFailure,
    accept,
    estimate,
    estimate_at,
    minimum_variance,
)
from covariance_research.inference import hac_interval, stationary_means
from covariance_research.simulation import covariance, draw_returns, rng_for


@pytest.mark.parametrize("p", [2, 8, 32, 96])
@pytest.mark.parametrize("structure", [0, 1, 2])
def test_intensity_matches_independent_reference(p, structure):
    truth = covariance(p, structure)
    x = draw_returns(np.random.default_rng(47), 252, np.linalg.cholesky(truth), 0)
    fit = estimate(x)
    sd = np.sqrt(np.diag(fit.sample))
    reference, intensity = ledoit_wolf(x / sd, assume_centered=True)
    assert_allclose(fit.intensity, intensity, atol=2e-12, rtol=2e-12)
    assert_allclose(fit.shrinkage, reference * sd[:, None] * sd[None, :], atol=1e-15, rtol=2e-12)
    assert_allclose(np.diag(fit.shrinkage), np.diag(fit.sample), rtol=2e-15)


def test_hand_calculable_diagonal_case_and_zero_variance_rejection():
    x = np.array([[1.0, 0.0], [-1.0, 0.0], [0.0, 2.0], [0.0, -2.0]])
    fit = estimate(x)
    assert_allclose(fit.sample, np.diag([0.5, 2]))
    assert_allclose(fit.shrinkage, fit.sample)
    assert fit.intensity == 1
    with pytest.raises(NumericalFailure):
        estimate(np.zeros((252, 2)))


def test_scaling_and_sign_transformations_preserve_intensity():
    x = np.random.default_rng(8).normal(size=(252, 8))
    scale = np.array([-0.1, 0.7, 3.0, -2.0, 5.0, 1.0, 0.9, 2.0])
    a, b = estimate(x), estimate(x * scale)
    assert_allclose(a.intensity, b.intensity)
    assert_allclose(b.shrinkage, scale[:, None] * a.shrinkage * scale[None, :])


def test_forecast_uses_exactly_previous_252_observations():
    x = np.random.default_rng(27).normal(size=(400, 8))
    initial = estimate_at(x, 300)
    changed = x.copy()
    changed[:48] *= 400
    changed[300:] *= 500
    after = estimate_at(changed, 300)
    assert_array_equal(initial.sample, after.sample)
    assert_array_equal(initial.shrinkage, after.shrinkage)
    assert_allclose(initial.sample, x[48:300].T @ x[48:300] / 252)
    with pytest.raises(NumericalFailure):
        estimate_at(x, 251)


def test_score_and_expected_regret_against_exact_moment_quadrature():
    truth = accept(np.array([[2.0, 0.4], [0.4, 1.0]]))
    prediction = accept(np.array([[1.5, 0.1], [0.1, 0.8]]))
    points = np.concatenate([np.sqrt(2) * truth.chol.T, -np.sqrt(2) * truth.chol.T])
    observed = np.mean([prediction.loss(point) - truth.loss(point) for point in points])
    assert_allclose(observed, prediction.expected_regret(truth), atol=1e-14)
    assert_allclose(truth.expected_regret(truth), 0, atol=1e-14)
    assert prediction.expected_regret(truth) >= 0


@pytest.mark.parametrize(
    "a",
    [
        np.ones((2, 2)),
        np.diag([1.0, 1e-13]),
        np.array([[1.0, 0.2], [0.1, 1.0]]),
        np.diag([1.0, np.nan]),
    ],
)
def test_invalid_matrices_fail_without_repairs(a):
    with pytest.raises(NumericalFailure):
        accept(a)


@pytest.mark.parametrize("a", [np.diag([1.0, 4.0]), np.array([[1.0, -0.2], [-0.2, 2.0]])])
def test_solver_matches_analytical_two_asset_optimum(a):
    result = minimum_variance(a)
    exact_first = (a[1, 1] - a[0, 1]) / (a[0, 0] + a[1, 1] - 2 * a[0, 1])
    assert result.valid
    assert_allclose(result.weights, [exact_first, 1 - exact_first], atol=2e-7)
    oracle_risk = result.weights @ a @ result.weights
    for w in ([1, 0], [0, 1], [0.5, 0.5]):
        assert np.array(w) @ a @ np.array(w) >= oracle_risk - 1e-10


def test_hac_fft_matches_direct_registered_formula():
    x = np.array([1.0, -2.0, 4.0, 3.0, -1.0, 0.3])
    u = x - x.mean()
    gamma = [u @ u / 6, u[1:] @ u[:-1] / 6, u[2:] @ u[:-2] / 6]
    expected = gamma[0] + 2 * ((2 / 3) * gamma[1] + (1 / 3) * gamma[2])
    result = hac_interval(x, lag=2)
    assert_allclose(result["long_run_variance"], expected, atol=1e-14)
    with pytest.raises(NumericalFailure):
        hac_interval(np.zeros(5040))


def test_bootstrap_prefix_sums_match_explicit_block_resampling():
    x = np.array([2.0, -1.0, 8.0, 4.0, -3.0])
    first = stationary_means(x, np.random.default_rng(189), 19, 3)
    rng = np.random.default_rng(189)
    indices = [[] for _ in range(19)]
    while any(len(items) < len(x) for items in indices):
        active = [i for i, items in enumerate(indices) if len(items) < len(x)]
        starts = rng.integers(0, len(x), len(active))
        lengths = rng.geometric(1 / 3, len(active))
        for rep, start, length in zip(active, starts, lengths, strict=True):
            length = min(length, len(x) - len(indices[rep]))
            indices[rep].extend((start + np.arange(length)) % len(x))
    explicit = np.array([x[items].mean() for items in indices])
    assert_allclose(first, explicit, atol=1e-14)


def test_t8_generator_has_covariance_not_unadjusted_scale():
    truth = covariance(8, 2)
    x = draw_returns(np.random.default_rng(1234), 100000, np.linalg.cholesky(truth), 1)
    second = x.T @ x / len(x)
    assert np.linalg.norm(second - truth) / np.linalg.norm(truth) < 0.035


def test_registered_rng_streams_do_not_depend_on_execution_order():
    a = rng_for(0, 2, 1, 32, 9).normal(size=20)
    rng_for(0, 1, 0, 8, 2).normal(size=100)
    b = rng_for(0, 2, 1, 32, 9).normal(size=20)
    assert_array_equal(a, b)
    assert not np.array_equal(a, rng_for(0, 2, 1, 32, 10).normal(size=20))
