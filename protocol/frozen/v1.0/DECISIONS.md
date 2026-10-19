# Planning decisions and remaining definitions

19 October 2026

**Planning only. No frozen protocol, data acquisition, implementation, simulations, backtests or publication for this project.** This records the user's choices and distinguishes them from remaining technical recommendations.

The user accepted proceeding with the concrete universe proposal and the next technical definitions. [PROTOCOL-DRAFT.md](PROTOCOL-DRAFT.md) now consolidates that direction and supplies exact proposed formulas, uncertainty settings, simulation generators, seeds, portfolio diagnostics and failure rules. It is the current technical proposal for review; metadata/source verification and protocol freeze remain outstanding. The open-detail labels below record the earlier discussion state rather than overruling that consolidated draft.

## Choices confirmed in discussion

| Decision | Selected direction | Detail still to settle |
|---|---|---|
| Emphasis | Covariance estimation and sequential risk forecasts primary; portfolio consequences secondary. | Exact primary hypothesis and evaluation rules. |
| Shrinkage target | Diagonal target preserving individual sample variances. | Precise covariance/correlation representation and centering. |
| Intensity | Analytical Ledoit–Wolf rule rather than an evaluation-sample tuning search. | Exact formulation consistent with the diagonal target. |
| Returns | Adjusted simple returns. | Provider conventions, common mean treatment and calendar policy. |
| Window | Medium rolling window. | 252 returns is the current recommendation, not a frozen value. |
| Uncertainty | One primary method plus predefined sensitivity analysis. | HAC primary plus dependent-bootstrap sensitivity is recommended; lag/block rules, interval construction, repetitions and seeds remain open. |
| Portfolio scope | Simulation-based true risk plus historical weight diagnostics. | Exact metrics, constraints and update schedule; no executable historical P&L in this phase. |
| Reporting | Preserve and report valid negative/inconclusive outcomes and computational failures honestly. | Exact failure consequences and correction/versioning procedure. |
| Potential extension | Nonlinear eigenvalue shrinkage is of interest. | Future hypothesis only; not included in the first comparison or authorized for execution. |
| Universe | Proceed with the eight-product mixed-asset proposal for planning. | SPY, EFA, EEM, IEF, TLT, LQD, GLD, VNQ; issuer/history verification remains outstanding. |
| Primary score | User requested a recommendation. | Matrix Gaussian quasi-likelihood is recommended below. |

## Precise estimator proposal

Ordinary off-the-shelf Ledoit–Wolf applied directly to raw returns usually shrinks toward a scaled identity matrix, changing individual variance estimates. That is not the diagonal-preserving specification selected here.

The working proposal is:

1. Construct the sample matrix S under an explicit shared mean/normalization convention.
2. Let D contain training-window sample standard deviations.
3. Standardize only the current training observations and apply the analytical Ledoit–Wolf rule in standardized units.
4. Shrink the correlation estimate R toward I and rescale:

`Sigma_hat = D * ((1-delta)*R + delta*I) * D`

When the standardization and estimator conventions match, this is equivalent to:

`Sigma_hat = (1-delta)*S + delta*diag(S)`

Diagonal entries are preserved; off-diagonal entries are damped. All standardization and intensity estimation must use training observations only. This is Ledoit–Wolf on standardized observations followed by rescaling, not the conventional raw-return Ledoit–Wolf covariance estimator. Its analytical estimation-loss rationale does not guarantee optimality for our forecast score or portfolio risk. Exact formulas and finite-sample conventions must be reviewed before freezing the protocol.

A zero conditional mean remains a proposal. Under that assumption, raw sample second moments are interpreted as covariance. If a mean is estimated instead, the same mean forecast must be used for both estimators and the evaluation residuals.

## Why an ETF universe can be useful

A fixed, economically defined ETF universe can represent genuine allocation exposures: equity regions, duration, credit, gold and listed real estate. The instruments are investable even though an estimator study is not an executable investment-performance study.

The universe does not need to be novel. Its purpose is to make target assumptions and diversification consequences economically interpretable. The distinctive work is a clear estimand, controlled tests, honest uncertainty and an understandable account of where the method succeeds or fails.

Limits must remain visible: small dimension can mean little benefit from shrinkage; exposures overlap; currently selected ETFs do not reconstruct a survivorship-free historical opportunity set; US listings do not remove asynchronous underlying-market information. Claims remain conditional on the fixed universe and data conventions.

Known-covariance simulations complement the ETF case study by examining predefined dimension/sample-size ratios and structures. They should include circumstances where a diagonal target is imperfect. Increasing the historical universe after seeing weak shrinkage results would not be an acceptable response.

## Recommended primary score

Use the matrix version of the variance QLIKE score from the earlier forecasting project:

`L = log(det(Sigma_hat)) + e_next_transpose * inverse(Sigma_hat) * e_next`

Here e is the next return vector minus the shared declared mean forecast. Under a zero-mean convention, e equals the return vector. Lower scores are better.

The log-determinant term and quadratic term together discourage broadly inflated risk estimates and overly confident forecasts in directions where observed returns move. The score evaluates variances and correlations jointly without pretending the true daily covariance matrix is observed. It requires positive-definite estimates and appropriate mean/moment assumptions; choosing a Gaussian quasi-likelihood score does not establish Gaussian market returns.

The primary contrast is the paired mean shrinkage-minus-sample score. A better observed mean is not sufficient for a statistically supported improvement claim. Dependence-aware uncertainty is required.

Secondary simulation diagnostics can include estimation error against known covariance and the population variance of estimated portfolio weights. An oracle minimum-variance portfolio with access to the true covariance is an ideal mathematical benchmark, not an available investment strategy.

Historical weight diagnostics can include concentration, maximum weights and changes in target weights. Target-weight change must not be labelled executed turnover without modelling drifted holdings and execution.

## Primary inference and sensitivity

The recommended structure is a named primary HAC procedure and a predefined dependent-bootstrap sensitivity analysis for the same paired score difference. Neither lag/block length nor the decision rule is fixed yet. They need a rationale and controlled assessment before historical score inspection.

The primary method determines the primary inference. Sensitivity results are reported even when they disagree; a more favourable sensitivity result cannot replace the primary result. Two procedures on the same data are not independent replication, and neither automatically handles historical regime changes.

## Failure and preservation principles

| Outcome | Reporting and consequence |
|---|---|
| Valid result with no improvement | Publish the finding and interpretation; do not change the target, window, universe or metric to obtain a win. |
| Valid estimate with an interval spanning zero | Report inconclusive evidence under the predefined procedure; do not claim equivalence or proof of no effect. |
| Malformed input, missing required observations or changed data identity | Stop and preserve evidence; the dataset is not accepted until the stated input requirements are met. No silent fill or sample deletion. |
| Singular, indefinite or otherwise invalid forecast matrix | Record the affected method/date and preserve partial evidence. Apply the predeclared consequence; do not silently add ridge, omit the date or report an ordinary completed primary comparison. |
| Optimizer failure confined to secondary weights | Preserve the valid primary risk scores, report the secondary analysis as incomplete and record solver/constraint diagnostics. It does not automatically invalidate a separate, valid primary covariance comparison. |
| Code defect discovered | Preserve the original artifacts and specify the correction and outcome knowledge. A corrected execution requires a distinct documented version/run identity rather than overwriting the original. |

Computational failure can be informative about robustness, but it is not equivalent to valid evidence that forecasts are equal or that shrinkage has no benefit. Detailed tolerances, stopping points and any allowed fallback must be fixed before execution.

## Future nonlinear-shrinkage extension

A possible question is whether selectively adjusting estimated eigenvalues improves risk estimation beyond uniform correlation shrinkage. Small-eigenvalue errors can be amplified by inverse-covariance calculations, making this a meaningful hypothesis.

The effect depends on dimension, sample size, eigenvector estimation and constraints. A small ETF universe may offer limited benefit. Any future extension must specify whether it operates in covariance or correlation space, how variance scaling is handled, its comparison family and its known-baseline exploratory status. It must not be added simply to find a favourable result after the first comparison.

## Next planning work

The [universe proposal](UNIVERSE-PROPOSAL.md) provides the economic case. The [consolidated protocol draft](PROTOCOL-DRAFT.md) now defines the remaining technical choices. No historical results have been inspected.

1. Review the consolidated technical design and its limitations.
2. Verify issuer metadata and source/adjustment/redistribution conventions without score inspection.
3. Record any amendments, then freeze the protocol before authorized implementation or market-data acquisition.
