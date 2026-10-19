# Protocol freeze record

**Protocol: correlation-shrinkage-v1.0**

Frozen at 2026-10-19T19:48:43.066232+00:00. The user approved freezing the plan and then beginning issuer verification. This expressly advances the ordering in the prior draft: the methodological design is frozen now, while issuer/source eligibility remains a prerequisite to accepting inputs and executing the study.

The exact approved planning documents are preserved in [frozen/v1.0/PROTOCOL-DRAFT.md](frozen/v1.0/PROTOCOL-DRAFT.md) and its accompanying decision/universe/options documents. Historical draft labels inside those byte-preserved snapshots describe their prior state; this freeze record establishes their present status.

The [manifest](frozen/v1.0/manifest.json) records SHA-256 hashes and byte counts for all five snapshots. Its SHA-256 is `72a337fd2b8093952cfc3cd00d82f35bb03c7d0bd4a1aaa9b4e0c4d960fa53da`. Local hashes detect changes against the recorded identities; this is not external preregistration or a cryptographic signature.

## Locked design

- Ordered candidate universe: SPY, EFA, EEM, IEF, TLT, LQD, GLD, VNQ, conditional on documented issuer/history eligibility.
- Daily adjusted simple returns, zero-mean approximation, 252-return windows; 2005–2025 prices and 2007–2025 next-session targets.
- Sample second moment versus the precisely specified standardized Ledoit–Wolf/rescaled diagonal-preserving estimator.
- Matrix Gaussian quasi-likelihood, paired shrinkage-minus-sample mean; primary HAC and predefined bootstrap sensitivity.
- All simulation structures, distributions, dimensions, repetitions, RNG settings, portfolio diagnostics, numerical acceptance and failure rules in the snapshot.
- No outcome-driven amendments or concealed failures. Nonlinear shrinkage remains a future extension.

## Verification and amendments

Issuer documents and provider conventions are checked after this freeze without historical forecast-score inspection. Product inception before the observation period is necessary, but does not prove complete adjusted-price history or an unchanged benchmark. A materially different identity, unsuitable history, or unacceptable provider convention requires a separately versioned amendment recording evidence and rationale; v1.0 is never overwritten. Nonmaterial factual observations belong in the separate verification record.

This authorization covers freeze and issuer/source verification. It does not by itself start market-data acquisition, implementation, simulations, backtests or GitHub publication. Those activities remain subsequent work.
