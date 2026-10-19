"""Historical summaries with explicit pre-existing calibration limitations."""

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def render_historical(output, ledger, portfolios, summary):
    hac, bootstrap = summary.get("hac"), summary.get("bootstrap")
    if hac and hac["high"] < 0:
        decision = "The registered HAC rule favours shrinkage (upper endpoint below zero)."
    elif hac and hac["low"] > 0:
        decision = "The registered HAC rule indicates higher mean forecast loss for shrinkage."
    elif hac:
        decision = "The registered HAC interval spans zero: the primary procedure is inconclusive."
    else:
        decision = (
            "The primary interval is unavailable; only descriptive loss differences are reported."
        )
    lines = [
        "# Historical covariance forecast results",
        "",
        "Frozen protocol correlation-shrinkage-v1.0, operational A1. "
        "Issuer/source acceptance was recorded before historical acquisition; "
        "methods and tolerances were not changed after synthetic outcomes.",
        "",
        "## Data and timing",
        "",
        "Ordered universe: SPY, EFA, EEM, IEF, TLT, LQD, GLD, VNQ. "
        "Yahoo distribution/split-adjusted simple returns in decimal units; "
        "zero conditional mean approximation, 252 trailing returns and next-session targets.",
        "",
        f"Complete XNYS price sessions: **5,283**, 2005–2025. "
        f"Paired target sessions: **{summary['targets']:,}/{summary['expected_targets']:,}**, "
        f"{ledger[0]['target_date']} through {ledger[-1]['target_date']}. "
        f"Primary matrix failures: **{summary['matrix_failures']}**. "
        "No date deletion, price filling, outlier clipping, matrix repair or fallback.",
        "",
        "## Registered forecast comparison",
        "",
        "Lower matrix Gaussian quasi-likelihood loss is better. "
        "Differences are shrinkage minus sample; these scores are not investment returns.",
        "",
        "| Quantity | Value |",
        "|---|---:|",
        f"| Sample mean loss | {summary['sample_mean_loss']:.10f} |",
        f"| Shrinkage mean loss | {summary['shrinkage_mean_loss']:.10f} |",
        f"| Mean paired difference | {summary['mean_difference']:+.10f} |",
    ]
    if hac:
        lines.extend(
            [
                f"| Primary HAC standard error | {hac['se']:.10f} |",
                f"| Primary HAC two-sided 95% interval | "
                f"[{hac['low']:+.10f}, {hac['high']:+.10f}] |",
            ]
        )
    if bootstrap:
        lines.append(
            f"| Bootstrap basic 95% sensitivity interval | "
            f"[{bootstrap['low']:+.10f}, {bootstrap['high']:+.10f}] |"
        )
    lines.extend(
        [
            "",
            decision,
            "",
            "**The nominal confidence level needs substantial qualification.** "
            "Before this historical run, registered diagnostics found only 88.1% HAC "
            "coverage and 89.0% bootstrap coverage under the long-overlap stress. "
            "Thus exclusion of zero under either approximation is not certified "
            "95%-reliable evidence for this changing market history. "
            "The historical confidence interval does not cure those calibration weaknesses.",
            "",
            "HAC uses Bartlett lag 252 and normal critical value 1.959963984540054. "
            "Sensitivity uses 4,999 stationary-bootstrap replications, expected block "
            "length 252, PCG64 seed 41002 and the registered basic interval. "
            "Neither setting was selected using these historical scores. "
            "Disagreement must remain visible; sensitivity cannot replace the primary result.",
            "",
            "## Secondary target-weight diagnostics",
            "",
            "Long-only fully invested minimum-variance targets at each final monthly session, "
            "January 2007–December 2025. Equal and inverse-volatility weights provide context.",
            "",
            f"Monthly origins: **{summary['monthly_origins']}**. "
            f"Sample optimizer acceptance failures: **{summary['portfolio_failures']['sample']}**; "
            f"shrinkage failures: **{summary['portfolio_failures']['shrinkage']}**. "
            "Complete sample/shrinkage weight pairs: "
            f"**{summary['complete_monthly_weight_pairs']}**.",
            "",
            "Raw solver weights, feasibility and KKT residuals are retained even on failure. "
            "Failed weights do not become accepted comparisons. Target distances are "
            "calculated only for adjacent accepted monthly targets, with no bridging "
            "over failed months. These distances are not executed turnover. "
            "No portfolio P&L, trading fills or investment-performance result is reported.",
            "",
            "## Scope and reproducibility",
            "",
            "This is a retrospective fixed-product case study, not a survivorship-free "
            "population or genuinely unseen market evidence. VNQ's benchmark transitions, "
            "GLD's gold-reference change, incomplete historical benchmark genealogy, "
            "foreign-market timing and revised adjusted prices remain limitations. "
            "The detailed issuer/source acceptance record is preserved with this run.",
            "",
            "Raw responses and calendar/adjustment validation remain local; redistribution "
            "rights have not been established. Manifests identify exact data, dependencies, "
            "source, protocol and timestamps. Original synthetic runs and failures are preserved.",
            "",
            "![Historical score and weight diagnostics](figures/historical-overview.png)",
            "",
        ]
    )
    if summary["uncertainty_failures"]:
        lines.extend(["Uncertainty failures: " + str(summary["uncertainty_failures"]), ""])
    (output / "REPORT.md").write_text("\n".join(lines))
    figure_dir = output / "figures"
    figure_dir.mkdir()
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), layout="constrained")
    dates = np.array([row["target_date"] for row in ledger], dtype="datetime64[D]")
    differences = np.array([row["difference"] for row in ledger])
    axes[0].plot(dates, np.cumsum(differences), color="#176b87")
    axes[0].axhline(0, color="grey", lw=1)
    axes[0].set(
        title="Cumulative forecast-loss difference (shrinkage minus sample)",
        ylabel="Cumulative score difference",
    )
    monthly = np.array([row["origin_date"] for row in portfolios], dtype="datetime64[D]")
    for name in ("sample", "shrinkage", "equal", "inverse_vol"):
        maximum = [row["methods"][name].get("maximum_weight", np.nan) for row in portfolios]
        axes[1].plot(monthly, maximum, label=name, lw=1)
    axes[1].set(
        title="Maximum monthly target weight; gaps are failed acceptance checks",
        ylabel="Weight",
        xlabel="Session",
    )
    axes[1].legend(ncol=4)
    fig.savefig(figure_dir / "historical-overview.png", dpi=170)
    fig.savefig(figure_dir / "historical-overview.pdf")
    plt.close(fig)
