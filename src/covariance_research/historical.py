"""Frozen-universe acquisition, strict calendar validation and sequential forecasts.

The historical component uses the same core/inference implementations as the
preserved synthetic run. Issuer/source acceptance is recorded before acquisition.
"""

import argparse
import hashlib
import json
import shutil
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import exchange_calendars as xc
import numpy as np

from .core import NumericalFailure, accept, estimate, estimate_at, minimum_variance
from .inference import bootstrap_interval, hac_interval
from .simulation import clean, write_json

TICKERS = ("SPY", "EFA", "EEM", "IEF", "TLT", "LQD", "GLD", "VNQ")
PROTOCOL_HASH = "72a337fd2b8093952cfc3cd00d82f35bb03c7d0bd4a1aaa9b4e0c4d960fa53da"


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sessions():
    calendar = xc.get_calendar("XNYS", start="2004-12-01", end="2026-01-02")
    return calendar.sessions_in_range("2005-01-01", "2025-12-31").strftime("%Y-%m-%d").tolist()


def parse_chart(payload, ticker, expected_dates):
    chart = payload.get("chart", {})
    if chart.get("error") or len(chart.get("result") or []) != 1:
        raise NumericalFailure(f"{ticker}: malformed or rejected chart response")
    item = chart["result"][0]
    metadata = item.get("meta", {})
    if metadata.get("symbol") != ticker or metadata.get("currency") != "USD":
        raise NumericalFailure(f"{ticker}: source identity or currency mismatch")
    if metadata.get("exchangeTimezoneName") != "America/New_York":
        raise NumericalFailure(f"{ticker}: unexpected exchange timezone")
    timestamps = item.get("timestamp") or []
    dates = [
        datetime.fromtimestamp(t, ZoneInfo("America/New_York")).date().isoformat()
        for t in timestamps
    ]
    if dates != expected_dates:
        missing = sorted(set(expected_dates) - set(dates))
        extra = sorted(set(dates) - set(expected_dates))
        raise NumericalFailure(
            f"{ticker}: calendar/order/duplicate mismatch; "
            f"missing={missing[:10]}, extra={extra[:10]}"
        )
    adjusted = item.get("indicators", {}).get("adjclose", [])
    if len(adjusted) != 1:
        raise NumericalFailure(f"{ticker}: missing adjusted-close series")
    prices = np.asarray(adjusted[0].get("adjclose", []), dtype=float)
    if len(prices) != len(dates) or not np.isfinite(prices).all() or np.any(prices <= 0):
        raise NumericalFailure(f"{ticker}: missing, nonfinite or nonpositive adjusted close")
    raw_close = np.asarray(item["indicators"]["quote"][0].get("close", []), dtype=float)
    return prices, metadata, raw_close, item.get("events", {})


def price_returns(prices):
    x = np.asarray(prices, dtype=float)
    if x.ndim != 2 or not np.isfinite(x).all() or np.any(x <= 0):
        raise NumericalFailure("Invalid accepted price panel")
    returns = x[1:] / x[:-1] - 1
    if not np.isfinite(returns).all():
        raise NumericalFailure("Nonfinite simple return")
    return returns


def acquire(destination):
    project = Path(__file__).resolve().parents[2]
    acceptance = project / "protocol/verification/ISSUER-ACCEPTANCE-20261019.md"
    if not acceptance.exists():
        raise RuntimeError("Issuer/source acceptance missing")
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(acceptance, destination / "ISSUER-SOURCE-ACCEPTANCE.md")
    dates = sessions()
    write_json(
        destination / "calendar.json",
        {"name": "XNYS", "package_version": xc.__version__, "sessions": dates},
    )
    parameters = {
        "period1": 1104537600,
        "period2": 1767225600,
        "interval": "1d",
        "includeAdjustedClose": "true",
        "events": "div,splits,capitalGains",
    }

    def fetch(ticker):
        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?"
            + urllib.parse.urlencode(parameters)
        )
        row = {"ticker": ticker, "url": url, "requested_at_utc": now()}
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=35) as response:
                data = response.read(20000000)
                row.update(
                    status=response.status,
                    final_url=response.url,
                    content_type=response.headers.get("Content-Type"),
                )
            path = destination / f"{ticker}.json"
            with path.open("xb") as handle:
                handle.write(data)
            row.update(file=path.name, bytes=len(data), sha256=sha(path), retrieved_at_utc=now())
        except Exception as exc:
            row["error"] = repr(exc)
        return row

    with ThreadPoolExecutor(max_workers=4) as pool:
        acquisitions = list(pool.map(fetch, TICKERS))
    write_json(
        destination / "acquisition-manifest.json",
        {
            "created_at_utc": now(),
            "protocol_hash": PROTOCOL_HASH,
            "issuer_source_acceptance_sha256": sha(acceptance),
            "parameters": parameters,
            "calendar_sha256": sha(destination / "calendar.json"),
            "assets": acquisitions,
        },
    )
    if any("error" in row for row in acquisitions):
        raise RuntimeError("Source acquisition failure; preserved without fallback")
    columns, diagnostics, flags = [], {}, []
    for ticker in TICKERS:
        prices, metadata, close, events = parse_chart(
            json.loads((destination / f"{ticker}.json").read_text()), ticker, dates
        )
        columns.append(prices)
        returns = prices[1:] / prices[:-1] - 1
        diagnostics[ticker] = {
            "rows": len(prices),
            "first_date": dates[0],
            "last_date": dates[-1],
            "metadata": metadata,
            "corporate_actions": events,
            "max_absolute_return": float(np.abs(returns).max()),
        }
        for index in np.flatnonzero(np.abs(returns) > 0.2):
            flags.append(
                {
                    "ticker": ticker,
                    "date": dates[index + 1],
                    "previous_date": dates[index],
                    "adjusted_return": returns[index],
                    "previous_adjusted": prices[index],
                    "adjusted": prices[index + 1],
                    "previous_close": close[index],
                    "close": close[index + 1],
                    "raw_close_return": close[index + 1] / close[index] - 1,
                }
            )
    panel = np.column_stack(columns)
    with (destination / "prices.npz").open("xb") as handle:
        np.savez_compressed(handle, prices=panel, dates=np.array(dates), tickers=np.array(TICKERS))
    write_json(
        destination / "validation.json",
        {
            "validated_at_utc": now(),
            "complete_calendar": True,
            "price_sessions": len(dates),
            "target_sessions": sum("2007-01-01" <= day <= "2025-12-31" for day in dates),
            "assets": diagnostics,
            "extreme_move_flags": flags,
            "status": "pending_recorded_input_acceptance",
            "panel_sha256": sha(destination / "prices.npz"),
        },
    )
    print(
        json.dumps(
            {
                "data_directory": str(destination),
                "rows": len(dates),
                "extreme_move_flags": clean(flags),
            }
        ),
        flush=True,
    )


def load_accepted(directory):
    acceptance = json.loads((directory / "DATA-ACCEPTANCE.json").read_text())
    if acceptance["status"] != "accepted":
        raise RuntimeError("Dataset has not been accepted")
    for relative, value in acceptance["hashes"].items():
        if sha(directory / relative) != value:
            raise RuntimeError("Accepted data artifact changed: " + relative)
    with np.load(directory / "prices.npz") as panel:
        prices, dates = panel["prices"].copy(), panel["dates"].tolist()
        if tuple(panel["tickers"]) != TICKERS:
            raise RuntimeError("Accepted column order changed")
    if dates != sessions():
        raise RuntimeError("Calendar no longer matches accepted panel")
    return prices, dates, acceptance


def execute(data_directory, output):
    from .historical_report import render_historical

    prices, dates, data_acceptance = load_accepted(data_directory)
    project = Path(__file__).resolve().parents[2]
    planning = project / "protocol"
    frozen = planning / "frozen/v1.0"
    if sha(frozen / "manifest.json") != PROTOCOL_HASH:
        raise RuntimeError("Protocol manifest changed")
    protocol = json.loads((frozen / "manifest.json").read_text())
    for item in protocol["files"]:
        if sha(frozen / item["path"]) != item["sha256"]:
            raise RuntimeError("Frozen protocol document changed")
    output.mkdir(parents=True, exist_ok=False)
    shutil.copytree(frozen, output / "protocol")
    shutil.copyfile(planning / "AMENDMENT-A1.md", output / "AMENDMENT-A1.md")
    shutil.copyfile(data_directory / "DATA-ACCEPTANCE.json", output / "DATA-ACCEPTANCE.json")
    shutil.copyfile(
        data_directory / "ISSUER-SOURCE-ACCEPTANCE.md", output / "ISSUER-SOURCE-ACCEPTANCE.md"
    )
    source_hashes = {}
    for path in sorted(
        [
            *project.glob("src/**/*.py"),
            *project.glob("tests/**/*.py"),
            project / "requirements-lock.txt",
            project / "pyproject.toml",
        ]
    ):
        relative = path.relative_to(project)
        target = output / "source" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        source_hashes[str(relative)] = sha(path)
    returns, return_dates = price_returns(prices), dates[1:]
    targets = [i for i, day in enumerate(return_dates) if "2007-01-01" <= day <= "2025-12-31"]
    expected = sum("2007-01-01" <= day <= "2025-12-31" for day in dates)
    if len(targets) != expected or min(targets) < 252:
        raise RuntimeError("Target count or initialization mismatch")
    write_json(
        output / "run-manifest.json",
        {
            "started_at_utc": now(),
            "protocol_hash": PROTOCOL_HASH,
            "source_hashes": source_hashes,
            "data_directory": str(data_directory),
            "data_acceptance_sha256": sha(data_directory / "DATA-ACCEPTANCE.json"),
            "issuer_acceptance_sha256": sha(data_directory / "ISSUER-SOURCE-ACCEPTANCE.md"),
            "tickers": TICKERS,
            "price_rows": len(dates),
            "expected_targets": expected,
            "calendar_version": xc.__version__,
            "known_synthetic_inference_weakness": True,
            "known_synthetic_optimizer_weakness": True,
        },
    )
    ledger, forecast_matrices = [], []
    try:
        with (output / "paired-scores.jsonl").open("x") as handle:
            for target in targets:
                row = {
                    "target_date": return_dates[target],
                    "origin_date": return_dates[target - 1],
                    "training_start_return_date": return_dates[target - 252],
                    "training_end_return_date": return_dates[target - 1],
                }
                try:
                    fitted = estimate_at(returns, target)
                    sample, shrink = accept(fitted.sample), accept(fitted.shrinkage)
                    row.update(
                        sample_loss=sample.loss(returns[target]),
                        shrinkage_loss=shrink.loss(returns[target]),
                        delta=fitted.intensity,
                        cancellation_clamped=fitted.cancellation_clamped,
                        sample_condition=sample.condition,
                        shrinkage_condition=shrink.condition,
                    )
                    row["difference"] = row["shrinkage_loss"] - row["sample_loss"]
                except NumericalFailure as exc:
                    write_json(
                        output / "primary-failure.json",
                        {**row, "error": str(exc), "preserved_targets": len(ledger)},
                    )
                    raise
                ledger.append(row)
                forecast_matrices.append([fitted.sample, fitted.shrinkage])
                handle.write(json.dumps(clean(row), allow_nan=False) + "\n")
        with (output / "forecasts.npz").open("xb") as handle:
            np.savez_compressed(
                handle,
                matrices=np.array(forecast_matrices),
                target_returns=returns[targets],
                target_dates=np.array([return_dates[index] for index in targets]),
            )
        differences = np.array([row["difference"] for row in ledger])
        summary = {
            "targets": len(ledger),
            "expected_targets": expected,
            "sample_mean_loss": float(np.mean([row["sample_loss"] for row in ledger])),
            "shrinkage_mean_loss": float(np.mean([row["shrinkage_loss"] for row in ledger])),
            "mean_difference": float(differences.mean()),
            "matrix_failures": 0,
            "known_inference_undercoverage": True,
            "uncertainty_failures": {},
        }
        try:
            summary["hac"] = hac_interval(differences)
        except NumericalFailure as exc:
            summary["uncertainty_failures"]["hac"] = str(exc)
        try:
            summary["bootstrap"] = bootstrap_interval(
                differences, np.random.Generator(np.random.PCG64(41002)), 4999
            )
        except NumericalFailure as exc:
            summary["uncertainty_failures"]["bootstrap"] = str(exc)
        portfolios = []
        monthly_indices = [
            i
            for i, day in enumerate(return_dates)
            if "2007-01-01" <= day <= "2025-12-31"
            and (i + 1 == len(return_dates) or return_dates[i + 1][:7] != day[:7])
        ]
        previous_valid = {}
        with (output / "monthly-weights.jsonl").open("x") as handle:
            for i in monthly_indices:
                fitted = estimate(returns[i - 251 : i + 1])
                row = {
                    "origin_date": return_dates[i],
                    "training_start_return_date": return_dates[i - 251],
                    "methods": {},
                }
                inverse = 1 / np.sqrt(np.diag(fitted.sample))
                inverse /= inverse.sum()
                for name, matrix in (("sample", fitted.sample), ("shrinkage", fitted.shrinkage)):
                    result = minimum_variance(matrix)
                    item = {"solver": asdict(result)}
                    if result.valid:
                        item.update(result.diagnostics())
                        if (
                            name in previous_valid
                            and previous_valid[name][0] == len(portfolios) - 1
                        ):
                            item["target_distance"] = float(
                                0.5 * np.abs(result.weights - previous_valid[name][1]).sum()
                            )
                        previous_valid[name] = (len(portfolios), result.weights.copy())
                    row["methods"][name] = item
                for name, weights in (("equal", np.full(8, 1 / 8)), ("inverse_vol", inverse)):
                    concentration = float(weights @ weights)
                    item = {
                        "weights": weights,
                        "concentration": concentration,
                        "effective_number": 1 / concentration,
                        "maximum_weight": float(weights.max()),
                    }
                    if name in previous_valid:
                        item["target_distance"] = float(
                            0.5 * np.abs(weights - previous_valid[name][1]).sum()
                        )
                    previous_valid[name] = (len(portfolios), weights.copy())
                    row["methods"][name] = item
                portfolios.append(clean(row))
                handle.write(json.dumps(clean(row), allow_nan=False) + "\n")
        summary["monthly_origins"] = len(portfolios)
        summary["portfolio_failures"] = {
            name: sum(not row["methods"][name]["solver"]["valid"] for row in portfolios)
            for name in ("sample", "shrinkage")
        }
        summary["complete_monthly_weight_pairs"] = sum(
            all(row["methods"][name]["solver"]["valid"] for name in ("sample", "shrinkage"))
            for row in portfolios
        )
        if any(sha(project / relative) != value for relative, value in source_hashes.items()):
            raise RuntimeError("Source modified during historical execution")
        write_json(output / "summary.json", summary)
        render_historical(output, ledger, portfolios, summary)
        hashes = {
            str(path.relative_to(output)): sha(path)
            for path in sorted(output.rglob("*"))
            if path.is_file()
        }
        write_json(output / "artifact-manifest.json", hashes)
        write_json(
            output / "completion.json",
            {
                "status": "complete",
                "completed_at_utc": now(),
                "paired_targets": len(ledger),
                "monthly_origins": len(portfolios),
            },
        )
        print(json.dumps(clean(summary), indent=2))
    except BaseException as exc:
        write_json(output / "execution-failure.json", {"time": now(), "error": repr(exc)})
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    acquisition = sub.add_parser("acquire")
    acquisition.add_argument("--output", type=Path, required=True)
    execution = sub.add_parser("run")
    execution.add_argument("--data", type=Path, required=True)
    execution.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "acquire":
        acquire(args.output.resolve())
    else:
        execute(args.data.resolve(), args.output.resolve())
