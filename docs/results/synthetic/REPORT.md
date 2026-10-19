# Registered synthetic experiment results

Protocol correlation-shrinkage-v1.0, operational ordering amendment A1. 
Synthetic mechanism evidence only. No historical ETF comparison has run; issuer access and source acceptance remain blocked.

Negative paired differences favour shrinkage for forecast loss and true risk. Monte Carlo standard errors describe simulation precision, not historical uncertainty.

## Independent training samples

18 fixed cells, 500 training samples per cell: 9,000 samples total. Every matrix uses T=252. Larger dimensions are separate simulation challenges.

| Structure | Returns | Assets | Sample regret | Shrinkage regret | Difference ± MCSE | Sample/oracle risk | Shrinkage/oracle risk | Risk pairs / 500 | Replications with a failure |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| common | gaussian | 8 | 0.15120 | 0.13728 | -0.01392 ± 0.00038 | 1.00815 | 1.00762 | 486 | 14 |
| common | t8 | 8 | 0.22879 | 0.19883 | -0.02995 ± 0.00100 | 1.01170 | 1.01047 | 491 | 9 |
| diagonal | gaussian | 8 | 0.14945 | 0.03231 | -0.11714 ± 0.00143 | unavailable | unavailable | 0 | 382 |
| diagonal | t8 | 8 | 0.22377 | 0.05434 | -0.16944 ± 0.00210 | unavailable | unavailable | 0 | 381 |
| mixed_factor | gaussian | 8 | 0.15151 | 0.13323 | -0.01828 ± 0.00064 | 1.01401 | 1.01482 | 359 | 141 |
| mixed_factor | t8 | 8 | 0.22789 | 0.19407 | -0.03381 ± 0.00141 | 1.02003 | 1.02166 | 353 | 147 |
| common | gaussian | 32 | 2.63044 | 2.29892 | -0.33151 ± 0.00196 | 1.03202 | 1.03055 | 71 | 429 |
| common | t8 | 32 | 3.76846 | 3.04803 | -0.72043 ± 0.00817 | 1.04375 | 1.04064 | 52 | 448 |
| diagonal | gaussian | 32 | 2.63711 | 0.12618 | -2.51092 ± 0.00967 | unavailable | unavailable | 0 | 500 |
| diagonal | t8 | 32 | 3.76805 | 0.22402 | -3.54403 ± 0.01660 | 1.08962 | 1.00580 | 1 | 499 |
| mixed_factor | gaussian | 32 | 2.62978 | 2.11610 | -0.51368 ± 0.00266 | 1.03507 | 1.03341 | 67 | 433 |
| mixed_factor | t8 | 32 | 3.75335 | 2.71170 | -1.04165 ± 0.00844 | 1.05068 | 1.04626 | 45 | 455 |
| common | gaussian | 96 | 38.55607 | 31.27365 | -7.28241 ± 0.02623 | 1.04236 | 1.04085 | 18 | 482 |
| common | t8 | 96 | 53.68817 | 38.08850 | -15.59966 ± 0.13844 | 1.06385 | 1.05999 | 8 | 492 |
| diagonal | gaussian | 96 | 38.68547 | 0.38787 | -38.29760 ± 0.06709 | unavailable | unavailable | 0 | 500 |
| diagonal | t8 | 96 | 53.88323 | 0.65545 | -53.22777 ± 0.14289 | unavailable | unavailable | 0 | 500 |
| mixed_factor | gaussian | 96 | 38.66215 | 27.28845 | -11.37370 ± 0.03054 | 1.06962 | 1.06435 | 12 | 488 |
| mixed_factor | t8 | 96 | 53.33453 | 30.86700 | -22.46753 ± 0.14036 | 1.08038 | 1.07310 | 7 | 493 |

Expected-score regret uses the known population covariance; it is not an observed historical loss. Ratios use a true-covariance long-only oracle with identical constraints. Ratios above one mean estimation increased true portfolio risk.

Grid replications with at least one recorded failure: **6793/9000**. All failures and raw returned weights are retained in the cell ledgers. Incomplete summaries have explicit denominators and are not complete-cell evidence.

## Abrupt covariance-change challenge

200 independent paths per return distribution, 1,260 targets per path. Covariance changes after target 630, including a 1.5x volatility increase. Uncertainty below is across independent path means.

| Returns | Segment | Regret difference ± MCSE | Risk-ratio difference ± MCSE | Complete risk paths / 200 |
|---|---|---:|---:|---:|
| gaussian | before | -0.013464 ± 0.000353 | -0.000511 ± 0.000019 | 1 |
| gaussian | after | -0.095338 ± 0.000914 | +0.000477 ± 0.000081 | 0 |
| gaussian | transition | -0.211922 ± 0.001819 | +0.000205 ± 0.000102 | 0 |
| t8 | before | -0.030077 ± 0.000914 | -0.001151 ± 0.000041 | 5 |
| t8 | after | -0.159694 ± 0.002682 | +0.000595 ± 0.000177 | 0 |
| t8 | transition | -0.345135 ± 0.006211 | -0.000244 ± 0.000272 | 0 |

Transition is the first 252 targets after the change and overlaps the after segment; these are registered descriptions, not independent discoveries.

Adaptation numerical/optimizer failure events: **70079**. The .npz files retain all target positions, masks through NaNs, returns, scores, risk diagnostics and raw weights; path JSON files retain failure details.

## Uncertainty stress diagnostics

Nominal coverage is 95%. HAC has 1,000 replications per process. Bootstrap uses the first 200 replications, 999 resamples each. All processes have known mean zero. MCSE is in percentage points.

| Process | Procedure | Coverage | MCSE | Valid / expected | Positive / negative rejections |
|---|---|---:|---:|---:|---:|
| ar1 | hac | 92.7% | 0.82 | 1000/1000 | 39 / 34 |
| ar1 | bootstrap | 89.5% | 2.17 | 200/200 | 12 / 9 |
| iid | hac | 93.4% | 0.79 | 1000/1000 | 29 / 37 |
| iid | bootstrap | 90.0% | 2.12 | 200/200 | 5 / 15 |
| ma252 | hac | 88.1% | 1.02 | 1000/1000 | 62 / 57 |
| ma252 | bootstrap | 89.0% | 2.21 | 200/200 | 8 / 14 |

Coverage below 95% means intervals missed the known truth too often in that controlled process. Long overlapping dependence is deliberately difficult. Neither procedure is certified for historical regime changes; diagnostic weaknesses must qualify any eventual historical interpretation. No lag, block length, target or primary outcome was changed in response to these results.

## Reproducibility and scope

The run manifest identifies the frozen protocol, amendment, archived source, dependencies, seeds, registered counts and execution timestamps. The artifact manifest hashes the resulting evidence. These are local preserved artifacts, not external preregistration or an independent review.

Issuer requests still fail at the environment network proxy. The historical ETF experiment has **not run**, and no historical outperformance or investment-performance claim follows from these simulations.

![Synthetic overview](figures/synthetic-overview.png)
