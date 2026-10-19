"""Training-only estimators, matrix scores and independently checked portfolios."""

from dataclasses import dataclass

import numpy as np
from scipy.linalg import cho_solve, cholesky
from scipy.optimize import minimize


class NumericalFailure(ValueError):
    """A registered numerical acceptance condition was not satisfied."""


@dataclass
class Estimates:
    sample: np.ndarray
    shrinkage: np.ndarray
    intensity: float
    cancellation_clamped: bool


def estimate(x: np.ndarray) -> Estimates:
    """Zero-centered second moments and standardized Ledoit–Wolf intensity."""
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or x.shape[0] < 2 or not np.isfinite(x).all():
        raise NumericalFailure("Invalid training matrix")
    t, p = x.shape
    sample = x.T @ x / t
    sd = np.sqrt(np.diag(sample))
    if not np.isfinite(sd).all() or np.any(sd <= 0):
        raise NumericalFailure("Nonpositive or nonfinite training variance")
    z = x / sd
    corr = z.T @ z / t
    if np.max(np.abs(np.diag(corr) - 1)) > 1e-12:
        raise NumericalFailure("Standardization diagonal mismatch")
    mu = np.trace(corr) / p
    q = float(np.sum((corr - mu * np.eye(p)) ** 2))
    fourth = float(np.mean(np.sum(z * z, axis=1) ** 2))
    b = (fourth - float(np.sum(corr * corr))) / t
    clamped = b < 0
    if b < -1e-12 * max(1, fourth):
        raise NumericalFailure("Materially negative intensity numerator")
    b = max(b, 0.0)
    delta = 1.0 if q == 0 else float(np.clip(b / q, 0, 1))
    shrinkage = (1 - delta) * sample + delta * np.diag(np.diag(sample))
    return Estimates(sample, shrinkage, delta, clamped)


def estimate_at(returns: np.ndarray, target: int, window: int = 252) -> Estimates:
    if target < window or target >= len(returns):
        raise NumericalFailure("Invalid forecast target index")
    return estimate(returns[target - window : target])


@dataclass
class AcceptedMatrix:
    matrix: np.ndarray
    chol: np.ndarray
    logdet: float
    condition: float

    def loss(self, target: np.ndarray) -> float:
        value = float(self.logdet + target @ cho_solve((self.chol, True), target))
        if not np.isfinite(value):
            raise NumericalFailure("Nonfinite forecast loss")
        return value

    def expected_regret(self, truth: "AcceptedMatrix") -> float:
        value = float(
            self.logdet
            - truth.logdet
            + np.trace(cho_solve((self.chol, True), truth.matrix))
            - len(self.matrix)
        )
        if not np.isfinite(value):
            raise NumericalFailure("Nonfinite expected score")
        return value


def accept(matrix: np.ndarray) -> AcceptedMatrix:
    a = np.asarray(matrix, dtype=float)
    if a.ndim != 2 or a.shape[0] != a.shape[1] or not np.isfinite(a).all():
        raise NumericalFailure("Nonfinite or nonsquare matrix")
    norm = np.linalg.norm(a, "fro")
    if norm == 0 or np.any(np.diag(a) <= 0):
        raise NumericalFailure("Nonpositive diagonal or zero matrix")
    if np.linalg.norm(a - a.T, "fro") / norm > 1e-12:
        raise NumericalFailure("Symmetry acceptance failed")
    try:
        factor = cholesky(a, lower=True)
        eigenvalues = np.linalg.eigvalsh(a)
    except np.linalg.LinAlgError as exc:
        raise NumericalFailure("Positive-definiteness failure") from exc
    if eigenvalues[0] <= 0:
        raise NumericalFailure("Nonpositive eigenvalue")
    condition = float(eigenvalues[-1] / eigenvalues[0])
    if condition > 1e12:
        raise NumericalFailure(f"Condition acceptance failed: {condition}")
    return AcceptedMatrix(a, factor, float(2 * np.log(np.diag(factor)).sum()), condition)


@dataclass
class Portfolio:
    weights: np.ndarray
    valid: bool
    solver_success: bool
    message: str
    iterations: int
    sum_error: float
    minimum_weight: float
    active_kkt_error: float
    inactive_kkt_margin: float

    def diagnostics(self) -> dict:
        concentration = float(self.weights @ self.weights)
        return {
            "concentration": concentration,
            "effective_number": 1 / concentration,
            "maximum_weight": float(self.weights.max()),
        }


def minimum_variance(a: np.ndarray) -> Portfolio:
    """Registered SLSQP settings; raw weights retained, with no repair/fallback."""
    scaled = a / np.trace(a)
    p = len(a)
    result = minimize(
        lambda w: float(w @ scaled @ w),
        np.full(p, 1 / p),
        jac=lambda w: 2 * scaled @ w,
        method="SLSQP",
        bounds=[(0, None)] * p,
        constraints={"type": "eq", "fun": lambda w: w.sum() - 1, "jac": lambda w: np.ones_like(w)},
        options={"ftol": 1e-12, "maxiter": 2000},
    )
    w = result.x
    g = 2 * scaled @ w
    level = w @ g
    active = w > 1e-7
    active_error = float(np.max(np.abs(g[active] - level))) if active.any() else np.inf
    inactive_margin = float(np.min(g[~active] - level)) if (~active).any() else np.inf
    sum_error = float(abs(w.sum() - 1))
    minimum = float(w.min())
    valid = bool(
        result.success
        and np.isfinite(w).all()
        and minimum >= -1e-10
        and sum_error <= 1e-8
        and active_error <= 1e-7
        and inactive_margin >= -1e-7
    )
    return Portfolio(
        w,
        valid,
        bool(result.success),
        str(result.message),
        int(result.nit),
        sum_error,
        minimum,
        active_error,
        inactive_margin,
    )
