# Proposed universe and historical study boundary

19 October 2026

**Planning proposal only. No market-data download, estimator implementation, simulation or backtest has been performed for this project. The instruments and settings below are recommendations for review, not a frozen protocol.**

The user accepted proceeding with this proposal into technical planning. [PROTOCOL-DRAFT.md](PROTOCOL-DRAFT.md) now consolidates it with exact estimator, uncertainty, simulation and failure definitions. Issuer/source verification remains outstanding.

## 1. Economic definition

Use a fixed eight-instrument case study representing common USD-based allocation exposures through US-listed, unleveraged exchange-traded products.

The universe is chosen to examine risk relationships across equity regions, interest-rate exposures, corporate credit, gold and listed property. It is not selected to maximize a backtest, manufacture unstable covariance matrices or favour a shrinkage target. Eight instruments are not eight independent economic risk factors.

## 2. Candidate instruments

The ticker/exposure mappings below are the proposed identification starting point. Current issuer identity, inception, benchmark and relevant structural changes must be verified from issuer documentation before protocol freeze; this planning draft does not claim that fresh verification has occurred.

| Proposed ticker | Exposure sleeve | Why it belongs | Important qualification |
|---|---|---|---|
| SPY | US large-cap equities | Core domestic equity exposure. | Not the entire US equity market; overlaps equity-related risks in other sleeves. |
| EFA | Developed-market equities outside the US and Canada | Geographic and currency exposure beyond US equities. | USD listing does not eliminate underlying currency exposure or foreign-market closing-time differences. |
| EEM | Emerging-market equities | A distinct equity-region and market-structure exposure. | Remains correlated with other equity markets; country composition changes over time. |
| IEF | US Treasuries in the 7–10-year maturity segment | Intermediate-maturity government-rate exposure. | Maturity is not the same as duration; market risk and fund holdings evolve. |
| TLT | US Treasuries in the 20-plus-year maturity segment | A longer-maturity rate exposure against which to assess shared and differing risk. | Shares Treasury risk with IEF; deliberately distinct maturity exposure, not an independent factor. |
| LQD | USD investment-grade corporate bonds | Adds credit-spread exposure alongside interest-rate risk. | Not a pure credit factor; overlaps government-rate exposure and can include non-US issuers. |
| GLD | Physical-gold exposure | A non-equity, non-credit sleeve with potentially different co-movement. | A gold trust/product, not an equity fund; not assumed to hedge equities in every period. |
| VNQ | US listed real estate | Listed-property equity exposure and its interaction with equity and rate risks. | Not direct property returns or an independent asset class free of equity risk. |

No instrument is labelled the best, most liquid or cheapest without a defined, verified criterion. These are longstanding exposure proxies proposed for clarity and history, rather than an optimization over funds within each sleeve.

## 3. Proposed inclusion rules

1. One predefined representative per exposure sleeve, apart from the explicitly distinct intermediate/long Treasury maturity sleeves.
2. US-listed, USD-quoted, non-inverse and non-leveraged exposure products. Physical gold is permitted; futures-based commodity-roll strategies are outside this first universe.
3. Identity and existence throughout the proposed observation period must be confirmed before accepting a fixed membership universe.
4. Sufficient common adjusted-price history for a 252-return training window at every scored origin.
5. Common US equity-market observation calendar with a complete, explicitly checked sequence of accepted prices.
6. No selection or replacement based on historical returns, Sharpe ratios, correlations, estimator wins or optimized weights.
7. No redundant pair of products tracking essentially the same index merely to create near-singularity.
8. If a candidate fails identity, history or input-quality requirements, pause and document a proposed revision before any forecast-score inspection. Do not silently switch ticker, shorten the sample or fill prices.

This is a fixed-universe conditional case study. It is not a reconstruction of every investable fund at every historical date. No claim of survivorship-free market-wide inference follows from selecting products that exist today.

## 4. Proposed dates and estimation frequency

| Item | Recommendation | Rationale / limit |
|---|---|---|
| Price coverage | Calendar years 2005–2025, subject to identity/history verification. | Supplies initialization and a complete historical endpoint without entering the other programme's prospective period. |
| Evaluation | Every eligible common session in calendar years 2007–2025. | Starts after ample training history; a fixed calendar span, not a selected best-performing regime. |
| Training | Last 252 observed return vectors through the origin. | Medium rolling window, roughly one trading year; a convention rather than an established optimum. |
| Forecast horizon | Next common session's adjusted simple return vector. | One-session risk forecast, evaluated on identical dates for both methods. |
| Re-estimation | Every forecast origin. | Analytic estimators are inexpensive at eight dimensions; no need to mix an update-frequency question into the primary test. |

The first price observation anchors the first return. Missing prices must not turn a multi-session return into an incorrectly labelled one-session target. Initial history is not itself an evaluation sample and must not be used to select a winning window.

These historical periods are familiar market history. Sequential forecasts will use only past observations, but that is distinct from claiming genuinely unseen research evidence. The date recommendations have not been checked against downloaded prices, and no forecast scores have been inspected.

## 5. Return and estimator definition

Use adjusted simple returns `r[i,t] = P_adj[i,t]/P_adj[i,t-1] - 1`. All assets use decimal units and the same adjustment convention. Adjusted close histories are provider-dependent and can be revised; they approximate distribution-adjusted return analysis and are not directly executable prices.

Recommended shared mean convention: zero conditional mean for this daily-risk study. Then `S_t = (1/252) * sum(r_s * r_s_transpose)` is the sample second moment, interpreted as covariance under that approximation. The same convention must apply to training standardization and the scoring residual. A nonzero conditional mean is a limitation, not a fact that can be ignored silently.

There are eight diagonal variance entries and 28 distinct off-diagonal entries. The selected target preserves the eight variance estimates and applies one analytically determined shrinkage intensity to the estimated correlation structure. The study does not claim to improve individual variance forecasts.

The ratio of dimensions to training observations is modest: 8/252, approximately 0.032. Sample covariance may be adequate. We should not increase the universe or reduce the window after observing little benefit. Predefined simulations can assess other dimension/sample-size ratios without changing the historical case study.

## 6. Proposed primary question and decision

> For a fixed mixed-asset ETF universe, does analytically determined diagonal-target shrinkage improve one-session risk forecasts relative to the sample second moment under a shared zero-mean approximation?

The proposed primary loss is matrix Gaussian quasi-likelihood. The paired difference is shrinkage loss minus sample loss; negative favours shrinkage. The proposed improvement claim requires a negative mean difference with the upper endpoint of the primary two-sided 95% interval below zero, subject to valid execution and the complete common-date policy.

Primary HAC inference and a predefined dependent-bootstrap sensitivity are the current recommendation. Exact lag/block rules, interval construction, seed and repetitions remain open. The sensitivity cannot replace an unfavourable primary conclusion. This design does not claim exact Gaussian returns, economic causality or investment alpha.

## 7. Portfolio interpretation

Recommended target weights solve minimum estimated variance with nonnegative weights summing to one. No leverage, shorts, expected-return forecast or outcome-dependent weight caps are proposed.

Low-volatility bond sleeves may receive large weights even under a perfectly known covariance matrix. Concentration alone therefore does not prove estimation failure. Known-covariance simulation can compare estimated portfolios with an oracle solution under identical constraints, separating objective-driven allocations from estimation error.

Secondary historical outputs are target-weight concentration, maximum weights and target-weight changes on a fixed schedule. These are risk/decision diagnostics, not executable P&L or realized turnover. Equal-weight and inverse-volatility references provide context without becoming substitute primary tests.

## 8. Before protocol freeze

- Verify product identity, inception and economically material benchmark/structure changes using issuer sources, without inspecting forecasting outcomes.
- Agree the eight sleeves and candidate tickers, date boundary and 252-return convention.
- Finalize diagonal-target/standardized Ledoit–Wolf formulas and finite-sample normalization.
- Specify score, HAC and bootstrap details, balanced simulation scenarios and numerical tolerances.
- Complete input, matrix and secondary-optimizer failure rules.
- Review the whole design before any implementation or market-data acquisition.

The current volatility-forecasting repository and every other completed/frozen research stream remain unchanged and outside this planning folder.
