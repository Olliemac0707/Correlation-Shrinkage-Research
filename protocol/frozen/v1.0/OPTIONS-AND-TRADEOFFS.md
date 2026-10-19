# Portfolio research: options and trade-offs

Planning review — 19 October 2026

This options review is retained as decision history. See [PROTOCOL-DRAFT.md](PROTOCOL-DRAFT.md) for the current consolidated technical proposal; options below are not additional registered comparisons.

**Nothing in this document is frozen. No data acquisition, code implementation, simulation or backtest is authorized by this review.** The agreed emphasis is covariance estimation and sequential risk forecasting, with portfolio consequences secondary.

This is a practical menu for a first study, plus alternatives worth deferring. It is not an exhaustive catalogue of the covariance-estimation literature. Targets, shrinkage intensity, observation weighting and portfolio objectives are different decisions; combining them without separation would make the result difficult to interpret.

## 1. What should the research claim concern?

| Option | Advantages | Disadvantages / interpretation limit |
|---|---|---|
| Full covariance forecast accuracy | Directly tests the risk estimator; clean paired comparison on common targets. | True daily covariance is latent; historical scoring needs an appropriate return-based loss and mean assumption. |
| Risk of a fixed reference portfolio | Easy economic interpretation; weights can be common to both forecasts. | Tests only selected exposures and can miss errors elsewhere in the matrix. |
| Risk of each model's optimized portfolio | Connects estimation to decisions and reveals sensitivity to errors. | Models choose different exposures; lower risk does not isolate matrix accuracy. |
| Highest net Sharpe or return | Familiar investor outcome. | Introduces expected-return exposures, trading assumptions and noisy ratios; weak identification of the covariance estimator's contribution. |

**Working recommendation:** full-matrix forecast loss is primary. Fixed-exposure and optimized-weight consequences are secondary and must not replace an inconclusive primary outcome.

## 2. Which structural target should shrinkage use?

For sample estimate S, linear shrinkage combines it with a target F: `(1-delta)*S + delta*F`.

| Target / method | Advantages | Disadvantages |
|---|---|---|
| Scaled identity, F = average variance times I | Standard, transparent Ledoit–Wolf reference implementation; regularizes small eigenvalues. | Pulls individual variances toward equality and correlations toward zero; that assumption is strong for a bond/equity/gold mixture. |
| Diagonal target, preserving sample variances | Isolates damping of estimated correlations; preserves large differences in individual asset risks. | Pulls genuine positive and negative correlations toward zero, potentially weakening useful hedge information; does not improve noisy individual variances. |
| Constant-correlation target | Retains an estimated common dependence level while reducing pair-specific noise. | A common correlation can be a poor description of mixed assets; positive equity-like dependence need not represent bonds or hedges. |
| Factor-structured target | Economic interpretation if factors are defined economically; can scale to larger universes. | Adds choices about factors, loadings, residual risks and estimation; harder to isolate the effect of shrinkage alone. |
| Nonlinear eigenvalue shrinkage | More flexible correction of the sample spectrum; potentially useful when dimensions are large relative to observations. | Greater mathematical and numerical complexity; a larger methodological jump than needed for a small ETF case study. |

**Working recommendation for a mixed-asset ETF universe:** correlation shrinkage preserving each asset's sample variance. One implementation candidate is Ledoit–Wolf on training-window-standardized returns followed by rescaling. This is **not identical** to applying conventional Ledoit–Wolf directly to raw covariance.

With D containing training-window sample standard deviations, R = inverse(D)*S*inverse(D). Shrinking R toward I and rescaling gives `Sigma_hat = D*((1-delta)*R + delta*I)*D`. Individual variances remain unchanged. All scaling must be estimated from the current training window only.

The analytically estimated intensity then concerns the standardized estimation problem; it is not guaranteed to minimize our historical covariance forecast score. The hypothesis becomes specifically whether regularizing correlation estimates helps under the chosen risk definition. A scaled-identity study remains a valid alternative if we deliberately want to test that conventional estimator.

## 3. How should the shrinkage intensity be chosen?

| Option | Advantages | Disadvantages |
|---|---|---|
| One fixed intensity | Very transparent; easy mathematical diagnostics. | Arbitrary unless justified; does not respond to estimation noise or sample size. |
| Analytical Ledoit–Wolf intensity | No evaluation-sample tuning grid; established bias/variance motivation. | Optimality concerns a particular estimation-loss framework and assumptions, not automatic superiority under every forecast loss or return process. |
| Oracle Approximating Shrinkage (OAS) | Simple established alternative; attractive small-sample behaviour under Gaussian-model assumptions. | Those assumptions are imperfect for fat-tailed financial returns; adding it creates another candidate and comparison. |
| Past-only temporal cross-validation | Can target a chosen predictive objective. | More hyperparameters, smaller effective training sets, computational work and dependence-aware validation choices; easy to introduce leakage. |
| Choose the best intensity from final evaluation losses | Can produce an attractive reported winner. | Invalid as an untouched evaluation: it converts the test sample into model selection. |

**Working recommendation:** one analytical intensity rule, with the exact centering and scaling documented. No intensity search on evaluation outcomes.

## 4. Which universe?

| Option | Advantages | Disadvantages |
|---|---|---|
| Roughly 8–12 economically defined US-listed multi-asset ETFs | Free daily data is practical; understandable exposures; common trading calendar; diverse variances make target assumptions visible. | Small dimension can leave limited shrinkage benefit; exposures overlap; a current fixed set is not a survivorship-free historical opportunity set. |
| A sector ETF set | Clear equity-risk setting; substantial correlations; simpler currency and underlying-market interpretation. | Less economic diversification; instrument inception dates can constrain history; results are narrow. |
| Dozens of individual equities | More covariance parameters and estimation noise; potentially stronger high-dimensional research relevance. | Historical membership, delistings, corporate actions and survivorship handling are much harder with free data. |
| Internationally listed instruments | More global portfolio realism and calendar/FX questions. | Asynchronous prices, FX conversion, holiday alignment and conventions can dominate the intended estimator question. |
| Synthetic assets only | Known true covariance; clean experiments and analytical validation. | No evidence of behaviour on actual market observations. |

**Working recommendation:** a small economically justified US-listed ETF case study plus simulations. Exact instruments and inception criteria remain open. More assets are not automatically more impressive, and a larger dimension must not be selected merely because it favours shrinkage.

US-listed international ETFs simplify the observation calendar, but their underlying markets still close at different times. Listing alignment does not eliminate asynchronous economic information.

## 5. Return definition and mean treatment

| Choice | Advantages | Disadvantages |
|---|---|---|
| Adjusted simple returns | Portfolio simple return is exactly a weighted sum over an interval for fixed beginning weights; covariance maps directly to w-transpose*Sigma*w. | Adjusted history is vendor-dependent and revised; still not an executable price series or a complete cash-flow ledger. |
| Adjusted log returns | Convenient time aggregation and familiar statistical modelling. | A weighted sum of asset log returns is generally not the portfolio's exact log return; risk interpretation requires an approximation. |
| Unadjusted price returns | Direct view of observed price changes. | Corporate actions and distributions can distort the intended economic-return risk question. |
| Common zero conditional mean | Avoids an additional noisy mean forecast; clear first-version convention at daily frequency. | Not literally true; raw second moments equal covariances only under that assumption. |
| Common rolling mean forecast | More explicit residual-based covariance interpretation. | Adds estimation error and a window choice; must be identical across covariance candidates. |
| A different mean model per covariance estimator | Allows complete joint forecast systems. | Confounds mean prediction and covariance estimation, changing this project's question. |

**Working recommendation:** adjusted simple returns with a common explicit zero-mean approximation, describing the estimated object accurately as a second moment under that assumption. This revises the earlier provisional log-return suggestion because portfolio variance is a more direct interpretation for simple returns.

## 6. Observation frequency, training window and dynamics

| Option | Advantages | Disadvantages |
|---|---|---|
| Daily targets | Many paired observations; practical common data; direct one-session risk question. | Noisy realizations, stale underlying information and dependence remain. |
| Weekly targets | May reduce some daily pricing noise. | Fewer targets; less estimation information for the same calendar history; a different horizon. |
| Monthly targets | Closer to some allocation horizons. | Very few evaluation observations; covariance estimation becomes demanding even at modest dimensions. |
| Short rolling window, e.g. about 60 sessions | Responds quickly to changing risks. | Higher estimation noise; any shrinkage advantage may be specific to the deliberately short window. |
| Medium rolling window, e.g. about 252 sessions | Understandable compromise between precision and responsiveness. | Can still lag abrupt changes; one year is a convention, not an objectively optimal value. |
| Long rolling window, e.g. several years | More estimation observations. | Mixes regimes and can give stale covariance forecasts; may reduce the estimator's relevant challenge. |
| Expanding history | Uses all available past information. | Increasingly slow adaptation; estimator behaviour changes with growing sample size. |
| EWMA, GARCH or other dynamic weighting | Explicitly adapts to recent volatility/dependence. | Changes time weighting as well as regularization; ordinary unweighted shrinkage formulas cannot automatically be reused without justification. |

**Working recommendation:** daily forecasts with one fixed medium rolling window. The exact length remains provisional. Explore sample-size effects in predefined simulations; do not choose the historical window from whichever one makes shrinkage look best.

Forecast update frequency and portfolio rebalancing frequency are separate decisions. Daily risk estimates do not require daily trading.

## 7. Which loss and evaluation target?

| Option | Advantages | Disadvantages |
|---|---|---|
| Gaussian covariance quasi-likelihood: log determinant plus return quadratic form | Evaluates the full positive-definite risk matrix; well-defined expected-score interpretation with the specified mean/second moment; natural primary comparison. | Sensitive to tiny eigenvalues and extreme returns; requires stable matrix calculations and dependence-aware uncertainty. Choosing it does not prove Gaussian returns. |
| Squared Frobenius matrix error against known population covariance | Direct estimation-error measurement in simulations. | True covariance is not directly observed in historical data; unscaled versions emphasize large-variance entries. |
| Squared matrix error against a daily outer-product proxy | Available from observations; can support an estimation-loss comparison under appropriate moment assumptions. | The proxy is extremely noisy; it must not be called the true daily covariance, and units affect what dominates the score. |
| Error against a future multi-session realized estimate | Averages more observations. | Changes the target horizon; overlapping future windows create extra dependence and possible evaluation mistakes. |
| Risk-calibration score for fixed reference portfolios | Easy economic interpretation. | Covers only the selected exposures and can hide errors in other directions. |
| Sharpe ratio or net return | Direct investor interest. | Does not isolate covariance accuracy; costly to interpret credibly without a fully specified trading study. |

**Working recommendation:** covariance quasi-likelihood primary, known-covariance errors in simulations secondary. A single observed return vector does not reveal an entire true covariance matrix.

## 8. Which uncertainty procedure?

| Option | Advantages | Disadvantages |
|---|---|---|
| IID standard error | Simple benchmark under independence. | Daily paired losses and overlapping estimation histories need not be independent; not a justified default. |
| Newey–West/HAC interval | Transparent, established way to accommodate short-run serial dependence. | Asymptotic; lag selection, tail behaviour and nonstationarity matter; a small lag is not automatically adequate because it is a default formula. |
| Moving-block or stationary bootstrap | Respects dependence within blocks; flexible interval construction. | Block-length choices and stationarity assumptions matter; bootstrapping stored losses does not reproduce every aspect of refitting on a new market history. |
| Predefined primary method plus secondary sensitivity | Shows whether interpretation depends on a particular approximation. | More outputs and possible ambiguity; neither result may replace the primary one after inspection. |

**Working recommendation:** choose one primary procedure and justify its lag/block rule before historical losses are inspected. HAC is a reasonable initial preference for transparency, with controlled simulation checks of coverage. A bootstrap is a legitimate alternative, not a rescue procedure after an unwelcome HAC result.

One historical primary contrast does not itself create a multiple-comparison family. Adding estimators, windows or formal subgroup claims would require a new family definition. Simulation-grid summaries should not silently become a collection of selected significance claims.

## 9. What should simulations include?

| Option | Advantages | Disadvantages |
|---|---|---|
| Constant Gaussian covariance | Known truth, simple theory, useful numerical and sampling checks. | Financial tails and time variation are absent; results apply to a favourable textbook environment. |
| Unequal variances and different correlation structures | Tests economically important target assumptions. | Scenarios must be set independently of which estimator wins. |
| Fat-tailed returns with finite required moments | Challenges robustness while retaining a known covariance. | Scaling and degrees of freedom must be correct; some inference procedures need higher moments than covariance existence alone. |
| Predefined covariance regime changes | Shows the precision/adaptation trade-off. | Adds assumptions about timing and size of changes; not a generic representation of crises. |
| One generator equal to the chosen shrinkage target | Easy positive illustration of regularization. | Would be an unbalanced performance demonstration if presented as general evidence. |

**Working recommendation:** a small balanced set of known-covariance cases, including heterogeneous variances and a factor-style structure, with a modest predefined tail/time-variation challenge. Set Monte Carlo repetition counts using a precision/computational rationale, not an impressive-looking round number. Technical pilots may establish numerical correctness and Monte Carlo precision; they must not select scenarios to manufacture an estimator advantage.

## 10. Portfolio objective, constraints and scope

| Option | Advantages | Disadvantages |
|---|---|---|
| Long-only, fully invested minimum variance | Directly exposes the role of covariance; convex problem; no estimated-return model. | Can concentrate in low-volatility assets and ignores expected-return differences; minimum variance is not universal investor optimality. |
| Minimum variance with fixed weight caps | Can improve diversification and practical interpretability. | Caps are additional policy assumptions; they can mask estimator differences. Never add them because an observed result looks concentrated. |
| Mean–variance allocation | Introduces explicit risk/return preferences. | Expected-return estimation error and risk-aversion choices can dominate; a broader research question. |
| Equal-risk-contribution allocation | Economically interpretable risk budgets. | Different objective and numerical problem; not the same as inverse-volatility weighting when correlations matter. |
| Synthetic true-risk and weight diagnostics | Isolates estimation/optimisation effects; no execution claims. | Does not establish implementable historical investment performance. |
| Historical target-weight diagnostics | Shows concentration and changes under real estimated matrices. | Changes between targets are not actual trade turnover: drifted pre-trade holdings and execution matter. |
| Fully implemented historical portfolio study | Can assess realised risk, cash, costs and turnover. | Requires separate decisions on timestamps, fills, distributions, cash, shares and costs; substantial additional scope. |

**Working recommendation:** fully invested, long-only minimum-variance weights, without outcome-driven caps. Equal weight and inverse volatility are secondary reference allocations. Start with true risk in simulation and historical weight diagnostics. Defer executable P&L until its own design is complete. Short selling and leverage remain outside the proposed project.

## 11. History, data quality and failures

| Option | Advantages | Disadvantages |
|---|---|---|
| Fixed familiar historical sample | Transparent and feasible; supports past-only sequential forecasts. | Cannot become genuinely unseen evidence just because a new protocol is written. |
| A predefined development/evaluation split | Separates implementation/model development from final numerical evaluation. | Familiar market periods remain familiar; choosing among many designs on development outcomes creates further selection history. |
| Future observations under a separate protocol | Genuinely new evidence as time passes. | Requires time and careful isolation from the other programme's protected prospective study. |
| Common complete observations with strict quality checks | Comparable estimators, coherent matrices and clear failures. | Vendor gaps must be diagnosed rather than hidden; some datasets may remain unusable under the frozen policy. |
| Pairwise deletion | Retains more observations per matrix entry. | Entries refer to different samples and may produce a matrix that is not positive semidefinite. |
| Forward filling | Convenient calendar completion. | Manufactures zero returns and distorts variance/correlation; not an acceptable silent default. |
| Fail closed on singular/invalid forecasts | Honest record; preserves the intended raw sample baseline. | Can prevent a complete primary conclusion; exact handling must be specified beforehand. |
| Predefined common eigenvalue floor or ridge | Can ensure usable matrix scores and optimisation. | Defines a regularized baseline rather than an untouched sample estimator; must be named, justified and counted. |
| Predefined fallback | Produces an operational pipeline with no discarded targets. | Changes the estimand to a model-plus-fallback system; differential failure frequency affects interpretation. |
| Drop failed targets | Makes finite scores easy to produce. | Selects the evaluation sample and can reward a fragile method; unsuitable for the primary comparison. |

**Working recommendation:** fixed retrospective dates selected before new score inspection, strict common inputs, no silent imputation/repair, and a fully written failure policy. For a small universe with substantially more observations than assets, first investigate whether a raw sample baseline can remain valid without added ridge. Specify tolerances and fail-closed consequences before execution.

## 12. Recommended first-version package, still subject to review

1. Small, economically defined multi-asset US-listed ETF universe.
2. Adjusted simple returns and a common explicit zero-mean approximation.
3. One primary comparison: sample second moment versus analytically determined correlation shrinkage preserving individual variances.
4. One fixed rolling window and daily forecast targets.
5. Covariance quasi-likelihood primary; appropriate dependence-aware uncertainty.
6. Balanced known-covariance simulations with their own predefined design and Monte Carlo precision goals.
7. Secondary minimum-variance weight/risk diagnostics, equal-weight and inverse-volatility references; no executable portfolio-return claims in the first phase.
8. Identical historical targets, complete provenance and explicit numerical/failure rules.

This package concentrates the question on **whether damping noisy correlations improves risk forecasts and the decisions derived from them**. It is a recommendation, not an agreed or frozen protocol. The exact instruments, dates, window, standardization/intensity definition, uncertainty rule, simulation grid and failure thresholds still require review.
