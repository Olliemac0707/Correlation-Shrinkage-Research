# Covariance estimation and portfolio construction

Planning draft — 18 October 2026

**Historical discussion draft.** The current consolidated technical proposal is [PROTOCOL-DRAFT.md](PROTOCOL-DRAFT.md), written 19 October 2026. Its diagonal-preserving estimator, simple returns, eight-product universe, dates and proposed statistical settings supersede unresolved alternatives here. No protocol is frozen or executed.

Options reviewed 19 October 2026: see [options and trade-offs](OPTIONS-AND-TRADEOFFS.md). Recommendations remain provisional.

The subsequent [decision record](DECISIONS.md) records the user's selected diagonal target, analytical Ledoit–Wolf rule, simple adjusted returns, medium rolling window, primary-plus-sensitivity inference and secondary portfolio scope. It distinguishes those choices from technical definitions still requiring review. Where this earlier draft presents multiple targets, the decision record is the latest planning position.

**Status: design discussion only. Not a frozen protocol or authorization to acquire data, implement estimators, or run simulations/backtests.**

## 1. Agreed objective

The user selected quantitative research as the emphasis: covariance estimation and sequential risk forecasting are primary; portfolio outcomes are secondary.

The central question is:

> Does a predefined covariance shrinkage estimator improve next-session multivariate risk forecasts relative to the sample estimator, and what consequences does the estimator have for minimum-variance portfolio construction?

This is a study of estimation error and decisions made from estimated risk. It is not an expected-return signal, a search for the highest Sharpe ratio, or evidence that a particular allocation is universally optimal.

## 2. Economic motivation

Diversification depends on variances and covariances. Their estimates contain noise, which optimisation can amplify through unstable or concentrated weights. Shrinkage deliberately exchanges some flexibility for lower estimation variance.

Improving matrix estimation and improving a portfolio are distinct questions. A change in the full covariance matrix may have little effect on the exposures chosen by an optimiser. Conversely, lower realised portfolio volatility may reflect a larger bond exposure rather than a better estimate.

With a small ETF universe and a long enough estimation window, sample covariance may already be adequate. A null result is acceptable. We will not increase dimensions, shorten windows or change targets after inspecting historical losses simply to create a favourable shrinkage result.

## 3. Proposed primary comparison

One candidate-versus-baseline contrast only:

- Baseline: sample second-moment/covariance estimate under the common declared mean assumption.
- Candidate: one analytically estimated Ledoit–Wolf shrinkage specification, with its exact target and asset scaling fixed before evaluation.

The primary estimand is the mean paired candidate-minus-baseline forecast-loss difference. Negative favours the candidate. The initial project will not compare a menu of shrinkage targets, covariance models or lookback windows and select a winner from the evaluation sample.

A conventional candidate worth discussing is shrinkage toward a scaled identity matrix:

`Sigma_hat = (1 - delta) * S + delta * mu * I`

where `mu = trace(S) / N` and delta is estimated analytically from training observations, rather than selected by searching evaluation losses.

This target shrinks both variances and covariances. On a mixed-asset universe it pulls individual variances toward a common level, which is an economically meaningful assumption. An alternative is shrinkage on standardized returns followed by rescaling, preserving individual variance estimates while shrinking correlations. These are different estimators. We must settle one before freezing the design and must not describe a result for one as a conclusion about shrinkage in general.

## 4. Return target and score

Updated recommendation after the options review: daily adjusted simple close-to-close returns for US-listed ETFs sharing a trading calendar. Simple returns map directly to the variance of weighted portfolio returns; weighted asset log returns would require an approximation. A zero conditional mean is a manageable first-version assumption, but it is an approximation, not a fact.

If zero mean is adopted, `S = (1/T) * sum(r * r_transpose)` estimates a second-moment matrix. Under the assumption this is interpreted as conditional covariance. The candidate's centering and normalization must match that definition. A library's default demeaning must not silently change the estimand.

Proposed primary score:

`L = log(det(Sigma_hat)) + r_next_transpose * inverse(Sigma_hat) * r_next`

This is a Gaussian quasi-likelihood score. It requires positive-definite forecast matrices, a common return definition and an explicit mean treatment. It is not a portfolio return. A normal return distribution is not automatically established by choosing this score.

Implementation, if later authorized, should use stable factorization and linear solves rather than explicitly forming an inverse or naively taking a determinant. Numerical repairs must not silently regularize the sample baseline into a different estimator.

## 5. Evidence layers

### Controlled simulation

Use a small, predefined collection of known covariance structures to verify mathematical behaviour and investigate estimation error. Proposed structures include unequal asset variances with moderate correlations and a simple factor covariance structure. Sample-size effects can be investigated using a registered grid, rather than selecting scenarios after seeing results.

Known population covariance permits direct assessment of matrix estimation error and the true variance of estimated portfolio weights. Monte Carlo uncertainty and repeated-sample behaviour should be reported. Synthetic scenarios are methodological demonstrations, not market evidence or a proof that an estimator will dominate under real data.

The exact generator, dimension/sample-size grid, seeds, repetitions and summary measures remain to be specified. They must not be chosen to favour the candidate.

### Historical sequential evaluation

Use a small universe justified by economic exposures and inception/data availability, rather than past performance. A proposed universe would represent US equities, developed international equities, emerging-market equities, intermediate and longer Treasury exposure, investment-grade credit, gold and listed real estate. Exact instruments and dates remain open.

US-listed instruments simplify session alignment but do not eliminate differences in underlying-market trading hours, stale pricing, overlapping exposures, liquidity or data revision. A fixed ETF set is a conditional case study, not a survivorship-free reconstruction of all historical investment opportunities.

All estimates must use only observations available through their forecast origin. Historical targets must be identical across methods. These can be past-only sequential forecasts while the overall study remains retrospective on familiar market history. Do not describe the evaluation as pristine unseen evidence.

## 6. Secondary portfolio component

The optimisation objective is minimum estimated variance subject to nonnegative weights summing to one. These are mathematical target weights, not automatically a whole-share executable portfolio.

Proposed allocations:

| Allocation | Purpose |
|---|---|
| Equal weights | Transparent allocation benchmark without estimated covariance. |
| Inverse-volatility weights | Uses individual risk estimates while ignoring correlations; not generally full risk parity. |
| Sample-estimate minimum variance | Isolates the conventional optimiser using the baseline estimator. |
| Shrinkage-estimate minimum variance | Changes the risk estimator while retaining the same optimisation constraints. |

The first-version recommendation is to emphasize mathematical weights, concentration, stability and true risk in controlled simulations. A historical allocation analysis is secondary and must be specified before examining its outcomes. It must not select a covariance estimator from whichever portfolio happens to look best.

If executable historical portfolio outcomes are included, independently settle decision time, execution price, rebalancing frequency, whole-share sizing, starting capital, residual cash, interest, distributions and costs. Close-based estimates must not be assigned impossible same-close fills. Adjusted closes are return-analysis inputs, not directly executable security prices. A comparison of idealized risk exposures must be labelled as such.

## 7. Uncertainty and decision rules

The primary analysis uses paired losses on common dates and an uncertainty procedure that addresses serial dependence. Rolling estimation windows overlap; observations must not be treated as independent without justification.

HAC inference or a dependent bootstrap are candidates, not yet a frozen choice. The exact dependence assumptions, lag/block rule and confidence-interval construction require a written rationale. Simulation can check performance under declared generating processes, but cannot certify coverage under real historical nonstationarity.

One primary contrast avoids a specification-search family in the first version. Secondary matrix and portfolio descriptions must not become replacement primary outcomes when the registered result is inconclusive. A better point estimate alone does not establish improvement; lack of significance does not establish equivalence.

## 8. Failure policy and validation requirements

- No future observations in training, scaling, shrinkage intensity or instrument selection.
- No pairwise covariance estimates built from different observation sets without an explicitly justified model.
- No silent forward fill, dropped target dates, covariance jitter or post-outcome change of the estimation window.
- Matrix symmetry, positive definiteness, unit scaling, numerical conditioning and optimizer constraints checked explicitly.
- Singular or invalid estimates retain failure evidence; the rule for their effect on the primary comparison must be specified before execution.
- Portfolio constraints checked independently; optimisation success flags alone are insufficient.
- Small analytic examples and known-covariance cases checked before historical execution.
- Free vendor data, revision limitations and public redistribution boundaries documented.
- Other research programmes' prospective paths, frozen experiments and authorities remain out of scope.

## 9. Decisions required before protocol freeze

| Decision | Current recommendation / issue |
|---|---|
| Primary emphasis | Agreed: covariance estimation and risk forecasting. |
| Primary contrast | One shrinkage estimator versus sample estimate. |
| Shrinkage specification | Decide scaled-identity covariance shrinkage versus standardized correlation shrinkage; document economic implications. |
| Universe | Small economically defined, US-listed ETF case study; exact instruments/inception criteria still open. |
| Return and mean | Daily adjusted simple returns with explicit common mean treatment; supersedes the earlier log-return suggestion. |
| Historical dates and window | Choose on design/data-availability grounds before loss inspection; not yet fixed. |
| Simulation | Predefine structures, sample-size ratios, seeds and repetitions. |
| Primary score | Gaussian covariance quasi-likelihood proposed; assumptions to review. |
| Uncertainty | Select and justify a dependence-aware procedure before evaluation. |
| Secondary portfolios | Prefer theory/simulation risk diagnostics first; executable historical scope remains to be decided. |
| Failure handling | Complete common-date policy without silent repair or deletion. |

## 10. Planning sequence

1. Resolve the research definition: estimator, target, score and portfolio scope.
2. Write the universe/data/timing specification and uncertainty rationale.
3. Define simulation cases, implementation validation and failure rules.
4. Review the complete design for confounding, leakage and scope.
5. Freeze the protocol only after these choices are settled.
6. Begin implementation and data acquisition only when separately authorized by the user.

No data acquisition, estimator implementation, simulation, backtest or GitHub publication has been performed for this proposed project.
