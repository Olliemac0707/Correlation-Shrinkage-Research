"""Summaries and exportable figures; no estimator or inference selection."""

from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .simulation import describe, write_json


def aggregate_adaptation(paths):
    output = []
    for distribution in (0, 1):
        selected = [path for path in paths if path["distribution"] == distribution]
        for segment in ("before", "after", "transition"):
            row = {
                "distribution": ("gaussian", "t8")[distribution],
                "segment": segment,
                "paths": len(selected),
                "expected_paths": 200,
                "metrics": {},
            }
            for metric in (
                "scores",
                "regrets",
                "true_variances",
                "risk_ratios",
                "concentration",
                "maximum_weight",
            ):
                cells = [item["segments"][segment][metric] for item in selected]
                row["metrics"][metric] = {
                    "paired_path_means": describe(
                        [item["paired_mean"] for item in cells if item["paired_mean"] is not None]
                    ),
                    "sample_path_means": describe(
                        [item["sample_mean"] for item in cells if item["sample_mean"] is not None]
                    ),
                    "shrinkage_path_means": describe(
                        [
                            item["shrinkage_mean"]
                            for item in cells
                            if item["shrinkage_mean"] is not None
                        ]
                    ),
                    "complete_paths": sum(
                        item["complete_targets"] == item["targets"] for item in cells
                    ),
                    "complete_targets": sum(item["complete_targets"] for item in cells),
                    "expected_targets": sum(item["targets"] for item in cells),
                }
            output.append(row)
    return output


def render(destination: Path, grid, paths, uncertainty):
    adaptation = aggregate_adaptation(paths)
    failures = sum(row["failure_replications"] for row in grid)
    adaptation_failures = sum(path["failure_count"] for path in paths)
    write_json(
        destination / "summary.json",
        {
            "grid": grid,
            "adaptation": adaptation,
            "uncertainty": uncertainty,
            "grid_failure_replications": failures,
            "adaptation_failure_events": adaptation_failures,
            "historical_status": "not_executed_by_synthetic_runner",
        },
    )
    lines = [
        "# Registered synthetic experiment results",
        "",
        "Protocol correlation-shrinkage-v1.0, operational ordering amendment A1. ",
        "Synthetic mechanism evidence only. Historical ETF results, where available, "
        "are documented in a separate report.",
        "",
        "Negative paired differences favour shrinkage for forecast loss and true risk. "
        "Monte Carlo standard errors describe simulation precision, not historical uncertainty.",
        "",
        "## Independent training samples",
        "",
        "18 fixed cells, 500 training samples per cell: 9,000 samples total. "
        "Every matrix uses T=252. Larger dimensions are separate simulation challenges.",
        "",
        "| Structure | Returns | Assets | Sample regret | Shrinkage regret | "
        "Difference ± MCSE | Sample/oracle risk | Shrinkage/oracle risk | "
        "Risk pairs / 500 | Replications with a failure |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(grid, key=lambda item: (item["p"], item["structure"], item["distribution"])):
        regret = row["metrics"]["regret"]
        risk = row["metrics"]["risk_ratio"]

        def mean(item):
            return f"{item['mean']:.5f}" if item.get("n") else "unavailable"

        diff = regret["paired_difference"]
        diff_text = f"{diff['mean']:+.5f} ± {diff['mcse']:.5f}" if diff.get("n") else "unavailable"
        lines.append(
            f"| {row['structure']} | {row['distribution']} | {row['p']} | "
            f"{mean(regret['sample'])} | {mean(regret['shrinkage'])} | {diff_text} | "
            f"{mean(risk['sample'])} | {mean(risk['shrinkage'])} | "
            f"{risk['complete_pairs']} | {row['failure_replications']} |"
        )
    lines.extend(
        [
            "",
            "Expected-score regret uses the known population covariance; it is not an "
            "observed historical loss. Ratios use a true-covariance long-only oracle "
            "with identical "
            "constraints. Ratios above one mean estimation increased true portfolio risk.",
            "",
            f"Grid replications with at least one recorded failure: **{failures}/9000**. "
            "All failures and raw returned weights are retained in the cell ledgers. "
            "Incomplete summaries have explicit denominators and are not complete-cell evidence.",
            "",
            "## Abrupt covariance-change challenge",
            "",
            "200 independent paths per return distribution, 1,260 targets per path. "
            "Covariance changes after target 630, including a 1.5x volatility increase. "
            "Uncertainty below is across independent path means.",
            "",
            "| Returns | Segment | Regret difference ± MCSE | "
            "Risk-ratio difference ± MCSE | Complete risk paths / 200 |",
            "|---|---|---:|---:|---:|",
        ]
    )
    for row in adaptation:
        regret = row["metrics"]["regrets"]["paired_path_means"]
        risk = row["metrics"]["risk_ratios"]["paired_path_means"]

        def delta(item):
            return f"{item['mean']:+.6f} ± {item['mcse']:.6f}" if item.get("n") else "unavailable"

        lines.append(
            f"| {row['distribution']} | {row['segment']} | {delta(regret)} | "
            f"{delta(risk)} | {row['metrics']['risk_ratios']['complete_paths']} |"
        )
    lines.extend(
        [
            "",
            "Transition is the first 252 targets after the change and overlaps the after "
            "segment; these are registered descriptions, not independent discoveries.",
            "",
            f"Adaptation numerical/optimizer failure events: **{adaptation_failures}**. "
            "The .npz files retain all target positions, masks through NaNs, returns, scores, "
            "risk diagnostics and raw weights; path JSON files retain failure details.",
            "",
            "## Uncertainty stress diagnostics",
            "",
            "Nominal coverage is 95%. HAC has 1,000 replications per process. "
            "Bootstrap uses the first 200 replications, 999 resamples each. "
            "All processes have known mean zero. MCSE is in percentage points.",
            "",
            "| Process | Procedure | Coverage | MCSE | Valid / expected | "
            "Positive / negative rejections |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in sorted(uncertainty, key=lambda item: item["process"]):
        for method, item in row["procedures"].items():
            lines.append(
                f"| {row['process']} | {method} | {100 * item['coverage']:.1f}% | "
                f"{100 * item['coverage_mcse']:.2f} | "
                f"{item['valid']}/{item['expected']} | "
                f"{item['positive_rejections']} / {item['negative_rejections']} |"
            )
    lines.extend(
        [
            "",
            "Coverage below 95% means intervals missed the known truth too often in that "
            "controlled process. Long overlapping dependence is deliberately difficult. "
            "Neither procedure is certified for historical regime changes; diagnostic weaknesses "
            "must qualify any eventual historical interpretation. No lag, block length, target "
            "or primary outcome was changed in response to these results.",
            "",
            "## Reproducibility and scope",
            "",
            "The run manifest identifies the frozen protocol, amendment, archived source, "
            "dependencies, seeds, registered counts and execution timestamps. "
            "The artifact manifest hashes the resulting evidence. "
            "These are local preserved artifacts, not external preregistration "
            "or an independent review.",
            "",
            "This runner does not acquire or evaluate historical ETF data. "
            "No historical outperformance or investment-performance claim follows "
            "from these simulations.",
            "",
            "![Synthetic overview](figures/synthetic-overview.png)",
            "",
        ]
    )
    (destination / "REPORT.md").write_text("\n".join(lines))
    figures = destination / "figures"
    figures.mkdir()
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.4), layout="constrained")
    for axis, distribution in zip(axes[:2], ("gaussian", "t8"), strict=True):
        for structure in ("diagonal", "common", "mixed_factor"):
            cells = sorted(
                [
                    row
                    for row in grid
                    if row["distribution"] == distribution and row["structure"] == structure
                ],
                key=lambda row: row["p"],
            )
            y = []
            for row in cells:
                metric = row["metrics"]["regret"]
                y.append(100 * (metric["shrinkage"]["mean"] / metric["sample"]["mean"] - 1))
            axis.plot([row["p"] for row in cells], y, "o-", label=structure)
        axis.axhline(0, color="grey", lw=1)
        axis.set(
            title=f"Expected-score regret: {distribution}",
            xlabel="Assets (252 observations)",
            ylabel="Change versus sample (%)",
        )
        axis.legend(fontsize=8)
    ordered = sorted(uncertainty, key=lambda row: ("iid", "ar1", "ma252").index(row["process"]))
    positions = np.arange(3)
    for offset, method in ((-0.18, "hac"), (0.18, "bootstrap")):
        values = [100 * row["procedures"][method]["coverage"] for row in ordered]
        errors = [100 * row["procedures"][method]["coverage_mcse"] for row in ordered]
        axes[2].bar(positions + offset, values, width=0.34, label=method, yerr=errors)
    axes[2].axhline(95, color="black", linestyle="--", lw=1, label="Nominal 95%")
    axes[2].set(
        xticks=positions,
        xticklabels=[row["process"] for row in ordered],
        ylim=(0, 102),
        ylabel="Coverage (%)",
        title="Uncertainty stress checks",
    )
    axes[2].legend(fontsize=8)
    fig.savefig(figures / "synthetic-overview.png", dpi=170)
    fig.savefig(figures / "synthetic-overview.pdf")
    plt.close(fig)
