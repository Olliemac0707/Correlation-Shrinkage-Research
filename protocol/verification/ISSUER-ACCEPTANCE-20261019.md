# Issuer and source acceptance for historical acquisition

19 October 2026, recorded before historical dataset acquisition or forecast-score inspection. Applies to frozen correlation-shrinkage-v1.0 and operational A1. No methodological parameters or instruments change.

## Issuer identity and eligibility

All eight official product pages and official factsheet PDFs were retrieved successfully. Raw documents, extracted text, requested/final URLs, timestamps and SHA-256 hashes are retained in `issuer-sources-20261019T202938Z/manifest.json` and its `documents/manifest.json`. Factsheets describe present products; they are not a complete point-in-time prospectus archive.

| Ticker | Issuer-stated inception/launch | Verified intended exposure | Supporting official source |
|---|---|---|---|
| SPY | 1993-01-22 | S&P 500 equity exposure; ETF trust | [State Street factsheet](https://www.ssga.com/library-content/products/factsheets/etfs/us/factsheet-us-en-spy.pdf), inception and investment objective |
| EFA | 2001-08-14 | Developed large/mid-cap equities outside US/Canada | [iShares factsheet](https://www.ishares.com/us/literature/fact-sheet/efa-ishares-msci-eafe-etf-fund-fact-sheet-en-us.pdf), fund description/key facts |
| EEM | 2003-04-07 | Emerging-market large/mid-cap equities | [iShares factsheet](https://www.ishares.com/us/literature/fact-sheet/eem-ishares-msci-emerging-markets-etf-fund-fact-sheet-en-us.pdf), fund description/key facts |
| IEF | 2002-07-22 | US Treasuries with remaining maturities 7–10 years | [iShares factsheet](https://www.ishares.com/us/literature/fact-sheet/ief-ishares-7-10-year-treasury-bond-etf-fund-fact-sheet-en-us.pdf), fund description/key facts |
| TLT | 2002-07-22 | US Treasuries with remaining maturities above 20 years | [iShares factsheet](https://www.ishares.com/us/literature/fact-sheet/tlt-ishares-20-year-treasury-bond-etf-fund-fact-sheet-en-us.pdf), fund description/key facts |
| LQD | 2002-07-22 | USD investment-grade corporate bonds | [iShares factsheet](https://www.ishares.com/us/literature/fact-sheet/lqd-ishares-iboxx-investment-grade-corporate-bond-etf-fund-fact-sheet-en-us.pdf), fund description/key facts |
| GLD | 2004-11-18 | Physically backed gold trust | [State Street factsheet](https://www.ssga.com/library-content/products/factsheets/etfs/us/factsheet-us-en-gld.pdf), objective/structure/inception |
| VNQ | 2004-09-23 | US listed real-estate equities | [Vanguard factsheet](https://fund-docs.vanguard.com/F0986.pdf), investment approach/quick facts/spliced-index notes |

Launch/inception is the issuer label, not an independently established first executable trading date. All precede the first required 2005 session. Current product pages identify USD US-listed instruments; factsheet objectives are plain index/physical-gold exposures rather than inverse or leveraged-return objectives. This does not assert that an ETF never uses derivatives, lending, or other portfolio techniques.

## Historical and structural qualifications

- **VNQ:** Vanguard's factsheet explicitly describes the spliced benchmark: MSCI US REIT Index with a 2% cash adjustment through 2009-04-30; MSCI US REIT Index through 2018-02-01; MSCI US Investable Market Real Estate 25/50 Transition Index through 2018-07-24; MSCI US Investable Market Real Estate 25/50 Index thereafter. It describes real-estate management/development companies alongside REITs. Accept as the already selected broad listed-real-estate product; do not claim constant REIT-only exposure or a single unchanged benchmark.
- **GLD:** State Street records adoption of LBMA Gold Price PM on 2015-03-20 in place of London PM Fix for NAV reference. The page states GLD is not an investment company registered under the 1940 Act and sells gold for ongoing expenses. This remains the selected physical-gold exposure, not a constant-price-reference or income-generating fund claim.
- **IEF/TLT:** Current factsheets name ICE US Treasury 7–10 Year and 20+ Year indices. Complete historical provider/benchmark genealogy is only partially supported by these current documents; no claim that today's index name or methodology applied unchanged throughout 2005–2025. Remaining-maturity exposure and product history are the relevant universe definitions. Maturity is not duration.
- **EFA/EEM/LQD:** Current index descriptions and product identity are supported. Historical membership, country weights, credit composition and methodology are not fixed or independently reconstructed. USD-denominated bonds do not imply exclusively US-domiciled issuers; USD listing does not remove foreign-equity currency or closing-time effects.
- **SPY:** The current page redirects to its State Street-branded name. The ticker, exposure and issuer-stated inception remain supported. Do not treat a brand-name redirect as an economic ticker substitution.
- **Issuer performance displays:** iShares reports switching market-price performance calculations from bid/ask midpoint to close on 2020-08-10. Vanguard reports a similar display convention change on 2024-07-15. This study will use one vendor's adjusted closing-price series consistently, not splice issuer-displayed performance histories.

Some attempted summary-prospectus links returned HTML wrappers despite a `.pdf` URL; those are preserved as HTML and are not cited as retrieved PDF prospectuses. The guessed Vanguard prospectus path returned 403. No unsupported claim of complete prospectus history follows. The available official evidence supports proceeding with the preselected broad exposure case study, with the above explicitly retained limitations. No exclusion, substitution or date change is made.

## Provider convention and use

Yahoo's [official history interface](https://finance.yahoo.com/quote/SPY/history/) was retrieved and archived as `documents/Yahoo-history-interface.html`, with its own hash manifest. It labels close as adjusted for splits, and explicitly states: **“Adjusted close price adjusted for splits and dividend and/or capital gain distributions.”** This provides a directly observed provider convention despite the separate help hostname being blocked.

Historical retrieval interface is fixed before acquisition: unauthenticated HTTPS GET to `https://query1.finance.yahoo.com/v8/finance/chart/{ticker}`, with daily interval, `includeAdjustedClose=true`, dividend/split/capital-gain events, period1=2005-01-01 00:00 UTC inclusive and period2=2026-01-01 00:00 UTC exclusive. Use the returned adjusted-close field without yfinance auto-adjustment, price repair, rounding, backfilling or source substitution. Record request parameters, response metadata/time zone/currency/symbol and exact raw response hashes. Interpret timestamps in the returned exchange timezone and accept only the frozen XNYS sessions.

These public interfaces are provider-dependent and can change; no official API stability guarantee is asserted. Yahoo legal/help hosts remain blocked and raw-data redistribution rights are not verified. This execution is local personal research; raw prices and issuer documents will not be uploaded or redistributed as part of it. Any later publication requires its own distribution review. No claim of a verified redistribution licence is made.

## Gate decision

**Issuer/basic source convention accepted for local historical acquisition**, subject to complete frozen-calendar validation and preservation of the stated historical/structural limitations. Existence before 2005 does not prove a complete provider history. No historical forecast scores have been viewed, and the eventual input dataset remains unaccepted until all numerical/session/corporate-action checks have been recorded. The earlier synthetic inference weaknesses and optimizer failures remain known and do not authorize changing historical methods.
