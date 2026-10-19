# Correlation shrinkage and portfolio risk: protocol draft

Version 0.1 — 19 October 2026

**Status: complete technical proposal for design review, not a frozen or executed experiment.** This consolidates the selected direction and supplies concrete technical defaults. No prices have been collected and no estimator, simulation or historical evaluation has been implemented for this project. Product metadata and data-provider details remain acceptance prerequisites. Earlier documents are discussion history; this document is the current proposed specification.

## 1. Question, mechanism and limits

For a fixed eight-product mixed-asset case study, does training-only analytical correlation shrinkage improve next-session multivariate risk forecasts relative to the sample second moment?

Estimated correlations contain noise. Reducing their magnitude can improve estimation and reduce an optimizer's reliance on spurious diversification. It can also destroy genuine positive dependence or negative hedge relationships. The experiment must allow either result. Individual variance estimates are identical between methods, so this is not a test of improved marginal volatility forecasts.

The primary estimand is the historical mean paired forecast-loss difference, shrinkage minus sample. Negative favours shrinkage. Portfolio diagnostics and known-truth simulations explain consequences; neither replaces the primary outcome. No return signal, investment alpha, executable P&L, or claim of universal estimator dominance is proposed.

## 2. Historical universe and inputs

Candidate order: **SPY, EFA, EEM, IEF, TLT, LQD, GLD, VNQ**. Economic roles and inclusion rules are in [UNIVERSE-PROPOSAL.md](UNIVERSE-PROPOSAL.md). This is a fixed-universe conditional case study, not a survivorship-free reconstruction of the investment opportunity set.

Proposed source: Yahoo Finance daily adjusted-close history, subject to documenting the actual retrieval interface, adjustment semantics and redistribution conditions before acquisition. No automatic substitute provider. Current issuer identity, inception, exposure and material benchmark/structure changes must be checked against issuer sources before accepting the universe. These checks must not inspect forecasting outcomes. If identity/history is unsuitable, document a design revision before implementation or score inspection.

| Setting | Proposed definition |
|---|---|
| Price dates | XNYS sessions from 2005-01-01 through 2025-12-31, inclusive |
| Target dates | Every XNYS session from 2007-01-01 through 2025-12-31, inclusive |
| Returns | Adjusted simple returns in decimal units, `r_t = P_adj,t / P_adj,t-1 - 1` |
| Window | Exactly 252 preceding return vectors, including the origin return |
| Horizon | Next XNYS session |
| Updates | Daily, for both methods |
| Conditional mean | Zero, shared by both methods and scoring |

XNYS means the specified historical exchange-session calendar, not weekdays. Pin the calendar package/version and save the accepted session index when implementation is authorized. Early-close sessions remain sessions. All products use the same complete index. A missing expected price is an input failure, not permission to redefine the next session, forward-fill, or create a multi-session daily return.

Require unique, ordered session labels; all required assets/sessions; finite positive prices; and finite returns. Preserve raw responses, retrieval timestamps, request settings, provider metadata and content hashes in an immutable local acquisition record. Preserve adjustment/corporate-action fields when available for diagnosis. Extreme finite moves are flagged for investigation, not winsorized or automatically removed. A confirmed bad value requires a documented corrected acquisition with a new identity; an unresolved one prevents accepting the dataset.

No full-sample normalization, return-based asset selection, pairwise deletion, evaluation-driven trimming or changes to dates/window. Adjusted histories can be revised and are not executable prices. USD listings do not eliminate foreign-market timing or currency exposures. Retrospective, past-only forecasts are not pristine unseen evidence.

## 3. Exact estimator definitions

Let the training matrix X have T=252 rows and p=8 columns, consisting only of returns known through origin t. Do not subtract a fitted sample mean. Define:

```
S = X'X / T
D = diag(sqrt(S_11), ..., sqrt(S_pp))
Z = X D^(-1)
R = Z'Z / T
mu = trace(R) / p
```

Under exact arithmetic, `diag(R)=1` and `mu=1`. S is a raw second moment, interpreted as covariance under the declared zero-conditional-mean approximation. The target of the chosen score is the conditional second moment; a nonzero actual conditional mean limits the covariance/portfolio interpretation.

**Baseline:** `Sigma_sample = S`.

**Candidate:** apply the conventional analytical scaled-identity Ledoit–Wolf rule to the already standardized Z with zero centering, then rescale. Fix the finite-sample formula as:

```
q = ||R - mu I||_F^2
b = (1/T) * [ (1/T) * sum_s ||z_s||_2^4 - ||R||_F^2 ]
if q = 0: delta = 1
otherwise: delta = min(1, max(0, b / q))

Sigma_shrink = D [(1-delta) R + delta I] D
             = (1-delta) S + delta diag(S)
```

The exact-zero branch has no effect on the resulting matrix because R is already I. No fitted tolerance around q=0 changes the rule. Nonpositive individual variances, nonfinite terms or a materially negative b are numerical/input failures. A negative b of absolute magnitude at most `1e-12 * max(1, (1/T)*sum_s ||z_s||^4)` may be set to zero as explicitly recorded floating-point cancellation handling. Clipping delta into [0,1] is part of the estimator, not a numerical repair selected after outcomes.

The candidate uses I in its final standardized target so individual variances remain exactly defined by S. mu occurs in the analytical intensity denominator; its difference from 1 must be only floating-point error. Require `max_i |R_ii-1| <= 1e-12`.

This is **Ledoit–Wolf on training-standardized observations, rescaled to a diagonal target**. It is not conventional Ledoit–Wolf on raw returns, nor a claim that this intensity is the oracle optimum for a random diagonal target, forecasting loss, or portfolio risk. Standardization itself is estimated from the same window. Its analytical rationale must not be presented as a dominance theorem under financial time variation.

Before any historical execution, implementation must reconcile this formula against a pinned reference implementation with centering disabled, including all scaling/normalization settings. Document the original Ledoit–Wolf reference and reference-library version in the eventual methods notes. A mismatch stops execution rather than silently adopting library defaults.

## 4. Forecast loss and hypothesis

For next-session target r and positive-definite forecast A:

```
L(A,r) = log(det(A)) + r' A^(-1) r
d_t = L(Sigma_shrink,t, r_t+1) - L(Sigma_sample,t, r_t+1)
```

Use Cholesky factorization and linear solves; do not explicitly invert matrices or compute an ordinary determinant. Both methods must have the same complete target set. No loss clipping. Large valid losses remain in the primary mean.

The Gaussian quasi-likelihood score is strictly consistent for a positive-definite conditional second moment under appropriate integrability. It does not require actual Gaussian returns. Under zero mean that second moment is covariance. No latent historical covariance is claimed observable.

The substantive improvement hypothesis is `E[d] < 0`; the no-improvement null is `E[d] >= 0`. Use the conservative predeclared decision of the **upper endpoint of a two-sided 95% primary interval being below zero**, rather than switching to a one-sided interval after observing outcomes. A positive lower endpoint supports worse forecasting under the same procedure. An interval spanning zero is inconclusive, not equivalence. Negative mean alone is only a descriptive improvement.

## 5. Dependence-aware uncertainty

Primary proposal: Newey–West HAC for the paired mean, Bartlett kernel, a fixed lag of **252 target sessions**, with normal critical value 1.959963984540054. For n complete loss differences and demeaned `u_t=d_t-mean(d)`:

```
gamma_k = (1/n) * sum_{t=k+1..n} u_t u_t-k
V = gamma_0 + 2 * sum_{k=1..252} (1-k/253) * gamma_k
SE = sqrt(V/n)
CI = mean(d) +/- 1.959963984540054 * SE
```

No fitted mean/intercept degrees-of-freedom multiplier. Require n>252. V must be finite and positive; otherwise inference is unavailable and the valid descriptive mean is preserved. No substitution of an independence standard error.

Rationale: one year is tied to the registered rolling window, not a convenient short default or a lag chosen to improve significance. Overlapping training windows can induce dependence but do not prove that dependence ends at 252 lags. Bartlett tapering and a long bandwidth have finite-sample bias/variance costs. Regime changes can invalidate stationary weak-dependence approximations. The interval is approximate, and a long history does not automatically provide thousands of independent observations.

Predefined sensitivity: **stationary bootstrap of the paired loss series**, 4,999 replications, expected block length 252, PCG64 seed 41002. Each resample has n indices: start uniformly, then with probability 1/252 restart uniformly and otherwise advance to the next original index, wrapping circularly. Resample d jointly as one paired series. For bootstrap means m_b, use the basic 95% interval `[2*m-q_0.975(m_b), 2*m-q_0.025(m_b)]`, with linear-interpolated empirical quantiles. This bootstraps stored losses, not a refitted market path.

Both procedures and settings are fixed together. Report both intervals and their disagreement. A favourable sensitivity cannot replace an unfavourable primary result. If the primary interval excludes zero but sensitivity does not, describe the primary result as supported under HAC but sensitive to the uncertainty procedure. Neither is independent replication or protection against arbitrary nonstationarity.

An uncertainty diagnostic, separate from estimator performance, will assess the registered procedures on known-mean synthetic score sequences: iid N(0,1); stationary AR(1) with rho=0.5 and innovation variance 0.75, initialized from N(0,1); and equal-weight MA(252), `d_t=sum_{j=0..252} eps_t-j / sqrt(253)`, with its required independent prehistory innovations generated. All have mean zero and unit marginal variance. Use n=5,040 and 1,000 replications for primary HAC coverage; run the bootstrap diagnostic on the first 200 replications using 999 resamples each. Diagnostic RNG is PCG64 with SeedSequence entropy 41003 and spawn_key `(process_id, replication, component)`, process IDs 0=iid, 1=AR, 2=MA, and component 0=sequence draws, 1=bootstrap draws. Report coverage, rejection direction and binomial Monte Carlo standard errors for every case. These are stress diagnostics, not proof of coverage for estimator losses. In particular, long overlapping dependence may expose poor finite-sample coverage; report that limitation, do not tune lag/block length to erase it or portray the interval as certified. Material calibration problems require qualified inference, not a replacement primary procedure.

## 6. Known-covariance simulations

Use a fixed factorial grid: dimensions **8, 32, 96**, T=252, three covariance structures and two return distributions. This is 18 cells with **500 independent training samples per cell**. No selected winning cells. At p=8 this matches historical dimension; larger p is a separate controlled sample-size challenge, not added historical assets.

For coordinate i, cycle annualized scales `(0.06, 0.12, 0.24)` and set daily scale `s_i=annual_scale/sqrt(252)`. Let A=diag(s). Define true Sigma=A C A using:

1. **Diagonal:** C=I. A favourable target case.
2. **Strong common correlation:** C=0.4 I + 0.6 11'. Shrinking genuine strong dependence can introduce substantial bias.
3. **Mixed-sign two-factor:** rows of B cycle `(0.75,0.10)`, `(0.65,0.25)`, `(-0.30,0.70)`, `(-0.40,0.55)`. Set `C=B B' + diag(1-row_sum(B^2))`. This is positive definite with unit diagonal and includes useful negative relationships.

Distributions:

- Gaussian: `r = chol(Sigma) g`, g standard multivariate normal.
- Multivariate Student t with 8 degrees of freedom: `r = chol(Sigma) g * sqrt(6/U)`, U independent chi-squared(8). The shared radial scale gives covariance exactly Sigma and finite fourth moments. Do not use unscaled t draws and call their scale matrix covariance.

These are stylized mathematical return models, not executable price processes. For each independent training sample, record:

- Relative squared covariance Frobenius error, `||estimate-Sigma||_F^2 / ||Sigma||_F^2`.
- Expected Gaussian-score regret, `logdet(estimate)-logdet(Sigma)+trace(solve(estimate,Sigma))-p`. Known truth removes next-return noise; this is not the historical observable score.
- True variance of estimated long-only GMV weights and the ratio to the true-covariance oracle minimum variance under the same constraints.
- Shrinkage intensity, concentration, maximum weight and numerical failures.

Summarize paired differences with Monte Carlo standard errors `sd(paired differences)/sqrt(M)`; also report medians and fixed 5th/95th percentiles as distribution descriptions. For failure/win proportions report binomial standard errors; M=500 gives at most about 2.24 percentage points per such standard error. Failure counts remain in each cell denominator; incomplete paired means must show their denominator and cannot be called complete-cell superiority. These are descriptive mechanism studies, not 18 primary hypothesis tests.

Add one predefined adaptation challenge at p=8: 252 initialization returns plus 1,260 scored returns, with the true covariance changing after scored return 630 from common-correlation Sigma to **2.25 times** mixed-factor Sigma (1.5 times each volatility). Generate 200 independent paths for each of Gaussian and t8 distributions. Refit on trailing windows every origin. Score against the next return and evaluate expected regret and portfolio true risk using the covariance of that next return. Summarize both halves and the first 252 targets after the switch, with path-level Monte Carlo uncertainty. This is a deliberate abrupt-change stress, not a model of every market crisis.

Use NumPy PCG64 and base SeedSequence entropy 41001, with spawn_key `(family, structure, distribution, dimension, replication)`. Family IDs: 0=independent-training grid, 1=adaptation paths. Structure IDs: 0=diagonal, 1=common correlation, 2=mixed factor, 3=registered adaptation switch. Distribution IDs: 0=Gaussian, 1=t8. Dimension is the actual p and replication is zero-indexed. Publish this mapping and library version so skipping a cell does not change another cell's draws. Inference diagnostic and historical bootstrap seeds are separate. No optional stopping or extra replications triggered by an unfavourable result.

## 7. Portfolio diagnostics

For each valid estimated matrix, solve `min_w w' A w`, with `w_i>=0` and `sum(w)=1`. No shorts, leverage, expected-return forecast, or caps added after concentration is observed. Reference allocations are equal weight and inverse sample standard deviation, normalized to sum to one. Inverse volatility is not generally risk parity.

Historical weights are calculated **at the final session of each calendar month from January 2007 through December 2025**, using only returns through that session; save the training endpoint. No subsequent return is needed for these diagnostics, including the final December 2025 origin. They are mathematical target diagnostics, not fills or subsequent returns. Compare concentration `sum(w_i^2)`, effective number `1/sum(w_i^2)`, maximum weight, and successive target distance `0.5*sum(abs(w_m-w_m-1))`. No first-month target distance. The latter is not executed turnover because drifted holdings are absent. Pairwise sample/shrinkage comparisons require the same monthly origins; failures remain visible.

Low-volatility bonds can dominate a legitimate minimum-variance objective even with known truth. Concentration is not by itself evidence of estimation failure. Simulations use an oracle under identical constraints to separate the objective from estimation error.

Proposed solver: SciPy SLSQP, equal-weight initialization, objective scaled by `trace(A)` for numerical units, analytic gradient, `ftol=1e-12`, maximum 2,000 iterations. Pin implementation/library versions before execution. Independently check simplex feasibility and first-order optimality; a success flag alone is insufficient. No second solver selected because it yields nicer weights.

## 8. Numerical acceptance and failures

Before scoring either matrix, require all values finite, positive diagonal, relative symmetry residual at most 1e-12, successful Cholesky factorization, and spectral condition number at most 1e12. Compute symmetry residual relative to Frobenius norm, with zero norm invalid. No added ridge, eigenvalue clipping, silent symmetry repair, pseudoinverse, or dropped score date. The finite condition threshold is an explicit acceptance boundary, not proof of mathematical singularity.

For scaled optimizer objective `w' A w / trace(A)`, require raw returned weights `min(w)>=-1e-10` and `|sum(w)-1|<=1e-8`. Any tolerated negative numerical weight must be recorded and must not be silently clipped or renormalized. For diagnostic reporting retain raw solver weights and identify tolerance-level feasibility; do not describe approximate numerical feasibility as exact arithmetic feasibility.

Let g be the analytic scaled gradient and `lambda=sum_i w_i*g_i`. For entries w_i>1e-7 require `|g_i-lambda|<=1e-7`; for remaining entries require `g_i-lambda>=-1e-7`. These KKT checks are necessary independent validation of the convex optimum alongside feasibility. An oracle risk ratio below `1-1e-7` is a numerical validation failure requiring investigation, not superior-to-oracle performance.

| Failure | Consequence |
|---|---|
| Missing/invalid required input | Stop before forecasts; preserve acquisition and rejection reason. No shortened primary dataset. |
| Invalid/nonaccepted primary matrix or score | Log method/date/diagnostics; stop historical run, preserve partial ledger. No ordinary completed primary inference from the surviving dates. |
| Invalid HAC variance | Preserve complete valid losses and mean; primary interval unavailable, no significance claim or substituted method. |
| Bootstrap failure | Record incomplete sensitivity; retain independently valid primary outputs and state limitation. |
| Secondary optimizer/KKT failure | Preserve primary scores; record failed secondary origin/cell, without imputed weights or concealed denominator changes. |
| Simulation estimator failure | Preserve replication, count in total, continue other registered replications; affected paired summaries explicitly incomplete. |
| Code defect | Preserve original version/run; document correction, known outcomes and distinct rerun identity. Never overwrite failed evidence. |

No estimator fallback is part of this protocol. A robust sample-plus-fallback system would be a different comparison.

## 9. Implementation verification and evidence, after authorization

Required substantive checks: hand-calculable diagonal/two-asset examples; intensity formula against a compatible reference; preservation of sample diagonals; scale/sign transformation consistency; past-only timing and one-session indexing; known-covariance expected-score identity; t8 covariance scaling; and feasibility/KKT/oracle risk checks. Verify Monte Carlo and bootstrap reproducibility under reordered task execution. Use synthetic fixtures before exposing any historical losses. Do not build tests that merely restate implementation output.

Each eventual run records protocol/code/dependency/data identities, settings, seeds, expected and actual target counts, failure records and complete paired ledgers. Preserve all valid negative, positive and inconclusive results. Publish summaries, figures and reproducible code only within verified data redistribution permissions; raw provider data need not be public.

Nonlinear eigenvalue shrinkage remains a separately specified future extension. Do not add it, change the target/window, select historical regimes or try additional estimators to rescue this comparison. Existing volatility research and other frozen/prospective programmes remain outside scope.

## 10. Remaining prerequisites and sequence

1. Review this technical proposal as a whole, including its approximate inference and fixed-universe limitations.
2. Verify issuer metadata and source adjustment/retrieval/redistribution conventions without inspecting return outcomes; record references and any resulting design amendments.
3. Settle any amendments, assign a frozen protocol identity and record the approval/date before implementation or market-data acquisition.
4. Once implementation is authorized: build and verify on synthetic fixtures, run the registered simulations and uncertainty diagnostics, then execute the historical comparison under the recorded design. Any conclusions about interval reliability must acknowledge diagnostic shortcomings; no result-driven retuning.

The present work completes the technical planning draft. It does not claim product metadata verification, numerical correctness of unwritten code, completed simulations, historical findings, or publication.
